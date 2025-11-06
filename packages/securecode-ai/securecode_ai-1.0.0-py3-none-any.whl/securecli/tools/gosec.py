"""
Gosec Tool Implementation
Go security analysis using gosec
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

class GosecScanner(SecurityScannerBase):
    """
    Gosec security analyzer for Go code
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tool_name = "gosec"
        self.description = "Security analyzer for Go code"
        self.supported_languages = ["go"]
        
        # Gosec configuration
        self.gosec_config = config.get('gosec', {})
        self.excluded_files = self.gosec_config.get('exclude', [])
        self.included_rules = self.gosec_config.get('include', [])
        self.excluded_rules = self.gosec_config.get('exclude_rules', [])
        self.severity_filter = self.gosec_config.get('severity', 'low')
        self.confidence_filter = self.gosec_config.get('confidence', 'low')
        
    def is_available(self) -> bool:
        """Check if gosec is available"""
        # Try direct gosec command first
        try:
            result = subprocess.run(
                ["gosec", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Continue to other attempts
        
        # Try Go bin directory
        try:
            gopath_result = subprocess.run(['go', 'env', 'GOPATH'], 
                                         capture_output=True, text=True, timeout=5)
            if gopath_result.returncode == 0:
                gopath = gopath_result.stdout.strip()
                gosec_path = f"{gopath}/bin/gosec"
                result = subprocess.run([gosec_path, "-version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return True
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass  # Continue to snap fallback
        
        # Try snap command as fallback
        try:
            result = subprocess.run(
                ["snap", "run", "gosec", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Dict[str, Any]) -> List[Finding]:
        """
        Run gosec analysis on Go code
        """
        logger.info(f"Running gosec analysis on {target_path}")
        
        if not self.is_available():
            logger.error("gosec is not available")
            return []
        
        # Find Go files
        go_files = self._find_go_files(target_path)
        if not go_files:
            logger.info("No Go files found")
            return []
        
        try:
            findings = await self._run_gosec_analysis(target_path, config)
            logger.info(f"gosec analysis complete. Found {len(findings)} issues")
            return findings
            
        except Exception as e:
            logger.error(f"Error running gosec analysis: {e}")
            return []
    
    def _find_go_files(self, target_path: str) -> List[str]:
        """Find all Go files in the target path"""
        path = Path(target_path)
        go_files = []
        
        if path.is_file() and path.suffix == '.go':
            go_files.append(str(path))
        elif path.is_dir():
            go_files.extend([
                str(f) for f in path.rglob("*.go")
                if not any(exclude in str(f) for exclude in ['vendor', '.git', 'node_modules'])
            ])
        
        return go_files
    
    async def _run_gosec_analysis(self, target_path: str, config: Dict[str, Any]) -> List[Finding]:
        """Run gosec analysis and parse results"""
        
        # Build gosec command
        cmd = self._build_gosec_command(target_path, config)
        
        try:
            # Run gosec
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            # gosec returns non-zero if issues are found, which is expected
            if stderr and process.returncode not in [0, 1]:
                logger.warning(f"gosec stderr: {stderr.decode()}")
            
            # Parse JSON output
            if stdout:
                return self._parse_gosec_output(stdout.decode())
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error running gosec: {e}")
            return []
    
    def _build_gosec_command(self, target_path: str, config: Dict[str, Any]) -> List[str]:
        """Build gosec command with appropriate options"""
        
        # Check if gosec is available directly
        try:
            subprocess.run(["gosec", "-version"], capture_output=True, timeout=5)
            cmd = ["gosec", "-fmt", "json"]
        except (subprocess.TimeoutExpired, FileNotFoundError):
            # Try Go bin directory
            try:
                gopath_result = subprocess.run(['go', 'env', 'GOPATH'], 
                                             capture_output=True, text=True, timeout=5)
                if gopath_result.returncode == 0:
                    gopath = gopath_result.stdout.strip()
                    gosec_path = f"{gopath}/bin/gosec"
                    subprocess.run([gosec_path, "-version"], capture_output=True, timeout=5)
                    cmd = [gosec_path, "-fmt", "json"]
                else:
                    # Use snap as final fallback
                    cmd = ["snap", "run", "gosec", "-fmt", "json"]
            except (subprocess.TimeoutExpired, FileNotFoundError):
                # Use snap as final fallback
                cmd = ["snap", "run", "gosec", "-fmt", "json"]
        
        # Add excluded files
        if self.excluded_files:
            for exclude in self.excluded_files:
                cmd.extend(["-exclude-dir", exclude])
        
        # Add rule filters
        if self.included_rules:
            cmd.extend(["-include", ",".join(self.included_rules)])
        
        if self.excluded_rules:
            cmd.extend(["-exclude", ",".join(self.excluded_rules)])
        
        # Add severity and confidence filters
        cmd.extend(["-severity", self.severity_filter])
        cmd.extend(["-confidence", self.confidence_filter])
        
        # Additional options
        if config.get('no_fail', False):
            cmd.append("-no-fail")
        
        if config.get('verbose', False):
            cmd.append("-verbose")
        
        # Add configuration file if specified
        gosec_config_file = config.get('config_file')
        if gosec_config_file and Path(gosec_config_file).exists():
            cmd.extend(["-conf", gosec_config_file])
        
        # Add target path
        cmd.append(target_path)
        
        return cmd
    
    def _parse_gosec_output(self, output: str) -> List[Finding]:
        """Parse gosec JSON output into Finding objects"""
        
        findings = []
        
        try:
            data = json.loads(output)
            issues = data.get('Issues', [])
            
            for issue in issues:
                finding = self._create_finding_from_issue(issue)
                if finding:
                    findings.append(finding)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse gosec JSON output: {e}")
        
        return findings
    
    def _create_finding_from_issue(self, issue: Dict[str, Any]) -> Optional[Finding]:
        """Create Finding object from gosec issue"""
        
        try:
            # Extract issue information
            rule_id = issue.get('rule_id', 'unknown')
            details = issue.get('details', 'Unknown issue')
            severity = issue.get('severity', 'MEDIUM')
            confidence = issue.get('confidence', 'MEDIUM')
            cwe = issue.get('cwe', {})
            
            # Extract location information
            filename = issue.get('file', '')
            line = issue.get('line', '')
            column = issue.get('column', '')
            code = issue.get('code', '')
            
            # Parse line number
            line_number = 0
            if line:
                try:
                    line_number = int(line)
                except ValueError:
                    pass
            
            # Map gosec severity to standard severity
            mapped_severity = self._map_severity(severity)
            
            # Create tool evidence
            tool_evidence = ToolEvidence(
                tool=self.tool_name,
                id=rule_id,
                raw=json.dumps(issue, indent=2)
            )
            
            # Create finding
            finding = Finding(
                file=filename,
                title=f"gosec: {rule_id}",
                description=details or f"gosec detected {rule_id} security issue",
                lines=str(line_number) if line_number else "1",
                impact=self._get_impact_description(rule_id),
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=self._get_cvss_score(mapped_severity), 
                    vector="AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
                ),
                owasp=self._get_owasp_categories(rule_id),
                cwe=[str(cwe.get('id'))] if cwe and cwe.get('id') else [],
                snippet=code or "No code snippet available",
                recommendation=self._get_recommendation(rule_id),
                sample_fix=self._get_sample_fix(rule_id),
                poc=self._get_poc(rule_id),
                references=self._get_references(rule_id),
                tool_evidence=[tool_evidence]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error creating finding from gosec issue: {e}")
            return None
    
    def _map_severity(self, gosec_severity: str) -> str:
        """Map gosec severity to standard severity levels"""
        severity_map = {
            'HIGH': 'high',
            'MEDIUM': 'medium', 
            'LOW': 'low'
        }
        return severity_map.get(gosec_severity.upper(), 'medium')
    
    def _map_confidence_to_score(self, confidence: str) -> int:
        """Map gosec confidence to numeric score"""
        confidence_map = {
            'HIGH': 90,
            'MEDIUM': 70,
            'LOW': 50
        }
        return confidence_map.get(confidence.upper(), 70)
    
    def _categorize_gosec_rule(self, rule_id: str) -> str:
        """Categorize gosec rule into vulnerability category"""
        
        # Map gosec rule IDs to categories
        category_map = {
            'G101': 'cryptography',      # Look for hard coded credentials
            'G102': 'network',           # Bind to all interfaces
            'G103': 'file_permissions',  # Audit the use of unsafe block
            'G104': 'error_handling',    # Audit errors not checked
            'G106': 'network',           # Audit the use of ssh.InsecureIgnoreHostKey
            'G107': 'network',           # Url provided to HTTP request as taint input
            'G108': 'file_handling',     # Profiling endpoint automatically exposed on /debug/pprof
            'G109': 'code_injection',    # Potential Integer overflow made by strconv.Atoi result conversion to int16/32
            'G110': 'code_injection',    # Potential DoS vulnerability via decompression bomb
            'G201': 'sql_injection',     # SQL query construction using format string
            'G202': 'sql_injection',     # SQL query construction using string concatenation
            'G203': 'code_injection',    # Use of unescaped data in HTML templates
            'G204': 'code_injection',    # Audit use of command execution
            'G301': 'file_permissions',  # Poor file permissions used when creating a directory
            'G302': 'file_permissions',  # Poor file permissions used with chmod
            'G303': 'file_permissions',  # Creating tempfile using a predictable path
            'G304': 'file_handling',     # File path provided as taint input
            'G305': 'file_handling',     # File traversal when extracting zip/tar archive
            'G306': 'file_permissions',  # Poor file permissions used when writing to a new file
            'G307': 'file_handling',     # Deferring a method which returns an error
            'G401': 'cryptography',      # Detect the usage of DES, RC4, MD5 or SHA1
            'G402': 'cryptography',      # Look for bad TLS connection settings
            'G403': 'cryptography',      # Ensure minimum RSA key length of 2048 bits
            'G404': 'cryptography',      # Insecure random number source (rand)
            'G501': 'cryptography',      # Import blocklist: crypto/md5
            'G502': 'cryptography',      # Import blocklist: crypto/des
            'G503': 'cryptography',      # Import blocklist: crypto/rc4
            'G504': 'cryptography',      # Import blocklist: net/http/cgi
            'G505': 'cryptography',      # Import blocklist: crypto/sha1
            'G601': 'memory_safety'      # Implicit memory aliasing in RangeStmt
        }
        
        return category_map.get(rule_id, 'general')
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return ['.go']
    
    def get_rule_info(self) -> Dict[str, Any]:
        """Get information about available gosec rules"""
        return {
            'rule_categories': {
                'cryptography': 'Cryptographic vulnerabilities',
                'code_injection': 'Code injection vulnerabilities', 
                'sql_injection': 'SQL injection vulnerabilities',
                'network': 'Network security issues',
                'file_handling': 'File handling vulnerabilities',
                'file_permissions': 'File permission issues',
                'error_handling': 'Error handling issues',
                'memory_safety': 'Memory safety issues'
            },
            'severity_levels': ['HIGH', 'MEDIUM', 'LOW'],
            'confidence_levels': ['HIGH', 'MEDIUM', 'LOW'],
            'common_rules': [
                'G101: Hard coded credentials',
                'G102: Bind to all interfaces',
                'G104: Errors not checked',
                'G201: SQL query construction using format string',
                'G204: Audit use of command execution',
                'G301: Poor file permissions used when creating a directory',
                'G304: File path provided as taint input',
                'G401: Detect the usage of DES, RC4, MD5 or SHA1',
                'G402: Look for bad TLS connection settings',
                'G404: Insecure random number source'
            ]
        }
    
    def get_module_analysis_info(self) -> Dict[str, Any]:
        """Get Go module specific analysis information"""
        return {
            'dependency_analysis': True,
            'go_mod_support': True,
            'vendor_scanning': True,
            'build_tag_support': True,
            'cgo_analysis': True
        }
    
    def get_version(self) -> str:
        """Get Gosec version"""
        # Try direct gosec command first
        try:
            result = subprocess.run(
                ["gosec", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try Go bin directory
        try:
            gopath_result = subprocess.run(['go', 'env', 'GOPATH'], 
                                         capture_output=True, text=True, timeout=5)
            if gopath_result.returncode == 0:
                gopath = gopath_result.stdout.strip()
                gosec_path = f"{gopath}/bin/gosec"
                result = subprocess.run([gosec_path, "-version"], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        # Try snap as fallback
        try:
            result = subprocess.run(
                ["snap", "run", "gosec", "-version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.TimeoutExpired, FileNotFoundError):
            pass
        
        return "not-available"
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """
        Convert Gosec JSON output to normalized Finding objects
        
        Args:
            raw_output: JSON output from Gosec
            metadata: Additional metadata
            
        Returns:
            List of normalized Finding objects
        """
        findings = []
        
        try:
            if not raw_output.strip():
                return findings
                
            data = json.loads(raw_output)
            
            # Process issues
            issues = data.get('Issues', [])
            
            for issue in issues:
                finding = Finding(
                    id=f"gosec-{issue.get('rule_id', 'unknown')}-{len(findings)}",
                    title=f"Gosec {issue.get('rule_id', 'Unknown')}: {issue.get('details', 'Security Issue')}",
                    description=issue.get('details', 'No description available'),
                    severity=self._map_severity(issue.get('severity', 'MEDIUM')),
                    category=self._get_category_from_rule_id(issue.get('rule_id', '')),
                    file=issue.get('file', 'unknown'),
                    line=int(issue.get('line', 0)),
                    column=int(issue.get('column', 0)),
                    tool='gosec',
                    evidence=ToolEvidence(
                        raw_output=json.dumps(issue),
                        confidence=issue.get('confidence', 'MEDIUM').lower(),
                        tool_version=self.get_version()
                    ),
                    owasp=self._get_owasp_mapping(issue.get('rule_id', '')),
                    cwe=self._get_cwe_mapping(issue.get('rule_id', '')),
                    references=[
                        f"https://securecodewarrior.github.io/gosec/rules/{issue.get('rule_id', '').lower()}.html"
                    ] if issue.get('rule_id') else []
                )
                findings.append(finding)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gosec output as JSON: {e}")
        except Exception as e:
            logger.error(f"Error normalizing Gosec findings: {e}")
        
        return findings
    
    def _map_severity(self, severity: str) -> str:
        """Map Gosec severity to standard severity"""
        mapping = {
            'HIGH': 'High',
            'MEDIUM': 'Medium', 
            'LOW': 'Low'
        }
        return mapping.get(severity.upper(), 'Medium')
    
    def _get_owasp_mapping(self, rule_id: str) -> List[str]:
        """Get OWASP mapping for rule ID"""
        owasp_map = {
            'G101': ['A07:2021 - Identification and Authentication Failures'],
            'G102': ['A05:2021 - Security Misconfiguration'],
            'G201': ['A03:2021 - Injection'],
            'G204': ['A03:2021 - Injection'],
            'G301': ['A05:2021 - Security Misconfiguration'],
            'G304': ['A01:2021 - Broken Access Control'],
            'G401': ['A02:2021 - Cryptographic Failures'],
            'G402': ['A07:2021 - Identification and Authentication Failures']
        }
        return owasp_map.get(rule_id, [])
    
    def _get_cwe_mapping(self, rule_id: str) -> List[str]:
        """Get CWE mapping for rule ID"""
        cwe_map = {
            'G101': ['798'],  # Hardcoded credentials
            'G102': ['200'],  # Network binding
            'G201': ['89'],   # SQL injection
            'G204': ['78'],   # Command injection
            'G301': ['276'],  # File permissions
            'G304': ['22'],   # File inclusion
            'G401': ['328'],  # Weak hash
            'G402': ['327'],  # Weak crypto
            'G501': ['327'],  # MD5 usage
            'G104': ['703']   # Unhandled errors
        }
        return cwe_map.get(rule_id, [])
    
    def _get_category_from_rule_id(self, rule_id: str) -> str:
        """Get category from rule ID"""
        return 'security'
    
    def _get_impact_description(self, rule_id: str) -> str:
        """Get impact description for rule"""
        impacts = {
            'G101': 'Hardcoded credentials can be extracted by attackers and used for unauthorized access',
            'G102': 'Binding to all interfaces may expose services to unintended networks',
            'G201': 'SQL injection vulnerabilities can lead to data theft or database compromise',
            'G204': 'Command injection can allow arbitrary command execution',
            'G301': 'Incorrect file permissions may allow unauthorized access to sensitive files',
            'G304': 'File inclusion vulnerabilities can lead to information disclosure',
            'G401': 'Weak cryptographic hashes can be easily cracked by attackers',
            'G402': 'Weak TLS configurations can be exploited for man-in-the-middle attacks',
            'G501': 'MD5 is cryptographically broken and can be compromised',
            'G104': 'Unhandled errors may leak sensitive information or cause application crashes'
        }
        return impacts.get(rule_id, 'Security vulnerability that could be exploited by attackers')
    
    def _get_recommendation(self, rule_id: str) -> str:
        """Get fix recommendation for rule"""
        recommendations = {
            'G101': 'Use environment variables or secure credential management systems',
            'G102': 'Bind to specific interfaces instead of 0.0.0.0',
            'G201': 'Use parameterized queries or prepared statements',
            'G204': 'Validate and sanitize all user inputs before using in commands',
            'G301': 'Set appropriate file permissions (644 for files, 755 for directories)',
            'G304': 'Validate file paths and use allow-lists for file access',
            'G401': 'Use strong cryptographic hash functions like SHA-256 or SHA-3',
            'G402': 'Configure TLS with strong ciphers and current protocol versions',
            'G501': 'Replace MD5 with SHA-256 or other secure hash functions',
            'G104': 'Always check and handle error return values'
        }
        return recommendations.get(rule_id, 'Review and fix the security issue according to best practices')
    
    def _get_sample_fix(self, rule_id: str) -> str:
        """Get sample fix for rule"""
        fixes = {
            'G101': 'password := os.Getenv("DB_PASSWORD")',
            'G102': 'listener, err := net.Listen("tcp", "127.0.0.1:8080")',
            'G201': 'rows, err := db.Query("SELECT * FROM users WHERE id = ?", userID)',
            'G204': 'cmd := exec.Command("ls", "-l", sanitizedPath)',
            'G301': 'err := os.WriteFile("config.txt", data, 0644)',
            'G304': 'if !isAllowedPath(filename) { return errors.New("invalid path") }',
            'G401': 'hash := sha256.Sum256(data)',
            'G402': 'tlsConfig := &tls.Config{MinVersion: tls.VersionTLS12}',
            'G501': 'hasher := sha256.New()',
            'G104': 'if err := someFunction(); err != nil { return err }'
        }
        return fixes.get(rule_id, '// Fix the security issue according to best practices')
    
    def _get_poc(self, rule_id: str) -> str:
        """Get proof of concept for rule"""
        pocs = {
            'G101': 'Attacker can find hardcoded credentials in source code or binaries',
            'G102': 'Attacker can access service from external networks when bound to 0.0.0.0',
            'G201': 'Attacker can inject SQL: \"; DROP TABLE users; --',
            'G204': 'Attacker can inject commands: "; rm -rf / #',
            'G301': 'Attacker can read/write files due to overly permissive permissions',
            'G304': 'Attacker can access arbitrary files: ../../../etc/passwd',
            'G401': 'Attacker can use rainbow tables or brute force to crack weak hashes',
            'G402': 'Attacker can downgrade connection to use weak ciphers',
            'G501': 'Attacker can use MD5 collisions to forge authentic-looking data',
            'G104': 'Attacker can cause crashes or information leaks through error conditions'
        }
        return pocs.get(rule_id, 'Security vulnerability can be exploited by attackers')
    
    def _get_references(self, rule_id: str) -> List[str]:
        """Get references for rule"""
        base_refs = [
            f"https://securecodewarrior.github.io/gosec/rules/{rule_id.lower()}.html" if rule_id else "",
            "https://owasp.org/www-project-go-secure-coding-practices-guide/"
        ]
        return [ref for ref in base_refs if ref]
    
    def _get_owasp_categories(self, rule_id: str) -> List[str]:
        """Get OWASP categories for rule"""
        owasp_map = {
            'G101': ['A07:2021 - Identification and Authentication Failures'],
            'G102': ['A05:2021 - Security Misconfiguration'],
            'G201': ['A03:2021 - Injection'],
            'G204': ['A03:2021 - Injection'],
            'G301': ['A05:2021 - Security Misconfiguration'],
            'G304': ['A01:2021 - Broken Access Control'],
            'G401': ['A02:2021 - Cryptographic Failures'],
            'G402': ['A07:2021 - Identification and Authentication Failures'],
            'G501': ['A02:2021 - Cryptographic Failures'],
            'G104': ['A09:2021 - Security Logging and Monitoring Failures']
        }
        return owasp_map.get(rule_id, ['A00:2021 - Security Misconfiguration'])
    
    def _get_cvss_score(self, severity: str) -> float:
        """Get CVSS score based on severity"""
        scores = {
            'Critical': 9.0,
            'High': 7.0,
            'Medium': 5.0,
            'Low': 3.0
        }
        return scores.get(severity, 5.0)