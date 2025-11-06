"""
Configuration schemas for SecureCLI
"""

from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field


class ToolConfig(BaseModel):
    """Configuration for individual security tools"""
    name: str = Field(..., description="Tool name")
    enabled: bool = Field(default=True, description="Whether tool is enabled")
    path: Optional[str] = Field(default=None, description="Path to tool executable")
    args: List[str] = Field(default_factory=list, description="Additional arguments")
    timeout: int = Field(default=300, description="Timeout in seconds")
    config: Dict[str, Any] = Field(default_factory=dict, description="Tool-specific config")


class SecurityConfig(BaseModel):
    """Main security configuration"""
    
    # General settings
    output_format: str = Field(default="json", description="Output format")
    log_level: str = Field(default="INFO", description="Logging level")
    max_file_size: int = Field(default=10485760, description="Max file size to analyze (bytes)")
    
    # Analysis settings
    parallel_jobs: int = Field(default=4, description="Number of parallel analysis jobs")
    include_patterns: List[str] = Field(
        default_factory=lambda: ["**/*.py", "**/*.js", "**/*.ts", "**/*.java", "**/*.go"],
        description="File patterns to include"
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["**/node_modules/**", "**/venv/**", "**/.git/**"],
        description="File patterns to exclude"
    )
    
    # Tool configurations
    tools: Dict[str, ToolConfig] = Field(
        default_factory=dict,
        description="Tool-specific configurations"
    )
    
    # AI/LLM settings
    ai_enabled: bool = Field(default=False, description="Enable AI analysis")
    openai_api_key: Optional[str] = Field(default=None, description="OpenAI API key")
    model_name: str = Field(default="gpt-4", description="AI model to use")
    
    # Output settings
    report_format: str = Field(default="html", description="Report format")
    output_directory: str = Field(default="./reports", description="Output directory")
    
    # Severity filtering
    min_severity: str = Field(default="LOW", description="Minimum severity to report")
    
    class Config:
        """Pydantic configuration"""
        json_encoders = {
            # Add custom encoders if needed
        }


class ConfigSchema(BaseModel):
    """Schema for SecureCLI configuration file"""
    version: str = Field(default="1.0", description="Config version")
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    
    class Config:
        """Pydantic configuration"""
        extra = "forbid"  # Don't allow extra fields