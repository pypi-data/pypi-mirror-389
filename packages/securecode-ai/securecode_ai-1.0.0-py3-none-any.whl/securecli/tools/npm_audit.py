"""
npm audit Tool Implementation
Node.js dependency vulnerability analysis using npm audit
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import SecurityScannerBase
from ..schemas.findings import Finding, ToolEvidence

logger = logging.getLogger(__name__)

class NpmAuditScanner(SecurityScannerBase):
    """
    npm audit for Node.js dependency vulnerability analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tool_name = "npm_audit"
        self.description = "Node.js dependency vulnerability scanner"
        self.supported_languages = ["javascript", "typescript"]
        
        # npm audit configuration
        self.audit_config = config.get('npm_audit', {})
        self.audit_level = self.audit_config.get('audit_level', 'low')
        self.production_only = self.audit_config.get('production_only', False)
        self.package_lock_only = self.audit_config.get('package_lock_only', False)
        
    def is_available(self) -> bool:
        """Check if npm is available"""
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Dict[str, Any]) -> List[Finding]:
        """
        Run npm audit analysis on Node.js projects
        """
        logger.info(f"Running npm audit analysis on {target_path}")
        
        if not self.is_available():
            logger.error("npm is not available")
            return []
        
        # Find package.json files
        package_files = self._find_package_files(target_path)
        if not package_files:
            logger.info("No package.json files found")
            return []
        
        try:
            findings = []
            for package_file in package_files:
                package_findings = await self._run_npm_audit_analysis(package_file, config)
                findings.extend(package_findings)
            
            logger.info(f"npm audit analysis complete. Found {len(findings)} vulnerabilities")
            return findings
            
        except Exception as e:
            logger.error(f"Error running npm audit analysis: {e}")
            return []
    
    def _find_package_files(self, target_path: str) -> List[str]:
        """Find all package.json files in the target path"""
        path = Path(target_path)
        package_files = []
        
        if path.is_file() and path.name == 'package.json':
            package_files.append(str(path.parent))
        elif path.is_dir():
            package_files.extend([
                str(f.parent) for f in path.rglob("package.json")
                if not any(exclude in str(f) for exclude in ['node_modules', '.git'])
            ])
        
        return package_files
    
    async def _run_npm_audit_analysis(self, project_path: str, config: Dict[str, Any]) -> List[Finding]:
        """Run npm audit analysis and parse results"""
        
        # Build npm audit command
        cmd = self._build_npm_audit_command(config)
        
        try:
            # Change to project directory and run npm audit
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=project_path
            )
            
            stdout, stderr = await process.communicate()
            
            # npm audit returns non-zero if vulnerabilities are found, which is expected
            if stderr and process.returncode not in [0, 1]:
                logger.warning(f"npm audit stderr: {stderr.decode()}")
            
            # Parse JSON output
            if stdout:
                return self._parse_npm_audit_output(stdout.decode(), project_path)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error running npm audit: {e}")
            return []
    
    def _build_npm_audit_command(self, config: Dict[str, Any]) -> List[str]:
        """Build npm audit command with appropriate options"""
        
        cmd = ["npm", "audit", "--json"]
        
        # Add audit level filter
        cmd.extend(["--audit-level", self.audit_level])
        
        # Production only
        if self.production_only:
            cmd.append("--production")
        
        # Package lock only
        if self.package_lock_only:
            cmd.append("--package-lock-only")
        
        # Additional options from config
        if config.get('dry_run', False):
            cmd.append("--dry-run")
        
        return cmd
    
    def _parse_npm_audit_output(self, output: str, project_path: str) -> List[Finding]:
        """Parse npm audit JSON output into Finding objects"""
        
        findings = []
        
        try:
            data = json.loads(output)
            vulnerabilities = data.get('vulnerabilities', {})
            
            for package_name, vuln_info in vulnerabilities.items():
                findings.extend(self._create_findings_from_vulnerability(package_name, vuln_info, project_path))
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse npm audit JSON output: {e}")
        
        return findings
    
    def _create_findings_from_vulnerability(self, package_name: str, vuln_info: Dict[str, Any], project_path: str) -> List[Finding]:
        """Create Finding objects from npm audit vulnerability"""
        
        findings = []
        
        try:
            # Extract vulnerability information
            name = vuln_info.get('name', package_name)
            severity = vuln_info.get('severity', 'moderate')
            via = vuln_info.get('via', [])
            effects = vuln_info.get('effects', [])
            range = vuln_info.get('range', '')
            nodes = vuln_info.get('nodes', [])
            fix_available = vuln_info.get('fixAvailable', False)
            
            # Process each vulnerability source
            if isinstance(via, list):
                for source in via:
                    if isinstance(source, dict):
                        finding = self._create_finding_from_source(
                            package_name, source, severity, project_path, fix_available
                        )
                        if finding:
                            findings.append(finding)
            
            # If no detailed sources, create a general finding
            if not findings and via:
                finding = self._create_general_finding(
                    package_name, vuln_info, project_path
                )
                if finding:
                    findings.append(finding)
        
        except Exception as e:
            logger.error(f"Error creating findings from vulnerability: {e}")
        
        return findings
    
    def _create_finding_from_source(self, package_name: str, source: Dict[str, Any], severity: str, project_path: str, fix_available: bool) -> Optional[Finding]:
        """Create Finding object from vulnerability source"""
        
        try:
            # Extract source information
            source_name = source.get('source', package_name)
            title = source.get('title', 'Unknown vulnerability')
            url = source.get('url', '')
            cves = source.get('cves', [])
            cvss = source.get('cvss', {})
            range_affected = source.get('range', '')
            
            # Map npm severity to standard severity
            mapped_severity = self._map_severity(severity)
            
            # Create description
            description = f"Vulnerability in {package_name}: {title}"
            if range_affected:
                description += f" (affected versions: {range_affected})"
            if fix_available:
                description += " - Fix available"
            
            # Create tool evidence
            tool_evidence = ToolEvidence(
                tool_name=self.tool_name,
                rule_id=f"npm_audit_{source_name}",
                rule_name=title,
                confidence=self._calculate_confidence_score(source),
                raw_output=json.dumps(source, indent=2)
            )
            
            # Create finding
            finding = Finding(
                id=f"NPM_AUDIT_{source_name}_{hash(package_name + title) % 10000}",
                title=f"npm audit: {title}",
                description=description,
                severity=mapped_severity,
                category=self._categorize_vulnerability(title, cves),
                file=str(Path(project_path) / "package.json"),
                line_number=0,
                code_snippet=f"Dependency: {package_name}",
                confidence_score=self._calculate_confidence_score(source),
                tool_evidence=[tool_evidence],
                cve_ids=cves,
                references=[url] if url else [],
                cvss_score=cvss.get('score') if cvss else None
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error creating finding from source: {e}")
            return None
    
    def _create_general_finding(self, package_name: str, vuln_info: Dict[str, Any], project_path: str) -> Optional[Finding]:
        """Create general Finding object when detailed source info is not available"""
        
        try:
            severity = vuln_info.get('severity', 'moderate')
            via = vuln_info.get('via', [])
            fix_available = vuln_info.get('fixAvailable', False)
            
            # Create description
            description = f"Vulnerability detected in {package_name}"
            if isinstance(via, list) and via:
                description += f" via {', '.join(str(v) for v in via)}"
            if fix_available:
                description += " - Fix available"
            
            # Map npm severity to standard severity
            mapped_severity = self._map_severity(severity)
            
            # Create tool evidence
            tool_evidence = ToolEvidence(
                tool_name=self.tool_name,
                rule_id=f"npm_audit_{package_name}",
                rule_name=f"Vulnerability in {package_name}",
                confidence=70,
                raw_output=json.dumps(vuln_info, indent=2)
            )
            
            # Create finding
            finding = Finding(
                id=f"NPM_AUDIT_{package_name}_{hash(str(vuln_info)) % 10000}",
                title=f"npm audit: Vulnerability in {package_name}",
                description=description,
                severity=mapped_severity,
                category='dependency',
                file=str(Path(project_path) / "package.json"),
                line_number=0,
                code_snippet=f"Dependency: {package_name}",
                confidence_score=70,
                tool_evidence=[tool_evidence]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error creating general finding: {e}")
            return None
    
    def _map_severity(self, npm_severity: str) -> str:
        """Map npm audit severity to standard severity levels"""
        severity_map = {
            'critical': 'high',
            'high': 'high',
            'moderate': 'medium', 
            'low': 'low',
            'info': 'low'
        }
        return severity_map.get(npm_severity.lower(), 'medium')
    
    def _calculate_confidence_score(self, source: Dict[str, Any]) -> int:
        """Calculate confidence score based on vulnerability information"""
        score = 50  # Base score
        
        # Increase confidence if CVEs are present
        if source.get('cves'):
            score += 20
        
        # Increase confidence if CVSS score is available
        if source.get('cvss', {}).get('score'):
            score += 15
        
        # Increase confidence if official source
        url = source.get('url', '')
        if 'npmjs.com' in url or 'github.com' in url or 'snyk.io' in url:
            score += 10
        
        return min(score, 95)
    
    def _categorize_vulnerability(self, title: str, cves: List[str]) -> str:
        """Categorize vulnerability based on title and CVEs"""
        
        title_lower = title.lower()
        
        # Categorize based on common vulnerability patterns
        if any(term in title_lower for term in ['xss', 'cross-site', 'script']):
            return 'xss'
        elif any(term in title_lower for term in ['sql', 'injection', 'sqli']):
            return 'sql_injection'
        elif any(term in title_lower for term in ['csrf', 'cross-site request']):
            return 'csrf'
        elif any(term in title_lower for term in ['dos', 'denial of service', 'crash']):
            return 'dos'
        elif any(term in title_lower for term in ['rce', 'remote code', 'code execution']):
            return 'code_injection'
        elif any(term in title_lower for term in ['path traversal', 'directory traversal']):
            return 'file_handling'
        elif any(term in title_lower for term in ['prototype pollution']):
            return 'prototype_pollution'
        elif any(term in title_lower for term in ['memory', 'buffer', 'overflow']):
            return 'memory_safety'
        elif any(term in title_lower for term in ['regex', 'redos', 'regular expression']):
            return 'regex_dos'
        elif any(term in title_lower for term in ['bypass', 'authentication', 'authorization']):
            return 'authentication'
        else:
            return 'dependency'
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return ['package.json', 'package-lock.json', 'yarn.lock']
    
    def get_vulnerability_info(self) -> Dict[str, Any]:
        """Get information about npm audit vulnerability categories"""
        return {
            'severity_levels': ['critical', 'high', 'moderate', 'low', 'info'],
            'vulnerability_categories': {
                'xss': 'Cross-Site Scripting vulnerabilities',
                'sql_injection': 'SQL injection vulnerabilities',
                'csrf': 'Cross-Site Request Forgery',
                'dos': 'Denial of Service vulnerabilities',
                'code_injection': 'Remote code execution vulnerabilities',
                'file_handling': 'Path traversal vulnerabilities',
                'prototype_pollution': 'Prototype pollution vulnerabilities',
                'memory_safety': 'Memory safety issues',
                'regex_dos': 'Regular expression denial of service',
                'authentication': 'Authentication bypass vulnerabilities',
                'dependency': 'General dependency vulnerabilities'
            },
            'data_sources': [
                'npm Advisory Database',
                'GitHub Security Advisories', 
                'Snyk Vulnerability Database',
                'CVE Database'
            ],
            'fix_types': [
                'Automatic fix available',
                'Manual review required',
                'Breaking change required',
                'No fix available'
            ]
        }
    
    def get_package_analysis_info(self) -> Dict[str, Any]:
        """Get Node.js package analysis information"""
        return {
            'package_lock_support': True,
            'yarn_lock_support': True,
            'dev_dependencies': True,
            'peer_dependencies': True,
            'optional_dependencies': True,
            'transitive_analysis': True,
            'fix_suggestions': True
        }
    
    def get_version(self) -> str:
        """Get npm audit version"""
        try:
            result = subprocess.run(
                ["npm", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return f"npm-{result.stdout.strip()}"
            return "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "not-available"
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """
        Convert npm audit JSON output to normalized Finding objects
        
        Args:
            raw_output: JSON output from npm audit
            metadata: Additional metadata
            
        Returns:
            List of normalized Finding objects
        """
        findings = []
        
        try:
            if not raw_output.strip():
                return findings
                
            data = json.loads(raw_output)
            
            # Process vulnerabilities
            vulnerabilities = data.get('vulnerabilities', {})
            
            for package_name, vuln_data in vulnerabilities.items():
                if isinstance(vuln_data, dict):
                    via = vuln_data.get('via', [])
                    
                    # Handle both direct vulnerabilities and array of vulnerabilities
                    vuln_list = via if isinstance(via, list) else [via]
                    
                    for vuln in vuln_list:
                        if isinstance(vuln, dict):
                            finding = Finding(
                                id=f"npm-audit-{package_name}-{vuln.get('cwe', [0])[0] if vuln.get('cwe') else len(findings)}",
                                title=f"npm audit: {vuln.get('title', f'Vulnerability in {package_name}')}",
                                description=vuln.get('url', 'No description available'),
                                severity=self._map_severity(vuln.get('severity', 'moderate')),
                                category='dependency',
                                file='package.json',
                                line=0,
                                column=0,
                                tool='npm-audit',
                                evidence=ToolEvidence(
                                    raw_output=json.dumps(vuln),
                                    confidence='high',
                                    tool_version=self.get_version()
                                ),
                                owasp=['A06:2021 - Vulnerable and Outdated Components'],
                                cwe=[f"CWE-{cwe}" for cwe in vuln.get('cwe', [])],
                                references=[vuln.get('url')] if vuln.get('url') else []
                            )
                            findings.append(finding)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse npm audit output as JSON: {e}")
        except Exception as e:
            logger.error(f"Error normalizing npm audit findings: {e}")
        
        return findings