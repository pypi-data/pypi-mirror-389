"""
GitHub Repository Integration
Direct repository analysis from GitHub URLs with comprehensive language support
"""

import asyncio
import os
import shutil
import tempfile
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from urllib.parse import urlparse
import subprocess

# Conditional git import
try:
    import git
    GIT_AVAILABLE = True
except (ImportError, Exception):
    GIT_AVAILABLE = False
    git = None

from ..schemas.findings import Finding
from ..modules import create_analysis_engine
from ..report import ReportGenerator
from ..analysis import annotate_cross_file_context

logger = logging.getLogger(__name__)

class GitHubRepositoryAnalyzer:
    """
    Analyzes GitHub repositories directly from URLs
    Supports all major programming languages and frameworks
    """
    
    # Comprehensive language support mapping
    LANGUAGE_EXTENSIONS = {
        # Web2 Frontend
        '.js': 'javascript',
        '.jsx': 'javascript',
        '.ts': 'typescript', 
        '.tsx': 'typescript',
        '.vue': 'vue',
        '.svelte': 'svelte',
        '.html': 'html',
        '.htm': 'html',
        '.css': 'css',
        '.scss': 'scss',
        '.sass': 'sass',
        '.less': 'less',
        '.styl': 'stylus',
        
        # Web2 Backend
        '.py': 'python',
        '.pyx': 'python',
        '.pyi': 'python',
        '.java': 'java',
        '.kt': 'kotlin',
        '.kts': 'kotlin',
        '.scala': 'scala',
        '.groovy': 'groovy',
        '.go': 'go',
        '.rs': 'rust',
        '.rb': 'ruby',
        '.php': 'php',
        '.cs': 'csharp',
        '.fs': 'fsharp',
        '.vb': 'vb.net',
        '.c': 'c',
        '.cc': 'cpp',
        '.cpp': 'cpp',
        '.cxx': 'cpp',
        '.c++': 'cpp',
        '.h': 'c_header',
        '.hpp': 'cpp_header',
        '.hxx': 'cpp_header',
        '.swift': 'swift',
        '.m': 'objective-c',
        '.mm': 'objective-cpp',
        '.pl': 'perl',
        '.pm': 'perl',
        '.r': 'r',
        '.R': 'r',
        '.lua': 'lua',
        '.dart': 'dart',
        '.ex': 'elixir',
        '.exs': 'elixir',
        '.erl': 'erlang',
        '.hrl': 'erlang',
        '.clj': 'clojure',
        '.cljs': 'clojurescript',
        '.hs': 'haskell',
        '.lhs': 'haskell',
        '.ml': 'ocaml',
        '.mli': 'ocaml',
        
        # Web3 & Blockchain
        '.sol': 'solidity',
        '.vy': 'vyper',
        '.fe': 'fe',
        '.cairo': 'cairo',
        '.clar': 'clarity',
        '.rsh': 'reach',
        '.ride': 'waves',
        '.ligo': 'ligo',
        '.mligo': 'cameligo',
        '.religo': 'reasonligo',
        '.jsligo': 'jsligo',
        '.aes': 'sophia',
        '.ak': 'aiken',
        '.purs': 'purescript',
        '.move': 'move',
        '.fc': 'func',
        '.teal': 'teal',
        '.py': 'algorand_python',  # Algorand PyTeal
        
        # Layer 1 & Layer 2 Specific
        '.wasm': 'webassembly',
        '.wat': 'webassembly_text',
        '.ink': 'ink',  # Polkadot
        '.near': 'near',
        '.cdc': 'cadence',  # Flow
        '.scilla': 'scilla',  # Zilliqa
        '.mvir': 'move_ir',  # Libra/Diem
        '.ton': 'ton',
        '.tact': 'tact',  # TON
        
        # Infrastructure & DevOps
        '.yml': 'yaml',
        '.yaml': 'yaml',
        '.json': 'json',
        '.toml': 'toml',
        '.ini': 'ini',
        '.cfg': 'config',
        '.conf': 'config',
        '.xml': 'xml',
        '.tf': 'terraform',
        '.tfvars': 'terraform_vars',
        '.hcl': 'hcl',
        '.nomad': 'nomad',
        '.consul': 'consul',
        '.k8s': 'kubernetes',
        '.helm': 'helm',
        
        # Shell & Scripts
        '.sh': 'bash',
        '.bash': 'bash',
        '.zsh': 'zsh',
        '.fish': 'fish',
        '.ps1': 'powershell',
        '.psm1': 'powershell',
        '.bat': 'batch',
        '.cmd': 'batch',
        
        # Database
        '.sql': 'sql',
        '.psql': 'postgresql',
        '.mysql': 'mysql',
        '.sqlite': 'sqlite',
        '.cql': 'cassandra',
        '.cypher': 'neo4j',
        '.gql': 'graphql',
        '.graphql': 'graphql',
        
        # Mobile
        '.android': 'android',
        '.ios': 'ios',
        '.flutter': 'flutter',
        '.rn': 'react_native',
        '.xamarin': 'xamarin',
        
        # Documentation
        '.md': 'markdown',
        '.mdx': 'mdx',
        '.rst': 'restructuredtext',
        '.tex': 'latex',
        '.adoc': 'asciidoc',
        
        # Configuration Files
        'dockerfile': 'dockerfile',
        'Dockerfile': 'dockerfile',
        'docker-compose.yml': 'docker_compose',
        'docker-compose.yaml': 'docker_compose',
        'package.json': 'npm_package',
        'yarn.lock': 'yarn_lock',
        'pnpm-lock.yaml': 'pnpm_lock',
        'Cargo.toml': 'cargo_manifest',
        'Cargo.lock': 'cargo_lock',
        'go.mod': 'go_module',
        'go.sum': 'go_sum',
        'requirements.txt': 'pip_requirements',
        'Pipfile': 'pipfile',
        'pyproject.toml': 'python_project',
        'setup.py': 'python_setup',
        'pom.xml': 'maven',
        'build.gradle': 'gradle',
        'CMakeLists.txt': 'cmake',
        'Makefile': 'makefile',
        'webpack.config.js': 'webpack',
        'rollup.config.js': 'rollup',
        'vite.config.js': 'vite',
        'tsconfig.json': 'typescript_config',
        '.eslintrc': 'eslint_config',
        '.prettierrc': 'prettier_config',
        'truffle-config.js': 'truffle',
        'hardhat.config.js': 'hardhat',
        'foundry.toml': 'foundry',
    }
    
    # Security-relevant file patterns
    SECURITY_FILES = [
        'package.json', 'package-lock.json', 'yarn.lock',
        'requirements.txt', 'Pipfile', 'pyproject.toml',
        'go.mod', 'go.sum', 'Cargo.toml', 'Cargo.lock',
        'pom.xml', 'build.gradle', 'composer.json',
        '.env', '.env.*', 'config.yml', 'config.yaml',
        'docker-compose.yml', 'Dockerfile', 'k8s/*.yml',
        'terraform/*.tf', '*.sol', '*.vy',
        '*.js', '*.ts', '*.py', '*.go', '*.rs',
        '*.java', '*.cs', '*.php', '*.rb'
    ]
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.temp_dir = None
        self.github_token = config.get('github.token', os.getenv('GITHUB_TOKEN'))
        self.analysis_engine = create_analysis_engine(config)
        self.report_generator = ReportGenerator(config)
        
    async def analyze_repository(
        self,
        repo_url: str,
        branch: str = 'main',
        scan_mode: str = 'comprehensive',
        target_paths: List[str] = None,
        exclude_paths: List[str] = None
    ) -> Dict[str, Any]:
        """
        Analyze a GitHub repository directly from URL
        
        Args:
            repo_url: GitHub repository URL (https://github.com/owner/repo)
            branch: Branch to analyze (default: main)
            scan_mode: Analysis depth (quick, comprehensive, deep)
            target_paths: Specific paths to analyze (optional)
            exclude_paths: Paths to exclude from analysis
            
        Returns:
            Complete analysis results with findings and reports
        """
        
        logger.info(f"Starting analysis of repository: {repo_url}")
        
        try:
            # Clone repository
            repo_path = await self._clone_repository(repo_url, branch)
            
            # Discover all files
            all_files = await self._discover_files(repo_path, target_paths, exclude_paths)
            
            # Filter security-relevant files
            analyzed_files = self._filter_security_files(all_files)
            
            logger.info(f"Found {len(analyzed_files)} files to analyze across {len(set(self._get_file_language(f) for f in analyzed_files))} languages")
            
            # Perform comprehensive analysis
            analysis_results = await self.analysis_engine.analyze_workspace(
                workspace_path=repo_path,
                file_list=analyzed_files,
                scan_mode=scan_mode
            )
            
            self._enrich_cross_file_context(repo_path, analyzed_files, analysis_results['findings'])

            # Add repository metadata
            analysis_results['repository'] = {
                'url': repo_url,
                'branch': branch,
                'commit': await self._get_latest_commit(repo_path),
                'total_files': len(all_files),
                'analyzed_files': len(analyzed_files),
                'languages_detected': list(set(self._get_file_language(f) for f in analyzed_files)),
                'scan_mode': scan_mode
            }
            
            # Generate file-by-file analysis
            file_analysis = await self._generate_file_analysis(analyzed_files, analysis_results['findings'])
            analysis_results['file_analysis'] = file_analysis
            
            # Generate comprehensive reports
            report_paths = await self.report_generator.generate_full_report(
                analysis_results['findings'],
                analysis_results['metadata'],
                ['markdown', 'json', 'sarif']
            )
            analysis_results['reports'] = report_paths
            
            logger.info(f"Analysis completed: {len(analysis_results['findings'])} findings across {len(analyzed_files)} files")
            
            return analysis_results
            
        finally:
            # Cleanup temporary directory
            await self._cleanup()
    
    async def analyze_multiple_repositories(
        self,
        repo_urls: List[str],
        scan_mode: str = 'comprehensive'
    ) -> Dict[str, Any]:
        """Analyze multiple repositories and generate comparative report"""
        
        results = {}
        all_findings = []
        
        for repo_url in repo_urls:
            try:
                repo_results = await self.analyze_repository(repo_url, scan_mode=scan_mode)
                results[repo_url] = repo_results
                all_findings.extend(repo_results['findings'])
            except Exception as e:
                logger.error(f"Failed to analyze {repo_url}: {e}")
                results[repo_url] = {'error': str(e)}
        
        # Generate comparative analysis
        comparative_analysis = {
            'summary': {
                'total_repositories': len(repo_urls),
                'successful_analyses': len([r for r in results.values() if 'error' not in r]),
                'total_findings': len(all_findings),
                'most_vulnerable_repo': self._find_most_vulnerable_repo(results),
                'common_vulnerabilities': self._find_common_vulnerabilities(results)
            },
            'repository_results': results,
            'comparative_metrics': self._calculate_comparative_metrics(results)
        }
        
        return comparative_analysis

    def _enrich_cross_file_context(
        self,
        repo_path: str,
        analyzed_files: List[str],
        findings: List[Finding],
    ) -> None:
        """Annotate findings with cross-file traces when Python code is present."""

        if not findings:
            return

        language_set = {
            self._get_file_language(file_path).lower()
            for file_path in analyzed_files
            if isinstance(file_path, str)
        }
        if "python" not in language_set:
            return

        root_path = Path(repo_path).resolve()
        if not root_path.is_dir():
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
            annotate_cross_file_context(root_path, typed_findings, files=files)
        except Exception as exc:
            logger.debug("Cross-file enrichment skipped: %s", exc)
    
    async def _clone_repository(self, repo_url: str, branch: str) -> str:
        """Clone repository to temporary directory"""
        
        if not GIT_AVAILABLE:
            raise RuntimeError("Git is not available. Please install Git and ensure it's in your PATH.")
        
        self.temp_dir = tempfile.mkdtemp(prefix='securecli_')
        repo_path = Path(self.temp_dir) / 'repo'
        
        try:
            # Add authentication if token is available
            if self.github_token:
                parsed_url = urlparse(repo_url)
                auth_url = f"https://{self.github_token}@{parsed_url.netloc}{parsed_url.path}"
            else:
                auth_url = repo_url
            
            # Clone repository
            logger.info(f"Cloning repository to {repo_path}")
            repo = git.Repo.clone_from(auth_url, repo_path, branch=branch, depth=1)
            
            logger.info(f"Successfully cloned repository (branch: {branch})")
            return str(repo_path)
            
        except Exception as e:
            logger.error(f"Failed to clone repository: {e}")
            raise RuntimeError(f"Failed to clone repository {repo_url}: {e}")
    
    async def _discover_files(
        self,
        repo_path: str,
        target_paths: List[str] = None,
        exclude_paths: List[str] = None
    ) -> List[str]:
        """Discover all files in repository"""
        
        repo = Path(repo_path)
        all_files = []
        
        # Default exclude patterns
        default_excludes = [
            '.git', '__pycache__', 'node_modules', '.venv', 'venv',
            'dist', 'build', 'target', 'out', '.tox', 'coverage',
            '.pytest_cache', '.mypy_cache', '.cache', 'vendor',
            'bower_components', '.nuxt', '.next', '.svelte-kit'
        ]
        
        exclude_patterns = default_excludes + (exclude_paths or [])
        
        # Walk through repository
        for file_path in repo.rglob('*'):
            if file_path.is_file():
                relative_path = file_path.relative_to(repo)
                
                # Check exclusions
                if any(exclude in str(relative_path) for exclude in exclude_patterns):
                    continue
                
                # Check if we should include this file
                if target_paths:
                    if not any(target in str(relative_path) for target in target_paths):
                        continue
                
                all_files.append(str(file_path))
        
        return all_files
    
    def _filter_security_files(self, all_files: List[str]) -> List[str]:
        """Filter files that are relevant for security analysis"""
        
        security_files = []
        
        for file_path in all_files:
            path = Path(file_path)
            
            # Check by extension
            if path.suffix.lower() in self.LANGUAGE_EXTENSIONS:
                security_files.append(file_path)
                continue
            
            # Check by filename
            if path.name.lower() in self.LANGUAGE_EXTENSIONS:
                security_files.append(file_path)
                continue
            
            # Check specific security-relevant patterns
            for pattern in self.SECURITY_FILES:
                if pattern.replace('*', '') in path.name.lower():
                    security_files.append(file_path)
                    break
        
        return security_files
    
    def _get_file_language(self, file_path: str) -> str:
        """Determine language for a file"""
        
        path = Path(file_path)
        
        # Check by extension first
        if path.suffix.lower() in self.LANGUAGE_EXTENSIONS:
            return self.LANGUAGE_EXTENSIONS[path.suffix.lower()]
        
        # Check by filename
        if path.name.lower() in self.LANGUAGE_EXTENSIONS:
            return self.LANGUAGE_EXTENSIONS[path.name.lower()]
        
        return 'unknown'
    
    async def _get_latest_commit(self, repo_path: str) -> str:
        """Get latest commit hash"""
        
        try:
            repo = git.Repo(repo_path)
            return repo.head.commit.hexsha[:8]
        except Exception:
            return 'unknown'
    
    async def _generate_file_analysis(
        self,
        analyzed_files: List[str],
        findings: List[Finding]
    ) -> Dict[str, Any]:
        """Generate detailed file-by-file analysis"""
        
        file_analysis = {}
        
        # Group findings by file
        findings_by_file = {}
        for finding in findings:
            file_path = finding.file
            if file_path not in findings_by_file:
                findings_by_file[file_path] = []
            findings_by_file[file_path].append(finding)
        
        # Analyze each file
        for file_path in analyzed_files:
            file_findings = findings_by_file.get(file_path, [])
            language = self._get_file_language(file_path)
            
            # Calculate file-specific metrics
            severity_counts = {'critical': 0, 'high': 0, 'medium': 0, 'low': 0}
            for finding in file_findings:
                severity_counts[finding.severity.lower()] += 1
            
            # Calculate risk score for file
            risk_score = self._calculate_file_risk_score(file_findings)
            
            file_analysis[file_path] = {
                'language': language,
                'findings_count': len(file_findings),
                'severity_distribution': severity_counts,
                'risk_score': risk_score,
                'findings': [
                    {
                        'id': f.id,
                        'title': f.title,
                        'severity': f.severity,
                        'line_number': self._parse_line_number(f.lines),
                        'confidence': f.confidence_score
                    }
                    for f in file_findings
                ],
                'recommendations': self._generate_file_recommendations(file_findings, language)
            }
        
        return file_analysis
    
    def _calculate_file_risk_score(self, findings: List[Finding]) -> float:
        """Calculate risk score for a single file"""
        
        if not findings:
            return 0.0
        
        severity_weights = {'critical': 10, 'high': 7, 'medium': 4, 'low': 1}
        total_score = 0
        max_possible = 0
        
        for finding in findings:
            weight = severity_weights.get(finding.severity.lower(), 1)
            confidence = finding.confidence_score / 100.0
            total_score += weight * confidence
            max_possible += weight
        
        if max_possible == 0:
            return 0.0
        
        return round((total_score / max_possible) * 100, 1)
    
    def _generate_file_recommendations(self, findings: List[Finding], language: str) -> List[str]:
        """Generate file-specific recommendations"""
        
        if not findings:
            return []
        
        recommendations = []
        
        # Language-specific recommendations
        if language == 'python':
            if any('bandit' in str(f.tool_evidence) for f in findings):
                recommendations.append("Consider using type hints and static analysis tools")
                recommendations.append("Review input validation and sanitization")
        
        elif language == 'javascript' or language == 'typescript':
            recommendations.append("Enable strict mode and use ESLint security rules")
            recommendations.append("Implement Content Security Policy (CSP)")
        
        elif language == 'solidity':
            recommendations.append("Use latest Solidity compiler version")
            recommendations.append("Implement proper access controls and reentrancy protection")
            recommendations.append("Consider formal verification for critical functions")
        
        # Severity-based recommendations
        critical_findings = [f for f in findings if f.severity.lower() == 'critical']
        if critical_findings:
            recommendations.append("🔴 URGENT: Address critical vulnerabilities immediately")
        
        high_findings = [f for f in findings if f.severity.lower() == 'high']
        if high_findings:
            recommendations.append("⚠️ Address high-severity issues within 7 days")
        
        return recommendations[:5]  # Limit to top 5
    
    def _find_most_vulnerable_repo(self, results: Dict[str, Any]) -> Optional[str]:
        """Find repository with highest risk score"""
        
        max_score = 0
        most_vulnerable = None
        
        for repo_url, result in results.items():
            if 'error' in result:
                continue
            
            findings = result.get('findings', [])
            if not findings:
                continue
            
            # Calculate total risk score
            critical = len([f for f in findings if f.severity.lower() == 'critical'])
            high = len([f for f in findings if f.severity.lower() == 'high'])
            
            score = critical * 10 + high * 5
            
            if score > max_score:
                max_score = score
                most_vulnerable = repo_url
        
        return most_vulnerable
    
    def _find_common_vulnerabilities(self, results: Dict[str, Any]) -> List[str]:
        """Find vulnerabilities common across repositories"""
        
        from collections import Counter
        
        all_categories = []
        for result in results.values():
            if 'error' in result:
                continue
            
            findings = result.get('findings', [])
            for finding in findings:
                all_categories.append(finding.category)
        
        # Find most common categories
        common = Counter(all_categories).most_common(5)
        return [f"{category} ({count} instances)" for category, count in common]
    
    def _calculate_comparative_metrics(self, results: Dict[str, Any]) -> Dict[str, Any]:
        """Calculate comparative metrics across repositories"""
        
        metrics = {
            'total_findings': 0,
            'avg_findings_per_repo': 0,
            'languages_coverage': set(),
            'most_common_issues': [],
            'security_score_distribution': []
        }
        
        valid_results = [r for r in results.values() if 'error' not in r]
        
        if not valid_results:
            return metrics
        
        # Calculate metrics
        total_findings = sum(len(r.get('findings', [])) for r in valid_results)
        metrics['total_findings'] = total_findings
        metrics['avg_findings_per_repo'] = round(total_findings / len(valid_results), 1)
        
        # Collect languages
        for result in valid_results:
            languages = result.get('repository', {}).get('languages_detected', [])
            metrics['languages_coverage'].update(languages)
        
        metrics['languages_coverage'] = list(metrics['languages_coverage'])
        
        return metrics
    
    def _parse_line_number(self, lines_str: str) -> int:
        """Parse line number from lines string (e.g., '10-15' -> 10, '42' -> 42)"""
        if not lines_str:
            return 0
        try:
            # Extract first number from lines string
            if '-' in lines_str:
                return int(lines_str.split('-')[0])
            else:
                return int(lines_str)
        except (ValueError, IndexError):
            return 0
    
    async def _cleanup(self):
        """Clean up temporary directory"""
        
        if self.temp_dir and Path(self.temp_dir).exists():
            try:
                shutil.rmtree(self.temp_dir)
                logger.info("Cleaned up temporary directory")
            except Exception as e:
                logger.warning(f"Failed to cleanup temporary directory: {e}")


# GitHub Repository URL parsing utilities
def parse_github_url(url: str) -> Dict[str, str]:
    """Parse GitHub repository URL into components"""
    
    parsed = urlparse(url)
    
    if 'github.com' not in parsed.netloc:
        raise ValueError("Not a valid GitHub URL")
    
    path_parts = parsed.path.strip('/').split('/')
    
    if len(path_parts) < 2:
        raise ValueError("Invalid GitHub repository URL format")
    
    return {
        'owner': path_parts[0],
        'repo': path_parts[1].replace('.git', ''),
        'branch': 'main',  # Default
        'path': '/'.join(path_parts[2:]) if len(path_parts) > 2 else ''
    }


def validate_github_url(url: str) -> bool:
    """Validate if URL is a valid GitHub repository URL"""
    
    try:
        parse_github_url(url)
        return True
    except ValueError:
        return False


# CLI integration for GitHub analysis
async def analyze_github_repo_cli(
    repo_url: str,
    config: Dict[str, Any],
    **kwargs
) -> Dict[str, Any]:
    """CLI wrapper for GitHub repository analysis"""
    
    analyzer = GitHubRepositoryAnalyzer(config)
    
    return await analyzer.analyze_repository(
        repo_url=repo_url,
        branch=kwargs.get('branch', 'main'),
        scan_mode=kwargs.get('scan_mode', 'comprehensive'),
        target_paths=kwargs.get('target_paths'),
        exclude_paths=kwargs.get('exclude_paths')
    )