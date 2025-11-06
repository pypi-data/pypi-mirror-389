"""
Agents Package
Multi-agent security analysis system with specialized roles
"""

from .base import BaseAgent, AgentOrchestrator
from .scanner import ScannerAgent  
from .auditor import AuditorAgent
from .refactor import RefactorAgent
from .reporter import ReporterAgent

def create_agent_orchestrator(config):
    """Create an agent orchestrator with the given config"""
    return AgentOrchestrator(config)

__all__ = [
    'BaseAgent',
    'ScannerAgent',
    'AuditorAgent', 
    'RefactorAgent',
    'ReporterAgent',
    'AgentOrchestrator',
    'create_agent_orchestrator'
]