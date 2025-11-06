"""
Universal Language Detection and Analysis System
Comprehensive support for Web2, Web3, and all major programming languages
"""

import os
import re
import json
import logging
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger(__name__)

class LanguageCategory(Enum):
    """Language categories for better organization"""
    WEB2_FRONTEND = "web2_frontend"
    WEB2_BACKEND = "web2_backend"
    WEB3_SMART_CONTRACT = "web3_smart_contract"
    BLOCKCHAIN_L1_L2 = "blockchain_l1_l2"
    MOBILE = "mobile"
    SYSTEMS = "systems"
    DATA_SCIENCE = "data_science"
    INFRASTRUCTURE = "infrastructure"
    CONFIGURATION = "configuration"
    DOCUMENTATION = "documentation"
    UNKNOWN = "unknown"

@dataclass
class LanguageInfo:
    """Complete language information"""
    name: str
    category: LanguageCategory
    extensions: List[str]
    security_tools: List[str]
    frameworks: List[str]
    vulnerability_patterns: List[str]
    analysis_priority: int  # 1-10, higher = more security critical
    ecosystem_risks: List[str]

class UniversalLanguageDetector:
    """
    Universal language detection supporting all major programming languages
    Web2, Web3, Mobile, Systems, Infrastructure, and more
    """
    
    def __init__(self):
        self.languages = self._initialize_language_registry()
        self.extension_map = self._build_extension_map()
        self.filename_map = self._build_filename_map()
        self.content_patterns = self._build_content_patterns()
    
    def _initialize_language_registry(self) -> Dict[str, LanguageInfo]:
        """Initialize comprehensive language registry"""
        
        return {
            # === WEB2 FRONTEND ===
            'javascript': LanguageInfo(
                name='JavaScript',
                category=LanguageCategory.WEB2_FRONTEND,
                extensions=['.js', '.mjs', '.jsx'],
                security_tools=['semgrep', 'eslint', 'retire.js', 'npm_audit'],
                frameworks=['React', 'Vue', 'Angular', 'Express', 'Node.js'],
                vulnerability_patterns=['XSS', 'prototype_pollution', 'code_injection', 'path_traversal'],
                analysis_priority=8,
                ecosystem_risks=['npm_vulnerabilities', 'supply_chain', 'dependency_confusion']
            ),
            
            'typescript': LanguageInfo(
                name='TypeScript',
                category=LanguageCategory.WEB2_FRONTEND,
                extensions=['.ts', '.tsx', '.d.ts'],
                security_tools=['semgrep', 'eslint', 'tslint', 'npm_audit'],
                frameworks=['React', 'Angular', 'Vue', 'Next.js', 'NestJS'],
                vulnerability_patterns=['type_confusion', 'any_type_abuse', 'unsafe_casting'],
                analysis_priority=7,
                ecosystem_risks=['npm_vulnerabilities', 'type_safety_bypass']
            ),
            
            'vue': LanguageInfo(
                name='Vue.js',
                category=LanguageCategory.WEB2_FRONTEND,
                extensions=['.vue'],
                security_tools=['semgrep', 'eslint-plugin-vue'],
                frameworks=['Vue.js', 'Nuxt.js', 'Quasar'],
                vulnerability_patterns=['template_injection', 'XSS', 'v-html_misuse'],
                analysis_priority=6,
                ecosystem_risks=['component_vulnerabilities', 'template_safety']
            ),
            
            'svelte': LanguageInfo(
                name='Svelte',
                category=LanguageCategory.WEB2_FRONTEND,
                extensions=['.svelte'],
                security_tools=['semgrep', 'eslint'],
                frameworks=['Svelte', 'SvelteKit'],
                vulnerability_patterns=['reactive_statement_injection', 'XSS'],
                analysis_priority=5,
                ecosystem_risks=['compilation_vulnerabilities']
            ),
            
            'html': LanguageInfo(
                name='HTML',
                category=LanguageCategory.WEB2_FRONTEND,
                extensions=['.html', '.htm'],
                security_tools=['semgrep', 'html_validator'],
                frameworks=['Bootstrap', 'Foundation'],
                vulnerability_patterns=['XSS', 'clickjacking', 'CSRF'],
                analysis_priority=4,
                ecosystem_risks=['inline_scripts', 'external_resources']
            ),
            
            'css': LanguageInfo(
                name='CSS',
                category=LanguageCategory.WEB2_FRONTEND,
                extensions=['.css', '.scss', '.sass', '.less', '.styl'],
                security_tools=['semgrep', 'stylelint'],
                frameworks=['Sass', 'Less', 'Stylus', 'PostCSS'],
                vulnerability_patterns=['css_injection', 'exfiltration', 'keyloggers'],
                analysis_priority=3,
                ecosystem_risks=['third_party_fonts', 'external_stylesheets']
            ),
            
            # === WEB2 BACKEND ===
            'python': LanguageInfo(
                name='Python',
                category=LanguageCategory.WEB2_BACKEND,
                extensions=['.py', '.pyw', '.pyx', '.pyi'],
                security_tools=['bandit', 'semgrep', 'safety', 'pip-audit'],
                frameworks=['Django', 'Flask', 'FastAPI', 'Tornado', 'Pyramid'],
                vulnerability_patterns=['sql_injection', 'code_injection', 'deserialization', 'path_traversal'],
                analysis_priority=9,
                ecosystem_risks=['pypi_vulnerabilities', 'pickle_deserialization', 'eval_injection']
            ),
            
            'java': LanguageInfo(
                name='Java',
                category=LanguageCategory.WEB2_BACKEND,
                extensions=['.java', '.class', '.jar'],
                security_tools=['semgrep', 'spotbugs', 'pmd', 'snyk'],
                frameworks=['Spring', 'Struts', 'JSF', 'Hibernate'],
                vulnerability_patterns=['deserialization', 'xml_injection', 'log4j', 'reflection'],
                analysis_priority=9,
                ecosystem_risks=['maven_vulnerabilities', 'serialization_attacks', 'class_loading']
            ),
            
            'csharp': LanguageInfo(
                name='C#',
                category=LanguageCategory.WEB2_BACKEND,
                extensions=['.cs', '.csx'],
                security_tools=['semgrep', 'security_code_scan', 'roslyn_analyzers'],
                frameworks=['.NET', 'ASP.NET', 'Entity Framework', 'Blazor'],
                vulnerability_patterns=['sql_injection', 'xml_injection', 'deserialization', 'ldap_injection'],
                analysis_priority=8,
                ecosystem_risks=['nuget_vulnerabilities', 'reflection_abuse']
            ),
            
            'go': LanguageInfo(
                name='Go',
                category=LanguageCategory.WEB2_BACKEND,
                extensions=['.go'],
                security_tools=['gosec', 'semgrep', 'nancy'],
                frameworks=['Gin', 'Echo', 'Fiber', 'Gorilla'],
                vulnerability_patterns=['sql_injection', 'path_traversal', 'race_conditions', 'crypto_weak'],
                analysis_priority=7,
                ecosystem_risks=['module_vulnerabilities', 'goroutine_leaks']
            ),
            
            'rust': LanguageInfo(
                name='Rust',
                category=LanguageCategory.SYSTEMS,
                extensions=['.rs'],
                security_tools=['semgrep', 'cargo_audit', 'clippy'],
                frameworks=['Actix', 'Rocket', 'Warp', 'Tokio'],
                vulnerability_patterns=['unsafe_code', 'memory_leaks', 'panic_abuse'],
                analysis_priority=6,
                ecosystem_risks=['crates_io_vulnerabilities', 'unsafe_blocks']
            ),
            
            'php': LanguageInfo(
                name='PHP',
                category=LanguageCategory.WEB2_BACKEND,
                extensions=['.php', '.phtml', '.php3', '.php4', '.php5'],
                security_tools=['semgrep', 'phpcs', 'psalm', 'phpstan'],
                frameworks=['Laravel', 'Symfony', 'CodeIgniter', 'Zend'],
                vulnerability_patterns=['sql_injection', 'lfi', 'rfi', 'code_injection', 'deserialization'],
                analysis_priority=9,
                ecosystem_risks=['composer_vulnerabilities', 'include_vulnerabilities']
            ),
            
            'ruby': LanguageInfo(
                name='Ruby',
                category=LanguageCategory.WEB2_BACKEND,
                extensions=['.rb', '.rbw'],
                security_tools=['brakeman', 'semgrep', 'bundler-audit'],
                frameworks=['Rails', 'Sinatra', 'Hanami'],
                vulnerability_patterns=['sql_injection', 'mass_assignment', 'csrf', 'yaml_deserialization'],
                analysis_priority=8,
                ecosystem_risks=['gem_vulnerabilities', 'eval_injection']
            ),
            
            # === WEB3 & SMART CONTRACTS ===
            'solidity': LanguageInfo(
                name='Solidity',
                category=LanguageCategory.WEB3_SMART_CONTRACT,
                extensions=['.sol'],
                security_tools=['slither', 'mythril', 'semgrep', 'manticore'],
                frameworks=['OpenZeppelin', 'Hardhat', 'Truffle', 'Foundry'],
                vulnerability_patterns=['reentrancy', 'integer_overflow', 'access_control', 'front_running'],
                analysis_priority=10,
                ecosystem_risks=['compiler_bugs', 'protocol_risks', 'economic_attacks']
            ),
            
            'vyper': LanguageInfo(
                name='Vyper',
                category=LanguageCategory.WEB3_SMART_CONTRACT,
                extensions=['.vy'],
                security_tools=['slither', 'semgrep', 'mythril'],
                frameworks=['Vyper', 'Ape'],
                vulnerability_patterns=['reentrancy', 'overflow', 'underflow', 'access_control'],
                analysis_priority=10,
                ecosystem_risks=['compiler_limitations', 'readability_assumptions']
            ),
            
            'cairo': LanguageInfo(
                name='Cairo',
                category=LanguageCategory.BLOCKCHAIN_L1_L2,
                extensions=['.cairo'],
                security_tools=['semgrep', 'cairo_analyzer'],
                frameworks=['StarkNet', 'StarkEx'],
                vulnerability_patterns=['proof_vulnerabilities', 'state_transitions', 'recursion_limits'],
                analysis_priority=9,
                ecosystem_risks=['proving_system_bugs', 'zkSTARK_limitations']
            ),
            
            'move': LanguageInfo(
                name='Move',
                category=LanguageCategory.BLOCKCHAIN_L1_L2,
                extensions=['.move'],
                security_tools=['move_prover', 'semgrep'],
                frameworks=['Aptos', 'Sui', 'Diem'],
                vulnerability_patterns=['resource_leaks', 'capability_misuse', 'module_publishing'],
                analysis_priority=9,
                ecosystem_risks=['vm_vulnerabilities', 'formal_verification_gaps']
            ),
            
            'func': LanguageInfo(
                name='FunC',
                category=LanguageCategory.BLOCKCHAIN_L1_L2,
                extensions=['.fc', '.func'],
                security_tools=['semgrep', 'tolk'],
                frameworks=['TON', 'Fift'],
                vulnerability_patterns=['gas_abuse', 'message_handling', 'storage_corruption'],
                analysis_priority=8,
                ecosystem_risks=['vm_limitations', 'actor_model_bugs']
            ),
            
            'tact': LanguageInfo(
                name='Tact',
                category=LanguageCategory.BLOCKCHAIN_L1_L2,
                extensions=['.tact'],
                security_tools=['semgrep', 'tact_analyzer'],
                frameworks=['TON'],
                vulnerability_patterns=['message_races', 'state_corruption', 'bouncing'],
                analysis_priority=8,
                ecosystem_risks=['compilation_bugs', 'runtime_exceptions']
            ),
            
            'clarity': LanguageInfo(
                name='Clarity',
                category=LanguageCategory.BLOCKCHAIN_L1_L2,
                extensions=['.clar'],
                security_tools=['clarinet', 'semgrep'],
                frameworks=['Stacks', 'Clarinet'],
                vulnerability_patterns=['trait_misuse', 'map_corruption', 'authorization_bypass'],
                analysis_priority=8,
                ecosystem_risks=['interpreter_bugs', 'decidability_issues']
            ),
            
            'ink': LanguageInfo(
                name='ink!',
                category=LanguageCategory.BLOCKCHAIN_L1_L2,
                extensions=['.ink'],
                security_tools=['cargo_contract', 'semgrep'],
                frameworks=['Polkadot', 'Substrate'],
                vulnerability_patterns=['trait_object_safety', 'panic_handling', 'storage_layout'],
                analysis_priority=8,
                ecosystem_risks=['wasm_vulnerabilities', 'substrate_runtime']
            ),
            
            'cadence': LanguageInfo(
                name='Cadence',
                category=LanguageCategory.BLOCKCHAIN_L1_L2,
                extensions=['.cdc'],
                security_tools=['flow_analyzer', 'semgrep'],
                frameworks=['Flow'],
                vulnerability_patterns=['resource_oriented_bugs', 'capability_leaks', 'path_storage'],
                analysis_priority=8,
                ecosystem_risks=['account_model_bugs', 'transaction_fees']
            ),
            
            # === MOBILE ===
            'swift': LanguageInfo(
                name='Swift',
                category=LanguageCategory.MOBILE,
                extensions=['.swift'],
                security_tools=['semgrep', 'swiftlint', 'periphery'],
                frameworks=['UIKit', 'SwiftUI', 'Combine'],
                vulnerability_patterns=['keychain_misuse', 'url_scheme_hijacking', 'data_protection'],
                analysis_priority=7,
                ecosystem_risks=['app_store_rejection', 'ios_api_misuse']
            ),
            
            'kotlin': LanguageInfo(
                name='Kotlin',
                category=LanguageCategory.MOBILE,
                extensions=['.kt', '.kts'],
                security_tools=['semgrep', 'detekt', 'android_lint'],
                frameworks=['Android', 'Ktor', 'Compose'],
                vulnerability_patterns=['intent_hijacking', 'webview_vulnerabilities', 'storage_leaks'],
                analysis_priority=7,
                ecosystem_risks=['android_api_misuse', 'permission_model']
            ),
            
            'dart': LanguageInfo(
                name='Dart',
                category=LanguageCategory.MOBILE,
                extensions=['.dart'],
                security_tools=['semgrep', 'dart_analyzer', 'flutter_lints'],
                frameworks=['Flutter'],
                vulnerability_patterns=['insecure_storage', 'network_security', 'webview_injection'],
                analysis_priority=6,
                ecosystem_risks=['pub_vulnerabilities', 'platform_channels']
            ),
            
            # === SYSTEMS PROGRAMMING ===
            'c': LanguageInfo(
                name='C',
                category=LanguageCategory.SYSTEMS,
                extensions=['.c', '.h'],
                security_tools=['semgrep', 'cppcheck', 'clang_analyzer', 'valgrind'],
                frameworks=['glibc', 'newlib'],
                vulnerability_patterns=['buffer_overflow', 'use_after_free', 'null_dereference', 'format_string'],
                analysis_priority=10,
                ecosystem_risks=['memory_corruption', 'undefined_behavior']
            ),
            
            'cpp': LanguageInfo(
                name='C++',
                category=LanguageCategory.SYSTEMS,
                extensions=['.cpp', '.cxx', '.cc', '.c++', '.hpp', '.hxx', '.h++'],
                security_tools=['semgrep', 'cppcheck', 'clang_analyzer', 'pvs_studio'],
                frameworks=['STL', 'Boost', 'Qt'],
                vulnerability_patterns=['buffer_overflow', 'use_after_free', 'double_free', 'raii_violations'],
                analysis_priority=10,
                ecosystem_risks=['memory_corruption', 'abi_compatibility']
            ),
            
            # === DATA SCIENCE ===
            'r': LanguageInfo(
                name='R',
                category=LanguageCategory.DATA_SCIENCE,
                extensions=['.r', '.R'],
                security_tools=['semgrep', 'lintr'],
                frameworks=['Shiny', 'ggplot2', 'dplyr'],
                vulnerability_patterns=['code_injection', 'deserialization', 'path_traversal'],
                analysis_priority=6,
                ecosystem_risks=['cran_vulnerabilities', 'data_exposure']
            ),
            
            'julia': LanguageInfo(
                name='Julia',
                category=LanguageCategory.DATA_SCIENCE,
                extensions=['.jl'],
                security_tools=['semgrep', 'julia_analyzer'],
                frameworks=['Plots.jl', 'DataFrames.jl'],
                vulnerability_patterns=['macro_injection', 'eval_abuse', 'package_loading'],
                analysis_priority=5,
                ecosystem_risks=['pkg_vulnerabilities', 'compilation_attacks']
            ),
            
            # === INFRASTRUCTURE ===
            'yaml': LanguageInfo(
                name='YAML',
                category=LanguageCategory.INFRASTRUCTURE,
                extensions=['.yml', '.yaml'],
                security_tools=['semgrep', 'yamllint', 'kube_score'],
                frameworks=['Kubernetes', 'Docker Compose', 'Ansible'],
                vulnerability_patterns=['yaml_bomb', 'deserialization', 'injection'],
                analysis_priority=7,
                ecosystem_risks=['configuration_exposure', 'privilege_escalation']
            ),
            
            'terraform': LanguageInfo(
                name='Terraform',
                category=LanguageCategory.INFRASTRUCTURE,
                extensions=['.tf', '.tfvars'],
                security_tools=['semgrep', 'tfsec', 'checkov', 'terrascan'],
                frameworks=['Terraform', 'Terragrunt'],
                vulnerability_patterns=['resource_exposure', 'privilege_escalation', 'secrets_exposure'],
                analysis_priority=8,
                ecosystem_risks=['state_file_exposure', 'provider_vulnerabilities']
            ),
            
            'dockerfile': LanguageInfo(
                name='Dockerfile',
                category=LanguageCategory.INFRASTRUCTURE,
                extensions=['dockerfile', 'Dockerfile'],
                security_tools=['semgrep', 'hadolint', 'docker_bench'],
                frameworks=['Docker', 'Podman'],
                vulnerability_patterns=['privilege_escalation', 'secrets_exposure', 'layer_vulnerabilities'],
                analysis_priority=8,
                ecosystem_risks=['base_image_vulnerabilities', 'supply_chain']
            ),
            
            # Add more languages as needed...
        }
    
    def _build_extension_map(self) -> Dict[str, str]:
        """Build mapping from file extensions to language names"""
        
        extension_map = {}
        for lang_name, lang_info in self.languages.items():
            for ext in lang_info.extensions:
                extension_map[ext.lower()] = lang_name
        
        return extension_map
    
    def _build_filename_map(self) -> Dict[str, str]:
        """Build mapping from specific filenames to language names"""
        
        return {
            # Configuration files
            'dockerfile': 'dockerfile',
            'Dockerfile': 'dockerfile',
            'docker-compose.yml': 'yaml',
            'docker-compose.yaml': 'yaml',
            'package.json': 'javascript',
            'tsconfig.json': 'typescript',
            'cargo.toml': 'rust',
            'go.mod': 'go',
            'requirements.txt': 'python',
            'pipfile': 'python',
            'gemfile': 'ruby',
            'pom.xml': 'java',
            'build.gradle': 'java',
            'makefile': 'makefile',
            'cmakelists.txt': 'cmake',
            
            # Web3 specific
            'truffle-config.js': 'javascript',
            'hardhat.config.js': 'javascript',
            'foundry.toml': 'rust',
            'dapp.toml': 'rust',
            
            # CI/CD
            '.gitlab-ci.yml': 'yaml',
            '.github/workflows/*.yml': 'yaml',
            'jenkinsfile': 'groovy',
            
            # Documentation
            'readme.md': 'markdown',
            'changelog.md': 'markdown',
        }
    
    def _build_content_patterns(self) -> Dict[str, List[str]]:
        """Build content-based detection patterns"""
        
        return {
            'solidity': [
                r'pragma solidity',
                r'contract\s+\w+',
                r'function\s+\w+.*external',
                r'mapping\s*\(',
                r'\.call\s*\('
            ],
            'vyper': [
                r'@external',
                r'@internal',
                r'@view',
                r'@pure',
                r'interface\s+\w+'
            ],
            'javascript': [
                r'require\s*\(',
                r'module\.exports',
                r'import\s+.*from',
                r'export\s+(default\s+)?',
                r'console\.log'
            ],
            'typescript': [
                r'interface\s+\w+',
                r'type\s+\w+\s*=',
                r':\s*(string|number|boolean)',
                r'export\s+type',
                r'import\s+type'
            ],
            'python': [
                r'def\s+\w+\s*\(',
                r'class\s+\w+',
                r'import\s+\w+',
                r'from\s+\w+\s+import',
                r'if\s+__name__\s*==\s*[\'"]__main__[\'"]'
            ],
            'rust': [
                r'fn\s+\w+\s*\(',
                r'use\s+\w+',
                r'struct\s+\w+',
                r'impl\s+\w+',
                r'let\s+mut\s+\w+'
            ],
            'go': [
                r'package\s+\w+',
                r'import\s+\(',
                r'func\s+\w+\s*\(',
                r'type\s+\w+\s+struct',
                r'go\s+\w+\s*\('
            ]
        }
    
    def detect_language(self, file_path: str, content: str = None) -> Tuple[str, float]:
        """
        Detect programming language for a file
        
        Args:
            file_path: Path to the file
            content: File content (optional, will read if not provided)
            
        Returns:
            Tuple of (language_name, confidence_score)
        """
        
        path = Path(file_path)
        
        # 1. Check by extension first (highest confidence)
        ext = path.suffix.lower()
        if ext in self.extension_map:
            return self.extension_map[ext], 0.9
        
        # 2. Check by filename
        filename = path.name.lower()
        if filename in self.filename_map:
            return self.filename_map[filename], 0.85
        
        # 3. Content-based detection (if content provided)
        if content:
            lang_scores = {}
            
            for lang, patterns in self.content_patterns.items():
                score = 0
                for pattern in patterns:
                    matches = len(re.findall(pattern, content, re.IGNORECASE | re.MULTILINE))
                    score += matches
                
                if score > 0:
                    lang_scores[lang] = score / len(patterns)
            
            if lang_scores:
                best_lang = max(lang_scores, key=lang_scores.get)
                confidence = min(0.8, lang_scores[best_lang] * 0.2)
                return best_lang, confidence
        
        # 4. Fallback to unknown
        return 'unknown', 0.0
    
    def get_language_info(self, language: str) -> Optional[LanguageInfo]:
        """Get complete information about a language"""
        return self.languages.get(language)
    
    def get_security_tools_for_language(self, language: str) -> List[str]:
        """Get applicable security tools for a language"""
        
        lang_info = self.get_language_info(language)
        if lang_info:
            return lang_info.security_tools
        return ['semgrep']  # Fallback to universal tool
    
    def get_vulnerability_patterns_for_language(self, language: str) -> List[str]:
        """Get common vulnerability patterns for a language"""
        
        lang_info = self.get_language_info(language)
        if lang_info:
            return lang_info.vulnerability_patterns
        return []
    
    def analyze_project_languages(self, project_path: str) -> Dict[str, Any]:
        """Analyze all languages used in a project"""
        
        project = Path(project_path)
        language_stats = {}
        total_files = 0
        
        # Scan all files
        for file_path in project.rglob('*'):
            if file_path.is_file():
                total_files += 1
                
                try:
                    # Read content for better detection
                    content = file_path.read_text(encoding='utf-8', errors='ignore')[:1000]  # First 1KB
                    
                    language, confidence = self.detect_language(str(file_path), content)
                    
                    if language not in language_stats:
                        language_stats[language] = {
                            'files': 0,
                            'total_confidence': 0.0,
                            'info': self.get_language_info(language)
                        }
                    
                    language_stats[language]['files'] += 1
                    language_stats[language]['total_confidence'] += confidence
                    
                except Exception as e:
                    logger.debug(f"Failed to read {file_path}: {e}")
                    continue
        
        # Calculate percentages and average confidence
        for lang, stats in language_stats.items():
            stats['percentage'] = (stats['files'] / total_files) * 100
            stats['avg_confidence'] = stats['total_confidence'] / stats['files']
        
        # Sort by file count
        sorted_languages = sorted(
            language_stats.items(),
            key=lambda x: x[1]['files'],
            reverse=True
        )
        
        return {
            'total_files': total_files,
            'languages_detected': len(language_stats),
            'language_breakdown': dict(sorted_languages),
            'primary_language': sorted_languages[0][0] if sorted_languages else 'unknown',
            'security_priority_languages': self._get_security_priority_languages(language_stats),
            'web3_languages': self._get_web3_languages(language_stats),
            'recommended_tools': self._get_recommended_tools(language_stats)
        }
    
    def _get_security_priority_languages(self, language_stats: Dict) -> List[str]:
        """Get languages that should be prioritized for security analysis"""
        
        priority_langs = []
        for lang, stats in language_stats.items():
            lang_info = stats.get('info')
            if lang_info and lang_info.analysis_priority >= 8:
                priority_langs.append(lang)
        
        return priority_langs
    
    def _get_web3_languages(self, language_stats: Dict) -> List[str]:
        """Get Web3/blockchain languages detected"""
        
        web3_langs = []
        web3_categories = [
            LanguageCategory.WEB3_SMART_CONTRACT,
            LanguageCategory.BLOCKCHAIN_L1_L2
        ]
        
        for lang, stats in language_stats.items():
            lang_info = stats.get('info')
            if lang_info and lang_info.category in web3_categories:
                web3_langs.append(lang)
        
        return web3_langs
    
    def _get_recommended_tools(self, language_stats: Dict) -> Set[str]:
        """Get recommended security tools based on detected languages"""
        
        tools = set()
        for lang, stats in language_stats.items():
            lang_info = stats.get('info')
            if lang_info:
                tools.update(lang_info.security_tools)
        
        return list(tools)


# Global instance
language_detector = UniversalLanguageDetector()

# Convenience functions
def detect_file_language(file_path: str, content: str = None) -> Tuple[str, float]:
    """Detect language for a single file"""
    return language_detector.detect_language(file_path, content)

def get_security_tools_for_file(file_path: str) -> List[str]:
    """Get security tools applicable for a file"""
    language, _ = detect_file_language(file_path)
    return language_detector.get_security_tools_for_language(language)

def analyze_project_languages(project_path: str) -> Dict[str, Any]:
    """Analyze all languages in a project"""
    return language_detector.analyze_project_languages(project_path)