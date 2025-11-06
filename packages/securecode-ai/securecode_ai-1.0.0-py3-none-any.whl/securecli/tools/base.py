"""
Base class for security scanner tools
Provides common interface and utilities for all scanners
"""

import asyncio
import subprocess
import json
import tempfile
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from datetime import datetime

from ..schemas.findings import Finding, ToolEvidence


@dataclass
class ScanResult:
    """Result from a security scanner"""
    tool_name: str
    version: str
    scan_time: datetime
    target_path: str
    findings: List[Finding]
    raw_output: str
    metadata: Dict[str, Any]
    exit_code: int
    error_output: Optional[str] = None


class SecurityScannerBase(ABC):
    """Base class for all security scanners"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.tool_name = self.__class__.__name__.lower().replace('scanner', '')
        self.timeout = config.get('tools.timeout', 300)
        self.enabled = self.tool_name in config.get('tools.enabled', [])
        
        # Tool-specific configuration
        self.tool_config = config.get(f'tools.configs.{self.tool_name}', {})
        self.tool_path = config.get(f'tools.paths.{self.tool_name}')
    
    @abstractmethod
    async def scan(self, target_path: str, **kwargs) -> ScanResult:
        """
        Perform security scan on target
        
        Args:
            target_path: Path to scan
            **kwargs: Scanner-specific options
            
        Returns:
            ScanResult with findings
        """
        pass
    
    @abstractmethod
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """
        Convert tool-specific output to normalized Finding objects
        
        Args:
            raw_output: Raw tool output
            metadata: Additional metadata
            
        Returns:
            List of normalized Finding objects
        """
        pass
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if tool is available on system"""
        pass
    
    @abstractmethod
    def get_version(self) -> str:
        """Get tool version"""
        pass
    
    async def _run_command(
        self, 
        command: List[str], 
        cwd: Optional[str] = None,
        input_data: Optional[str] = None
    ) -> Tuple[str, str, int]:
        """
        Run command safely with timeout and capture output
        
        Args:
            command: Command and arguments
            cwd: Working directory
            input_data: Data to send to stdin
            
        Returns:
            Tuple of (stdout, stderr, exit_code)
        """
        try:
            process = await asyncio.create_subprocess_exec(
                *command,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                stdin=asyncio.subprocess.PIPE if input_data else None
            )
            
            stdout, stderr = await asyncio.wait_for(
                process.communicate(input=input_data.encode() if input_data else None),
                timeout=self.timeout
            )
            
            return (
                stdout.decode('utf-8', errors='replace'),
                stderr.decode('utf-8', errors='replace'),
                process.returncode or 0
            )
            
        except asyncio.TimeoutError:
            if process:
                process.kill()
                await process.wait()
            raise TimeoutError(f"Command timed out after {self.timeout} seconds")
        
        except Exception as e:
            raise RuntimeError(f"Command execution failed: {e}")
    
    def _create_temp_config(self, config_content: str, suffix: str = '.yml') -> str:
        """Create temporary configuration file"""
        with tempfile.NamedTemporaryFile(mode='w', suffix=suffix, delete=False) as f:
            f.write(config_content)
            return f.name
    
    def _severity_mapping(self, tool_severity: str) -> str:
        """Map tool-specific severity to standard severity levels"""
        severity_map = {
            # Common mappings
            'critical': 'Critical',
            'high': 'High', 
            'medium': 'Medium',
            'low': 'Low',
            'info': 'Low',
            'warning': 'Medium',
            'error': 'High',
            
            # Tool-specific mappings will be overridden in subclasses
        }
        
        normalized = tool_severity.lower().strip()
        return severity_map.get(normalized, 'Medium')
    
    def _calculate_cvss_score(self, severity: str, vulnerability_type: str) -> float:
        """Calculate basic CVSS score based on severity and type"""
        # Simplified CVSS scoring - should be enhanced with proper CVSS calculator
        base_scores = {
            'Critical': 9.0,
            'High': 7.5,
            'Medium': 5.5,
            'Low': 2.5
        }
        
        base_score = base_scores.get(severity, 5.0)
        
        # Adjust based on vulnerability type
        type_adjustments = {
            'injection': 1.0,
            'authentication': 0.8,
            'cryptography': 0.7,
            'authorization': 0.6,
            'information_disclosure': 0.4,
            'denial_of_service': 0.3
        }
        
        # Find matching type
        for vuln_type, adjustment in type_adjustments.items():
            if vuln_type in vulnerability_type.lower():
                base_score = min(10.0, base_score + adjustment)
                break
        
        return round(base_score, 1)
    
    def _map_to_cwe(self, vulnerability_type: str, description: str) -> List[str]:
        """Map vulnerability to CWE identifiers"""
        # Basic CWE mapping - should be enhanced with comprehensive database
        cwe_mappings = {
            'sql injection': ['CWE-89'],
            'xss': ['CWE-79'],
            'csrf': ['CWE-352'],
            'path traversal': ['CWE-22'],
            'command injection': ['CWE-78'],
            'buffer overflow': ['CWE-120'],
            'use after free': ['CWE-416'],
            'null pointer dereference': ['CWE-476'],
            'integer overflow': ['CWE-190'],
            'race condition': ['CWE-362'],
            'insecure random': ['CWE-338'],
            'weak crypto': ['CWE-327'],
            'hardcoded password': ['CWE-798'],
            'missing authentication': ['CWE-306'],
            'missing authorization': ['CWE-862'],
            'information disclosure': ['CWE-200'],
            'reentrancy': ['CWE-841'],  # Smart contract specific
        }
        
        found_cwes = []
        text_to_check = (vulnerability_type + " " + description).lower()
        
        for pattern, cwes in cwe_mappings.items():
            if pattern in text_to_check:
                found_cwes.extend(cwes)
        
        return found_cwes if found_cwes else ['CWE-1000']  # Generic weakness
    
    def _map_to_owasp(self, vulnerability_type: str) -> List[str]:
        """Map vulnerability to OWASP categories"""
        owasp_mappings = {
            'injection': ['A03:2021'],
            'authentication': ['A07:2021'],
            'sensitive data': ['A02:2021'],
            'xxe': ['A05:2021'],
            'broken access control': ['A01:2021'],
            'security misconfiguration': ['A05:2021'],
            'xss': ['A03:2021'],
            'deserialization': ['A08:2021'],
            'vulnerable components': ['A06:2021'],
            'logging': ['A09:2021'],
            'ssrf': ['A10:2021'],
        }
        
        text_to_check = vulnerability_type.lower()
        
        for pattern, owasp_ids in owasp_mappings.items():
            if pattern in text_to_check:
                return owasp_ids
        
        return ['A06:2021']  # Generic vulnerable components
    
    def _extract_code_snippet(
        self, 
        file_path: str, 
        line_number: int, 
        context_lines: int = 3
    ) -> str:
        """Extract code snippet around specified line"""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            
            snippet_lines = []
            for i in range(start_line, end_line):
                line_num = i + 1
                line_content = lines[i].rstrip()
                marker = ">>> " if line_num == line_number else "    "
                snippet_lines.append(f"{marker}{line_num:4d}: {line_content}")
            
            return "\n".join(snippet_lines)
            
        except Exception:
            return f"// Could not extract snippet from {file_path}:{line_number}"
    
    def _generate_poc(self, finding: Finding) -> str:
        """Generate proof of concept for finding"""
        # Basic PoC templates - should be enhanced per vulnerability type
        poc_templates = {
            'sql_injection': "# SQL Injection PoC\n# payload: ' OR 1=1 --",
            'xss': "# XSS PoC\n# payload: <script>alert('XSS')</script>",
            'path_traversal': "# Path Traversal PoC\n# payload: ../../etc/passwd",
            'command_injection': "# Command Injection PoC\n# payload: ; cat /etc/passwd",
        }
        
        vuln_type = finding.title.lower().replace(' ', '_')
        
        for template_key, template in poc_templates.items():
            if template_key in vuln_type:
                return template
        
        return "# Manual verification required"
    
    async def health_check(self) -> Dict[str, Any]:
        """Check tool health and availability"""
        return {
            'tool_name': self.tool_name,
            'available': self.is_available(),
            'version': self.get_version() if self.is_available() else None,
            'enabled': self.enabled,
            'config': self.tool_config
        }


# Alias for backward compatibility with language-specific tools  
BaseTool = SecurityScannerBase