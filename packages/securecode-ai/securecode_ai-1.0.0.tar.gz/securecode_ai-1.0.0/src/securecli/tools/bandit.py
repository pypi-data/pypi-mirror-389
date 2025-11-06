"""
Bandit Tool Implementation
Python security analysis using Bandit
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import SecurityScannerBase
from ..schemas.findings import Finding, ToolEvidence, CVSSv4

logger = logging.getLogger(__name__)

class BanditScanner(SecurityScannerBase):
    """
    Bandit security linter for Python code
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tool_name = "bandit"
        self.description = "Security linter for Python code"
        self.supported_languages = ["python"]
        
        # Bandit configuration
        self.bandit_config = config.get('bandit', {})
        self.excluded_paths = self.bandit_config.get('exclude', [])
        self.included_tests = self.bandit_config.get('tests', [])
        self.skipped_tests = self.bandit_config.get('skip', [])
        self.confidence_level = self.bandit_config.get('confidence', 'low')
        self.severity_level = self.bandit_config.get('severity', 'low')
        
    def is_available(self) -> bool:
        """Check if Bandit is available"""
        try:
            result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Dict[str, Any]) -> List[Finding]:
        """
        Run Bandit analysis on Python code
        """
        logger.info(f"Running Bandit analysis on {target_path}")
        
        if not self.is_available():
            logger.error("Bandit is not available")
            return []
        
        # Find Python files
        python_files = self._find_python_files(target_path)
        if not python_files:
            logger.info("No Python files found")
            return []
        
        try:
            findings = await self._run_bandit_analysis(target_path, config)
            logger.info(f"Bandit analysis complete. Found {len(findings)} issues")
            return findings
            
        except Exception as e:
            logger.error(f"Error running Bandit analysis: {e}")
            return []
    
    def _find_python_files(self, target_path: str) -> List[str]:
        """Find all Python files in the target path"""
        path = Path(target_path)
        python_files = []
        
        if path.is_file() and path.suffix == '.py':
            python_files.append(str(path))
        elif path.is_dir():
            python_files.extend([
                str(f) for f in path.rglob("*.py")
                if not any(exclude in str(f) for exclude in ['__pycache__', '.git', 'venv', '.venv'])
            ])
        
        return python_files
    
    async def _run_bandit_analysis(self, target_path: str, config: Dict[str, Any]) -> List[Finding]:
        """Run Bandit analysis and parse results"""
        
        # Build Bandit command
        cmd = self._build_bandit_command(target_path, config)
        
        try:
            # Run Bandit
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # Log stderr for debugging but don't treat it as an error for exit codes 0 or 1
            if stderr:
                stderr_text = stderr.decode().strip()
                if process.returncode not in [0, 1]:
                    logger.warning(f"Bandit stderr: {stderr_text}")
                else:
                    # Bandit often prints informational messages to stderr even on success
                    logger.debug(f"Bandit info: {stderr_text}")
            
            # Parse JSON output
            if stdout and stdout.strip():
                return self._parse_bandit_output(stdout.decode())
            else:
                logger.info("Bandit found no issues or no Python files to scan")
                return []
                
        except Exception as e:
            logger.error(f"Error running Bandit: {e}")
            return []
    
    def _build_bandit_command(self, target_path: str, config: Dict[str, Any]) -> List[str]:
        """Build Bandit command with appropriate options"""
        
        cmd = ["bandit", "-r", target_path, "-f", "json"]
        
        # Default exclusions for common directories that shouldn't be scanned
        default_exclusions = ["__pycache__", ".git", ".venv", "venv", "node_modules", "dist", "build"]
        all_exclusions = default_exclusions + (self.excluded_paths or [])
        
        # Add excluded paths
        if all_exclusions:
            cmd.extend(["-x", ",".join(all_exclusions)])
        
        # Add test filters
        if self.included_tests:
            cmd.extend(["-t", ",".join(self.included_tests)])
        
        if self.skipped_tests:
            cmd.extend(["-s", ",".join(self.skipped_tests)])
        
        # Add confidence level using the proper --confidence-level flag
        cmd.extend(["--confidence-level", self.confidence_level])
        
        # Add severity level using the proper --severity-level flag  
        cmd.extend(["--severity-level", self.severity_level])
        
        # Add configuration file if specified (only if it exists)
        bandit_config_file = config.get('bandit', {}).get('config_file')
        if bandit_config_file and Path(bandit_config_file).exists():
            cmd.extend(["--config", bandit_config_file])
        
        # Additional options
        if config.get('ignore_nosec', False):
            cmd.append("--ignore-nosec")
        
        return cmd
    
    def _parse_bandit_output(self, output: str) -> List[Finding]:
        """Parse Bandit JSON output into Finding objects"""
        
        findings = []
        
        # Handle empty output
        if not output or not output.strip():
            logger.info("Bandit returned empty output - no issues found")
            return findings
        
        try:
            data = json.loads(output)
            results = data.get('results', [])
            
            for result in results:
                finding = self._create_finding_from_result(result)
                if finding:
                    findings.append(finding)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit JSON output: {e}")
            logger.debug(f"Bandit output was: {output[:200]}...")  # Log first 200 chars for debugging
        
        return findings
    
    def _create_finding_from_result(self, result: Dict[str, Any]) -> Optional[Finding]:
        """Create Finding object from Bandit result"""
        
        try:
            # Extract result information
            test_id = result.get('test_id', 'unknown')
            test_name = result.get('test_name', 'Unknown Test')
            issue_severity = result.get('issue_severity', 'UNDEFINED')
            issue_confidence = result.get('issue_confidence', 'UNDEFINED')
            issue_text = result.get('issue_text', '')
            
            # Extract location information
            filename = result.get('filename', '')
            line_number = result.get('line_number', 0)
            code = result.get('code', '')
            
            # Map Bandit severity to standard severity
            severity = self._map_severity(issue_severity)
            
            # Create tool evidence
            tool_evidence = ToolEvidence(
                tool=self.tool_name,
                id=test_id,
                raw=json.dumps(result, indent=2)
            )
            
            # Create finding with all required fields
            finding = Finding(
                file=filename.replace('./test_scan/', '').replace('./', ''),  # Clean up file path
                title=f"{test_name} security issue",
                description=issue_text or f"Bandit detected {test_name} security issue",
                lines=str(line_number),
                impact=self._get_impact_description(test_id, issue_severity),
                severity=severity.title(),  # Convert to title case
                cvss_v4=CVSSv4(
                    score=self._map_severity_to_cvss(issue_severity),
                    vector=f"CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:H/VI:N/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=code.strip() if code else f"Line {line_number}: Issue detected",
                recommendation=self._get_recommendation(test_id),
                sample_fix=self._get_sample_fix(test_id),
                poc=self._get_poc(test_id),
                owasp=self._get_owasp_categories(test_id),
                cwe=self._get_cwe_ids(result),
                tool_evidence=[tool_evidence]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error creating finding from Bandit result: {e}")
            return None

    def _get_impact_description(self, test_id: str, severity: str) -> str:
        """Get impact description for test ID"""
        impact_map = {
            'B105': 'Hardcoded credentials can be extracted and used by attackers',
            'B301': 'Unsafe deserialization can lead to code execution',
            'B307': 'Code injection can allow arbitrary code execution',
            'B602': 'Command injection can allow system compromise',
            'B608': 'SQL injection can lead to data breach'
        }
        default_impact = f"{severity.title()} security vulnerability detected"
        return impact_map.get(test_id, default_impact)

    def _get_recommendation(self, test_id: str) -> str:
        """Get recommendation for test ID"""
        rec_map = {
            'B105': 'Store secrets in environment variables or secure key management',
            'B301': 'Use safe serialization formats like JSON instead of pickle',
            'B307': 'Use ast.literal_eval() or validate input before eval()',
            'B602': 'Use subprocess with shell=False and validate inputs',
            'B608': 'Use parameterized queries to prevent SQL injection'
        }
        return rec_map.get(test_id, 'Review and fix the security issue')

    def _get_sample_fix(self, test_id: str) -> str:
        """Get sample fix for test ID"""
        fix_map = {
            'B105': 'password = os.environ.get("DB_PASSWORD")',
            'B301': 'data = json.loads(serialized_data)',
            'B307': 'result = ast.literal_eval(user_input)',
            'B602': 'subprocess.run([cmd, arg1, arg2], shell=False)',
            'B608': 'cursor.execute("SELECT * FROM users WHERE id = %s", (user_id,))'
        }
        return fix_map.get(test_id, '# Apply appropriate security fix')

    def _get_poc(self, test_id: str) -> str:
        """Get proof of concept for test ID"""
        poc_map = {
            'B105': 'Credentials can be found in source code or binary',
            'B301': 'Malicious pickle can execute arbitrary code on deserialization',
            'B307': 'eval("__import__(\'os\').system(\'ls\')") executes system commands',
            'B602': 'shell=True allows command injection via user input',
            'B608': 'SQL injection: user_id = "1; DROP TABLE users--"'
        }
        return poc_map.get(test_id, 'Security vulnerability can be exploited')

    def _get_owasp_categories(self, test_id: str) -> List[str]:
        """Get OWASP categories for test ID"""
        owasp_map = {
            'B105': ['A07:2021 - Identification and Authentication Failures'],
            'B301': ['A08:2021 - Software and Data Integrity Failures'],
            'B307': ['A03:2021 - Injection'],
            'B602': ['A03:2021 - Injection'],
            'B608': ['A03:2021 - Injection']
        }
        return owasp_map.get(test_id, ['A00:2021 - Security Misconfiguration'])

    def _get_cwe_ids(self, result: Dict[str, Any]) -> List[str]:
        """Get CWE IDs from Bandit result"""
        cwe_info = result.get('issue_cwe', {})
        if isinstance(cwe_info, dict) and 'id' in cwe_info:
            return [f"CWE-{cwe_info['id']}"]
        return []

    def _map_severity_to_cvss(self, severity: str) -> float:
        """Map severity to CVSS score"""
        cvss_map = {
            'HIGH': 8.5,
            'MEDIUM': 5.5,
            'LOW': 2.5,
            'UNDEFINED': 1.0
        }
        return cvss_map.get(severity.upper(), 1.0)
    
    def _map_severity(self, bandit_severity: str) -> str:
        """Map Bandit severity to standard severity levels"""
        severity_map = {
            'HIGH': 'high',
            'MEDIUM': 'medium', 
            'LOW': 'low',
            'UNDEFINED': 'low'
        }
        return severity_map.get(bandit_severity.upper(), 'low')
    
    def _map_confidence_to_score(self, confidence: str) -> int:
        """Map Bandit confidence to numeric score"""
        confidence_map = {
            'HIGH': 90,
            'MEDIUM': 70,
            'LOW': 50,
            'UNDEFINED': 30
        }
        return confidence_map.get(confidence.upper(), 50)
    
    def _categorize_bandit_test(self, test_id: str) -> str:
        """Categorize Bandit test into vulnerability category"""
        
        # Map Bandit test IDs to categories
        category_map = {
            'B101': 'testing',        # assert_used
            'B102': 'testing',        # exec_used
            'B103': 'file_permissions',  # set_bad_file_permissions
            'B104': 'network',        # hardcoded_bind_all_interfaces
            'B105': 'cryptography',   # hardcoded_password_string
            'B106': 'cryptography',   # hardcoded_password_funcarg
            'B107': 'cryptography',   # hardcoded_password_default
            'B108': 'file_handling',  # hardcoded_tmp_directory
            'B110': 'testing',        # try_except_pass
            'B112': 'testing',        # try_except_continue
            'B201': 'deserialization',  # flask_debug_true
            'B301': 'deserialization',  # pickle
            'B302': 'deserialization',  # marshal
            'B303': 'cryptography',   # md5
            'B304': 'cryptography',   # des
            'B305': 'cryptography',   # cipher
            'B306': 'file_handling',  # mktemp_q
            'B307': 'code_injection', # eval
            'B308': 'file_handling',  # mark_safe
            'B309': 'http',           # httpsconnection
            'B310': 'network',        # urllib_urlopen
            'B311': 'random',         # random
            'B312': 'network',        # telnetlib
            'B313': 'code_injection', # xml_bad_cElementTree
            'B314': 'code_injection', # xml_bad_ElementTree
            'B315': 'code_injection', # xml_bad_expatreader
            'B316': 'code_injection', # xml_bad_expatbuilder
            'B317': 'code_injection', # xml_bad_sax
            'B318': 'code_injection', # xml_bad_minidom
            'B319': 'code_injection', # xml_bad_pulldom
            'B320': 'code_injection', # xml_bad_etree
            'B321': 'network',        # ftplib
            'B322': 'code_injection', # input
            'B323': 'file_handling',  # unverified_context
            'B324': 'cryptography',   # hashlib_new_insecure_functions
            'B325': 'file_handling',  # tempnam
            'B401': 'code_injection', # import_telnetlib
            'B402': 'code_injection', # import_ftplib
            'B403': 'code_injection', # import_pickle
            'B404': 'code_injection', # import_subprocess
            'B405': 'code_injection', # import_xml_etree
            'B406': 'code_injection', # import_xml_sax
            'B407': 'code_injection', # import_xml_expat
            'B408': 'code_injection', # import_xml_minidom
            'B409': 'code_injection', # import_xml_pulldom
            'B410': 'code_injection', # import_lxml
            'B411': 'code_injection', # import_xmlrpclib
            'B412': 'code_injection', # import_httpoxy
            'B413': 'cryptography',   # import_pycrypto
            'B501': 'network',        # request_with_no_cert_validation
            'B502': 'cryptography',   # ssl_with_bad_version
            'B503': 'cryptography',   # ssl_with_bad_defaults
            'B504': 'cryptography',   # ssl_with_no_version
            'B505': 'cryptography',   # weak_cryptographic_key
            'B506': 'cryptography',   # yaml_load
            'B507': 'network',        # ssh_no_host_key_verification
            'B601': 'code_injection', # paramiko_calls
            'B602': 'code_injection', # subprocess_popen_with_shell_equals_true
            'B603': 'code_injection', # subprocess_without_shell_equals_true
            'B604': 'code_injection', # any_other_function_with_shell_equals_true
            'B605': 'code_injection', # start_process_with_a_shell
            'B606': 'code_injection', # start_process_with_no_shell
            'B607': 'code_injection', # start_process_with_partial_path
            'B608': 'sql_injection',  # hardcoded_sql_expressions
            'B609': 'code_injection', # linux_commands_wildcard_injection
            'B610': 'sql_injection',  # django_extra_used
            'B611': 'sql_injection',  # django_rawsql_used
            'B701': 'testing',        # jinja2_autoescape_false
            'B702': 'testing',        # use_of_mako_templates
            'B703': 'network'         # django_mark_safe
        }
        
        return category_map.get(test_id, 'general')
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return ['.py']
    
    def get_test_info(self) -> Dict[str, Any]:
        """Get information about available Bandit tests"""
        return {
            'test_categories': {
                'cryptography': 'Cryptographic vulnerabilities',
                'code_injection': 'Code injection vulnerabilities', 
                'sql_injection': 'SQL injection vulnerabilities',
                'network': 'Network security issues',
                'file_handling': 'File handling vulnerabilities',
                'deserialization': 'Unsafe deserialization',
                'testing': 'Testing and debugging issues'
            },
            'severity_levels': ['HIGH', 'MEDIUM', 'LOW'],
            'confidence_levels': ['HIGH', 'MEDIUM', 'LOW'],
            'common_tests': [
                'B101: assert_used',
                'B102: exec_used', 
                'B105: hardcoded_password_string',
                'B107: hardcoded_password_default',
                'B301: pickle',
                'B303: md5',
                'B307: eval',
                'B311: random',
                'B501: request_with_no_cert_validation',
                'B602: subprocess_popen_with_shell_equals_true',
                'B608: hardcoded_sql_expressions'
            ]
        }
    
    def get_version(self) -> str:
        """Get Bandit version"""
        try:
            result = subprocess.run(
                ["bandit", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "not-available"
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """
        Convert Bandit JSON output to normalized Finding objects
        
        Args:
            raw_output: JSON output from Bandit
            metadata: Additional metadata
            
        Returns:
            List of normalized Finding objects
        """
        findings = []
        
        try:
            if not raw_output.strip():
                return findings
                
            data = json.loads(raw_output)
            
            # Process results
            results = data.get('results', [])
            
            for result in results:
                finding = Finding(
                    id=f"bandit-{result.get('test_id', 'unknown')}-{len(findings)}",
                    title=f"Bandit {result.get('test_id', 'Unknown')}: {result.get('test_name', 'Security Issue')}",
                    description=result.get('issue_text', 'No description available'),
                    severity=self._map_severity(result.get('issue_severity', 'LOW')),
                    category=self._get_category_from_test_id(result.get('test_id', '')),
                    file=result.get('filename', 'unknown'),
                    line=result.get('line_number', 0),
                    column=result.get('col_offset', 0),
                    tool='bandit',
                    evidence=ToolEvidence(
                        raw_output=json.dumps(result),
                        confidence=result.get('issue_confidence', 'MEDIUM').lower(),
                        tool_version=self.get_version()
                    ),
                    owasp=self._get_owasp_mapping(result.get('test_id', '')),
                    cwe=self._get_cwe_mapping(result.get('test_id', '')),
                    references=[
                        f"https://bandit.readthedocs.io/en/latest/plugins/{result.get('test_id', '').lower()}.html"
                    ] if result.get('test_id') else []
                )
                findings.append(finding)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Bandit output as JSON: {e}")
        except Exception as e:
            logger.error(f"Error normalizing Bandit findings: {e}")
        
        return findings
    
    def _map_severity(self, severity: str) -> str:
        """Map Bandit severity to standard severity"""
        mapping = {
            'HIGH': 'critical',
            'MEDIUM': 'high', 
            'LOW': 'medium'
        }
        return mapping.get(severity.upper(), 'medium')
    
    def _get_owasp_mapping(self, test_id: str) -> List[str]:
        """Get OWASP mapping for test ID"""
        owasp_map = {
            'B105': ['A07:2021 - Identification and Authentication Failures'],
            'B107': ['A07:2021 - Identification and Authentication Failures'],
            'B301': ['A08:2021 - Software and Data Integrity Failures'],
            'B303': ['A02:2021 - Cryptographic Failures'],
            'B307': ['A03:2021 - Injection'],
            'B501': ['A07:2021 - Identification and Authentication Failures'],
            'B602': ['A03:2021 - Injection'],
            'B608': ['A03:2021 - Injection']
        }
        return owasp_map.get(test_id, [])
    
    def _get_cwe_mapping(self, test_id: str) -> List[str]:
        """Get CWE mapping for test ID"""
        cwe_map = {
            'B105': ['CWE-798'],  # Hard-coded credentials
            'B107': ['CWE-798'],  # Hard-coded credentials
            'B301': ['CWE-502'],  # Deserialization
            'B303': ['CWE-327'],  # Weak crypto
            'B307': ['CWE-95'],   # Code injection
            'B501': ['CWE-295'],  # Certificate validation
            'B602': ['CWE-78'],   # Command injection
            'B608': ['CWE-89']    # SQL injection
        }
        return cwe_map.get(test_id, [])

# Alias for backward compatibility
BanditTool = BanditScanner