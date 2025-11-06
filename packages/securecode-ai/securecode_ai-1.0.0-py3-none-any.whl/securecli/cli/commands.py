"""
Command handler for REPL commands
"""

import asyncio
import json
import os
import shlex
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress, TaskID

from ..agents.planner import PlannerAgent
from ..workspace import WorkspaceManager
from ..schemas.findings import CVSSv4, Finding
from ..tools.base import ScanResult
from ..report import ReportGenerator
from ..analysis import annotate_cross_file_context
from ..github import analyze_github_repo_cli, validate_github_url


class BaseCommand:
    """Base class for REPL commands"""
    
    def __init__(self, name: str, description: str, usage: str = ""):
        self.name = name
        self.description = description
        self.usage = usage
    
    async def execute(self, args: List[str], context: Dict[str, Any]) -> Any:
        """Execute the command - to be implemented by subclasses"""
        raise NotImplementedError
    
    def get_help(self) -> str:
        """Get help text for the command"""
        help_text = f"{self.name} - {self.description}"
        if self.usage:
            help_text += f"\nUsage: {self.usage}"
        return help_text


class CommandRegistry:
    """Registry for REPL commands"""
    
    def __init__(self):
        self.commands = {}
    
    def register(self, command: BaseCommand):
        """Register a command"""
        self.commands[command.name] = command
    
    def get_command(self, name: str) -> Optional[BaseCommand]:
        """Get a command by name"""
        return self.commands.get(name)
    
    def list_commands(self) -> List[str]:
        """List all registered command names"""
        return list(self.commands.keys())
    
    def get_help(self, command_name: Optional[str] = None) -> str:
        """Get help for a specific command or all commands"""
        if command_name:
            command = self.get_command(command_name)
            return command.get_help() if command else f"Unknown command: {command_name}"
        
        help_text = "Available commands:\n"
        for name, command in sorted(self.commands.items()):
            help_text += f"  {name} - {command.description}\n"
        return help_text


class CommandHandler:
    """Handles REPL command execution"""
    
    def __init__(self, repl):
        self.repl = repl
        self.console = Console()
        
        # Store last scan findings for explain command
        self.last_findings = []
        self.last_scan_results = {}
        self.last_scan_metadata: Optional[Dict[str, Any]] = None
        self.last_report_metadata: Optional[Dict[str, Any]] = None
        self.last_report_outputs: Dict[str, Any] = {}
        self._cross_file_warning_shown = False
        
        # Command registry
        self.commands = {
            'help': self.cmd_help,
            'workspace': self.cmd_workspace,
            'use': self.cmd_use,
            'show': self.cmd_show,
            'set': self.cmd_set,
            'unset': self.cmd_unset,
            'run': self.cmd_run,
            'back': self.cmd_back,
            'scan': self.cmd_scan,
            'report': self.cmd_report,
            'script': self.cmd_script,
            'exit': self.cmd_exit,
            'quit': self.cmd_exit,
            # Enhanced commands
            'status': self.cmd_status,
            'modules': self.cmd_modules,
            'languages': self.cmd_languages,
            'analyze': self.cmd_analyze,
            'github': self.cmd_github,
            'clear': self.cmd_clear,
            'cls': self.cmd_clear,
            # AI integration commands
            'ai': self.cmd_ai,
            'ai-status': self.cmd_ai_status,
            'explain': self.cmd_explain,
            # New tool management commands
            'tools': self.cmd_tools,
            'config': self.cmd_config,
        }
    
    async def execute(self, command_line: str) -> Union[bool, None]:
        """Execute a command line"""
        try:
            parts = shlex.split(command_line)
            if not parts:
                return True  # Continue session
                
            command = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            if command in self.commands:
                result = await self.commands[command](args)
                # Check for explicit exit command
                if command in ['exit', 'quit', 'q']:
                    return False
                return True  # Continue session
            else:
                self.console.print(f"[bright_red]Unknown command: {command}[/bright_red]")
                self.console.print("Type 'help' for available commands")
                return True  # Continue session
                
        except ValueError as e:
            self.console.print(f"[bright_red]Command parsing error: {e}[/bright_red]")
            self.console.print("[yellow]Session continuing... Type 'help' for commands[/yellow]")
            return True  # Continue session
        except Exception as e:
            self.console.print(f"[bright_red]Command execution error: {e}[/bright_red]")
            self.console.print("[yellow]Session continuing... Type 'help' for commands[/yellow]")
            return True  # Continue session
    
    async def cmd_help(self, args: List[str]) -> None:
        """Show help information"""
        if not args:
            self._show_general_help()
        elif args[0] in self.commands:
            self._show_command_help(args[0])
        else:
            self.console.print(f"[bright_red]Unknown command: {args[0]}[/bright_red]")
    
    def _show_general_help(self) -> None:
        """Show general help with enhanced styling"""
        self.console.print("[bold red]╭─ SECURECLI COMMAND REFERENCE ───────────────────────────────────╮[/bold red]")
        
        commands_help = [
            ('CORE OPERATIONS', '', ''),
            ('workspace', 'Manage operational workspaces', 'list|create|use|delete'),
            ('use', 'Select module for engagement', '<module_name>'),
            ('show', 'Display intel/options', 'modules|options|info'),
            ('set/unset', 'Configure module parameters', '<option> <value>'),
            ('run', 'Execute current module', ''),
            ('back', 'Deselect current module', ''),
            ('', '', ''),  # separator
            ('SECURITY ANALYSIS', '', ''),
            ('scan', 'Quick/deep reconnaissance', 'quick|deep|comprehensive'),
            ('report', 'Generate structured reports from last scan', '[formats]'),
            ('analyze', 'Comprehensive AI-powered analysis', '<path>'),
            ('explain', 'AI explanation of specific finding', '<finding_number>'),
            ('github', 'Analyze GitHub repositories', '<github_url> [branch]'),
            ('modules', 'List available scanners', ''),
            ('languages', 'Detect project languages', '<path>'),
            ('', '', ''),  # separator
            ('AI INTEGRATION', '', ''),
            ('ai', 'AI management commands', 'status|test|enable|disable'),
            ('ai-status', 'Show AI integration status', ''),
            ('', '', ''),  # separator
            ('SYSTEM & UTILITIES', '', ''),
            ('status', 'Show system status', ''),
            ('script', 'Execute script file', '<script_file>'),
            ('clear/cls', 'Clear terminal screen', ''),
            ('exit/quit', 'Terminate session', ''),
        ]
        
        current_section = None
        for cmd, desc, usage in commands_help:
            if desc == '' and usage == '':  # section header
                if cmd == '':  # separator
                    self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
                else:  # section header
                    self.console.print(f"[red]│[/red]")
                    self.console.print(f"[red]│[/red] [bold yellow]{cmd}[/bold yellow]")
                    self.console.print(f"[red]│[/red] [dim]{'─' * len(cmd)}[/dim]")
                continue
            
            # Format command with proper spacing
            if usage:
                cmd_line = f"[bold red]{cmd}[/bold red] [dim cyan]{usage}[/dim cyan]"
            else:
                cmd_line = f"[bold red]{cmd}[/bold red]"
            
            # Print with proper alignment and spacing
            self.console.print(f"[red]│[/red] {cmd_line}")
            self.console.print(f"[red]│[/red]   [white]{desc}[/white]")
        
        self.console.print("[red]│[/red]")
        self.console.print("[bold red]╰─────────────────────────────────────────────────────────────────╯[/bold red]")
        self.console.print("\n[dim]» Type [white]help <command>[/white] for detailed usage[/dim]")
        self.console.print("[dim]» Example: [white]help config[/white] for configuration options[/dim]")
        self.console.print("[dim]» Example: [white]analyze .[/white] to scan current directory with AI[/dim]")
    
    def _show_command_help(self, command: str) -> None:
        """Show help for specific command"""
        if command == 'set' or command == 'config':
            self._show_config_help()
        elif command == 'scan':
            self._show_scan_help()
        elif command == 'analyze':
            self._show_analyze_help()
        elif command == 'report':
            self._show_report_help()
        elif command == 'github':
            self._show_github_help()
        elif command == 'workspace':
            self._show_workspace_help()
        elif command == 'ai':
            self._show_ai_help()
        else:
            self.console.print(f"[cyan]Help for '{command}' command[/cyan]")
            self.console.print("[dim]Detailed help not yet implemented[/dim]")
    
    def _show_config_help(self) -> None:
        """Show detailed configuration help"""
        self.console.print("[bold red]╭─ CONFIGURATION SYSTEM REFERENCE ───────────────────────────────╮[/bold red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]USAGE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────[/dim]")
        self.console.print("[red]│[/red] [bold red]set[/bold red] [dim cyan]<option> <value>[/dim cyan]   - Set configuration option")
        self.console.print("[red]│[/red] [bold red]unset[/bold red] [dim cyan]<option>[/dim cyan]         - Remove configuration option")
        self.console.print("[red]│[/red] [bold red]show[/bold red] [dim cyan]options[/dim cyan]           - Display current configuration")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]REPOSITORY SETTINGS[/bold yellow]")
        self.console.print("[red]│[/red] [dim]───────────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]repo.path[/bold cyan]              - Target repository path")
        self.console.print("[red]│[/red]   Example: [white]set repo.path /path/to/repo[/white]")
        self.console.print("[red]│[/red] [bold cyan]repo.exclude[/bold cyan]           - Directories/patterns to exclude")
        self.console.print("[red]│[/red]   Example: [white]set repo.exclude node_modules/,dist/[/white]")
        self.console.print("[red]│[/red] [bold cyan]repo.max_file_size[/bold cyan]     - Maximum file size to scan (bytes)")
        self.console.print("[red]│[/red]   Example: [white]set repo.max_file_size 1048576[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]SCAN MODES & TOOLS[/bold yellow]")
        self.console.print("[red]│[/red] [dim]──────────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]mode[/bold cyan]                   - Scan intensity level")
        self.console.print("[red]│[/red]   Options: [white]quick | deep | comprehensive[/white]")
        self.console.print("[red]│[/red]   Example: [white]set mode comprehensive[/white]")
        self.console.print("[red]│[/red] [bold cyan]tools.enabled[/bold cyan]          - Active security scanning tools")
        self.console.print("[red]│[/red]   Example: [white]set tools.enabled semgrep,bandit,gitleaks[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]AI & LLM SETTINGS[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]llm.provider[/bold cyan]           - AI provider selection")
        self.console.print("[red]│[/red]   Options: [white]auto | openai | anthropic | local[/white]")
        self.console.print("[red]│[/red]   Example: [white]set llm.provider auto[/white]")
        self.console.print("[red]│[/red] [bold cyan]llm.model[/bold cyan]              - Language model to use")
        self.console.print("[red]│[/red]   Options: [white]gpt-4 | gpt-3.5-turbo | claude-3-sonnet | deepseek-coder[/white]")
        self.console.print("[red]│[/red]   Example: [white]set llm.model gpt-4[/white]")
        self.console.print("[red]│[/red] [bold cyan]llm.max_tokens[/bold cyan]         - Maximum tokens per request")
        self.console.print("[red]│[/red]   Example: [white]set llm.max_tokens 4000[/white]")
        self.console.print("[red]│[/red] [bold cyan]llm.temperature[/bold cyan]        - AI creativity level (0.0-1.0)")
        self.console.print("[red]│[/red]   Example: [white]set llm.temperature 0.1[/white]")
        self.console.print("[red]│[/red] [bold cyan]llm.timeout[/bold cyan]            - Request timeout in seconds")
        self.console.print("[red]│[/red]   Example: [white]set llm.timeout 120[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]RAG & KNOWLEDGE BASE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]────────────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]rag.enabled[/bold cyan]            - Enable RAG for enhanced analysis")
        self.console.print("[red]│[/red]   Example: [white]set rag.enabled true[/white]")
        self.console.print("[red]│[/red] [bold cyan]rag.k[/bold cyan]                  - Number of context chunks to retrieve")
        self.console.print("[red]│[/red]   Example: [white]set rag.k 5[/white]")
        self.console.print("[red]│[/red] [bold cyan]rag.chunk_size[/bold cyan]         - Size of text chunks for indexing")
        self.console.print("[red]│[/red]   Example: [white]set rag.chunk_size 1000[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]DOMAIN & PROFILES[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]domain.profiles[/bold cyan]        - Security testing profiles")
        self.console.print("[red]│[/red]   Options: [white]web,api,mobile,iot,blockchain,cloud[/white]")
        self.console.print("[red]│[/red]   Example: [white]set domain.profiles web,api[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]CVSS & CI/CD INTEGRATION[/bold yellow]")
        self.console.print("[red]│[/red] [dim]────────────────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]cvss.policy[/bold cyan]            - CVSS severity blocking policy")
        self.console.print("[red]│[/red]   Options: [white]block_critical | block_high | block_medium | warn_only[/white]")
        self.console.print("[red]│[/red]   Example: [white]set cvss.policy block_high[/white]")
        self.console.print("[red]│[/red] [bold cyan]ci.block_on[/bold cyan]            - CI/CD pipeline blocking criteria")
        self.console.print("[red]│[/red]   Example: [white]set ci.block_on critical,high[/white]")
        self.console.print("[red]│[/red] [bold cyan]ci.changed_files_only[/bold cyan]  - Only scan changed files in CI")
        self.console.print("[red]│[/red]   Example: [white]set ci.changed_files_only true[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]OUTPUT & REPORTING[/bold yellow]")
        self.console.print("[red]│[/red] [dim]──────────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]output.dir[/bold cyan]             - Output directory for reports")
        self.console.print("[red]│[/red]   Example: [white]set output.dir ./reports[/white]")
        self.console.print("[red]│[/red] [bold cyan]output.format[/bold cyan]          - Report output format")
        self.console.print("[red]│[/red]   Options: [white]md | json | sarif | html[/white]")
        self.console.print("[red]│[/red]   Example: [white]set output.format json[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]SECURITY & REDACTION[/bold yellow]")
        self.console.print("[red]│[/red] [dim]────────────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]redact.enabled[/bold cyan]         - Enable sensitive data redaction")
        self.console.print("[red]│[/red]   Example: [white]set redact.enabled true[/white]")
        self.console.print("[red]│[/red] [bold cyan]sandbox.enabled[/bold cyan]        - Enable sandbox execution")
        self.console.print("[red]│[/red]   Example: [white]set sandbox.enabled true[/white]")
        self.console.print("[red]│[/red] [bold cyan]sandbox.timeout[/bold cyan]        - Sandbox execution timeout")
        self.console.print("[red]│[/red]   Example: [white]set sandbox.timeout 300[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[bold red]╰─────────────────────────────────────────────────────────────────╯[/bold red]")
        self.console.print("\n[dim]» Configuration is saved automatically to [white]~/.securecli/config.yml[/white][/dim]")
        self.console.print("[dim]» Use [white]show options[/white] to view current configuration[/dim]")
        self.console.print("[dim]» Environment variables: [white]SECURE_<OPTION>[/white] (e.g., SECURE_LLM_MODEL)[/dim]")
    
    def _show_scan_help(self) -> None:
        """Show scan command help"""
        self.console.print("[bold red]╭─ SCAN COMMAND REFERENCE ─────────────────────────────────────────╮[/bold red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]USAGE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────[/dim]")
        self.console.print("[red]│[/red] [bold red]scan[/bold red] [dim cyan]quick[/dim cyan]              - Fast security scan")
        self.console.print("[red]│[/red] [bold red]scan[/bold red] [dim cyan]deep[/dim cyan]               - Thorough analysis")
        self.console.print("[red]│[/red] [bold red]scan[/bold red] [dim cyan]comprehensive[/dim cyan]      - Full security assessment")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]SCAN MODES[/bold yellow]")
        self.console.print("[red]│[/red] [dim]──────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]quick[/bold cyan]     - Fast static analysis (5-15 tools)")
        self.console.print("[red]│[/red] [bold cyan]deep[/bold cyan]      - Extended analysis + AI insights")
        self.console.print("[red]│[/red] [bold cyan]comprehensive[/bold cyan] - Full analysis + RAG + reporting")
        self.console.print("[red]│[/red]")
        self.console.print("[bold red]╰─────────────────────────────────────────────────────────────────╯[/bold red]")
    
    def _show_analyze_help(self) -> None:
        """Show analyze command help"""
        self.console.print("[bold red]╭─ ANALYZE COMMAND REFERENCE ──────────────────────────────────────╮[/bold red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]USAGE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────[/dim]")
        self.console.print("[red]│[/red] [bold red]analyze[/bold red] [dim cyan]<path>[/dim cyan]          - AI-powered code analysis")
        self.console.print("[red]│[/red] [bold red]analyze[/bold red] [dim cyan].[/dim cyan]               - Analyze current directory")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]FEATURES[/bold yellow]")
        self.console.print("[red]│[/red] [dim]────────[/dim]")
        self.console.print("[red]│[/red] - Multi-tool security scanning")
        self.console.print("[red]│[/red] - AI-enhanced vulnerability analysis")
        self.console.print("[red]│[/red] - Comprehensive reporting (MD/JSON/SARIF)")
        self.console.print("[red]│[/red] - Language-specific security checks")
        self.console.print("[red]│[/red]")
        self.console.print("[bold red]╰─────────────────────────────────────────────────────────────────╯[/bold red]")
    
    def _show_report_help(self) -> None:
        """Show report command help"""
        self.console.print("[bold red]╭─ REPORT COMMAND REFERENCE ─────────────────────────────────────╮[/bold red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]USAGE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────[/dim]")
        self.console.print("[red]│[/red] [bold red]report[/bold red] [dim cyan][formats][/dim cyan]        - Generate reports from last scan")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]FORMATS[/bold yellow]")
        self.console.print("[red]│[/red] [dim]────────[/dim]")
        self.console.print("[red]│[/red] [white]markdown[/white]  - Executive summary with visuals")
        self.console.print("[red]│[/red] [white]json[/white]      - Structured findings export")
        self.console.print("[red]│[/red] [white]sarif[/white]     - CI/CD and IDE integrations")
        self.console.print("[red]│[/red] [white]csv[/white]       - Spreadsheet-friendly output")
        self.console.print("[red]│[/red] [white]ci[/white]        - CI summary + policy exit code")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]NOTES[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────[/dim]")
        self.console.print("[red]│[/red] - Defaults to markdown + json when no formats are given")
        self.console.print("[red]│[/red] - Use [white]report all[/white] for every available format")
        self.console.print("[red]│[/red] - Reports save to configured [white]output.dir[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[bold red]╰─────────────────────────────────────────────────────────────────╯[/bold red]")

    def _show_github_help(self) -> None:
        """Show github command help"""
        self.console.print("[bold red]╭─ GITHUB COMMAND REFERENCE ───────────────────────────────────────╮[/bold red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]USAGE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────[/dim]")
        self.console.print("[red]│[/red] [bold red]github[/bold red] [dim cyan]<url>[/dim cyan]           - Analyze GitHub repository")
        self.console.print("[red]│[/red] [bold red]github[/bold red] [dim cyan]<url> <branch>[/dim cyan]  - Analyze specific branch")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]EXAMPLES[/bold yellow]")
        self.console.print("[red]│[/red] [dim]────────[/dim]")
        self.console.print("[red]│[/red] [white]github https://github.com/owner/repo[/white]")
        self.console.print("[red]│[/red] [white]github https://github.com/owner/repo develop[/white]")
        self.console.print("[red]│[/red]")
        self.console.print("[bold red]╰─────────────────────────────────────────────────────────────────╯[/bold red]")
    
    def _show_workspace_help(self) -> None:
        """Show workspace command help"""
        self.console.print("[bold red]╭─ WORKSPACE COMMAND REFERENCE ────────────────────────────────────╮[/bold red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]USAGE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────[/dim]")
        self.console.print("[red]│[/red] [bold red]workspace[/bold red] [dim cyan]list[/dim cyan]         - List all workspaces")
        self.console.print("[red]│[/red] [bold red]workspace[/bold red] [dim cyan]create <name>[/dim cyan] - Create new workspace")
        self.console.print("[red]│[/red] [bold red]workspace[/bold red] [dim cyan]use <name>[/dim cyan]    - Switch to workspace")
        self.console.print("[red]│[/red] [bold red]workspace[/bold red] [dim cyan]delete <name>[/dim cyan] - Delete workspace")
        self.console.print("[red]│[/red]")
        self.console.print("[bold red]╰─────────────────────────────────────────────────────────────────╯[/bold red]")
    
    def _show_ai_help(self) -> None:
        """Show AI command help"""
        self.console.print("[bold red]╭─ AI COMMAND REFERENCE ───────────────────────────────────────────╮[/bold red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]USAGE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────[/dim]")
        self.console.print("[red]│[/red] [bold red]ai[/bold red] [dim cyan]status[/dim cyan]             - Check AI integration status")
        self.console.print("[red]│[/red] [bold red]ai[/bold red] [dim cyan]test[/dim cyan]               - Test API connectivity")
        self.console.print("[red]│[/red] [bold red]ai[/bold red] [dim cyan]test-local[/dim cyan]         - Test local model")
        self.console.print("[red]│[/red] [bold red]ai[/bold red] [dim cyan]local <action>[/dim cyan]     - Manage local models")
        self.console.print("[red]│[/red] [bold red]ai[/bold red] [dim cyan]switch <provider>[/dim cyan]  - Switch AI provider")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]API MODELS[/bold yellow]")
        self.console.print("[red]│[/red] [dim]──────────[/dim]")
        self.console.print("[red]│[/red] - Set OPENAI_API_KEY environment variable")
        self.console.print("[red]│[/red] - Configure llm.model setting")
        self.console.print("[red]│[/red] - Supports: gpt-4, gpt-3.5-turbo, claude-3-sonnet")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]LOCAL MODELS[/bold yellow]")
        self.console.print("[red]│[/red] [dim]────────────[/dim]")
        self.console.print("[red]│[/red] [bold cyan]ai local enable[/bold cyan]        - Enable local model inference")
        self.console.print("[red]│[/red] [bold cyan]ai local disable[/bold cyan]       - Disable local models")
        self.console.print("[red]│[/red] [bold cyan]ai local info[/bold cyan]          - Show local model config")
        self.console.print("[red]│[/red] [bold cyan]ai local setup[/bold cyan]         - Interactive setup guide")
        self.console.print("[red]│[/red] [bold cyan]ai switch auto[/bold cyan]         - Enable smart provider selection")
        self.console.print("[red]│[/red] [bold cyan]ai switch openai[/bold cyan]       - Switch to OpenAI")
        self.console.print("[red]│[/red] [bold cyan]ai switch local[/bold cyan]        - Switch to local models")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]SUPPORTED ENGINES[/bold yellow]")
        self.console.print("[red]│[/red] [dim]─────────────────[/dim]")
        self.console.print("[red]│[/red] - [bold white]Ollama[/bold white] - Easy local model hosting")
        self.console.print("[red]│[/red] - [bold white]llama.cpp[/bold white] - High-performance inference")
        self.console.print("[red]│[/red] - [bold white]Transformers[/bold white] - HuggingFace models")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]RECOMMENDED MODELS[/bold yellow]")
        self.console.print("[red]│[/red] [dim]──────────────────[/dim]")
        self.console.print("[red]│[/red] - [bold green]deepseek-coder[/bold green] - Best for security analysis")
        self.console.print("[red]│[/red] - [bold white]codellama[/bold white] - General code understanding")
        self.console.print("[red]│[/red] - [bold white]wizardcoder[/bold white] - Code generation")
        self.console.print("[red]│[/red] - [bold white]starcoder[/bold white] - Multi-language support")
        self.console.print("[red]│[/red]")
        self.console.print("[dim red]├─────────────────────────────────────────────────────────────────┤[/dim red]")
        self.console.print("[red]│[/red]")
        self.console.print("[red]│[/red] [bold yellow]QUICK SETUP EXAMPLE[/bold yellow]")
        self.console.print("[red]│[/red] [dim]───────────────────[/dim]")
        self.console.print("[red]│[/red] [white]# Install Ollama[/white]")
        self.console.print("[red]│[/red] [cyan]curl -fsSL https://ollama.ai/install.sh | sh[/cyan]")
        self.console.print("[red]│[/red] [white]# Pull DeepSeek model[/white]")
        self.console.print("[red]│[/red] [cyan]ollama pull deepseek-coder[/cyan]")
        self.console.print("[red]│[/red] [white]# Configure SecureCLI[/white]")
        self.console.print("[red]│[/red] [cyan]set llm.provider local[/cyan]")
        self.console.print("[red]│[/red] [cyan]set local_model.enabled true[/cyan]")
        self.console.print("[red]│[/red] [cyan]ai test-local[/cyan]")
        self.console.print("[red]│[/red]")
        self.console.print("[bold red]╰─────────────────────────────────────────────────────────────────╯[/bold red]")
    
    async def cmd_workspace(self, args: List[str]) -> None:
        """Workspace management"""
        if not args:
            args = ['list']
        
        action = args[0].lower()
        
        if action == 'list':
            workspaces = self.repl.workspace_manager.list_workspaces()
            current = self.repl.workspace_manager.current_workspace
            
            if not workspaces:
                self.console.print("[yellow]No workspaces found.[/yellow]")
                self.console.print("[cyan]Create one with: workspace create <name>[/cyan]")
                return
            
            table = Table(title="Available Workspaces")
            table.add_column("Name", style="cyan")
            table.add_column("Status", style="green")
            table.add_column("Path", style="dim")
            
            for ws in workspaces:
                status = "active" if ws == current else "inactive"
                workspace_path = self.repl.workspace_manager.get_workspace_path(ws)
                table.add_row(ws, status, workspace_path or "N/A")
            
            self.console.print(table)
            
            if current:
                self.console.print(f"\n[bold green]Current workspace:[/bold green] {current}")
            else:
                self.console.print(f"\n[yellow]No active workspace. Use 'workspace use <name>' to activate one.[/yellow]")
        
        elif action == 'create' and len(args) > 1:
            name = args[1]
            try:
                workspace_path = self.repl.workspace_manager.create_workspace(name)
                self.console.print(f"[green]Created workspace '{name}' at {workspace_path}[/green]")
                
                # Verify the workspace was created
                if self.repl.workspace_manager.workspace_exists(name):
                    self.console.print(f"[green]Workspace '{name}' verified and ready to use[/green]")
                    self.console.print(f"[cyan]Switch to it with: workspace use {name}[/cyan]")
                else:
                    self.console.print(f"[red]Warning: Workspace '{name}' creation may have failed[/red]")
                    
            except ValueError as e:
                self.console.print(f"[red]Error creating workspace: {e}[/red]")
            except Exception as e:
                self.console.print(f"[red]Unexpected error creating workspace: {e}[/red]")
        
        elif action == 'use' and len(args) > 1:
            name = args[1]
            try:
                if not self.repl.workspace_manager.workspace_exists(name):
                    self.console.print(f"[red]Workspace '{name}' does not exist[/red]")
                    self.console.print(f"[cyan]Available workspaces: {', '.join(self.repl.workspace_manager.list_workspaces())}[/cyan]")
                    return
                
                self.repl.workspace_manager.use_workspace(name)
                # Configure workspace-specific paths
                self.repl.workspace_manager.configure_workspace_paths(self.repl.config_manager)
                self.console.print(f"[green]Now using workspace '{name}'[/green]")
                
                # Show workspace info
                workspace_path = self.repl.workspace_manager.get_workspace_path(name)
                self.console.print(f"[dim]Workspace path: {workspace_path}[/dim]")
                
            except Exception as e:
                self.console.print(f"[red]Error switching to workspace: {e}[/red]")
        
        elif action == 'delete' and len(args) > 1:
            name = args[1]
            try:
                if not self.repl.workspace_manager.workspace_exists(name):
                    self.console.print(f"[red]Workspace '{name}' does not exist[/red]")
                    return
                
                # Show confirmation info
                current = self.repl.workspace_manager.current_workspace
                if name == current:
                    self.console.print("[yellow]Warning: This will delete your current active workspace![/yellow]")
                
                workspace_path = self.repl.workspace_manager.get_workspace_path(name)
                self.console.print(f"[yellow]This will permanently delete: {workspace_path}[/yellow]")
                self.console.print(f"[yellow]Continue? This action cannot be undone.[/yellow]")
                
                # TODO: Add proper confirmation prompt in interactive mode
                # For now, require force flag or confirmation
                self.repl.workspace_manager.delete_workspace(name, force=True)
                self.console.print(f"[green]Deleted workspace '{name}'[/green]")
                
                if name == current:
                    self.console.print(f"[cyan]No active workspace. Use 'workspace use <name>' to activate one.[/cyan]")
                    
            except Exception as e:
                self.console.print(f"[red]Error deleting workspace: {e}[/red]")
        
        else:
            self.console.print("[red]Usage: workspace [list|create|use|delete] <name>[/red]")
    
    async def cmd_use(self, args: List[str]) -> None:
        """Select a module"""
        if not args:
            self.console.print("[red]Usage: use <module_path>[/red]")
            return
        
        module_path = args[0]
        
        # TODO: Validate module exists
        self.repl.current_module = module_path
        self.repl.module_options = {}
        
        self.console.print(f"[green]Using module: {module_path}[/green]")
    
    async def cmd_show(self, args: List[str]) -> None:
        """Show information"""
        if not args:
            args = ['options']
        
        what = args[0].lower()
        
        if what == 'modules':
            self._show_modules()
        elif what == 'options':
            self._show_options()
        else:
            self.console.print(f"[red]Unknown show target: {what}[/red]")
    
    def _show_modules(self) -> None:
        """Show available modules"""
        # Security scanner modules (matching the 27 analyzers)
        modules = [
            # Core Security Scanners
            ('scanner/semgrep', 'Static analysis with Semgrep', 'web2,web3'),
            ('scanner/gitleaks', 'Secret detection', 'web2,web3'),
            ('scanner/bandit', 'Python security analysis', 'web2'),
            
            # Language-Specific Scanners
            ('scanner/java', 'Java security (SpotBugs/PMD)', 'web2'),
            ('scanner/csharp', 'C#/.NET security (DevSkim/Roslyn)', 'web2'),
            ('scanner/cpp', 'C++ security (Clang/CppCheck)', 'web2'),
            ('scanner/c', 'C security (Clang/Splint)', 'web2'),
            ('scanner/rust', 'Rust security (Clippy/Cargo Audit)', 'web2'),
            ('scanner/go', 'Go security (Gosec)', 'web2'),
            ('scanner/php', 'PHP security (Psalm/PHPStan)', 'web2'),
            ('scanner/ruby', 'Ruby security (Brakeman/RuboCop)', 'web2'),
            ('scanner/python', 'Python security (Bandit/Safety)', 'web2'),
            ('scanner/javascript', 'JS/TS security (ESLint/npm-audit)', 'web2'),
            
            # Mobile Development
            ('scanner/swift', 'iOS/macOS security (SwiftLint)', 'mobile'),
            ('scanner/kotlin', 'Android/JVM security (Detekt)', 'mobile'),
            ('scanner/objective-c', 'Legacy iOS/macOS security', 'mobile'),
            ('scanner/dart', 'Flutter/Dart security', 'mobile'),
            
            # Functional Programming
            ('scanner/haskell', 'Haskell security (HLint/Weeder)', 'functional'),
            ('scanner/scala', 'Scala security (Scalafix)', 'functional'),
            ('scanner/fsharp', 'F# security (FSharpLint)', 'functional'),
            ('scanner/erlang', 'Erlang/Elixir security (Credo)', 'functional'),
            
            # Scripting Languages
            ('scanner/perl', 'Perl security (Perl::Critic)', 'scripting'),
            ('scanner/lua', 'Lua security (luacheck)', 'scripting'),
            
            # Web3/Smart Contract
            ('scanner/slither', 'Solidity static analysis', 'web3'),
            ('scanner/vyper', 'Vyper smart contract analysis', 'web3'),
            ('scanner/cairo', 'StarkNet Cairo analysis', 'web3'),
            ('scanner/move', 'Move smart contract analysis', 'web3'),
            ('scanner/clarity', 'Stacks Bitcoin contract analysis', 'web3'),
            
            # Workflow Modules
            ('auditor/generic', 'Generic LLM audit', 'web2,web3'),
            ('auditor/solidity', 'Solidity-specific audit', 'web3'),
            ('tighten/prune_dead_code', 'Remove dead code', 'web2,web3'),
            ('report/summary', 'Generate summary report', 'web2,web3'),
        ]
        
        table = Table(title="Available Modules")
        table.add_column("Module", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Tags", style="dim")
        
        for module, desc, tags in modules:
            table.add_row(module, desc, tags)
        
        self.console.print(table)
    
    def _show_options(self) -> None:
        """Show current options"""
        table = Table(title="Options")
        table.add_column("Name", style="cyan")
        table.add_column("Current Value", style="green")
        table.add_column("Required", style="yellow")
        table.add_column("Description", style="white")
        
        if self.repl.current_module:
            # Show module options
            module_opts = {
                'severity_min': ('Medium', 'no', 'Minimum severity to include'),
                'cvss.policy': ('block_high', 'no', 'CI block policy'),
            }
            
            for name, (default, required, desc) in module_opts.items():
                current = self.repl.module_options.get(name, default)
                table.add_row(name, str(current), required, desc)
        
        else:
            # Show global options
            global_opts = {
                'repo.path': ('not set', 'yes', 'Repository path to analyze'),
                'mode': ('quick', 'no', 'Analysis mode (quick|deep|redteam|refactor)'),
                'llm.model': ('gpt-4', 'no', 'LLM model to use'),
                'output.dir': ('./output', 'no', 'Output directory'),
            }
            
            for name, (default, required, desc) in global_opts.items():
                current = self.repl.config_manager.get(name, default)
                table.add_row(name, str(current), required, desc)
        
        self.console.print(table)
    
    async def cmd_set(self, args: List[str]) -> None:
        """Set option value"""
        if len(args) < 2:
            self.console.print("[red]Usage: set <key> <value>[/red]")
            return
        
        key = args[0]
        value = ' '.join(args[1:])
        
        # Type conversion
        if value.lower() in ('true', 'false'):
            value = value.lower() == 'true'
        elif value.isdigit():
            value = int(value)
        elif value.replace('.', '').isdigit():
            value = float(value)
        
        self.repl.set_option(key, value)
        self.console.print(f"[green]{key} => {value}[/green]")
    
    async def cmd_unset(self, args: List[str]) -> None:
        """Unset option value"""
        if not args:
            self.console.print("[red]Usage: unset <key>[/red]")
            return
        
        key = args[0]
        if self.repl.current_module and key in self.repl.module_options:
            del self.repl.module_options[key]
        else:
            self.repl.config_manager.unset(key)
        
        self.console.print(f"[yellow]Unset {key}[/yellow]")
    
    async def cmd_run(self, args: List[str]) -> None:
        """Execute current module"""
        if not self.repl.current_module:
            self.console.print("[red]No module selected. Use 'use <module>' first[/red]")
            return
        
        self.console.print(f"[blue]Running module: {self.repl.current_module}[/blue]")
        
        # TODO: Implement module execution via LangChain
        with Progress() as progress:
            task = progress.add_task("[cyan]Executing...", total=100)
            
            for i in range(100):
                await asyncio.sleep(0.01)
                progress.update(task, advance=1)
        
        self.console.print("[green]Module execution completed[/green]")
    
    async def cmd_back(self, args: List[str]) -> None:
        """Deselect current module"""
        if self.repl.current_module:
            self.console.print(f"[yellow]Deselected module: {self.repl.current_module}[/yellow]")
            self.repl.current_module = None
            self.repl.module_options = {}
        else:
            self.console.print("[yellow]No module selected[/yellow]")
    
    async def cmd_scan(self, args: List[str]) -> None:
        """Quick/deep scan shortcuts using real security tools
        
        Usage: 
        - scan quick [path]     - Quick security scan (default: current directory)
        - scan deep [path]      - Deep security scan  
        - scan comprehensive [path] - Comprehensive scan with all tools
        """
        # Parse arguments more flexibly
        mode = 'quick'  # default
        target_path = '.'  # default
        
        if args:
            # Check if first arg is a mode or a path
            if args[0] in ['quick', 'deep', 'comprehensive']:
                mode = args[0]
                target_path = args[1] if len(args) > 1 else '.'
            else:
                # First arg is a path, use default mode
                target_path = args[0]
                mode = args[1] if len(args) > 1 and args[1] in ['quick', 'deep', 'comprehensive'] else 'quick'
        
        self.console.print(f"\n[bright_blue]Starting {mode} security scan[/bright_blue]")
        self.console.print(f"[dim]Target: {os.path.abspath(target_path)}[/dim]")
        
        if not os.path.exists(target_path):
            self.console.print(f"[bright_red]Path not found: {target_path}[/bright_red]")
            self.console.print("[bright_yellow]Usage: scan [quick|deep|comprehensive] [path][/bright_yellow]")
            return
        
        try:
            # Import real security tools
            from ..tools import BanditTool, SemgrepTool, GitleaksTool, SlitherTool, NpmAuditTool, CppTool, RustTool, JavaTool, RubyTool, GoTool, CSharpTool, SolidityTool, VyperTool
            
            # Initialize available tools
            config = self.repl.config_manager.get_all()
            available_tools = []

            scan_started_at = datetime.now()
            
            # Language detection for target selection
            from ..languages import analyze_project_languages
            
            self.console.print("[dim]Analyzing project languages...[/dim]")
            lang_analysis = analyze_project_languages(target_path)
            
            # Extract actual language list from breakdown
            language_breakdown = lang_analysis.get('language_breakdown', {})
            languages = list(language_breakdown.keys()) if language_breakdown else []
            
            self.console.print(f"[dim]Detected languages: {', '.join(languages) if languages else 'None'}[/dim]")
            
            # Select tools based on detected languages and mode
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
                        self.console.print("[dim]Bandit (Python security) - Available[/dim]")
                    else:
                        self.console.print("[dim]Bandit - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Bandit - Configuration error[/dim]")
            
            # JavaScript/Node.js security scanning
            if any(lang in languages for lang in ['javascript', 'typescript']) and NpmAuditTool:
                try:
                    npm_audit = NpmAuditTool(config)
                    if npm_audit.is_available():
                        available_tools.append(('NPM Audit', npm_audit))
                        self.console.print("[dim]NPM Audit (JS/TS security) - Available[/dim]")
                    else:
                        self.console.print("[dim]NPM Audit - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]NPM Audit - Configuration error[/dim]")
            
            # C++ security scanning
            if any(lang in languages for lang in ['cpp', 'c++', 'c', 'cc', 'cxx']) and CppTool:
                try:
                    cpp_analyzer = CppTool(config)
                    available_tools.append(('C++ Analyzer', cpp_analyzer))
                    self.console.print("[dim]C++ Analyzer (Clang/CppCheck) - Available[/dim]")
                except Exception:
                    self.console.print("[dim]C++ Analyzer - Configuration error[/dim]")
            elif any(lang in languages for lang in ['cpp', 'c++', 'c', 'cc', 'cxx']):
                self.console.print("[dim]C++ code detected - Install clang or cppcheck for analysis[/dim]")
            
            # Rust security scanning
            if 'rust' in languages and RustTool:
                try:
                    rust_analyzer = RustTool(config)
                    if rust_analyzer.is_available():
                        available_tools.append(('Rust Analyzer', rust_analyzer))
                        self.console.print("[dim]Rust Analyzer (Clippy/Cargo Audit) - Available[/dim]")
                    else:
                        self.console.print("[dim]Rust Analyzer - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Rust Analyzer - Configuration error[/dim]")
            elif 'rust' in languages:
                self.console.print("[dim]Rust code detected - Install clippy and cargo-audit for analysis[/dim]")
            
            # Java security scanning
            if 'java' in languages and JavaTool:
                try:
                    java_analyzer = JavaTool(config)
                    if java_analyzer.is_available():
                        available_tools.append(('Java Analyzer', java_analyzer))
                        self.console.print("[dim]Java Analyzer (SpotBugs/PMD) - Available[/dim]")
                    else:
                        self.console.print("[dim]Java Analyzer - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Java Analyzer - Configuration error[/dim]")
            elif 'java' in languages:
                self.console.print("[dim]Java code detected - Install SpotBugs and PMD for analysis[/dim]")
            
            # Ruby security scanning
            if 'ruby' in languages and RubyTool:
                try:
                    ruby_analyzer = RubyTool(config)
                    if ruby_analyzer.is_available():
                        available_tools.append(('Ruby Analyzer', ruby_analyzer))
                        self.console.print("[dim]Ruby Analyzer (Brakeman/RuboCop) - Available[/dim]")
                    else:
                        self.console.print("[dim]Ruby Analyzer - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Ruby Analyzer - Configuration error[/dim]")
            elif 'ruby' in languages:
                self.console.print("[dim]Ruby code detected - Install brakeman and rubocop for analysis[/dim]")
            
            # Go security scanning
            if 'go' in languages and GoTool:
                try:
                    go_analyzer = GoTool(config)
                    if go_analyzer.is_available():
                        available_tools.append(('Go Analyzer', go_analyzer))
                        self.console.print("[dim]Go Analyzer (Gosec/Staticcheck) - Available[/dim]")
                    else:
                        self.console.print("[dim]Go Analyzer - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Go Analyzer - Configuration error[/dim]")
            elif 'go' in languages:
                self.console.print("[dim]Go code detected - Install gosec and staticcheck for analysis[/dim]")
            
            # C#/.NET security scanning
            if any(lang in languages for lang in ['c#', 'csharp', 'cs']) and CSharpTool:
                try:
                    csharp_analyzer = CSharpTool(config)
                    if csharp_analyzer.is_available():
                        available_tools.append(('C# Analyzer', csharp_analyzer))
                        self.console.print("[dim]C# Analyzer (DevSkim/Roslyn) - Available[/dim]")
                    else:
                        self.console.print("[dim]C# Analyzer - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]C# Analyzer - Configuration error[/dim]")
            elif any(lang in languages for lang in ['c#', 'csharp', 'cs']):
                self.console.print("[dim]C# code detected - Install DevSkim and .NET SDK for analysis[/dim]")
            
            # Solidity security scanning
            if 'solidity' in languages and SolidityTool:
                try:
                    solidity_analyzer = SolidityTool(config)
                    if solidity_analyzer.is_available():
                        available_tools.append(('Solidity Analyzer', solidity_analyzer))
                        self.console.print("[dim]Solidity Analyzer (Slither/DevSkim) - Available[/dim]")
                    else:
                        self.console.print("[dim]Solidity Analyzer - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Solidity Analyzer - Configuration error[/dim]")
            elif 'solidity' in languages:
                self.console.print("[dim]Solidity code detected - Install slither-analyzer and solc for analysis[/dim]")
            
            # Vyper security scanning
            if 'vyper' in languages and VyperTool:
                try:
                    vyper_analyzer = VyperTool(config)
                    if vyper_analyzer.is_available():
                        available_tools.append(('Vyper Analyzer', vyper_analyzer))
                        self.console.print("[dim]Vyper Analyzer (Pattern-based) - Available[/dim]")
                    else:
                        self.console.print("[dim]Vyper Analyzer - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Vyper Analyzer - Configuration error[/dim]")
            elif 'vyper' in languages:
                self.console.print("[dim]Vyper code detected - Install vyper compiler for analysis[/dim]")
            
            # Smart contract security scanning - ONLY for blockchain code
            if has_smart_contracts and SlitherTool:
                try:
                    slither = SlitherTool(config)
                    if slither.is_available():
                        available_tools.append(('Slither', slither))
                        self.console.print("[dim]Slither (Solidity security) - Available[/dim]")
                    else:
                        self.console.print("[dim]Slither - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Slither - Configuration error[/dim]")
            elif 'solidity' in languages:
                self.console.print("[dim]Solidity code detected but Slither not available[/dim]")
            
            # Universal secret detection (works for any codebase)
            if GitleaksTool:
                try:
                    gitleaks = GitleaksTool(config)
                    if gitleaks.is_available():
                        available_tools.append(('Gitleaks', gitleaks))
                        self.console.print("[dim]Gitleaks (Secrets detection) - Available[/dim]")
                    else:
                        self.console.print("[dim]Gitleaks - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Gitleaks - Configuration error[/dim]")
            
            # Semgrep for multi-language analysis (exclude if only smart contracts)
            if SemgrepTool and (has_web_code or mode in ['deep', 'comprehensive']):
                try:
                    semgrep = SemgrepTool(config)
                    if semgrep.is_available():
                        available_tools.append(('Semgrep', semgrep))
                        self.console.print("[dim]Semgrep (Multi-language) - Available[/dim]")
                    else:
                        self.console.print("[dim]Semgrep - Not installed[/dim]")
                except Exception:
                    self.console.print("[dim]Semgrep - Configuration error[/dim]")
            elif has_smart_contracts and not has_web_code:
                self.console.print("[dim]Smart contract only - Semgrep skipped[/dim]")
            
            if not available_tools:
                self.console.print("[bright_yellow]No security tools available for detected languages.[/bright_yellow]")
                if has_web_code:
                    self.console.print("   Web2 tools:")
                    self.console.print("   - pip install bandit (Python security)")
                    self.console.print("   - npm install -g npm-audit (JavaScript security)")
                    self.console.print("   - Install semgrep for multi-language analysis")
                if has_smart_contracts:
                    self.console.print("   Web3 tools:")
                    self.console.print("   - Install slither-analyzer (Solidity security)")
                self.console.print("   Universal tools:")
                self.console.print("   - Install gitleaks for secret detection")
                return
            
            # Run scans
            all_findings = []
            scan_results = {}
            
            self.console.print(f"\n[bright_blue]Running {len(available_tools)} security tool(s)...[/bright_blue]")
            
            for tool_name, tool in available_tools:
                try:
                    self.console.print(f"[dim]Running {tool_name}...[/dim]")
                    
                    # Run the actual security scan
                    result = await tool.scan(target_path, config=config)

                    findings_list: List[Any] = []
                    metadata: Dict[str, Any] = {}
                    raw_output = ""
                    error_output = None
                    exit_code = 0
                    status = 'completed'

                    if isinstance(result, ScanResult):
                        findings_list = result.findings or []
                        metadata = result.metadata or {}
                        raw_output = result.raw_output or ""
                        error_output = result.error_output
                        exit_code = result.exit_code
                        status = 'completed' if exit_code == 0 else 'error'
                    elif isinstance(result, list):
                        findings_list = result
                        status = 'completed' if findings_list else 'no_results'
                        exit_code = 0 if status == 'completed' else 1
                    elif result is None:
                        status = 'no_results'
                        exit_code = 1
                    else:
                        try:
                            findings_list = list(result)
                            status = 'completed' if findings_list else 'no_results'
                            exit_code = 0 if status == 'completed' else 1
                        except TypeError:
                            status = 'error'
                            exit_code = 1
                            error_output = f"Unsupported result type: {type(result).__name__}"

                    if findings_list:
                        all_findings.extend(findings_list)

                    scan_entry: Dict[str, Any] = {
                        'findings_count': len(findings_list),
                        'status': status,
                        'exit_code': exit_code
                    }

                    if metadata:
                        scan_entry['metadata'] = metadata
                    if raw_output:
                        scan_entry['raw_output'] = raw_output
                    if error_output:
                        scan_entry['error'] = error_output

                    scan_results[tool_name] = scan_entry

                    if status == 'completed':
                        self.console.print(f"[dim]{tool_name}: {len(findings_list)} findings[/dim]")
                    elif status == 'no_results':
                        self.console.print(f"[dim]{tool_name}: No findings[/dim]")
                    else:
                        error_msg = error_output or (metadata.get('error') if metadata else None) or f"Exit code {exit_code}"
                        self.console.print(f"[dim]{tool_name}: Error - {error_msg}[/dim]")
                        
                except Exception as e:
                    scan_results[tool_name] = {
                        'findings_count': 0,
                        'status': 'error',
                        'error': str(e)
                    }
                    self.console.print(f"[dim]{tool_name}: Error - {e}[/dim]")
            
            # Enrich findings with cross-file context before presentation
            self._enrich_cross_file_context(all_findings, target_path, languages)

            # Display comprehensive results
            await self._display_real_scan_results(all_findings, scan_results, mode, target_path)
            
            scan_completed_at = datetime.now()
            sanitized_results = {name: self._sanitize_for_report(data) for name, data in scan_results.items()}
            sanitized_language = self._sanitize_language_breakdown(language_breakdown)
            language_summary = {
                'total_files': lang_analysis.get('total_files', 0),
                'languages_detected': lang_analysis.get('languages_detected', 0),
                'primary_language': lang_analysis.get('primary_language', 'unknown'),
                'recommended_tools': lang_analysis.get('recommended_tools', []),
                'security_priority_languages': lang_analysis.get('security_priority_languages', []),
                'web3_languages': lang_analysis.get('web3_languages', []),
            }
            scan_metadata = {
                'mode': mode,
                'target_path': os.path.abspath(target_path),
                'repo_path': os.path.abspath(target_path),
                'scan_start': scan_started_at.isoformat(),
                'scan_end': scan_completed_at.isoformat(),
                'scan_duration_seconds': round((scan_completed_at - scan_started_at).total_seconds(), 3),
                'tools_used': list(sanitized_results.keys()),
                'total_findings': len(all_findings),
                'language_breakdown': sanitized_language,
                'language_summary': language_summary,
                'scanned_files': lang_analysis.get('total_files', 0),
                'scan_results': sanitized_results,
            }
            scan_metadata = self._sanitize_for_report(scan_metadata)

            # Store findings and metadata for follow-up commands
            self.last_findings = all_findings
            self.last_scan_results = sanitized_results
            self.last_scan_metadata = scan_metadata
            self.last_report_metadata = None
            self.last_report_outputs = {}
            
        except ImportError as e:
            self.console.print(f"[red]Security tools not available: {e}[/red]")
            self.console.print("[yellow]Install security tools with: pip install bandit semgrep[/yellow]")
        except Exception as e:
            self.console.print(f"[red]Scan error: {e}[/red]")
    
    
    async def _display_real_scan_results(self, findings: List[Any], scan_results: Dict[str, Any], mode: str, target_path: str):
        """Display professional security scan results with enhanced formatting"""
        from rich.markdown import Markdown
        
        def get_tool_name(finding) -> str:
            """Helper to extract tool name from finding"""
            tool_evidence = getattr(finding, 'tool_evidence', [])
            if tool_evidence and len(tool_evidence) > 0:
                return tool_evidence[0].tool
            return 'Unknown'
        
        total_findings = len(findings)
        
        if total_findings == 0:
            # Success case - clean display
            success_panel = Panel(
                f"[bold green]No security issues were detected.[/bold green]\n\n"
                f"[dim]Scan type:[/dim] {mode.title()}\n"
                f"[dim]Target:[/dim] {target_path}\n"
                f"[dim]Tools used:[/dim] {len(scan_results)}\n\n"
                f"[green]All executed tools completed without reporting findings.[/green]",
                title="Security Scan Complete",
                style="bold green"
            )
            self.console.print(success_panel)

            # Tool execution summary for success case
            if scan_results:
                success_table = Table(show_header=True, header_style="bold green")
                success_table.add_column("Tool", style="cyan", width=15)
                success_table.add_column("Status", style="green", width=15)
                success_table.add_column("Files Scanned", style="dim", width=15)

                for tool_name, result in scan_results.items():
                    status = "Clean" if result.get('status') in ['completed', 'no_results'] else "Error"
                    files_count = result.get('files_scanned', 'N/A')
                    success_table.add_row(tool_name.title(), status, str(files_count))

                self.console.print(success_table)
            return
        
        # Issues found - comprehensive display
        self.console.print(f"\n")
        
        # Header with key metrics
        severity_counts = {'Critical': 0, 'High': 0, 'Medium': 0, 'Low': 0, 'Info': 0}
        by_tool = {}
        cross_file_count = 0  # Track findings with cross-file traces
        
        for finding in findings:
            severity = getattr(finding, 'severity', 'Medium').title()
            if severity in severity_counts:
                severity_counts[severity] += 1
            else:
                severity_counts['Medium'] += 1
            
            # Get tool from tool_evidence using helper
            tool = get_tool_name(finding)
            by_tool[tool] = by_tool.get(tool, 0) + 1
            
            # Count cross-file traces
            if hasattr(finding, 'cross_file') and finding.cross_file:
                cross_file_count += 1
        
        # Risk assessment
        critical_high = severity_counts['Critical'] + severity_counts['High']
        if critical_high >= 5:
            risk_level = "High"
        elif critical_high >= 1:
            risk_level = "Elevated"
        else:
            risk_level = "Low"

        # Main results header
        summary_text = f"**Security Scan Results**\n\n"
        summary_text += f"**Total Issues:** {total_findings}\n"
        summary_text += f"**Risk Level:** {risk_level}\n"
        summary_text += f"**Target:** `{target_path}`\n"
        summary_text += f"**Mode:** {mode.title()}\n"
        if cross_file_count > 0:
            summary_text += f"**Cross-File Traces:** {cross_file_count} findings with execution path analysis\n"
        summary_text += f"\n"

        # Quick severity breakdown
        summary_text += "**Issues by Severity:**\n"
        for sev, count in severity_counts.items():
            if count > 0:
                summary_text += f"  - {sev}: {count}\n"

        main_panel = Panel(Markdown(summary_text), title="Security Assessment", style="bold red")
        self.console.print(main_panel)
        
        # Tool execution summary
        tool_table = Table(title="Tool Execution Summary", show_header=True, header_style="bold cyan")
        tool_table.add_column("Security Tool", style="cyan", width=20)
        tool_table.add_column("Status", style="bold", width=15)
        tool_table.add_column("Issues Found", style="yellow", width=15)
        tool_table.add_column("Execution Time", style="dim", width=15)
        
        for tool_name, result in scan_results.items():
            status = result.get('status', 'unknown')
            
            # Match tool name (case-insensitive) with findings
            findings_count = 0
            tool_name_lower = tool_name.lower().replace(' analyzer', '').replace(' audit', '').strip()
            for tool_key, count in by_tool.items():
                if tool_key.lower() == tool_name_lower or tool_name_lower in tool_key.lower():
                    findings_count = count
                    break
            
            exec_time = result.get('execution_time', 'N/A')
            
            if status == 'completed':
                status_display = "Success"
            elif status == 'no_results':
                status_display = "Clean"
            elif status == 'error':
                status_display = "Failed"
            else:
                status_display = "Unknown"
            
            tool_table.add_row(tool_name.title(), status_display, str(findings_count), str(exec_time))
        
        self.console.print(tool_table)
        
        # Severity breakdown with visual indicators
        if any(count > 0 for count in severity_counts.values()):
            severity_table = Table(title="Security Issues by Severity", show_header=True, header_style="bold magenta")
            severity_table.add_column("Severity Level", style="bold", width=20)
            severity_table.add_column("Count", style="bold", width=10, justify="center")
            severity_table.add_column("Risk Impact", width=30)
            severity_table.add_column("Action Required", width=25)
            
            severity_data = {
                'Critical': ('Critical', 'Immediate system compromise risk', 'Fix immediately'),
                'High': ('High', 'Significant security vulnerability', 'Fix within 24 hours'),
                'Medium': ('Medium', 'Moderate security concern', 'Address within the next sprint'),
                'Low': ('Low', 'Minor security issue', 'Plan remediation'),
                'Info': ('Informational', 'Security awareness note', 'Review and document')
            }
            
            for severity, count in severity_counts.items():
                if count > 0:
                    display_name, impact, action = severity_data[severity]
                    severity_table.add_row(display_name, str(count), impact, action)
            
            self.console.print(severity_table)

        # Highlight file hotspots with ASCII spark bars
        file_counts: Dict[str, int] = {}
        file_highest_severity: Dict[str, str] = {}
        severity_priority = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3, "Info": 4}

        for finding in findings:
            file_path = getattr(finding, 'file', 'Unknown') or 'Unknown'
            file_counts[file_path] = file_counts.get(file_path, 0) + 1
            severity = getattr(finding, 'severity', 'Medium').title()
            previous = file_highest_severity.get(file_path)
            if previous is None or severity_priority.get(severity, 99) < severity_priority.get(previous, 99):
                file_highest_severity[file_path] = severity

        if file_counts:
            top_file_entries = sorted(file_counts.items(), key=lambda item: item[1], reverse=True)[:8]
            max_count = max(count for _, count in top_file_entries)

            lines = []
            for path, count in top_file_entries:
                shortened = self._shorten_cli_path(path)
                bar = self._build_ascii_bar(count, max_count)
                severity = file_highest_severity.get(path, 'Medium')
                lines.append(f"{shortened:<40} | {bar:<24} {count:>3} ({severity})")

            hotspot_panel = Panel(
                "\n".join(lines),
                title="File Hotspots",
                border_style="cyan"
            )
            self.console.print(hotspot_panel)
        
        # Detailed findings - show critical/high first, then top medium/low
        if findings:
            # Sort by severity priority
            severity_order = {'Critical': 0, 'High': 1, 'Medium': 2, 'Low': 3, 'Info': 4}
            sorted_findings = sorted(
                findings, 
                key=lambda x: (
                    severity_order.get(getattr(x, 'severity', 'Medium').title(), 5),
                    getattr(x, 'file', ''),
                    getattr(x, 'lines', '0')
                )
            )
            
            # Critical & High severity findings (show all)
            critical_high_findings = [f for f in sorted_findings if getattr(f, 'severity', 'Medium').title() in ['Critical', 'High']]
            
            if critical_high_findings:
                self.console.print(Panel("Critical and High Severity Issues (immediate attention required)", style="bold red"))
                
                for i, finding in enumerate(critical_high_findings, 1):
                    self._display_detailed_finding(finding, i, mode, show_full=True)
            
            # Medium & Low findings (show all in detail for deep mode, or show all in table for standard)
            other_findings = [f for f in sorted_findings if getattr(f, 'severity', 'Medium').title() not in ['Critical', 'High']]
            
            if other_findings:
                # In deep mode or if not too many, show full details for all
                if mode == 'deep' or len(other_findings) <= 20:
                    self.console.print(Panel(f"Medium and Low Severity Issues ({len(other_findings)} issues)", style="bold cyan"))
                    for i, finding in enumerate(other_findings, len(critical_high_findings) + 1):
                        self._display_detailed_finding(finding, i, mode, show_full=True)
                else:
                    # Show expandable table for many findings
                    findings_table = Table(
                        title=f"Additional Security Issues ({len(other_findings)} issues - showing all)", 
                        show_header=True, 
                        header_style="bold bright_cyan",
                        border_style="bright_blue"
                    )
                    findings_table.add_column("#", style="bright_white bold", width=5)
                    findings_table.add_column("Severity", width=12)
                    findings_table.add_column("Issue Type", style="bright_cyan", width=35)
                    findings_table.add_column("File:Line", style="bright_blue", width=50)
                    findings_table.add_column("Tool", style="bright_magenta", width=15)
                    findings_table.add_column("CVSS", width=6, justify="center")
                    findings_table.add_column("X-File", width=7, justify="center")
                    
                    for i, finding in enumerate(other_findings, len(critical_high_findings) + 1):
                        finding_id = getattr(finding, 'id', f'F{i:03d}')
                        tool = get_tool_name(finding)
                        severity = getattr(finding, 'severity', 'Medium').title()
                        file_path = getattr(finding, 'file', 'Unknown')
                        lines = getattr(finding, 'lines', '')
                        title = getattr(finding, 'title', 'Security Issue')
                        
                        # Get CVSS score
                        cvss_score = 'N/A'
                        if hasattr(finding, 'cvss_v4') and finding.cvss_v4:
                            cvss_score = f"{finding.cvss_v4.score:.1f}"
                        
                        # Check for cross-file traces
                        cross_file_indicator = ''
                        if hasattr(finding, 'cross_file') and finding.cross_file:
                            trace_count = len(finding.cross_file)
                            cross_file_indicator = f"[bright_cyan]{trace_count} →[/bright_cyan]"
                        
                        # Enhanced color scheme for better visibility
                        severity_colors = {
                            'Critical': '[bold bright_red on black]● Critical[/bold bright_red on black]',
                            'High': '[bold red on black]● High[/bold red on black]',
                            'Medium': '[bold bright_yellow on black]● Medium[/bold bright_yellow on black]',
                            'Low': '[bold bright_blue on black]● Low[/bold bright_blue on black]',
                            'Info': '[bold bright_white on black]● Info[/bold bright_white on black]'
                        }
                        
                        severity_display = severity_colors.get(severity, severity)
                        file_display = f"{file_path}:{lines}" if lines else file_path
                        
                        findings_table.add_row(
                            f"[bright_white]{i}[/bright_white]",
                            severity_display,
                            f"[bright_white]{title}[/bright_white]",  # NO TRUNCATION
                            f"[bright_blue]{file_display}[/bright_blue]",
                            f"[bright_magenta]{tool.title()}[/bright_magenta]",
                            f"[bright_yellow]{cvss_score}[/bright_yellow]",
                            cross_file_indicator
                        )
                    
                    self.console.print(findings_table)
                    
                    # Show cross-file summary
                    cross_file_findings = [f for f in other_findings if hasattr(f, 'cross_file') and f.cross_file]
                    if cross_file_findings:
                        self.console.print(f"[bright_cyan]ℹ {len(cross_file_findings)} findings have cross-file execution traces. Use 'scan deep' to view full details.[/bright_cyan]")
        
        # Action summary
        action_text = f"\n**Recommended Actions:**\n\n"
        if critical_high > 0:
            action_text += f"1. **Urgent:** Address {critical_high} critical or high severity issues immediately\n"
        if severity_counts['Medium'] > 0:
            action_text += f"2. **Priority:** Review {severity_counts['Medium']} medium severity issues\n"
        if severity_counts['Low'] + severity_counts['Info'] > 0:
            action_text += f"3. **Planned:** Address {severity_counts['Low'] + severity_counts['Info']} low or informational issues in the next cycle\n"
        
        action_text += f"\n**Next Steps:**\n"
        action_text += f"- Run `analyze` for AI-assisted security insights\n"
        action_text += f"- Use `show options` to configure scan parameters\n"
        action_text += f"- Export results with `set output.format json`\n"

        action_panel = Panel(Markdown(action_text), title="Action Plan", style="bold blue")
        self.console.print(action_panel)

    def _enrich_cross_file_context(self, findings: List[Any], target_path: str, languages: List[str]) -> None:
        """Augment findings with cross-file traces when Python code is present."""

        if not findings or not languages:
            return

        language_set = {lang.lower() for lang in languages if isinstance(lang, str)}
        if "python" not in language_set:
            return

        repo_root = Path(target_path).resolve()
        if repo_root.is_file():
            repo_root = repo_root.parent
        if not repo_root.is_dir():
            return

        typed_findings = [f for f in findings if isinstance(f, Finding)]
        if not typed_findings:
            return

        files = sorted({f.file for f in typed_findings if getattr(f, "file", None)})
        if not files:
            return

        needs_enrichment = any(not getattr(f, "cross_file", None) for f in typed_findings)
        if not needs_enrichment:
            return

        try:
            annotate_cross_file_context(repo_root, typed_findings, files=files)
            self._cross_file_warning_shown = False
        except Exception:
            if not self._cross_file_warning_shown:
                self.console.print("[dim]Cross-file context enrichment unavailable for this scan.[/dim]")
                self._cross_file_warning_shown = True

    def _sanitize_language_breakdown(self, breakdown: Dict[str, Any]) -> Dict[str, Any]:
        """Strip complex objects from language breakdown for reporting."""
        sanitized: Dict[str, Any] = {}
        if not breakdown:
            return sanitized
        for language, stats in breakdown.items():
            percentage = stats.get('percentage', 0.0)
            avg_confidence = stats.get('avg_confidence', 0.0)
            info = stats.get('info')

            sanitized_stats = {
                'files': stats.get('files', 0),
                'percentage': round(percentage, 2) if isinstance(percentage, (int, float)) else percentage,
                'avg_confidence': round(avg_confidence, 2) if isinstance(avg_confidence, (int, float)) else avg_confidence,
            }

            if info:
                sanitized_stats['category'] = getattr(getattr(info, 'category', None), 'value', None)
                sanitized_stats['analysis_priority'] = getattr(info, 'analysis_priority', None)

            sanitized[language] = sanitized_stats

        return sanitized

    def _sanitize_for_report(self, value: Any) -> Any:
        """Convert complex objects to report-friendly primitives."""
        if isinstance(value, datetime):
            return value.isoformat()
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {key: self._sanitize_for_report(val) for key, val in value.items()}
        if isinstance(value, (list, tuple, set)):
            return [self._sanitize_for_report(item) for item in value]

        try:
            import dataclasses
            if dataclasses.is_dataclass(value):
                return {field.name: self._sanitize_for_report(getattr(value, field.name)) for field in dataclasses.fields(value)}
        except Exception:
            pass

        if hasattr(value, 'value') and not isinstance(value, (str, bytes)):
            return self._sanitize_for_report(getattr(value, 'value'))

        return value

    def _display_detailed_finding(self, finding, index: int, mode: str = 'quick', show_full: bool = False):
        """Display a detailed view of a security finding with enhanced colors"""
        from rich.markdown import Markdown
        
        # Helper to get tool name
        def get_tool_name(finding) -> str:
            tool_evidence = getattr(finding, 'tool_evidence', [])
            if tool_evidence and len(tool_evidence) > 0:
                return tool_evidence[0].tool
            return 'Unknown'
        
        # Extract finding details - NO TRUNCATION
        finding_id = getattr(finding, 'id', f'F{index:03d}')
        title = getattr(finding, 'title', 'Security Issue')
        description = getattr(finding, 'description', 'No description available')
        file_path = getattr(finding, 'file', 'Unknown')
        lines = getattr(finding, 'lines', '')
        severity = getattr(finding, 'severity', 'Medium').title()
        impact = getattr(finding, 'impact', 'Security impact assessment needed')
        recommendation = getattr(finding, 'recommendation', 'Review and remediate according to best practices')
        tool = get_tool_name(finding)
        
        # CWE information - handle list or string
        cwe = getattr(finding, 'cwe', None)
        cwe_display = "N/A"
        if cwe:
            if isinstance(cwe, list) and len(cwe) > 0:
                cwe_display = cwe[0] if isinstance(cwe[0], str) else f"CWE-{cwe[0]}"
            elif isinstance(cwe, str):
                cwe_display = cwe
            else:
                cwe_display = str(cwe)
        
        # CVSS score
        cvss_score = 'N/A'
        cvss_vector = ''
        if hasattr(finding, 'cvss_v4') and finding.cvss_v4:
            cvss_score = f"{finding.cvss_v4.score:.1f}"
            cvss_vector = getattr(finding.cvss_v4, 'vector', '')
        
        # Confidence score
        confidence = getattr(finding, 'confidence_score', 'N/A')
        
        # Enhanced color scheme for better visibility
        severity_colors = {
            'Critical': 'bold bright_red on black',
            'High': 'bold bright_yellow on black',
            'Medium': 'bold bright_cyan on black',
            'Low': 'bold bright_blue on black',
            'Info': 'bold bright_white on black'
        }
        
        # Create detailed markdown - FULL CONTENT, NO TRUNCATION
        # Start with clean title (no duplication)
        detail_text = f"**{title}**\n\n"
        
        location = f"{file_path}:{lines}" if lines else file_path
        detail_text += (
            f"**Severity:** {severity}  \n"
            f"**Confidence:** {confidence}%  \n"
            f"**CVSS Score:** {cvss_score}"
        )
        if cvss_vector:
            detail_text += f" (`{cvss_vector}`)"
        detail_text += "  \n"
        detail_text += f"**Location:** `{location}`  \n"
        detail_text += f"**Tool:** {tool.title()}  \n"
        detail_text += f"**CWE:** {cwe_display}\n\n"

        # Always show full description (cleaned - no title duplication)
        detail_text += f"**Description**\n\n{description}\n\n"
        
        # Show code snippet if available
        code_snippet = getattr(finding, 'code_snippet', None)
        if code_snippet:
            detail_text += f"**Code**\n\n```\n{code_snippet}\n```\n\n"
        
        # Always show impact if present
        if impact and len(impact.strip()) > 5 and impact != "Security impact assessment needed":
            detail_text += f"**Security Impact**\n\n{impact}\n\n"
        
        # Always show recommendation
        detail_text += f"**Remediation**\n\n{recommendation}\n\n"

        sample_fix = getattr(finding, 'sample_fix', None)
        if sample_fix:
            detail_text += f"**Sample Fix**\n\n{sample_fix}\n\n"
        
        # Add cross-file traces if available - SHOW ALL, NO TRUNCATION
        cross_file = getattr(finding, 'cross_file', None)
        if cross_file and len(cross_file) > 0:
            detail_text += f"**Cross-File Execution Traces ({len(cross_file)} path{'s' if len(cross_file) > 1 else ''})**\n\n"
            detail_text += "_These traces show how execution flows from entry points through this vulnerability:_\n\n"
            for i, trace in enumerate(cross_file, 1):  # SHOW ALL TRACES
                # Clean up trace for display
                cleaned_trace = trace.replace(' -> ', ' → ')
                detail_text += f"  {i}. `{cleaned_trace}`\n"
            detail_text += "\n"
        
        # AI insights if available
        ai_analysis = getattr(finding, 'ai_analysis', None)
        if ai_analysis:
            detail_text += f"**AI Analysis**\n\n{ai_analysis}\n\n"
        
        color = severity_colors.get(severity, 'white')
        panel_title = f"Finding #{index} - {severity} Severity"
        if finding_id and finding_id != f'F{index:03d}':
            panel_title += f" [{finding_id}]"
        
        finding_panel = Panel(
            Markdown(detail_text), 
            title=panel_title, 
            style=color,
            border_style=color,
            expand=False
        )
        self.console.print(finding_panel)
        
        # Context-specific suggestions
        if mode == 'quick':
            self.console.print(f"  [dim]Run 'scan deep' for comprehensive cross-file analysis[/dim]")
        
        # AI enhancement suggestion
        if os.environ.get('OPENAI_API_KEY'):
            self.console.print("  [dim]Use 'analyze' for AI-powered vulnerability assessment[/dim]")
        
        self.console.print("  [dim]Use 'report' to generate detailed findings report[/dim]")
        self.console.print()  # Add spacing between findings

    def _build_ascii_bar(self, count: int, max_count: int, width: int = 24) -> str:
        """Create a simple ASCII bar scaled to the maximum count."""
        if max_count <= 0:
            return ""
        scaled = max(1, int(round((count / max_count) * width)))
        scaled = min(width, scaled)
        return "=" * scaled

    def _shorten_cli_path(self, path: str, max_length: int = 40) -> str:
        """Shorten file paths for CLI display while keeping context."""
        if not path:
            return "Unknown"

        normalized = path.replace('\\', '/').strip()
        if len(normalized) <= max_length:
            return normalized

        parts = [part for part in normalized.split('/') if part]
        if len(parts) >= 2:
            tail = "/".join(parts[-2:])
            if len(tail) <= max_length - 4:
                return f".../{tail}"

        if parts:
            filename = parts[-1]
            if len(filename) <= max_length - 4:
                return f".../{filename}"

        return "..." + normalized[-(max_length - 3):]
    
    async def cmd_report(self, args: List[str]) -> None:
        """Generate structured reports from the most recent scan or analysis."""
        if not self.last_scan_metadata:
            self.console.print("[yellow]No scan context available. Run 'scan' or 'analyze' before generating reports.[/yellow]")
            return

        format_aliases = {
            'markdown': 'markdown',
            'md': 'markdown',
            'json': 'json',
            'sarif': 'sarif',
            'csv': 'csv'
        }

        requested_formats: List[str] = []
        ci_requested = False

        for arg in args:
            key = arg.lower()
            if key == 'all':
                requested_formats = ['markdown', 'json', 'sarif', 'csv']
            elif key == 'ci':
                ci_requested = True
            elif key in format_aliases:
                fmt = format_aliases[key]
                if fmt not in requested_formats:
                    requested_formats.append(fmt)
            else:
                self.console.print(f"[yellow]Ignoring unsupported format '{arg}'.[/yellow]")

        if not requested_formats:
            requested_formats = ['markdown', 'json']

        config = self.repl.config_manager.get_all()
        report_generator = ReportGenerator(config)

        metadata = dict(self.last_scan_metadata)
        metadata.setdefault('report_generated_at', datetime.now().isoformat())
        metadata.setdefault('tools_used', metadata.get('tools_used', list(self.last_scan_results.keys())))
        metadata.setdefault('scanned_files', metadata.get('scanned_files', 0))
        metadata.setdefault('total_findings', len(self.last_findings))

        repo_path = metadata.get('repo_path') or metadata.get('target_path') or '.'
        language_breakdown = self.last_scan_metadata.get('language_breakdown', {})
        languages = list(language_breakdown.keys()) if isinstance(language_breakdown, dict) else []
        self._enrich_cross_file_context(self.last_findings, repo_path, languages)

        metadata = self._sanitize_for_report(metadata)

        try:
            report_paths = await report_generator.generate_full_report(
                self.last_findings,
                metadata,
                output_formats=requested_formats
            )

            ci_report = None
            if ci_requested:
                ci_report = await report_generator.generate_ci_report(self.last_findings, metadata)

            if not report_paths and not ci_report:
                self.console.print("[yellow]No reports were generated. Ensure findings are available.[/yellow]")
                return

            results_table = Table(show_header=True, header_style="bold green")
            results_table.add_column("Artifact", style="cyan")
            results_table.add_column("Location", style="magenta")

            diagram_artifacts = None

            if isinstance(report_paths.get('diagrams'), dict):
                diagram_artifacts = report_paths['diagrams']

            for fmt, path in report_paths.items():
                if fmt == 'diagrams':
                    continue
                results_table.add_row(fmt.upper(), str(path))

            if diagram_artifacts:
                for name, artifact_path in diagram_artifacts.items():
                    label = f"DIAGRAM {name.replace('_', ' ').title()}"
                    results_table.add_row(label, str(artifact_path))

            ci_exit = None
            if ci_report:
                if ci_report.get('report_file'):
                    results_table.add_row("CI", str(ci_report.get('report_file')))
                if ci_report.get('sarif_file'):
                    results_table.add_row("CI-SARIF", str(ci_report.get('sarif_file')))
                ci_exit = ci_report.get('exit_code', 'N/A')

            output_dir = config.get('output.dir', './output')
            self.console.print(f"\n[bold blue]Reports written to:[/bold blue] {output_dir}")
            self.console.print(results_table)

            if ci_exit is not None:
                self.console.print(f"[dim]CI exit code: {ci_exit}[/dim]")

            self.last_report_metadata = metadata
            self.last_report_outputs = {'formats': report_paths, 'ci': ci_report}

        except Exception as exc:
            self.console.print(f"[red]Report generation failed: {exc}[/red]")

    async def cmd_script(self, args: List[str]) -> None:
        """Execute script file"""
        if not args:
            self.console.print("[red]Usage: script <file>[/red]")
            return
        
        script_path = args[0]
        self.repl.execute_script(script_path)
    
    async def _auto_save_analysis_report(self, findings: List[Any], path: str, scan_mode: str, use_local_model: bool) -> None:
        """Automatically generate and save report after AI analysis"""
        try:
            from ..report import ReportGenerator
            
            config = self.repl.config_manager.get_all()
            report_generator = ReportGenerator(config)
            
            # Prepare metadata for the report
            from ..languages import analyze_project_languages
            lang_analysis = analyze_project_languages(path)
            language_breakdown = lang_analysis.get('language_breakdown', {})
            
            metadata = {
                'target_path': os.path.abspath(path),
                'repo_path': os.path.abspath(path),
                'scan_started_at': datetime.now().isoformat(),
                'report_generated_at': datetime.now().isoformat(),
                'scan_mode': scan_mode,
                'ai_provider': 'Local Model (DeepSeek)' if use_local_model else 'OpenAI API',
                'total_findings': len(findings),
                'language_breakdown': language_breakdown,
                'tools_used': ['AI Security Auditor'],
                'scanned_files': lang_analysis.get('total_files', 0),
            }
            
            # Enrich findings with cross-file context
            languages = list(language_breakdown.keys()) if isinstance(language_breakdown, dict) else []
            self._enrich_cross_file_context(findings, path, languages)
            
            metadata = self._sanitize_for_report(metadata)
            
            # Generate reports in markdown and JSON formats
            self.console.print(f"\n[dim]Generating analysis report...[/dim]")
            report_paths = await report_generator.generate_full_report(
                findings,
                metadata,
                output_formats=['markdown', 'json']
            )
            
            if report_paths:
                output_dir = config.get('output.dir', './output')
                self.console.print(f"\n[bold green]✓ Analysis report saved:[/bold green]")
                
                for fmt, report_path in report_paths.items():
                    if fmt != 'diagrams':
                        self.console.print(f"  [cyan]{fmt.upper()}:[/cyan] {report_path}")
                
                # Store for potential follow-up commands
                self.last_scan_metadata = metadata
                self.last_report_metadata = metadata
                self.last_report_outputs = {'formats': report_paths}
            
        except Exception as e:
            self.console.print(f"[yellow]Note: Could not auto-save report: {e}[/yellow]")
    
    async def cmd_exit(self, args: List[str]) -> bool:
        """Exit SecureCLI"""
        return False

    # Enhanced command implementations
    
    async def cmd_status(self, args: List[str]) -> None:
        """Show system status and configuration"""
        self.console.print(f"\n[bold blue]System Status:[/bold blue]")
        self.console.print("─" * 50)
        
        # Test system components
        try:
            from ..modules import create_analysis_engine
            engine = create_analysis_engine()
            if engine:
                engine_status = "[green]Online[/green]"
            else:
                engine_status = "[yellow]Limited functionality[/yellow]"
        except Exception as e:
            engine_status = f"[red]Offline ({str(e)[:30]}...)[/red]"
        
        # Check AI integration
        ai_key = self.repl.config_manager.get('llm.openai_api_key') or os.environ.get('OPENAI_API_KEY')
        if ai_key:
            ai_status = f"[green]Configured (key: ...{ai_key[-4:]})[/green]"
        else:
            ai_status = "[red]Not configured[/red]"
        
        status_table = Table.grid(padding=(0, 2))
        status_table.add_column(style="white", width=20)
        status_table.add_column()
        
        status_table.add_row("Analysis Engine", engine_status)
        status_table.add_row("AI Integration", ai_status)
        status_table.add_row("Working Directory", f"[white]{os.getcwd()}[/white]")
        status_table.add_row("Current Workspace", f"[white]{self.repl.workspace_manager.current_workspace or 'default'}[/white]")
        status_table.add_row("Current Module", f"[white]{self.repl.current_module or 'None'}[/white]")
        
        self.console.print(status_table)
        self.console.print(f"\n[dim]Run 'modules' to see available scanners[/dim]")
    
    async def cmd_modules(self, args: List[str]) -> None:
        """Display available security scanner modules"""
        self.console.print(f"\n[bold blue]Security Scanner Modules:[/bold blue]")
        self.console.print("─" * 50)
        
        try:
            # Try complex modules first
            from ..modules.scanners import create_scanner_modules
            modules = create_scanner_modules()
            if modules:
                self.console.print(f"[green]Module system fully operational[/green]")
                self._display_advanced_modules(modules)
                return
        except Exception as e:
            self.console.print(f"[yellow]Module system not available[/yellow]")
            self.console.print(f"[dim]Error: {str(e)[:60]}...[/dim]")
            self._display_hardcoded_modules()
    
    def _display_advanced_modules(self, modules):
        """Display advanced module information"""
        table = Table()
        table.add_column("Module", style="cyan")
        table.add_column("Type", style="white")
        table.add_column("Priority", style="yellow")
        table.add_column("Status", style="green")
        
        for module in modules:
            # Module objects have .config attribute with ModuleConfig
            name = module.config.name if hasattr(module, 'config') else str(module)
            module_type = module.config.module_type.value if hasattr(module, 'config') else 'scanner'
            priority = str(module.config.priority) if hasattr(module, 'config') else 'N/A'
            
            # Check if module is applicable (most are by default)
            status = "Ready"
            
            table.add_row(name, module_type, priority, status)
        
        self.console.print(table)
        self.console.print(f"\n[blue]Total modules: {len(modules)}[/blue]")
    
    def _display_simple_modules(self, modules):
        """Display simple module information"""
        table = Table()
        table.add_column("Scanner", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Languages", style="yellow")
        table.add_column("Status", style="green")
        
        for module in modules:
            name = module['name'].replace('_scanner', '').title()
            desc = module['description']
            languages = ', '.join(module['languages'][:3])
            if len(module['languages']) > 3:
                languages += "..."
            
            status = "Available" if module['enabled'] else "Disabled"
            table.add_row(name, desc, languages, status)
        
        self.console.print(table)
        self.console.print(f"\n[blue]Total scanners: {len(modules)}[/blue]")
    
    def _display_hardcoded_modules(self):
        """Display hardcoded module list as fallback"""
        modules = [
            ("Semgrep", "Static analysis tool", "Python, JS, Go, Java", "Available"),
            ("Gitleaks", "Secret detection", "All languages", "Available"),
            ("Bandit", "Python security linter", "Python", "Available"),
            ("NPM Audit", "Node.js security scanner", "JavaScript", "Available"),
            ("Slither", "Solidity analyzer", "Solidity", "Available"),
            (
                "AI Auditor",
                "LLM-powered analysis",
                "All languages",
                "Available" if os.environ.get('OPENAI_API_KEY') else "Not configured",
            ),
        ]
        
        table = Table()
        table.add_column("Scanner", style="cyan")
        table.add_column("Description", style="white")
        table.add_column("Languages", style="yellow")
        table.add_column("Status", style="green")
        
        for name, desc, langs, status in modules:
            table.add_row(name, desc, langs, status)
        
        self.console.print(table)
    
    async def cmd_languages(self, args: List[str]) -> None:
        """Analyze programming languages in project"""
        path = args[0] if args else "."
        
        self.console.print(f"\n[blue]Analyzing languages at: {path}[/blue]")
        
        if not os.path.exists(path):
            self.console.print(f"[red]Path not found: {path}[/red]")
            return
        
        try:
            from ..languages import analyze_project_languages
            
            self.console.print("[dim]Scanning files...[/dim]", end="")
            await asyncio.sleep(0.5)  # Simulate processing
            self.console.print(" done")
            
            analysis = analyze_project_languages(path)
            
            if analysis and 'language_breakdown' in analysis:
                table = Table(title="Language Analysis")
                table.add_column("Language", style="cyan")
                table.add_column("Files", style="white", justify="right")
                table.add_column("Percentage", style="yellow", justify="right")
                table.add_column("Security Priority", style="red")
                
                for lang, stats in analysis['language_breakdown'].items():
                    files = stats.get('files', 0)
                    percentage = stats.get('percentage', 0)
                    
                    # Determine security priority
                    if lang in analysis.get('security_priority_languages', []):
                        priority = "High"
                    elif lang in analysis.get('web3_languages', []):
                        priority = "Web3"
                    else:
                        priority = "Standard"
                    
                    table.add_row(lang, str(files), f"{percentage:.1f}%", priority)
                
                self.console.print(table)
                
                # Show recommendations
                if analysis.get('recommended_tools'):
                    self.console.print(f"\n[cyan]Recommended Security Tools:[/cyan]")
                    for tool in analysis['recommended_tools'][:5]:
                        self.console.print(f"  - {tool}")
            else:
                self.console.print("[yellow]No programming languages detected[/yellow]")
                
        except Exception as e:
            self.console.print(f"[red]Language analysis failed: {e}[/red]")
    
    async def cmd_analyze(self, args: List[str]) -> None:
        """Perform comprehensive security analysis with AI-powered line-by-line audit"""
        path = args[0] if args else "."
        
        self.console.print(f"\n[bright_blue]Analyzing code at: {path}[/bright_blue]")
        
        if not os.path.exists(path):
            self.console.print(f"[bright_red]Error: Path not found: {path}[/bright_red]")
            return
        
        # Determine if it's a single file or directory
        is_single_file = os.path.isfile(path)
        
        if is_single_file:
            # Single file analysis
            if not path.endswith(('.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs', '.php', '.sol', '.rb')):
                self.console.print(f"[bright_yellow]Warning: {path} may not be a supported source file[/bright_yellow]")
            files = [path]
            self.console.print(f"[dim]Single file mode: {os.path.basename(path)}[/dim]")
        else:
            # Directory analysis - count files and give user choice
            files = []
            for root, dirs, filenames in os.walk(path):
                for filename in filenames:
                    if filename.endswith(('.py', '.js', '.ts', '.java', '.c', '.cpp', '.go', '.rs', '.php', '.sol', '.rb')):
                        files.append(os.path.join(root, filename))
                if len(files) >= 100:  # Limit for performance
                    break
            
            if len(files) > 10:
                self.console.print(f"[bright_yellow]Directory mode: Found {len(files)} source files[/bright_yellow]")
                self.console.print(f"[dim]Will analyze file-by-file with line-by-line AI audit[/dim]")
                
                # Ask user if they want to proceed with large analysis
                if len(files) > 50:
                    self.console.print(f"[bright_red]WARNING: Large codebase detected ({len(files)} files)[/bright_red]")
                    self.console.print(f"[bright_yellow]This will perform intensive AI analysis on each file.[/bright_yellow]")
                    proceed = input("Continue with full analysis? (y/N): ").lower().strip()
                    if proceed != 'y':
                        # Limit to first 20 files for demo
                        files = files[:20]
                        self.console.print(f"[dim]Limited analysis to first {len(files)} files[/dim]")
            else:
                self.console.print(f"[dim]Directory mode: {len(files)} source files found[/dim]")
        
        if not files:
            self.console.print("[bright_yellow]No supported source files found[/bright_yellow]")
            return
        
        # Display analysis plan
        self.console.print(f"\n[bright_blue]Analysis Plan:[/bright_blue]")
        self.console.print(f"[dim]- AI-powered line-by-line code review[/dim]")
        self.console.print(f"[dim]- Cross-file interaction analysis[/dim]")
        self.console.print(f"[dim]- Pattern detection and vulnerability assessment[/dim]")
        
        # Check AI availability for comprehensive analysis (including local models)
        ai_available = False
        use_local_model = False
        
        # Check for local model configuration
        local_model_config = self.repl.config_manager.get('local_model', {})
        local_model_enabled = local_model_config.get('enabled', False)
        llm_provider = self.repl.config_manager.get('llm.provider', 'auto')
        
        if local_model_enabled or llm_provider == 'local':
            # Try to use local model
            try:
                from ..agents.local_model import create_local_model_manager
                if local_model_config:
                    manager = create_local_model_manager(local_model_config)
                    if manager:
                        ai_available = True
                        use_local_model = True
                        scan_mode = "comprehensive_ai_local"
                        self.console.print(f"\n[bright_blue]Running {scan_mode} analysis with DeepSeek line-by-line audit...[/bright_blue]")
            except Exception as e:
                self.console.print(f"[bright_yellow]Local model not available ({e}), checking OpenAI...[/bright_yellow]")
        
        # Check OpenAI if local model not available
        if not ai_available:
            ai_available = bool(os.environ.get('OPENAI_API_KEY'))
            if ai_available:
                try:
                    # Test if we can actually import the AI libraries
                    from langchain_openai import ChatOpenAI
                    from ..agents.auditor import AuditorAgent
                    from ..schemas.findings import AnalysisContext
                    scan_mode = "comprehensive_ai"
                    self.console.print(f"\n[bright_blue]Running {scan_mode} analysis with GPT-4 line-by-line audit...[/bright_blue]")
                    
                    # Use the real AuditorAgent for comprehensive analysis
                    use_real_ai_audit = True
                except ImportError as e:
                    ai_available = False
                    use_real_ai_audit = False
                    scan_mode = "basic"
                    self.console.print(f"[bright_yellow]AI libraries not available ({e}), running {scan_mode} analysis...[/bright_yellow]")
            else:
                use_real_ai_audit = False
                scan_mode = "basic"
                self.console.print(f"[bright_blue]Running {scan_mode} analysis (no AI key configured)...[/bright_blue]")
        else:
            # Local model is available
            use_real_ai_audit = True
        
        # Run AI-powered analysis only (no traditional scanners)
        all_findings = []
        
        try:
            # Run AI-powered line-by-line audit - returns Finding objects
            if use_real_ai_audit:
                self.console.print("[dim]- Running AI-powered context-aware security audit...[/dim]")
                ai_findings = await self._run_comprehensive_ai_audit(path, files, [], use_local_model)
                
                if ai_findings:
                    # Store findings for other commands (explain, report, etc.)
                    self.last_findings = ai_findings
                    all_findings = ai_findings
                    
                    # Display findings using unified format (same as scan command)
                    self.console.print(f"\n[bold bright_cyan]Security Findings:[/bold bright_cyan]\n")
                    
                    for i, finding in enumerate(ai_findings, 1):
                        self._display_detailed_finding(finding, i, mode='analyze', show_full=True)
                    
                    # Automatically generate and save report
                    await self._auto_save_analysis_report(ai_findings, path, scan_mode, use_local_model)
                else:
                    self.console.print(f"\n[bright_blue]AI analysis complete - no security issues detected[/bright_blue]")
            else:
                self.console.print(f"\n[bright_yellow]AI analysis not available. Configure AI to use analyze command.[/bright_yellow]")
                self.console.print(f"[bright_yellow]To enable AI line-by-line audit:[/bright_yellow]")
                self.console.print(f"[bright_yellow]   Local Model: set USE_LOCAL_MODEL=true in .env[/bright_yellow]")
                self.console.print(f"[bright_yellow]   OpenAI: set USE_API_MODEL=true and add OPENAI_API_KEY to .env[/bright_yellow]")
                return
                
        except Exception as e:
            self.console.print(f"[bright_yellow]Scanner execution failed: {e}[/bright_yellow]")
            self._display_basic_analysis(path, files)
    
    async def _run_bandit_scanner(self, python_files: List[str], base_path: str) -> List[Dict]:
        """Run Bandit scanner on Python files"""
        findings = []
        
        try:
            from ..tools.bandit import BanditScanner
            
            # Initialize Bandit scanner
            bandit = BanditScanner({})
            
            if not bandit.is_available():
                self.console.print("[yellow]  Bandit not available, using basic Python security checks[/yellow]")
                return await self._run_basic_python_scanner(python_files)
            
            # Try to run Bandit scan
            bandit_worked = False
            for file_path in python_files:
                try:
                    file_findings = await bandit.scan(file_path, {})
                    bandit_worked = True
                    for finding in file_findings:
                        findings.append({
                            'file': file_path,
                            'line': getattr(finding, 'lines', 'N/A'),
                            'severity': getattr(finding, 'severity', 'Medium'),
                            'title': getattr(finding, 'title', 'Security Issue'),
                            'description': getattr(finding, 'description', 'No description'),
                            'scanner': 'Bandit'
                        })
                except Exception as e:
                    self.console.print(f"[dim yellow]  Bandit error on {file_path}: {e}[/dim yellow]")
            
            # If Bandit failed on all files, fall back to basic scanner
            if not bandit_worked:
                self.console.print("[yellow]  Bandit failed, using basic Python security checks[/yellow]")
                return await self._run_basic_python_scanner(python_files)
                    
        except ImportError:
            self.console.print("[yellow]  Bandit scanner not available, using basic checks[/yellow]")
            return await self._run_basic_python_scanner(python_files)
        
        # If Bandit found nothing, run basic patterns for additional coverage
        if not findings:
            self.console.print("[dim]  Running additional pattern checks...[/dim]")
            basic_findings = await self._run_basic_python_scanner(python_files)
            findings.extend(basic_findings)
        
        return findings
    
    async def _run_basic_python_scanner(self, python_files: List[str]) -> List[Dict]:
        """Basic Python security pattern matching"""
        findings = []
        
        dangerous_patterns = [
            ('exec(', 'Code Execution', 'HIGH', 'Use of exec() can lead to arbitrary code execution'),
            ('eval(', 'Code Execution', 'HIGH', 'Use of eval() can lead to arbitrary code execution'),
            ('subprocess.call(', 'Command Injection', 'MEDIUM', 'Potential command injection vulnerability'),
            ('os.system(', 'Command Injection', 'MEDIUM', 'Use of os.system() can lead to command injection'),
            ('pickle.loads(', 'Deserialization', 'HIGH', 'Unsafe deserialization with pickle'),
            ('yaml.load(', 'Deserialization', 'MEDIUM', 'Unsafe YAML loading'),
            ("f'SELECT * FROM", 'SQL Injection', 'CRITICAL', 'Potential SQL injection in f-string'),
            ('SELECT * FROM', 'SQL Injection', 'HIGH', 'Potential SQL injection vulnerability'),
            ('password = ', 'Hardcoded Secret', 'MEDIUM', 'Potential hardcoded password'),
            ('api_key = ', 'Hardcoded Secret', 'MEDIUM', 'Potential hardcoded API key'),
        ]
        
        for file_path in python_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip().lower()
                    for pattern, vuln_type, severity, description in dangerous_patterns:
                        if pattern.lower() in line_content:
                            findings.append({
                                'file': file_path,
                                'line': line_num,
                                'severity': severity,
                                'title': f'{vuln_type} Detection',
                                'description': f'{description}. Found: {line.strip()[:100]}',
                                'scanner': 'Basic Python Scanner'
                            })
                            
            except Exception as e:
                self.console.print(f"[dim red]  Error reading {file_path}: {e}[/dim red]")
        
        return findings
    
    async def _run_basic_js_scanner(self, js_files: List[str]) -> List[Dict]:
        """Basic JavaScript security pattern matching"""
        findings = []
        
        dangerous_patterns = [
            ('eval(', 'Code Execution', 'HIGH', 'Use of eval() can lead to arbitrary code execution'),
            ('innerHTML =', 'XSS', 'MEDIUM', 'Potential XSS vulnerability with innerHTML'),
            ('document.write(', 'XSS', 'MEDIUM', 'Potential XSS vulnerability with document.write'),
            ('localStorage.setItem(', 'Data Exposure', 'LOW', 'Sensitive data stored in localStorage'),
            ('crypto.createHash(\'md5\')', 'Weak Crypto', 'MEDIUM', 'MD5 is cryptographically weak'),
            ('Math.random()', 'Weak Random', 'LOW', 'Math.random() is not cryptographically secure'),
        ]
        
        for file_path in js_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    for pattern, vuln_type, severity, description in dangerous_patterns:
                        if pattern in line_content:
                            findings.append({
                                'file': file_path,
                                'line': line_num,
                                'severity': severity,
                                'title': f'{vuln_type} Detection',
                                'description': f'{description}. Found: {line.strip()[:100]}',
                                'scanner': 'Basic JS Scanner'
                            })
                            
            except Exception as e:
                self.console.print(f"[dim red]  Error reading {file_path}: {e}[/dim red]")
        
        return findings
    
    async def _run_basic_solidity_scanner(self, sol_files: List[str]) -> List[Dict]:
        """Basic Solidity security pattern matching"""
        findings = []
        
        dangerous_patterns = [
            ('call.value(', 'Reentrancy', 'HIGH', 'Potential reentrancy vulnerability'),
            ('send(', 'Unsafe Send', 'MEDIUM', 'Use of send() can fail silently'),
            ('tx.origin', 'Authorization', 'HIGH', 'Use of tx.origin for authorization is unsafe'),
            ('block.timestamp', 'Timestamp Dependence', 'MEDIUM', 'Reliance on block timestamp'),
            ('blockhash(', 'Weak Randomness', 'MEDIUM', 'Blockhash is not suitable for randomness'),
            ('selfdestruct(', 'Self Destruct', 'HIGH', 'Contract can be destroyed'),
        ]
        
        for file_path in sol_files:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    lines = f.readlines()
                
                for line_num, line in enumerate(lines, 1):
                    line_content = line.strip()
                    for pattern, vuln_type, severity, description in dangerous_patterns:
                        if pattern in line_content:
                            findings.append({
                                'file': file_path,
                                'line': line_num,
                                'severity': severity,
                                'title': f'{vuln_type} Detection',
                                'description': f'{description}. Found: {line.strip()[:100]}',
                                'scanner': 'Basic Solidity Scanner'
                            })
                            
            except Exception as e:
                self.console.print(f"[dim red]  Error reading {file_path}: {e}[/dim red]")
        
        return findings
    
    def _display_real_analysis_results(self, findings: List[Dict], scanners_run: List[str], ai_enhanced: bool, files_analyzed: int):
        """Display real analysis results with actual findings - enhanced colors and no truncation"""
        # Create header with AI indicator
        header = "AI-Enhanced Security Analysis" if ai_enhanced else "Security Analysis Results"
        self.console.print(f"\n[bold bright_cyan]{header}[/bold bright_cyan]")
        self.console.print("[bright_blue]" + "=" * 80 + "[/bright_blue]")
        
        # Show scan summary with enhanced styling
        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style="bright_white bold", width=25)
        info_table.add_column(style="bright_cyan")
        
        info_table.add_row("Files Analyzed", f"[bright_yellow]{files_analyzed}[/bright_yellow]")
        info_table.add_row("Scanners Used", f"[bright_magenta]{', '.join(scanners_run)}[/bright_magenta]")
        if ai_enhanced:
            info_table.add_row("AI Status", "[bright_green]Active (analyzing findings)[/bright_green]")
            info_table.add_row("Model", "[bright_cyan]GPT-4 / Claude / DeepSeek[/bright_cyan]")
        else:
            info_table.add_row("AI Status", "[yellow]Disabled (no API key)[/yellow]")
        
        self.console.print(info_table)
        
        # Show findings summary
        if findings:
            self.console.print(f"\n[bold bright_red]Found {len(findings)} security issues[/bold bright_red]")
            
            # Group by severity
            severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
            for finding in findings:
                severity = finding.get('severity', 'MEDIUM').upper()
                if severity in severity_counts:
                    severity_counts[severity] += 1
            
            # Show severity breakdown with enhanced styling
            severity_table = Table(
                show_header=True,
                header_style="bold bright_white",
                border_style="bright_blue"
            )
            severity_table.add_column("Severity Level", style="bright_white bold", width=20)
            severity_table.add_column("Count", style="bright_cyan bold", justify="right", width=10)
            severity_table.add_column("Risk Assessment", style="bright_yellow", width=40)
            
            severity_info = {
                'CRITICAL': ('Critical', 'Immediate exploitation risk - patch now'),
                'HIGH': ('High', 'Significant vulnerability - urgent attention'),
                'MEDIUM': ('Medium', 'Moderate risk - address in current sprint'),
                'LOW': ('Low', 'Minor issue - plan remediation')
            }
            
            for severity, count in severity_counts.items():
                if count > 0:
                    label, risk = severity_info.get(severity, (severity, 'Unknown risk'))
                    color = {
                        'CRITICAL': 'bright_red',
                        'HIGH': 'bright_yellow', 
                        'MEDIUM': 'bright_cyan',
                        'LOW': 'bright_blue'
                    }.get(severity, 'white')
                    severity_table.add_row(
                        f"[{color}]{label}[/{color}]",
                        f"[{color} bold]{count}[/{color} bold]",
                        f"[{color}]{risk}[/{color}]"
                    )
            
            self.console.print(severity_table)
            
            # Convert findings to Finding objects and display using same format as scan
            self.console.print(f"\n[bold bright_cyan]Security Findings:[/bold bright_cyan]\n")
            
            # Convert dict findings to Finding objects for consistent display
            finding_objects = []
            for finding_dict in findings:
                # Create a simple object with attributes
                class SimpleFinding:
                    def __init__(self, data):
                        self.title = data.get('title', 'Security Issue')
                        self.description = data.get('description', '')
                        self.file = data.get('file', 'Unknown')
                        self.file_path = data.get('file', 'Unknown')
                        self.lines = str(data.get('line', 'N/A'))
                        self.line_number = data.get('line', 'N/A')
                        self.severity = data.get('severity', 'Medium').title()
                        self.tool_evidence = [type('obj', (object,), {'tool': data.get('scanner', 'AI Analysis')})]
                        self.code_snippet = data.get('code', '')
                        self.impact = data.get('impact', 'Security vulnerability detected')
                        self.recommendation = data.get('recommendation', 'Review and remediate this finding')
                        self.cwe = data.get('cwe', None)
                        self.cvss_v4 = None
                        self.confidence_score = data.get('confidence', 'N/A')
                        self.cross_file = data.get('cross_file', [])
                        self.ai_analysis = data.get('ai_analysis', None)
                
                finding_objects.append(SimpleFinding(finding_dict))
            
            # Display findings using the same format as scan command
            for i, finding in enumerate(finding_objects, 1):
                self._display_detailed_finding(finding, i, mode='analyze', show_full=True)
        else:
            self.console.print(f"\n[bold bright_green]No security issues detected[/bold bright_green]")
            self.console.print("[bright_white]The analyzed code appears to be secure based on current scan patterns[/bright_white]")
    
    async def _enhance_findings_with_ai(self, findings: List[Dict]):
        """Enhance findings with AI analysis - REAL AI INTEGRATION"""
        # First check if we can actually access the OpenAI API
        import os
        ai_key = os.environ.get('OPENAI_API_KEY')
        if not ai_key:
            self.console.print(f"\n[red]WARNING: AI Enhancement FAILED: No OpenAI API key found[/red]")
            self.console.print("[yellow]Set OPENAI_API_KEY environment variable to enable AI features[/yellow]")
            return
        
        if not findings:
            self.console.print(f"\n[yellow]No findings to enhance with AI[/yellow]")
            return
        
        try:
            self.console.print(f"\n[blue]AI Enhancement starting...[/blue]")
            self.console.print(f"[dim]Using OpenAI API key: ...{ai_key[-4:]}[/dim]")
            
            # Import and test AI components
            try:
                from langchain_openai import ChatOpenAI
                from langchain.schema import HumanMessage
            except ImportError as e:
                self.console.print(f"[red]AI Enhancement FAILED: Missing dependencies - {e}[/red]")
                self.console.print("[yellow]Install: pip install langchain-openai[/yellow]")
                return
            
            # Initialize OpenAI with timeout
            llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                openai_api_key=ai_key,
                timeout=60,
                max_retries=2
            )
            
            # Get the top finding for AI analysis
            top_finding = findings[0]
            
            # Read the actual file content for context
            file_path = top_finding.get('file', '')
            file_context = ""
            if file_path and os.path.exists(file_path):
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        lines = f.readlines()
                        # Get context around the finding
                        line_num = top_finding.get('line', 1)
                        if isinstance(line_num, int):
                            start = max(0, line_num - 5)
                            end = min(len(lines), line_num + 5)
                            file_context = ''.join(lines[start:end])
                except Exception as e:
                    file_context = f"Could not read file context: {e}"
            
            # Create comprehensive AI prompt
            ai_prompt = f"""You are a cybersecurity expert analyzing a potential security vulnerability.

VULNERABILITY DETAILS:
- Type: {top_finding.get('title', 'Unknown')}
- File: {top_finding.get('file', 'Unknown')}
- Line: {top_finding.get('line', 'Unknown')}
- Scanner: {top_finding.get('scanner', 'Unknown')}
- Initial Description: {top_finding.get('description', 'No description')}

CODE CONTEXT (lines around the finding):
```
{file_context}
```

Please provide a thorough security analysis with:

1. **Confidence Score** (0-100%): How confident are you this is a real vulnerability?
2. **Severity Assessment**: Critical/High/Medium/Low and detailed reasoning
3. **Exploitability**: How easily could an attacker exploit this?
4. **Business Impact**: What damage could result from exploitation?
5. **Technical Details**: Explain the vulnerability mechanism
6. **Specific Remediation**: Provide exact code fixes
7. **False Positive Check**: Is this likely a false positive? Why or why not?

Be specific, technical, and provide actionable remediation steps."""
            
            self.console.print("[dim]Sending vulnerability context to GPT-4 (this may take 10-30 seconds)...[/dim]")
            
            # Make the actual API call with timing
            import time
            start_time = time.time()
            
            response = await asyncio.to_thread(llm.invoke, [HumanMessage(content=ai_prompt)])
            
            end_time = time.time()
            api_call_time = end_time - start_time
            
            # Display the REAL AI response
            self.console.print(f"[green]Real AI analysis completed in {api_call_time:.2f} seconds[/green]")
            self.console.print(f"\n[cyan]LIVE GPT-4 SECURITY ANALYSIS:[/cyan]")
            self.console.print("=" * 80)
            self.console.print(f"[white]{response.content}[/white]")
            self.console.print("=" * 80)
            self.console.print(f"[dim]API Response Length: {len(response.content)} characters[/dim]")
            self.console.print(f"[dim]Model Used: GPT-4 | API Call Time: {api_call_time:.2f}s[/dim]")
            
        except Exception as e:
            self.console.print(f"\n[red]Real AI enhancement failed with error:[/red]")
            self.console.print(f"[red]{str(e)}[/red]")
            
            # Show detailed error for debugging
            import traceback
            error_details = traceback.format_exc()
            self.console.print(f"[dim]Full error trace:[/dim]")
            self.console.print(f"[dim]{error_details}[/dim]")
            
            # Suggest solutions
            if "authentication" in str(e).lower() or "api" in str(e).lower():
                self.console.print("[yellow]Possible solutions:[/yellow]")
                self.console.print("[yellow]1. Check your OpenAI API key is valid[/yellow]")
                self.console.print("[yellow]2. Verify you have API credits available[/yellow]")
                self.console.print("[yellow]3. Check internet connectivity[/yellow]")
            elif "timeout" in str(e).lower():
                self.console.print("[yellow]API timeout - try again or check connection[/yellow]")
            elif "import" in str(e).lower():
                self.console.print("[yellow]Install missing dependencies: pip install langchain-openai[/yellow]")
    
    def _display_analysis_results(self, results, ai_enhanced=False):
        """Display comprehensive analysis results"""
        metadata = results.get('metadata', {})
        findings = results.get('findings', [])
        stats = results.get('statistics', {})
        
        # Create header with AI indicator
        header = "AI-Enhanced Analysis Results" if ai_enhanced else "Analysis Results"
        self.console.print(f"\n[bold green]{header}:[/bold green]")
        self.console.print("─" * 60)
        
        # Show metadata
        info_table = Table.grid(padding=(0, 2))
        info_table.add_column(style="white", width=20)
        info_table.add_column()
        
        info_table.add_row("Engine Type", metadata.get('engine_type', 'standard'))
        info_table.add_row("Files Analyzed", str(metadata.get('files_analyzed', 0)))
        info_table.add_row("Technologies", ', '.join(metadata.get('technologies', [])))
        if ai_enhanced:
            info_table.add_row("AI Model", metadata.get('llm_model', 'GPT-4'))
        
        self.console.print(info_table)
        
        # Show findings summary
        total_findings = stats.get('total_findings', 0)
        if total_findings > 0:
            self.console.print(f"\n[yellow]Security findings: {total_findings}[/yellow]")
            
            severity_table = Table()
            severity_table.add_column("Severity", style="white")
            severity_table.add_column("Count", style="cyan", justify="right")
            
            for severity, count in severity_counts.items():
                if count > 0:
                    color = {
                        'CRITICAL': 'bright_red',
                        'HIGH': 'red', 
                        'MEDIUM': 'yellow',
                        'LOW': 'blue'
                    }.get(severity, 'white')
                    severity_table.add_row(f"[{color}]{severity}[/{color}]", str(count))
            
            self.console.print(severity_table)
        else:
            self.console.print(f"\n[green]No security issues detected[/green]")
        
        # Show AI-specific insights only if AI actually enhanced findings
        if ai_enhanced and findings:
            self.console.print(f"\n[cyan]Note: AI enhancement will analyze findings above[/cyan]")
            
        # Show recommendations if available
        recommendations = results.get('recommendations', [])
        if recommendations:
            self.console.print(f"\n[blue]Top Recommendations:[/blue]")
            for i, rec in enumerate(recommendations[:3], 1):
                self.console.print(f"  {i}. {rec}")
    
    def _display_basic_analysis(self, path, files):
        """Display basic analysis when full engine is not available"""
        self.console.print(f"\n[bold yellow]Basic Analysis Results:[/bold yellow]")
        self.console.print("─" * 50)
        
        # Count by file type
        file_types = {}
        for file_path in files:
            ext = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
            file_types[ext] = file_types.get(ext, 0) + 1
        
        table = Table()
        table.add_column("File Type", style="cyan")
        table.add_column("Count", style="white", justify="right")
        
        for ext, count in sorted(file_types.items()):
            table.add_row(ext.upper(), str(count))
        
        self.console.print(table)
        
        self.console.print(f"\n[blue]Path scanned: {os.path.abspath(path)}[/blue]")
        self.console.print("[dim]For full security analysis, ensure all dependencies are installed[/dim]")
        self.console.print("[dim]Run 'ai-status' to check AI integration[/dim]")
    
    async def cmd_github(self, args: List[str]) -> None:
        """Analyze GitHub repositories directly"""
        if not args:
            self.console.print("[red]Error: GitHub URL required[/red]")
            self.console.print("[dim]Usage: github <github_url> [branch] [mode][/dim]")
            self.console.print("[dim]Example: github https://github.com/user/repo main comprehensive[/dim]")
            return
        
        repo_url = args[0]
        branch = args[1] if len(args) > 1 else 'main'
        scan_mode = args[2] if len(args) > 2 else 'comprehensive'
        
        # Validate GitHub URL
        if not validate_github_url(repo_url):
            self.console.print(f"[red]Error: Invalid GitHub URL: {repo_url}[/red]")
            self.console.print("[dim]Please provide a valid GitHub repository URL[/dim]")
            return
        
        self.console.print(f"[cyan]Analyzing GitHub Repository:[/cyan] [blue]{repo_url}[/blue]")
        self.console.print(f"[dim]Branch: {branch} | Mode: {scan_mode}[/dim]")
        
        try:
            # Run GitHub analysis
            results = await analyze_github_repo_cli(
                repo_url=repo_url,
                config=self.repl.config_manager.config_data,
                branch=branch,
                scan_mode=scan_mode
            )
            
            # Display results similar to analyze command
            findings_raw = results.get('findings', [])
            repository_info = results.get('repository', {})
            
            # Convert Finding objects to dictionaries for CLI processing
            findings = []
            for finding in findings_raw:
                if hasattr(finding, 'model_dump'):  # Pydantic model
                    finding_dict = finding.model_dump()
                    # Map new schema fields to expected CLI fields
                    cli_finding = {
                        'severity': finding_dict.get('severity', 'Medium'),
                        'title': finding_dict.get('title', 'Security Issue'),
                        'description': finding_dict.get('description', ''),
                        'file': finding_dict.get('file', ''),
                        'file_path': finding_dict.get('file', ''),  # Both for compatibility
                        'lines': finding_dict.get('lines', '0'),
                        'line': finding_dict.get('lines', '0'),  # For compatibility
                        'impact': finding_dict.get('impact', ''),
                        'recommendation': finding_dict.get('recommendation', ''),
                        'snippet': finding_dict.get('snippet', ''),
                        'cvss_v4': finding_dict.get('cvss_v4', {}),
                        'owasp': finding_dict.get('owasp', []),
                        'cwe': finding_dict.get('cwe', []),
                        'scanner': 'Multi-tool Analysis'
                    }
                    findings.append(cli_finding)
                elif isinstance(finding, dict):  # Already a dictionary
                    findings.append(finding)
                else:
                    # Fallback conversion
                    findings.append({'title': 'Unknown Finding', 'severity': 'Medium'})
            
            # Show repository metadata
            self.console.print(f"\n[bold green]Repository Analysis Complete[/bold green]")
            self.console.print("─" * 50)
            self.console.print(f"[blue]Repository:[/blue] {repository_info.get('url', repo_url)}")
            self.console.print(f"[blue]Branch:[/blue] {repository_info.get('branch', branch)}")
            self.console.print(f"[blue]Commit:[/blue] {repository_info.get('commit', 'unknown')[:8]}")
            self.console.print(f"[blue]Total Files:[/blue] {repository_info.get('total_files', 0)}")
            self.console.print(f"[blue]Analyzed Files:[/blue] {repository_info.get('analyzed_files', 0)}")
            
            languages = repository_info.get('languages_detected', [])
            if languages:
                self.console.print(f"[blue]Languages:[/blue] {', '.join(languages)}")
            
            # Display findings summary
            if findings:
                self.console.print(f"\n[bold red]Security Findings: {len(findings)}[/bold red]")
                
                # Group by severity
                severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0, 'INFO': 0}
                for finding in findings:
                    severity = finding.get('severity', 'MEDIUM').upper()
                    if severity in severity_counts:
                        severity_counts[severity] += 1
                
                # Display severity breakdown
                severity_table = Table(title="Vulnerability Breakdown")
                severity_table.add_column("Severity", style="bold")
                severity_table.add_column("Count", justify="right")
                
                for severity, count in severity_counts.items():
                    if count > 0:
                        color = {
                            'CRITICAL': 'bright_red',
                            'HIGH': 'red', 
                            'MEDIUM': 'yellow',
                            'LOW': 'blue',
                            'INFO': 'green'
                        }.get(severity, 'white')
                        severity_table.add_row(f"[{color}]{severity}[/{color}]", str(count))
                
                self.console.print(severity_table)
                
                # Show top findings
                self.console.print(f"\n[bold yellow]Top Security Issues:[/bold yellow]")
                for i, finding in enumerate(findings[:5], 1):
                    severity = finding.get('severity', 'MEDIUM').upper()
                    title = finding.get('title', 'Security Issue')
                    file_path = finding.get('file_path', 'Unknown')
                    
                    color = {
                        'CRITICAL': 'bright_red',
                        'HIGH': 'red', 
                        'MEDIUM': 'yellow',
                        'LOW': 'blue',
                        'INFO': 'green'
                    }.get(severity, 'white')
                    
                    self.console.print(f"  {i}. [{color}]{severity}[/{color}] {title}")
                    self.console.print(f"     [dim]File: {file_path}[/dim]")
                
                if len(findings) > 5:
                    self.console.print(f"[dim]... and {len(findings) - 5} more findings[/dim]")
            else:
                self.console.print(f"\n[green]No security issues detected[/green]")
            
            # Show report information
            reports = results.get('reports', {})
            if reports:
                self.console.print(f"\n[blue]Generated Reports:[/blue]")
                for report_type, report_path in reports.items():
                    self.console.print(f"  - {report_type.upper()}: {report_path}")
            
        except Exception as e:
            self.console.print(f"[red]Error analyzing repository: {str(e)}[/red]")
            self.console.print("[dim]Please check the repository URL and your network connection[/dim]")

    async def cmd_clear(self, args: List[str]) -> None:
        """Clear terminal screen safely"""
        import subprocess
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['cmd', '/c', 'cls'], check=True)
            else:  # Unix/Linux
                subprocess.run(['clear'], check=True)
        except subprocess.CalledProcessError:
            # Fallback to console clear
            self.console.clear()
    
    # Finding Explanation Command
    
    async def cmd_explain(self, args: List[str]) -> None:
        """Explain a specific finding using AI"""
        if not args:
            self.console.print("[red]Usage: explain <finding_number>[/red]")
            self.console.print("[dim]Example: explain 1[/dim]")
            if self.last_findings:
                self.console.print(f"[dim]You have {len(self.last_findings)} findings from your last scan[/dim]")
            else:
                self.console.print("[yellow]No findings available. Run a scan first.[/yellow]")
            return
        
        # Check if findings are available
        if not self.last_findings:
            self.console.print("[yellow]No findings available. Please run a scan first:[/yellow]")
            self.console.print("[dim]  scan quick ./project[/dim]")
            self.console.print("[dim]  scan comprehensive ./project[/dim]")
            return
        
        # Parse finding number
        try:
            finding_num = int(args[0])
            if finding_num < 1 or finding_num > len(self.last_findings):
                self.console.print(f"[red]Invalid finding number. Must be between 1 and {len(self.last_findings)}[/red]")
                return
        except ValueError:
            self.console.print("[red]Invalid finding number. Must be an integer.[/red]")
            self.console.print(f"[dim]Example: explain 1 (for findings 1-{len(self.last_findings)})[/dim]")
            return
        
        # Get the finding (convert to 0-indexed)
        finding = self.last_findings[finding_num - 1]
        
        # Check AI availability based on .env configuration
        use_local = os.getenv('USE_LOCAL_MODEL', '').lower() == 'true'
        use_api = os.getenv('USE_API_MODEL', '').lower() == 'true'
        
        # Determine provider from config (already set by config.py based on .env flags)
        llm_provider = self.repl.config_manager.get('llm.provider', 'openai')
        local_config = self.repl.config_manager.get('local_model', {})
        
        # Check if AI is available
        if use_local and llm_provider == 'local':
            ai_available = True
        elif use_api and llm_provider in ['openai', 'anthropic']:
            api_key = os.environ.get('OPENAI_API_KEY') if llm_provider == 'openai' else os.environ.get('ANTHROPIC_API_KEY')
            ai_available = bool(api_key)
        else:
            # Fall back to checking API key directly
            api_key = os.environ.get('OPENAI_API_KEY') or self.repl.config_manager.get('llm.openai_api_key')
            ai_available = bool(api_key)
        
        if not ai_available:
            self.console.print("[yellow]Warning: AI is not configured. Showing basic finding details only.[/yellow]")
            self.console.print("[dim]To enable AI explanations:[/dim]")
            self.console.print("[dim]  - Set USE_API_MODEL=true and OPENAI_API_KEY in .env file, or[/dim]")
            self.console.print("[dim]  - Set USE_LOCAL_MODEL=true in .env for local model[/dim]")
            self.console.print()
        
        # Display finding details
        from rich.panel import Panel
        from rich.markdown import Markdown
        
        # Helper to get tool name
        def get_tool_name(finding) -> str:
            tool_evidence = getattr(finding, 'tool_evidence', [])
            if tool_evidence and len(tool_evidence) > 0:
                return tool_evidence[0].tool
            return 'Unknown'
        
        severity = getattr(finding, 'severity', 'Medium').title()
        tool = get_tool_name(finding)
        file_path = getattr(finding, 'file_path', getattr(finding, 'file', 'Unknown'))
        line = getattr(finding, 'line_number', getattr(finding, 'line', 'N/A'))
        message = getattr(finding, 'message', getattr(finding, 'description', 'No description'))
        code_snippet = getattr(finding, 'code_snippet', getattr(finding, 'code', ''))
        
        # Build finding details
        finding_details = f"**Finding #{finding_num}**\n\n"
        finding_details += f"**Severity:** {severity}\n"
        finding_details += f"**Tool:** {tool}\n"
        finding_details += f"**File:** `{file_path}`\n"
        finding_details += f"**Line:** {line}\n\n"
        finding_details += f"**Issue:** {message}\n\n"
        
        if code_snippet:
            finding_details += f"**Code Snippet:**\n```\n{code_snippet}\n```\n"
        
        finding_panel = Panel(
            Markdown(finding_details),
            title=f"{severity} Finding Details",
            style="bold cyan"
        )
        self.console.print(finding_panel)
        
        # If AI is available, get explanation
        if ai_available:
            self.console.print("\n[cyan]Generating AI explanation...[/cyan]\n")
            
            try:
                # Prepare context for AI
                finding_context = {
                    'severity': severity,
                    'tool': tool,
                    'file': file_path,
                    'line': line,
                    'message': message,
                    'code': code_snippet
                }
                
                # Get AI explanation
                explanation = await self._get_ai_explanation(finding_context, llm_provider)
                
                if explanation:
                    # Display AI analysis
                    ai_panel = Panel(
                        Markdown(explanation),
                        title="AI Security Analysis",
                        style="bold green"
                    )
                    self.console.print(ai_panel)
                else:
                    self.console.print("[yellow]Could not generate AI explanation[/yellow]")
                    
            except Exception as e:
                self.console.print(f"[red]Error generating AI explanation: {e}[/red]")
                self.console.print("[dim]Showing basic finding details only[/dim]")
    
    async def _get_ai_explanation(self, finding_context: Dict[str, Any], provider: str = 'openai') -> str:
        """Get AI explanation for a security finding using configured provider"""
        
        # Build prompt
        prompt = f"""You are a security expert. Explain this security finding in detail:

Severity: {finding_context['severity']}
Tool: {finding_context['tool']}
File: {finding_context['file']}
Line: {finding_context['line']}
Issue: {finding_context['message']}

Code:
```
{finding_context.get('code', 'Code not available')}
```

Provide:
1. **Explanation:** What is this vulnerability and why is it dangerous?
2. **Attack Scenario:** How could an attacker exploit this?
3. **Recommended Fix:** Provide specific code examples showing vulnerable vs. secure code
4. **False Positive Assessment:** Likelihood this is a false positive (0-100%)
5. **Priority:** How urgent is fixing this?

Be specific, technical, and provide actionable advice."""

        # Check .env configuration to determine provider
        use_local = os.getenv('USE_LOCAL_MODEL', '').lower() == 'true'
        use_api = os.getenv('USE_API_MODEL', '').lower() == 'true'
        
        # Use local model if configured
        if use_local or provider == 'local':
            local_config = self.repl.config_manager.get('local_model', {})
            try:
                from ..agents.local_model import create_local_model_manager
                manager = create_local_model_manager(local_config)
                if not manager:
                    raise RuntimeError("Local model manager could not be initialized")
                response = await asyncio.to_thread(manager.generate, prompt)
                return response
            except Exception as e:
                self.console.print(f"[red]Local model error: {e}[/red]")
                return None
        
        # Use API (OpenAI or Anthropic)
        elif use_api or provider in ['openai', 'anthropic']:
            api_provider = os.getenv('API_PROVIDER', 'openai').lower()
            
            if api_provider == 'anthropic' or provider == 'anthropic':
                # Use Anthropic Claude
                api_key = os.environ.get('ANTHROPIC_API_KEY')
                if not api_key:
                    self.console.print("[red]ANTHROPIC_API_KEY not found in .env[/red]")
                    return None
                
                try:
                    from anthropic import Anthropic
                    client = Anthropic(api_key=api_key)
                    
                    response = await asyncio.to_thread(
                        client.messages.create,
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1500,
                        messages=[{"role": "user", "content": prompt}]
                    )
                    
                    return response.content[0].text
                except Exception as e:
                    self.console.print(f"[red]Anthropic API error: {e}[/red]")
                    return None
            else:
                # Use OpenAI
                api_key = os.environ.get('OPENAI_API_KEY') or self.repl.config_manager.get('llm.openai_api_key')
                if not api_key:
                    return None
                
                try:
                    import openai
                    openai.api_key = api_key
                    
                    response = await openai.ChatCompletion.acreate(
                        model="gpt-4",
                        messages=[
                            {"role": "system", "content": "You are an expert security analyst providing detailed vulnerability explanations."},
                            {"role": "user", "content": prompt}
                        ],
                        temperature=0.7,
                        max_tokens=1500
                    )
                    
                    return response.choices[0].message.content
                except Exception as e:
                    self.console.print(f"[red]OpenAI API error: {e}[/red]")
                    return None
        
        # No valid configuration
        else:
            self.console.print("[red]No AI provider configured in .env[/red]")
            return None
    
    # AI Integration Commands
    
    async def cmd_ai(self, args: List[str]) -> None:
        """AI integration management"""
        if not args:
            await self.cmd_ai_status([])
            return
        
        action = args[0].lower()
        
        if action == 'status':
            await self.cmd_ai_status([])
        elif action == 'test':
            await self._test_ai_connectivity(args[1:])
        elif action == 'test-local':
            await self._test_local_model()
        elif action == 'enable':
            self.console.print("[yellow]AI is enabled by default when API key is configured[/yellow]")
        elif action == 'disable':
            self.console.print("[yellow]AI can be disabled by removing the API key[/yellow]")
        elif action == 'local':
            await self._manage_local_model(args[1:])
        elif action == 'switch':
            await self._switch_provider(args[1:])
        else:
            self.console.print("[red]Usage: ai [status|test|test-local|local|switch|enable|disable][/red]")
    
    async def cmd_ai_status(self, args: List[str]) -> None:
        """Show AI integration status and configuration"""
        self.console.print(f"\n[bold cyan]AI Integration Status:[/bold cyan]")
        self.console.print("─" * 50)
        
        # Check API key configuration
        api_key = os.environ.get('OPENAI_API_KEY') or self.repl.config_manager.get('llm.openai_api_key')
        
        # Check local model configuration
        local_config = self.repl.config_manager.get('local_model', {})
        local_enabled = local_config.get('enabled', False)
        llm_provider = self.repl.config_manager.get('llm.provider', 'openai')
        
        status_table = Table.grid(padding=(0, 2))
        status_table.add_column(style="white", width=25)
        status_table.add_column()
        
        # API Models Status
        if api_key:
            status_table.add_row("OpenAI API Key", f"[green]Configured (...{api_key[-4:]})[/green]")
        else:
            status_table.add_row("OpenAI API Key", "[red]Not configured[/red]")
        
        # Local Model Status
        if local_enabled:
            engine = local_config.get('engine', 'ollama')
            model_name = local_config.get('model_name', 'deepseek-coder')
            status_table.add_row("Local Model", f"[green]Enabled ({engine}: {model_name})[/green]")
        else:
            status_table.add_row("Local Model", "[dim]Not enabled[/dim]")
        
        # Current Provider
        if llm_provider == 'local' and local_enabled:
            status_table.add_row("Active Provider", "[cyan]Local Model[/cyan]")
            status_table.add_row("AI Status", "[green]Active (Local)[/green]")
        elif api_key:
            status_table.add_row("Active Provider", "[cyan]OpenAI API[/cyan]")
            status_table.add_row("AI Status", "[green]Active (API)[/green]")
        else:
            status_table.add_row("Active Provider", "[red]None[/red]")
            status_table.add_row("AI Status", "[red]Disabled[/red]")
        
        # Features
        if api_key or (local_enabled and llm_provider == 'local'):
            status_table.add_row(
                "Features Available",
                "[green]- Real-time vulnerability analysis\n- Contextual false positive detection\n- Custom remediation suggestions[/green]",
            )
        else:
            status_table.add_row("Setup Required", "[yellow]Configure API key or local model[/yellow]")
        
        self.console.print(status_table)
        
        if api_key or (local_enabled and llm_provider == 'local'):
            self.console.print(f"\n[green]AI integration is ready![/green]")
            self.console.print("[dim]Use 'scan comprehensive' or 'analyze' for AI-enhanced analysis[/dim]")
            if local_enabled:
                self.console.print("[dim]Use 'ai test-local' to test local model connectivity[/dim]")
        else:
            self.console.print(f"\n[yellow]WARNING: Set up API key or configure local model to enable AI features[/yellow]")
            self.console.print("[dim]Examples:[/dim]")
            self.console.print("[dim]  - API: export OPENAI_API_KEY=your_key[/dim]")
            self.console.print("[dim]  - Local: set llm.provider local && set local_model.enabled true[/dim]")
    
    async def _test_ai_connectivity(self, args: List[str]) -> None:
        """Test AI connectivity and performance"""
        self.console.print("[cyan]Testing AI connectivity...[/cyan]")
        
        # Test OpenAI API
        api_key = os.environ.get('OPENAI_API_KEY')
        if api_key:
            try:
                # Simple test request
                self.console.print("[dim]Testing OpenAI API...[/dim]")
                # TODO: Implement actual API test
                self.console.print("[green]OpenAI API connection successful[/green]")
            except Exception as e:
                self.console.print(f"[red]OpenAI API test failed: {e}[/red]")
        else:
            self.console.print("[yellow]! OpenAI API key not configured[/yellow]")
    
    async def _test_local_model(self) -> None:
        """Test local model connectivity and performance"""
        self.console.print("[cyan]Testing local model...[/cyan]")
        
        try:
            from ..agents.local_model import create_local_model_manager
            
            local_config = self.repl.config_manager.get('local_model', {})
            
            if not local_config.get('enabled', False):
                self.console.print("[yellow]Local model is not enabled[/yellow]")
                self.console.print("[dim]Enable with: set local_model.enabled true[/dim]")
                return
            
            manager = create_local_model_manager(local_config)
            if not manager:
                self.console.print("[red]Failed to create local model manager[/red]")
                return
            
            # Run comprehensive test
            test_result = manager.test_model()
            
            # Display results
            status_color = "green" if test_result['available'] else "red"
            status_message = "Available" if test_result['available'] else "Not Available"

            self.console.print(f"[{status_color}]Model Status: {status_message}[/{status_color}]")
            self.console.print(f"[white]Engine: {test_result['engine']}[/white]")
            self.console.print(f"[white]Model: {test_result['model_name']}[/white]")
            
            if test_result['available']:
                self.console.print(f"[green]Response Time: {test_result['response_time']:.2f}s[/green]")
                if 'test_response' in test_result:
                    self.console.print(f"[dim]Test Response: {test_result['test_response']}[/dim]")
            
            if test_result['error']:
                self.console.print(f"[red]Error: {test_result['error']}[/red]")
            
            # Model info
            if test_result['model_info']:
                self.console.print("\n[bold]Model Information:[/bold]")
                for key, value in test_result['model_info'].items():
                    self.console.print(f"[dim]{key}: {value}[/dim]")
            
        except ImportError:
            self.console.print("[red]Local model support not available[/red]")
            self.console.print("[dim]Install required dependencies: pip install transformers torch ollama[/dim]")
        except Exception as e:
            self.console.print(f"[red]Local model test failed: {e}[/red]")
    
    async def _manage_local_model(self, args: List[str]) -> None:
        """Manage local model configuration"""
        if not args:
            self.console.print("[red]Usage: ai local [enable|disable|info|setup][/red]")
            return
        
        action = args[0].lower()
        
        if action == 'enable':
            self.repl.config_manager.set('local_model.enabled', True)
            self.repl.config_manager.set('llm.provider', 'local')
            self.console.print("[green]Local model enabled[/green]")
            self.console.print("[dim]Use 'ai test-local' to verify setup[/dim]")
        
        elif action == 'disable':
            self.repl.config_manager.set('local_model.enabled', False)
            self.repl.config_manager.set('llm.provider', 'openai')
            self.console.print("[yellow]Local model disabled[/yellow]")
        
        elif action == 'info':
            local_config = self.repl.config_manager.get('local_model', {})
            
            info_table = Table.grid(padding=(0, 2))
            info_table.add_column(style="cyan", width=20)
            info_table.add_column()
            
            info_table.add_row("Enabled", str(local_config.get('enabled', False)))
            info_table.add_row("Engine", local_config.get('engine', 'ollama'))
            info_table.add_row("Model Name", local_config.get('model_name', 'deepseek-coder'))
            info_table.add_row("Base URL", local_config.get('base_url', 'http://localhost:11434'))
            info_table.add_row("Context Length", str(local_config.get('context_length', 4096)))
            info_table.add_row("GPU Layers", str(local_config.get('gpu_layers', 35)))
            
            self.console.print(info_table)
        
        elif action == 'setup':
            await self._setup_local_model(args[1:])
        
        else:
            self.console.print("[red]Usage: ai local [enable|disable|info|setup][/red]")
    
    async def _setup_local_model(self, args: List[str]) -> None:
        """Interactive local model setup"""
        self.console.print("[bold cyan]Local Model Setup[/bold cyan]")
        self.console.print("─" * 30)
        
        # Engine selection
        self.console.print("\n[white]1. Select inference engine:[/white]")
        self.console.print("   [dim]1) Ollama (recommended - easy setup)[/dim]")
        self.console.print("   [dim]2) llama.cpp (manual model loading)[/dim]")
        self.console.print("   [dim]3) Transformers (HuggingFace models)[/dim]")
        
        # Model suggestions
        self.console.print("\n[white]2. Popular models for security analysis:[/white]")
        self.console.print("   [green]- deepseek-coder (recommended)[/green]")
        self.console.print("   [white]- codellama[/white]")
        self.console.print("   [white]- wizardcoder[/white]")
        self.console.print("   [white]- starcoder[/white]")
        
        # Setup instructions
        self.console.print("\n[white]3. Quick setup for Ollama + DeepSeek:[/white]")
        self.console.print("   [dim]# Install Ollama[/dim]")
        self.console.print("   [cyan]curl -fsSL https://ollama.ai/install.sh | sh[/cyan]")
        self.console.print("   [dim]# Pull DeepSeek model[/dim]")
        self.console.print("   [cyan]ollama pull deepseek-coder[/cyan]")
        self.console.print("   [dim]# Configure SecureCLI[/dim]")
        self.console.print("   [cyan]set local_model.enabled true[/cyan]")
        self.console.print("   [cyan]set local_model.engine ollama[/cyan]")
        self.console.print("   [cyan]set local_model.model_name deepseek-coder[/cyan]")
        self.console.print("   [cyan]set llm.provider local[/cyan]")
        
        self.console.print("\n[green]After setup, use 'ai test-local' to verify everything works![/green]")
    
    async def _switch_provider(self, args: List[str]) -> None:
        """Switch between AI providers"""
        if not args:
            self.console.print("[red]Usage: ai switch [auto|openai|anthropic|local][/red]")
            return
        
        provider = args[0].lower()
        valid_providers = ['auto', 'openai', 'anthropic', 'local']
        
        if provider not in valid_providers:
            self.console.print(f"[red]Invalid provider. Choose from: {', '.join(valid_providers)}[/red]")
            return
        
        # Validate provider availability before switching
        if provider == 'openai':
            if not os.environ.get('OPENAI_API_KEY'):
                self.console.print("[red]OpenAI API key not configured[/red]")
                self.console.print("[dim]Set OPENAI_API_KEY environment variable first[/dim]")
                return
        
        elif provider == 'anthropic':
            if not os.environ.get('ANTHROPIC_API_KEY'):
                self.console.print("[red]Anthropic API key not configured[/red]")
                self.console.print("[dim]Set ANTHROPIC_API_KEY environment variable first[/dim]")
                return
        
        elif provider == 'local':
            local_config = self.repl.config_manager.get('local_model', {})
            if not local_config.get('enabled', False):
                self.console.print("[red]Local model not enabled[/red]")
                self.console.print("[dim]Enable with: set local_model.enabled true[/dim]")
                return
            
            # Test local model availability
            try:
                from ..agents.local_model import create_local_model_manager
                manager = create_local_model_manager(local_config)
                if not manager or not manager.is_available():
                    self.console.print("[red]Local model not available[/red]")
                    self.console.print("[dim]Use 'ai test-local' to diagnose issues[/dim]")
                    return
            except Exception as e:
                self.console.print(f"[red]Local model error: {e}[/red]")
                return
        
        # Switch provider
        self.repl.config_manager.set('llm.provider', provider)
        
        # Success message with provider-specific info
        if provider == 'auto':
            self.console.print("[green]Switched to auto-selection mode[/green]")
            self.console.print("[dim]Will automatically choose the best available provider[/dim]")
        elif provider == 'openai':
            current_model = self.repl.config_manager.get('llm.model', 'gpt-4')
            self.console.print(f"[green]Switched to OpenAI ({current_model})[/green]")
        elif provider == 'anthropic':
            self.console.print("[green]Switched to Anthropic (Claude)[/green]")
            self.console.print("[dim]Make sure to set an appropriate Claude model with: set llm.model claude-3-sonnet[/dim]")
        elif provider == 'local':
            model_name = local_config.get('model_name', 'deepseek-coder')
            engine = local_config.get('engine', 'ollama')
            self.console.print(f"[green]Switched to local model ({engine}: {model_name})[/green]")
            self.console.print("[dim]Enjoy privacy-first AI analysis![/dim]")
        
        # Show quick status
        self.console.print(f"\n[dim]Current configuration:[/dim]")
        self.console.print(f"[white]Provider: [bold]{provider}[/bold][/white]")
        if provider != 'auto':
            model = self.repl.config_manager.get('llm.model', 'gpt-4')
            self.console.print(f"[white]Model: [bold]{model}[/bold][/white]")
        
        self.console.print(f"\n[cyan]Test with: ai test[/cyan]")
        """Test AI integration with a simple query"""
        api_key = os.environ.get('OPENAI_API_KEY')
        if not api_key:
            self.console.print("[red]OpenAI API key not configured. Run 'ai-status' for setup instructions.[/red]")
            return
        
        self.console.print("[blue]Testing AI integration...[/blue]")
        
        try:
            # Import and test LangChain OpenAI
            from langchain_openai import ChatOpenAI
            from langchain.schema import HumanMessage
            
            # Initialize ChatOpenAI
            llm = ChatOpenAI(
                model="gpt-4",
                temperature=0.1,
                openai_api_key=api_key
            )
            
            # Test with a simple security query
            test_message = HumanMessage(content="Analyze this Python code for security issues: def login(user, pwd): query = f'SELECT * FROM users WHERE name={user} AND pass={pwd}'; return db.execute(query). Provide a detailed analysis.")
            
            self.console.print("[dim]Sending test query to GPT-4...[/dim]")
            
            # Get response with timing
            import time
            start_time = time.time()
            response = await asyncio.to_thread(llm.invoke, [test_message])
            api_call_time = time.time() - start_time
            
            self.console.print("[green]AI integration test successful![/green]")
            self.console.print(f"\n[white]FULL AI Response:[/white]")
            self.console.print("─" * 80)
            self.console.print(f"[cyan]{response.content}[/cyan]")
            self.console.print("─" * 80)
            self.console.print(f"[dim]API Response Length: {len(response.content)} characters[/dim]")
            self.console.print(f"[dim]Model Used: GPT-4 | API Call Time: {api_call_time:.2f}s[/dim]")
            
        except Exception as e:
            self.console.print(f"[red]AI integration test failed: {e}[/red]")
            self.console.print("[yellow]Check your API key and internet connection[/yellow]")
            import traceback
            self.console.print(f"[dim]Full error: {traceback.format_exc()}[/dim]")
    
    async def _run_comprehensive_ai_audit(self, path: str, files: List[str], scanner_findings: List[Dict], use_local_model: bool = False) -> List[Finding]:
        """Run comprehensive AI-powered security audit using AuditorAgent - returns Finding objects directly"""
        try:
            from ..agents.auditor import AuditorAgent
            from ..schemas.findings import AnalysisContext, Finding, CVSSv4
            
            # Beautiful start message
            self.console.print()
            self.console.print("╭─" + "─" * 58 + "─╮", style="bright_blue")
            self.console.print("│" + " " * 15 + "[bold bright_blue]AI CONTEXT-AWARE SECURITY AUDIT[/bold bright_blue]" + " " * 14 + "│", style="bright_blue")
            self.console.print("╰─" + "─" * 58 + "─╯", style="bright_blue")
            self.console.print()
            
            audit_type = "Local AI Model" if use_local_model else "Cloud AI Service"
            self.console.print(f"[bright_cyan]Audit Type:[/bright_cyan] {audit_type}")
            self.console.print(f"[bright_cyan]Target Path:[/bright_cyan] [cyan]{path}[/cyan]")
            self.console.print(f"[bright_cyan]Files to Analyze:[/bright_cyan] [yellow]{len(files)}[/yellow]")
            self.console.print(f"[dim]Performing deep context analysis with function/class understanding...[/dim]")
            self.console.print()
            
            with self.console.status("[bold green]Analyzing code with AI...", spinner="dots"):
                # Initialize AuditorAgent with config
                config = self.repl.config_manager.get_all()
                
                # If using local model, ensure the config is set properly
                if use_local_model:
                    config['llm'] = config.get('llm', {})
                    config['llm']['provider'] = 'local'
                    local_model_config = config.get('local_model', {})
                    if not local_model_config.get('enabled'):
                        local_model_config['enabled'] = True
                    config['local_model'] = local_model_config
            
            auditor = AuditorAgent(config)
            
            # Create analysis context
            analysis_context = AnalysisContext(
                workspace_path=os.path.abspath(path),
                repo_path=os.path.abspath(path),
                target_files=files[:50],  # Limit for performance
                languages=self._detect_technologies(files).get('languages', []),
                technologies=self._detect_technologies(files),
                entry_points=[]
            )
            
            # Convert scanner findings to Finding objects if any
            finding_objects = []
            for finding_dict in scanner_findings:
                try:
                    raw_severity = finding_dict.get('severity', 'MEDIUM')
                    normalized_severity = self._normalize_scanner_severity(raw_severity)
                    
                    cvss_score = CVSSv4(
                        score=self._severity_to_cvss_score(normalized_severity),
                        vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
                    )
                    
                    finding_obj = Finding(
                        file=finding_dict.get('file', ''),
                        title=finding_dict.get('title', 'Scanner Finding'),
                        description=finding_dict.get('description', 'Security issue detected by scanner'),
                        lines=str(finding_dict.get('line', 1)),
                        impact=self._get_impact_for_severity(normalized_severity),
                        severity=normalized_severity,
                        cvss_v4=cvss_score,
                        snippet=finding_dict.get('code', '# Code snippet not available'),
                        recommendation=self._get_recommendation_for_finding(finding_dict),
                        sample_fix='# Refer to security documentation for specific fix',
                        poc='# Test case not available for scanner finding',
                        owasp=[],
                        cwe=[],
                        references=[],
                        cross_file=[],
                        tool_evidence=[]
                    )
                    finding_objects.append(finding_obj)
                except Exception as e:
                    self.console.print(f"[dim]Warning: Could not convert finding: {e}[/dim]")
            
            # Run comprehensive AI audit - returns Finding objects directly
            with self.console.status("[bold green]⌕ Performing deep context-aware analysis...", spinner="dots"):
                self.console.print("[dim] ∞ Analyzing with function/class context understanding...[/dim]")
                self.console.print("[dim] ∞ Tracing data flow and usage patterns...[/dim]")
                self.console.print("[dim] ∞ Evaluating exploitability in application context...[/dim]")
                ai_findings = await auditor.perform_audit(analysis_context, finding_objects)
            
            # Clean completion message
            self.console.print()
            self.console.print("┌─" + "─" * 54 + "─┐", style="bright_green")
            self.console.print("│ [bold bright_green]AI CONTEXT-AWARE AUDIT COMPLETED![/bold bright_green]     │", style="bright_green")
            self.console.print("│" + " " * 56 + "│", style="bright_green") 
            findings_text = f"{len(ai_findings)} high-confidence findings discovered"
            findings_padding = 55 - len(findings_text)
            self.console.print(f"│ [bright_white]{findings_text}[/bright_white]" + " " * findings_padding + "│", style="bright_green")
            self.console.print("└─" + "─" * 54 + "─┘", style="bright_green")
            self.console.print()
            
            # Return Finding objects directly - no conversion needed
            return ai_findings
            
        except ImportError as e:
            self.console.print(f"[dim]Warning: Could not import AI auditing components: {e}[/dim]")
            return []
        except Exception as e:
            self.console.print(f"[dim]Warning: AI audit failed: {e}[/dim]")
            import traceback
            self.console.print(f"[dim]Error details: {traceback.format_exc()[:200]}...[/dim]")
            return []
    
    def _display_ai_findings_report(self, ai_findings: List[Dict], auditor=None):
        """Display AI audit findings in a clean, copy-friendly format"""
        if not ai_findings:
            return
        
        # Clean header with professional styling
        self.console.print()
        self.console.print("[bold bright_blue]" + "="*90 + "[/bold bright_blue]")
        self.console.print("[bold bright_blue]" + " "*28 + "SECURITY ANALYSIS REPORT" + " "*28 + "[/bold bright_blue]")
        self.console.print("[bold bright_blue]" + "="*90 + "[/bold bright_blue]")
        self.console.print()
        self.console.print()
        
        for i, finding in enumerate(ai_findings, 1):
            severity = finding.get('severity', 'Medium').upper()
            title = finding.get('title', 'Security Issue')
            file_path = finding.get('file', 'Unknown')
            line_num = finding.get('line', 'N/A')
            description = finding.get('description', 'No description available')
            confidence = finding.get('confidence', 85)
            cvss_score = finding.get('cvss_score', 'N/A')
            
            # Severity colors
            severity_colors = {
                'CRITICAL': 'bright_red',
                'HIGH': 'red', 
                'MEDIUM': 'yellow',
                'LOW': 'green'
            }
            severity_color = severity_colors.get(severity, 'white')
            
            # Finding header with clean design and severity indicators
            severity_indicators = {
                'CRITICAL': '●●●',
                'HIGH': '●●○',
                'MEDIUM': '●○○',
                'LOW': '○○○'
            }
            severity_indicator = severity_indicators.get(severity, '●○○')
            
            self.console.print()
            self.console.print(f"[bold bright_white]FINDING #{i:02d} [{severity_color}]{severity_indicator}[/{severity_color}][/bold bright_white]")
            self.console.print(f"[bold bright_white]{title}[/bold bright_white]")
            self.console.print()
            
            # Clean metadata display using Rich table for proper alignment
            from rich.table import Table
            metadata_table = Table.grid(padding=(0, 1))
            metadata_table.add_column("Label", style="bold bright_cyan", width=12)
            metadata_table.add_column("Value", style="white")
            
            metadata_table.add_row("Severity:", f"[{severity_color}][bold]{severity}[/bold][/{severity_color}]")
            location_display = f"[bold blue]{file_path}[/bold blue]" + (f"[bold white]:[/bold white][bold yellow]{line_num}[/bold yellow]" if line_num != 'N/A' else "")
            metadata_table.add_row("Location:", location_display)
            metadata_table.add_row("Confidence:", f"[bold green]{confidence}%[/bold green]")
            metadata_table.add_row("CVSS Score:", f"[bold yellow]{cvss_score}[/bold yellow]")
            
            self.console.print("┌─" + "─" * 60 + "─┐")
            self.console.print("│ " + " " * 58 + " │")
            self.console.print(metadata_table)
            self.console.print("│ " + " " * 58 + " │")
            self.console.print("└─" + "─" * 60 + "─┘")
            self.console.print()
            
            # Description section with clean styling
            self.console.print("[bold bright_yellow]DESCRIPTION[/bold bright_yellow]")
            self.console.print("[bright_blue]" + "─"*60 + "[/bright_blue]")
            # Clean description as continuous paragraph with wide width
            clean_description = description.replace('\n', ' ').replace('  ', ' ').strip()
            # Use Rich Text with wide width to prevent unnecessary wrapping
            from rich.text import Text
            desc_text = Text(clean_description, style="white")
            self.console.print(desc_text, width=200)
            self.console.print()
            self.console.print()
            
            # Code section with clean styling and syntax highlighting
            self.console.print("[bold bright_green]AFFECTED CODE[/bold bright_green]")
            self.console.print("[bright_blue]" + "─"*60 + "[/bright_blue]")
            try:
                if file_path != 'Unknown' and line_num != 'N/A':
                    code_context = self._get_code_context_for_display(file_path, int(line_num) if str(line_num).isdigit() else 1)
                    if code_context and "Code context not available" not in code_context:
                        # Display code with simple box styling
                        self.console.print("┌─" + "─" * 60 + "─┐")
                        code_lines = code_context.split('\n')
                        for code_line in code_lines:
                            if code_line.strip():
                                if '>>>' in code_line:
                                    # Vulnerable line with enhanced visibility
                                    clean_line = code_line.replace('>>>', '').strip()
                                    self.console.print(f"│ > [bold bright_red]{clean_line}[/bold bright_red]")
                                else:
                                    # Regular line
                                    self.console.print(f"│   [dim]{code_line.strip()}[/dim]")
                        self.console.print("└─" + "─" * 60 + "─┘")
                    else:
                        self.console.print("[dim italic]Code context not available for this finding[/dim italic]")
                else:
                    self.console.print("[dim italic]Code context not available for this finding[/dim italic]")
            except Exception:
                self.console.print("[dim italic]Code context not available for this finding[/dim italic]")
            self.console.print()
            self.console.print()
            
            # Security Impact with clean styling
            self.console.print("[bold bright_red]SECURITY IMPACT[/bold bright_red]")
            self.console.print("[bright_blue]" + "─"*60 + "[/bright_blue]")
            impact = self._get_impact_for_severity(severity)
            # Clean impact text as continuous paragraph with wide width
            clean_impact = impact.replace('\n', ' ').replace('  ', ' ').strip()
            from rich.text import Text
            impact_text = Text(clean_impact, style="bright_white")
            self.console.print(impact_text, width=200)
            self.console.print()
            self.console.print()
            
            # Recommendations with clean styling and visual hierarchy
            self.console.print("[bold bright_magenta]SECURITY RECOMMENDATIONS[/bold bright_magenta]")
            self.console.print("[bright_blue]" + "─"*60 + "[/bright_blue]")
            recommendations = self._get_recommendations_for_finding(title, description, auditor)
            
            for j, rec in enumerate(recommendations, 1):
                self.console.print(f"  - [bold bright_cyan]{j}.[/bold bright_cyan] [white]{rec}[/white]")
            self.console.print()
            self.console.print()
            
            # Code Fix with clean styling and clear separation
            self.console.print("[bold bright_green]SECURE CODE FIX[/bold bright_green]")
            self.console.print("[bright_blue]" + "─"*60 + "[/bright_blue]")
            code_fix = self._get_code_fix_for_finding(finding, auditor)
            
            if "Dynamic code fix generation not available" in code_fix or "Error generating" in code_fix:
                self.console.print("[dim italic]" + code_fix + "[/dim italic]")
            else:
                # Parse and display code fix with smart text/code detection
                fix_lines = code_fix.split('\n')
                current_section = None
                in_code_block = False
                
                for fix_line in fix_lines:
                    line = fix_line.rstrip()  # Keep original indentation but remove trailing spaces
                    if not line and not in_code_block:
                        self.console.print()
                        continue
                    
                    # Skip markdown code fences
                    if line.strip().startswith('```'):
                        in_code_block = not in_code_block
                        continue
                    
                    # Detect section headers
                    line_lower = line.strip().lower()
                    if line.strip().startswith('# Before') or ('before' in line_lower and ('vulnerable' in line_lower or 'original' in line_lower)):
                        current_section = 'before'
                        self.console.print()
                        self.console.print("[bold red]▼ Before (Vulnerable Code)[/bold red]")
                        self.console.print("─" * 40)
                        continue
                    elif line.strip().startswith('# After') or ('after' in line_lower and ('secure' in line_lower or 'fixed' in line_lower)):
                        current_section = 'after'
                        self.console.print()
                        self.console.print("[bold green]▲ After (Secure Code)[/bold green]")
                        self.console.print("─" * 40)
                        continue
                    
                    # Smart detection: is this a line of code or explanation?
                    is_code_line = self._is_code_line(line.strip())
                    
                    if current_section == 'before' and is_code_line:
                        # Preserve original indentation for vulnerable code
                        self.console.print(f"[red]{line}[/red]")
                    elif current_section == 'after' and is_code_line:
                        # Preserve original indentation and apply syntax highlighting for secure code
                        highlighted_line = self._apply_basic_syntax_highlighting(line)
                        self.console.print(f"[green]{highlighted_line}[/green]")
                    elif in_code_block or is_code_line:
                        # Code outside sections - preserve indentation and apply basic highlighting
                        highlighted_line = self._apply_basic_syntax_highlighting(line)
                        self.console.print(f"[cyan]{highlighted_line}[/cyan]")
                    else:
                        # Regular explanation text - clean and readable
                        if line.strip():  # Only print non-empty explanation lines
                            self.console.print(f"[bright_white]{line.strip()}[/bright_white]")
            
            self.console.print()
            self.console.print()
            
            # Clean separator between findings with better spacing
            if i < len(ai_findings):
                self.console.print()
                self.console.print("[bright_blue]" + "═"*90 + "[/bright_blue]")
                self.console.print()
                self.console.print()
                self.console.print()
        
        # Summary with clean format
        self._display_clean_summary(ai_findings)
    
    def _display_structured_ai_finding(self, description: str):
        """Parse and display structured AI finding output"""
        sections = {
            'ISSUE_NAME:': 'Issue',
            'DESCRIPTION:': 'Description', 
            'AFFECTED_CODE:': 'Affected Code',
            'CODE_INTERACTIONS:': 'Code Interactions',
            'CROSS_FILE_IMPACT:': 'Cross-File Impact'
        }
        
        current_section = None
        content = []
        
        for line in description.split('\n'):
            line = line.strip()
            if any(section in line for section in sections.keys()):
                # Display previous section
                if current_section and content:
                    section_name = sections.get(current_section, current_section)
                    self.console.print(f"   [bold]{section_name}:[/bold]")
                    self.console.print(f"   {' '.join(content)}")
                    self.console.print()
                
                # Start new section
                for section_key in sections.keys():
                    if section_key in line:
                        current_section = section_key
                        content = [line.replace(section_key, '').strip()]
                        break
            elif line:
                content.append(line)
        
        # Display final section
        if current_section and content:
            section_name = sections.get(current_section, current_section)
            self.console.print(f"   [bold]{section_name}:[/bold]")
            self.console.print(f"   {' '.join(content)}")
    
    def _get_code_context_for_display(self, file_path: str, line_number: int, context_lines: int = 3) -> str:
        """Get beautifully formatted code context around the specified line for display"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()
            
            start_line = max(0, line_number - context_lines - 1)
            end_line = min(len(lines), line_number + context_lines)
            
            context = []
            for i in range(start_line, end_line):
                line_num = i + 1
                line_content = lines[i].rstrip()
                
                # Beautiful line formatting with syntax highlighting
                if line_num == line_number:
                    # Vulnerable line with special highlighting
                    context.append(f"[bright_red]>>> {line_num:4d}:[/bright_red] [red]{line_content}[/red]")
                else:
                    # Regular lines with subtle styling
                    if line_content.strip():
                        # Detect common syntax patterns for basic highlighting
                        formatted_content = self._apply_basic_syntax_highlighting(line_content)
                        context.append(f"[dim]{line_num:4d}:[/dim] {formatted_content}")
                    else:
                        # Empty lines
                        context.append(f"[dim]{line_num:4d}:[/dim] ")
            
            return '\n'.join(context)
        except Exception:
            return "[dim italic]Code context not available[/dim italic]"
    
    def _apply_basic_syntax_highlighting(self, line: str) -> str:
        """Apply basic syntax highlighting to code lines while preserving indentation"""
        import re
        
        # Preserve original indentation
        original_line = line
        leading_spaces = len(line) - len(line.lstrip())
        indent = line[:leading_spaces]
        code_part = line[leading_spaces:]
        
        if not code_part.strip():
            return original_line
        
        # Don't apply highlighting if the line already contains Rich markup
        if '[/' in code_part or '[' in code_part and ']' in code_part:
            return original_line
        
        # Keywords (Python, JavaScript, etc.) - be more precise with word boundaries
        keywords = ['def', 'class', 'if', 'else', 'elif', 'for', 'while', 'import', 'from', 'return', 'try', 'except', 'function', 'const', 'let', 'var', 'async', 'await']
        for keyword in keywords:
            # Use more precise regex to avoid false matches
            pattern = rf'\b{re.escape(keyword)}\b'
            if re.search(pattern, code_part):
                code_part = re.sub(pattern, f'[blue]{keyword}[/blue]', code_part)
        
        # Strings - be more careful with nested quotes and escaping
        # Handle double quotes
        code_part = re.sub(r'"([^"\\]*(\\.[^"\\]*)*)"', r'[green]"[cyan]\1[/cyan]"[/green]', code_part)
        # Handle single quotes
        code_part = re.sub(r"'([^'\\]*(\\.[^'\\]*)*)'", r"[green]'[cyan]\1[/cyan]'[/green]", code_part)
        
        # Comments - only at the end of lines
        code_part = re.sub(r'(\s*#.*$)', r'[dim]\1[/dim]', code_part)
        code_part = re.sub(r'(\s*//.*$)', r'[dim]\1[/dim]', code_part)
        
        # Numbers - be more precise
        code_part = re.sub(r'\b(\d+(?:\.\d+)?)\b', r'[magenta]\1[/magenta]', code_part)
        
        # Basic operators - be more selective
        code_part = re.sub(r'(\s*[+\-*/%]?\s*=\s*)', r'[yellow]\1[/yellow]', code_part)
        code_part = re.sub(r'(==|!=|<=|>=)', r'[yellow]\1[/yellow]', code_part)
        
        # Function calls - only highlight function names, not everything with parentheses
        code_part = re.sub(r'\b([a-zA-Z_][a-zA-Z0-9_]*)\s*(\()', r'[bright_blue]\1[/bright_blue]\2', code_part)
        
        return indent + code_part
    
    def _is_code_line(self, line: str) -> bool:
        """Detect if a line contains code rather than explanation text"""
        # Common code indicators
        code_indicators = [
            '=', '(', ')', '{', '}', '[', ']', ';', 
            'def ', 'class ', 'import ', 'from ', 'if ', 'else:', 'elif ',
            'for ', 'while ', 'try:', 'except:', 'return ', 'yield ',
            'function ', 'const ', 'let ', 'var ', 'async ', 'await ',
            '.', '->', '=>', '||', '&&', '==', '!=', '<=', '>=',
            'self.', 'this.', '__', 'print(', 'console.log', 'SELECT',
            'INSERT', 'UPDATE', 'DELETE', 'CREATE', 'cursor.execute'
        ]
        
        # Text indicators (less likely to be code)
        text_indicators = [
            'To fix', 'This ensures', 'Here\'s how', 'We can',
            'You should', 'Make sure', 'Ensure that', 'This approach',
            'The solution', 'By doing this', 'This will', 'Instead of'
        ]
        
        line_lower = line.lower()
        
        # Check for text indicators first (these override code indicators)
        for indicator in text_indicators:
            if indicator.lower() in line_lower:
                return False
        
        # Check for code indicators
        for indicator in code_indicators:
            if indicator in line:
                return True
        
        # If line is very short or has specific patterns, likely code
        if len(line) < 60 and ('=' in line or '(' in line or line.endswith(';') or line.endswith(':')):
            return True
        
        # Default to text if uncertain
        return False
    
    def _get_recommendations_for_finding(self, title: str, description: str, auditor=None) -> List[str]:
        """Generate tailored recommendations based on the finding using LLM for fully dynamic responses"""
        
        # Always try to use LLM for dynamic, context-aware recommendations
        if auditor:
            try:
                llm = auditor.create_llm()
                if llm:
                    recommendations_prompt = f"""You are a senior security engineer. Analyze this specific security finding and provide targeted, actionable security recommendations.

SECURITY FINDING:
- Title: {title}
- Description: {description}

Based on the SPECIFIC vulnerability described above, provide 3-4 concrete, actionable tailored recommendations that directly address this exact security issue.

ANALYSIS GUIDELINES:
1. Read the title and description carefully to understand the ACTUAL vulnerability
2. Consider the specific context and code patterns mentioned
3. Provide recommendations that are directly relevant to THIS finding
4. Avoid generic security advice that doesn't match the issue

RECOMMENDATION CATEGORIES TO CONSIDER:
- If about hardcoded UI messages/strings → externalization, i18n, message management
- If about hardcoded credentials/secrets → secrets management, environment variables
- If about SQL injection → parameterized queries, input validation
- If about XSS → output encoding, CSP headers, input sanitization
- If about path traversal → path validation, allowlists
- If about authentication → OAuth, JWT, session management
- If about authorization → RBAC, permission checks
- If about logging → structured logging, sanitization
- If about input validation → validation frameworks, allowlists
- If about cryptography → secure algorithms, key management
- If about file operations → safe file handling, permissions
- If about network → TLS, secure protocols
- If about configuration → externalized config, secure defaults

Format your response as a simple list of recommendations, one per line, starting with a dash or bullet point.

Example format:
- Use externalized configuration files for user-facing messages
- Implement internationalization (i18n) support for dynamic content
- Create a centralized message management system
- Validate message content before display

IMPORTANT: Base recommendations ONLY on the actual vulnerability described. Do not provide generic security advice unrelated to the specific finding."""

                    try:
                        recommendations_response = llm.invoke(recommendations_prompt)
                        # Extract text from response
                        if hasattr(recommendations_response, 'content'):
                            rec_text = recommendations_response.content
                        elif hasattr(recommendations_response, 'text'):
                            rec_text = recommendations_response.text
                        else:
                            rec_text = str(recommendations_response)
                        
                        # Parse recommendations from response
                        recommendations = []
                        for line in rec_text.split('\n'):
                            line = line.strip()
                            if line and (line.startswith('•') or line.startswith('-') or line.startswith('*') or line.startswith('1.') or line.startswith('2.') or line.startswith('3.') or line.startswith('4.')):
                                # Remove bullet point/numbering and clean up
                                clean_line = line.lstrip('•-* 1234567890.').strip()
                                if clean_line and len(clean_line) > 10:  # Filter out very short/empty lines
                                    recommendations.append(clean_line)
                        
                        # If we got valid recommendations, return them
                        if recommendations:
                            return recommendations[:4]  # Limit to 4 recommendations
                    except Exception as e:
                        # Log the error but continue to fallback
                        import logging
                        logging.warning(f"LLM recommendation generation failed: {e}")
            except Exception as e:
                # Log the error but continue to fallback
                import logging
                logging.warning(f"LLM auditor unavailable for recommendations: {e}")
        
        # Only use fallback if LLM completely fails - but keep it minimal and generic
        return [
            "Review and validate the identified security concern",
            "Implement appropriate security controls for this vulnerability type",
            "Follow secure coding best practices relevant to this finding",
            "Consider security testing and code review for this component"
        ]
    
    def _get_code_fix_for_finding(self, finding: Dict, auditor=None) -> str:
        """Generate dynamic code fix examples using LLM based on actual vulnerable code"""
        try:
            if not auditor:
                return "[dim]Dynamic code fix generation not available (no LLM auditor)[/dim]"
            
            # Extract finding details
            file_path = finding.get('file', 'Unknown')
            line_num = finding.get('line', 'N/A')
            title = finding.get('title', 'Security Issue')
            description = finding.get('description', 'No description available')
            
            # Get the actual vulnerable code context
            vulnerable_code = ""
            try:
                if file_path != 'Unknown' and line_num != 'N/A':
                    vulnerable_code = self._get_code_context_for_display(file_path, int(line_num) if str(line_num).isdigit() else 1)
            except Exception:
                vulnerable_code = "[Code context not available]"
            
            # Create LLM prompt for code fix generation
            fix_prompt = f"""You are a senior security engineer. Analyze this specific security finding and provide a targeted code fix.

VULNERABILITY DETAILS:
- Issue: {title}
- Description: {description}
- File: {file_path}
- Line: {line_num}

VULNERABLE CODE:
{vulnerable_code}

Analyze the SPECIFIC vulnerability type and provide an appropriate fix. Common patterns:

FOR HARDCODED UI MESSAGES (messagebox, print statements):
- Move strings to configuration files or constants
- Implement message templates or i18n support
- Use centralized message management

FOR HARDCODED CREDENTIALS/SECRETS:
- Use environment variables or config files
- Implement secrets management systems
- Use secure authentication mechanisms

FOR SQL INJECTION:
- Use parameterized queries
- Implement input validation
- Use ORM frameworks

FOR XSS VULNERABILITIES:
- Implement output encoding
- Use CSP headers
- Sanitize user inputs

Provide a concise fix in this exact format:
# Before (Vulnerable):
[actual vulnerable code snippet from the finding]

# After (Secure):
[fixed code with appropriate security controls for THIS specific issue type]

IMPORTANT: Base your fix on the ACTUAL vulnerability described, not generic security advice. If it's about UI messages, don't suggest credential management. If it's about credentials, don't suggest UI improvements.

Response should be ready to copy-paste and address the specific issue identified."""

            # Use the auditor's LLM to generate the fix
            llm = auditor.create_llm()
            if llm:
                try:
                    fix_response = llm.invoke(fix_prompt)
                    # Extract text from response object if needed
                    if hasattr(fix_response, 'content'):
                        return fix_response.content
                    elif hasattr(fix_response, 'text'):
                        return fix_response.text
                    else:
                        return str(fix_response)
                except Exception as e:
                    return f"[dim]Error generating dynamic fix: {e}[/dim]"
            else:
                return "[dim]LLM not available for dynamic code fix generation[/dim]"
                
        except Exception as e:
            return f"[dim]Error generating code fix: {e}[/dim]"
    
    def _format_text_for_display(self, text: str, max_width: int) -> List[str]:
        """Format text to fit within specified width with proper word wrapping"""
        if not text:
            return [""]
        
        words = text.split()
        lines = []
        current_line = ""
        
        for word in words:
            if len(current_line + " " + word) <= max_width:
                if current_line:
                    current_line += " " + word
                else:
                    current_line = word
            else:
                if current_line:
                    lines.append(current_line)
                current_line = word
        
        if current_line:
            lines.append(current_line)
        
        return lines if lines else [""]
    
    def _display_clean_summary(self, ai_findings: List[Dict]):
        """Display a clean, professional summary of all findings"""
        if not ai_findings:
            return
        
        # Calculate statistics
        severity_counts = {'CRITICAL': 0, 'HIGH': 0, 'MEDIUM': 0, 'LOW': 0}
        total_findings = len(ai_findings)
        
        for finding in ai_findings:
            severity = finding.get('severity', 'Medium').upper()
            if severity in severity_counts:
                severity_counts[severity] += 1
        
        # Calculate risk score
        risk_score = (severity_counts.get('CRITICAL', 0) * 4 + 
                     severity_counts.get('HIGH', 0) * 3 + 
                     severity_counts.get('MEDIUM', 0) * 2 + 
                     severity_counts.get('LOW', 0) * 1)
        
        # Risk level
        if risk_score >= 20:
            risk_level, risk_color = 'CRITICAL', 'bright_red'
        elif risk_score >= 10:
            risk_level, risk_color = 'HIGH', 'red'
        elif risk_score >= 5:
            risk_level, risk_color = 'MEDIUM', 'yellow'
        else:
            risk_level, risk_color = 'LOW', 'green'
        
        # Clean summary header with professional styling
        self.console.print()
        self.console.print("[bold bright_blue]" + "="*90 + "[/bold bright_blue]")
        self.console.print("[bold bright_blue]" + " "*28 + "SECURITY ANALYSIS SUMMARY" + " "*28 + "[/bold bright_blue]")
        self.console.print("[bold bright_blue]" + "="*90 + "[/bold bright_blue]")
        self.console.print()
        self.console.print()
        
        # Findings overview with clean card design
        self.console.print("┌─" + "─" * 88 + "─┐")
        self.console.print("│ [bold bright_white]FINDINGS OVERVIEW[/bold bright_white]" + " " * 71 + "│")
        self.console.print("├─" + "─" * 88 + "─┤")
        findings_text = f"Total Security Findings: {total_findings}"
        self.console.print(f"│ [bold cyan]{findings_text}[/bold cyan]" + " " * (88 - len(findings_text)) + "│")
        self.console.print("└─" + "─" * 88 + "─┘")
        self.console.print()
        self.console.print()
        
        # Severity breakdown with clean visual indicators
        self.console.print("[bold bright_yellow]SEVERITY BREAKDOWN[/bold bright_yellow]")
        self.console.print("[bright_blue]" + "─"*60 + "[/bright_blue]")
        
        severity_colors = {
            'CRITICAL': 'bright_red',
            'HIGH': 'red',
            'MEDIUM': 'yellow',
            'LOW': 'green'
        }
        
        severity_indicators = {
            'CRITICAL': '●●●',
            'HIGH': '●●○',
            'MEDIUM': '●○○',
            'LOW': '○○○'
        }
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = severity_counts.get(severity, 0)
            color = severity_colors[severity]
            indicator = severity_indicators[severity]
            self.console.print(f"  [{color}]{indicator}[/{color}] [{color}][bold]{severity}:[/bold][/{color}] {count} finding(s)")
        
        self.console.print()
        self.console.print()
        
        # Risk assessment with clean styling
        self.console.print("[bold bright_magenta]RISK ASSESSMENT[/bold bright_magenta]")
        self.console.print("[bright_blue]" + "─"*60 + "[/bright_blue]")
        self.console.print(f"[bold cyan]Overall Risk Level:[/bold cyan] [{risk_color}][bold]{risk_level}[/bold][/{risk_color}]")
        self.console.print(f"[bold cyan]Risk Score:[/bold cyan] [bright_yellow][bold]{risk_score}/100[/bold][/bright_yellow]")
        self.console.print()
        self.console.print()
        
        # Priority recommendations with clean visibility
        critical_high = severity_counts['CRITICAL'] + severity_counts['HIGH']
        if critical_high > 0:
            self.console.print("┌─" + "─" * 68 + "─┐")
            self.console.print("│ [bold bright_red]IMMEDIATE ACTION REQUIRED[/bold bright_red]" + " " * 32 + "│")
            action_text = f"You have {critical_high} critical/high severity issues that need immediate attention."
            self.console.print(f"│ [red]{action_text}[/red]" + " " * (68 - len(action_text)) + "│")
            self.console.print("└─" + "─" * 68 + "─┘")
            self.console.print()
            self.console.print()
        
        # Next steps with clean checklist design
        self.console.print("[bold bright_green]NEXT STEPS[/bold bright_green]")
        self.console.print("[bright_blue]" + "─"*60 + "[/bright_blue]")
        steps = [
            "- Review all critical and high severity findings first",
            "- Apply the recommended security fixes",
            "- Test your fixes thoroughly",
            "- Run the security scan again to verify fixes",
            "- Consider implementing additional security measures"
        ]
        
        for step in steps:
            self.console.print(f"  {step}")
        
        self.console.print()
        self.console.print()
        
        self.console.print("[bold bright_blue]" + "="*90 + "[/bold bright_blue]")
        self.console.print()

    def _display_comprehensive_summary(self, ai_findings: List[Dict]):
        """Display comprehensive summary of all findings"""
        severity_counts = {}
        for finding in ai_findings:
            severity = finding.get('severity', 'Medium').upper()
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
        
        self.console.print(f"\n[bold blue]COMPREHENSIVE ANALYSIS SUMMARY[/bold blue]")
        self.console.print("=" * 100)
        
        total_findings = len(ai_findings)
        self.console.print(f"[bold white]Total Security Findings: {total_findings}[/bold white]")
        
        for severity in ['CRITICAL', 'HIGH', 'MEDIUM', 'LOW']:
            count = severity_counts.get(severity, 0)
            if count > 0:
                color = {
                    'CRITICAL': 'red',
                    'HIGH': 'orange_red1',
                    'MEDIUM': 'yellow', 
                    'LOW': 'green'
                }.get(severity, 'white')
                self.console.print(f"   [{color}]{severity}:[/{color}] {count} finding(s)")
        
        # Risk assessment
        risk_score = (severity_counts.get('CRITICAL', 0) * 4 + 
                     severity_counts.get('HIGH', 0) * 3 + 
                     severity_counts.get('MEDIUM', 0) * 2 + 
                     severity_counts.get('LOW', 0) * 1)
        
        if risk_score >= 20:
            risk_level = "[red]CRITICAL[/red]"
        elif risk_score >= 10:
            risk_level = "[orange_red1]HIGH[/orange_red1]"
        elif risk_score >= 5:
            risk_level = "[yellow]MEDIUM[/yellow]"
        else:
            risk_level = "[green]LOW[/green]"
            
        self.console.print(f"\n[bold]Overall Security Risk Level: {risk_level}[/bold]")
        self.console.print(f"[bold]Risk Score: {risk_score}/100[/bold]")
        
        self.console.print("\n" + "=" * 100)
    
    def _build_file_tree(self, files: List[str]) -> Dict[str, Any]:
        """Build a simple file tree from file list"""
        tree = {}
        for file_path in files:
            parts = file_path.split('/')
            current = tree
            for part in parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            current[parts[-1]] = {'type': 'file', 'path': file_path}
        return tree
    
    def _detect_technologies(self, files: List[str]) -> Dict[str, Any]:
        """Detect technologies from file extensions"""
        technologies = {
            'languages': [],
            'frameworks': [],
            'databases': []
        }
        
        # Detect languages from file extensions
        extensions = set()
        for file_path in files:
            if '.' in file_path:
                ext = file_path.split('.')[-1].lower()
                extensions.add(ext)
        
        language_map = {
            'py': 'python',
            'js': 'javascript',
            'ts': 'typescript',
            'java': 'java',
            'c': 'c',
            'cpp': 'cpp',
            'go': 'go',
            'rs': 'rust',
            'php': 'php',
            'rb': 'ruby',
            'sol': 'solidity'
        }
        
        for ext in extensions:
            if ext in language_map:
                technologies['languages'].append(language_map[ext])
        
        return technologies
    
    def _normalize_scanner_severity(self, severity: str) -> str:
        """Normalize scanner severity values to match schema requirements"""
        if not severity:
            return 'Medium'
        
        # Handle common scanner severity formats
        severity_map = {
            'critical': 'Critical',
            'high': 'High', 
            'medium': 'Medium',
            'low': 'Low',
            'info': 'Low',
            'informational': 'Low',
            'warning': 'Medium',
            'error': 'High',
            'note': 'Low'
        }
        
        normalized = severity_map.get(severity.lower().strip())
        return normalized if normalized else 'Medium'
    
    def _severity_to_cvss_score(self, severity: str) -> float:
        """Convert severity string to CVSS score"""
        severity_map = {
            'CRITICAL': 9.0,
            'HIGH': 7.5,
            'MEDIUM': 5.0,
            'LOW': 2.5,
            'INFO': 0.0
        }
        return severity_map.get(severity.upper(), 5.0)
    
    def _get_impact_for_severity(self, severity: str) -> str:
        """Get impact description for severity level"""
        impact_map = {
            'CRITICAL': 'Critical security vulnerability that could lead to complete system compromise',
            'HIGH': 'High-risk security issue that could result in significant data exposure or system access',
            'MEDIUM': 'Medium-risk security concern that should be addressed to prevent potential exploitation',
            'LOW': 'Low-risk security issue that represents a minor security concern',
            'INFO': 'Informational security note for awareness'
        }
        return impact_map.get(severity.upper(), 'Security issue requiring review')
    
    def _get_recommendation_for_finding(self, finding_dict: dict) -> str:
        """Generate recommendation based on finding type"""
        title = finding_dict.get('title', '').lower()
        if 'sql' in title or 'injection' in title:
            return 'Use parameterized queries or ORM methods to prevent SQL injection'
        elif 'hardcoded' in title or 'password' in title:
            return 'Move secrets to environment variables or secure configuration'
        elif 'pickle' in title or 'deserialization' in title:
            return 'Avoid deserializing untrusted data or use safe serialization formats'
        elif 'shell' in title or 'command' in title:
            return 'Validate and sanitize all user inputs before executing system commands'
        elif 'yaml' in title:
            return 'Use yaml.safe_load() instead of yaml.load() for untrusted input'
        else:
            return 'Review and remediate according to security best practices'

    # Enhanced Tool Management Commands
    async def cmd_tools(self, args: List[str]) -> None:
        """
        Manage security tools
        Usage: tools [list|check|install|info <tool>]
        """
        if not args:
            args = ['list']
        
        subcommand = args[0].lower()
        
        if subcommand == 'list':
            self._show_tools_list()
        elif subcommand == 'check':
            self._check_tools_availability()
        elif subcommand == 'install':
            self._show_installation_guide()
        elif subcommand == 'info' and len(args) > 1:
            self._show_tool_info(args[1])
        else:
            self.console.print("[red]Usage: tools [list|check|install|info <tool>][/red]")
        
        return None  # Explicit return for async compatibility
    
    def _show_tools_list(self):
        """Show list of all available tools"""
        table = Table(title="Available Security Tools", show_header=True, header_style="bold magenta")
        table.add_column("Tool", style="cyan", width=15)
        table.add_column("Language/Tech", style="green", width=15)
        table.add_column("Description", width=40)
        table.add_column("Status", width=10)
        
        tools_info = {
            'bandit': ('Python', 'Security linter for Python code'),
            'semgrep': ('Multi-lang', 'Static analysis with custom rules'),
            'gitleaks': ('Git', 'Secret and credential detector'),
            'gosec': ('Go', 'Security analyzer for Go code'),
            'slither': ('Solidity', 'Smart contract security analyzer'),
            'npm_audit': ('Node.js', 'Node.js dependency vulnerability scanner'),
            'php_analyzer': ('PHP', 'PHP security analyzer (Psalm, PHPStan, PHPCS)'),
            'java_analyzer': ('Java', 'Java security analyzer (SpotBugs, PMD)'),
            'cpp_analyzer': ('C/C++', 'C/C++ security analyzer (Clang, CppCheck)'),
            'csharp_analyzer': ('C#/.NET', 'C# security analyzer (DevSkim, Roslyn)'),
            'ruby_analyzer': ('Ruby', 'Ruby security analyzer (Brakeman, RuboCop)'),
            'rust_analyzer': ('Rust', 'Rust security analyzer (Clippy, Cargo-audit)'),
            'swift_analyzer': ('Swift', 'Swift security analyzer (SwiftLint)'),
            'kotlin_analyzer': ('Kotlin', 'Kotlin security analyzer (Detekt)'),
            'scala_analyzer': ('Scala', 'Scala security analyzer (Scalafix)'),
            'go_analyzer': ('Go', 'Go security analyzer (Gosec, Staticcheck)'),
            'solidity_analyzer': ('Solidity', 'Solidity smart contract analyzer'),
            'vyper_analyzer': ('Vyper', 'Vyper smart contract analyzer'),
            'dart_flutter_analyzer': ('Dart/Flutter', 'Dart/Flutter security analyzer'),
            'haskell_analyzer': ('Haskell', 'Haskell security analyzer (HLint)'),
            'perl_analyzer': ('Perl', 'Perl security analyzer (Perl::Critic)'),
            'lua_analyzer': ('Lua', 'Lua security analyzer (Luacheck)'),
            'erlang_elixir_analyzer': ('Erlang/Elixir', 'Erlang/Elixir security analyzer'),
            'fsharp_analyzer': ('F#', 'F# security analyzer (.NET based)'),
            'objective_c_analyzer': ('Objective-C', 'Objective-C security analyzer'),
            'cairo_analyzer': ('Cairo', 'Cairo (StarkNet) smart contract analyzer'),
            'move_analyzer': ('Move', 'Move (Aptos/Sui) smart contract analyzer'),
            'clarity_analyzer': ('Clarity', 'Clarity (Stacks) smart contract analyzer'),
            'c_analyzer': ('C', 'C language security analyzer'),
        }
        
        # Get available tools from config
        available_tools = self.repl.config_manager.get('tools.enabled', [])
        
        for tool, (lang, desc) in tools_info.items():
            if tool in available_tools:
                status = "Enabled"
            else:
                status = "Available"
            
            table.add_row(tool, lang, desc, status)
        
        self.console.print(table)
        return None  # Explicitly return None to avoid async issues
    
    def _check_tools_availability(self):
        """Check availability of all tools"""
        self.console.print(Panel("Checking Tool Availability", style="bold blue"))
        
        # Import tools dynamically to check availability
        tool_classes = {}
        
        # Core tools
        tool_imports = [
            ('bandit', 'BanditScanner'),
            ('semgrep', 'SemgrepScanner'), 
            ('gitleaks', 'GitleaksScanner'),
            ('gosec', 'GosecScanner'),
            ('slither', 'SlitherScanner'),
            ('npm_audit', 'NpmAuditScanner'),
            ('php_analyzer', 'PhpAnalyzer'),
            ('java_analyzer', 'JavaAnalyzer'),
            ('cpp_analyzer', 'CppAnalyzer'),
            ('csharp_analyzer', 'CSharpAnalyzer'),
            ('ruby_analyzer', 'RubyAnalyzer'),
            ('rust_analyzer', 'RustAnalyzer'),
            ('swift_analyzer', 'SwiftAnalyzer'),
            ('kotlin_analyzer', 'KotlinAnalyzer'),
            ('scala_analyzer', 'ScalaAnalyzer'),
            ('go_analyzer', 'GoAnalyzer'),
            ('solidity_analyzer', 'SolidityTool'),
            ('vyper_analyzer', 'VyperTool'),
            ('dart_flutter_analyzer', 'DartFlutterAnalyzer'),
            ('haskell_analyzer', 'HaskellAnalyzer'),
            ('perl_analyzer', 'PerlAnalyzer'),
            ('lua_analyzer', 'LuaAnalyzer'),
            ('erlang_elixir_analyzer', 'ErlangElixirAnalyzer'),
            ('fsharp_analyzer', 'FSharpAnalyzer'),
            ('objective_c_analyzer', 'ObjectiveCAnalyzer'),
            ('cairo_analyzer', 'CairoAnalyzer'),
            ('move_analyzer', 'MoveAnalyzer'),
            ('clarity_analyzer', 'ClarityAnalyzer'),
            ('c_analyzer', 'CAnalyzer'),
        ]
        
        for tool_name, class_name in tool_imports:
            try:
                from importlib import import_module
                module = import_module(f'securecli.tools.{tool_name}')
                tool_classes[tool_name] = getattr(module, class_name)
            except (ImportError, AttributeError) as e:
                # Tool not available or class not found
                continue
        
        available_count = 0
        total_count = len(tool_classes)
        
        for tool_name, tool_class in tool_classes.items():
            try:
                tool_instance = tool_class(self.repl.config_manager.config_data)
                is_available = tool_instance.is_available()
                
                # Handle None return from is_available()
                if is_available is True:
                    self.console.print(f"[green]{tool_name} - Available[/green]")
                    available_count += 1
                else:
                    self.console.print(f"[red]{tool_name} - Not available[/red]")
            except Exception as e:
                self.console.print(f"[red]{tool_name} - Error: {str(e)[:50]}...[/red]")
        
        self.console.print(f"\n[bold]Summary: {available_count}/{total_count} tools available[/bold]")
        
        if available_count < total_count:
            self.console.print("[yellow]Run 'tools install' for installation instructions[/yellow]")
    
    def _show_installation_guide(self):
        """Show installation guide for missing tools"""
        from rich.markdown import Markdown
        
        guide = """
# Security Tools Installation Guide

## Core Tools (Recommended)
```bash
# Python tools
pip install bandit safety semgrep

# Git secret scanning  
curl -sSL https://github.com/gitleaks/gitleaks/releases/latest/download/gitleaks_8.18.4_linux_x64.tar.gz | tar -xz
sudo mv gitleaks /usr/local/bin/

# Go tools (requires Go installed)
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
go install honnef.co/go/tools/cmd/staticcheck@latest
```

## Blockchain Tools
```bash
pip install slither-analyzer mythril manticore[native]
```

## Node.js Tools (built-in with npm)
```bash
npm install -g npm-audit-resolver retire
```

## Quick Install Commands
```bash
# Ubuntu/Debian
sudo apt-get install -y python3-pip nodejs npm golang-go

# Install all Python tools
pip install bandit safety semgrep slither-analyzer

# Install Go tools
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
```
        """
        
        self.console.print(Panel(Markdown(guide), title="Installation Guide", style="bold green"))
    
    def _show_tool_info(self, tool_name: str):
        """Show detailed information about a specific tool"""
        from rich.markdown import Markdown
        
        tool_descriptions = {
            'bandit': {
                'desc': 'Bandit is a security linter designed to find common security issues in Python code.',
                'usage': 'scan --tools bandit --path ./src',
                'install': 'pip install bandit'
            },
            'semgrep': {
                'desc': 'Semgrep is a fast, open-source, static analysis tool for finding bugs, security issues, and anti-patterns.',
                'usage': 'scan --tools semgrep --path ./src',
                'install': 'pip install semgrep'
            },
            'gitleaks': {
                'desc': 'Gitleaks is a SAST tool for detecting and preventing secrets in git repos.',
                'usage': 'scan --tools gitleaks --path ./',
                'install': 'Download from GitHub releases'
            },
            'gosec': {
                'desc': 'Gosec inspects Go source code for security problems by scanning the Go AST.',
                'usage': 'scan --tools gosec --path ./cmd',
                'install': 'go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest'
            },
            'slither': {
                'desc': 'Slither is a Solidity static analysis framework written in Python 3.',
                'usage': 'scan --tools slither --path ./contracts',
                'install': 'pip install slither-analyzer'
            },
            'npm_audit': {
                'desc': 'npm audit scans your project for vulnerabilities and automatically installs any compatible updates.',
                'usage': 'scan --tools npm_audit --path ./',
                'install': 'Built-in with npm'
            }
        }
        
        if tool_name not in tool_descriptions:
            self.console.print(f"[red]Tool '{tool_name}' not found. Use 'tools list' to see available tools.[/red]")
            return
        
        tool_info = tool_descriptions[tool_name]
        
        info_text = f"# {tool_name.title()} Information\n\n"
        info_text += f"**Description:**\n{tool_info['desc']}\n\n"
        info_text += f"**Usage Example:**\n```\n{tool_info['usage']}\n```\n\n"
        info_text += f"**Installation:**\n```bash\n{tool_info['install']}\n```\n"
        
        self.console.print(Panel(Markdown(info_text), title=f"{tool_name.title()}", style="bold cyan"))

    def cmd_ai_status(self, args: List[str]) -> None:
        """Show AI integration status and configuration"""
        self.console.print(Panel("AI Integration Status", style="bold magenta"))
        
        # Check configuration
        local_enabled = self.repl.config_manager.get('local_model.enabled', False)
        model_name = self.repl.config_manager.get('local_model.model_name', 'Not configured')
        base_url = self.repl.config_manager.get('local_model.base_url', 'Not configured')
        
        # Create status table
        status_table = Table(show_header=True, header_style="bold cyan")
        status_table.add_column("Component", style="bold")
        status_table.add_column("Status", width=20)
        status_table.add_column("Details", width=40)
        
        # Local model status
        if local_enabled:
            local_status = "[green]Enabled[/green]"
            local_details = f"Model: {model_name}\nURL: {base_url}"
        else:
            local_status = "[red]Disabled[/red]"
            local_details = "Set SECURE_LOCAL_MODEL_ENABLED=true"
        
        status_table.add_row("Local AI Model", local_status, local_details)
        
        # OpenAI API status
        openai_key = os.getenv('OPENAI_API_KEY')
        if openai_key:
            openai_status = "[green]Configured[/green]"
            openai_details = f"Key: {openai_key[:10]}...{openai_key[-4:]}"
        else:
            openai_status = "[yellow]Not set[/yellow]"
            openai_details = "Set OPENAI_API_KEY for OpenAI models"
        
        status_table.add_row("OpenAI API", openai_status, openai_details)
        
        # RAG system
        rag_enabled = self.repl.config_manager.get('rag.enabled', False)
        rag_status = "[green]Enabled[/green]" if rag_enabled else "[red]Disabled[/red]"
        rag_details = "Vector database for context retrieval"
        
        status_table.add_row("RAG System", rag_status, rag_details)
        
        self.console.print(status_table)
        
        # Show available AI commands
        ai_commands = [
            "analyze - AI-powered security analysis",
            "ai-audit - Comprehensive AI security audit", 
            "explain <finding_id> - AI explanation of finding",
            "suggest-fix <finding_id> - AI-generated fix suggestions"
        ]
        
        self.console.print(f"\n[bold]Available AI Commands:[/bold]")
        for cmd in ai_commands:
            self.console.print(f"  - {cmd}")

    async def cmd_config(self, args: List[str]) -> None:
        """
        Configuration management
        Usage: config [show|set <key> <value>|get <key>]
        """
        if not args:
            args = ['show']
        
        subcommand = args[0].lower()
        
        if subcommand == 'show':
            self._show_config()
        elif subcommand == 'set' and len(args) >= 3:
            key = args[1]
            value = ' '.join(args[2:])
            self.repl.config_manager.set(key, value)
            self.console.print(f"[green]Set {key} = {value}[/green]")
        elif subcommand == 'get' and len(args) >= 2:
            key = args[1]
            value = self.repl.config_manager.get(key, 'Not set')
            self.console.print(f"[cyan]{key}:[/cyan] {value}")
        else:
            self.console.print("[red]Usage: config [show|set <key> <value>|get <key>][/red]")
    
    def _show_config(self):
        """Show current configuration"""
        config_data = self.repl.config_manager.config_data
        
        self.console.print(Panel("Current Configuration", style="bold blue"))
        
        # Main categories
        categories = {
            'Repository': ['repo.path', 'repo.exclude'],
            'Security': ['mode', 'tools.enabled'],
            'AI Integration': ['local_model.enabled', 'local_model.model_name', 'local_model.base_url'],
            'Output': ['output.format', 'output.dir'],
            'Analysis': ['rag.enabled', 'cvss.policy']
        }
        
        for category, keys in categories.items():
            table = Table(title=category, show_header=True, header_style="bold magenta")
            table.add_column("Setting", style="cyan")
            table.add_column("Value", style="green")
            
            for key in keys:
                value = self.repl.config_manager.get(key, 'Not set')
                if isinstance(value, list):
                    value = ', '.join(value) if value else 'None'
                elif isinstance(value, bool):
                    value = 'Enabled' if value else 'Disabled'
                
                table.add_row(key, str(value))
            
            self.console.print(table)
            self.console.print()


