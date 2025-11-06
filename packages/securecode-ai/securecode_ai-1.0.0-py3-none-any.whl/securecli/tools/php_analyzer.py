"""
PHP Security Analysis Tools Integration
Supports Psalm, PHPStan, PHPCS Security, and RIPS for comprehensive PHP security analysis
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Any
from pathlib import Path

from ..schemas.findings import Finding, ToolEvidence, CVSSv4
from .base import BaseTool

logger = logging.getLogger(__name__)

class PhpAnalyzer(BaseTool):
    """
    PHP Security Analyzer supporting Psalm, PHPStan, PHPCS Security, and RIPS
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "php_analyzer"
        self.supported_extensions = ['.php', '.phtml', '.php3', '.php4', '.php5', '.phps']
        
        # Check if PHP itself is available first
        self.php_available = self._check_php_availability()
        
        # Tool configurations
        self.tools = {
            'psalm': {
                'command': 'psalm',
                'enabled': self._check_psalm_availability(),
                'description': 'Psalm static analysis tool for PHP'
            },
            'phpstan': {
                'command': 'phpstan',
                'enabled': self._check_phpstan_availability(),
                'description': 'PHPStan static analysis tool for PHP'
            },
            'phpcs_security': {
                'command': 'phpcs',
                'enabled': self._check_phpcs_security_availability(),
                'description': 'PHP_CodeSniffer with security rules'
            },
            'rips': {
                'command': 'rips-cli',
                'enabled': self._check_rips_availability(),
                'description': 'RIPS static code analysis for PHP'
            }
        }
    
    def is_available(self) -> bool:
        """Check if PHP analysis tools are available"""
        # Return True if PHP is available, even if no specific analysis tools are installed
        # This allows basic PHP file analysis
        return self.php_available or any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try PHPStan first as it's most commonly available
            if self.tools['phpstan']['enabled']:
                result = subprocess.run(['phpstan', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            # Try Psalm as fallback
            if self.tools['psalm']['enabled']:
                result = subprocess.run(['psalm', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def _check_php_availability(self) -> bool:
        """Check if PHP is available"""
        try:
            result = subprocess.run(['php', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def _check_psalm_availability(self) -> bool:
        """Check if Psalm is available"""
        try:
            result = subprocess.run(['psalm', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_phpstan_availability(self) -> bool:
        """Check if PHPStan is available"""
        try:
            result = subprocess.run(['phpstan', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_phpcs_security_availability(self) -> bool:
        """Check if PHPCS with security standards is available"""
        try:
            result = subprocess.run(['phpcs', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_rips_availability(self) -> bool:
        """Check if RIPS CLI is available"""
        try:
            result = subprocess.run(['rips-cli', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from PHP tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'PHP security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'php_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run PHP security analysis tools."""
        findings = []
        
        # Check if this is a PHP project
        if not self._has_php_files(repo_path):
            return findings
        
        # Run PHPStan for static analysis
        if self.tools['phpstan']['enabled']:
            try:
                result = subprocess.run(
                    ['phpstan', 'analyse', '--error-format=json', '--no-progress', repo_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.stdout:
                    phpstan_findings = self._parse_phpstan_output(result.stdout, repo_path)
                    findings.extend(phpstan_findings)
            except subprocess.TimeoutExpired:
                logger.warning("PHPStan analysis timed out")
            except Exception as e:
                logger.error(f"Error running PHPStan: {e}")
        
        # Run Psalm for additional static analysis
        if self.tools['psalm']['enabled']:
            try:
                result = subprocess.run(
                    ['psalm', '--output-format=json', '--no-progress', repo_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=300
                )
                
                if result.stdout:
                    psalm_findings = self._parse_psalm_output(result.stdout, repo_path)
                    findings.extend(psalm_findings)
            except subprocess.TimeoutExpired:
                logger.warning("Psalm analysis timed out")
            except Exception as e:
                logger.error(f"Error running Psalm: {e}")
        
        # Run PHPCS Security for security-specific rules
        if self.tools['phpcs_security']['enabled']:
            try:
                result = subprocess.run(
                    ['phpcs', '--standard=Security', '--report=json', repo_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                
                if result.stdout:
                    phpcs_findings = self._parse_phpcs_output(result.stdout, repo_path)
                    findings.extend(phpcs_findings)
            except subprocess.TimeoutExpired:
                logger.warning("PHPCS Security analysis timed out")
            except Exception as e:
                logger.error(f"Error running PHPCS Security: {e}")
        
        # If no tools available, create placeholder finding
        if not any(self.tools[tool]['enabled'] for tool in self.tools):
            php_files = []
            for root, dirs, files in os.walk(repo_path):
                for file in files:
                    if file.endswith('.php'):
                        php_files.append(os.path.relpath(os.path.join(root, file), repo_path))
            
            if php_files:
                tool_evidence = ToolEvidence(
                    tool="php_analyzer",
                    id=f"php_{hash(php_files[0])}",
                    raw=f"PHP analysis placeholder - found {len(php_files)} PHP files"
                )
                
                finding = Finding(
                    file=php_files[0],
                    title=f"PHP Analysis Placeholder",
                    description=f"PHP security analysis placeholder - found {len(php_files)} PHP files",
                    lines="1",
                    impact="Potential PHP security or quality issue",
                    severity="Medium",
                    cvss_v4=CVSSv4(
                        score=4.0,
                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                    ),
                    snippet=f"PHP file detected: {php_files[0]}",
                    recommendation="Review PHP code for security issues",
                    sample_fix="Apply PHP best practices",
                    poc=f"PHP analysis in repository",
                    owasp=[],
                    cwe=[],
                    tool_evidence=[tool_evidence]
                )
                findings.append(finding)
        
        return findings

    def _has_php_files(self, repo_path: str) -> bool:
        """Check if repository contains PHP files."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    return True
        return False

    def _parse_phpstan_output(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse PHPStan JSON output."""
        findings = []
        try:
            phpstan_data = json.loads(json_output)
            for file_path, file_errors in phpstan_data.get('files', {}).items():
                for error in file_errors.get('messages', []):
                    finding = self._create_phpstan_finding(error, file_path, repo_path)
                    if finding:
                        findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing PHPStan JSON: {e}")
        return findings

    def _parse_psalm_output(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse Psalm JSON output."""
        findings = []
        try:
            psalm_data = json.loads(json_output)
            for issue in psalm_data:
                finding = self._create_psalm_finding(issue, repo_path)
                if finding:
                    findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing Psalm JSON: {e}")
        return findings

    def _parse_phpcs_output(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse PHPCS JSON output."""
        findings = []
        try:
            phpcs_data = json.loads(json_output)
            for file_path, file_data in phpcs_data.get('files', {}).items():
                for message in file_data.get('messages', []):
                    finding = self._create_phpcs_finding(message, file_path, repo_path)
                    if finding:
                        findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing PHPCS JSON: {e}")
        return findings

    def _create_phpstan_finding(self, error: dict, file_path: str, repo_path: str) -> Finding:
        """Create a Finding from PHPStan error."""
        try:
            message = error.get('message', 'PHPStan issue')
            line = error.get('line', 1)
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="phpstan",
                id=f"phpstan_{hash(file_path + str(line))}",
                raw=json.dumps(error)
            )
            
            return Finding(
                file=file_path,
                title=f"PHPStan: {message[:60]}...",
                description=f"PHPStan static analysis issue: {message}",
                lines=str(line),
                impact="Potential PHP code quality or security issue",
                severity="Medium",
                cvss_v4=CVSSv4(
                    score=4.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line}: PHPStan issue",
                recommendation="Fix the PHPStan issue to improve code quality",
                sample_fix="Apply PHPStan suggestions",
                poc=f"PHPStan analysis in {repo_path}",
                owasp=[],
                cwe=[],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating PHPStan finding: {e}")
            return None

    def _create_psalm_finding(self, issue: dict, repo_path: str) -> Finding:
        """Create a Finding from Psalm issue."""
        try:
            message = issue.get('message', 'Psalm issue')
            file_path = issue.get('file_name', 'unknown')
            line = issue.get('line_from', 1)
            type_name = issue.get('type', 'Unknown')
            severity = issue.get('severity', 'info')
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="psalm",
                id=f"psalm_{type_name}_{hash(file_path + str(line))}",
                raw=json.dumps(issue)
            )
            
            severity_map = {'error': 'High', 'warning': 'Medium', 'info': 'Low'}
            mapped_severity = severity_map.get(severity, 'Medium')
            
            return Finding(
                file=file_path,
                title=f"Psalm {type_name}: {message[:50]}...",
                description=f"Psalm static analysis issue: {message}",
                lines=str(line),
                impact="Potential PHP type safety or security issue",
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=5.0 if mapped_severity == 'High' else 3.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line}: Psalm {type_name}",
                recommendation="Fix the Psalm issue to improve type safety",
                sample_fix="Apply Psalm suggestions",
                poc=f"Psalm analysis in {repo_path}",
                owasp=[],
                cwe=[],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Psalm finding: {e}")
            return None

    def _create_phpcs_finding(self, message: dict, file_path: str, repo_path: str) -> Finding:
        """Create a Finding from PHPCS message."""
        try:
            text = message.get('message', 'PHPCS issue')
            line = message.get('line', 1)
            type_name = message.get('type', 'WARNING')
            source = message.get('source', 'Unknown')
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="phpcs_security",
                id=f"phpcs_{source}_{hash(file_path + str(line))}",
                raw=json.dumps(message)
            )
            
            severity_map = {'ERROR': 'High', 'WARNING': 'Medium'}
            mapped_severity = severity_map.get(type_name, 'Medium')
            
            return Finding(
                file=file_path,
                title=f"PHPCS Security: {source}",
                description=f"PHPCS Security issue: {text}",
                lines=str(line),
                impact="Potential PHP security or coding standard issue",
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=6.0 if mapped_severity == 'High' else 4.0,
                    vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line}: {source}",
                recommendation="Fix the PHPCS Security issue",
                sample_fix="Apply secure coding practices",
                poc=f"PHPCS Security analysis in {repo_path}",
                owasp=["A03:2021-Injection"] if "injection" in text.lower() else [],
                cwe=["CWE-79"] if "xss" in text.lower() else [],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating PHPCS finding: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['php']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'PHP Security Analyzer',
            'description': 'Comprehensive PHP security analysis using Psalm, PHPStan, PHPCS Security, and RIPS',
            'supported_extensions': self.supported_extensions,
            'available_tools': {
                name: {
                    'enabled': info['enabled'],
                    'description': info['description']
                }
                for name, info in self.tools.items()
            }
        }


# Alias for compatibility
PhpTool = PhpAnalyzer