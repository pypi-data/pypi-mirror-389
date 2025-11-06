"""
Cairo Smart Contract Security Analyzer for SecureCLI
Comprehensive Cairo smart contract security analysis for StarkNet
"""

import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import BaseTool
from ..schemas.findings import Finding, CVSSv4, ToolEvidence


class CairoAnalyzer(BaseTool):
    """
    Comprehensive Cairo smart contract security analyzer for StarkNet
    
    Integrates Cairo security analysis tools:
    - Cairo compiler: Built-in security checks
    - Protostar: Cairo development framework with testing
    - Custom Cairo security patterns
    - StarkNet-specific vulnerability patterns
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "cairo_analyzer"
        self.display_name = "Cairo Smart Contract Analyzer"
        self.description = "Comprehensive Cairo smart contract security analysis for StarkNet"
        self.version = "1.0.0"
    
    def is_available(self) -> bool:
        """Check if any Cairo analysis tools are available"""
        tools = [
            self._check_cairo(),
            self._check_protostar(),
            True  # Pattern analysis always available
        ]
        return any(tools)
    
    def _check_cairo(self) -> bool:
        """Check if Cairo compiler is available"""
        try:
            result = subprocess.run(
                ['cairo-compile', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_protostar(self) -> bool:
        """Check if Protostar is available"""
        try:
            result = subprocess.run(
                ['protostar', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Optional[Dict] = None) -> List[Finding]:
        """Perform comprehensive Cairo smart contract security analysis"""
        findings = []
        
        # Find Cairo contract files
        cairo_files = self._find_cairo_files(target_path)
        if not cairo_files:
            return findings
        
        # Check project type
        is_protostar_project = self._is_protostar_project(target_path)
        
        # Run tool-based analysis
        if self._check_cairo():
            findings.extend(await self._run_cairo_compiler_checks(cairo_files))
        
        if self._check_protostar() and is_protostar_project:
            findings.extend(await self._run_protostar_analysis(target_path))
        
        # Always run pattern analysis
        findings.extend(await self._run_cairo_pattern_analysis(cairo_files))
        
        return findings
    
    def _is_protostar_project(self, target_path: str) -> bool:
        """Check if target is a Protostar project"""
        protostar_toml = os.path.join(target_path, 'protostar.toml')
        return os.path.exists(protostar_toml)
    
    def _find_cairo_files(self, target_path: str) -> List[str]:
        """Find Cairo contract files"""
        cairo_extensions = {'.cairo'}
        cairo_files = []
        
        if os.path.isfile(target_path):
            if Path(target_path).suffix.lower() in cairo_extensions:
                cairo_files.append(target_path)
        else:
            for root, dirs, files in os.walk(target_path):
                # Skip build directories
                dirs[:] = [d for d in dirs if d not in ['build', 'cache', '.git', 'node_modules']]
                
                for file in files:
                    if Path(file).suffix.lower() in cairo_extensions:
                        cairo_files.append(os.path.join(root, file))
        
        return cairo_files
    
    async def _run_cairo_compiler_checks(self, cairo_files: List[str]) -> List[Finding]:
        """Run Cairo compiler checks"""
        findings = []
        
        for cairo_file in cairo_files:
            try:
                cmd = ['cairo-compile', cairo_file, '--output', '/dev/null']
                
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                # Parse compiler output for warnings/errors
                if stderr:
                    findings.extend(self._parse_cairo_compiler_output(stderr.decode(), cairo_file))
                    
            except Exception as e:
                continue  # Skip compilation errors
        
        return findings
    
    async def _run_protostar_analysis(self, target_path: str) -> List[Finding]:
        """Run Protostar analysis"""
        findings = []
        
        try:
            # Try to run tests which might reveal issues
            cmd = ['protostar', 'test', '--dry-run']
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse Protostar output
            if stderr:
                findings.extend(self._parse_protostar_output(stderr.decode(), target_path))
            
        except Exception as e:
            # Create a finding about Protostar failure
            finding = self._create_finding(
                file_path=target_path,
                title="Protostar Analysis Error",
                description=f"Failed to run Protostar analysis: {e}",
                severity="Low",
                lines="1",
                recommendation="Install Protostar: curl -L https://raw.githubusercontent.com/software-mansion/protostar/master/install.sh | bash"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_cairo_pattern_analysis(self, cairo_files: List[str]) -> List[Finding]:
        """Run custom Cairo security pattern analysis"""
        findings = []
        
        # Cairo-specific security patterns
        security_patterns = [
            # Access control
            ('@external', 'External Function', 'MEDIUM', 'External functions need proper access control'),
            ('@view', 'View Function', 'LOW', 'View functions should not modify state'),
            ('@constructor', 'Constructor', 'MEDIUM', 'Verify constructor access control'),
            
            # State management
            ('@storage_var', 'Storage Variable', 'LOW', 'Storage variables should be properly initialized'),
            ('felt', 'Felt Usage', 'LOW', 'Verify felt arithmetic overflow protection'),
            ('assert ', 'Assertion', 'MEDIUM', 'Assertions can cause transaction reversion'),
            
            # StarkNet specific
            ('get_caller_address()', 'Caller Address', 'MEDIUM', 'Verify caller address validation'),
            ('get_contract_address()', 'Contract Address', 'LOW', 'Contract address usage needs validation'),
            ('call_contract(', 'Contract Call', 'HIGH', 'External contract calls are risky'),
            ('library_call(', 'Library Call', 'MEDIUM', 'Library calls need validation'),
            ('delegate_call(', 'Delegate Call', 'HIGH', 'Delegate calls can be dangerous'),
            
            # Cryptographic operations
            ('pedersen_hash(', 'Hash Function', 'LOW', 'Verify hash input validation'),
            ('verify_ecdsa_signature(', 'Signature Verification', 'HIGH', 'Signature verification needs proper validation'),
            
            # Arithmetic operations
            ('*', 'Multiplication', 'LOW', 'Verify overflow protection in multiplication'),
            ('/', 'Division', 'MEDIUM', 'Check for division by zero'),
            ('+', 'Addition', 'LOW', 'Verify overflow protection in addition'),
            ('-', 'Subtraction', 'LOW', 'Verify underflow protection in subtraction'),
            ('**', 'Exponentiation', 'MEDIUM', 'Exponentiation can cause overflow'),
            
            # Array and struct operations
            ('[', 'Array Access', 'MEDIUM', 'Array access needs bounds checking'),
            ('len(', 'Length Function', 'LOW', 'Verify length calculation'),
            
            # Event logging
            ('@event', 'Event Definition', 'LOW', 'Events should not leak sensitive information'),
            
            # Import statements
            ('from starkware.', 'StarkWare Import', 'LOW', 'Verify imported library security'),
            ('from cairo_common.', 'Cairo Common Import', 'LOW', 'Verify common library usage'),
            
            # Memory operations
            ('alloc()', 'Memory Allocation', 'MEDIUM', 'Memory allocation needs bounds checking'),
            ('memcpy(', 'Memory Copy', 'HIGH', 'Memory copy operations can be unsafe'),
            ('memset(', 'Memory Set', 'MEDIUM', 'Memory set operations need validation'),
            
            # Serialization
            ('serialize_word(', 'Serialization', 'MEDIUM', 'Serialization needs input validation'),
            ('deserialize_word(', 'Deserialization', 'HIGH', 'Deserialization can be unsafe'),
            
            # Error handling
            ('with_attr error_message', 'Error Message', 'LOW', 'Error messages should not leak information'),
            
            # Range checks
            ('RANGE_CHECK_BOUND', 'Range Check', 'MEDIUM', 'Range checks need proper bounds'),
            
            # Bitwise operations
            ('bitwise_and(', 'Bitwise AND', 'LOW', 'Verify bitwise operation logic'),
            ('bitwise_or(', 'Bitwise OR', 'LOW', 'Verify bitwise operation logic'),
            ('bitwise_xor(', 'Bitwise XOR', 'LOW', 'Verify bitwise operation logic'),
            
            # Time-related functions
            ('get_block_timestamp()', 'Block Timestamp', 'MEDIUM', 'Block timestamp can be manipulated'),
            ('get_block_number()', 'Block Number', 'LOW', 'Block number can be predicted'),
            
            # Recursion
            ('tempvar', 'Temporary Variable', 'LOW', 'Temporary variables need proper scope'),
            ('ap +=', 'Stack Pointer', 'MEDIUM', 'Stack pointer manipulation is risky'),
            ('fp +', 'Frame Pointer', 'MEDIUM', 'Frame pointer manipulation is risky'),
            
            # Comments indicating issues
            ('TODO', 'TODO Comment', 'LOW', 'TODO comments may indicate incomplete code'),
            ('FIXME', 'FIXME Comment', 'MEDIUM', 'FIXME comments indicate known issues'),
            ('BUG', 'Bug Comment', 'HIGH', 'Bug comments indicate known problems'),
            ('HACK', 'Hack Comment', 'HIGH', 'Hack comments indicate workarounds'),
        ]
        
        for file_path in cairo_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    
                    # Skip comments for most patterns
                    if line_content.startswith('#'):
                        # Only check comment-specific patterns for comments
                        comment_patterns = [p for p in security_patterns if p[1] in ['TODO Comment', 'FIXME Comment', 'Bug Comment', 'Hack Comment']]
                        for pattern, vuln_type, severity, description in comment_patterns:
                            if pattern in line_content.upper():
                                finding = self._create_finding(
                                    file_path=file_path,
                                    title=f"Cairo {vuln_type}",
                                    description=f"{description}. Found: {line_content[:100]}",
                                    severity=severity,
                                    lines=str(line_num),
                                    snippet=line_content,
                                    recommendation=self._get_cairo_recommendation(vuln_type)
                                )
                                findings.append(finding)
                        continue
                    
                    for pattern, vuln_type, severity, description in security_patterns:
                        if vuln_type.endswith('Comment'):
                            continue  # Skip comment patterns for code lines
                            
                        if pattern in line_content:
                            finding = self._create_finding(
                                file_path=file_path,
                                title=f"Cairo {vuln_type}",
                                description=f"{description}. Found: {line_content[:100]}",
                                severity=severity,
                                lines=str(line_num),
                                snippet=line_content,
                                recommendation=self._get_cairo_recommendation(vuln_type)
                            )
                            findings.append(finding)
                            
            except Exception as e:
                continue  # Skip files that can't be read
        
        return findings
    
    def _parse_cairo_compiler_output(self, output: str, file_path: str) -> List[Finding]:
        """Parse Cairo compiler output for warnings"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'warning' in line.lower() or 'error' in line.lower():
                severity = 'HIGH' if 'error' in line.lower() else 'MEDIUM'
                
                finding = self._create_finding(
                    file_path=file_path,
                    title="Cairo Compiler Issue",
                    description=line.strip(),
                    severity=severity,
                    lines="1",
                    recommendation="Fix Cairo compiler warnings and errors"
                )
                findings.append(finding)
        
        return findings
    
    def _parse_protostar_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Protostar output for issues"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'error' in line.lower() or 'warning' in line.lower():
                severity = 'HIGH' if 'error' in line.lower() else 'MEDIUM'
                
                finding = self._create_finding(
                    file_path=target_path,
                    title="Protostar Issue",
                    description=line.strip(),
                    severity=severity,
                    lines="1",
                    recommendation="Fix Protostar build issues"
                )
                findings.append(finding)
        
        return findings
    
    def _get_cairo_recommendation(self, vuln_type: str) -> str:
        """Get specific recommendations for Cairo vulnerability types"""
        recommendations = {
            'External Function': 'Implement proper access control with caller validation',
            'Constructor': 'Ensure constructor has proper initialization logic',
            'Storage Variable': 'Initialize storage variables properly and validate access',
            'Caller Address': 'Validate caller address against authorized addresses',
            'Contract Call': 'Validate external contract addresses and handle failures',
            'Signature Verification': 'Properly validate ECDSA signatures and handle edge cases',
            'Division': 'Check for division by zero before performing division',
            'Array Access': 'Implement bounds checking for array access',
            'Memory Allocation': 'Validate memory allocation size and handle failures',
            'Memory Copy': 'Validate source and destination for memory operations',
            'Deserialization': 'Validate input data before deserialization',
            'Block Timestamp': 'Do not rely on block timestamp for critical logic',
            'Stack Pointer': 'Avoid manual stack pointer manipulation',
            'TODO Comment': 'Complete TODO items before deployment',
            'FIXME Comment': 'Fix known issues before deployment',
            'Bug Comment': 'Resolve bug comments before deployment',
            'Hack Comment': 'Replace hacks with proper solutions'
        }
        return recommendations.get(vuln_type, 'Review and fix the Cairo security issue')
    
    def _create_finding(self, file_path: str, title: str, description: str, 
                       severity: str, lines: str, snippet: str = None, 
                       recommendation: str = None) -> Finding:
        """Create a standardized Finding object"""
        
        # Create CVSS score
        cvss_scores = {'CRITICAL': 9.8, 'HIGH': 7.5, 'MEDIUM': 5.5, 'LOW': 3.0, 'INFO': 2.0}
        cvss_score = CVSSv4(
            score=cvss_scores.get(severity, 5.0),
            vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
        )
        
        # Create tool evidence
        evidence = ToolEvidence(
            tool_name=self.name,
            tool_version=self.version,
            confidence_score=80,
            raw_output=f"Cairo security analysis detected: {title}",
            analysis_metadata={
                'analyzer': 'CairoAnalyzer',
                'contract_type': 'cairo',
                'blockchain': 'starknet',
                'pattern_based': snippet is None,
                'file_path': file_path
            }
        )
        
        return Finding(
            file=file_path,
            title=title,
            description=description,
            lines=lines,
            impact=f"Cairo smart contract {severity.lower()} severity security issue that could affect StarkNet contract security and user funds",
            severity=severity.title(),
            cvss_v4=cvss_score,
            snippet=snippet or f"// Cairo smart contract analysis in {os.path.basename(file_path)}",
            recommendation=recommendation or "Review and address the Cairo smart contract security issue",
            sample_fix="// Implement proper Cairo security practices for StarkNet",
            poc="// No proof-of-concept available for static analysis finding",
            owasp=["A03:2021 – Injection", "A04:2021 – Insecure Design"],
            cwe=["CWE-20", "CWE-703"],
            references=[
                "https://www.cairo-lang.org/docs/",
                "https://starknet.io/docs/",
                "https://github.com/software-mansion/protostar",
                "https://book.starknet.io/",
                "https://github.com/starkware-libs/cairo-lang",
                "https://docs.starknet.io/documentation/"
            ],
            cross_file=[],
            tool_evidence=[evidence]
        )
    
    def get_version(self) -> str:
        """Get tool version"""
        return self.version
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """
        Convert tool-specific output to normalized Finding objects
        
        Args:
            raw_output: Raw tool output
            metadata: Additional metadata
            
        Returns:
            List of normalized Finding objects
        """
        findings = []
        
        # Parse the raw output and create Finding objects
        file_path = metadata.get('file_path', 'unknown.cairo')
        
        # Simple parsing - look for Cairo compiler errors and warnings
        lines = raw_output.strip().split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'security', 'cairo']):
                # Extract basic information from the line
                title = line.strip()
                description = f"Cairo security issue detected: {title}"
                
                # Determine severity based on content
                severity = 'Medium'
                if any(keyword in line.lower() for keyword in ['critical', 'external', 'unsafe']):
                    severity = 'High'
                elif 'warning' in line.lower():
                    severity = 'Medium'
                elif 'error' in line.lower():
                    severity = 'High'
                
                finding = self._create_finding(
                    file_path=file_path,
                    title=title[:100],  # Truncate if too long
                    description=description,
                    severity=severity,
                    lines=str(i + 1),
                    snippet=line.strip(),
                    recommendation=self._get_recommendation('General')
                )
                findings.append(finding)
        
        return findings


# Export the analyzer
__all__ = ['CairoAnalyzer']