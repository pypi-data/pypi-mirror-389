"""
JSON report exporter for SecureCLI
Exports security findings and reports in structured JSON format
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional

from ..schemas.findings import Finding, ExecutiveSummary


class JSONExporter:
    """Exports security data in JSON format"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get('output.dir', './output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_findings(
        self,
        findings: List[Finding],
        output_path: Optional[str] = None
    ) -> str:
        """Export findings to JSON format"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"findings_{timestamp}.json"
        
        # Convert findings to dict format
        findings_data = [finding.dict() for finding in findings]
        
        # Create export structure
        export_data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "tool": "SecureCLI",
            "findings_count": len(findings),
            "findings": findings_data
        }
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    async def export_full_report(
        self,
        findings: List[Finding],
        executive_summary: ExecutiveSummary,
        metadata: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Export complete report in JSON format"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"security_report_{timestamp}.json"
        
        # Prepare comprehensive report
        report_data = {
            "version": "1.0",
            "generated_at": datetime.now().isoformat(),
            "tool": "SecureCLI",
            "metadata": self._prepare_metadata(metadata),
            "executive_summary": executive_summary.dict(),
            "statistics": self._calculate_statistics(findings),
            "findings": {
                "total": len(findings),
                "by_severity": self._group_by_severity(findings),
                "by_file": self._group_by_file(findings),
                "by_category": self._group_by_category(findings),
                "cross_file": self._get_cross_file_findings(findings),
                "details": [finding.dict() for finding in findings]
            }
        }
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(report_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    async def export_sarif(
        self,
        findings: List[Finding],
        metadata: Dict[str, Any],
        output_path: Optional[str] = None
    ) -> str:
        """Export findings in SARIF format for CI/CD integration"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"security_results_{timestamp}.sarif"
        
        # Create SARIF structure
        sarif_data = {
            "version": "2.1.0",
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "SecureCLI",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/securecli/securecli",
                            "rules": self._generate_sarif_rules(findings)
                        }
                    },
                    "results": self._convert_to_sarif_results(findings),
                    "invocations": [
                        {
                            "executionSuccessful": True,
                            "startTimeUtc": metadata.get('scan_start', datetime.now().isoformat()),
                            "endTimeUtc": metadata.get('scan_end', datetime.now().isoformat())
                        }
                    ]
                }
            ]
        }
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sarif_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    async def export_csv(
        self,
        findings: List[Finding],
        output_path: Optional[str] = None
    ) -> str:
        """Export findings summary in CSV format"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"findings_summary_{timestamp}.csv"
        
        import csv
        
        # Define CSV headers
        headers = [
            'File', 'Title', 'Severity', 'CVSS_Score', 'Lines', 
            'OWASP', 'CWE', 'Tool', 'Description', 'Recommendation'
        ]
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)
            
            for finding in findings:
                # Prepare row data
                row = [
                    finding.file,
                    finding.title,
                    finding.severity,
                    finding.cvss_v4.score,
                    finding.lines,
                    '; '.join(finding.owasp),
                    '; '.join(finding.cwe),
                    '; '.join([evidence.tool for evidence in finding.tool_evidence]),
                    finding.description[:200] + '...' if len(finding.description) > 200 else finding.description,
                    finding.recommendation[:200] + '...' if len(finding.recommendation) > 200 else finding.recommendation
                ]
                writer.writerow(row)
        
        return str(output_path)
    
    def _prepare_metadata(self, metadata: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare metadata for JSON export"""
        return {
            "repo_path": metadata.get('repo_path', 'Unknown'),
            "scan_mode": metadata.get('mode', 'quick'),
            "domain_profiles": metadata.get('domain_profiles', []),
            "tools_used": metadata.get('tools_used', []),
            "scan_duration": metadata.get('scan_duration', 'Unknown'),
            "target_files": metadata.get('target_files', 0),
            "scanned_files": metadata.get('scanned_files', 0),
            "scan_start": metadata.get('scan_start'),
            "scan_end": metadata.get('scan_end')
        }
    
    def _calculate_statistics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Calculate statistics for JSON export"""
        if not findings:
            return {
                "total_findings": 0,
                "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
                "files_affected": 0,
                "avg_cvss_score": 0.0
            }
        
        stats = {
            "total_findings": len(findings),
            "by_severity": {"Critical": 0, "High": 0, "Medium": 0, "Low": 0},
            "files_affected": len(set(f.file for f in findings)),
            "avg_cvss_score": sum(f.cvss_v4.score for f in findings) / len(findings),
            "categories": {},
            "tools": {}
        }
        
        for finding in findings:
            # Count by severity
            stats["by_severity"][finding.severity] += 1
            
            # Count categories
            for category in finding.owasp + finding.cwe:
                stats["categories"][category] = stats["categories"].get(category, 0) + 1
            
            # Count tools
            for evidence in finding.tool_evidence:
                tool = evidence.tool
                stats["tools"][tool] = stats["tools"].get(tool, 0) + 1
        
        return stats
    
    def _group_by_severity(self, findings: List[Finding]) -> Dict[str, List[Dict[str, Any]]]:
        """Group findings by severity"""
        groups = {"Critical": [], "High": [], "Medium": [], "Low": []}
        
        for finding in findings:
            if finding.severity in groups:
                groups[finding.severity].append(finding.dict())
        
        return groups
    
    def _group_by_file(self, findings: List[Finding]) -> Dict[str, List[Dict[str, Any]]]:
        """Group findings by file"""
        groups = {}
        
        for finding in findings:
            file_path = finding.file
            if file_path not in groups:
                groups[file_path] = []
            groups[file_path].append(finding.dict())
        
        return groups
    
    def _group_by_category(self, findings: List[Finding]) -> Dict[str, List[Dict[str, Any]]]:
        """Group findings by OWASP/CWE categories"""
        groups = {}
        
        for finding in findings:
            categories = finding.owasp + finding.cwe
            for category in categories:
                if category not in groups:
                    groups[category] = []
                groups[category].append(finding.dict())
        
        return groups
    
    def _get_cross_file_findings(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Get cross-file findings"""
        cross_file = []
        
        for finding in findings:
            if finding.cross_file:
                cross_file.append(finding.dict())
        
        return cross_file
    
    def _generate_sarif_rules(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Generate SARIF rules from findings"""
        rules = {}
        
        for finding in findings:
            for evidence in finding.tool_evidence:
                rule_id = f"{evidence.tool}_{evidence.id}"
                
                if rule_id not in rules:
                    rules[rule_id] = {
                        "id": rule_id,
                        "name": finding.title,
                        "shortDescription": {
                            "text": finding.title
                        },
                        "fullDescription": {
                            "text": finding.description
                        },
                        "defaultConfiguration": {
                            "level": self._severity_to_sarif_level(finding.severity)
                        },
                        "properties": {
                            "tags": finding.owasp + finding.cwe,
                            "security-severity": str(finding.cvss_v4.score)
                        }
                    }
        
        return list(rules.values())
    
    def _convert_to_sarif_results(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Convert findings to SARIF results"""
        results = []
        
        for finding in findings:
            # Convert line numbers
            lines = finding.lines
            start_line = 1
            end_line = 1
            
            if '-' in lines:
                parts = lines.split('-')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    start_line = int(parts[0])
                    end_line = int(parts[1])
            elif lines.isdigit():
                start_line = end_line = int(lines)
            
            for evidence in finding.tool_evidence:
                rule_id = f"{evidence.tool}_{evidence.id}"
                
                result = {
                    "ruleId": rule_id,
                    "message": {
                        "text": finding.description
                    },
                    "locations": [
                        {
                            "physicalLocation": {
                                "artifactLocation": {
                                    "uri": finding.file
                                },
                                "region": {
                                    "startLine": start_line,
                                    "endLine": end_line
                                }
                            }
                        }
                    ],
                    "level": self._severity_to_sarif_level(finding.severity),
                    "properties": {
                        "cvss_score": finding.cvss_v4.score,
                        "owasp": finding.owasp,
                        "cwe": finding.cwe
                    }
                }
                results.append(result)
        
        return results
    
    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level"""
        mapping = {
            "Critical": "error",
            "High": "error", 
            "Medium": "warning",
            "Low": "note"
        }
        return mapping.get(severity, "warning")


class SARIFExporter:
    """Exports security findings in SARIF format"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get('output.dir', './output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_findings(
        self,
        findings: List[Finding],
        output_path: Optional[str] = None
    ) -> str:
        """Export findings to SARIF format"""
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"findings_{timestamp}.sarif"
        
        # Create SARIF structure
        sarif_data = {
            "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
            "version": "2.1.0",
            "runs": [
                {
                    "tool": {
                        "driver": {
                            "name": "SecureCLI",
                            "version": "1.0.0",
                            "informationUri": "https://github.com/securecli/securecli"
                        }
                    },
                    "results": self._convert_findings_to_sarif(findings)
                }
            ]
        }
        
        # Write to file
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(sarif_data, f, indent=2, ensure_ascii=False)
        
        return str(output_path)
    
    def _convert_findings_to_sarif(self, findings: List[Finding]) -> List[Dict[str, Any]]:
        """Convert findings to SARIF results format"""
        results = []
        
        for finding in findings:
            # Convert line numbers
            lines = finding.lines
            start_line = 1
            end_line = 1
            
            if '-' in lines:
                parts = lines.split('-')
                if len(parts) == 2 and parts[0].isdigit() and parts[1].isdigit():
                    start_line = int(parts[0])
                    end_line = int(parts[1])
            elif lines.isdigit():
                start_line = end_line = int(lines)
            
            result = {
                "ruleId": finding.title,
                "message": {
                    "text": finding.description
                },
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {
                                "uri": finding.file
                            },
                            "region": {
                                "startLine": start_line,
                                "endLine": end_line
                            }
                        }
                    }
                ],
                "level": self._severity_to_sarif_level(finding.severity),
                "properties": {
                    "cvss_score": finding.cvss_v4.score,
                    "owasp": finding.owasp,
                    "cwe": finding.cwe,
                    "snippet": finding.snippet,
                    "recommendation": finding.recommendation
                }
            }
            results.append(result)
        
        return results
    
    def _severity_to_sarif_level(self, severity: str) -> str:
        """Convert severity to SARIF level"""
        mapping = {
            "Critical": "error",
            "High": "error", 
            "Medium": "warning",
            "Low": "note"
        }
        return mapping.get(severity, "warning")


class CSVExporter:
    """Exports security findings in CSV format"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.output_dir = Path(config.get('output.dir', './output'))
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    async def export_findings(
        self,
        findings: List[Finding],
        output_path: Optional[str] = None
    ) -> str:
        """Export findings to CSV format"""
        import csv
        
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.output_dir / f"findings_{timestamp}.csv"
        
        # Define CSV headers
        headers = [
            'file', 'title', 'description', 'lines', 'severity', 
            'cvss_score', 'impact', 'owasp', 'cwe', 'recommendation'
        ]
        
        # Write CSV
        with open(output_path, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(headers)
            
            for finding in findings:
                row = [
                    finding.file,
                    finding.title,
                    finding.description,
                    finding.lines,
                    finding.severity,
                    finding.cvss_v4.score,
                    finding.impact,
                    ';'.join(finding.owasp),
                    ';'.join(finding.cwe),
                    finding.recommendation
                ]
                writer.writerow(row)
        
        return str(output_path)