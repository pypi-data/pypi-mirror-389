"""
SecureCLI - AI-Powered Security Analysis Tool
GitHub Integration and Universal Language Support
"""

__version__ = "1.0.0"
__author__ = "SecureCLI Team"
__description__ = "AI-Powered Security Analysis with GitHub Integration and Universal Language Support"

# Import key components for easy access with error handling
try:
    from .github import GitHubRepositoryAnalyzer, analyze_github_repo_cli, validate_github_url
    GITHUB_AVAILABLE = True
except ImportError:
    GITHUB_AVAILABLE = False
    GitHubRepositoryAnalyzer = None
    analyze_github_repo_cli = None
    validate_github_url = None

try:
    from .languages import (
        UniversalLanguageDetector,
        language_detector,
        detect_file_language,
        analyze_project_languages
    )
    LANGUAGES_AVAILABLE = True
except ImportError:
    LANGUAGES_AVAILABLE = False
    UniversalLanguageDetector = None
    language_detector = None
    detect_file_language = None
    analyze_project_languages = None

try:
    from .modules import create_analysis_engine, AnalysisProfile
    MODULES_AVAILABLE = True
except ImportError:
    MODULES_AVAILABLE = False
    create_analysis_engine = None
    AnalysisProfile = None

try:
    # Temporarily disabled due to syntax error
    # from .agents import create_agent_orchestrator
    AGENTS_AVAILABLE = False
    create_agent_orchestrator = None
except ImportError:
    AGENTS_AVAILABLE = False
    create_agent_orchestrator = None

try:
    from .report import ReportGenerator
    REPORTING_AVAILABLE = True
except ImportError:
    REPORTING_AVAILABLE = False
    ReportGenerator = None

try:
    from .config import ConfigManager
    CONFIG_AVAILABLE = True
except ImportError:
    CONFIG_AVAILABLE = False
    ConfigManager = None

# Build dynamic __all__ based on available components
__all__ = ["__version__", "__author__", "__description__"]

if CONFIG_AVAILABLE and ConfigManager:
    __all__.append("ConfigManager")
if MODULES_AVAILABLE and create_analysis_engine:
    __all__.extend(["create_analysis_engine", "AnalysisProfile"])
if AGENTS_AVAILABLE and create_agent_orchestrator:
    __all__.append("create_agent_orchestrator")
if REPORTING_AVAILABLE and ReportGenerator:
    __all__.append("ReportGenerator")
if GITHUB_AVAILABLE:
    __all__.extend(["GitHubRepositoryAnalyzer", "analyze_github_repo_cli", "validate_github_url"])
if LANGUAGES_AVAILABLE:
    __all__.extend([
        "UniversalLanguageDetector",
        "language_detector", 
        "detect_file_language",
        "analyze_project_languages"
    ])