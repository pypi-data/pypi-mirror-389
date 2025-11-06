"""
Move Smart Contract Security Analyzer for SecureCLI
Comprehensive Move smart contract security analysis for Aptos, Sui, and Diem
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


class MoveAnalyzer(BaseTool):
    """
    Comprehensive Move smart contract security analyzer
    
    Integrates Move security analysis tools:
    - Move compiler: Built-in security checks
    - Move Prover: Formal verification for Move
    - Aptos CLI: Aptos-specific analysis
    - Sui CLI: Sui-specific analysis
    - Custom Move security patterns
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "move_analyzer"
        self.display_name = "Move Smart Contract Analyzer"
        self.description = "Comprehensive Move smart contract security analysis for Aptos, Sui, and Diem"
        self.version = "1.0.0"
    
    def is_available(self) -> bool:
        """Check if any Move analysis tools are available"""
        tools = [
            self._check_move(),
            self._check_move_prover(),
            self._check_aptos_cli(),
            self._check_sui_cli(),
            True  # Pattern analysis always available
        ]
        return any(tools)
    
    def _check_move(self) -> bool:
        """Check if Move compiler is available"""
        try:
            result = subprocess.run(
                ['move', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_move_prover(self) -> bool:
        """Check if Move Prover is available"""
        try:
            result = subprocess.run(
                ['move', 'prove', '--help'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_aptos_cli(self) -> bool:
        """Check if Aptos CLI is available"""
        try:
            result = subprocess.run(
                ['aptos', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_sui_cli(self) -> bool:
        """Check if Sui CLI is available"""
        try:
            result = subprocess.run(
                ['sui', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Optional[Dict] = None) -> List[Finding]:
        """Perform comprehensive Move smart contract security analysis"""
        findings = []
        
        # Find Move contract files
        move_files = self._find_move_files(target_path)
        if not move_files:
            return findings
        
        # Detect project type
        project_type = self._detect_project_type(target_path)
        
        # Run tool-based analysis
        if self._check_move():
            findings.extend(await self._run_move_compiler_checks(move_files))
        
        if self._check_move_prover():
            findings.extend(await self._run_move_prover(target_path))
        
        if self._check_aptos_cli() and project_type == 'aptos':
            findings.extend(await self._run_aptos_analysis(target_path))
        
        if self._check_sui_cli() and project_type == 'sui':
            findings.extend(await self._run_sui_analysis(target_path))
        
        # Always run pattern analysis
        findings.extend(await self._run_move_pattern_analysis(move_files, project_type))
        
        return findings
    
    def _detect_project_type(self, target_path: str) -> str:
        """Detect Move project type (Aptos, Sui, or generic)"""
        # Check for Aptos project
        if os.path.exists(os.path.join(target_path, 'Move.toml')):
            try:
                with open(os.path.join(target_path, 'Move.toml'), 'r') as f:
                    content = f.read()
                    if 'aptos' in content.lower():
                        return 'aptos'
                    elif 'sui' in content.lower():
                        return 'sui'
            except FileNotFoundError:
                pass
        
        # Check for Sui project
        if os.path.exists(os.path.join(target_path, 'Sui.toml')):
            return 'sui'
        
        return 'generic'
    
    def _find_move_files(self, target_path: str) -> List[str]:
        """Find Move contract files"""
        move_extensions = {'.move'}
        move_files = []
        
        if os.path.isfile(target_path):
            if Path(target_path).suffix.lower() in move_extensions:
                move_files.append(target_path)
        else:
            for root, dirs, files in os.walk(target_path):
                # Skip build directories
                dirs[:] = [d for d in dirs if d not in ['build', 'target', '.git', 'node_modules']]
                
                for file in files:
                    if Path(file).suffix.lower() in move_extensions:
                        move_files.append(os.path.join(root, file))
        
        return move_files
    
    async def _run_move_compiler_checks(self, move_files: List[str]) -> List[Finding]:
        """Run Move compiler checks"""
        findings = []
        
        for move_file in move_files:
            try:
                # Get the directory containing the Move file
                move_dir = os.path.dirname(move_file)
                if not move_dir:
                    move_dir = '.'
                
                cmd = ['move', 'check', '--path', move_dir]
                
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=move_dir
                )
                
                stdout, stderr = await result.communicate()
                
                # Parse compiler output for warnings/errors
                if stderr:
                    findings.extend(self._parse_move_compiler_output(stderr.decode(), move_file))
                if stdout:
                    findings.extend(self._parse_move_compiler_output(stdout.decode(), move_file))
                    
            except Exception as e:
                continue  # Skip compilation errors
        
        return findings
    
    async def _run_move_prover(self, target_path: str) -> List[Finding]:
        """Run Move Prover formal verification"""
        findings = []
        
        try:
            cmd = ['move', 'prove', '--path', target_path]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse Move Prover output
            if stderr:
                findings.extend(self._parse_move_prover_output(stderr.decode(), target_path))
            if stdout:
                findings.extend(self._parse_move_prover_output(stdout.decode(), target_path))
            
        except Exception as e:
            # Create a finding about Move Prover failure
            finding = self._create_finding(
                file_path=target_path,
                title="Move Prover Analysis Error",
                description=f"Failed to run Move Prover: {e}",
                severity="Low",
                lines="1",
                recommendation="Install Move Prover: Follow Move installation guide"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_aptos_analysis(self, target_path: str) -> List[Finding]:
        """Run Aptos-specific analysis"""
        findings = []
        
        try:
            cmd = ['aptos', 'move', 'compile', '--package-dir', target_path]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse Aptos output
            if stderr:
                findings.extend(self._parse_aptos_output(stderr.decode(), target_path))
            
        except Exception as e:
            # Create a finding about Aptos analysis failure
            finding = self._create_finding(
                file_path=target_path,
                title="Aptos Analysis Error",
                description=f"Failed to run Aptos analysis: {e}",
                severity="Low",
                lines="1",
                recommendation="Install Aptos CLI: curl -fsSL 'https://aptos.dev/scripts/install_cli.py' | python3"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_sui_analysis(self, target_path: str) -> List[Finding]:
        """Run Sui-specific analysis"""
        findings = []
        
        try:
            cmd = ['sui', 'move', 'build', '--path', target_path]
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse Sui output
            if stderr:
                findings.extend(self._parse_sui_output(stderr.decode(), target_path))
            
        except Exception as e:
            # Create a finding about Sui analysis failure
            finding = self._create_finding(
                file_path=target_path,
                title="Sui Analysis Error",
                description=f"Failed to run Sui analysis: {e}",
                severity="Low",
                lines="1",
                recommendation="Install Sui CLI: cargo install --git https://github.com/MystenLabs/sui.git --bin sui sui"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_move_pattern_analysis(self, move_files: List[str], project_type: str) -> List[Finding]:
        """Run custom Move security pattern analysis"""
        findings = []
        
        # Move-specific security patterns
        security_patterns = [
            # Access control and permissions
            ('public entry fun', 'Public Entry Function', 'MEDIUM', 'Public entry functions need proper access control'),
            ('public fun', 'Public Function', 'LOW', 'Public functions should validate inputs'),
            ('friend', 'Friend Declaration', 'LOW', 'Friend modules have privileged access'),
            ('native', 'Native Function', 'HIGH', 'Native functions bypass Move VM safety'),
            
            # Resource management
            ('resource', 'Resource Declaration', 'LOW', 'Resources need proper ownership management'),
            ('struct ', 'Struct Declaration', 'LOW', 'Structs should have proper abilities'),
            ('has key', 'Key Ability', 'MEDIUM', 'Key ability allows global storage access'),
            ('has store', 'Store Ability', 'LOW', 'Store ability allows value persistence'),
            ('has copy', 'Copy Ability', 'LOW', 'Copy ability allows value duplication'),
            ('has drop', 'Drop Ability', 'LOW', 'Drop ability allows value destruction'),
            
            # Move operations
            ('move_to(', 'Move To Global', 'MEDIUM', 'Moving resources to global storage needs validation'),
            ('move_from(', 'Move From Global', 'HIGH', 'Moving resources from global storage is risky'),
            ('borrow_global(', 'Borrow Global', 'MEDIUM', 'Global borrowing needs proper access control'),
            ('borrow_global_mut(', 'Mutable Global Borrow', 'HIGH', 'Mutable global access is risky'),
            ('exists<', 'Resource Existence Check', 'LOW', 'Verify resource existence checks'),
            
            # Signer operations
            ('signer::', 'Signer Operation', 'MEDIUM', 'Signer operations need proper validation'),
            ('address_of(', 'Address Extraction', 'LOW', 'Address extraction should be validated'),
            
            # Arithmetic operations
            ('+', 'Addition', 'LOW', 'Addition can overflow in Move'),
            ('-', 'Subtraction', 'LOW', 'Subtraction can underflow in Move'),
            ('*', 'Multiplication', 'MEDIUM', 'Multiplication can overflow'),
            ('/', 'Division', 'HIGH', 'Division by zero causes abort'),
            ('%', 'Modulo', 'HIGH', 'Modulo by zero causes abort'),
            
            # Comparison and equality
            ('==', 'Equality Check', 'LOW', 'Verify equality comparison logic'),
            ('!=', 'Inequality Check', 'LOW', 'Verify inequality comparison logic'),
            
            # Assertions and aborts
            ('assert!(', 'Assertion', 'MEDIUM', 'Assertions cause transaction abort on failure'),
            ('abort ', 'Abort Statement', 'MEDIUM', 'Abort statements should use meaningful error codes'),
            
            # Vector operations
            ('vector::', 'Vector Operation', 'MEDIUM', 'Vector operations need bounds checking'),
            ('push_back(', 'Vector Push', 'LOW', 'Vector push operations need validation'),
            ('pop_back(', 'Vector Pop', 'MEDIUM', 'Vector pop can panic on empty vector'),
            ('borrow(', 'Vector Borrow', 'MEDIUM', 'Vector borrowing needs bounds checking'),
            ('borrow_mut(', 'Mutable Vector Borrow', 'MEDIUM', 'Mutable borrowing needs validation'),
            
            # Option operations
            ('option::', 'Option Operation', 'LOW', 'Option operations should handle None cases'),
            ('some(', 'Option Some', 'LOW', 'Option Some creation should be validated'),
            ('none(', 'Option None', 'LOW', 'Option None should be handled properly'),
            ('extract(', 'Option Extract', 'HIGH', 'Option extract panics on None'),
            
            # String operations
            ('string::', 'String Operation', 'LOW', 'String operations need input validation'),
            ('utf8(', 'UTF-8 Conversion', 'MEDIUM', 'UTF-8 conversion can fail'),
            
            # Cryptographic operations
            ('hash::', 'Hash Operation', 'LOW', 'Hash operations should validate inputs'),
            ('signature::', 'Signature Operation', 'HIGH', 'Signature operations need proper validation'),
            ('ed25519', 'Ed25519 Signature', 'MEDIUM', 'Ed25519 signatures need proper verification'),
            ('secp256k1', 'Secp256k1 Signature', 'MEDIUM', 'Secp256k1 signatures need validation'),
            
            # Time operations
            ('timestamp::', 'Timestamp Operation', 'MEDIUM', 'Timestamp can be manipulated by validators'),
            
            # Account operations (Aptos-specific)
            ('account::', 'Account Operation', 'MEDIUM', 'Account operations need proper authorization'),
            ('coin::', 'Coin Operation', 'HIGH', 'Coin operations affect financial security'),
            ('token::', 'Token Operation', 'HIGH', 'Token operations need careful validation'),
            
            # Object operations (Sui-specific)
            ('object::', 'Object Operation', 'MEDIUM', 'Object operations need ownership validation'),
            ('transfer::', 'Transfer Operation', 'HIGH', 'Transfer operations affect ownership'),
            ('sui::', 'Sui Framework', 'LOW', 'Sui framework usage needs validation'),
            
            # Event operations
            ('event::', 'Event Operation', 'LOW', 'Events should not leak sensitive information'),
            ('emit(', 'Event Emission', 'LOW', 'Event emission should be validated'),
            
            # Table operations
            ('table::', 'Table Operation', 'MEDIUM', 'Table operations need proper access control'),
            ('add(', 'Table Add', 'LOW', 'Table additions should validate keys'),
            ('remove(', 'Table Remove', 'MEDIUM', 'Table removal should check existence'),
            
            # Gas and limits
            ('while (', 'While Loop', 'MEDIUM', 'While loops can cause gas limit issues'),
            ('loop {', 'Infinite Loop', 'HIGH', 'Infinite loops can cause transaction failure'),
            
            # Comments indicating issues
            ('TODO', 'TODO Comment', 'LOW', 'TODO comments may indicate incomplete code'),
            ('FIXME', 'FIXME Comment', 'MEDIUM', 'FIXME comments indicate known issues'),
            ('BUG', 'Bug Comment', 'HIGH', 'Bug comments indicate known problems'),
            ('HACK', 'Hack Comment', 'HIGH', 'Hack comments indicate workarounds'),
        ]
        
        for file_path in move_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    
                    # Skip comments for most patterns
                    if line_content.startswith('//'):
                        # Only check comment-specific patterns for comments
                        comment_patterns = [p for p in security_patterns if p[1] in ['TODO Comment', 'FIXME Comment', 'Bug Comment', 'Hack Comment']]
                        for pattern, vuln_type, severity, description in comment_patterns:
                            if pattern in line_content.upper():
                                finding = self._create_finding(
                                    file_path=file_path,
                                    title=f"Move {vuln_type}",
                                    description=f"{description}. Found: {line_content[:100]}",
                                    severity=severity,
                                    lines=str(line_num),
                                    snippet=line_content,
                                    recommendation=self._get_move_recommendation(vuln_type, project_type)
                                )
                                findings.append(finding)
                        continue
                    
                    for pattern, vuln_type, severity, description in security_patterns:
                        if vuln_type.endswith('Comment'):
                            continue  # Skip comment patterns for code lines
                            
                        if pattern in line_content:
                            finding = self._create_finding(
                                file_path=file_path,
                                title=f"Move {vuln_type}",
                                description=f"{description}. Found: {line_content[:100]}",
                                severity=severity,
                                lines=str(line_num),
                                snippet=line_content,
                                recommendation=self._get_move_recommendation(vuln_type, project_type)
                            )
                            findings.append(finding)
                            
            except Exception as e:
                continue  # Skip files that can't be read
        
        return findings
    
    def _parse_move_compiler_output(self, output: str, file_path: str) -> List[Finding]:
        """Parse Move compiler output for warnings"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'warning' in line.lower() or 'error' in line.lower():
                severity = 'HIGH' if 'error' in line.lower() else 'MEDIUM'
                
                finding = self._create_finding(
                    file_path=file_path,
                    title="Move Compiler Issue",
                    description=line.strip(),
                    severity=severity,
                    lines="1",
                    recommendation="Fix Move compiler warnings and errors"
                )
                findings.append(finding)
        
        return findings
    
    def _parse_move_prover_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Move Prover output for verification failures"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'failed' in line.lower() or 'error' in line.lower():
                finding = self._create_finding(
                    file_path=target_path,
                    title="Move Prover Verification Failure",
                    description=line.strip(),
                    severity='HIGH',
                    lines="1",
                    recommendation="Fix Move Prover verification failures"
                )
                findings.append(finding)
        
        return findings
    
    def _parse_aptos_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Aptos CLI output for issues"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'error' in line.lower() or 'warning' in line.lower():
                severity = 'HIGH' if 'error' in line.lower() else 'MEDIUM'
                
                finding = self._create_finding(
                    file_path=target_path,
                    title="Aptos Build Issue",
                    description=line.strip(),
                    severity=severity,
                    lines="1",
                    recommendation="Fix Aptos build issues"
                )
                findings.append(finding)
        
        return findings
    
    def _parse_sui_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Sui CLI output for issues"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'error' in line.lower() or 'warning' in line.lower():
                severity = 'HIGH' if 'error' in line.lower() else 'MEDIUM'
                
                finding = self._create_finding(
                    file_path=target_path,
                    title="Sui Build Issue",
                    description=line.strip(),
                    severity=severity,
                    lines="1",
                    recommendation="Fix Sui build issues"
                )
                findings.append(finding)
        
        return findings
    
    def _get_move_recommendation(self, vuln_type: str, project_type: str) -> str:
        """Get specific recommendations for Move vulnerability types"""
        recommendations = {
            'Public Entry Function': 'Implement proper authorization checks for entry functions',
            'Native Function': 'Avoid native functions or audit them carefully',
            'Move From Global': 'Verify authorization before moving resources from global storage',
            'Mutable Global Borrow': 'Implement access control for mutable global borrows',
            'Division': 'Check for zero divisor before division operations',
            'Modulo': 'Check for zero divisor before modulo operations',
            'Assertion': 'Use meaningful error codes in assertions',
            'Vector Pop': 'Check vector length before pop operations',
            'Option Extract': 'Use option::borrow or pattern matching instead of extract',
            'Signature Operation': 'Properly validate signatures and handle verification failures',
            'Coin Operation': 'Implement proper authorization for coin operations',
            'Transfer Operation': 'Validate ownership before transfer operations',
            'While Loop': 'Implement loop bounds to prevent gas limit issues',
            'Infinite Loop': 'Add break conditions to prevent infinite loops',
            'TODO Comment': 'Complete TODO items before deployment',
            'FIXME Comment': 'Fix known issues before deployment',
            'Bug Comment': 'Resolve bug comments before deployment',
            'Hack Comment': 'Replace hacks with proper solutions'
        }
        
        base_recommendation = recommendations.get(vuln_type, 'Review and fix the Move security issue')
        
        # Add project-specific context
        if project_type == 'aptos':
            base_recommendation += ' (Aptos-specific: Consider Aptos framework best practices)'
        elif project_type == 'sui':
            base_recommendation += ' (Sui-specific: Consider Sui object model best practices)'
        
        return base_recommendation
    
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
            confidence_score=85,
            raw_output=f"Move security analysis detected: {title}",
            analysis_metadata={
                'analyzer': 'MoveAnalyzer',
                'contract_type': 'move',
                'blockchain': 'aptos/sui/diem',
                'pattern_based': snippet is None,
                'file_path': file_path
            }
        )
        
        return Finding(
            file=file_path,
            title=title,
            description=description,
            lines=lines,
            impact=f"Move smart contract {severity.lower()} severity security issue that could affect contract security and user assets",
            severity=severity.title(),
            cvss_v4=cvss_score,
            snippet=snippet or f"// Move smart contract analysis in {os.path.basename(file_path)}",
            recommendation=recommendation or "Review and address the Move smart contract security issue",
            sample_fix="// Implement proper Move security practices",
            poc="// No proof-of-concept available for static analysis finding",
            owasp=["A03:2021 – Injection", "A04:2021 – Insecure Design"],
            cwe=["CWE-20", "CWE-703"],
            references=[
                "https://move-language.github.io/move/",
                "https://aptos.dev/move/move-on-aptos/",
                "https://docs.sui.io/devnet/build/move",
                "https://github.com/move-language/move",
                "https://aptos.dev/guides/move-guides/move-security-guidelines/",
                "https://docs.sui.io/devnet/build/programming-with-objects"
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
        file_path = metadata.get('file_path', 'unknown.move')
        
        # Simple parsing - look for Move compiler errors and warnings
        lines = raw_output.strip().split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'security', 'unsafe', 'resource']):
                # Extract basic information from the line
                title = line.strip()
                description = f"Move smart contract issue detected: {title}"
                
                # Determine severity based on content
                severity = 'Medium'
                if any(keyword in line.lower() for keyword in ['critical', 'unsafe', 'resource leak']):
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
                    recommendation=self._get_move_recommendation('General', 'aptos')
                )
                findings.append(finding)
        
        return findings


# Export the analyzer
__all__ = ['MoveAnalyzer']