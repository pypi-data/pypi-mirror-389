"""
Scanner Agent Implementation
Coordinates execution of automated security scanning tools
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
try:
    from langgraph.prebuilt import create_agent_executor
    AGENT_EXECUTOR_AVAILABLE = True
except ImportError:
    AGENT_EXECUTOR_AVAILABLE = False
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import BaseMessage
try:
    from langchain_core.tools import StructuredTool
except ImportError:
    # Fallback for older versions
    StructuredTool = None

from ..tools.base import SecurityScannerBase as SecurityTool
from ..tools.semgrep import SemgrepScanner as SemgrepTool
from ..tools.gitleaks import GitleaksScanner as GitleaksTool
from ..tools.slither import SlitherScanner as SlitherTool
from ..tools.bandit import BanditScanner as BanditTool
from ..tools.gosec import GosecScanner as GosecTool
from ..tools.npm_audit import NpmAuditScanner as NpmAuditTool
from ..schemas.findings import Finding, AnalysisContext
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ScannerAgent(BaseAgent):
    """
    Scanner Agent coordinates execution of multiple security scanning tools
    and normalizes their outputs into standardized findings.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        self.tools_registry = self._initialize_tools()
        self.agent_executor = self._create_agent_executor()
        
    def _initialize_tools(self) -> Dict[str, SecurityTool]:
        """Initialize available security tools"""
        tools = {}
        
        # Static analysis tools
        try:
            tools['semgrep'] = SemgrepTool(self.config.get('semgrep', {}))
        except Exception as e:
            logger.warning(f"Failed to initialize Semgrep: {e}")
            
        try:
            tools['bandit'] = BanditTool(self.config.get('bandit', {}))
        except Exception as e:
            logger.warning(f"Failed to initialize Bandit: {e}")
            
        try:
            tools['gosec'] = GosecTool(self.config.get('gosec', {}))
        except Exception as e:
            logger.warning(f"Failed to initialize Gosec: {e}")
        
        # Secret detection
        try:
            tools['gitleaks'] = GitleaksTool(self.config.get('gitleaks', {}))
        except Exception as e:
            logger.warning(f"Failed to initialize Gitleaks: {e}")
            
        # Smart contract analysis
        try:
            tools['slither'] = SlitherTool(self.config.get('slither', {}))
        except Exception as e:
            logger.warning(f"Failed to initialize Slither: {e}")
            
        # Dependency scanning
        try:
            tools['npm_audit'] = NpmAuditTool(self.config.get('npm_audit', {}))
        except Exception as e:
            logger.warning(f"Failed to initialize NPM Audit: {e}")
            
        return tools
    
    def _create_agent_executor(self):
        """Create LangChain agent executor for scanner coordination"""
        
        if not AGENT_EXECUTOR_AVAILABLE:
            # Fallback to simple coordination without LangChain agents
            return None
        
        # Create tools for LangChain
        langchain_tools = []
        
        if StructuredTool is None:
            logger.warning("StructuredTool not available, skipping tool creation")
            return None
        
        for tool_name, tool in self.tools_registry.items():
            langchain_tool = StructuredTool.from_function(
                func=self._create_tool_wrapper(tool),
                name=f"run_{tool_name}",
                description=f"Run {tool_name} security scanner on the target path"
            )
            langchain_tools.append(langchain_tool)
        
        # Create LLM using base agent method
        llm = self.create_llm()
        
        # Create agent executor using new API
        try:
            return create_agent_executor(llm, langchain_tools, verbose=True)
        except Exception as e:
            logger.warning(f"Failed to create agent executor: {e}")
            return None
    
    def _create_tool_wrapper(self, tool: SecurityTool):
        """Create wrapper function for LangChain tool"""
        async def tool_wrapper(target_path: str) -> str:
            try:
                findings = await tool.scan(target_path, {})
                return f"Found {len(findings)} issues with {tool.__class__.__name__}"
            except Exception as e:
                return f"Error running {tool.__class__.__name__}: {str(e)}"
        return tool_wrapper
    
    async def execute_scanners(self, context: AnalysisContext) -> List[Finding]:
        """
        Main method to execute security scanners based on analysis context
        """
        logger.info(f"Starting scanner execution for {context.workspace_path}")
        
        # Determine applicable tools based on context
        applicable_tools = self._select_applicable_tools(context)
        
        if not applicable_tools:
            logger.warning("No applicable security tools found for this context")
            return []
        
        # Execute tools in parallel for performance
        tasks = []
        for tool_name in applicable_tools:
            tool = self.tools_registry[tool_name]
            task = self._run_tool_with_retry(tool, context.workspace_path)
            tasks.append(task)
        
        # Wait for all scans to complete
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Consolidate findings
        all_findings = []
        for i, result in enumerate(results):
            tool_name = applicable_tools[i]
            
            if isinstance(result, Exception):
                logger.error(f"Tool {tool_name} failed: {result}")
                continue
                
            if isinstance(result, list):
                all_findings.extend(result)
                logger.info(f"Tool {tool_name} found {len(result)} findings")
        
        logger.info(f"Scanner execution complete. Total findings: {len(all_findings)}")
        return all_findings
    
    def _select_applicable_tools(self, context: AnalysisContext) -> List[str]:
        """
        Select which tools to run based on analysis context
        """
        applicable_tools = []
        
        # Always run secret detection
        if 'gitleaks' in self.tools_registry:
            applicable_tools.append('gitleaks')
        
        # Language-specific tools
        for tech in context.technologies:
            if tech.language == 'python':
                if 'bandit' in self.tools_registry:
                    applicable_tools.append('bandit')
                    
            elif tech.language == 'go':
                if 'gosec' in self.tools_registry:
                    applicable_tools.append('gosec')
                    
            elif tech.language == 'solidity':
                if 'slither' in self.tools_registry:
                    applicable_tools.append('slither')
                    
            elif tech.language in ['javascript', 'typescript']:
                if 'npm_audit' in self.tools_registry:
                    applicable_tools.append('npm_audit')
        
        # Always run Semgrep for general static analysis
        if 'semgrep' in self.tools_registry:
            applicable_tools.append('semgrep')
        
        return list(set(applicable_tools))  # Remove duplicates
    
    async def _run_tool_with_retry(self, tool: SecurityTool, target_path: str, max_retries: int = 3) -> List[Finding]:
        """
        Run a security tool with retry logic
        """
        for attempt in range(max_retries):
            try:
                findings = await tool.scan(target_path, {})
                return findings
            except Exception as e:
                logger.warning(f"Tool {tool.__class__.__name__} attempt {attempt + 1} failed: {e}")
                if attempt == max_retries - 1:
                    raise
                await asyncio.sleep(2 ** attempt)  # Exponential backoff
        
        return []
    
    async def run_specific_tool(self, tool_name: str, target_path: str, config: Optional[Dict] = None) -> List[Finding]:
        """
        Run a specific security tool
        """
        if tool_name not in self.tools_registry:
            raise ValueError(f"Tool {tool_name} not available. Available tools: {list(self.tools_registry.keys())}")
        
        tool = self.tools_registry[tool_name]
        tool_config = config or {}
        
        logger.info(f"Running {tool_name} on {target_path}")
        findings = await tool.scan(target_path, tool_config)
        logger.info(f"{tool_name} completed with {len(findings)} findings")
        
        return findings
    
    def get_available_tools(self) -> List[str]:
        """Get list of available security tools"""
        return list(self.tools_registry.keys())
    
    def get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """Get information about a specific tool"""
        if tool_name not in self.tools_registry:
            return {}
        
        tool = self.tools_registry[tool_name]
        return {
            'name': tool_name,
            'class': tool.__class__.__name__,
            'description': getattr(tool, 'description', 'No description available'),
            'supported_languages': getattr(tool, 'supported_languages', []),
            'is_available': tool.is_available()
        }