"""
Scanner modules for SecureCLI
Implements automated security scanning modules
"""

from typing import Dict, List, Any
from pathlib import Path

from .base import BaseModule, ModuleConfig, ModuleType, DomainProfile
from ..schemas.findings import Finding
from ..tools.semgrep import SemgrepScanner as SemgrepTool
from ..tools.gitleaks import GitleaksScanner as GitleaksTool
from ..tools.slither import SlitherScanner as SlitherTool
from ..tools.bandit import BanditScanner as BanditTool
from ..tools.gosec import GosecScanner as GosecTool
from ..tools.npm_audit import NpmAuditScanner as NpmAuditTool

# Import all language-specific analyzers
try:
    from ..tools.java_analyzer import JavaAnalyzer
except ImportError:
    JavaAnalyzer = None

try:
    from ..tools.csharp_analyzer import CSharpAnalyzer
except ImportError:
    CSharpAnalyzer = None

try:
    from ..tools.cpp_analyzer import CppAnalyzer
except ImportError:
    CppAnalyzer = None

try:
    from ..tools.c_analyzer import CAnalyzer
except ImportError:
    CAnalyzer = None

try:
    from ..tools.rust_analyzer import RustAnalyzer
except ImportError:
    RustAnalyzer = None

try:
    from ..tools.php_analyzer import PhpAnalyzer
except ImportError:
    PhpAnalyzer = None

try:
    from ..tools.ruby_analyzer import RubyAnalyzer
except ImportError:
    RubyAnalyzer = None

try:
    from ..tools.swift_analyzer import SwiftAnalyzer
except ImportError:
    SwiftAnalyzer = None

try:
    from ..tools.kotlin_analyzer import KotlinAnalyzer
except ImportError:
    KotlinAnalyzer = None

try:
    from ..tools.go_analyzer import GoAnalyzer
except ImportError:
    GoAnalyzer = None

try:
    from ..tools.solidity_analyzer import SolidityTool as SolidityAnalyzer
except ImportError:
    SolidityAnalyzer = None

try:
    from ..tools.dart_flutter_analyzer import DartFlutterAnalyzer
except ImportError:
    DartFlutterAnalyzer = None

try:
    from ..tools.objective_c_analyzer import ObjectiveCAnalyzer
except ImportError:
    ObjectiveCAnalyzer = None

try:
    from ..tools.haskell_analyzer import HaskellAnalyzer
except ImportError:
    HaskellAnalyzer = None

try:
    from ..tools.scala_analyzer import ScalaAnalyzer
except ImportError:
    ScalaAnalyzer = None

try:
    from ..tools.fsharp_analyzer import FSharpAnalyzer
except ImportError:
    FSharpAnalyzer = None

try:
    from ..tools.erlang_elixir_analyzer import ErlangElixirAnalyzer
except ImportError:
    ErlangElixirAnalyzer = None

try:
    from ..tools.perl_analyzer import PerlAnalyzer
except ImportError:
    PerlAnalyzer = None

try:
    from ..tools.lua_analyzer import LuaAnalyzer
except ImportError:
    LuaAnalyzer = None

try:
    from ..tools.vyper_analyzer import VyperTool as VyperAnalyzer
except ImportError:
    VyperAnalyzer = None

try:
    from ..tools.cairo_analyzer import CairoAnalyzer
except ImportError:
    CairoAnalyzer = None

try:
    from ..tools.move_analyzer import MoveAnalyzer
except ImportError:
    MoveAnalyzer = None

try:
    from ..tools.clarity_analyzer import ClarityAnalyzer
except ImportError:
    ClarityAnalyzer = None


class SemgrepScannerModule(BaseModule):
    """Semgrep-based security scanner module"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.semgrep = SemgrepTool(config.config)
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute Semgrep scanning"""
        
        # Get target files from context
        target_files = context.get('target_files', [])
        if not target_files:
            return []
        
        # Determine appropriate rulesets based on domain profiles
        rulesets = self._get_rulesets_for_context(context)
        
        # Run Semgrep with domain-specific rules
        findings = []
        for ruleset in rulesets:
            try:
                ruleset_findings = await self.semgrep.scan(workspace_path, {'ruleset': ruleset})
                findings.extend(ruleset_findings)
            except Exception as e:
                print(f"Error running Semgrep with ruleset {ruleset}: {e}")
        
        return findings
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if Semgrep is applicable"""
        
        # Semgrep is a universal tool - should always run
        target_files = context.get('target_files', [])
        if not target_files:
            return False
        
        # Check if any files are supported by Semgrep or if any supported languages detected
        supported_extensions = {
            '.py', '.js', '.jsx', '.ts', '.tsx', '.java', '.go', '.rb', '.php',
            '.cs', '.c', '.cpp', '.h', '.hpp', '.scala', '.kt', '.swift', '.rs',
            '.sol', '.vy'  # Web3 support
        }
        
        # Check file extensions
        for file_path in target_files:
            if any(file_path.endswith(ext) for ext in supported_extensions):
                return True
        
        # Check detected languages
        technologies = context.get('technologies', {})
        if isinstance(technologies, dict):
            detected_languages = technologies.get('languages', [])
        else:
            detected_languages = technologies if isinstance(technologies, list) else []
        
        semgrep_supported_languages = {
            'python', 'javascript', 'typescript', 'java', 'go', 'ruby', 'php',
            'csharp', 'c', 'cpp', 'scala', 'kotlin', 'swift', 'rust',
            'solidity', 'vyper'
        }
        
        return any(lang in semgrep_supported_languages for lang in detected_languages)
    
    def _get_rulesets_for_context(self, context: Dict[str, Any]) -> List[str]:
        """Get appropriate Semgrep rulesets based on context"""
        
        rulesets = ["auto"]  # Default ruleset
        
        technologies = context.get('technologies', {})
        languages = technologies.get('languages', [])
        
        # Language-specific rulesets
        if 'python' in languages:
            rulesets.extend(['python', 'django', 'flask'])
        if 'javascript' in languages or 'typescript' in languages:
            rulesets.extend(['javascript', 'typescript', 'react'])
        if 'java' in languages:
            rulesets.extend(['java', 'spring'])
        if 'go' in languages:
            rulesets.append('go')
        if 'php' in languages:
            rulesets.append('php')
        if 'ruby' in languages:
            rulesets.append('ruby')
        
        # Domain-specific rulesets
        domain_profiles = context.get('domain_profiles', [])
        
        for profile in domain_profiles:
            if profile == DomainProfile.WEB2_FRONTEND:
                rulesets.extend(['xss', 'security'])
            elif profile == DomainProfile.WEB2_BACKEND:
                rulesets.extend(['security', 'owasp-top-ten'])
            elif profile == DomainProfile.WEB2_API:
                rulesets.extend(['security', 'jwt'])
            elif profile == DomainProfile.INFRASTRUCTURE:
                rulesets.extend(['docker', 'kubernetes'])
        
        # Remove duplicates and return
        return list(set(rulesets))


class GitleaksSecretScannerModule(BaseModule):
    """Gitleaks-based secret scanner module"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.gitleaks = GitleaksTool(config.config)
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute Gitleaks secret scanning"""
        
        try:
            findings = await self.gitleaks.scan(workspace_path, {})
            return findings
        except Exception as e:
            print(f"Error running Gitleaks: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Gitleaks is applicable to all repositories"""
        return True


class SlitherWeb3ScannerModule(BaseModule):
    """Slither-based Solidity scanner module"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.slither = SlitherTool(config.config)
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute Slither scanning on Solidity contracts"""
        
        # Find Solidity files
        solidity_files = [
            f for f in context.get('target_files', [])
            if f.endswith('.sol')
        ]
        
        if not solidity_files:
            return []
        
        try:
            findings = await self.slither.scan(workspace_path, context)
            return findings
        except Exception as e:
            print(f"Error running Slither: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if we have Solidity files"""
        
        target_files = context.get('target_files', [])
        return any(f.endswith('.sol') for f in target_files)


class BanditPythonScannerModule(BaseModule):
    """Bandit-based Python security scanner"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.bandit = BanditTool(config.config)
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute Bandit scanning on Python files"""
        
        # Find Python files
        python_files = [
            f for f in context.get('target_files', [])
            if f.endswith('.py')
        ]
        
        if not python_files:
            return []
        
        try:
            findings = await self.bandit.scan(workspace_path, context)
            return findings
        except Exception as e:
            print(f"Error running Bandit: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if we have Python files or Python detected as language"""
        
        # Check file extensions
        target_files = context.get('target_files', [])
        has_python_files = any(f.endswith('.py') for f in target_files)
        
        if has_python_files:
            return True
        
        # Check detected languages
        technologies = context.get('technologies', {})
        if isinstance(technologies, dict):
            detected_languages = technologies.get('languages', [])
        else:
            detected_languages = technologies if isinstance(technologies, list) else []
        
        return 'python' in detected_languages


class GosecGoScannerModule(BaseModule):
    """Gosec-based Go security scanner"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.gosec = GosecTool(config.config)
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute Gosec scanning on Go files"""
        
        # Find Go files
        go_files = [
            f for f in context.get('target_files', [])
            if f.endswith('.go')
        ]
        
        if not go_files:
            return []
        
        try:
            findings = await self.gosec.scan(workspace_path, context)
            return findings
        except Exception as e:
            print(f"Error running Gosec: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if we have Go files"""
        
        target_files = context.get('target_files', [])
        return any(f.endswith('.go') for f in target_files)


class DependencyScannerModule(BaseModule):
    """Dependency vulnerability scanner"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.npm_audit = NpmAuditTool(config.config)
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Scan for dependency vulnerabilities"""
        
        findings = []
        workspace = Path(workspace_path)
        
        # Check for Node.js package files
        package_json = workspace / 'package.json'
        if package_json.exists():
            try:
                npm_findings = await self.npm_audit.scan(str(workspace), context)
                findings.extend(npm_findings)
            except Exception as e:
                print(f"Error scanning package.json: {e}")
        
        # TODO: Add other dependency scanners
        # - Python: safety, pip-audit
        # - Go: govulncheck
        # - Rust: cargo audit
        # - Java: mvn dependency:check
        
        return findings
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if we have dependency files"""
        
        target_files = context.get('target_files', [])
        dependency_files = {
            'package.json', 'requirements.txt', 'Pipfile', 'go.mod',
            'Cargo.toml', 'pom.xml', 'build.gradle', 'composer.json'
        }
        
        return any(
            any(filename in file_path for filename in dependency_files)
            for file_path in target_files
        )


class LanguageSpecificScannerModule(BaseModule):
    """Generic language-specific scanner module"""
    
    def __init__(self, config: ModuleConfig, analyzer_class, file_extensions: List[str]):
        super().__init__(config)
        self.analyzer_class = analyzer_class
        self.file_extensions = file_extensions
        
        # Try to create analyzer, handle cases where it may not be fully implemented
        try:
            self.analyzer = analyzer_class(config.config) if analyzer_class else None
        except (TypeError, NotImplementedError, Exception) as e:
            print(f"Warning: Could not initialize {analyzer_class.__name__}: {e}")
            self.analyzer = None
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute language-specific scanning"""
        
        if not self.analyzer:
            return []  # Skip if analyzer not available
        
        # Find files matching our extensions
        target_files = [
            f for f in context.get('target_files', [])
            if any(f.endswith(ext) for ext in self.file_extensions)
        ]
        
        if not target_files:
            return []
        
        try:
            findings = await self.analyzer.scan(workspace_path, context)
            return findings
        except Exception as e:
            print(f"Error running {self.config.name}: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if we have files matching our extensions or detected languages"""
        
        if not self.analyzer:
            return False
        
        # Check file extensions
        target_files = context.get('target_files', [])
        has_matching_files = any(
            any(f.endswith(ext) for ext in self.file_extensions)
            for f in target_files
        )
        
        if has_matching_files:
            return True
        
        # Check detected languages based on scanner name
        technologies = context.get('technologies', {})
        if isinstance(technologies, dict):
            detected_languages = technologies.get('languages', [])
        else:
            detected_languages = technologies if isinstance(technologies, list) else []
        
        # Map scanner names to language names
        scanner_to_language = {
            'java_scanner': 'java',
            'csharp_scanner': 'csharp',
            'cpp_scanner': 'cpp',
            'c_scanner': 'c',
            'rust_scanner': 'rust',
            'php_scanner': 'php',
            'ruby_scanner': 'ruby',
            'swift_scanner': 'swift',
            'kotlin_scanner': 'kotlin',
            'objective-c_scanner': 'objective-c',
            'dart_scanner': 'dart',
            'haskell_scanner': 'haskell',
            'scala_scanner': 'scala',
            'fsharp_scanner': 'fsharp',
            'erlang_scanner': 'erlang',
            'perl_scanner': 'perl',
            'lua_scanner': 'lua',
            'vyper_scanner': 'vyper',
            'cairo_scanner': 'cairo',
            'move_scanner': 'move',
            'clarity_scanner': 'clarity'
        }
        
        expected_language = scanner_to_language.get(self.config.name)
        return expected_language in detected_languages if expected_language else False


# Scanner module factory
def create_scanner_modules():
    """Create and configure all scanner modules"""
    
    modules = []

    # === CORE UNIVERSAL SCANNERS (always run) ===
    
    # Semgrep scanner - universal static analysis
    semgrep_config = ModuleConfig(
        name="semgrep_scanner",
        module_type=ModuleType.SCANNER,
        domain_profiles=[
            DomainProfile.WEB2_FRONTEND,
            DomainProfile.WEB2_BACKEND,
            DomainProfile.WEB2_API,
            DomainProfile.WEB3_SMART_CONTRACT,
            DomainProfile.INFRASTRUCTURE
        ],
        priority=95,
        config={}
    )
    modules.append(SemgrepScannerModule(semgrep_config))
    
    # Gitleaks secret scanner - universal secret detection
    gitleaks_config = ModuleConfig(
        name="gitleaks_scanner",
        module_type=ModuleType.SCANNER,
        domain_profiles=[
            DomainProfile.WEB2_BACKEND, 
            DomainProfile.WEB2_API,
            DomainProfile.WEB3_SMART_CONTRACT,
            DomainProfile.INFRASTRUCTURE
        ],
        priority=98,
        config={}
    )
    modules.append(GitleaksSecretScannerModule(gitleaks_config))
    
    # === LANGUAGE-SPECIFIC SCANNERS ===
    
    # Python scanners
    bandit_config = ModuleConfig(
        name="bandit_scanner",
        module_type=ModuleType.SCANNER,
        domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API],
        priority=85,
        config={}
    )
    modules.append(BanditPythonScannerModule(bandit_config))
    
    # Additional Python scanner using general python analyzer
    python_config = ModuleConfig(
        name="python_scanner",
        module_type=ModuleType.SCANNER,
        domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API],
        priority=80,
        config={}
    )
    # Note: Uses bandit internally but this could be extended with Safety, pip-audit etc.
    modules.append(BanditPythonScannerModule(python_config))
    
    # JavaScript/TypeScript scanner
    javascript_config = ModuleConfig(
        name="javascript_scanner",
        module_type=ModuleType.SCANNER,
        domain_profiles=[DomainProfile.WEB2_FRONTEND, DomainProfile.WEB2_BACKEND],
        priority=80,
        config={}
    )
    modules.append(LanguageSpecificScannerModule(
        javascript_config, 
        NpmAuditTool,  # Using npm audit as JS scanner
        ['.js', '.jsx', '.ts', '.tsx', '.mjs']
    ))
    
    # Java scanner
    if JavaAnalyzer:
        java_config = ModuleConfig(
            name="java_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API],
            priority=80,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            java_config, JavaAnalyzer, ['.java', '.class', '.jar']
        ))
    
    # C# scanner
    if CSharpAnalyzer:
        csharp_config = ModuleConfig(
            name="csharp_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API],
            priority=80,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            csharp_config, CSharpAnalyzer, ['.cs', '.csx']
        ))
    
    # C++ scanner
    if CppAnalyzer:
        cpp_config = ModuleConfig(
            name="cpp_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.INFRASTRUCTURE],
            priority=85,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            cpp_config, CppAnalyzer, ['.cpp', '.cxx', '.cc', '.c++', '.hpp', '.hxx', '.h++']
        ))
    
    # C scanner
    if CAnalyzer:
        c_config = ModuleConfig(
            name="c_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.INFRASTRUCTURE],
            priority=85,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            c_config, CAnalyzer, ['.c', '.h']
        ))
    
    # Rust scanner
    if RustAnalyzer:
        rust_config = ModuleConfig(
            name="rust_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.INFRASTRUCTURE],
            priority=75,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            rust_config, RustAnalyzer, ['.rs']
        ))
    
    # Go scanner
    gosec_config = ModuleConfig(
        name="go_scanner",
        module_type=ModuleType.SCANNER,
        domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API, DomainProfile.INFRASTRUCTURE],
        priority=80,
        config={}
    )
    modules.append(GosecGoScannerModule(gosec_config))
    
    # Go comprehensive analyzer
    if GoAnalyzer:
        go_analyzer_config = ModuleConfig(
            name="go_analyzer_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API, DomainProfile.INFRASTRUCTURE],
            priority=85,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            go_analyzer_config, GoAnalyzer, ['.go']
        ))
    
    # PHP scanner
    if PhpAnalyzer:
        php_config = ModuleConfig(
            name="php_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API],
            priority=85,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            php_config, PhpAnalyzer, ['.php', '.phtml', '.php3', '.php4', '.php5']
        ))
    
    # Ruby scanner
    if RubyAnalyzer:
        ruby_config = ModuleConfig(
            name="ruby_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API],
            priority=80,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            ruby_config, RubyAnalyzer, ['.rb', '.rbw']
        ))
    
    # === MOBILE SCANNERS ===
    
    # Swift scanner
    if SwiftAnalyzer:
        swift_config = ModuleConfig(
            name="swift_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.MOBILE],
            priority=75,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            swift_config, SwiftAnalyzer, ['.swift']
        ))
    
    # Kotlin scanner
    if KotlinAnalyzer:
        kotlin_config = ModuleConfig(
            name="kotlin_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.MOBILE, DomainProfile.WEB2_BACKEND],
            priority=75,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            kotlin_config, KotlinAnalyzer, ['.kt', '.kts']
        ))
    
    # Objective-C scanner
    if ObjectiveCAnalyzer:
        objc_config = ModuleConfig(
            name="objective-c_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.MOBILE],
            priority=70,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            objc_config, ObjectiveCAnalyzer, ['.m', '.mm']
        ))
    
    # Dart scanner
    if DartFlutterAnalyzer:
        dart_config = ModuleConfig(
            name="dart_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.MOBILE],
            priority=70,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            dart_config, DartFlutterAnalyzer, ['.dart']
        ))
    
    # === FUNCTIONAL LANGUAGE SCANNERS ===
    
    # Haskell scanner
    if HaskellAnalyzer:
        haskell_config = ModuleConfig(
            name="haskell_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND],
            priority=65,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            haskell_config, HaskellAnalyzer, ['.hs', '.lhs']
        ))
    
    # Scala scanner
    if ScalaAnalyzer:
        scala_config = ModuleConfig(
            name="scala_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND],
            priority=70,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            scala_config, ScalaAnalyzer, ['.scala']
        ))
    
    # F# scanner
    if FSharpAnalyzer:
        fsharp_config = ModuleConfig(
            name="fsharp_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND],
            priority=65,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            fsharp_config, FSharpAnalyzer, ['.fs', '.fsx']
        ))
    
    # Erlang/Elixir scanner
    if ErlangElixirAnalyzer:
        erlang_config = ModuleConfig(
            name="erlang_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND],
            priority=65,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            erlang_config, ErlangElixirAnalyzer, ['.erl', '.hrl', '.ex', '.exs']
        ))
    
    # === SCRIPTING LANGUAGE SCANNERS ===
    
    # Perl scanner
    if PerlAnalyzer:
        perl_config = ModuleConfig(
            name="perl_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND],
            priority=60,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            perl_config, PerlAnalyzer, ['.pl', '.pm']
        ))
    
    # Lua scanner
    if LuaAnalyzer:
        lua_config = ModuleConfig(
            name="lua_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB2_BACKEND],
            priority=60,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            lua_config, LuaAnalyzer, ['.lua']
        ))
    
    # === WEB3/SMART CONTRACT SCANNERS ===
    
    # Solidity scanner (Slither)
    slither_config = ModuleConfig(
        name="slither_scanner",
        module_type=ModuleType.SCANNER,
        domain_profiles=[
            DomainProfile.WEB3_SMART_CONTRACT,
            DomainProfile.WEB3_DEFI,
            DomainProfile.WEB3_NFT,
            DomainProfile.WEB3_DAO
        ],
        priority=90,
        config={}
    )
    modules.append(SlitherWeb3ScannerModule(slither_config))
    
    # Solidity comprehensive analyzer
    if SolidityAnalyzer:
        solidity_config = ModuleConfig(
            name="solidity_analyzer_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB3_SMART_CONTRACT, DomainProfile.WEB3_DEFI],
            priority=88,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            solidity_config, SolidityAnalyzer, ['.sol']
        ))
    
    # Vyper scanner
    if VyperAnalyzer:
        vyper_config = ModuleConfig(
            name="vyper_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB3_SMART_CONTRACT, DomainProfile.WEB3_DEFI],
            priority=85,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            vyper_config, VyperAnalyzer, ['.vy']
        ))
    
    # Cairo scanner
    if CairoAnalyzer:
        cairo_config = ModuleConfig(
            name="cairo_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB3_SMART_CONTRACT],
            priority=80,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            cairo_config, CairoAnalyzer, ['.cairo']
        ))
    
    # Move scanner
    if MoveAnalyzer:
        move_config = ModuleConfig(
            name="move_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB3_SMART_CONTRACT],
            priority=80,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            move_config, MoveAnalyzer, ['.move']
        ))
    
    # Clarity scanner
    if ClarityAnalyzer:
        clarity_config = ModuleConfig(
            name="clarity_scanner",
            module_type=ModuleType.SCANNER,
            domain_profiles=[DomainProfile.WEB3_SMART_CONTRACT],
            priority=80,
            config={}
        )
        modules.append(LanguageSpecificScannerModule(
            clarity_config, ClarityAnalyzer, ['.clar']
        ))
    
    # === DEPENDENCY SCANNERS ===
    
    # Dependency scanner (npm, pip, etc.)
    dependency_config = ModuleConfig(
        name="dependency_scanner",
        module_type=ModuleType.SCANNER,
        domain_profiles=[
            DomainProfile.WEB2_FRONTEND, 
            DomainProfile.WEB2_BACKEND,
            DomainProfile.WEB3_SMART_CONTRACT
        ],
        priority=90,
        config={}
    )
    modules.append(DependencyScannerModule(dependency_config))
    
    return modules