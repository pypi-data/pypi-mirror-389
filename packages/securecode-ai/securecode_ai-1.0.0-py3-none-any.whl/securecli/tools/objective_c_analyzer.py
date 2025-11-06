"""
Objective-C Security Analysis Tools Integration
Supports Clang Static Analyzer, OCLint, and iOS-specific security checks
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

class ObjectiveCAnalyzer(BaseTool):
    """
    Objective-C Security Analyzer supporting Clang Static Analyzer, OCLint, and iOS security checks
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "objective_c_analyzer"
        self.supported_extensions = ['.m', '.mm', '.h']
        
        # Tool configurations
        self.tools = {
            'clang_static_analyzer': {
                'command': 'clang',
                'enabled': self._check_clang_availability(),
                'description': 'Clang Static Analyzer for Objective-C'
            },
            'oclint': {
                'command': 'oclint',
                'enabled': self._check_oclint_availability(),
                'description': 'OCLint static analysis for Objective-C'
            },
            'xcode_analyzer': {
                'command': 'xcodebuild',
                'enabled': self._check_xcode_availability(),
                'description': 'Xcode integrated static analyzer'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Objective-C analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try Clang first as it's most commonly available
            if self.tools['clang_static_analyzer']['enabled']:
                result = subprocess.run(['clang', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Clang {result.stdout.split()[2]}"
            
            # Try OCLint as fallback
            if self.tools['oclint']['enabled']:
                result = subprocess.run(['oclint', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"OCLint {result.stdout.strip()}"
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def _check_clang_availability(self) -> bool:
        """Check if Clang Static Analyzer is available"""
        try:
            result = subprocess.run(['clang', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_oclint_availability(self) -> bool:
        """Check if OCLint is available"""
        try:
            result = subprocess.run(['oclint', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_xcode_availability(self) -> bool:
        """Check if Xcode build tools are available"""
        try:
            result = subprocess.run(['xcodebuild', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Objective-C tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Objective-C security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'objective_c_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Objective-C security analysis tools."""
        findings = []
        
        # Check if this is an Objective-C project
        objc_files = self._find_objc_files(repo_path)
        if not objc_files:
            return findings
        
        # Run Clang Static Analyzer
        if self.tools['clang_static_analyzer']['enabled']:
            try:
                for objc_file in objc_files[:10]:  # Limit to first 10 files to avoid timeout
                    result = subprocess.run(
                        ['clang', '--analyze', '-Xanalyzer', '-analyzer-output=plist-multi-file', objc_file],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    # Parse Clang analyzer output
                    clang_findings = self._parse_clang_output(result.stderr, objc_file, repo_path)
                    findings.extend(clang_findings)
                    
            except subprocess.TimeoutExpired:
                logger.warning("Clang Static Analyzer timed out")
            except Exception as e:
                logger.error(f"Error running Clang Static Analyzer: {e}")
        
        # Run OCLint for additional checks
        if self.tools['oclint']['enabled']:
            try:
                # OCLint requires compilation database or manual file specification
                for objc_file in objc_files[:5]:  # Limit files
                    result = subprocess.run(
                        ['oclint', objc_file, '--', '-I.'],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=120
                    )
                    
                    oclint_findings = self._parse_oclint_output(result.stdout, objc_file, repo_path)
                    findings.extend(oclint_findings)
                    
            except subprocess.TimeoutExpired:
                logger.warning("OCLint analysis timed out")
            except Exception as e:
                logger.error(f"Error running OCLint: {e}")
        
        # Run iOS-specific security checks
        ios_findings = self._check_ios_security_patterns(objc_files, repo_path)
        findings.extend(ios_findings)
        
        # If no tools available, create placeholder finding
        if not any(self.tools[tool]['enabled'] for tool in self.tools):
            if objc_files:
                tool_evidence = ToolEvidence(
                    tool="objective_c_analyzer",
                    id=f"objc_{hash(objc_files[0])}",
                    raw=f"Objective-C analysis placeholder - found {len(objc_files)} Objective-C files"
                )
                
                finding = Finding(
                    file=os.path.relpath(objc_files[0], repo_path),
                    title=f"Objective-C Analysis Placeholder",
                    description=f"Objective-C security analysis placeholder - found {len(objc_files)} Objective-C files",
                    lines="1",
                    impact="Potential iOS/macOS security or memory safety issue",
                    severity="Medium",
                    cvss_v4=CVSSv4(
                        score=5.0,
                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                    ),
                    snippet=f"Objective-C file detected: {os.path.basename(objc_files[0])}",
                    recommendation="Review Objective-C code for iOS/macOS security best practices",
                    sample_fix="Apply memory safety and iOS security guidelines",
                    poc=f"Objective-C analysis in repository",
                    owasp=["A06:2021-Vulnerable and Outdated Components"],
                    cwe=["CWE-119"],
                    tool_evidence=[tool_evidence]
                )
                findings.append(finding)
        
        return findings

    def _find_objc_files(self, repo_path: str) -> List[str]:
        """Find Objective-C files in the repository."""
        objc_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    objc_files.append(os.path.join(root, file))
        return objc_files

    def _parse_clang_output(self, output: str, file_path: str, repo_path: str) -> List[Finding]:
        """Parse Clang Static Analyzer output."""
        findings = []
        
        if not output.strip():
            return findings
        
        # Simple parsing of Clang warnings/errors
        lines = output.split('\n')
        for line in lines:
            if 'warning:' in line or 'error:' in line:
                finding = self._create_clang_finding(line, file_path, repo_path)
                if finding:
                    findings.append(finding)
        
        return findings

    def _parse_oclint_output(self, output: str, file_path: str, repo_path: str) -> List[Finding]:
        """Parse OCLint output."""
        findings = []
        
        if not output.strip():
            return findings
        
        # Parse OCLint output format
        lines = output.split('\n')
        for line in lines:
            if ':' in line and ('P1' in line or 'P2' in line or 'P3' in line):
                finding = self._create_oclint_finding(line, file_path, repo_path)
                if finding:
                    findings.append(finding)
        
        return findings

    def _check_ios_security_patterns(self, objc_files: List[str], repo_path: str) -> List[Finding]:
        """Check for iOS-specific security patterns in Objective-C code."""
        findings = []
        
        # Security patterns to look for
        security_patterns = [
            ('NSLog', 'Potential information disclosure through logging'),
            ('malloc', 'Manual memory management - potential memory issues'),
            ('strcpy', 'Unsafe string function - buffer overflow risk'),
            ('sprintf', 'Unsafe string formatting - buffer overflow risk'),
            ('gets', 'Dangerous input function - buffer overflow risk'),
            ('system(', 'Command injection risk'),
            ('exec', 'Command execution - potential security risk'),
            ('NSUserDefaults', 'Potential sensitive data storage in user defaults'),
            ('Keychain', 'Keychain usage - ensure proper implementation'),
            ('UDID', 'Deprecated device identifier usage'),
            ('NSHTTPCookieAcceptPolicy', 'Cookie policy - ensure secure configuration'),
            ('allowsAnyHTTPSCertificate', 'Certificate validation bypass'),
            ('NSURLRequest', 'Network request - ensure HTTPS and validation')
        ]
        
        for objc_file in objc_files[:10]:  # Limit to first 10 files
            try:
                with open(objc_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, description in security_patterns:
                            if pattern in line:
                                tool_evidence = ToolEvidence(
                                    tool="ios_security_check",
                                    id=f"ios_{pattern}_{hash(objc_file + str(line_num))}",
                                    raw=f"Pattern '{pattern}' found in line: {line.strip()}"
                                )
                                
                                # Determine severity based on pattern
                                high_risk_patterns = ['strcpy', 'sprintf', 'gets', 'system(', 'exec', 'allowsAnyHTTPSCertificate']
                                severity = "High" if pattern in high_risk_patterns else "Medium"
                                
                                finding = Finding(
                                    file=os.path.relpath(objc_file, repo_path),
                                    title=f"iOS Security Pattern: {pattern}",
                                    description=description,
                                    lines=str(line_num),
                                    impact=f"Potential iOS security vulnerability: {description}",
                                    severity=severity,
                                    cvss_v4=CVSSv4(
                                        score=7.0 if severity == "High" else 5.0,
                                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                                    ),
                                    snippet=line.strip(),
                                    recommendation=f"Review usage of {pattern} for security implications",
                                    sample_fix="Use secure alternatives and follow iOS security guidelines",
                                    poc=f"Pattern found in {objc_file}",
                                    owasp=["A03:2021-Injection"] if 'system' in pattern or 'exec' in pattern else ["A06:2021-Vulnerable and Outdated Components"],
                                    cwe=["CWE-119"] if any(p in pattern for p in ['strcpy', 'sprintf', 'gets']) else ["CWE-200"],
                                    tool_evidence=[tool_evidence]
                                )
                                findings.append(finding)
                                
            except Exception as e:
                logger.error(f"Error reading file {objc_file}: {e}")
        
        return findings

    def _create_clang_finding(self, line: str, file_path: str, repo_path: str) -> Finding:
        """Create a Finding from Clang analyzer output line."""
        try:
            # Parse Clang output format: file:line:column: warning/error: message
            parts = line.split(':')
            if len(parts) < 4:
                return None
            
            line_num = parts[1] if parts[1].isdigit() else "1"
            message_type = 'error' if 'error:' in line else 'warning'
            message = ':'.join(parts[3:]).strip()
            
            tool_evidence = ToolEvidence(
                tool="clang_static_analyzer",
                id=f"clang_{hash(file_path + line_num)}",
                raw=line
            )
            
            severity = "High" if message_type == 'error' else "Medium"
            
            return Finding(
                file=os.path.relpath(file_path, repo_path),
                title=f"Clang {message_type.title()}: {message[:50]}...",
                description=f"Clang Static Analyzer {message_type}: {message}",
                lines=line_num,
                impact=f"Potential Objective-C {message_type} affecting security or stability",
                severity=severity,
                cvss_v4=CVSSv4(
                    score=6.0 if severity == "High" else 4.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line_num}: {message_type}",
                recommendation="Fix the Clang analyzer issue to improve code quality and security",
                sample_fix="Follow Objective-C and iOS security best practices",
                poc=f"Clang analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-119"] if 'memory' in message.lower() else ["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Clang finding: {e}")
            return None

    def _create_oclint_finding(self, line: str, file_path: str, repo_path: str) -> Finding:
        """Create a Finding from OCLint output line."""
        try:
            # Parse OCLint output format
            parts = line.split(':')
            if len(parts) < 3:
                return None
            
            line_num = "1"
            message = line
            priority = "P2"  # Default priority
            
            # Extract line number and priority if available
            for part in parts:
                if part.strip().isdigit():
                    line_num = part.strip()
                if part.strip() in ['P1', 'P2', 'P3']:
                    priority = part.strip()
            
            tool_evidence = ToolEvidence(
                tool="oclint",
                id=f"oclint_{hash(file_path + line_num)}",
                raw=line
            )
            
            # Map OCLint priority to severity
            priority_map = {'P1': 'High', 'P2': 'Medium', 'P3': 'Low'}
            severity = priority_map.get(priority, 'Medium')
            
            return Finding(
                file=os.path.relpath(file_path, repo_path),
                title=f"OCLint {priority}: {message[:50]}...",
                description=f"OCLint issue: {message}",
                lines=line_num,
                impact="Code quality issue that may affect security",
                severity=severity,
                cvss_v4=CVSSv4(
                    score=5.0 if severity == "High" else 3.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line_num}: {priority}",
                recommendation="Fix the OCLint issue to improve code quality",
                sample_fix="Follow OCLint recommendations and Objective-C best practices",
                poc=f"OCLint analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating OCLint finding: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['objective-c']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Objective-C Security Analyzer',
            'description': 'Comprehensive Objective-C security analysis using Clang Static Analyzer, OCLint, and iOS security checks',
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
ObjectiveCTool = ObjectiveCAnalyzer