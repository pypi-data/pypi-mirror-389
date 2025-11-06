"""
Lua Security Analysis Tools Integration
Supports Luacheck and custom security patterns for comprehensive Lua security analysis
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

class LuaAnalyzer(BaseTool):
    """
    Lua Security Analyzer supporting Luacheck and custom security pattern analysis
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "lua_analyzer"
        self.supported_extensions = ['.lua']
        
        # Tool configurations
        self.tools = {
            'luacheck': {
                'command': 'luacheck',
                'enabled': self._check_luacheck_availability(),
                'description': 'Luacheck static analyzer for Lua'
            },
            'lua_interpreter': {
                'command': 'lua',
                'enabled': self._check_lua_availability(),
                'description': 'Lua interpreter for syntax checking'
            },
            'lua_security_check': {
                'command': 'custom',
                'enabled': True,
                'description': 'Custom Lua security pattern analysis'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Lua analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try Luacheck first
            if self.tools['luacheck']['enabled']:
                result = subprocess.run(['luacheck', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"Luacheck {result.stdout.strip()}"
            
            # Try Lua interpreter as fallback
            if self.tools['lua_interpreter']['enabled']:
                result = subprocess.run(['lua', '-v'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            return "Custom Lua Security Analyzer"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Custom Lua Security Analyzer"

    def _check_luacheck_availability(self) -> bool:
        """Check if Luacheck is available"""
        try:
            result = subprocess.run(['luacheck', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_lua_availability(self) -> bool:
        """Check if Lua interpreter is available"""
        try:
            result = subprocess.run(['lua', '-v'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Lua tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Lua security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'lua_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Lua security analysis tools."""
        findings = []
        
        # Check if this is a Lua project
        lua_files = self._find_lua_files(repo_path)
        if not lua_files:
            return findings
        
        # Run Luacheck for static analysis
        if self.tools['luacheck']['enabled']:
            try:
                result = subprocess.run(
                    ['luacheck', '--formatter', 'plain', '--codes'] + lua_files[:10],  # Limit to first 10 files
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                luacheck_findings = self._parse_luacheck_output(result.stdout, repo_path)
                findings.extend(luacheck_findings)
                
            except subprocess.TimeoutExpired:
                logger.warning("Luacheck analysis timed out")
            except Exception as e:
                logger.error(f"Error running Luacheck: {e}")
        
        # Run Lua syntax checking
        if self.tools['lua_interpreter']['enabled']:
            for lua_file in lua_files[:10]:  # Limit to first 10 files
                try:
                    result = subprocess.run(
                        ['lua', '-c', lua_file],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if result.returncode != 0:
                        syntax_finding = self._create_syntax_finding(result.stderr, lua_file, repo_path)
                        if syntax_finding:
                            findings.append(syntax_finding)
                            
                except subprocess.TimeoutExpired:
                    logger.warning(f"Lua syntax check timed out for {lua_file}")
                except Exception as e:
                    logger.error(f"Error running Lua syntax check: {e}")
        
        # Run custom Lua security pattern analysis
        if self.tools['lua_security_check']['enabled']:
            security_findings = self._check_lua_security_patterns(lua_files, repo_path)
            findings.extend(security_findings)
        
        # If no tools available, create placeholder finding
        if not any(self.tools[tool]['enabled'] for tool in self.tools if tool != 'lua_security_check'):
            if lua_files:
                tool_evidence = ToolEvidence(
                    tool="lua_analyzer",
                    id=f"lua_{hash(lua_files[0])}",
                    raw=f"Lua analysis placeholder - found {len(lua_files)} Lua files"
                )
                
                finding = Finding(
                    file=os.path.relpath(lua_files[0], repo_path),
                    title=f"Lua Analysis Placeholder",
                    description=f"Lua security analysis placeholder - found {len(lua_files)} Lua files",
                    lines="1",
                    impact="Potential Lua security or quality issue",
                    severity="Medium",
                    cvss_v4=CVSSv4(
                        score=4.0,
                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                    ),
                    snippet=f"Lua file detected: {os.path.basename(lua_files[0])}",
                    recommendation="Review Lua code for security and quality issues",
                    sample_fix="Apply Lua security best practices",
                    poc=f"Lua analysis in repository",
                    owasp=["A06:2021-Vulnerable and Outdated Components"],
                    cwe=["CWE-1104"],
                    tool_evidence=[tool_evidence]
                )
                findings.append(finding)
        
        return findings

    def _find_lua_files(self, repo_path: str) -> List[str]:
        """Find Lua files in the repository."""
        lua_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.lua'):
                    lua_files.append(os.path.join(root, file))
                # Check for Lua shebang scripts
                elif not any(file.endswith(ext) for ext in ['.py', '.js', '.rb', '.sh', '.pl']):
                    file_path = os.path.join(root, file)
                    if self._has_lua_shebang(file_path):
                        lua_files.append(file_path)
        return lua_files

    def _has_lua_shebang(self, file_path: str) -> bool:
        """Check if file has Lua shebang."""
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                first_line = f.readline().strip()
                return first_line.startswith('#!') and 'lua' in first_line
        except Exception:
            return False

    def _parse_luacheck_output(self, output: str, repo_path: str) -> List[Finding]:
        """Parse Luacheck output."""
        findings = []
        
        if not output.strip():
            return findings
        
        lines = output.split('\n')
        for line in lines:
            # Luacheck format: file:line:column: (Wcode) message
            if ':' in line and '(' in line and 'W' in line:
                finding = self._create_luacheck_finding(line, repo_path)
                if finding:
                    findings.append(finding)
        
        return findings

    def _check_lua_security_patterns(self, lua_files: List[str], repo_path: str) -> List[Finding]:
        """Check for Lua-specific security patterns."""
        findings = []
        
        # Security patterns to look for
        security_patterns = [
            ('loadstring(', 'Code evaluation - potential code injection risk'),
            ('load(', 'Dynamic code loading - potential security risk'),
            ('dofile(', 'File execution - validate file paths'),
            ('loadfile(', 'File loading - validate file paths'),
            ('os.execute(', 'Command execution - potential command injection'),
            ('io.popen(', 'Process execution - potential command injection'),
            ('io.open(', 'File operation - review for path traversal'),
            ('require(', 'Module loading - validate module names'),
            ('package.loadlib(', 'Library loading - validate library paths'),
            ('debug.', 'Debug functions - may expose sensitive information'),
            ('getfenv(', 'Environment access - review for security implications'),
            ('setfenv(', 'Environment modification - potential security risk'),
            ('rawget(', 'Raw table access - bypass metamethods'),
            ('rawset(', 'Raw table modification - bypass metamethods'),
            ('_G[', 'Global environment access - potential security risk'),
            ('math.random(', 'Random number generation - ensure proper seeding'),
            ('string.dump(', 'Function serialization - review for security'),
            ('collectgarbage(', 'Garbage collection control - potential DoS'),
            ('coroutine.', 'Coroutine usage - review for security implications'),
            ('bit32.', 'Bit operations - review for security implications')
        ]
        
        for lua_file in lua_files[:15]:  # Limit to first 15 files
            try:
                with open(lua_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, description in security_patterns:
                            if pattern in line:
                                tool_evidence = ToolEvidence(
                                    tool="lua_security_check",
                                    id=f"lua_{pattern}_{hash(lua_file + str(line_num))}",
                                    raw=f"Pattern '{pattern}' found in line: {line.strip()}"
                                )
                                
                                # Determine severity based on pattern
                                high_risk_patterns = ['loadstring(', 'load(', 'os.execute(', 'io.popen(', 'setfenv(']
                                medium_risk_patterns = ['dofile(', 'loadfile(', 'require(', 'package.loadlib(', 'debug.']
                                
                                if any(p in pattern for p in high_risk_patterns):
                                    severity = "High"
                                elif any(p in pattern for p in medium_risk_patterns):
                                    severity = "Medium"
                                else:
                                    severity = "Low"
                                
                                finding = Finding(
                                    file=os.path.relpath(lua_file, repo_path),
                                    title=f"Lua Security Pattern: {pattern.rstrip('(')}",
                                    description=description,
                                    lines=str(line_num),
                                    impact=f"Potential Lua security vulnerability: {description}",
                                    severity=severity,
                                    cvss_v4=CVSSv4(
                                        score=7.0 if severity == "High" else (5.0 if severity == "Medium" else 3.0),
                                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                                    ),
                                    snippet=line.strip(),
                                    recommendation=f"Review usage of {pattern} for security implications",
                                    sample_fix="Use secure alternatives and validate all inputs",
                                    poc=f"Pattern found in {lua_file}",
                                    owasp=["A03:2021-Injection"] if any(p in pattern for p in ['loadstring', 'load', 'execute', 'popen']) else ["A06:2021-Vulnerable and Outdated Components"],
                                    cwe=["CWE-94"] if any(p in pattern for p in ['loadstring', 'load']) else ["CWE-78"] if any(p in pattern for p in ['execute', 'popen']) else ["CWE-200"],
                                    tool_evidence=[tool_evidence]
                                )
                                findings.append(finding)
                                
            except Exception as e:
                logger.error(f"Error reading file {lua_file}: {e}")
        
        return findings

    def _create_luacheck_finding(self, line: str, repo_path: str) -> Finding:
        """Create a Finding from Luacheck output line."""
        try:
            # Parse Luacheck output format: file:line:column: (Wcode) message
            parts = line.split(':')
            if len(parts) < 3:
                return None
            
            file_path = parts[0]
            line_num = parts[1] if parts[1].isdigit() else "1"
            message_part = ':'.join(parts[3:]) if len(parts) > 3 else line
            
            # Extract warning code
            warning_code = "W000"
            if '(' in message_part and ')' in message_part:
                warning_match = message_part.split('(')[1].split(')')[0]
                if warning_match.startswith('W'):
                    warning_code = warning_match
            
            # Extract message
            message = message_part.split(') ')[-1] if ') ' in message_part else message_part
            
            tool_evidence = ToolEvidence(
                tool="luacheck",
                id=f"luacheck_{warning_code}_{hash(file_path + line_num)}",
                raw=line
            )
            
            # Map Luacheck warning codes to severity
            high_severity_codes = ['W113', 'W131', 'W142']  # Undefined variables, unused arguments, etc.
            medium_severity_codes = ['W211', '212', 'W213', 'W221', 'W231']  # Unused variables, arguments
            
            if warning_code in high_severity_codes:
                severity = "High"
            elif warning_code in medium_severity_codes:
                severity = "Medium"
            else:
                severity = "Low"
            
            return Finding(
                file=os.path.relpath(file_path, repo_path),
                title=f"Luacheck {warning_code}: {message[:50]}...",
                description=f"Luacheck warning: {message}",
                lines=line_num,
                impact="Code quality issue that may affect functionality or security",
                severity=severity,
                cvss_v4=CVSSv4(
                    score=5.0 if severity == "High" else (3.0 if severity == "Medium" else 1.0),
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line_num}: {warning_code}",
                recommendation="Fix the Luacheck warning to improve code quality",
                sample_fix="Follow Lua best practices and coding standards",
                poc=f"Luacheck analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Luacheck finding: {e}")
            return None

    def _create_syntax_finding(self, error_output: str, file_path: str, repo_path: str) -> Finding:
        """Create a Finding from Lua syntax error."""
        try:
            tool_evidence = ToolEvidence(
                tool="lua_syntax_check",
                id=f"lua_syntax_{hash(file_path)}",
                raw=error_output
            )
            
            # Extract line number from error if possible
            line_num = "1"
            if ':' in error_output:
                parts = error_output.split(':')
                for part in parts:
                    if part.strip().isdigit():
                        line_num = part.strip()
                        break
            
            return Finding(
                file=os.path.relpath(file_path, repo_path),
                title="Lua Syntax Error",
                description=f"Lua syntax error: {error_output.strip()}",
                lines=line_num,
                impact="Syntax error prevents code execution",
                severity="High",
                cvss_v4=CVSSv4(
                    score=6.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Syntax error at line {line_num}",
                recommendation="Fix the syntax error to enable code execution",
                sample_fix="Review Lua syntax and fix the reported error",
                poc=f"Lua syntax check in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-1176"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Lua syntax finding: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['lua']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Lua Security Analyzer',
            'description': 'Comprehensive Lua security analysis using Luacheck and custom security pattern checks',
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
LuaTool = LuaAnalyzer