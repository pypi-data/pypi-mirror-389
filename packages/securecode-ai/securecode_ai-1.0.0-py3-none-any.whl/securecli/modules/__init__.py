"""
Module registry and initialization for SecureCLI
Manages all security modules and provides unified access
"""

from typing import Dict, List, Any, Optional, Tuple

# Attempt to import core base components; if unavailable, provide safe fallbacks.
try:
    from .base import ModuleRegistry, ModuleManager, TechnologyDetector, DomainProfile, ModuleType
    BASE_AVAILABLE = True
    
    # Define AnalysisProfile class
    class AnalysisProfile:
        """Analysis profile constants"""
        FRONTEND = "frontend"
        BACKEND = "backend"
        WEB3 = "web3"
        MOBILE = "mobile"
        DEVOPS = "devops"

        def __init__(self, name: str):
            self.name = name
            self.value = name
            
except Exception as e:
    # Avoid raising on import failure; provide lightweight fallbacks so module can be imported.
    BASE_AVAILABLE = False
    ModuleRegistry = None
    ModuleManager = None
    TechnologyDetector = None
    DomainProfile = None
    ModuleType = None

    class AnalysisProfile:
        """Fallback analysis profile when base modules unavailable"""
        FRONTEND = "frontend"
        BACKEND = "backend"
        WEB3 = "web3"
        MOBILE = "mobile"
        DEVOPS = "devops"

        def __init__(self, name: str):
            self.name = name
            self.value = name

# Module creator factories may live in subpackages; provide safe defaults if missing.
try:
    from .scanners import create_scanner_modules  # type: ignore
except Exception:
    def create_scanner_modules() -> List[Any]:
        return []

try:
    from .auditors import create_auditor_modules  # type: ignore
except Exception:
    def create_auditor_modules() -> List[Any]:
        return []

try:
    from .tighten import create_tighten_modules  # type: ignore
except Exception:
    def create_tighten_modules() -> List[Any]:
        return []


class SecureCLIModuleRegistry:
    """SecureCLI-specific module registry with built-in modules"""

    def __init__(self, config: Dict[str, Any] = None):
        if not BASE_AVAILABLE:
            raise RuntimeError("Base modules not available - required dependencies missing")

        # Initialize base registry
        if ModuleRegistry:
            self.base_registry = ModuleRegistry()
        else:
            # Minimal fallback registry to allow registering/lookups
            class _FallbackRegistry:
                def __init__(self):
                    self.modules = {}

                def register_module(self, module):
                    name = getattr(module, "name", None)
                    if name:
                        self.modules[name] = module
                    return module

            self.base_registry = _FallbackRegistry()

        self.config = config or {}
        self._initialize_builtin_modules()

    def register_module(self, module):
        """Register a module"""
        if hasattr(self.base_registry, "register_module"):
            return self.base_registry.register_module(module)
        return None

    @property
    def modules(self):
        """Get registered modules"""
        return getattr(self.base_registry, "modules", {})

    def _initialize_builtin_modules(self):
        """Initialize all built-in security modules"""

        # Register scanner modules
        try:
            scanner_modules = create_scanner_modules()
            for module in scanner_modules:
                if self._is_module_enabled(getattr(module, "name", "")):
                    self.register_module(module)
        except Exception as e:
            print("Warning: Failed to initialize scanner modules:", e)

        # Register auditor modules
        try:
            auditor_modules = create_auditor_modules()
            for module in auditor_modules:
                if self._is_module_enabled(getattr(module, "name", "")):
                    self.register_module(module)
        except Exception as e:
            print("Warning: Failed to initialize auditor modules:", e)

        # Register tighten modules
        try:
            tighten_modules = create_tighten_modules()
            for module in tighten_modules:
                if self._is_module_enabled(getattr(module, "name", "")):
                    self.register_module(module)
        except Exception as e:
            print("Warning: Failed to initialize tighten modules:", e)

    def _is_module_enabled(self, module_name: str) -> bool:
        """Check if module is enabled in configuration"""

        modules_config = self.config.get("modules", {})

        # If 'disabled' list exists, modules listed there are disabled
        if isinstance(modules_config, dict) and "disabled" in modules_config:
            disabled = modules_config.get("disabled") or []
            return module_name not in disabled

        # If 'enabled' list exists, only those are enabled
        if isinstance(modules_config, dict) and "enabled" in modules_config:
            enabled = modules_config.get("enabled") or []
            return module_name in enabled

        # Module-specific setting fallback
        module_config = modules_config.get(module_name, {}) if isinstance(modules_config, dict) else {}
        return bool(module_config.get("enabled", True))


class AnalysisEngine:
    """Main analysis engine that coordinates module execution"""

    def __init__(self, config: Dict[str, Any] = None):
        if not BASE_AVAILABLE:
            raise RuntimeError("Base modules not available - required dependencies missing")

        self.config = config or {}
        self.registry = SecureCLIModuleRegistry(self.config)

        # Initialize manager and detector if available
        try:
            self.manager = ModuleManager(self.registry.base_registry) if ModuleManager else None
        except Exception:
            self.manager = None

        try:
            self.technology_detector = TechnologyDetector() if TechnologyDetector else None
        except Exception:
            self.technology_detector = None

    async def analyze_workspace(
        self,
        workspace_path: str,
        file_list: List[str],
        scan_mode: str = "comprehensive",
    ) -> Dict[str, Any]:
        """
        Perform comprehensive security analysis of workspace

        Args:
            workspace_path: Path to workspace/repository
            file_list: List of files to analyze
            scan_mode: Analysis mode (quick, comprehensive, deep)

        Returns:
            Analysis results with findings and metadata
        """

        # Language detection for comprehensive scanner selection
        from ..languages.detector import analyze_project_languages
        
        language_analysis = {}
        detected_languages = []
        recommended_tools = []
        
        try:
            language_analysis = analyze_project_languages(workspace_path)
            detected_languages = list(language_analysis.get('language_breakdown', {}).keys())
            recommended_tools = language_analysis.get('recommended_tools', [])
        except Exception as e:
            print(f"Warning: Language detection failed: {e}")

        if not self.technology_detector:
            technologies: List[str] = detected_languages  # Use detected languages as fallback
            domain_profiles: List[Any] = []
        else:
            technologies = self.technology_detector.detect_technologies(file_list)
            domain_profiles = self.technology_detector.infer_domain_profiles(technologies)
            # Merge detected languages with existing technologies
            if isinstance(technologies, list):
                technologies = list(set(technologies + detected_languages))
            else:
                # If technologies is not a list, use detected_languages
                technologies = detected_languages

        context: Dict[str, Any] = {
            "target_files": file_list,
            "technologies": {"languages": detected_languages, "frameworks": technologies},
            "domain_profiles": domain_profiles,
            "scan_mode": scan_mode,
            "workspace_path": workspace_path,
            "language_analysis": language_analysis,
            "recommended_tools": recommended_tools,
            "priority_languages": language_analysis.get('security_priority_languages', []),
            "web3_languages": language_analysis.get('web3_languages', [])
        }

        if self.manager:
            results = await self._execute_analysis_phases(context, workspace_path)
        else:
            results = {"all_findings": [], "phase_results": {}, "modules_executed": []}

        analysis_results = {
            "metadata": {
                "workspace_path": workspace_path,
                "scan_mode": scan_mode,
                "technologies": technologies,
                "detected_languages": detected_languages,
                "language_analysis": language_analysis,
                "domain_profiles": [getattr(p, "value", p) for p in domain_profiles] if domain_profiles else [],
                "files_analyzed": len(file_list),
                "modules_executed": results.get("modules_executed", []),
                "recommended_tools": recommended_tools
            },
            "findings": results.get("all_findings", []),
            "statistics": self._calculate_statistics(results.get("all_findings", [])),
            "phase_results": results.get("phase_results", {}),
        }

        return analysis_results

    async def _execute_analysis_phases(self, context: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Execute analysis in phases based on scan mode"""

        if not self.manager:
            return {"all_findings": [], "phase_results": {}, "modules_executed": []}

        scan_mode = context.get("scan_mode", "comprehensive")
        all_findings: List[Any] = []
        phase_results: Dict[str, Any] = {}

        # Phase 1: Scanners
        try:
            scanner_findings = await self.manager.execute_modules(
                context, workspace_path, module_type=(ModuleType.SCANNER if ModuleType else "scanner")
            )
            all_findings.extend(scanner_findings or [])
            phase_results["scanners"] = {
                "findings_count": len(scanner_findings or []),
                "findings": scanner_findings or []
            }
        except Exception as e:
            phase_results["scanners"] = {"findings_count": 0, "findings": [], "error": str(e)}

        context["scanner_findings"] = phase_results["scanners"].get("findings", [])

        # Phase 2: Auditors
        if scan_mode in ("comprehensive", "deep"):
            try:
                auditor_findings = await self.manager.execute_modules(
                    context, workspace_path, module_type=(ModuleType.AUDITOR if ModuleType else "auditor")
                )
                all_findings.extend(auditor_findings or [])
                phase_results["auditors"] = {
                    "findings_count": len(auditor_findings or []),
                    "findings": auditor_findings or []
                }
            except Exception as e:
                phase_results["auditors"] = {"findings_count": 0, "findings": [], "error": str(e)}

        # Phase 3: Tighten
        if scan_mode == "deep":
            context["all_findings"] = all_findings
            try:
                tighten_findings = await self.manager.execute_modules(
                    context, workspace_path, module_type=(ModuleType.TIGHTEN if ModuleType else "tighten")
                )
                all_findings.extend(tighten_findings or [])
                phase_results["tighten"] = {
                    "findings_count": len(tighten_findings or []),
                    "findings": tighten_findings or []
                }
            except Exception as e:
                phase_results["tighten"] = {"findings_count": 0, "findings": [], "error": str(e)}

        modules_executed = list(self.registry.modules.keys()) if self.registry.modules else []

        return {
            "all_findings": all_findings,
            "phase_results": phase_results,
            "modules_executed": modules_executed
        }

    def _calculate_statistics(self, findings: List[Any]) -> Dict[str, Any]:
        """Calculate analysis statistics"""

        if not findings:
            return {
                "total_findings": 0,
                "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "by_type": {},
                "files_affected": 0
            }

        stats = {
            "total_findings": len(findings),
            "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            "by_type": {},
            "files_affected": len(set(getattr(f, "file", None) for f in findings if getattr(f, "file", None))),
            "cross_file_issues": len([f for f in findings if getattr(f, "cross_file", False)]),
        }

        for finding in findings:
            severity = getattr(finding, "severity", "Unknown")
            if severity in stats["by_severity"]:
                stats["by_severity"][severity] += 1
            owasp_categories = getattr(finding, "owasp", []) or []
            for category in owasp_categories:
                stats["by_type"][category] = stats["by_type"].get(category, 0) + 1

        return stats

    def get_analysis_config(self) -> Dict[str, Any]:
        """Get current analysis configuration"""

        config = {
            "scan_modes": {
                "quick": "Fast scan using automated tools only",
                "comprehensive": "Automated tools + AI-powered analysis",
                "deep": "Full analysis including hardening recommendations",
            }
        }

        if self.manager and hasattr(self.manager, "get_module_info"):
            try:
                config["modules"] = self.manager.get_module_info()
            except Exception as e:
                config["modules"] = {"error": str(e)}
        else:
            config["modules"] = {"available": False}

        if DomainProfile:
            try:
                config["supported_domains"] = [profile.value for profile in DomainProfile]
            except Exception:
                config["supported_domains"] = []
        else:
            config["supported_domains"] = []

        if self.technology_detector:
            try:
                ext_map = getattr(self.technology_detector, "EXTENSION_MAPPINGS", {}) or {}
                fw_map = getattr(self.technology_detector, "FRAMEWORK_PATTERNS", {}) or {}
                config["technology_detection"] = {
                    "languages": list(ext_map.keys()),
                    "frameworks": list(fw_map.keys())
                }
            except Exception:
                config["technology_detection"] = {"available": False}
        else:
            config["technology_detection"] = {"available": False}

        return config


def create_analysis_engine(config: Dict[str, Any] = None) -> Optional['AnalysisEngine']:
    """
    Create and configure analysis engine

    Args:
        config: Configuration dictionary

    Returns:
        Configured AnalysisEngine instance or None if dependencies missing
    """
    try:
        if BASE_AVAILABLE:
            return AnalysisEngine(config)
        else:
            # Return simple fallback engine
            return SimpleAnalysisEngine(config)
    except RuntimeError as e:
        print("Warning: Cannot create analysis engine:", e)
        return None


class SimpleAnalysisEngine:
    """Simple fallback analysis engine when full modules are not available"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
    
    async def analyze_workspace(self, workspace_path: str, file_list: List[str], scan_mode: str = "comprehensive") -> Dict[str, Any]:
        """Simple analysis that counts files and detects basic technologies"""
        
        # Basic file analysis
        file_extensions = {}
        for file_path in file_list:
            ext = file_path.split('.')[-1].lower() if '.' in file_path else 'unknown'
            file_extensions[ext] = file_extensions.get(ext, 0) + 1
        
        # Map extensions to technologies
        tech_mapping = {
            'py': 'Python',
            'js': 'JavaScript', 
            'ts': 'TypeScript',
            'java': 'Java',
            'go': 'Go',
            'rs': 'Rust',
            'php': 'PHP',
            'rb': 'Ruby',
            'sol': 'Solidity',
            'c': 'C',
            'cpp': 'C++',
            'h': 'C/C++',
            'html': 'HTML',
            'css': 'CSS',
            'json': 'JSON',
            'yaml': 'YAML',
            'yml': 'YAML'
        }
        
        detected_technologies = []
        for ext, count in file_extensions.items():
            if ext in tech_mapping:
                detected_technologies.append(f"{tech_mapping[ext]} ({count} files)")
        
        return {
            "metadata": {
                "workspace_path": workspace_path,
                "scan_mode": scan_mode,
                "technologies": detected_technologies,
                "files_analyzed": len(file_list),
                "engine_type": "simple_fallback"
            },
            "findings": [],
            "statistics": {
                "total_findings": 0,
                "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "files_by_type": file_extensions
            },
            "recommendations": [
                "Install full SecureCLI dependencies for complete security analysis",
                "Run 'pip install securecli[full]' for enhanced scanning capabilities"
            ]
        }
    
    def get_analysis_config(self) -> Dict[str, Any]:
        """Get simple analysis configuration"""
        return {
            "engine_type": "simple_fallback",
            "available_scanners": ["basic_file_analysis"],
            "scan_modes": ["basic"],
            "note": "Limited functionality - install full dependencies for complete analysis"
        }


def get_default_module_config() -> Dict[str, Any]:
    """Get default module configuration"""

    return {
        "modules": {
            "enabled": [
                "semgrep_scanner",
                "gitleaks_scanner",
                "dependency_scanner",
                "llm_frontend_auditor",
                "llm_backend_auditor",
                "llm_web3_auditor",
                "architecture_auditor",
            ],
            "semgrep_scanner": {
                "enabled": True,
                "rulesets": ["auto", "security"],
                "timeout": 300
            },
            "gitleaks_scanner": {
                "enabled": True,
                "redact_secrets": True,
                "timeout": 60
            },
            "llm_frontend_auditor": {
                "enabled": True,
                "max_files": 10,
                "model": "gpt-4"
            },
            "llm_backend_auditor": {
                "enabled": True,
                "max_files": 10,
                "model": "gpt-4"
            },
            "llm_web3_auditor": {
                "enabled": True,
                "max_files": 5,
                "model": "gpt-4"
            },
        },
        "scan_modes": {
            "quick": {
                "modules": ["scanners"],
                "timeout": 300
            },
            "comprehensive": {
                "modules": ["scanners", "auditors"],
                "timeout": 900
            },
            "deep": {
                "modules": ["scanners", "auditors", "tighten"],
                "timeout": 1800
            },
        },
    }


def validate_module_config(config: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
    """
    Validate module configuration

    Args:
        config: Configuration to validate

    Returns:
        Tuple of (is_valid, error_message)
    """
    try:
        if "modules" not in config:
            return False, "Missing 'modules' section in configuration"

        modules_config = config["modules"]

        if "enabled" in modules_config and not isinstance(modules_config["enabled"], list):
            return False, "'enabled' must be a list of module names"

        known_modules = {
            "semgrep_scanner",
            "gitleaks_scanner",
            "slither_scanner",
            "bandit_scanner",
            "gosec_scanner",
            "dependency_scanner",
            "llm_frontend_auditor",
            "llm_backend_auditor",
            "llm_web3_auditor",
            "architecture_auditor",
        }

        for module_name, module_config in modules_config.items():
            if module_name in ("enabled", "disabled"):
                continue
            if module_name not in known_modules:
                return False, f"Unknown module: {module_name}"
            if not isinstance(module_config, dict):
                return False, f"Module config for {module_name} must be a dictionary"

        return True, None
    except Exception as e:
        return False, f"Configuration validation error: {e}"


# Public exports
__all__ = [
    "create_analysis_engine",
    "get_default_module_config",
    "validate_module_config",
    "AnalysisProfile"
]

if BASE_AVAILABLE:
    __all__.extend(["SecureCLIModuleRegistry", "AnalysisEngine"])