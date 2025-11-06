"""
Core REPL implementation using prompt_toolkit
Metasploit-style interactive shell with autocomplete, syntax highlighting, and history
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any

from prompt_toolkit import PromptSession
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.history import FileHistory
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.lexers import PygmentsLexer
from prompt_toolkit.shortcuts import confirm
from prompt_toolkit.styles import Style
from pygments.lexers.shell import BashLexer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from ..config import ConfigManager
from ..workspace import WorkspaceManager
from .commands import CommandHandler
from .completers import SecureCompleter
from .formatters import OutputFormatter


class SecureREPL:
    """Metasploit-style REPL for SecureCLI"""
    
    def __init__(self, config_manager: ConfigManager, workspace_manager: WorkspaceManager):
        self.config_manager = config_manager
        self.workspace_manager = workspace_manager
        self.console = Console()
        self.formatter = OutputFormatter()
        self.command_handler = CommandHandler(self)
        
        # Current module state
        self.current_module: Optional[str] = None
        self.module_options: Dict[str, Any] = {}
        
        # Background jobs
        self.jobs: Dict[str, Any] = {}
        self.sessions: Dict[str, Any] = {}
        
        # Setup prompt session
        self.session = PromptSession(
            history=FileHistory(str(Path.home() / ".securecli_history")),
            auto_suggest=AutoSuggestFromHistory(),
            completer=SecureCompleter(self),
            lexer=PygmentsLexer(BashLexer),
            style=self._get_style(),
            key_bindings=self._get_key_bindings(),
        )
    
    def _get_style(self) -> Style:
        """Define prompt style"""
        return Style.from_dict({
            'prompt': 'ansibrightred bold',
            'module': 'ansibrightred bold',
            'path': 'ansired',
            'error': 'ansibrightred bold',
            'warning': 'ansiyellow',
            'success': 'ansibrightgreen bold',
            'info': 'ansiwhite',
            'dim': 'ansibrightblack',
        })
    
    def _get_key_bindings(self) -> KeyBindings:
        """Define key bindings"""
        kb = KeyBindings()
        
        @kb.add('c-c')
        def _(event):
            """Ctrl+C handling"""
            if self.current_module:
                self.current_module = None
                self.module_options = {}
                event.app.output.write('\n')
                event.app.exit()
            else:
                event.app.exit(exception=KeyboardInterrupt)
        
        return kb
    
    def _get_prompt(self) -> HTML:
        """Generate dynamic prompt"""
        workspace = self.workspace_manager.current_workspace or "default"
        
        if self.current_module:
            return HTML(f'<prompt>secureᶜˡⁱ</prompt>(<module>{self.current_module}</module>)› ')
        else:
            return HTML(f'<prompt>secureᶜˡⁱ</prompt>(<path>{workspace}</path>)› ')
    
    def _show_banner(self) -> None:
        """Display startup banner with enhanced styling"""
        # Clear screen safely
        import subprocess
        try:
            if os.name == 'nt':  # Windows
                subprocess.run(['cmd', '/c', 'cls'], check=True)
            else:  # Unix/Linux
                subprocess.run(['clear'], check=True)
        except subprocess.CalledProcessError:
            # Fallback to console clear
            self.console.clear()
        
        banner = r"""[bold red]
   ███████ ███████  ██████ ██   ██ ██████  ███████  ██████ ██      ██ 
   ██      ██      ██      ██   ██ ██   ██ ██      ██      ██      ██ 
   ███████ █████   ██      ██   ██ ██████  █████   ██      ██      ██ 
        ██ ██      ██      ██   ██ ██   ██ ██      ██      ██      ██ 
   ███████ ███████  ██████  █████  ██   ██ ███████  ██████ ███████ ██[/bold red]
        
[bold cyan]                          Code Security Assessment[/bold cyan]
[bold bright_magenta]                      hit me up on https://x.com/5m477[/bold bright_magenta]
[bold red]   ┌─────────────────────────────────────────────────────────────────┐[/bold red]
[bold red]   │[/bold red] [bold white]AI-Powered Security Analysis with GitHub Integration[/bold white]         [bold red]   │[/bold red]
[bold red]   │[/bold red] [dim]Version 1.0.0 - Multi-Agent Architecture - LLM Enhanced[/dim]        [bold red] │[/bold red]
[bold red]   └─────────────────────────────────────────────────────────────────┘[/bold red]
        """
        self.console.print(banner)
        
        # Enhanced status display
        workspace = self.workspace_manager.current_workspace or "default"
        repo_path = self.config_manager.get("repo.path")
        
        # Check AI status
        ai_key = os.environ.get('OPENAI_API_KEY')
        ai_status = "[green]Active[/green]" if ai_key else "[red]Disabled[/red]"
        
        if repo_path and repo_path != "None":
            repo_display = f"[green]{repo_path}[/green]"
        else:
            repo_display = "[dim red]Not set[/dim red]"
        
        # Status table
        status_info = f"""[red]┌─ SYSTEM STATUS ──────────────────────────────────────────────────┐[/red]
[red]│[/red] [bold]Target Repository:[/bold] {repo_display:<40} [red]                        │[/red]
[red]│[/red] [bold]Active Workspace:[/bold] [cyan]{workspace}[/cyan]                                    [red]    │[/red]
[red]│[/red] [bold]AI Integration:[/bold]   {ai_status}                                    [red] │[/red]
[red]│[/red] [bold]Current Module:[/bold]    [white]{self.current_module or 'None'}[/white]                             [red]             │[/red]
[red]└──────────────────────────────────────────────────────────────────┘[/red]

[dim]» Type [white]help[/white] for commands - [white]status[/white] for details - [white]ai-status[/white] for AI info[/dim]
"""
        self.console.print(status_info)
    
    async def run(self) -> None:
        """Main REPL loop with enhanced session stability"""
        self._show_banner()
        
        session_active = True
        consecutive_errors = 0
        max_consecutive_errors = 5
        
        while session_active:
            try:
                # Reset error counter on successful iteration
                consecutive_errors = 0
                
                command_line = await self.session.prompt_async(self._get_prompt())
                
                if not command_line.strip():
                    continue
                
                # Handle shell escapes safely
                if command_line.startswith('!'):
                    shell_command = command_line[1:].strip()
                    if shell_command:
                        self.console.print("[yellow]Warning: Shell execution disabled for security[/yellow]")
                        self.console.print("[dim]Use built-in commands instead[/dim]")
                    continue
                
                # Parse and execute command
                try:
                    result = await self.command_handler.execute(command_line.strip())
                    
                    if result is False:  # exit command
                        session_active = False
                        break
                except Exception as cmd_error:
                    self.console.print(f"[red]Command execution error: {cmd_error}[/red]")
                    self.console.print("[yellow]Session continuing... Type 'help' for commands[/yellow]")
                    # Don't break the loop - continue with the session
                    
            except KeyboardInterrupt:
                if self.current_module:
                    self.console.print("\n[yellow]Deselecting module...[/yellow]")
                    self.current_module = None
                    self.module_options = {}
                else:
                    self.console.print("\n[yellow]Use 'exit' to quit or Ctrl+C again to force exit[/yellow]")
                    try:
                        await asyncio.sleep(0.1)
                        continue
                    except KeyboardInterrupt:
                        session_active = False
                        break
            except EOFError:
                session_active = False
                break
            except Exception as e:
                consecutive_errors += 1
                self.console.print(f"[red]Session error: {e}[/red]")
                
                if consecutive_errors >= max_consecutive_errors:
                    self.console.print(f"[red]Too many consecutive errors ({consecutive_errors}). Ending session.[/red]")
                    session_active = False
                    break
                else:
                    self.console.print(f"[yellow]Error {consecutive_errors}/{max_consecutive_errors}. Session continuing...[/yellow]")
                    await asyncio.sleep(0.1)  # Brief pause before continuing
        
        self.console.print("\n[cyan]Goodbye![/cyan]")
    
    def execute_script(self, script_path: str) -> None:
        """Execute commands from a script file"""
        try:
            with open(script_path, 'r') as f:
                commands = f.readlines()
            
            self.console.print(f"[blue]Executing script: {script_path}[/blue]")
            
            for line_num, command_line in enumerate(commands, 1):
                command_line = command_line.strip()
                
                if not command_line or command_line.startswith('#'):
                    continue
                
                self.console.print(f"[dim]>>> {command_line}[/dim]")
                
                try:
                    asyncio.run(self.command_handler.execute(command_line))
                except Exception as e:
                    self.console.print(f"[red]Error on line {line_num}: {e}[/red]")
                    break
                    
        except FileNotFoundError:
            self.console.print(f"[red]Script file not found: {script_path}[/red]")
        except Exception as e:
            self.console.print(f"[red]Error executing script: {e}[/red]")
    
    def set_option(self, key: str, value: Any) -> None:
        """Set a configuration option"""
        if self.current_module:
            self.module_options[key] = value
        else:
            self.config_manager.set(key, value)
    
    def get_option(self, key: str, default: Any = None) -> Any:
        """Get a configuration option"""
        if self.current_module and key in self.module_options:
            return self.module_options[key]
        return self.config_manager.get(key, default)