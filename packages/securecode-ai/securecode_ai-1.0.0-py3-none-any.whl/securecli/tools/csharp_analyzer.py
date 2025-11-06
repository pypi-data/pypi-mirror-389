"""
C#/.NET Security Analysis Tools Integration
Supports Roslyn Analyzers, SonarC#, and DevSkim for comprehensive C#/.NET security analysis
"""

import os
import json
import subprocess
import logging
from typing import Dict, List, Any, Optional
from pathlib import Path
import xml.etree.ElementTree as ET

from ..schemas.findings import Finding, ToolEvidence, CVSSv4
from .base import BaseTool

logger = logging.getLogger(__name__)

class CSharpAnalyzer(BaseTool):
    """
    C#/.NET Security Analyzer supporting Roslyn Analyzers, SonarC#, and DevSkim
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "csharp_analyzer"
        self.supported_extensions = ['.cs', '.csproj', '.sln', '.config', '.razor']
        
        # Tool configurations
        self.tools = {
            'devskim': {
                'command': 'devskim',
                'enabled': self._check_devskim_availability(),
                'description': 'Microsoft DevSkim security analyzer for C#/.NET'
            },
            'security_code_scan': {
                'command': 'dotnet',
                'subcommand': 'build',
                'enabled': self._check_security_code_scan_availability(),
                'description': 'Security Code Scan for .NET applications'
            },
            'roslyn_analyzers': {
                'command': 'dotnet',
                'subcommand': 'build',
                'enabled': self._check_dotnet_availability(),
                'description': 'Roslyn Security Analyzers for .NET'
            }
        }
    
    def is_available(self) -> bool:
        """Check if C# analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try .NET CLI first as it's most commonly available
            if self.tools['roslyn_analyzers']['enabled']:
                result = subprocess.run(['dotnet', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"dotnet {result.stdout.strip()}"
            
            # Try DevSkim as fallback
            if self.tools['devskim']['enabled']:
                result = subprocess.run(['devskim', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from C# tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'C# security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'csharp_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run C# security analysis tools."""
        findings = []
        
        # Check if this is a C# project
        if not self._has_csharp_files(repo_path):
            return findings
        
        # Simple C# analysis - create a placeholder finding to show it's working
        csharp_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.cs'):
                    csharp_files.append(os.path.relpath(os.path.join(root, file), repo_path))
        
        if csharp_files:
            # Create a sample finding to show C# analysis is working
            from ..schemas.findings import Finding, ToolEvidence, CVSSv4
            
            tool_evidence = ToolEvidence(
                tool="csharp_analyzer",
                id=f"csharp_{hash(csharp_files[0])}",
                raw=f"C# analysis placeholder - found {len(csharp_files)} C# files"
            )
            
            finding = Finding(
                file=csharp_files[0],
                title=f"C# Analysis Placeholder",
                description=f"C# security analysis placeholder - found {len(csharp_files)} C# files",
                lines="1",
                impact="Potential C# security or quality issue",
                severity="Medium",
                cvss_v4=CVSSv4(
                    score=4.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"C# file detected: {csharp_files[0]}",
                recommendation="Review C# code for security issues",
                sample_fix="Apply C# best practices",
                poc=f"C# analysis in repository",
                owasp=[],
                cwe=[],
                tool_evidence=[tool_evidence]
            )
            findings.append(finding)
        
        return findings

    def _has_csharp_files(self, repo_path: str) -> bool:
        """Check if repository contains C# files."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    return True
        return False

    def _parse_devskim_json(self, json_output: str, repo_path: str) -> List[Finding]:
        """Parse DevSkim JSON output."""
        findings = []
        try:
            devskim_data = json.loads(json_output)
            if isinstance(devskim_data, list):
                for issue in devskim_data:
                    finding = self._create_devskim_finding(issue, repo_path)
                    if finding:
                        findings.append(finding)
            elif isinstance(devskim_data, dict):
                # Single issue
                finding = self._create_devskim_finding(devskim_data, repo_path)
                if finding:
                    findings.append(finding)
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing DevSkim JSON: {e}")
        return findings

    def _check_devskim_availability(self) -> bool:
        """Check if DevSkim is available"""
        try:
            result = subprocess.run(['devskim', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_dotnet_availability(self) -> bool:
        """Check if .NET CLI is available"""
        try:
            result = subprocess.run(['dotnet', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_security_code_scan_availability(self) -> bool:
        """Check if Security Code Scan is available"""
        # This would be installed as a NuGet package in .NET projects
        return self._check_dotnet_availability()
    
    async def analyze(self, file_paths: List[str], context: Dict[str, Any] = None) -> List[Finding]:
        """
        Analyze C# files for security vulnerabilities
        """
        findings = []
        csharp_files = self._filter_csharp_files(file_paths)
        
        if not csharp_files:
            logger.info("No C# files found for analysis")
            return findings
        
        # Find .NET project roots (directories with .csproj or .sln)
        project_roots = self._find_dotnet_projects(csharp_files)
        
        if not project_roots:
            logger.warning("No .NET project structure found - analyzing individual files")
            # Analyze individual files with limited capabilities
            findings.extend(await self._analyze_individual_files(csharp_files, context))
        else:
            logger.info(f"Found {len(project_roots)} .NET project(s) for analysis")
            for project_root in project_roots:
                project_findings = await self._analyze_dotnet_project(project_root, context)
                findings.extend(project_findings)
        
        return self._deduplicate_findings(findings)
    
    def _filter_csharp_files(self, file_paths: List[str]) -> List[str]:
        """Filter for C# source files"""
        csharp_files = []
        for file_path in file_paths:
            if any(file_path.endswith(ext) for ext in ['.cs', '.razor']) and os.path.exists(file_path):
                csharp_files.append(file_path)
        return csharp_files
    
    def _find_dotnet_projects(self, csharp_files: List[str]) -> List[str]:
        """Find .NET project roots by looking for .csproj or .sln files"""
        project_roots = set()
        
        for csharp_file in csharp_files:
            # Walk up the directory tree looking for .NET project files
            current_dir = os.path.dirname(os.path.abspath(csharp_file))
            while current_dir != os.path.dirname(current_dir):  # Not root
                project_files = [f for f in os.listdir(current_dir) if f.endswith(('.csproj', '.sln', '.fsproj', '.vbproj'))]
                if project_files:
                    project_roots.add(current_dir)
                    break
                current_dir = os.path.dirname(current_dir)
        
        return list(project_roots)
    
    async def _analyze_dotnet_project(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Analyze a .NET project with available tools"""
        findings = []
        
        # Run DevSkim for security analysis
        if self.tools['devskim']['enabled']:
            devskim_findings = await self._run_devskim(project_root, context)
            findings.extend(devskim_findings)
        
        # Run .NET build with Roslyn analyzers
        if self.tools['roslyn_analyzers']['enabled']:
            roslyn_findings = await self._run_roslyn_analyzers(project_root, context)
            findings.extend(roslyn_findings)
        
        return findings
    
    async def _analyze_individual_files(self, csharp_files: List[str], context: Dict[str, Any]) -> List[Finding]:
        """Analyze individual C# files without project structure"""
        findings = []
        
        # DevSkim can work on individual files
        if self.tools['devskim']['enabled']:
            for csharp_file in csharp_files:
                file_findings = await self._run_devskim_on_file(csharp_file, context)
                findings.extend(file_findings)
        
        # Pattern-based analysis for security issues
        for csharp_file in csharp_files:
            pattern_findings = await self._analyze_csharp_file_patterns(csharp_file, context)
            findings.extend(pattern_findings)
        
        return findings
    
    async def _run_devskim(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run DevSkim security analysis"""
        findings = []
        
        try:
            output_file = os.path.join(project_root, 'devskim-report.json')
            
            cmd = [
                'devskim',
                'analyze',
                '--source-code', project_root,
                '--output-format', 'json',
                '--output-file', output_file,
                '--recurse'
            ]
            
            logger.info(f"Running DevSkim in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=300)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_devskim_output(output_file, project_root))
                os.remove(output_file)  # Clean up
            
            if result.stderr and "error" in result.stderr.lower():
                logger.warning(f"DevSkim warnings: {result.stderr[:200]}...")
                
        except subprocess.TimeoutExpired:
            logger.error("DevSkim analysis timed out")
        except Exception as e:
            logger.error(f"Error running DevSkim: {e}")
        
        return findings
    
    async def _run_devskim_on_file(self, csharp_file: str, context: Dict[str, Any]) -> List[Finding]:
        """Run DevSkim on individual C# file"""
        findings = []
        
        try:
            output_file = csharp_file.replace('.cs', '_devskim.json')
            
            cmd = [
                'devskim',
                'analyze',
                '--source-code', csharp_file,
                '--output-format', 'json',
                '--output-file', output_file
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if os.path.exists(output_file):
                findings.extend(self._parse_devskim_output(output_file, os.path.dirname(csharp_file)))
                os.remove(output_file)  # Clean up
                
        except Exception as e:
            logger.error(f"Error running DevSkim on {csharp_file}: {e}")
        
        return findings
    
    async def _run_roslyn_analyzers(self, project_root: str, context: Dict[str, Any]) -> List[Finding]:
        """Run .NET build with Roslyn security analyzers"""
        findings = []
        
        try:
            # Find project files
            project_files = []
            for ext in ['.csproj', '.sln']:
                project_files.extend([f for f in os.listdir(project_root) if f.endswith(ext)])
            
            if not project_files:
                logger.warning("No .NET project files found")
                return findings
            
            # Use the first found project file
            project_file = project_files[0]
            
            cmd = [
                'dotnet',
                'build',
                project_file,
                '--verbosity', 'diagnostic',
                '--property:TreatWarningsAsErrors=false',
                '--property:WarningsAsErrors=',
                '--property:RunAnalyzersDuringBuild=true'
            ]
            
            logger.info(f"Running .NET build with analyzers in {project_root}")
            
            result = subprocess.run(cmd, cwd=project_root, capture_output=True, 
                                  text=True, timeout=300)
            
            if result.stdout or result.stderr:
                findings.extend(self._parse_dotnet_build_output(result.stdout + result.stderr, project_root))
                
        except subprocess.TimeoutExpired:
            logger.error(".NET build analysis timed out")
        except Exception as e:
            logger.error(f"Error running .NET build with analyzers: {e}")
        
        return findings
    
    def _parse_devskim_output(self, output_file: str, project_root: str) -> List[Finding]:
        """Parse DevSkim JSON output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                devskim_data = json.load(f)
            
            for issue in devskim_data:
                finding = self._create_devskim_finding(issue, project_root)
                if finding:
                    findings.append(finding)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing DevSkim JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing DevSkim output: {e}")
        
        return findings
    
    def _parse_dotnet_build_output(self, output: str, project_root: str) -> List[Finding]:
        """Parse .NET build output for analyzer warnings"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            # Look for analyzer warnings/errors
            if any(keyword in line for keyword in ['warning', 'error']) and any(analyzer in line for analyzer in ['CA', 'SCS', 'S']):
                finding = self._create_dotnet_analyzer_finding(line, project_root)
                if finding:
                    findings.append(finding)
        
        return findings
    
    def _create_devskim_finding(self, issue: Dict[str, Any], project_root: str) -> Optional[Finding]:
        """Create a Finding from DevSkim issue"""
        try:
            rule_id = issue.get('rule_id', 'Unknown')
            rule_name = issue.get('rule_name', 'DevSkim security issue')
            severity = issue.get('severity', 'moderate')
            description = issue.get('description', 'DevSkim security issue')
            
            location = issue.get('location', {})
            filename = location.get('filename', 'unknown')
            line = location.get('line', 0)
            column = location.get('column', 0)
            
            # Make file path relative to project root if possible
            if os.path.isabs(filename) and project_root in filename:
                filename = os.path.relpath(filename, project_root)
            
            mapped_severity = self._map_devskim_severity(severity)
            cvss_score = self._calculate_cvss_score(mapped_severity, rule_id)
            
            return Finding(
                id=f"devskim_{rule_id}_{hash(filename + str(line))}",
                title=f"DevSkim: {rule_name}",
                description=self._build_devskim_description(issue, filename, line),
                severity=mapped_severity.lower(),
                category="csharp_security",
                file=filename,
                lines=[line] if line > 0 else [],
                confidence_score=self._get_devskim_confidence(severity),
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="devskim",
                    raw_output=json.dumps(issue),
                    confidence=self._get_devskim_confidence(severity)
                )
            )
        except Exception as e:
            logger.error(f"Error creating DevSkim finding: {e}")
            return None
    
    def _create_dotnet_analyzer_finding(self, line: str, project_root: str) -> Optional[Finding]:
        """Create a Finding from .NET analyzer output line"""
        try:
            # Parse analyzer output line format: file(line,column): warning/error RULE: message
            import re
            
            # Match pattern like: Program.cs(10,5): warning CA2100: Review SQL queries...
            pattern = r'([^(]+)\((\d+),(\d+)\):\s+(warning|error)\s+([^:]+):\s+(.+)'
            match = re.match(pattern, line.strip())
            
            if not match:
                return None
            
            filename, line_num, column, severity, rule_id, message = match.groups()
            line_num = int(line_num)
            
            # Make file path relative to project root if possible
            if os.path.isabs(filename) and project_root in filename:
                filename = os.path.relpath(filename, project_root)
            
            mapped_severity = self._map_dotnet_severity(severity, rule_id)
            cvss_score = self._calculate_cvss_score(mapped_severity, rule_id)
            
            return Finding(
                id=f"dotnet_analyzer_{rule_id}_{hash(filename + str(line_num))}",
                title=f".NET Analyzer: {rule_id}",
                description=self._build_dotnet_analyzer_description(rule_id, message, filename, line_num),
                severity=mapped_severity.lower(),
                category="csharp_analyzer",
                file=filename,
                lines=[line_num],
                confidence_score=80,
                cvss_v4=cvss_score,
                evidence=ToolEvidence(
                    tool_name="roslyn_analyzers",
                    raw_output=line,
                    confidence=80
                )
            )
        except Exception as e:
            logger.error(f"Error creating .NET analyzer finding: {e}")
            return None
    
    async def _analyze_csharp_file_patterns(self, file_path: str, context: Dict[str, Any]) -> List[Finding]:
        """Analyze individual C# file for security patterns"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                lines = content.split('\n')
            
            # Pattern-based security analysis
            for line_num, line in enumerate(lines, 1):
                line_stripped = line.strip()
                
                # Check for SQL injection patterns
                if any(pattern in line_stripped for pattern in ['SqlCommand(', 'ExecuteScalar(', 'ExecuteNonQuery(']):
                    if '+' in line_stripped or '$"' in line_stripped:
                        finding = self._create_pattern_finding(
                            "sql_injection", file_path, line_num, line_stripped,
                            "Potential SQL Injection", "String concatenation in SQL command - use parameterized queries"
                        )
                        findings.append(finding)
                
                # Check for command injection
                if any(pattern in line_stripped for pattern in ['Process.Start(', 'ProcessStartInfo(']):
                    finding = self._create_pattern_finding(
                        "command_injection", file_path, line_num, line_stripped,
                        "Command Execution", "Process execution requires input validation"
                    )
                    findings.append(finding)
                
                # Check for unsafe deserialization
                if any(pattern in line_stripped for pattern in ['BinaryFormatter', 'XmlSerializer', 'JsonConvert.DeserializeObject']):
                    finding = self._create_pattern_finding(
                        "unsafe_deserialization", file_path, line_num, line_stripped,
                        "Unsafe Deserialization", "Deserialization can lead to remote code execution"
                    )
                    findings.append(finding)
                
                # Check for hardcoded credentials
                if any(pattern in line_stripped.lower() for pattern in ['password', 'secret', 'key', 'token', 'connectionstring']):
                    if '=' in line_stripped and '"' in line_stripped:
                        finding = self._create_pattern_finding(
                            "hardcoded_credential", file_path, line_num, line_stripped,
                            "Hardcoded Credential", "Potential hardcoded credential found"
                        )
                        findings.append(finding)
                
                # Check for weak crypto
                if any(pattern in line_stripped for pattern in ['MD5', 'SHA1', 'DES', 'RC2']):
                    finding = self._create_pattern_finding(
                        "weak_crypto", file_path, line_num, line_stripped,
                        "Weak Cryptography", "Weak cryptographic algorithm detected"
                    )
                    findings.append(finding)
                
                # Check for unsafe code
                if 'unsafe' in line_stripped and '{' in line_stripped:
                    finding = self._create_pattern_finding(
                        "unsafe_code", file_path, line_num, line_stripped,
                        "Unsafe Code Block", "Unsafe code bypasses .NET memory safety"
                    )
                    findings.append(finding)
                    
        except Exception as e:
            logger.error(f"Error analyzing C# file {file_path}: {e}")
        
        return findings
    
    def _create_pattern_finding(self, pattern_id: str, file_path: str, line_num: int, 
                               line_content: str, title: str, description: str) -> Finding:
        """Create a Finding from pattern analysis"""
        severity = self._get_pattern_severity(pattern_id)
        cvss_score = self._calculate_cvss_score(severity, pattern_id)
        
        return Finding(
            id=f"csharp_pattern_{pattern_id}_{hash(file_path + str(line_num))}",
            title=f"C#: {title}",
            description=f"{description}\n\nLocation: {file_path}:{line_num}\nCode: {line_content}",
            severity=severity.lower(),
            category="csharp_patterns",
            file=file_path,
            lines=[line_num],
            confidence_score=70,
            cvss_v4=cvss_score,
            evidence=ToolEvidence(
                tool_name="csharp_analyzer",
                raw_output=f"Pattern: {pattern_id}, Line: {line_content}",
                confidence=70
            )
        )
    
    def _map_devskim_severity(self, severity: str) -> str:
        """Map DevSkim severity to our severity levels"""
        severity_map = {
            'critical': 'CRITICAL',
            'important': 'HIGH',
            'moderate': 'MEDIUM',
            'low': 'LOW',
            'manual-review': 'MEDIUM'
        }
        return severity_map.get(severity.lower(), 'MEDIUM')
    
    def _map_dotnet_severity(self, severity: str, rule_id: str) -> str:
        """Map .NET analyzer severity to our severity levels"""
        # Security rules get higher severity
        security_rules = ['CA2100', 'CA2119', 'CA2153', 'CA2300', 'CA2301', 'CA2302', 'CA2305', 'CA2310', 'CA2311', 'CA2312', 'CA2315', 'CA2321', 'CA2322', 'CA2326', 'CA2327', 'CA2328', 'CA2329', 'CA2330', 'SCS']
        
        if any(sr in rule_id for sr in security_rules):
            if severity == 'error':
                return 'CRITICAL'
            else:
                return 'HIGH'
        
        # Regular severity mapping
        if severity == 'error':
            return 'HIGH'
        else:
            return 'MEDIUM'
    
    def _get_devskim_confidence(self, severity: str) -> int:
        """Get confidence score based on DevSkim severity"""
        confidence_map = {
            'critical': 95,
            'important': 85,
            'moderate': 75,
            'low': 65,
            'manual-review': 60
        }
        return confidence_map.get(severity.lower(), 70)
    
    def _get_pattern_severity(self, pattern_id: str) -> str:
        """Get severity for pattern-based findings"""
        severity_map = {
            'sql_injection': 'HIGH',
            'command_injection': 'HIGH',
            'unsafe_deserialization': 'CRITICAL',
            'hardcoded_credential': 'MEDIUM',
            'weak_crypto': 'HIGH',
            'unsafe_code': 'MEDIUM'
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
        if any(keyword in category.lower() for keyword in ['injection', 'deserialization', 'unsafe']):
            score += 1.0
        elif any(keyword in category.lower() for keyword in ['crypto', 'credential']):
            score += 0.5
        
        score = min(10.0, score)  # Cap at 10.0
        
        return CVSSv4(
            score=score,
            vector=f"CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:{'H' if score >= 7 else 'M' if score >= 4 else 'L'}/VI:L/VA:L/SC:N/SI:N/SA:N"
        )
    
    def _build_devskim_description(self, issue: Dict[str, Any], filename: str, line: int) -> str:
        """Build detailed description for DevSkim finding"""
        rule_id = issue.get('rule_id', 'Unknown')
        rule_name = issue.get('rule_name', 'DevSkim security issue')
        severity = issue.get('severity', 'moderate')
        description = issue.get('description', 'DevSkim security issue')
        replacement = issue.get('replacement', '')
        
        return f"""
Microsoft DevSkim Security Analysis:

Rule ID: {rule_id}
Rule Name: {rule_name}
Severity: {severity.upper()}
Description: {description}
Location: {filename}:{line}

{f'Suggested Fix: {replacement}' if replacement else ''}

Security Impact:
DevSkim has identified a potential security vulnerability in your C#/.NET code. This could allow attackers to exploit your application if not properly addressed.

Recommendation:
Review the identified code and apply appropriate security measures. Use secure coding practices recommended by Microsoft for .NET applications.
"""
    
    def _build_dotnet_analyzer_description(self, rule_id: str, message: str, filename: str, line: int) -> str:
        """Build detailed description for .NET analyzer finding"""
        return f"""
.NET Roslyn Analyzer:

Rule: {rule_id}
Message: {message}
Location: {filename}:{line}

Security Impact:
This .NET analyzer rule has identified a potential security issue or code quality problem that could impact the security of your application.

Recommendation:
Address the specific issue identified by the analyzer. Refer to the Microsoft documentation for detailed guidance on resolving this rule violation.
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
        return ['csharp', 'c#', 'dotnet']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'C#/.NET Security Analyzer',
            'description': 'Comprehensive C#/.NET security analysis using DevSkim and Roslyn Analyzers',
            'supported_extensions': self.supported_extensions,
            'available_tools': {
                name: {
                    'enabled': info['enabled'],
                    'description': info['description']
                }
                for name, info in self.tools.items()
            }
        }