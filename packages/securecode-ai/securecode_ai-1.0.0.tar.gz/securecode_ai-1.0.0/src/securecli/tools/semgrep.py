"""
Semgrep security scanner integration
Static analysis for multiple languages with custom rules
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime

from .base import SecurityScannerBase, ScanResult
from ..schemas.findings import Finding, ToolEvidence, CVSSv4


class SemgrepScanner(SecurityScannerBase):
    """Semgrep static analysis scanner"""
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.rules_path = self.tool_config.get('rules_path')
        self.rule_config = self.tool_config.get('config', 'auto')
        
        # Default rule sets
        self.default_rulesets = [
            'p/security-audit',
            'p/secrets',
            'p/owasp-top-ten',
            'p/r2c-security-audit',
            'p/r2c-best-practices'
        ]
    
    async def scan(self, target_path: str, config: Dict[str, Any]) -> List[Finding]:
        """Run Semgrep scan on target"""
        if not self.is_available():
            raise RuntimeError("Semgrep is not available")
        
        # Prepare command
        command = self._build_command(target_path, config=config)
        
        # Run scan
        # Use current directory as cwd and provide absolute path to target
        cwd = os.getcwd()
        stdout, stderr, exit_code = await self._run_command(command, cwd=cwd)
        
        # Parse results
        findings = []
        metadata = {
            'target_path': target_path,
            'rules_used': self._get_rules_used(config),
            'scan_stats': self._extract_scan_stats(stderr)
        }
        
        if stdout.strip():
            try:
                semgrep_results = json.loads(stdout)
                findings = self.normalize_findings(stdout, metadata)
            except json.JSONDecodeError as e:
                metadata['parse_error'] = str(e)
        else:
            print("DEBUG: Semgrep stdout was empty")
        
        return findings
    
    def _build_command(self, target_path: str, config: Dict[str, Any]) -> List[str]:
        """Build Semgrep command"""
        command = ['semgrep']
        
        # Output format
        command.extend(['--json'])
        
        # Rules configuration
        if self.rules_path and Path(self.rules_path).exists():
            command.extend(['--config', self.rules_path])
        elif config.get('rules'):
            for rule in config['rules']:
                command.extend(['--config', rule])
        else:
            # Use default rulesets
            for ruleset in self.default_rulesets:
                command.extend(['--config', ruleset])
        
        # Additional options
        if config.get('severity_min'):
            severity_levels = {
                'low': ['ERROR', 'WARNING', 'INFO'],
                'medium': ['ERROR', 'WARNING'],
                'high': ['ERROR'],
                'critical': ['ERROR']
            }
            levels = severity_levels.get(config['severity_min'], ['ERROR', 'WARNING'])
            for level in levels:
                command.extend(['--severity', level])
        
        # Exclude patterns
        exclude_patterns = config.get('exclude', [])
        for pattern in exclude_patterns:
            command.extend(['--exclude', pattern])
        
        # Performance options
        command.extend(['--max-memory', '2048'])
        command.extend(['--timeout', str(self.timeout)])
        
        # Target path
        command.append(target_path)
        
        return command
    
    def _get_rules_used(self, config: Dict[str, Any]) -> List[str]:
        """Get list of rules that will be used"""
        if self.rules_path:
            return [self.rules_path]
        elif config.get('rules'):
            return config['rules']
        else:
            return self.default_rulesets
    
    def _extract_scan_stats(self, stderr: str) -> Dict[str, Any]:
        """Extract scan statistics from stderr"""
        stats = {
            'files_scanned': 0,
            'rules_loaded': 0,
            'scan_time': None
        }
        
        # Parse stderr for statistics
        for line in stderr.split('\n'):
            if 'scanned' in line.lower():
                # Extract file count
                import re
                match = re.search(r'(\d+)\s+files?', line)
                if match:
                    stats['files_scanned'] = int(match.group(1))
            
            elif 'rules loaded' in line.lower():
                match = re.search(r'(\d+)\s+rules?', line)
                if match:
                    stats['rules_loaded'] = int(match.group(1))
        
        return stats
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """Convert Semgrep output to normalized findings"""
        findings = []
        
        try:
            semgrep_data = json.loads(raw_output)
            
            results = semgrep_data.get('results', [])
            
            for result in results:
                finding = self._convert_semgrep_result(result, metadata)
                if finding:
                    findings.append(finding)
        
        except json.JSONDecodeError as e:
            # If JSON parsing fails, create a generic finding
            # If JSON parsing fails, create a generic finding
            findings.append(Finding(
                file="unknown",
                title="Semgrep Parse Error",
                description="Failed to parse Semgrep output",
                lines="unknown",
                impact="Could not analyze results",
                severity="Medium",
                cvss_v4={"score": 5.0, "vector": "CVSS:4.0/AV:N/AC:L/PR:N/UI:N/S:U/C:N/I:N/A:N"},
                owasp=[],
                cwe=[],
                snippet="",
                recommendation="Review Semgrep configuration and output",
                sample_fix="",
                poc="",
                references=[],
                tool_evidence=[ToolEvidence(
                    tool="semgrep",
                    id="parse_error",
                    raw=raw_output[:500]
                )]
            ))
        
        return findings
    
    def _convert_semgrep_result(self, result: Dict[str, Any], metadata: Dict[str, Any]) -> Optional[Finding]:
        """Convert single Semgrep result to Finding"""
        try:
            # Extract basic information
            rule_id = result.get('check_id', 'unknown')
            message = result.get('extra', {}).get('message', 'No description')
            severity = result.get('extra', {}).get('severity', 'WARNING')
            
            # File and location info
            file_path = result.get('path', 'unknown')
            start_line = result.get('start', {}).get('line', 0)
            end_line = result.get('end', {}).get('line', start_line)
            
            # Extract code snippet
            snippet = self._extract_code_snippet(file_path, start_line)
            
            # Normalize severity
            normalized_severity = self._map_semgrep_severity(severity)
            
            # Map to security taxonomies
            cwes = self._extract_cwes_from_rule(result)
            owasp = self._map_to_owasp(rule_id)
            
            # Calculate CVSS score
            cvss_score = self._calculate_cvss_score(normalized_severity, rule_id)
            
            # Extract references
            references = self._extract_references(result)
            
            finding = Finding(
                file=file_path,
                title=f"Semgrep: {message[:100] if message else 'Security Issue'}",
                description=message or "Semgrep detected a security issue",
                lines=f"{start_line}-{end_line}" if end_line != start_line else str(start_line),
                impact="Security vulnerability detected by Semgrep analysis",
                severity=normalized_severity,
                cvss_v4=CVSSv4(
                    score=cvss_score,
                    vector="CVSS:4.0/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N"
                ),
                owasp=owasp or [],
                cwe=cwes or [],
                snippet=snippet or f"Line {start_line}: Issue detected",
                recommendation="Review the code and apply appropriate security fixes",
                sample_fix="# Apply security best practices",
                poc="See Semgrep documentation for exploitation details",
                references=references or [],
                tool_evidence=[ToolEvidence(
                    tool="semgrep",
                    id=rule_id,
                    raw=json.dumps(result, indent=2)
                )]
            )
            
            return finding
            
        except Exception as e:
            # Return None for malformed results
            return None
    
    def _map_semgrep_severity(self, severity: str) -> str:
        """Map Semgrep severity to standard levels"""
        mapping = {
            'ERROR': 'High',
            'WARNING': 'Medium', 
            'INFO': 'Low'
        }
        return mapping.get(severity.upper(), 'Medium')
    
    def _extract_cwes_from_rule(self, result: Dict[str, Any]) -> List[str]:
        """Extract CWE IDs from Semgrep rule metadata"""
        cwes = []
        
        # Check rule metadata
        metadata = result.get('extra', {}).get('metadata', {})
        
        # Look for CWE references in various fields
        for field in ['cwe', 'references', 'source']:
            value = metadata.get(field, [])
            if isinstance(value, list):
                for item in value:
                    if isinstance(item, str) and 'CWE-' in item:
                        # Extract CWE-XXX patterns
                        import re
                        matches = re.findall(r'CWE-(\d+)', item)
                        for match in matches:
                            cwes.append(f"CWE-{match}")
        
        # Fallback to rule-based mapping
        if not cwes:
            rule_id = result.get('check_id', '')
            cwes = self._map_to_cwe(rule_id, result.get('extra', {}).get('message', ''))
        
        return list(set(cwes))  # Remove duplicates
    
    def _format_description(self, result: Dict[str, Any]) -> str:
        """Format detailed description from Semgrep result"""
        rule_id = result.get('check_id', 'unknown')
        message = result.get('extra', {}).get('message', 'No description')
        
        description = f"Rule: {rule_id}\n\n{message}"
        
        # Add additional context from metadata
        metadata = result.get('extra', {}).get('metadata', {})
        
        if 'shortDescription' in metadata:
            description += f"\n\nShort Description: {metadata['shortDescription']}"
        
        if 'category' in metadata:
            description += f"\nCategory: {metadata['category']}"
        
        return description
    
    def _generate_impact(self, result: Dict[str, Any]) -> str:
        """Generate impact description"""
        rule_id = result.get('check_id', '')
        
        # Impact templates based on rule patterns
        impact_patterns = {
            'sql-injection': 'Attacker could execute arbitrary SQL queries',
            'xss': 'Attacker could execute malicious scripts in user browsers',
            'path-traversal': 'Attacker could access files outside intended directory',
            'command-injection': 'Attacker could execute arbitrary system commands',
            'crypto': 'Cryptographic implementation may be vulnerable to attacks',
            'secrets': 'Hardcoded secrets could be exposed',
            'auth': 'Authentication bypass or weakness detected'
        }
        
        for pattern, impact in impact_patterns.items():
            if pattern in rule_id.lower():
                return impact
        
        return "Security vulnerability detected that could be exploited by attackers"
    
    def _generate_recommendation(self, result: Dict[str, Any]) -> str:
        """Generate fix recommendation"""
        rule_id = result.get('check_id', '')
        
        # Check if rule has built-in fix
        fix = result.get('extra', {}).get('fix')
        if fix:
            return f"Apply the suggested fix: {fix}"
        
        # Generic recommendations based on rule type
        rec_patterns = {
            'sql-injection': 'Use parameterized queries or prepared statements',
            'xss': 'Sanitize user input and use output encoding',
            'path-traversal': 'Validate and sanitize file paths',
            'command-injection': 'Avoid dynamic command execution, use safe APIs',
            'crypto': 'Use secure cryptographic algorithms and implementations',
            'secrets': 'Remove hardcoded secrets, use environment variables or secret management',
            'auth': 'Implement proper authentication and authorization checks'
        }
        
        for pattern, rec in rec_patterns.items():
            if pattern in rule_id.lower():
                return rec
        
        return "Follow secure coding practices to address this vulnerability"
    
    def _generate_sample_fix(self, result: Dict[str, Any]) -> str:
        """Generate sample fix code"""
        # Check if Semgrep provides a fix
        fix = result.get('extra', {}).get('fix')
        if fix:
            return fix
        
        # Generate basic fix templates
        rule_id = result.get('check_id', '')
        
        if 'sql-injection' in rule_id.lower():
            return """// Use parameterized queries
// Before: query = "SELECT * FROM users WHERE id = " + user_id
// After: 
PreparedStatement stmt = conn.prepareStatement("SELECT * FROM users WHERE id = ?");
stmt.setString(1, user_id);"""
        
        elif 'xss' in rule_id.lower():
            return """// Sanitize output
// Before: response.write(user_input)
// After: response.write(escapeHtml(user_input))"""
        
        return "// Apply appropriate security controls for this vulnerability type"
    
    def _generate_poc_from_result(self, result: Dict[str, Any]) -> str:
        """Generate PoC specific to the finding"""
        return self._generate_poc(None)  # Use base class implementation
    
    def _extract_references(self, result: Dict[str, Any]) -> List[str]:
        """Extract references from Semgrep rule"""
        references = []
        
        metadata = result.get('extra', {}).get('metadata', {})
        
        # Get references from metadata
        refs = metadata.get('references', [])
        if isinstance(refs, list):
            references.extend(refs)
        
        # Add rule source if available
        source = metadata.get('source')
        if source:
            references.append(source)
        
        # Add Semgrep rule URL
        rule_id = result.get('check_id', '')
        if rule_id:
            references.append(f"https://semgrep.dev/r/{rule_id}")
        
        return references
    
    def is_available(self) -> bool:
        """Check if Semgrep is available"""
        try:
            import subprocess
            result = subprocess.run(['semgrep', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
            return False
    
    def get_version(self) -> str:
        """Get Semgrep version"""
        try:
            import subprocess
            result = subprocess.run(['semgrep', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
        except Exception:
            pass
        return "unknown"