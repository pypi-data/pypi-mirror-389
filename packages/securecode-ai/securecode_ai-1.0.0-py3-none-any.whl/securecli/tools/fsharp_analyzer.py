"""
F# Security Analyzer for SecureCLI
Comprehensive F# security analysis using FSharpLint and functional programming security patterns
"""

import asyncio
import json
import os
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Any

from .base import BaseTool
from ..schemas.findings import Finding, CVSSv4, ToolEvidence


class FSharpAnalyzer(BaseTool):
    """
    Comprehensive F# security analyzer
    
    Integrates F# security analysis tools:
    - FSharpLint: Static analysis for F# code
    - Fantomas: Code formatter with lint capabilities
    - Custom functional programming security patterns
    - .NET security patterns adapted for F#
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "fsharp_analyzer"
        self.display_name = "F# Security Analyzer"
        self.description = "Comprehensive F# security analysis using FSharpLint and functional security patterns"
        self.version = "1.0.0"
    
    def is_available(self) -> bool:
        """Check if any F# analysis tools are available"""
        tools = [
            self._check_fsharplint(),
            self._check_dotnet_cli(),
            True  # Pattern analysis always available
        ]
        return any(tools)
    
    def _check_fsharplint(self) -> bool:
        """Check if FSharpLint is available"""
        try:
            result = subprocess.run(
                ['fsharplint', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_dotnet_cli(self) -> bool:
        """Check if .NET CLI is available"""
        try:
            result = subprocess.run(
                ['dotnet', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Optional[Dict] = None) -> List[Finding]:
        """Perform comprehensive F# security analysis"""
        findings = []
        
        # Find F# files
        fsharp_files = self._find_fsharp_files(target_path)
        if not fsharp_files:
            return findings
        
        # Check if it's a .NET project
        is_dotnet_project = self._is_dotnet_project(target_path)
        
        # Run tool-based analysis
        if self._check_fsharplint():
            findings.extend(await self._run_fsharplint(fsharp_files, target_path))
        
        if self._check_dotnet_cli() and is_dotnet_project:
            findings.extend(await self._run_dotnet_analysis(target_path))
        
        # Always run pattern analysis
        findings.extend(await self._run_pattern_analysis(fsharp_files))
        
        return findings
    
    def _is_dotnet_project(self, target_path: str) -> bool:
        """Check if target is a .NET project"""
        for root, dirs, files in os.walk(target_path):
            for file in files:
                if file.endswith(('.fsproj', '.sln')):
                    return True
        return False
    
    def _find_fsharp_files(self, target_path: str) -> List[str]:
        """Find F# source files"""
        fsharp_extensions = {'.fs', '.fsx', '.fsi'}
        fsharp_files = []
        
        if os.path.isfile(target_path):
            if Path(target_path).suffix.lower() in fsharp_extensions:
                fsharp_files.append(target_path)
        else:
            for root, dirs, files in os.walk(target_path):
                # Skip build directories
                if 'bin' in dirs:
                    dirs.remove('bin')
                if 'obj' in dirs:
                    dirs.remove('obj')
                
                for file in files:
                    if Path(file).suffix.lower() in fsharp_extensions:
                        fsharp_files.append(os.path.join(root, file))
        
        return fsharp_files
    
    async def _run_fsharplint(self, fsharp_files: List[str], target_path: str) -> List[Finding]:
        """Run FSharpLint static analysis"""
        findings = []
        
        try:
            # Create temporary output file
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as temp_file:
                output_file = temp_file.name
            
            # Run FSharpLint
            cmd = [
                'fsharplint',
                '--format', 'msbuild',
                '--output', output_file
            ]
            cmd.extend(fsharp_files[:10])  # Limit files for performance
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse FSharpLint output
            if os.path.exists(output_file):
                findings.extend(self._parse_fsharplint_output(output_file))
                os.unlink(output_file)  # Clean up
                
        except Exception as e:
            # Create a finding about FSharpLint failure
            finding = self._create_finding(
                file_path=target_path,
                title="FSharpLint Analysis Error",
                description=f"Failed to run FSharpLint: {e}",
                severity="Low",
                lines="1",
                recommendation="Install FSharpLint: dotnet tool install -g dotnet-fsharplint"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_dotnet_analysis(self, target_path: str) -> List[Finding]:
        """Run .NET CLI analysis for F# projects"""
        findings = []
        
        try:
            # Try to build the project
            cmd = ['dotnet', 'build', '--verbosity', 'normal']
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse build output for warnings
            if stdout:
                findings.extend(self._parse_dotnet_output(stdout.decode(), target_path))
            if stderr:
                findings.extend(self._parse_dotnet_output(stderr.decode(), target_path))
                
        except Exception as e:
            # Create a finding about .NET analysis failure
            finding = self._create_finding(
                file_path=target_path,
                title="F# .NET Analysis Error",
                description=f"Failed to run .NET analysis: {e}",
                severity="Low",
                lines="1",
                recommendation="Ensure F# project builds successfully"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_pattern_analysis(self, fsharp_files: List[str]) -> List[Finding]:
        """Run custom F# security pattern analysis"""
        findings = []
        
        # F# security patterns - functional programming focus
        security_patterns = [
            # Unsafe operations
            ('unbox', 'Unsafe Cast', 'MEDIUM', 'unbox can cause runtime exceptions if types don\'t match'),
            ('box', 'Boxing', 'LOW', 'Boxing can cause performance issues and type safety concerns'),
            ('!!', 'Type Coercion', 'MEDIUM', 'Type coercion operator can be unsafe'),
            
            # Mutable state (functional programming violation)
            ('mutable', 'Mutable State', 'LOW', 'Mutable state can cause thread safety issues in F#'),
            ('ref ', 'Reference Cell', 'LOW', 'Reference cells break functional purity'),
            ('Array.', 'Mutable Array', 'LOW', 'Arrays are mutable and can cause side effects'),
            
            # Exceptions (not functional)
            ('raise', 'Exception Throwing', 'LOW', 'Consider using Result<\'T,\'TError> instead of exceptions'),
            ('failwith', 'Failure Exception', 'MEDIUM', 'failwith creates exceptions - use Result type'),
            ('invalidArg', 'Argument Exception', 'LOW', 'Consider using Option or Result types'),
            
            # Unsafe .NET interop
            ('System.Runtime.InteropServices', 'P/Invoke', 'HIGH', 'P/Invoke can introduce memory safety issues'),
            ('DllImport', 'Native Code', 'HIGH', 'Native code calls can be unsafe'),
            ('Marshal.', 'Memory Marshal', 'HIGH', 'Memory marshaling can cause security issues'),
            
            # Serialization issues (same as C#)
            ('BinaryFormatter', 'Unsafe Deserialization', 'CRITICAL', 'BinaryFormatter is unsafe'),
            ('NetDataContractSerializer', 'Unsafe Deserialization', 'HIGH', 'Use safe serializers'),
            
            # SQL and data access
            ('SqlCommand', 'SQL Injection', 'HIGH', 'Use parameterized queries in F#'),
            ('sprintf', 'String Formatting', 'MEDIUM', 'sprintf with user input can be dangerous'),
            ('printf', 'String Formatting', 'LOW', 'printf with user input may expose information'),
            
            # File operations
            ('System.IO.File', 'File Operations', 'MEDIUM', 'Validate file paths and permissions'),
            ('System.IO.Path.Combine', 'Path Operations', 'LOW', 'Validate paths to prevent traversal'),
            
            # Reflection
            ('System.Reflection', 'Reflection', 'MEDIUM', 'Reflection can bypass type safety'),
            ('Assembly.LoadFrom', 'Dynamic Loading', 'HIGH', 'Dynamic assembly loading is dangerous'),
            ('Activator.CreateInstance', 'Dynamic Creation', 'MEDIUM', 'Validate types for dynamic creation'),
            
            # Async and parallel issues
            ('Async.RunSynchronously', 'Async Blocking', 'LOW', 'Blocking async operations can cause deadlocks'),
            ('Task.Result', 'Task Blocking', 'LOW', 'Blocking on tasks can cause deadlocks'),
            ('lock', 'Locking', 'LOW', 'Locks can cause deadlocks - prefer immutable data'),
            
            # Type providers (F# specific)
            ('type SqlDataProvider', 'SQL Type Provider', 'MEDIUM', 'Validate SQL type provider connection strings'),
            ('type JsonProvider', 'JSON Type Provider', 'LOW', 'Validate JSON schemas for type providers'),
            ('type XmlProvider', 'XML Type Provider', 'MEDIUM', 'XML type providers may be vulnerable to XXE'),
            
            # Computational expressions with side effects
            ('seq {', 'Sequence Expression', 'LOW', 'Ensure sequence expressions don\'t have side effects'),
            ('async {', 'Async Expression', 'LOW', 'Handle async exceptions properly'),
            
            # Cryptography
            ('System.Security.Cryptography.MD5', 'Weak Hash', 'MEDIUM', 'MD5 is cryptographically broken'),
            ('System.Security.Cryptography.SHA1', 'Weak Hash', 'LOW', 'SHA1 is weak for new applications'),
            ('Random(', 'Weak Random', 'MEDIUM', 'Use cryptographically secure random'),
            
            # Web-specific (if using web frameworks)
            ('HttpContext', 'Web Context', 'MEDIUM', 'Validate all web inputs in F#'),
            ('Request.', 'HTTP Request', 'MEDIUM', 'Validate HTTP request data'),
            ('Response.Redirect', 'Open Redirect', 'MEDIUM', 'Validate redirect URLs'),
            
            # Functional anti-patterns
            ('|> ignore', 'Ignored Result', 'LOW', 'Ignoring function results may hide errors'),
            ('do!', 'Side Effect', 'LOW', 'Ensure side effects are intentional and safe'),
            ('use!', 'Resource Usage', 'LOW', 'Ensure proper resource disposal'),
        ]
        
        for file_path in fsharp_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    
                    for pattern, vuln_type, severity, description in security_patterns:
                        if pattern in line_content:
                            finding = self._create_finding(
                                file_path=file_path,
                                title=f"F# {vuln_type}",
                                description=f"{description}. Found: {line_content[:100]}",
                                severity=severity,
                                lines=str(line_num),
                                snippet=line_content,
                                recommendation=self._get_recommendation(vuln_type)
                            )
                            findings.append(finding)
                            
            except Exception as e:
                continue  # Skip files that can't be read
        
        return findings
    
    def _parse_fsharplint_output(self, output_file: str) -> List[Finding]:
        """Parse FSharpLint output"""
        findings = []
        
        try:
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Simple parsing of MSBuild format
            lines = content.split('\n')
            for line in lines:
                if 'warning' in line.lower() or 'error' in line.lower():
                    parts = line.split(':', 4)
                    if len(parts) >= 5:
                        try:
                            file_path = parts[0].strip()
                            line_num = parts[1].strip() if parts[1].strip().isdigit() else '1'
                            severity = 'HIGH' if 'error' in line.lower() else 'MEDIUM'
                            message = parts[4].strip() if len(parts) > 4 else 'FSharpLint issue'
                            
                            finding = self._create_finding(
                                file_path=file_path,
                                title="FSharpLint Issue",
                                description=message,
                                severity=severity,
                                lines=line_num,
                                recommendation="Review and fix FSharpLint warnings"
                            )
                            findings.append(finding)
                        except (ValueError, IndexError):
                            continue
                            
        except FileNotFoundError:
            pass
        
        return findings
    
    def _parse_dotnet_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse .NET build output for F# warnings"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if 'warning' in line.lower() and ('FS' in line or 'security' in line.lower()):
                # Parse F# warning format
                parts = line.split(':', 4)
                if len(parts) >= 5:
                    try:
                        file_part = parts[0].strip()
                        line_part = parts[1].strip() if parts[1].strip().isdigit() else '1'
                        warning_code = parts[3].strip() if len(parts) > 3 else 'Unknown'
                        message = parts[4].strip() if len(parts) > 4 else 'F# warning'
                        
                        severity = 'MEDIUM'
                        if 'security' in message.lower():
                            severity = 'HIGH'
                        
                        finding = self._create_finding(
                            file_path=file_part,
                            title=f"F# Compiler Warning: {warning_code}",
                            description=message,
                            severity=severity,
                            lines=line_part,
                            recommendation="Review and fix F# compiler warnings"
                        )
                        findings.append(finding)
                    except (ValueError, IndexError):
                        continue
        
        return findings
    
    def _get_recommendation(self, vuln_type: str) -> str:
        """Get specific recommendations for vulnerability types"""
        recommendations = {
            'Unsafe Cast': 'Use pattern matching or safe casting alternatives',
            'Mutable State': 'Prefer immutable data structures and functional approaches',
            'Exception Throwing': 'Use Result<\'T,\'TError> or Option<\'T> instead of exceptions',
            'P/Invoke': 'Minimize native code usage, validate all inputs/outputs',
            'Unsafe Deserialization': 'Use safe serializers like DataContractSerializer',
            'SQL Injection': 'Use type providers or parameterized queries',
            'String Formatting': 'Validate format strings and user inputs',
            'File Operations': 'Validate file paths and use proper permissions',
            'Reflection': 'Minimize reflection usage, validate type names',
            'Async Blocking': 'Use proper async/await patterns, avoid blocking',
            'SQL Type Provider': 'Use secure connection strings and validate schemas',
            'Weak Hash': 'Use SHA-256 or stronger hash functions',
            'Weak Random': 'Use System.Security.Cryptography.RNGCryptoServiceProvider',
            'Web Context': 'Validate all web inputs and use proper authentication',
            'Side Effect': 'Minimize side effects, use pure functions when possible'
        }
        return recommendations.get(vuln_type, 'Review and fix the security issue')
    
    def _create_finding(self, file_path: str, title: str, description: str, 
                       severity: str, lines: str, snippet: str = None, 
                       recommendation: str = None) -> Finding:
        """Create a standardized Finding object"""
        
        # Create CVSS score
        cvss_scores = {'CRITICAL': 9.8, 'HIGH': 7.5, 'MEDIUM': 5.5, 'LOW': 3.0}
        cvss_score = CVSSv4(
            score=cvss_scores.get(severity, 5.0),
            vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
        )
        
        # Create tool evidence
        evidence = ToolEvidence(
            tool_name=self.name,
            tool_version=self.version,
            confidence_score=75,
            raw_output=f"F# security analysis detected: {title}",
            analysis_metadata={
                'analyzer': 'FSharpAnalyzer',
                'pattern_based': snippet is None,
                'file_path': file_path
            }
        )
        
        return Finding(
            file=file_path,
            title=title,
            description=description,
            lines=lines,
            impact=f"F# {severity.lower()} severity security issue that could affect functional programming safety",
            severity=severity.title(),
            cvss_v4=cvss_score,
            snippet=snippet or f"# F# code analysis in {os.path.basename(file_path)}",
            recommendation=recommendation or "Review and address the F# security issue",
            sample_fix="// Implement functional F# practices and avoid unsafe operations",
            poc="// No proof-of-concept available for static analysis finding",
            owasp=[],
            cwe=[],
            references=[
                "https://fsharp.org/",
                "https://docs.microsoft.com/en-us/dotnet/fsharp/",
                "https://github.com/fsprojects/FSharpLint",
                "https://fsharpforfunandprofit.com/posts/designing-with-types-making-illegal-states-unrepresentable/"
            ],
            cross_file=[],
            tool_evidence=[evidence]
        )
    
    def get_version(self) -> str:
        """Get tool version"""
        return self.version
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """
        Convert tool-specific output to normalized Finding objects
        
        Args:
            raw_output: Raw tool output
            metadata: Additional metadata
            
        Returns:
            List of normalized Finding objects
        """
        findings = []
        
        # Parse the raw output and create Finding objects
        file_path = metadata.get('file_path', 'unknown.fs')
        
        # Simple parsing - look for F# compiler warnings and errors
        lines = raw_output.strip().split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'fs', 'security']):
                # Extract basic information from the line
                title = line.strip()
                description = f"F# security issue detected: {title}"
                
                # Determine severity based on content
                severity = 'Medium'
                if 'error' in line.lower() or 'security' in line.lower():
                    severity = 'High'
                elif 'warning' in line.lower():
                    severity = 'Medium'
                
                finding = self._create_finding(
                    file_path=file_path,
                    title=title[:100],  # Truncate if too long
                    description=description,
                    severity=severity,
                    lines=str(i + 1),
                    snippet=line.strip(),
                    recommendation=self._get_recommendation('General')
                )
                findings.append(finding)
        
        return findings


# Export the analyzer
__all__ = ['FSharpAnalyzer']