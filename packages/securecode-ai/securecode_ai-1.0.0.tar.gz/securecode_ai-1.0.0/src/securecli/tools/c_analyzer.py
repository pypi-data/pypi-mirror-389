"""
C Security Analyzer for SecureCLI
Comprehensive C security analysis using multiple tools and patterns
"""

import asyncio
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import BaseTool
from ..schemas.findings import Finding, CVSSv4, ToolEvidence


class CAnalyzer(BaseTool):
    """
    Comprehensive C security analyzer
    
    Integrates multiple C security analysis tools:
    - Clang Static Analyzer: LLVM-based static analysis
    - Splint: Lightweight static checker for C
    - Frama-C: Framework for static analysis (if available)
    - CBMC: Bounded model checker (if available)
    - Custom security pattern detection
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "c_analyzer"
        self.display_name = "C Security Analyzer"
        self.description = "Comprehensive C security analysis using Clang, Splint, and security patterns"
        self.version = "1.0.0"
    
    def is_available(self) -> bool:
        """Check if any C analysis tools are available"""
        tools = [
            self._check_clang_analyzer(),
            self._check_splint(),
            True  # Pattern analysis always available
        ]
        return any(tools)
    
    def _check_clang_analyzer(self) -> bool:
        """Check if Clang Static Analyzer is available"""
        try:
            result = subprocess.run(
                ['clang', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_splint(self) -> bool:
        """Check if Splint is available"""
        try:
            result = subprocess.run(
                ['splint', '-help'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Optional[Dict] = None) -> List[Finding]:
        """Perform comprehensive C security analysis"""
        findings = []
        
        # Find C files
        c_files = self._find_c_files(target_path)
        if not c_files:
            return findings
        
        # Run available tools
        if self._check_clang_analyzer():
            findings.extend(await self._run_clang_analyzer(c_files, target_path))
        
        if self._check_splint():
            findings.extend(await self._run_splint(c_files, target_path))
        
        # Always run pattern analysis
        findings.extend(await self._run_pattern_analysis(c_files))
        
        return findings
    
    def _find_c_files(self, target_path: str) -> List[str]:
        """Find C source files"""
        c_extensions = {'.c', '.h'}
        c_files = []
        
        if os.path.isfile(target_path):
            if Path(target_path).suffix.lower() in c_extensions:
                c_files.append(target_path)
        else:
            for root, dirs, files in os.walk(target_path):
                for file in files:
                    if Path(file).suffix.lower() in c_extensions:
                        c_files.append(os.path.join(root, file))
        
        return c_files
    
    async def _run_clang_analyzer(self, c_files: List[str], target_path: str) -> List[Finding]:
        """Run Clang Static Analyzer for C"""
        findings = []
        
        for file_path in c_files[:10]:  # Limit for performance
            try:
                # Run clang static analyzer with C-specific checks
                cmd = [
                    'clang', '--analyze', 
                    '-Xanalyzer', '-analyzer-output=text',
                    '-Xanalyzer', '-analyzer-checker=security',
                    '-Xanalyzer', '-analyzer-checker=alpha.security',
                    '-Xanalyzer', '-analyzer-checker=unix',
                    '-Xanalyzer', '-analyzer-checker=alpha.unix',
                    file_path
                ]
                
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=target_path
                )
                
                stdout, stderr = await result.communicate()
                
                # Parse Clang analyzer output
                if stderr:
                    findings.extend(self._parse_clang_output(stderr.decode(), file_path))
                    
            except Exception as e:
                # Create a finding about the analysis failure
                finding = self._create_finding(
                    file_path=file_path,
                    title="Clang Analysis Error",
                    description=f"Failed to run Clang static analyzer: {e}",
                    severity="Low",
                    lines="1",
                    recommendation="Ensure Clang is properly installed and configured"
                )
                findings.append(finding)
        
        return findings
    
    async def _run_splint(self, c_files: List[str], target_path: str) -> List[Finding]:
        """Run Splint static analysis"""
        findings = []
        
        for file_path in c_files[:15]:  # Limit files for performance
            try:
                # Prepare Splint command
                cmd = [
                    'splint',
                    '+bounds',      # Buffer overflow detection
                    '+nullret',     # Null pointer return
                    '+usedef',      # Use before definition
                    '+mustfreefresh',  # Memory management
                    file_path
                ]
                
                result = await asyncio.create_subprocess_exec(
                    *cmd,
                    stdout=asyncio.subprocess.PIPE,
                    stderr=asyncio.subprocess.PIPE,
                    cwd=target_path
                )
                
                stdout, stderr = await result.communicate()
                
                # Parse Splint output
                if stdout:
                    findings.extend(self._parse_splint_output(stdout.decode(), file_path))
                    
            except Exception as e:
                # Create a finding about Splint failure
                finding = self._create_finding(
                    file_path=file_path,
                    title="Splint Analysis Error", 
                    description=f"Failed to run Splint: {e}",
                    severity="Low",
                    lines="1",
                    recommendation="Install Splint: apt-get install splint or brew install splint"
                )
                findings.append(finding)
        
        return findings
    
    async def _run_pattern_analysis(self, c_files: List[str]) -> List[Finding]:
        """Run custom C security pattern analysis"""
        findings = []
        
        # C security patterns - more comprehensive than C++
        security_patterns = [
            # Critical Buffer Overflow Issues
            ('strcpy(', 'Buffer Overflow', 'CRITICAL', 'strcpy() is extremely dangerous - use strncpy()'),
            ('strcat(', 'Buffer Overflow', 'CRITICAL', 'strcat() can cause buffer overflow - use strncat()'),
            ('sprintf(', 'Buffer Overflow', 'CRITICAL', 'sprintf() can cause buffer overflow - use snprintf()'),
            ('gets(', 'Buffer Overflow', 'CRITICAL', 'gets() is banned - use fgets() instead'),
            ('scanf(', 'Buffer Overflow', 'HIGH', 'scanf() can cause buffer overflow - limit field width'),
            
            # Memory Management
            ('malloc(', 'Memory Management', 'MEDIUM', 'malloc() requires careful memory management'),
            ('calloc(', 'Memory Management', 'MEDIUM', 'calloc() requires careful memory management'),
            ('realloc(', 'Memory Management', 'MEDIUM', 'realloc() can fail - check return value'),
            ('free(', 'Memory Management', 'MEDIUM', 'free() - ensure no double-free or use-after-free'),
            ('alloca(', 'Stack Overflow', 'HIGH', 'alloca() can cause stack overflow'),
            
            # Format String Vulnerabilities
            ('printf(', 'Format String', 'HIGH', 'printf() with user input can be dangerous'),
            ('fprintf(', 'Format String', 'HIGH', 'fprintf() with user input can be dangerous'),
            ('snprintf(', 'Format String', 'MEDIUM', 'snprintf() format string should be constant'),
            
            # Integer Issues
            ('atoi(', 'Integer Overflow', 'MEDIUM', 'atoi() does not handle errors - use strtol()'),
            ('atol(', 'Integer Overflow', 'MEDIUM', 'atol() does not handle errors - use strtoll()'),
            ('strtol(', 'Integer Overflow', 'LOW', 'strtol() - check for overflow conditions'),
            
            # File and System Operations
            ('fopen(', 'File Security', 'MEDIUM', 'fopen() - validate file paths and check permissions'),
            ('system(', 'Command Injection', 'CRITICAL', 'system() can lead to command injection'),
            ('exec(', 'Command Injection', 'HIGH', 'exec family functions need careful input validation'),
            ('popen(', 'Command Injection', 'HIGH', 'popen() can be dangerous with user input'),
            
            # Random Number Generation
            ('rand(', 'Weak Randomness', 'MEDIUM', 'rand() is not cryptographically secure'),
            ('srand(', 'Weak Randomness', 'MEDIUM', 'srand() seed should be unpredictable'),
            
            # Signal Handling
            ('signal(', 'Signal Handling', 'MEDIUM', 'signal() handlers should be async-safe'),
            ('sigaction(', 'Signal Handling', 'LOW', 'sigaction() is better than signal()'),
            
            # Time-of-Check-Time-of-Use (TOCTOU)
            ('access(', 'TOCTOU', 'MEDIUM', 'access() followed by file operation can cause race conditions'),
            ('stat(', 'TOCTOU', 'LOW', 'stat() followed by file operation may cause race conditions'),
            
            # Dangerous Functions
            ('mktemp(', 'Insecure Temp File', 'HIGH', 'mktemp() is insecure - use mkstemp()'),
            ('tmpnam(', 'Insecure Temp File', 'HIGH', 'tmpnam() is insecure - use mkstemp()'),
            ('tempnam(', 'Insecure Temp File', 'HIGH', 'tempnam() is insecure - use mkstemp()'),
            
            # Networking Security
            ('send(', 'Network Security', 'LOW', 'send() - ensure data validation'),
            ('recv(', 'Network Security', 'MEDIUM', 'recv() - validate received data length'),
            ('bind(', 'Network Security', 'LOW', 'bind() - ensure proper address validation'),
        ]
        
        for file_path in c_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    
                    for pattern, vuln_type, severity, description in security_patterns:
                        if pattern in line_content:
                            finding = self._create_finding(
                                file_path=file_path,
                                title=f"C {vuln_type}",
                                description=f"{description}. Found: {line_content[:100]}",
                                severity=severity,
                                lines=str(line_num),
                                snippet=line_content,
                                recommendation=self._get_recommendation(vuln_type)
                            )
                            findings.append(finding)
                            
            except Exception as e:
                continue  # Skip files that can't be read
        
        return findings
    
    def _parse_clang_output(self, output: str, file_path: str) -> List[Finding]:
        """Parse Clang Static Analyzer output"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'warning:' in line.lower() or 'error:' in line.lower():
                parts = line.split(':')
                if len(parts) >= 4:
                    try:
                        line_num = parts[1].strip()
                        message = ':'.join(parts[3:]).strip()
                        
                        severity = 'HIGH' if 'error' in line.lower() else 'MEDIUM'
                        
                        finding = self._create_finding(
                            file_path=file_path,
                            title="Clang Static Analysis Issue",
                            description=message,
                            severity=severity,
                            lines=line_num,
                            recommendation="Review and fix the reported issue"
                        )
                        findings.append(finding)
                    except (ValueError, IndexError):
                        continue
        
        return findings
    
    def _parse_splint_output(self, output: str, file_path: str) -> List[Finding]:
        """Parse Splint output"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if file_path in line and (':' in line):
                try:
                    # Parse Splint output format: file:line:column: message
                    parts = line.split(':')
                    if len(parts) >= 4:
                        line_num = parts[1].strip()
                        message = ':'.join(parts[3:]).strip()
                        
                        # Determine severity based on message content
                        severity = 'MEDIUM'
                        if 'buffer overflow' in message.lower():
                            severity = 'HIGH'
                        elif 'memory' in message.lower():
                            severity = 'MEDIUM'
                        elif 'null' in message.lower():
                            severity = 'MEDIUM'
                        
                        finding = self._create_finding(
                            file_path=file_path,
                            title="Splint Analysis Issue",
                            description=message,
                            severity=severity,
                            lines=line_num,
                            recommendation="Review Splint findings and fix issues"
                        )
                        findings.append(finding)
                except (ValueError, IndexError):
                    continue
        
        return findings
    
    def _get_recommendation(self, vuln_type: str) -> str:
        """Get specific recommendations for vulnerability types"""
        recommendations = {
            'Buffer Overflow': 'Use safe string functions like strncpy(), strncat(), snprintf()',
            'Memory Management': 'Check return values, avoid double-free, use static analysis tools',
            'Format String': 'Use constant format strings, validate user input',
            'Integer Overflow': 'Use safe conversion functions, check bounds before operations',
            'Command Injection': 'Use execv() family with validated arguments, avoid system()',
            'Weak Randomness': 'Use /dev/urandom or cryptographically secure PRNGs',
            'Signal Handling': 'Use only async-safe functions in signal handlers',
            'TOCTOU': 'Use file descriptors instead of filenames when possible',
            'Insecure Temp File': 'Use mkstemp() and proper file permissions',
            'Network Security': 'Validate all network input and use secure protocols'
        }
        return recommendations.get(vuln_type, 'Review and fix the security issue')
    
    def _create_finding(self, file_path: str, title: str, description: str, 
                       severity: str, lines: str, snippet: str = None, 
                       recommendation: str = None) -> Finding:
        """Create a standardized Finding object"""
        
        # Create CVSS score
        cvss_scores = {'CRITICAL': 9.8, 'HIGH': 7.5, 'MEDIUM': 5.5, 'LOW': 3.0}
        cvss_score = CVSSv4(
            score=cvss_scores.get(severity, 5.0),
            vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
        )
        
        # Create tool evidence
        evidence = ToolEvidence(
            tool_name=self.name,
            tool_version=self.version,
            confidence_score=90,
            raw_output=f"C security analysis detected: {title}",
            analysis_metadata={
                'analyzer': 'CAnalyzer',
                'pattern_based': snippet is None,
                'file_path': file_path
            }
        )
        
        return Finding(
            file=file_path,
            title=title,
            description=description,
            lines=lines,
            impact=f"C {severity.lower()} severity security issue that could affect application security",
            severity=severity.title(),
            cvss_v4=cvss_score,
            snippet=snippet or f"# C code analysis in {os.path.basename(file_path)}",
            recommendation=recommendation or "Review and address the C security issue",
            sample_fix="// Implement secure C practices and use safe alternatives",
            poc="// No proof-of-concept available for static analysis finding",
            owasp=[],
            cwe=[],
            references=[
                "https://cwe.mitre.org/data/definitions/119.html",  # Buffer Overflow
                "https://cwe.mitre.org/data/definitions/78.html",   # Command Injection
                "https://www.securecoding.cert.org/confluence/display/c/"  # CERT C Guidelines
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
        # This is a basic implementation that can be extended
        
        file_path = metadata.get('file_path', 'unknown.c')
        
        # Simple parsing - look for common patterns in C analysis output
        lines = raw_output.strip().split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'vulnerability', 'security']):
                # Extract basic information from the line
                title = line.strip()
                description = f"C security issue detected: {title}"
                
                finding = self._create_finding(
                    file_path=file_path,
                    title=title[:100],  # Truncate if too long
                    description=description,
                    severity='Medium',  # Default severity
                    lines=str(i + 1),
                    snippet=line.strip(),
                    recommendation=self._get_recommendation_for_type('General')
                )
                findings.append(finding)
        
        return findings


# Export the analyzer
__all__ = ['CAnalyzer']