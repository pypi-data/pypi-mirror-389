"""
Clarity Smart Contract Security Analyzer for SecureCLI
Comprehensive Clarity smart contract security analysis for Stacks Bitcoin
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


class ClarityAnalyzer(BaseTool):
    """
    Comprehensive Clarity smart contract security analyzer for Stacks
    
    Integrates Clarity security analysis tools:
    - Clarinet: Clarity development environment
    - clarity-repl: Interactive Clarity environment
    - Custom Clarity security patterns
    - Stacks-specific vulnerability patterns
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "clarity_analyzer"
        self.display_name = "Clarity Smart Contract Analyzer"
        self.description = "Comprehensive Clarity smart contract security analysis for Stacks Bitcoin"
        self.version = "1.0.0"
    
    def is_available(self) -> bool:
        """Check if any Clarity analysis tools are available"""
        tools = [
            self._check_clarinet(),
            self._check_clarity_repl(),
            True  # Pattern analysis always available
        ]
        return any(tools)
    
    def get_version(self) -> str:
        """Get analyzer version"""
        return self.version
    
    def normalize_findings(self, raw_findings: List[Dict]) -> List[Finding]:
        """Normalize raw findings to Finding objects"""
        findings = []
        for raw_finding in raw_findings:
            try:
                finding = Finding(**raw_finding)
                findings.append(finding)
            except Exception as e:
                # Log error and skip malformed findings
                continue
        return findings
    
    def _check_clarinet(self) -> bool:
        """Check if Clarinet is available"""
        try:
            result = subprocess.run(
                ['clarinet', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_clarity_repl(self) -> bool:
        """Check if clarity-repl is available"""
        try:
            result = subprocess.run(
                ['clarity-repl', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Optional[Dict] = None) -> List[Finding]:
        """Perform comprehensive Clarity smart contract security analysis"""
        findings = []
        
        # Find Clarity contract files
        clarity_files = self._find_clarity_files(target_path)
        if not clarity_files:
            return findings
        
        # Check project type
        is_clarinet_project = self._is_clarinet_project(target_path)
        
        # Run tool-based analysis
        if self._check_clarinet() and is_clarinet_project:
            findings.extend(await self._run_clarinet_analysis(target_path))
        
        if self._check_clarity_repl():
            findings.extend(await self._run_clarity_checks(clarity_files))
        
        # Always run pattern analysis
        findings.extend(await self._run_clarity_pattern_analysis(clarity_files))
        
        return findings
    
    def _is_clarinet_project(self, target_path: str) -> bool:
        """Check if target is a Clarinet project"""
        clarinet_toml = os.path.join(target_path, 'Clarinet.toml')
        return os.path.exists(clarinet_toml)
    
    def _find_clarity_files(self, target_path: str) -> List[str]:
        """Find Clarity contract files"""
        clarity_extensions = {'.clar'}
        clarity_files = []
        
        if os.path.isfile(target_path):
            if Path(target_path).suffix.lower() in clarity_extensions:
                clarity_files.append(target_path)
        else:
            for root, dirs, files in os.walk(target_path):
                # Skip build directories
                dirs[:] = [d for d in dirs if d not in ['deployments', 'cache', '.git', 'node_modules']]
                
                for file in files:
                    if Path(file).suffix.lower() in clarity_extensions:
                        clarity_files.append(os.path.join(root, file))
        
        return clarity_files
    
    async def _run_clarinet_analysis(self, target_path: str) -> List[Finding]:
        """Run Clarinet analysis"""
        findings = []
        
        try:
            # Run clarinet check
            cmd = ['clarinet', 'check']
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse Clarinet output
            if stderr:
                findings.extend(self._parse_clarinet_output(stderr.decode(), target_path))
            if stdout:
                findings.extend(self._parse_clarinet_output(stdout.decode(), target_path))
            
            # Also try to run tests to catch runtime issues
            try:
                test_cmd = ['clarinet', 'test', '--coverage']
                test_result = await asyncio.create_subprocess_exec(
                    *test_cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=target_path
                )
                test_stdout, test_stderr = await test_result.communicate()
                
                if test_stderr:
                    findings.extend(self._parse_clarinet_test_output(test_stderr.decode(), target_path))
            except Exception:
                pass  # Test failures are not critical for security analysis
            
        except Exception as e:
            # Create a finding about Clarinet failure
            finding = self._create_finding(
                file_path=target_path,
                title="Clarinet Analysis Error",
                description=f"Failed to run Clarinet analysis: {e}",
                severity="Low",
                lines="1",
                recommendation="Install Clarinet: curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh && cargo install clarinet"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_clarity_checks(self, clarity_files: List[str]) -> List[Finding]:
        """Run clarity-repl syntax checks"""
        findings = []
        
        for clarity_file in clarity_files:
            try:
                # Use clarity-repl to check syntax
                cmd = ['clarity-repl', '--check', clarity_file]
                
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE
                )
                
                stdout, stderr = await result.communicate()
                
                # Parse clarity-repl output
                if stderr:
                    findings.extend(self._parse_clarity_repl_output(stderr.decode(), clarity_file))
                    
            except Exception as e:
                continue  # Skip files that can't be checked
        
        return findings
    
    async def _run_clarity_pattern_analysis(self, clarity_files: List[str]) -> List[Finding]:
        """Run custom Clarity security pattern analysis"""
        findings = []
        
        # Clarity-specific security patterns
        security_patterns = [
            # Contract access control
            ('(define-public', 'Public Function', 'MEDIUM', 'Public functions need proper access control'),
            ('(define-read-only', 'Read-Only Function', 'LOW', 'Read-only functions should not modify state'),
            ('(define-private', 'Private Function', 'LOW', 'Private functions are only callable internally'),
            ('(define-constant', 'Constant Definition', 'LOW', 'Constants should be properly validated'),
            ('(define-data-var', 'Data Variable', 'MEDIUM', 'Data variables need proper access control'),
            ('(define-map', 'Map Definition', 'LOW', 'Maps need proper key validation'),
            ('(define-fungible-token', 'Fungible Token', 'HIGH', 'Token definitions need careful security review'),
            ('(define-non-fungible-token', 'Non-Fungible Token', 'HIGH', 'NFT definitions need security validation'),
            
            # Access control checks
            ('contract-caller', 'Contract Caller', 'MEDIUM', 'Contract caller validation is critical'),
            ('tx-sender', 'Transaction Sender', 'MEDIUM', 'Transaction sender should be validated'),
            ('is-eq contract-caller', 'Caller Check', 'LOW', 'Caller equality checks should be comprehensive'),
            ('is-eq tx-sender', 'Sender Check', 'LOW', 'Sender equality checks need validation'),
            
            # Arithmetic operations
            ('(+', 'Addition', 'LOW', 'Addition can overflow in Clarity'),
            ('(-', 'Subtraction', 'LOW', 'Subtraction can underflow in Clarity'),
            ('(*', 'Multiplication', 'MEDIUM', 'Multiplication can overflow'),
            ('(/', 'Division', 'HIGH', 'Division by zero causes runtime error'),
            ('(mod', 'Modulo', 'HIGH', 'Modulo by zero causes runtime error'),
            ('(pow', 'Power', 'MEDIUM', 'Power operations can cause overflow'),
            
            # Token operations
            ('ft-mint?', 'Token Mint', 'HIGH', 'Token minting needs authorization'),
            ('ft-burn?', 'Token Burn', 'HIGH', 'Token burning needs authorization'),
            ('ft-transfer?', 'Token Transfer', 'HIGH', 'Token transfers need validation'),
            ('ft-get-balance', 'Balance Check', 'LOW', 'Balance checks should handle errors'),
            ('nft-mint?', 'NFT Mint', 'HIGH', 'NFT minting needs authorization'),
            ('nft-burn?', 'NFT Burn', 'HIGH', 'NFT burning needs authorization'),
            ('nft-transfer?', 'NFT Transfer', 'HIGH', 'NFT transfers need validation'),
            
            # STX operations
            ('stx-transfer?', 'STX Transfer', 'HIGH', 'STX transfers are critical operations'),
            ('stx-burn?', 'STX Burn', 'CRITICAL', 'STX burning is irreversible'),
            ('stx-get-balance', 'STX Balance', 'LOW', 'STX balance checks should handle errors'),
            
            # Map operations
            ('map-set', 'Map Set', 'MEDIUM', 'Map set operations need validation'),
            ('map-insert', 'Map Insert', 'MEDIUM', 'Map insert operations should check duplicates'),
            ('map-delete', 'Map Delete', 'MEDIUM', 'Map delete operations need authorization'),
            ('map-get?', 'Map Get', 'LOW', 'Map get operations should handle none'),
            
            # Contract calls
            ('contract-call?', 'Contract Call', 'HIGH', 'External contract calls are risky'),
            ('as-contract', 'As Contract', 'HIGH', 'as-contract changes execution context'),
            
            # Error handling
            ('unwrap!', 'Unwrap', 'HIGH', 'unwrap! panics on errors - use unwrap-err-panic instead'),
            ('unwrap-err!', 'Unwrap Error', 'MEDIUM', 'unwrap-err! should be used carefully'),
            ('unwrap-panic', 'Unwrap Panic', 'HIGH', 'unwrap-panic should be avoided'),
            ('unwrap-err-panic', 'Unwrap Error Panic', 'MEDIUM', 'Use with meaningful error messages'),
            ('try!', 'Try', 'LOW', 'try! is deprecated, use match or if'),
            
            # Response handling
            ('ok ', 'OK Response', 'LOW', 'OK responses should be meaningful'),
            ('err ', 'Error Response', 'LOW', 'Error responses should use proper error codes'),
            ('is-ok', 'OK Check', 'LOW', 'OK checks should handle both cases'),
            ('is-err', 'Error Check', 'LOW', 'Error checks should handle both cases'),
            
            # Option handling
            ('some ', 'Some Option', 'LOW', 'Some values should be validated'),
            ('none', 'None Option', 'LOW', 'None should be handled properly'),
            ('is-some', 'Some Check', 'LOW', 'Some checks should handle none case'),
            ('is-none', 'None Check', 'LOW', 'None checks should handle some case'),
            
            # List operations
            ('list ', 'List Definition', 'LOW', 'Lists should have proper bounds'),
            ('append', 'List Append', 'LOW', 'List append should check limits'),
            ('len ', 'Length Function', 'LOW', 'Length functions should be validated'),
            ('element-at', 'Element Access', 'MEDIUM', 'Element access needs bounds checking'),
            
            # String operations
            ('concat', 'String Concat', 'LOW', 'String concatenation should check limits'),
            ('slice?', 'String Slice', 'MEDIUM', 'String slicing needs bounds checking'),
            
            # Type conversion
            ('int-to-ascii', 'Integer to ASCII', 'LOW', 'Type conversions should be validated'),
            ('int-to-utf8', 'Integer to UTF8', 'LOW', 'Type conversions should be validated'),
            ('string-to-int?', 'String to Integer', 'MEDIUM', 'String to int conversion can fail'),
            ('string-to-uint?', 'String to UInt', 'MEDIUM', 'String to uint conversion can fail'),
            
            # Block operations
            ('block-height', 'Block Height', 'MEDIUM', 'Block height can be manipulated'),
            ('burn-block-height', 'Burn Block Height', 'MEDIUM', 'Burn block height checks need validation'),
            
            # Principal operations
            ('principal-of?', 'Principal Of', 'MEDIUM', 'Principal operations need validation'),
            ('principal-construct?', 'Principal Construct', 'HIGH', 'Principal construction can fail'),
            
            # Hash operations
            ('hash160', 'Hash160', 'LOW', 'Hash operations should validate inputs'),
            ('sha256', 'SHA256', 'LOW', 'Hash operations should validate inputs'),
            ('sha512', 'SHA512', 'LOW', 'Hash operations should validate inputs'),
            
            # Signature verification
            ('secp256k1-recover?', 'Signature Recovery', 'HIGH', 'Signature recovery needs validation'),
            ('secp256k1-verify', 'Signature Verification', 'HIGH', 'Signature verification is critical'),
            
            # Comments indicating issues
            ('TODO', 'TODO Comment', 'LOW', 'TODO comments may indicate incomplete code'),
            ('FIXME', 'FIXME Comment', 'MEDIUM', 'FIXME comments indicate known issues'),
            ('BUG', 'Bug Comment', 'HIGH', 'Bug comments indicate known problems'),
            ('HACK', 'Hack Comment', 'HIGH', 'Hack comments indicate workarounds'),
            
            # Deprecated or risky patterns
            ('(var-set', 'Variable Set', 'MEDIUM', 'Variable modifications need authorization'),
            ('(var-get', 'Variable Get', 'LOW', 'Variable access should be validated'),
            
            # Advanced patterns
            ('fold ', 'Fold Operation', 'LOW', 'Fold operations should have proper bounds'),
            ('filter ', 'Filter Operation', 'LOW', 'Filter operations should be efficient'),
            ('map ', 'Map Operation', 'LOW', 'Map operations should handle large lists carefully'),
        ]
        
        for file_path in clarity_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    
                    # Skip comments for most patterns
                    if line_content.startswith(';;'):
                        # Only check comment-specific patterns for comments
                        comment_patterns = [p for p in security_patterns if p[1] in ['TODO Comment', 'FIXME Comment', 'Bug Comment', 'Hack Comment']]
                        for pattern, vuln_type, severity, description in comment_patterns:
                            if pattern in line_content.upper():
                                finding = self._create_finding(
                                    file_path=file_path,
                                    title=f"Clarity {vuln_type}",
                                    description=f"{description}. Found: {line_content[:100]}",
                                    severity=severity,
                                    lines=str(line_num),
                                    snippet=line_content,
                                    recommendation=self._get_clarity_recommendation(vuln_type)
                                )
                                findings.append(finding)
                        continue
                    
                    for pattern, vuln_type, severity, description in security_patterns:
                        if vuln_type.endswith('Comment'):
                            continue  # Skip comment patterns for code lines
                            
                        if pattern in line_content:
                            finding = self._create_finding(
                                file_path=file_path,
                                title=f"Clarity {vuln_type}",
                                description=f"{description}. Found: {line_content[:100]}",
                                severity=severity,
                                lines=str(line_num),
                                snippet=line_content,
                                recommendation=self._get_clarity_recommendation(vuln_type)
                            )
                            findings.append(finding)
                            
            except Exception as e:
                continue  # Skip files that can't be read
        
        return findings
    
    def _parse_clarinet_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Clarinet output for issues"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'error' in line.lower() or 'warning' in line.lower():
                severity = 'HIGH' if 'error' in line.lower() else 'MEDIUM'
                
                finding = self._create_finding(
                    file_path=target_path,
                    title="Clarinet Issue",
                    description=line.strip(),
                    severity=severity,
                    lines="1",
                    recommendation="Fix Clarinet build issues"
                )
                findings.append(finding)
        
        return findings
    
    def _parse_clarinet_test_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Clarinet test output for failures"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'failed' in line.lower() or 'panic' in line.lower():
                finding = self._create_finding(
                    file_path=target_path,
                    title="Clarinet Test Failure",
                    description=line.strip(),
                    severity='MEDIUM',
                    lines="1",
                    recommendation="Fix failing tests to ensure contract reliability"
                )
                findings.append(finding)
        
        return findings
    
    def _parse_clarity_repl_output(self, output: str, file_path: str) -> List[Finding]:
        """Parse clarity-repl output for syntax errors"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'error' in line.lower() or 'syntax' in line.lower():
                finding = self._create_finding(
                    file_path=file_path,
                    title="Clarity Syntax Issue",
                    description=line.strip(),
                    severity='HIGH',
                    lines="1",
                    recommendation="Fix Clarity syntax errors"
                )
                findings.append(finding)
        
        return findings
    
    def _get_clarity_recommendation(self, vuln_type: str) -> str:
        """Get specific recommendations for Clarity vulnerability types"""
        recommendations = {
            'Public Function': 'Implement proper caller validation using contract-caller or tx-sender',
            'Token Mint': 'Implement authorization checks before minting tokens',
            'Token Transfer': 'Validate transfer amounts and recipient addresses',
            'STX Transfer': 'Implement proper authorization for STX transfers',
            'STX Burn': 'Add multiple authorization layers for STX burning',
            'Contract Call': 'Validate external contract addresses and handle failures',
            'As Contract': 'Use as-contract carefully and validate the context change',
            'Unwrap': 'Use match or if statements instead of unwrap! to handle errors gracefully',
            'Division': 'Check for zero divisor before division operations',
            'Map Set': 'Validate map keys and values before setting',
            'Element Access': 'Check list bounds before accessing elements',
            'String Slice': 'Validate slice bounds to prevent runtime errors',
            'Principal Construct': 'Handle principal construction failures properly',
            'Signature Verification': 'Properly validate signatures and handle verification failures',
            'Block Height': 'Do not rely solely on block height for critical logic',
            'Variable Set': 'Implement authorization checks before modifying variables',
            'TODO Comment': 'Complete TODO items before deployment',
            'FIXME Comment': 'Fix known issues before deployment',
            'Bug Comment': 'Resolve bug comments before deployment',
            'Hack Comment': 'Replace hacks with proper solutions'
        }
        return recommendations.get(vuln_type, 'Review and fix the Clarity security issue')
    
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
            tool=self.name,
            id=f"clarity_{hash(title)%10000}",
            raw=f"Clarity security analysis detected: {title}"
        )
        
        return Finding(
            file=file_path,
            title=title,
            description=description,
            lines=lines,
            impact=f"Clarity smart contract {severity.lower()} severity security issue that could affect Stacks Bitcoin contract security and user funds",
            severity=severity.title(),
            cvss_v4=cvss_score,
            snippet=snippet or f";; Clarity smart contract analysis in {os.path.basename(file_path)}",
            recommendation=recommendation or "Review and address the Clarity smart contract security issue",
            sample_fix=";; Implement proper Clarity security practices for Stacks",
            poc=";; No proof-of-concept available for static analysis finding",
            owasp=["A03:2021 – Injection", "A04:2021 – Insecure Design"],
            cwe=["CWE-20", "CWE-703"],
            references=[
                "https://docs.stacks.co/write-smart-contracts/clarity-language/",
                "https://clarity-lang.org/",
                "https://github.com/hirosystems/clarinet",
                "https://book.clarity-lang.org/",
                "https://docs.stacks.co/write-smart-contracts/principals",
                "https://github.com/clarity-lang/reference"
            ],
            cross_file=[],
            tool_evidence=[evidence]
        )


# Export the analyzer
__all__ = ['ClarityAnalyzer']