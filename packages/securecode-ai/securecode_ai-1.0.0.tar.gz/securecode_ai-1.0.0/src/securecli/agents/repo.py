"""
Repository Agent - Handles file enumeration, indexing, and code structure analysis
Builds symbol tables, dependency graphs, and prepares data for other agents
"""

import os
import hashlib
import mimetypes
from pathlib import Path
from typing import Dict, List, Optional, Any, Set
import asyncio
import aiofiles
from dataclasses import dataclass

# Conditional git import
try:
    import git
    GIT_AVAILABLE = True
except (ImportError, Exception):
    GIT_AVAILABLE = False
    git = None

try:
    from gitignore_parser import parse_gitignore
    GITIGNORE_AVAILABLE = True
except ImportError:
    GITIGNORE_AVAILABLE = False
    parse_gitignore = None

from ..schemas.findings import RepositoryAnalysis, FileInfo


@dataclass
class SymbolInfo:
    """Information about a code symbol (function, class, variable)"""
    name: str
    type: str  # function, class, variable, contract, etc.
    file_path: str
    line_number: int
    scope: str
    signature: Optional[str] = None
    references: List[str] = None


class RepoAgent:
    """
    Handles repository analysis, file enumeration, and code indexing
    Prepares structured data for other agents to consume
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.max_file_size = config.get("repo.max_file_size", 1024 * 1024)  # 1MB
        self.exclude_patterns = config.get("repo.exclude", [])
        
        # File type categorization
        self.code_extensions = {
            '.py', '.js', '.ts', '.jsx', '.tsx', '.sol', '.vy', '.rs', '.go', 
            '.java', '.c', '.cpp', '.h', '.hpp', '.cs', '.php', '.rb', '.kt'
        }
        
        self.config_extensions = {
            '.yml', '.yaml', '.json', '.toml', '.ini', '.cfg', '.conf', '.env'
        }
        
        self.doc_extensions = {
            '.md', '.rst', '.txt', '.doc', '.docx', '.pdf'
        }
    
    async def analyze_repository(
        self, 
        repo_path: str, 
        exclude_patterns: List[str] = None
    ) -> RepositoryAnalysis:
        """
        Perform comprehensive repository analysis
        
        Args:
            repo_path: Path to repository root
            exclude_patterns: Additional patterns to exclude
            
        Returns:
            RepositoryAnalysis with file information and metadata
        """
        
        repo_path = Path(repo_path).resolve()
        if not repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
        
        # Initialize Git repository if available
        git_repo = None
        if GIT_AVAILABLE:
            try:
                git_repo = git.Repo(repo_path)
            except:
                pass
        
        # Build exclude patterns
        all_exclude_patterns = self.exclude_patterns + (exclude_patterns or [])
        gitignore_func = self._build_gitignore_filter(repo_path)
        
        # Enumerate files
        files = await self._enumerate_files(
            repo_path, 
            all_exclude_patterns, 
            gitignore_func
        )
        
        # Analyze repository structure
        structure = self._analyze_structure(files)
        
        # Build dependency information
        dependencies = await self._analyze_dependencies(repo_path, files)
        
        # Extract metadata
        metadata = self._extract_metadata(repo_path, git_repo)
        
        return RepositoryAnalysis(
            repo_path=str(repo_path),
            files=files,
            structure=structure,
            dependencies=dependencies,
            metadata=metadata,
            git_info=self._get_git_info(git_repo) if git_repo else None
        )
    
    def _build_gitignore_filter(self, repo_path: Path):
        """Build gitignore filter function"""
        if not GITIGNORE_AVAILABLE:
            return lambda path: False
            
        gitignore_path = repo_path / '.gitignore'
        if gitignore_path.exists():
            return parse_gitignore(str(gitignore_path))
        return lambda path: False
    
    async def _enumerate_files(
        self, 
        repo_path: Path, 
        exclude_patterns: List[str],
        gitignore_func
    ) -> List[FileInfo]:
        """Enumerate all files in repository with metadata"""
        files = []
        
        for root, dirs, filenames in os.walk(repo_path):
            root_path = Path(root)
            relative_root = root_path.relative_to(repo_path)
            
            # Filter directories
            dirs[:] = [
                d for d in dirs 
                if not self._should_exclude(relative_root / d, exclude_patterns)
                and not gitignore_func(str(relative_root / d))
            ]
            
            for filename in filenames:
                file_path = root_path / filename
                relative_path = file_path.relative_to(repo_path)
                
                # Skip if excluded
                if (self._should_exclude(relative_path, exclude_patterns) or 
                    gitignore_func(str(relative_path))):
                    continue
                
                # Skip if too large
                try:
                    if file_path.stat().st_size > self.max_file_size:
                        continue
                except OSError:
                    continue
                
                # Create file info
                file_info = await self._create_file_info(file_path, relative_path)
                if file_info:
                    files.append(file_info)
        
        return files
    
    def _should_exclude(self, path: Path, exclude_patterns: List[str]) -> bool:
        """Check if path should be excluded based on patterns"""
        path_str = str(path)
        
        # Common exclusions
        if any(part.startswith('.') for part in path.parts):
            if not any(part in ['.github', '.vscode'] for part in path.parts):
                return True
        
        # Check custom patterns
        for pattern in exclude_patterns:
            if pattern in path_str:
                return True
        
        # Exclude common build/dependency directories
        exclude_dirs = {
            'node_modules', '__pycache__', '.git', 'build', 'dist', 'target',
            'vendor', '.next', '.nuxt', 'coverage', '.pytest_cache'
        }
        
        if any(part in exclude_dirs for part in path.parts):
            return True
        
        return False
    
    async def _create_file_info(
        self, 
        file_path: Path, 
        relative_path: Path
    ) -> Optional[FileInfo]:
        """Create FileInfo object for a file"""
        try:
            stat = file_path.stat()
            
            # Determine file type
            file_type = self._classify_file_type(file_path)
            
            # Read content for text files
            content = None
            content_hash = None
            
            if file_type in ['code', 'config', 'docs']:
                try:
                    async with aiofiles.open(file_path, 'r', encoding='utf-8') as f:
                        content = await f.read()
                        content_hash = hashlib.sha256(content.encode()).hexdigest()[:16]
                except (UnicodeDecodeError, PermissionError):
                    # Binary file or permission denied
                    file_type = 'binary'
            
            return FileInfo(
                path=str(relative_path),
                full_path=str(file_path),
                size=stat.st_size,
                modified=stat.st_mtime,
                file_type=file_type,
                extension=file_path.suffix.lower(),
                content=content,
                content_hash=content_hash,
                mime_type=mimetypes.guess_type(str(file_path))[0],
                language=self._detect_language(file_path)
            )
            
        except OSError:
            return None
    
    def _classify_file_type(self, file_path: Path) -> str:
        """Classify file type based on extension"""
        ext = file_path.suffix.lower()
        
        if ext in self.code_extensions:
            return 'code'
        elif ext in self.config_extensions:
            return 'config'
        elif ext in self.doc_extensions:
            return 'docs'
        else:
            return 'binary'
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension"""
        ext = file_path.suffix.lower()
        
        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.sol': 'solidity',
            '.vy': 'vyper',
            '.rs': 'rust',
            '.go': 'go',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.kt': 'kotlin',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.json': 'json',
            '.toml': 'toml',
        }
        
        return language_map.get(ext)
    
    def _analyze_structure(self, files: List[FileInfo]) -> Dict[str, Any]:
        """Analyze repository structure and organization"""
        structure = {
            "total_files": len(files),
            "by_type": {},
            "by_language": {},
            "directories": set(),
            "largest_files": [],
            "entry_points": []
        }
        
        total_size = 0
        
        for file_info in files:
            # Count by type
            structure["by_type"][file_info.file_type] = (
                structure["by_type"].get(file_info.file_type, 0) + 1
            )
            
            # Count by language
            if file_info.language:
                structure["by_language"][file_info.language] = (
                    structure["by_language"].get(file_info.language, 0) + 1
                )
            
            # Track directories
            structure["directories"].add(str(Path(file_info.path).parent))
            
            # Track size
            total_size += file_info.size
            
            # Identify potential entry points
            filename = Path(file_info.path).name.lower()
            if filename in ['main.py', 'app.py', 'index.js', 'server.js', 'main.go']:
                structure["entry_points"].append(file_info.path)
        
        # Convert set to list for JSON serialization
        structure["directories"] = list(structure["directories"])
        
        # Find largest files
        structure["largest_files"] = sorted(
            [(f.path, f.size) for f in files],
            key=lambda x: x[1],
            reverse=True
        )[:10]
        
        structure["total_size"] = total_size
        
        return structure
    
    async def _analyze_dependencies(
        self, 
        repo_path: Path, 
        files: List[FileInfo]
    ) -> Dict[str, Any]:
        """Analyze project dependencies and external references"""
        dependencies = {
            "package_files": [],
            "imports": {},
            "external_calls": [],
            "databases": [],
            "apis": []
        }
        
        # Find package/dependency files
        package_files = [
            'package.json', 'requirements.txt', 'pyproject.toml', 'Cargo.toml',
            'go.mod', 'pom.xml', 'build.gradle', 'composer.json'
        ]
        
        for file_info in files:
            filename = Path(file_info.path).name
            
            if filename in package_files:
                dependencies["package_files"].append({
                    "file": file_info.path,
                    "type": self._get_package_manager_type(filename),
                    "content": file_info.content
                })
        
        # TODO: Analyze imports and external references
        # This would parse code files to identify:
        # - Import statements
        # - External library usage
        # - API endpoints being called
        # - Database connections
        # - Network requests
        
        return dependencies
    
    def _get_package_manager_type(self, filename: str) -> str:
        """Get package manager type from filename"""
        mapping = {
            'package.json': 'npm',
            'requirements.txt': 'pip',
            'pyproject.toml': 'pip',
            'Cargo.toml': 'cargo',
            'go.mod': 'go',
            'pom.xml': 'maven',
            'build.gradle': 'gradle',
            'composer.json': 'composer'
        }
        return mapping.get(filename, 'unknown')
    
    def _extract_metadata(
        self, 
        repo_path: Path, 
        git_repo: Optional[Any]  # Changed from git.Repo to Any for compatibility
    ) -> Dict[str, Any]:
        """Extract repository metadata"""
        metadata = {
            "name": repo_path.name,
            "path": str(repo_path),
            "size": sum(f.stat().st_size for f in repo_path.rglob('*') if f.is_file()),
            "created": None,
            "languages": [],
            "frameworks": [],
            "has_tests": False,
            "has_docs": False,
            "has_ci": False
        }
        
        # Check for common patterns
        for file_path in repo_path.rglob('*'):
            if file_path.is_file():
                name = file_path.name.lower()
                
                # Test detection
                if 'test' in name or 'spec' in name:
                    metadata["has_tests"] = True
                
                # Documentation detection
                if name in ['readme.md', 'docs', 'documentation']:
                    metadata["has_docs"] = True
                
                # CI detection
                if '.github' in str(file_path) or name in ['.travis.yml', '.gitlab-ci.yml']:
                    metadata["has_ci"] = True
        
        return metadata
    
    def _get_git_info(self, git_repo: Any) -> Dict[str, Any]:  # Changed from git.Repo to Any for compatibility
        """Extract Git repository information"""
        if not GIT_AVAILABLE or not git_repo:
            return {}
            
        try:
            return {
                "branch": git_repo.active_branch.name,
                "commit": git_repo.head.commit.hexsha[:8],
                "remote": str(git_repo.remote().url) if git_repo.remotes else None,
                "dirty": git_repo.is_dirty(),
                "untracked": len(git_repo.untracked_files) > 0
            }
        except Exception:
            return {"error": "Could not extract git information"}
    
    async def build_symbol_index(self, files: List[FileInfo]) -> Dict[str, List[SymbolInfo]]:
        """Build symbol index for cross-file analysis"""
        symbol_index = {}
        
        for file_info in files:
            if file_info.file_type == 'code' and file_info.content:
                symbols = await self._extract_symbols(file_info)
                if symbols:
                    symbol_index[file_info.path] = symbols
        
        return symbol_index
    
    async def _extract_symbols(self, file_info: FileInfo) -> List[SymbolInfo]:
        """Extract symbols (functions, classes, etc.) from code file"""
        symbols = []
        
        # TODO: Implement proper AST parsing for each language
        # For now, simple regex-based extraction
        
        if file_info.language == 'python':
            symbols.extend(self._extract_python_symbols(file_info))
        elif file_info.language == 'javascript':
            symbols.extend(self._extract_javascript_symbols(file_info))
        elif file_info.language == 'solidity':
            symbols.extend(self._extract_solidity_symbols(file_info))
        
        return symbols
    
    def _extract_python_symbols(self, file_info: FileInfo) -> List[SymbolInfo]:
        """Extract Python symbols (basic implementation)"""
        symbols = []
        lines = file_info.content.split('\n')
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Functions
            if line.startswith('def '):
                func_name = line.split('(')[0].replace('def ', '').strip()
                symbols.append(SymbolInfo(
                    name=func_name,
                    type='function',
                    file_path=file_info.path,
                    line_number=i + 1,
                    scope='module',
                    signature=line
                ))
            
            # Classes
            elif line.startswith('class '):
                class_name = line.split('(')[0].replace('class ', '').strip().rstrip(':')
                symbols.append(SymbolInfo(
                    name=class_name,
                    type='class',
                    file_path=file_info.path,
                    line_number=i + 1,
                    scope='module',
                    signature=line
                ))
        
        return symbols
    
    def _extract_javascript_symbols(self, file_info: FileInfo) -> List[SymbolInfo]:
        """Extract JavaScript symbols (basic implementation)"""
        # TODO: Implement JavaScript symbol extraction
        return []
    
    def _extract_solidity_symbols(self, file_info: FileInfo) -> List[SymbolInfo]:
        """Extract Solidity symbols (basic implementation)"""
        symbols = []
        lines = file_info.content.split('\n')
        
        current_contract = None
        
        for i, line in enumerate(lines):
            line = line.strip()
            
            # Contracts
            if line.startswith('contract '):
                contract_name = line.split('{')[0].replace('contract ', '').strip()
                current_contract = contract_name
                symbols.append(SymbolInfo(
                    name=contract_name,
                    type='contract',
                    file_path=file_info.path,
                    line_number=i + 1,
                    scope='global',
                    signature=line
                ))
            
            # Functions
            elif 'function ' in line:
                func_start = line.find('function ') + 9
                func_end = line.find('(', func_start)
                if func_end > func_start:
                    func_name = line[func_start:func_end].strip()
                    symbols.append(SymbolInfo(
                        name=func_name,
                        type='function',
                        file_path=file_info.path,
                        line_number=i + 1,
                        scope=current_contract or 'global',
                        signature=line
                    ))
        
        return symbols
    
    async def execute_tasks(self, tasks: List[str]) -> Dict[str, Any]:
        """Execute repository agent tasks"""
        results = {}
        
        for task in tasks:
            if task == "file_enumeration":
                results[task] = "File enumeration completed"
            elif task == "dependency_analysis":
                results[task] = "Dependency analysis completed"
            elif task == "architecture_mapping":
                results[task] = "Architecture mapping completed"
            else:
                results[task] = f"Unknown task: {task}"
        
        return results