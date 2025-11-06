"""
Erlang/Elixir Security Analyzer for SecureCLI
Comprehensive Erlang and Elixir security analysis using Dialyzer, Credo, and BEAM patterns
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


class ErlangElixirAnalyzer(BaseTool):
    """
    Comprehensive Erlang/Elixir security analyzer
    
    Integrates BEAM ecosystem security analysis tools:
    - Dialyzer: Static analysis for Erlang/Elixir type errors
    - Credo: Elixir static code analysis
    - Sobelow: Phoenix/web security scanner
    - Custom BEAM virtual machine security patterns
    - OTP (Open Telecom Platform) security analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "erlang_elixir_analyzer"
        self.display_name = "Erlang/Elixir Security Analyzer"
        self.description = "Comprehensive Erlang/Elixir security analysis using Dialyzer, Credo, and BEAM patterns"
        self.version = "1.0.0"
    
    def is_available(self) -> bool:
        """Check if any Erlang/Elixir analysis tools are available"""
        tools = [
            self._check_erlang(),
            self._check_elixir(),
            self._check_dialyzer(),
            self._check_credo(),
            self._check_sobelow(),
            True  # Pattern analysis always available
        ]
        return any(tools)
    
    def _check_erlang(self) -> bool:
        """Check if Erlang is available"""
        try:
            result = subprocess.run(
                ['erl', '-version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_elixir(self) -> bool:
        """Check if Elixir is available"""
        try:
            result = subprocess.run(
                ['elixir', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_dialyzer(self) -> bool:
        """Check if Dialyzer is available"""
        try:
            result = subprocess.run(
                ['dialyzer', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_credo(self) -> bool:
        """Check if Credo is available"""
        try:
            result = subprocess.run(
                ['mix', 'credo', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    def _check_sobelow(self) -> bool:
        """Check if Sobelow is available"""
        try:
            result = subprocess.run(
                ['mix', 'sobelow', '--version'], 
                capture_output=True, 
                text=True, 
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Optional[Dict] = None) -> List[Finding]:
        """Perform comprehensive Erlang/Elixir security analysis"""
        findings = []
        
        # Find Erlang/Elixir files
        erl_files = self._find_erlang_files(target_path)
        elixir_files = self._find_elixir_files(target_path)
        
        if not erl_files and not elixir_files:
            return findings
        
        # Check project type
        is_elixir_project = self._is_elixir_project(target_path)
        is_phoenix_project = self._is_phoenix_project(target_path)
        
        # Run tool-based analysis
        if self._check_dialyzer() and (erl_files or elixir_files):
            findings.extend(await self._run_dialyzer(target_path, erl_files + elixir_files))
        
        if self._check_credo() and is_elixir_project:
            findings.extend(await self._run_credo(target_path))
        
        if self._check_sobelow() and is_phoenix_project:
            findings.extend(await self._run_sobelow(target_path))
        
        # Always run pattern analysis
        if erl_files:
            findings.extend(await self._run_erlang_pattern_analysis(erl_files))
        if elixir_files:
            findings.extend(await self._run_elixir_pattern_analysis(elixir_files))
        
        return findings
    
    def _is_elixir_project(self, target_path: str) -> bool:
        """Check if target is an Elixir project"""
        mix_file = os.path.join(target_path, 'mix.exs')
        return os.path.exists(mix_file)
    
    def _is_phoenix_project(self, target_path: str) -> bool:
        """Check if target is a Phoenix project"""
        if not self._is_elixir_project(target_path):
            return False
        
        mix_file = os.path.join(target_path, 'mix.exs')
        try:
            with open(mix_file, 'r') as f:
                content = f.read()
                return 'phoenix' in content.lower()
        except FileNotFoundError:
            return False
    
    def _find_erlang_files(self, target_path: str) -> List[str]:
        """Find Erlang source files"""
        erlang_extensions = {'.erl', '.hrl'}
        erlang_files = []
        
        if os.path.isfile(target_path):
            if Path(target_path).suffix.lower() in erlang_extensions:
                erlang_files.append(target_path)
        else:
            for root, dirs, files in os.walk(target_path):
                # Skip build directories
                dirs[:] = [d for d in dirs if d not in ['_build', 'deps', '.git']]
                
                for file in files:
                    if Path(file).suffix.lower() in erlang_extensions:
                        erlang_files.append(os.path.join(root, file))
        
        return erlang_files
    
    def _find_elixir_files(self, target_path: str) -> List[str]:
        """Find Elixir source files"""
        elixir_extensions = {'.ex', '.exs'}
        elixir_files = []
        
        if os.path.isfile(target_path):
            if Path(target_path).suffix.lower() in elixir_extensions:
                elixir_files.append(target_path)
        else:
            for root, dirs, files in os.walk(target_path):
                # Skip build directories
                dirs[:] = [d for d in dirs if d not in ['_build', 'deps', '.git']]
                
                for file in files:
                    if Path(file).suffix.lower() in elixir_extensions:
                        elixir_files.append(os.path.join(root, file))
        
        return elixir_files
    
    async def _run_dialyzer(self, target_path: str, files: List[str]) -> List[Finding]:
        """Run Dialyzer static analysis"""
        findings = []
        
        try:
            # Create temporary PLT if needed
            plt_path = os.path.join(target_path, '.dialyzer_plt')
            
            # Run Dialyzer
            cmd = [
                'dialyzer',
                '--no_check_plt',
                '--quiet'
            ]
            cmd.extend(files[:20])  # Limit files for performance
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse Dialyzer output
            if stdout:
                findings.extend(self._parse_dialyzer_output(stdout.decode(), target_path))
            
        except Exception as e:
            # Create a finding about Dialyzer failure
            finding = self._create_finding(
                file_path=target_path,
                title="Dialyzer Analysis Error",
                description=f"Failed to run Dialyzer: {e}",
                severity="Low",
                lines="1",
                recommendation="Install Dialyzer: Install Erlang/OTP and ensure dialyzer is available"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_credo(self, target_path: str) -> List[Finding]:
        """Run Credo static analysis for Elixir"""
        findings = []
        
        try:
            cmd = ['mix', 'credo', '--format', 'json', '--all']
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse Credo JSON output
            if stdout:
                findings.extend(self._parse_credo_output(stdout.decode(), target_path))
            
        except Exception as e:
            # Create a finding about Credo failure
            finding = self._create_finding(
                file_path=target_path,
                title="Credo Analysis Error",
                description=f"Failed to run Credo: {e}",
                severity="Low",
                lines="1",
                recommendation="Install Credo: Add {:credo, '~> 1.6'} to mix.exs dependencies"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_sobelow(self, target_path: str) -> List[Finding]:
        """Run Sobelow security scanner for Phoenix"""
        findings = []
        
        try:
            cmd = ['mix', 'sobelow', '--format', 'json', '--verbose']
            
            result = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE,
                cwd=target_path
            )
            
            stdout, stderr = await result.communicate()
            
            # Parse Sobelow JSON output
            if stdout:
                findings.extend(self._parse_sobelow_output(stdout.decode(), target_path))
            
        except Exception as e:
            # Create a finding about Sobelow failure
            finding = self._create_finding(
                file_path=target_path,
                title="Sobelow Analysis Error",
                description=f"Failed to run Sobelow: {e}",
                severity="Low",
                lines="1",
                recommendation="Install Sobelow: Add {:sobelow, '~> 0.11'} to mix.exs dependencies"
            )
            findings.append(finding)
        
        return findings
    
    async def _run_erlang_pattern_analysis(self, erlang_files: List[str]) -> List[Finding]:
        """Run custom Erlang security pattern analysis"""
        findings = []
        
        # Erlang security patterns
        security_patterns = [
            # Process and concurrency issues
            ('spawn_link', 'Uncontrolled Process Creation', 'MEDIUM', 'spawn_link without proper error handling'),
            ('spawn_monitor', 'Process Monitoring', 'LOW', 'Ensure proper process monitoring'),
            ('exit(', 'Process Exit', 'LOW', 'Uncontrolled process exits can affect system stability'),
            ('erlang:halt', 'System Halt', 'HIGH', 'System halt can cause denial of service'),
            
            # Message passing security
            ('receive', 'Message Handling', 'LOW', 'Validate all received messages'),
            ('!', 'Message Send', 'LOW', 'Ensure message recipients are trusted'),
            ('gen_server:call', 'Synchronous Call', 'LOW', 'Implement proper timeout handling'),
            ('gen_server:cast', 'Asynchronous Cast', 'LOW', 'Validate cast message contents'),
            
            # File and I/O operations
            ('file:read', 'File Read', 'MEDIUM', 'Validate file paths and permissions'),
            ('file:write', 'File Write', 'MEDIUM', 'Validate file paths and sanitize content'),
            ('file:delete', 'File Delete', 'HIGH', 'Validate file deletion permissions'),
            ('file:open', 'File Open', 'MEDIUM', 'Use proper file open modes and error handling'),
            ('os:cmd', 'OS Command', 'CRITICAL', 'OS command execution can be dangerous'),
            ('erlang:open_port', 'Port Opening', 'HIGH', 'Port operations can be unsafe'),
            
            # Network operations
            ('gen_tcp:connect', 'TCP Connection', 'MEDIUM', 'Validate connection parameters'),
            ('gen_tcp:listen', 'TCP Listen', 'MEDIUM', 'Secure TCP listening with proper validation'),
            ('gen_udp:', 'UDP Operations', 'MEDIUM', 'UDP operations need input validation'),
            ('ssl:', 'SSL Operations', 'MEDIUM', 'Ensure proper SSL configuration'),
            ('httpc:', 'HTTP Client', 'MEDIUM', 'Validate HTTP client requests and responses'),
            
            # Code loading and evaluation
            ('code:load_file', 'Dynamic Code Loading', 'HIGH', 'Dynamic code loading is dangerous'),
            ('erlang:load_nif', 'NIF Loading', 'CRITICAL', 'Native code loading can be unsafe'),
            ('erl_eval:expr', 'Dynamic Evaluation', 'CRITICAL', 'Dynamic code evaluation is dangerous'),
            
            # Cryptography
            ('crypto:rand_bytes', 'Random Generation', 'LOW', 'Use crypto:strong_rand_bytes for security'),
            ('crypto:md5', 'Weak Hash', 'MEDIUM', 'MD5 is cryptographically broken'),
            ('crypto:sha', 'Legacy Hash', 'LOW', 'Use newer SHA variants'),
            
            # ETS/DETS table operations
            ('ets:new', 'ETS Table', 'LOW', 'Configure ETS tables with proper access controls'),
            ('ets:insert', 'ETS Insert', 'LOW', 'Validate data before ETS insertion'),
            ('dets:open_file', 'DETS File', 'MEDIUM', 'Validate DETS file paths'),
            
            # Binary operations
            ('binary_to_term', 'Unsafe Deserialization', 'CRITICAL', 'binary_to_term can execute code'),
            ('term_to_binary', 'Serialization', 'LOW', 'Be careful with term serialization'),
            ('binary_to_atom', 'Atom Creation', 'MEDIUM', 'Unlimited atom creation can cause memory issues'),
            
            # Distribution and clustering
            ('net_adm:ping', 'Node Ping', 'MEDIUM', 'Validate node names in clustering'),
            ('rpc:call', 'Remote Call', 'HIGH', 'Remote procedure calls need validation'),
            ('global:register_name', 'Global Registration', 'MEDIUM', 'Validate global name registration'),
            
            # Error handling
            ('catch', 'Exception Catching', 'LOW', 'Ensure proper error handling'),
            ('throw(', 'Exception Throwing', 'LOW', 'Use proper exception handling'),
            
            # Memory operations
            ('erlang:memory', 'Memory Info', 'LOW', 'Memory information disclosure'),
            ('erlang:garbage_collect', 'GC Control', 'LOW', 'Manual GC can affect performance'),
        ]
        
        for file_path in erlang_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    
                    for pattern, vuln_type, severity, description in security_patterns:
                        if pattern in line_content:
                            finding = self._create_finding(
                                file_path=file_path,
                                title=f"Erlang {vuln_type}",
                                description=f"{description}. Found: {line_content[:100]}",
                                severity=severity,
                                lines=str(line_num),
                                snippet=line_content,
                                recommendation=self._get_erlang_recommendation(vuln_type)
                            )
                            findings.append(finding)
                            
            except Exception as e:
                continue  # Skip files that can't be read
        
        return findings
    
    async def _run_elixir_pattern_analysis(self, elixir_files: List[str]) -> List[Finding]:
        """Run custom Elixir security pattern analysis"""
        findings = []
        
        # Elixir security patterns
        security_patterns = [
            # Process and GenServer issues
            ('GenServer.start_link', 'GenServer Creation', 'LOW', 'Ensure proper GenServer supervision'),
            ('Agent.start_link', 'Agent Creation', 'LOW', 'Validate Agent state management'),
            ('Task.start_link', 'Task Creation', 'LOW', 'Handle Task failures properly'),
            ('spawn_link', 'Process Creation', 'MEDIUM', 'Use supervised processes when possible'),
            ('Process.exit', 'Process Exit', 'MEDIUM', 'Uncontrolled process exits'),
            
            # Message passing
            ('send(', 'Message Send', 'LOW', 'Validate message recipients and content'),
            ('receive do', 'Message Receive', 'LOW', 'Implement proper message validation'),
            ('GenServer.call', 'Synchronous Call', 'LOW', 'Use proper timeout values'),
            ('GenServer.cast', 'Asynchronous Cast', 'LOW', 'Validate cast parameters'),
            
            # File operations
            ('File.read', 'File Read', 'MEDIUM', 'Validate file paths and handle errors'),
            ('File.write', 'File Write', 'MEDIUM', 'Sanitize file content and validate paths'),
            ('File.rm', 'File Delete', 'HIGH', 'Validate file deletion permissions'),
            ('System.cmd', 'OS Command', 'CRITICAL', 'OS command execution is dangerous'),
            ('Port.open', 'Port Operations', 'HIGH', 'Port operations can be unsafe'),
            
            # Network operations
            (':gen_tcp.connect', 'TCP Connection', 'MEDIUM', 'Validate TCP connection parameters'),
            (':ssl.connect', 'SSL Connection', 'MEDIUM', 'Use proper SSL configuration'),
            ('HTTPoison.', 'HTTP Client', 'MEDIUM', 'Validate HTTP requests and responses'),
            ('Plug.Conn', 'Web Connection', 'MEDIUM', 'Validate all web inputs'),
            
            # Phoenix specific
            ('Phoenix.Controller', 'Controller', 'MEDIUM', 'Implement proper authentication/authorization'),
            ('Phoenix.Channel', 'WebSocket Channel', 'MEDIUM', 'Validate WebSocket messages'),
            ('Ecto.Query', 'Database Query', 'MEDIUM', 'Use parameterized queries'),
            ('Repo.query', 'Raw SQL', 'HIGH', 'Avoid raw SQL queries, use Ecto'),
            
            # Code evaluation
            ('Code.eval_string', 'Code Evaluation', 'CRITICAL', 'Dynamic code evaluation is dangerous'),
            ('Code.compile_string', 'Code Compilation', 'HIGH', 'Dynamic compilation can be unsafe'),
            (':erlang.binary_to_term', 'Unsafe Deserialization', 'CRITICAL', 'binary_to_term can execute code'),
            
            # Cryptography
            (':crypto.strong_rand_bytes', 'Random Generation', 'INFO', 'Good cryptographic randomness'),
            (':crypto.rand_bytes', 'Weak Random', 'LOW', 'Use strong_rand_bytes for security'),
            (':crypto.md5', 'Weak Hash', 'MEDIUM', 'MD5 is cryptographically broken'),
            (':crypto.sha', 'Legacy Hash', 'LOW', 'Use newer SHA variants'),
            
            # ETS operations
            (':ets.new', 'ETS Table', 'LOW', 'Configure ETS with proper access controls'),
            (':ets.insert', 'ETS Insert', 'LOW', 'Validate data before insertion'),
            
            # String operations that might be unsafe
            ('String.to_atom', 'Atom Creation', 'MEDIUM', 'Unlimited atom creation causes memory issues'),
            ('String.to_existing_atom', 'Atom Lookup', 'LOW', 'Safer than to_atom but validate input'),
            
            # Serialization
            (':erlang.term_to_binary', 'Serialization', 'LOW', 'Be careful with term serialization'),
            ('Jason.decode!', 'JSON Parsing', 'MEDIUM', 'Use Jason.decode for error handling'),
            ('Poison.decode!', 'JSON Parsing', 'MEDIUM', 'Use Poison.decode for error handling'),
            
            # Distribution
            ('Node.connect', 'Node Connection', 'HIGH', 'Validate node connections in clusters'),
            (':rpc.call', 'Remote Call', 'HIGH', 'Remote procedure calls need validation'),
            
            # Macro usage (potential code injection)
            ('quote do', 'Macro Quote', 'LOW', 'Validate macro inputs for code injection'),
            ('unquote(', 'Macro Unquote', 'MEDIUM', 'Unquote can lead to code injection'),
            
            # Pattern matching issues
            ('binary_to_term', 'Unsafe Deserialization', 'CRITICAL', 'Can execute arbitrary code'),
            
            # Phoenix specific security
            ('conn.params', 'Parameter Access', 'MEDIUM', 'Validate all request parameters'),
            ('get_session', 'Session Access', 'LOW', 'Validate session data'),
            ('redirect(', 'Redirect', 'MEDIUM', 'Validate redirect URLs to prevent open redirects'),
        ]
        
        for file_path in elixir_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    
                    for pattern, vuln_type, severity, description in security_patterns:
                        if pattern in line_content:
                            finding = self._create_finding(
                                file_path=file_path,
                                title=f"Elixir {vuln_type}",
                                description=f"{description}. Found: {line_content[:100]}",
                                severity=severity,
                                lines=str(line_num),
                                snippet=line_content,
                                recommendation=self._get_elixir_recommendation(vuln_type)
                            )
                            findings.append(finding)
                            
            except Exception as e:
                continue  # Skip files that can't be read
        
        return findings
    
    def _parse_dialyzer_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Dialyzer output"""
        findings = []
        
        lines = output.split('\n')
        for line in lines:
            if line.strip() and not line.startswith('Checking'):
                # Dialyzer format: filename:line: Warning: description
                parts = line.split(':', 3)
                if len(parts) >= 3:
                    try:
                        file_path = parts[0].strip()
                        line_num = parts[1].strip() if parts[1].strip().isdigit() else '1'
                        message = parts[2].strip() if len(parts) > 2 else 'Dialyzer warning'
                        
                        severity = 'MEDIUM'
                        if 'error' in message.lower():
                            severity = 'HIGH'
                        
                        finding = self._create_finding(
                            file_path=file_path,
                            title="Dialyzer Warning",
                            description=message,
                            severity=severity,
                            lines=line_num,
                            recommendation="Fix Dialyzer type warnings to improve code safety"
                        )
                        findings.append(finding)
                    except (ValueError, IndexError):
                        continue
        
        return findings
    
    def _parse_credo_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Credo JSON output"""
        findings = []
        
        try:
            data = json.loads(output)
            issues = data.get('issues', [])
            
            for issue in issues:
                file_path = issue.get('filename', 'unknown')
                line_num = str(issue.get('line_no', 1))
                category = issue.get('category', 'unknown')
                message = issue.get('message', 'Credo issue')
                priority = issue.get('priority', 'normal')
                
                severity = 'LOW'
                if priority == 'high':
                    severity = 'MEDIUM'
                elif category in ['readability', 'refactor']:
                    severity = 'LOW'
                elif category in ['warning', 'design']:
                    severity = 'MEDIUM'
                
                finding = self._create_finding(
                    file_path=file_path,
                    title=f"Credo {category.title()} Issue",
                    description=message,
                    severity=severity,
                    lines=line_num,
                    recommendation="Address Credo code quality issues"
                )
                findings.append(finding)
                
        except json.JSONDecodeError:
            pass
        
        return findings
    
    def _parse_sobelow_output(self, output: str, target_path: str) -> List[Finding]:
        """Parse Sobelow JSON output"""
        findings = []
        
        try:
            data = json.loads(output)
            findings_data = data.get('findings', [])
            
            for finding_data in findings_data:
                file_path = finding_data.get('filename', 'unknown')
                line_num = str(finding_data.get('line', 1))
                vuln_type = finding_data.get('type', 'Security Issue')
                message = finding_data.get('message', 'Security vulnerability detected')
                severity = finding_data.get('severity', 'medium').upper()
                
                finding = self._create_finding(
                    file_path=file_path,
                    title=f"Sobelow {vuln_type}",
                    description=message,
                    severity=severity,
                    lines=line_num,
                    recommendation="Address Phoenix security vulnerabilities"
                )
                findings.append(finding)
                
        except json.JSONDecodeError:
            pass
        
        return findings
    
    def _get_erlang_recommendation(self, vuln_type: str) -> str:
        """Get specific recommendations for Erlang vulnerability types"""
        recommendations = {
            'Uncontrolled Process Creation': 'Use supervisor trees and monitor processes',
            'Process Exit': 'Handle process exits gracefully with proper supervision',
            'Message Handling': 'Validate all incoming messages and handle unknown messages',
            'File Read': 'Validate file paths and handle read errors',
            'File Write': 'Sanitize content and validate write permissions',
            'OS Command': 'Avoid OS commands, use Erlang libraries instead',
            'Port Opening': 'Validate port parameters and handle port failures',
            'Dynamic Code Loading': 'Avoid dynamic code loading or validate sources',
            'Unsafe Deserialization': 'Never use binary_to_term with untrusted data',
            'Weak Hash': 'Use SHA-256 or stronger hash functions',
            'Remote Call': 'Validate remote call parameters and authenticate nodes'
        }
        return recommendations.get(vuln_type, 'Review and fix the Erlang security issue')
    
    def _get_elixir_recommendation(self, vuln_type: str) -> str:
        """Get specific recommendations for Elixir vulnerability types"""
        recommendations = {
            'GenServer Creation': 'Use proper supervision strategies',
            'Process Creation': 'Use supervised processes and handle failures',
            'Message Send': 'Validate message recipients and content',
            'File Read': 'Use File.read/1 and handle {:error, reason} tuples',
            'OS Command': 'Avoid System.cmd, use Elixir libraries instead',
            'Code Evaluation': 'Never evaluate untrusted code strings',
            'Unsafe Deserialization': 'Never deserialize untrusted binary data',
            'Weak Hash': 'Use :crypto.hash(:sha256, data) or stronger',
            'Atom Creation': 'Use String.to_existing_atom or validate input',
            'Parameter Access': 'Validate all request parameters with schemas',
            'Redirect': 'Validate redirect URLs against whitelist'
        }
        return recommendations.get(vuln_type, 'Review and fix the Elixir security issue')
    
    def _create_finding(self, file_path: str, title: str, description: str, 
                       severity: str, lines: str, snippet: str = None, 
                       recommendation: str = None) -> Finding:
        """Create a standardized Finding object"""
        
        # Create CVSS score
        cvss_scores = {'CRITICAL': 9.8, 'HIGH': 7.5, 'MEDIUM': 5.5, 'LOW': 3.0, 'INFO': 2.0}
        cvss_score = CVSSv4(
            score=cvss_scores.get(severity, 5.0),
            vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
        )
        
        # Create tool evidence
        evidence = ToolEvidence(
            tool_name=self.name,
            tool_version=self.version,
            confidence_score=80,
            raw_output=f"Erlang/Elixir security analysis detected: {title}",
            analysis_metadata={
                'analyzer': 'ErlangElixirAnalyzer',
                'pattern_based': snippet is None,
                'file_path': file_path,
                'language': 'erlang' if file_path.endswith('.erl') else 'elixir'
            }
        )
        
        return Finding(
            file=file_path,
            title=title,
            description=description,
            lines=lines,
            impact=f"Erlang/Elixir {severity.lower()} severity security issue affecting BEAM virtual machine security",
            severity=severity.title(),
            cvss_v4=cvss_score,
            snippet=snippet or f"# BEAM platform code analysis in {os.path.basename(file_path)}",
            recommendation=recommendation or "Review and address the Erlang/Elixir security issue",
            sample_fix="% Implement proper BEAM security practices",
            poc="% No proof-of-concept available for static analysis finding",
            owasp=[],
            cwe=[],
            references=[
                "https://erlang.org/doc/",
                "https://elixir-lang.org/",
                "https://hexdocs.pm/dialyxir/",
                "https://hexdocs.pm/credo/",
                "https://sobelow.io/",
                "https://erlang.org/doc/man/dialyzer.html"
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
        file_path = metadata.get('file_path', 'unknown.ex')
        
        # Simple parsing - look for Erlang/Elixir warnings and errors
        lines = raw_output.strip().split('\n')
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in ['error', 'warning', 'security', 'unsafe']):
                # Extract basic information from the line
                title = line.strip()
                description = f"Erlang/Elixir security issue detected: {title}"
                
                # Determine severity based on content
                severity = 'Medium'
                if any(keyword in line.lower() for keyword in ['critical', 'unsafe', 'dangerous']):
                    severity = 'High'
                elif 'warning' in line.lower():
                    severity = 'Medium'
                elif 'error' in line.lower():
                    severity = 'High'
                
                finding = self._create_finding(
                    file_path=file_path,
                    title=title[:100],  # Truncate if too long
                    description=description,
                    severity=severity,
                    lines=str(i + 1),
                    snippet=line.strip()
                )
                findings.append(finding)
        
        return findings


# Export the analyzer
__all__ = ['ErlangElixirAnalyzer']