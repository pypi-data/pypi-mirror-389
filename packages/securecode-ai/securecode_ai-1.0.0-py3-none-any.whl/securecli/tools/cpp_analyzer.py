"""
C++ Security Analysis Tools Integration
Supports Clang Static Analyzer and CppCheck for comprehensive C++ security analysis
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path

from ..schemas.findings import Finding, ToolEvidence, CVSSv4
from .base import BaseTool

logger = logging.getLogger(__name__)

class CppAnalyzer(BaseTool):
    """
    C++ Security Analyzer supporting multiple static analysis tools
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "cpp_analyzer"
        self.supported_extensions = ['.cpp', '.cc', '.cxx', '.c++', '.hpp', '.h', '.hh', '.hxx', '.h++']
        
        # Tool configurations
        self.tools = {
            'clang_analyzer': {
                'command': 'scan-build',
                'enabled': self._check_tool_availability('scan-build'),
                'description': 'Clang Static Analyzer for C++ security analysis'
            },
            'cppcheck': {
                'command': 'cppcheck',
                'enabled': self._check_tool_availability('cppcheck'),
                'description': 'CppCheck static analysis tool'
            }
        }
    
    def is_available(self) -> bool:
        """Check if C++ analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try cppcheck first as it's more commonly available
            if self.tools['cppcheck']['enabled']:
                result = subprocess.run(['cppcheck', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            # Try clang as fallback
            if self.tools['clang_analyzer']['enabled']:
                result = subprocess.run(['clang', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.split('\n')[0]
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from C++ tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'C++ security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'cpp_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run C++ security analysis tools."""
        findings = []
        
        # Check if this is a C++ project
        if not self._has_cpp_files(repo_path):
            return findings
        
        # Get C++ files for analysis
        cpp_files = self._get_cpp_files(repo_path)
        if not cpp_files:
            return findings
        
        # Run Clang Static Analyzer if available
        if self.tools['clang_analyzer']['enabled']:
            try:
                clang_findings = await self._run_clang_static_analyzer(repo_path, cpp_files)
                findings.extend(clang_findings)
            except Exception as e:
                logger.error(f"Clang Static Analyzer failed: {e}")
        
        # Run CppCheck if available
        if self.tools['cppcheck']['enabled']:
            try:
                cppcheck_findings = await self._run_cppcheck(repo_path, cpp_files)
                findings.extend(cppcheck_findings)
            except Exception as e:
                logger.error(f"CppCheck failed: {e}")
        
        return findings
    
    def _get_cpp_files(self, repo_path: str) -> List[str]:
        """Get list of C++ files for analysis"""
        cpp_files = []
        for root, dirs, files in os.walk(repo_path):
            # Skip build directories
            dirs[:] = [d for d in dirs if d not in ['build', 'target', 'cmake-build-debug', 'cmake-build-release']]
            
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    cpp_files.append(os.path.join(root, file))
        return cpp_files
    
    async def _run_clang_static_analyzer(self, repo_path: str, cpp_files: List[str]) -> List[Finding]:
        """Run Clang Static Analyzer"""
        findings = []
        
        try:
            # Create output directory for analysis results
            output_dir = os.path.join(repo_path, '.clang_analysis')
            os.makedirs(output_dir, exist_ok=True)
            
            # Run scan-build on the entire project
            cmd = [
                'scan-build',
                '-o', output_dir,
                '--format', 'html',
                '--status-bugs',
                'make'  # This would need to be adapted based on build system
            ]
            
            # If no Makefile, try direct clang analysis on individual files
            if not os.path.exists(os.path.join(repo_path, 'Makefile')):
                for cpp_file in cpp_files[:5]:  # Limit to first 5 files for performance
                    cmd = [
                        'clang',
                        '--analyze',
                        '-Xanalyzer', '-analyzer-output=text',
                        cpp_file
                    ]
                    
                    result = await self._run_subprocess(cmd, cwd=repo_path)
                    if result.stderr:
                        findings.extend(self._parse_clang_output(result.stderr, cpp_file))
            
        except Exception as e:
            logger.error(f"Clang Static Analyzer error: {e}")
        
        return findings
    
    async def _run_cppcheck(self, repo_path: str, cpp_files: List[str]) -> List[Finding]:
        """Run CppCheck static analysis"""
        findings = []
        
        try:
            cmd = [
                'cppcheck',
                '--enable=all',
                '--xml',
                '--xml-version=2',
                '--suppress=missingIncludeSystem',
                '--suppress=unusedFunction',
                repo_path
            ]
            
            result = await self._run_subprocess(cmd, cwd=repo_path)
            
            if result.stderr:  # CppCheck outputs XML to stderr
                findings.extend(self._parse_cppcheck_xml(result.stderr, repo_path))
                
        except Exception as e:
            logger.error(f"CppCheck error: {e}")
        
        return findings
    
    def _parse_clang_output(self, output: str, file_path: str) -> List[Finding]:
        """Parse Clang Static Analyzer output"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'warning:' in line or 'error:' in line:
                # Parse clang output format: file:line:column: warning: message
                parts = line.split(':', 4)
                if len(parts) >= 4:
                    try:
                        file_name = parts[0]
                        line_num = parts[1]
                        severity = 'HIGH' if 'error' in line else 'MEDIUM'
                        message = parts[3] if len(parts) > 3 else 'Clang analysis issue'
                        
                        finding = self._create_finding(
                            file_path=file_name,
                            title="Clang Static Analyzer Issue",
                            description=message.strip(),
                            severity=severity,
                            lines=line_num,
                            tool_name="clang_static_analyzer"
                        )
                        findings.append(finding)
                    except (ValueError, IndexError):
                        continue
        
        return findings
    
    def _parse_cppcheck_xml(self, xml_output: str, repo_path: str) -> List[Finding]:
        """Parse CppCheck XML output"""
        findings = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_output)
            
            for error in root.findall('.//error'):
                error_id = error.get('id', 'unknown')
                severity = error.get('severity', 'style')
                message = error.get('msg', 'CppCheck issue')
                
                # Map CppCheck severity to our severity levels
                severity_map = {
                    'error': 'HIGH',
                    'warning': 'MEDIUM',
                    'style': 'LOW',
                    'performance': 'LOW',
                    'portability': 'LOW',
                    'information': 'INFO'
                }
                mapped_severity = severity_map.get(severity, 'MEDIUM')
                
                # Get location information
                location = error.find('location')
                if location is not None:
                    file_path = location.get('file', 'unknown')
                    line_num = location.get('line', '1')
                    
                    finding = self._create_finding(
                        file_path=os.path.relpath(file_path, repo_path),
                        title=f"CppCheck: {error_id}",
                        description=message,
                        severity=mapped_severity,
                        lines=line_num,
                        tool_name="cppcheck"
                    )
                    findings.append(finding)
                    
        except ET.ParseError as e:
            logger.error(f"Failed to parse CppCheck XML: {e}")
        
        return findings
    
    def _create_finding(self, file_path: str, title: str, description: str,
                       severity: str, lines: str, tool_name: str) -> Finding:
        """Create a standardized Finding object"""
        
        # Create CVSS score based on severity
        cvss_scores = {'CRITICAL': 9.8, 'HIGH': 7.5, 'MEDIUM': 5.5, 'LOW': 3.0, 'INFO': 2.0}
        cvss_score = CVSSv4(
            score=cvss_scores.get(severity, 5.0),
            vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
        )
        
        # Create tool evidence
        evidence = ToolEvidence(
            tool_name=tool_name,
            tool_version=self.version,
            confidence_score=80,
            raw_output=description,
            analysis_metadata={
                'analyzer': 'CppAnalyzer',
                'file_path': file_path,
                'tool_used': tool_name
            }
        )
        
        return Finding(
            file=file_path,
            title=title,
            description=description,
            lines=lines,
            impact=f"C++ {severity.lower()} severity security issue that could affect application security",
            severity=severity.title(),
            cvss_v4=cvss_score,
            snippet=f"// C++ security issue detected by {tool_name}",
            recommendation="Review and fix the identified C++ security issue",
            sample_fix="// Apply C++ security best practices",
            poc="// No proof-of-concept available for static analysis finding",
            owasp=["A03:2021 – Injection", "A06:2021 – Vulnerable Components"],
            cwe=["CWE-20", "CWE-119"],
            references=[
                "https://clang-analyzer.llvm.org/",
                "http://cppcheck.sourceforge.net/",
                "https://wiki.sei.cmu.edu/confluence/pages/viewpage.action?pageId=88046682"
            ],
            cross_file=[],
            tool_evidence=[evidence]
        )
    
    async def _run_subprocess(self, cmd: List[str], cwd: str = None):
        """Run subprocess command asynchronously"""
        import asyncio
        
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=cwd
        )
        
        stdout, stderr = await process.communicate()
        
        class Result:
            def __init__(self, returncode, stdout, stderr):
                self.returncode = returncode
                self.stdout = stdout.decode() if stdout else ""
                self.stderr = stderr.decode() if stderr else ""
        
        return Result(process.returncode, stdout, stderr)

    def _has_cpp_files(self, repo_path: str) -> bool:
        """Check if repository contains C++ files."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    return True
        return False

    def _check_tool_availability(self, tool_name: str) -> bool:
        """Check if a tool is available in the system PATH"""
        try:
            result = subprocess.run([tool_name, '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    async def analyze(self, file_paths: List[str], context: Dict[str, Any] = None) -> List[Finding]:
        """
        Analyze C++ files for security vulnerabilities
        """
        findings = []
        cpp_files = self._filter_cpp_files(file_paths)
        
        if not cpp_files:
            logger.info("No C++ files found for analysis")
            return findings
        
        logger.info(f"Analyzing {len(cpp_files)} C++ files")
        
        # Run Clang Static Analyzer
        if self.tools['clang_analyzer']['enabled']:
            clang_findings = await self._run_clang_analyzer(cpp_files, context)
            findings.extend(clang_findings)
        
        # Run CppCheck
        if self.tools['cppcheck']['enabled']:
            cppcheck_findings = await self._run_cppcheck(cpp_files, context)
            findings.extend(cppcheck_findings)
        
        if not any(tool['enabled'] for tool in self.tools.values()):
            logger.warning("No C++ analysis tools are available. Install clang or cppcheck.")
        
        return self._deduplicate_findings(findings)
    
    def _filter_cpp_files(self, file_paths: List[str]) -> List[str]:
        """Filter for C++ source and header files"""
        cpp_files = []
        for file_path in file_paths:
            if any(file_path.endswith(ext) for ext in self.supported_extensions):
                if os.path.exists(file_path):
                    cpp_files.append(file_path)
        return cpp_files
    
    async def _run_clang_analyzer(self, files: List[str], context: Dict[str, Any]) -> List[Finding]:
        """Run Clang Static Analyzer on C++ files"""
        findings = []
        
        try:
            # Create temporary directory for analysis results
            import tempfile
            with tempfile.TemporaryDirectory() as temp_dir:
                
                # Prepare scan-build command
                cmd = [
                    'scan-build',
                    '-o', temp_dir,
                    '--status-bugs',
                    '-enable-checker', 'security',
                    '-enable-checker', 'alpha.security',
                    '-enable-checker', 'alpha.unix',
                    '-enable-checker', 'alpha.core',
                    '--format', 'plist-multi-file'
                ]
                
                # Add build command (try to detect build system)
                build_cmd = self._detect_build_system(files)
                cmd.extend(build_cmd)
                
                logger.info(f"Running Clang Static Analyzer: {' '.join(cmd)}")
                
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
                
                if result.returncode == 0 or result.returncode == 1:  # 1 means bugs found
                    findings.extend(self._parse_clang_results(temp_dir, files))
                else:
                    logger.error(f"Clang analyzer failed: {result.stderr}")
                    
        except subprocess.TimeoutExpired:
            logger.error("Clang analyzer timed out")
        except Exception as e:
            logger.error(f"Error running Clang analyzer: {e}")
        
        return findings
    
    async def _run_cppcheck(self, files: List[str], context: Dict[str, Any]) -> List[Finding]:
        """Run CppCheck on C++ files"""
        findings = []
        
        try:
            cmd = [
                'cppcheck',
                '--enable=warning,style,performance,portability,information,missingInclude',
                '--inconclusive',
                '--xml',
                '--xml-version=2'
            ]
            cmd.extend(files)  # Properly extend the list
            
            logger.info(f"Running CppCheck: {' '.join(cmd[:5])}... ({len(files)} files)")
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=300)
            
            if result.stderr:  # CppCheck outputs to stderr
                findings.extend(self._parse_cppcheck_results(result.stderr, files))
            
        except subprocess.TimeoutExpired:
            logger.error("CppCheck timed out")
        except Exception as e:
            logger.error(f"Error running CppCheck: {e}")
        
        return findings
    
    def _detect_build_system(self, files: List[str]) -> List[str]:
        """Detect build system and return appropriate build command"""
        project_dir = os.path.dirname(files[0]) if files else '.'
        
        # Check for CMakeLists.txt
        if os.path.exists(os.path.join(project_dir, 'CMakeLists.txt')):
            return ['cmake', '--build', '.']
        
        # Check for Makefile
        if os.path.exists(os.path.join(project_dir, 'Makefile')):
            return ['make']
        
        # Check for build.sh or similar
        for build_script in ['build.sh', 'compile.sh']:
            if os.path.exists(os.path.join(project_dir, build_script)):
                return [f'./{build_script}']
        
        # Fallback: try to compile individual files
        return ['clang++', '-c'] + files
    
    def _parse_clang_results(self, results_dir: str, files: List[str]) -> List[Finding]:
        """Parse Clang Static Analyzer results"""
        findings = []
        
        try:
            # Look for plist files in results directory
            for root, dirs, filenames in os.walk(results_dir):
                for filename in filenames:
                    if filename.endswith('.plist'):
                        plist_path = os.path.join(root, filename)
                        findings.extend(self._parse_plist_file(plist_path))
        except Exception as e:
            logger.error(f"Error parsing Clang results: {e}")
        
        return findings
    
    def _parse_plist_file(self, plist_path: str) -> List[Finding]:
        """Parse a Clang plist file for findings"""
        findings = []
        
        try:
            import plistlib
            with open(plist_path, 'rb') as f:
                data = plistlib.load(f)
            
            for diagnostic in data.get('diagnostics', []):
                finding = self._create_clang_finding(diagnostic)
                if finding:
                    findings.append(finding)
                    
        except Exception as e:
            logger.error(f"Error parsing plist file {plist_path}: {e}")
        
        return findings
    
    def _create_clang_finding(self, diagnostic: Dict[str, Any]) -> Optional[Finding]:
        """Create a Finding object from Clang diagnostic"""
        try:
            location = diagnostic.get('location', {})
            file_path = location.get('file', 'unknown')
            line_number = location.get('line', 0)
            
            severity = self._map_clang_severity(diagnostic.get('type', 'warning'))
            cvss_score = self._calculate_cvss_score(severity, diagnostic.get('category', ''))
            
            return Finding(
                id=f"clang_{hash(str(diagnostic))}",
                title=f"Clang: {diagnostic.get('description', 'Security Issue')}",
                description=self._build_clang_description(diagnostic),
                severity=severity.lower(),
                category="cpp_security",
                file=file_path,
                lines=[line_number],
                confidence_score=85,
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="clang_analyzer",
                    raw_output=str(diagnostic),
                    confidence=85
                )
            )
        except Exception as e:
            logger.error(f"Error creating Clang finding: {e}")
            return None
    
    def _parse_cppcheck_results(self, xml_output: str, files: List[str]) -> List[Finding]:
        """Parse CppCheck XML output"""
        findings = []
        
        try:
            import xml.etree.ElementTree as ET
            root = ET.fromstring(xml_output)
            
            for error in root.findall('.//error'):
                finding = self._create_cppcheck_finding(error)
                if finding:
                    findings.append(finding)
                    
        except ET.ParseError as e:
            logger.error(f"Error parsing CppCheck XML: {e}")
        except Exception as e:
            logger.error(f"Error processing CppCheck results: {e}")
        
        return findings
    
    def _create_cppcheck_finding(self, error_elem) -> Optional[Finding]:
        """Create a Finding object from CppCheck error element"""
        try:
            error_id = error_elem.get('id', 'unknown')
            severity = error_elem.get('severity', 'style')
            msg = error_elem.get('msg', 'CppCheck issue')
            
            # Get location information
            location = error_elem.find('location')
            if location is not None:
                file_path = location.get('file', 'unknown')
                line_number = int(location.get('line', 0))
            else:
                file_path = 'unknown'
                line_number = 0
            
            mapped_severity = self._map_cppcheck_severity(severity)
            cvss_score = self._calculate_cvss_score(mapped_severity, error_id)
            
            return Finding(
                id=f"cppcheck_{error_id}_{hash(file_path + str(line_number))}",
                title=f"CppCheck: {error_id}",
                description=self._build_cppcheck_description(error_elem),
                severity=mapped_severity.lower(),
                category="cpp_security",
                file=file_path,
                lines=[line_number],
                confidence_score=75,
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="cppcheck",
                    raw_output=ET.tostring(error_elem, encoding='unicode'),
                    confidence=75
                )
            )
        except Exception as e:
            logger.error(f"Error creating CppCheck finding: {e}")
            return None
    
    def _map_clang_severity(self, clang_type: str) -> str:
        """Map Clang diagnostic type to our severity levels"""
        severity_map = {
            'error': 'HIGH',
            'warning': 'MEDIUM',
            'note': 'LOW'
        }
        return severity_map.get(clang_type.lower(), 'MEDIUM')
    
    def _map_cppcheck_severity(self, cppcheck_severity: str) -> str:
        """Map CppCheck severity to our severity levels"""
        severity_map = {
            'error': 'HIGH',
            'warning': 'MEDIUM',
            'style': 'LOW',
            'performance': 'LOW',
            'portability': 'LOW',
            'information': 'LOW'
        }
        return severity_map.get(cppcheck_severity.lower(), 'MEDIUM')
    
    def _calculate_cvss_score(self, severity: str, category: str) -> CVSSv4:
        """Calculate CVSS score based on severity and category"""
        base_scores = {
            'HIGH': 7.5,
            'MEDIUM': 5.0,
            'LOW': 2.5
        }
        
        score = base_scores.get(severity, 5.0)
        
        # Adjust score based on security category
        if any(keyword in category.lower() for keyword in ['buffer', 'overflow', 'underflow']):
            score += 1.0
        elif any(keyword in category.lower() for keyword in ['use-after-free', 'double-free']):
            score += 1.5
        elif any(keyword in category.lower() for keyword in ['format', 'injection']):
            score += 0.5
        
        score = min(10.0, score)  # Cap at 10.0
        
        return CVSSv4(
            score=score,
            vector=f"CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:{'H' if score >= 7 else 'M' if score >= 4 else 'L'}/VI:L/VA:L/SC:N/SI:N/SA:N"
        )
    
    def _build_clang_description(self, diagnostic: Dict[str, Any]) -> str:
        """Build detailed description for Clang finding"""
        description = diagnostic.get('description', 'Security issue detected')
        category = diagnostic.get('category', 'General')
        
        location = diagnostic.get('location', {})
        file_path = location.get('file', 'unknown')
        line_number = location.get('line', 0)
        
        return f"""
Clang Static Analyzer Security Finding:

Issue: {description}
Category: {category}
Location: {file_path}:{line_number}

Security Impact:
This issue was detected by Clang's static analyzer, which performs deep code analysis to identify potential security vulnerabilities, memory safety issues, and logic errors in C++ code.

Recommendation:
Review the flagged code for potential security implications. Consider the specific warning category and apply appropriate fixes to ensure memory safety and prevent potential exploits.
"""
    
    def _build_cppcheck_description(self, error_elem) -> str:
        """Build detailed description for CppCheck finding"""
        error_id = error_elem.get('id', 'unknown')
        severity = error_elem.get('severity', 'style')
        msg = error_elem.get('msg', 'CppCheck issue')
        
        location = error_elem.find('location')
        if location is not None:
            file_path = location.get('file', 'unknown')
            line_number = location.get('line', 0)
        else:
            file_path = 'unknown'
            line_number = 0
        
        return f"""
CppCheck Static Analysis Finding:

Issue ID: {error_id}
Message: {msg}
Severity: {severity}
Location: {file_path}:{line_number}

Security Impact:
CppCheck has identified a potential issue in your C++ code. Depending on the specific issue type, this could lead to memory safety problems, undefined behavior, or security vulnerabilities.

Recommendation:
Review the specific CppCheck rule violation and apply the recommended fix. Ensure proper memory management, bounds checking, and adherence to C++ best practices.
"""
    
    def _deduplicate_findings(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicate findings based on file, line, and issue type"""
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
        return ['cpp', 'c++', 'c', 'cc', 'cxx']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'C++ Security Analyzer',
            'description': 'Comprehensive C++ security analysis using Clang and CppCheck',
            'supported_extensions': self.supported_extensions,
            'available_tools': {
                name: {
                    'enabled': info['enabled'],
                    'description': info['description']
                }
                for name, info in self.tools.items()
            }
        }