# AI + Cross-File Analysis Integration

## Overview

**Yes, cross-file analysis and tracing works with AI—including local models!** The AI auditor agent automatically enriches all findings—whether discovered by cloud AI (OpenAI, Anthropic), local models (Ollama, LlamaCpp), static analysis tools, or manual inspection—with AST-based cross-file call graph traces.

## Local Model Support

Cross-file analysis is **completely model-agnostic**. It works equally well with:

- ✅ **Cloud Models**: OpenAI GPT-4, Anthropic Claude
- ✅ **Local Ollama**: DeepSeek-Coder, CodeLlama, Llama 3.1, Mistral
- ✅ **Local LlamaCpp**: Any GGUF quantized models
- ✅ **Local Transformers**: HuggingFace models

### Why Local Models?

**Privacy & Security:**
- Code never leaves your machine
- No cloud API keys required
- Compliant with strict data policies

**Cost Efficiency:**
- No per-token API charges
- Unlimited analysis runs
- One-time model download

**Performance:**
- No network latency
- GPU acceleration available
- Fast cross-file tracing (~100ms)

## How It Works

### Integration Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    AI Auditor Agent                          │
│                                                              │
│  1. AI discovers vulnerabilities (LLM reasoning)             │
│  2. Validates scanner findings (reduces false positives)     │
│  3. Performs line-by-line deep analysis                      │
│  4. Analyzes cross-file data flows (AI-based)                │
│                                                              │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  All findings combined                               │   │
│  └───────────────────┬─────────────────────────────────┘   │
│                      │                                       │
│                      ▼                                       │
│  ┌─────────────────────────────────────────────────────┐   │
│  │  AST-Based Cross-File Enrichment                     │   │
│  │  (annotate_cross_file_context)                       │   │
│  │                                                       │   │
│  │  • Builds call graph from source code                │   │
│  │  • Traces function calls across files                │   │
│  │  • Adds execution paths to findings                  │   │
│  └─────────────────────────────────────────────────────┘   │
│                      │                                       │
│                      ▼                                       │
│             Enriched Findings                                │
└─────────────────────────────────────────────────────────────┘
```

### Code Integration

In `src/securecli/agents/auditor.py`:

```python
async def perform_audit(self, context: AnalysisContext) -> List[Finding]:
    # ... AI analysis discovers vulnerabilities ...
    
    # Combine all findings from various sources
    all_findings = validated_findings + ai_findings + line_by_line_findings + cross_file_findings
    
    # Enrich ALL findings with AST-based cross-file tracing
    if context.workspace_root and all_findings:
        try:
            logger.info("Enriching findings with cross-file call graph traces")
            annotate_cross_file_context(context.workspace_root, all_findings)
            logger.info(f"Added cross-file traces to {sum(1 for f in all_findings if f.cross_file)} findings")
        except Exception as e:
            logger.warning(f"Cross-file enrichment failed: {e}")
    
    return final_findings
```

## Benefits of AI + Cross-File Analysis

### 1. **AI Discovers, Static Analysis Traces**

- **AI Auditor**: Uses LLM reasoning to identify complex vulnerabilities that static tools might miss
- **Cross-File Analyzer**: Provides concrete execution paths showing how the vulnerability propagates

**Example:**
```
AI Finding: "Insufficient file upload validation allows malicious files"
Cross-File Trace: app.py:handle_upload → validator.py:validate_file → storage.py:store_file
```

### 2. **Reduced False Positives**

- AI validates scanner findings using contextual understanding
- Cross-file traces provide evidence of actual code paths
- Combined analysis confirms vulnerability exploitability

### 3. **Complete Impact Assessment**

- AI identifies the security issue
- Static analysis shows which components are affected
- Traces reveal the full attack surface

### 4. **Enhanced Explanations**

Findings include both:
- **AI Reasoning**: Why it's a vulnerability, what could go wrong
- **Static Traces**: Concrete code paths showing dataflow

## What Gets Enriched

### All Finding Sources

1. **AI-Discovered Vulnerabilities**
   - Deep semantic analysis findings
   - Pattern-based vulnerability detection
   - Business logic flaws

2. **Validated Scanner Findings**
   - Tool findings confirmed by AI
   - Reduced false positive rate
   - Context-aware severity adjustment

3. **Line-by-Line Analysis**
   - Detailed code inspection results
   - Context-specific vulnerabilities

4. **Cross-File Data Flow Analysis**
   - AI-detected data flow issues
   - Plus AST-based call graphs

## Demonstration Results

### Test Case: File Upload Vulnerability

**Setup:**
- `app.py`: Entry point handling uploads
- `validator.py`: File validation logic
- `storage.py`: File storage operations

**AI Finding:**
```
Title: Insufficient File Upload Validation
Severity: High
Description: AI detected that file upload validation is insufficient
```

**After Cross-File Enrichment:**
```
Cross-File Traces (2 paths):
1. app.py:handle_upload → validator.py:validate_file
2. app.py:handle_upload → validator.py:validate_file → storage.py:check_file_type

Components Traced: Entry Point → Validator → Storage
```

**Result:** ✓ AI identified the vulnerability, static analysis traced its impact across 3 components

## Usage

### Automatic in AI Auditor (Cloud or Local)

When using the AI auditor agent with any model provider, cross-file enrichment happens automatically:

```python
from securecli.agents.auditor import AuditorAgent

# Works with any model: OpenAI, Anthropic, or local
auditor = AuditorAgent()
findings = await auditor.perform_audit(context)

# Findings already include cross-file traces
for finding in findings:
    if finding.cross_file:
        print(f"Traces: {finding.cross_file}")
```

### Configuration Examples

**Cloud Model (OpenAI):**
```yaml
ai:
  provider: openai
  api_key: sk-...
  model: gpt-4
```

**Local Model (Ollama):**
```yaml
ai:
  provider: local
  local_model:
    enabled: true
    engine: ollama
    model_name: deepseek-coder
    base_url: http://localhost:11434
```

**Local Model (LlamaCpp):**
```yaml
ai:
  provider: local
  local_model:
    enabled: true
    engine: llamacpp
    model_path: /path/to/model.gguf
    gpu_layers: 35
```

### Manual Enrichment

You can also manually enrich any findings:

```python
from securecli.analysis import annotate_cross_file_context

# Your findings from any source (AI, scanners, manual)
findings = [...]

# Enrich with cross-file traces
annotate_cross_file_context(repo_root, findings)
```

## Technical Details

### AI Analysis Methods

The AI auditor uses multiple analysis techniques:

1. **Validation Analysis**: Reviews scanner findings with context
2. **Deep Semantic Analysis**: Discovers new vulnerabilities using LLM
3. **Line-by-Line Inspection**: Detailed code review with AI reasoning
4. **Data Flow Analysis**: Traces data movement (AI-based)

### Cross-File Enrichment

After AI analysis completes:

1. **AST Parsing**: Parse Python source files
2. **Call Graph Construction**: Build function-to-function mappings
3. **Path Tracing**: BFS traversal to find execution paths
4. **Finding Annotation**: Attach traces to `Finding.cross_file` field

### Performance

- **AI Analysis**: Depends on LLM (GPT-4, Claude, etc.)
- **Cross-File Enrichment**: ~100ms for typical projects
- **Combined**: Marginal overhead, significant value

## Limitations

### Current Scope

1. **Language Support**: Cross-file tracing currently Python-only
   - AI analysis works for all languages
   - Static tracing limited to Python AST

2. **Analysis Depth**: 
   - AI provides semantic understanding
   - Static analysis provides concrete paths
   - Dynamic behavior not captured

3. **Call Graph Accuracy**:
   - Direct function calls traced accurately
   - Dynamic dispatch, callbacks limited
   - Reflection/metaprogramming not resolved

## Future Enhancements

### Planned Improvements

1. **Multi-Language Tracing**
   - JavaScript/TypeScript support
   - Go, Java, Rust analyzers
   - Cross-language boundary tracing

2. **AI-Guided Tracing**
   - LLM helps resolve dynamic calls
   - Semantic understanding of frameworks
   - Intent-based path discovery

3. **Hybrid Analysis**
   - Combine AI insights with static traces
   - LLM explains why paths are vulnerable
   - Prioritize traces by AI-assessed risk

4. **Interactive Exploration**
   - Ask AI questions about traces
   - "Show me how user input reaches the database"
   - AI-generated attack scenarios

## Examples

### Example 1: SQL Injection with AI + Tracing

**AI Discovery:**
```
Finding: SQL Injection via User Input
Confidence: 95%
Reasoning: User-controlled data flows into SQL query without sanitization
```

**Cross-File Trace:**
```
web/routes.py:login_handler
  → auth/validator.py:check_credentials
    → db/queries.py:execute_raw_query [VULNERABLE]
```

**Combined Result:**
- AI explains the vulnerability pattern
- Trace shows exact code path from entry to sink
- Clear remediation guidance with specific file:line references

### Example 2: Business Logic Flaw

**AI Discovery:**
```
Finding: Authorization Bypass in Payment Flow
Confidence: 88%
Reasoning: Payment verification skipped when using discount codes
```

**Cross-File Trace:**
```
api/payment.py:process_payment
  → services/discount.py:apply_discount
    → models/order.py:finalize_order [BYPASSES CHECK]
```

**Combined Result:**
- AI identified subtle logic flaw
- Trace proves the vulnerable path exists
- Shows which functions need authorization checks

## Comparison

### Before Integration

**AI Only:**
- ✓ Discovers complex vulnerabilities
- ✓ Explains security implications
- ✗ No concrete code paths
- ✗ Hard to verify findings

**Static Analysis Only:**
- ✓ Shows exact code paths
- ✓ Fast, deterministic results
- ✗ Misses semantic issues
- ✗ High false positive rate

### After Integration

**AI + Cross-File Analysis:**
- ✓ Discovers complex vulnerabilities (AI)
- ✓ Shows concrete execution paths (Static)
- ✓ Explains security implications (AI)
- ✓ Proves exploitability (Static traces)
- ✓ Reduced false positives (AI validation + Static proof)
- ✓ Complete impact assessment (Combined)

## Conclusion

**Cross-file analysis works seamlessly with AI**, providing the best of both worlds:

- **AI Intelligence**: Discovers vulnerabilities that static tools miss
- **Static Precision**: Proves findings with concrete code paths
- **Automatic Integration**: No extra work required
- **Enhanced Value**: Better findings with more context

The integration is automatic, efficient, and significantly enhances the quality and actionability of security findings.

## References

- [AI Auditor Implementation](../src/securecli/agents/auditor.py)
- [Cross-File Analyzer](../src/securecli/analysis/cross_file.py)
- [Integration Test](../examples/test_ai_cross_file.py)
- [Cross-File Analysis Documentation](./CROSS_FILE_ANALYSIS.md)
