"""
Mermaid diagram generator for SecureCLI reports
Creates visual diagrams for security findings and architecture
"""

from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime
from pathlib import Path

try:
    import matplotlib.pyplot as plt  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    plt = None

from ..schemas.findings import Finding


class MermaidDiagramGenerator:
    """Generates Mermaid diagrams for security visualization"""
    
    def __init__(self):
        self.colors = {
            "Critical": "#d73027",
            "High": "#f46d43", 
            "Medium": "#fdae61",
            "Low": "#abd9e9",
            "None": "#74add1"
        }
    
    def generate_severity_chart(self, findings: List[Finding]) -> str:
        """Generate pie chart showing severity distribution"""
        
        # Count by severity
        severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
        
        for finding in findings:
            if finding.severity in severity_counts:
                severity_counts[finding.severity] += 1
        
        # Generate Mermaid pie chart
        chart_data = []
        for severity, count in severity_counts.items():
            if count > 0:
                chart_data.append(f'    "{severity}" : {count}')
        
        if not chart_data:
            return "```mermaid\npie title No Findings\n    \"No Issues\" : 1\n```"
        
        mermaid = "```mermaid\n"
        mermaid += "pie title Security Findings by Severity\n"
        mermaid += "\n".join(chart_data)
        mermaid += "\n```"
        
        return mermaid
    
    def generate_file_heatmap(self, findings: List[Finding]) -> str:
        """Generate minimalist bar chart showing files with most findings"""
        
        # Count findings per file
        file_counts = defaultdict(int)
        for finding in findings:
            file_counts[finding.file] += 1
        
        if not file_counts:
            return "```mermaid\nchart LR\n    title No Files Analyzed\n```"
        
        # Sort files by finding count (top 10)
        top_files = sorted(file_counts.items(), key=lambda x: x[1], reverse=True)[:10]
        mermaid_lines = [
            "```mermaid",
            "%%{init: {'theme': 'neutral'}}%%",
            "chart LR",
            "    title Top Files by Findings",
            "    x-axis Findings",
            "    y-axis Files",
            "    bar"
        ]
        
        for file_path, count in top_files:
            display_name = self._shorten_path(file_path)
            label = display_name.replace('"', "'")
            mermaid_lines.append(f"        \"{label}\" : {count}")
        
        mermaid_lines.append("```")
        
        return "\n".join(mermaid_lines)

    def generate_severity_chart_image(
        self,
        findings: List[Finding],
        output_dir: Path,
        timestamp: str,
    ) -> Optional[Path]:
        """Create a static bar chart of severity distribution if matplotlib is available."""

        if plt is None:
            return None

        severity_order = ["Critical", "High", "Medium", "Low"]
        severity_counts = {severity: 0 for severity in severity_order}

        for finding in findings:
            if finding.severity in severity_counts:
                severity_counts[finding.severity] += 1

        categories = [severity for severity in severity_order if severity_counts[severity] > 0]
        if not categories:
            return None

        counts = [severity_counts[severity] for severity in categories]
        colors = [self.colors.get(severity, "#888888") for severity in categories]

        fig, ax = plt.subplots(figsize=(6, 3.5))
        ax.barh(categories, counts, color=colors)
        ax.set_xlabel("Findings")
        ax.set_ylabel("Severity")
        ax.set_title("Security Findings by Severity")
        ax.set_xlim(0, max(counts) * 1.1)

        for index, value in enumerate(counts):
            ax.text(value + max(counts) * 0.02, index, str(value), va="center", fontsize=10, color="#333333")

        fig.tight_layout()
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / f"severity_distribution_{timestamp}.png"
        fig.savefig(image_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return image_path

    def generate_file_heatmap_image(
        self,
        findings: List[Finding],
        output_dir: Path,
        timestamp: str,
    ) -> Optional[Path]:
        """Create a horizontal bar chart of file hotspots if matplotlib is available."""

        if plt is None:
            return None

        file_counts = defaultdict(int)
        file_severities: Dict[str, List[str]] = defaultdict(list)

        for finding in findings:
            file_path = finding.file or "Unknown"
            file_counts[file_path] += 1
            file_severities[file_path].append(finding.severity)

        if not file_counts:
            return None

        top_files = sorted(file_counts.items(), key=lambda item: item[1], reverse=True)[:10]
        labels = [self._shorten_path(path, max_length=45) for path, _ in top_files]
        counts = [count for _, count in top_files]

        colors = []
        for path, _ in top_files:
            severities = file_severities[path]
            max_severity = self._get_max_severity(severities)
            colors.append(self.colors.get(max_severity, "#888888"))

        fig, ax = plt.subplots(figsize=(7.5, 4.5))
        y_positions = list(range(len(top_files)))[::-1]
        ax.barh(y_positions, counts, color=colors)
        ax.set_yticks(y_positions)
        ax.set_yticklabels(labels)
        ax.set_xlabel("Findings")
        ax.set_title("Top Files by Security Findings")
        ax.set_xlim(0, max(counts) * 1.1)

        for idx, value in enumerate(counts):
            ax.text(value + max(counts) * 0.02, len(top_files) - idx - 1, str(value), va="center", fontsize=9, color="#333333")

        fig.tight_layout()
        output_dir.mkdir(parents=True, exist_ok=True)
        image_path = output_dir / f"file_hotspots_{timestamp}.png"
        fig.savefig(image_path, dpi=150, bbox_inches="tight")
        plt.close(fig)

        return image_path

    def generate_static_images(
        self,
        findings: List[Finding],
        output_dir: Path,
        timestamp: str,
    ) -> Dict[str, Path]:
        """Generate static chart images when matplotlib is installed."""

        if plt is None:
            return {}

        artifacts: Dict[str, Path] = {}

        severity_path = self.generate_severity_chart_image(findings, output_dir, timestamp)
        if severity_path:
            artifacts["severity_distribution_image"] = severity_path

        hotspot_path = self.generate_file_heatmap_image(findings, output_dir, timestamp)
        if hotspot_path:
            artifacts["file_hotspots_image"] = hotspot_path

        return artifacts
    
    def generate_attack_flow(self, findings: List[Finding]) -> str:
        """Generate attack flow diagram based on findings"""
        
        # Categorize findings by attack phase
        attack_phases = {
            "reconnaissance": [],
            "initial_access": [],
            "execution": [],
            "persistence": [],
            "privilege_escalation": [],
            "defense_evasion": [],
            "credential_access": [],
            "discovery": [],
            "lateral_movement": [],
            "collection": [],
            "exfiltration": [],
            "impact": []
        }
        
        # Map findings to attack phases based on vulnerability types
        for finding in findings:
            phase = self._map_to_attack_phase(finding)
            attack_phases[phase].append(finding)
        
        # Generate flow diagram
        mermaid = "```mermaid\n"
        mermaid += "flowchart LR\n"
        
        # Define main flow
        phases_with_findings = [
            phase for phase, findings_list in attack_phases.items() 
            if findings_list
        ]
        
        if not phases_with_findings:
            return "```mermaid\nflowchart LR\n    A[No Attack Vectors Identified]\n```"
        
        # Create main flow
        for i, phase in enumerate(phases_with_findings):
            phase_display = phase.replace('_', ' ').title()
            node_id = f"P{i}"
            count = len(attack_phases[phase])
            
            mermaid += f"    {node_id}[{phase_display}<br/>{count} issues]\n"
            
            if i > 0:
                prev_node = f"P{i-1}"
                mermaid += f"    {prev_node} --> {node_id}\n"
        
        # Add severity coloring
        for i, phase in enumerate(phases_with_findings):
            node_id = f"P{i}"
            max_severity = self._get_max_severity([f.severity for f in attack_phases[phase]])
            color_class = self._severity_to_class(max_severity)
            mermaid += f"    class {node_id} {color_class}\n"
        
        # Add CSS classes
        mermaid += "\n    classDef critical fill:#d73027,stroke:#333,stroke-width:2px,color:#fff\n"
        mermaid += "    classDef high fill:#f46d43,stroke:#333,stroke-width:2px,color:#fff\n"
        mermaid += "    classDef medium fill:#fdae61,stroke:#333,stroke-width:2px\n"
        mermaid += "    classDef low fill:#abd9e9,stroke:#333,stroke-width:2px\n"
        
        mermaid += "\n```"
        
        return mermaid
    
    def generate_technology_stack(self, metadata: Dict[str, Any]) -> str:
        """Generate technology stack diagram"""
        
        technologies = metadata.get('technologies', {})
        
        if not technologies:
            return "```mermaid\nflowchart TD\n    A[Technology Stack Unknown]\n```"
        
        mermaid = "```mermaid\n"
        mermaid += "flowchart TD\n"
        mermaid += "    App[Application]\n"
        
        # Frontend technologies
        frontend = technologies.get('frontend', [])
        if frontend:
            mermaid += "    App --> FE[Frontend]\n"
            for i, tech in enumerate(frontend):
                mermaid += f"    FE --> FE{i}[{tech}]\n"
        
        # Backend technologies
        backend = technologies.get('backend', [])
        if backend:
            mermaid += "    App --> BE[Backend]\n"
            for i, tech in enumerate(backend):
                mermaid += f"    BE --> BE{i}[{tech}]\n"
        
        # Database technologies
        databases = technologies.get('databases', [])
        if databases:
            mermaid += "    App --> DB[Databases]\n"
            for i, tech in enumerate(databases):
                mermaid += f"    DB --> DB{i}[{tech}]\n"
        
        # Infrastructure
        infrastructure = technologies.get('infrastructure', [])
        if infrastructure:
            mermaid += "    App --> INFRA[Infrastructure]\n"
            for i, tech in enumerate(infrastructure):
                mermaid += f"    INFRA --> INFRA{i}[{tech}]\n"
        
        mermaid += "\n```"
        
        return mermaid
    
    def generate_remediation_timeline(self, findings: List[Finding]) -> str:
        """Generate Gantt chart for remediation timeline"""
        
        # Group findings by severity for timeline
        severity_order = ["Critical", "High", "Medium", "Low"]
        
        mermaid = "```mermaid\n"
        mermaid += "gantt\n"
        mermaid += "    title Recommended Remediation Timeline\n"
        mermaid += "    dateFormat  YYYY-MM-DD\n"
        mermaid += "    axisFormat  %m/%d\n"
        
        # Calculate timeline based on severity
        base_date = datetime.now()
        
        timeline_items = []
        current_date = base_date
        
        for severity in severity_order:
            severity_findings = [f for f in findings if f.severity == severity]
            if not severity_findings:
                continue
            
            # Calculate duration based on severity and count
            count = len(severity_findings)
            if severity == "Critical":
                days = min(1, count)  # Immediate
                priority = "crit"
            elif severity == "High":
                days = min(7, count * 2)  # 1-7 days
                priority = "active"
            elif severity == "Medium":
                days = min(30, count * 3)  # 1-30 days
                priority = ""
            else:  # Low
                days = min(90, count * 7)  # 1-90 days
                priority = ""
            
            start_date = current_date.strftime("%Y-%m-%d")
            current_date = current_date + timedelta(days=days)
            end_date = current_date.strftime("%Y-%m-%d")
            
            section_name = f"{severity} Priority ({count} issues)"
            task_name = f"Fix {severity.lower()} issues"
            
            mermaid += f"\n    section {section_name}\n"
            if priority:
                mermaid += f"    {task_name} :{priority}, {start_date}, {end_date}\n"
            else:
                mermaid += f"    {task_name} :{start_date}, {end_date}\n"
        
        mermaid += "\n```"
        
        return mermaid
    
    def generate_owasp_mapping(self, findings: List[Finding]) -> str:
        """Generate OWASP Top 10 mapping diagram"""
        
        # Count findings by OWASP category
        owasp_counts = defaultdict(int)
        
        for finding in findings:
            for owasp in finding.owasp:
                owasp_counts[owasp] += 1
        
        if not owasp_counts:
            return "```mermaid\nflowchart TD\n    A[No OWASP Mappings Found]\n```"
        
        mermaid = "```mermaid\n"
        mermaid += "mindmap\n"
        mermaid += "  root((OWASP Top 10))\n"
        
        # Sort by count
        sorted_owasp = sorted(owasp_counts.items(), key=lambda x: x[1], reverse=True)
        
        for owasp, count in sorted_owasp:
            # Clean up OWASP category name
            clean_name = owasp.replace("OWASP-", "").replace("-", " ")
            mermaid += f"    {clean_name}\n"
            mermaid += f"      {count} issues\n"
        
        mermaid += "\n```"
        
        return mermaid
    
    def _map_to_attack_phase(self, finding: Finding) -> str:
        """Map finding to MITRE ATT&CK phase"""
        
        title_lower = finding.title.lower()
        desc_lower = finding.description.lower()
        text = f"{title_lower} {desc_lower}"
        
        # Simple mapping based on keywords
        if any(word in text for word in ["information", "disclosure", "debug", "error"]):
            return "reconnaissance"
        elif any(word in text for word in ["injection", "upload", "deserialization"]):
            return "initial_access"
        elif any(word in text for word in ["command", "exec", "system", "shell"]):
            return "execution"
        elif any(word in text for word in ["backdoor", "persistence", "startup"]):
            return "persistence"
        elif any(word in text for word in ["privilege", "escalation", "admin", "root"]):
            return "privilege_escalation"
        elif any(word in text for word in ["bypass", "evasion", "disable"]):
            return "defense_evasion"
        elif any(word in text for word in ["credential", "password", "token", "key"]):
            return "credential_access"
        elif any(word in text for word in ["enumeration", "discovery", "scan"]):
            return "discovery"
        elif any(word in text for word in ["lateral", "movement", "pivot"]):
            return "lateral_movement"
        elif any(word in text for word in ["collection", "harvest", "gather"]):
            return "collection"
        elif any(word in text for word in ["exfiltration", "data", "transfer"]):
            return "exfiltration"
        elif any(word in text for word in ["impact", "destruction", "denial"]):
            return "impact"
        else:
            return "initial_access"  # Default
    
    def _get_max_severity(self, severities: List[str]) -> str:
        """Get maximum severity from list"""
        severity_order = ["Critical", "High", "Medium", "Low", "None"]
        
        for severity in severity_order:
            if severity in severities:
                return severity
        
        return "Low"
    
    def _severity_to_class(self, severity: str) -> str:
        """Convert severity to CSS class name"""
        return severity.lower()
    
    def _shorten_path(self, path: str, max_length: int = 30) -> str:
        """Shorten file path for display"""
        if len(path) <= max_length:
            return path
        
        # Try to keep last two path components for context
        parts = [part for part in path.split('/') if part]
        if len(parts) >= 2:
            last_two = "/".join(parts[-2:])
            if len(last_two) <= max_length - 4:
                return f".../{last_two}"
        if parts:
            filename = parts[-1]
            if len(filename) <= max_length - 3:
                return f".../{filename}"
        
        # Truncate from beginning
        return "..." + path[-(max_length-3):]


# Import timedelta for timeline generation
from datetime import timedelta