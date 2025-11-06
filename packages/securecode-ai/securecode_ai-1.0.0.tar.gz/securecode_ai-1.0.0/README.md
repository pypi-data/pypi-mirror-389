# SecureCLI - Comprehensive Multi-Language Security Analysis Platform

<p align="center">
  <img src="https://img.shields.io/badge/security-analysis-blue.svg" alt="Security Analysis" />
  <img src="https://img.shields.io/badge/languages-10%2B-green.svg" alt="Languages" />
  <img src="https://img.shields.io/badge/tools-20%2B-orange.svg" alt="Tools" />
  <img src="https://img.shields.io/badge/license-MIT-blue.svg" alt="License" />
</p>

<p align="center">
  <strong>Enterprise-grade security analysis for modern development teams</strong><br>
  Supporting 10+ programming languages with 20+ integrated security tools
</p>

## 🛡️ Overview

SecureCLI is a comprehensive security analysis platform that provides unified security scanning across multiple programming languages and frameworks. Built for modern development workflows, it integrates seamlessly with CI/CD pipelines and provides actionable security insights.

### 🌟 Key Features

- **🌍 Multi-Language Support**: Python, JavaScript/TypeScript, Java, C/C++, Rust, Ruby, Go, C#/.NET, Solidity, Vyper
- **🔧 20+ Security Tools**: Bandit, Semgrep, ESLint, SpotBugs, Gosec, Slither, DevSkim, and more
- **🔗 Smart Contract Security**: Specialized analysis for Ethereum, Vyper, and EVM-compatible contracts
- **📊 Multiple Output Formats**: JSON, Markdown, CSV, HTML reports
- **⚡ Fast & Scalable**: Parallel processing and intelligent caching
- **🔄 CI/CD Integration**: GitHub Actions, GitLab CI, Jenkins ready
- **📈 Enterprise Features**: CVSS scoring, vulnerability tracking, compliance reporting

## 🚀 Quick Start

### Installation

```bash
# Install SecureCLI
pip install securecli

# Install security analysis tools
./scripts/install-security-tools.sh  # Linux/WSL
# OR
.\scripts\install-security-tools.ps1  # Windows PowerShell (as admin)

# Verify installation
python scripts/validate-tools.py
```

### Basic Usage

```bash
# Scan current directory
securecli scan .

# Scan specific file
securecli scan app.py

# Generate JSON report
securecli scan . --format json --output security-report.json

# High-severity findings only
securecli scan . --severity-min HIGH

# Verbose output
securecli scan . --verbose
```

### Example Output

```
🔍 SecureCLI Security Analysis Report

📁 Scanned: ./my-project (42 files)
🕒 Duration: 23.4s
🔧 Tools: bandit, semgrep, gosec, eslint, slither

📊 Summary:
  🔴 Critical: 2
  🟠 High:     5
  🟡 Medium:   8
  🟢 Low:      3

🔴 Critical Issues:
  SQL Injection in user_auth.py:45
  Hardcoded Secret in config.js:12

🟠 High Issues:
  Command Injection in file_handler.py:78
  Reentrancy Vulnerability in Token.sol:134
  ...

💡 Run with --verbose for detailed recommendations
```

## 📋 Supported Languages & Tools

| Language | Extensions | Primary Tools | Additional Tools |
|----------|------------|---------------|------------------|
| **Python** | `.py` | Bandit, Semgrep | Safety, pip-audit |
| **JavaScript/TypeScript** | `.js`, `.ts`, `.jsx`, `.tsx` | ESLint Security, Semgrep | npm audit, retire.js |
| **Java** | `.java`, `.jsp` | SpotBugs, PMD | Find Security Bugs |
| **C/C++** | `.c`, `.cpp`, `.h`, `.hpp` | Clang Static Analyzer | CppCheck |
| **Rust** | `.rs`, `.toml` | Clippy, Cargo Audit | RustSec Advisory |
| **Ruby** | `.rb` | Brakeman, RuboCop Security | bundler-audit |
| **Go** | `.go` | Gosec, Staticcheck | go-critic |
| **C#/.NET** | `.cs`, `.razor` | DevSkim, Roslyn Analyzers | Security Code Scan |
| **Solidity** | `.sol` | Slither, solc | Pattern-based analysis |
| **Vyper** | `.vy` | Vyper compiler | Pattern-based analysis |

## 🔧 Installation Guide

### Automated Installation (Recommended)

#### Linux/WSL
```bash
git clone <repository-url>
cd SecureCLI
chmod +x scripts/install-security-tools.sh
./scripts/install-security-tools.sh
```

#### Windows PowerShell (Run as Administrator)
```powershell
git clone <repository-url>
cd SecureCLI
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\install-security-tools.ps1
```

### Manual Installation

#### Python Dependencies
```bash
pip install -r requirements-dev.txt
```

#### Language-Specific Tools
```bash
# Rust tools
rustup component add clippy
cargo install cargo-audit

# Ruby tools
gem install brakeman rubocop rubocop-security bundler-audit

# Go tools
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
go install honnef.co/go/tools/cmd/staticcheck@latest

# .NET tools
dotnet tool install --global Microsoft.CST.DevSkim.CLI

# Smart contract tools
npm install -g solc
pip install slither-analyzer vyper
```

### Verification
```bash
# Run comprehensive test
python scripts/comprehensive-test.py

# Validate specific tools
python scripts/validate-tools.py
```

## 🌍 Language-Specific Examples

### Python Security Analysis
```bash
# Basic Python scan
securecli scan app.py

# Django project scan
securecli scan . --include="*.py" --exclude="venv,migrations"

# Focus on high-severity issues
securecli scan . --language python --severity-min HIGH
```

### Smart Contract Security
```bash
# Solidity contract analysis
securecli scan contracts/ --include="*.sol"

# Vyper contract analysis  
securecli scan contracts/ --include="*.vy"

# Comprehensive DeFi audit
securecli scan . --include="*.sol,*.vy" --format json --output defi-audit.json
```

### Web Application Security
```bash
# Full-stack JavaScript application
securecli scan . --include="*.js,*.ts,*.jsx,*.tsx"

# Backend API security
securecli scan backend/ --language java,python

# Frontend security scan
securecli scan frontend/ --language javascript --tools eslint,semgrep
```

## ⚙️ Configuration

### Configuration File
Create `securecli.yml`:

```yaml
# SecureCLI Configuration
project:
  name: "My Project"
  version: "1.0.0"

scanning:
  parallel_jobs: 4
  timeout: 300
  exclude_paths:
    - "node_modules/"
    - "venv/"
    - "target/"
    - "*.test.*"

tools:
  bandit:
    enabled: true
    config_file: ".bandit"
  
  semgrep:
    enabled: true
    rules: ["auto", "security", "secrets"]
  
  slither:
    enabled: true
    detectors: ["all"]
    exclude_detectors: ["solc-version"]

  gosec:
    enabled: true
    include_tests: false

reporting:
  format: "json"
  output_file: "security-report.json"
  include_code_snippets: true
  severity_filter: "MEDIUM"
  
  cvss:
    enabled: true
    version: "4.0"
  
  compliance:
    standards: ["OWASP", "CWE", "NIST"]
```

### Tool-Specific Configuration

#### Bandit (Python)
`.bandit`:
```ini
[bandit]
exclude = /tests/,/venv/
skips = B101,B601
```

#### ESLint (JavaScript)
`.eslintrc.js`:
```javascript
module.exports = {
  extends: ['@microsoft/eslint-plugin-security'],
  rules: {
    'security/detect-object-injection': 'error',
    'security/detect-non-literal-fs-filename': 'warn'
  }
};
```

## 📊 Reporting & Output Formats

### JSON Report
```json
{
  "summary": {
    "scan_id": "scan_20240101_120000",
    "timestamp": "2024-01-01T12:00:00Z",
    "duration": 23.4,
    "files_scanned": 42,
    "tools_used": ["bandit", "semgrep", "gosec"],
    "findings_count": {
      "critical": 2,
      "high": 5,
      "medium": 8,
      "low": 3
    }
  },
  "findings": [
    {
      "id": "FINDING_001",
      "tool": "bandit",
      "rule_id": "B602",
      "title": "Use of subprocess with shell=True",
      "severity": "HIGH",
      "confidence": "HIGH",
      "file_path": "app/utils.py",
      "line_number": 45,
      "column_number": 12,
      "code_snippet": "subprocess.call(cmd, shell=True)",
      "description": "Use of subprocess with shell=True can lead to command injection",
      "cwe_id": "CWE-78",
      "cvss_score": 8.1,
      "recommendation": "Use subprocess without shell=True or validate input"
    }
  ]
}
```

### Markdown Report
```markdown
# Security Analysis Report

## Summary
- **Scan ID**: scan_20240101_120000
- **Files Scanned**: 42
- **Duration**: 23.4s
- **Critical**: 2 🔴
- **High**: 5 🟠

## Critical Findings

### Command Injection in app/utils.py
- **Line**: 45
- **Tool**: bandit
- **CVSS**: 8.1
- **CWE**: CWE-78

```python
subprocess.call(cmd, shell=True)  # ❌ Vulnerable
```

**Recommendation**: Use `subprocess` without `shell=True`
```

### CSV Export
```csv
ID,Tool,Rule,Severity,File,Line,Description,CWE,CVSS
FINDING_001,bandit,B602,HIGH,app/utils.py,45,Command injection,CWE-78,8.1
FINDING_002,semgrep,javascript.express.security.audit.express-session-secret.express-session-secret,MEDIUM,server.js,23,Hardcoded session secret,CWE-798,6.5
```

## 🔄 CI/CD Integration

### GitHub Actions
```yaml
name: Security Analysis
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      
      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install SecureCLI
        run: |
          pip install securecli
          ./scripts/install-security-tools.sh
      
      - name: Security Scan
        run: |
          securecli scan . --format json --output security-report.json
          
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: security-report.json
          
      - name: Comment PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            // Add security results to PR comment
```

### GitLab CI
```yaml
security_scan:
  stage: test
  image: python:3.11
  before_script:
    - pip install securecli
    - ./scripts/install-security-tools.sh
  script:
    - securecli scan . --format json --output security-report.json
  artifacts:
    reports:
      junit: security-report.json
    paths:
      - security-report.json
  rules:
    - if: $CI_PIPELINE_SOURCE == "merge_request_event"
    - if: $CI_COMMIT_BRANCH == $CI_DEFAULT_BRANCH
```

### Jenkins Pipeline
```groovy
pipeline {
    agent any
    
    stages {
        stage('Security Analysis') {
            steps {
                sh 'pip install securecli'
                sh './scripts/install-security-tools.sh'
                sh 'securecli scan . --format json --output security-report.json'
                
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: '.',
                    reportFiles: 'security-report.json',
                    reportName: 'Security Report'
                ])
            }
        }
    }
}
```

## 🧪 Testing & Validation

### Comprehensive Test Suite
```bash
# Run full test suite
python scripts/comprehensive-test.py

# Test specific languages
securecli scan tests/samples/ --language python,javascript

# Performance benchmarking
securecli scan large-project/ --benchmark --parallel 8
```

### Sample Vulnerable Code
The repository includes sample vulnerable code for testing:

```
tests/samples/
├── python/
│   ├── sql_injection.py
│   ├── command_injection.py
│   └── hardcoded_secrets.py
├── javascript/
│   ├── xss_vulnerability.js
│   └── prototype_pollution.js
├── java/
│   ├── SQLInjection.java
│   └── PathTraversal.java
├── solidity/
│   ├── Reentrancy.sol
│   └── AccessControl.sol
└── ...
```

## 📚 Documentation

- **[Installation Guide](INSTALLATION.md)** - Comprehensive setup instructions
- **[Usage Guide](USAGE.md)** - Detailed usage examples and best practices
- **[Smart Contract Security](docs/SMART_CONTRACT_SECURITY.md)** - Blockchain security analysis
- **[Architecture](ARCHITECTURE.md)** - System design and architecture
- **[API Reference](docs/api/)** - API documentation and integration guides
- **[Contributing](CONTRIBUTING.md)** - Development and contribution guidelines

## 🛡️ Security Features

### Vulnerability Detection
- **Code Injection**: SQL, Command, Code injection detection
- **Cryptographic Issues**: Weak algorithms, hardcoded secrets
- **Authentication Flaws**: Access control bypasses, session issues
- **Smart Contract Vulnerabilities**: Reentrancy, integer overflow, access control
- **Dependency Vulnerabilities**: Known CVEs in dependencies
- **Configuration Issues**: Insecure defaults, misconfigurations

### Compliance Standards
- **OWASP Top 10**: Web application security risks
- **CWE**: Common Weakness Enumeration mapping
- **NIST**: Cybersecurity framework alignment
- **SANS**: Security best practices
- **GDPR**: Data protection compliance checks

### Enterprise Features
- **Role-Based Access**: Team and organizational access controls
- **Custom Rules**: Organization-specific security policies
- **Audit Trails**: Complete security scanning history
- **Integration APIs**: REST APIs for enterprise integration
- **Compliance Reporting**: Automated compliance documentation

## 🤝 Contributing

We welcome contributions from the security community! Ways to contribute:

1. **🐛 Bug Reports**: Report issues and bugs
2. **✨ Feature Requests**: Suggest new features and improvements
3. **🔧 Tool Integration**: Add support for new security tools
4. **🌍 Language Support**: Add new programming language analyzers
5. **📖 Documentation**: Improve documentation and examples
6. **🧪 Testing**: Add test cases and validation scenarios

### Development Setup
```bash
# Clone repository
git clone <repository-url>
cd SecureCLI

# Setup development environment
python -m venv venv
source venv/bin/activate  # Linux/macOS
# venv\Scripts\activate    # Windows

# Install development dependencies
pip install -r requirements-dev.txt
pip install -e .

# Run tests
pytest tests/
python scripts/validate-tools.py
```

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

## 📈 Performance & Scalability

### Performance Optimization
- **Parallel Processing**: Multi-threaded scanning
- **Intelligent Caching**: Results caching for faster re-scans
- **Incremental Analysis**: Scan only changed files
- **Memory Management**: Efficient memory usage for large codebases
- **Network Optimization**: Optimized tool downloads and updates

### Scalability Features
- **Distributed Scanning**: Scale across multiple machines
- **Container Support**: Docker and Kubernetes deployment
- **Cloud Integration**: AWS, Azure, GCP support
- **Database Storage**: PostgreSQL, MySQL result storage
- **Message Queues**: Redis, RabbitMQ for job processing

### Benchmarks
```
Large Enterprise Codebase (100k+ files):
- Scan Time: ~45 minutes
- Memory Usage: ~2GB peak
- CPU Cores: 8 (parallel processing)
- Findings: ~1,200 security issues identified
```

## 🔗 Integrations

### IDEs & Editors
- **VS Code**: SecureCLI extension for real-time analysis
- **IntelliJ IDEA**: Plugin for JetBrains IDEs
- **Vim/Neovim**: Command-line integration
- **Sublime Text**: Package for syntax highlighting

### Security Platforms
- **SIEM Integration**: Splunk, Elastic, IBM QRadar
- **Vulnerability Management**: Qualys, Rapid7, Tenable
- **Code Quality**: SonarQube, CodeClimate integration
- **Bug Tracking**: Jira, GitHub Issues, Azure DevOps

### Development Tools
- **Git Hooks**: Pre-commit and pre-push validation
- **Package Managers**: npm, pip, cargo, maven integration
- **Build Tools**: Gradle, Maven, webpack, rollup
- **Testing Frameworks**: Jest, pytest, JUnit, RSpec

## 🆘 Support & Community

### Getting Help
- **📖 Documentation**: Comprehensive guides and examples
- **🐛 Issues**: GitHub Issues for bug reports and feature requests
- **💬 Discussions**: Community discussions and Q&A
- **📧 Email**: Direct support for enterprise customers

### Community Resources
- **🎓 Tutorials**: Step-by-step security analysis guides
- **📝 Blog Posts**: Security insights and best practices
- **🎥 Videos**: Demonstration videos and tutorials
- **📊 Case Studies**: Real-world security analysis examples

### Professional Services
- **🏢 Enterprise Support**: 24/7 support for enterprise customers
- **🎯 Custom Training**: Security analysis training programs
- **🔧 Custom Development**: Tailored security solutions
- **📋 Security Consulting**: Expert security assessment services

## 📜 License

SecureCLI is released under the **MIT License**. See [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

SecureCLI integrates with many excellent open-source security tools:

- **[Bandit](https://github.com/PyCQA/bandit)** - Python security linter
- **[Semgrep](https://github.com/returntocorp/semgrep)** - Static analysis engine
- **[Slither](https://github.com/crytic/slither)** - Solidity static analyzer
- **[Gosec](https://github.com/securecodewarrior/gosec)** - Go security analyzer
- **[ESLint Security](https://github.com/eslint-community/eslint-plugin-security)** - JavaScript security rules
- **[SpotBugs](https://github.com/spotbugs/spotbugs)** - Java static analyzer
- **[Brakeman](https://github.com/presidentbeef/brakeman)** - Ruby on Rails security scanner

Special thanks to all contributors and the security research community for making secure software development accessible to everyone.

---

<p align="center">
  <strong>🛡️ Secure your code. Protect your users. Build with confidence.</strong>
</p>