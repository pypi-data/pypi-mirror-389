"""
Rust Security Analysis Tools Integration
Supports Clippy and Cargo Audit for comprehensive Rust security analysis
"""

import logging
import subprocess
import os
import json
from typing import Dict, List, Any
from pathlib import Path

from ..schemas.findings import Finding, ToolEvidence
from .base import BaseTool

logger = logging.getLogger(__name__)

class RustAnalyzer(BaseTool):
    """
    Rust Security Analyzer supporting Clippy and Cargo Audit
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "rust_analyzer"
        self.supported_extensions = ['.rs', '.toml']
        
        # Add cargo bin to PATH if it exists
        import os
        cargo_bin = os.path.expanduser('~/.cargo/bin')
        if os.path.exists(cargo_bin):
            current_path = os.environ.get('PATH', '')
            if cargo_bin not in current_path:
                os.environ['PATH'] = f"{cargo_bin}:{current_path}"
    
    def is_available(self) -> bool:
        """Check if Rust analysis tools are available"""
        rustc_available = self._check_rustc_availability()
        clippy_available = self._check_clippy_availability()
        
        # Return True if Rust is available (rustc or clippy)
        return rustc_available or clippy_available
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            result = subprocess.run(['cargo', 'clippy', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            if result.returncode == 0:
                return result.stdout.strip()
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"
    
    def _check_rustc_availability(self) -> bool:
        """Check if rustc (Rust compiler) is available"""
        try:
            result = subprocess.run(['rustc', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_clippy_availability(self) -> bool:
        """Check if Clippy is available"""
        try:
            result = subprocess.run(['cargo', 'clippy', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_cargo_audit_availability(self) -> bool:
        """Check if cargo-audit is installed"""
        try:
            result = subprocess.run(['cargo', 'audit', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Rust tools to standard format."""
        normalized = []
        for finding in raw_findings:
            # Handle Clippy findings
            if finding.get('tool') == 'clippy':
                normalized.append(Finding(
                    title=finding.get('message', 'Clippy warning'),
                    description=finding.get('rendered', ''),
                    file_path=finding.get('spans', [{}])[0].get('file_name', ''),
                    line_number=finding.get('spans', [{}])[0].get('line_start', 0),
                    severity=self._map_clippy_level(finding.get('level', 'warning')),
                    tool='clippy',
                    rule_id=finding.get('code', {}).get('code', '')
                ))
            # Handle Cargo Audit findings
            elif finding.get('tool') == 'cargo-audit':
                normalized.append(Finding(
                    title=f"Vulnerability in {finding.get('package', {}).get('name', 'unknown')}",
                    description=finding.get('advisory', {}).get('description', ''),
                    file_path='Cargo.toml',
                    line_number=1,
                    severity=self._map_audit_severity(finding.get('advisory', {}).get('severity', 'medium')),
                    tool='cargo-audit',
                    rule_id=finding.get('advisory', {}).get('id', '')
                ))
        return normalized

    def _create_clippy_finding(self, clippy_finding: dict, repo_path: str) -> Finding:
        """Create a Finding from Clippy result."""
        try:
            message = clippy_finding.get('message', {})
            spans = message.get('spans', [{}])
            main_span = spans[0] if spans else {}
            
            file_name = main_span.get('file_name', 'unknown')
            line_start = main_span.get('line_start', 0)
            code = message.get('code', {}).get('code', 'clippy')
            level = message.get('level', 'warning')
            text = message.get('message', 'Clippy warning')
            
            # Make file path relative
            if file_name.startswith(repo_path):
                file_name = os.path.relpath(file_name, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="clippy",
                id=f"clippy_{code}_{hash(file_name + str(line_start))}",
                raw=json.dumps(clippy_finding)
            )
            
            return Finding(
                file=file_name,
                title=f"Clippy: {text[:60]}...",
                description=f"Clippy {level}: {text}",
                lines=str(line_start),
                impact=f"Code quality and potential security issue detected by Clippy",
                severity=self._map_clippy_level(level).title(),
                cvss_v4=self._get_clippy_cvss(level),
                snippet=main_span.get('text', '')[:200] or f"Line {line_start}",
                recommendation="Address the Clippy warning to improve code quality and security",
                sample_fix="Apply suggested Clippy fix or refactor the code",
                poc=f"cargo clippy in {repo_path}",
                owasp=[],
                cwe=[],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Clippy finding: {e}")
            return None

    def _create_cargo_audit_finding(self, vuln: dict, repo_path: str) -> Finding:
        """Create a Finding from Cargo Audit result."""
        try:
            package = vuln.get('package', {})
            advisory = vuln.get('advisory', {})
            
            package_name = package.get('name', 'unknown')
            version = package.get('version', 'unknown')
            advisory_id = advisory.get('id', 'unknown')
            title = advisory.get('title', 'Dependency vulnerability')
            description = advisory.get('description', '')
            severity = advisory.get('severity', 'medium')
            
            tool_evidence = ToolEvidence(
                tool="cargo-audit",
                id=f"cargo_audit_{advisory_id}_{package_name}",
                raw=json.dumps(vuln)
            )
            
            return Finding(
                file="Cargo.toml",
                title=f"Vulnerable dependency: {package_name}",
                description=f"Security vulnerability in {package_name} v{version}: {description}",
                lines="1",
                impact=f"Dependency vulnerability could compromise application security",
                severity=self._map_audit_severity(severity).title(),
                cvss_v4=self._get_audit_cvss(severity),
                snippet=f"Dependency: {package_name} = \"{version}\"",
                recommendation=f"Update {package_name} to a patched version",
                sample_fix=f"cargo update -p {package_name}",
                poc=f"cargo audit in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-1104"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Cargo Audit finding: {e}")
            return None

    def _get_clippy_cvss(self, level: str) -> dict:
        """Get CVSS score for Clippy finding."""
        scores = {'error': 6.0, 'warning': 4.0, 'note': 2.0, 'help': 1.0}
        score = scores.get(level.lower(), 4.0)
        return CVSSv4(
            score=score,
            vector=f"CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
        )

    def _get_audit_cvss(self, severity: str) -> dict:
        """Get CVSS score for Cargo Audit finding."""
        scores = {'critical': 9.0, 'high': 7.5, 'medium': 5.0, 'low': 2.5}
        score = scores.get(severity.lower(), 5.0)
        return CVSSv4(
            score=score,
            vector=f"CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
        )

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Rust security analysis tools."""
        findings = []
        
        # Check if this is a Rust project
        if not self._has_rust_files(repo_path):
            return findings
        
        # Run Clippy for code quality and security lints
        try:
            clippy_result = subprocess.run(
                ['cargo', 'clippy', '--message-format=json', '--', '-W', 'clippy::all'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if clippy_result.stdout:
                for line in clippy_result.stdout.strip().split('\n'):
                    if line and line.startswith('{'):
                        try:
                            clippy_finding = json.loads(line)
                            if clippy_finding.get('reason') == 'compiler-message':
                                finding = self._create_clippy_finding(clippy_finding, repo_path)
                                if finding:
                                    findings.append(finding)
                        except json.JSONDecodeError:
                            continue
        except subprocess.TimeoutExpired:
            logger.warning("Clippy analysis timed out")
        except Exception as e:
            logger.error(f"Error running Clippy: {e}")
        
        # Run Cargo Audit for vulnerability scanning
        try:
            audit_result = subprocess.run(
                ['cargo', 'audit', '--format', 'json'],
                cwd=repo_path,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if audit_result.stdout:
                try:
                    audit_data = json.loads(audit_result.stdout)
                    for vuln in audit_data.get('vulnerabilities', {}).get('list', []):
                        finding = self._create_cargo_audit_finding(vuln, repo_path)
                        if finding:
                            findings.append(finding)
                except json.JSONDecodeError:
                    pass
        except subprocess.TimeoutExpired:
            logger.warning("Cargo audit timed out")
        except Exception as e:
            logger.error(f"Error running Cargo Audit: {e}")
        
        return findings

    def _has_rust_files(self, repo_path: str) -> bool:
        """Check if repository contains Rust files."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.rs') or file == 'Cargo.toml':
                    return True
        return False

    def _map_clippy_level(self, level: str) -> str:
        """Map Clippy severity levels to standard severity."""
        mapping = {
            'error': 'high',
            'warning': 'medium',
            'note': 'low',
            'help': 'info'
        }
        return mapping.get(level.lower(), 'medium')

    def _map_audit_severity(self, severity: str) -> str:
        """Map Cargo Audit severity to standard severity."""
        mapping = {
            'critical': 'critical',
            'high': 'high',
            'medium': 'medium',
            'low': 'low'
        }
        return mapping.get(severity.lower(), 'medium')


# Alias for compatibility
RustTool = RustAnalyzer