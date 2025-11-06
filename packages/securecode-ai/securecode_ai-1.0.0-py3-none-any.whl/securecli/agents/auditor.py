"""
Auditor Agent Implementation
Performs AI-powered deep security analysis using LLMs
"""

import os
import asyncio
import logging
import warnings
from typing import Dict, List, Any, Optional, Tuple
import re

# Suppress all warnings for clean output
os.environ['PYTHONWARNINGS'] = 'ignore'
warnings.filterwarnings("ignore")
warnings.simplefilter("ignore")

# Check if LangChain is available
try:
    from langgraph.prebuilt import create_agent_executor
    from langchain_openai import ChatOpenAI
    from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
    from langchain_core.messages import BaseMessage
    from langchain_core.tools import StructuredTool
    LANGCHAIN_AVAILABLE = True
except ImportError:
    LANGCHAIN_AVAILABLE = False

# Import custom modules - handle import errors gracefully
try:
    from ..schemas.findings import Finding, AnalysisContext, SecurityPattern, VulnerabilityClass, CVSSv4, ToolEvidence
    from ..analysis import annotate_cross_file_context
except ImportError:
    # Define minimal schemas if not available
    from dataclasses import dataclass
    from typing import Optional, List
    
    @dataclass
    class CVSSv4:
        score: float
        vector: str
    
    @dataclass 
    class ToolEvidence:
        tool: str
        id: str
        raw: str
    
    @dataclass
    class Finding:
        file: str
        title: str
        description: str
        lines: str
        impact: str
        severity: str
        cvss_v4: CVSSv4
        snippet: str
        recommendation: str
        sample_fix: str
        poc: str
        owasp: List[str]
        cwe: List[str]
        references: List[str]
        cross_file: List[str]
        tool_evidence: List[ToolEvidence]
    
    @dataclass
    class SecurityPattern:
        name: str
        description: str
        category: str
        patterns: List[str]
        languages: List[str]
        severity: str
    
    @dataclass
    class AnalysisContext:
        workspace_path: str
        repo_path: str
        target_files: List[str]
        languages: List[str]
        technologies: Dict[str, Any]

try:
    from ..rag.vectorstore import CodeVectorStore
    from ..rag.embeddings import CodeEmbedder
except ImportError:
    # Mock classes if not available
    class CodeEmbedder:
        def __init__(self, config):
            self.embeddings = None
    
    class CodeVectorStore:
        def __init__(self, embeddings, storage_path, store_type):
            self.vectorstore = None
        
        async def load_index(self):
            pass
        
        async def similarity_search(self, query, k=5):
            return []

try:
    from .base import BaseAgent
except ImportError:
    # Mock base class if not available
    class BaseAgent:
        def __init__(self, config):
            self.config = config
            self.logger = logging.getLogger(__name__)
        
        def handle_error(self, error, context):
            return {
                'success': False,
                'error': str(error),
                'context': context
            }

logger = logging.getLogger(__name__)

class AuditorAgent(BaseAgent):
    """
    Auditor Agent performs AI-powered security analysis using LLMs
    and retrieval-augmented generation for context-aware vulnerability detection.
    """
    
    def __init__(self, config: Dict[str, Any]):
        # Extract and properly structure configuration for base agent
        agent_config = {
            'llm_model': config.get('llm', {}).get('model', 'gpt-4'),
            'temperature': config.get('llm', {}).get('temperature', 0.1),
            'max_tokens': config.get('llm', {}).get('max_tokens', 4000),
            'timeout': config.get('llm', {}).get('timeout', 300),
            'llm_provider': config.get('llm', {}).get('provider', 'auto'),
            'local_model': config.get('local_model', {}),
            'retry_attempts': 3
        }
        super().__init__(agent_config)
        
        # Initialize embedder first
        self.embedder = CodeEmbedder(config.get('embeddings', {}))
        
        # Initialize vector store with proper parameters
        vector_store_config = config.get('vector_store', {})
        storage_path = vector_store_config.get('storage_path', '.securecli/vectorstore')
        self.vector_store = CodeVectorStore(
            embeddings=self.embedder.embeddings,
            storage_path=storage_path,
            store_type=vector_store_config.get('store_type', 'faiss')
        )
        
        # Initialize LangChain components if available
        if LANGCHAIN_AVAILABLE:
            self.memory = ConversationBufferWindowMemory(k=10, return_messages=True)
            self.agent_executor = self._create_agent_executor()
        else:
            self.memory = None
            self.agent_executor = None
        
        # Security patterns database
        self.security_patterns = self._load_security_patterns()
        
    def _load_security_patterns(self) -> List[SecurityPattern]:
        """Load known security patterns and vulnerability signatures"""
        patterns = [
            SecurityPattern(
                name="sql_injection",
                description="SQL injection vulnerability patterns",
                category="injection",
                patterns=["f\"SELECT * FROM", "WHERE {}", "ORDER BY {}", "+ WHERE +"],
                languages=["python", "php", "java", "csharp"],
                severity="critical"
            ),
            SecurityPattern(
                name="xss_vulnerability", 
                description="Cross-site scripting vulnerability patterns",
                category="injection",
                patterns=["dangerouslySetInnerHTML", "innerHTML =", "document.write(", "eval("],
                languages=["javascript", "typescript"],
                severity="high"
            ),
            SecurityPattern(
                name="hardcoded_secrets",
                description="Hardcoded credentials and secrets",
                category="secrets",
                patterns=["password =", "api_key =", "secret =", "token ="],
                languages=["python", "javascript", "java", "go"],
                severity="critical"
            ),
            SecurityPattern(
                name="command_injection",
                description="Command injection vulnerability patterns",
                category="injection", 
                patterns=["os.system(", "subprocess.call(", "exec(", "shell_exec("],
                languages=["python", "php", "ruby"],
                severity="critical"
            ),
            SecurityPattern(
                name="reentrancy",
                description="Smart contract reentrancy vulnerability",
                category="smart_contract",
                patterns=[".call{value:", "external call", "state change after call"],
                languages=["solidity"],
                severity="critical"
            ),
            SecurityPattern(
                name="integer_overflow",
                description="Integer overflow/underflow vulnerabilities",
                category="smart_contract",
                patterns=["unchecked {", "assembly {", "SafeMath"],
                languages=["solidity"],
                severity="high"
            )
        ]
        return patterns
    
    def _create_agent_executor(self) -> Optional[Any]:
        """Create LangChain agent executor for security auditing"""
        if not LANGCHAIN_AVAILABLE:
            return None
        
        try:
            # Create tools for code analysis
            tools = [
                StructuredTool.from_function(
                    func=self._analyze_code_block,
                    name="analyze_code_block",
                    description="Analyze a specific code block for security vulnerabilities"
                ),
                StructuredTool.from_function(
                    func=self._search_similar_vulnerabilities,
                    name="search_similar_vulnerabilities",
                    description="Search for similar vulnerability patterns in the codebase"
                ),
                StructuredTool.from_function(
                    func=self._assess_vulnerability_impact,
                    name="assess_vulnerability_impact",
                    description="Assess the impact and exploitability of a vulnerability"
                ),
                StructuredTool.from_function(
                    func=self._generate_remediation_advice,
                    name="generate_remediation_advice", 
                    description="Generate specific remediation advice for a vulnerability"
                )
            ]
            
            # Create prompt template
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert security auditor with deep knowledge of:
                - OWASP Top 10 vulnerabilities and secure coding practices
                - Smart contract security patterns and common attack vectors
                - Static analysis techniques and false positive reduction
                - Risk assessment and vulnerability impact analysis
                
                Your role is to:
                1. Analyze code for security vulnerabilities using context and patterns
                2. Reduce false positives through intelligent reasoning
                3. Provide detailed vulnerability assessments with CVSS scoring
                4. Generate actionable remediation guidance
                5. Identify complex multi-file vulnerabilities
                
                Use the available tools to perform thorough security analysis.
                Always provide confidence scores and reasoning for your findings.
                """),
                ("user", "Perform security audit on the following context:\n{context}"),
                MessagesPlaceholder(variable_name="chat_history"),
                MessagesPlaceholder(variable_name="agent_scratchpad")
            ])
            
            # Create LLM using base agent method
            llm = self.create_llm()
            if not llm:
                return None
            
            # Check if this is a local model that doesn't support function calling
            is_local_model = hasattr(llm, 'manager') and hasattr(llm.manager, 'config')
            
            logger.debug(f"LLM type: {type(llm)}, has manager: {hasattr(llm, 'manager')}")
            if hasattr(llm, 'manager'):
                logger.debug(f"Manager type: {type(llm.manager)}, has config: {hasattr(llm.manager, 'config')}")
            
            if is_local_model:
                # For local models, skip agent executor creation as they don't support function calling
                logger.warning("Skipping agent executor creation for local model (no function calling support)")
                return None
            
            # Bind tools to LLM (only for API models)
            llm_with_tools = llm.bind_functions(tools)
            
            # Create agent
            agent = (
                {
                    "context": lambda x: x["context"],
                    "chat_history": lambda x: x.get("chat_history", []),
                    "agent_scratchpad": lambda x: format_to_openai_function_messages(
                        x["intermediate_steps"]
                    ),
                }
                | prompt
                | llm_with_tools
                | OpenAIFunctionsAgentOutputParser()
            )
            
            return AgentExecutor(
                agent=agent, 
                tools=tools, 
                memory=self.memory,
                verbose=False,
                max_iterations=5
            )
        except Exception as e:
            # Suppress expected errors when local model is not available
            if "Local model not available" in str(e) or "model requires more system memory" in str(e):
                logger.debug(f"Agent executor not available (local model issue): {e}")
            else:
                logger.error(f"Error creating agent executor: {e}")
            return None
    
    async def perform_audit(self, context: AnalysisContext, scanner_findings: List[Finding]) -> List[Finding]:
        """
        Main method to perform AI-powered security audit
        """
        logger.info(f"Starting security audit for {context.workspace_path}")
        
        try:
            # Prepare code context for analysis
            code_context = await self._prepare_code_context(context)
            
            # Analyze scanner findings for false positives
            validated_findings = await self._validate_scanner_findings(scanner_findings, code_context)
            
            # Perform deep code analysis for new vulnerabilities
            ai_findings = await self._perform_deep_analysis(code_context, context)
            
            # Perform line-by-line analysis on source files
            line_by_line_findings = await self.perform_line_by_line_analysis(context.target_files, context)
            
            # Cross-file vulnerability analysis
            cross_file_findings = await self._analyze_cross_file_vulnerabilities(code_context, context)
            
            # Combine all findings
            all_findings = validated_findings + ai_findings + line_by_line_findings + cross_file_findings
            
            # Enrich all findings with AST-based cross-file tracing
            if context.workspace_path and all_findings:
                try:
                    logger.info("Enriching findings with cross-file call graph traces")
                    annotate_cross_file_context(context.workspace_path, all_findings)
                    logger.info(f"Added cross-file traces to {sum(1 for f in all_findings if f.cross_file)} findings")
                except Exception as e:
                    logger.warning(f"Cross-file enrichment failed: {e}")
            
            # Remove duplicates and rank by confidence
            final_findings = self._deduplicate_and_rank(all_findings)
            
            logger.info(f"Security audit complete. Found {len(final_findings)} validated findings")
            return final_findings
        
        except Exception as e:
            logger.error(f"Error in perform_audit: {e}")
            return []
    
    async def _prepare_code_context(self, context: AnalysisContext) -> Dict[str, Any]:
        """
        Prepare code context for AI analysis including embeddings and cross-references
        """
        logger.info("Preparing code context for analysis")
        
        try:
            # Initialize vector store (skip repository storage for now)
            await self.vector_store.load_index()
        except Exception as e:
            logger.warning(f"Vector store initialization failed: {e}")
        
        # Extract key code patterns and structures
        code_context = {
            'technologies': context.technologies,
            'entry_points': await self._identify_entry_points(context),
            'data_flows': await self._analyze_data_flows(context),
            'security_boundaries': await self._identify_security_boundaries(context)
        }
        
        return code_context
    
    async def _validate_scanner_findings(self, findings: List[Finding], code_context: Dict[str, Any]) -> List[Finding]:
        """
        Validate scanner findings to reduce false positives using AI reasoning
        """
        logger.info(f"Validating {len(findings)} scanner findings")
        
        validated_findings = []
        
        for finding in findings:
            try:
                # Parse line number from lines field
                line_number = self._extract_line_number(finding.lines)
                
                # Get surrounding code context
                context_code = await self._get_code_context(finding.file, line_number)
                
                # Use LLM to assess if finding is a real vulnerability
                validation_prompt = f"""
                Analyze this security finding to determine if it's a real vulnerability or false positive:
                
                Finding: {finding.title}
                Description: {finding.description}
                File: {finding.file}:{finding.lines}
                
                Code context:
                {context_code}
                
                Consider:
                1. Is the vulnerable pattern actually exploitable?
                2. Are there mitigating controls in place?
                3. Is user input properly validated?
                4. What is the actual risk level?
                
                Provide confidence score (0-100) and reasoning.
                """
                
                if self.agent_executor:
                    result = await self.agent_executor.ainvoke({
                        "context": validation_prompt
                    })
                    
                    # Parse confidence score from result
                    confidence = self._extract_confidence_score(result["output"])
                    
                    if confidence >= self.config.get('min_confidence', 70):
                        validated_findings.append(finding)
                    else:
                        logger.debug(f"Filtered out low-confidence finding: {finding.title}")
                else:
                    # If no agent executor, include finding with default confidence
                    validated_findings.append(finding)
                        
            except Exception as e:
                logger.error(f"Error validating finding {finding.title}: {e}")
                # Include finding if validation fails
                validated_findings.append(finding)
        
        logger.info(f"Validated {len(validated_findings)} findings")
        return validated_findings
    
    def _extract_line_number(self, lines: str) -> int:
        """Extract line number from lines field"""
        try:
            return int(lines.split('-')[0]) if lines else 1
        except (ValueError, AttributeError):
            return 1
    
    async def _perform_deep_analysis(self, code_context: Dict[str, Any], context: AnalysisContext) -> List[Finding]:
        """
        Perform deep AI-powered code analysis to find new vulnerabilities
        """
        logger.info("Performing deep security analysis")
        
        findings = []
        
        try:
            # Analyze each security pattern
            for pattern in self.security_patterns:
                pattern_findings = await self._analyze_security_pattern(pattern, code_context, context)
                findings.extend(pattern_findings)
            
            # Analyze business logic vulnerabilities
            logic_findings = await self._analyze_business_logic(code_context, context)
            findings.extend(logic_findings)
            
            # Analyze architecture-level security issues
            arch_findings = await self._analyze_architecture_security(code_context, context)
            findings.extend(arch_findings)
        
        except Exception as e:
            logger.error(f"Error in deep analysis: {e}")
        
        return findings
    
    async def _analyze_security_pattern(self, pattern: SecurityPattern, code_context: Dict[str, Any], context: AnalysisContext) -> List[Finding]:
        """
        Analyze code for specific security patterns
        """
        findings = []
        
        try:
            # Check if vector store is initialized
            if not hasattr(self.vector_store, 'vectorstore') or not self.vector_store.vectorstore:
                logger.debug("Vector store not initialized, skipping pattern search")
                return findings
            
            # Use similarity search for pattern indicators
            for indicator in pattern.patterns[:3]:  # Limit for performance
                matches = await self.vector_store.similarity_search(indicator, k=5)
                for match in matches:
                    result = await self._analyze_pattern_match(match, pattern, context)
                    if result:
                        findings.append(result)
        except Exception as e:
            logger.warning(f"Vector store search failed: {e}")
        
        return findings
    
    async def _analyze_pattern_match(self, match, pattern: SecurityPattern, context: AnalysisContext) -> Optional[Finding]:
        """Analyze a specific pattern match found by vector search"""
        try:
            analysis_prompt = f"""
            Analyze this code for {pattern.name} vulnerabilities:
            
            Pattern: {pattern.description}
            File: {match.get('file', 'unknown')}
            Code: {match.get('code', 'unknown')}
            
            Look for:
            - {', '.join(pattern.patterns)}
            
            If vulnerability found, provide:
            1. Exact location and vulnerable code
            2. Attack scenario and impact
            3. CVSS v4.0 scoring rationale
            4. Specific remediation steps
            """
            
            if self.agent_executor:
                result = await self.agent_executor.ainvoke({
                    "context": analysis_prompt
                })
                
                # Extract finding if vulnerability detected
                if "VULNERABILITY FOUND" in result["output"].upper():
                    finding = await self._parse_structured_ai_response(
                        result["output"], 
                        match.get('file', 'unknown'), 
                        1,
                        match.get('code', ''),
                        context
                    )
                    return finding
                        
        except Exception as e:
            logger.error(f"Error analyzing pattern {pattern.name}: {e}")
        
        return None
    
    async def _analyze_cross_file_vulnerabilities(self, code_context: Dict[str, Any], context: AnalysisContext) -> List[Finding]:
        """
        Analyze vulnerabilities that span multiple files
        """
        logger.info("Analyzing cross-file vulnerabilities")
        
        findings = []
        
        try:
            # Analyze data flow across files
            data_flows = code_context.get('data_flows', [])
            
            for flow in data_flows:
                if self._is_vulnerable_data_flow(flow):
                    # Create finding for cross-file vulnerability
                    cvss_score = CVSSv4(score=7.0, vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:L/VA:L/SC:N/SI:N/SA:N")
                    
                    finding = Finding(
                        file=flow.get('sink_file', 'unknown'),
                        title=f"Cross-file data flow vulnerability",
                        description=f"Untrusted data flows from {flow['source']} to {flow['sink']} without validation",
                        lines=str(flow.get('sink_line', 0)),
                        impact="Cross-file data flow security risk",
                        severity="High",
                        cvss_v4=cvss_score,
                        snippet=flow.get('code', ''),
                        recommendation="Implement proper data validation and sanitization",
                        sample_fix="Add input validation at data flow boundaries",
                        poc="# Test cross-file data flow",
                        owasp=[],
                        cwe=[],
                        references=[],
                        cross_file=[flow.get('source_file', '')],
                        tool_evidence=[self._create_tool_evidence("Cross-file Data Flow Analysis", f"Data flow from {flow['source']} to {flow['sink']}")]
                    )
                    findings.append(finding)
        
        except Exception as e:
            logger.error(f"Error in cross-file analysis: {e}")
        
        return findings
    
    # Tool functions for LangChain agent
    def _analyze_code_block(self, code: str, file_path: str, line_number: int) -> str:
        """Tool function: Analyze a specific code block"""
        return f"Analyzed code block in {file_path}:{line_number}"
    
    def _search_similar_vulnerabilities(self, vulnerability_type: str, context: str) -> str:
        """Tool function: Search for similar vulnerabilities"""
        return f"Found similar vulnerabilities of type: {vulnerability_type}"
    
    def _assess_vulnerability_impact(self, vulnerability: str, context: str) -> str:
        """Tool function: Assess vulnerability impact"""
        return f"Impact assessment for: {vulnerability}"
    
    def _generate_remediation_advice(self, vulnerability: str, code_context: str) -> str:
        """Tool function: Generate remediation advice"""
        return f"Remediation advice for: {vulnerability}"
    
    # Helper methods
    async def _identify_entry_points(self, context: AnalysisContext) -> List[str]:
        """Identify application entry points"""
        entry_points = []
        try:
            for file_path in context.target_files:
                if os.path.exists(file_path):
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                        # Look for common entry point patterns
                        if any(pattern in content for pattern in ['def main(', 'if __name__', 'app.run(', 'fastapi']):
                            entry_points.append(file_path)
        except Exception as e:
            logger.error(f"Error identifying entry points: {e}")
        return entry_points
    
    async def _analyze_data_flows(self, context: AnalysisContext) -> List[Dict[str, Any]]:
        """Analyze data flows in the application"""
        data_flows = []
        try:
            # Basic data flow analysis implementation
            for file_path in context.target_files:
                if os.path.exists(file_path):
                    flows = await self._extract_file_data_flows(file_path)
                    data_flows.extend(flows)
        except Exception as e:
            logger.error(f"Error analyzing data flows: {e}")
        return data_flows
    
    async def _extract_file_data_flows(self, file_path: str) -> List[Dict[str, Any]]:
        """Extract data flows from a single file"""
        flows = []
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                
            for line_num, line in enumerate(lines, 1):
                # Look for data flow patterns
                if 'request' in line.lower() and ('get' in line or 'post' in line):
                    flows.append({
                        'source': 'user_input',
                        'sink': 'request_handler',
                        'source_file': file_path,
                        'sink_file': file_path,
                        'source_line': line_num,
                        'sink_line': line_num,
                        'code': line.strip()
                    })
        except Exception as e:
            logger.error(f"Error extracting flows from {file_path}: {e}")
        return flows
    
    async def _identify_security_boundaries(self, context: AnalysisContext) -> List[str]:
        """Identify security boundaries in the application"""
        boundaries = []
        try:
            for file_path in context.target_files:
                if any(keyword in file_path.lower() for keyword in ['auth', 'security', 'login', 'middleware']):
                    boundaries.append(file_path)
        except Exception as e:
            logger.error(f"Error identifying security boundaries: {e}")
        return boundaries
    
    async def _get_code_context(self, file_path: str, line_number: int, context_lines: int = 5) -> str:
        """Get code context around a specific line"""
        try:
            if not os.path.exists(file_path):
                return "File not found"
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            start = max(0, line_number - context_lines - 1)
            end = min(len(lines), line_number + context_lines)
            
            context = []
            for i in range(start, end):
                context.append(f"{i+1:3d}: {lines[i].rstrip()}")
            
            return '\n'.join(context)
        except Exception as e:
            logger.error(f"Error getting code context: {e}")
            return "Error reading file"
    
    def _extract_confidence_score(self, text: str) -> int:
        """Extract confidence score from LLM output"""
        try:
            match = re.search(r'confidence[:\s]+(\d+)', text.lower())
            if match:
                return int(match.group(1))
        except Exception:
            pass
        return 75  # Default confidence
    
    def _severity_to_cvss_score(self, severity: str) -> float:
        """Convert severity string to CVSS score"""
        severity_map = {
            'CRITICAL': 9.0,
            'HIGH': 7.5,
            'MEDIUM': 5.0,
            'LOW': 2.5,
            'INFO': 0.0
        }
        return severity_map.get(severity.upper(), 5.0)
    
    def _is_vulnerable_data_flow(self, flow: Dict[str, Any]) -> bool:
        """Check if a data flow represents a vulnerability"""
        try:
            # Check if data flows from untrusted source to sensitive sink
            untrusted_sources = ['user_input', 'request', 'form_data', 'url_param']
            sensitive_sinks = ['database', 'file_system', 'command_execution', 'eval']
            
            source = flow.get('source', '').lower()
            sink = flow.get('sink', '').lower()
            
            return any(us in source for us in untrusted_sources) and any(ss in sink for ss in sensitive_sinks)
        except Exception:
            return False
    
    def _deduplicate_and_rank(self, findings: List[Finding]) -> List[Finding]:
        """Remove duplicates and rank findings by severity"""
        try:
            seen = set()
            unique_findings = []
            
            # Sort by severity first
            severity_order = {'Critical': 4, 'High': 3, 'Medium': 2, 'Low': 1}
            sorted_findings = sorted(findings, 
                                   key=lambda x: severity_order.get(x.severity, 0), 
                                   reverse=True)
            
            for finding in sorted_findings:
                key = (finding.title, finding.file, finding.lines)
                if key not in seen:
                    seen.add(key)
                    unique_findings.append(finding)
            
            return unique_findings
        except Exception as e:
            logger.error(f"Error deduplicating findings: {e}")
            return findings
    
    async def perform_line_by_line_analysis(self, files: List[str], context: AnalysisContext) -> List[Finding]:
        """
        Perform line-by-line security analysis of source files
        """
        all_findings = []
        
        for file_path in files:
            if not os.path.exists(file_path):
                logger.warning(f"File not found: {file_path}")
                continue
                
            try:
                file_findings = await self._analyze_file_line_by_line(file_path, context)
                all_findings.extend(file_findings)
                logger.info(f"Analyzed {file_path}: {len(file_findings)} findings")
            except Exception as e:
                logger.error(f"Error analyzing {file_path}: {e}")
        
        return self._deduplicate_and_rank(all_findings)
    
    async def _analyze_file_line_by_line(self, file_path: str, context: AnalysisContext) -> List[Finding]:
        """Analyze a single file line by line for security issues"""
        findings = []
        
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            for line_num, line_content in enumerate(lines, 1):
                line_content = line_content.strip()
                
                # Skip empty lines and comments
                if not line_content or line_content.startswith('#'):
                    continue
                
                # Check if line contains potential security patterns
                if await self._line_contains_security_pattern(line_content, line_num, file_path):
                    line_findings = await self._ai_analyze_line(
                        line_content, line_num, file_path, lines, context
                    )
                    findings.extend(line_findings)
            
            # Multi-line pattern analysis
            multi_line_findings = await self._analyze_multi_line_patterns(file_path, lines, context)
            findings.extend(multi_line_findings)
            
        except Exception as e:
            logger.error(f"Error reading file {file_path}: {e}")
        
        return findings
    
    async def _line_contains_security_pattern(self, line: str, line_num: int, file_path: str) -> bool:
        """Quick check if a line might contain security-relevant patterns"""
        security_keywords = [
            'exec', 'eval', 'compile', 'subprocess', 'os.system', 'shell=True',
            'open(', 'pickle.load', 'yaml.load', 'input(', 'SELECT', 'INSERT', 
            'UPDATE', 'DELETE', 'password', 'secret', 'key', 'token', 'md5', 
            'sha1', '../', 'innerHTML', 'eval(', 'document.write'
        ]
        
        line_lower = line.lower()
        return any(keyword.lower() in line_lower for keyword in security_keywords)
    
    async def _ai_analyze_line(self, line: str, line_num: int, file_path: str, 
                              all_lines: List[str], context: AnalysisContext) -> List[Finding]:
        """Use AI to analyze a specific line for security vulnerabilities with full context awareness"""
        
        try:
            # Get comprehensive context for intelligent analysis
            start_idx = max(0, line_num - 10)  # Increased context window
            end_idx = min(len(all_lines), line_num + 10)
            context_lines = all_lines[start_idx:end_idx]
            context_code = ''.join(f"{start_idx + i + 1:3d}: {line}" for i, line in enumerate(context_lines))
            
            # Extract full function/class/method context
            function_context = self._get_comprehensive_function_context(all_lines, line_num)
            
            # Analyze how this line is used across the file
            usage_context = self._analyze_line_usage_in_file(line, all_lines, file_path)
            
            # Get imports and dependencies to understand available security controls
            imports_context = self._extract_imports_and_dependencies(all_lines)
            
            # Check configuration for LLM provider using base agent properties
            llm_provider = self.llm_provider.lower()
            local_model_enabled = self.local_model_config.get('enabled', False)
            
            if llm_provider == 'local' or local_model_enabled:
                return await self._local_llm_analyze_line(line, line_num, file_path, context_code, function_context, context)
            else:
                return await self._openai_analyze_line(line, line_num, file_path, context_code, function_context, context)
        
        except Exception as e:
            logger.error(f"Error in AI analysis for line {line_num}: {e}")
            return []
    
    async def _local_llm_analyze_line(self, line: str, line_num: int, file_path: str, 
                                     context_code: str, function_context: str, context: AnalysisContext,
                                     usage_context: str = "", imports_context: str = "") -> List[Finding]:
        """Enhanced line analysis using local LLM with comprehensive context awareness"""
        
        analysis_prompt = f"""You are a senior security engineer performing a comprehensive code security audit.

FILE: {file_path}
TARGET LINE {line_num}: {line.strip()}

FUNCTION/CLASS CONTEXT:
{function_context}

CODE CONTEXT (with line numbers):
{context_code}

USAGE ANALYSIS:
{usage_context}

IMPORTS & DEPENDENCIES:
{imports_context}

PROJECT TECHNOLOGIES: {', '.join(context.technologies.get('languages', []))}

COMPREHENSIVE SECURITY ANALYSIS INSTRUCTIONS:
1. Understand the PURPOSE of this line within its function/class context
2. Analyze HOW this line interacts with the rest of the application
3. Consider data flow: Where does the data come from? Where does it go?
4. Evaluate security controls: Input validation, output encoding, authentication, authorization
5. Assess exploitability in the REAL WORLD context of this application
6. Consider false positive likelihood based on mitigating controls

VULNERABILITY CATEGORIES TO CHECK:
- Injection flaws (SQL, Command, Code, XSS, Path Traversal)
- Authentication/Authorization bypasses
- Cryptographic weaknesses
- Insecure deserialization
- Business logic vulnerabilities
- API security issues
- Race conditions and TOCTOU
- Resource exhaustion

RESPONSE FORMAT (ONLY if real vulnerability found):
VULNERABILITY: [Specific vulnerability name]
SEVERITY: [Critical/High/Medium/Low]
CONFIDENCE: [0-100 - how certain are you this is exploitable?]
DESCRIPTION: [Explain the vulnerability in context of the function and application]
ATTACK_SCENARIO: [How would an attacker exploit this in THIS specific context?]
IMPACT: [Real-world security impact considering the function's purpose]
ROOT_CAUSE: [Why is this vulnerable? What security principle is violated?]
FIX: [Specific code fix that addresses the root cause]
CWE: [CWE number if applicable]

If NO EXPLOITABLE vulnerability (or false positive), respond: "SAFE"

Analyze now:"""

        try:
            local_llm = self.create_llm()
            if local_llm:
                response = await local_llm.ainvoke(analysis_prompt)
                
                if hasattr(response, 'content'):
                    ai_response = response.content
                else:
                    ai_response = str(response)
                
                # Only create finding if vulnerability is real and exploitable
                if "SAFE" not in ai_response.upper() and "VULNERABILITY:" in ai_response:
                    finding = self._parse_comprehensive_llm_response(
                        ai_response, file_path, line_num, line, context, 
                        function_context, usage_context
                    )
                    if finding:
                        return [finding]
            
        except Exception as e:
            if "model requires more system memory" in str(e) or "Local model not available" in str(e):
                logger.debug(f"Local model not available for line {line_num}: {e}")
            else:
                logger.error(f"Error in local LLM analysis for line {line_num}: {e}")
        
        return []
    
    async def _openai_analyze_line(self, line: str, line_num: int, file_path: str, 
                                  context_code: str, function_context: str, context: AnalysisContext,
                                  usage_context: str = "", imports_context: str = "") -> List[Finding]:
        """OpenAI-based line analysis with comprehensive context awareness"""
        
        # Analyze cross-file connections
        cross_file_connections = await self._analyze_line_cross_file_connections(line, file_path, context)
        
        analysis_prompt = f"""You are a senior application security engineer performing a comprehensive code security audit.

CONTEXT INFORMATION:
File: {file_path}
Target Line {line_num}: {line.strip()}
Technologies: {', '.join(context.technologies.get('languages', []))}

FUNCTION/CLASS CONTEXT (Understanding purpose and scope):
{function_context}

CODE CONTEXT (Lines with numbers):
{context_code}

USAGE ANALYSIS (How this code is used in the application):
{usage_context}

IMPORTS & SECURITY CONTROLS:
{imports_context}

CROSS-FILE CONNECTIONS:
{cross_file_connections}

COMPREHENSIVE SECURITY ANALYSIS REQUIREMENTS:
Perform a thorough analysis considering:

1. CONTEXTUAL UNDERSTANDING:
   - What is the PURPOSE of this line within its function/class?
   - How does this fit into the overall application logic?
   - Is this an entry point, data processor, or output handler?

2. DATA FLOW ANALYSIS:
   - Where does the data originate? (User input, database, external API, trusted source)
   - What transformations occur?
   - Where does the data go? (Database, external system, user output)
   - Are there validation/sanitization controls in the data flow?

3. SECURITY CONTROLS ASSESSMENT:
   - Input validation present?
   - Output encoding applied?
   - Authentication/authorization checks?
   - Security libraries being used?

4. EXPLOITABILITY:
   - Can an attacker realistically exploit this?
   - What would the attack vector look like IN THIS SPECIFIC CONTEXT?
   - Are there mitigating controls that prevent exploitation?
   - What is the confidence level (0-100) this is truly exploitable?

5. FALSE POSITIVE ASSESSMENT:
   - Could this be a false positive due to context not visible in this snippet?
   - Are there framework-level protections?

VULNERABILITY CATEGORIES TO CHECK:
- Injection flaws (SQL, NoSQL, Command, LDAP, XPath, Code)
- Cross-Site Scripting (XSS) - Stored, Reflected, DOM-based
- Authentication & Session Management flaws
- Authorization bypasses (IDOR, privilege escalation)
- Security misconfiguration
- Cryptographic failures
- Insecure deserialization
- Path traversal & file inclusion
- Business logic vulnerabilities
- API security issues
- Race conditions

RESPONSE FORMAT (ONLY if genuine, exploitable vulnerability found with confidence >= 70%):

ISSUE_NAME: [Specific vulnerability name]
SEVERITY: [Critical/High/Medium/Low with justification based on exploitability and impact]
CONFIDENCE: [70-100: How certain are you this is exploitable in THIS context?]
DESCRIPTION: [Comprehensive explanation considering function context and application flow]
ATTACK_SCENARIO: [Detailed, realistic attack scenario specific to THIS application context]
AFFECTED_CODE: Line {line_num}: {line.strip()}
IMPACT: [Real-world impact considering the function's role in the application]
ROOT_CAUSE: [Fundamental security principle violated]
TAILORED_RECOMMENDATION: [Specific fix for THIS context, not generic advice]
SECURE_CODE_EXAMPLE: [Show the exact secure implementation]
CWE: [CWE number if applicable]
REFERENCES: [Relevant OWASP, security standards]

If NO genuine exploitable vulnerability OR confidence < 70% OR mitigating controls present, respond: "NO_VULNERABILITY_FOUND"

Analyze now with thorough contextual understanding:"""
        
        try:
            llm = self.create_llm()
            if llm:
                response = await llm.ainvoke(analysis_prompt)
                
                if hasattr(response, 'content'):
                    ai_response = response.content
                elif hasattr(response, 'text'):
                    ai_response = response.text
                else:
                    ai_response = str(response)
                
                # Only create finding if confidence is high enough
                if "NO_VULNERABILITY_FOUND" not in ai_response and "ISSUE_NAME:" in ai_response:
                    # Check confidence level
                    confidence_match = re.search(r'CONFIDENCE:\s*(\d+)', ai_response)
                    if confidence_match and int(confidence_match.group(1)) >= 70:
                        finding = await self._parse_comprehensive_ai_response(
                            ai_response, file_path, line_num, line, context,
                            function_context, usage_context
                        )
                        if finding:
                            return [finding]
            
        except Exception as e:
            if "No API keys available" in str(e) and self.llm_provider == "local":
                logger.debug(f"API not available in local mode for line {line_num}: {e}")
            else:
                logger.error(f"Error in OpenAI analysis for line {line_num}: {e}")
        
        return []
    
    async def _parse_comprehensive_ai_response(self, ai_response: str, file_path: str, line_num: int, 
                                              line: str, context: AnalysisContext,
                                              function_context: str, usage_context: str) -> Optional[Finding]:
        """Parse comprehensive AI response into Finding object"""
        try:
            issue_name = self._extract_ai_field(ai_response, "ISSUE_NAME")
            description = self._deduplicate_paragraphs(self._extract_ai_field(ai_response, "DESCRIPTION") or "")
            impact = self._deduplicate_paragraphs(self._extract_ai_field(ai_response, "IMPACT") or "")
            severity = self._extract_ai_field(ai_response, "SEVERITY")
            confidence_raw = self._extract_ai_field(ai_response, "CONFIDENCE") or "75"
            attack_scenario = self._deduplicate_paragraphs(self._extract_ai_field(ai_response, "ATTACK_SCENARIO") or "")
            root_cause = self._deduplicate_paragraphs(self._extract_ai_field(ai_response, "ROOT_CAUSE") or "")
            recommendation = self._deduplicate_paragraphs(self._extract_ai_field(ai_response, "TAILORED_RECOMMENDATION") or "")
            secure_example = self._deduplicate_paragraphs(self._extract_ai_field(ai_response, "SECURE_CODE_EXAMPLE") or "")
            cwe_raw = self._extract_ai_field(ai_response, "CWE") or ""
            references = self._extract_ai_field(ai_response, "REFERENCES") or ""
            affected_code = self._deduplicate_paragraphs(self._extract_ai_field(ai_response, "AFFECTED_CODE") or "")
            
            # Skip if missing critical fields or empty description
            if not issue_name or not description or len(description.strip()) < 10:
                return None
            
            # Extract CWE number
            cwe_match = re.search(r'CWE-(\d+)', cwe_raw)
            cwe = f"CWE-{cwe_match.group(1)}" if cwe_match else ""
            
            # Extract numeric confidence value
            confidence_match = re.search(r'(\d+)', confidence_raw)
            confidence = int(confidence_match.group(1)) if confidence_match else 75
            
            # Skip low confidence findings
            if confidence < 70:
                return None
            
            # Extract severity level
            severity_match = re.search(r'(Critical|High|Medium|Low)', severity, re.IGNORECASE)
            severity_level = severity_match.group(1) if severity_match else "Medium"
            
            cvss_score = CVSSv4(
                score=self._severity_to_cvss_score(severity_level),
                vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
            )
            
            # Clean function context
            clean_function_context = self._clean_context_text(
                function_context,
                fallback=f"Line {line_num}: `{line.strip()}`",
                line=line,
                line_num=line_num,
                file_path=file_path,
                mode="function"
            )
            
            # Only show data flow if meaningful
            data_flow_info = ""
            if usage_context:
                clean_usage = self._clean_context_text(usage_context, mode="usage")
                if clean_usage:
                    data_flow_info = f"\n\n**Data Flow:**\n{clean_usage}"
            
            # If no meaningful context, just show affected line
            if not clean_function_context or len(clean_function_context.strip()) < 10:
                clean_function_context = affected_code or f"Line {line_num}: `{line.strip()}`"
            
            # Build professional, clean description
            full_description = f"""{description}

**Affected Code:**
{clean_function_context}{data_flow_info}"""
            
            if attack_scenario:
                full_description += f"\n\n**Attack Scenario:**\n{attack_scenario}"
            
            if root_cause:
                full_description += f"\n\n**Root Cause:**\n{root_cause}"
            
            # Build clean remediation section
            recommendation_parts = []
            
            if recommendation:
                recommendation_parts.append(f"**Remediation:**\n{recommendation}")
            
            if secure_example and secure_example.strip() and secure_example.strip() != recommendation.strip():
                recommendation_parts.append(f"**Secure Code Example:**\n```\n{secure_example}\n```")
            
            # Location
            recommendation_parts.append(f"**Location:**\nFile: `{file_path}`, Line: {line_num}")
            
            # Impact
            if impact:
                recommendation_parts.append(f"**Impact:**\n{impact}")
            
            # References
            if cwe:
                reference_text = cwe
                if cwe_raw and len(cwe_raw) > len(cwe):
                    # Include CWE description
                    reference_text = cwe_raw
                recommendation_parts.append(f"**Reference:**\n{reference_text}")
            
            if references:
                recommendation_parts.append(f"**Additional References:**\n{references}")
            
            full_recommendation = "\n\n".join(self._deduplicate_list(recommendation_parts))
            
            finding = Finding(
                file=file_path,
                title=issue_name,
                description=full_description,
                lines=str(line_num),
                impact=impact or "Security vulnerability detected",
                severity=self._normalize_severity(severity_level),
                confidence_score=confidence,
                cvss_v4=cvss_score,
                snippet=line.strip(),
                recommendation=full_recommendation,
                sample_fix=secure_example or recommendation,
                poc=f"# Security test for line {line_num}",
                owasp=[],
                cwe=[cwe] if cwe else [],
                references=references.split(',') if references else [],
                cross_file=[],
                tool_evidence=[self._create_tool_evidence("AI Comprehensive Analysis", f"Context-aware analysis")]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error parsing comprehensive AI response: {e}")
            return None
    
    def _parse_local_llm_response(self, response: str, file_path: str, line_num: int, 
                                 line: str, context: AnalysisContext) -> Optional[Finding]:
        """Parse local LLM response into Finding object"""
        try:
            vulnerability_name = self._extract_field(response, "VULNERABILITY")
            severity = self._extract_field(response, "SEVERITY") or "Medium"
            description = self._extract_field(response, "DESCRIPTION") or "Security vulnerability detected"
            impact = self._extract_field(response, "IMPACT") or "Potential security risk"
            fix = self._extract_field(response, "FIX") or "Review and fix this code"
            cwe = self._extract_field(response, "CWE")
            
            if not vulnerability_name:
                return None
            
            cvss_score = CVSSv4(
                score=self._severity_to_cvss_score(severity),
                vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
            )
            
            recommendation = f"""SECURITY ISSUE DETECTED:

VULNERABILITY: {vulnerability_name}
SEVERITY: {severity}

ANALYSIS:
{description}

SECURITY IMPACT:
{impact}

RECOMMENDED FIX:
{fix}

LOCATION:
File: {file_path}
Line {line_num}: {line.strip()}
"""

            if cwe:
                recommendation += f"\nCWE REFERENCE: {cwe}"
            
            finding = Finding(
                file=file_path,
                title=f"{vulnerability_name} (Line {line_num})",
                description=description,
                lines=str(line_num),
                impact=impact,
                severity=self._normalize_severity(severity),
                cvss_v4=cvss_score,
                snippet=line.strip(),
                recommendation=recommendation,
                sample_fix=fix,
                poc=f"# Test case for {vulnerability_name}\n# Review line {line_num} in {file_path}",
                owasp=[],
                cwe=[cwe] if cwe else [],
                references=[],
                cross_file=[],
                tool_evidence=[self._create_tool_evidence("Local LLM Analysis", f"Line {line_num} security analysis")]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error parsing local LLM response: {e}")
            return None
    
    async def _parse_ai_response(self, ai_response: str, file_path: str, line_num: int, 
                                line: str, context: AnalysisContext) -> Optional[Finding]:
        """Parse AI response into Finding object"""
        try:
            issue_name = self._extract_ai_field(ai_response, "ISSUE_NAME")
            description = self._extract_ai_field(ai_response, "DESCRIPTION")
            impact = self._extract_ai_field(ai_response, "IMPACT")
            severity = self._extract_ai_field(ai_response, "SEVERITY")
            recommendation = self._extract_ai_field(ai_response, "TAILORED_RECOMMENDATION")
            secure_example = self._extract_ai_field(ai_response, "SECURE_CODE_EXAMPLE")
            references = self._extract_ai_field(ai_response, "REFERENCES")
            
            if not issue_name or not description:
                return None
            
            severity_level = self._normalize_severity(severity.split()[0] if severity else "Medium")
            cvss_score = CVSSv4(
                score=self._severity_to_cvss_score(severity_level),
                vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:N/VI:N/VA:N/SC:N/SI:N/SA:N"
            )
            
            full_recommendation = f"""SECURITY VULNERABILITY ANALYSIS:

ISSUE: {issue_name}
SEVERITY: {severity or severity_level}

DESCRIPTION:
{description}

SECURITY IMPACT:
{impact or 'Security risk identified'}

LOCATION:
File: {file_path}
Line {line_num}: {line.strip()}

RECOMMENDED FIX:
{recommendation or 'Review and secure this code'}

SECURE CODE EXAMPLE:
{secure_example or 'Apply security best practices'}

SECURITY REFERENCES:
{references or 'Review OWASP and security guidelines'}
"""
            
            finding = Finding(
                file=file_path,
                title=f"{issue_name} (Line {line_num})",
                description=description,
                lines=str(line_num),
                impact=impact or "Security vulnerability detected",
                severity=severity_level,
                cvss_v4=cvss_score,
                snippet=line.strip(),
                recommendation=full_recommendation,
                sample_fix=secure_example or recommendation,
                poc=f"# Security test for {issue_name}\n# Verify line {line_num} in {file_path}",
                owasp=[],
                cwe=[],
                references=[references] if references else [],
                cross_file=[],
                tool_evidence=[self._create_tool_evidence("AI Security Analysis", f"Line {line_num} vulnerability detection")]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error parsing AI response: {e}")
            return None
    
    def _extract_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract field value from structured response - handles ** markers"""
        # Remove ** markers that AI might add
        text = re.sub(r'\*\*\s*', '', text)
        
        # Extract content between field name and next field or end
        pattern = rf"{field_name}:\s*(.+?)(?=\n(?:[A-Z_]+:|$))"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Stop at the first occurrence of another field name in CAPS
            content = re.split(r'\n[A-Z_]+:', content)[0].strip()
            return content
        return None
    
    def _extract_ai_field(self, text: str, field_name: str) -> Optional[str]:
        """Extract field value from AI response - handles ** markers"""
        # Remove ** markers that AI might add
        text = re.sub(r'\*\*\s*', '', text)
        
        # Extract content between field name and next field or end
        pattern = rf"{field_name}:\s*(.+?)(?=\n(?:[A-Z_]+:|$))"
        match = re.search(pattern, text, re.IGNORECASE | re.DOTALL)
        if match:
            content = match.group(1).strip()
            # Stop at the first occurrence of another field name in CAPS
            content = re.split(r'\n[A-Z_]+:', content)[0].strip()
            return content
        return None
    
    def _get_function_context(self, all_lines: List[str], line_num: int) -> str:
        """Find which function/class the current line belongs to"""
        function_context = "Global scope"
        
        try:
            for i in range(line_num - 1, max(0, line_num - 50), -1):
                line = all_lines[i].strip()
                
                if line.startswith('def '):
                    function_match = re.match(r'def\s+(\w+)\s*\((.*?)\)', line)
                    if function_match:
                        function_name = function_match.group(1)
                        params = function_match.group(2)
                        function_context = f"Function: {function_name}({params}) [Line {i+1}]"
                        break
                
                elif line.startswith('class '):
                    class_match = re.match(r'class\s+(\w+)', line)
                    if class_match:
                        class_name = class_match.group(1)
                        function_context = f"Class: {class_name} [Line {i+1}]"
                        break
            
            # Add variable analysis
            current_line = all_lines[line_num - 1] if line_num > 0 else ""
            variables_in_line = re.findall(r'\b([a-zA-Z_]\w*)\b', current_line)
            variables_info = f"Variables: {', '.join(set(variables_in_line[:5]))}" if variables_in_line else "No variables"
            
            return f"{function_context}\n{variables_info}"
        
        except Exception as e:
            logger.error(f"Error getting function context: {e}")
            return "Function context unavailable"
    
    def _get_comprehensive_function_context(self, all_lines: List[str], line_num: int) -> str:
        """Extract complete function/class context including purpose and data flow"""
        try:
            context_parts = []
            
            # Find enclosing function/class with full signature
            for i in range(line_num - 1, max(0, line_num - 100), -1):
                line = all_lines[i].strip()
                
                # Check for function definition
                if line.startswith('def '):
                    func_match = re.match(r'def\s+(\w+)\s*\((.*?)\)', line)
                    if func_match:
                        func_name = func_match.group(1)
                        params = func_match.group(2)
                        context_parts.append(f"FUNCTION: {func_name}({params})")
                        
                        # Extract docstring if available
                        docstring = self._extract_docstring(all_lines, i + 1)
                        if docstring:
                            context_parts.append(f"PURPOSE: {docstring}")
                        
                        # Extract function body context
                        func_body = self._extract_function_body(all_lines, i)
                        context_parts.append(f"FUNCTION_BODY_PREVIEW:\n{func_body}")
                        break
                
                # Check for class definition
                elif line.startswith('class '):
                    class_match = re.match(r'class\s+(\w+)', line)
                    if class_match:
                        class_name = class_match.group(1)
                        context_parts.append(f"CLASS: {class_name}")
                        
                        # Extract class docstring
                        docstring = self._extract_docstring(all_lines, i + 1)
                        if docstring:
                            context_parts.append(f"CLASS_PURPOSE: {docstring}")
                        break
            
            # Analyze variable assignments and data flow in current scope
            data_flow = self._analyze_local_data_flow(all_lines, line_num)
            if data_flow:
                context_parts.append(f"DATA_FLOW:\n{data_flow}")
            
            return '\n\n'.join(context_parts) if context_parts else "Global scope - no enclosing function/class"
        
        except Exception as e:
            logger.error(f"Error getting comprehensive function context: {e}")
            return "Context unavailable"
    
    def _extract_docstring(self, lines: List[str], start_line: int) -> str:
        """Extract docstring from function/class"""
        try:
            if start_line >= len(lines):
                return ""
            
            line = lines[start_line].strip()
            if line.startswith('"""') or line.startswith("'''"):
                delimiter = '"""' if '"""' in line else "'''"
                docstring_lines = [line.replace(delimiter, '')]
                
                # Multi-line docstring
                if line.count(delimiter) < 2:
                    for i in range(start_line + 1, min(start_line + 20, len(lines))):
                        docstring_lines.append(lines[i].strip())
                        if delimiter in lines[i]:
                            break
                
                return ' '.join(docstring_lines).replace(delimiter, '').strip()[:200]
        except Exception:
            pass
        return ""
    
    def _extract_function_body(self, lines: List[str], func_start: int, max_lines: int = 15) -> str:
        """Extract preview of function body"""
        try:
            body_lines = []
            base_indent = len(lines[func_start]) - len(lines[func_start].lstrip())
            
            for i in range(func_start + 1, min(func_start + max_lines, len(lines))):
                line = lines[i]
                current_indent = len(line) - len(line.lstrip())
                
                # Stop at next function/class at same level
                if current_indent <= base_indent and line.strip() and not line.strip().startswith(('#', '"', "'")):
                    break
                
                if line.strip():
                    body_lines.append(f"  {line.rstrip()}")
            
            return '\n'.join(body_lines[:10])  # Limit to first 10 lines
        except Exception:
            return "Body unavailable"
    
    def _analyze_local_data_flow(self, lines: List[str], target_line: int) -> str:
        """Analyze how data flows to the target line"""
        try:
            flow_info = []
            target_vars = re.findall(r'\b([a-zA-Z_]\w*)\b', lines[target_line - 1])
            
            # Look backwards to find where variables are defined
            for var in set(target_vars[:5]):  # Limit to 5 most important variables
                for i in range(target_line - 1, max(0, target_line - 30), -1):
                    line = lines[i]
                    # Check if variable is assigned
                    if re.search(rf'\b{var}\b\s*=', line):
                        flow_info.append(f"Line {i+1}: {var} = {line.strip()[:80]}")
                        break
                    # Check if variable comes from function parameter
                    if f"def " in line and var in line:
                        flow_info.append(f"Line {i+1}: {var} is function parameter")
                        break
            
            return '\n'.join(flow_info) if flow_info else "No clear data flow traced"
        except Exception:
            return "Data flow analysis unavailable"
    
    def _analyze_line_usage_in_file(self, line: str, all_lines: List[str], file_path: str) -> str:
        """Analyze how the current line's variables/functions are used elsewhere"""
        try:
            usage_info = []
            
            # Extract function calls or variable assignments from current line
            assignments = re.findall(r'(\w+)\s*=', line)
            function_defs = re.findall(r'def\s+(\w+)', line)
            
            entities_to_track = assignments + function_defs
            
            for entity in entities_to_track[:3]:  # Limit to 3 entities
                usage_count = sum(1 for l in all_lines if entity in l)
                if usage_count > 1:  # Used more than just at definition
                    usage_info.append(f"{entity}: used {usage_count} times in this file")
                    
                    # Find first few usages
                    for idx, l in enumerate(all_lines[:200]):  # Limit search
                        if entity in l and idx != (all_lines.index(line) if line in all_lines else -1):
                            usage_info.append(f"  Line {idx+1}: {l.strip()[:60]}")
                            if len(usage_info) > 5:
                                break
            
            return '\n'.join(usage_info) if usage_info else "No significant usage tracked"
        except Exception:
            return "Usage analysis unavailable"
    
    def _extract_imports_and_dependencies(self, lines: List[str]) -> str:
        """Extract imports to understand available security libraries"""
        try:
            imports = []
            security_libs = []
            
            for line in lines[:100]:  # Check first 100 lines for imports
                line = line.strip()
                if line.startswith('import ') or line.startswith('from '):
                    imports.append(line)
                    
                    # Check for security-related libraries
                    if any(lib in line.lower() for lib in ['bcrypt', 'hashlib', 'hmac', 'secrets', 'ssl', 'cryptography']):
                        security_libs.append(line)
            
            result = []
            if security_libs:
                result.append(f"SECURITY LIBRARIES: {', '.join(security_libs)}")
            if imports:
                result.append(f"TOTAL IMPORTS: {len(imports)}")
                result.append(f"KEY IMPORTS: {'; '.join(imports[:5])}")
            
            return '\n'.join(result) if result else "No imports detected"
        except Exception:
            return "Import analysis unavailable"
    
    def _parse_comprehensive_llm_response(self, response: str, file_path: str, line_num: int, 
                                         line: str, context: AnalysisContext, 
                                         function_context: str, usage_context: str) -> Optional[Finding]:
        """Parse comprehensive LLM response with enhanced context into Finding object"""
        try:
            vulnerability_name = self._strip_inline_ai_labels(self._extract_field(response, "VULNERABILITY"))
            severity = self._extract_field(response, "SEVERITY") or "Medium"
            confidence_raw = self._extract_field(response, "CONFIDENCE") or "85"
            description = self._strip_inline_ai_labels(
                self._deduplicate_paragraphs(self._extract_field(response, "DESCRIPTION") or "")
            )
            attack_scenario = self._strip_inline_ai_labels(
                self._deduplicate_paragraphs(self._extract_field(response, "ATTACK_SCENARIO") or "")
            )
            impact = self._strip_inline_ai_labels(
                self._deduplicate_paragraphs(self._extract_field(response, "IMPACT") or "")
            )
            root_cause = self._strip_inline_ai_labels(
                self._deduplicate_paragraphs(self._extract_field(response, "ROOT_CAUSE") or "")
            )
            fix = self._strip_inline_ai_labels(
                self._deduplicate_paragraphs(self._extract_field(response, "FIX") or "")
            )
            cwe_raw = self._extract_field(response, "CWE") or ""
            code_fix = self._strip_inline_ai_labels(
                self._deduplicate_paragraphs(self._extract_field(response, "CODE_FIX") or fix)
            )
            
            # Extract CWE number
            cwe_match = re.search(r'CWE-(\d+)', cwe_raw)
            cwe = f"CWE-{cwe_match.group(1)}" if cwe_match else ""
            
            # Extract numeric confidence value
            confidence_match = re.search(r'(\d+)', confidence_raw)
            confidence = int(confidence_match.group(1)) if confidence_match else 85
            
            # Skip if no vulnerability name, empty description, or low confidence
            if not vulnerability_name or not description or confidence < 60:
                return None
            
            # Clean function context with professional formatting
            clean_function_context = self._clean_context_text(
                function_context,
                fallback=f"Line {line_num}: `{line.strip()}`",
                line=line,
                line_num=line_num,
                file_path=file_path,
                mode="function"
            )
            
            # Only show data flow if meaningful
            data_flow_info = ""
            if usage_context:
                clean_usage = self._clean_context_text(usage_context, mode="usage")
                if clean_usage:
                    data_flow_info = f"\n\n**Data Flow:**\n{clean_usage}"
            
            cvss_score = CVSSv4(
                score=self._severity_to_cvss_score(severity),
                vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:H/VI:H/VA:H/SC:N/SI:N/SA:N"
            )
            
            # Build professional, clean description
            full_description = f"""{description}

**Affected Code:**
{clean_function_context}{data_flow_info}"""
            
            if attack_scenario:
                full_description += f"\n\n**Attack Scenario:**\n{attack_scenario}"
            
            if root_cause:
                full_description += f"\n\n**Root Cause:**\n{root_cause}"
            
            # Build clean remediation section
            recommendation_sections: List[str] = []
            guidance_lines: List[str] = []

            if fix:
                for raw_line in fix.splitlines():
                    normalized = raw_line.strip()
                    if not normalized:
                        continue
                    normalized = normalized.strip("•-* \t")
                    if not normalized or self._looks_like_code_line(normalized):
                        continue
                    guidance_lines.append(normalized)

                if guidance_lines:
                    if len(guidance_lines) == 1:
                        recommendation_sections.append(guidance_lines[0])
                    else:
                        bullets = [f"- {line}" for line in guidance_lines]
                        recommendation_sections.append("\n".join(bullets))

            # References
            if cwe:
                reference_text = cwe
                if cwe_raw and len(cwe_raw) > len(cwe):
                    # Include CWE description
                    reference_text = cwe_raw
                recommendation_sections.append(f"**Reference:**\n{reference_text}")

            recommendation = "\n\n".join(self._deduplicate_list(recommendation_sections))
            if not recommendation:
                recommendation = "Review and remediate according to best practices"

            sample_fix_text = ""
            cleaned_code_fix = code_fix.strip() if code_fix else ""

            if cleaned_code_fix:
                if not cleaned_code_fix.startswith("```"):
                    sample_fix_text = f"```\n{cleaned_code_fix}\n```"
                else:
                    sample_fix_text = cleaned_code_fix
            elif guidance_lines:
                sample_fix_text = "```\n# Apply the remediation guidance above in code\n```"
            else:
                sample_fix_text = "```\n# Apply security best practices\n```"
            
            finding = Finding(
                file=file_path,
                title=vulnerability_name,
                description=full_description,
                lines=str(line_num),
                impact=impact or "Security vulnerability detected",
                severity=self._normalize_severity(severity),
                confidence_score=confidence,
                cvss_v4=cvss_score,
                snippet=line.strip(),
                recommendation=recommendation,
                sample_fix=sample_fix_text,
                poc=f"# Security test for line {line_num}",
                owasp=[],
                cwe=[cwe] if cwe else [],
                references=[],
                cross_file=[],
                tool_evidence=[self._create_tool_evidence("AI Context-Aware Analysis", f"Line-by-line audit with context")]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error parsing comprehensive LLM response: {e}")
            return None
    
    def _clean_context_text(
        self,
        text: str,
        *,
        fallback: Optional[str] = None,
        line: str = "",
        line_num: Optional[int] = None,
        file_path: Optional[str] = None,
        mode: str = "function"
    ) -> str:
        """Clean and format context for professional output."""
        if not text:
            return fallback or ""

        sections = self._parse_context_sections(text)

        if mode == "usage":
            formatted_usage = self._format_usage_context(sections)
            return formatted_usage.strip()

        formatted_context = self._format_function_context(
            sections,
            line=line,
            line_num=line_num,
            file_path=file_path
        )

        if formatted_context:
            return formatted_context

        return fallback or ""

    def _parse_context_sections(self, text: str) -> Dict[str, List[str]]:
        """Break context strings into structured sections."""
        sections: Dict[str, List[str]] = {}
        if not text:
            return sections

        lines = text.split('\n')
        current_key = "GENERAL"

        for raw_line in lines:
            line = raw_line.strip()
            if not line:
                continue

            if re.search(r'Test \d+:', line) or re.search(r'[═━]+', line):
                continue

            if len(line) < 3:
                continue

            header_match = re.match(r'^([A-Z][A-Z_]+):\s*(.*)$', line)
            if header_match:
                current_key = header_match.group(1)
                value = header_match.group(2).strip()
                sections.setdefault(current_key, [])
                if value:
                    sections[current_key].append(value)
                continue

            sections.setdefault(current_key, [])
            sections[current_key].append(line)

        return sections

    def _format_function_context(
        self,
        sections: Dict[str, List[str]],
        *,
        line: str = "",
        line_num: Optional[int] = None,
        file_path: Optional[str] = None
    ) -> str:
        """Convert structured sections into readable function context."""
        if not sections:
            return ""

        formatted_parts: List[str] = []

        if 'FUNCTION' in sections:
            function_detail = ' '.join(sections['FUNCTION']).strip()
            if function_detail:
                formatted_parts.append(f"- Function: {function_detail}")
        elif 'CLASS' in sections:
            class_detail = ' '.join(sections['CLASS']).strip()
            if class_detail:
                formatted_parts.append(f"- Class: {class_detail}")

        if 'PURPOSE' in sections:
            purpose = ' '.join(sections['PURPOSE']).strip()
            if purpose:
                formatted_parts.append(f"- Purpose: {purpose}")
        elif 'CLASS_PURPOSE' in sections:
            class_purpose = ' '.join(sections['CLASS_PURPOSE']).strip()
            if class_purpose:
                formatted_parts.append(f"- Purpose: {class_purpose}")

        snippet_lines = sections.get('FUNCTION_BODY_PREVIEW') or sections.get('CLASS_BODY_PREVIEW')
        if snippet_lines:
            snippet = self._truncate_snippet('\n'.join(snippet_lines))
            if snippet:
                formatted_parts.append("**Snippet:**")
                formatted_parts.append(f"```\n{snippet}\n```")

        general_lines = sections.get('GENERAL', [])
        if general_lines:
            general_text = self._truncate_snippet('\n'.join(general_lines))
            if general_text:
                formatted_parts.append(general_text)

        cleaned_parts = self._deduplicate_list(formatted_parts)
        joined = '\n'.join(cleaned_parts).strip()

        if joined:
            return joined

        if line and line.strip():
            if line_num is not None:
                return f"Line {line_num}: `{line.strip()}`"
            return line.strip()

        return ""

    def _format_usage_context(self, sections: Dict[str, List[str]]) -> str:
        """Format data flow/usage information as tidy bullet points."""
        if not sections:
            return ""

        usage_lines: List[str] = []
        for key in ["DATA_FLOW", "USAGE", "USAGE_ANALYSIS", "GENERAL"]:
            for entry in sections.get(key, []):
                if not entry:
                    continue
                entry_clean = entry.strip()
                lowered = entry_clean.lower()
                if (not entry_clean or lowered.startswith("no clear data flow")
                        or "no significant usage" in lowered):
                    continue
                usage_lines.append(entry_clean)

        unique_lines = self._deduplicate_list(usage_lines)
        if not unique_lines:
            return ""

        return '\n'.join(f"- {line}" for line in unique_lines)

    def _truncate_snippet(self, snippet: str, max_lines: int = 8, max_chars: int = 400) -> str:
        """Trim code/context snippets to manageable size."""
        if not snippet:
            return ""

        lines = [line.rstrip() for line in snippet.strip().splitlines() if line.strip()]
        if len(lines) > max_lines:
            lines = lines[:max_lines] + ['...']

        trimmed = '\n'.join(lines)
        if len(trimmed) > max_chars:
            trimmed = trimmed[:max_chars].rstrip() + '...'

        return trimmed

    def _looks_like_code_line(self, line: str) -> bool:
        """Heuristic to decide whether a line is code rather than human guidance."""
        if not line:
            return False

        code_markers = (
            r"^```",
            r"^#",
            r"^//",
            r"^\/\/",
            r"^\s*return ",
            r"^\s*(import|from)\s+",
            r"^\s*(def|class|func|function|const|let|var)\b",
            r"\b=\b",
            r"\b:\s*$",
            r"\b\w+\(.*\)"
        )

        for pattern in code_markers:
            if re.search(pattern, line):
                return True
        return False

    def _deduplicate_list(self, values: List[str]) -> List[str]:
        """Remove near-duplicate entries while preserving order."""
        unique_values: List[str] = []
        seen: set = set()

        for value in values:
            if not value:
                continue
            normalized = re.sub(r'\s+', ' ', value).strip().lower()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            unique_values.append(value)

        return unique_values

    def _sanitize_ai_text(self, text: str) -> str:
        """Strip LLM prompt artefacts and noisy sections from generated text."""
        if not text:
            return ""

        cleaned = text

        label_tokens = [
            "SEVERITY",
            "CONFIDENCE",
            "DESCRIPTION",
            "IMPACT",
            "ROOT_CAUSE",
            "ATTACK_SCENARIO",
            "FIX",
            "REMEDIATION",
            "SECURE_CODE_EXAMPLE",
            "REFERENCE",
            "REFERENCES"
        ]

        for token in label_tokens:
            cleaned = re.sub(rf"(?<!\n){token}\s*:", f"\n{token}:", cleaned, flags=re.IGNORECASE)

        extraneous_headings = [
            "EVALUATE FALSE POSITIVE LIKELIHOOD BASED ON MITIGATING CONTROLS",
            "VULNERABILITY CATEGORIES TO CHECK",
            "CONCLUSION",
            "VULNERABILITY FOUND"
        ]

        for heading in extraneous_headings:
            pattern = rf"(?:^|\n)\s*{re.escape(heading)}:\s*(?:\n(?!\s*[A-Z][A-Z\s]+:).*)*"
            cleaned = re.sub(pattern, '\n', cleaned)

        cleaned = re.sub(r'\n{3,}', '\n\n', cleaned)
        cleaned = re.sub(r'[\t ]+\n', '\n', cleaned)

        return cleaned.strip()

    def _strip_inline_ai_labels(self, text: str) -> str:
        """Remove trailing inline metadata labels from AI segments."""
        if not text:
            return ""

        cleaned = self._sanitize_ai_text(text)
        label_pattern = re.compile(
            r"\b(SEVERITY|CONFIDENCE|DESCRIPTION|IMPACT|ROOT_CAUSE|ATTACK_SCENARIO|FIX|REMEDIATION|SECURE_CODE_EXAMPLE|REFERENCE|REFERENCES)\s*:\s*",
            re.IGNORECASE
        )

        match = label_pattern.search(cleaned)
        if match:
            cleaned = cleaned[:match.start()].strip()

        return cleaned.strip()

    def _deduplicate_paragraphs(self, text: str) -> str:
        """Remove repeated paragraphs and whitespace noise."""
        if not text:
            return ""

        sanitized = self._sanitize_ai_text(text)
        paragraphs = [p.strip() for p in re.split(r'\n\s*\n', sanitized) if p.strip()]
        unique_paragraphs: List[str] = []
        seen: set = set()

        for paragraph in paragraphs:
            normalized = re.sub(r'\s+', ' ', paragraph).strip().lower()
            if normalized in seen:
                continue
            seen.add(normalized)
            unique_paragraphs.append(paragraph)

        return '\n\n'.join(unique_paragraphs)
    
    async def _analyze_line_cross_file_connections(self, line: str, file_path: str, context: AnalysisContext) -> str:
        """Analyze how this line connects to other files"""
        connections = []
        
        try:
            # Check for imports
            if 'import ' in line or 'from ' in line:
                import_matches = re.findall(r'(?:from\s+(\S+)\s+)?import\s+([^#\n]+)', line)
                for module, items in import_matches:
                    if module:
                        connections.append(f"IMPORT: from {module} import {items.strip()}")
                    else:
                        connections.append(f"IMPORT: import {items.strip()}")
            
            # Check for function calls
            function_calls = re.findall(r'(\w+)\s*\(', line)
            if function_calls:
                real_functions = [f for f in function_calls if f not in ['if', 'for', 'while', 'with', 'try', 'except']]
                if real_functions:
                    connections.append(f"FUNCTION_CALLS: {', '.join(real_functions)}")
            
            # Check for file operations
            file_ops = re.findall(r'(open|read|write|file)\s*\(', line)
            if file_ops:
                connections.append(f"FILE_OPERATIONS: {', '.join(file_ops)}")
            
            return '\n'.join(connections) if connections else "No significant cross-file connections detected"
        
        except Exception as e:
            logger.error(f"Error analyzing cross-file connections: {e}")
            return "Cross-file analysis unavailable"
    
    async def _analyze_multi_line_patterns(self, file_path: str, lines: List[str], 
                                         context: AnalysisContext) -> List[Finding]:
        """Analyze multi-line patterns that span across multiple lines."""
        findings: List[Finding] = []

        try:
            full_content = ''.join(lines)

            pattern_metadata: Dict[str, Dict[str, Any]] = {
                'SQL injection via dynamic query construction': {
                    'title': 'Dynamic SQL Query Without Parameterization',
                    'description': (
                        'The query is built by interpolating untrusted input directly into the SQL '
                        'string before execution. This construction enables attackers to append '
                        'arbitrary SQL fragments and tamper with the database call.'
                    ),
                    'impact': (
                        'An attacker can supply crafted values for the route parameter to leak or '
                        'modify records, bypass authorisation, or drop tables because the database '
                        'executes the concatenated statement verbatim.'
                    ),
                    'recommendation': [
                        'Switch to parameterised queries or prepared statements so user input is '
                        'bound as data, not executable SQL.',
                        'Normalise and validate the identifier (for example, ensure it is numeric '
                        'before it reaches the database layer).',
                        'Prefer ORM helpers or query builders that escape parameters automatically.'
                    ],
                    'sample_fix': (
                        '```ruby\n'
                        "db.execute('SELECT * FROM users WHERE id = ?', params[:id].to_i)\n"
                        '```'
                    ),
                    'poc': (
                        'Invoke the endpoint with `?id=1 OR 1=1` to demonstrate data leakage and '
                        'confirm the query is injectable.'
                    ),
                    'cwe': ['CWE-89']
                },
                'Function contains exec() call': {
                    'title': 'Arbitrary Command Execution via exec()',
                    'description': (
                        'The function invokes `exec()` on values that can be influenced by callers. '
                        'Executing dynamically constructed commands makes it trivial for attackers to '
                        'inject additional shell payloads.'
                    ),
                    'impact': (
                        'Supplying shell metacharacters alongside legitimate input lets an attacker '
                        'run arbitrary commands with the privileges of the process, leading to full '
                        'system compromise.'
                    ),
                    'recommendation': [
                        'Avoid `exec()` for user-controlled strings; prefer high-level APIs such as '
                        '`subprocess.run` or language-specific command wrappers.',
                        'If shell execution is required, supply arguments as a list and set '
                        '`shell=False` (or equivalent) to prevent command concatenation.',
                        'Validate or allow-list permitted commands before execution.'
                    ],
                    'sample_fix': (
                        '```python\n'
                        'import os\n'
                        'import subprocess\n\n'
                        'def execute_directory_listing(path: str) -> None:\n'
                        '    safe_path = os.path.abspath(path)\n'
                        '    subprocess.run(["ls", safe_path], check=True)\n'
                        '```'
                    ),
                    'poc': (
                        'Pass a payload such as `"; rm -rf /"` to show that the current implementation '
                        'will execute arbitrary commands.'
                    ),
                    'cwe': ['CWE-78', 'CWE-94']
                },
                'File operation with user input': {
                    'title': 'Untrusted File Path Handling',
                    'description': (
                        'User-controlled data is fed into a file operation without validation. '
                        'Attackers can traverse directories or overwrite files by manipulating the '
                        'supplied path.'
                    ),
                    'impact': (
                        'Unauthorised file reads or writes allow disclosure of sensitive data, '
                        'modification of application resources, or remote code execution when '
                        'combined with log or template poisoning.'
                    ),
                    'recommendation': [
                        'Resolve paths against a known base directory and reject paths that escape '
                        'that boundary.',
                        'Validate filenames against an allow-list or explicit pattern before using '
                        'them in `open()`/`File.read` calls.',
                        'Use safe wrappers (for example, `pathlib.Path.resolve()` or framework '
                        'helpers) that enforce canonical paths.'
                    ],
                    'sample_fix': (
                        '```python\n'
                        'from pathlib import Path\n\n'
                        'def safe_read(filename: str) -> str:\n'
                        '    base = Path("/uploads").resolve()\n'
                        '    candidate = (base / filename).resolve()\n'
                        '    if base not in candidate.parents:\n'
                        '        raise ValueError("Invalid path supplied")\n'
                        '    return candidate.read_text()\n'
                        '```'
                    ),
                    'poc': (
                        'Attempt to read `../../etc/passwd` to verify that the current implementation '
                        'exposes files outside the intended directory.'
                    ),
                    'cwe': ['CWE-22']
                }
            }

            patterns_to_check = [
                (r'query\s*=\s*["\'].*?["\'].+?execute\(query', 'SQL injection via dynamic query construction'),
                (r'def\s+\w+.*?exec\s*\(', 'Function contains exec() call'),
                (r'open\s*\(\s*.*?input\s*\(', 'File operation with user input'),
            ]

            for pattern, pattern_key in patterns_to_check:
                matches = re.finditer(pattern, full_content, re.IGNORECASE | re.DOTALL)

                for match in matches:
                    line_num = full_content[:match.start()].count('\n') + 1
                    span_lines = match.group(0).count('\n') + 1
                    end_line = line_num + span_lines - 1
                    line_range = f"{line_num}-{end_line}" if end_line > line_num else str(line_num)

                    start_index = max(0, line_num - 3)
                    end_index = min(len(lines), end_line + 2)
                    snippet_lines = [f"{idx + 1:04d}: {lines[idx].rstrip()}" for idx in range(start_index, end_index)]
                    snippet = '\n'.join(snippet_lines).strip()

                    metadata = pattern_metadata.get(pattern_key, {})
                    title = metadata.get('title', f"Multi-line security pattern: {pattern_key}")
                    base_description = metadata.get('description', f"Detected multi-line pattern: {pattern_key}.")
                    poc_text = metadata.get('poc', f"Review the code around line {line_num} for security implications.")
                    impact_text = metadata.get('impact', 'Potential security vulnerability detected across multiple lines')
                    rec_items = metadata.get('recommendation', ['Review the multi-line code pattern for security implications.'])
                    recommendation = '\n'.join(f"- {item}" for item in rec_items)
                    sample_fix = metadata.get('sample_fix', '# Apply appropriate security controls for this pattern')
                    cwe_ids = metadata.get('cwe', [])

                    description = (
                        f"{base_description}\n\n"
                        f"**Affected Code:**\n```\n{snippet}\n```"
                    )

                    cvss_score = CVSSv4(
                        score=6.0,
                        vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:L/SC:N/SI:N/SA:N"
                    )

                    finding = Finding(
                        file=file_path,
                        title=title,
                        description=description,
                        lines=line_range,
                        impact=impact_text,
                        severity=metadata.get('severity', 'Medium'),
                        confidence_score=80,
                        cvss_v4=cvss_score,
                        snippet=snippet,
                        recommendation=recommendation,
                        sample_fix=sample_fix,
                        poc=poc_text,
                        owasp=[],
                        cwe=cwe_ids,
                        references=[],
                        cross_file=[],
                        tool_evidence=[
                            self._create_tool_evidence(
                                "Multi-line Pattern Detection",
                                f"{title} detected at line {line_num}"
                            )
                        ]
                    )

                    findings.append(finding)

        except Exception as e:
            logger.error(f"Error in multi-line analysis: {e}")

        return findings
    
    async def _analyze_business_logic(self, code_context: Dict[str, Any], context: AnalysisContext) -> List[Finding]:
        """Analyze business logic vulnerabilities"""
        # Placeholder implementation
        return []
    
    async def _analyze_architecture_security(self, code_context: Dict[str, Any], context: AnalysisContext) -> List[Finding]:
        """Analyze architecture-level security issues"""
        # Placeholder implementation
        return []
    
    async def _parse_structured_ai_response(self, ai_response: str, file_path: str, 
                                          line_num: int, line_content: str, 
                                          context: AnalysisContext) -> Optional[Finding]:
        """Parse structured AI response into Finding object"""
        try:
            # Extract structured information from AI response
            sections = {}
            current_section = None
            current_content = []
            
            for line in ai_response.split('\n'):
                line = line.strip()
                if line.endswith(':') and line.upper().replace('_', '') in [
                    'ISSUENAME:', 'DESCRIPTION:', 'AFFECTEDCODE:', 'IMPACT:', 'SEVERITY:', 
                    'TAILOREDRECOMMENDATION:', 'SECURECODEEXAMPLE:', 'REFERENCES:'
                ]:
                    if current_section:
                        sections[current_section] = '\n'.join(current_content)
                    current_section = line.rstrip(':').upper().replace('_', '')
                    current_content = []
                elif current_section:
                    current_content.append(line)
            
            if current_section:
                sections[current_section] = '\n'.join(current_content)
            
            title = sections.get('ISSUENAME', 'AI-detected security vulnerability')
            description = sections.get('DESCRIPTION', ai_response[:300])
            impact = sections.get('IMPACT', 'Potential security risk')
            severity = self._normalize_severity(self._extract_severity_from_text(sections.get('SEVERITY', 'Medium')))
            recommendation = sections.get('TAILOREDRECOMMENDATION', 'Review and address the security issue')
            secure_example = sections.get('SECURECODEEXAMPLE', '# See recommendation for fix')
            references = sections.get('REFERENCES', '')
            
            cvss_score = CVSSv4(
                score=self._severity_to_cvss_score(severity),
                vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:L/SC:N/SI:N/SA:N"
            )
            
            finding = Finding(
                file=file_path,
                title=title,
                description=description,
                lines=str(line_num),
                impact=impact,
                severity=severity,
                cvss_v4=cvss_score,
                snippet=line_content,
                recommendation=recommendation,
                sample_fix=secure_example,
                poc=f"Line {line_num}: {line_content}",
                owasp=[],
                cwe=[],
                references=[ref.strip() for ref in references.split(',') if ref.strip()],
                cross_file=[],
                tool_evidence=[]
            )
            
            return finding
            
        except Exception as e:
            logger.error(f"Error parsing structured AI response: {e}")
            return None
    
    def _extract_severity_from_text(self, text: str) -> str:
        """Extract severity level from AI response text"""
        text_lower = text.lower()
        if 'critical' in text_lower:
            return 'Critical'
        elif 'high' in text_lower:
            return 'High'
        elif 'medium' in text_lower:
            return 'Medium'
        elif 'low' in text_lower:
            return 'Low'
        return 'Medium'
    
    def _normalize_severity(self, severity: str) -> str:
        """Normalize severity to match schema validation"""
        if not severity:
            return 'Medium'
        
        severity_map = {
            'critical': 'Critical',
            'high': 'High', 
            'medium': 'Medium',
            'low': 'Low',
            'info': 'Low',
            'informational': 'Low'
        }
        
        normalized = severity_map.get(severity.lower().strip())
        return normalized if normalized else 'Medium'
    
    def _create_tool_evidence(self, tool_name: str, evidence_text: str) -> ToolEvidence:
        """Create a ToolEvidence object"""
        import uuid
        return ToolEvidence(
            tool=tool_name,
            id=str(uuid.uuid4())[:8],
            raw=evidence_text
        )
    
    async def analyze_findings_with_ai(self, findings: List[Finding], context: AnalysisContext) -> List[Finding]:
        """Analyze existing findings with AI to enhance them"""
        enhanced_findings = []
        
        for finding in findings:
            try:
                # Get additional context for the finding
                line_num = self._extract_line_number(finding.lines)
                code_context = await self._get_code_context(finding.file, line_num)
                
                # Enhance finding with AI analysis
                enhanced_finding = await self._enhance_finding_with_ai(finding, code_context, context)
                enhanced_findings.append(enhanced_finding or finding)
                
            except Exception as e:
                logger.error(f"Error enhancing finding {finding.title}: {e}")
                enhanced_findings.append(finding)
        
        return enhanced_findings
    
    async def _enhance_finding_with_ai(self, finding: Finding, code_context: str, 
                                     context: AnalysisContext) -> Optional[Finding]:
        """Enhance a finding with AI analysis"""
        try:
            enhancement_prompt = f"""
            Enhance this security finding with additional analysis:
            
            Original Finding:
            Title: {finding.title}
            Description: {finding.description}
            Severity: {finding.severity}
            File: {finding.file}:{finding.lines}
            
            Code Context:
            {code_context}
            
            Provide enhanced analysis including:
            1. More detailed impact assessment
            2. Specific exploitation scenarios
            3. Improved remediation advice
            4. Updated severity if needed
            """
            
            if self.agent_executor:
                result = await self.agent_executor.ainvoke({
                    "context": enhancement_prompt
                })
                
                # Parse enhancement and update finding
                enhanced_description = result.get("output", finding.description)
                
                # Create enhanced finding
                enhanced_finding = Finding(
                    file=finding.file,
                    title=finding.title,
                    description=enhanced_description,
                    lines=finding.lines,
                    impact=finding.impact,
                    severity=finding.severity,
                    cvss_v4=finding.cvss_v4,
                    snippet=finding.snippet,
                    recommendation=finding.recommendation,
                    sample_fix=finding.sample_fix,
                    poc=finding.poc,
                    owasp=finding.owasp,
                    cwe=finding.cwe,
                    references=finding.references,
                    cross_file=finding.cross_file,
                    tool_evidence=finding.tool_evidence + [self._create_tool_evidence("AI Enhancement", "AI-enhanced security analysis")]
                )
                
                return enhanced_finding
            
        except Exception as e:
            logger.error(f"Error enhancing finding: {e}")
        
        return None
    
    async def execute(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Main execution method for AI-powered security audit
        """
        try:
            workspace_path = context.get('workspace_path', '.')
            target_files = context.get('target_files', [])
            findings = context.get('findings', [])
            
            if not target_files:
                return {
                    'success': False,
                    'error': 'No target files provided for analysis',
                    'ai_findings': []
                }
            
            # Create AnalysisContext
            analysis_context = AnalysisContext(
                workspace_path=workspace_path,
                repo_path=workspace_path,
                target_files=target_files[:10],  # Limit for performance
                languages=context.get('languages', []),
                technologies=context.get('technologies', {}),
            )
            
            ai_findings = []
            
            # Analyze existing scanner findings if provided
            if findings:
                enhanced_findings = await self.analyze_findings_with_ai(findings, analysis_context)
                ai_findings.extend(enhanced_findings)
            
            # Perform line-by-line analysis
            line_by_line_findings = await self.perform_line_by_line_analysis(target_files, analysis_context)
            ai_findings.extend(line_by_line_findings)
            
            # Perform cross-file analysis if multiple files
            if len(target_files) > 1:
                cross_file_findings = await self._analyze_cross_file_interactions(target_files, analysis_context)
                ai_findings.extend(cross_file_findings)
            
            return {
                'success': True,
                'ai_findings': ai_findings,
                'analysis_context': analysis_context,
                'stats': {
                    'files_analyzed': len(target_files),
                    'ai_findings_count': len(ai_findings),
                    'line_by_line_findings': len(line_by_line_findings),
                    'enhancement_applied': len(findings) > 0
                }
            }
            
        except Exception as e:
            logger.error(f"AuditorAgent execution failed: {e}")
            return self.handle_error(e, context)
    
    async def _analyze_cross_file_interactions(self, files: List[str], context: AnalysisContext) -> List[Finding]:
        """Analyze interactions between multiple files for security issues"""
        findings = []
        
        if len(files) < 2:
            return findings
        
        try:
            logger.info(f"Starting cross-file analysis for {len(files)} files")
            
            # Simple cross-file analysis implementation
            file_imports = {}
            file_functions = {}
            
            # Parse each file for imports and function definitions
            for file_path in files:
                if not os.path.exists(file_path):
                    continue
                
                try:
                    with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                        content = f.read()
                    
                    # Extract imports
                    imports = re.findall(r'(?:from\s+(\S+)\s+)?import\s+([^\n#]+)', content)
                    file_imports[file_path] = imports
                    
                    # Extract function definitions
                    functions = re.findall(r'def\s+(\w+)\s*\(', content)
                    file_functions[file_path] = functions
                    
                except Exception as e:
                    logger.error(f"Error parsing file {file_path}: {e}")
            
            # Look for potential security issues across files
            for file_path, imports in file_imports.items():
                for import_info in imports:
                    if await self._is_dangerous_cross_file_pattern(file_path, import_info, file_functions):
                        cvss_score = CVSSv4(score=6.0, vector="CVSS:4.0/AV:N/AC:L/AT:N/PR:N/UI:N/VC:L/VI:L/VA:L/SC:N/SI:N/SA:N")
                        
                        finding = Finding(
                            file=file_path,
                            title=f"Potentially Dangerous Cross-File Import",
                            description=f"Dangerous import pattern detected: {import_info}",
                            lines="1",
                            impact="Cross-file security dependency may introduce vulnerabilities",
                            severity="Medium",
                            cvss_v4=cvss_score,
                            snippet=str(import_info),
                            recommendation="Review the security implications of this cross-file import",
                            sample_fix="Validate imported functionality and apply security controls",
                            poc="# Review cross-file import security",
                            owasp=[],
                            cwe=[],
                            references=[],
                            cross_file=list(file_functions.keys()),
                            tool_evidence=[self._create_tool_evidence("Cross-file Interaction Analysis", f"Import analysis: {import_info}")]
                        )
                        findings.append(finding)
            
            logger.info(f"Cross-file analysis completed: {len(findings)} findings")
        
        except Exception as e:
            logger.error(f"Error in cross-file analysis: {e}")
        
        return findings
    
    async def _is_dangerous_cross_file_pattern(self, file_path: str, import_info: tuple, 
                                             file_functions: Dict[str, List[str]]) -> bool:
        """Check if a cross-file import pattern represents a security risk"""
        dangerous_patterns = [
            'subprocess', 'os', 'pickle', 'marshal', 'eval', 'exec',
            'input', 'raw_input', 'urllib', 'requests'
        ]
        
        module_name = import_info[1] if len(import_info) > 1 else import_info[0]
        return any(pattern in str(module_name).lower() for pattern in dangerous_patterns)