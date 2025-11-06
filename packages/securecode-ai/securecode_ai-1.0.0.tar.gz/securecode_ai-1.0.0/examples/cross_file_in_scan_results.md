# Cross-File Analysis in Scan Results

## Summary

Yes, **cross-file traces now appear in scan findings automatically**! Here's how they're displayed:

## 1. Summary Statistics (Top of Scan Results)

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃                    Security Assessment                         ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ Security Scan Results                                          ┃
┃                                                                ┃
┃ Total Issues: 8                                                ┃
┃ Risk Level: Elevated                                           ┃
┃ Target: /path/to/project                                       ┃
┃ Mode: Deep                                                     ┃
┃ Cross-File Traces: 5 findings with execution path analysis    ┃  ← NEW!
┃                                                                ┃
┃ Issues by Severity:                                            ┃
┃   - Critical: 1                                                ┃
┃   - High: 2                                                    ┃
┃   - Medium: 3                                                  ┃
┃   - Low: 2                                                     ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## 2. Critical & High Severity Findings (Detailed View)

All Critical and High severity findings **automatically show full cross-file traces**:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃           Critical and High Severity Issues                    ┃
┃           (immediate attention required)                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛

┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ 🔴 Finding #1: SQL Injection (Critical)                        ┃
┣━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┫
┃ File: backend/database.py:145                                  ┃
┃ Tool: Bandit                                                   ┃
┃ CWE: CWE-89                                                    ┃
┃ CVSS: 9.8 (Critical)                                           ┃
┃                                                                ┃
┃ Description:                                                   ┃
┃ User input is passed to SQL query without sanitization        ┃
┃                                                                ┃
┃ Cross-File Execution Traces (3 paths):                         ┃  ← DETAILED!
┃   1. frontend/api.js:getUserData                               ┃
┃      → backend/routes.py:handle_user_request                   ┃
┃      → backend/service.py:fetch_user                           ┃
┃      → backend/database.py:execute_query  [VULNERABLE]         ┃
┃                                                                ┃
┃   2. admin/dashboard.py:load_user_profile                      ┃
┃      → backend/service.py:get_profile                          ┃
┃      → backend/database.py:execute_query  [VULNERABLE]         ┃
┃                                                                ┃
┃   3. api/external.py:third_party_webhook                       ┃
┃      → backend/handlers.py:process_webhook                     ┃
┃      → backend/database.py:execute_query  [VULNERABLE]         ┃
┃                                                                ┃
┃ Remediation:                                                   ┃
┃ Use parameterized queries or ORM methods                       ┃
┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛
```

## 3. Medium & Low Findings (Table with Cross-File Indicator)

Medium and Low severity findings show in a table with a **X-File column** indicating trace count:

```
┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃            Additional Security Issues (5 issues)                        ┃
┣━━━━━━━━┳━━━━━━━━━━━━┳━━━━━━━━━━┳━━━━━━━━━━━━━━━━━━┳━━━━━━━━━━━━━┳━━━━━━┳━━━━━━━━┫
┃ ID     ┃ Tool       ┃ Severity ┃ File             ┃ Issue       ┃ CVSS ┃ X-File ┃
┣━━━━━━━━╋━━━━━━━━━━━━╋━━━━━━━━━━╋━━━━━━━━━━━━━━━━━━╋━━━━━━━━━━━━━╋━━━━━━╋━━━━━━━━┫
┃ F003   ┃ Bandit     ┃ Medium   ┃ utils/helper.py  ┃ Hardcoded   ┃ 5.3  ┃ 2 →    ┃  ← HAS TRACES
┃ F004   ┃ Semgrep    ┃ Medium   ┃ auth/login.py    ┃ Weak hash   ┃ 6.1  ┃ 4 →    ┃  ← HAS TRACES
┃ F005   ┃ Bandit     ┃ Low      ┃ config/load.py   ┃ Insecure    ┃ 3.7  ┃        ┃  ← NO TRACES
┃ F006   ┃ Npm Audit  ┃ Medium   ┃ package.json     ┃ Vuln dep    ┃ N/A  ┃        ┃  ← NO TRACES
┃ F007   ┃ Bandit     ┃ Low      ┃ tests/test.py    ┃ Assert used ┃ 2.1  ┃ 1 →    ┃  ← HAS TRACES
┗━━━━━━━━┻━━━━━━━━━━━━┻━━━━━━━━━━┻━━━━━━━━━━━━━━━━━━┻━━━━━━━━━━━━━┻━━━━━━┻━━━━━━━━┛

ℹ 3 findings have cross-file execution traces. Use 'scan deep' to view details.
```

The **X-File column** shows:
- **Empty**: No cross-file traces found
- **`2 →`**: Finding has 2 execution traces through other files
- **`4 →`**: Finding has 4 execution traces

## 4. How to See Full Details for Medium/Low Findings

To see the **complete cross-file traces** for Medium/Low findings:

### Option 1: Deep Scan Mode
```bash
scan deep <target>
```
This shows all findings (including Medium/Low) with full cross-file trace details.

### Option 2: Generate a Report
```bash
set output.format markdown
scan <target>
```
The markdown report includes complete cross-file traces for all severity levels.

### Option 3: Export to JSON
```bash
set output.format json
scan <target>
```
JSON export contains full `cross_file` arrays for all findings.

### Option 4: Interactive Analysis
```bash
analyze
```
AI-powered analysis includes cross-file context for all findings.

## 5. What Gets Traced

The cross-file analyzer traces:
- **Function calls** across files
- **Import chains** and dependencies
- **Execution paths** from entry points (UI, API, webhooks)
- **Data flow** through multiple layers (UI → API → Service → Database)

**Example trace chain:**
```
UI Button Click (frontend/app.js:handleSubmit)
  → API Request (api/routes.py:create_user)
    → Business Logic (services/user.py:register)
      → Database Call (models/user.py:insert)  [VULNERABLE]
        → External API (integrations/email.py:send_verification)
```

## 6. Key Features

✅ **Automatic**: Cross-file analysis runs during every scan  
✅ **No configuration needed**: Works out of the box for Python projects  
✅ **Multi-language**: Expandable to JavaScript, Go, Java, etc.  
✅ **Performance**: Lightweight AST parsing, no runtime overhead  
✅ **Detailed**: Shows up to 6 hops in call chain  
✅ **Actionable**: Helps identify attack surface and impact radius  

## 7. Example Output Summary

After running `scan .`:

```
Security Scan Results

Total Issues: 8
Risk Level: Elevated
Target: /home/user/project
Mode: Standard
Cross-File Traces: 5 findings with execution path analysis  ← YOU SEE THIS

Issues by Severity:
  - Critical: 1  (shows full traces)
  - High: 2      (shows full traces)
  - Medium: 3    (table shows "3 →" indicator)
  - Low: 2       (table shows "1 →" indicator)
```

**Bottom line**: Yes, cross-file traces are visible in scan results! Critical/High findings show full details automatically, while Medium/Low findings show an indicator. Use `scan deep` or reports for complete trace details.
