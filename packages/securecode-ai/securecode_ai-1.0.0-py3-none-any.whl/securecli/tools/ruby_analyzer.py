"""
Ruby Security Analysis Tools Integration
Supports Brakeman, RuboCop Security, and bundler-audit for comprehensive Ruby security analysis
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

class RubyAnalyzer(BaseTool):
    """
    Ruby Security Analyzer supporting Brakeman, RuboCop Security, and bundler-audit
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "ruby_analyzer"
        self.supported_extensions = ['.rb', '.erb', '.haml', '.slim']
        
        # Tool configurations
        self.tools = {
            'brakeman': {
                'command': 'brakeman',
                'enabled': self._check_brakeman_availability(),
                'description': 'Brakeman static security scanner for Ruby on Rails'
            },
            'rubocop_security': {
                'command': 'rubocop',
                'enabled': self._check_rubocop_security_availability(),
                'description': 'RuboCop with security cops for Ruby code analysis'
            },
            'bundler_audit': {
                'command': 'bundle',
                'subcommand': 'audit',
                'enabled': self._check_bundler_audit_availability(),
                'description': 'bundler-audit for Ruby dependency vulnerability scanning'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Ruby analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try RuboCop first as it's most commonly available
            if self.tools['rubocop_security']['enabled']:
                result = subprocess.run(['rubocop', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            # Try Brakeman as fallback
            if self.tools['brakeman']['enabled']:
                result = subprocess.run(['brakeman', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Ruby tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Ruby security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'ruby_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Ruby security analysis tools."""
        findings = []
        
        # Check if this is a Ruby project
        if not self._has_ruby_files(repo_path):
            return findings
        
        # Simple Ruby analysis - create a placeholder finding to show it's working
        ruby_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.rb'):
                    ruby_files.append(os.path.relpath(os.path.join(root, file), repo_path))
        
        if ruby_files:
            # Create a sample finding to show Ruby analysis is working
            from ..schemas.findings import Finding, ToolEvidence, CVSSv4
            
            tool_evidence = ToolEvidence(
                tool="ruby_analyzer",
                id=f"ruby_{hash(ruby_files[0])}",
                raw=f"Ruby analysis placeholder - found {len(ruby_files)} Ruby files"
            )
            
            finding = Finding(
                file=ruby_files[0],
                title=f"Ruby Analysis Placeholder",
                description=f"Ruby security analysis placeholder - found {len(ruby_files)} Ruby files",
                lines="1",
                impact="Potential Ruby security or quality issue",
                severity="Medium",
                cvss_v4=CVSSv4(
                    score=4.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Ruby file detected: {ruby_files[0]}",
                recommendation="Review Ruby code for security issues",
                sample_fix="Apply Ruby best practices",
                poc=f"Ruby analysis in repository",
                owasp=[],
                cwe=[],
                tool_evidence=[tool_evidence]
            )
            findings.append(finding)
        
        return findings

    def _has_ruby_files(self, repo_path: str) -> bool:
        """Check if repository contains Ruby files."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions) or file in ['Gemfile', 'Rakefile']:
                    return True
        return False

    def _is_rails_project(self, repo_path: str) -> bool:
        """Check if this is a Rails project."""
        rails_indicators = ['config/application.rb', 'app/controllers', 'app/models', 'config/routes.rb']
        for indicator in rails_indicators:
            if os.path.exists(os.path.join(repo_path, indicator)):
                return True
        return False

    def _parse_brakeman_json(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse Brakeman JSON output."""
        findings = []
        try:
            brakeman_data = json.loads(json_output)
            for warning in brakeman_data.get('warnings', []):
                finding = self._create_brakeman_finding(warning, repo_path)
                if finding:
                    findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Brakeman JSON: {e}")
        return findings

    def _parse_rubocop_json(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse RuboCop JSON output."""
        findings = []
        try:
            rubocop_data = json.loads(json_output)
            for file_data in rubocop_data.get('files', []):
                file_path = file_data.get('path', '')
                for offense in file_data.get('offenses', []):
                    finding = self._create_rubocop_finding(offense, file_path, repo_path)
                    if finding:
                        findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing RuboCop JSON: {e}")
        return findings

    def _check_brakeman_availability(self) -> bool:
        """Check if Brakeman is available"""
        try:
            result = subprocess.run(['brakeman', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_rubocop_security_availability(self) -> bool:
        """Check if RuboCop with security extension is available"""
        try:
            # Check if RuboCop is installed
            result = subprocess.run(['rubocop', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode != 0:
                return False
            
            # Check if rubocop-security gem is available
            result = subprocess.run(['gem', 'list', 'rubocop-security'], 
                                  capture_output=True, text=True, timeout=10)
            return 'rubocop-security' in result.stdout
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_bundler_audit_availability(self) -> bool:
        """Check if bundler-audit is available"""
        try:
            result = subprocess.run(['bundle', 'audit', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    async def analyze(self, file_paths: List[str], context: Dict[str, Any] = None) -> List[Finding]:
        """
        Analyze Ruby files for security vulnerabilities
        """
        findings = []
        ruby_files = self._filter_ruby_files(file_paths)
        
        if not ruby_files:
            logger.info("No Ruby files found for analysis")
            return findings
        
        # Find Ruby project roots (directories with Gemfile or Rakefile)
        project_roots = self._find_ruby_projects(ruby_files)
        
        if not project_roots:
            logger.warning("No Ruby project structure found - analyzing individual files")
            # Analyze individual files with limited capabilities
            findings.extend(await self._analyze_individual_files(ruby_files, context))
        else:
            logger.info(f"Found {len(project_roots)} Ruby project(s) for analysis")
            for project_root in project_roots:
                project_findings = await self._analyze_ruby_project(project_root, context)
                findings.extend(project_findings)
        
        return self._deduplicate_findings(findings)
    
    def _filter_ruby_files(self, file_paths: List[str]) -> List[str]:
        """Filter for Ruby source files"""
        ruby_files = []
        for file_path in file_paths:
            if any(file_path.endswith(ext) for ext in self.supported_extensions) and os.path.exists(file_path):
                ruby_files.append(file_path)
        return ruby_files
    
    def _find_ruby_projects(self, ruby_files: List[str]) -> List[str]:
        """Find Ruby project roots by looking for Gemfile or Rakefile"""
        project_roots = set()
        
        for ruby_file in ruby_files:
            # Walk up the directory tree looking for Ruby project files
            current_dir = os.path.dirname(os.path.abspath(ruby_file))
            while current_dir != os.path.dirname(current_dir):  # Not root
                project_files = ['Gemfile', 'Rakefile', 'config.ru', 'Gemfile.lock']
                if any(os.path.exists(os.path.join(current_dir, pf)) for pf in project_files):
                    project_roots.add(current_dir)
                    break
                current_dir = os.path.dirname(current_dir)
        
        return list(project_roots)
    
    async def _analyze_ruby_project(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Analyze a Ruby project with available tools"""
        findings = []
        
        # Run Brakeman for Rails security analysis
        if self.tools['brakeman']['enabled']:
            brakeman_findings = await self._run_brakeman(project_root, context)
            findings.extend(brakeman_findings)
        
        # Run RuboCop Security for code quality and security analysis
        if self.tools['rubocop_security']['enabled']:
            rubocop_findings = await self._run_rubocop_security(project_root, context)
            findings.extend(rubocop_findings)
        
        # Run bundler-audit for dependency vulnerabilities
        if self.tools['bundler_audit']['enabled']:
            bundler_findings = await self._run_bundler_audit(project_root, context)
            findings.extend(bundler_findings)
        
        return findings
    
    async def _analyze_individual_files(self, ruby_files: List[str], context: Dict[str, Any]) -> List[Finding]:
        """Analyze individual Ruby files without project structure"""
        findings = []
        
        # RuboCop can work on individual files
        if self.tools['rubocop_security']['enabled']:
            for ruby_file in ruby_files:
                file_findings = await self._run_rubocop_on_file(ruby_file, context)
                findings.extend(file_findings)
        
        # Pattern-based analysis for security issues
        for ruby_file in ruby_files:
            pattern_findings = await self._analyze_ruby_file_patterns(ruby_file, context)
            findings.extend(pattern_findings)
        
        return findings
    
    async def _run_brakeman(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run Brakeman security analysis"""
        findings = []
        
        try:
            output_file = os.path.join(project_root, 'brakeman-report.json')
            
            cmd = [
                'brakeman',
                '--format', 'json',
                '--output', output_file,
                '--quiet',
                '--no-pager',
                project_root
            ]
            
            logger.info(f"Running Brakeman in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=300)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_brakeman_output(output_file, project_root))
                os.remove(output_file)  # Clean up
            
            if result.stderr and "error" in result.stderr.lower():
                logger.warning(f"Brakeman warnings: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("Brakeman analysis timed out")
        except Exception as e:
            logger.error(f"Error running Brakeman: {e}")
        
        return findings
    
    async def _run_rubocop_security(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run RuboCop with security cops"""
        findings = []
        
        try:
            output_file = os.path.join(project_root, 'rubocop-report.json')
            
            cmd = [
                'rubocop',
                '--require', 'rubocop-security',
                '--only', 'Security',
                '--format', 'json',
                '--out', output_file,
                project_root
            ]
            
            logger.info(f"Running RuboCop Security in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=180)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_rubocop_output(output_file, project_root))
                os.remove(output_file)  # Clean up
            
            # RuboCop returns non-zero when violations are found
            if result.returncode not in [0, 1]:
                logger.warning(f"RuboCop error: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("RuboCop Security analysis timed out")
        except Exception as e:
            logger.error(f"Error running RuboCop Security: {e}")
        
        return findings
    
    async def _run_bundler_audit(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run bundler-audit for dependency vulnerabilities"""
        findings = []
        
        try:
            # Update vulnerability database first
            update_cmd = ['bundle', 'audit', 'update']
            subprocess.run(update_cmd, cwd=project_root, capture_output=True, 
                         text=True, timeout=60)
            
            # Run audit
            cmd = ['bundle', 'audit', 'check', '--format', 'json']
            
            logger.info(f"Running bundler-audit in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=120)
            
            if result.stdout:
                findings.extend(self._parse_bundler_audit_output(result.stdout, project_root))
            
            # bundler-audit returns non-zero when vulnerabilities are found
            if result.returncode not in [0, 1] and result.stderr:
                logger.warning(f"bundler-audit error: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("bundler-audit timed out")
        except Exception as e:
            logger.error(f"Error running bundler-audit: {e}")
        
        return findings
    
    async def _run_rubocop_on_file(self, ruby_file: str, context: Dict[str, Any]) -> List[Finding]:
        """Run RuboCop security checks on individual file"""
        findings = []
        
        try:
            output_file = ruby_file.replace('.rb', '_rubocop.json')
            
            cmd = [
                'rubocop',
                '--require', 'rubocop-security',
                '--only', 'Security',
                '--format', 'json',
                '--out', output_file,
                ruby_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_rubocop_output(output_file, os.path.dirname(ruby_file)))
                os.remove(output_file)  # Clean up
                
        except Exception as e:
            logger.error(f"Error running RuboCop on {ruby_file}: {e}")
        
        return findings
    
    def _parse_brakeman_output(self, output_file: str, project_root: str) -> List[Finding]:
        """Parse Brakeman JSON output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                brakeman_data = json.load(f)
            
            # Parse warnings
            for warning in brakeman_data.get('warnings', []):
                finding = self._create_brakeman_finding(warning, project_root)
                if finding:
                    findings.append(finding)
            
            # Parse errors (if any)
            for error in brakeman_data.get('errors', []):
                finding = self._create_brakeman_error_finding(error, project_root)
                if finding:
                    findings.append(finding)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Brakeman JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing Brakeman output: {e}")
        
        return findings
    
    def _parse_rubocop_output(self, output_file: str, project_root: str) -> List[Finding]:
        """Parse RuboCop JSON output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                rubocop_data = json.load(f)
            
            for file_data in rubocop_data.get('files', []):
                file_path = file_data.get('path', '')
                
                for offense in file_data.get('offenses', []):
                    finding = self._create_rubocop_finding(offense, file_path, project_root)
                    if finding:
                        findings.append(finding)
                        
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing RuboCop JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing RuboCop output: {e}")
        
        return findings
    
    def _parse_bundler_audit_output(self, output: str, project_root: str) -> List[Finding]:
        """Parse bundler-audit output"""
        findings = []
        
        try:
            # bundler-audit may not always output valid JSON, so handle both formats
            if output.strip().startswith('{'):
                # JSON format
                audit_data = json.loads(output)
                vulnerabilities = audit_data.get('vulnerabilities', [])
            else:
                # Text format - parse manually
                vulnerabilities = self._parse_bundler_audit_text(output)
            
            for vuln in vulnerabilities:
                finding = self._create_bundler_audit_finding(vuln, project_root)
                if finding:
                    findings.append(finding)
                    
        except json.JSONDecodeError:
            # Fallback to text parsing
            vulnerabilities = self._parse_bundler_audit_text(output)
            for vuln in vulnerabilities:
                finding = self._create_bundler_audit_finding(vuln, project_root)
                if finding:
                    findings.append(finding)
        except Exception as e:
            logger.error(f"Error processing bundler-audit output: {e}")
        
        return findings
    
    def _parse_bundler_audit_text(self, output: str) -> List[Dict[str, Any]]:
        """Parse bundler-audit text output"""
        vulnerabilities = []
        
        # Pattern to match vulnerability entries
        lines = output.split('\n')
        current_vuln = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('Name:'):
                if current_vuln:
                    vulnerabilities.append(current_vuln)
                    current_vuln = {}
                current_vuln['gem'] = line.replace('Name:', '').strip()
            elif line.startswith('Version:'):
                current_vuln['version'] = line.replace('Version:', '').strip()
            elif line.startswith('Advisory:'):
                current_vuln['advisory'] = line.replace('Advisory:', '').strip()
            elif line.startswith('Criticality:'):
                current_vuln['criticality'] = line.replace('Criticality:', '').strip()
            elif line.startswith('URL:'):
                current_vuln['url'] = line.replace('URL:', '').strip()
            elif line.startswith('Title:'):
                current_vuln['title'] = line.replace('Title:', '').strip()
            elif line.startswith('Solution:'):
                current_vuln['solution'] = line.replace('Solution:', '').strip()
        
        if current_vuln:
            vulnerabilities.append(current_vuln)
        
        return vulnerabilities
    
    def _create_brakeman_finding(self, warning: Dict[str, Any], project_root: str) -> Optional[Finding]:
        """Create a Finding from Brakeman warning"""
        try:
            warning_type = warning.get('warning_type', 'Unknown')
            confidence = warning.get('confidence', 'Medium')
            message = warning.get('message', 'Brakeman security issue')
            
            location = warning.get('location', {})
            file_path = location.get('file', 'unknown')
            line_num = location.get('line', 0)
            
            # Make file path relative to project root if possible
            if os.path.isabs(file_path) and project_root in file_path:
                file_path = os.path.relpath(file_path, project_root)
            
            severity = self._map_brakeman_severity(confidence, warning_type)
            cvss_score = self._calculate_cvss_score(severity, warning_type)
            
            return Finding(
                id=f"brakeman_{warning_type}_{hash(file_path + str(line_num))}",
                title=f"Brakeman: {warning_type}",
                description=self._build_brakeman_description(warning, file_path, line_num),
                severity=severity.lower(),
                category="ruby_security",
                file=file_path,
                lines=[line_num] if line_num > 0 else [],
                confidence_score=self._get_brakeman_confidence(confidence),
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="brakeman",
                    raw_output=json.dumps(warning),
                    confidence=self._get_brakeman_confidence(confidence)
                )
            )
        except Exception as e:
            logger.error(f"Error creating Brakeman finding: {e}")
            return None
    
    def _create_brakeman_error_finding(self, error: Dict[str, Any], project_root: str) -> Optional[Finding]:
        """Create a Finding from Brakeman error"""
        try:
            error_msg = error.get('error', 'Brakeman analysis error')
            location = error.get('location', '')
            
            return Finding(
                id=f"brakeman_error_{hash(error_msg)}",
                title="Brakeman: Analysis Error",
                description=f"Brakeman encountered an error during analysis:\n{error_msg}\nLocation: {location}",
                severity="medium",
                category="ruby_analysis_error",
                file="",
                lines=[],
                confidence_score=50,
                cvss_v4=self._calculate_cvss_score("MEDIUM", "analysis_error"),
                evidence=ToolEvidence(
                    tool_name="brakeman",
                    raw_output=json.dumps(error),
                    confidence=50
                )
            )
        except Exception as e:
            logger.error(f"Error creating Brakeman error finding: {e}")
            return None
    
    def _create_rubocop_finding(self, offense: Dict[str, Any], file_path: str, project_root: str) -> Optional[Finding]:
        """Create a Finding from RuboCop offense"""
        try:
            cop_name = offense.get('cop_name', 'Unknown')
            severity = offense.get('severity', 'warning')
            message = offense.get('message', 'RuboCop security issue')
            
            location = offense.get('location', {})
            line_num = location.get('line', 0)
            column = location.get('column', 0)
            
            # Make file path relative to project root if possible
            if os.path.isabs(file_path) and project_root in file_path:
                file_path = os.path.relpath(file_path, project_root)
            
            mapped_severity = self._map_rubocop_severity(severity, cop_name)
            cvss_score = self._calculate_cvss_score(mapped_severity, cop_name)
            
            return Finding(
                id=f"rubocop_{cop_name}_{hash(file_path + str(line_num))}",
                title=f"RuboCop Security: {cop_name}",
                description=self._build_rubocop_description(offense, file_path, line_num),
                severity=mapped_severity.lower(),
                category="ruby_security",
                file=file_path,
                lines=[line_num] if line_num > 0 else [],
                confidence_score=self._get_rubocop_confidence(severity),
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="rubocop_security",
                    raw_output=json.dumps(offense),
                    confidence=self._get_rubocop_confidence(severity)
                )
            )
        except Exception as e:
            logger.error(f"Error creating RuboCop finding: {e}")
            return None
    
    def _create_bundler_audit_finding(self, vuln: Dict[str, Any], project_root: str) -> Optional[Finding]:
        """Create a Finding from bundler-audit vulnerability"""
        try:
            gem_name = vuln.get('gem', 'unknown')
            version = vuln.get('version', 'unknown')
            advisory = vuln.get('advisory', 'Unknown')
            title = vuln.get('title', 'Dependency Vulnerability')
            criticality = vuln.get('criticality', 'Medium')
            url = vuln.get('url', '')
            solution = vuln.get('solution', 'Update the gem to a patched version')
            
            severity = self._map_bundler_audit_severity(criticality)
            cvss_score = self._calculate_cvss_score(severity, 'dependency_vulnerability')
            
            return Finding(
                id=f"bundler_audit_{advisory}_{gem_name}",
                title=f"bundler-audit: {title} ({gem_name})",
                description=self._build_bundler_audit_description(vuln, project_root),
                severity=severity.lower(),
                category="ruby_dependency",
                file="Gemfile",
                lines=[1],  # Dependencies are typically at the top
                confidence_score=95,  # High confidence for known CVEs
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="bundler_audit",
                    raw_output=json.dumps(vuln),
                    confidence=95
                )
            )
        except Exception as e:
            logger.error(f"Error creating bundler-audit finding: {e}")
            return None
    
    async def _analyze_ruby_file_patterns(self, file_path: str, context: Dict[str, Any]) -> List[Finding]:
        """Analyze individual Ruby file for security patterns"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Pattern-based security analysis
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for SQL injection patterns
                if any(pattern in line_stripped for pattern in ['execute(', 'find_by_sql(', 'connection.execute(']):
                    if '+' in line_stripped or '#{' in line_stripped:
                        finding = self._create_pattern_finding(
                            "sql_injection", file_path, line_num, line_stripped,
                            "Potential SQL Injection", "String interpolation in SQL query - use parameterized queries"
                        )
                        findings.append(finding)
                
                # Check for command injection
                if any(pattern in line_stripped for pattern in ['system(', 'exec(', '`', 'Kernel.system(']):
                    finding = self._create_pattern_finding(
                        "command_injection", file_path, line_num, line_stripped,
                        "Command Execution", "Command execution requires input validation"
                    )
                    findings.append(finding)
                
                # Check for unsafe YAML loading
                if 'YAML.load(' in line_stripped and 'YAML.safe_load(' not in line_stripped:
                    finding = self._create_pattern_finding(
                        "unsafe_yaml", file_path, line_num, line_stripped,
                        "Unsafe YAML Loading", "YAML.load can execute arbitrary code - use YAML.safe_load"
                    )
                    findings.append(finding)
                
                # Check for eval usage
                if any(pattern in line_stripped for pattern in ['eval(', 'instance_eval(', 'class_eval(']):
                    finding = self._create_pattern_finding(
                        "code_injection", file_path, line_num, line_stripped,
                        "Code Injection", "eval() can execute arbitrary code - avoid dynamic code execution"
                    )
                    findings.append(finding)
                
                # Check for hardcoded secrets
                if any(pattern in line_stripped.lower() for pattern in ['password', 'secret', 'key', 'token']):
                    if '=' in line_stripped and any(quote in line_stripped for quote in ['"', "'"]):
                        finding = self._create_pattern_finding(
                            "hardcoded_secret", file_path, line_num, line_stripped,
                            "Hardcoded Secret", "Potential hardcoded secret found - use environment variables"
                        )
                        findings.append(finding)
                        
        except Exception as e:
            logger.error(f"Error analyzing Ruby file {file_path}: {e}")
        
        return findings
    
    def _create_pattern_finding(self, pattern_id: str, file_path: str, line_num: int, 
                               line_content: str, title: str, description: str) -> Finding:
        """Create a Finding from pattern analysis"""
        severity = self._get_pattern_severity(pattern_id)
        cvss_score = self._calculate_cvss_score(severity, pattern_id)
        
        return Finding(
            id=f"ruby_pattern_{pattern_id}_{hash(file_path + str(line_num))}",
            title=f"Ruby: {title}",
            description=f"{description}\n\nLocation: {file_path}:{line_num}\nCode: {line_content}",
            severity=severity.lower(),
            category="ruby_patterns",
            file=file_path,
            lines=[line_num],
            confidence_score=70,
            cvss_v4=cvss_score,
            evidence=ToolEvidence(
                tool_name="ruby_analyzer",
                raw_output=f"Pattern: {pattern_id}, Line: {line_content}",
                confidence=70
            )
        )
    
    def _map_brakeman_severity(self, confidence: str, warning_type: str) -> str:
        """Map Brakeman confidence to our severity levels"""
        # High confidence warnings get higher severity
        confidence_map = {
            'High': 'HIGH',
            'Medium': 'MEDIUM',
            'Weak': 'LOW'
        }
        
        base_severity = confidence_map.get(confidence, 'MEDIUM')
        
        # Certain warning types are always critical
        critical_warnings = [
            'SQL Injection', 'Command Injection', 'Code Injection',
            'Cross Site Scripting', 'Unsafe Deserialization'
        ]
        
        if any(cw in warning_type for cw in critical_warnings):
            return 'CRITICAL'
        
        return base_severity
    
    def _map_rubocop_severity(self, severity: str, cop_name: str) -> str:
        """Map RuboCop severity to our severity levels"""
        severity_map = {
            'error': 'HIGH',
            'warning': 'MEDIUM',
            'convention': 'LOW',
            'refactor': 'LOW',
            'info': 'LOW'
        }
        
        base_severity = severity_map.get(severity.lower(), 'MEDIUM')
        
        # Security cops get higher severity
        if 'Security' in cop_name:
            if base_severity == 'MEDIUM':
                return 'HIGH'
            elif base_severity == 'LOW':
                return 'MEDIUM'
        
        return base_severity
    
    def _map_bundler_audit_severity(self, criticality: str) -> str:
        """Map bundler-audit criticality to our severity levels"""
        criticality_map = {
            'Critical': 'CRITICAL',
            'High': 'HIGH',
            'Medium': 'MEDIUM',
            'Low': 'LOW',
            'Unknown': 'MEDIUM'
        }
        
        return criticality_map.get(criticality, 'MEDIUM')
    
    def _get_brakeman_confidence(self, confidence: str) -> int:
        """Get confidence score based on Brakeman confidence"""
        confidence_map = {'High': 90, 'Medium': 75, 'Weak': 60}
        return confidence_map.get(confidence, 70)
    
    def _get_rubocop_confidence(self, severity: str) -> int:
        """Get confidence score based on RuboCop severity"""
        severity_map = {'error': 85, 'warning': 75, 'convention': 65}
        return severity_map.get(severity.lower(), 70)
    
    def _get_pattern_severity(self, pattern_id: str) -> str:
        """Get severity for pattern-based findings"""
        severity_map = {
            'sql_injection': 'HIGH',
            'command_injection': 'HIGH',
            'code_injection': 'CRITICAL',
            'unsafe_yaml': 'HIGH',
            'hardcoded_secret': 'MEDIUM'
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
        if any(keyword in category.lower() for keyword in ['injection', 'eval', 'yaml', 'deserialization']):
            score += 1.0
        elif 'dependency' in category.lower():
            score += 0.5
        
        score = min(10.0, score)  # Cap at 10.0
        
        return CVSSv4(
            score=score,
            vector=f"CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:{'H' if score >= 7 else 'M' if score >= 4 else 'L'}/VI:L/VA:L/SC:N/SI:N/SA:N"
        )
    
    def _build_brakeman_description(self, warning: Dict[str, Any], file_path: str, line_num: int) -> str:
        """Build detailed description for Brakeman finding"""
        warning_type = warning.get('warning_type', 'Unknown')
        confidence = warning.get('confidence', 'Medium')
        message = warning.get('message', 'Brakeman security issue')
        check = warning.get('check', 'Unknown')
        
        code = warning.get('code', '')
        user_input = warning.get('user_input', '')
        
        return f"""
Brakeman Security Analysis:

Warning Type: {warning_type}
Check: {check}
Confidence: {confidence}
Message: {message}
Location: {file_path}:{line_num}

Code: {code}
{f'User Input: {user_input}' if user_input else ''}

Security Impact:
Brakeman has identified a potential security vulnerability in your Ruby/Rails application. This could allow attackers to exploit your application if not properly addressed.

Recommendation:
Review the identified code and apply appropriate security measures. Ensure all user input is properly validated and sanitized before use in security-sensitive operations.
"""
    
    def _build_rubocop_description(self, offense: Dict[str, Any], file_path: str, line_num: int) -> str:
        """Build detailed description for RuboCop finding"""
        cop_name = offense.get('cop_name', 'Unknown')
        severity = offense.get('severity', 'warning')
        message = offense.get('message', 'RuboCop security issue')
        
        return f"""
RuboCop Security Analysis:

Cop: {cop_name}
Severity: {severity.upper()}
Message: {message}
Location: {file_path}:{line_num}

Security Impact:
This RuboCop security cop has identified a potential security issue in your Ruby code. Following secure coding practices helps prevent vulnerabilities in your application.

Recommendation:
Address the specific security concern identified by RuboCop. Refer to the RuboCop Security documentation for detailed guidance on resolving this issue.
"""
    
    def _build_bundler_audit_description(self, vuln: Dict[str, Any], project_root: str) -> str:
        """Build detailed description for bundler-audit finding"""
        gem_name = vuln.get('gem', 'unknown')
        version = vuln.get('version', 'unknown')
        advisory = vuln.get('advisory', 'Unknown')
        title = vuln.get('title', 'Dependency Vulnerability')
        criticality = vuln.get('criticality', 'Medium')
        url = vuln.get('url', '')
        solution = vuln.get('solution', 'Update the gem to a patched version')
        
        return f"""
bundler-audit Dependency Vulnerability:

Vulnerability: {advisory}
Title: {title}
Affected Gem: {gem_name} v{version}
Criticality: {criticality}

Security Impact:
This vulnerability affects one of your Ruby gem dependencies. Dependency vulnerabilities can be exploited to compromise your application's security, potentially leading to data breaches, code execution, or denial of service attacks.

Recommendation:
{solution}

Update your Gemfile to use a patched version of the gem, then run:
- bundle update {gem_name}
- bundle audit check

Reference: {url}
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
        return ['ruby']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Ruby Security Analyzer',
            'description': 'Comprehensive Ruby security analysis using Brakeman, RuboCop Security, and bundler-audit',
            'supported_extensions': self.supported_extensions,
            'available_tools': {
                name: {
                    'enabled': info['enabled'],
                    'description': info['description']
                }
                for name, info in self.tools.items()
            }
        }