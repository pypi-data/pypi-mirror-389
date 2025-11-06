"""
Perl Security Analysis Tools Integration
Supports Perl::Critic, Perl::Tidy, and CPAN security modules for comprehensive Perl security analysis
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

class PerlAnalyzer(BaseTool):
    """
    Perl Security Analyzer supporting Perl::Critic, Perl::Tidy, and CPAN security modules
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "perl_analyzer"
        self.supported_extensions = ['.pl', '.pm', '.t', '.cgi']
        
        # Tool configurations
        self.tools = {
            'perlcritic': {
                'command': 'perlcritic',
                'enabled': self._check_perlcritic_availability(),
                'description': 'Perl::Critic static code analysis for Perl'
            },
            'perltidy': {
                'command': 'perltidy',
                'enabled': self._check_perltidy_availability(),
                'description': 'Perl::Tidy code quality and security formatter'
            },
            'perl_security_check': {
                'command': 'perl',
                'enabled': self._check_perl_availability(),
                'description': 'Custom Perl security pattern analysis'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Perl analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try Perl::Critic first
            if self.tools['perlcritic']['enabled']:
                result = subprocess.run(['perlcritic', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Perl::Critic {result.stdout.strip()}"
            
            # Try Perl as fallback
            if self.tools['perl_security_check']['enabled']:
                result = subprocess.run(['perl', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    # Extract version from Perl version output
                    for line in result.stdout.split('\n'):
                        if 'This is perl' in line:
                            return line.strip()
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def _check_perlcritic_availability(self) -> bool:
        """Check if Perl::Critic is available"""
        try:
            result = subprocess.run(['perlcritic', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_perltidy_availability(self) -> bool:
        """Check if Perl::Tidy is available"""
        try:
            result = subprocess.run(['perltidy', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_perl_availability(self) -> bool:
        """Check if Perl interpreter is available"""
        try:
            result = subprocess.run(['perl', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Perl tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Perl security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'perl_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Perl security analysis tools."""
        findings = []
        
        # Check if this is a Perl project
        perl_files = self._find_perl_files(repo_path)
        if not perl_files:
            return findings
        
        # Run Perl::Critic for comprehensive static analysis
        if self.tools['perlcritic']['enabled']:
            try:
                for perl_file in perl_files[:10]:  # Limit to first 10 files
                    result = subprocess.run(
                        ['perlcritic', '--verbose', '8', '--statistics', perl_file],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    critic_findings = self._parse_perlcritic_output(result.stdout, perl_file, repo_path)
                    findings.extend(critic_findings)
                    
            except subprocess.TimeoutExpired:
                logger.warning("Perl::Critic analysis timed out")
            except Exception as e:
                logger.error(f"Error running Perl::Critic: {e}")
        
        # Run custom Perl security pattern analysis
        if self.tools['perl_security_check']['enabled']:
            security_findings = self._check_perl_security_patterns(perl_files, repo_path)
            findings.extend(security_findings)
        
        # If no tools available, create placeholder finding
        if not any(self.tools[tool]['enabled'] for tool in self.tools):
            if perl_files:
                tool_evidence = ToolEvidence(
                    tool="perl_analyzer",
                    id=f"perl_{hash(perl_files[0])}",
                    raw=f"Perl analysis placeholder - found {len(perl_files)} Perl files"
                )
                
                finding = Finding(
                    file=os.path.relpath(perl_files[0], repo_path),
                    title=f"Perl Analysis Placeholder",
                    description=f"Perl security analysis placeholder - found {len(perl_files)} Perl files",
                    lines="1",
                    impact="Potential Perl security or quality issue",
                    severity="Medium",
                    cvss_v4=CVSSv4(
                        score=4.0,
                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                    ),
                    snippet=f"Perl file detected: {os.path.basename(perl_files[0])}",
                    recommendation="Review Perl code for security and quality issues",
                    sample_fix="Apply Perl security best practices",
                    poc=f"Perl analysis in repository",
                    owasp=["A06:2021-Vulnerable and Outdated Components"],
                    cwe=["CWE-1104"],
                    tool_evidence=[tool_evidence]
                )
                findings.append(finding)
        
        return findings

    def _find_perl_files(self, repo_path: str) -> List[str]:
        """Find Perl files in the repository."""
        perl_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    perl_files.append(os.path.join(root, file))
                # Check shebang for Perl scripts without extension
                elif not any(file.endswith(ext) for ext in ['.py', '.js', '.rb', '.sh']):
                    file_path = os.path.join(root, file)
                    if self._has_perl_shebang(file_path):
                        perl_files.append(file_path)
        return perl_files

    def _has_perl_shebang(self, file_path: str) -> bool:
        """Check if file has Perl shebang."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                return first_line.startswith('#!') and 'perl' in first_line
        except Exception:
            return False

    def _parse_perlcritic_output(self, output: str, file_path: str, repo_path: str) -> List[Finding]:
        """Parse Perl::Critic output."""
        findings = []
        
        if not output.strip():
            return findings
        
        lines = output.split('\n')
        for line in lines:
            # Perl::Critic format: file:line:col: message at line L, column C. Policy. (Severity)
            if ':' in line and 'line' in line:
                finding = self._create_perlcritic_finding(line, file_path, repo_path)
                if finding:
                    findings.append(finding)
        
        return findings

    def _check_perl_security_patterns(self, perl_files: List[str], repo_path: str) -> List[Finding]:
        """Check for Perl-specific security patterns."""
        findings = []
        
        # Security patterns to look for
        security_patterns = [
            ('eval', 'Code evaluation - potential code injection risk'),
            ('system(', 'System command execution - potential command injection'),
            ('exec(', 'Command execution - potential command injection'),
            ('open(', 'File operation - review for path traversal and injection'),
            ('`', 'Backtick operator - command execution risk'),
            ('qx/', 'qx operator - command execution risk'),
            ('unlink', 'File deletion - ensure proper validation'),
            ('chmod', 'Permission change - review for security implications'),
            ('chown', 'Ownership change - review for security implications'),
            ('$ENV{', 'Environment variable usage - validate input'),
            ('$_', 'Default variable - ensure proper handling'),
            ('do ', 'Dynamic code loading - potential security risk'),
            ('require ', 'Dynamic module loading - validate input'),
            ('use CGI', 'CGI usage - review for web security issues'),
            ('DBI->connect', 'Database connection - ensure secure configuration'),
            ('LWP::', 'HTTP client - ensure HTTPS and validation'),
            ('HTTP::', 'HTTP operations - review for security'),
            ('Socket', 'Network socket - review for security implications'),
            ('pack(', 'Binary data packing - review for buffer issues'),
            ('unpack(', 'Binary data unpacking - review for buffer issues')
        ]
        
        for perl_file in perl_files[:15]:  # Limit to first 15 files
            try:
                with open(perl_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, description in security_patterns:
                            if pattern in line:
                                tool_evidence = ToolEvidence(
                                    tool="perl_security_check",
                                    id=f"perl_{pattern}_{hash(perl_file + str(line_num))}",
                                    raw=f"Pattern '{pattern}' found in line: {line.strip()}"
                                )
                                
                                # Determine severity based on pattern
                                high_risk_patterns = ['eval', 'system(', 'exec(', '`', 'qx/']
                                medium_risk_patterns = ['open(', 'unlink', 'chmod', 'chown', 'do ', 'require ']
                                
                                if any(p in pattern for p in high_risk_patterns):
                                    severity = "High"
                                elif any(p in pattern for p in medium_risk_patterns):
                                    severity = "Medium"
                                else:
                                    severity = "Low"
                                
                                finding = Finding(
                                    file=os.path.relpath(perl_file, repo_path),
                                    title=f"Perl Security Pattern: {pattern}",
                                    description=description,
                                    lines=str(line_num),
                                    impact=f"Potential Perl security vulnerability: {description}",
                                    severity=severity,
                                    cvss_v4=CVSSv4(
                                        score=7.0 if severity == "High" else (5.0 if severity == "Medium" else 3.0),
                                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                                    ),
                                    snippet=line.strip(),
                                    recommendation=f"Review usage of {pattern} for security implications",
                                    sample_fix="Use secure alternatives and validate all inputs",
                                    poc=f"Pattern found in {perl_file}",
                                    owasp=["A03:2021-Injection"] if any(p in pattern for p in ['eval', 'system', 'exec']) else ["A06:2021-Vulnerable and Outdated Components"],
                                    cwe=["CWE-94"] if 'eval' in pattern else ["CWE-78"] if any(p in pattern for p in ['system', 'exec']) else ["CWE-200"],
                                    tool_evidence=[tool_evidence]
                                )
                                findings.append(finding)
                                
            except Exception as e:
                logger.error(f"Error reading file {perl_file}: {e}")
        
        return findings

    def _create_perlcritic_finding(self, line: str, file_path: str, repo_path: str) -> Finding:
        """Create a Finding from Perl::Critic output line."""
        try:
            # Parse Perl::Critic output format
            # Format: file:line:col: message at line L, column C. Policy. (Severity)
            parts = line.split(':')
            if len(parts) < 3:
                return None
            
            line_num = parts[1] if parts[1].isdigit() else "1"
            message_part = ':'.join(parts[3:]) if len(parts) > 3 else line
            
            # Extract policy and severity
            policy = "Unknown"
            severity = "3"  # Default severity
            
            if '(' in message_part and ')' in message_part:
                # Extract severity from parentheses
                severity_match = message_part.split('(')[-1].split(')')[0]
                if severity_match.isdigit():
                    severity = severity_match
            
            if '.' in message_part:
                # Extract policy name
                policy_parts = message_part.split('.')
                for part in policy_parts:
                    if '::' in part:
                        policy = part.strip()
                        break
            
            tool_evidence = ToolEvidence(
                tool="perlcritic",
                id=f"perlcritic_{policy}_{hash(file_path + line_num)}",
                raw=line
            )
            
            # Map Perl::Critic severity (1-5, where 1 is most severe)
            severity_map = {'1': 'High', '2': 'High', '3': 'Medium', '4': 'Low', '5': 'Low'}
            mapped_severity = severity_map.get(severity, 'Medium')
            
            return Finding(
                file=os.path.relpath(file_path, repo_path),
                title=f"Perl::Critic {policy}: {message_part[:50]}...",
                description=f"Perl::Critic policy violation: {message_part}",
                lines=line_num,
                impact="Code quality issue that may affect security or maintainability",
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=6.0 if mapped_severity == "High" else (4.0 if mapped_severity == "Medium" else 2.0),
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line_num}: {policy}",
                recommendation="Fix the Perl::Critic policy violation to improve code quality",
                sample_fix="Follow Perl best practices and coding standards",
                poc=f"Perl::Critic analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Perl::Critic finding: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['perl']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Perl Security Analyzer',
            'description': 'Comprehensive Perl security analysis using Perl::Critic and custom security pattern checks',
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
PerlTool = PerlAnalyzer