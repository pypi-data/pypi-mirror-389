"""
Solidity Smart Contract Security Analyzer
Comprehensive security analysis for Solidity smart contracts using Slither and pattern-based detection.
"""

import json
import re
import subprocess
import tempfile
import os
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple

from ..schemas.findings import Finding, Severity, ToolEvidence, CVSSv4
from .base import SecurityScannerBase


@dataclass
class SolidityPattern:
    """Represents a security pattern for Solidity analysis."""
    name: str
    pattern: str
    severity: Severity
    description: str
    category: str
    cwe_id: Optional[str] = None
    recommendation: Optional[str] = None


class SolidityTool(SecurityScannerBase):
    """Security analysis tool for Solidity smart contracts."""
    
    name = "solidity"
    description = "Solidity smart contract security analyzer with Slither integration"
    
    # Solidity-specific security patterns
    SECURITY_PATTERNS = [
        SolidityPattern(
            name="reentrancy_vulnerability",
            pattern=r"(\.call\.value|\.transfer|\.send)\s*\([^)]*\).*?(?=\n.*?(?!require|assert))",
            severity=Severity.HIGH,
            description="Potential reentrancy vulnerability - state changes after external calls",
            category="smart_contract",
            cwe_id="CWE-841",
            recommendation="Use checks-effects-interactions pattern and reentrancy guards"
        ),
        SolidityPattern(
            name="unchecked_low_level_call",
            pattern=r"\.call\s*\((?!.*require|.*assert)",
            severity=Severity.HIGH,
            description="Unchecked low-level call - return value should be verified",
            category="smart_contract",
            cwe_id="CWE-252",
            recommendation="Always check return value of low-level calls"
        ),
        SolidityPattern(
            name="unsafe_delegatecall",
            pattern=r"\.delegatecall\s*\(",
            severity=Severity.HIGH,
            description="Unsafe delegatecall usage can lead to storage corruption",
            category="smart_contract",
            cwe_id="CWE-470",
            recommendation="Avoid delegatecall or ensure target contract is trusted"
        ),
        SolidityPattern(
            name="integer_overflow",
            pattern=r"(\w+\s*[\+\-\*\/]\s*\w+)(?!.*(?:SafeMath|unchecked))",
            severity=Severity.MEDIUM,
            description="Potential integer overflow/underflow (pre-Solidity 0.8.0)",
            category="smart_contract",
            cwe_id="CWE-190",
            recommendation="Use SafeMath library or Solidity 0.8.0+ with built-in checks"
        ),
        SolidityPattern(
            name="weak_randomness",
            pattern=r"(block\.timestamp|block\.number|block\.difficulty|blockhash)\s*%",
            severity=Severity.HIGH,
            description="Weak randomness source using block properties",
            category="smart_contract",
            cwe_id="CWE-338",
            recommendation="Use commit-reveal schemes or external oracles for randomness"
        ),
        SolidityPattern(
            name="tx_origin_usage",
            pattern=r"tx\.origin",
            severity=Severity.MEDIUM,
            description="Usage of tx.origin for authorization is unsafe",
            category="smart_contract",
            cwe_id="CWE-346",
            recommendation="Use msg.sender instead of tx.origin for authorization"
        ),
        SolidityPattern(
            name="missing_access_control",
            pattern=r"function\s+(\w+)\s*\([^)]*\)\s*(?:public|external)(?!.*(?:onlyOwner|require\s*\(\s*msg\.sender))",
            severity=Severity.MEDIUM,
            description="Public/external function missing access control",
            category="smart_contract",
            cwe_id="CWE-284",
            recommendation="Add appropriate access control modifiers or checks"
        ),
        SolidityPattern(
            name="uninitialized_storage_pointer",
            pattern=r"(struct|mapping).*?storage\s+\w+(?!\s*=)",
            severity=Severity.HIGH,
            description="Uninitialized storage pointer can corrupt contract storage",
            category="smart_contract",
            cwe_id="CWE-457",
            recommendation="Initialize storage pointers before use"
        ),
        SolidityPattern(
            name="deprecated_functions",
            pattern=r"\.(suicide|throw|sha3|callcode)\s*\(",
            severity=Severity.MEDIUM,
            description="Usage of deprecated Solidity functions",
            category="smart_contract",
            cwe_id="CWE-477",
            recommendation="Replace with modern alternatives: selfdestruct, revert, keccak256, delegatecall"
        ),
        SolidityPattern(
            name="unsafe_external_call",
            pattern=r"this\.(\w+)\s*\(",
            severity=Severity.LOW,
            description="External call to own function via 'this'",
            category="smart_contract",
            cwe_id="CWE-252",
            recommendation="Use internal function calls when possible"
        ),
        SolidityPattern(
            name="hardcoded_gas_limit",
            pattern=r"\.gas\s*\(\s*\d+\s*\)",
            severity=Severity.LOW,
            description="Hardcoded gas limit may cause issues with gas price changes",
            category="smart_contract",
            cwe_id="CWE-665",
            recommendation="Use gasleft() or allow dynamic gas limits"
        ),
        SolidityPattern(
            name="floating_pragma",
            pattern=r"pragma\s+solidity\s+\^",
            severity=Severity.LOW,
            description="Floating pragma allows compilation with multiple versions",
            category="smart_contract",
            cwe_id="CWE-670",
            recommendation="Use specific Solidity version for production contracts"
        ),
        SolidityPattern(
            name="assembly_usage",
            pattern=r"assembly\s*\{",
            severity=Severity.MEDIUM,
            description="Inline assembly usage requires careful security review",
            category="smart_contract",
            cwe_id="CWE-919",
            recommendation="Minimize assembly usage and ensure thorough testing"
        ),
        SolidityPattern(
            name="selfdestruct_usage",
            pattern=r"selfdestruct\s*\(",
            severity=Severity.HIGH,
            description="selfdestruct can be dangerous if not properly protected",
            category="smart_contract",
            cwe_id="CWE-284",
            recommendation="Ensure selfdestruct is properly access-controlled"
        ),
        SolidityPattern(
            name="denial_of_service_gas",
            pattern=r"for\s*\([^)]*;\s*\w+\s*<\s*\w+\.length\s*;",
            severity=Severity.MEDIUM,
            description="Loop over dynamic array may cause gas limit DoS",
            category="smart_contract",
            cwe_id="CWE-400",
            recommendation="Implement pagination or gas-efficient iteration patterns"
        ),
        SolidityPattern(
            name="timestamp_dependence",
            pattern=r"block\.timestamp\s*[<>=!]",
            severity=Severity.LOW,
            description="Block timestamp manipulation by miners",
            category="smart_contract",
            cwe_id="CWE-367",
            recommendation="Use block.number for time-dependent logic or allow reasonable variance"
        )
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.slither_available = False
    
    async def scan(self, target_path: str, **kwargs) -> Any:
        """Scan a Solidity file or directory."""
        from .base import ScanResult
        from datetime import datetime
        
        target = Path(target_path)
        findings = []
        
        if target.is_file():
            findings = self.analyze_file(target)
        elif target.is_dir():
            for sol_file in target.rglob("*.sol"):
                findings.extend(self.analyze_file(sol_file))
        
        return ScanResult(
            tool_name=self.name,
            version=self.get_version(),
            scan_time=datetime.now(),
            target_path=str(target_path),
            findings=findings,
            raw_output="",
            metadata={},
            exit_code=0
        )
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """Normalize findings from raw output."""
        # This tool generates Finding objects directly, no normalization needed
        return []
    
    def get_version(self) -> str:
        """Get tool version."""
        try:
            result = subprocess.run(
                ["slither", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        try:
            result = subprocess.run(
                ["solc", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                # Extract version from solc output
                lines = result.stdout.strip().split('\n')
                for line in lines:
                    if 'Version:' in line:
                        return line.split('Version:')[1].strip()
                return result.stdout.strip().split('\n')[0]
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return "unknown"
    
    def is_available(self) -> bool:
        """Check if Slither is available."""
        try:
            result = subprocess.run(
                ["slither", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.slither_available = True
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
        # Check if solc is available (minimum requirement)
        try:
            result = subprocess.run(
                ["solc", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.SubprocessError, FileNotFoundError):
            return False
    
    def get_file_patterns(self) -> List[str]:
        """Get file patterns for Solidity files."""
        return ["*.sol"]
    
    def analyze_file(self, file_path: Path) -> List[Finding]:
        """Analyze a single Solidity file."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return findings
        
        # Perform pattern-based analysis
        findings.extend(self._analyze_patterns(file_path, content))
        
        # Run Slither if available
        if self.slither_available:
            findings.extend(self._run_slither(file_path))
        
        # Run solc for basic compilation check
        findings.extend(self._run_solc_check(file_path))
        
        return findings
    
    def _analyze_patterns(self, file_path: Path, content: str) -> List[Finding]:
        """Analyze file using security patterns."""
        findings = []
        lines = content.split('\n')
        
        for pattern in self.SECURITY_PATTERNS:
            regex = re.compile(pattern.pattern, re.MULTILINE | re.IGNORECASE)
            
            for match in regex.finditer(content):
                line_num = content[:match.start()].count('\n') + 1
                line_content = lines[line_num - 1] if line_num <= len(lines) else ""
                
                # Skip false positives
                if self._is_false_positive(pattern, match.group(), line_content):
                    continue
                
                # Create CVSS score
                from ..report.cvss import CVSSCalculator
                cvss = CVSSCalculator.vulnerability_to_cvss("smart_contract", {})
                
                finding = Finding(
                    file=str(file_path),
                    title=pattern.description,
                    description=self._build_description(pattern, match.group()),
                    lines=str(line_num),
                    impact=f"Smart contract vulnerability could lead to loss of funds, unauthorized access, or contract malfunction.",
                    severity=pattern.severity.value.capitalize() if hasattr(pattern.severity, 'value') else str(pattern.severity).capitalize(),
                    cvss_v4=cvss,
                    snippet=line_content.strip(),
                    recommendation=pattern.recommendation or "Review and fix the identified security issue",
                    sample_fix=f"# Fix for {pattern.name}\n# Review the code and apply appropriate security measures",
                    poc=f"# Proof of concept\n# Line {line_num}: {line_content.strip()}",
                    owasp=["OWASP-A03"] if pattern.category == "smart_contract" else [],
                    cwe=[pattern.cwe_id] if pattern.cwe_id else [],
                    tool_evidence=[ToolEvidence(tool=self.name, id=f"solidity_{pattern.name}", raw=match.group())]
                )
                findings.append(finding)
        
        return findings
    
    def _is_false_positive(self, pattern: SolidityPattern, matched_text: str, line_content: str) -> bool:
        """Check if a pattern match is a false positive."""
        
        # Skip commented lines
        if re.match(r'\s*(/\*|//)', line_content):
            return True
        
        # Skip string literals
        if matched_text in re.findall(r'["\'].*?["\']', line_content):
            return True
        
        # Pattern-specific false positive checks
        if pattern.name == "missing_access_control":
            # Skip view/pure functions and constructors
            if re.search(r'\b(view|pure|constructor)\b', line_content):
                return True
            # Skip functions with obvious access control
            if re.search(r'\b(onlyOwner|require|assert|modifier)\b', line_content):
                return True
        
        if pattern.name == "integer_overflow":
            # Skip if using SafeMath or unchecked block
            if re.search(r'\b(SafeMath|unchecked)\b', line_content):
                return True
            # Skip Solidity 0.8.0+ which has built-in overflow checks
            if '0.8' in line_content and 'pragma' in line_content:
                return True
        
        if pattern.name == "reentrancy_vulnerability":
            # Skip if there's a reentrancy guard
            if re.search(r'\b(nonReentrant|ReentrancyGuard)\b', line_content):
                return True
        
        return False
    
    def _build_description(self, pattern: SolidityPattern, matched_text: str) -> str:
        """Build detailed description for a finding."""
        base_desc = pattern.description
        
        if pattern.name == "reentrancy_vulnerability":
            return f"{base_desc}. Found: '{matched_text}'. Ensure state changes occur before external calls."
        elif pattern.name == "weak_randomness":
            return f"{base_desc}. Found: '{matched_text}'. Block properties are predictable by miners."
        elif pattern.name == "tx_origin_usage":
            return f"{base_desc}. tx.origin can be manipulated through phishing attacks."
        elif pattern.name == "deprecated_functions":
            replacements = {
                "suicide": "selfdestruct",
                "throw": "revert",
                "sha3": "keccak256",
                "callcode": "delegatecall"
            }
            func_name = matched_text.split('(')[0].split('.')[-1]
            replacement = replacements.get(func_name, "modern alternative")
            return f"{base_desc}. Replace '{func_name}' with '{replacement}'."
        
        return f"{base_desc}. Found: '{matched_text}'"
    
    def _run_slither(self, file_path: Path) -> List[Finding]:
        """Run Slither static analyzer."""
        findings = []
        
        try:
            # Create temporary directory for compilation artifacts
            with tempfile.TemporaryDirectory() as temp_dir:
                result = subprocess.run(
                    ["slither", str(file_path), "--json", "-"],
                    capture_output=True,
                    text=True,
                    timeout=60,
                    cwd=temp_dir
                )
                
                if result.stdout:
                    findings.extend(self._parse_slither_output(file_path, result.stdout))
                    
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Slither timeout for {file_path}")
        except Exception as e:
            self.logger.error(f"Error running Slither on {file_path}: {e}")
        
        return findings
    
    def _parse_slither_output(self, file_path: Path, output: str) -> List[Finding]:
        """Parse Slither JSON output."""
        findings = []
        
        try:
            data = json.loads(output)
            
            for result in data.get('results', {}).get('detectors', []):
                # Map Slither impact to our severity
                impact = result.get('impact', 'Low').lower()
                severity_map = {
                    'informational': Severity.LOW,
                    'low': Severity.LOW,
                    'medium': Severity.MEDIUM,
                    'high': Severity.HIGH,
                    'critical': Severity.CRITICAL
                }
                severity = severity_map.get(impact, Severity.MEDIUM)
                
                # Extract location information
                elements = result.get('elements', [])
                line_number = 1
                code_snippet = ""
                
                if elements:
                    element = elements[0]
                    source_mapping = element.get('source_mapping', {})
                    if source_mapping:
                        line_number = source_mapping.get('lines', [1])[0]
                    
                    # Get code snippet if available
                    if 'source_mapping' in element and 'content' in element['source_mapping']:
                        code_snippet = element['source_mapping']['content']
                
                # Create CVSS score
                from ..report.cvss import CVSSCalculator
                cvss = CVSSCalculator.vulnerability_to_cvss("smart_contract", {})
                
                finding = Finding(
                    file=str(file_path),
                    title=result.get('check', 'Slither Detection'),
                    description=result.get('description', 'No description available'),
                    lines=str(line_number),
                    impact="Smart contract security issue identified by Slither analyzer.",
                    severity=severity.value.capitalize() if hasattr(severity, 'value') else str(severity).capitalize(),
                    cvss_v4=cvss,
                    snippet=code_snippet[:200] if code_snippet else "",
                    recommendation="Review Slither documentation for specific remediation",
                    sample_fix="# Review Slither recommendations and apply appropriate fixes",
                    poc=f"# Slither detection: {result.get('check', 'unknown')}",
                    owasp=["OWASP-A03"],
                    cwe=[],
                    tool_evidence=[ToolEvidence(tool=self.name, id=f"slither_{result.get('check', 'unknown')}", raw=result.get('description', ''))]
                )
                findings.append(finding)
                
        except json.JSONDecodeError as e:
            self.logger.error(f"Error parsing Slither output: {e}")
        except Exception as e:
            self.logger.error(f"Error processing Slither results: {e}")
        
        return findings
    
    def _run_solc_check(self, file_path: Path) -> List[Finding]:
        """Run solc compiler for basic syntax checking."""
        findings = []
        
        try:
            result = subprocess.run(
                ["solc", "--optimize", str(file_path)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode != 0:
                findings.extend(self._parse_solc_errors(file_path, result.stderr))
                
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Solc timeout for {file_path}")
        except Exception as e:
            self.logger.error(f"Error running solc on {file_path}: {e}")
        
        return findings
    
    def _parse_solc_errors(self, file_path: Path, error_output: str) -> List[Finding]:
        """Parse solc compiler error output."""
        findings = []
        
        # Parse solc error format: filename:line:column: Error: message
        pattern = r'([^:]+):(\d+):(\d+):\s*(Error|Warning):\s*(.*)'
        
        for match in re.finditer(pattern, error_output, re.MULTILINE):
            filename, line_str, col_str, error_type, message = match.groups()
            
            line_num = int(line_str)
            col_num = int(col_str)
            
            severity = Severity.HIGH if error_type == "Error" else Severity.MEDIUM
            
            # Create CVSS score
            from ..report.cvss import CVSSCalculator
            cvss = CVSSCalculator.vulnerability_to_cvss("compilation", {})
            
            finding = Finding(
                file=str(file_path),
                title=f"Solidity Compiler {error_type}",
                description=f"Compiler {error_type.lower()}: {message}",
                lines=str(line_num),
                impact=f"Compilation {error_type.lower()} prevents contract deployment and may indicate security issues.",
                severity=severity.value.capitalize() if hasattr(severity, 'value') else str(severity).capitalize(),
                cvss_v4=cvss,
                snippet="",
                recommendation="Fix compilation errors before deployment",
                sample_fix=f"# Fix the compilation {error_type.lower()} at line {line_num}",
                poc=f"# Compiler {error_type}: {message}",
                owasp=[],
                cwe=[],
                tool_evidence=[ToolEvidence(tool=self.name, id="solc_compiler_issue", raw=message)]
            )
            findings.append(finding)
        
        return findings
    
    def supports_file(self, file_path: Path) -> bool:
        """Check if the tool supports analyzing the given file."""
        return file_path.suffix.lower() == '.sol'
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for the tool."""
        return {
            "type": "object",
            "properties": {
                "use_slither": {
                    "type": "boolean",
                    "default": True,
                    "description": "Use Slither for advanced analysis (requires installation)"
                },
                "enabled_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [p.name for p in self.SECURITY_PATTERNS],
                    "description": "List of security patterns to check"
                },
                "severity_override": {
                    "type": "object",
                    "properties": {
                        pattern.name: {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]}
                        for pattern in self.SECURITY_PATTERNS
                    },
                    "description": "Override severity levels for specific patterns"
                },
                "exclude_patterns": {
                    "type": "array",
                    "items": {"type": "string"},
                    "default": [],
                    "description": "Patterns to exclude from analysis"
                },
                "compiler_checks": {
                    "type": "boolean",
                    "default": True,
                    "description": "Enable Solidity compiler validation"
                }
            }
        }
    
    def configure(self, config: Dict[str, Any]) -> None:
        """Configure the tool with provided settings."""
        super().configure(config)
        
        # Filter enabled patterns
        enabled_patterns = config.get('enabled_patterns', [p.name for p in self.SECURITY_PATTERNS])
        self.SECURITY_PATTERNS = [p for p in self.SECURITY_PATTERNS if p.name in enabled_patterns]
        
        # Apply severity overrides
        severity_override = config.get('severity_override', {})
        for pattern in self.SECURITY_PATTERNS:
            if pattern.name in severity_override:
                pattern.severity = Severity(severity_override[pattern.name])
    
    def get_installation_instructions(self) -> str:
        """Get installation instructions for Solidity tools."""
        return """
To install Solidity analysis tools:

1. Install Solidity compiler:
   npm install -g solc
   # OR
   snap install solc
   # OR
   brew install solidity

2. Install Slither (recommended):
   pip install slither-analyzer
   
   # Additional dependencies for better analysis:
   pip install crytic-compile
   
3. Verify installation:
   solc --version
   slither --version

For development environment:
   npm install -g @remix-project/remixd
   npm install -g truffle
   npm install -g hardhat

Documentation:
- Solidity: https://docs.soliditylang.org/
- Slither: https://github.com/crytic/slither
        """.strip()