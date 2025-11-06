"""
Planner Agent - Orchestrates the security review workflow
Routes tasks to appropriate agents based on repository analysis
"""

from typing import Dict, List, Optional, Any
from pathlib import Path
import asyncio

try:
    from langgraph.prebuilt import create_agent_executor
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
try:
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.tools import BaseTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field

from ..schemas.findings import PlanningResult, RepositoryAnalysis
from .repo import RepoAgent
from .scanner import ScannerAgent
from .auditor import AuditorAgent
from .refactor import RefactorAgent
from .reporter import ReporterAgent


class PlannerAgent:
    """
    Orchestrates the security review workflow by analyzing repository
    structure and routing tasks to appropriate specialized agents
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.llm = ChatOpenAI(
            model=config.get("llm.model", "gpt-4"),
            temperature=0.1,
            max_tokens=config.get("llm.max_tokens", 2000)
        )
        
        # Initialize specialized agents
        self.repo_agent = RepoAgent(config)
        self.scanner_agent = ScannerAgent(config)
        self.auditor_agent = AuditorAgent(config)
        self.refactor_agent = RefactorAgent(config)
        self.reporter_agent = ReporterAgent(config)
        
        self.prompt = self._create_prompt()
    
    def _create_prompt(self) -> ChatPromptTemplate:
        """Create planning prompt template"""
        return ChatPromptTemplate.from_messages([
            ("system", """You are a Senior Security Architect planning a comprehensive code security review.

Your role is to:
1. Analyze repository structure and technology stack
2. Identify security-relevant surfaces and entry points
3. Plan appropriate scanning and audit strategies
4. Route tasks to specialized agents
5. Ensure comprehensive coverage

Repository Context:
- Path: {repo_path}
- Files: {file_count} files
- Stack: {tech_stack}
- Profiles: {domain_profiles}

Analysis Mode: {mode}
- quick: Essential security checks, automated tools first
- deep: Thorough manual review, cross-file analysis
- redteam: Adversarial perspective, exploit chains
- refactor: Security tightening focus

CRITICAL: You must be systematic and evidence-based. Every recommendation
must cite specific files, functions, or patterns. No hallucinations.

Plan the review workflow and output a structured plan."""),
            
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ])
    
    async def plan_review(
        self, 
        repo_path: str, 
        mode: str = "quick",
        domain_profiles: List[str] = None,
        exclude_patterns: List[str] = None
    ) -> PlanningResult:
        """
        Analyze repository and create comprehensive review plan
        
        Args:
            repo_path: Path to repository to analyze
            mode: Analysis mode (quick|deep|redteam|refactor)
            domain_profiles: Web2/Web3 domain profiles to apply
            exclude_patterns: Files/directories to exclude
            
        Returns:
            PlanningResult with workflow plan and task routing
        """
        
        # Step 1: Repository Analysis
        repo_analysis = await self.repo_agent.analyze_repository(
            repo_path=repo_path,
            exclude_patterns=exclude_patterns or []
        )
        
        # Step 2: Stack Detection and Surface Mapping
        tech_stack = self._detect_tech_stack(repo_analysis)
        security_surfaces = self._identify_security_surfaces(repo_analysis, tech_stack)
        
        # Step 3: Create Review Plan
        plan = await self._create_review_plan(
            repo_analysis=repo_analysis,
            tech_stack=tech_stack,
            security_surfaces=security_surfaces,
            mode=mode,
            domain_profiles=domain_profiles or []
        )
        
        return plan
    
    def _detect_tech_stack(self, repo_analysis: RepositoryAnalysis) -> Dict[str, Any]:
        """Detect technology stack from repository analysis"""
        stack = {
            "languages": [],
            "frameworks": [],
            "build_tools": [],
            "package_managers": [],
            "infrastructure": [],
            "blockchain": []
        }
        
        # Language detection from file extensions
        for file_info in repo_analysis.files:
            ext = Path(file_info.path).suffix.lower()
            
            if ext in ['.py']:
                if 'python' not in stack["languages"]:
                    stack["languages"].append('python')
            elif ext in ['.js', '.ts', '.jsx', '.tsx']:
                if 'javascript' not in stack["languages"]:
                    stack["languages"].append('javascript')
            elif ext in ['.sol']:
                if 'solidity' not in stack["languages"]:
                    stack["languages"].append('solidity')
                    stack["blockchain"].append('ethereum')
            elif ext in ['.rs']:
                if 'rust' not in stack["languages"]:
                    stack["languages"].append('rust')
            elif ext in ['.go']:
                if 'go' not in stack["languages"]:
                    stack["languages"].append('go')
        
        # Framework and tool detection from filenames
        for file_info in repo_analysis.files:
            filename = Path(file_info.path).name.lower()
            
            if filename == 'package.json':
                stack["package_managers"].append('npm')
            elif filename == 'requirements.txt' or filename == 'pyproject.toml':
                stack["package_managers"].append('pip')
            elif filename == 'cargo.toml':
                stack["package_managers"].append('cargo')
            elif filename == 'foundry.toml':
                stack["build_tools"].append('foundry')
                stack["blockchain"].append('ethereum')
            elif filename == 'hardhat.config.js':
                stack["build_tools"].append('hardhat')
                stack["blockchain"].append('ethereum')
            elif filename == 'dockerfile':
                stack["infrastructure"].append('docker')
            elif filename.endswith('.yaml') or filename.endswith('.yml'):
                if 'kubernetes' in file_info.content or 'k8s' in file_info.content:
                    stack["infrastructure"].append('kubernetes')
        
        return stack
    
    def _identify_security_surfaces(
        self, 
        repo_analysis: RepositoryAnalysis, 
        tech_stack: Dict[str, Any]
    ) -> Dict[str, List[str]]:
        """Identify security-relevant attack surfaces"""
        surfaces = {
            "api_endpoints": [],
            "authentication": [],
            "authorization": [],
            "data_handling": [],
            "external_calls": [],
            "crypto_operations": [],
            "file_operations": [],
            "network_operations": [],
            "smart_contracts": [],
            "bridge_operations": [],
            "consensus_logic": []
        }
        
        # TODO: Implement surface detection logic
        # This would analyze code patterns to identify:
        # - HTTP endpoints and routes
        # - Authentication/authorization logic
        # - Database operations
        # - External API calls
        # - Cryptographic operations
        # - File I/O operations
        # - Smart contract functions
        # - Bridge logic
        # - Consensus mechanisms
        
        return surfaces
    
    async def _create_review_plan(
        self,
        repo_analysis: RepositoryAnalysis,
        tech_stack: Dict[str, Any],
        security_surfaces: Dict[str, List[str]],
        mode: str,
        domain_profiles: List[str]
    ) -> PlanningResult:
        """Create detailed review plan using LLM reasoning"""
        
        # Prepare context for LLM
        context = {
            "repo_path": repo_analysis.repo_path,
            "file_count": len(repo_analysis.files),
            "tech_stack": tech_stack,
            "domain_profiles": domain_profiles,
            "mode": mode,
            "security_surfaces": security_surfaces
        }
        
        # TODO: Use LLM to generate intelligent plan
        # For now, create a basic plan structure
        
        plan = PlanningResult(
            repo_path=repo_analysis.repo_path,
            mode=mode,
            tech_stack=tech_stack,
            domain_profiles=domain_profiles,
            phases=[
                {
                    "name": "Repository Mapping",
                    "agent": "repo",
                    "tasks": ["file_enumeration", "dependency_analysis", "architecture_mapping"],
                    "priority": 1
                },
                {
                    "name": "Automated Scanning", 
                    "agent": "scanner",
                    "tasks": self._select_scanners(tech_stack),
                    "priority": 2
                },
                {
                    "name": "Manual Code Audit",
                    "agent": "auditor", 
                    "tasks": self._select_audit_focus(security_surfaces, mode),
                    "priority": 3
                },
                {
                    "name": "Security Tightening",
                    "agent": "refactor",
                    "tasks": ["remove_dead_code", "restrict_permissions", "simplify_complex"],
                    "priority": 4
                },
                {
                    "name": "Report Generation",
                    "agent": "reporter",
                    "tasks": ["compile_findings", "generate_reports", "create_visualizations"],
                    "priority": 5
                }
            ],
            estimated_duration="30-60 minutes" if mode == "quick" else "2-4 hours"
        )
        
        return plan
    
    def _select_scanners(self, tech_stack: Dict[str, Any]) -> List[str]:
        """Select appropriate scanners based on technology stack"""
        scanners = ["gitleaks"]  # Always scan for secrets
        
        if 'python' in tech_stack["languages"]:
            scanners.extend(["bandit", "semgrep"])
        
        if 'javascript' in tech_stack["languages"]:
            scanners.extend(["semgrep", "eslint-security"])
        
        if 'solidity' in tech_stack["languages"]:
            scanners.extend(["slither", "mythril"])
        
        if 'rust' in tech_stack["languages"]:
            scanners.append("cargo-audit")
        
        if 'go' in tech_stack["languages"]:
            scanners.append("gosec")
        
        return scanners
    
    def _select_audit_focus(
        self, 
        security_surfaces: Dict[str, List[str]], 
        mode: str
    ) -> List[str]:
        """Select audit focus areas based on surfaces and mode"""
        focus_areas = []
        
        if security_surfaces["api_endpoints"]:
            focus_areas.append("api_security_review")
        
        if security_surfaces["authentication"]:
            focus_areas.append("auth_flow_analysis")
        
        if security_surfaces["smart_contracts"]:
            focus_areas.extend(["reentrancy_analysis", "overflow_analysis", "access_control"])
        
        if mode == "deep":
            focus_areas.extend(["cross_file_analysis", "business_logic_review"])
        elif mode == "redteam":
            focus_areas.extend(["exploit_chain_analysis", "privilege_escalation"])
        
        return focus_areas
    
    async def execute_plan(self, plan: PlanningResult) -> Dict[str, Any]:
        """Execute the planned review workflow"""
        results = {}
        
        for phase in sorted(plan.phases, key=lambda p: p["priority"]):
            print(f"[*] Executing phase: {phase['name']}")
            
            agent_name = phase["agent"]
            tasks = phase["tasks"]
            
            if agent_name == "repo":
                phase_result = await self.repo_agent.execute_tasks(tasks)
            elif agent_name == "scanner":
                phase_result = await self.scanner_agent.execute_tasks(tasks)
            elif agent_name == "auditor":
                phase_result = await self.auditor_agent.execute_tasks(tasks)
            elif agent_name == "refactor":
                phase_result = await self.refactor_agent.execute_tasks(tasks)
            elif agent_name == "reporter":
                phase_result = await self.reporter_agent.execute_tasks(tasks)
            else:
                print(f"[!] Unknown agent: {agent_name}")
                continue
            
            results[phase["name"]] = phase_result
        
        return results