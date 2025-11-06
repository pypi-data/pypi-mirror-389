"""
SecureCLI Security Schemas
Data models for security findings, vulnerabilities, and threat intelligence
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum
import uuid

class Severity(Enum):
    """Security finding severity levels"""
    INFO = 1
    LOW = 3
    MEDIUM = 5
    HIGH = 7
    CRITICAL = 9

class Confidence(Enum):
    """Confidence level in finding accuracy"""
    LOW = 1
    MEDIUM = 5
    HIGH = 9

class Category(Enum):
    """Security finding categories based on common vulnerability types"""
    INJECTION = "injection"
    XSS = "cross_site_scripting"
    BROKEN_AUTH = "broken_authentication"
    SENSITIVE_DATA = "sensitive_data_exposure"
    XML_EXTERNAL = "xml_external_entities"
    BROKEN_ACCESS = "broken_access_control"
    SECURITY_MISCONFIG = "security_misconfiguration"
    XSS_SCRIPTING = "cross_site_scripting"
    INSECURE_DESERIALIZATION = "insecure_deserialization"
    VULNERABLE_COMPONENTS = "vulnerable_components"
    INSUFFICIENT_LOGGING = "insufficient_logging"
    CRYPTO = "cryptographic_issues"
    BUFFER_OVERFLOW = "buffer_overflow"
    RACE_CONDITION = "race_condition"
    PRIVILEGE_ESCALATION = "privilege_escalation"
    DENIAL_OF_SERVICE = "denial_of_service"
    INFORMATION_DISCLOSURE = "information_disclosure"
    INPUT_VALIDATION = "input_validation"
    OUTPUT_ENCODING = "output_encoding"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    SESSION_MANAGEMENT = "session_management"
    CSRF = "cross_site_request_forgery"
    CLICKJACKING = "clickjacking"
    REDIRECT_FORWARD = "unvalidated_redirects"
    SECRETS = "hardcoded_secrets"
    INSECURE_COMMUNICATION = "insecure_communication"
    ACCESS_CONTROL = "access_control"
    BUSINESS_LOGIC = "business_logic"
    OTHER = "other"

class ExploitabilityLevel(Enum):
    """How easily a vulnerability can be exploited"""
    THEORETICAL = "theoretical"
    DIFFICULT = "difficult"
    MODERATE = "moderate"
    EASY = "easy"
    AUTOMATED = "automated"

class ImpactLevel(Enum):
    """Business/technical impact of vulnerability"""
    MINIMAL = "minimal"
    MINOR = "minor"
    MODERATE = "moderate"
    SIGNIFICANT = "significant"
    SEVERE = "severe"

@dataclass
class CodeLocation:
    """Location of code issue"""
    file_path: str
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    end_line: Optional[int] = None
    end_column: Optional[int] = None
    function_name: Optional[str] = None
    class_name: Optional[str] = None
    method_name: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'file_path': self.file_path,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'end_line': self.end_line,
            'end_column': self.end_column,
            'function_name': self.function_name,
            'class_name': self.class_name,
            'method_name': self.method_name
        }

@dataclass
class Finding:
    """Security finding from analysis tools"""
    # Core identification
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    tool: str = ""
    rule_id: str = ""
    rule_name: str = ""
    
    # Classification
    category: Category = Category.OTHER
    severity: Severity = Severity.LOW
    confidence: Confidence = Confidence.MEDIUM
    
    # Description
    title: str = ""
    message: str = ""
    description: str = ""
    
    # Location
    file_path: str = ""
    line_number: Optional[int] = None
    column_number: Optional[int] = None
    code_snippet: Optional[str] = None
    locations: List[CodeLocation] = field(default_factory=list)
    
    # Metadata
    cwe_id: Optional[str] = None
    cve_id: Optional[str] = None
    owasp_category: Optional[str] = None
    language: Optional[str] = None
    
    # Risk assessment
    exploitability: Optional[ExploitabilityLevel] = None
    impact: Optional[ImpactLevel] = None
    risk_score: Optional[float] = None
    
    # Remediation
    fix_guidance: Optional[str] = None
    references: List[str] = field(default_factory=list)
    tags: Set[str] = field(default_factory=set)
    
    # Tracking
    discovered_at: datetime = field(default_factory=datetime.now)
    last_seen: datetime = field(default_factory=datetime.now)
    status: str = "new"
    false_positive: bool = False
    
    # Additional context
    context: Dict[str, Any] = field(default_factory=dict)
    related_findings: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'id': self.id,
            'tool': self.tool,
            'rule_id': self.rule_id,
            'rule_name': self.rule_name,
            'category': self.category.value,
            'severity': self.severity.value,
            'confidence': self.confidence.value,
            'title': self.title,
            'message': self.message,
            'description': self.description,
            'file_path': self.file_path,
            'line_number': self.line_number,
            'column_number': self.column_number,
            'code_snippet': self.code_snippet,
            'locations': [loc.to_dict() for loc in self.locations],
            'cwe_id': self.cwe_id,
            'cve_id': self.cve_id,
            'owasp_category': self.owasp_category,
            'language': self.language,
            'exploitability': self.exploitability.value if self.exploitability else None,
            'impact': self.impact.value if self.impact else None,
            'risk_score': self.risk_score,
            'fix_guidance': self.fix_guidance,
            'references': self.references,
            'tags': list(self.tags),
            'discovered_at': self.discovered_at.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'status': self.status,
            'false_positive': self.false_positive,
            'context': self.context,
            'related_findings': self.related_findings
        }

@dataclass
class Vulnerability:
    """Known vulnerability information"""
    # Identification
    vuln_id: str
    cve_id: Optional[str] = None
    cwe_id: Optional[str] = None
    
    # Basic info
    title: str = ""
    description: str = ""
    severity: Severity = Severity.MEDIUM
    
    # CVSS scoring
    cvss_base_score: Optional[float] = None
    cvss_temporal_score: Optional[float] = None
    cvss_environmental_score: Optional[float] = None
    cvss_vector: Optional[str] = None
    
    # Affected components
    affected_products: List[str] = field(default_factory=list)
    affected_versions: List[str] = field(default_factory=list)
    
    # Timeline
    published_date: Optional[datetime] = None
    modified_date: Optional[datetime] = None
    disclosure_date: Optional[datetime] = None
    
    # Exploitation
    exploitability: ExploitabilityLevel = ExploitabilityLevel.THEORETICAL
    exploit_available: bool = False
    exploit_maturity: str = "unproven"
    
    # Mitigation
    patch_available: bool = False
    patch_info: Optional[str] = None
    workaround: Optional[str] = None
    remediation: Optional[str] = None
    
    # References
    references: List[str] = field(default_factory=list)
    advisories: List[str] = field(default_factory=list)
    
    # Metadata
    source: str = ""
    last_updated: datetime = field(default_factory=datetime.now)
    tags: Set[str] = field(default_factory=set)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'vuln_id': self.vuln_id,
            'cve_id': self.cve_id,
            'cwe_id': self.cwe_id,
            'title': self.title,
            'description': self.description,
            'severity': self.severity.value,
            'cvss_base_score': self.cvss_base_score,
            'cvss_temporal_score': self.cvss_temporal_score,
            'cvss_environmental_score': self.cvss_environmental_score,
            'cvss_vector': self.cvss_vector,
            'affected_products': self.affected_products,
            'affected_versions': self.affected_versions,
            'published_date': self.published_date.isoformat() if self.published_date else None,
            'modified_date': self.modified_date.isoformat() if self.modified_date else None,
            'disclosure_date': self.disclosure_date.isoformat() if self.disclosure_date else None,
            'exploitability': self.exploitability.value,
            'exploit_available': self.exploit_available,
            'exploit_maturity': self.exploit_maturity,
            'patch_available': self.patch_available,
            'patch_info': self.patch_info,
            'workaround': self.workaround,
            'remediation': self.remediation,
            'references': self.references,
            'advisories': self.advisories,
            'source': self.source,
            'last_updated': self.last_updated.isoformat(),
            'tags': list(self.tags)
        }

@dataclass
class ThreatActor:
    """Threat actor information"""
    actor_id: str
    name: str
    aliases: List[str] = field(default_factory=list)
    description: str = ""
    motivation: List[str] = field(default_factory=list)
    sophistication: str = "unknown"
    origin_country: Optional[str] = None
    targets: List[str] = field(default_factory=list)
    attack_patterns: List[str] = field(default_factory=list)
    tools_used: List[str] = field(default_factory=list)
    first_seen: Optional[datetime] = None
    last_seen: Optional[datetime] = None
    active: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'actor_id': self.actor_id,
            'name': self.name,
            'aliases': self.aliases,
            'description': self.description,
            'motivation': self.motivation,
            'sophistication': self.sophistication,
            'origin_country': self.origin_country,
            'targets': self.targets,
            'attack_patterns': self.attack_patterns,
            'tools_used': self.tools_used,
            'first_seen': self.first_seen.isoformat() if self.first_seen else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None,
            'active': self.active
        }

@dataclass
class AttackPattern:
    """MITRE ATT&CK pattern or similar"""
    pattern_id: str
    name: str
    description: str = ""
    tactics: List[str] = field(default_factory=list)
    techniques: List[str] = field(default_factory=list)
    platforms: List[str] = field(default_factory=list)
    data_sources: List[str] = field(default_factory=list)
    defenses_bypassed: List[str] = field(default_factory=list)
    permissions_required: List[str] = field(default_factory=list)
    mitigations: List[str] = field(default_factory=list)
    detection_methods: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'pattern_id': self.pattern_id,
            'name': self.name,
            'description': self.description,
            'tactics': self.tactics,
            'techniques': self.techniques,
            'platforms': self.platforms,
            'data_sources': self.data_sources,
            'defenses_bypassed': self.defenses_bypassed,
            'permissions_required': self.permissions_required,
            'mitigations': self.mitigations,
            'detection_methods': self.detection_methods
        }

@dataclass
class SecurityControl:
    """Security control or countermeasure"""
    control_id: str
    name: str
    description: str = ""
    control_type: str = "preventive"  # preventive, detective, corrective
    implementation_status: str = "not_implemented"
    effectiveness: Optional[float] = None
    cost: Optional[str] = None
    complexity: Optional[str] = None
    compliance_frameworks: List[str] = field(default_factory=list)
    threats_mitigated: List[str] = field(default_factory=list)
    implementation_guidance: Optional[str] = None
    testing_procedures: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'control_id': self.control_id,
            'name': self.name,
            'description': self.description,
            'control_type': self.control_type,
            'implementation_status': self.implementation_status,
            'effectiveness': self.effectiveness,
            'cost': self.cost,
            'complexity': self.complexity,
            'compliance_frameworks': self.compliance_frameworks,
            'threats_mitigated': self.threats_mitigated,
            'implementation_guidance': self.implementation_guidance,
            'testing_procedures': self.testing_procedures
        }

# Helper functions for finding creation
def create_finding(
    tool: str,
    rule_id: str,
    title: str,
    message: str,
    file_path: str,
    severity: Severity = Severity.MEDIUM,
    category: Category = Category.OTHER,
    line_number: Optional[int] = None,
    **kwargs
) -> Finding:
    """Helper function to create a Finding with common parameters"""
    return Finding(
        tool=tool,
        rule_id=rule_id,
        title=title,
        message=message,
        file_path=file_path,
        severity=severity,
        category=category,
        line_number=line_number,
        **kwargs
    )

def create_vulnerability(
    vuln_id: str,
    title: str,
    description: str,
    severity: Severity = Severity.MEDIUM,
    cve_id: Optional[str] = None,
    **kwargs
) -> Vulnerability:
    """Helper function to create a Vulnerability with common parameters"""
    return Vulnerability(
        vuln_id=vuln_id,
        title=title,
        description=description,
        severity=severity,
        cve_id=cve_id,
        **kwargs
    )

# Export all security-related classes and enums
__all__ = [
    # Enums
    'Severity',
    'Confidence', 
    'Category',
    'ExploitabilityLevel',
    'ImpactLevel',
    
    # Data classes
    'CodeLocation',
    'Finding',
    'Vulnerability',
    'ThreatActor',
    'AttackPattern',
    'SecurityControl',
    
    # Helper functions
    'create_finding',
    'create_vulnerability',
]