"""
Local Model Integration for SecureCLI
Supports DeepSeek and other local models via multiple inference engines
"""

import os
import json
import requests
import logging
from typing import Dict, Any, Optional, List, Generator
from dataclasses import dataclass
from abc import ABC, abstractmethod

try:
    from langchain_community.llms import Ollama
    from langchain_community.llms import LlamaCpp
    from langchain.callbacks.manager import CallbackManagerForLLMRun
    from langchain.llms.base import LLM
    from langchain_core.outputs import LLMResult, Generation, ChatGeneration
    from langchain_core.messages import AIMessage, BaseMessage
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False
    LLM = object
    CallbackManagerForLLMRun = None
    LLMResult = None
    Generation = None
    ChatGeneration = None
    AIMessage = None
    BaseMessage = None

try:
    import transformers
    from transformers import AutoTokenizer, AutoModelForCausalLM
    import torch
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False


@dataclass
class LocalModelConfig:
    """Configuration for local model inference"""
    engine: str = "ollama"  # ollama, llamacpp, transformers
    model_name: str = "deepseek-coder"
    base_url: str = "http://localhost:11434"
    model_path: Optional[str] = None
    context_length: int = 4096
    gpu_layers: int = 35
    threads: int = 8
    batch_size: int = 512
    quantization: str = "q4_k_m"
    max_tokens: int = 2000
    temperature: float = 0.1
    timeout: int = 60


class LocalModelClient(ABC):
    """Abstract base class for local model clients"""
    
    def __init__(self, config: LocalModelConfig):
        self.config = config
        self.logger = logging.getLogger(__name__)
    
    @abstractmethod
    def is_available(self) -> bool:
        """Check if the model/engine is available"""
        pass
    
    @abstractmethod
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text from prompt"""
        pass
    
    @abstractmethod
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate text from prompt with streaming"""
        pass
    
    @abstractmethod
    def get_model_info(self) -> Dict[str, Any]:
        """Get information about the loaded model"""
        pass


class OllamaClient(LocalModelClient):
    """Client for Ollama local model inference"""
    
    def __init__(self, config: LocalModelConfig):
        super().__init__(config)
        self.base_url = config.base_url.rstrip('/')
        self._llm = None
        
    def is_available(self) -> bool:
        """Check if Ollama is running and model is available"""
        try:
            # Check if Ollama server is running
            response = requests.get(f"{self.base_url}/api/version", timeout=5)
            if response.status_code != 200:
                return False
            
            # Check if model is available
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.config.model_name},
                timeout=10
            )
            return response.status_code == 200
            
        except Exception as e:
            self.logger.debug(f"Ollama availability check failed: {e}")
            return False
    
    def _get_llm(self):
        """Get or create LangChain Ollama LLM"""
        if self._llm is None and LANGCHAIN_AVAILABLE:
            self._llm = Ollama(
                model=self.config.model_name,
                base_url=self.config.base_url,
                temperature=self.config.temperature,
                num_ctx=self.config.context_length,
                timeout=self.config.timeout
            )
        return self._llm
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Ollama"""
        if LANGCHAIN_AVAILABLE:
            llm = self._get_llm()
            if llm:
                return llm.invoke(prompt)
        
        # Fallback to direct API call
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": kwargs.get("temperature", self.config.temperature),
                        "num_ctx": kwargs.get("context_length", self.config.context_length),
                        "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
                    }
                },
                timeout=self.config.timeout
            )
            response.raise_for_status()
            return response.json().get("response", "")
            
        except Exception as e:
            self.logger.error(f"Ollama generation failed: {e}")
            raise
    
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate text with streaming"""
        try:
            response = requests.post(
                f"{self.base_url}/api/generate",
                json={
                    "model": self.config.model_name,
                    "prompt": prompt,
                    "stream": True,
                    "options": {
                        "temperature": kwargs.get("temperature", self.config.temperature),
                        "num_ctx": kwargs.get("context_length", self.config.context_length),
                        "num_predict": kwargs.get("max_tokens", self.config.max_tokens)
                    }
                },
                stream=True,
                timeout=self.config.timeout
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    data = json.loads(line)
                    if "response" in data:
                        yield data["response"]
                    if data.get("done", False):
                        break
                        
        except Exception as e:
            self.logger.error(f"Ollama streaming failed: {e}")
            raise
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get Ollama model information"""
        try:
            response = requests.post(
                f"{self.base_url}/api/show",
                json={"name": self.config.model_name},
                timeout=10
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Failed to get Ollama model info: {e}")
            return {}


class LlamaCppClient(LocalModelClient):
    """Client for llama.cpp local model inference"""
    
    def __init__(self, config: LocalModelConfig):
        super().__init__(config)
        self._llm = None
        
    def is_available(self) -> bool:
        """Check if llama.cpp model is available"""
        if not LANGCHAIN_AVAILABLE:
            return False
        
        if not self.config.model_path or not os.path.exists(self.config.model_path):
            return False
        
        try:
            # Try to initialize the model
            self._get_llm()
            return True
        except Exception as e:
            self.logger.debug(f"LlamaCpp availability check failed: {e}")
            return False
    
    def _get_llm(self):
        """Get or create LangChain LlamaCpp LLM"""
        if self._llm is None and LANGCHAIN_AVAILABLE:
            self._llm = LlamaCpp(
                model_path=self.config.model_path,
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
                n_ctx=self.config.context_length,
                n_gpu_layers=self.config.gpu_layers,
                n_threads=self.config.threads,
                n_batch=self.config.batch_size,
                verbose=False
            )
        return self._llm
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using llama.cpp"""
        llm = self._get_llm()
        if not llm:
            raise RuntimeError("LlamaCpp LLM not available")
        
        return llm.invoke(prompt)
    
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate text with streaming (not implemented for llama.cpp)"""
        # LlamaCpp doesn't support streaming in LangChain
        result = self.generate(prompt, **kwargs)
        yield result
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "engine": "llamacpp",
            "model_path": self.config.model_path,
            "context_length": self.config.context_length,
            "gpu_layers": self.config.gpu_layers
        }


class TransformersClient(LocalModelClient):
    """Client for HuggingFace Transformers local model inference"""
    
    def __init__(self, config: LocalModelConfig):
        super().__init__(config)
        self._model = None
        self._tokenizer = None
        
    def is_available(self) -> bool:
        """Check if transformers and model are available"""
        if not TRANSFORMERS_AVAILABLE:
            return False
        
        try:
            self._load_model()
            return True
        except Exception as e:
            self.logger.debug(f"Transformers availability check failed: {e}")
            return False
    
    def _load_model(self):
        """Load model and tokenizer"""
        if self._model is None and TRANSFORMERS_AVAILABLE:
            model_path = self.config.model_path or self.config.model_name
            
            self._tokenizer = AutoTokenizer.from_pretrained(model_path)
            self._model = AutoModelForCausalLM.from_pretrained(
                model_path,
                torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
                device_map="auto" if torch.cuda.is_available() else None,
                trust_remote_code=True
            )
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using Transformers"""
        if not TRANSFORMERS_AVAILABLE:
            raise RuntimeError("Transformers not available")
        
        self._load_model()
        
        inputs = self._tokenizer.encode(prompt, return_tensors="pt")
        
        with torch.no_grad():
            outputs = self._model.generate(
                inputs,
                max_new_tokens=kwargs.get("max_tokens", self.config.max_tokens),
                temperature=kwargs.get("temperature", self.config.temperature),
                do_sample=True,
                pad_token_id=self._tokenizer.eos_token_id
            )
        
        response = self._tokenizer.decode(outputs[0], skip_special_tokens=True)
        # Remove the input prompt from response
        return response[len(prompt):].strip()
    
    def generate_stream(self, prompt: str, **kwargs) -> Generator[str, None, None]:
        """Generate text with streaming (simplified)"""
        result = self.generate(prompt, **kwargs)
        # Simple chunked yielding for streaming effect
        chunk_size = 10
        for i in range(0, len(result), chunk_size):
            yield result[i:i+chunk_size]
    
    def get_model_info(self) -> Dict[str, Any]:
        """Get model information"""
        return {
            "engine": "transformers",
            "model_name": self.config.model_name,
            "model_path": self.config.model_path,
            "device": "cuda" if torch.cuda.is_available() else "cpu"
        }


class LocalModelManager:
    """Manager for local model clients"""
    
    def __init__(self, config_dict: Dict[str, Any]):
        # Filter config to only include fields that LocalModelConfig accepts
        valid_fields = {
            'engine', 'model_name', 'base_url', 'model_path', 'context_length',
            'gpu_layers', 'threads', 'batch_size', 'quantization', 'max_tokens',
            'temperature', 'timeout'
        }
        filtered_config = {k: v for k, v in config_dict.items() if k in valid_fields}
        self.config = LocalModelConfig(**filtered_config)
        self.logger = logging.getLogger(__name__)
        self._client = None
    
    def get_client(self) -> Optional[LocalModelClient]:
        """Get the appropriate client based on configuration"""
        if self._client is None:
            if self.config.engine == "ollama":
                self._client = OllamaClient(self.config)
            elif self.config.engine == "llamacpp":
                self._client = LlamaCppClient(self.config)
            elif self.config.engine == "transformers":
                self._client = TransformersClient(self.config)
            else:
                raise ValueError(f"Unsupported engine: {self.config.engine}")
        
        return self._client
    
    def is_available(self) -> bool:
        """Check if local model is available"""
        try:
            client = self.get_client()
            return client.is_available() if client else False
        except Exception as e:
            self.logger.error(f"Local model availability check failed: {e}")
            return False
    
    def generate(self, prompt: str, **kwargs) -> str:
        """Generate text using local model"""
        client = self.get_client()
        if not client:
            raise RuntimeError("No local model client available")
        
        if not client.is_available():
            raise RuntimeError(f"Local model ({self.config.engine}) is not available")
        
        return client.generate(prompt, **kwargs)
    
    def test_model(self) -> Dict[str, Any]:
        """Test local model and return diagnostics"""
        result = {
            "available": False,
            "engine": self.config.engine,
            "model_name": self.config.model_name,
            "error": None,
            "response_time": None,
            "model_info": {}
        }
        
        try:
            import time
            client = self.get_client()
            
            if not client:
                result["error"] = "Failed to create client"
                return result
            
            if not client.is_available():
                result["error"] = "Model not available"
                return result
            
            # Test generation
            start_time = time.time()
            test_prompt = "Write a short Python function that adds two numbers:"
            response = client.generate(test_prompt, max_tokens=100)
            end_time = time.time()
            
            result["available"] = True
            result["response_time"] = end_time - start_time
            result["model_info"] = client.get_model_info()
            result["test_response"] = response[:200] + "..." if len(response) > 200 else response
            
        except Exception as e:
            result["error"] = str(e)
            self.logger.error(f"Local model test failed: {e}")
        
        return result


# LangChain-compatible wrapper for local models
if LANGCHAIN_AVAILABLE:
    class LocalModelLLM(LLM):
        """LangChain-compatible wrapper for local models"""
        
        manager: LocalModelManager
        
        def __init__(self, manager: LocalModelManager):
            super().__init__(manager=manager)
        
        @property
        def _llm_type(self) -> str:
            return "local_model"
        
        def _call(
            self,
            prompt: str,
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> str:
            """Call the local model and return text"""
            return self.manager.generate(prompt, **kwargs)
        
        def _generate(
            self,
            prompts: List[str],
            stop: Optional[List[str]] = None,
            run_manager: Optional[CallbackManagerForLLMRun] = None,
            **kwargs: Any,
        ) -> LLMResult:
            """Generate responses for multiple prompts and return LLMResult with ChatGeneration"""
            generations = []
            for prompt in prompts:
                text = self.manager.generate(prompt, **kwargs)
                # Create AIMessage for ChatGeneration
                message = AIMessage(content=text)
                # Create ChatGeneration with the message
                chat_generation = ChatGeneration(message=message, text=text)
                generations.append([chat_generation])
            
            return LLMResult(generations=generations)
        
        def invoke(self, input_text: str, **kwargs) -> AIMessage:
            """Invoke the model and return an AIMessage"""
            response_text = self.manager.generate(input_text, **kwargs)
            return AIMessage(content=response_text)
        
        async def ainvoke(self, input_text: str, **kwargs) -> AIMessage:
            """Async invoke the model and return an AIMessage"""
            # Run the synchronous generate in a thread pool to make it async
            import asyncio
            response_text = await asyncio.to_thread(self.manager.generate, input_text, **kwargs)
            return AIMessage(content=response_text)
        
        @property
        def _identifying_params(self) -> Dict[str, Any]:
            """Get identifying parameters"""
            return {
                "engine": self.manager.config.engine,
                "model_name": self.manager.config.model_name,
            }
        
        def bind_functions(self, functions):
            """Dummy method for compatibility with OpenAI function binding"""
            # Local models don't support function calling in the same way
            # Return self to maintain compatibility
            return self
else:
    # Simple response wrapper for non-LangChain environments
    class MockAIMessage:
        """Simple wrapper to mimic AIMessage structure"""
        def __init__(self, content: str):
            self.content = content
        
        def __str__(self):
            return self.content
    
    class LocalModelLLM:
        """Mock LLM class when LangChain is not available"""
        def __init__(self, manager: LocalModelManager):
            self.manager = manager
        
        def invoke(self, input_text: str, **kwargs):
            """Invoke the model and return MockAIMessage"""
            response_text = self.manager.generate(input_text, **kwargs)
            return MockAIMessage(content=response_text)
        
        async def ainvoke(self, input_text: str, **kwargs):
            """Async invoke the model and return MockAIMessage"""
            import asyncio
            response_text = await asyncio.to_thread(self.manager.generate, input_text, **kwargs)
            return MockAIMessage(content=response_text)


def create_local_model_manager(config: Dict[str, Any]) -> Optional[LocalModelManager]:
    """Factory function to create local model manager"""
    try:
        return LocalModelManager(config)
    except Exception as e:
        logging.getLogger(__name__).error(f"Failed to create local model manager: {e}")
        return None