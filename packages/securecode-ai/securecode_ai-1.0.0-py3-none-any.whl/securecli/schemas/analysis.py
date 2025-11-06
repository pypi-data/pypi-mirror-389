"""
SecureCLI Analysis Schemas
Data models for scan results, findings, and analysis outputs
"""

from datetime import datetime
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass, field
from enum import Enum
import uuid

from .security import Severity, Category, Finding

@dataclass
class SecurityMetrics:
    """Security metrics and statistics"""
    total_findings: int = 0
    critical_count: int = 0
    high_count: int = 0
    medium_count: int = 0
    low_count: int = 0
    info_count: int = 0
    files_analyzed: int = 0
    tools_used: List[str] = field(default_factory=list)

@dataclass
class AnalysisResult:
    """Complete analysis result"""
    workspace_path: str
    scan_mode: str
    findings: List[Finding] = field(default_factory=list)
    metrics: SecurityMetrics = field(default_factory=SecurityMetrics)
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class ScanResult:
    """Complete scan result with findings and metadata"""
    target_path: str
    languages: List[str]
    tools_used: List[str]
    findings: List[Finding]
    metrics: Dict[str, Any]
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    scan_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'scan_id': self.scan_id,
            'target_path': self.target_path,
            'languages': self.languages,
            'tools_used': self.tools_used,
            'findings': [f.to_dict() for f in self.findings],
            'metrics': self.metrics,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'error_message': self.error_message
        }

@dataclass
class ComplianceCheck:
    """Compliance framework check result"""
    framework: str
    control_id: str
    control_name: str
    description: str
    passed: bool
    findings_count: int
    related_findings: List[str]
    severity: Severity
    check_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'check_id': self.check_id,
            'framework': self.framework,
            'control_id': self.control_id,
            'control_name': self.control_name,
            'description': self.description,
            'passed': self.passed,
            'findings_count': self.findings_count,
            'related_findings': self.related_findings,
            'severity': self.severity.value
        }

@dataclass
class AuditResult:
    """Complete audit result with compliance and risk analysis"""
    target_path: str
    scan_result: Optional[ScanResult]
    compliance_checks: List[ComplianceCheck]
    risk_analysis: Dict[str, Any]
    remediation_plan: List[Dict[str, Any]]
    trend_data: Dict[str, Any]
    audit_metrics: Dict[str, Any]
    frameworks_checked: List[str]
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    audit_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'audit_id': self.audit_id,
            'target_path': self.target_path,
            'scan_result': self.scan_result.to_dict() if self.scan_result else None,
            'compliance_checks': [c.to_dict() for c in self.compliance_checks],
            'risk_analysis': self.risk_analysis,
            'remediation_plan': self.remediation_plan,
            'trend_data': self.trend_data,
            'audit_metrics': self.audit_metrics,
            'frameworks_checked': self.frameworks_checked,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'error_message': self.error_message
        }

@dataclass
class LanguageDetectionResult:
    """Result of language detection analysis"""
    target_path: str
    detected_languages: Dict[str, Dict[str, Any]]
    total_files: int
    analyzed_files: int
    language_distribution: Dict[str, float]
    file_extensions: Dict[str, int]
    largest_files: List[Dict[str, Any]]
    detection_confidence: float
    detection_time: datetime = field(default_factory=datetime.now)
    detection_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'detection_id': self.detection_id,
            'target_path': self.target_path,
            'detected_languages': self.detected_languages,
            'total_files': self.total_files,
            'analyzed_files': self.analyzed_files,
            'language_distribution': self.language_distribution,
            'file_extensions': self.file_extensions,
            'largest_files': self.largest_files,
            'detection_confidence': self.detection_confidence,
            'detection_time': self.detection_time.isoformat()
        }

@dataclass
class GitHubAnalysisResult:
    """Result of GitHub repository analysis"""
    repository_url: str
    repository_name: str
    branch: str
    clone_path: str
    languages_detected: Dict[str, Any]
    scan_result: Optional[ScanResult]
    files_analyzed: int
    total_files: int
    analysis_mode: str
    github_metadata: Dict[str, Any]
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    success: bool
    error_message: Optional[str] = None
    analysis_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'analysis_id': self.analysis_id,
            'repository_url': self.repository_url,
            'repository_name': self.repository_name,
            'branch': self.branch,
            'clone_path': self.clone_path,
            'languages_detected': self.languages_detected,
            'scan_result': self.scan_result.to_dict() if self.scan_result else None,
            'files_analyzed': self.files_analyzed,
            'total_files': self.total_files,
            'analysis_mode': self.analysis_mode,
            'github_metadata': self.github_metadata,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat(),
            'duration_seconds': self.duration_seconds,
            'success': self.success,
            'error_message': self.error_message
        }

@dataclass
class ReportSection:
    """Section of a security report"""
    title: str
    content: str
    section_type: str
    priority: int
    metadata: Dict[str, Any] = field(default_factory=dict)
    subsections: List['ReportSection'] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'title': self.title,
            'content': self.content,
            'section_type': self.section_type,
            'priority': self.priority,
            'metadata': self.metadata,
            'subsections': [s.to_dict() for s in self.subsections]
        }

@dataclass
class SecurityReport:
    """Complete security analysis report"""
    title: str
    executive_summary: str
    target_info: Dict[str, Any]
    scan_results: List[ScanResult]
    audit_results: List[AuditResult]
    sections: List[ReportSection]
    recommendations: List[str]
    appendices: Dict[str, Any]
    metadata: Dict[str, Any]
    generated_at: datetime = field(default_factory=datetime.now)
    report_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'report_id': self.report_id,
            'title': self.title,
            'executive_summary': self.executive_summary,
            'target_info': self.target_info,
            'scan_results': [s.to_dict() for s in self.scan_results],
            'audit_results': [a.to_dict() for a in self.audit_results],
            'sections': [s.to_dict() for s in self.sections],
            'recommendations': self.recommendations,
            'appendices': self.appendices,
            'metadata': self.metadata,
            'generated_at': self.generated_at.isoformat()
        }

class AnalysisStatus(Enum):
    """Status of an analysis operation"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class AnalysisJob:
    """Analysis job tracking"""
    job_id: str
    job_type: str
    target: str
    status: AnalysisStatus
    progress: float
    result: Optional[Any] = None
    error_message: Optional[str] = None
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'job_id': self.job_id,
            'job_type': self.job_type,
            'target': self.target,
            'status': self.status.value,
            'progress': self.progress,
            'result': self.result.to_dict() if hasattr(self.result, 'to_dict') else self.result,
            'error_message': self.error_message,
            'created_at': self.created_at.isoformat(),
            'started_at': self.started_at.isoformat() if self.started_at else None,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None,
            'metadata': self.metadata
        }

@dataclass
class ToolExecution:
    """Individual tool execution result"""
    tool_name: str
    tool_version: Optional[str]
    command: str
    exit_code: int
    stdout: str
    stderr: str
    findings: List[Finding]
    execution_time: float
    success: bool
    start_time: datetime
    end_time: datetime
    execution_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'execution_id': self.execution_id,
            'tool_name': self.tool_name,
            'tool_version': self.tool_version,
            'command': self.command,
            'exit_code': self.exit_code,
            'stdout': self.stdout,
            'stderr': self.stderr,
            'findings': [f.to_dict() for f in self.findings],
            'execution_time': self.execution_time,
            'success': self.success,
            'start_time': self.start_time.isoformat(),
            'end_time': self.end_time.isoformat()
        }

@dataclass
class ProjectMetadata:
    """Metadata about analyzed project"""
    project_name: str
    project_path: str
    project_type: str
    languages: List[str]
    frameworks: List[str]
    dependencies: Dict[str, List[str]]
    file_count: int
    total_lines: int
    git_info: Optional[Dict[str, Any]] = None
    build_info: Optional[Dict[str, Any]] = None
    last_modified: Optional[datetime] = None
    size_bytes: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation"""
        return {
            'project_name': self.project_name,
            'project_path': self.project_path,
            'project_type': self.project_type,
            'languages': self.languages,
            'frameworks': self.frameworks,
            'dependencies': self.dependencies,
            'file_count': self.file_count,
            'total_lines': self.total_lines,
            'git_info': self.git_info,
            'build_info': self.build_info,
            'last_modified': self.last_modified.isoformat() if self.last_modified else None,
            'size_bytes': self.size_bytes
        }

# Export all schema classes
__all__ = [
    'ScanResult',
    'ComplianceCheck', 
    'AuditResult',
    'LanguageDetectionResult',
    'GitHubAnalysisResult',
    'ReportSection',
    'SecurityReport',
    'AnalysisStatus',
    'AnalysisJob',
    'ToolExecution',
    'ProjectMetadata',
]