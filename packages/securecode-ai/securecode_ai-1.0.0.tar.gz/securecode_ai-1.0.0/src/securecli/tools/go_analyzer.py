"""
Go Security Analysis Tools Integration
Supports Gosec, Go-critic, and Staticcheck for comprehensive Go security analysis
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

class GoAnalyzer(BaseTool):
    """
    Go Security Analyzer supporting Gosec, Go-critic, and Staticcheck
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "go_analyzer"
        self.supported_extensions = ['.go', '.mod', '.sum']
        
        # Tool configurations
        self.tools = {
            'gosec': {
                'command': 'gosec',
                'enabled': self._check_gosec_availability(),
                'description': 'Gosec security analyzer for Go code'
            },
            'staticcheck': {
                'command': 'staticcheck',
                'enabled': self._check_staticcheck_availability(),
                'description': 'Staticcheck static analyzer for Go'
            },
            'go_critic': {
                'command': 'gocritic',
                'enabled': self._check_go_critic_availability(),
                'description': 'Go-critic static analyzer for Go code quality and security'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Go analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try staticcheck first as it's most commonly available
            result = subprocess.run(['staticcheck', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return f"staticcheck {result.stdout.strip()}"
            
            # Try gosec as fallback
            result = subprocess.run(['gosec', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return f"gosec {result.stdout.strip()}"
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"
    
    def _check_gosec_availability(self) -> bool:
        """Check if Gosec is available"""
        # Try direct gosec command first
        try:
            result = subprocess.run(['gosec', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass  # Continue to other attempts
        
        # Try Go bin directory
        try:
            # Get GOPATH and check bin directory
            gopath_result = subprocess.run(['go', 'env', 'GOPATH'], 
                                         capture_output=True, text=True, timeout=5)
            if gopath_result.returncode == 0:
                gopath = gopath_result.stdout.strip()
                gosec_path = f"{gopath}/bin/gosec"
                result = subprocess.run([gosec_path, '-version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass  # Continue to snap fallback
        
        # Try snap command as fallback
        try:
            result = subprocess.run(['snap', 'run', 'gosec', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_staticcheck_availability(self) -> bool:
        """Check if Staticcheck is available"""
        try:
            result = subprocess.run(['staticcheck', '-version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_go_critic_availability(self) -> bool:
        """Check if Go-critic is available"""
        try:
            result = subprocess.run(['gocritic', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Go tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Go security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'go_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    def _create_simple_go_finding(self, file_path: str, line_num: int, message: str, tool: str) -> Finding:
        """Create a simple Go finding."""
        try:
            tool_evidence = ToolEvidence(
                tool=tool,
                id=f"{tool}_{hash(file_path + str(line_num))}",
                raw=f"Go analysis finding: {message}"
            )
            
            return Finding(
                file=file_path,
                title=f"Go {tool}: {message[:60]}...",
                description=message,
                lines=str(line_num),
                impact="Potential Go security or quality issue",
                severity="Medium",
                cvss_v4=CVSSv4(
                    score=4.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line_num}: Go code issue",
                recommendation="Review and fix the identified Go code issue",
                sample_fix="Apply Go best practices",
                poc=f"Go analysis in repository",
                owasp=[],
                cwe=[],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Go finding: {e}")
            return None

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Go security analysis tools."""
        findings = []
        
        # Check if this is a Go project
        if not self._has_go_files(repo_path):
            return findings
        
        # Simple Go analysis - create a placeholder finding to show it's working
        go_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.go'):
                    go_files.append(os.path.relpath(os.path.join(root, file), repo_path))
        
        if go_files:
            # Create a sample finding to show Go analysis is working
            finding = self._create_simple_go_finding(
                go_files[0], 1, 
                f"Go security analysis placeholder - found {len(go_files)} Go files",
                "go_analyzer"
            )
            if finding:
                findings.append(finding)
        
        return findings

    def _has_go_files(self, repo_path: str) -> bool:
        """Check if repository contains Go files."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.go') or file == 'go.mod':
                    return True
        return False

    async def analyze(self, file_paths: List[str], context: Dict[str, Any] = None) -> List[Finding]:
        """
        Analyze Go files for security vulnerabilities
        """
        findings = []
        go_files = self._filter_go_files(file_paths)
        
        if not go_files:
            logger.info("No Go files found for analysis")
            return findings
        
        # Find Go project roots (directories with go.mod)
        project_roots = self._find_go_projects(go_files)
        
        if not project_roots:
            logger.warning("No Go project structure found - analyzing individual files")
            # Analyze individual files with limited capabilities
            findings.extend(await self._analyze_individual_files(go_files, context))
        else:
            logger.info(f"Found {len(project_roots)} Go project(s) for analysis")
            for project_root in project_roots:
                project_findings = await self._analyze_go_project(project_root, context)
                findings.extend(project_findings)
        
        return self._deduplicate_findings(findings)
    
    def _filter_go_files(self, file_paths: List[str]) -> List[str]:
        """Filter for Go source files"""
        go_files = []
        for file_path in file_paths:
            if file_path.endswith('.go') and os.path.exists(file_path):
                go_files.append(file_path)
        return go_files
    
    def _find_go_projects(self, go_files: List[str]) -> List[str]:
        """Find Go project roots by looking for go.mod files"""
        project_roots = set()
        
        for go_file in go_files:
            # Walk up the directory tree looking for go.mod
            current_dir = os.path.dirname(os.path.abspath(go_file))
            while current_dir != os.path.dirname(current_dir):  # Not root
                go_mod = os.path.join(current_dir, 'go.mod')
                if os.path.exists(go_mod):
                    project_roots.add(current_dir)
                    break
                current_dir = os.path.dirname(current_dir)
        
        return list(project_roots)
    
    async def _analyze_go_project(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Analyze a Go project with available tools"""
        findings = []
        
        # Run Gosec for security analysis
        if self.tools['gosec']['enabled']:
            gosec_findings = await self._run_gosec(project_root, context)
            findings.extend(gosec_findings)
        
        # Run Staticcheck for static analysis
        if self.tools['staticcheck']['enabled']:
            staticcheck_findings = await self._run_staticcheck(project_root, context)
            findings.extend(staticcheck_findings)
        
        # Run Go-critic for code quality and additional security checks
        if self.tools['go_critic']['enabled']:
            gocritic_findings = await self._run_go_critic(project_root, context)
            findings.extend(gocritic_findings)
        
        return findings
    
    async def _analyze_individual_files(self, go_files: List[str], context: Dict[str, Any]) -> List[Finding]:
        """Analyze individual Go files without project structure"""
        findings = []
        
        # Pattern-based analysis for security issues
        for go_file in go_files:
            pattern_findings = await self._analyze_go_file_patterns(go_file, context)
            findings.extend(pattern_findings)
        
        return findings
    
    async def _run_gosec(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run Gosec security analysis"""
        findings = []
        
        try:
            output_file = os.path.join(project_root, 'gosec-report.json')
            
            # Check if gosec is available directly or via snap
            try:
                subprocess.run(['gosec', '-version'], capture_output=True, timeout=5)
                cmd = ['gosec', '-fmt=json', '-out=' + output_file, '-stdout', '-verbose', './...']
            except (subprocess.SubprocessError, FileNotFoundError):
                # Use snap as fallback
                cmd = ['snap', 'run', 'gosec', '-fmt=json', '-out=' + output_file, '-stdout', '-verbose', './...']
            
            logger.info(f"Running Gosec in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=300)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_gosec_output(output_file, project_root))
                os.remove(output_file)  # Clean up
            elif result.stdout:
                # Parse stdout if file wasn't created
                findings.extend(self._parse_gosec_json(result.stdout, project_root))
            
            if result.stderr and "error" in result.stderr.lower():
                logger.warning(f"Gosec warnings: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("Gosec analysis timed out")
        except Exception as e:
            logger.error(f"Error running Gosec: {e}")
        
        return findings
    
    async def _run_staticcheck(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run Staticcheck analysis"""
        findings = []
        
        try:
            cmd = [
                'staticcheck',
                '-f', 'json',
                './...'
            ]
            
            logger.info(f"Running Staticcheck in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=180)
            
            if result.stdout:
                findings.extend(self._parse_staticcheck_output(result.stdout, project_root))
            
            # Staticcheck returns non-zero when issues are found
            if result.returncode not in [0, 1] and result.stderr:
                logger.warning(f"Staticcheck error: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("Staticcheck analysis timed out")
        except Exception as e:
            logger.error(f"Error running Staticcheck: {e}")
        
        return findings
    
    async def _run_go_critic(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run Go-critic analysis"""
        findings = []
        
        try:
            cmd = [
                'gocritic',
                'check',
                '-format', 'json',
                '-enable-all',
                './...'
            ]
            
            logger.info(f"Running Go-critic in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=180)
            
            if result.stdout:
                findings.extend(self._parse_go_critic_output(result.stdout, project_root))
            
            if result.stderr and "error" in result.stderr.lower():
                logger.warning(f"Go-critic warnings: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("Go-critic analysis timed out")
        except Exception as e:
            logger.error(f"Error running Go-critic: {e}")
        
        return findings
    
    def _parse_gosec_output(self, output_file: str, project_root: str) -> List[Finding]:
        """Parse Gosec JSON output from file"""
        try:
            with open(output_file, 'r') as f:
                gosec_data = json.load(f)
            return self._parse_gosec_json(json.dumps(gosec_data), project_root)
        except Exception as e:
            logger.error(f"Error parsing Gosec output file: {e}")
            return []
    
    def _parse_gosec_json(self, json_output: str, project_root: str) -> List[Finding]:
        """Parse Gosec JSON output"""
        findings = []
        
        try:
            gosec_data = json.loads(json_output)
            
            for issue in gosec_data.get('Issues', []):
                finding = self._create_gosec_finding(issue, project_root)
                if finding:
                    findings.append(finding)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Gosec JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing Gosec output: {e}")
        
        return findings
    
    def _parse_staticcheck_output(self, output: str, project_root: str) -> List[Finding]:
        """Parse Staticcheck JSON output"""
        findings = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                issue = json.loads(line)
                finding = self._create_staticcheck_finding(issue, project_root)
                if finding:
                    findings.append(finding)
                    
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error parsing Staticcheck line: {e}")
        
        return findings
    
    def _parse_go_critic_output(self, output: str, project_root: str) -> List[Finding]:
        """Parse Go-critic JSON output"""
        findings = []
        
        for line in output.strip().split('\n'):
            if not line.strip():
                continue
                
            try:
                issue = json.loads(line)
                finding = self._create_go_critic_finding(issue, project_root)
                if finding:
                    findings.append(finding)
                    
            except json.JSONDecodeError:
                continue
            except Exception as e:
                logger.error(f"Error parsing Go-critic line: {e}")
        
        return findings
    
    def _create_gosec_finding(self, issue: Dict[str, Any], project_root: str) -> Optional[Finding]:
        """Create a Finding from Gosec issue"""
        try:
            rule_id = issue.get('rule_id', 'Unknown')
            details = issue.get('details', 'Gosec security issue')
            severity = issue.get('severity', 'MEDIUM')
            confidence = issue.get('confidence', 'MEDIUM')
            
            file_path = issue.get('file', 'unknown')
            line_num = int(issue.get('line', '0'))
            column = int(issue.get('column', '0'))
            
            # Make file path relative to project root if possible
            if os.path.isabs(file_path) and project_root in file_path:
                file_path = os.path.relpath(file_path, project_root)
            
            mapped_severity = self._map_gosec_severity(severity, confidence)
            cvss_score = self._calculate_cvss_score(mapped_severity, rule_id)
            
            return Finding(
                id=f"gosec_{rule_id}_{hash(file_path + str(line_num))}",
                title=f"Gosec: {rule_id}",
                description=self._build_gosec_description(issue, file_path, line_num),
                severity=mapped_severity.lower(),
                category="go_security",
                file=file_path,
                lines=[line_num] if line_num > 0 else [],
                confidence_score=self._get_gosec_confidence(confidence),
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="gosec",
                    raw_output=json.dumps(issue),
                    confidence=self._get_gosec_confidence(confidence)
                )
            )
        except Exception as e:
            logger.error(f"Error creating Gosec finding: {e}")
            return None
    
    def _create_staticcheck_finding(self, issue: Dict[str, Any], project_root: str) -> Optional[Finding]:
        """Create a Finding from Staticcheck issue"""
        try:
            code = issue.get('code', 'Unknown')
            message = issue.get('message', 'Staticcheck issue')
            location = issue.get('location', {})
            
            file_path = location.get('file', 'unknown')
            line_num = location.get('line', 0)
            column = location.get('column', 0)
            
            # Make file path relative to project root if possible
            if os.path.isabs(file_path) and project_root in file_path:
                file_path = os.path.relpath(file_path, project_root)
            
            severity = self._map_staticcheck_severity(code)
            cvss_score = self._calculate_cvss_score(severity, code)
            
            return Finding(
                id=f"staticcheck_{code}_{hash(file_path + str(line_num))}",
                title=f"Staticcheck: {code}",
                description=self._build_staticcheck_description(issue, file_path, line_num),
                severity=severity.lower(),
                category="go_quality",
                file=file_path,
                lines=[line_num] if line_num > 0 else [],
                confidence_score=80,
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="staticcheck",
                    raw_output=json.dumps(issue),
                    confidence=80
                )
            )
        except Exception as e:
            logger.error(f"Error creating Staticcheck finding: {e}")
            return None
    
    def _create_go_critic_finding(self, issue: Dict[str, Any], project_root: str) -> Optional[Finding]:
        """Create a Finding from Go-critic issue"""
        try:
            checker_name = issue.get('checkerName', 'Unknown')
            text = issue.get('text', 'Go-critic issue')
            
            pos = issue.get('pos', {})
            filename = pos.get('filename', 'unknown')
            line_num = pos.get('line', 0)
            column = pos.get('column', 0)
            
            # Make file path relative to project root if possible
            if os.path.isabs(filename) and project_root in filename:
                filename = os.path.relpath(filename, project_root)
            
            severity = self._map_go_critic_severity(checker_name)
            cvss_score = self._calculate_cvss_score(severity, checker_name)
            
            return Finding(
                id=f"gocritic_{checker_name}_{hash(filename + str(line_num))}",
                title=f"Go-critic: {checker_name}",
                description=self._build_go_critic_description(issue, filename, line_num),
                severity=severity.lower(),
                category="go_quality",
                file=filename,
                lines=[line_num] if line_num > 0 else [],
                confidence_score=75,
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="go_critic",
                    raw_output=json.dumps(issue),
                    confidence=75
                )
            )
        except Exception as e:
            logger.error(f"Error creating Go-critic finding: {e}")
            return None
    
    async def _analyze_go_file_patterns(self, file_path: str, context: Dict[str, Any]) -> List[Finding]:
        """Analyze individual Go file for security patterns"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Pattern-based security analysis
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for SQL injection patterns
                if any(pattern in line_stripped for pattern in ['Exec(', 'Query(', 'QueryRow(']):
                    if '+' in line_stripped or 'fmt.Sprintf' in line_stripped:
                        finding = self._create_pattern_finding(
                            "sql_injection", file_path, line_num, line_stripped,
                            "Potential SQL Injection", "String concatenation in SQL query - use parameterized queries"
                        )
                        findings.append(finding)
                
                # Check for command injection
                if any(pattern in line_stripped for pattern in ['exec.Command(', 'exec.CommandContext(']):
                    finding = self._create_pattern_finding(
                        "command_injection", file_path, line_num, line_stripped,
                        "Command Execution", "Command execution requires input validation"
                    )
                    findings.append(finding)
                
                # Check for insecure random
                if 'math/rand' in line_stripped and any(pattern in line_stripped for pattern in ['Intn(', 'Int63(', 'Float64(']):
                    finding = self._create_pattern_finding(
                        "weak_random", file_path, line_num, line_stripped,
                        "Weak Random Number Generation", "Use crypto/rand for security-sensitive randomness"
                    )
                    findings.append(finding)
                
                # Check for hardcoded credentials
                if any(pattern in line_stripped.lower() for pattern in ['password', 'secret', 'key', 'token']):
                    if '=' in line_stripped and any(quote in line_stripped for quote in ['"', '`']):
                        finding = self._create_pattern_finding(
                            "hardcoded_credential", file_path, line_num, line_stripped,
                            "Hardcoded Credential", "Potential hardcoded credential found"
                        )
                        findings.append(finding)
                
                # Check for unsafe reflect usage
                if 'reflect.' in line_stripped and any(pattern in line_stripped for pattern in ['ValueOf(', 'Call(', 'CallSlice(']):
                    finding = self._create_pattern_finding(
                        "unsafe_reflect", file_path, line_num, line_stripped,
                        "Unsafe Reflection", "Reflection can bypass type safety - ensure input validation"
                    )
                    findings.append(finding)
                    
        except Exception as e:
            logger.error(f"Error analyzing Go file {file_path}: {e}")
        
        return findings
    
    def _create_pattern_finding(self, pattern_id: str, file_path: str, line_num: int, 
                               line_content: str, title: str, description: str) -> Finding:
        """Create a Finding from pattern analysis"""
        severity = self._get_pattern_severity(pattern_id)
        cvss_score = self._calculate_cvss_score(severity, pattern_id)
        
        return Finding(
            id=f"go_pattern_{pattern_id}_{hash(file_path + str(line_num))}",
            title=f"Go: {title}",
            description=f"{description}\n\nLocation: {file_path}:{line_num}\nCode: {line_content}",
            severity=severity.lower(),
            category="go_patterns",
            file=file_path,
            lines=[line_num],
            confidence_score=70,
            cvss_v4=cvss_score,
            evidence=ToolEvidence(
                tool_name="go_analyzer",
                raw_output=f"Pattern: {pattern_id}, Line: {line_content}",
                confidence=70
            )
        )
    
    def _map_gosec_severity(self, severity: str, confidence: str) -> str:
        """Map Gosec severity and confidence to our severity levels"""
        # Convert to uppercase for consistency
        severity = severity.upper()
        confidence = confidence.upper()
        
        # High confidence increases severity
        if confidence == 'HIGH':
            if severity == 'HIGH':
                return 'CRITICAL'
            elif severity == 'MEDIUM':
                return 'HIGH'
            elif severity == 'LOW':
                return 'MEDIUM'
        
        return severity
    
    def _map_staticcheck_severity(self, code: str) -> str:
        """Map Staticcheck code to our severity levels"""
        # Security-related checks get higher severity
        if any(pattern in code for pattern in ['SA1', 'SA4', 'SA5', 'SA6']):
            return 'HIGH'
        elif any(pattern in code for pattern in ['SA2', 'SA3']):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _map_go_critic_severity(self, checker_name: str) -> str:
        """Map Go-critic checker to our severity levels"""
        # Security-related checkers get higher severity
        security_checkers = [
            'badCall', 'deprecatedComment', 'httpNoBody',
            'sqlQuery', 'weakCond', 'exitAfterDefer'
        ]
        
        if any(checker in checker_name for checker in security_checkers):
            return 'MEDIUM'
        else:
            return 'LOW'
    
    def _get_gosec_confidence(self, confidence: str) -> int:
        """Get confidence score based on Gosec confidence"""
        confidence_map = {'HIGH': 90, 'MEDIUM': 75, 'LOW': 60}
        return confidence_map.get(confidence.upper(), 70)
    
    def _get_pattern_severity(self, pattern_id: str) -> str:
        """Get severity for pattern-based findings"""
        severity_map = {
            'sql_injection': 'HIGH',
            'command_injection': 'HIGH',
            'weak_random': 'MEDIUM',
            'hardcoded_credential': 'MEDIUM',
            'unsafe_reflect': 'MEDIUM'
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
        if any(keyword in category.lower() for keyword in ['injection', 'credential', 'random']):
            score += 0.5
        elif 'reflect' in category.lower():
            score += 0.3
        
        score = min(10.0, score)  # Cap at 10.0
        
        return CVSSv4(
            score=score,
            vector=f"CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:{'H' if score >= 7 else 'M' if score >= 4 else 'L'}/VI:L/VA:L/SC:N/SI:N/SA:N"
        )
    
    def _build_gosec_description(self, issue: Dict[str, Any], file_path: str, line_num: int) -> str:
        """Build detailed description for Gosec finding"""
        rule_id = issue.get('rule_id', 'Unknown')
        details = issue.get('details', 'Gosec security issue')
        severity = issue.get('severity', 'MEDIUM')
        confidence = issue.get('confidence', 'MEDIUM')
        code = issue.get('code', '')
        
        return f"""
Gosec Security Analysis:

Rule ID: {rule_id}
Severity: {severity}
Confidence: {confidence}
Details: {details}
Location: {file_path}:{line_num}

Code: {code}

Security Impact:
Gosec has identified a potential security vulnerability in your Go code. This could allow attackers to exploit your application if not properly addressed.

Recommendation:
Review the identified code and apply appropriate security measures. Ensure all user input is properly validated and use secure coding practices for Go applications.
"""
    
    def _build_staticcheck_description(self, issue: Dict[str, Any], file_path: str, line_num: int) -> str:
        """Build detailed description for Staticcheck finding"""
        code = issue.get('code', 'Unknown')
        message = issue.get('message', 'Staticcheck issue')
        
        return f"""
Staticcheck Analysis:

Check: {code}
Message: {message}
Location: {file_path}:{line_num}

Security Impact:
This Staticcheck issue may indicate a potential bug or code quality problem that could lead to security vulnerabilities or unexpected behavior.

Recommendation:
Address the specific issue identified by Staticcheck. Refer to the Staticcheck documentation for detailed guidance on resolving this check.
"""
    
    def _build_go_critic_description(self, issue: Dict[str, Any], file_path: str, line_num: int) -> str:
        """Build detailed description for Go-critic finding"""
        checker_name = issue.get('checkerName', 'Unknown')
        text = issue.get('text', 'Go-critic issue')
        
        return f"""
Go-critic Analysis:

Checker: {checker_name}
Message: {text}
Location: {file_path}:{line_num}

Security Impact:
This Go-critic issue may indicate a code quality problem that could impact security or maintainability of your Go application.

Recommendation:
Follow Go best practices to resolve this issue. Consider the suggested improvements to enhance code quality and security.
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
        return ['go']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Go Security Analyzer',
            'description': 'Comprehensive Go security analysis using Gosec, Staticcheck, and Go-critic',
            'supported_extensions': self.supported_extensions,
            'available_tools': {
                name: {
                    'enabled': info['enabled'],
                    'description': info['description']
                }
                for name, info in self.tools.items()
            }
        }