"""
Base Agent Implementation
Provides common functionality for all SecureCLI agents
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

# LangChain imports
try:
    from langgraph.prebuilt import create_agent_executor
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import BaseMessage
    from langchain_core.tools import StructuredTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    # Fallback when langchain is not available
    AgentExecutor = None
    ChatOpenAI = None
    ChatPromptTemplate = None
    MessagesPlaceholder = None
    BaseMessage = None
    StructuredTool = None
    ConversationBufferWindowMemory = None
    LANGCHAIN_AVAILABLE = False

# Local model imports
try:
    from .local_model import LocalModelManager, LocalModelLLM, create_local_model_manager
    LOCAL_MODEL_AVAILABLE = True
except ImportError:
    LOCAL_MODEL_AVAILABLE = False
    LocalModelManager = None
    LocalModelLLM = None

logger = logging.getLogger(__name__)

@dataclass
class AgentConfig:
    """Configuration for agents"""
    name: str
    llm_model: str = "gpt-4"
    temperature: float = 0.1
    max_tokens: int = 4000
    timeout: int = 300  # 5 minutes
    retry_attempts: int = 3
    enable_memory: bool = True
    custom_config: Dict[str, Any] = None

class BaseAgent(ABC):
    """
    Base class for all SecureCLI agents providing common functionality
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"{__name__}.{self.name}")
        
        # Initialize common agent properties
        self.llm_model = config.get('llm_model', config.get('llm', {}).get('model', 'gpt-4'))
        self.temperature = config.get('temperature', config.get('llm', {}).get('temperature', 0.1))
        self.max_tokens = config.get('max_tokens', config.get('llm', {}).get('max_tokens', 4000))
        self.timeout = config.get('timeout', config.get('llm', {}).get('timeout', 300))
        self.retry_attempts = config.get('retry_attempts', 3)
        
        # LLM provider configuration
        self.llm_provider = config.get('llm_provider', config.get('llm', {}).get('provider', 'auto'))
        self.local_model_config = config.get('local_model', {})
        
        self.logger.info(f"Initialized {self.name} with model {self.llm_model} via {self.llm_provider}")
        
        # Debug local model configuration
        if self.llm_provider == 'local' or self.local_model_config.get('enabled'):
            self.logger.info(f"Local model config: engine={self.local_model_config.get('engine')}, model={self.local_model_config.get('model_name')}, enabled={self.local_model_config.get('enabled')}")
    
    def create_llm(self):
        """Create the appropriate LLM based on configuration with intelligent fallback"""
        provider = self.llm_provider.lower()
        
        # Try the configured provider first
        if provider == "local":
            llm = self._try_create_local_llm()
            if llm:
                return llm
            # For local provider, provide helpful error message
            self.logger.warning("Local model not available. Skipping AI analysis. Consider using a smaller model or increasing system memory.")
            return None
        
        elif provider in ["openai", "anthropic"]:
            return self._create_api_llm(provider)
        
        elif provider == "auto":
            # Intelligent provider selection
            return self._create_auto_llm()
        
        else:
            # Unknown provider, try auto-selection
            self.logger.warning(f"Unknown provider '{provider}', using auto-selection")
            return self._create_auto_llm()
    
    def _try_create_local_llm(self):
        """Try to create local model LLM, return None if not available"""
        try:
            if not LOCAL_MODEL_AVAILABLE:
                self.logger.debug("Local model support not available")
                return None
            
            # Check if local model is enabled
            if not self.local_model_config.get('enabled', False):
                self.logger.debug("Local model not enabled")
                return None
            
            # Create local model manager
            manager = create_local_model_manager(self.local_model_config)
            if not manager or not manager.is_available():
                self.logger.debug("Local model manager not available")
                return None
            
            self.logger.info(f"Using local model: {self.local_model_config.get('model_name')}")
            return LocalModelLLM(manager)
            
        except Exception as e:
            self.logger.debug(f"Failed to create local LLM: {e}")
            return None
    
    def _create_api_llm(self, provider=None):
        """Create API-based LLM (OpenAI/Anthropic)"""
        provider = provider or self.llm_provider
        
        # If LangChain is available, use it
        if LANGCHAIN_AVAILABLE:
            if provider == "anthropic":
                # Check for Anthropic support
                try:
                    from langchain_anthropic import ChatAnthropic
                    api_key = os.environ.get('ANTHROPIC_API_KEY')
                    if not api_key:
                        raise ValueError("ANTHROPIC_API_KEY not found")
                    
                    self.logger.info(f"Using Anthropic model: {self.llm_model}")
                    return ChatAnthropic(
                        model=self.llm_model,
                        temperature=self.temperature,
                        max_tokens=self.max_tokens,
                        timeout=self.timeout
                    )
                except ImportError:
                    self.logger.warning("Anthropic package not available, falling back to OpenAI")
                except Exception as e:
                    self.logger.warning(f"Failed to create Anthropic LLM: {e}")
            
            # Default to OpenAI with LangChain
            api_key = os.environ.get('OPENAI_API_KEY')
            if not api_key:
                raise RuntimeError("No API key available. Set OPENAI_API_KEY or configure local models.")
            
            self.logger.info(f"Using OpenAI model: {self.llm_model}")
            return ChatOpenAI(
                model=self.llm_model,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
        else:
            # LangChain not available, use direct OpenAI client
            try:
                from openai import AsyncOpenAI
                api_key = os.environ.get('OPENAI_API_KEY')
                if not api_key:
                    raise RuntimeError("No API key available. Set OPENAI_API_KEY or configure local models.")
                
                self.logger.info(f"Using OpenAI model (direct API): {self.llm_model}")
                
                # Return a wrapper that has the same interface as LangChain's LLM
                class DirectOpenAIWrapper:
                    def __init__(self, model, temperature, max_tokens, timeout):
                        self.client = AsyncOpenAI(api_key=api_key, timeout=timeout)
                        self.model = model
                        self.temperature = temperature
                        self.max_tokens = max_tokens
                    
                    async def ainvoke(self, prompt):
                        """Compatible with LangChain's ainvoke interface"""
                        response = await self.client.chat.completions.create(
                            model=self.model,
                            messages=[{"role": "user", "content": prompt}],
                            temperature=self.temperature,
                            max_tokens=self.max_tokens
                        )
                        # Return object with .content attribute like LangChain
                        class Response:
                            def __init__(self, content):
                                self.content = content
                                self.text = content
                        
                        return Response(response.choices[0].message.content)
                
                return DirectOpenAIWrapper(
                    model=self.llm_model,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                    timeout=self.timeout
                )
            except ImportError:
                raise RuntimeError("OpenAI package not available. Install with: pip install openai")
    
    def _create_best_api_llm(self):
        """Create the best available API LLM"""
        # Try OpenAI first
        if os.environ.get('OPENAI_API_KEY'):
            try:
                return self._create_api_llm("openai")
            except Exception as e:
                self.logger.debug(f"OpenAI failed: {e}")
        
        # Try Anthropic
        if os.environ.get('ANTHROPIC_API_KEY'):
            try:
                return self._create_api_llm("anthropic")
            except Exception as e:
                self.logger.debug(f"Anthropic failed: {e}")
        
        raise RuntimeError("No API keys available. Please set OPENAI_API_KEY or ANTHROPIC_API_KEY, or configure local models.")
    
    def _create_auto_llm(self):
        """Automatically select the best available LLM"""
        # Priority order: Local (if high-end GPU) -> OpenAI -> Anthropic -> Local (fallback)
        
        # Check if we have a powerful GPU for local inference
        local_preferred = self._should_prefer_local()
        
        if local_preferred:
            local_llm = self._try_create_local_llm()
            if local_llm:
                return local_llm
        
        # Try API models
        try:
            return self._create_best_api_llm()
        except Exception:
            # Last resort: try local even without GPU preference
            if not local_preferred:
                local_llm = self._try_create_local_llm()
                if local_llm:
                    self.logger.info("Using local model as fallback")
                    return local_llm
            
            raise RuntimeError("No AI providers available. Please configure API keys or local models.")
    
    def _should_prefer_local(self):
        """Determine if local models should be preferred based on system capabilities"""
        try:
            # Check if we have GPU available
            import torch
            if torch.cuda.is_available():
                gpu_memory = torch.cuda.get_device_properties(0).total_memory
                # Prefer local if we have at least 8GB GPU memory
                if gpu_memory >= 8 * 1024**3:  # 8GB
                    return True
        except ImportError:
            pass
        
        # Check CPU cores for CPU inference
        import multiprocessing
        cpu_cores = multiprocessing.cpu_count()
        # Prefer local for high-end CPUs (16+ cores)
        return cpu_cores >= 16
    
    @abstractmethod
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for the agent
        Must be implemented by each specific agent
        """
        pass
    
    async def health_check(self) -> bool:
        """
        Perform health check to ensure agent is ready
        """
        try:
            # Basic configuration validation
            required_config = ['llm_model']
            for key in required_config:
                if key not in self.config:
                    self.logger.error(f"Missing required config: {key}")
                    return False
            
            # Test LLM connectivity if needed
            if hasattr(self, 'agent_executor'):
                # Could add LLM ping test here
                pass
            
            self.logger.debug(f"{self.name} health check passed")
            return True
            
        except Exception as e:
            self.logger.error(f"{self.name} health check failed: {e}")
            return False
    
    def get_capabilities(self) -> List[str]:
        """
        Return list of capabilities this agent provides
        """
        return []
    
    def get_status(self) -> Dict[str, Any]:
        """
        Get current agent status and metrics
        """
        return {
            'name': self.name,
            'healthy': True,  # Could implement actual health check
            'model': self.llm_model,
            'capabilities': self.get_capabilities(),
            'config': {
                'temperature': self.temperature,
                'max_tokens': self.max_tokens,
                'timeout': self.timeout
            }
        }
    
    async def validate_input(self, context: Dict[str, Any]) -> bool:
        """
        Validate input context before execution
        """
        if not context:
            self.logger.error("Empty context provided")
            return False
        
        return True
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle and log errors consistently across agents
        """
        self.logger.error(f"{self.name} error: {error}")
        
        return {
            'success': False,
            'error': str(error),
            'error_type': error.__class__.__name__,
            'agent': self.name,
            'context_summary': self._summarize_context(context)
        }
    
    def _summarize_context(self, context: Dict[str, Any]) -> str:
        """
        Create a summary of context for logging
        """
        if not context:
            return "empty"
        
        summary_parts = []
        
        if 'workspace_path' in context:
            summary_parts.append(f"workspace: {context['workspace_path']}")
        
        if 'findings' in context:
            summary_parts.append(f"findings: {len(context['findings'])}")
        
        if 'technologies' in context:
            summary_parts.append(f"technologies: {len(context['technologies'])}")
        
        return ", ".join(summary_parts) if summary_parts else "unknown"
    
    async def retry_with_backoff(self, func, *args, **kwargs):
        """
        Execute function with exponential backoff retry
        """
        import asyncio
        
        for attempt in range(self.retry_attempts):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                if attempt == self.retry_attempts - 1:
                    raise e
                
                wait_time = 2 ** attempt
                self.logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                await asyncio.sleep(wait_time)
        
        raise Exception(f"All {self.retry_attempts} attempts failed")

class AgentOrchestrator:
    """
    Orchestrates multiple agents for complex workflows
    """
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.agents = {}
        self.logger = logging.getLogger(__name__)
    
    def register_agent(self, agent_name: str, agent: BaseAgent):
        """Register an agent with the orchestrator"""
        self.agents[agent_name] = agent
        self.logger.info(f"Registered agent: {agent_name}")
    
    async def execute_workflow(self, workflow: List[Dict[str, Any]], context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Execute a workflow consisting of multiple agent steps
        """
        results = {}
        current_context = context.copy()
        
        for step in workflow:
            agent_name = step.get('agent')
            step_config = step.get('config', {})
            
            if agent_name not in self.agents:
                raise ValueError(f"Agent {agent_name} not registered")
            
            agent = self.agents[agent_name]
            
            try:
                # Merge step config with current context
                step_context = {**current_context, **step_config}
                
                # Execute agent
                step_result = await agent.execute(step_context)
                
                # Store result and update context for next step
                results[agent_name] = step_result
                current_context.update(step_result)
                
                self.logger.info(f"Completed workflow step: {agent_name}")
                
            except Exception as e:
                self.logger.error(f"Workflow step {agent_name} failed: {e}")
                results[agent_name] = {'error': str(e)}
                
                # Check if workflow should continue on error
                if not step.get('continue_on_error', False):
                    break
        
        return {
            'workflow_results': results,
            'final_context': current_context,
            'success': all('error' not in result for result in results.values())
        }
    
    async def health_check_all(self) -> Dict[str, bool]:
        """Perform health check on all registered agents"""
        health_status = {}
        
        for agent_name, agent in self.agents.items():
            try:
                health_status[agent_name] = await agent.health_check()
            except Exception as e:
                self.logger.error(f"Health check failed for {agent_name}: {e}")
                health_status[agent_name] = False
        
        return health_status
    
    def get_agent_statuses(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all registered agents"""
        statuses = {}
        
        for agent_name, agent in self.agents.items():
            statuses[agent_name] = agent.get_status()
        
        return statuses