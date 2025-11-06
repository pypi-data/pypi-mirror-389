"""
Configuration management for SecureCLI
Handles YAML/JSON config files, environment variables, and workspace overrides
"""

import os
import yaml
import json
from pathlib import Path
from typing import Any, Dict, Optional, Union, List
from copy import deepcopy

# Load .env file if available
try:
    from dotenv import load_dotenv
    # Try to load .env from current directory and project root
    for env_path in ['.env', Path(__file__).parents[2] / '.env']:
        if Path(env_path).exists():
            load_dotenv(env_path)
            break
except ImportError:
    pass  # dotenv not available, continue without it

from .schemas.config import ConfigSchema


class ConfigManager:
    """Manages configuration from multiple sources with precedence"""
    
    def __init__(self, config_path: Optional[str] = None):
        self.config_path = config_path
        self.config_data = {}
        self.default_config = self._load_default_config()
        self.user_config = self._load_user_config()
        self.workspace_config = {}
        
        # Merge configurations with precedence:
        # defaults < user config < workspace config < env vars
        self._merge_configs()
    
    def _load_default_config(self) -> Dict[str, Any]:
        """Load default configuration"""
        default_config = {
            "repo": {
                "path": None,
                "exclude": [
                    "node_modules/", "__pycache__/", ".git/", "build/", "dist/",
                    "vendor/", ".pytest_cache/", "coverage/", ".next/", ".nuxt/"
                ],
                "max_file_size": 1048576,  # 1MB
            },
            "mode": "quick",
            "domain": {
                "profiles": []
            },
            "llm": {
                "model": "gpt-4",
                "max_tokens": 2000,
                "temperature": 0.1,
                "timeout": 60,
                "provider": "auto"  # auto, openai, anthropic, local
            },
            "local_model": {
                "enabled": False,
                "engine": "ollama",  # ollama, llamacpp, transformers
                "model_name": "deepseek-coder-v2:16b",
                "base_url": "http://localhost:11434",
                "model_path": None,  # For llamacpp/transformers
                "context_length": 8192,
                "gpu_layers": 35,  # Number of layers to run on GPU
                "threads": 8,  # CPU threads for inference
                "batch_size": 512,
                "quantization": "q5_k_m"  # Model quantization
            },
            "rag": {
                "enabled": True,
                "k": 5,
                "chunk_size": 1000,
                "chunk_overlap": 200
            },
            "cvss": {
                "policy": "block_high"
            },
            "ci": {
                "block_on": ["critical", "high"],
                "changed_files_only": False
            },
            "output": {
                "dir": "./output",
                "format": "md"
            },
            "redact": {
                "enabled": True,
                "patterns": [
                    r"(?i)(password|secret|key|token)\s*[:=]\s*['\"][^'\"]+['\"]",
                    r"(?i)api_key\s*[:=]\s*['\"][^'\"]+['\"]",
                    r"sk-[a-zA-Z0-9]{48}",  # OpenAI API keys
                    r"ghp_[a-zA-Z0-9]{36}",  # GitHub tokens
                ]
            },
            "sandbox": {
                "enabled": True,
                "timeout": 300,
                "memory_limit": "512MB"
            },
            "tools": {
                "enabled": [
                    "semgrep", "gitleaks", "bandit", "gosec"
                ],
                "paths": {},
                "configs": {}
            },
            "logging": {
                "level": "INFO",
                "file": None,
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            }
        }
        
        return default_config
    
    def _load_user_config(self) -> Dict[str, Any]:
        """Load user configuration from ~/.securecli/config.yml"""
        user_config_dir = Path.home() / ".securecli"
        user_config_file = user_config_dir / "config.yml"
        
        if self.config_path:
            # Use explicitly provided config path
            config_file = Path(self.config_path)
        else:
            config_file = user_config_file
        
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    return yaml.safe_load(f) or {}
            except Exception as e:
                print(f"Warning: Could not load config file {config_file}: {e}")
        
        return {}
    
    def load_workspace_config(self, workspace_path: str) -> None:
        """Load workspace-specific configuration"""
        workspace_config_file = Path(workspace_path) / "config.yml"
        
        if workspace_config_file.exists():
            try:
                with open(workspace_config_file, 'r') as f:
                    self.workspace_config = yaml.safe_load(f) or {}
                    self._merge_configs()
            except Exception as e:
                print(f"Warning: Could not load workspace config: {e}")
        else:
            self.workspace_config = {}
    
    def _merge_configs(self) -> None:
        """Merge all configuration sources with proper precedence"""
        self.config_data = deepcopy(self.default_config)
        
        # Merge user config
        self._deep_merge(self.config_data, self.user_config)
        
        # Merge workspace config
        self._deep_merge(self.config_data, self.workspace_config)
        
        # Override with environment variables
        self._apply_env_overrides()
    
    def _deep_merge(self, base: Dict, override: Dict) -> None:
        """Recursively merge dictionaries"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def _apply_env_overrides(self) -> None:
        """Apply environment variable overrides"""
        env_prefix = "SECURE_"
        
        # Check .env settings for LLM provider selection
        use_local = os.getenv('USE_LOCAL_MODEL', '').lower() == 'true'
        use_api = os.getenv('USE_API_MODEL', '').lower() == 'true'
        
        # Set LLM provider based on .env settings
        if use_local and not use_api:
            # Use local model
            self.config_data['llm']['provider'] = 'local'
            self.config_data['local_model']['enabled'] = True
        elif use_api and not use_local:
            # Use API provider
            api_provider = os.getenv('API_PROVIDER', 'openai').lower()
            self.config_data['llm']['provider'] = api_provider
            self.config_data['local_model']['enabled'] = False
        elif use_local and use_api:
            # Both enabled - prefer local
            self.config_data['llm']['provider'] = 'local'
            self.config_data['local_model']['enabled'] = True
        # If neither is set, use existing config
        
        # Apply local model settings from .env (without SECURE_ prefix)
        local_model_mappings = {
            'LOCAL_MODEL_ENGINE': 'local_model.engine',
            'LOCAL_MODEL_NAME': 'local_model.model_name',
            'LOCAL_MODEL_BASE_URL': 'local_model.base_url',
            'LOCAL_MODEL_CONTEXT_LENGTH': 'local_model.context_length',
            'LOCAL_MODEL_GPU_LAYERS': 'local_model.gpu_layers',
            'LOCAL_MODEL_THREADS': 'local_model.threads',
            'LOCAL_MODEL_BATCH_SIZE': 'local_model.batch_size',
            'LOCAL_MODEL_QUANTIZATION': 'local_model.quantization',
        }
        
        for env_var, config_path in local_model_mappings.items():
            value = os.getenv(env_var)
            if value:
                self.set(config_path, self._convert_env_value(value))
        
        # Define special mapping for environment variables to config paths
        env_mappings = {
            'LOCAL_MODEL_ENABLED': 'local_model.enabled',
            'LOCAL_MODEL_ENGINE': 'local_model.engine', 
            'LOCAL_MODEL_MODEL_NAME': 'local_model.model_name',
            'LOCAL_MODEL_BASE_URL': 'local_model.base_url',
            'LOCAL_MODEL_MODEL_PATH': 'local_model.model_path',
            'LOCAL_MODEL_CONTEXT_LENGTH': 'local_model.context_length',
            'LOCAL_MODEL_GPU_LAYERS': 'local_model.gpu_layers',
            'LOCAL_MODEL_THREADS': 'local_model.threads',
            'LOCAL_MODEL_BATCH_SIZE': 'local_model.batch_size',
            'LOCAL_MODEL_QUANTIZATION': 'local_model.quantization',
        }
        
        for env_var, value in os.environ.items():
            if env_var.startswith(env_prefix):
                env_key = env_var[len(env_prefix):]
                
                # Check if we have a special mapping
                if env_key in env_mappings:
                    config_path = env_mappings[env_key]
                else:
                    # Default conversion: SECURE_LLM_MODEL to llm.model
                    config_path = env_key.lower().replace('_', '.')
                
                self.set(config_path, self._convert_env_value(value))
    
    def _convert_env_value(self, value: str) -> Union[str, int, float, bool, list]:
        """Convert environment variable string to appropriate type"""
        # Boolean
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer
        if value.isdigit():
            return int(value)
        
        # Float
        try:
            if '.' in value:
                return float(value)
        except ValueError:
            pass
        
        # List (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # String
        return value
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value using dot notation"""
        keys = key.split('.')
        value = self.config_data
        
        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default
        
        return value
    
    def set(self, key: str, value: Any) -> None:
        """Set configuration value using dot notation"""
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the value
        config[keys[-1]] = value
    
    def unset(self, key: str) -> None:
        """Unset configuration value"""
        keys = key.split('.')
        config = self.config_data
        
        # Navigate to the parent dictionary
        for k in keys[:-1]:
            if k not in config:
                return
            config = config[k]
        
        # Remove the key
        if keys[-1] in config:
            del config[keys[-1]]
    
    def get_all(self) -> Dict[str, Any]:
        """Get all configuration as dictionary"""
        return deepcopy(self.config_data)
    
    def save_user_config(self) -> None:
        """Save current configuration to user config file"""
        user_config_dir = Path.home() / ".securecli"
        user_config_dir.mkdir(exist_ok=True)
        
        user_config_file = user_config_dir / "config.yml"
        
        # Only save non-default values
        config_to_save = self._get_non_default_config()
        
        try:
            with open(user_config_file, 'w') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise Exception(f"Could not save user config: {e}")
    
    def save_workspace_config(self, workspace_path: str) -> None:
        """Save current configuration to workspace config file"""
        workspace_config_file = Path(workspace_path) / "config.yml"
        
        # Only save non-default values
        config_to_save = self._get_non_default_config()
        
        try:
            with open(workspace_config_file, 'w') as f:
                yaml.dump(config_to_save, f, default_flow_style=False, indent=2)
        except Exception as e:
            raise Exception(f"Could not save workspace config: {e}")
    
    def _get_non_default_config(self) -> Dict[str, Any]:
        """Get configuration that differs from defaults"""
        # TODO: Implement diff between current config and defaults
        # For now, return current config minus some obvious defaults
        
        config_copy = deepcopy(self.config_data)
        
        # Remove paths that are likely to be machine-specific
        if 'repo' in config_copy and 'path' in config_copy['repo']:
            if config_copy['repo']['path'] is None:
                del config_copy['repo']['path']
        
        return config_copy
    
    def validate(self) -> List[str]:
        """Validate configuration and return list of errors"""
        errors = []
        
        # Validate required fields
        if not self.get('llm.model'):
            errors.append("llm.model is required")
        
        # Validate repo path if set
        repo_path = self.get('repo.path')
        if repo_path and not Path(repo_path).exists():
            errors.append(f"repo.path does not exist: {repo_path}")
        
        # Validate output directory
        output_dir = self.get('output.dir')
        if output_dir:
            output_path = Path(output_dir)
            if not output_path.parent.exists():
                errors.append(f"output.dir parent directory does not exist: {output_path.parent}")
        
        # Validate CVSS policy
        valid_policies = ['block_critical', 'block_high', 'block_medium', 'warn_only']
        if self.get('cvss.policy') not in valid_policies:
            errors.append(f"cvss.policy must be one of: {valid_policies}")
        
        return errors
    
    def reset_to_defaults(self) -> None:
        """Reset configuration to defaults"""
        self.config_data = deepcopy(self.default_config)
        self.user_config = {}
        self.workspace_config = {}
    
    def export_config(self, format: str = 'yaml') -> str:
        """Export configuration as YAML or JSON string"""
        if format.lower() == 'json':
            return json.dumps(self.config_data, indent=2)
        else:
            return yaml.dump(self.config_data, default_flow_style=False, indent=2)
    
    def import_config(self, config_str: str, format: str = 'yaml') -> None:
        """Import configuration from YAML or JSON string"""
        try:
            if format.lower() == 'json':
                imported_config = json.loads(config_str)
            else:
                imported_config = yaml.safe_load(config_str)
            
            # Merge imported config
            self._deep_merge(self.config_data, imported_config)
            
        except Exception as e:
            raise Exception(f"Could not import config: {e}")
    
    def get_api_keys(self) -> Dict[str, str]:
        """Get API keys from configuration and environment"""
        api_keys = {}
        
        # OpenAI API Key
        openai_key = (
            os.getenv('OPENAI_API_KEY') or 
            self.get('api_keys.openai') or
            os.getenv('SECURE_OPENAI_API_KEY')
        )
        if openai_key:
            api_keys['openai'] = openai_key
        
        # Anthropic API Key
        anthropic_key = (
            os.getenv('ANTHROPIC_API_KEY') or
            self.get('api_keys.anthropic') or
            os.getenv('SECURE_ANTHROPIC_API_KEY')
        )
        if anthropic_key:
            api_keys['anthropic'] = anthropic_key
        
        # GitHub Token
        github_token = (
            os.getenv('GITHUB_TOKEN') or
            self.get('api_keys.github') or
            os.getenv('SECURE_GITHUB_TOKEN')
        )
        if github_token:
            api_keys['github'] = github_token
        
        return api_keys