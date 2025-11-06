"""
Output formatters for SecureCLI
Handles formatting of command output and results
"""

import json
from typing import Dict, List, Any, Optional
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.syntax import Syntax
from rich.tree import Tree
from rich.text import Text
from rich.box import ROUNDED


class OutputFormatter:
    """Handles formatting of output for the CLI"""
    
    def __init__(self, console: Console = None):
        self.console = console or Console()
    
    def format_findings(self, findings: List[Dict[str, Any]], format_type: str = "table") -> None:
        """Format and display security findings"""
        if not findings:
            self.console.print("[yellow]No findings to display[/yellow]")
            return
        
        if format_type == "table":
            self._format_findings_table(findings)
        elif format_type == "json":
            self._format_findings_json(findings)
        elif format_type == "summary":
            self._format_findings_summary(findings)
        else:
            self._format_findings_table(findings)
    
    def _format_findings_table(self, findings: List[Dict[str, Any]]) -> None:
        """Format findings as a clean table with proper wrapping"""
        table = Table(
            title="[bold red]Security Findings[/bold red]",
            show_header=True,
            header_style="bold cyan",
            box=ROUNDED,
            expand=False,
            show_lines=True
        )
        
        table.add_column("#", style="dim", width=4, justify="right")
        table.add_column("Severity", style="bold", width=10)
        table.add_column("Location", style="white", width=30)
        table.add_column("Issue", style="white", no_wrap=False)
        
        for i, finding in enumerate(findings, 1):
            severity = finding.get('severity', 'Unknown')
            severity_style = self._get_severity_style(severity)
            file_path = finding.get('file', 'Unknown')
            lines = finding.get('lines', '?')
            title = finding.get('title', 'Unknown')
            
            # Create location string
            location = f"{file_path}:{lines}"
            
            # Severity display with consistent styling
            severity_display = f"[{severity_style}]{severity}[/{severity_style}]"
            
            table.add_row(
                str(i),
                severity_display,
                location,
                title
            )
        
        self.console.print(table)
    
    def _format_findings_json(self, findings: List[Dict[str, Any]]) -> None:
        """Format findings as JSON"""
        json_output = json.dumps(findings, indent=2)
        syntax = Syntax(json_output, "json", theme="monokai", line_numbers=True)
        self.console.print(syntax)
    
    def _format_findings_summary(self, findings: List[Dict[str, Any]]) -> None:
        """Format findings as a clean summary"""
        severity_counts = {}
        for finding in findings:
            severity = finding.get('severity', 'Unknown')
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        # Create summary panel
        summary_text = Text()
        summary_text.append(f"Total Vulnerabilities: {len(findings)}\n\n", style="bold white")
        
        for severity in ["Critical", "High", "Medium", "Low", "Info"]:
            if severity in severity_counts:
                count = severity_counts[severity]
                style = self._get_severity_style(severity)
                summary_text.append(f"{severity:8} ", style=style)
                summary_text.append(f"{count:>3}\n", style="white")
        
        panel = Panel(
            summary_text,
            title="[bold red]Threat Assessment[/bold red]",
            border_style="red",
            box=ROUNDED,
            expand=False
        )
        self.console.print(panel)
    
    def _get_severity_style(self, severity: str) -> str:
        """Get Rich style for severity level"""
        severity_styles = {
            "Critical": "bold bright_red",
            "High": "bright_red",
            "Medium": "yellow",
            "Low": "green",
            "Info": "white"
        }
        return severity_styles.get(severity, "white")
    
    def format_status(self, status: Dict[str, Any]) -> None:
        """Format and display status information"""
        tree = Tree("[bold cyan]SecureCLI Status[/bold cyan]")
        
        for key, value in status.items():
            if isinstance(value, dict):
                branch = tree.add(f"[bold]{key}[/bold]")
                for sub_key, sub_value in value.items():
                    branch.add(f"{sub_key}: {sub_value}")
            else:
                tree.add(f"[bold]{key}[/bold]: {value}")
        
        self.console.print(tree)
    
    def format_error(self, error: str, details: Optional[str] = None) -> None:
        """Format and display error messages"""
        error_panel = Panel(
            f"[bold red]{error}[/bold red]\n{details if details else ''}",
            title="ERROR",
            border_style="red",
            box=ROUNDED,
            expand=False
        )
        self.console.print(error_panel)
    
    def format_success(self, message: str, details: Optional[str] = None) -> None:
        """Format and display success messages"""
        self.console.print(f"[bold green]SUCCESS[/bold green] {message}")
        if details:
            self.console.print(f"[dim]{details}[/dim]")
    
    def format_warning(self, message: str, details: Optional[str] = None) -> None:
        """Format and display warning messages"""
        self.console.print(f"[bold yellow]WARNING[/bold yellow] {message}")
        if details:
            self.console.print(f"[dim]{details}[/dim]")
    
    def format_info(self, message: str, details: Optional[str] = None) -> None:
        """Format and display info messages"""
        self.console.print(f"[bold cyan]INFO[/bold cyan] {message}")
        if details:
            self.console.print(f"[dim]{details}[/dim]")
    
    def format_code_snippet(self, code: str, language: str = "python", title: Optional[str] = None) -> None:
        """Format and display code snippets"""
        syntax = Syntax(code, language, theme="monokai", line_numbers=True)
        if title:
            panel = Panel(
                syntax,
                title=title,
                border_style="cyan",
                box=ROUNDED,
                expand=False
            )
            self.console.print(panel)
        else:
            self.console.print(syntax)
    
    def format_list(self, items: List[str], title: Optional[str] = None) -> None:
        """Format and display a list of items"""
        if title:
            self.console.print(f"\n[bold cyan]{title}:[/bold cyan]")
        
        for item in items:
            self.console.print(f"  - {item}")
        
        self.console.print()
    
    def format_progress(self, current: int, total: int, description: str = "") -> None:
        """Format and display progress information"""
        percentage = (current / total) * 100 if total > 0 else 0
        progress_text = f"Progress: {current}/{total} ({percentage:.1f}%)"
        if description:
            progress_text += f" - {description}"
        
        self.console.print(f"[bold blue]{progress_text}[/bold blue]")
    
    def format_detailed_finding(self, finding: Dict[str, Any], finding_number: int) -> None:
        """Format a single finding with full details"""
        severity = finding.get('severity', 'Unknown')
        severity_style = self._get_severity_style(severity)
        
        # Create header
        header_text = Text()
        header_text.append(f"Finding #{finding_number}: ", style="bold cyan")
        header_text.append(finding.get('title', 'Unknown'), style="bold white")
        
        # Create content
        content = Text()
        content.append(f"File: {finding.get('file', 'Unknown')}\n", style="white")
        content.append(f"Lines: {finding.get('lines', '?')}\n", style="white")
        content.append("Severity: ", style="white")
        content.append(severity, style=severity_style)
        content.append(f" (CVSS: {finding.get('cvss_score', 'N/A')})\n\n", style="white")
        
        content.append("Description:\n", style="bold white")
        content.append(f"{finding.get('description', 'No description available')}\n\n", style="dim white")
        
        if finding.get('recommendation'):
            content.append("Recommendation:\n", style="bold green")
            content.append(f"{finding.get('recommendation')}\n", style="dim white")
        
        panel = Panel(
            content,
            title=header_text,
            border_style=severity_style,
            box=ROUNDED,
            expand=False
        )
        self.console.print(panel)