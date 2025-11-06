"""
Vyper Smart Contract Security Analyzer
Comprehensive security analysis for Vyper smart contracts with pattern-based detection.
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
class VyperPattern:
    """Represents a security pattern for Vyper analysis."""
    name: str
    pattern: str
    severity: Severity
    description: str
    category: str
    cwe_id: Optional[str] = None
    recommendation: Optional[str] = None


class VyperTool(SecurityScannerBase):
    """Security analysis tool for Vyper smart contracts."""
    
    name = "vyper"
    description = "Vyper smart contract security analyzer"
    
    # Vyper-specific security patterns
    SECURITY_PATTERNS = [
        VyperPattern(
            name="reentrancy_vulnerability",
            pattern=r"(send|raw_call)\s*\([^)]*\)\s*(?!.*require|.*assert)",
            severity=Severity.HIGH,
            description="Potential reentrancy vulnerability - external call without proper checks",
            category="smart_contract",
            cwe_id="CWE-841",
            recommendation="Use checks-effects-interactions pattern and reentrancy guards"
        ),
        VyperPattern(
            name="unchecked_send",
            pattern=r"send\s*\([^)]*\)(?!\s*(?:and|or|\.|,))",
            severity=Severity.MEDIUM,
            description="Unchecked send() call - return value should be verified",
            category="smart_contract",
            cwe_id="CWE-252",
            recommendation="Always check return value of send() calls"
        ),
        VyperPattern(
            name="unsafe_raw_call",
            pattern=r"raw_call\s*\([^)]*,\s*[^,)]*,\s*gas\s*=\s*msg\.gas",
            severity=Severity.HIGH,
            description="Unsafe raw_call with all remaining gas",
            category="smart_contract",
            cwe_id="CWE-400",
            recommendation="Specify explicit gas limits for external calls"
        ),
        VyperPattern(
            name="integer_overflow",
            pattern=r"(\w+\s*[\+\-\*\/]\s*\w+)(?!.*(?:checked_|safe_))",
            severity=Severity.MEDIUM,
            description="Potential integer overflow/underflow",
            category="smart_contract",
            cwe_id="CWE-190",
            recommendation="Use Vyper's built-in overflow protection or explicit checks"
        ),
        VyperPattern(
            name="weak_randomness",
            pattern=r"(block\.timestamp|block\.number|block\.difficulty)\s*%",
            severity=Severity.HIGH,
            description="Weak randomness source using block properties",
            category="smart_contract",
            cwe_id="CWE-338",
            recommendation="Use commit-reveal schemes or external oracles for randomness"
        ),
        VyperPattern(
            name="missing_access_control",
            pattern=r"def\s+(\w+)\s*\([^)]*\)\s*->.*?:\s*(?!.*(?:assert|require).*(?:msg\.sender|self\.owner))",
            severity=Severity.MEDIUM,
            description="Function missing access control checks",
            category="smart_contract",
            cwe_id="CWE-284",
            recommendation="Add appropriate access control checks (owner, permissions)"
        ),
        VyperPattern(
            name="unsafe_delegatecall",
            pattern=r"raw_call\s*\([^)]*,\s*[^,)]*,\s*delegate_call\s*=\s*True",
            severity=Severity.HIGH,
            description="Unsafe delegatecall usage",
            category="smart_contract",
            cwe_id="CWE-470",
            recommendation="Avoid delegatecall or ensure target contract is trusted"
        ),
        VyperPattern(
            name="hardcoded_gas_limit",
            pattern=r"gas\s*=\s*\d+(?!.*(?:gasleft|gas_remaining))",
            severity=Severity.LOW,
            description="Hardcoded gas limit may cause issues with gas price changes",
            category="smart_contract",
            cwe_id="CWE-665",
            recommendation="Use dynamic gas calculations or gas estimation"
        ),
        VyperPattern(
            name="uninitialized_storage",
            pattern=r"(\w+:\s*(?:HashMap|DynArray).*?=\s*empty)",
            severity=Severity.MEDIUM,
            description="Potentially uninitialized storage variable",
            category="smart_contract",
            cwe_id="CWE-457",
            recommendation="Ensure proper initialization of storage variables"
        ),
        VyperPattern(
            name="tx_origin_usage",
            pattern=r"tx\.origin",
            severity=Severity.MEDIUM,
            description="Usage of tx.origin for authorization is unsafe",
            category="smart_contract",
            cwe_id="CWE-346",
            recommendation="Use msg.sender instead of tx.origin for authorization"
        ),
        VyperPattern(
            name="unchecked_external_call",
            pattern=r"(\w+)\.(\w+)\([^)]*\)(?!\s*(?:and|or|,|\.))",
            severity=Severity.MEDIUM,
            description="External contract call without error handling",
            category="smart_contract",
            cwe_id="CWE-252",
            recommendation="Check return values and handle potential failures"
        ),
        VyperPattern(
            name="denial_of_service_gas",
            pattern=r"for\s+\w+\s+in\s+range\s*\(\s*len\s*\(\s*\w+\s*\)\s*\)",
            severity=Severity.MEDIUM,
            description="Unbounded loop may cause gas limit DoS",
            category="smart_contract",
            cwe_id="CWE-400",
            recommendation="Implement pagination or gas-efficient iteration patterns"
        ),
        VyperPattern(
            name="front_running_vulnerability",
            pattern=r"block\.timestamp.*<.*\d+",
            severity=Severity.LOW,
            description="Time-dependent logic vulnerable to front-running",
            category="smart_contract",
            cwe_id="CWE-362",
            recommendation="Use commit-reveal schemes for time-sensitive operations"
        ),
        VyperPattern(
            name="insufficient_gas_griefing",
            pattern=r"raw_call\s*\([^)]*,\s*[^,)]*,\s*gas\s*=\s*\d+\s*\)",
            severity=Severity.LOW,
            description="Fixed gas amount may be insufficient for complex operations",
            category="smart_contract",
            cwe_id="CWE-400",
            recommendation="Use gas estimation or allow for gas parameter adjustment"
        )
    ]
    
    def __init__(self, config: Dict[str, Any] = None):
        if config is None:
            config = {}
        super().__init__(config)
        self.vyper_executable = None
    
    async def scan(self, target_path: str, **kwargs) -> Any:
        """Scan a Vyper file or directory."""
        from .base import ScanResult
        from datetime import datetime
        
        target = Path(target_path)
        findings = []
        
        if target.is_file():
            findings = self.analyze_file(target)
        elif target.is_dir():
            for vy_file in target.rglob("*.vy"):
                findings.extend(self.analyze_file(vy_file))
        
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
                ["vyper", "--version"],
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
                ["python", "-c", "import vyper; print(vyper.__version__)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
        
        return "unknown"
    
    def is_available(self) -> bool:
        """Check if Vyper compiler is available."""
        try:
            result = subprocess.run(
                ["vyper", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.vyper_executable = "vyper"
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
        # Check if vyper is available via Python
        try:
            result = subprocess.run(
                ["python", "-c", "import vyper; print(vyper.__version__)"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                self.vyper_executable = "python"
                return True
        except (subprocess.SubprocessError, FileNotFoundError):
            pass
            
        return False
    
    def get_file_patterns(self) -> List[str]:
        """Get file patterns for Vyper files."""
        return ["*.vy"]
    
    def analyze_file(self, file_path: Path) -> List[Finding]:
        """Analyze a single Vyper file."""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            self.logger.error(f"Error reading file {file_path}: {e}")
            return findings
        
        # Perform pattern-based analysis
        findings.extend(self._analyze_patterns(file_path, content))
        
        # Try to run Vyper compiler for syntax and basic checks
        findings.extend(self._run_vyper_compiler(file_path))
        
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
                
                # Skip false positives for certain patterns
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
                    tool_evidence=[ToolEvidence(tool=self.name, id=f"vyper_{pattern.name}", raw=match.group())]
                )
                findings.append(finding)
        
        return findings
    
    def _is_false_positive(self, pattern: VyperPattern, matched_text: str, line_content: str) -> bool:
        """Check if a pattern match is a false positive."""
        
        # Skip commented lines
        if line_content.strip().startswith('#'):
            return True
        
        # Skip string literals
        if matched_text in re.findall(r'["\'].*?["\']', line_content):
            return True
        
        # Pattern-specific false positive checks
        if pattern.name == "missing_access_control":
            # Skip view functions and internal functions
            if re.search(r'@view|@internal|@pure', line_content):
                return True
            # Skip constructor
            if 'def __init__' in matched_text:
                return True
        
        if pattern.name == "integer_overflow":
            # Skip if using safe math or explicit checks
            if re.search(r'assert|require|SafeMath', line_content):
                return True
        
        if pattern.name == "unchecked_external_call":
            # Skip known safe calls
            if re.search(r'\.(balance|code|codehash)', matched_text):
                return True
        
        return False
    
    def _build_description(self, pattern: VyperPattern, matched_text: str) -> str:
        """Build detailed description for a finding."""
        base_desc = pattern.description
        
        if pattern.name == "reentrancy_vulnerability":
            return f"{base_desc}. Found external call: '{matched_text}'. Ensure state changes occur before external calls."
        elif pattern.name == "weak_randomness":
            return f"{base_desc}. Found: '{matched_text}'. Block properties are predictable and manipulable by miners."
        elif pattern.name == "tx_origin_usage":
            return f"{base_desc}. tx.origin can be manipulated through phishing attacks."
        elif pattern.name == "denial_of_service_gas":
            return f"{base_desc}. Loop over dynamic array can consume excessive gas."
        
        return f"{base_desc}. Found: '{matched_text}'"
    
    def _run_vyper_compiler(self, file_path: Path) -> List[Finding]:
        """Run Vyper compiler to check for compilation errors and warnings."""
        findings = []
        
        if not self.vyper_executable:
            return findings
        
        try:
            if self.vyper_executable == "vyper":
                # Use vyper CLI
                result = subprocess.run(
                    ["vyper", str(file_path), "--format", "combined_json"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            else:
                # Use vyper via Python
                result = subprocess.run(
                    ["python", "-c", f"""
import vyper
from vyper import compiler
import json
try:
    with open('{file_path}', 'r') as f:
        source = f.read()
    result = compiler.compile_code(source, output_formats=['combined_json'])
    print(json.dumps(result))
except Exception as e:
    print(json.dumps({{"error": str(e)}}))
"""],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
            
            if result.returncode != 0:
                # Parse compilation errors
                error_output = result.stderr
                findings.extend(self._parse_compiler_errors(file_path, error_output))
            
        except subprocess.TimeoutExpired:
            self.logger.warning(f"Vyper compiler timeout for {file_path}")
        except Exception as e:
            self.logger.error(f"Error running Vyper compiler on {file_path}: {e}")
        
        return findings
    
    def _parse_compiler_errors(self, file_path: Path, error_output: str) -> List[Finding]:
        """Parse Vyper compiler error output."""
        findings = []
        
        # Parse different error formats
        patterns = [
            # Standard compiler error format
            r'line (\d+):(\d+):\s*(.*)',
            # Alternative format
            r'Error in line (\d+):\s*(.*)',
            # JSON error format
            r'"line":\s*(\d+).*?"message":\s*"([^"]+)"'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, error_output, re.MULTILINE)
            for match in matches:
                if len(match.groups()) >= 2:
                    line_num = int(match.group(1))
                    message = match.group(-1)  # Last group is the message
                    
                    # Determine severity based on error type
                    severity = Severity.HIGH
                    if any(keyword in message.lower() for keyword in ['warning', 'deprecated']):
                        severity = Severity.MEDIUM
                    
                    # Create CVSS score
                    from ..report.cvss import CVSSCalculator
                    cvss = CVSSCalculator.vulnerability_to_cvss("compilation", {})
                    
                    finding = Finding(
                        file=str(file_path),
                        title="Vyper Compiler Issue",
                        description=f"Compiler error: {message}",
                        lines=str(line_num),
                        impact="Compilation error prevents contract deployment and may indicate security issues.",
                        severity=severity.value.capitalize() if hasattr(severity, 'value') else str(severity).capitalize(),
                        cvss_v4=cvss,
                        snippet="",
                        recommendation="Fix compilation errors before deployment",
                        sample_fix=f"# Fix the compilation error at line {line_num}",
                        poc=f"# Compiler error: {message}",
                        owasp=[],
                        cwe=[],
                        tool_evidence=[ToolEvidence(tool=self.name, id="vyper_compiler_error", raw=message)]
                    )
                    findings.append(finding)
        
        return findings
    
    def supports_file(self, file_path: Path) -> bool:
        """Check if the tool supports analyzing the given file."""
        return file_path.suffix.lower() == '.vy'
    
    def get_config_schema(self) -> Dict[str, Any]:
        """Get configuration schema for the tool."""
        return {
            "type": "object",
            "properties": {
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
                    "description": "Enable Vyper compiler validation"
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
        """Get installation instructions for Vyper."""
        return """
To install Vyper for security analysis:

Option 1: Install via pip
pip install vyper

Option 2: Install via conda
conda install -c conda-forge vyper

Option 3: Build from source
git clone https://github.com/vyperlang/vyper.git
cd vyper
pip install .

Verify installation:
vyper --version

For development:
pip install vyper[dev]

Documentation: https://docs.vyperlang.org/
        """.strip()