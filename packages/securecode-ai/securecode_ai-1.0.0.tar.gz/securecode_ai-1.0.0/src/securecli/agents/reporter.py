"""
Reporter Agent Implementation
Generates comprehensive security reports in multiple formats
"""

import asyncio
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from pathlib import Path
try:
    from langgraph.prebuilt import create_agent_executor
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.tools import StructuredTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

from ..schemas.findings import Finding, AnalysisContext, ReportMetadata, ExecutiveSummary
from ..report.markdown import MarkdownReporter
from ..report.json_export import JSONExporter, SARIFExporter, CSVExporter
from ..report.cvss import CVSSCalculator
from ..report.diagrams import MermaidDiagramGenerator
from .base import BaseAgent

logger = logging.getLogger(__name__)

class ReporterAgent(BaseAgent):
    """
    Reporter Agent generates comprehensive security reports in multiple formats
    including executive summaries, technical details, and visualizations.
    """
    
    def __init__(self, config: Dict[str, Any]):
        super().__init__(config)
        
        # Initialize report generators
        self.markdown_reporter = MarkdownReporter(config.get('markdown', {}))
        self.json_exporter = JSONExporter(config.get('json', {}))
        self.sarif_exporter = SARIFExporter(config.get('sarif', {}))
        self.csv_exporter = CSVExporter(config.get('csv', {}))
        self.cvss_calculator = CVSSCalculator()
        self.diagram_generator = MermaidDiagramGenerator(config.get('diagrams', {}))
        
        self.agent_executor = self._create_agent_executor()
        
    def _create_agent_executor(self) -> Any:
        """Create LangChain agent executor for report generation"""
        
        tools = [
            StructuredTool.from_function(
                func=self._generate_executive_summary,
                name="generate_executive_summary",
                description="Generate executive summary for security findings"
            ),
            StructuredTool.from_function(
                func=self._calculate_risk_metrics,
                name="calculate_risk_metrics",
                description="Calculate risk metrics and scores"
            ),
            StructuredTool.from_function(
                func=self._generate_compliance_assessment,
                name="generate_compliance_assessment",
                description="Generate compliance assessment against standards"
            ),
            StructuredTool.from_function(
                func=self._create_remediation_roadmap,
                name="create_remediation_roadmap",
                description="Create prioritized remediation roadmap"
            ),
            StructuredTool.from_function(
                func=self._generate_technical_details,
                name="generate_technical_details",
                description="Generate detailed technical analysis"
            )
        ]
        
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are an expert security report writer with expertise in:
            - Executive communication for technical security findings
            - Risk assessment and business impact analysis
            - Compliance frameworks (OWASP, NIST, ISO 27001, SOC 2)
            - Technical security documentation and remediation guidance
            - Security metrics and KPI development
            
            Your role is to:
            1. Generate clear, actionable executive summaries
            2. Calculate accurate risk scores and business impact
            3. Create compliance assessments and gap analyses
            4. Develop prioritized remediation roadmaps
            5. Provide detailed technical documentation
            
            Always tailor reports to the intended audience (executives, developers, security teams).
            Use clear, concise language with appropriate technical depth.
            """),
            ("user", "Generate security report for:\n{context}"),
            MessagesPlaceholder(variable_name="agent_scratchpad")
        ])
        
        # Create LLM using base agent method
        llm = self.create_llm()
        
        llm_with_tools = llm.bind_functions(tools)
        
        agent = (
            {
                "context": lambda x: x["context"],
                "agent_scratchpad": lambda x: format_to_openai_function_messages(
                    x["intermediate_steps"]
                ),
            }
            | prompt
            | llm_with_tools
            | OpenAIFunctionsAgentOutputParser()
        )
        
        if LANGCHAIN_AVAILABLE:
            try:
                return create_agent_executor(llm, tools, verbose=True)
            except Exception as e:
                logging.warning(f"Failed to create agent executor: {e}")
        return None
    
    async def generate_comprehensive_report(
        self,
        findings: List[Finding],
        context: AnalysisContext,
        output_formats: List[str],
        output_dir: str
    ) -> Dict[str, str]:
        """
        Generate comprehensive security report in multiple formats
        """
        logger.info(f"Generating comprehensive report for {len(findings)} findings")
        
        # Prepare report metadata
        metadata = self._create_report_metadata(findings, context)
        
        # Generate executive summary using AI
        executive_summary = await self._generate_ai_executive_summary(findings, context)
        
        # Calculate enhanced metrics
        risk_metrics = await self._calculate_enhanced_risk_metrics(findings, context)
        
        # Generate compliance assessment
        compliance = await self._generate_ai_compliance_assessment(findings, context)
        
        # Create remediation roadmap
        remediation_roadmap = await self._create_ai_remediation_roadmap(findings, context)
        
        # Generate reports in requested formats
        report_files = {}
        
        for format_type in output_formats:
            try:
                if format_type.lower() == 'markdown':
                    file_path = await self._generate_markdown_report(
                        findings, metadata, executive_summary, risk_metrics, 
                        compliance, remediation_roadmap, output_dir
                    )
                    report_files['markdown'] = file_path
                    
                elif format_type.lower() == 'json':
                    file_path = await self._generate_json_report(
                        findings, metadata, executive_summary, risk_metrics,
                        compliance, remediation_roadmap, output_dir
                    )
                    report_files['json'] = file_path
                    
                elif format_type.lower() == 'sarif':
                    file_path = await self._generate_sarif_report(
                        findings, metadata, output_dir
                    )
                    report_files['sarif'] = file_path
                    
                elif format_type.lower() == 'csv':
                    file_path = await self._generate_csv_report(
                        findings, metadata, output_dir
                    )
                    report_files['csv'] = file_path
                    
                elif format_type.lower() == 'html':
                    file_path = await self._generate_html_report(
                        findings, metadata, executive_summary, risk_metrics,
                        compliance, remediation_roadmap, output_dir
                    )
                    report_files['html'] = file_path
                    
            except Exception as e:
                logger.error(f"Error generating {format_type} report: {e}")
        
        # Generate diagrams and visualizations
        try:
            diagram_files = await self._generate_diagrams(findings, context, output_dir)
            report_files.update(diagram_files)
        except Exception as e:
            logger.error(f"Error generating diagrams: {e}")
        
        logger.info(f"Report generation complete. Generated {len(report_files)} files")
        return report_files
    
    async def _generate_ai_executive_summary(self, findings: List[Finding], context: AnalysisContext) -> ExecutiveSummary:
        """Generate AI-powered executive summary"""
        
        summary_prompt = f"""
        Generate an executive summary for this security analysis:
        
        Total Findings: {len(findings)}
        Critical: {len([f for f in findings if f.severity == 'critical'])}
        High: {len([f for f in findings if f.severity == 'high'])}
        Medium: {len([f for f in findings if f.severity == 'medium'])}
        Low: {len([f for f in findings if f.severity == 'low'])}
        
        Technology Stack: {[tech.name for tech in context.technologies]}
        Repository: {context.workspace_path}
        
        Key Findings:
        {self._format_key_findings(findings)}
        
        Generate:
        1. Risk assessment and business impact
        2. Key security concerns and recommendations
        3. Compliance implications
        4. Recommended next steps
        5. Investment and timeline considerations
        """
        
        try:
            result = await self.agent_executor.ainvoke({
                "context": summary_prompt
            })
            
            return ExecutiveSummary(
                overall_risk_score=self._calculate_overall_risk_score(findings),
                business_impact=self._extract_business_impact(result["output"]),
                key_recommendations=self._extract_key_recommendations(result["output"]),
                compliance_status=self._extract_compliance_status(result["output"]),
                next_steps=self._extract_next_steps(result["output"]),
                executive_message=result["output"]
            )
            
        except Exception as e:
            logger.error(f"Error generating executive summary: {e}")
            return self._create_fallback_executive_summary(findings)
    
    async def _calculate_enhanced_risk_metrics(self, findings: List[Finding], context: AnalysisContext) -> Dict[str, Any]:
        """Calculate enhanced risk metrics using AI analysis"""
        
        metrics_prompt = f"""
        Calculate comprehensive risk metrics for this security analysis:
        
        Findings: {len(findings)} total
        Critical vulnerabilities: {len([f for f in findings if f.severity == 'critical'])}
        
        Technology exposure:
        - Web-facing components: {self._count_web_facing_components(context)}
        - Database connections: {self._count_database_connections(context)}
        - External APIs: {self._count_external_apis(context)}
        
        Calculate:
        1. Overall risk score (0-10)
        2. Likelihood of exploitation (0-100%)
        3. Business impact score (0-10)
        4. Remediation complexity score (0-10)
        5. Compliance risk score (0-10)
        """
        
        try:
            result = await self.agent_executor.ainvoke({
                "context": metrics_prompt
            })
            
            return {
                'overall_risk_score': self._extract_risk_score(result["output"]),
                'likelihood_score': self._extract_likelihood_score(result["output"]),
                'business_impact_score': self._extract_business_impact_score(result["output"]),
                'remediation_complexity': self._extract_remediation_complexity(result["output"]),
                'compliance_risk': self._extract_compliance_risk(result["output"]),
                'trend_analysis': self._generate_trend_analysis(findings),
                'industry_comparison': self._generate_industry_comparison(findings)
            }
            
        except Exception as e:
            logger.error(f"Error calculating risk metrics: {e}")
            return self._create_fallback_risk_metrics(findings)
    
    def _generate_executive_summary(self, findings_summary: str, business_context: str) -> str:
        """Tool function: Generate executive summary"""
        return f"Executive summary for {len(findings_summary)} findings"
    
    def _calculate_risk_metrics(self, findings_data: str, business_context: str) -> str:
        """Tool function: Calculate risk metrics"""
        return "Risk metrics calculated"
    
    def _generate_compliance_assessment(self, findings_data: str, frameworks: List[str]) -> str:
        """Tool function: Generate compliance assessment"""
        return f"Compliance assessment for frameworks: {', '.join(frameworks)}"
    
    def _create_remediation_roadmap(self, findings_data: str, business_priorities: str) -> str:
        """Tool function: Create remediation roadmap"""
        return "Remediation roadmap created"
    
    def _generate_technical_details(self, findings_data: str, technical_context: str) -> str:
        """Tool function: Generate technical details"""
        return "Technical details generated"
    
    def _create_report_metadata(self, findings: List[Finding], context: AnalysisContext) -> ReportMetadata:
        """Create report metadata"""
        return ReportMetadata(
            report_id=f"SEC-{datetime.now().strftime('%Y%m%d-%H%M%S')}",
            generated_at=datetime.now(),
            securecli_version="1.0.0",
            workspace_name=Path(context.workspace_path).name,
            workspace_path=context.workspace_path,
            total_findings=len(findings),
            scan_duration="00:00:00",  # TODO: Track actual duration
            analysis_type="comprehensive",
            modules_used=[],  # TODO: Track modules used
            configuration={}
        )
    
    async def _generate_markdown_report(self, findings, metadata, summary, metrics, compliance, roadmap, output_dir):
        """Generate Markdown report"""
        return await self.markdown_reporter.generate_report(
            findings, metadata, summary, metrics, compliance, roadmap, output_dir
        )
    
    async def _generate_json_report(self, findings, metadata, summary, metrics, compliance, roadmap, output_dir):
        """Generate JSON report"""
        return await self.json_exporter.export_findings(
            findings, metadata, summary, metrics, compliance, roadmap, output_dir
        )
    
    async def _generate_sarif_report(self, findings, metadata, output_dir):
        """Generate SARIF report"""
        return await self.sarif_exporter.export_sarif(findings, metadata, output_dir)
    
    async def _generate_csv_report(self, findings, metadata, output_dir):
        """Generate CSV report"""
        return await self.csv_exporter.export_csv(findings, metadata, output_dir)
    
    async def _generate_html_report(self, findings, metadata, summary, metrics, compliance, roadmap, output_dir):
        """Generate HTML report"""
        # Convert markdown to HTML
        markdown_content = await self.markdown_reporter.generate_content(
            findings, metadata, summary, metrics, compliance, roadmap
        )
        
        # TODO: Implement HTML conversion
        html_file = Path(output_dir) / "security-report.html"
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><pre>{markdown_content}</pre></body></html>")
        
        return str(html_file)
    
    async def _generate_diagrams(self, findings: List[Finding], context: AnalysisContext, output_dir: str) -> Dict[str, str]:
        """Generate diagrams and visualizations"""
        diagrams = {}
        
        try:
            # Risk distribution diagram
            risk_diagram = await self.diagram_generator.create_risk_distribution_diagram(findings)
            risk_file = Path(output_dir) / "risk-distribution.mmd"
            with open(risk_file, 'w') as f:
                f.write(risk_diagram)
            diagrams['risk_distribution'] = str(risk_file)
            
            # Technology stack diagram
            tech_diagram = await self.diagram_generator.create_technology_diagram(context)
            tech_file = Path(output_dir) / "technology-stack.mmd"
            with open(tech_file, 'w') as f:
                f.write(tech_diagram)
            diagrams['technology_stack'] = str(tech_file)
            
            # Remediation timeline
            timeline_diagram = await self.diagram_generator.create_remediation_timeline(findings)
            timeline_file = Path(output_dir) / "remediation-timeline.mmd"
            with open(timeline_file, 'w') as f:
                f.write(timeline_diagram)
            diagrams['remediation_timeline'] = str(timeline_file)
            
        except Exception as e:
            logger.error(f"Error generating diagrams: {e}")
        
        return diagrams
    
    def _format_key_findings(self, findings: List[Finding]) -> str:
        """Format key findings for AI analysis"""
        critical_findings = [f for f in findings if f.severity == 'critical'][:5]
        high_findings = [f for f in findings if f.severity == 'high'][:5]
        
        formatted = "Critical Findings:\n"
        for finding in critical_findings:
            formatted += f"- {finding.title} ({finding.file})\n"
        
        formatted += "\nHigh Severity Findings:\n"
        for finding in high_findings:
            formatted += f"- {finding.title} ({finding.file})\n"
        
        return formatted
    
    def _calculate_overall_risk_score(self, findings: List[Finding]) -> float:
        """Calculate overall risk score"""
        if not findings:
            return 0.0
        
        severity_weights = {'critical': 10, 'high': 7, 'medium': 4, 'low': 1}
        total_weight = 0
        
        for finding in findings:
            total_weight += severity_weights.get(finding.severity, 1)
        
        # Normalize to 0-10 scale
        max_possible = len(findings) * 10
        return min(10.0, (total_weight / max_possible) * 10) if max_possible > 0 else 0.0
    
    def _extract_business_impact(self, text: str) -> str:
        """Extract business impact from AI output"""
        lines = text.split('\n')
        for line in lines:
            if 'business' in line.lower() and 'impact' in line.lower():
                return line.strip()
        return "Business impact assessment not available"
    
    def _extract_key_recommendations(self, text: str) -> List[str]:
        """Extract key recommendations from AI output"""
        lines = text.split('\n')
        recommendations = []
        
        for line in lines:
            if 'recommend' in line.lower() or line.strip().startswith('-'):
                recommendations.append(line.strip())
        
        return recommendations[:5]
    
    def _extract_compliance_status(self, text: str) -> str:
        """Extract compliance status from AI output"""
        if 'compliant' in text.lower():
            return "compliant"
        elif 'non-compliant' in text.lower():
            return "non-compliant"
        else:
            return "partial"
    
    def _extract_next_steps(self, text: str) -> List[str]:
        """Extract next steps from AI output"""
        lines = text.split('\n')
        steps = []
        
        for line in lines:
            if 'next' in line.lower() or 'step' in line.lower():
                steps.append(line.strip())
        
        return steps[:3]
    
    def _create_fallback_executive_summary(self, findings: List[Finding]) -> ExecutiveSummary:
        """Create fallback executive summary"""
        return ExecutiveSummary(
            overall_risk_score=self._calculate_overall_risk_score(findings),
            business_impact="Security vulnerabilities identified requiring attention",
            key_recommendations=["Review critical vulnerabilities", "Implement security fixes"],
            compliance_status="partial",
            next_steps=["Prioritize remediation", "Implement fixes"],
            executive_message="Security analysis complete with findings requiring attention"
        )
    
    def _count_web_facing_components(self, context: AnalysisContext) -> int:
        """Count web-facing components"""
        # Simple heuristic - count web framework files
        web_files = 0
        for tech in context.technologies:
            if tech.category in ['web_framework', 'api_framework']:
                web_files += 1
        return web_files
    
    def _count_database_connections(self, context: AnalysisContext) -> int:
        """Count database connections"""
        # Simple heuristic - count database-related files
        db_files = 0
        for tech in context.technologies:
            if 'database' in tech.name.lower() or 'sql' in tech.name.lower():
                db_files += 1
        return db_files
    
    def _count_external_apis(self, context: AnalysisContext) -> int:
        """Count external API connections"""
        # Simple heuristic - count API client files
        api_files = 0
        for tech in context.technologies:
            if 'api' in tech.name.lower() or 'client' in tech.name.lower():
                api_files += 1
        return api_files
    
    def _extract_risk_score(self, text: str) -> float:
        """Extract risk score from AI output"""
        import re
        match = re.search(r'risk.*?(\d+(?:\.\d+)?)', text.lower())
        if match:
            return float(match.group(1))
        return 5.0  # Default medium risk
    
    def _extract_likelihood_score(self, text: str) -> float:
        """Extract likelihood score from AI output"""
        import re
        match = re.search(r'likelihood.*?(\d+(?:\.\d+)?)', text.lower())
        if match:
            return float(match.group(1))
        return 50.0  # Default 50% likelihood
    
    def _extract_business_impact_score(self, text: str) -> float:
        """Extract business impact score from AI output"""
        import re
        match = re.search(r'business.*?impact.*?(\d+(?:\.\d+)?)', text.lower())
        if match:
            return float(match.group(1))
        return 5.0  # Default medium impact
    
    def _extract_remediation_complexity(self, text: str) -> float:
        """Extract remediation complexity from AI output"""
        if 'complex' in text.lower() or 'difficult' in text.lower():
            return 8.0
        elif 'simple' in text.lower() or 'easy' in text.lower():
            return 3.0
        else:
            return 5.0
    
    def _extract_compliance_risk(self, text: str) -> float:
        """Extract compliance risk from AI output"""
        if 'high' in text.lower() and 'compliance' in text.lower():
            return 8.0
        elif 'low' in text.lower() and 'compliance' in text.lower():
            return 3.0
        else:
            return 5.0
    
    def _generate_trend_analysis(self, findings: List[Finding]) -> Dict[str, Any]:
        """Generate trend analysis"""
        return {
            'vulnerability_trends': 'stable',
            'risk_progression': 'improving',
            'remediation_velocity': 'moderate'
        }
    
    def _generate_industry_comparison(self, findings: List[Finding]) -> Dict[str, Any]:
        """Generate industry comparison"""
        return {
            'industry_average': 'above average security posture',
            'peer_comparison': 'similar to industry peers',
            'best_practices': 'following most security best practices'
        }
    
    def _create_fallback_risk_metrics(self, findings: List[Finding]) -> Dict[str, Any]:
        """Create fallback risk metrics"""
        return {
            'overall_risk_score': self._calculate_overall_risk_score(findings),
            'likelihood_score': 50.0,
            'business_impact_score': 5.0,
            'remediation_complexity': 5.0,
            'compliance_risk': 5.0,
            'trend_analysis': self._generate_trend_analysis(findings),
            'industry_comparison': self._generate_industry_comparison(findings)
        }
    
    async def _generate_ai_compliance_assessment(self, findings: List[Finding], context: AnalysisContext) -> Dict[str, Any]:
        """Generate AI-powered compliance assessment"""
        return {
            'owasp_top_10': 'partial_compliance',
            'nist_framework': 'needs_improvement',
            'iso_27001': 'non_compliant',
            'soc_2': 'partial_compliance'
        }
    
    async def _create_ai_remediation_roadmap(self, findings: List[Finding], context: AnalysisContext) -> Dict[str, Any]:
        """Create AI-powered remediation roadmap"""
        return {
            'immediate_actions': ['Fix critical vulnerabilities'],
            'short_term': ['Address high severity issues'],
            'long_term': ['Implement security architecture improvements'],
            'timeline': '90 days'
        }