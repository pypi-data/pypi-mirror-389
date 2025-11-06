"""
Report generator interface for SecureCLI
Provides unified interface for generating security reports in multiple formats
"""

from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from ..schemas.findings import Finding, ExecutiveSummary
from .markdown import MarkdownReporter
from .json_export import JSONExporter
from ..utils.cvss import SimpleVulnerabilityClassifier
from .diagrams import MermaidDiagramGenerator


class ReportGenerator:
    """Unified report generation interface"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.markdown_reporter = MarkdownReporter(config)
        self.json_exporter = JSONExporter(config)
        self.diagram_generator = MermaidDiagramGenerator()
        self.vulnerability_classifier = SimpleVulnerabilityClassifier()
        self.generate_chart_images = config.get('output.generate_chart_images', False)
        
        # Output directory
        self.output_dir = Path(config.get('output.dir', './output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def generate_full_report(
        self,
        findings: List[Finding],
        metadata: Dict[str, Any],
        output_formats: List[str] = None
    ) -> Dict[str, Any]:
        """
        Generate complete security report in multiple formats
        
        Args:
            findings: List of security findings
            metadata: Scan metadata and context
            output_formats: List of formats to generate (markdown, json, sarif, csv)
        
        Returns:
            Dictionary mapping format to output file path
        """
        
        if output_formats is None:
            output_formats = ['markdown', 'json']
        
        # Auto-score findings that don't have CVSS scores
        findings = await self._ensure_cvss_scores(findings)
        
        # Generate executive summary
        executive_summary = await self._generate_executive_summary(findings, metadata)
        
        # Generate reports in requested formats
        results = {}
        
        if 'markdown' in output_formats:
            results['markdown'] = await self._generate_markdown_report(
                findings, executive_summary, metadata
            )
        
        if 'json' in output_formats:
            results['json'] = await self.json_exporter.export_full_report(
                findings, executive_summary, metadata
            )
        
        if 'sarif' in output_formats:
            results['sarif'] = await self.json_exporter.export_sarif(
                findings, metadata
            )
        
        if 'csv' in output_formats:
            results['csv'] = await self.json_exporter.export_csv(findings)
        
        # Generate additional artifacts
        if self.config.get('generate_diagrams', True):
            diagram_artifacts = await self._generate_diagram_files(findings, metadata)
            if diagram_artifacts:
                results['diagrams'] = diagram_artifacts
        
        return results
    
    async def generate_ci_report(
        self,
        findings: List[Finding],
        metadata: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate CI-friendly report with exit codes and summary
        
        Args:
            findings: List of security findings
            metadata: Scan metadata
        
        Returns:
            CI report data with exit codes and summary
        """
        
        # Calculate statistics
        stats = self._calculate_statistics(findings)
        
        # Determine CI exit code based on findings
        exit_code = self._calculate_exit_code(findings)
        
        # Generate SARIF for CI integration
        sarif_path = await self.json_exporter.export_sarif(findings, metadata)
        
        # Create CI summary
        ci_report = {
            "exit_code": exit_code,
            "success": exit_code == 0,
            "statistics": stats,
            "sarif_file": sarif_path,
            "summary": self._generate_ci_summary(stats),
            "recommendations": self._generate_ci_recommendations(findings)
        }
        
        # Write CI report
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        ci_report_path = self.output_dir / f"ci_report_{timestamp}.json"
        
        import json
        with open(ci_report_path, 'w') as f:
            json.dump(ci_report, f, indent=2)
        
        ci_report["report_file"] = str(ci_report_path)
        
        return ci_report
    
    async def _ensure_cvss_scores(self, findings: List[Finding]) -> List[Finding]:
        """Ensure all findings have CVSS scores"""
        
        scored_findings = []
        
        for finding in findings:
            if finding.cvss_v4.score == 0.0:
                # Auto-generate CVSS score
                cvss = self.vulnerability_classifier.auto_score_finding(
                    finding.title,
                    finding.description,
                    {
                        "public_facing": "web" in finding.file.lower(),
                        "authenticated_required": "auth" in finding.description.lower(),
                        "user_interaction": "user" in finding.description.lower()
                    }
                )
                
                # Update finding with calculated score
                finding.cvss_v4 = cvss
                finding.severity = cvss.severity
            
            scored_findings.append(finding)
        
        return scored_findings
    
    async def _generate_executive_summary(
        self,
        findings: List[Finding],
        metadata: Dict[str, Any]
    ) -> ExecutiveSummary:
        """Generate executive summary"""
        
        stats = self._calculate_statistics(findings)
        
        # Calculate risk score (weighted average)
        risk_score = self._calculate_risk_score(findings)
        
        # Generate key findings
        key_findings = self._identify_key_findings(findings)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(findings)
        
        return ExecutiveSummary(
            total_findings=stats["total_findings"],
            critical_count=stats["by_severity"]["Critical"],
            high_count=stats["by_severity"]["High"], 
            medium_count=stats["by_severity"]["Medium"],
            low_count=stats["by_severity"]["Low"],
            files_scanned=metadata.get('scanned_files', 0),
            risk_score=risk_score,
            key_findings=key_findings,
            recommendations=recommendations
        )
    
    async def _generate_markdown_report(
        self,
        findings: List[Finding],
        executive_summary: ExecutiveSummary,
        metadata: Dict[str, Any]
    ) -> str:
        """Generate markdown report with diagrams"""
        
        # Generate diagrams
        diagrams = {
            "severity_chart": self.diagram_generator.generate_severity_chart(findings),
            "file_heatmap": self.diagram_generator.generate_file_heatmap(findings),
            "attack_flow": self.diagram_generator.generate_attack_flow(findings),
            "owasp_mapping": self.diagram_generator.generate_owasp_mapping(findings)
        }
        
        return await self.markdown_reporter.generate_full_report(
            findings, executive_summary, metadata
        )
    
    async def _generate_diagram_files(
        self,
        findings: List[Finding],
        metadata: Dict[str, Any]
    ) -> Dict[str, str]:
        """Generate standalone diagram files."""
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Generate individual diagram files
        diagrams = {
            "severity_distribution": self.diagram_generator.generate_severity_chart(findings),
            "file_analysis": self.diagram_generator.generate_file_heatmap(findings),
            "attack_vectors": self.diagram_generator.generate_attack_flow(findings),
            "owasp_coverage": self.diagram_generator.generate_owasp_mapping(findings),
            "remediation_timeline": self.diagram_generator.generate_remediation_timeline(findings)
        }
        
        # Write diagram files
        diagram_dir = self.output_dir / "diagrams"
        diagram_dir.mkdir(exist_ok=True)
        
        artifact_paths: Dict[str, str] = {}

        for name, content in diagrams.items():
            diagram_path = diagram_dir / f"{name}_{timestamp}.md"
            with open(diagram_path, 'w', encoding='utf-8') as f:
                f.write(f"# {name.replace('_', ' ').title()}\n\n")
                f.write(content)
            artifact_paths[name] = str(diagram_path)

        if self.generate_chart_images:
            image_artifacts = self.diagram_generator.generate_static_images(findings, diagram_dir, timestamp)
            for key, path in image_artifacts.items():
                artifact_paths[key] = str(path)

        return artifact_paths
    
    def _calculate_statistics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Calculate comprehensive statistics"""
        
        if not findings:
            return {
                "total_findings": 0,
                "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "files_affected": 0,
                "avg_cvss_score": 0.0,
                "categories": {},
                "tools": {}
            }
        
        stats = {
            "total_findings": len(findings),
            "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            "files_affected": len(set(f.file for f in findings)),
            "avg_cvss_score": sum(f.cvss_v4.score for f in findings) / len(findings),
            "categories": {},
            "tools": {},
            "cross_file_issues": len([f for f in findings if f.cross_file])
        }
        
        for finding in findings:
            # Count by severity
            stats["by_severity"][finding.severity] += 1
            
            # Count categories
            for category in finding.owasp + finding.cwe:
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Count tools
            for evidence in finding.tool_evidence:
                tool = evidence.tool
                stats["tools"][tool] = stats["tools"].get(tool, 0) + 1
        
        return stats
    
    def _calculate_risk_score(self, findings: List[Finding]) -> float:
        """Calculate overall risk score (0-100)"""
        
        if not findings:
            return 0.0
        
        # Weight findings by severity
        weights = {"Critical": 10, "High": 7, "Medium": 4, "Low": 1}
        total_weight = 0
        max_possible = 0
        
        for finding in findings:
            weight = weights.get(finding.severity, 1)
            total_weight += weight * finding.cvss_v4.score
            max_possible += weight * 10.0  # Max CVSS score
        
        if max_possible == 0:
            return 0.0
        
        # Scale to 0-100
        risk_score = (total_weight / max_possible) * 100
        return round(risk_score, 1)
    
    def _identify_key_findings(self, findings: List[Finding]) -> List[str]:
        """Identify key findings for executive summary"""
        
        key_findings = []
        
        # Critical findings
        critical = [f for f in findings if f.severity == "Critical"]
        if critical:
            key_findings.append(f"{len(critical)} critical security vulnerabilities requiring immediate attention")
        
        # High severity findings
        high = [f for f in findings if f.severity == "High"]
        if high:
            key_findings.append(f"{len(high)} high-severity issues that should be addressed within 7 days")
        
        # Cross-file vulnerabilities
        cross_file = [f for f in findings if f.cross_file]
        if cross_file:
            key_findings.append(f"{len(cross_file)} vulnerabilities span multiple files, indicating systemic issues")
        
        # Common vulnerability categories
        from collections import Counter
        all_categories = []
        for finding in findings:
            all_categories.extend(finding.owasp + finding.cwe)
        
        if all_categories:
            common_categories = Counter(all_categories).most_common(3)
            top_category = common_categories[0]
            key_findings.append(f"Most common vulnerability type: {top_category[0]} ({top_category[1]} instances)")
        
        return key_findings[:5]  # Limit to top 5
    
    def _generate_recommendations(self, findings: List[Finding]) -> List[str]:
        """Generate high-level recommendations"""
        
        recommendations = []
        
        # Priority-based recommendations
        critical = [f for f in findings if f.severity == "Critical"]
        if critical:
            recommendations.append("Immediately patch critical vulnerabilities before deployment")
        
        high = [f for f in findings if f.severity == "High"]
        if high:
            recommendations.append("Address high-severity issues within the next sprint")
        
        # Tool-based recommendations
        from collections import Counter
        all_tools = []
        for finding in findings:
            all_tools.extend([ev.tool for ev in finding.tool_evidence])
        
        if all_tools:
            tool_counts = Counter(all_tools)
            if tool_counts.get('semgrep', 0) > 5:
                recommendations.append("Integrate Semgrep into CI/CD pipeline for automated code analysis")
            if tool_counts.get('gitleaks', 0) > 0:
                recommendations.append("Implement secret scanning in version control")
        
        # Category-based recommendations
        all_categories = []
        for finding in findings:
            all_categories.extend(finding.owasp + finding.cwe)
        
        category_counts = Counter(all_categories)
        
        if category_counts.get('OWASP-A03', 0) > 0:  # Injection
            recommendations.append("Implement input validation and parameterized queries")
        if category_counts.get('OWASP-A01', 0) > 0:  # Broken Access Control
            recommendations.append("Review and strengthen access control mechanisms")
        if category_counts.get('OWASP-A02', 0) > 0:  # Cryptographic Failures
            recommendations.append("Upgrade cryptographic implementations to current standards")
        
        # General recommendations
        if len(findings) > 10:
            recommendations.append("Establish regular security testing as part of development process")
        
        recommendations.append("Consider security training for development team")
        
        return recommendations[:7]  # Limit to top 7
    
    def _calculate_exit_code(self, findings: List[Finding]) -> int:
        """Calculate CI exit code based on findings"""
        
        critical = len([f for f in findings if f.severity == "Critical"])
        high = len([f for f in findings if f.severity == "High"])
        
        # Exit codes:
        # 0 = Success (no critical/high findings)
        # 1 = Warning (high findings but no critical)
        # 2 = Failure (critical findings)
        
        if critical > 0:
            return 2  # Failure
        elif high > 0:
            return 1  # Warning
        else:
            return 0  # Success
    
    def _generate_ci_summary(self, stats: Dict[str, Any]) -> str:
        """Generate CI summary text"""
        
        total = stats["total_findings"]
        critical = stats["by_severity"]["Critical"]
        high = stats["by_severity"]["High"]
        medium = stats["by_severity"]["Medium"]
        low = stats["by_severity"]["Low"]
        
        if total == 0:
            return "✅ No security issues found"
        
        summary_parts = []
        
        if critical > 0:
            summary_parts.append(f"🔴 {critical} Critical")
        if high > 0:
            summary_parts.append(f"🟠 {high} High")
        if medium > 0:
            summary_parts.append(f"🟡 {medium} Medium")
        if low > 0:
            summary_parts.append(f"🔵 {low} Low")
        
        return f"Found {total} security issues: " + ", ".join(summary_parts)
    
    def _generate_ci_recommendations(self, findings: List[Finding]) -> List[str]:
        """Generate CI-specific recommendations"""
        
        recommendations = []
        
        critical = [f for f in findings if f.severity == "Critical"]
        high = [f for f in findings if f.severity == "High"]
        
        if critical:
            recommendations.append("🚨 Block deployment until critical issues are resolved")
        elif high:
            recommendations.append("⚠️ Consider blocking deployment for high-severity issues")
        
        # Add top 3 actionable recommendations
        general_recs = self._generate_recommendations(findings)
        recommendations.extend(general_recs[:3])
        
        return recommendations