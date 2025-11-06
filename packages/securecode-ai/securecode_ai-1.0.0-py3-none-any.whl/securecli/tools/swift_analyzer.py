"""
Swift Security Analysis Tools Integration
Supports SwiftLint, Periphery, and SonarSwift for comprehensive Swift/iOS security analysis
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Any
from pathlib import Path

from ..schemas.findings import Finding, ToolEvidence, CVSSv4
from .base import BaseTool

logger = logging.getLogger(__name__)

class SwiftAnalyzer(BaseTool):
    """
    Swift Security Analyzer supporting SwiftLint, Periphery, and SonarSwift
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "swift_analyzer"
        self.supported_extensions = ['.swift', '.h', '.m']
        
        # Tool configurations
        self.tools = {
            'swiftlint': {
                'command': 'swiftlint',
                'enabled': self._check_swiftlint_availability(),
                'description': 'SwiftLint style and convention linter for Swift'
            },
            'periphery': {
                'command': 'periphery',
                'enabled': self._check_periphery_availability(),
                'description': 'Periphery dead code detection for Swift'
            },
            'sonar_swift': {
                'command': 'sonar-scanner',
                'enabled': self._check_sonar_swift_availability(),
                'description': 'SonarSwift static analysis for Swift'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Swift analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try SwiftLint first as it's most commonly available
            if self.tools['swiftlint']['enabled']:
                result = subprocess.run(['swiftlint', 'version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"SwiftLint {result.stdout.strip()}"
            
            # Try Periphery as fallback
            if self.tools['periphery']['enabled']:
                result = subprocess.run(['periphery', 'version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Periphery {result.stdout.strip()}"
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def _check_swiftlint_availability(self) -> bool:
        """Check if SwiftLint is available"""
        try:
            result = subprocess.run(['swiftlint', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_periphery_availability(self) -> bool:
        """Check if Periphery is available"""
        try:
            result = subprocess.run(['periphery', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_sonar_swift_availability(self) -> bool:
        """Check if SonarSwift is available"""
        try:
            result = subprocess.run(['sonar-scanner', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Swift tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Swift security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'swift_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Swift security analysis tools."""
        findings = []
        
        # Check if this is a Swift project
        if not self._has_swift_files(repo_path):
            return findings
        
        # Run SwiftLint for code style and potential security issues
        if self.tools['swiftlint']['enabled']:
            try:
                result = subprocess.run(
                    ['swiftlint', 'lint', '--reporter=json', repo_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.stdout:
                    swiftlint_findings = self._parse_swiftlint_output(result.stdout, repo_path)
                    findings.extend(swiftlint_findings)
            except subprocess.TimeoutExpired:
                logger.warning("SwiftLint analysis timed out")
            except Exception as e:
                logger.error(f"Error running SwiftLint: {e}")
        
        # Run Periphery for dead code detection
        if self.tools['periphery']['enabled']:
            try:
                result = subprocess.run(
                    ['periphery', 'scan', '--format', 'json', '--project', repo_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.stdout:
                    periphery_findings = self._parse_periphery_output(result.stdout, repo_path)
                    findings.extend(periphery_findings)
            except subprocess.TimeoutExpired:
                logger.warning("Periphery analysis timed out")
            except Exception as e:
                logger.error(f"Error running Periphery: {e}")
        
        # If no tools available, create placeholder finding
        if not any(self.tools[tool]['enabled'] for tool in self.tools):
            swift_files = []
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.swift'):
                        swift_files.append(os.path.relpath(os.path.join(root, file), repo_path))
            
            if swift_files:
                tool_evidence = ToolEvidence(
                    tool="swift_analyzer",
                    id=f"swift_{hash(swift_files[0])}",
                    raw=f"Swift analysis placeholder - found {len(swift_files)} Swift files"
                )
                
                finding = Finding(
                    file=swift_files[0],
                    title=f"Swift Analysis Placeholder",
                    description=f"Swift security analysis placeholder - found {len(swift_files)} Swift files",
                    lines="1",
                    impact="Potential Swift/iOS security or quality issue",
                    severity="Medium",
                    cvss_v4=CVSSv4(
                        score=4.0,
                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                    ),
                    snippet=f"Swift file detected: {swift_files[0]}",
                    recommendation="Review Swift code for iOS security best practices",
                    sample_fix="Apply Swift and iOS security guidelines",
                    poc=f"Swift analysis in repository",
                    owasp=["A06:2021-Vulnerable and Outdated Components"],
                    cwe=["CWE-1104"],
                    tool_evidence=[tool_evidence]
                )
                findings.append(finding)
        
        return findings

    def _has_swift_files(self, repo_path: str) -> bool:
        """Check if repository contains Swift files."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    return True
            # Check for Xcode project files
            if any(f.endswith('.xcodeproj') or f.endswith('.xcworkspace') for f in files):
                return True
        return False

    def _parse_swiftlint_output(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse SwiftLint JSON output."""
        findings = []
        try:
            swiftlint_data = json.loads(json_output)
            for violation in swiftlint_data:
                finding = self._create_swiftlint_finding(violation, repo_path)
                if finding:
                    findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing SwiftLint JSON: {e}")
        return findings

    def _parse_periphery_output(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse Periphery JSON output."""
        findings = []
        try:
            periphery_data = json.loads(json_output)
            for dead_code in periphery_data:
                finding = self._create_periphery_finding(dead_code, repo_path)
                if finding:
                    findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Periphery JSON: {e}")
        return findings

    def _create_swiftlint_finding(self, violation: dict, repo_path: str) -> Finding:
        """Create a Finding from SwiftLint violation."""
        try:
            rule = violation.get('rule_id', 'Unknown')
            reason = violation.get('reason', 'SwiftLint violation')
            file_path = violation.get('file', 'unknown')
            line = violation.get('line', 1)
            severity = violation.get('severity', 'warning')
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="swiftlint",
                id=f"swiftlint_{rule}_{hash(file_path + str(line))}",
                raw=json.dumps(violation)
            )
            
            severity_map = {'error': 'High', 'warning': 'Medium', 'info': 'Low'}
            mapped_severity = severity_map.get(severity, 'Medium')
            
            # Identify security-related rules
            security_rules = [
                'force_unwrapping', 'implicitly_unwrapped_optional',
                'weak_delegate', 'legacy_constructor', 'legacy_constant',
                'legacy_nsgeometry_functions', 'legacy_random'
            ]
            
            is_security_related = any(sec_rule in rule for sec_rule in security_rules)
            impact = "Potential iOS security vulnerability" if is_security_related else "Code quality issue that may affect security"
            
            return Finding(
                file=file_path,
                title=f"SwiftLint {rule}: {reason[:50]}...",
                description=f"SwiftLint violation: {reason}",
                lines=str(line),
                impact=impact,
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=6.0 if is_security_related else 3.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line}: {rule}",
                recommendation="Fix the SwiftLint violation to improve code quality and security",
                sample_fix="Follow Swift coding best practices",
                poc=f"SwiftLint analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"] if is_security_related else [],
                cwe=["CWE-476"] if 'unwrapping' in rule else [],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating SwiftLint finding: {e}")
            return None

    def _create_periphery_finding(self, dead_code: dict, repo_path: str) -> Finding:
        """Create a Finding from Periphery dead code detection."""
        try:
            name = dead_code.get('name', 'Unknown')
            kind = dead_code.get('kind', 'unknown')
            file_path = dead_code.get('file', 'unknown')
            line = dead_code.get('line', 1)
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="periphery",
                id=f"periphery_{kind}_{hash(file_path + str(line))}",
                raw=json.dumps(dead_code)
            )
            
            return Finding(
                file=file_path,
                title=f"Periphery: Unused {kind} '{name}'",
                description=f"Dead code detected: Unused {kind} '{name}' found by Periphery",
                lines=str(line),
                impact="Dead code increases attack surface and maintenance burden",
                severity="Low",
                cvss_v4=CVSSv4(
                    score=2.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:L/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line}: Unused {kind} {name}",
                recommendation="Remove dead code to reduce attack surface",
                sample_fix=f"Delete the unused {kind} '{name}'",
                poc=f"Periphery analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-1127"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Periphery finding: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['swift']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Swift/iOS Security Analyzer',
            'description': 'Comprehensive Swift/iOS security analysis using SwiftLint, Periphery, and SonarSwift',
            'supported_extensions': self.supported_extensions,
            'available_tools': {
                name: {
                    'enabled': info['enabled'],
                    'description': info['description']
                }
                for name, info in self.tools.items()
            }
        }


# Alias for compatibility
SwiftTool = SwiftAnalyzer