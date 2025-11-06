"""
Markdown report generator for SecureCLI
Creates comprehensive security assessment reports in Markdown format
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional
from jinja2 import Template

from ..schemas.findings import Finding, ExecutiveSummary


class MarkdownReporter:
    """Generates Markdown security reports"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get('output.dir', './output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Report templates
        self.main_template = self._get_main_template()
        self.finding_template = self._get_finding_template()
        self.summary_template = self._get_summary_template()
    
    async def generate_full_report(
        self,
        findings: List[Finding],
        executive_summary: ExecutiveSummary,
        metadata: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Generate complete security assessment report"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"security_report_{timestamp}.md"
        
        # Prepare report data
        report_data = {
            'metadata': self._prepare_metadata(metadata),
            'executive_summary': executive_summary,
            'findings': self._organize_findings(findings),
            'statistics': self._calculate_statistics(findings),
            'generated_at': datetime.now().isoformat(),
            'total_findings': len(findings)
        }
        
        # Render report
        report_content = self.main_template.render(**report_data)
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(output_path)
    
    async def generate_summary_report(
        self,
        executive_summary: ExecutiveSummary,
        metadata: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Generate executive summary report"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"security_summary_{timestamp}.md"
        
        report_data = {
            'metadata': self._prepare_metadata(metadata),
            'executive_summary': executive_summary,
            'generated_at': datetime.now().isoformat()
        }
        
        report_content = self.summary_template.render(**report_data)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(report_content)
        
        return str(output_path)
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for template rendering"""
        return {
            'repo_path': metadata.get('repo_path', 'Unknown'),
            'scan_mode': metadata.get('mode', 'quick'),
            'domain_profiles': metadata.get('domain_profiles', []),
            'tools_used': metadata.get('tools_used', []),
            'scan_duration': metadata.get('scan_duration', 'Unknown'),
            'target_files': metadata.get('target_files', 0),
            'scanned_files': metadata.get('scanned_files', 0)
        }
    
    def _organize_findings(self, findings: List[Finding]) -> Dict[str, Any]:
        """Organize findings by various categories"""
        organized = {
            'by_severity': {'Critical': [], 'High': [], 'Medium': [], 'Low': []},
            'by_file': {},
            'by_category': {},
            'cross_file': []
        }
        
        for finding in findings:
            # By severity
            severity = finding.severity
            if severity in organized['by_severity']:
                organized['by_severity'][severity].append(finding)
            
            # By file
            file_path = finding.file
            if file_path not in organized['by_file']:
                organized['by_file'][file_path] = []
            organized['by_file'][file_path].append(finding)
            
            # By category (based on OWASP/CWE)
            categories = finding.owasp + finding.cwe
            for category in categories:
                if category not in organized['by_category']:
                    organized['by_category'][category] = []
                organized['by_category'][category].append(finding)
            
            # Cross-file issues
            if finding.cross_file:
                organized['cross_file'].append(finding)
        
        return organized
    
    def _calculate_statistics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Calculate report statistics"""
        stats = {
            'total_findings': len(findings),
            'by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0},
            'files_affected': len(set(f.file for f in findings)),
            'avg_cvss_score': 0.0,
            'top_categories': {},
            'tools_breakdown': {}
        }
        
        total_cvss = 0.0
        
        for finding in findings:
            # Count by severity
            stats['by_severity'][finding.severity] += 1
            
            # Accumulate CVSS scores
            total_cvss += finding.cvss_v4.score
            
            # Count categories
            for category in finding.owasp + finding.cwe:
                stats['top_categories'][category] = stats['top_categories'].get(category, 0) + 1
            
            # Count tools
            for evidence in finding.tool_evidence:
                tool = evidence.tool
                stats['tools_breakdown'][tool] = stats['tools_breakdown'].get(tool, 0) + 1
        
        # Calculate average CVSS
        if findings:
            stats['avg_cvss_score'] = round(total_cvss / len(findings), 1)
        
        # Sort top categories
        stats['top_categories'] = dict(sorted(
            stats['top_categories'].items(),
            key=lambda x: x[1],
            reverse=True
        )[:10])
        
        return stats
    
    def _get_main_template(self) -> Template:
        """Get main report template"""
        template_content = """# Security Assessment Report

## Executive Summary

**Repository:** `{{ metadata.repo_path }}`  
**Scan Mode:** `{{ metadata.scan_mode }}`  
**Generated:** {{ generated_at }}  
**Total Findings:** {{ total_findings }}

### Risk Overview

{% if executive_summary.heatmap %}
| Severity | Count | Percentage |
|----------|-------|------------|
{% for severity, count in executive_summary.heatmap.items() -%}
| {{ severity }} | {{ count }} | {{ "%.1f"|format((count / total_findings * 100) if total_findings > 0 else 0) }}% |
{% endfor %}
{% endif %}

### Top Risks

{% for risk in executive_summary.top_risks[:5] %}
{{ loop.index }}. **{{ risk.title }}** ({{ risk.severity }}, CVSS: {{ risk.cvss_v4.score }})  
   {{ risk.one_line }}
{% endfor %}

### Security Themes

{% for theme in executive_summary.themes %}
- {{ theme }}
{% endfor %}

---

## Scan Information

**Repository Path:** `{{ metadata.repo_path }}`  
**Scan Mode:** `{{ metadata.scan_mode }}`  
**Domain Profiles:** {{ metadata.domain_profiles | join(', ') if metadata.domain_profiles else 'None' }}  
**Tools Used:** {{ metadata.tools_used | join(', ') if metadata.tools_used else 'None' }}  
**Files Scanned:** {{ metadata.scanned_files }} / {{ metadata.target_files }}  
**Duration:** {{ metadata.scan_duration }}

---

## Statistics

| Metric | Value |
|--------|-------|
| Total Findings | {{ statistics.total_findings }} |
| Files Affected | {{ statistics.files_affected }} |
| Average CVSS Score | {{ "%.1f"|format(statistics.avg_cvss_score) }} |
| Cross-File Issues | {{ statistics.cross_file_issues if statistics.cross_file_issues is defined else 0 }} |

### Findings by Severity

| Severity | Count |
|----------|-------|
{% for severity in ['Critical', 'High', 'Medium', 'Low'] -%}
| {{ severity }} | {{ statistics.by_severity.get(severity, 0) }} |
{% endfor %}

### Top Vulnerability Categories

| Category | Occurrences |
|----------|-------------|
{% for category, count in statistics.top_categories.items() -%}
| {{ category }} | {{ count }} |
{% endfor %}

---

## Detailed Findings

### Critical Findings

{% if findings.by_severity.Critical %}
{% for finding in findings.by_severity.Critical %}
{{ _render_finding(finding, loop.index) }}
{% endfor %}
{% else %}
No critical findings detected.
{% endif %}

### High Severity Findings

{% if findings.by_severity.High %}
{% for finding in findings.by_severity.High %}
{{ _render_finding(finding, loop.index) }}
{% endfor %}
{% else %}
No high severity findings detected.
{% endif %}

### Medium Severity Findings

{% if findings.by_severity.Medium %}
{% for finding in findings.by_severity.Medium %}
{{ _render_finding(finding, loop.index) }}
{% endfor %}
{% else %}
No medium severity findings detected.
{% endif %}

### Low Severity Findings

{% if findings.by_severity.Low %}
{% for finding in findings.by_severity.Low %}
{{ _render_finding(finding, loop.index) }}
{% endfor %}
{% else %}
No low severity findings detected.
{% endif %}

---

## Cross-File Security Issues

{% if findings.cross_file %}
These vulnerabilities span multiple files, indicating potential systemic issues:

{% for finding in findings.cross_file %}
{{ _render_finding(finding, loop.index) }}
{% endfor %}
{% else %}
No cross-file security issues detected.
{% endif %}

---

## Remediation Roadmap

{% if executive_summary.roadmap %}
### Immediate Actions (0-30 days)
{% for action in executive_summary.roadmap.immediate %}
- {{ action }}
{% endfor %}

### Near-term Actions (1-3 months)
{% for action in executive_summary.roadmap.near_term %}
- {{ action }}
{% endfor %}

### Long-term Actions (3+ months)
{% for action in executive_summary.roadmap.long_term %}
- {{ action }}
{% endfor %}
{% endif %}

---

## Appendix

### Tools Used

| Tool | Findings Count |
|------|----------------|
{% for tool, count in statistics.tools_breakdown.items() -%}
| {{ tool }} | {{ count }} |
{% endfor %}

### Files Analyzed

{% for file_path, file_findings in findings.by_file.items() %}
- `{{ file_path }}`: {{ file_findings | length }} finding(s)
{% endfor %}

---

<div align="center">
<sub>Report generated by <strong>SecureCLI</strong> at {{ generated_at }}</sub>
</div>
"""
        
        # Custom template function to render individual findings
        def _render_finding(finding, index=None):
            return self.finding_template.render(finding=finding, index=index)
        
        template = Template(template_content)
        template.globals['_render_finding'] = _render_finding
        return template
    
    def _get_finding_template(self) -> Template:
        """Get finding template"""
        template_content = """
#### {% if index %}{{ index }}.{% endif %} {{ finding.title }}

**File:** `{{ finding.file }}:{{ finding.lines }}`  
**Severity:** {{ finding.severity }} | **CVSS v4.0:** {{ finding.cvss_v4.score }} ({{ finding.cvss_v4.vector }})

**Description:**  
{{ finding.description }}

**Impact:**  
{{ finding.impact }}

<details>
<summary><strong>Code Snippet</strong></summary>

```{{ finding.file.split('.')[-1] if '.' in finding.file else 'text' }}
{{ finding.snippet }}
```
</details>

<details>
<summary><strong>Recommendation</strong></summary>

{{ finding.recommendation }}

{% if finding.sample_fix %}
**Sample Fix:**
```{{ finding.file.split('.')[-1] if '.' in finding.file else 'text' }}
{{ finding.sample_fix }}
```
{% endif %}
</details>

{% if finding.poc %}
<details>
<summary><strong>Proof of Concept</strong></summary>

```
{{ finding.poc }}
```
</details>
{% endif %}

{% if finding.references %}
**References:**
{% for ref in finding.references %}
- {{ ref }}
{% endfor %}
{% endif %}

{% if finding.cross_file %}
<details>
<summary><strong>Cross-File Execution Traces ({{ finding.cross_file | length }})</strong></summary>

These traces show how this vulnerability connects across multiple files:

{% for trace in finding.cross_file %}
{{ loop.index }}. `{{ trace }}`
{% endfor %}
</details>
{% endif %}

{% if finding.tool_evidence %}
<details>
<summary><strong>Tool Evidence</strong></summary>

{% for evidence in finding.tool_evidence %}
- **{{ evidence.tool }}** ({{ evidence.id }})
{% endfor %}
</details>
{% endif %}

---
"""
        return Template(template_content)
    
    def _get_summary_template(self) -> Template:
        """Get summary report template"""
        template_content = """# Security Assessment Summary

**Repository:** `{{ metadata.repo_path }}`  
**Generated:** {{ generated_at }}

---

## Executive Summary

{% if executive_summary.heatmap %}
### Risk Distribution

| Severity | Count | Percentage |
|----------|-------|------------|
{% for severity, count in executive_summary.heatmap.items() -%}
| {{ severity }} | {{ count }} | {{ "%.1f"|format((count / (executive_summary.critical_count + executive_summary.high_count + executive_summary.medium_count + executive_summary.low_count) * 100) if (executive_summary.critical_count + executive_summary.high_count + executive_summary.medium_count + executive_summary.low_count) > 0 else 0) }}% |
{% endfor %}
{% endif %}

---

### Top Security Risks

{% for risk in executive_summary.top_risks %}
**{{ loop.index }}. {{ risk.title }}** ({{ risk.severity }})  
{{ risk.one_line }}  
*CVSS Score: {{ risk.cvss_v4.score }}*
{% endfor %}

---

### Key Security Themes

{% for theme in executive_summary.themes %}
- {{ theme }}
{% endfor %}

---

## Recommended Actions

{% if executive_summary.roadmap %}
### Immediate (0-30 days)
{% for action in executive_summary.roadmap.immediate %}
- {{ action }}
{% endfor %}

### Near-term (1-3 months)
{% for action in executive_summary.roadmap.near_term %}
- {{ action }}
{% endfor %}

### Long-term (3+ months)
{% for action in executive_summary.roadmap.long_term %}
- {{ action }}
{% endfor %}
{% endif %}

---

<div align="center">
<sub>Summary generated by <strong>SecureCLI</strong> at {{ generated_at }}</sub>
</div>
"""
        return Template(template_content)