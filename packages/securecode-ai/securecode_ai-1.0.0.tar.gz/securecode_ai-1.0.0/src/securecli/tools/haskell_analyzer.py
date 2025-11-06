"""
Haskell Security Analysis Tools Integration
Supports HLint, Weeder, and GHC warnings for comprehensive Haskell security analysis
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

class HaskellAnalyzer(BaseTool):
    """
    Haskell Security Analyzer supporting HLint, Weeder, and GHC warnings
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.name = "haskell_analyzer"
        self.supported_extensions = ['.hs', '.lhs']
        
        # Tool configurations
        self.tools = {
            'hlint': {
                'command': 'hlint',
                'enabled': self._check_hlint_availability(),
                'description': 'HLint suggestions and code quality analysis for Haskell'
            },
            'weeder': {
                'command': 'weeder',
                'enabled': self._check_weeder_availability(),
                'description': 'Weeder dead code detection for Haskell'
            },
            'ghc': {
                'command': 'ghc',
                'enabled': self._check_ghc_availability(),
                'description': 'GHC compiler warnings and type checking'
            },
            'stack': {
                'command': 'stack',
                'enabled': self._check_stack_availability(),
                'description': 'Stack build tool for Haskell projects'
            }
        }
    
    def is_available(self) -> bool:
        """Check if Haskell analysis tools are available"""
        return any(tool_info['enabled'] for tool_info in self.tools.values())
    
    def get_version(self) -> str:
        """Get tool version information"""
        try:
            # Try HLint first
            if self.tools['hlint']['enabled']:
                result = subprocess.run(['hlint', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return f"HLint {result.stdout.strip()}"
            
            # Try GHC as fallback
            if self.tools['ghc']['enabled']:
                result = subprocess.run(['ghc', '--version'], 
                                      capture_output=True, text=True, timeout=10)
                if result.returncode == 0:
                    return result.stdout.strip()
            
            return "Unknown"
        except (subprocess.SubprocessError, FileNotFoundError):
            return "Not available"

    def _check_hlint_availability(self) -> bool:
        """Check if HLint is available"""
        try:
            result = subprocess.run(['hlint', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_weeder_availability(self) -> bool:
        """Check if Weeder is available"""
        try:
            result = subprocess.run(['weeder', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_ghc_availability(self) -> bool:
        """Check if GHC is available"""
        try:
            result = subprocess.run(['ghc', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def _check_stack_availability(self) -> bool:
        """Check if Stack is available"""
        try:
            result = subprocess.run(['stack', '--version'], 
                                  capture_output=True, text=True, timeout=10)
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False

    def normalize_findings(self, raw_findings: list) -> List[Finding]:
        """Normalize findings from Haskell tools to standard format."""
        normalized = []
        for finding in raw_findings:
            if isinstance(finding, Finding):
                # Already normalized
                normalized.append(finding)
            elif isinstance(finding, dict):
                # Convert dict to Finding
                normalized.append(Finding(
                    title=finding.get('title', 'Haskell security issue'),
                    description=finding.get('description', ''),
                    file_path=finding.get('file_path', ''),
                    line_number=finding.get('line_number', 0),
                    severity=finding.get('severity', 'medium'),
                    tool=finding.get('tool', 'haskell_analyzer'),
                    rule_id=finding.get('rule_id', '')
                ))
        return normalized

    async def scan(self, repo_path: str, config: Dict[str, Any] = None) -> List[Finding]:
        """Run Haskell security analysis tools."""
        findings = []
        
        # Check if this is a Haskell project
        haskell_files = self._find_haskell_files(repo_path)
        if not haskell_files:
            return findings
        
        is_stack_project = self._is_stack_project(repo_path)
        is_cabal_project = self._is_cabal_project(repo_path)
        
        # Run HLint for code quality and suggestions
        if self.tools['hlint']['enabled']:
            try:
                result = subprocess.run(
                    ['hlint', '--json', repo_path],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=120
                )
                
                hlint_findings = self._parse_hlint_output(result.stdout, repo_path)
                findings.extend(hlint_findings)
                
            except subprocess.TimeoutExpired:
                logger.warning("HLint analysis timed out")
            except Exception as e:
                logger.error(f"Error running HLint: {e}")
        
        # Run Weeder for dead code detection (if it's a Stack or Cabal project)
        if self.tools['weeder']['enabled'] and (is_stack_project or is_cabal_project):
            try:
                result = subprocess.run(
                    ['weeder'],
                    cwd=repo_path,
                    capture_output=True,
                    text=True,
                    timeout=180
                )
                
                weeder_findings = self._parse_weeder_output(result.stdout, repo_path)
                findings.extend(weeder_findings)
                
            except subprocess.TimeoutExpired:
                logger.warning("Weeder analysis timed out")
            except Exception as e:
                logger.error(f"Error running Weeder: {e}")
        
        # Run GHC type checking and warnings
        if self.tools['ghc']['enabled']:
            for haskell_file in haskell_files[:10]:  # Limit to first 10 files
                try:
                    result = subprocess.run(
                        ['ghc', '-Wall', '-fno-warn-unused-imports', '-fno-code', haskell_file],
                        cwd=repo_path,
                        capture_output=True,
                        text=True,
                        timeout=60
                    )
                    
                    ghc_findings = self._parse_ghc_output(result.stderr, haskell_file, repo_path)
                    findings.extend(ghc_findings)
                    
                except subprocess.TimeoutExpired:
                    logger.warning(f"GHC analysis timed out for {haskell_file}")
                except Exception as e:
                    logger.error(f"Error running GHC: {e}")
        
        # Run Haskell security pattern analysis
        security_findings = self._check_haskell_security_patterns(haskell_files, repo_path)
        findings.extend(security_findings)
        
        # If no tools available, create placeholder finding
        if not any(self.tools[tool]['enabled'] for tool in self.tools):
            if haskell_files:
                tool_evidence = ToolEvidence(
                    tool="haskell_analyzer",
                    id=f"haskell_{hash(haskell_files[0])}",
                    raw=f"Haskell analysis placeholder - found {len(haskell_files)} Haskell files"
                )
                
                finding = Finding(
                    file=os.path.relpath(haskell_files[0], repo_path),
                    title=f"Haskell Analysis Placeholder",
                    description=f"Haskell security analysis placeholder - found {len(haskell_files)} Haskell files",
                    lines="1",
                    impact="Potential Haskell security or quality issue",
                    severity="Medium",
                    cvss_v4=CVSSv4(
                        score=4.0,
                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                    ),
                    snippet=f"Haskell file detected: {os.path.basename(haskell_files[0])}",
                    recommendation="Review Haskell code for functional programming security best practices",
                    sample_fix="Apply Haskell security and type safety guidelines",
                    poc=f"Haskell analysis in repository",
                    owasp=["A06:2021-Vulnerable and Outdated Components"],
                    cwe=["CWE-1104"],
                    tool_evidence=[tool_evidence]
                )
                findings.append(finding)
        
        return findings

    def _find_haskell_files(self, repo_path: str) -> List[str]:
        """Find Haskell files in the repository."""
        haskell_files = []
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if any(file.endswith(ext) for ext in self.supported_extensions):
                    haskell_files.append(os.path.join(root, file))
        return haskell_files

    def _is_stack_project(self, repo_path: str) -> bool:
        """Check if this is a Stack project."""
        return os.path.exists(os.path.join(repo_path, 'stack.yaml'))

    def _is_cabal_project(self, repo_path: str) -> bool:
        """Check if this is a Cabal project."""
        for root, dirs, files in os.walk(repo_path):
            for file in files:
                if file.endswith('.cabal'):
                    return True
        return False

    def _parse_hlint_output(self, output: str, repo_path: str) -> List[Finding]:
        """Parse HLint JSON output."""
        findings = []
        
        if not output.strip():
            return findings
        
        try:
            hlint_data = json.loads(output)
            
            for hint in hlint_data:
                finding = self._create_hlint_finding(hint, repo_path)
                if finding:
                    findings.append(finding)
                    
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing HLint JSON: {e}")
        except Exception as e:
            logger.error(f"Error processing HLint output: {e}")
        
        return findings

    def _parse_weeder_output(self, output: str, repo_path: str) -> List[Finding]:
        """Parse Weeder output."""
        findings = []
        
        if not output.strip():
            return findings
        
        lines = output.split('\n')
        current_finding = {}
        
        for line in lines:
            line = line.strip()
            if line.startswith('='):
                if current_finding:
                    finding = self._create_weeder_finding(current_finding, repo_path)
                    if finding:
                        findings.append(finding)
                    current_finding = {}
            elif ':' in line and line.count(':') >= 2:
                # Format: file:line:col: message
                parts = line.split(':')
                if len(parts) >= 3:
                    current_finding['file'] = parts[0]
                    current_finding['line'] = parts[1]
                    current_finding['message'] = ':'.join(parts[3:]).strip()
        
        if current_finding:
            finding = self._create_weeder_finding(current_finding, repo_path)
            if finding:
                findings.append(finding)
        
        return findings

    def _parse_ghc_output(self, output: str, file_path: str, repo_path: str) -> List[Finding]:
        """Parse GHC warning/error output."""
        findings = []
        
        if not output.strip():
            return findings
        
        lines = output.split('\n')
        for line in lines:
            if 'warning:' in line.lower() or 'error:' in line.lower():
                finding = self._create_ghc_finding(line, file_path, repo_path)
                if finding:
                    findings.append(finding)
        
        return findings

    def _check_haskell_security_patterns(self, haskell_files: List[str], repo_path: str) -> List[Finding]:
        """Check for Haskell-specific security patterns."""
        findings = []
        
        # Security patterns to look for
        security_patterns = [
            ('unsafePerformIO', 'Unsafe IO operation - breaks referential transparency'),
            ('unsafeCoerce', 'Unsafe type coercion - can cause runtime errors'),
            ('unsafeHead', 'Unsafe head operation - can throw exception on empty list'),
            ('unsafeTail', 'Unsafe tail operation - can throw exception on empty list'),
            ('unsafeIndex', 'Unsafe indexing - can cause out-of-bounds errors'),
            ('undefined', 'Undefined value - causes runtime exception'),
            ('error ', 'Error function - causes runtime exception'),
            ('fromJust', 'Unsafe Maybe extraction - can throw exception on Nothing'),
            ('fromLeft', 'Unsafe Either extraction - can throw exception'),
            ('fromRight', 'Unsafe Either extraction - can throw exception'),
            ('read ', 'Unsafe string parsing - can throw exception on invalid input'),
            ('!!', 'Unsafe list indexing - can cause out-of-bounds errors'),
            ('head ', 'Unsafe head function - can throw exception on empty list'),
            ('tail ', 'Unsafe tail function - can throw exception on empty list'),
            ('init ', 'Unsafe init function - can throw exception on empty list'),
            ('last ', 'Unsafe last function - can throw exception on empty list'),
            ('maximum ', 'Unsafe maximum function - can throw exception on empty list'),
            ('minimum ', 'Unsafe minimum function - can throw exception on empty list'),
            ('succ ', 'Successor function - can overflow'),
            ('pred ', 'Predecessor function - can underflow'),
            ('toEnum ', 'Enum conversion - can throw exception on invalid value'),
            ('div ', 'Division - can throw exception on division by zero'),
            ('fromIntegral', 'Numeric conversion - potential overflow/underflow'),
            ('realToFrac', 'Floating point conversion - potential precision loss'),
            ('System.Process', 'Process execution - potential command injection'),
            ('System.IO.Unsafe', 'Unsafe IO operations - breaks purity'),
            ('Foreign.', 'Foreign function interface - potential memory safety issues'),
            ('Ptr ', 'Raw pointer usage - potential memory safety issues'),
            ('alloca', 'Memory allocation - potential memory leaks'),
            ('malloc', 'Manual memory management - potential memory issues')
        ]
        
        for haskell_file in haskell_files[:15]:  # Limit to first 15 files
            try:
                with open(haskell_file, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    lines = content.split('\n')
                    
                    for line_num, line in enumerate(lines, 1):
                        for pattern, description in security_patterns:
                            if pattern in line:
                                tool_evidence = ToolEvidence(
                                    tool="haskell_security_check",
                                    id=f"haskell_{pattern}_{hash(haskell_file + str(line_num))}",
                                    raw=f"Pattern '{pattern}' found in line: {line.strip()}"
                                )
                                
                                # Determine severity based on pattern
                                high_risk_patterns = ['unsafePerformIO', 'unsafeCoerce', 'undefined', 'error ', 'System.Process']
                                medium_risk_patterns = ['unsafeHead', 'unsafeTail', 'fromJust', 'read ', '!!', 'div ']
                                
                                if any(p in pattern for p in high_risk_patterns):
                                    severity = "High"
                                elif any(p in pattern for p in medium_risk_patterns):
                                    severity = "Medium"
                                else:
                                    severity = "Low"
                                
                                finding = Finding(
                                    file=os.path.relpath(haskell_file, repo_path),
                                    title=f"Haskell Security Pattern: {pattern.strip()}",
                                    description=description,
                                    lines=str(line_num),
                                    impact=f"Potential Haskell safety violation: {description}",
                                    severity=severity,
                                    cvss_v4=CVSSv4(
                                        score=7.0 if severity == "High" else (5.0 if severity == "Medium" else 3.0),
                                        vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                                    ),
                                    snippet=line.strip(),
                                    recommendation=f"Review usage of {pattern} for safety implications",
                                    sample_fix="Use safe alternatives and handle potential exceptions",
                                    poc=f"Pattern found in {haskell_file}",
                                    owasp=["A06:2021-Vulnerable and Outdated Components"],
                                    cwe=["CWE-248"] if 'unsafe' in pattern.lower() else ["CWE-754"],
                                    tool_evidence=[tool_evidence]
                                )
                                findings.append(finding)
                                
            except Exception as e:
                logger.error(f"Error reading file {haskell_file}: {e}")
        
        return findings

    def _create_hlint_finding(self, hint: dict, repo_path: str) -> Finding:
        """Create a Finding from HLint hint."""
        try:
            severity = hint.get('severity', 'Warning')
            hint_type = hint.get('hint', 'HLint suggestion')
            file_path = hint.get('file', 'unknown')
            
            start_line = hint.get('startLine', 1)
            end_line = hint.get('endLine', start_line)
            
            from_code = hint.get('from', '')
            to_code = hint.get('to', '')
            note = hint.get('note', [])
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="hlint",
                id=f"hlint_{hint_type}_{hash(file_path + str(start_line))}",
                raw=json.dumps(hint)
            )
            
            severity_map = {'Error': 'High', 'Warning': 'Medium', 'Suggestion': 'Low'}
            mapped_severity = severity_map.get(severity, 'Medium')
            
            description = f"HLint {severity}: {hint_type}"
            if from_code and to_code:
                description += f"\n\nFound: {from_code}\nSuggestion: {to_code}"
            if note:
                description += f"\nNote: {' '.join(note)}"
            
            return Finding(
                file=file_path,
                title=f"HLint: {hint_type}",
                description=description,
                lines=f"{start_line}" if start_line == end_line else f"{start_line}-{end_line}",
                impact="Code quality issue that may affect maintainability",
                severity=mapped_severity,
                cvss_v4=CVSSv4(
                    score=5.0 if mapped_severity == "High" else (3.0 if mapped_severity == "Medium" else 1.0),
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=from_code if from_code else f"Line {start_line}",
                recommendation="Apply the HLint suggestion to improve code quality",
                sample_fix=to_code if to_code else "Follow HLint recommendations",
                poc=f"HLint analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating HLint finding: {e}")
            return None

    def _create_weeder_finding(self, weeder_data: dict, repo_path: str) -> Finding:
        """Create a Finding from Weeder output."""
        try:
            file_path = weeder_data.get('file', 'unknown')
            line_num = weeder_data.get('line', '1')
            message = weeder_data.get('message', 'Dead code detected')
            
            # Make file path relative
            if file_path.startswith(repo_path):
                file_path = os.path.relpath(file_path, repo_path)
            
            tool_evidence = ToolEvidence(
                tool="weeder",
                id=f"weeder_{hash(file_path + line_num)}",
                raw=f"File: {file_path}, Line: {line_num}, Message: {message}"
            )
            
            return Finding(
                file=file_path,
                title="Weeder: Dead Code Detected",
                description=f"Weeder found dead code: {message}",
                lines=line_num,
                impact="Dead code increases maintenance burden and potential attack surface",
                severity="Low",
                cvss_v4=CVSSv4(
                    score=2.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line_num}: dead code",
                recommendation="Remove dead code to improve maintainability",
                sample_fix="Delete unused functions, imports, or data types",
                poc=f"Weeder analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-1164"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating Weeder finding: {e}")
            return None

    def _create_ghc_finding(self, line: str, file_path: str, repo_path: str) -> Finding:
        """Create a Finding from GHC warning/error."""
        try:
            is_error = 'error:' in line.lower()
            severity = "High" if is_error else "Medium"
            
            # Extract line number if present
            line_num = "1"
            if ':' in line:
                parts = line.split(':')
                for part in parts:
                    if part.strip().isdigit():
                        line_num = part.strip()
                        break
            
            tool_evidence = ToolEvidence(
                tool="ghc",
                id=f"ghc_{hash(file_path + line_num)}",
                raw=line
            )
            
            message_type = "error" if is_error else "warning"
            
            return Finding(
                file=os.path.relpath(file_path, repo_path),
                title=f"GHC {message_type.title()}: Type System Issue",
                description=f"GHC {message_type}: {line.strip()}",
                lines=line_num,
                impact=f"Type system {message_type} affecting code safety",
                severity=severity,
                cvss_v4=CVSSv4(
                    score=6.0 if severity == "High" else 4.0,
                    vector="CVSS:4.0/AV:L/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:N/SC:N/SI:N/SA:N"
                ),
                snippet=f"Line {line_num}: {message_type}",
                recommendation=f"Fix the GHC {message_type} to ensure type safety",
                sample_fix="Resolve type errors and warnings for safe code",
                poc=f"GHC analysis in {repo_path}",
                owasp=["A06:2021-Vulnerable and Outdated Components"],
                cwe=["CWE-704"] if is_error else ["CWE-691"],
                tool_evidence=[tool_evidence]
            )
        except Exception as e:
            logger.error(f"Error creating GHC finding: {e}")
            return None

    def get_supported_languages(self) -> List[str]:
        """Return list of supported languages"""
        return ['haskell']
    
    def get_tool_info(self) -> Dict[str, Any]:
        """Return information about available tools"""
        return {
            'name': 'Haskell Security Analyzer',
            'description': 'Comprehensive Haskell security analysis using HLint, Weeder, GHC warnings, and functional programming safety checks',
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
HaskellTool = HaskellAnalyzer