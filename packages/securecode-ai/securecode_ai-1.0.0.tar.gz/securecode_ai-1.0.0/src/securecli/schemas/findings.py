"""
Pydantic schemas for SecureCLI data structures
Defines finding formats, configuration schemas, and module interfaces
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Union
from enum import Enum
import uuid
from pydantic import BaseModel, Field, validator


class FindingSeverity(str, Enum):
    """Finding severity levels"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    INFO = "info"


# Alias for backward compatibility
Severity = FindingSeverity


class ToolEvidence(BaseModel):
    """Evidence from a security tool"""
    tool: str = Field(..., description="Tool name that generated the evidence")
    id: str = Field(..., description="Tool-specific finding ID")
    raw: str = Field(..., description="Raw tool output")


class CVSSv4(BaseModel):
    """CVSS v4.0 scoring information"""
    score: float = Field(..., ge=0.0, le=10.0, description="CVSS score (0.0-10.0)")
    vector: str = Field(..., description="CVSS vector string")


class SecurityTightening(BaseModel):
    """Security tightening recommendation"""
    type: str = Field(..., description="Type of tightening (Remove|Restrict|Simplify|Encapsulate)")
    evidence: str = Field(..., description="Evidence supporting the recommendation")
    diff: Optional[str] = Field(None, description="PR-ready diff")


class Finding(BaseModel):
    """Standardized security finding"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()), description="Unique identifier for this finding")
    file: str = Field(..., description="File path relative to repository root")
    title: str = Field(..., description="Short, specific finding title")
    description: str = Field(..., description="Detailed description with context and root cause")
    lines: str = Field(..., description="Affected line numbers (e.g., '10-15' or '42')")
    impact: str = Field(..., description="Potential impact if exploited")
    severity: str = Field(..., description="Severity level (Low|Medium|High|Critical)")
    confidence_score: int = Field(default=85, ge=0, le=100, description="Confidence score (0-100)")
    cvss_v4: CVSSv4 = Field(..., description="CVSS v4.0 scoring")
    owasp: List[str] = Field(default_factory=list, description="OWASP categories")
    cwe: List[str] = Field(default_factory=list, description="CWE identifiers")
    snippet: str = Field(..., description="Code snippet showing the issue")
    recommendation: str = Field(..., description="Stack-specific fix recommendation")
    sample_fix: str = Field(default="# Apply security best practices", description="Sample code showing the fix")
    poc: str = Field(..., description="Proof of concept or test case")
    references: List[str] = Field(default_factory=list, description="External references")
    cross_file: List[str] = Field(default_factory=list, description="Related files or symbols")
    tightening: Optional[SecurityTightening] = Field(None, description="Security tightening recommendation")
    tool_evidence: List[ToolEvidence] = Field(default_factory=list, description="Supporting tool evidence")

    @validator('severity')
    def validate_severity(cls, v):
        valid_severities = ['Low', 'Medium', 'High', 'Critical']
        if v not in valid_severities:
            raise ValueError(f'Severity must be one of: {valid_severities}')
        return v


class ExecutiveSummary(BaseModel):
    """Executive summary of security assessment"""
    top_risks: List[Dict[str, Any]] = Field(default_factory=list, description="Top security risks")
    heatmap: Dict[str, int] = Field(default_factory=dict, description="Findings by severity")
    themes: List[str] = Field(default_factory=list, description="Common vulnerability themes")
    roadmap: Dict[str, List[str]] = Field(default_factory=dict, description="Remediation roadmap")


class FileInfo(BaseModel):
    """Information about a file in the repository"""
    path: str = Field(..., description="Relative path from repository root")
    full_path: str = Field(..., description="Absolute file path")
    size: int = Field(..., description="File size in bytes")
    modified: float = Field(..., description="Last modified timestamp")
    file_type: str = Field(..., description="File type (code|config|docs|binary)")
    extension: str = Field(..., description="File extension")
    content: Optional[str] = Field(None, description="File content (for text files)")
    content_hash: Optional[str] = Field(None, description="Hash of file content")
    mime_type: Optional[str] = Field(None, description="MIME type")
    language: Optional[str] = Field(None, description="Programming language")


class RepositoryAnalysis(BaseModel):
    """Complete repository analysis results"""
    repo_path: str = Field(..., description="Repository path")
    files: List[FileInfo] = Field(default_factory=list, description="File information")
    structure: Dict[str, Any] = Field(default_factory=dict, description="Repository structure analysis")
    dependencies: Dict[str, Any] = Field(default_factory=dict, description="Dependency analysis")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Repository metadata")
    git_info: Optional[Dict[str, Any]] = Field(None, description="Git repository information")


class PlanningPhase(BaseModel):
    """A phase in the security review plan"""
    name: str = Field(..., description="Phase name")
    agent: str = Field(..., description="Agent responsible for this phase")
    tasks: List[str] = Field(default_factory=list, description="Tasks to execute")
    priority: int = Field(..., description="Execution priority")


class PlanningResult(BaseModel):
    """Result of security review planning"""
    repo_path: str = Field(..., description="Repository path")
    mode: str = Field(..., description="Analysis mode")
    tech_stack: Dict[str, Any] = Field(default_factory=dict, description="Detected technology stack")
    domain_profiles: List[str] = Field(default_factory=list, description="Applied domain profiles")
    phases: List[PlanningPhase] = Field(default_factory=list, description="Execution phases")
    estimated_duration: str = Field(..., description="Estimated completion time")


class ModuleConfig(BaseModel):
    """Module configuration schema"""
    name: str = Field(..., description="Module name")
    version: str = Field(..., description="Module version")
    description: str = Field(..., description="Module description")
    author: str = Field(..., description="Module author")
    tags: List[str] = Field(default_factory=list, description="Module tags")
    category: str = Field(..., description="Module category (scanner|auditor|tighten|report)")
    
    # Dependencies
    requires: List[str] = Field(default_factory=list, description="Required tools or modules")
    supports: List[str] = Field(default_factory=list, description="Supported languages/frameworks")
    
    # Configuration options
    options: Dict[str, Dict[str, Any]] = Field(default_factory=dict, description="Module options")
    
    # Execution settings
    timeout: int = Field(default=300, description="Execution timeout in seconds")
    concurrent: bool = Field(default=True, description="Can run concurrently with other modules")


class ConfigSchema(BaseModel):
    """Complete configuration schema"""
    
    class RepoConfig(BaseModel):
        path: Optional[str] = None
        exclude: List[str] = Field(default_factory=list)
        max_file_size: int = 1048576  # 1MB
    
    class LLMConfig(BaseModel):
        model: str = "gpt-4"
        max_tokens: int = 2000
        temperature: float = 0.1
        timeout: int = 60
    
    class RAGConfig(BaseModel):
        enabled: bool = True
        k: int = 5
        chunk_size: int = 1000
        chunk_overlap: int = 200
        embedding_model: str = "text-embedding-ada-002"
    
    class CVSSConfig(BaseModel):
        policy: str = "block_high"
    
    class CIConfig(BaseModel):
        block_on: List[str] = Field(default_factory=lambda: ["critical", "high"])
        changed_files_only: bool = False
    
    class OutputConfig(BaseModel):
        dir: str = "./output"
        format: str = "md"
    
    class RedactionConfig(BaseModel):
        enabled: bool = True
        patterns: List[str] = Field(default_factory=list)
    
    class SandboxConfig(BaseModel):
        enabled: bool = True
        timeout: int = 300
        memory_limit: str = "512MB"
    
    class ToolsConfig(BaseModel):
        enabled: List[str] = Field(default_factory=list)
        paths: Dict[str, str] = Field(default_factory=dict)
        configs: Dict[str, Dict[str, Any]] = Field(default_factory=dict)
    
    class LoggingConfig(BaseModel):
        level: str = "INFO"
        file: Optional[str] = None
        format: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # Main configuration sections
    repo: RepoConfig = Field(default_factory=RepoConfig)
    mode: str = "quick"
    domain: Dict[str, List[str]] = Field(default_factory=lambda: {"profiles": []})
    llm: LLMConfig = Field(default_factory=LLMConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    cvss: CVSSConfig = Field(default_factory=CVSSConfig)
    ci: CIConfig = Field(default_factory=CIConfig)
    output: OutputConfig = Field(default_factory=OutputConfig)
    redact: RedactionConfig = Field(default_factory=RedactionConfig)
    sandbox: SandboxConfig = Field(default_factory=SandboxConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


class DomainProfile(BaseModel):
    """Domain-specific security profile"""
    name: str = Field(..., description="Profile name (e.g., web3:solidity)")
    description: str = Field(..., description="Profile description")
    category: str = Field(..., description="Domain category (web2|web3)")
    
    # Technology matching
    languages: List[str] = Field(default_factory=list, description="Target languages")
    frameworks: List[str] = Field(default_factory=list, description="Target frameworks")
    file_patterns: List[str] = Field(default_factory=list, description="File patterns to match")
    
    # Security focus areas
    focus_areas: List[str] = Field(default_factory=list, description="Security focus areas")
    scanners: List[str] = Field(default_factory=list, description="Recommended scanners")
    audit_checklist: List[str] = Field(default_factory=list, description="Audit checklist items")
    
    # Risk categories
    high_risk_patterns: List[str] = Field(default_factory=list, description="High-risk code patterns")
    common_vulnerabilities: List[str] = Field(default_factory=list, description="Common vulnerability types")


class SessionInfo(BaseModel):
    """Information about an active session"""
    session_id: str = Field(..., description="Unique session identifier")
    workspace: str = Field(..., description="Associated workspace")
    created: datetime = Field(..., description="Session creation time")
    last_activity: datetime = Field(..., description="Last activity timestamp")
    status: str = Field(..., description="Session status (active|paused|completed)")
    context: Dict[str, Any] = Field(default_factory=dict, description="Session context")


class JobInfo(BaseModel):
    """Information about a background job"""
    job_id: str = Field(..., description="Unique job identifier")
    module: str = Field(..., description="Module being executed")
    status: str = Field(..., description="Job status (running|completed|failed)")
    started: datetime = Field(..., description="Job start time")
    completed: Optional[datetime] = Field(None, description="Job completion time")
    progress: float = Field(default=0.0, ge=0.0, le=1.0, description="Job progress (0.0-1.0)")
    result: Optional[Any] = Field(None, description="Job result")
    error: Optional[str] = Field(None, description="Error message if failed")


class AnalysisContext(BaseModel):
    """Context information for security analysis"""
    workspace_path: str = Field(..., description="Path to the analyzed workspace")
    repo_path: str = Field(..., description="Repository root path")
    target_files: List[str] = Field(default_factory=list, description="Files to analyze")
    excluded_files: List[str] = Field(default_factory=list, description="Files to exclude")
    languages: List[str] = Field(default_factory=list, description="Detected programming languages")
    frameworks: List[str] = Field(default_factory=list, description="Detected frameworks")
    technologies: Dict[str, Any] = Field(default_factory=dict, description="Technology stack information")
    domain_profiles: List[str] = Field(default_factory=list, description="Applied domain profiles")
    mode: str = Field(default="quick", description="Analysis mode")
    config: Dict[str, Any] = Field(default_factory=dict, description="Analysis configuration")


class SecurityPattern(BaseModel):
    """Security pattern for analysis"""
    name: str = Field(..., description="Pattern name")
    description: str = Field(..., description="Pattern description")
    category: str = Field(..., description="Pattern category")
    severity: str = Field(..., description="Default severity level")
    languages: List[str] = Field(default_factory=list, description="Applicable languages")
    patterns: List[str] = Field(default_factory=list, description="Code patterns to match")
    owasp_categories: List[str] = Field(default_factory=list, description="OWASP categories")
    cwe_ids: List[str] = Field(default_factory=list, description="CWE identifiers")


class VulnerabilityClass(BaseModel):
    """Vulnerability classification"""
    name: str = Field(..., description="Vulnerability class name")
    description: str = Field(..., description="Vulnerability description")
    category: str = Field(..., description="Vulnerability category")
    severity: str = Field(..., description="Severity level")
    owasp_categories: List[str] = Field(default_factory=list, description="OWASP categories")
    cwe_ids: List[str] = Field(default_factory=list, description="CWE identifiers")
    impact: str = Field(..., description="Potential impact")
    likelihood: str = Field(..., description="Likelihood of exploitation")


class ReportMetadata(BaseModel):
    """Report metadata information"""
    report_id: str = Field(..., description="Unique report identifier")
    generated_at: datetime = Field(..., description="Report generation timestamp")
    workspace: str = Field(..., description="Analyzed workspace")
    analysis_mode: str = Field(..., description="Analysis mode used")
    total_files: int = Field(..., description="Total files analyzed")
    total_findings: int = Field(..., description="Total findings discovered")
    severity_counts: Dict[str, int] = Field(default_factory=dict, description="Findings by severity")
    technologies: List[str] = Field(default_factory=list, description="Detected technologies")
    analysis_duration: float = Field(..., description="Analysis duration in seconds")


class RemediationRecommendation(BaseModel):
    """Remediation recommendation"""
    id: str = Field(..., description="Recommendation identifier")
    title: str = Field(..., description="Recommendation title")
    description: str = Field(..., description="Detailed description")
    type: str = Field(..., description="Recommendation type")
    priority: str = Field(..., description="Priority level")
    effort: str = Field(..., description="Implementation effort")
    impact: str = Field(..., description="Security impact")
    affected_findings: List[str] = Field(default_factory=list, description="Related finding IDs")
    implementation_steps: List[str] = Field(default_factory=list, description="Implementation steps")
    code_changes: Optional[str] = Field(None, description="Suggested code changes")
    verification_steps: List[str] = Field(default_factory=list, description="Verification steps")


class SecurityHardening(BaseModel):
    """Security hardening plan"""
    plan_id: str = Field(..., description="Hardening plan identifier")
    workspace: str = Field(..., description="Target workspace")
    generated_at: datetime = Field(..., description="Plan generation timestamp")
    security_posture: Dict[str, Any] = Field(default_factory=dict, description="Current security posture")
    hardening_categories: Dict[str, List[str]] = Field(default_factory=dict, description="Hardening by category")
    priority_recommendations: List[str] = Field(default_factory=list, description="Priority recommendations")
    implementation_roadmap: Dict[str, List[str]] = Field(default_factory=dict, description="Implementation roadmap")
    estimated_effort: str = Field(..., description="Estimated implementation effort")
    expected_impact: str = Field(..., description="Expected security impact")