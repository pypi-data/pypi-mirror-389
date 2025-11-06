"""
Tighten (Security Hardening) modules for SecureCLI
Implements security hardening and remediation modules
"""

from typing import Dict, List, Any
from pathlib import Path

from .base import BaseModule, ModuleConfig, ModuleType, DomainProfile
from ..schemas.findings import Finding
from ..agents.refactor import RefactorAgent


class WebSecurityHardeningModule(BaseModule):
    """Security hardening for web applications"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        try:
            self.refactor_agent = RefactorAgent(config.config)
        except Exception as e:
            print(f"Warning: Could not initialize RefactorAgent: {e}")
            self.refactor_agent = None
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute web security hardening"""
        
        if not self.refactor_agent:
            return []  # Skip if refactor agent not available
        
        hardening_context = {
            'existing_findings': context.get('all_findings', []),
            'technologies': context.get('technologies', {}),
            'target_files': context.get('target_files', [])
        }
        
        try:
            hardening_suggestions = await self.refactor_agent.generate_hardening_plan(
                hardening_context, workspace_path
            )
            return hardening_suggestions
        except Exception as e:
            print(f"Error in web security hardening: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if web hardening is applicable"""
        domain_profiles = context.get('domain_profiles', [])
        web_domains = {
            DomainProfile.WEB2_FRONTEND,
            DomainProfile.WEB2_BACKEND,
            DomainProfile.WEB2_API
        }
        return any(profile in web_domains for profile in domain_profiles)


class Web3SecurityHardeningModule(BaseModule):
    """Security hardening for Web3/smart contract applications"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        try:
            self.refactor_agent = RefactorAgent(config.config)
        except Exception as e:
            print(f"Warning: Could not initialize RefactorAgent: {e}")
            self.refactor_agent = None
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute Web3 security hardening"""
        
        # Find Solidity files
        solidity_files = [
            f for f in context.get('target_files', [])
            if f.endswith('.sol')
        ]
        
        if not solidity_files:
            return []
        
        hardening_context = {
            'existing_findings': context.get('all_findings', []),
            'smart_contract_files': solidity_files,
            'contract_type': self._detect_contract_type(context)
        }
        
        try:
            hardening_suggestions = await self.refactor_agent.generate_smart_contract_hardening(
                hardening_context, workspace_path
            )
            return hardening_suggestions
        except Exception as e:
            print(f"Error in Web3 security hardening: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if Web3 hardening is applicable"""
        domain_profiles = context.get('domain_profiles', [])
        web3_domains = {
            DomainProfile.WEB3_SMART_CONTRACT,
            DomainProfile.WEB3_DEFI,
            DomainProfile.WEB3_NFT,
            DomainProfile.WEB3_DAO
        }
        return any(profile in web3_domains for profile in domain_profiles)
    
    def _detect_contract_type(self, context: Dict[str, Any]) -> str:
        """Detect the type of smart contract"""
        domain_profiles = context.get('domain_profiles', [])
        
        if DomainProfile.WEB3_DEFI in domain_profiles:
            return 'defi'
        elif DomainProfile.WEB3_NFT in domain_profiles:
            return 'nft'
        elif DomainProfile.WEB3_DAO in domain_profiles:
            return 'dao'
        else:
            return 'general'


class InfrastructureHardeningModule(BaseModule):
    """Security hardening for infrastructure and DevOps"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        try:
            self.refactor_agent = RefactorAgent(config.config)
        except Exception as e:
            print(f"Warning: Could not initialize RefactorAgent: {e}")
            self.refactor_agent = None
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute infrastructure security hardening"""
        
        # Find infrastructure files
        infra_files = self._find_infrastructure_files(context.get('target_files', []))
        
        if not infra_files:
            return []
        
        hardening_context = {
            'existing_findings': context.get('all_findings', []),
            'infrastructure_files': infra_files,
            'deployment_type': self._detect_deployment_type(infra_files)
        }
        
        try:
            hardening_suggestions = await self.refactor_agent.generate_infrastructure_hardening(
                hardening_context, workspace_path
            )
            return hardening_suggestions
        except Exception as e:
            print(f"Error in infrastructure security hardening: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if infrastructure hardening is applicable"""
        target_files = context.get('target_files', [])
        infra_files = self._find_infrastructure_files(target_files)
        return len(infra_files) > 0
    
    def _find_infrastructure_files(self, files: List[str]) -> List[str]:
        """Find infrastructure-related files"""
        infra_patterns = [
            '.yml', '.yaml',           # Docker Compose, Kubernetes, CI/CD
            '.tf', '.tfvars',          # Terraform
            'dockerfile', 'Dockerfile', # Docker
            '.json'                    # Various config files
        ]
        
        infra_files = []
        for file_path in files:
            file_lower = file_path.lower()
            if any(pattern in file_lower for pattern in infra_patterns):
                infra_files.append(file_path)
            elif any(name in file_lower for name in ['docker', 'k8s', 'kubernetes', 'helm']):
                infra_files.append(file_path)
        
        return infra_files
    
    def _detect_deployment_type(self, infra_files: List[str]) -> str:
        """Detect deployment type from infrastructure files"""
        file_names = [Path(f).name.lower() for f in infra_files]
        
        if any('terraform' in name or name.endswith('.tf') for name in file_names):
            return 'terraform'
        elif any('docker' in name for name in file_names):
            return 'docker'
        elif any('k8s' in name or 'kubernetes' in name for name in file_names):
            return 'kubernetes'
        elif any('compose' in name for name in file_names):
            return 'docker_compose'
        else:
            return 'general'


class DependencyHardeningModule(BaseModule):
    """Security hardening for dependencies and supply chain"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        try:
            self.refactor_agent = RefactorAgent(config.config)
        except Exception as e:
            print(f"Warning: Could not initialize RefactorAgent: {e}")
            self.refactor_agent = None
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute dependency security hardening"""
        
        # Find dependency files
        dependency_files = self._find_dependency_files(context.get('target_files', []))
        
        if not dependency_files:
            return []
        
        hardening_context = {
            'existing_findings': context.get('all_findings', []),
            'dependency_files': dependency_files,
            'technologies': context.get('technologies', {})
        }
        
        try:
            hardening_suggestions = await self.refactor_agent.generate_dependency_hardening(
                hardening_context, workspace_path
            )
            return hardening_suggestions
        except Exception as e:
            print(f"Error in dependency security hardening: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if dependency hardening is applicable"""
        target_files = context.get('target_files', [])
        dependency_files = self._find_dependency_files(target_files)
        return len(dependency_files) > 0
    
    def _find_dependency_files(self, files: List[str]) -> List[str]:
        """Find dependency management files"""
        dependency_patterns = [
            'package.json', 'package-lock.json', 'yarn.lock',  # Node.js
            'requirements.txt', 'Pipfile', 'pyproject.toml',   # Python
            'go.mod', 'go.sum',                                # Go
            'Cargo.toml', 'Cargo.lock',                        # Rust
            'pom.xml', 'build.gradle',                         # Java
            'composer.json'                                    # PHP
        ]
        
        dependency_files = []
        for file_path in files:
            file_name = Path(file_path).name
            if file_name in dependency_patterns:
                dependency_files.append(file_path)
        
        return dependency_files


class AuthenticationHardeningModule(BaseModule):
    """Security hardening focused on authentication and authorization"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        try:
            self.refactor_agent = RefactorAgent(config.config)
        except Exception as e:
            print(f"Warning: Could not initialize RefactorAgent: {e}")
            self.refactor_agent = None
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute authentication/authorization hardening"""
        
        # Look for authentication-related findings
        auth_findings = self._filter_auth_findings(context.get('all_findings', []))
        
        if not auth_findings:
            return []
        
        hardening_context = {
            'auth_findings': auth_findings,
            'technologies': context.get('technologies', {}),
            'target_files': context.get('target_files', [])
        }
        
        try:
            hardening_suggestions = await self.refactor_agent.generate_auth_hardening(
                hardening_context, workspace_path
            )
            return hardening_suggestions
        except Exception as e:
            print(f"Error in authentication security hardening: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if auth hardening is applicable"""
        all_findings = context.get('all_findings', [])
        auth_findings = self._filter_auth_findings(all_findings)
        return len(auth_findings) > 0
    
    def _filter_auth_findings(self, findings: List[Finding]) -> List[Finding]:
        """Filter findings related to authentication/authorization"""
        auth_keywords = [
            'authentication', 'authorization', 'auth', 'login', 'session',
            'jwt', 'token', 'password', 'credential', 'access control',
            'permission', 'privilege', 'role', 'oauth'
        ]
        
        auth_findings = []
        for finding in findings:
            title_lower = finding.title.lower()
            desc_lower = finding.description.lower()
            
            if any(keyword in title_lower or keyword in desc_lower for keyword in auth_keywords):
                auth_findings.append(finding)
        
        return auth_findings


class CryptographyHardeningModule(BaseModule):
    """Security hardening focused on cryptographic issues"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        try:
            self.refactor_agent = RefactorAgent(config.config)
        except Exception as e:
            print(f"Warning: Could not initialize RefactorAgent: {e}")
            self.refactor_agent = None
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute cryptography hardening"""
        
        # Look for cryptography-related findings
        crypto_findings = self._filter_crypto_findings(context.get('all_findings', []))
        
        if not crypto_findings:
            return []
        
        hardening_context = {
            'crypto_findings': crypto_findings,
            'technologies': context.get('technologies', {}),
            'target_files': context.get('target_files', [])
        }
        
        try:
            hardening_suggestions = await self.refactor_agent.generate_crypto_hardening(
                hardening_context, workspace_path
            )
            return hardening_suggestions
        except Exception as e:
            print(f"Error in cryptography security hardening: {e}")
            return []
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if crypto hardening is applicable"""
        all_findings = context.get('all_findings', [])
        crypto_findings = self._filter_crypto_findings(all_findings)
        return len(crypto_findings) > 0
    
    def _filter_crypto_findings(self, findings: List[Finding]) -> List[Finding]:
        """Filter findings related to cryptography"""
        crypto_keywords = [
            'crypto', 'encryption', 'decrypt', 'hash', 'md5', 'sha1',
            'weak crypto', 'insecure random', 'ssl', 'tls', 'certificate',
            'key', 'cipher', 'aes', 'rsa', 'ecdsa', 'hmac'
        ]
        
        crypto_findings = []
        for finding in findings:
            title_lower = finding.title.lower()
            desc_lower = finding.description.lower()
            
            if any(keyword in title_lower or keyword in desc_lower for keyword in crypto_keywords):
                crypto_findings.append(finding)
        
        return crypto_findings


# Tighten module factory
def create_tighten_modules() -> List[BaseModule]:
    """Create and configure tighten (hardening) modules"""
    
    modules = []
    
    # Web Security Hardening
    web_hardening_config = ModuleConfig(
        name="web_security_hardening",
        module_type=ModuleType.TIGHTEN,
        domain_profiles=[
            DomainProfile.WEB2_FRONTEND,
            DomainProfile.WEB2_BACKEND,
            DomainProfile.WEB2_API
        ],
        priority=30,
        dependencies=["semgrep_scanner", "llm_frontend_auditor", "llm_backend_auditor"],
        config={}
    )
    modules.append(WebSecurityHardeningModule(web_hardening_config))
    
    # Web3 Security Hardening
    web3_hardening_config = ModuleConfig(
        name="web3_security_hardening",
        module_type=ModuleType.TIGHTEN,
        domain_profiles=[
            DomainProfile.WEB3_SMART_CONTRACT,
            DomainProfile.WEB3_DEFI,
            DomainProfile.WEB3_NFT,
            DomainProfile.WEB3_DAO
        ],
        priority=30,
        dependencies=["slither_scanner", "llm_web3_auditor"],
        config={}
    )
    modules.append(Web3SecurityHardeningModule(web3_hardening_config))
    
    # Infrastructure Hardening
    infra_hardening_config = ModuleConfig(
        name="infrastructure_hardening",
        module_type=ModuleType.TIGHTEN,
        domain_profiles=[DomainProfile.INFRASTRUCTURE, DomainProfile.DEVOPS],
        priority=30,
        dependencies=["semgrep_scanner"],
        config={}
    )
    modules.append(InfrastructureHardeningModule(infra_hardening_config))
    
    # Dependency Hardening
    dependency_hardening_config = ModuleConfig(
        name="dependency_hardening",
        module_type=ModuleType.TIGHTEN,
        domain_profiles=list(DomainProfile),  # Applicable to all domains
        priority=25,
        dependencies=["dependency_scanner"],
        config={}
    )
    modules.append(DependencyHardeningModule(dependency_hardening_config))
    
    # Authentication Hardening
    auth_hardening_config = ModuleConfig(
        name="authentication_hardening",
        module_type=ModuleType.TIGHTEN,
        domain_profiles=[
            DomainProfile.WEB2_BACKEND,
            DomainProfile.WEB2_API,
            DomainProfile.WEB2_FRONTEND
        ],
        priority=35,
        dependencies=["semgrep_scanner"],
        config={}
    )
    modules.append(AuthenticationHardeningModule(auth_hardening_config))
    
    # Cryptography Hardening
    crypto_hardening_config = ModuleConfig(
        name="cryptography_hardening",
        module_type=ModuleType.TIGHTEN,
        domain_profiles=list(DomainProfile),  # Applicable to all domains
        priority=25,
        dependencies=["semgrep_scanner"],
        config={}
    )
    modules.append(CryptographyHardeningModule(crypto_hardening_config))
    
    return modules