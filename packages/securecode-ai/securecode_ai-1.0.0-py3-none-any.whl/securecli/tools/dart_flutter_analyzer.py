"""
Dart/Flutter Security Analysis Tools Integration
Supports Dart Analyzer, Flutter Analyzer, and Flutter-specific security checks
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

class DartFlutterAnalyzer(BaseTool):
    """
    Dart/Flutter Security Analyzer supporting Dart Analyzer, Flutter tools, and mobile security checks
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "dart_flutter_analyzer"
        self.supported_extensions = ['.dart']
        
        # Tool configurations
        self.tools = {
            'dart_analyzer': {
                'command': 'dart',
                'enabled': self._check_dart_availability(),
                'description': 'Dart static analyzer'
            },
            'flutter_analyzer': {
                'command': 'flutter',
                'enabled': self._check_flutter_availability(),
                'description': 'Flutter framework analyzer'
            },
            'dartanalyzer': {
                'command': 'dartanalyzer',
                'enabled': self._check_dartanalyzer_availability(),
                'description': 'Legacy Dart analyzer (dartanalyzer)'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Dart/Flutter analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try Dart first
            if self.tools['dart_analyzer']['enabled']:
                result = subprocess.run(['dart', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Dart {result.stderr.strip()}"  # Dart outputs version to stderr
            
            # Try Flutter as fallback
            if self.tools['flutter_analyzer']['enabled']:
                result = subprocess.run(['flutter', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Flutter {result.stdout.split()[1]}"
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def _check_dart_availability(self) -> bool:
        """Check if Dart SDK is available"""
        try:
            result = subprocess.run(['dart', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_flutter_availability(self) -> bool:
        """Check if Flutter SDK is available"""
        try:
            result = subprocess.run(['flutter', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_dartanalyzer_availability(self) -> bool:
        """Check if legacy dartanalyzer is available"""
        try:
            result = subprocess.run(['dartanalyzer', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Dart/Flutter tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Dart/Flutter security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'dart_flutter_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Dart/Flutter security analysis tools."""
        findings = []
        
        # Check if this is a Dart/Flutter project
        dart_files = self._find_dart_files(repo_path)
        if not dart_files:
            return findings
        
        is_flutter_project = self._is_flutter_project(repo_path)
        
        # Run Dart analyzer
        if self.tools['dart_analyzer']['enabled']:
            try:
                result = subprocess.run(
                    ['dart', 'analyze', '--format=json'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                dart_findings = self._parse_dart_analyzer_output(result.stdout, repo_path)
                findings.extend(dart_findings)
                
            except subprocess.TimeoutExpired:
                logger.warning("Dart analyzer timed out")
            except Exception as e:
                logger.error(f"Error running Dart analyzer: {e}")
        
        # Run Flutter-specific analysis if it's a Flutter project
        if is_flutter_project and self.tools['flutter_analyzer']['enabled']:
            try:
                result = subprocess.run(
                    ['flutter', 'analyze'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                flutter_findings = self._parse_flutter_analyzer_output(result.stdout, repo_path)
                findings.extend(flutter_findings)
                
            except subprocess.TimeoutExpired:
                logger.warning("Flutter analyzer timed out")
            except Exception as e:
                logger.error(f"Error running Flutter analyzer: {e}")
        
        # Run Dart/Flutter security pattern checks
        security_findings = self._check_dart_security_patterns(dart_files, repo_path, is_flutter_project)
        findings.extend(security_findings)
        
        # If no tools available, create placeholder finding
        if not any(self.tools[tool]['enabled'] for tool in self.tools):
            if dart_files:
                tool_evidence = ToolEvidence(
                    tool="dart_flutter_analyzer",
                    id=f"dart_{hash(dart_files[0])}",
                    raw=f"Dart/Flutter analysis placeholder - found {len(dart_files)} Dart files"
                )
                
                project_type = "Flutter" if is_flutter_project else "Dart"
                
                finding = Finding(
                    file=os.path.relpath(dart_files[0], repo_path),
                    title=f"{project_type} Analysis Placeholder",
                    description=f"{project_type} security analysis placeholder - found {len(dart_files)} Dart files",
                    lines="1",
                    impact=f"Potential {project_type} security or quality issue",
                    severity="Medium",
                    cvss_v4=CVSSv4(
                        score=4.0,
                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                    ),
                    snippet=f"{project_type} file detected: {os.path.basename(dart_files[0])}",
                    recommendation=f"Review {project_type} code for mobile security best practices",
                    sample_fix=f"Apply {project_type} and mobile security guidelines",
                    poc=f"{project_type} analysis in repository",
                    owasp=["A06:2021-Vulnerable and Outdated Components"],
                    cwe=["CWE-1104"],
                    tool_evidence=[tool_evidence]
                )
                findings.append(finding)
        
        return findings

    def _find_dart_files(self, repo_path: str) -> List[str]:
        """Find Dart files in the repository."""
        dart_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.dart'):
                    dart_files.append(os.path.join(root, file))
        return dart_files

    def _is_flutter_project(self, repo_path: str) -> bool:
        """Check if this is a Flutter project."""
        # Check for pubspec.yaml with Flutter dependencies
        pubspec_path = os.path.join(repo_path, 'pubspec.yaml')
        if os.path.exists(pubspec_path):
            try:
                with open(pubspec_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                    if 'flutter:' in content or 'flutter_test:' in content:
                        return True
            except Exception:
                pass
        
        # Check for flutter directory structure
        flutter_dirs = ['android', 'ios', 'lib', 'test']
        flutter_dir_count = sum(1 for d in flutter_dirs if os.path.exists(os.path.join(repo_path, d)))
        return flutter_dir_count >= 2

    def _parse_dart_analyzer_output(self, output: str, repo_path: str) -> List[Finding]:
        """Parse Dart analyzer JSON output."""
        findings = []
        
        if not output.strip():
            return findings
        
        try:
            # Try to parse as JSON
            data = json.loads(output)
            
            if isinstance(data, dict) and 'diagnostics' in data:
                for diagnostic in data['diagnostics']:
                    finding = self._create_dart_finding(diagnostic, repo_path)
                    if finding:
                        findings.append(finding)
            elif isinstance(data, list):
                for diagnostic in data:
                    finding = self._create_dart_finding(diagnostic, repo_path)
                    if finding:
                        findings.append(finding)
        except json.JSONDecodeError:
            # If not JSON, try to parse as text output
            lines = output.split('\n')
            for line in lines:
                if ' • ' in line:  # Dart analyzer format
                    finding = self._create_dart_text_finding(line, repo_path)
                    if finding:
                        findings.append(finding)
        except Exception as e:
            logger.error(f"Error parsing Dart analyzer output: {e}")
        
        return findings

    def _parse_flutter_analyzer_output(self, output: str, repo_path: str) -> List[Finding]:
        """Parse Flutter analyzer output."""
        findings = []
        
        if not output.strip():
            return findings
        
        lines = output.split('\n')
        for line in lines:
            if ' • ' in line or 'warning:' in line or 'error:' in line:
                finding = self._create_flutter_finding(line, repo_path)
                if finding:
                    findings.append(finding)
        
        return findings

    def _check_dart_security_patterns(self, dart_files: List[str], repo_path: str, is_flutter: bool) -> List[Finding]:
        """Check for Dart/Flutter-specific security patterns."""
        findings = []
        
        # Security patterns to look for
        dart_patterns = [
            ('print(', 'Potential information disclosure through console output'),
            ('HttpClient', 'HTTP client usage - ensure HTTPS and certificate validation'),
            ('dart:io', 'File system access - review for security implications'),
            ('Platform.', 'Platform-specific code - review for security implications'),
            ('Random()', 'Random number generation - ensure cryptographically secure for security contexts'),
            ('eval(', 'Code evaluation - potential code injection risk'),
            ('new ProcessResult', 'Process execution - potential command injection risk'),
            ('Process.run', 'Process execution - potential command injection risk'),
            ('dart:html', 'Web API usage - review for XSS and other web vulnerabilities'),
            ('allowInterop', 'JavaScript interop - potential security boundary crossing')
        ]
        
        flutter_patterns = [
            ('WebView', 'WebView usage - review for web security vulnerabilities'),
            ('url_launcher', 'URL launching - validate URLs to prevent malicious redirects'),
            ('shared_preferences', 'Local storage - avoid storing sensitive data'),
            ('sqflite', 'Database usage - ensure proper data protection'),
            ('http.get', 'HTTP request - ensure HTTPS and input validation'),
            ('http.post', 'HTTP request - ensure HTTPS and input validation'),
            ('FirebaseAuth', 'Firebase authentication - review implementation'),
            ('GoogleSignIn', 'Google Sign-In - review implementation for security'),
            ('Navigator.pushNamed', 'Navigation - validate route parameters'),
            ('FutureBuilder', 'Async operations - handle errors securely'),
            ('StreamBuilder', 'Stream operations - handle errors securely'),
            ('MethodChannel', 'Platform channel - validate data crossing boundaries'),
            ('PlatformView', 'Platform view - review for security implications'),
            ('rootBundle', 'Asset access - ensure secure asset handling')
        ]
        
        patterns = dart_patterns + (flutter_patterns if is_flutter else [])
        
        for dart_file in dart_files[:15]:  # Limit to first 15 files
            try:
                with open(dart_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, description in patterns:
                            if pattern in line:
                                tool_evidence = ToolEvidence(
                                    tool="dart_security_check",
                                    id=f"dart_{pattern}_{hash(dart_file + str(line_num))}",
                                    raw=f"Pattern '{pattern}' found in line: {line.strip()}"
                                )
                                
                                # Determine severity based on pattern
                                high_risk_patterns = ['eval(', 'Process.run', 'ProcessResult']
                                medium_risk_patterns = ['WebView', 'http.', 'HttpClient', 'url_launcher']
                                
                                if any(p in pattern for p in high_risk_patterns):
                                    severity = "High"
                                elif any(p in pattern for p in medium_risk_patterns):
                                    severity = "Medium"
                                else:
                                    severity = "Low"
                                
                                project_type = "Flutter" if is_flutter else "Dart"
                                
                                finding = Finding(
                                    file=os.path.relpath(dart_file, repo_path),
                                    title=f"{project_type} Security Pattern: {pattern}",
                                    description=description,
                                    lines=str(line_num),
                                    impact=f"Potential {project_type} security vulnerability: {description}",
                                    severity=severity,
                                    cvss_v4=CVSSv4(
                                        score=7.0 if severity == "High" else (5.0 if severity == "Medium" else 3.0),
                                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                                    ),
                                    snippet=line.strip(),
                                    recommendation=f"Review usage of {pattern} for security implications",
                                    sample_fix=f"Use secure alternatives and follow {project_type} security guidelines",
                                    poc=f"Pattern found in {dart_file}",
                                    owasp=["A03:2021-Injection"] if 'eval' in pattern or 'Process' in pattern else ["A06:2021-Vulnerable and Outdated Components"],
                                    cwe=["CWE-94"] if 'eval' in pattern else ["CWE-200"],
                                    tool_evidence=[tool_evidence]
                                )
                                findings.append(finding)
                                
            except Exception as e:
                logger.error(f"Error reading file {dart_file}: {e}")
        
        return findings

    def _create_dart_finding(self, diagnostic: dict, repo_path: str) -> Finding:
        """Create a Finding from Dart analyzer diagnostic."""
        try:
            file_path = diagnostic.get('file', 'unknown')
            line = diagnostic.get('line', 1)
            message = diagnostic.get('message', 'Dart analyzer issue')
            severity = diagnostic.get('severity', 'warning')
            rule_id = diagnostic.get('code', 'dart_issue')
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="dart_analyzer",
                id=f"dart_{rule_id}_{hash(file_path + str(line))}",
                raw=json.dumps(diagnostic)
            )
            
            severity_map = {'error': 'High', 'warning': 'Medium', 'info': 'Low'}
            mapped_severity = severity_map.get(severity, 'Medium')
            
            return Finding(
                file=file_path,
                title=f"Dart Analyzer {rule_id}: {message[:50]}...",
                description=f"Dart analyzer issue: {message}",
                lines=str(line),
                impact="Code quality issue that may affect security",
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=5.0 if mapped_severity == "High" else 3.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line}: {rule_id}",
                recommendation="Fix the Dart analyzer issue to improve code quality",
                sample_fix="Follow Dart coding best practices",
                poc=f"Dart analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Dart finding: {e}")
            return None

    def _create_dart_text_finding(self, line: str, repo_path: str) -> Finding:
        """Create a Finding from Dart analyzer text output."""
        try:
            # Parse format: "level • description • file:line:column"
            parts = line.split(' • ')
            if len(parts) < 2:
                return None
            
            level = parts[0].strip()
            description = parts[1].strip()
            location = parts[2] if len(parts) > 2 else "unknown:1:1"
            
            # Extract file and line
            loc_parts = location.split(':')
            file_path = loc_parts[0] if loc_parts else 'unknown'
            line_num = loc_parts[1] if len(loc_parts) > 1 and loc_parts[1].isdigit() else "1"
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="dart_analyzer",
                id=f"dart_text_{hash(file_path + line_num)}",
                raw=line
            )
            
            severity_map = {'error': 'High', 'warning': 'Medium', 'info': 'Low', 'hint': 'Low'}
            severity = severity_map.get(level.lower(), 'Medium')
            
            return Finding(
                file=file_path,
                title=f"Dart Analyzer: {description[:50]}...",
                description=f"Dart analyzer {level}: {description}",
                lines=line_num,
                impact="Code quality issue that may affect security",
                severity=severity,
                cvss_v4=CVSSv4(
                    score=5.0 if severity == "High" else 3.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line_num}: {level}",
                recommendation="Fix the Dart analyzer issue to improve code quality",
                sample_fix="Follow Dart coding best practices",
                poc=f"Dart analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Dart text finding: {e}")
            return None

    def _create_flutter_finding(self, line: str, repo_path: str) -> Finding:
        """Create a Finding from Flutter analyzer output."""
        try:
            # Similar to Dart text parsing but Flutter-specific
            if ' • ' in line:
                parts = line.split(' • ')
                level = parts[0].strip()
                description = parts[1].strip() if len(parts) > 1 else line
            else:
                level = 'info'
                description = line.strip()
            
            tool_evidence = ToolEvidence(
                tool="flutter_analyzer",
                id=f"flutter_{hash(line)}",
                raw=line
            )
            
            severity_map = {'error': 'High', 'warning': 'Medium', 'info': 'Low'}
            severity = severity_map.get(level.lower(), 'Medium')
            
            return Finding(
                file="unknown",
                title=f"Flutter Analyzer: {description[:50]}...",
                description=f"Flutter analyzer {level}: {description}",
                lines="1",
                impact="Flutter-specific issue that may affect app security",
                severity=severity,
                cvss_v4=CVSSv4(
                    score=5.0 if severity == "High" else 3.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=line.strip(),
                recommendation="Fix the Flutter analyzer issue to improve app quality",
                sample_fix="Follow Flutter and mobile security best practices",
                poc=f"Flutter analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Flutter finding: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['dart', 'flutter']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Dart/Flutter Security Analyzer',
            'description': 'Comprehensive Dart and Flutter security analysis with mobile-specific checks',
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
DartFlutterTool = DartFlutterAnalyzer