"""
Slither Tool Implementation
Smart contract security analysis using Slither
"""

import asyncio
import json
import logging
import subprocess
from pathlib import Path
from typing import Dict, List, Any, Optional

from .base import SecurityScannerBase
from ..schemas.findings import Finding, ToolEvidence

logger = logging.getLogger(__name__)

class SlitherScanner(SecurityScannerBase):
    """
    Slither static analysis tool for Solidity smart contracts
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tool_name = "slither"
        self.description = "Static analysis framework for Solidity smart contracts"
        self.supported_languages = ["solidity"]
        
        # Slither configuration
        self.slither_config = config.get('slither', {})
        self.excluded_detectors = self.slither_config.get('exclude', [])
        self.included_detectors = self.slither_config.get('include', [])
        self.severity_filter = self.slither_config.get('severity_filter', ['high', 'medium', 'low'])
        
    def is_available(self) -> bool:
        """Check if Slither is available"""
        try:
            result = subprocess.run(
                ["slither", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            return result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return False
    
    async def scan(self, target_path: str, config: Dict[str, Any]) -> List[Finding]:
        """
        Run Slither analysis on Solidity contracts
        """
        logger.info(f"Running Slither analysis on {target_path}")
        
        if not self.is_available():
            logger.error("Slither is not available")
            return []
        
        # Find Solidity files
        solidity_files = self._find_solidity_files(target_path)
        if not solidity_files:
            logger.info("No Solidity files found")
            return []
        
        findings = []
        
        # Run Slither on each contract
        for sol_file in solidity_files:
            try:
                file_findings = await self._analyze_contract(sol_file, config)
                findings.extend(file_findings)
            except Exception as e:
                logger.error(f"Error analyzing {sol_file}: {e}")
        
        logger.info(f"Slither analysis complete. Found {len(findings)} issues")
        return findings
    
    def _find_solidity_files(self, target_path: str) -> List[str]:
        """Find all Solidity files in the target path"""
        path = Path(target_path)
        solidity_files = []
        
        if path.is_file() and path.suffix == '.sol':
            solidity_files.append(str(path))
        elif path.is_dir():
            solidity_files.extend([
                str(f) for f in path.rglob("*.sol")
                if not any(exclude in str(f) for exclude in ['node_modules', '.git', 'test'])
            ])
        
        return solidity_files
    
    async def _analyze_contract(self, contract_path: str, config: Dict[str, Any]) -> List[Finding]:
        """Analyze a single Solidity contract"""
        
        # Build Slither command
        cmd = self._build_slither_command(contract_path, config)
        
        try:
            # Run Slither
            process = await asyncio.create_subprocess_exec(
                *cmd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            if process.returncode != 0 and stderr:
                logger.warning(f"Slither warning/error: {stderr.decode()}")
            
            # Parse results
            if stdout:
                return self._parse_slither_output(stdout.decode(), contract_path)
            else:
                return []
                
        except Exception as e:
            logger.error(f"Error running Slither on {contract_path}: {e}")
            return []
    
    def _build_slither_command(self, contract_path: str, config: Dict[str, Any]) -> List[str]:
        """Build Slither command with appropriate options"""
        
        cmd = ["slither", contract_path, "--json", "-"]
        
        # Add detector filters
        if self.excluded_detectors:
            cmd.extend(["--exclude", ",".join(self.excluded_detectors)])
        
        if self.included_detectors:
            cmd.extend(["--include", ",".join(self.included_detectors)])
        
        # Add configuration options
        if config.get('disable_optimizations'):
            cmd.append("--disable-optimizations")
        
        if config.get('ignore_return'):
            cmd.append("--ignore-return-value")
        
        # Add custom Slither config file if specified
        slither_config_file = config.get('config_file')
        if slither_config_file and Path(slither_config_file).exists():
            cmd.extend(["--config-file", slither_config_file])
        
        return cmd
    
    def _parse_slither_output(self, output: str, contract_path: str) -> List[Finding]:
        """Parse Slither JSON output into Finding objects"""
        
        findings = []
        
        try:
            # Slither outputs JSON with detectors and their results
            data = json.loads(output)
            
            # Handle different Slither output formats
            results = data.get('results', {})
            detectors = results.get('detectors', [])
            
            for detector in detectors:
                finding = self._create_finding_from_detector(detector, contract_path)
                if finding and self._should_include_finding(finding):
                    findings.append(finding)
        
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Slither JSON output: {e}")
            # Fallback to text parsing
            findings = self._parse_slither_text_output(output, contract_path)
        
        return findings
    
    def _create_finding_from_detector(self, detector: Dict[str, Any], contract_path: str) -> Optional[Finding]:
        """Create Finding object from Slither detector result"""
        
        try:
            # Extract detector information
            check = detector.get('check', 'unknown')
            impact = detector.get('impact', 'Unknown')
            confidence = detector.get('confidence', 'Unknown')
            description = detector.get('description', '')
            
            # Map Slither impact to severity
            severity = self._map_impact_to_severity(impact)
            
            # Extract location information
            elements = detector.get('elements', [])
            file_path = contract_path
            line_number = 0
            
            if elements:
                # Get first element location
                first_element = elements[0]
                source_mapping = first_element.get('source_mapping', {})
                if source_mapping:
                    line_number = source_mapping.get('lines', [0])[0]
                    file_path = source_mapping.get('filename_absolute', contract_path)
            
            # Create tool evidence
            tool_evidence = ToolEvidence(
                tool=self.tool_name,
                id=check,
                raw=json.dumps(detector, indent=2)
            )
            
            # Create finding
            finding = Finding(
                id=f"SLITHER_{check}_{hash(str(detector)) % 10000}",
                file=file_path,
                title=f"Slither: {check.replace('-', ' ').title()}",
                description=description or f"Slither detected {check} vulnerability",
                lines=str(line_number) if line_number else "0",
                impact=self._generate_impact_description(check, description),
                severity=severity.title(),  # Convert to Title case
                cvss_v4={
                    "score": self._calculate_cvss_score(severity),
                    "vector": "CVSS:4.0/AV:N/AC:L/PR:N/UI:N/S:U/C:L/I:L/A:N"
                },
                owasp=["A06:2021"],  # Default OWASP category
                cwe=self._get_cwe_for_check(check),
                snippet=self._extract_code_snippet(file_path, line_number),
                recommendation=self._generate_recommendation(check),
                sample_fix=self._generate_sample_fix(check),
                poc=self._generate_poc(check),
                references=[f"https://github.com/crytic/slither/wiki/Detector-Documentation#{check}"],
                tool_evidence=[tool_evidence]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error creating finding from detector: {e}")
            return None
    
    def _parse_slither_text_output(self, output: str, contract_path: str) -> List[Finding]:
        """Fallback parser for text output"""
        findings = []
        
        lines = output.split('\n')
        current_finding = None
        
        for line in lines:
            line = line.strip()
            
            # Look for Slither detector output patterns
            if 'Impact:' in line and 'Confidence:' in line:
                # Parse impact and confidence
                parts = line.split()
                impact = None
                confidence = None
                
                for i, part in enumerate(parts):
                    if part == 'Impact:' and i + 1 < len(parts):
                        impact = parts[i + 1]
                    elif part == 'Confidence:' and i + 1 < len(parts):
                        confidence = parts[i + 1]
                
                if current_finding and impact and confidence:
                    current_finding['impact'] = impact
                    current_finding['confidence'] = confidence
                    
                    # Create finding
                    finding = self._create_text_finding(current_finding, contract_path)
                    if finding:
                        findings.append(finding)
                
                current_finding = {}
            
            elif line and not line.startswith('INFO:') and current_finding is not None:
                # Accumulate description
                if 'description' not in current_finding:
                    current_finding['description'] = line
                else:
                    current_finding['description'] += ' ' + line
        
        return findings
    
    def _create_text_finding(self, finding_data: Dict[str, Any], contract_path: str) -> Optional[Finding]:
        """Create finding from text parsing"""
        
        try:
            description = finding_data.get('description', 'Unknown issue')
            impact = finding_data.get('impact', 'Unknown')
            confidence = finding_data.get('confidence', 'Unknown')
            
            severity = self._map_impact_to_severity(impact)
            
            tool_evidence = ToolEvidence(
                tool=self.tool_name,
                id="text_parsing",
                raw=str(finding_data)
            )
            
            finding = Finding(
                id=f"SLITHER_TEXT_{hash(description) % 10000}",
                title="Slither: Smart Contract Issue",
                description=description,
                severity=severity,
                category="smart_contract",
                file=contract_path,
                line_number=0,
                confidence_score=self._map_confidence_to_score(confidence),
                tool_evidence=[tool_evidence]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error creating text finding: {e}")
            return None
    
    def _map_impact_to_severity(self, impact: str) -> str:
        """Map Slither impact to standard severity"""
        impact_lower = impact.lower()
        
        if impact_lower in ['high', 'critical']:
            return 'Critical'
        elif impact_lower == 'medium':
            return 'High'
        elif impact_lower == 'low':
            return 'Medium'
        elif impact_lower in ['informational', 'info']:
            return 'Low'
        else:
            return 'Medium'  # Default
    
    def _generate_impact_description(self, check: str, description: str) -> str:
        """Generate impact description for the vulnerability"""
        impact_map = {
            'reentrancy': 'Attacker could drain contract funds through reentrancy attacks',
            'weak-prng': 'Predictable random numbers could be exploited by attackers',
            'controlled-delegatecall': 'Attacker could execute arbitrary code in contract context',
            'erc20-interface': 'Token may not work correctly with DeFi protocols',
            'unchecked-send': 'Failed transfers could lead to unexpected behavior',
            'timestamp': 'Contract behavior could be manipulated by miners',
            'assembly': 'Low-level code may introduce vulnerabilities',
            'solc-version': 'Compiler bugs could introduce security issues',
            'low-level-calls': 'Call failures are not handled properly',
            'naming-convention': 'Code may be harder to audit and maintain'
        }
        
        for pattern, impact in impact_map.items():
            if pattern in check:
                return impact
        
        return f"This {check} vulnerability could compromise contract security"
    
    def _calculate_cvss_score(self, severity: str) -> float:
        """Calculate CVSS score based on severity"""
        score_map = {
            'Critical': 9.0,
            'High': 7.5,
            'Medium': 5.0,
            'Low': 2.5
        }
        return score_map.get(severity, 5.0)
    
    def _get_cwe_for_check(self, check: str) -> list:
        """Get CWE identifiers for Slither check"""
        cwe_map = {
            'reentrancy': ['CWE-362', 'CWE-841'],
            'weak-prng': ['CWE-338'],
            'controlled-delegatecall': ['CWE-20'],
            'erc20-interface': ['CWE-697'],
            'unchecked-send': ['CWE-252'],
            'timestamp': ['CWE-829'],
            'assembly': ['CWE-119'],
            'solc-version': ['CWE-1104'],
            'low-level-calls': ['CWE-252'],
            'naming-convention': ['CWE-1099']
        }
        
        for pattern, cwe in cwe_map.items():
            if pattern in check:
                return cwe
        
        return ['CWE-1006']  # Default
    
    def _extract_code_snippet(self, file_path: str, line_number: int) -> str:
        """Extract code snippet from file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
                
            if 0 < line_number <= len(lines):
                # Get 3 lines of context
                start = max(0, line_number - 2)
                end = min(len(lines), line_number + 2)
                snippet_lines = lines[start:end]
                
                return ''.join(snippet_lines).strip()
            
        except Exception:
            pass
        
        return f"// Code at {file_path}:{line_number}"
    
    def _generate_recommendation(self, check: str) -> str:
        """Generate fix recommendation"""
        rec_map = {
            'reentrancy': 'Use checks-effects-interactions pattern and reentrancy guards',
            'weak-prng': 'Use secure randomness sources like Chainlink VRF',
            'controlled-delegatecall': 'Validate delegatecall targets and use whitelist',
            'erc20-interface': 'Implement standard ERC20 interface correctly',
            'unchecked-send': 'Check return values of send/transfer operations',
            'timestamp': 'Avoid using block.timestamp for critical logic',
            'assembly': 'Minimize assembly usage and audit carefully',
            'solc-version': 'Use latest stable Solidity compiler version',
            'low-level-calls': 'Handle call failures and check return values',
            'naming-convention': 'Follow Solidity style guide naming conventions'
        }
        
        for pattern, rec in rec_map.items():
            if pattern in check:
                return rec
        
        return f"Review and fix the {check} issue according to Solidity best practices"
    
    def _generate_sample_fix(self, check: str) -> str:
        """Generate sample fix code"""
        fix_map = {
            'reentrancy': '''// Before: Vulnerable to reentrancy
function withdraw() external {
    uint amount = balances[msg.sender];
    msg.sender.call{value: amount}("");
    balances[msg.sender] = 0;
}

// After: Reentrancy-safe
function withdraw() external nonReentrant {
    uint amount = balances[msg.sender];
    balances[msg.sender] = 0;
    (bool success,) = msg.sender.call{value: amount}("");
    require(success, "Transfer failed");
}''',
            'weak-prng': '''// Before: Weak randomness
uint random = uint(keccak256(abi.encodePacked(block.timestamp, block.difficulty)));

// After: Use Chainlink VRF
import "@chainlink/contracts/src/v0.8/VRFConsumerBase.sol";

contract RandomContract is VRFConsumerBase {
    function getRandomNumber() external returns (bytes32 requestId) {
        return requestRandomness(keyHash, fee);
    }
}''',
            'unchecked-send': '''// Before: Unchecked send
address.send(amount);

// After: Check return value
(bool success,) = address.call{value: amount}("");
require(success, "Transfer failed");'''
        }
        
        for pattern, fix in fix_map.items():
            if pattern in check:
                return fix
        
        return f"// Review and fix {check} according to best practices"
    
    def _generate_poc(self, check: str) -> str:
        """Generate proof of concept"""
        poc_map = {
            'reentrancy': '''// Reentrancy attack example
contract Attack {
    VulnerableContract target;
    
    function attack() external payable {
        target.deposit{value: msg.value}();
        target.withdraw();
    }
    
    receive() external payable {
        if (address(target).balance > 0) {
            target.withdraw();
        }
    }
}''',
            'weak-prng': '''// Predictable randomness attack
contract PredictableAttack {
    function predictOutcome() external view returns (uint) {
        return uint(keccak256(abi.encodePacked(block.timestamp, block.difficulty)));
    }
}'''
        }
        
        for pattern, poc in poc_map.items():
            if pattern in check:
                return poc
        
        return f"# {check} vulnerability demonstration would go here"
    
    def _map_confidence_to_score(self, confidence: str) -> int:
        """Map Slither confidence to numeric score"""
        confidence_lower = confidence.lower()
        
        if confidence_lower == 'high':
            return 90
        elif confidence_lower == 'medium':
            return 70
        elif confidence_lower == 'low':
            return 50
        else:
            return 60  # Default
    
    def _should_include_finding(self, finding: Finding) -> bool:
        """Check if finding should be included based on filters"""
        return finding.severity in self.severity_filter
    
    def get_supported_file_types(self) -> List[str]:
        """Get list of supported file types"""
        return ['.sol']
    
    def get_detector_info(self) -> Dict[str, Any]:
        """Get information about available Slither detectors"""
        return {
            'available_detectors': [
                'reentrancy-eth',
                'reentrancy-no-eth', 
                'uninitialized-state',
                'uninitialized-storage',
                'uninitialized-local',
                'arbitrary-send',
                'controlled-delegatecall',
                'controlled-array-length',
                'delegatecall-loop',
                'msg-value-loop',
                'tx-origin',
                'assembly',
                'assert-state-change',
                'boolean-equal',
                'boolean-cst',
                'divide-before-multiply',
                'locked-ether',
                'multiple-constructors',
                'name-reused',
                'public-mappings-nested',
                'rtlo',
                'shadowing-abstract',
                'shadowing-builtin',
                'shadowing-local',
                'shadowing-state',
                'solc-version',
                'unchecked-lowlevel',
                'unchecked-send',
                'unprotected-upgrade',
                'unused-return',
                'unused-state',
                'costly-loop',
                'dead-code',
                'reentrancy-benign',
                'reentrancy-events',
                'timestamp',
                'assembly',
                'deprecated-standards',
                'erc20-interface',
                'erc721-interface',
                'incorrect-equality',
                'locked-ether',
                'mapping-deletion',
                'shadowing-abstract',
                'tautology',
                'write-after-write'
            ],
            'impact_levels': ['High', 'Medium', 'Low', 'Informational'],
            'confidence_levels': ['High', 'Medium', 'Low']
        }
    
    def get_version(self) -> str:
        """Get Slither version"""
        try:
            result = subprocess.run(
                ["slither", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                return result.stdout.strip()
            return "unknown"
        except (subprocess.TimeoutExpired, FileNotFoundError):
            return "not-available"
    
    def normalize_findings(self, raw_output: str, metadata: Dict[str, Any]) -> List[Finding]:
        """
        Convert Slither JSON output to normalized Finding objects
        
        Args:
            raw_output: JSON output from Slither
            metadata: Additional metadata
            
        Returns:
            List of normalized Finding objects
        """
        findings = []
        
        try:
            if not raw_output.strip():
                return findings
                
            data = json.loads(raw_output)
            
            # Handle both direct results and nested results
            results = data.get('results', {})
            detectors = results.get('detectors', [])
            
            for detector in detectors:
                finding = Finding(
                    id=f"slither-{detector.get('check', 'unknown')}-{len(findings)}",
                    title=detector.get('check', 'Slither Detection'),
                    description=detector.get('description', 'No description available'),
                    severity=self._map_severity(detector.get('impact', 'Low')),
                    category='smart-contract',
                    file=self._extract_file_path(detector),
                    line=self._extract_line_number(detector),
                    column=0,
                    tool='slither',
                    evidence=ToolEvidence(
                        raw_output=json.dumps(detector),
                        confidence=detector.get('confidence', 'Medium').lower(),
                        tool_version=self.get_version()
                    ),
                    owasp=['A06:2021 - Vulnerable and Outdated Components'] if 'security' in detector.get('check', '') else [],
                    cwe=[],
                    references=[]
                )
                findings.append(finding)
                
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Slither output as JSON: {e}")
        except Exception as e:
            logger.error(f"Error normalizing Slither findings: {e}")
        
        return findings
    
    def _extract_file_path(self, detector: Dict[str, Any]) -> str:
        """Extract file path from detector result"""
        elements = detector.get('elements', [])
        if elements and isinstance(elements[0], dict):
            source_mapping = elements[0].get('source_mapping', {})
            filename = source_mapping.get('filename_absolute', '')
            if filename:
                return filename
        return "unknown"
    
    def _extract_line_number(self, detector: Dict[str, Any]) -> int:
        """Extract line number from detector result"""
        elements = detector.get('elements', [])
        if elements and isinstance(elements[0], dict):
            source_mapping = elements[0].get('source_mapping', {})
            lines = source_mapping.get('lines', [])
            if lines:
                return lines[0]
        return 0
    
    def _map_severity(self, impact: str) -> str:
        """Map Slither impact to standard severity"""
        mapping = {
            'High': 'critical',
            'Medium': 'high', 
            'Low': 'medium',
            'Informational': 'low'
        }
        return mapping.get(impact, 'medium')