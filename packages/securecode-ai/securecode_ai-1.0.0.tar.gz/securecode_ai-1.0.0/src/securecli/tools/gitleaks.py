"""
Gitleaks secret detection scanner integration
Detects secrets, credentials, and sensitive data in repositories
"""

import json
import tempfile
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import SecurityScannerBase
from ..schemas.findings import Finding, ToolEvidence


class GitleaksScanner(SecurityScannerBase):
    """Gitleaks secret detection scanner"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.config_path = self.tool_config.get('config_path')
        self.detect_mode = self.tool_config.get('detect_mode', 'detect')
        
        # Secret patterns to detect
        self.additional_patterns = self.tool_config.get('additional_patterns', [])
    
    async def scan(self, target_path: str, config: Dict[str, Any]) -> List[Finding]:
        """Run Gitleaks scan on target"""
        if not self.is_available():
            raise RuntimeError("Gitleaks is not available")
        
        # Ensure target_path is a string
        if isinstance(target_path, dict):
            target_path = target_path.get('path', '.')
        target_path = str(target_path)
        
        # Prepare command
        command = self._build_command(target_path, config=config)
        
        # Run scan
        stdout, stderr, exit_code = await self._run_command(command, cwd=target_path)
        
        # Parse results
        findings = []
        metadata = {
            'target_path': target_path,
            'detect_mode': self.detect_mode,
            'scan_stats': self._extract_scan_stats(stderr)
        }
        
        if stdout.strip():
            try:
                findings = self.normalize_findings(stdout, metadata)
            except json.JSONDecodeError as e:
                metadata['parse_error'] = str(e)
        
        return findings
    
    def _build_command(self, target_path: str, config: Dict[str, Any]) -> List[str]:
        """Build Gitleaks command"""
        command = ['gitleaks']
        
        # Detection mode
        mode = config.get('mode', self.detect_mode)
        command.append(mode)
        
        # Source path
        command.extend(['--source', target_path])
        
        # Output format
        command.extend(['--format', 'json'])
        
        # Configuration
        if self.config_path and Path(self.config_path).exists():
            command.extend(['--config', self.config_path])
        elif config.get('config'):
            command.extend(['--config', config['config']])
        
        # Additional options
        if config.get('verbose'):
            command.append('--verbose')
        
        # Redact secrets in output
        if self.config.get('redact.enabled', True):
            command.append('--redact')
        
        # Exit code handling
        command.append('--exit-code=2')  # Exit with code 2 if leaks found
        
        return command
    
    def _extract_scan_stats(self, stderr: str) -> Dict[str, Any]:
        """Extract scan statistics from stderr"""
        stats = {
            'files_scanned': 0,
            'commits_scanned': 0,
            'rules_loaded': 0
        }
        
        # Parse stderr for statistics
        for line in stderr.split('\n'):
            if 'scanning' in line.lower():
                # Extract file/commit counts
                import re
                file_match = re.search(r'(\d+)\s+files?', line)
                if file_match:
                    stats['files_scanned'] = int(file_match.group(1))
                
                commit_match = re.search(r'(\d+)\s+commits?', line)
                if commit_match:
                    stats['commits_scanned'] = int(commit_match.group(1))
        
        return stats
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """Convert Gitleaks output to normalized findings"""
        findings = []
        
        try:
            # Gitleaks outputs one JSON object per line
            for line in raw_output.strip().split('\n'):
                if line.strip():
                    leak = json.loads(line)
                    finding = self._convert_gitleaks_result(leak, metadata)
                    if finding:
                        findings.append(finding)
        
        except json.JSONDecodeError as e:
            # Create error finding
            findings.append(Finding(
                file="unknown",
                title="Gitleaks Parse Error",
                description=f"Failed to parse Gitleaks output: {e}",
                lines="unknown",
                impact="Could not analyze secret detection results",
                severity="Medium",
                cvss_v4={"score": 5.0, "vector": "CVSS:4.0/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:N/A:N"},
                owasp=["A02:2021"],
                cwe=["CWE-200"],
                snippet="",
                recommendation="Review Gitleaks configuration and output",
                sample_fix="",
                poc="",
                references=["https://github.com/gitleaks/gitleaks"],
                tool_evidence=[ToolEvidence(
                    tool="gitleaks",
                    id="parse_error",
                    raw=raw_output[:500]
                )]
            ))
        
        return findings
    
    def _convert_gitleaks_result(self, leak: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[Finding]:
        """Convert single Gitleaks result to Finding"""
        try:
            # Extract basic information
            rule_id = leak.get('RuleID', 'unknown')
            description = leak.get('Description', 'Secret detected')
            file_path = leak.get('File', 'unknown')
            line_number = leak.get('StartLine', 0)
            secret = leak.get('Secret', '')
            
            # Determine severity based on secret type
            severity = self._determine_secret_severity(rule_id, description)
            
            # Extract code snippet (redacted)
            snippet = self._extract_redacted_snippet(file_path, line_number, secret)
            
            # Map to security taxonomies
            cwes = self._map_secret_to_cwe(rule_id)
            owasp = ["A02:2021"]  # Cryptographic Failures
            
            # Calculate CVSS score
            cvss_score = self._calculate_secret_cvss(severity, rule_id)
            
            return Finding(
                file=file_path,
                title=f"Secret Detected: {description}",
                description=self._format_secret_description(leak),
                lines=str(line_number),
                impact=self._generate_secret_impact(rule_id, description),
                severity=severity,
                cvss_v4={
                    "score": cvss_score,
                    "vector": "CVSS:4.0/AV:N/AC:L/PR:N/UI:N/S:U/C:H/I:N/A:N"
                },
                owasp=owasp,
                cwe=cwes,
                snippet=snippet,
                recommendation=self._generate_secret_recommendation(rule_id),
                sample_fix=self._generate_secret_fix(rule_id),
                poc=self._generate_secret_poc(rule_id),
                references=self._get_secret_references(rule_id),
                tool_evidence=[ToolEvidence(
                    tool="gitleaks",
                    id=rule_id,
                    raw=json.dumps({k: v for k, v in leak.items() if k != 'Secret'}, indent=2)
                )]
            )
            
        except Exception as e:
            return None
    
    def _determine_secret_severity(self, rule_id: str, description: str) -> str:
        """Determine severity based on secret type"""
        high_severity_patterns = [
            'private-key', 'rsa-private-key', 'openssh-private-key',
            'aws-access-token', 'aws-secret-key',
            'github-pat', 'github-oauth',
            'stripe-secret-key', 'stripe-restricted-key',
            'openai-api-key',
            'database-password', 'db-password'
        ]
        
        medium_severity_patterns = [
            'api-key', 'access-token', 'auth-token',
            'jwt', 'bearer-token',
            'webhook-secret',
            'encryption-key'
        ]
        
        rule_lower = rule_id.lower()
        desc_lower = description.lower()
        
        for pattern in high_severity_patterns:
            if pattern in rule_lower or pattern in desc_lower:
                return 'High'
        
        for pattern in medium_severity_patterns:
            if pattern in rule_lower or pattern in desc_lower:
                return 'Medium'
        
        return 'Medium'  # Default for secrets
    
    def _extract_redacted_snippet(self, file_path: str, line_number: int, secret: str) -> str:
        """Extract code snippet with secret redacted"""
        try:
            snippet = self._extract_code_snippet(file_path, line_number)
            
            # Redact the secret
            if secret and len(secret) > 4:
                redacted = secret[:2] + '*' * (len(secret) - 4) + secret[-2:]
                snippet = snippet.replace(secret, redacted)
            
            return snippet
            
        except Exception:
            return f"// Secret found in {file_path}:{line_number} (redacted)"
    
    def _map_secret_to_cwe(self, rule_id: str) -> List[str]:
        """Map secret type to CWE"""
        cwe_mapping = {
            'private-key': ['CWE-312', 'CWE-798'],
            'password': ['CWE-798'],
            'api-key': ['CWE-798', 'CWE-200'],
            'token': ['CWE-798', 'CWE-200'],
            'secret': ['CWE-798'],
            'credential': ['CWE-798'],
            'auth': ['CWE-798', 'CWE-306'],
        }
        
        rule_lower = rule_id.lower()
        
        for pattern, cwes in cwe_mapping.items():
            if pattern in rule_lower:
                return cwes
        
        return ['CWE-798']  # Use of Hard-coded Credentials
    
    def _calculate_secret_cvss(self, severity: str, rule_id: str) -> float:
        """Calculate CVSS score for secret"""
        base_scores = {
            'High': 8.5,
            'Medium': 6.5,
            'Low': 4.0
        }
        
        score = base_scores.get(severity, 6.5)
        
        # Adjust based on secret type
        if 'private-key' in rule_id.lower():
            score = min(10.0, score + 1.0)
        elif 'aws' in rule_id.lower() or 'cloud' in rule_id.lower():
            score = min(10.0, score + 0.8)
        
        return round(score, 1)
    
    def _format_secret_description(self, leak: Dict[str, Any]) -> str:
        """Format detailed description for secret"""
        rule_id = leak.get('RuleID', 'unknown')
        description = leak.get('Description', 'Secret detected')
        file_path = leak.get('File', 'unknown')
        line_number = leak.get('StartLine', 0)
        
        desc = f"Secret Type: {rule_id}\n"
        desc += f"Description: {description}\n"
        desc += f"Location: {file_path}:{line_number}\n"
        
        # Add commit information if available
        if 'Commit' in leak:
            desc += f"Commit: {leak['Commit']}\n"
        
        if 'Author' in leak:
            desc += f"Author: {leak['Author']}\n"
        
        if 'Date' in leak:
            desc += f"Date: {leak['Date']}\n"
        
        desc += "\nThis secret should be removed from the codebase and rotated if actively used."
        
        return desc
    
    def _generate_secret_impact(self, rule_id: str, description: str) -> str:
        """Generate impact description for secret"""
        impact_map = {
            'private-key': 'Attacker could impersonate the system or decrypt sensitive data',
            'aws': 'Attacker could access AWS resources and data',
            'github': 'Attacker could access GitHub repositories and actions',
            'database': 'Attacker could access database with full privileges',
            'api-key': 'Attacker could access external services using these credentials',
            'stripe': 'Attacker could access payment processing capabilities',
            'openai': 'Attacker could use AI services at your expense',
            'webhook': 'Attacker could intercept or modify webhook communications'
        }
        
        rule_lower = rule_id.lower()
        desc_lower = description.lower()
        
        for pattern, impact in impact_map.items():
            if pattern in rule_lower or pattern in desc_lower:
                return impact
        
        return 'Exposed credentials could allow unauthorized access to systems or data'
    
    def _generate_secret_recommendation(self, rule_id: str) -> str:
        """Generate recommendation for secret remediation"""
        return """1. Remove the secret from the codebase immediately
2. Revoke/rotate the exposed credential
3. Use environment variables or secret management systems
4. Add the secret pattern to .gitignore or gitleaks config
5. Scan git history and clean if necessary
6. Implement pre-commit hooks to prevent future exposures"""
    
    def _generate_secret_fix(self, rule_id: str) -> str:
        """Generate sample fix for secret"""
        return """// Before: hardcoded secret
const apiKey = "sk-1234567890abcdef";

// After: use environment variable
const apiKey = process.env.API_KEY;

// Or use secret management
import { getSecret } from './secretManager';
const apiKey = await getSecret('api-key');"""
    
    def _generate_secret_poc(self, rule_id: str) -> str:
        """Generate PoC for secret exposure"""
        return """# Secret Exposure PoC
# 1. Clone repository
# 2. Search for exposed secret
# 3. Use secret to access associated service
# 4. Demonstrate unauthorized access"""
    
    def _get_secret_references(self, rule_id: str) -> List[str]:
        """Get references for secret types"""
        references = [
            "https://github.com/gitleaks/gitleaks",
            "https://owasp.org/Top10/A02_2021-Cryptographic_Failures/",
            "https://cwe.mitre.org/data/definitions/798.html"
        ]
        
        # Add specific references based on secret type
        if 'aws' in rule_id.lower():
            references.append("https://docs.aws.amazon.com/general/latest/gr/aws-access-keys-best-practices.html")
        elif 'github' in rule_id.lower():
            references.append("https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/managing-your-personal-access-tokens")
        elif 'private-key' in rule_id.lower():
            references.append("https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-ssh-keys")
        
        return references
    
    def is_available(self) -> bool:
        """Check if Gitleaks is available"""
        try:
            import subprocess
            result = subprocess.run(['gitleaks', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def get_version(self) -> str:
        """Get Gitleaks version"""
        try:
            import subprocess
            result = subprocess.run(['gitleaks', 'version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                # Extract version from output
                for line in result.stdout.split('\n'):
                    if 'version' in line.lower():
                        return line.strip()
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"