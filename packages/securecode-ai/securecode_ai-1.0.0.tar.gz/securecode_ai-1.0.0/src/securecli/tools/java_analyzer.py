"""
Java Security Analysis Tools Integration
Supports SpotBugs, PMD, and Find Security Bugs for comprehensive Java security analysis
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import xml.etree.ElementTree as ET

from ..schemas.findings import Finding, ToolEvidence, CVSSv4
from .base import BaseTool

logger = logging.getLogger(__name__)

class JavaAnalyzer(BaseTool):
    """
    Java Security Analyzer supporting SpotBugs, PMD, and Find Security Bugs
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "java_analyzer"
        self.supported_extensions = ['.java', '.jsp', '.properties', '.xml']
        
        # Tool configurations
        self.tools = {
            'spotbugs': {
                'command': 'spotbugs',
                'enabled': self._check_spotbugs_availability(),
                'description': 'SpotBugs static analysis for Java bytecode'
            },
            'pmd': {
                'command': 'pmd',
                'enabled': self._check_pmd_availability(),
                'description': 'PMD source code analyzer for Java'
            },
            'findsecbugs': {
                'command': 'spotbugs',  # Find Security Bugs is a SpotBugs plugin
                'enabled': self._check_findsecbugs_availability(),
                'description': 'Find Security Bugs plugin for SpotBugs'
            }
        }
    
    def _check_spotbugs_availability(self) -> bool:
        """Check if SpotBugs is available"""
        try:
            result = subprocess.run(['spotbugs', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            # Check for SpotBugs in common installation locations
            spotbugs_paths = [
                '/opt/spotbugs/lib/spotbugs.jar',
                '/usr/share/spotbugs/lib/spotbugs.jar',
                '~/spotbugs-*/lib/spotbugs.jar'
            ]
            
            for jar_path in spotbugs_paths:
                try:
                    expanded_path = os.path.expanduser(jar_path)
                    if os.path.exists(expanded_path):
                        result = subprocess.run(['java', '-jar', expanded_path, '-version'], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            return True
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            return False
    
    def _check_pmd_availability(self) -> bool:
        """Check if PMD is available"""
        try:
            result = subprocess.run(['pmd', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            # Check PMD in installation directories
            pmd_paths = [
                '/opt/pmd/bin/run.sh',
                '/usr/local/pmd/bin/run.sh',
                '~/pmd-*/bin/run.sh'
            ]
            
            for pmd_path in pmd_paths:
                try:
                    expanded_path = os.path.expanduser(pmd_path)
                    if os.path.exists(expanded_path):
                        result = subprocess.run([expanded_path, 'pmd', '--version'], 
                                              capture_output=True, text=True, timeout=10)
                        if result.returncode == 0:
                            return True
                except (subprocess.SubprocessError, FileNotFoundError):
                    continue
            return False
    
    def _check_findsecbugs_availability(self) -> bool:
        """Check if Find Security Bugs plugin is available"""
        # Find Security Bugs is a SpotBugs plugin, so we check if SpotBugs is available
        # and if the plugin is in the classpath or configured
        if not self._check_spotbugs_availability():
            return False
        
        # Check if Find Security Bugs plugin JAR is available
        common_paths = [
            '/usr/share/java/findsecbugs-plugin.jar',
            '/opt/findsecbugs/findsecbugs-plugin.jar',
            './findsecbugs-plugin.jar',
            '~/.spotbugs/findsecbugs-plugin.jar'
        ]
        
        for path in common_paths:
            if os.path.exists(os.path.expanduser(path)):
                return True
        
        return False
    
    async def analyze(self, file_paths: List[str], context: Dict[str, Any] = None) -> List[Finding]:
        """
        Analyze Java files for security vulnerabilities
        """
        findings = []
        java_files = self._filter_java_files(file_paths)
        
        if not java_files:
            logger.info("No Java files found for analysis")
            return findings
        
        # Find Java project roots (directories with pom.xml, build.gradle, or build.xml)
        project_roots = self._find_java_projects(java_files)
        
        if not project_roots:
            logger.warning("No Java project structure found - analyzing individual files")
            # Analyze individual files with limited capabilities
            findings.extend(await self._analyze_individual_files(java_files, context))
        else:
            logger.info(f"Found {len(project_roots)} Java project(s) for analysis")
            for project_root in project_roots:
                project_findings = await self._analyze_java_project(project_root, context)
                findings.extend(project_findings)
        
        return self._deduplicate_findings(findings)
    
    def _filter_java_files(self, file_paths: List[str]) -> List[str]:
        """Filter for Java source files, including files within directories"""
        java_files = []
        for file_path in file_paths:
            if os.path.isfile(file_path):
                # Handle individual files
                if file_path.endswith(('.java', '.jsp')) and os.path.exists(file_path):
                    java_files.append(file_path)
            elif os.path.isdir(file_path):
                # Handle directories - recursively find Java files
                for root, dirs, files in os.walk(file_path):
                    for file in files:
                        if file.endswith(('.java', '.jsp')):
                            java_files.append(os.path.join(root, file))
        return java_files
    
    def _find_java_projects(self, java_files: List[str]) -> List[str]:
        """Find Java project roots by looking for build files"""
        project_roots = set()
        
        for java_file in java_files:
            # Walk up the directory tree looking for build files
            current_dir = os.path.dirname(os.path.abspath(java_file))
            while current_dir != os.path.dirname(current_dir):  # Not root
                build_files = ['pom.xml', 'build.gradle', 'build.gradle.kts', 'build.xml', 'project.clj']
                if any(os.path.exists(os.path.join(current_dir, bf)) for bf in build_files):
                    project_roots.add(current_dir)
                    break
                current_dir = os.path.dirname(current_dir)
        
        return list(project_roots)
    
    async def _analyze_java_project(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Analyze a Java project with available tools"""
        findings = []
        
        # Compile project if needed (for bytecode analysis)
        compiled_classes = await self._ensure_compilation(project_root)
        
        # Run SpotBugs if available
        if self.tools['spotbugs']['enabled'] and compiled_classes:
            spotbugs_findings = await self._run_spotbugs(project_root, compiled_classes, context)
            findings.extend(spotbugs_findings)
        
        # Run Find Security Bugs if available
        if self.tools['findsecbugs']['enabled'] and compiled_classes:
            findsecbugs_findings = await self._run_findsecbugs(project_root, compiled_classes, context)
            findings.extend(findsecbugs_findings)
        
        # Run PMD for source code analysis
        if self.tools['pmd']['enabled']:
            pmd_findings = await self._run_pmd(project_root, context)
            findings.extend(pmd_findings)
        
        return findings
    
    async def _analyze_individual_files(self, java_files: List[str], context: Dict[str, Any]) -> List[Finding]:
        """Analyze individual Java files without project structure"""
        findings = []
        
        # PMD can work on individual files
        if self.tools['pmd']['enabled']:
            for java_file in java_files:
                file_findings = await self._run_pmd_on_file(java_file, context)
                findings.extend(file_findings)
        
        # Pattern-based analysis for security issues
        for java_file in java_files:
            pattern_findings = await self._analyze_java_file_patterns(java_file, context)
            findings.extend(pattern_findings)
        
        return findings
    
    async def _ensure_compilation(self, project_root: str) -> Optional[str]:
        """Ensure Java project is compiled for bytecode analysis"""
        try:
            # Check for existing compiled classes
            target_dir = os.path.join(project_root, 'target', 'classes')
            build_dir = os.path.join(project_root, 'build', 'classes')
            out_dir = os.path.join(project_root, 'out')
            
            # Look for existing compiled classes
            for classes_dir in [target_dir, build_dir, out_dir]:
                if os.path.exists(classes_dir) and os.listdir(classes_dir):
                    logger.info(f"Found compiled classes in {classes_dir}")
                    return classes_dir
            
            # Try to compile using available build tools
            if os.path.exists(os.path.join(project_root, 'pom.xml')):
                # Maven project
                result = subprocess.run(['mvn', 'compile', '-q'], 
                                      cwd=project_root, capture_output=True, text=True, timeout=120)
                if result.returncode == 0 and os.path.exists(target_dir):
                    return target_dir
            
            elif os.path.exists(os.path.join(project_root, 'build.gradle')):
                # Gradle project
                gradle_cmd = 'gradlew' if os.path.exists(os.path.join(project_root, 'gradlew')) else 'gradle'
                result = subprocess.run([gradle_cmd, 'compileJava', '-q'], 
                                      cwd=project_root, capture_output=True, text=True, timeout=120)
                if result.returncode == 0 and os.path.exists(build_dir):
                    return build_dir
            
            # Manual compilation as fallback
            java_files = []
            for root, dirs, files in os.walk(project_root):
                if 'src' in root:  # Only compile source files
                    java_files.extend([os.path.join(root, f) for f in files if f.endswith('.java')])
            
            if java_files:
                output_dir = os.path.join(project_root, 'temp_classes')
                os.makedirs(output_dir, exist_ok=True)
                
                cmd = ['javac', '-d', output_dir] + java_files[:50]  # Limit for command length
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
                
                if result.returncode == 0:
                    return output_dir
                    
        except Exception as e:
            logger.warning(f"Could not compile Java project: {e}")
        
        return None
    
    async def _run_spotbugs(self, project_root: str, classes_dir: str, context: Dict[str, Any]) -> List[Finding]:
        """Run SpotBugs analysis"""
        findings = []
        
        try:
            output_file = os.path.join(project_root, 'spotbugs-results.xml')
            
            # Use the correct SpotBugs path
            cmd = [
                'java', '-jar', '/opt/spotbugs/lib/spotbugs.jar',
                '-xml:withMessages',
                '-output', output_file,
                '-low',  # Include low priority issues too
                classes_dir
            ]
            
            logger.info(f"Running SpotBugs in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=300)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_spotbugs_output(output_file, project_root))
                os.remove(output_file)  # Clean up
            else:
                # Try parsing stderr if no output file was created
                if result.stdout:
                    logger.info(f"SpotBugs stdout: {result.stdout[:500]}...")
                if result.stderr:
                    logger.warning(f"SpotBugs stderr: {result.stderr[:500]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("SpotBugs analysis timed out")
        except Exception as e:
            logger.error(f"Error running SpotBugs: {e}")
        
        return findings
    
    async def _run_findsecbugs(self, project_root: str, classes_dir: str, context: Dict[str, Any]) -> List[Finding]:
        """Run Find Security Bugs analysis"""
        findings = []
        
        try:
            output_file = os.path.join(project_root, 'findsecbugs-results.xml')
            
            # Find Security Bugs plugin path
            plugin_path = self._find_findsecbugs_plugin()
            if not plugin_path:
                logger.warning("Find Security Bugs plugin not found")
                return findings
            
            cmd = [
                'spotbugs',
                '-xml:withMessages',
                '-output', output_file,
                '-pluginList', plugin_path,
                '-auxclasspath', self._get_classpath(project_root),
                classes_dir
            ]
            
            logger.info(f"Running Find Security Bugs in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=300)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_spotbugs_output(output_file, project_root, is_security=True))
                os.remove(output_file)  # Clean up
                
        except subprocess.TimeoutExpired:
            logger.error("Find Security Bugs analysis timed out")
        except Exception as e:
            logger.error(f"Error running Find Security Bugs: {e}")
        
        return findings
    
    async def _run_pmd(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run PMD analysis"""
        findings = []
        
        try:
            output_file = os.path.join(project_root, 'pmd-results.xml')
            
            # Find source directories
            src_dirs = self._find_source_directories(project_root)
            if not src_dirs:
                logger.warning("No Java source directories found")
                return findings
            
            for src_dir in src_dirs:
                cmd = [
                    'pmd',
                    '-R', 'category/java/security.xml',
                    '-R', 'category/java/bestpractices.xml',
                    '-f', 'xml',
                    '-r', output_file,
                    '-d', src_dir
                ]
                
                logger.info(f"Running PMD on {src_dir}")
                
                result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                      text=True, timeout=180)
                
                if os.path.exists(output_file):
                    findings.extend(self._parse_pmd_output(output_file, project_root))
                    os.remove(output_file)  # Clean up
                    
        except subprocess.TimeoutExpired:
            logger.error("PMD analysis timed out")
        except Exception as e:
            logger.error(f"Error running PMD: {e}")
        
        return findings
    
    async def _run_pmd_on_file(self, java_file: str, context: Dict[str, Any]) -> List[Finding]:
        """Run PMD on individual Java file"""
        findings = []
        
        try:
            output_file = java_file.replace('.java', '_pmd.xml')
            
            cmd = [
                '/opt/pmd/bin/run.sh', 'pmd',
                '-R', 'category/java/security.xml,rulesets/java/quickstart.xml',
                '-f', 'xml',
                '-r', output_file,
                '-d', java_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_pmd_output(output_file, os.path.dirname(java_file)))
                os.remove(output_file)  # Clean up
            else:
                # Log PMD output for debugging
                if result.stdout:
                    logger.info(f"PMD stdout: {result.stdout[:500]}...")
                if result.stderr:
                    logger.warning(f"PMD stderr: {result.stderr[:500]}...")
                
        except Exception as e:
            logger.error(f"Error running PMD on {java_file}: {e}")
        
        return findings
    
    def _get_classpath(self, project_root: str) -> str:
        """Get project classpath for SpotBugs"""
        classpath_parts = []
        
        # Common library directories
        lib_dirs = [
            os.path.join(project_root, 'lib'),
            os.path.join(project_root, 'target', 'dependency'),
            os.path.join(project_root, 'build', 'libs')
        ]
        
        for lib_dir in lib_dirs:
            if os.path.exists(lib_dir):
                jar_files = [os.path.join(lib_dir, f) for f in os.listdir(lib_dir) if f.endswith('.jar')]
                classpath_parts.extend(jar_files)
        
        return ':'.join(classpath_parts) if classpath_parts else '.'
    
    def _find_findsecbugs_plugin(self) -> Optional[str]:
        """Find Find Security Bugs plugin JAR"""
        common_paths = [
            '/usr/share/java/findsecbugs-plugin.jar',
            '/opt/findsecbugs/findsecbugs-plugin.jar',
            './findsecbugs-plugin.jar',
            os.path.expanduser('~/.spotbugs/findsecbugs-plugin.jar')
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    def _find_source_directories(self, project_root: str) -> List[str]:
        """Find Java source directories"""
        src_dirs = []
        
        # Common source directory patterns
        patterns = [
            'src/main/java',
            'src/java',
            'src',
            'java'
        ]
        
        for pattern in patterns:
            src_path = os.path.join(project_root, pattern)
            if os.path.exists(src_path) and any(f.endswith('.java') for f in os.listdir(src_path)):
                src_dirs.append(src_path)
        
        return src_dirs
    
    def _parse_spotbugs_output(self, output_file: str, project_root: str, is_security: bool = False) -> List[Finding]:
        """Parse SpotBugs XML output"""
        findings = []
        
        try:
            tree = ET.parse(output_file)
            root = tree.getroot()
            
            for bug_instance in root.findall('.//BugInstance'):
                finding = self._create_spotbugs_finding(bug_instance, project_root, is_security)
                if finding:
                    findings.append(finding)
                    
        except ET.ParseError as e:
            logger.error(f"Error parsing SpotBugs XML: {e}")
        except Exception as e:
            logger.error(f"Error processing SpotBugs output: {e}")
        
        return findings
    
    def _parse_pmd_output(self, output_file: str, project_root: str) -> List[Finding]:
        """Parse PMD XML output"""
        findings = []
        
        try:
            tree = ET.parse(output_file)
            root = tree.getroot()
            
            for violation in root.findall('.//violation'):
                finding = self._create_pmd_finding(violation, project_root)
                if finding:
                    findings.append(finding)
                    
        except ET.ParseError as e:
            logger.error(f"Error parsing PMD XML: {e}")
        except Exception as e:
            logger.error(f"Error processing PMD output: {e}")
        
        return findings
    
    def _create_spotbugs_finding(self, bug_instance: ET.Element, project_root: str, is_security: bool) -> Optional[Finding]:
        """Create a Finding from SpotBugs bug instance"""
        try:
            bug_type = bug_instance.get('type', 'UNKNOWN')
            priority = bug_instance.get('priority', '3')
            category = bug_instance.get('category', 'UNKNOWN')
            
            # Get source line information
            source_line = bug_instance.find('.//SourceLine')
            if source_line is None:
                return None
            
            file_path = source_line.get('sourcepath', 'unknown')
            start_line = int(source_line.get('start', '0'))
            end_line = int(source_line.get('end', start_line))
            
            # Make file path relative to project root if possible
            if os.path.isabs(file_path) and project_root in file_path:
                file_path = os.path.relpath(file_path, project_root)
            
            severity = self._map_spotbugs_severity(priority, bug_type, is_security)
            cvss_score = self._calculate_cvss_score(severity, bug_type)
            
            tool_name = 'find_security_bugs' if is_security else 'spotbugs'
            
            # Format line numbers
            lines_str = f"{start_line}-{end_line}" if start_line != end_line else str(start_line)
            
            # Get code snippet (mock for now)
            snippet = f"Line {start_line}: {bug_type} detected"
            
            return Finding(
                file=file_path,
                title=f"{'Security Bug' if is_security else 'SpotBugs'}: {bug_type}",
                description=self._build_spotbugs_description(bug_instance, file_path, start_line, is_security),
                lines=lines_str,
                impact=self._get_spotbugs_impact(bug_type, category, is_security),
                severity=severity.title(),  # Ensure proper capitalization
                cvss_v4=cvss_score,
                owasp=self._get_spotbugs_owasp_categories(bug_type, is_security),
                cwe=self._get_spotbugs_cwe(bug_type, is_security),
                snippet=snippet,
                recommendation=self._get_spotbugs_recommendation(bug_type, is_security),
                sample_fix=self._get_spotbugs_sample_fix(bug_type, is_security),
                poc=self._get_spotbugs_poc(bug_type, is_security),
                references=self._get_spotbugs_references(bug_type, is_security),
                cross_file=[],  # Could be populated with related files
                tool_evidence=[ToolEvidence(
                    tool=tool_name,
                    id=f"{tool_name}_{bug_type}_{hash(file_path + str(start_line))}",
                    raw=ET.tostring(bug_instance, encoding='unicode')
                )]
            )
        except Exception as e:
            logger.error(f"Error creating SpotBugs finding: {e}")
            return None
    
    def _create_pmd_finding(self, violation: ET.Element, project_root: str) -> Optional[Finding]:
        """Create a Finding from PMD violation"""
        try:
            rule = violation.get('rule', 'Unknown')
            ruleset = violation.get('ruleset', 'Unknown')
            priority = violation.get('priority', '3')
            
            file_path = violation.get('filename', 'unknown')
            line_num = int(violation.get('beginline', '0'))
            end_line = int(violation.get('endline', line_num))
            
            description = violation.text.strip() if violation.text else ''
            
            # Make file path relative to project root if possible
            if os.path.isabs(file_path) and project_root in file_path:
                file_path = os.path.relpath(file_path, project_root)
            
            severity = self._map_pmd_severity(priority, rule, ruleset)
            cvss_score = self._calculate_cvss_score(severity, rule)
            
            # Format line numbers
            lines_str = f"{line_num}-{end_line}" if line_num != end_line else str(line_num)
            
            # Get code snippet (mock for now)
            snippet = f"Line {line_num}: {rule} violation"
            
            is_security = 'security' in ruleset.lower()
            
            return Finding(
                file=file_path,
                title=f"PMD: {rule}",
                description=self._build_pmd_description(violation, file_path, line_num),
                lines=lines_str,
                impact=self._get_pmd_impact(rule, ruleset),
                severity=severity.title(),
                cvss_v4=cvss_score,
                owasp=self._get_pmd_owasp_categories(rule, is_security),
                cwe=self._get_pmd_cwe(rule, is_security),
                snippet=snippet,
                recommendation=self._get_pmd_recommendation(rule),
                sample_fix=self._get_pmd_sample_fix(rule),
                poc=self._get_pmd_poc(rule),
                references=self._get_pmd_references(rule),
                cross_file=[],
                tool_evidence=[ToolEvidence(
                    tool="pmd",
                    id=f"pmd_{rule}_{hash(file_path + str(line_num))}",
                    raw=ET.tostring(violation, encoding='unicode')
                )]
            )
        except Exception as e:
            logger.error(f"Error creating PMD finding: {e}")
            return None
    
    async def _analyze_java_file_patterns(self, file_path: str, context: Dict[str, Any]) -> List[Finding]:
        """Analyze individual Java file for security patterns"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Pattern-based security analysis
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for SQL injection patterns
                if any(pattern in line_stripped for pattern in ['Statement.execute(', 'PreparedStatement.execute(', '.createQuery(']):
                    if '+' in line_stripped or 'concat' in line_stripped:
                        finding = self._create_pattern_finding(
                            "sql_injection", file_path, line_num, line_stripped,
                            "Potential SQL Injection", "String concatenation in SQL query - use parameterized queries"
                        )
                        findings.append(finding)
                
                # Check for hardcoded credentials
                if any(pattern in line_stripped.lower() for pattern in ['password', 'pwd', 'secret', 'key', 'token']):
                    if '=' in line_stripped and any(quote in line_stripped for quote in ['"', "'"]):
                        finding = self._create_pattern_finding(
                            "hardcoded_credential", file_path, line_num, line_stripped,
                            "Hardcoded Credential", "Potential hardcoded credential found"
                        )
                        findings.append(finding)
                
                # Check for command injection
                if any(pattern in line_stripped for pattern in ['Runtime.exec(', 'ProcessBuilder(', '.exec(']):
                    finding = self._create_pattern_finding(
                        "command_injection", file_path, line_num, line_stripped,
                        "Command Execution", "Command execution requires input validation"
                    )
                    findings.append(finding)
                
                # Check for unsafe deserialization
                if 'readObject(' in line_stripped or 'ObjectInputStream' in line_stripped:
                    finding = self._create_pattern_finding(
                        "unsafe_deserialization", file_path, line_num, line_stripped,
                        "Unsafe Deserialization", "Deserialization can lead to remote code execution"
                    )
                    findings.append(finding)
                    
        except Exception as e:
            logger.error(f"Error analyzing Java file {file_path}: {e}")
        
        return findings
    
    def _create_pattern_finding(self, pattern_id: str, file_path: str, line_num: int, 
                               line_content: str, title: str, description: str) -> Finding:
        """Create a Finding from pattern analysis"""
        severity = self._get_pattern_severity(pattern_id)
        cvss_score = self._calculate_cvss_score(severity, pattern_id)
        
        return Finding(
            id=f"java_pattern_{pattern_id}_{hash(file_path + str(line_num))}",
            title=f"Java: {title}",
            description=f"{description}\n\nLocation: {file_path}:{line_num}\nCode: {line_content}",
            severity=severity.lower(),
            category="java_patterns",
            file=file_path,
            lines=[line_num],
            confidence_score=70,
            cvss_v4=cvss_score,
            evidence=ToolEvidence(
                tool_name="java_analyzer",
                raw_output=f"Pattern: {pattern_id}, Line: {line_content}",
                confidence=70
            )
        )
    
    def _map_spotbugs_severity(self, priority: str, bug_type: str, is_security: bool) -> str:
        """Map SpotBugs priority to our severity levels"""
        # Security bugs get higher severity
        if is_security:
            if priority == '1':
                return 'CRITICAL'
            elif priority == '2':
                return 'HIGH'
            else:
                return 'MEDIUM'
        
        # Regular SpotBugs priorities
        if priority == '1':
            return 'HIGH'
        elif priority == '2':
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _map_pmd_severity(self, priority: str, rule: str, ruleset: str) -> str:
        """Map PMD priority to our severity levels"""
        # Security rules get higher severity
        if 'security' in ruleset.lower() or any(sec in rule.lower() for sec in ['security', 'crypto', 'sql', 'xss']):
            if priority in ['1', '2']:
                return 'HIGH'
            else:
                return 'MEDIUM'
        
        # Regular PMD priorities
        if priority == '1':
            return 'MEDIUM'
        elif priority == '2':
            return 'LOW'
        else:
            return 'LOW'
    
    def _get_spotbugs_confidence(self, priority: str) -> int:
        """Get confidence score based on SpotBugs priority"""
        priority_map = {'1': 90, '2': 80, '3': 70}
        return priority_map.get(priority, 60)
    
    def _get_pmd_confidence(self, priority: str) -> int:
        """Get confidence score based on PMD priority"""
        priority_map = {'1': 85, '2': 75, '3': 65}
        return priority_map.get(priority, 60)
    
    def _get_pattern_severity(self, pattern_id: str) -> str:
        """Get severity for pattern-based findings"""
        severity_map = {
            'sql_injection': 'HIGH',
            'command_injection': 'HIGH',
            'unsafe_deserialization': 'CRITICAL',
            'hardcoded_credential': 'MEDIUM'
        }
        return severity_map.get(pattern_id, 'LOW')
    
    def _calculate_cvss_score(self, severity: str, category: str) -> CVSSv4:
        """Calculate CVSS score based on severity and category"""
        base_scores = {
            'CRITICAL': 9.0,
            'HIGH': 7.5,
            'MEDIUM': 5.0,
            'LOW': 2.5
        }
        
        score = base_scores.get(severity, 5.0)
        
        # Adjust score based on security category
        if any(keyword in category.lower() for keyword in ['injection', 'deserialization', 'security']):
            score += 1.0
        elif 'credential' in category.lower():
            score += 0.5
        
        score = min(10.0, score)  # Cap at 10.0
        
        return CVSSv4(
            score=score,
            vector=f"CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:{'H' if score >= 7 else 'M' if score >= 4 else 'L'}/VI:L/VA:L/SC:N/SI:N/SA:N"
        )
    
    def _build_spotbugs_description(self, bug_instance: ET.Element, file_path: str, line_num: int, is_security: bool) -> str:
        """Build detailed description for SpotBugs finding"""
        bug_type = bug_instance.get('type', 'UNKNOWN')
        priority = bug_instance.get('priority', '3')
        
        short_message = bug_instance.find('.//ShortMessage')
        long_message = bug_instance.find('.//LongMessage')
        
        short_text = short_message.text if short_message is not None else 'SpotBugs issue'
        long_text = long_message.text if long_message is not None else 'No detailed description available'
        
        tool_name = 'Find Security Bugs' if is_security else 'SpotBugs'
        
        return f"""
{tool_name} Analysis:

Bug Type: {bug_type}
Priority: {priority}
Summary: {short_text}
Details: {long_text}
Location: {file_path}:{line_num}

Security Impact:
{'This security vulnerability could allow attackers to compromise your application.' if is_security else 'This code quality issue may lead to bugs or maintenance problems.'}

Recommendation:
{'Address this security vulnerability immediately to prevent potential exploits.' if is_security else 'Consider fixing this issue to improve code quality and maintainability.'}
"""
    
    def _build_pmd_description(self, violation: ET.Element, file_path: str, line_num: int) -> str:
        """Build detailed description for PMD finding"""
        rule = violation.get('rule', 'Unknown')
        ruleset = violation.get('ruleset', 'Unknown')
        priority = violation.get('priority', '3')
        description = violation.text.strip() if violation.text else 'No description available'
        
        return f"""
PMD Analysis:

Rule: {rule}
Ruleset: {ruleset}
Priority: {priority}
Description: {description}
Location: {file_path}:{line_num}

Security Impact:
{'This rule violation may have security implications for your Java application.' if 'security' in ruleset.lower() else 'This code quality issue should be addressed for better maintainability.'}

Recommendation:
Follow PMD best practices to resolve this violation and improve code quality.
"""
    
    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings"""
        seen = set()
        deduplicated = []
        
        for finding in findings:
            # Create a key based on file, line, and title
            key = (finding.file, tuple(finding.lines), finding.title)
            if key not in seen:
                seen.add(key)
                deduplicated.append(finding)
        
        return deduplicated
    
    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['java']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Java Security Analyzer',
            'description': 'Comprehensive Java security analysis using SpotBugs, PMD, and Find Security Bugs',
            'supported_extensions': self.supported_extensions,
            'available_tools': {
                name: {
                    'enabled': info['enabled'],
                    'description': info['description']
                }
                for name, info in self.tools.items()
            }
        }
    
    # Required abstract methods from BaseTool
    def is_available(self) -> bool:
        """Check if Java analysis tools are available"""
        return any(tool['enabled'] for tool in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool versions"""
        versions = []
        
        if self.tools['spotbugs']['enabled']:
            try:
                result = subprocess.run(['java', '-jar', '/opt/spotbugs/lib/spotbugs.jar', '-version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    versions.append(f"SpotBugs: {result.stdout.strip()}")
                else:
                    versions.append("SpotBugs: ")
            except:
                versions.append("SpotBugs: ")
        
        if self.tools['pmd']['enabled']:
            try:
                result = subprocess.run(['/opt/pmd/bin/run.sh', 'pmd', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    versions.append(f"PMD: {result.stdout.strip()}")
                else:
                    versions.append("PMD: ")
            except:
                versions.append("PMD: ")
        
        return '; '.join(versions) if versions else "Unknown"
    
    async def scan(self, target_path: str, **kwargs) -> List[Finding]:
        """
        Perform security scan on target using analyze method
        
        Args:
            target_path: Path to scan
            **kwargs: Scanner-specific options
            
        Returns:
            List[Finding] directly (not ScanResult)
        """
        try:
            # Use existing analyze method
            findings = await self.analyze([target_path], kwargs.get('context', {}))
            return findings
        except Exception as e:
            logger.error(f"Java analyzer scan error: {e}")
            return []
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """
        Convert tool-specific output to normalized Finding objects
        This is handled by individual tool methods (_create_spotbugs_finding, etc.)
        """
        # This method is implemented in the individual tool analysis methods
        return []
    
    # Required abstract method implementations
    def is_available(self) -> bool:
        """Check if Java analysis tools are available"""
        return any(tool['enabled'] for tool in self.tools.values())
    
    def get_version(self) -> str:
        """Get Java analyzer version information"""
        versions = []
        
        if self.tools['spotbugs']['enabled']:
            try:
                # Try to get SpotBugs version
                result = subprocess.run(['java', '-jar', '/opt/spotbugs/lib/spotbugs.jar', '-version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    versions.append(f"SpotBugs: {result.stdout.strip()}")
            except:
                versions.append("SpotBugs: Available")
        
        if self.tools['pmd']['enabled']:
            try:
                # Try to get PMD version
                result = subprocess.run(['/opt/pmd/bin/run.sh', 'pmd', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    versions.append(f"PMD: {result.stdout.strip()}")
            except:
                versions.append("PMD: Available")
        
        return "; ".join(versions) if versions else "Java Analyzer v1.0"
    
    def _get_spotbugs_impact(self, bug_type: str, category: str, is_security: bool) -> str:
        """Get impact description for SpotBugs finding"""
        if is_security or category == "SECURITY":
            if "SQL" in bug_type:
                return "SQL injection attacks could allow unauthorized data access or manipulation"
            elif "COMMAND" in bug_type:
                return "Command injection could allow arbitrary code execution"
            elif "XSS" in bug_type:
                return "Cross-site scripting could compromise user accounts"
            elif "CRYPTO" in bug_type:
                return "Weak cryptography could expose sensitive data"
            else:
                return "Security vulnerability could compromise application security"
        else:
            return "Code quality issue that may lead to bugs or maintenance problems"
    
    def _get_spotbugs_owasp_categories(self, bug_type: str, is_security: bool) -> List[str]:
        """Get OWASP categories for SpotBugs finding"""
        if not is_security:
            return []
        
        if "SQL" in bug_type:
            return ["A03:2021 - Injection"]
        elif "XSS" in bug_type:
            return ["A03:2021 - Injection"]
        elif "CRYPTO" in bug_type:
            return ["A02:2021 - Cryptographic Failures"]
        elif "PATH" in bug_type:
            return ["A01:2021 - Broken Access Control"]
        else:
            return ["A06:2021 - Vulnerable and Outdated Components"]
    
    def _get_spotbugs_cwe(self, bug_type: str, is_security: bool) -> List[str]:
        """Get CWE identifiers for SpotBugs finding"""
        if not is_security:
            return []
        
        if "SQL" in bug_type:
            return ["CWE-89"]
        elif "XSS" in bug_type:
            return ["CWE-79"]
        elif "COMMAND" in bug_type:
            return ["CWE-78"]
        elif "CRYPTO" in bug_type:
            return ["CWE-327"]
        elif "PATH" in bug_type:
            return ["CWE-22"]
        else:
            return ["CWE-693"]
    
    def _get_spotbugs_recommendation(self, bug_type: str, is_security: bool) -> str:
        """Get recommendation for SpotBugs finding"""
        if "SQL" in bug_type:
            return "Use parameterized queries or prepared statements to prevent SQL injection"
        elif "XSS" in bug_type:
            return "Properly escape output and validate input to prevent XSS attacks"
        elif "COMMAND" in bug_type:
            return "Avoid executing system commands with user input; use safe alternatives"
        elif "CRYPTO" in bug_type:
            return "Use strong, up-to-date cryptographic algorithms and proper key management"
        elif "PATH" in bug_type:
            return "Validate and sanitize file paths to prevent directory traversal"
        else:
            return "Follow secure coding practices and review the flagged code for security issues"
    
    def _get_spotbugs_sample_fix(self, bug_type: str, is_security: bool) -> str:
        """Get sample fix for SpotBugs finding"""
        if "SQL" in bug_type:
            return """// Instead of:
String sql = "SELECT * FROM users WHERE name = '" + userInput + "'";
Statement stmt = conn.createStatement();
ResultSet rs = stmt.executeQuery(sql);

// Use:
String sql = "SELECT * FROM users WHERE name = ?";
PreparedStatement pstmt = conn.prepareStatement(sql);
pstmt.setString(1, userInput);
ResultSet rs = pstmt.executeQuery();"""
        elif "RANDOM" in bug_type:
            return """// Instead of:
Random rand = new Random();
int token = rand.nextInt(1000000);

// Use:
SecureRandom secureRand = new SecureRandom();
byte[] tokenBytes = new byte[32];
secureRand.nextBytes(tokenBytes);
String token = Base64.getEncoder().encodeToString(tokenBytes);"""
        else:
            return "Review the flagged code and apply appropriate security measures"
    
    def _get_spotbugs_poc(self, bug_type: str, is_security: bool) -> str:
        """Get proof of concept for SpotBugs finding"""
        if "SQL" in bug_type:
            return "Test with input: '; DROP TABLE users; --"
        elif "XSS" in bug_type:
            return "Test with input: <script>alert('XSS')</script>"
        elif "PATH" in bug_type:
            return "Test with input: ../../../etc/passwd"
        else:
            return "Review the specific vulnerability type for appropriate testing methods"
    
    def _get_spotbugs_references(self, bug_type: str, is_security: bool) -> List[str]:
        """Get references for SpotBugs finding"""
        refs = ["https://spotbugs.readthedocs.io/"]
        
        if "SQL" in bug_type:
            refs.extend([
                "https://owasp.org/www-community/attacks/SQL_Injection",
                "https://cwe.mitre.org/data/definitions/89.html"
            ])
        elif "XSS" in bug_type:
            refs.extend([
                "https://owasp.org/www-community/attacks/xss/",
                "https://cwe.mitre.org/data/definitions/79.html"
            ])
        
        return refs
    
    def _get_pmd_impact(self, rule: str, ruleset: str) -> str:
        """Get impact description for PMD finding"""
        if 'security' in ruleset.lower():
            return "Security-related code quality issue that may introduce vulnerabilities"
        elif 'performance' in ruleset.lower():
            return "Performance issue that may degrade application responsiveness"
        elif 'resource' in rule.lower():
            return "Resource management issue that may cause memory leaks or resource exhaustion"
        else:
            return "Code quality issue that may lead to bugs or maintenance problems"
    
    def _get_pmd_owasp_categories(self, rule: str, is_security: bool) -> List[str]:
        """Get OWASP categories for PMD finding"""
        if not is_security:
            return []
        return ["A06:2021 - Vulnerable and Outdated Components"]
    
    def _get_pmd_cwe(self, rule: str, is_security: bool) -> List[str]:
        """Get CWE identifiers for PMD finding"""
        if not is_security:
            return []
        if 'resource' in rule.lower():
            return ["CWE-401"]  # Missing Release of Memory after Effective Lifetime
        return ["CWE-693"]  # Protection Mechanism Failure
    
    def _get_pmd_recommendation(self, rule: str) -> str:
        """Get recommendation for PMD finding"""
        if 'resource' in rule.lower():
            return "Properly close resources using try-with-resources or finally blocks"
        elif 'null' in rule.lower():
            return "Add null checks and proper error handling"
        elif 'security' in rule.lower():
            return "Review the code for security best practices"
        else:
            return "Follow Java coding best practices and refactor the flagged code"
    
    def _get_pmd_sample_fix(self, rule: str) -> str:
        """Get sample fix for PMD finding"""
        if 'resource' in rule.lower():
            return """// Instead of:
FileInputStream fis = new FileInputStream(file);
// ... use fis
fis.close(); // May not execute if exception occurs

// Use:
try (FileInputStream fis = new FileInputStream(file)) {
    // ... use fis
} // Automatically closed"""
        else:
            return "Review PMD documentation for specific rule guidance"
    
    def _get_pmd_poc(self, rule: str) -> str:
        """Get proof of concept for PMD finding"""
        if 'resource' in rule.lower():
            return "Monitor application memory usage under load to identify resource leaks"
        else:
            return "Review the specific PMD rule for testing recommendations"
    
    def _get_pmd_references(self, rule: str) -> List[str]:
        """Get references for PMD finding"""
        return [
            "https://pmd.github.io/",
            f"https://pmd.github.io/pmd/pmd_rules_java.html"
        ]
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """Convert raw output to normalized findings"""
        # This method is used by the base class scan method
        # Our analyze method already returns normalized findings
        return []