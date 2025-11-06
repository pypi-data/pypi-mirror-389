"""
Auto-completion for REPL commands
Provides intelligent tab completion for commands, modules, and options
"""

from typing import Dict, List, Iterable

from prompt_toolkit.completion import Completer, Completion
from prompt_toolkit.document import Document


class SecureCompleter(Completer):
    """Tab completion for SecureCLI commands"""
    
    def __init__(self, repl):
        self.repl = repl
        
        # Command completions
        self.commands = [
            'help', 'workspace', 'use', 'show', 'set', 'unset', 'run', 'back',
            'scan', 'report', 'script', 'exit', 'quit', 'status', 'modules',
            'languages', 'analyze', 'github', 'clear', 'cls', 'ai', 'ai-status',
            'explain', 'tools', 'config'
        ]
        
        # Available modules (all 27+ security scanners)
        self.modules = [
            # Core Security Scanners
            'scanner/semgrep',
            'scanner/gitleaks', 
            'scanner/bandit',
            
            # Language-Specific Scanners
            'scanner/java',
            'scanner/csharp',
            'scanner/cpp',
            'scanner/c',
            'scanner/rust',
            'scanner/go',
            'scanner/php',
            'scanner/ruby',
            'scanner/python',
            'scanner/javascript',
            
            # Mobile Development
            'scanner/swift',
            'scanner/kotlin',
            'scanner/objective-c',
            'scanner/dart',
            
            # Functional Programming
            'scanner/haskell',
            'scanner/scala',
            'scanner/fsharp',
            'scanner/erlang',
            
            # Scripting Languages
            'scanner/perl',
            'scanner/lua',
            
            # Web3/Smart Contract
            'scanner/slither',
            'scanner/vyper',
            'scanner/cairo',
            'scanner/move',
            'scanner/clarity',
            
            # Legacy support
            'scanner/gosec',  # alias for scanner/go
            
            # Workflow Modules
            'auditor/generic',
            'auditor/solidity',
            'auditor/web2/api',
            'auditor/web2/frontend',
            'auditor/web3/contracts',
            'auditor/web3/bridges',
            'tighten/prune_dead_code',
            'tighten/remove_unused',
            'tighten/restrict_permissions',
            'report/summary',
            'report/full',
            'report/mermaid',
        ]
        
        # Global options
        self.global_options = [
            'repo.path',
            'repo.exclude',
            'mode',
            'domain.profiles',
            'llm.model',
            'llm.provider',
            'llm.max_tokens',
            'rag.enabled',
            'rag.k',
            'cvss.policy',
            'ci.block_on',
            'output.dir',
            'output.generate_chart_images',
            'redact.enabled',
            'sandbox.enabled',
            'tools.enabled',
            'severity_min',
        ]
        
        # Module-specific options
        self.module_options = {
            # Core Security Scanners
            'scanner/semgrep': ['rules_path', 'config', 'severity_min'],
            'scanner/gitleaks': ['config_path', 'detect_mode'],
            'scanner/bandit': ['config_file', 'skip_tests', 'severity_level'],
            
            # Language-Specific Scanners
            'scanner/java': ['spotbugs_config', 'pmd_ruleset', 'include_tests'],
            'scanner/csharp': ['devskim_rules', 'roslyn_analyzers', 'exclude_generated'],
            'scanner/cpp': ['clang_checks', 'cppcheck_config', 'include_headers'],
            'scanner/c': ['splint_config', 'clang_static', 'gcc_warnings'],
            'scanner/rust': ['clippy_config', 'cargo_audit', 'deny_config'],
            'scanner/go': ['gosec_config', 'exclude_rules', 'include_tests'],
            'scanner/php': ['psalm_config', 'phpstan_level', 'phpcs_standard'],
            'scanner/ruby': ['brakeman_config', 'rubocop_config', 'bundle_audit'],
            'scanner/python': ['bandit_config', 'safety_db', 'exclude_dirs'],
            'scanner/javascript': ['eslint_config', 'npm_audit', 'typescript'],
            
            # Mobile Development
            'scanner/swift': ['swiftlint_config', 'periphery_config', 'xcode_project'],
            'scanner/kotlin': ['detekt_config', 'ktlint_rules', 'android_lint'],
            'scanner/objective-c': ['oclint_config', 'clang_checks', 'xcode_warnings'],
            'scanner/dart': ['analysis_options', 'flutter_analyze', 'pub_deps'],
            
            # Functional Programming
            'scanner/haskell': ['hlint_config', 'weeder_config', 'ghc_warnings'],
            'scanner/scala': ['scalafix_config', 'wartremover_rules', 'scalastyle'],
            'scanner/fsharp': ['fsharplint_config', 'fantomas_config', 'ionide_rules'],
            'scanner/erlang': ['elvis_config', 'dialyzer_plt', 'credo_config'],
            
            # Scripting Languages
            'scanner/perl': ['perlcritic_config', 'severity_level', 'policy_theme'],
            'scanner/lua': ['luacheck_config', 'globals', 'std_modules'],
            
            # Web3/Smart Contract
            'scanner/slither': ['solc_version', 'optimization'],
            'scanner/vyper': ['vyper_version', 'mythril_config'],
            'scanner/cairo': ['cairo_version', 'protostar_config'],
            'scanner/move': ['move_prover', 'sui_analyzer'],
            'scanner/clarity': ['clarinet_config', 'stacks_version'],
            
            # Legacy aliases
            'scanner/gosec': ['gosec_config', 'exclude_rules', 'include_tests'],
            
            # Workflow Modules
            'auditor/generic': ['temperature', 'max_tokens', 'model'],
            'auditor/solidity': ['focus_areas', 'check_reentrancy', 'check_overflow'],
        }
        
        # Domain profiles
        self.profiles = [
            'web2:api',
            'web2:frontend', 
            'web2:microservices',
            'web2:data',
            'web2:infra',
            'web3:solidity',
            'web3:vyper',
            'web3:rust',
            'web3:bridges',
            'web3:consensus',
            'web3:wallets',
        ]
    
    def get_completions(self, document: Document, complete_event) -> Iterable[Completion]:
        """Generate completions based on current context"""
        text = document.text_before_cursor
        words = text.split()
        
        if not words:
            # Complete command names
            for cmd in self.commands:
                yield Completion(cmd, start_position=0)
            return
        
        command = words[0].lower()
        
        # Command-specific completions
        if command == 'help':
            self._complete_help(words, text, complete_event)
        elif command == 'workspace':
            yield from self._complete_workspace(words, text)
        elif command == 'use':
            yield from self._complete_use(words, text)
        elif command == 'show':
            yield from self._complete_show(words, text)
        elif command == 'set':
            yield from self._complete_set(words, text)
        elif command == 'unset':
            yield from self._complete_unset(words, text)
        elif command == 'profiles':
            yield from self._complete_profiles(words, text)
        elif command == 'scan':
            yield from self._complete_scan(words, text)
        elif command == 'report':
            yield from self._complete_report(words, text)
        elif command == 'explain':
            yield from self._complete_explain(words, text)
        elif command == 'github':
            yield from self._complete_github(words, text)
        elif command == 'tools':
            yield from self._complete_tools(words, text)
        elif command == 'config':
            yield from self._complete_config(words, text)
        elif len(words) == 1 and not text.endswith(' '):
            # Still typing command name
            prefix = words[0]
            for cmd in self.commands:
                if cmd.startswith(prefix):
                    yield Completion(cmd, start_position=-len(prefix))
    
    def _complete_help(self, words: List[str], text: str, complete_event) -> Iterable[Completion]:
        """Complete help command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            prefix = words[1] if len(words) == 2 else ''
            for cmd in self.commands:
                if cmd.startswith(prefix):
                    yield Completion(cmd, start_position=-len(prefix))
    
    def _complete_workspace(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete workspace command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            actions = ['list', 'create', 'use', 'delete']
            prefix = words[1] if len(words) == 2 else ''
            for action in actions:
                if action.startswith(prefix):
                    yield Completion(action, start_position=-len(prefix))
        elif len(words) >= 2 and words[1] in ['use', 'delete']:
            # Complete workspace names
            workspaces = self.repl.workspace_manager.list_workspaces()
            prefix = words[2] if len(words) == 3 and not text.endswith(' ') else ''
            for ws in workspaces:
                if ws.startswith(prefix):
                    yield Completion(ws, start_position=-len(prefix))
    
    def _complete_use(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete use command (modules)"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            prefix = words[1] if len(words) == 2 else ''
            for module in self.modules:
                if module.startswith(prefix):
                    yield Completion(module, start_position=-len(prefix))
    
    def _complete_show(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete show command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            targets = ['modules', 'options']
            prefix = words[1] if len(words) == 2 else ''
            for target in targets:
                if target.startswith(prefix):
                    yield Completion(target, start_position=-len(prefix))
    
    def _complete_set(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete set command (options)"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            # Complete option names
            if self.repl.current_module:
                options = self.module_options.get(self.repl.current_module, [])
            else:
                options = self.global_options
            
            prefix = words[1] if len(words) == 2 else ''
            for option in options:
                if option.startswith(prefix):
                    yield Completion(option, start_position=-len(prefix))
        elif len(words) == 3 and not text.endswith(' '):
            # Complete option values
            option_name = words[1]
            self._complete_option_values(option_name, words[2])
    
    def _complete_unset(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete unset command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            # Show currently set options
            if self.repl.current_module:
                options = list(self.repl.module_options.keys())
            else:
                options = self.global_options  # TODO: Get actually set options
            
            prefix = words[1] if len(words) == 2 else ''
            for option in options:
                if option.startswith(prefix):
                    yield Completion(option, start_position=-len(prefix))
    
    def _complete_profiles(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete profiles command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            actions = ['list', 'use', 'show']
            prefix = words[1] if len(words) == 2 else ''
            for action in actions:
                if action.startswith(prefix):
                    yield Completion(action, start_position=-len(prefix))
        elif len(words) >= 2 and words[1] == 'use':
            prefix = words[2] if len(words) == 3 and not text.endswith(' ') else ''
            for profile in self.profiles:
                if profile.startswith(prefix):
                    yield Completion(profile, start_position=-len(prefix))
    
    def _complete_scan(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete scan command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            modes = ['quick', 'deep', 'comprehensive']
            prefix = words[1] if len(words) == 2 else ''
            for mode in modes:
                if mode.startswith(prefix):
                    yield Completion(mode, start_position=-len(prefix))
    
    def _complete_report(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete report command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            types = ['markdown', 'json', 'sarif', 'csv', 'all', 'ci']
            prefix = words[1] if len(words) == 2 else ''
            for rtype in types:
                if rtype.startswith(prefix):
                    yield Completion(rtype, start_position=-len(prefix))

    def _complete_explain(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete explain command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            prefix = words[1] if len(words) == 2 else ''
            findings = getattr(self.repl.command_handler, 'last_findings', [])
            total = len(findings)
            if total == 0:
                return
            for i in range(1, min(total, 20) + 1):
                candidate = str(i)
                if candidate.startswith(prefix):
                    yield Completion(candidate, start_position=-len(prefix))
    
    def _complete_option_values(self, option_name: str, prefix: str) -> Iterable[Completion]:
        """Complete option values based on option type"""
        value_suggestions = {
            'mode': ['quick', 'deep', 'comprehensive', 'redteam', 'refactor'],
            'severity_min': ['low', 'medium', 'high', 'critical'],
            'cvss.policy': ['block_critical', 'block_high', 'block_medium', 'warn_only'],
            'llm.model': ['gpt-4', 'gpt-3.5-turbo', 'claude-3', 'llama2', 'deepseek-coder'],
            'llm.provider': ['auto', 'openai', 'anthropic', 'local'],
            'rag.enabled': ['true', 'false'],
            'sandbox.enabled': ['true', 'false'],
            'redact.enabled': ['true', 'false'],
            'output.generate_chart_images': ['true', 'false'],
        }
        
        if option_name in value_suggestions:
            for value in value_suggestions[option_name]:
                if value.startswith(prefix):
                    yield Completion(value, start_position=-len(prefix))
    
    def _complete_github(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete github command"""
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            # Suggest common GitHub URL patterns
            prefix = words[1] if len(words) == 2 else ''
            suggestions = [
                'https://github.com/',
                'git@github.com:',
            ]
            for suggestion in suggestions:
                if suggestion.startswith(prefix):
                    yield Completion(suggestion, start_position=-len(prefix))
        elif len(words) == 2 or (len(words) == 3 and not text.endswith(' ')):
            # Branch name suggestions
            prefix = words[2] if len(words) == 3 else ''
            branches = ['main', 'master', 'develop', 'dev', 'staging']
            for branch in branches:
                if branch.startswith(prefix):
                    yield Completion(branch, start_position=-len(prefix))
        elif len(words) == 3 or (len(words) == 4 and not text.endswith(' ')):
            # Scan mode suggestions
            prefix = words[3] if len(words) == 4 else ''
            modes = ['quick', 'comprehensive', 'deep']
            for mode in modes:
                if mode.startswith(prefix):
                    yield Completion(mode, start_position=-len(prefix))

    def _complete_tools(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete tools command"""
        subcommands = ['list', 'check', 'install', 'info']
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            prefix = words[1] if len(words) == 2 else ''
            for sub in subcommands:
                if sub.startswith(prefix):
                    yield Completion(sub, start_position=-len(prefix))
        elif len(words) == 3 and words[1] == 'info' and not text.endswith(' '):
            tools = [
                'bandit', 'semgrep', 'gitleaks', 'gosec', 'slither', 'npm_audit',
                'php_analyzer', 'java_analyzer', 'cpp_analyzer', 'csharp_analyzer',
                'ruby_analyzer', 'rust_analyzer', 'swift_analyzer', 'kotlin_analyzer',
                'scala_analyzer', 'go_analyzer', 'solidity_analyzer', 'vyper_analyzer'
            ]
            prefix = words[2]
            for tool in tools:
                if tool.startswith(prefix):
                    yield Completion(tool, start_position=-len(prefix))

    def _complete_config(self, words: List[str], text: str) -> Iterable[Completion]:
        """Complete config command"""
        subcommands = ['show', 'set', 'get']
        if len(words) == 1 or (len(words) == 2 and not text.endswith(' ')):
            prefix = words[1] if len(words) == 2 else ''
            for sub in subcommands:
                if sub.startswith(prefix):
                    yield Completion(sub, start_position=-len(prefix))
        elif len(words) == 3 and words[1] in ['set', 'get'] and not text.endswith(' '):
            # Re-use option completion
            prefix = words[2]
            options = self.global_options
            for option in options:
                if option.startswith(prefix):
                    yield Completion(option, start_position=-len(prefix))
        elif len(words) >= 4 and words[1] == 'set' and not text.endswith(' '):
            option_name = words[2]
            prefix = words[-1]
            yield from self._complete_option_values(option_name, prefix)