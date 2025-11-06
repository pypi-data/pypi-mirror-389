# Cross-File Analysis

## Overview

SecureCLI now includes cross-file context tracing for security findings. This feature tracks how vulnerable code flows across multiple files in your codebase, helping identify the full scope and impact of security issues.

## Features

### Automatic Call Graph Construction

The analyzer automatically builds a lightweight call graph for Python codebases by:
- Parsing Python files using AST (Abstract Syntax Tree) analysis
- Extracting function definitions and their calls to other functions
- Tracking cross-file function invocations
- Building a map of function dependencies

### Finding Enrichment

When security findings are detected, the system:
1. Locates the function containing the vulnerable code
2. Traces function calls across files (up to 6 hops deep)
3. Generates up to 10 representative call chains
4. Attaches traces to the finding's `cross_file` field

### End-to-End Request Tracing

The analyzer can trace request flows through multiple layers:
- **UI Layer** → User interface code handling input
- **API Layer** → Request handlers and routing
- **Service Layer** → Business logic and processing
- **Data Layer** → Database access and queries
- **External Calls** → Third-party API integrations

## Integration Points

### CLI Commands

Cross-file analysis is automatically applied in:
- `scan` command - Enriches scan results before display
- `report` command - Includes traces in generated reports

### CI/CD Pipeline

The analysis is integrated into the main CI workflow:
- Runs after all security tools complete scanning
- Enriches findings before generating reports
- Automatically includes traces in JSON/Markdown output

### GitHub Analyzer

Repository analysis includes cross-file tracing:
- Analyzes workspace after cloning
- Traces vulnerabilities across repository structure
- Includes traces in analysis results

## API Usage

### Programmatic Access

```python
from pathlib import Path
from securecli.analysis import annotate_cross_file_context
from securecli.schemas.findings import Finding

# Create or load findings
findings = [...]  # Your Finding objects

# Enrich with cross-file traces
repo_root = Path("/path/to/repo")
annotate_cross_file_context(repo_root, findings)

# Access traces
for finding in findings:
    if finding.cross_file:
        print(f"Finding: {finding.title}")
        for trace in finding.cross_file:
            print(f"  → {trace}")
```

### Direct Analyzer Usage

```python
from pathlib import Path
from securecli.analysis.cross_file import CrossFileAnalyzer

# Initialize analyzer
analyzer = CrossFileAnalyzer(Path("/path/to/repo"))

# Build call graph
analyzer.index_repository()

# Enrich findings
analyzer.enrich_findings(findings)
```

## Output Format

### Cross-File Traces

Traces are formatted as function call chains:
```
ui.py:handle_request -> api.py:process_data -> db.py:execute_query
```

Each trace shows:
- Source file and function name
- Arrow (`->`) indicating call direction
- Target file and function name

### Report Integration

#### JSON Reports
```json
{
  "findings": [
    {
      "id": "finding-001",
      "title": "SQL Injection",
      "file": "database.py",
      "cross_file": [
        "routes.py:login -> auth.py:authenticate -> database.py:check_credentials"
      ]
    }
  ]
}
```

#### Markdown Reports
```markdown
### Finding: SQL Injection

**File:** `database.py`

**Cross-File Context:**
- `routes.py:login` → `auth.py:authenticate` → `database.py:check_credentials`
```

## Configuration

### Analysis Depth

The analyzer uses the following defaults:
- **Max Traces:** 10 traces per finding
- **Max Depth:** 6 function calls deep
- **File Filter:** Python files only (`.py`)

### Performance

The analyzer is designed for efficiency:
- Caches parsed AST trees
- Only parses Python files once
- Uses depth-limited BFS for tracing
- Skips files with syntax errors gracefully

## Test Coverage

Comprehensive test suite with **87.72% coverage**:

### Unit Tests (`tests/unit/test_cross_file_analysis.py`)

✅ **test_function_node_qualified_name** - Verifies node naming conventions
✅ **test_analyzer_index_simple_repo** - Tests repository indexing
✅ **test_trace_cross_file_paths** - Validates cross-file tracing logic
✅ **test_enrich_findings_with_cross_file_context** - Tests finding enrichment
✅ **test_end_to_end_request_trace** - Validates full stack tracing (UI→API→Service→Data→External)
✅ **test_no_cross_file_when_self_contained** - Ensures self-contained code isn't flagged
✅ **test_handles_syntax_errors_gracefully** - Verifies error handling for broken files
✅ **test_integration_with_scan_pipeline** - Tests pipeline integration

## Limitations

### Current Scope

- **Python Only:** Currently supports Python codebases
- **Static Analysis:** Uses AST parsing (no runtime tracing)
- **Direct Calls:** Tracks direct function calls only
- **No Dynamic Dispatch:** Doesn't resolve polymorphic calls

### Not Tracked

- Indirect calls via function pointers or callbacks
- Dynamic imports or `eval()`-style execution
- Method calls through reflection
- Calls to external libraries (tracked as endpoints)

## Future Enhancements

### Planned Features

1. **Multi-Language Support**
   - JavaScript/TypeScript call tracing
   - Go, Java, and other language support

2. **Advanced Analysis**
   - Data flow tracking (taint analysis)
   - Control flow graph integration
   - Dynamic dispatch resolution

3. **Visualization**
   - Interactive call graph diagrams
   - Flow visualization in reports
   - Dependency heat maps

4. **Layer Classification**
   - Automatic detection of architectural layers
   - UI/API/Service/Data/External classification
   - Layer violation detection

## Examples

### Example 1: SQL Injection Trace

Finding in `database.py` line 42:
```python
def execute_query(username):
    query = f"SELECT * FROM users WHERE name='{username}'"  # Vulnerable
    return db.execute(query)
```

Cross-file trace shows origin:
```
web/routes.py:user_profile -> auth/validator.py:check_user -> database.py:execute_query
```

### Example 2: Multi-Layer Request Flow

Finding in `api_client.py` line 15:
```python
def fetch_user_data(user_id):
    url = f"https://api.example.com/users/{user_id}"  # Unvalidated input
    return requests.get(url)
```

Cross-file trace shows full flow:
```
ui/dashboard.py:render_profile -> api/handlers.py:get_profile -> services/user_service.py:fetch_details -> data/api_client.py:fetch_user_data
```

## Troubleshooting

### No Traces Generated

If findings don't have cross-file traces:
1. Verify the repository is Python-based
2. Check that finding line numbers are within function definitions
3. Ensure the vulnerable function makes cross-file calls
4. Verify files don't have syntax errors

### Missing Expected Traces

If some traces are missing:
1. Check if depth limit (6 hops) was exceeded
2. Verify function calls use standard Python syntax
3. Check if dynamic dispatch or callbacks are used
4. Ensure imported modules are in the repository

### Performance Issues

If analysis is slow:
1. Check repository size (10,000+ Python files may be slow)
2. Verify no extremely large files (>10,000 lines)
3. Check for circular dependencies in codebase
4. Consider filtering specific directories

## Contributing

To extend cross-file analysis:

1. **Add Language Support:** Implement parsers for other languages
2. **Enhance Tracing:** Add taint analysis or data flow tracking
3. **Improve Performance:** Optimize AST parsing and caching
4. **Add Visualizations:** Create interactive call graph displays

See `src/securecli/analysis/cross_file.py` for implementation details.

## References

- [Python AST Documentation](https://docs.python.org/3/library/ast.html)
- [Static Analysis Techniques](https://en.wikipedia.org/wiki/Static_program_analysis)
- [Call Graph Construction](https://en.wikipedia.org/wiki/Call_graph)
- [Taint Analysis](https://en.wikipedia.org/wiki/Taint_checking)
