"""
Auditor modules for SecureCLI
Implements AI-powered security auditing modules using LangChain
"""

from typing import Dict, List, Any
import json

from .base import BaseModule, ModuleConfig, ModuleType, DomainProfile
from ..schemas.findings import Finding, ToolEvidence
from ..agents.auditor import AuditorAgent
from ..utils.cvss import SimpleVulnerabilityClassifier
from langchain.schema import HumanMessage, SystemMessage


class LLMAuditorModule(BaseModule):
    """Base LLM-powered auditor module"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.auditor_agent = AuditorAgent(config.config)
        self.vulnerability_classifier = SimpleVulnerabilityClassifier()
        
        # Domain-specific prompts
        self.domain_prompts = {
            DomainProfile.WEB2_FRONTEND: self._get_frontend_audit_prompt(),
            DomainProfile.WEB2_BACKEND: self._get_backend_audit_prompt(),
            DomainProfile.WEB2_API: self._get_api_audit_prompt(),
            DomainProfile.WEB3_SMART_CONTRACT: self._get_smart_contract_audit_prompt(),
            DomainProfile.WEB3_DEFI: self._get_defi_audit_prompt(),
            DomainProfile.INFRASTRUCTURE: self._get_infrastructure_audit_prompt()
        }
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Execute LLM-powered security audit"""
        
        findings = []
        
        # Get existing scanner findings for context
        scanner_findings = context.get('scanner_findings', [])
        
        # Perform domain-specific audits
        for profile in self.domain_profiles:
            if profile in context.get('domain_profiles', []):
                profile_findings = await self._audit_domain(
                    profile, context, workspace_path, scanner_findings
                )
                findings.extend(profile_findings)
        
        return findings
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Check if any domain profiles match"""
        domain_profiles = context.get('domain_profiles', [])
        return any(profile in self.domain_profiles for profile in domain_profiles)
    
    async def _audit_domain(
        self,
        domain: DomainProfile,
        context: Dict[str, Any],
        workspace_path: str,
        scanner_findings: List[Finding]
    ) -> List[Finding]:
        """Perform domain-specific audit"""
        
        # Get relevant files for this domain
        relevant_files = self._get_relevant_files(domain, context)
        if not relevant_files:
            return []
        
        # Get domain-specific prompt
        audit_prompt = self.domain_prompts.get(domain, self._get_generic_audit_prompt())
        
        # Prepare context for LLM
        file_contents = await self._get_file_contents(relevant_files[:10])  # Limit files
        scanner_context = self._format_scanner_findings(scanner_findings)
        
        # Build audit prompt
        prompt = audit_prompt.format(
            files=json.dumps(file_contents, indent=2),
            scanner_findings=scanner_context,
            domain=domain.value
        )
        
        # Execute LLM audit
        try:
            analysis_context = {
                'files': file_contents,
                'scanner_findings': scanner_findings,
                'domain': domain.value
            }
            
            findings = await self.auditor_agent.deep_analysis(analysis_context, workspace_path)
            return findings
        except Exception as e:
            print(f"Error in LLM audit for {domain.value}: {e}")
            return []
    
    def _get_relevant_files(self, domain: DomainProfile, context: Dict[str, Any]) -> List[str]:
        """Get files relevant to specific domain"""
        
        all_files = context.get('target_files', [])
        
        # Domain-specific file filtering
        if domain == DomainProfile.WEB2_FRONTEND:
            return [f for f in all_files if any(f.endswith(ext) for ext in 
                   ['.js', '.jsx', '.ts', '.tsx', '.vue', '.html', '.css'])]
        elif domain == DomainProfile.WEB2_BACKEND:
            return [f for f in all_files if any(f.endswith(ext) for ext in 
                   ['.py', '.java', '.go', '.rb', '.php', '.cs'])]
        elif domain == DomainProfile.WEB3_SMART_CONTRACT:
            return [f for f in all_files if f.endswith('.sol')]
        elif domain == DomainProfile.INFRASTRUCTURE:
            return [f for f in all_files if any(f.endswith(ext) for ext in 
                   ['.yml', '.yaml', '.json', '.tf', '.dockerfile'])]
        else:
            return all_files[:20]  # Generic fallback
    
    async def _get_file_contents(self, file_paths: List[str]) -> Dict[str, str]:
        """Get contents of specified files"""
        
        contents = {}
        
        for file_path in file_paths:
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    # Truncate very long files
                    if len(content) > 10000:
                        content = content[:10000] + "\n... [truncated]"
                    contents[file_path] = content
            except Exception as e:
                contents[file_path] = f"Error reading file: {e}"
        
        return contents
    
    def _format_scanner_findings(self, findings: List[Finding]) -> str:
        """Format scanner findings for LLM context"""
        
        if not findings:
            return "No scanner findings available."
        
        formatted = "Scanner Findings:\n"
        for i, finding in enumerate(findings[:10]):  # Limit to top 10
            formatted += f"{i+1}. {finding.title}\n"
            formatted += f"   File: {finding.file}\n"
            formatted += f"   Severity: {finding.severity}\n"
            formatted += f"   Description: {finding.description[:200]}...\n\n"
        
        return formatted
    
    def _parse_llm_response(self, response: str, domain: DomainProfile) -> List[Finding]:
        """Parse LLM response into Finding objects"""
        
        findings = []
        
        try:
            # Try to parse as JSON first
            if response.startswith('{') or response.startswith('['):
                data = json.loads(response)
                if isinstance(data, list):
                    for item in data:
                        finding = self._create_finding_from_dict(item, domain)
                        if finding:
                            findings.append(finding)
                elif isinstance(data, dict) and 'findings' in data:
                    for item in data['findings']:
                        finding = self._create_finding_from_dict(item, domain)
                        if finding:
                            findings.append(finding)
            else:
                # Parse as structured text
                findings = self._parse_text_response(response, domain)
        
        except json.JSONDecodeError:
            # Fallback to text parsing
            findings = self._parse_text_response(response, domain)
        
        return findings
    
    def _create_finding_from_dict(self, data: Dict[str, Any], domain: DomainProfile) -> Finding:
        """Create Finding from dictionary data"""
        
        try:
            # Auto-generate CVSS score
            cvss = self.vulnerability_classifier.auto_score_finding(
                data.get('title', ''),
                data.get('description', ''),
                {'domain': domain.value}
            )
            
            # Create tool evidence
            evidence = ToolEvidence(
                tool_name="llm_auditor",
                rule_id=f"llm_{hash(data.get('title', ''))%10000}",
                rule_name=data.get('title', 'LLM Security Finding'),
                confidence=80,
                raw_output=json.dumps(data)
            )
            
            return Finding(
                id=f"LLM_{hash(data.get('title', ''))%10000}",
                title=data.get('title', 'LLM Security Finding'),
                description=data.get('description', ''),
                severity=cvss.severity,
                category='llm_analysis',
                file=data.get('file', 'unknown'),
                line_number=data.get('line', 1),
                code_snippet="",
                confidence_score=80,
                tool_evidence=[evidence],
                cwe_ids=data.get('cwe', []),
                references=[]
            )
        
        except Exception as e:
            print(f"Error creating finding from dict: {e}")
            return None
    
    def _parse_text_response(self, text: str, domain: DomainProfile) -> List[Finding]:
        """Parse text response into findings"""
        
        findings = []
        
        # Simple text parsing for findings
        lines = text.split('\n')
        current_finding = {}
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('FINDING:') or line.startswith('Finding:'):
                if current_finding:
                    finding = self._create_finding_from_dict(current_finding, domain)
                    if finding:
                        findings.append(finding)
                current_finding = {'title': line.replace('FINDING:', '').replace('Finding:', '').strip()}
            
            elif line.startswith('File:'):
                current_finding['file'] = line.replace('File:', '').strip()
            elif line.startswith('Description:'):
                current_finding['description'] = line.replace('Description:', '').strip()
            elif line.startswith('Recommendation:'):
                current_finding['recommendation'] = line.replace('Recommendation:', '').strip()
        
        # Don't forget the last finding
        if current_finding:
            finding = self._create_finding_from_dict(current_finding, domain)
            if finding:
                findings.append(finding)
        
        return findings
    
    # Domain-specific audit prompts
    def _get_frontend_audit_prompt(self) -> str:
        return """
You are a security auditor specializing in frontend web applications. 
Analyze the provided frontend code for security vulnerabilities.

Focus on:
- Cross-Site Scripting (XSS) vulnerabilities
- Client-side injection attacks
- Insecure data handling
- Authentication and session management issues
- CORS misconfigurations
- Content Security Policy violations
- Sensitive data exposure in client code

Files to analyze:
{files}

Previous scanner findings:
{scanner_findings}

Provide findings in JSON format with title, file, description, recommendation, owasp, and cwe fields.
"""
    
    def _get_backend_audit_prompt(self) -> str:
        return """
You are a security auditor specializing in backend web applications.
Analyze the provided backend code for security vulnerabilities.

Focus on:
- SQL Injection vulnerabilities
- Command injection attacks
- Authentication bypass
- Authorization flaws
- Input validation issues
- Insecure direct object references
- Server-side request forgery (SSRF)
- Insecure deserialization

Files to analyze:
{files}

Previous scanner findings:
{scanner_findings}

Provide findings in JSON format with title, file, description, recommendation, owasp, and cwe fields.
"""
    
    def _get_api_audit_prompt(self) -> str:
        return """
You are a security auditor specializing in API security.
Analyze the provided API code for security vulnerabilities.

Focus on:
- Authentication and authorization flaws
- API endpoint security
- Input validation and sanitization
- Rate limiting and abuse prevention
- Data exposure through APIs
- OWASP API Security Top 10 issues
- JWT security issues

Files to analyze:
{files}

Previous scanner findings:
{scanner_findings}

Provide findings in JSON format with title, file, description, recommendation, owasp, and cwe fields.
"""
    
    def _get_smart_contract_audit_prompt(self) -> str:
        return """
You are a security auditor specializing in smart contract security.
Analyze the provided Solidity code for security vulnerabilities.

Focus on:
- Reentrancy attacks
- Integer overflow/underflow
- Access control issues
- Uninitialized storage pointers
- Delegatecall vulnerabilities
- Front-running attacks
- Gas optimization issues
- Logic errors in financial calculations

Files to analyze:
{files}

Previous scanner findings:
{scanner_findings}

Provide findings in JSON format with title, file, description, recommendation, owasp, and cwe fields.
"""
    
    def _get_defi_audit_prompt(self) -> str:
        return """
You are a security auditor specializing in DeFi protocol security.
Analyze the provided DeFi smart contract code for security vulnerabilities.

Focus on:
- Flash loan attacks
- Price oracle manipulation
- Liquidity pool vulnerabilities
- Governance attacks
- MEV-related issues
- Economic model flaws
- Integration risks with external protocols
- Yield farming security

Files to analyze:
{files}

Previous scanner findings:
{scanner_findings}

Provide findings in JSON format with title, file, description, recommendation, owasp, and cwe fields.
"""
    
    def _get_infrastructure_audit_prompt(self) -> str:
        return """
You are a security auditor specializing in infrastructure security.
Analyze the provided infrastructure code and configuration for security vulnerabilities.

Focus on:
- Container security issues
- Kubernetes misconfigurations
- CI/CD pipeline security
- Secrets management
- Network security configurations
- Infrastructure as Code security
- Cloud security misconfigurations
- Access control policies

Files to analyze:
{files}

Previous scanner findings:
{scanner_findings}

Provide findings in JSON format with title, file, description, recommendation, owasp, and cwe fields.
"""
    
    def _get_generic_audit_prompt(self) -> str:
        return """
You are a security auditor. Analyze the provided code for security vulnerabilities.

Focus on common security issues such as:
- Injection vulnerabilities
- Authentication and authorization flaws
- Sensitive data exposure
- Security misconfigurations
- Insecure components
- Insufficient logging and monitoring

Files to analyze:
{files}

Previous scanner findings:
{scanner_findings}

Provide findings in JSON format with title, file, description, recommendation, owasp, and cwe fields.
"""


class ArchitectureAuditorModule(BaseModule):
    """Audits overall application architecture for security issues"""
    
    def __init__(self, config: ModuleConfig):
        super().__init__(config)
        self.auditor_agent = AuditorAgent(config.config)
        self.vulnerability_classifier = SimpleVulnerabilityClassifier()
    
    async def execute(
        self,
        context: Dict[str, Any],
        workspace_path: str
    ) -> List[Finding]:
        """Audit application architecture"""
        
        # Analyze overall architecture
        architecture_analysis = await self._analyze_architecture(context, workspace_path)
        
        # Generate architectural findings
        findings = self._generate_architectural_findings(architecture_analysis, context)
        
        return findings
    
    def is_applicable(self, context: Dict[str, Any]) -> bool:
        """Architecture audit is applicable to larger codebases"""
        target_files = context.get('target_files', [])
        return len(target_files) > 10  # Only for larger projects
    
    async def _analyze_architecture(self, context: Dict[str, Any], workspace_path: str) -> Dict[str, Any]:
        """Analyze application architecture"""
        
        # Get technology stack
        technologies = context.get('technologies', {})
        
        # Analyze file structure
        file_structure = self._analyze_file_structure(context.get('target_files', []))
        
        # Look for architectural patterns
        patterns = self._detect_architectural_patterns(context)
        
        return {
            'technologies': technologies,
            'file_structure': file_structure,
            'patterns': patterns
        }
    
    def _analyze_file_structure(self, files: List[str]) -> Dict[str, Any]:
        """Analyze file structure for architectural insights"""
        
        structure = {
            'total_files': len(files),
            'directories': set(),
            'file_types': {},
            'depth': 0
        }
        
        for file_path in files:
            # Extract directories
            parts = file_path.split('/')
            structure['depth'] = max(structure['depth'], len(parts))
            
            for i in range(len(parts) - 1):
                structure['directories'].add('/'.join(parts[:i+1]))
            
            # Count file types
            if '.' in parts[-1]:
                ext = '.' + parts[-1].split('.')[-1]
                structure['file_types'][ext] = structure['file_types'].get(ext, 0) + 1
        
        structure['directories'] = list(structure['directories'])
        return structure
    
    def _detect_architectural_patterns(self, context: Dict[str, Any]) -> List[str]:
        """Detect architectural patterns from files and structure"""
        
        patterns = []
        files = context.get('target_files', [])
        
        # Detect common patterns
        file_names = [f.split('/')[-1].lower() for f in files]
        
        if any('controller' in name for name in file_names):
            patterns.append('MVC')
        if any('service' in name for name in file_names):
            patterns.append('Service Layer')
        if any('repository' in name or 'dao' in name for name in file_names):
            patterns.append('Repository Pattern')
        if any('middleware' in name for name in file_names):
            patterns.append('Middleware Pattern')
        if any('model' in name for name in file_names):
            patterns.append('Domain Model')
        
        return patterns
    
    def _generate_architectural_findings(
        self,
        analysis: Dict[str, Any],
        context: Dict[str, Any]
    ) -> List[Finding]:
        """Generate findings based on architectural analysis"""
        
        findings = []
        
        # Check for common architectural security issues
        
        # Missing security layers
        if 'Middleware Pattern' not in analysis['patterns']:
            findings.append(self._create_architectural_finding(
                "Missing Security Middleware Layer",
                "Application lacks centralized security middleware for authentication, authorization, and input validation",
                "Implement security middleware layer to handle cross-cutting security concerns",
                "OWASP-A01"  # Broken Access Control
            ))
        
        # Monolithic architecture concerns
        if analysis['file_structure']['total_files'] > 100 and len(analysis['patterns']) < 3:
            findings.append(self._create_architectural_finding(
                "Monolithic Architecture Security Concerns",
                "Large codebase with minimal architectural patterns may lack proper separation of concerns",
                "Consider implementing microservices architecture or clear layered architecture",
                "OWASP-A04"  # Insecure Design
            ))
        
        # Missing data access layer
        if 'Repository Pattern' not in analysis['patterns'] and any(
            tech in analysis['technologies'].get('languages', [])
            for tech in ['python', 'java', 'csharp']
        ):
            findings.append(self._create_architectural_finding(
                "Direct Database Access Pattern",
                "Application may be using direct database access without proper abstraction layer",
                "Implement repository pattern or ORM to abstract database access and prevent SQL injection",
                "OWASP-A03"  # Injection
            ))
        
        return findings
    
    def _create_architectural_finding(
        self,
        title: str,
        description: str,
        recommendation: str,
        owasp: str
    ) -> Finding:
        """Create an architectural finding"""
        
        # Generate CVSS score for architectural issue
        cvss = self.vulnerability_classifier.auto_score_finding(title, description)
        
        evidence = ToolEvidence(
            tool_name="architecture_auditor",
            rule_id=f"arch_{hash(title)%10000}",
            rule_name=title,
            confidence=70,
            raw_output=f"Architectural analysis finding: {title}"
        )
        
        return Finding(
            id=f"ARCH_{hash(title)%10000}",
            title=title,
            description=description,
            severity=cvss.severity,
            category='architecture',
            file="architecture",
            line_number=1,
            code_snippet="",
            confidence_score=70,
            tool_evidence=[evidence],
            cwe_ids=[],
            references=[]
        )


# Auditor module factory
def create_auditor_modules() -> List[BaseModule]:
    """Create and configure auditor modules"""
    
    modules = []
    
    # LLM Web2 Frontend Auditor
    frontend_auditor_config = ModuleConfig(
        name="llm_frontend_auditor",
        module_type=ModuleType.AUDITOR,
        domain_profiles=[DomainProfile.WEB2_FRONTEND],
        priority=60,
        dependencies=["semgrep_scanner"],
        config={}
    )
    modules.append(LLMAuditorModule(frontend_auditor_config))
    
    # LLM Web2 Backend Auditor
    backend_auditor_config = ModuleConfig(
        name="llm_backend_auditor",
        module_type=ModuleType.AUDITOR,
        domain_profiles=[DomainProfile.WEB2_BACKEND, DomainProfile.WEB2_API],
        priority=60,
        dependencies=["semgrep_scanner"],
        config={}
    )
    modules.append(LLMAuditorModule(backend_auditor_config))
    
    # LLM Web3 Smart Contract Auditor
    web3_auditor_config = ModuleConfig(
        name="llm_web3_auditor", 
        module_type=ModuleType.AUDITOR,
        domain_profiles=[
            DomainProfile.WEB3_SMART_CONTRACT,
            DomainProfile.WEB3_DEFI,
            DomainProfile.WEB3_NFT,
            DomainProfile.WEB3_DAO
        ],
        priority=60,
        dependencies=["slither_scanner"],
        config={}
    )
    modules.append(LLMAuditorModule(web3_auditor_config))
    
    # Architecture Auditor
    arch_auditor_config = ModuleConfig(
        name="architecture_auditor",
        module_type=ModuleType.AUDITOR,
        domain_profiles=list(DomainProfile),  # Applicable to all domains
        priority=40,
        dependencies=["semgrep_scanner"],
        config={}
    )
    modules.append(ArchitectureAuditorModule(arch_auditor_config))
    
    return modules