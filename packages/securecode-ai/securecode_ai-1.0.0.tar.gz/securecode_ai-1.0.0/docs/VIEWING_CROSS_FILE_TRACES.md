# Viewing Cross-File Traces in Interactive CLI

This guide shows you how to confirm and view cross-file analysis traces in the SecureCLI interactive environment.

## Quick Answer

Cross-file traces appear automatically in:
1. **Detailed finding views** (`scan deep` command)
2. **Report output** (Markdown and JSON formats)
3. **Console output** (when enrichment completes)

## Method 1: Interactive CLI - Detailed View

### Step 1: Start Interactive CLI

```bash
securecli
```

Or enter REPL mode:
```bash
securecli repl
```

### Step 2: Run Deep Scan

```
SecureCLI> scan deep /path/to/your/project
```

The `deep` mode shows full finding details including cross-file traces.

### Example Output:

```
╭─────────────────────────────────────────────────────────────╮
│              Finding #1 - High Severity                      │
╰─────────────────────────────────────────────────────────────╯

SQL Injection in User Query

File: database.py:42
Tool: Bandit
CVSS Score: 8.5
Confidence: 95%

Description:
User input directly concatenated into SQL query without sanitization

Impact:
Database compromise, data exfiltration possible

Recommendation:
Use parameterized queries with bound parameters

Cross-File Execution Traces (3 paths):
1. `web/routes.py:login_handler → auth/verify.py:check_credentials → database.py:execute_query`
2. `web/routes.py:profile_handler → auth/verify.py:check_credentials → database.py:execute_query`
3. `api/handlers.py:user_api → auth/verify.py:check_credentials → database.py:execute_query`
```

### Step 3: Check Enrichment Status

When cross-file analysis runs, you'll see:

```
[*] Enriching findings with cross-file call graph traces
[*] Added cross-file traces to 5 findings
```

## Method 2: Generate Reports

### Markdown Report

```bash
securecli report /path/to/project --format markdown --output security-report.md
```

Open `security-report.md` and look for the **"Cross-File Execution Traces"** section in each finding.

### Example Markdown Output:

```markdown
#### 1. SQL Injection in Authentication

**File:** `database.py:42`
**Severity:** Critical | **CVSS v4.0:** 9.8

<details>
<summary><strong>Cross-File Execution Traces (3)</strong></summary>

These traces show how this vulnerability connects across multiple files:

1. `web/routes.py:login_handler → auth/verify.py:check_credentials → database.py:execute_query`
2. `web/routes.py:profile_handler → auth/verify.py:check_credentials → database.py:execute_query`
3. `api/handlers.py:user_api → auth/verify.py:check_credentials → database.py:execute_query`

</details>
```

### JSON Report

```bash
securecli report /path/to/project --format json --output security-report.json
```

Open `security-report.json` and look for `cross_file` arrays:

```json
{
  "findings": [
    {
      "id": "finding-001",
      "title": "SQL Injection",
      "file": "database.py",
      "lines": "42",
      "cross_file": [
        "web/routes.py:login_handler -> auth/verify.py:check_credentials -> database.py:execute_query",
        "web/routes.py:profile_handler -> auth/verify.py:check_credentials -> database.py:execute_query"
      ]
    }
  ],
  "statistics": {
    "cross_file_issues": 5
  }
}
```

## Method 3: Programmatic Access

### Python Script

```python
from pathlib import Path
from securecli.analysis import CrossFileAnalyzer

# Initialize analyzer
repo_root = Path("/path/to/your/project")
analyzer = CrossFileAnalyzer(repo_root)

# Build call graph
analyzer.index_repository()
print(f"Indexed {len(analyzer._functions_by_name)} functions")

# Check findings (assuming you have some)
from securecli.schemas.findings import Finding

findings = [...]  # Your findings

# Enrich with traces
analyzer.enrich_findings(findings)

# View traces
for finding in findings:
    if finding.cross_file:
        print(f"\n{finding.title}")
        print(f"  Cross-file traces: {len(finding.cross_file)}")
        for trace in finding.cross_file:
            print(f"    → {trace}")
```

## Method 4: Check Statistics

### View Summary Statistics

After running a scan or generating a report, check the statistics section:

```
╭─────────────────────────────────────────╮
│        Security Analysis Summary         │
╰─────────────────────────────────────────╯

Total Findings:        12
Critical Issues:        3
High Severity:          5
Cross-File Issues:      7    ← Look for this!

Files Analyzed:        45
Tools Used:             3
```

## Method 5: Live Test with Example Code

### Create Test Repository

```bash
mkdir test-cross-file
cd test-cross-file

# Create multi-file app
cat > app.py << 'EOF'
def handle_upload(file_data):
    result = validate_file(file_data)
    return save_upload(result)
EOF

cat > validator.py << 'EOF'
def validate_file(file_data):
    return check_file_type(file_data)
EOF

cat > storage.py << 'EOF'
def check_file_type(file_data):
    return store_file(file_data)

def store_file(file_data):
    return True
EOF
```

### Run Analysis

```bash
securecli scan deep .
```

### Expected Output

You should see traces connecting:
- `app.py:handle_upload` →
- `validator.py:validate_file` →
- `storage.py:check_file_type`

## Verification Checklist

Use this checklist to confirm cross-file analysis is working:

- [ ] Console shows "Enriching findings with cross-file call graph traces"
- [ ] Console shows "Added cross-file traces to X findings"
- [ ] Detailed finding view shows "Cross-File Execution Traces" section
- [ ] Traces use arrow notation (`→` or `->`)
- [ ] Traces span multiple files
- [ ] Markdown report includes `<details>` section for traces
- [ ] JSON report includes `cross_file` arrays
- [ ] Statistics show `cross_file_issues` count

## Troubleshooting

### "No cross-file traces" in Output

**Possible Causes:**
1. **Python-only**: Cross-file analysis currently only works for Python
2. **Self-contained code**: Functions don't call across files
3. **Syntax errors**: Some files have parsing errors (check logs)
4. **Leaf functions**: Vulnerability is in a function that doesn't call others

**Solutions:**
- Check your project is Python
- Look at `cross_file_issues` count in statistics
- Review logs for parsing errors
- Try with a known-good test case

### Traces Don't Show All Layers

**Possible Causes:**
1. **Depth limit**: Traces limited to 6 hops
2. **Trace limit**: Max 10 traces per finding
3. **Name matching**: Function names don't match exactly

**Solutions:**
- Most important traces are shown first
- Check full JSON report for all traces
- Review function naming conventions

### Can't See Traces in CLI

**Solution:**
Make sure you're using `scan deep` not just `scan`:
```
SecureCLI> scan deep /path/to/project
```

The `deep` mode shows full details including traces.

## Advanced: Filtering Cross-File Findings

### Show Only Cross-File Issues

In Python script:
```python
cross_file_findings = [f for f in findings if f.cross_file]
print(f"Found {len(cross_file_findings)} cross-file vulnerabilities")
```

### Export Cross-File Issues Only

```bash
# Generate report with all findings
securecli report . --format json -o full-report.json

# Filter cross-file issues with jq
jq '.findings[] | select(.cross_file | length > 0)' full-report.json
```

## Interactive Commands Summary

| Command | Purpose | Shows Traces? |
|---------|---------|---------------|
| `scan /path` | Quick scan | No (summary only) |
| `scan deep /path` | Deep scan | **Yes** (full details) |
| `report /path` | Generate report | **Yes** (in report file) |
| `analyze` | AI analysis | **Yes** (AI + traces) |
| `help scan` | Command help | N/A |

## Example Session

Here's a complete example session:

```
$ securecli

   ____                           __________    ____
  / __/___  _______  __________  / ____/ / /   /  _/
  \__ \/ _ \/ ___/ / / / ___/ _ \/ /   / / /    / /  
 ___/ /  __/ /__/ /_/ / /  /  __/ /___/ /____/ /   
/____/\___/\___/\__,_/_/   \___/\____/_____/___/   

Security Analysis CLI - AI-Powered Code Security

SecureCLI> scan deep examples/vulnerable-webapp/backend

[*] Scanning target: examples/vulnerable-webapp/backend
[*] Detected languages: Python
[*] Running security tools: bandit, semgrep
[*] Enriching findings with cross-file call graph traces
[*] Added cross-file traces to 3 findings

╭─────────────────────────────────────────────────────────────╮
│         Finding #1 - Critical Severity                       │
╰─────────────────────────────────────────────────────────────╯

SQL Injection in User Authentication

File: app.py:23
Tool: Bandit
CVSS Score: 9.8
Confidence: 95%

Description:
Direct string formatting of SQL query with user input

Impact:
Complete database compromise possible

Cross-File Execution Traces (2 paths):
1. `app.py:login → app.py:authenticate_user`
2. `app.py:profile → app.py:get_user_data → app.py:authenticate_user`

Recommendation:
Use parameterized queries with SQLAlchemy or similar ORM

SecureCLI> report . --format markdown -o security-report.md

[*] Generating markdown report
[*] Report saved to: security-report.md

SecureCLI> exit
```

## Key Takeaways

1. **Use `scan deep`** to see full finding details with traces
2. **Check console output** for enrichment confirmation
3. **Generate reports** for persistent documentation
4. **Look for arrow symbols** (`→` or `->`) in traces
5. **Cross-file traces work automatically** - no configuration needed

## Next Steps

- Try the example code provided above
- Run `scan deep` on your own projects
- Generate markdown reports to share with team
- Check the `cross_file_issues` statistic in summaries
- Explore JSON reports for programmatic access

---

**Need Help?**
- See `securecli --help`
- Check `docs/CROSS_FILE_ANALYSIS.md` for technical details
- Review `examples/test_cross_file.py` for code examples
