"""
Refactor Agent Implementation
Generates security hardening recommendations and remediation guidance
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional, Tuple
try:
    from langgraph.prebuilt import create_agent_executor
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
try:
    from langchain_core.tools import StructuredTool
except ImportError:
    StructuredTool = None

from ..schemas.findings import Finding, AnalysisContext, RemediationRecommendation, SecurityHardening
from .base import BaseAgent

logger = logging.getLogger(__name__)

class RefactorAgent(BaseAgent):
    """
    Refactor Agent generates security hardening recommendations,
    remediation guidance, and code improvement suggestions.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.memory = ConversationBufferWindowMemory(k=10, return_messages=True)
        self.agent_executor = self._create_agent_executor()
        
        # Security hardening patterns
        self.hardening_patterns = self._load_hardening_patterns()
        
    def _load_hardening_patterns(self) -> Dict[str, Dict[str, Any]]:
        """Load security hardening patterns and best practices"""
        return {
            'python': {
                'input_validation': {
                    'description': 'Implement comprehensive input validation',
                    'patterns': ['marshmallow', 'pydantic', 'cerberus'],
                    'examples': ['from marshmallow import Schema, fields, validate']
                },
                'secure_headers': {
                    'description': 'Add security headers to HTTP responses',
                    'patterns': ['flask-talisman', 'django-security'],
                    'examples': ['Talisman(app, force_https=True)']
                },
                'authentication': {
                    'description': 'Implement secure authentication',
                    'patterns': ['flask-login', 'passlib', 'bcrypt'],
                    'examples': ['from passlib.hash import bcrypt']
                }
            },
            'javascript': {
                'xss_protection': {
                    'description': 'Implement XSS protection',
                    'patterns': ['DOMPurify', 'xss-filters', 'validator'],
                    'examples': ['import DOMPurify from "dompurify"']
                },
                'csrf_protection': {
                    'description': 'Add CSRF protection',
                    'patterns': ['csurf', 'csrf-token'],
                    'examples': ['app.use(csrf())']
                },
                'secure_storage': {
                    'description': 'Use secure client-side storage',
                    'patterns': ['secure-ls', 'crypto-js'],
                    'examples': ['const secureStorage = new SecureLS()']
                }
            },
            'solidity': {
                'reentrancy_protection': {
                    'description': 'Implement reentrancy guards',
                    'patterns': ['ReentrancyGuard', 'checks-effects-interactions'],
                    'examples': ['modifier nonReentrant() { require(!locked); locked = true; _; locked = false; }']
                },
                'access_control': {
                    'description': 'Implement proper access controls',
                    'patterns': ['AccessControl', 'Ownable', 'Role-based'],
                    'examples': ['import "@openzeppelin/contracts/access/AccessControl.sol"']
                },
                'safe_math': {
                    'description': 'Use safe arithmetic operations',
                    'patterns': ['SafeMath', 'checked arithmetic'],
                    'examples': ['using SafeMath for uint256']
                }
            }
        }
    
    def _create_agent_executor(self) -> Any:
        """Create LangChain agent executor for refactoring recommendations"""
        
        tools = [
            StructuredTool.from_function(
                func=self._generate_remediation_code,
                name="generate_remediation_code",
                description="Generate specific code fixes for security vulnerabilities"
            ),
            StructuredTool.from_function(
                func=self._suggest_architecture_improvements,
                name="suggest_architecture_improvements",
                description="Suggest architecture-level security improvements"
            ),
            StructuredTool.from_function(
                func=self._recommend_security_libraries,
                name="recommend_security_libraries",
                description="Recommend security libraries and frameworks"
            ),
            StructuredTool.from_function(
                func=self._generate_security_tests,
                name="generate_security_tests",
                description="Generate security test cases for vulnerabilities"
            ),
            StructuredTool.from_function(
                func=self._create_security_policies,
                name="create_security_policies",
                description="Create security policies and configuration"
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert security architect and code reviewer with expertise in:
            - Secure coding practices across multiple languages and frameworks
            - Architecture design patterns for security
            - Remediation strategies for common vulnerabilities
            - Security testing and validation approaches
            - Compliance frameworks and security standards
            
            Your role is to:
            1. Generate specific, actionable remediation code for vulnerabilities
            2. Recommend architecture improvements for security
            3. Suggest security libraries and frameworks
            4. Create security test cases and validation approaches
            5. Provide compliance guidance and best practices
            
            Always provide practical, implementable solutions with code examples.
            Consider performance, maintainability, and security trade-offs.
            """),
            ("user", "Generate security hardening recommendations for:\n{context}"),
            MessagesPlaceholder(variable_name="chat_history"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create LLM using base agent method
        llm = self.create_llm()
        
        llm_with_tools = llm.bind_functions(tools)
        
        agent = (
            {
                "context": lambda x: x["context"],
                "chat_history": lambda x: x.get("chat_history", []),
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        )
        
        if LANGCHAIN_AVAILABLE:
            try:
                return create_agent_executor(llm, tools, verbose=True)
            except Exception as e:
                logging.warning(f"Failed to create agent executor: {e}")
        return None
    
    async def generate_remediation_recommendations(self, findings: List[Finding], context: AnalysisContext) -> List[RemediationRecommendation]:
        """
        Generate comprehensive remediation recommendations for security findings
        """
        logger.info(f"Generating remediation recommendations for {len(findings)} findings")
        
        recommendations = []
        
        # Group findings by type for efficient processing
        findings_by_type = self._group_findings_by_type(findings)
        
        for vulnerability_type, type_findings in findings_by_type.items():
            # Generate type-specific recommendations
            type_recommendations = await self._generate_type_recommendations(
                vulnerability_type, type_findings, context
            )
            recommendations.extend(type_recommendations)
        
        # Generate architecture-level recommendations
        arch_recommendations = await self._generate_architecture_recommendations(findings, context)
        recommendations.extend(arch_recommendations)
        
        # Generate process improvements
        process_recommendations = await self._generate_process_recommendations(findings, context)
        recommendations.extend(process_recommendations)
        
        logger.info(f"Generated {len(recommendations)} remediation recommendations")
        return recommendations
    
    async def generate_security_hardening_plan(self, context: AnalysisContext) -> SecurityHardening:
        """
        Generate comprehensive security hardening plan for the application
        """
        logger.info("Generating security hardening plan")
        
        # Analyze current security posture
        security_assessment = await self._assess_security_posture(context)
        
        # Generate hardening recommendations by category
        hardening_plan = SecurityHardening(
            authentication=await self._generate_authentication_hardening(context),
            authorization=await self._generate_authorization_hardening(context),
            input_validation=await self._generate_input_validation_hardening(context),
            output_encoding=await self._generate_output_encoding_hardening(context),
            cryptography=await self._generate_cryptography_hardening(context),
            infrastructure=await self._generate_infrastructure_hardening(context),
            monitoring=await self._generate_monitoring_hardening(context),
            dependencies=await self._generate_dependency_hardening(context)
        )
        
        return hardening_plan
    
    async def _generate_type_recommendations(self, vulnerability_type: str, findings: List[Finding], context: AnalysisContext) -> List[RemediationRecommendation]:
        """Generate recommendations for a specific vulnerability type"""
        
        recommendations = []
        
        # Get the primary language for context
        primary_language = self._get_primary_language(context)
        
        # Generate remediation prompt
        remediation_prompt = f"""
        Generate specific remediation recommendations for {vulnerability_type} vulnerabilities:
        
        Findings count: {len(findings)}
        Primary language: {primary_language}
        Technology stack: {[tech.name for tech in context.technologies]}
        
        Sample finding:
        {findings[0].description if findings else 'No specific finding details'}
        
        Provide:
        1. Immediate fix with code examples
        2. Long-term prevention strategies
        3. Testing approaches
        4. Implementation priority
        """
        
        try:
            result = await self.agent_executor.ainvoke({
                "context": remediation_prompt
            })
            
            # Parse recommendations from LLM output
            recommendation = RemediationRecommendation(
                vulnerability_type=vulnerability_type,
                findings_count=len(findings),
                immediate_actions=self._extract_immediate_actions(result["output"]),
                long_term_improvements=self._extract_long_term_improvements(result["output"]),
                code_examples=self._extract_code_examples(result["output"]),
                testing_approach=self._extract_testing_approach(result["output"]),
                priority="high" if any(f.severity == "critical" for f in findings) else "medium",
                effort_estimate=self._estimate_effort(findings),
                implementation_order=len(recommendations) + 1
            )
            
            recommendations.append(recommendation)
            
        except Exception as e:
            logger.error(f"Error generating recommendations for {vulnerability_type}: {e}")
        
        return recommendations
    
    async def _generate_architecture_recommendations(self, findings: List[Finding], context: AnalysisContext) -> List[RemediationRecommendation]:
        """Generate architecture-level security recommendations"""
        
        architecture_prompt = f"""
        Analyze the overall security architecture and recommend improvements:
        
        Total findings: {len(findings)}
        Critical findings: {len([f for f in findings if f.severity == 'critical'])}
        Technologies: {[tech.name for tech in context.technologies]}
        File structure: {len(context.file_tree)} files
        
        Focus on:
        1. Security architecture patterns
        2. Defense in depth strategies
        3. Security boundaries and controls
        4. Monitoring and logging improvements
        5. Infrastructure security
        """
        
        try:
            result = await self.agent_executor.ainvoke({
                "context": architecture_prompt
            })
            
            recommendation = RemediationRecommendation(
                vulnerability_type="architecture",
                findings_count=len(findings),
                immediate_actions=self._extract_immediate_actions(result["output"]),
                long_term_improvements=self._extract_long_term_improvements(result["output"]),
                code_examples=self._extract_code_examples(result["output"]),
                testing_approach=self._extract_testing_approach(result["output"]),
                priority="medium",
                effort_estimate="high",
                implementation_order=999  # Lower priority than specific fixes
            )
            
            return [recommendation]
            
        except Exception as e:
            logger.error(f"Error generating architecture recommendations: {e}")
            return []
    
    def _generate_remediation_code(self, vulnerability_type: str, code_context: str, language: str) -> str:
        """Tool function: Generate specific remediation code"""
        
        # Get hardening patterns for the language
        patterns = self.hardening_patterns.get(language, {})
        
        if vulnerability_type.lower() in patterns:
            pattern = patterns[vulnerability_type.lower()]
            return f"""
            Remediation for {vulnerability_type}:
            
            Description: {pattern['description']}
            Recommended libraries: {', '.join(pattern['patterns'])}
            
            Example implementation:
            {pattern['examples'][0] if pattern['examples'] else 'No example available'}
            """
        
        return f"Generic remediation guidance for {vulnerability_type} in {language}"
    
    def _suggest_architecture_improvements(self, current_architecture: str, security_issues: str) -> str:
        """Tool function: Suggest architecture improvements"""
        return f"Architecture improvements for: {current_architecture}"
    
    def _recommend_security_libraries(self, language: str, vulnerability_types: List[str]) -> str:
        """Tool function: Recommend security libraries"""
        
        recommendations = []
        patterns = self.hardening_patterns.get(language, {})
        
        for vuln_type in vulnerability_types:
            if vuln_type in patterns:
                pattern = patterns[vuln_type]
                recommendations.append(f"{vuln_type}: {', '.join(pattern['patterns'])}")
        
        return "\n".join(recommendations)
    
    def _generate_security_tests(self, vulnerability_type: str, code_context: str) -> str:
        """Tool function: Generate security test cases"""
        return f"Security test cases for {vulnerability_type}"
    
    def _create_security_policies(self, organization_context: str, compliance_requirements: List[str]) -> str:
        """Tool function: Create security policies"""
        return f"Security policies for compliance: {', '.join(compliance_requirements)}"
    
    def _group_findings_by_type(self, findings: List[Finding]) -> Dict[str, List[Finding]]:
        """Group findings by vulnerability type"""
        groups = {}
        for finding in findings:
            category = finding.category or "general"
            if category not in groups:
                groups[category] = []
            groups[category].append(finding)
        return groups
    
    def _get_primary_language(self, context: AnalysisContext) -> str:
        """Get the primary programming language from context"""
        if context.technologies:
            return context.technologies[0].language
        return "unknown"
    
    def _extract_immediate_actions(self, text: str) -> List[str]:
        """Extract immediate actions from LLM output"""
        # Simple extraction - in production, use more sophisticated parsing
        lines = text.split('\n')
        actions = []
        
        for line in lines:
            if 'immediate' in line.lower() or 'fix' in line.lower():
                actions.append(line.strip())
        
        return actions[:5]  # Limit to top 5
    
    def _extract_long_term_improvements(self, text: str) -> List[str]:
        """Extract long-term improvements from LLM output"""
        lines = text.split('\n')
        improvements = []
        
        for line in lines:
            if 'long-term' in line.lower() or 'improvement' in line.lower():
                improvements.append(line.strip())
        
        return improvements[:5]
    
    def _extract_code_examples(self, text: str) -> List[str]:
        """Extract code examples from LLM output"""
        import re
        
        # Find code blocks
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', text, re.DOTALL)
        return code_blocks[:3]  # Limit to 3 examples
    
    def _extract_testing_approach(self, text: str) -> str:
        """Extract testing approach from LLM output"""
        lines = text.split('\n')
        
        for line in lines:
            if 'test' in line.lower():
                return line.strip()
        
        return "No specific testing approach provided"
    
    def _estimate_effort(self, findings: List[Finding]) -> str:
        """Estimate implementation effort based on findings"""
        critical_count = len([f for f in findings if f.severity == "critical"])
        high_count = len([f for f in findings if f.severity == "high"])
        
        if critical_count > 5 or high_count > 10:
            return "high"
        elif critical_count > 2 or high_count > 5:
            return "medium"
        else:
            return "low"
    
    async def _assess_security_posture(self, context: AnalysisContext) -> Dict[str, Any]:
        """Assess current security posture"""
        return {
            'authentication': 'weak',
            'authorization': 'missing',
            'input_validation': 'insufficient',
            'cryptography': 'weak'
        }
    
    async def _generate_authentication_hardening(self, context: AnalysisContext) -> List[str]:
        """Generate authentication hardening recommendations"""
        return [
            "Implement multi-factor authentication",
            "Use secure password hashing (bcrypt/Argon2)",
            "Add account lockout protection",
            "Implement session management security"
        ]
    
    async def _generate_authorization_hardening(self, context: AnalysisContext) -> List[str]:
        """Generate authorization hardening recommendations"""
        return [
            "Implement role-based access control (RBAC)",
            "Add resource-level permissions",
            "Implement principle of least privilege",
            "Add authorization testing"
        ]
    
    async def _generate_input_validation_hardening(self, context: AnalysisContext) -> List[str]:
        """Generate input validation hardening recommendations"""
        return [
            "Implement comprehensive input validation",
            "Use whitelist-based validation",
            "Add input sanitization",
            "Implement rate limiting"
        ]
    
    async def _generate_output_encoding_hardening(self, context: AnalysisContext) -> List[str]:
        """Generate output encoding hardening recommendations"""
        return [
            "Implement context-aware output encoding",
            "Use templating engines with auto-escaping",
            "Add Content Security Policy (CSP)",
            "Implement XSS protection headers"
        ]
    
    async def _generate_cryptography_hardening(self, context: AnalysisContext) -> List[str]:
        """Generate cryptography hardening recommendations"""
        return [
            "Use strong encryption algorithms (AES-256)",
            "Implement proper key management",
            "Use secure random number generation",
            "Add certificate pinning"
        ]
    
    async def _generate_infrastructure_hardening(self, context: AnalysisContext) -> List[str]:
        """Generate infrastructure hardening recommendations"""
        return [
            "Enable HTTPS with proper TLS configuration",
            "Implement security headers",
            "Use secure container configurations",
            "Add network security controls"
        ]
    
    async def _generate_monitoring_hardening(self, context: AnalysisContext) -> List[str]:
        """Generate monitoring hardening recommendations"""
        return [
            "Implement security event logging",
            "Add intrusion detection system (IDS)",
            "Implement security monitoring dashboards",
            "Add automated alert systems"
        ]
    
    async def _generate_dependency_hardening(self, context: AnalysisContext) -> List[str]:
        """Generate dependency hardening recommendations"""
        return [
            "Implement automated dependency scanning",
            "Use dependency pinning and lock files",
            "Add supply chain security controls",
            "Implement regular dependency updates"
        ]
    
    async def _generate_process_recommendations(self, findings: List[Finding], context: AnalysisContext) -> List[RemediationRecommendation]:
        """Generate process improvement recommendations"""
        
        process_recommendation = RemediationRecommendation(
            vulnerability_type="process_improvement",
            findings_count=len(findings),
            immediate_actions=[
                "Integrate security scanning into CI/CD pipeline",
                "Establish security code review process",
                "Implement security training for developers"
            ],
            long_term_improvements=[
                "Establish secure development lifecycle (SDL)",
                "Implement regular penetration testing",
                "Create security champion program",
                "Establish incident response procedures"
            ],
            code_examples=[],
            testing_approach="Implement security testing at all SDLC phases",
            priority="medium",
            effort_estimate="medium",
            implementation_order=1000
        )
        
        return [process_recommendation]