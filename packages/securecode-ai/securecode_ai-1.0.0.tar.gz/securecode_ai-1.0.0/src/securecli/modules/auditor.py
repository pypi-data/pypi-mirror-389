"""
SecureCLI Auditor Module
Provides detailed security auditing and compliance checking
"""

import asyncio
import logging
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from ..schemas.analysis import AuditResult, ComplianceCheck, ScanResult
from ..schemas.security import Severity, Category, Finding

logger = logging.getLogger(__name__)

class ComplianceFramework(Enum):
    """Supported compliance frameworks"""
    OWASP_TOP_10 = "owasp_top_10"
    CWE_TOP_25 = "cwe_top_25"
    NIST_CYBERSECURITY = "nist_cybersecurity"
    ISO_27001 = "iso_27001"
    SOC2 = "soc2"
    PCI_DSS = "pci_dss"
    GDPR = "gdpr"
    HIPAA = "hipaa"

@dataclass
class AuditConfiguration:
    """Configuration for security auditing"""
    target_path: Path
    frameworks: Set[ComplianceFramework] = field(default_factory=set)
    include_scan: bool = True
    trend_analysis: bool = True
    baseline_path: Optional[Path] = None
    export_formats: Set[str] = field(default_factory=lambda: {"json", "html"})
    detailed_remediation: bool = True
    risk_scoring: bool = True

class SecurityAuditor:
    """
    Comprehensive security auditor with compliance checking
    """
    
    def __init__(self):
        # Compliance rule mappings
        self.compliance_rules = {
            ComplianceFramework.OWASP_TOP_10: {
                'A01_Broken_Access_Control': ['CWE-22', 'CWE-79', 'CWE-200'],
                'A02_Cryptographic_Failures': ['CWE-327', 'CWE-328', 'CWE-326'],
                'A03_Injection': ['CWE-79', 'CWE-89', 'CWE-78'],
                'A04_Insecure_Design': ['CWE-209', 'CWE-256', 'CWE-501'],
                'A05_Security_Misconfiguration': ['CWE-16', 'CWE-2', 'CWE-209'],
                'A06_Vulnerable_Components': ['CWE-1104', 'CWE-829'],
                'A07_Authentication_Failures': ['CWE-287', 'CWE-384', 'CWE-620'],
                'A08_Software_Data_Integrity': ['CWE-502', 'CWE-829'],
                'A09_Security_Logging_Failures': ['CWE-117', 'CWE-223'],
                'A10_SSRF': ['CWE-918']
            },
            ComplianceFramework.CWE_TOP_25: {
                'CWE-79': 'Cross-site Scripting',
                'CWE-787': 'Out-of-bounds Write',
                'CWE-20': 'Improper Input Validation',
                'CWE-125': 'Out-of-bounds Read',
                'CWE-119': 'Improper Restriction of Operations',
                'CWE-89': 'SQL Injection',
                'CWE-200': 'Information Exposure',
                'CWE-416': 'Use After Free',
                'CWE-352': 'Cross-Site Request Forgery',
                'CWE-78': 'OS Command Injection'
            }
        }
        
        # Risk scoring weights
        self.risk_weights = {
            'severity': 0.4,
            'exploitability': 0.3,
            'business_impact': 0.2,
            'compliance_impact': 0.1
        }
    
    async def audit_project(self, config: AuditConfiguration) -> AuditResult:
        """
        Perform comprehensive security audit
        
        Args:
            config: Audit configuration
            
        Returns:
            AuditResult: Complete audit results
        """
        logger.info(f"Starting security audit of {config.target_path}")
        start_time = datetime.now()
        
        try:
            # Step 1: Run security scan if requested
            scan_result = None
            if config.include_scan:
                if config.scan_config is None:
                    scan_config = ScanConfiguration(target_path=config.target_path)
                else:
                    scan_config = config.scan_config
                
                scan_result = await self.scanner.scan_project(scan_config)
                logger.info(f"Scan completed with {len(scan_result.findings)} findings")
            
            # Step 2: Perform compliance checks
            compliance_checks = []
            if config.frameworks:
                compliance_checks = await self._perform_compliance_checks(
                    scan_result.findings if scan_result else [],
                    config.frameworks
                )
                logger.info(f"Completed {len(compliance_checks)} compliance checks")
            
            # Step 3: Calculate risk scores
            risk_analysis = {}
            if config.risk_scoring and scan_result:
                risk_analysis = await self._calculate_risk_scores(scan_result.findings)
                logger.info("Risk scoring completed")
            
            # Step 4: Generate remediation recommendations
            remediation_plan = []
            if config.detailed_remediation and scan_result:
                remediation_plan = await self._generate_remediation_plan(scan_result.findings)
                logger.info(f"Generated {len(remediation_plan)} remediation items")
            
            # Step 5: Trend analysis
            trend_data = {}
            if config.trend_analysis and config.baseline_path:
                trend_data = await self._analyze_trends(scan_result, config.baseline_path)
                logger.info("Trend analysis completed")
            
            # Step 6: Calculate overall audit metrics
            audit_metrics = self._calculate_audit_metrics(
                scan_result, compliance_checks, risk_analysis
            )
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            result = AuditResult(
                target_path=str(config.target_path),
                scan_result=scan_result,
                compliance_checks=compliance_checks,
                risk_analysis=risk_analysis,
                remediation_plan=remediation_plan,
                trend_data=trend_data,
                audit_metrics=audit_metrics,
                frameworks_checked=list(config.frameworks),
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                success=True
            )
            
            logger.info(f"Audit completed in {duration:.2f}s")
            return result
            
        except Exception as e:
            logger.error(f"Audit failed: {str(e)}")
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            return AuditResult(
                target_path=str(config.target_path),
                scan_result=None,
                compliance_checks=[],
                risk_analysis={},
                remediation_plan=[],
                trend_data={},
                audit_metrics={},
                frameworks_checked=[],
                start_time=start_time,
                end_time=end_time,
                duration_seconds=duration,
                success=False,
                error_message=str(e)
            )
    
    async def _perform_compliance_checks(
        self, 
        findings: List[Finding], 
        frameworks: Set[ComplianceFramework]
    ) -> List[ComplianceCheck]:
        """Perform compliance framework checks"""
        compliance_checks = []
        
        for framework in frameworks:
            logger.info(f"Checking compliance with {framework.value}")
            
            if framework in self.compliance_rules:
                rules = self.compliance_rules[framework]
                framework_checks = await self._check_framework_compliance(
                    findings, framework, rules
                )
                compliance_checks.extend(framework_checks)
        
        return compliance_checks
    
    async def _check_framework_compliance(
        self,
        findings: List[Finding],
        framework: ComplianceFramework,
        rules: Dict[str, Any]
    ) -> List[ComplianceCheck]:
        """Check compliance against specific framework"""
        checks = []
        
        if framework == ComplianceFramework.OWASP_TOP_10:
            for category, cwe_list in rules.items():
                # Count findings matching this OWASP category
                matching_findings = [
                    f for f in findings 
                    if any(cwe in (f.cwe_id or '') for cwe in cwe_list)
                ]
                
                passed = len(matching_findings) == 0
                
                check = ComplianceCheck(
                    framework=framework.value,
                    control_id=category,
                    control_name=category.replace('_', ' ').title(),
                    description=f"OWASP Top 10 - {category}",
                    passed=passed,
                    findings_count=len(matching_findings),
                    related_findings=[f.id for f in matching_findings],
                    severity=self._determine_compliance_severity(matching_findings)
                )
                checks.append(check)
        
        elif framework == ComplianceFramework.CWE_TOP_25:
            for cwe_id, description in rules.items():
                matching_findings = [
                    f for f in findings 
                    if f.cwe_id == cwe_id
                ]
                
                passed = len(matching_findings) == 0
                
                check = ComplianceCheck(
                    framework=framework.value,
                    control_id=cwe_id,
                    control_name=description,
                    description=f"CWE Top 25 - {description}",
                    passed=passed,
                    findings_count=len(matching_findings),
                    related_findings=[f.id for f in matching_findings],
                    severity=self._determine_compliance_severity(matching_findings)
                )
                checks.append(check)
        
        return checks
    
    def _determine_compliance_severity(self, findings: List[Finding]) -> Severity:
        """Determine severity level for compliance check"""
        if not findings:
            return Severity.INFO
        
        max_severity = max(f.severity for f in findings)
        return max_severity
    
    async def _calculate_risk_scores(self, findings: List[Finding]) -> Dict[str, Any]:
        """Calculate risk scores for findings"""
        risk_analysis = {
            'overall_risk_score': 0,
            'risk_distribution': {},
            'critical_risks': [],
            'findings_by_risk': {}
        }
        
        total_risk = 0
        risk_counts = {'LOW': 0, 'MEDIUM': 0, 'HIGH': 0, 'CRITICAL': 0}
        
        for finding in findings:
            # Calculate individual risk score
            severity_score = finding.severity.value
            exploitability_score = self._estimate_exploitability(finding)
            business_impact_score = self._estimate_business_impact(finding)
            compliance_impact_score = self._estimate_compliance_impact(finding)
            
            risk_score = (
                severity_score * self.risk_weights['severity'] +
                exploitability_score * self.risk_weights['exploitability'] +
                business_impact_score * self.risk_weights['business_impact'] +
                compliance_impact_score * self.risk_weights['compliance_impact']
            )
            
            finding.risk_score = risk_score
            total_risk += risk_score
            
            # Categorize risk level
            if risk_score >= 8:
                risk_level = 'CRITICAL'
                risk_analysis['critical_risks'].append(finding)
            elif risk_score >= 6:
                risk_level = 'HIGH'
            elif risk_score >= 4:
                risk_level = 'MEDIUM'
            else:
                risk_level = 'LOW'
            
            risk_counts[risk_level] += 1
            
            if risk_level not in risk_analysis['findings_by_risk']:
                risk_analysis['findings_by_risk'][risk_level] = []
            risk_analysis['findings_by_risk'][risk_level].append(finding)
        
        if findings:
            risk_analysis['overall_risk_score'] = total_risk / len(findings)
        
        risk_analysis['risk_distribution'] = risk_counts
        
        return risk_analysis
    
    def _estimate_exploitability(self, finding: Finding) -> float:
        """Estimate how easily a finding can be exploited"""
        # Simple heuristic based on category and context
        high_exploitability = [
            Category.INJECTION,
            Category.XSS,
            Category.AUTHENTICATION,
            Category.SECRETS
        ]
        
        if finding.category in high_exploitability:
            return 8.0
        elif finding.category in [Category.CRYPTO, Category.ACCESS_CONTROL]:
            return 6.0
        else:
            return 4.0
    
    def _estimate_business_impact(self, finding: Finding) -> float:
        """Estimate business impact of a finding"""
        # Simple heuristic based on severity and file type
        if finding.severity == Severity.CRITICAL:
            return 9.0
        elif finding.severity == Severity.HIGH:
            return 7.0
        elif finding.severity == Severity.MEDIUM:
            return 5.0
        else:
            return 3.0
    
    def _estimate_compliance_impact(self, finding: Finding) -> float:
        """Estimate compliance impact of a finding"""
        # Simple heuristic based on CWE mapping
        if finding.cwe_id in ['CWE-79', 'CWE-89', 'CWE-22']:
            return 8.0  # High compliance impact
        elif finding.cwe_id in ['CWE-200', 'CWE-287', 'CWE-352']:
            return 6.0  # Medium compliance impact
        else:
            return 4.0  # Low compliance impact
    
    async def _generate_remediation_plan(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Generate detailed remediation plan"""
        remediation_plan = []
        
        # Group findings by category for better remediation planning
        findings_by_category = {}
        for finding in findings:
            category = finding.category
            if category not in findings_by_category:
                findings_by_category[category] = []
            findings_by_category[category].append(finding)
        
        for category, category_findings in findings_by_category.items():
            # Create category-specific remediation item
            remediation_item = {
                'category': category.value,
                'priority': self._calculate_remediation_priority(category_findings),
                'findings_count': len(category_findings),
                'estimated_effort': self._estimate_remediation_effort(category_findings),
                'recommended_actions': self._get_category_remediation_actions(category),
                'related_findings': [f.id for f in category_findings],
                'tools_needed': self._get_remediation_tools(category),
                'timeline': self._estimate_remediation_timeline(category_findings)
            }
            remediation_plan.append(remediation_item)
        
        # Sort by priority
        remediation_plan.sort(key=lambda x: x['priority'], reverse=True)
        
        return remediation_plan
    
    def _calculate_remediation_priority(self, findings: List[Finding]) -> int:
        """Calculate priority for remediation (1-10)"""
        if not findings:
            return 1
        
        max_severity = max(f.severity.value for f in findings)
        avg_risk = sum(getattr(f, 'risk_score', 5) for f in findings) / len(findings)
        
        return min(10, int((max_severity + avg_risk) / 2))
    
    def _estimate_remediation_effort(self, findings: List[Finding]) -> str:
        """Estimate effort needed for remediation"""
        if len(findings) <= 2:
            return "Low"
        elif len(findings) <= 10:
            return "Medium"
        else:
            return "High"
    
    def _get_category_remediation_actions(self, category: Category) -> List[str]:
        """Get recommended actions for a category"""
        actions = {
            Category.INJECTION: [
                "Implement input validation and sanitization",
                "Use parameterized queries or prepared statements",
                "Apply least privilege principle for database access",
                "Enable proper error handling"
            ],
            Category.XSS: [
                "Implement output encoding/escaping",
                "Use Content Security Policy (CSP)",
                "Validate and sanitize all user inputs",
                "Use secure templating engines"
            ],
            Category.CRYPTO: [
                "Use strong, up-to-date cryptographic algorithms",
                "Implement proper key management",
                "Use secure random number generation",
                "Apply proper salt and hashing for passwords"
            ],
            Category.AUTHENTICATION: [
                "Implement strong password policies",
                "Use multi-factor authentication",
                "Implement account lockout mechanisms",
                "Use secure session management"
            ],
            Category.SECRETS: [
                "Remove hardcoded secrets from code",
                "Use environment variables or secret management systems",
                "Implement proper access controls for secrets",
                "Regularly rotate credentials"
            ]
        }
        
        return actions.get(category, ["Review and address security findings"])
    
    def _get_remediation_tools(self, category: Category) -> List[str]:
        """Get recommended tools for remediation"""
        tools = {
            Category.INJECTION: ["SQLMap", "OWASP ZAP", "Burp Suite"],
            Category.XSS: ["OWASP ZAP", "Burp Suite", "XSS Hunter"],
            Category.CRYPTO: ["HashiCorp Vault", "AWS KMS", "CyberChef"],
            Category.AUTHENTICATION: ["Auth0", "Okta", "LDAP"],
            Category.SECRETS: ["HashiCorp Vault", "AWS Secrets Manager", "Git-secrets"]
        }
        
        return tools.get(category, [])
    
    def _estimate_remediation_timeline(self, findings: List[Finding]) -> str:
        """Estimate timeline for remediation"""
        high_severity_count = sum(1 for f in findings if f.severity.value >= 7)
        
        if high_severity_count > 5:
            return "Immediate (1-3 days)"
        elif high_severity_count > 0:
            return "Short-term (1-2 weeks)"
        elif len(findings) > 10:
            return "Medium-term (2-4 weeks)"
        else:
            return "Long-term (1-2 months)"
    
    async def _analyze_trends(self, current_result: ScanResult, baseline_path: Path) -> Dict[str, Any]:
        """Analyze trends compared to baseline"""
        # This would load and compare with previous scan results
        # For now, return placeholder structure
        return {
            'baseline_date': None,
            'findings_trend': 'stable',
            'new_findings': 0,
            'resolved_findings': 0,
            'severity_trends': {},
            'category_trends': {}
        }
    
    def _calculate_audit_metrics(
        self,
        scan_result: Optional[ScanResult],
        compliance_checks: List[ComplianceCheck],
        risk_analysis: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Calculate overall audit metrics"""
        metrics = {
            'security_score': 0,
            'compliance_score': 0,
            'risk_score': 0,
            'overall_score': 0,
            'findings_summary': {},
            'compliance_summary': {},
            'recommendations_count': 0
        }
        
        # Calculate security score
        if scan_result and scan_result.findings:
            total_findings = len(scan_result.findings)
            critical_findings = sum(1 for f in scan_result.findings if f.severity == Severity.CRITICAL)
            high_findings = sum(1 for f in scan_result.findings if f.severity == Severity.HIGH)
            
            # Simple scoring: start with 100, deduct points for findings
            security_score = max(0, 100 - (critical_findings * 20) - (high_findings * 10) - ((total_findings - critical_findings - high_findings) * 2))
            metrics['security_score'] = security_score
        else:
            metrics['security_score'] = 100
        
        # Calculate compliance score
        if compliance_checks:
            passed_checks = sum(1 for c in compliance_checks if c.passed)
            compliance_score = (passed_checks / len(compliance_checks)) * 100
            metrics['compliance_score'] = compliance_score
        else:
            metrics['compliance_score'] = 100
        
        # Calculate risk score
        if risk_analysis and 'overall_risk_score' in risk_analysis:
            # Invert risk score to get a positive score (lower risk = higher score)
            risk_score = max(0, 100 - (risk_analysis['overall_risk_score'] * 10))
            metrics['risk_score'] = risk_score
        else:
            metrics['risk_score'] = 100
        
        # Overall score is weighted average
        metrics['overall_score'] = (
            metrics['security_score'] * 0.4 +
            metrics['compliance_score'] * 0.3 +
            metrics['risk_score'] * 0.3
        )
        
        return metrics

# Export main components
__all__ = [
    'SecurityAuditor',
    'AuditConfiguration',
    'ComplianceFramework',
]