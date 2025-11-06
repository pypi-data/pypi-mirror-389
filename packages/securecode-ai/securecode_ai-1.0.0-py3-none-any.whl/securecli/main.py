"""
SecureCLI - AI-Powered Secure Code Review Tool
Main entry point with GitHub repository analysis and universal language support
"""

import sys
import asyncio
import warnings
from pathlib import Path
from typing import Iterable, Optional, Sequence, Union

# Suppress all deprecation warnings for clean output
warnings.filterwarnings("ignore", category=DeprecationWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import click
from rich.console import Console

from .cli.repl import SecureREPL
from .config import ConfigManager
from .workspace import WorkspaceManager
from .modules import create_analysis_engine
from .report import ReportGenerator
from .analysis import annotate_cross_file_context
from .schemas.findings import Finding
from .github import analyze_github_repo_cli, validate_github_url
from .languages import analyze_project_languages


console = Console()


def _enrich_cross_file_context(
    findings: Iterable[Finding],
    repo_root: Union[str, Path],
    languages: Sequence[str],
    verbose: bool = False,
) -> None:
    """Augment findings with cross-file traces when Python code is detected."""

    findings_list = list(findings)
    if not findings_list or not languages:
        return

    language_set = {lang.lower() for lang in languages if isinstance(lang, str)}
    if "python" not in language_set:
        return

    root_path = Path(repo_root).resolve()
    if root_path.is_file():
        root_path = root_path.parent
    if not root_path.is_dir():
        return

    typed_findings = [f for f in findings_list if isinstance(f, Finding)]
    if not typed_findings:
        return

    files = sorted({f.file for f in typed_findings if getattr(f, "file", None)})
    if not files:
        return

    needs_enrichment = any(not getattr(f, "cross_file", None) for f in typed_findings)
    if not needs_enrichment:
        return

    try:
        annotate_cross_file_context(root_path, typed_findings, files=files)
        if verbose:
            console.print("[dim]Cross-file context enriched for Python findings[/dim]")
    except Exception as exc:
        if verbose:
            console.print(f"[dim]Cross-file enrichment skipped: {exc}[/dim]")


@click.command()
@click.option("--workspace", "-w", help="Workspace to use")
@click.option("--config", "-c", help="Configuration file path")
@click.option("--repo", "-r", help="Repository path to analyze")
@click.option("--github-url", "-g", help="GitHub repository URL to analyze")
@click.option("--branch", "-b", default="main", help="Git branch to analyze (default: main)")
@click.option("--scan-mode", default="comprehensive", help="Scan mode: quick, comprehensive, deep")
@click.option("--non-interactive", is_flag=True, help="Run in CI/headless mode")
@click.option("--script", "-s", help="Script file to execute")
@click.option("--changed-files", is_flag=True, help="Analyze only changed files (Git)")
@click.option("--format", default="md", help="Output format (md, json, sarif)")
@click.option("--output", "-o", help="Output file path")
@click.option("--severity-min", default="medium", help="Minimum severity (low, medium, high, critical)")
@click.option("--profile", multiple=True, help="Domain profiles to use")
@click.option("--languages", is_flag=True, help="Show detected languages and exit")
@click.option("--file-by-file", is_flag=True, help="Generate file-by-file analysis report")
@click.option("--show-all-findings", is_flag=True, help="Show all findings (not just critical/high)")
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
def main(
    workspace: Optional[str] = None,
    config: Optional[str] = None,
    repo: Optional[str] = None,
    github_url: Optional[str] = None,
    branch: str = "main",
    scan_mode: str = "comprehensive",
    non_interactive: bool = False,
    script: Optional[str] = None,
    changed_files: bool = False,
    format: str = "md",
    output: Optional[str] = None,
    severity_min: str = "medium",
    profile: tuple = (),
    languages: bool = False,
    file_by_file: bool = False,
    show_all_findings: bool = False,
    verbose: bool = False,
) -> None:
    """SecureCLI - AI-Powered Secure Code Review Tool with GitHub Integration"""
    
    try:
        # Initialize configuration
        config_manager = ConfigManager(config_path=config)
        
        # Handle GitHub repository analysis
        if github_url:
            if not validate_github_url(github_url):
                console.print(f"[red]Error: Invalid GitHub URL: {github_url}[/red]")
                sys.exit(1)
            
            console.print(f"[green]Analyzing GitHub repository: {github_url}[/green]")
            return asyncio.run(run_github_analysis(
                github_url=github_url,
                branch=branch,
                scan_mode=scan_mode,
                config_manager=config_manager,
                format=format,
                output=output,
                severity_min=severity_min,
                profile=profile,
                file_by_file=file_by_file,
                show_all_findings=show_all_findings,
                verbose=verbose,
            ))
        
        # Handle language detection only
        if languages:
            target_path = repo or "."
            return run_language_analysis(target_path, verbose)
        
        # Initialize workspace
        workspace_manager = WorkspaceManager()
        if workspace:
            workspace_manager.use_workspace(workspace)
        
        if non_interactive:
            # CI/Headless mode
            return run_ci_mode(
                config_manager=config_manager,
                workspace_manager=workspace_manager,
                repo=repo,
                changed_files=changed_files,
                format=format,
                output=output,
                severity_min=severity_min,
                profile=profile,
                verbose=verbose,
            )
        
        # Interactive REPL mode
        repl = SecureREPL(
            config_manager=config_manager,
            workspace_manager=workspace_manager,
        )
        
        # Set initial values if provided
        if repo:
            repl.set_option("repo.path", repo)
        if profile:
            repl.set_option("domain.profiles", list(profile))
        if severity_min:
            repl.set_option("severity_min", severity_min)
        
        # Execute script if provided
        if script:
            repl.execute_script(script)
        else:
            # Start interactive session
            asyncio.run(repl.run())
            
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted by user[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


async def run_github_analysis(
    github_url: str,
    branch: str,
    scan_mode: str,
    config_manager: ConfigManager,
    format: str,
    output: Optional[str],
    severity_min: str,
    profile: tuple,
    file_by_file: bool,
    show_all_findings: bool,
    verbose: bool,
) -> None:
    """Run analysis on GitHub repository"""
    
    console.print(f"[blue]Starting GitHub repository analysis...[/blue]")
    console.print(f"Repository: {github_url}")
    console.print(f"Branch: {branch}")
    console.print(f"Scan Mode: {scan_mode}")
    
    try:
        # Get configuration
        config = config_manager.get_all()
        
        # Perform GitHub analysis
        results = await analyze_github_repo_cli(
            repo_url=github_url,
            config=config,
            branch=branch,
            scan_mode=scan_mode,
            target_paths=None,
            exclude_paths=None
        )
        
        # Display summary
        console.print(f"\n[green]Analysis completed![/green]")
        console.print(f"Total findings: {len(results['findings'])}")
        console.print(f"Files analyzed: {results['repository']['analyzed_files']}")
        console.print(f"Languages detected: {', '.join(results['repository']['languages_detected'])}")
        
        # Show severity breakdown
        severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
        for finding in results['findings']:
            severity_counts[finding.severity.lower()] += 1
        
        console.print(f"\nSeverity Breakdown:")
        console.print(f"  Critical: {severity_counts['critical']}")
        console.print(f"  High: {severity_counts['high']}")
        console.print(f"  Medium: {severity_counts['medium']}")
        console.print(f"  Low: {severity_counts['low']}")
        
        # File-by-file analysis
        if file_by_file and 'file_analysis' in results:
            console.print(f"\n[blue]File-by-File Analysis:[/blue]")
            for file_path, analysis in results['file_analysis'].items():
                console.print(f"  {file_path} ({analysis['language']}) - {analysis['findings_count']} findings")
        
        # Save results if output specified
        if output:
            output_path = Path(output)
            if format == 'json':
                import json
                output_path.write_text(json.dumps(results, indent=2, default=str))
                console.print(f"Results saved to: {output_path}")
            elif format == 'sarif':
                # SARIF format would need additional conversion
                console.print("[yellow]SARIF format not yet implemented for GitHub analysis[/yellow]")
            else:
                # Markdown format (default)
                if results.get('reports'):
                    md_report = results['reports'].get('markdown')
                    if md_report:
                        import shutil
                        shutil.copy2(md_report, output_path)
                        console.print(f"Report saved to: {output_path}")
        
        # Show comprehensive vulnerability details
        if results['findings']:
            total_findings = len(results['findings'])
            console.print(f"\n[red]Security Issues Found ({total_findings} total):[/red]")
            
            # Show all findings by severity
            for severity in ['critical', 'high', 'medium', 'low']:
                severity_findings = [f for f in results['findings'] 
                                   if f.severity.lower() == severity]
                
                if severity_findings:
                    severity_color = {
                        'critical': 'bright_red',
                        'high': 'red', 
                        'medium': 'yellow',
                        'low': 'blue'
                    }.get(severity, 'white')
                    
                    console.print(f"\n[{severity_color}]{severity.upper()} SEVERITY ({len(severity_findings)} issues):[/{severity_color}]")
                    
                    # Determine how many findings to show based on flags
                    if show_all_findings:
                        # Show all findings when flag is set
                        display_count = len(severity_findings)
                    else:
                        # Default: Show all critical/high, top 10 for medium/low
                        display_count = len(severity_findings) if severity in ['critical', 'high'] else min(10, len(severity_findings))
                    
                    for i, finding in enumerate(severity_findings[:display_count], 1):
                        # Extract file name and line info
                        file_path = finding.file
                        file_name = file_path.split('/')[-1] if file_path else 'Unknown'
                        line_info = f" (Line {finding.lines})" if hasattr(finding, 'lines') and finding.lines != '0' else ""
                        
                        # Show finding with better formatting
                        console.print(f"  {i:2d}. [{severity_color}]{finding.title}[/{severity_color}]")
                        console.print(f"      File: {file_name}{line_info}")
                        
                        # Show which tool found this issue
                        if hasattr(finding, 'tool_evidence') and finding.tool_evidence:
                            tools = [evidence.tool for evidence in finding.tool_evidence]
                            tools_str = ", ".join(set(tools))
                            console.print(f"      Tool: {tools_str}")
                        
                        # Show recommendation if available
                        if hasattr(finding, 'recommendation') and finding.recommendation:
                            rec_short = finding.recommendation[:100] + "..." if len(finding.recommendation) > 100 else finding.recommendation
                            console.print(f"      Fix: {rec_short}")
                        
                        # Show impact if available  
                        if hasattr(finding, 'impact') and finding.impact:
                            impact_short = finding.impact[:80] + "..." if len(finding.impact) > 80 else finding.impact
                            console.print(f"      Impact: {impact_short}")
                        
                        console.print()  # Empty line between findings
                    
                    # Show truncation message if there are more findings
                    if len(severity_findings) > display_count:
                        remaining = len(severity_findings) - display_count
                        console.print(f"      ... and {remaining} more {severity} severity issues")
                        console.print()
            
            # Summary with actionable advice and tool info
            critical_count = len([f for f in results['findings'] if f.severity.lower() == 'critical'])
            high_count = len([f for f in results['findings'] if f.severity.lower() == 'high'])
            
            # Show which tools were used
            all_tools = set()
            for finding in results['findings']:
                if hasattr(finding, 'tool_evidence') and finding.tool_evidence:
                    for evidence in finding.tool_evidence:
                        all_tools.add(evidence.tool)
            
            if all_tools:
                console.print(f"\n[blue]🔧 Security tools used: {', '.join(sorted(all_tools))}[/blue]")
            
            if critical_count > 0:
                console.print(f"[bright_red]🚨 URGENT: {critical_count} critical vulnerabilities require immediate attention![/bright_red]")
            if high_count > 0:
                console.print(f"[red]⚠️  {high_count} high-severity issues should be addressed within 7 days[/red]")
            
            help_msg = "[blue]💡 Use --output results.json to save detailed findings, --file-by-file for per-file analysis"
            if not show_all_findings:
                help_msg += ", or --show-all-findings to see all issues"
            help_msg += "[/blue]"
            console.print(f"\n{help_msg}")
        
    except Exception as e:
        console.print(f"[red]Error during GitHub analysis: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


def run_language_analysis(target_path: str, verbose: bool) -> None:
    """Run language detection analysis"""
    
    console.print(f"[blue]Analyzing languages in: {target_path}[/blue]")
    
    try:
        # Analyze project languages
        analysis = analyze_project_languages(target_path)
        
        console.print(f"\n[green]Language Analysis Results:[/green]")
        console.print(f"Total files: {analysis['total_files']}")
        console.print(f"Languages detected: {analysis['languages_detected']}")
        console.print(f"Primary language: {analysis['primary_language']}")
        
        # Show language breakdown
        console.print(f"\n[blue]Language Breakdown:[/blue]")
        for lang, stats in analysis['language_breakdown'].items():
            percentage = stats['percentage']
            files = stats['files']
            console.print(f"  {lang}: {files} files ({percentage:.1f}%)")
        
        # Show security-priority languages
        if analysis['security_priority_languages']:
            console.print(f"\n[red]High Security Priority Languages:[/red]")
            for lang in analysis['security_priority_languages']:
                console.print(f"  - {lang}")
        
        # Show Web3 languages
        if analysis['web3_languages']:
            console.print(f"\n[yellow]Web3/Blockchain Languages:[/yellow]")
            for lang in analysis['web3_languages']:
                console.print(f"  - {lang}")
        
        # Show recommended tools
        console.print(f"\n[cyan]Recommended Security Tools:[/cyan]")
        for tool in analysis['recommended_tools']:
            console.print(f"  - {tool}")
        
        if verbose:
            console.print(f"\n[dim]Detailed breakdown available in analysis object[/dim]")
        
    except Exception as e:
        console.print(f"[red]Error during language analysis: {e}[/red]")
        if verbose:
            import traceback
            console.print(f"[dim]{traceback.format_exc()}[/dim]")
        sys.exit(1)


def run_ci_mode(
    config_manager,
    workspace_manager,
    repo: Optional[str],
    changed_files: bool,
    format: str,
    output: Optional[str],
    severity_min: str,
    profile: tuple,
    verbose: bool,
) -> None:
    """Run in CI/headless mode"""
    console.print("[blue]Running SecureCLI in CI mode...[/blue]")
    
    try:
        # Auto-detect repository if not provided
        if not repo:
            repo = str(Path.cwd())
            console.print(f"[yellow]Auto-detected repository: {repo}[/yellow]")
        
        repo_path = Path(repo)
        if not repo_path.exists():
            console.print(f"[red]Repository path does not exist: {repo}[/red]")
            sys.exit(1)
        
        # Get all files to analyze
        if changed_files:
            # TODO: Implement git diff logic to get only changed files
            console.print("[yellow]Changed files analysis not yet implemented, analyzing all files[/yellow]")
        
        # Find all source files
        file_patterns = ['*.py', '*.js', '*.jsx', '*.ts', '*.tsx', '*.sol', '*.vy', '*.go', '*.java', '*.jsp', '*.php', '*.rb', '*.cs', '*.razor', '*.rs', '*.toml', '*.cpp', '*.c', '*.cc', '*.cxx', '*.h', '*.hpp']
        all_files = []
        
        for pattern in file_patterns:
            files = list(repo_path.rglob(pattern))
            # Filter out common ignore patterns
            filtered_files = [
                str(f) for f in files 
                if not any(ignore in str(f) for ignore in [
                    'node_modules', '.git', '__pycache__', '.venv', 'venv', 
                    'dist', 'build', '.tox', 'coverage'
                ])
            ]
            all_files.extend(filtered_files)
        
        if not all_files:
            console.print("[yellow]No source files found to analyze[/yellow]")
            return
        
        console.print(f"[green]Found {len(all_files)} files to analyze[/green]")
        
        # Run analysis using the module system
        asyncio.run(_run_analysis(
            config_manager=config_manager,
            repo_path=str(repo_path),
            file_list=all_files,
            format=format,
            output=output,
            severity_min=severity_min,
            profile=profile,
            verbose=verbose
        ))
        
    except Exception as e:
        console.print(f"[red]CI mode failed: {e}[/red]")
        if verbose:
            console.print_exception()
        sys.exit(1)


def _calculate_ci_statistics(findings):
    """Calculate CI statistics from findings"""
    if not findings:
        return {
            'total_findings': 0,
            'by_severity': {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0},
            'files_affected': 0,
            'avg_cvss_score': 0.0,
            'categories': {},
            'tools': {}
        }
    
    # Count by severity
    severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0}
    for finding in findings:
        severity = getattr(finding, 'severity', 'Low').title()
        if severity in severity_counts:
            severity_counts[severity] += 1
    
    # Count unique files affected
    files_affected = len(set(getattr(f, 'file', '') for f in findings if getattr(f, 'file', '')))
    
    # Count by categories
    categories = {}
    for finding in findings:
        category = getattr(finding, 'category', 'Unknown')
        categories[category] = categories.get(category, 0) + 1
    
    # Count by tools
    tools = {}
    for finding in findings:
        tool = getattr(finding, 'tool', 'Unknown')
        tools[tool] = tools.get(tool, 0) + 1
    
    return {
        'total_findings': len(findings),
        'by_severity': severity_counts,
        'files_affected': files_affected,
        'avg_cvss_score': 0.0,  # TODO: Calculate from CVSS scores if available
        'categories': categories,
        'tools': tools
    }


async def _run_analysis(
    config_manager,
    repo_path: str,
    file_list: list,
    format: str,
    output: Optional[str],
    severity_min: str,
    profile: tuple,
    verbose: bool
):
    """Run the actual security analysis using working security tools"""
    
    config = config_manager.get_all()
    scan_mode = config.get('ci.scan_mode', 'comprehensive')
    
    console.print(f"[blue]Starting {scan_mode} security analysis...[/blue]")
    
    # Use our working security tools implementation instead of broken module system
    try:
        from .tools import BanditTool, SemgrepTool, GitleaksTool, SlitherTool, NpmAuditTool, CppTool, RustTool, JavaTool, RubyTool, GoTool, CSharpTool
        from .languages import analyze_project_languages
        
        # Language detection for target selection
        if verbose:
            console.print("[dim]Analyzing project languages...[/dim]")
        
        lang_analysis = analyze_project_languages(repo_path)
        language_breakdown = lang_analysis.get('language_breakdown', {})
        languages = list(language_breakdown.keys()) if language_breakdown else []
        
        if verbose:
            console.print(f"[dim]Detected languages: {', '.join(languages) if languages else 'None'}[/dim]")
        
        # Initialize available tools based on languages
        available_tools = []
        smart_contract_languages = ['solidity', 'vyper', 'cairo', 'move']
        web_languages = ['javascript', 'typescript', 'python', 'java', 'go', 'rust', 'php', 'ruby']
        
        has_smart_contracts = any(lang in languages for lang in smart_contract_languages)
        has_web_code = any(lang in languages for lang in web_languages)
        
        # Python security scanning
        if 'python' in languages and BanditTool:
            try:
                bandit = BanditTool(config)
                if bandit.is_available():
                    available_tools.append(('Bandit', bandit))
                    if verbose:
                        console.print("[dim]✓ Bandit (Python security) - Available[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ Bandit - Configuration error: {e}[/dim]")
        
        # JavaScript/Node.js security scanning
        if any(lang in languages for lang in ['javascript', 'typescript']) and NpmAuditTool:
            try:
                npm_audit = NpmAuditTool(config)
                if npm_audit.is_available():
                    available_tools.append(('NPM Audit', npm_audit))
                    if verbose:
                        console.print("[dim]✓ NPM Audit (JS/TS security) - Available[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ NPM Audit - Configuration error: {e}[/dim]")
        
        # C/C++ security scanning
        if any(lang in languages for lang in ['cpp', 'c++', 'c', 'cc', 'cxx']) and CppTool:
            try:
                cpp_analyzer = CppTool(config)
                if cpp_analyzer.is_available():
                    available_tools.append(('C++ Analyzer', cpp_analyzer))
                    if verbose:
                        console.print("[dim]✓ C++ Analyzer (Clang/CppCheck) - Available[/dim]")
                else:
                    if verbose:
                        console.print("[dim]✗ C++ Analyzer - Not available (install clang-tidy, cppcheck)[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ C++ Analyzer - Configuration error: {e}[/dim]")
        
        # Rust security scanning  
        if 'rust' in languages and RustTool:
            try:
                rust_analyzer = RustTool(config)
                if rust_analyzer.is_available():
                    available_tools.append(('Rust Analyzer', rust_analyzer))
                    if verbose:
                        console.print("[dim]✓ Rust Analyzer (Clippy/Cargo Audit) - Available[/dim]")
                else:
                    if verbose:
                        console.print("[dim]✗ Rust Analyzer - Not available (run: source ~/.cargo/env)[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ Rust Analyzer - Configuration error: {e}[/dim]")
        
        # Java security scanning
        if 'java' in languages and JavaTool:
            try:
                java_analyzer = JavaTool(config)
                if java_analyzer.is_available():
                    available_tools.append(('Java Analyzer', java_analyzer))
                    if verbose:
                        console.print("[dim]✓ Java Analyzer (SpotBugs/PMD/Find Security Bugs) - Available[/dim]")
                else:
                    if verbose:
                        console.print("[dim]✗ Java Analyzer - Not available (check spotbugs, pmd installation)[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ Java Analyzer - Configuration error: {e}[/dim]")
        
        # Ruby security scanning
        if 'ruby' in languages and RubyTool:
            try:
                ruby_analyzer = RubyTool(config)
                if ruby_analyzer.is_available():
                    available_tools.append(('Ruby Analyzer', ruby_analyzer))
                    if verbose:
                        console.print("[dim]✓ Ruby Analyzer (Brakeman/RuboCop/bundler-audit) - Available[/dim]")
                else:
                    if verbose:
                        console.print("[dim]✗ Ruby Analyzer - Not available (gems not installed)[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ Ruby Analyzer - Configuration error: {e}[/dim]")
        
        # Go security scanning
        if 'go' in languages and GoTool:
            try:
                go_analyzer = GoTool(config)
                if go_analyzer.is_available():
                    available_tools.append(('Go Analyzer', go_analyzer))
                    if verbose:
                        console.print("[dim]✓ Go Analyzer (Gosec/Staticcheck/Go-critic) - Available[/dim]")
                else:
                    if verbose:
                        console.print("[dim]✗ Go Analyzer - Not available (run: export PATH=$PATH:~/go/bin)[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ Go Analyzer - Configuration error: {e}[/dim]")
        
        # C#/.NET security scanning
        if any(lang in languages for lang in ['csharp', 'c#', 'dotnet']) and CSharpTool:
            try:
                csharp_analyzer = CSharpTool(config)
                if csharp_analyzer.is_available():
                    available_tools.append(('C# Analyzer', csharp_analyzer))
                    if verbose:
                        console.print("[dim]✓ C# Analyzer (DevSkim/Roslyn Analyzers) - Available[/dim]")
                else:
                    if verbose:
                        console.print("[dim]✗ C# Analyzer - Not available (install DevSkim)[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ C# Analyzer - Configuration error: {e}[/dim]")
        
        # Smart contract security scanning - ONLY for blockchain code
        if has_smart_contracts and SlitherTool:
            try:
                slither = SlitherTool(config)
                if slither.is_available():
                    available_tools.append(('Slither', slither))
                    if verbose:
                        console.print("[dim]✓ Slither (Solidity security) - Available[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ Slither - Configuration error: {e}[/dim]")
        
        # Universal secret detection (works for any codebase)
        if GitleaksTool:
            try:
                gitleaks = GitleaksTool(config)
                if gitleaks.is_available():
                    available_tools.append(('Gitleaks', gitleaks))
                    if verbose:
                        console.print("[dim]✓ Gitleaks (Secrets detection) - Available[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ Gitleaks - Configuration error: {e}[/dim]")
        
        # Semgrep for multi-language analysis (exclude if only smart contracts)
        if SemgrepTool and (has_web_code or scan_mode in ['deep', 'comprehensive']):
            try:
                semgrep = SemgrepTool(config)
                if semgrep.is_available():
                    available_tools.append(('Semgrep', semgrep))
                    if verbose:
                        console.print("[dim]✓ Semgrep (Multi-language) - Available[/dim]")
            except Exception as e:
                if verbose:
                    console.print(f"[dim]✗ Semgrep - Configuration error: {e}[/dim]")
        
        # Run scans
        all_findings = []
        tool_results = {}
        
        if verbose:
            console.print(f"[blue]Running {len(available_tools)} security tool(s)...[/blue]")
        
        for tool_name, tool in available_tools:
            try:
                if verbose:
                    console.print(f"[dim]Running {tool_name}...[/dim]")
                
                # Run the actual security scan
                findings = await tool.scan(repo_path, config=config)
                
                if findings is not None:
                    all_findings.extend(findings)
                    tool_results[tool_name] = {
                        'findings_count': len(findings),
                        'status': 'completed'
                    }
                    if verbose:
                        console.print(f"[dim]✓ {tool_name}: {len(findings)} findings[/dim]")
                else:
                    tool_results[tool_name] = {
                        'findings_count': 0,
                        'status': 'no_results'
                    }
                    if verbose:
                        console.print(f"[dim]✓ {tool_name}: No findings[/dim]")
                        
            except Exception as e:
                tool_results[tool_name] = {
                    'findings_count': 0,
                    'status': 'error',
                    'error': str(e)
                }
                if verbose:
                    console.print(f"[dim]✗ {tool_name}: Error - {e}[/dim]")
        
        _enrich_cross_file_context(all_findings, repo_path, languages, verbose=verbose)

        # Create results in expected format
        results = {
            'metadata': {
                'workspace_path': repo_path,
                'scan_mode': scan_mode,
                'technologies': languages,
                'files_analyzed': len(file_list),
                'tools_executed': list(tool_results.keys())
            },
            'findings': all_findings,
            'statistics': _calculate_ci_statistics(all_findings),
            'tool_results': tool_results
        }
        
    except ImportError as e:
        console.print(f"[red]Security tools not available: {e}[/red]")
        results = {
            'metadata': {'workspace_path': repo_path, 'scan_mode': scan_mode, 'error': str(e)},
            'findings': [],
            'statistics': {'total_findings': 0},
            'tool_results': {}
        }
    
    # Filter findings by severity
    severity_levels = ['low', 'medium', 'high', 'critical']
    min_level = severity_levels.index(severity_min.lower())
    
    filtered_findings = [
        finding for finding in results['findings']
        if severity_levels.index(finding.severity.lower()) >= min_level
    ]
    
    console.print(f"[green]Analysis completed: {len(filtered_findings)} findings (>= {severity_min})[/green]")
    
    # Generate reports
    report_generator = ReportGenerator(config)
    
    # Determine output formats
    output_formats = [format] if format else ['markdown', 'json']
    
    # Generate CI report
    ci_report = await report_generator.generate_ci_report(filtered_findings, results['metadata'])
    
    # Generate full reports
    report_paths = await report_generator.generate_full_report(
        filtered_findings, 
        results['metadata'], 
        output_formats
    )
    
    # Print CI summary
    console.print(f"\n[bold]{ci_report['summary']}[/bold]")
    
    # Print recommendations
    if ci_report['recommendations']:
        console.print("\n[bold]Recommendations:[/bold]")
        for rec in ci_report['recommendations']:
            console.print(f"  • {rec}")
    
    # Print output file paths
    console.print(f"\n[bold]Generated Reports:[/bold]")
    for fmt, path in report_paths.items():
        console.print(f"  • {fmt.upper()}: {path}")
    
    # Print CI report path
    console.print(f"  • CI Report: {ci_report['report_file']}")
    
    # Exit with appropriate code
    exit_code = ci_report['exit_code']
    if exit_code == 0:
        console.print(f"\n[green]✅ Security scan passed[/green]")
    elif exit_code == 1:
        console.print(f"\n[yellow]⚠️  Security scan found issues but allows continuation[/yellow]")
    else:
        console.print(f"\n[red]🔴 Security scan failed - blocking issues found[/red]")
    
    sys.exit(exit_code)


if __name__ == "__main__":
    main()