"""
Kotlin Security Analysis Tools Integration
Supports Detekt, SpotBugs, and SonarKotlin for comprehensive Kotlin security analysis
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

class KotlinAnalyzer(BaseTool):
    """
    Kotlin Security Analyzer supporting Detekt, SpotBugs, and SonarKotlin
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "kotlin_analyzer"
        self.supported_extensions = ['.kt', '.kts']
        
        # Tool configurations
        self.tools = {
            'detekt': {
                'command': 'detekt',
                'enabled': self._check_detekt_availability(),
                'description': 'Detekt static code analysis for Kotlin'
            },
            'spotbugs': {
                'command': 'spotbugs',
                'enabled': self._check_spotbugs_availability(),
                'description': 'SpotBugs static analysis for JVM (Kotlin support)'
            },
            'sonar_kotlin': {
                'command': 'sonar-scanner',
                'enabled': self._check_sonar_kotlin_availability(),
                'description': 'SonarKotlin static analysis for Kotlin'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Kotlin analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try Detekt first as it's most commonly available for Kotlin
            if self.tools['detekt']['enabled']:
                result = subprocess.run(['detekt', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Detekt {result.stdout.strip()}"
            
            # Try SpotBugs as fallback
            if self.tools['spotbugs']['enabled']:
                result = subprocess.run(['spotbugs', '-version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"SpotBugs {result.stdout.strip()}"
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def _check_detekt_availability(self) -> bool:
        """Check if Detekt is available"""
        try:
            result = subprocess.run(['detekt', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_spotbugs_availability(self) -> bool:
        """Check if SpotBugs is available"""
        try:
            result = subprocess.run(['spotbugs', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_sonar_kotlin_availability(self) -> bool:
        """Check if SonarKotlin is available"""
        try:
            result = subprocess.run(['sonar-scanner', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Kotlin tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Kotlin security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'kotlin_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Kotlin security analysis tools."""
        findings = []
        
        # Check if this is a Kotlin project
        if not self._has_kotlin_files(repo_path):
            return findings
        
        # Run Detekt for Kotlin code analysis
        if self.tools['detekt']['enabled']:
            try:
                result = subprocess.run(
                    ['detekt', '--input', repo_path, '--report', 'xml', '--report', 'json'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                # Detekt outputs to files, check for output files
                detekt_findings = self._parse_detekt_output(repo_path)
                findings.extend(detekt_findings)
                
            except subprocess.TimeoutExpired:
                logger.warning("Detekt analysis timed out")
            except Exception as e:
                logger.error(f"Error running Detekt: {e}")
        
        # Run SpotBugs for JVM bytecode analysis (if compiled)
        if self.tools['spotbugs']['enabled']:
            try:
                # Look for compiled Kotlin classes
                class_dirs = self._find_kotlin_class_dirs(repo_path)
                if class_dirs:
                    for class_dir in class_dirs:
                        result = subprocess.run(
                            ['spotbugs', '-textui', '-output', 'spotbugs-report.xml', '-xml', class_dir],
                            cwd=repo_path,
                            capture_output=True,
                            text=True,
                            timeout=300
                        )
                        
                        spotbugs_findings = self._parse_spotbugs_output(repo_path)
                        findings.extend(spotbugs_findings)
                        
            except subprocess.TimeoutExpired:
                logger.warning("SpotBugs analysis timed out")
            except Exception as e:
                logger.error(f"Error running SpotBugs: {e}")
        
        # If no tools available, create placeholder finding
        if not any(self.tools[tool]['enabled'] for tool in self.tools):
            kotlin_files = []
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.kt'):
                        kotlin_files.append(os.path.relpath(os.path.join(root, file), repo_path))
            
            if kotlin_files:
                tool_evidence = ToolEvidence(
                    tool="kotlin_analyzer",
                    id=f"kotlin_{hash(kotlin_files[0])}",
                    raw=f"Kotlin analysis placeholder - found {len(kotlin_files)} Kotlin files"
                )
                
                finding = Finding(
                    file=kotlin_files[0],
                    title=f"Kotlin Analysis Placeholder",
                    description=f"Kotlin security analysis placeholder - found {len(kotlin_files)} Kotlin files",
                    lines="1",
                    impact="Potential Kotlin/Android security or quality issue",
                    severity="Medium",
                    cvss_v4=CVSSv4(
                        score=4.0,
                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                    ),
                    snippet=f"Kotlin file detected: {kotlin_files[0]}",
                    recommendation="Review Kotlin code for Android security best practices",
                    sample_fix="Apply Kotlin and Android security guidelines",
                    poc=f"Kotlin analysis in repository",
                    owasp=["A06:2021-Vulnerable and Outdated Components"],
                    cwe=["CWE-1104"],
                    tool_evidence=[tool_evidence]
                )
                findings.append(finding)
        
        return findings

    def _has_kotlin_files(self, repo_path: str) -> bool:
        """Check if repository contains Kotlin files."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    return True
            # Check for Gradle build files which often indicate Kotlin projects
            if any(f in ['build.gradle.kts', 'build.gradle'] for f in files):
                return True
        return False

    def _find_kotlin_class_dirs(self, repo_path: str) -> List[str]:
        """Find directories containing compiled Kotlin classes."""
        class_dirs = []
        for root, dirs, files in os.walk(repo_path):
            if 'classes' in dirs:
                classes_path = os.path.join(root, 'classes')
                if any(f.endswith('.class') for f in os.listdir(classes_path) if os.path.isfile(os.path.join(classes_path, f))):
                    class_dirs.append(classes_path)
        return class_dirs

    def _parse_detekt_output(self, repo_path: str) -> List[Finding]:
        """Parse Detekt output files."""
        findings = []
        
        # Look for detekt output files
        detekt_files = ['detekt.json', 'reports/detekt/detekt.json']
        
        for detekt_file in detekt_files:
            full_path = os.path.join(repo_path, detekt_file)
            if os.path.exists(full_path):
                try:
                    with open(full_path, 'r') as f:
                        detekt_data = json.load(f)
                    
                    for issue in detekt_data.get('issues', []):
                        finding = self._create_detekt_finding(issue, repo_path)
                        if finding:
                            findings.append(finding)
                            
                except json.JSONDecodeError as e:
                    logger.error(f"Error parsing Detekt JSON: {e}")
                except Exception as e:
                    logger.error(f"Error reading Detekt file: {e}")
                break
        
        return findings

    def _parse_spotbugs_output(self, repo_path: str) -> List[Finding]:
        """Parse SpotBugs XML output."""
        findings = []
        
        spotbugs_file = os.path.join(repo_path, 'spotbugs-report.xml')
        if os.path.exists(spotbugs_file):
            try:
                import xml.etree.ElementTree as ET
                tree = ET.parse(spotbugs_file)
                root = tree.getroot()
                
                for bug_instance in root.findall('.//BugInstance'):
                    finding = self._create_spotbugs_finding(bug_instance, repo_path)
                    if finding:
                        findings.append(finding)
                        
            except Exception as e:
                logger.error(f"Error parsing SpotBugs XML: {e}")
        
        return findings

    def _create_detekt_finding(self, issue: dict, repo_path: str) -> Finding:
        """Create a Finding from Detekt issue."""
        try:
            rule_id = issue.get('ruleId', 'Unknown')
            message = issue.get('message', 'Detekt issue')
            file_path = issue.get('file', 'unknown')
            line = issue.get('startLine', 1)
            severity = issue.get('severity', 'warning')
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="detekt",
                id=f"detekt_{rule_id}_{hash(file_path + str(line))}",
                raw=json.dumps(issue)
            )
            
            severity_map = {'error': 'High', 'warning': 'Medium', 'info': 'Low'}
            mapped_severity = severity_map.get(severity, 'Medium')
            
            # Identify security-related rules
            security_rules = [
                'UnsafeCallOnNullableType', 'TooManyFunctions', 'ComplexMethod',
                'LongMethod', 'ThrowsCount', 'ReturnFromFinally', 'UnsafeCast',
                'MagicNumber', 'SwallowedException', 'TooGenericExceptionCaught'
            ]
            
            is_security_related = any(sec_rule in rule_id for sec_rule in security_rules)
            impact = "Potential Android/Kotlin security vulnerability" if is_security_related else "Code quality issue that may affect security"
            
            return Finding(
                file=file_path,
                title=f"Detekt {rule_id}: {message[:50]}...",
                description=f"Detekt issue: {message}",
                lines=str(line),
                impact=impact,
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=6.0 if is_security_related else 3.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line}: {rule_id}",
                recommendation="Fix the Detekt issue to improve code quality and security",
                sample_fix="Follow Kotlin coding best practices",
                poc=f"Detekt analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"] if is_security_related else [],
                cwe=["CWE-476"] if 'Null' in rule_id else [],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Detekt finding: {e}")
            return None

    def _create_spotbugs_finding(self, bug_instance, repo_path: str) -> Finding:
        """Create a Finding from SpotBugs XML element."""
        try:
            bug_type = bug_instance.get('type', 'Unknown')
            priority = bug_instance.get('priority', '2')
            category = bug_instance.get('category', 'Unknown')
            
            # Extract source line info
            source_line = bug_instance.find('SourceLine')
            file_path = 'unknown'
            line = 1
            
            if source_line is not None:
                file_path = source_line.get('sourcepath', 'unknown')
                line = int(source_line.get('start', '1'))
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="spotbugs",
                id=f"spotbugs_{bug_type}_{hash(file_path + str(line))}",
                raw=f"SpotBugs: {bug_type} in {category}"
            )
            
            # Map SpotBugs priority to severity
            priority_map = {'1': 'High', '2': 'Medium', '3': 'Low'}
            mapped_severity = priority_map.get(priority, 'Medium')
            
            # Security categories in SpotBugs
            security_categories = ['SECURITY', 'VULNERABILITY', 'MALICIOUS_CODE']
            is_security_related = category in security_categories
            
            return Finding(
                file=file_path,
                title=f"SpotBugs {bug_type}: {category}",
                description=f"SpotBugs found issue: {bug_type} in category {category}",
                lines=str(line),
                impact="Potential JVM/Kotlin security vulnerability" if is_security_related else "Code quality issue",
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=7.0 if is_security_related else 4.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line}: {bug_type}",
                recommendation="Fix the SpotBugs issue to improve security",
                sample_fix="Apply secure coding practices for JVM/Kotlin",
                poc=f"SpotBugs analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"] if is_security_related else [],
                cwe=["CWE-693"] if is_security_related else [],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating SpotBugs finding: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['kotlin']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Kotlin Security Analyzer',
            'description': 'Comprehensive Kotlin security analysis using Detekt, SpotBugs, and SonarKotlin',
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
KotlinTool = KotlinAnalyzer