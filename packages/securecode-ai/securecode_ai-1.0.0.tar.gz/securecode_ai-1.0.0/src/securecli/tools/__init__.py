"""
Security Tools Package
Provides integration with various security scanning tools
"""

from .base import SecurityScannerBase as SecurityTool

# Import tools conditionally to handle missing dependencies gracefully
try:
    from .semgrep import SemgrepScanner as SemgrepTool
except ImportError:
    SemgrepTool = None

try:
    from .gitleaks import GitleaksScanner as GitleaksTool
except ImportError:
    GitleaksTool = None

try:
    from .slither import SlitherScanner as SlitherTool
except ImportError:
    SlitherTool = None

try:
    from .bandit import BanditScanner as BanditTool
except ImportError:
    BanditTool = None

try:
    from .gosec import GosecScanner as GosecTool
except ImportError:
    GosecTool = None

try:
    from .npm_audit import NpmAuditScanner as NpmAuditTool
except ImportError:
    NpmAuditTool = None

try:
    from .cpp_analyzer import CppAnalyzer as CppTool
except ImportError:
    CppTool = None

try:
    from .rust_analyzer import RustAnalyzer as RustTool
except ImportError:
    RustTool = None

try:
    from .java_analyzer import JavaAnalyzer as JavaTool
except ImportError:
    JavaTool = None

try:
    from .ruby_analyzer import RubyAnalyzer as RubyTool
except ImportError:
    RubyTool = None

try:
    from .go_analyzer import GoAnalyzer as GoTool
except ImportError:
    GoTool = None

try:
    from .csharp_analyzer import CSharpAnalyzer as CSharpTool
except ImportError:
    CSharpTool = None

try:
    from .solidity_analyzer import SolidityTool
except ImportError:
    SolidityTool = None

try:
    from .vyper_analyzer import VyperTool
except ImportError:
    VyperTool = None

# New language analyzers
try:
    from .php_analyzer import PhpAnalyzer as PhpTool
except ImportError:
    PhpTool = None

try:
    from .swift_analyzer import SwiftAnalyzer as SwiftTool
except ImportError:
    SwiftTool = None

try:
    from .kotlin_analyzer import KotlinAnalyzer as KotlinTool
except ImportError:
    KotlinTool = None

try:
    from .objective_c_analyzer import ObjectiveCAnalyzer as ObjectiveCTool
except ImportError:
    ObjectiveCTool = None

try:
    from .dart_flutter_analyzer import DartFlutterAnalyzer as DartFlutterTool
except ImportError:
    DartFlutterTool = None

try:
    from .perl_analyzer import PerlAnalyzer as PerlTool
except ImportError:
    PerlTool = None

try:
    from .lua_analyzer import LuaAnalyzer as LuaTool
except ImportError:
    LuaTool = None

try:
    from .haskell_analyzer import HaskellAnalyzer as HaskellTool
except ImportError:
    HaskellTool = None

try:
    from .scala_analyzer import ScalaAnalyzer as ScalaTool
except ImportError:
    ScalaTool = None

# Only export available tools
__all__ = ['SecurityTool']
if SemgrepTool:
    __all__.append('SemgrepTool')
if GitleaksTool:
    __all__.append('GitleaksTool')
if SlitherTool:
    __all__.append('SlitherTool')
if BanditTool:
    __all__.append('BanditTool')
if GosecTool:
    __all__.append('GosecTool')
if NpmAuditTool:
    __all__.append('NpmAuditTool')
if CppTool:
    __all__.append('CppTool')
if RustTool:
    __all__.append('RustTool')
if JavaTool:
    __all__.append('JavaTool')
if RubyTool:
    __all__.append('RubyTool')
if GoTool:
    __all__.append('GoTool')
if CSharpTool:
    __all__.append('CSharpTool')
if SolidityTool:
    __all__.append('SolidityTool')
if VyperTool:
    __all__.append('VyperTool')
# New language analyzers
if PhpTool:
    __all__.append('PhpTool')
if SwiftTool:
    __all__.append('SwiftTool')
if KotlinTool:
    __all__.append('KotlinTool')
if ObjectiveCTool:
    __all__.append('ObjectiveCTool')
if DartFlutterTool:
    __all__.append('DartFlutterTool')
if PerlTool:
    __all__.append('PerlTool')
if LuaTool:
    __all__.append('LuaTool')
if HaskellTool:
    __all__.append('HaskellTool')
if ScalaTool:
    __all__.append('ScalaTool')