"""
Base module system for SecureCLI
Provides modular security analysis capabilities
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from ..schemas.findings import Finding


class ModuleType(Enum):
    """Types of security modules"""
    SCANNER = "scanner"      # Automated security scanners
    AUDITOR = "auditor"      # AI-powered security auditors  
    TIGHTEN = "tighten"      # Security hardening modules
    REPORTER = "reporter"    # Report generation modules


class DomainProfile(Enum):
    """Domain-specific security profiles"""
    WEB2_FRONTEND = "web2_frontend"
    WEB2_BACKEND = "web2_backend"
    WEB2_API = "web2_api"
    WEB2_DATABASE = "web2_database"
    WEB3_SMART_CONTRACT = "web3_smart_contract"
    WEB3_DEFI = "web3_defi"
    WEB3_NFT = "web3_nft"
    WEB3_DAO = "web3_dao"
    INFRASTRUCTURE = "infrastructure"
    MOBILE = "mobile"
    DEVOPS = "devops"


@dataclass
class ModuleConfig:
    """Configuration for security modules"""
    name: str
    module_type: ModuleType
    domain_profiles: List[DomainProfile]
    enabled: bool = True
    priority: int = 50
    config: Dict[str, Any] = None
    dependencies: List[str] = None
    
    def __post_init__(self):
        if self.config is None:
            self.config = {}
        if self.dependencies is None:
            self.dependencies = []


class BaseModule(ABC):
    """Base class for all security modules"""
    
    def __init__(self, config: ModuleConfig):
        self.config = config
        self.name = config.name
        self.module_type = config.module_type
        self.domain_profiles = config.domain_profiles
        self.enabled = config.enabled
        self.priority = config.priority
    
    @abstractmethod
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """
        Execute the module and return findings
        
        Args:
            context: Analysis context (files, technologies, etc.)
            workspace_path: Path to workspace/repository
        
        Returns:
            List of security findings
        """
        pass
    
    @abstractmethod
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """
        Check if module is applicable to the given context
        
        Args:
            context: Analysis context
        
        Returns:
            True if module should be executed
        """
        pass
    
    def get_dependencies(self) -> List[str]:
        """Get module dependencies"""
        return self.config.dependencies
    
    def validate_dependencies(self, available_modules: List[str]) -> bool:
        """Validate that all dependencies are available"""
        return all(dep in available_modules for dep in self.get_dependencies())


class ModuleRegistry:
    """Registry for managing security modules"""
    
    def __init__(self):
        self.modules: Dict[str, BaseModule] = {}
        self.domain_profiles: Dict[DomainProfile, List[str]] = {}
        self._initialize_domain_profiles()
    
    def register_module(self, module: BaseModule):
        """Register a security module"""
        self.modules[module.name] = module
        
        # Update domain profile mappings
        for profile in module.domain_profiles:
            if profile not in self.domain_profiles:
                self.domain_profiles[profile] = []
            self.domain_profiles[profile].append(module.name)
    
    def get_module(self, name: str) -> Optional[BaseModule]:
        """Get module by name"""
        return self.modules.get(name)
    
    def get_modules_for_domain(self, domain: DomainProfile) -> List[BaseModule]:
        """Get modules applicable to a domain"""
        module_names = self.domain_profiles.get(domain, [])
        return [self.modules[name] for name in module_names if name in self.modules]
    
    def get_applicable_modules(
        self,
        context: Dict[str, Any],
        module_type: Optional[ModuleType] = None
    ) -> List[BaseModule]:
        """
        Get modules applicable to the given context
        
        Args:
            context: Analysis context
            module_type: Optional filter by module type
        
        Returns:
            List of applicable modules
        """
        applicable = []
        
        for module in self.modules.values():
            if not module.enabled:
                continue
            
            if module_type and module.module_type != module_type:
                continue
            
            if module.is_applicable(context):
                applicable.append(module)
        
        # Sort by priority (higher priority first)
        applicable.sort(key=lambda m: m.priority, reverse=True)
        
        return applicable
    
    def resolve_dependencies(self, modules: List[BaseModule]) -> List[BaseModule]:
        """Resolve module dependencies and return execution order"""
        resolved = []
        remaining = modules.copy()
        
        while remaining:
            # Find modules with no unresolved dependencies
            ready = []
            for module in remaining:
                deps = module.get_dependencies()
                if all(dep in [m.name for m in resolved] for dep in deps):
                    ready.append(module)
            
            if not ready:
                # Circular dependency or missing dependency
                missing_deps = []
                for module in remaining:
                    for dep in module.get_dependencies():
                        if dep not in [m.name for m in resolved] and dep not in self.modules:
                            missing_deps.append(f"{module.name} -> {dep}")
                
                if missing_deps:
                    raise ValueError(f"Missing dependencies: {missing_deps}")
                else:
                    raise ValueError("Circular dependency detected")
            
            # Add ready modules to resolved list
            resolved.extend(ready)
            for module in ready:
                remaining.remove(module)
        
        return resolved
    
    def _initialize_domain_profiles(self):
        """Initialize domain profile mappings"""
        # This will be populated as modules are registered
        for profile in DomainProfile:
            self.domain_profiles[profile] = []


class ModuleManager:
    """Manages module execution and coordination"""
    
    def __init__(self, registry: ModuleRegistry):
        self.registry = registry
    
    async def execute_modules(
        self,
        context: Dict[str, Any],
        workspace_path: str,
        module_type: Optional[ModuleType] = None,
        domain_filter: Optional[List[DomainProfile]] = None
    ) -> List[Finding]:
        """
        Execute applicable modules and collect findings
        
        Args:
            context: Analysis context
            workspace_path: Workspace path
            module_type: Optional module type filter
            domain_filter: Optional domain profile filter
        
        Returns:
            Aggregated findings from all modules
        """
        
        # Get applicable modules
        modules = self.registry.get_applicable_modules(context, module_type)
        
        # Apply domain filter if specified
        if domain_filter:
            filtered_modules = []
            for module in modules:
                if any(profile in module.domain_profiles for profile in domain_filter):
                    filtered_modules.append(module)
            modules = filtered_modules
        
        # Resolve dependencies
        try:
            execution_order = self.registry.resolve_dependencies(modules)
        except ValueError as e:
            raise RuntimeError(f"Module dependency error: {e}")
        
        # Execute modules in dependency order
        all_findings = []
        
        for module in execution_order:
            try:
                findings = await module.execute(context, workspace_path)
                all_findings.extend(findings)
                
                # Update context with module results
                context[f"module_{module.name}_findings"] = findings
                
            except Exception as e:
                # Log error but continue with other modules
                print(f"Error executing module {module.name}: {e}")
        
        return all_findings
    
    def get_module_info(self) -> Dict[str, Any]:
        """Get information about registered modules"""
        info = {
            "total_modules": len(self.registry.modules),
            "modules_by_type": {},
            "modules_by_domain": {},
            "modules": {}
        }
        
        # Count by type
        for module in self.registry.modules.values():
            module_type = module.module_type.value
            if module_type not in info["modules_by_type"]:
                info["modules_by_type"][module_type] = 0
            info["modules_by_type"][module_type] += 1
        
        # Count by domain
        for profile, module_names in self.registry.domain_profiles.items():
            info["modules_by_domain"][profile.value] = len(module_names)
        
        # Module details
        for name, module in self.registry.modules.items():
            info["modules"][name] = {
                "type": module.module_type.value,
                "domains": [p.value for p in module.domain_profiles],
                "enabled": module.enabled,
                "priority": module.priority,
                "dependencies": module.get_dependencies()
            }
        
        return info


# Technology detection utilities
class TechnologyDetector:
    """Detects technologies and frameworks in codebase"""
    
    # File extension mappings
    EXTENSION_MAPPINGS = {
        # Web2 Frontend
        ".js": ["javascript", "web2_frontend"],
        ".jsx": ["react", "web2_frontend"],
        ".ts": ["typescript", "web2_frontend"], 
        ".tsx": ["react", "typescript", "web2_frontend"],
        ".vue": ["vue", "web2_frontend"],
        ".html": ["html", "web2_frontend"],
        ".css": ["css", "web2_frontend"],
        ".scss": ["sass", "web2_frontend"],
        
        # Web2 Backend
        ".py": ["python", "web2_backend"],
        ".java": ["java", "web2_backend"],
        ".go": ["golang", "web2_backend"],
        ".rb": ["ruby", "web2_backend"],
        ".php": ["php", "web2_backend"],
        ".cs": ["csharp", "web2_backend"],
        
        # Web3
        ".sol": ["solidity", "web3_smart_contract"],
        ".vy": ["vyper", "web3_smart_contract"],
        
        # Infrastructure
        ".yml": ["yaml", "infrastructure"],
        ".yaml": ["yaml", "infrastructure"],
        ".json": ["json", "infrastructure"],
        ".tf": ["terraform", "infrastructure"],
        ".dockerfile": ["docker", "infrastructure"],
        
        # Mobile
        ".swift": ["swift", "mobile"],
        ".kt": ["kotlin", "mobile"],
        ".dart": ["dart", "mobile"]
    }
    
    # Framework detection patterns
    FRAMEWORK_PATTERNS = {
        # Package.json patterns
        "react": ["react", "@react"],
        "vue": ["vue", "@vue"],
        "angular": ["@angular", "angular"],
        "express": ["express"],
        "fastapi": ["fastapi"],
        "django": ["django"],
        "flask": ["flask"],
        "spring": ["spring-boot", "springframework"],
        
        # Web3 patterns
        "hardhat": ["hardhat"],
        "truffle": ["truffle"],
        "foundry": ["foundry-rs"],
        "brownie": ["eth-brownie"],
        "web3": ["web3", "ethers"]
    }
    
    @classmethod
    def detect_technologies(cls, file_list: List[str]) -> Dict[str, List[str]]:
        """
        Detect technologies from file list
        
        Args:
            file_list: List of file paths
        
        Returns:
            Dictionary mapping technology categories to detected technologies
        """
        
        technologies = {
            "languages": set(),
            "frameworks": set(),
            "domains": set()
        }
        
        # Analyze file extensions
        for file_path in file_list:
            for ext, tech_info in cls.EXTENSION_MAPPINGS.items():
                if file_path.endswith(ext):
                    technologies["languages"].add(tech_info[0])
                    if len(tech_info) > 1:
                        technologies["domains"].add(tech_info[1])
        
        # Convert to lists and return
        return {
            "languages": list(technologies["languages"]),
            "frameworks": list(technologies["frameworks"]),
            "domains": list(technologies["domains"])
        }
    
    @classmethod
    def infer_domain_profiles(cls, technologies: Dict[str, List[str]]) -> List[DomainProfile]:
        """
        Infer domain profiles from detected technologies
        
        Args:
            technologies: Technology detection results
        
        Returns:
            List of applicable domain profiles
        """
        
        profiles = set()
        domains = technologies.get("domains", [])
        languages = technologies.get("languages", [])
        frameworks = technologies.get("frameworks", [])
        
        # Direct domain mappings
        if "web2_frontend" in domains:
            profiles.add(DomainProfile.WEB2_FRONTEND)
        if "web2_backend" in domains:
            profiles.add(DomainProfile.WEB2_BACKEND)
        if "web3_smart_contract" in domains:
            profiles.add(DomainProfile.WEB3_SMART_CONTRACT)
        if "infrastructure" in domains:
            profiles.add(DomainProfile.INFRASTRUCTURE)
        if "mobile" in domains:
            profiles.add(DomainProfile.MOBILE)
        
        # Language-based inference
        if "solidity" in languages or "vyper" in languages:
            profiles.add(DomainProfile.WEB3_SMART_CONTRACT)
        if "javascript" in languages or "typescript" in languages:
            profiles.add(DomainProfile.WEB2_FRONTEND)
            if "express" in frameworks:
                profiles.add(DomainProfile.WEB2_BACKEND)
        
        # Framework-based inference
        if any(fw in frameworks for fw in ["react", "vue", "angular"]):
            profiles.add(DomainProfile.WEB2_FRONTEND)
        if any(fw in frameworks for fw in ["django", "flask", "fastapi", "spring"]):
            profiles.add(DomainProfile.WEB2_BACKEND)
        if any(fw in frameworks for fw in ["hardhat", "truffle", "foundry"]):
            profiles.add(DomainProfile.WEB3_SMART_CONTRACT)
        
        # Web3 sub-domains
        if DomainProfile.WEB3_SMART_CONTRACT in profiles:
            # Could add more specific detection for DeFi, NFT, DAO
            profiles.add(DomainProfile.WEB3_DEFI)  # Default assumption
        
        return list(profiles)