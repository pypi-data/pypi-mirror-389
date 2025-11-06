"""
Simple CVSS classification for findings
"""

from typing import Dict, Any
from dataclasses import dataclass

@dataclass
class SimpleCVSS:
    """Simple CVSS-like scoring"""
    score: float
    severity: str
    vector: str = ""

class SimpleVulnerabilityClassifier:
    """Simple vulnerability classifier for generating CVSS-like scores"""
    
    def auto_score_finding(self, title: str, description: str, context: Dict[str, Any] = None) -> SimpleCVSS:
        """Generate a simple score based on title and description"""
        
        title_lower = title.lower()
        desc_lower = description.lower()
        
        # High severity keywords
        high_keywords = [
            'rce', 'remote code execution', 'sql injection', 'command injection',
            'authentication bypass', 'privilege escalation', 'reentrancy',
            'critical', 'arbitrary code'
        ]
        
        # Medium severity keywords  
        medium_keywords = [
            'xss', 'csrf', 'access control', 'authorization', 'sensitive data',
            'information disclosure', 'path traversal', 'deserialization',
            'overflow', 'integer overflow'
        ]
        
        # Low severity keywords
        low_keywords = [
            'weak crypto', 'insecure random', 'hardcoded', 'logging',
            'information leak', 'weak password', 'missing header'
        ]
        
        # Determine severity
        if any(keyword in title_lower or keyword in desc_lower for keyword in high_keywords):
            return SimpleCVSS(score=8.5, severity='high')
        elif any(keyword in title_lower or keyword in desc_lower for keyword in medium_keywords):
            return SimpleCVSS(score=6.0, severity='medium')
        elif any(keyword in title_lower or keyword in desc_lower for keyword in low_keywords):
            return SimpleCVSS(score=3.5, severity='low')
        else:
            return SimpleCVSS(score=5.0, severity='medium')  # Default