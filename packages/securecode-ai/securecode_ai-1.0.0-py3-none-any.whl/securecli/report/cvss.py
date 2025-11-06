"""
CVSS v4.0 scoring utilities for SecureCLI
Provides CVSS calculation, validation, and scoring utilities
"""

from typing import Dict, Any, Optional, Tuple
from enum import Enum
from dataclasses import dataclass

from ..schemas.findings import CVSSv4


class CVSSMetrics(Enum):
    """CVSS v4.0 metric enumerations"""
    
    # Attack Vector (AV)
    AV_NETWORK = "N"
    AV_ADJACENT = "A"
    AV_LOCAL = "L"
    AV_PHYSICAL = "P"
    
    # Attack Complexity (AC)
    AC_LOW = "L"
    AC_HIGH = "H"
    
    # Attack Requirements (AT)
    AT_NONE = "N"
    AT_PRESENT = "P"
    
    # Privileges Required (PR)
    PR_NONE = "N"
    PR_LOW = "L"
    PR_HIGH = "H"
    
    # User Interaction (UI)
    UI_NONE = "N"
    UI_PASSIVE = "P"
    UI_ACTIVE = "A"
    
    # Vulnerable System Impact (VS)
    VS_HIGH = "H"
    VS_LOW = "L"
    VS_NONE = "N"
    
    # Subsequent System Impact (SS)
    SS_HIGH = "H"
    SS_LOW = "L"
    SS_NONE = "N"


@dataclass
class CVSSCalculator:
    """CVSS v4.0 score calculator"""
    
    # CVSS v4.0 base score mapping
    CVSS_LOOKUP = {
        # Mapping from metric combination to base score
        # This is a simplified version - full CVSS v4.0 has 4+ million combinations
        # We'll use heuristics and common patterns
    }
    
    @staticmethod
    def calculate_base_score(
        attack_vector: str = "N",
        attack_complexity: str = "L", 
        attack_requirements: str = "N",
        privileges_required: str = "N",
        user_interaction: str = "N",
        vulnerable_system_confidentiality: str = "H",
        vulnerable_system_integrity: str = "H",
        vulnerable_system_availability: str = "H",
        subsequent_system_confidentiality: str = "N",
        subsequent_system_integrity: str = "N",
        subsequent_system_availability: str = "N"
    ) -> float:
        """
        Calculate CVSS v4.0 base score using heuristic approach
        
        Args:
            attack_vector: Network, Adjacent, Local, Physical
            attack_complexity: Low, High
            attack_requirements: None, Present
            privileges_required: None, Low, High
            user_interaction: None, Passive, Active
            vulnerable_system_*: High, Low, None
            subsequent_system_*: High, Low, None
        
        Returns:
            CVSS base score (0.0-10.0)
        """
        
        # Base impact calculation
        vs_impact = CVSSCalculator._calculate_impact(
            vulnerable_system_confidentiality,
            vulnerable_system_integrity,
            vulnerable_system_availability
        )
        
        ss_impact = CVSSCalculator._calculate_impact(
            subsequent_system_confidentiality,
            subsequent_system_integrity,
            subsequent_system_availability
        )
        
        # Combined impact
        max_impact = max(vs_impact, ss_impact)
        
        # Exploitability calculation
        exploitability = CVSSCalculator._calculate_exploitability(
            attack_vector,
            attack_complexity,
            attack_requirements,
            privileges_required,
            user_interaction
        )
        
        # Base score calculation (simplified CVSS v4.0 formula)
        if max_impact <= 0:
            return 0.0
        
        base_score = min(10.0, ((max_impact + exploitability) * 0.6))
        
        # Round to 1 decimal place
        return round(base_score, 1)
    
    @staticmethod
    def _calculate_impact(conf: str, integ: str, avail: str) -> float:
        """Calculate impact score for CIA triad"""
        impact_values = {"H": 0.56, "L": 0.22, "N": 0.0}
        
        conf_val = impact_values.get(conf, 0.0)
        integ_val = impact_values.get(integ, 0.0)
        avail_val = impact_values.get(avail, 0.0)
        
        # Calculate impact using CVSS formula
        impact = 1 - ((1 - conf_val) * (1 - integ_val) * (1 - avail_val))
        return impact * 6.42  # CVSS v4.0 scaling factor
    
    @staticmethod
    def _calculate_exploitability(
        av: str, ac: str, at: str, pr: str, ui: str
    ) -> float:
        """Calculate exploitability score"""
        
        # Attack Vector scoring
        av_scores = {"N": 0.85, "A": 0.62, "L": 0.55, "P": 0.2}
        av_score = av_scores.get(av, 0.85)
        
        # Attack Complexity scoring
        ac_scores = {"L": 0.77, "H": 0.44}
        ac_score = ac_scores.get(ac, 0.77)
        
        # Attack Requirements scoring
        at_scores = {"N": 0.85, "P": 0.7}
        at_score = at_scores.get(at, 0.85)
        
        # Privileges Required scoring (simplified)
        pr_scores = {"N": 0.85, "L": 0.62, "H": 0.27}
        pr_score = pr_scores.get(pr, 0.85)
        
        # User Interaction scoring
        ui_scores = {"N": 0.85, "P": 0.62, "A": 0.45}
        ui_score = ui_scores.get(ui, 0.85)
        
        # Calculate exploitability
        exploitability = av_score * ac_score * at_score * pr_score * ui_score
        return exploitability * 8.22  # CVSS v4.0 scaling factor
    
    @staticmethod
    def vulnerability_to_cvss(
        vulnerability_type: str,
        context: Dict[str, Any] = None
    ) -> CVSSv4:
        """
        Convert vulnerability type and context to CVSS v4.0 score
        
        Args:
            vulnerability_type: Type of vulnerability (SQL injection, XSS, etc.)
            context: Additional context (location, exposure, etc.)
        
        Returns:
            CVSSv4 object with calculated score and vector
        """
        
        context = context or {}
        
        # Vulnerability type mappings
        vuln_mappings = {
            # High severity vulnerabilities
            "sql_injection": {
                "av": "N", "ac": "L", "at": "N", "pr": "N", "ui": "N",
                "vsc": "H", "vsi": "H", "vsa": "H",
                "ssc": "L", "ssi": "L", "ssa": "N"
            },
            "command_injection": {
                "av": "N", "ac": "L", "at": "N", "pr": "L", "ui": "N",
                "vsc": "H", "vsi": "H", "vsa": "H",
                "ssc": "H", "ssi": "H", "ssa": "H"
            },
            "xss": {
                "av": "N", "ac": "L", "at": "N", "pr": "N", "ui": "P",
                "vsc": "L", "vsi": "L", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "csrf": {
                "av": "N", "ac": "L", "at": "N", "pr": "N", "ui": "P",
                "vsc": "L", "vsi": "L", "vsa": "L",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "path_traversal": {
                "av": "N", "ac": "L", "at": "N", "pr": "L", "ui": "N",
                "vsc": "H", "vsi": "L", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "insecure_direct_object_reference": {
                "av": "N", "ac": "L", "at": "N", "pr": "L", "ui": "N",
                "vsc": "H", "vsi": "L", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "hardcoded_secret": {
                "av": "L", "ac": "L", "at": "N", "pr": "N", "ui": "N",
                "vsc": "H", "vsi": "H", "vsa": "H",
                "ssc": "H", "ssi": "H", "ssa": "H"
            },
            "weak_cryptography": {
                "av": "N", "ac": "H", "at": "P", "pr": "N", "ui": "N",
                "vsc": "H", "vsi": "H", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "insecure_deserialization": {
                "av": "N", "ac": "L", "at": "N", "pr": "N", "ui": "N",
                "vsc": "H", "vsi": "H", "vsa": "H",
                "ssc": "H", "ssi": "H", "ssa": "H"
            },
            "buffer_overflow": {
                "av": "N", "ac": "H", "at": "N", "pr": "N", "ui": "N",
                "vsc": "H", "vsi": "H", "vsa": "H",
                "ssc": "L", "ssi": "L", "ssa": "L"
            },
            # Medium severity vulnerabilities
            "information_disclosure": {
                "av": "N", "ac": "L", "at": "N", "pr": "L", "ui": "N",
                "vsc": "L", "vsi": "N", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "missing_authentication": {
                "av": "N", "ac": "L", "at": "N", "pr": "N", "ui": "N",
                "vsc": "L", "vsi": "L", "vsa": "L",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "weak_password_policy": {
                "av": "N", "ac": "H", "at": "P", "pr": "N", "ui": "A",
                "vsc": "L", "vsi": "L", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            # Low severity vulnerabilities
            "missing_security_headers": {
                "av": "N", "ac": "L", "at": "P", "pr": "N", "ui": "P",
                "vsc": "L", "vsi": "N", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "insecure_cookie": {
                "av": "A", "ac": "H", "at": "P", "pr": "N", "ui": "P",
                "vsc": "L", "vsi": "N", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            },
            "verbose_error": {
                "av": "N", "ac": "L", "at": "N", "pr": "N", "ui": "N",
                "vsc": "L", "vsi": "N", "vsa": "N",
                "ssc": "N", "ssi": "N", "ssa": "N"
            }
        }
        
        # Get base mapping
        mapping = vuln_mappings.get(vulnerability_type.lower(), {
            "av": "N", "ac": "L", "at": "N", "pr": "L", "ui": "N",
            "vsc": "L", "vsi": "L", "vsa": "L",
            "ssc": "N", "ssi": "N", "ssa": "N"
        })
        
        # Apply context modifications
        if context.get("public_facing", False):
            mapping["av"] = "N"  # Network accessible
        elif context.get("internal_only", False):
            mapping["av"] = "L"  # Local access only
        
        if context.get("authenticated_required", False):
            mapping["pr"] = "L"  # Low privileges required
        
        if context.get("user_interaction", False):
            mapping["ui"] = "P"  # Passive interaction
        
        # Calculate score
        score = CVSSCalculator.calculate_base_score(
            attack_vector=mapping["av"],
            attack_complexity=mapping["ac"],
            attack_requirements=mapping["at"],
            privileges_required=mapping["pr"],
            user_interaction=mapping["ui"],
            vulnerable_system_confidentiality=mapping["vsc"],
            vulnerable_system_integrity=mapping["vsi"],
            vulnerable_system_availability=mapping["vsa"],
            subsequent_system_confidentiality=mapping["ssc"],
            subsequent_system_integrity=mapping["ssi"],
            subsequent_system_availability=mapping["ssa"]
        )
        
        # Generate CVSS vector
        vector = f"CVSS:4.0/AV:{mapping['av']}/AC:{mapping['ac']}/AT:{mapping['at']}/PR:{mapping['pr']}/UI:{mapping['ui']}/VC:{mapping['vsc']}/VI:{mapping['vsi']}/VA:{mapping['vsa']}/SC:{mapping['ssc']}/SI:{mapping['ssi']}/SA:{mapping['ssa']}"
        
        return CVSSv4(
            score=score,
            vector=vector,
            severity=CVSSCalculator.score_to_severity(score)
        )
    
    @staticmethod
    def score_to_severity(score: float) -> str:
        """Convert CVSS score to severity level"""
        if score >= 9.0:
            return "Critical"
        elif score >= 7.0:
            return "High"
        elif score >= 4.0:
            return "Medium"
        elif score > 0.0:
            return "Low"
        else:
            return "None"
    
    @staticmethod
    def validate_vector(vector: str) -> Tuple[bool, Optional[str]]:
        """
        Validate CVSS v4.0 vector string
        
        Args:
            vector: CVSS vector string
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        
        if not vector.startswith("CVSS:4.0/"):
            return False, "Vector must start with 'CVSS:4.0/'"
        
        # Extract metrics
        parts = vector.split("/")[1:]  # Skip CVSS:4.0
        
        required_metrics = {
            "AV", "AC", "AT", "PR", "UI", "VC", "VI", "VA", "SC", "SI", "SA"
        }
        
        found_metrics = set()
        
        for part in parts:
            if ":" not in part:
                return False, f"Invalid metric format: {part}"
            
            metric, value = part.split(":", 1)
            
            if metric in found_metrics:
                return False, f"Duplicate metric: {metric}"
            
            found_metrics.add(metric)
            
            # Validate metric values
            valid_values = CVSSCalculator._get_valid_values(metric)
            if value not in valid_values:
                return False, f"Invalid value for {metric}: {value}. Valid values: {valid_values}"
        
        # Check required metrics
        missing = required_metrics - found_metrics
        if missing:
            return False, f"Missing required metrics: {missing}"
        
        return True, None
    
    @staticmethod
    def _get_valid_values(metric: str) -> list:
        """Get valid values for a CVSS metric"""
        values_map = {
            "AV": ["N", "A", "L", "P"],
            "AC": ["L", "H"],
            "AT": ["N", "P"],
            "PR": ["N", "L", "H"],
            "UI": ["N", "P", "A"],
            "VC": ["H", "L", "N"],
            "VI": ["H", "L", "N"],
            "VA": ["H", "L", "N"],
            "SC": ["H", "L", "N"],
            "SI": ["H", "L", "N"],
            "SA": ["H", "L", "N"]
        }
        return values_map.get(metric, [])


class VulnerabilityClassifier:
    """Classifies vulnerabilities and maps to CVSS scores"""
    
    # Common vulnerability patterns and their types
    PATTERN_MAPPINGS = {
        # SQL Injection patterns
        r"(?i)(sql.*injection|sqli|union.*select|order.*by|drop.*table)": "sql_injection",
        r"(?i)(prepare.*statement|parameterized.*query).*(?:not|missing|absent)": "sql_injection",
        
        # Command Injection patterns
        r"(?i)(command.*injection|shell.*injection|exec|system|eval)": "command_injection",
        r"(?i)(os\.system|subprocess|shell_exec|passthru)": "command_injection",
        
        # XSS patterns
        r"(?i)(cross.*site.*scripting|xss|script.*injection)": "xss",
        r"(?i)(innerHTML|document\.write).*user.*input": "xss",
        
        # Path Traversal patterns
        r"(?i)(path.*traversal|directory.*traversal|\.\./)": "path_traversal",
        r"(?i)(file.*inclusion|local.*file.*inclusion|lfi)": "path_traversal",
        
        # Cryptography patterns
        r"(?i)(weak.*crypto|md5|sha1|des|rc4)": "weak_cryptography",
        r"(?i)(hardcoded.*key|hardcoded.*password|embedded.*secret)": "hardcoded_secret",
        
        # Authentication patterns
        r"(?i)(missing.*auth|no.*authentication|unauthenticated)": "missing_authentication",
        r"(?i)(weak.*password|default.*password|password.*policy)": "weak_password_policy",
        
        # Information Disclosure patterns
        r"(?i)(information.*disclosure|data.*leak|sensitive.*data)": "information_disclosure",
        r"(?i)(error.*message|stack.*trace|debug.*info)": "verbose_error",
        
        # Security Headers patterns
        r"(?i)(missing.*header|security.*header|csp|cors)": "missing_security_headers",
        r"(?i)(insecure.*cookie|secure.*flag|httponly)": "insecure_cookie"
    }
    
    @classmethod
    def classify_vulnerability(cls, title: str, description: str) -> str:
        """
        Classify vulnerability based on title and description
        
        Args:
            title: Vulnerability title
            description: Vulnerability description
        
        Returns:
            Vulnerability type string
        """
        
        import re
        
        text = f"{title} {description}".lower()
        
        for pattern, vuln_type in cls.PATTERN_MAPPINGS.items():
            if re.search(pattern, text):
                return vuln_type
        
        # Default classification
        return "information_disclosure"
    
    @classmethod
    def auto_score_finding(cls, title: str, description: str, context: Dict[str, Any] = None) -> CVSSv4:
        """
        Automatically score a finding using classification and CVSS calculation
        
        Args:
            title: Finding title
            description: Finding description
            context: Additional context information
        
        Returns:
            CVSSv4 score object
        """
        
        # Classify vulnerability
        vuln_type = cls.classify_vulnerability(title, description)
        
        # Generate CVSS score
        return CVSSCalculator.vulnerability_to_cvss(vuln_type, context)