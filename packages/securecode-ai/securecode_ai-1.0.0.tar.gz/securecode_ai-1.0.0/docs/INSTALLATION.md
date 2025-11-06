# SecureCLI Multi-Language Security Analysis Setup

This guide covers the complete installation and setup of SecureCLI with comprehensive multi-language security analysis capabilities.

## 📋 Supported Languages & Tools

SecureCLI supports security analysis for the following programming languages with their respective tools:

### 🐍 Python
- **Bandit** - Security linter for Python code
- **Semgrep** - Static analysis with customizable rules
- **Safety** - Checks dependencies for known vulnerabilities
- **pip-audit** - Audits Python packages for vulnerabilities

### ⚡ C/C++
- **Clang Static Analyzer** - Advanced static analysis from LLVM
- **CppCheck** - Static analysis for C/C++ code

### 🦀 Rust
- **Clippy** - Rust's built-in linter with security checks
- **Cargo Audit** - Checks Rust dependencies for vulnerabilities

### ☕ Java
- **SpotBugs** - Static analysis for Java bytecode
- **PMD** - Source code analyzer for Java
- **Find Security Bugs** - Security-focused SpotBugs plugin

### 💎 Ruby
- **Brakeman** - Static analysis for Ruby on Rails
- **RuboCop Security** - Security-focused Ruby linting
- **bundler-audit** - Checks Ruby gems for vulnerabilities

### 🐹 Go
- **Gosec** - Security-focused static analyzer for Go
- **Staticcheck** - Advanced Go static analyzer
- **Go-critic** - Comprehensive Go linter

### 🔷 C#/.NET
- **DevSkim** - Microsoft's security linter
- **Roslyn Analyzers** - .NET compiler-based analysis
- **.NET CLI** - Built-in security analysis

### 🌐 JavaScript/TypeScript
- **npm audit** - Node.js dependency vulnerability scanner
- **ESLint Security** - Security-focused JavaScript linting
- **Retire.js** - Scanner for vulnerable JavaScript libraries

### 🔧 Universal Tools
- **Gitleaks** - Detects secrets in git repositories
- **Semgrep** - Multi-language static analysis platform

## 🚀 Quick Installation

### Option 1: Automated Installation (Recommended)

#### For Linux/WSL:
```bash
# Make script executable
chmod +x scripts/install-security-tools.sh

# Run installation script
./scripts/install-security-tools.sh
```

#### For Windows PowerShell (Run as Administrator):
```powershell
# Set execution policy (if needed)
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser

# Run installation script
.\scripts\install-security-tools.ps1
```

### Option 2: Manual Installation

#### 1. Install System Dependencies

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install -y curl wget git build-essential cmake ninja-build \
    python3-pip default-jdk maven gradle ruby ruby-dev nodejs npm \
    dotnet-sdk-8.0 clang clang-tools cppcheck
```

**Windows (via Chocolatey):**
```powershell
# Install Chocolatey first if not installed
Set-ExecutionPolicy Bypass -Scope Process -Force; [System.Net.ServicePointManager]::SecurityProtocol = [System.Net.ServicePointManager]::SecurityProtocol -bor 3072; iex ((New-Object System.Net.WebClient).DownloadString('https://community.chocolatey.org/install.ps1'))

# Install tools
choco install git cmake ninja python3 openjdk maven gradle ruby nodejs dotnet-sdk llvm cppcheck -y
```

#### 2. Install Language-Specific Tools

**Python Tools:**
```bash
pip install bandit semgrep safety pip-audit cyclonedx-python
```

**Rust Tools:**
```bash
# Install Rust if not installed
curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh
source ~/.cargo/env

# Install Rust security tools
rustup component add clippy
cargo install cargo-audit
```

**Java Tools:**
```bash
# SpotBugs
wget https://github.com/spotbugs/spotbugs/releases/download/4.8.1/spotbugs-4.8.1.tgz
tar -xzf spotbugs-4.8.1.tgz
sudo mv spotbugs-4.8.1 /opt/spotbugs
sudo ln -s /opt/spotbugs/bin/spotbugs /usr/local/bin/

# PMD
wget https://github.com/pmd/pmd/releases/download/pmd_releases%2F6.55.0/pmd-bin-6.55.0.zip
unzip pmd-bin-6.55.0.zip
sudo mv pmd-bin-6.55.0 /opt/pmd
sudo ln -s /opt/pmd/bin/run.sh /usr/local/bin/pmd

# Find Security Bugs plugin
sudo wget -P /opt/spotbugs/plugin \
    https://github.com/find-sec-bugs/find-sec-bugs/releases/download/version-1.12.0/findsecbugs-plugin-1.12.0.jar
```

**Ruby Tools:**
```bash
gem install brakeman rubocop rubocop-security bundler-audit
```

**Go Tools:**
```bash
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
go install honnef.co/go/tools/cmd/staticcheck@latest
go install github.com/go-critic/go-critic/cmd/gocritic@latest
```

**.NET Tools:**
```bash
dotnet tool install --global Microsoft.CST.DevSkim.CLI
```

**Node.js Tools:**
```bash
npm install -g eslint @microsoft/eslint-plugin-security retire audit-ci
```

**Universal Tools:**
```bash
# Gitleaks
wget https://github.com/gitleaks/gitleaks/releases/download/v8.18.0/gitleaks_8.18.0_linux_x64.tar.gz
tar -xzf gitleaks_8.18.0_linux_x64.tar.gz
sudo mv gitleaks /usr/local/bin/
```

## 🔧 Installation Verification

After installation, verify all tools are working:

```bash
# Run the validation script
python scripts/validate-tools.py
```

This will:
- Check if all tools are installed and accessible
- Test functionality with sample vulnerable code
- Generate a detailed validation report
- Provide specific installation instructions for missing tools

## 📦 Python Dependencies

### Core Dependencies (pyproject.toml)
The main dependencies are managed in `pyproject.toml`:

```toml
[project]
dependencies = [
    "click>=8.1.0",
    "pyyaml>=6.0",
    "pydantic>=2.0.0",
    "rich>=13.0.0",
    "typer>=0.9.0",
    "pathspec>=0.11.0",
    "gitpython>=3.1.30",
    "jinja2>=3.1.0",
    "requests>=2.31.0",
    "aiofiles>=23.0.0",
    "asyncio-mqtt>=0.13.0",
]
```

### Development Dependencies (requirements-dev.txt)
Additional development and security tools:

```bash
# Install development dependencies
pip install -r requirements-dev.txt
```

## 🧪 Testing the Installation

### 1. Basic Functionality Test
```bash
# Check SecureCLI installation
python -m securecli --help

# Test scanning
python -m securecli scan --help
```

### 2. Language-Specific Tests
```bash
# Test Python analysis
echo "exec(input())" > vulnerable.py
python -m securecli scan vulnerable.py

# Test multi-language analysis
python -m securecli scan . --recursive
```

### 3. Comprehensive Test
```bash
# Run full validation
python scripts/validate-tools.py

# Check the generated report
cat tool_validation_report.md
```

## 🔄 Environment Setup

### PATH Configuration

Ensure all tools are in your system PATH:

**Linux/WSL (~/.bashrc):**
```bash
# Rust tools
export PATH="$HOME/.cargo/bin:$PATH"

# Go tools
export PATH="$HOME/go/bin:$PATH"

# .NET tools
export PATH="$HOME/.dotnet/tools:$PATH"

# Java tools (if manually installed)
export PATH="/opt/spotbugs/bin:/opt/pmd/bin:$PATH"
```

**Windows (Environment Variables):**
```powershell
# Add to system PATH via System Properties > Environment Variables
# Or use PowerShell:
$env:PATH += ";$env:USERPROFILE\.cargo\bin"
$env:PATH += ";$env:USERPROFILE\go\bin"
$env:PATH += ";$env:USERPROFILE\.dotnet\tools"
```

### WSL Configuration

For optimal WSL performance:

```bash
# Update WSL
wsl --update

# Ensure WSL 2
wsl --set-version <distro-name> 2

# Configure git (if needed)
git config --global user.name "Your Name"
git config --global user.email "your.email@example.com"
```

## 🐛 Troubleshooting

### Common Issues

#### 1. Tool Not Found in PATH
```bash
# Check if tool is installed
which <tool-name>

# Add to PATH if needed
export PATH="/path/to/tool:$PATH"
```

#### 2. Permission Issues (Linux)
```bash
# Fix permissions for scripts
chmod +x scripts/*.sh

# Install tools with proper permissions
sudo chown -R $USER:$USER ~/.cargo ~/.go
```

#### 3. .NET Tool Issues
```bash
# Clear .NET tool cache
dotnet tool uninstall --global Microsoft.CST.DevSkim.CLI
dotnet tool install --global Microsoft.CST.DevSkim.CLI

# Add .NET tools to PATH
export PATH="$HOME/.dotnet/tools:$PATH"
```

#### 4. Ruby Gem Issues
```bash
# Update RubyGems
gem update --system

# Install with user permissions
gem install --user-install brakeman rubocop
```

#### 5. Node.js Permission Issues
```bash
# Use npm prefix for global installs
npm config set prefix ~/.npm-global
export PATH="$HOME/.npm-global/bin:$PATH"
```

### Tool-Specific Issues

#### SpotBugs Java Version
```bash
# Check Java version (requires Java 8+)
java -version

# Set JAVA_HOME if needed
export JAVA_HOME="/usr/lib/jvm/default-java"
```

#### Rust Clippy Missing
```bash
# Reinstall clippy
rustup component remove clippy
rustup component add clippy
```

#### Go Tools Missing
```bash
# Enable Go modules
export GO111MODULE=on

# Reinstall tools
go clean -modcache
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
```

## 📊 Performance Optimization

### Large Codebase Scanning
```bash
# Use parallel scanning
python -m securecli scan --parallel 4

# Exclude unnecessary files
python -m securecli scan --exclude "node_modules,vendor,*.test"

# Focus on specific languages
python -m securecli scan --language python,javascript
```

### Memory Usage
```bash
# Monitor memory usage
python -m securecli scan --memory-limit 2G

# Use streaming for large files
python -m securecli scan --stream-results
```

## 🔄 Maintenance

### Updating Tools
```bash
# Update Python tools
pip install --upgrade bandit semgrep safety

# Update Rust tools
cargo install --force cargo-audit

# Update Ruby tools
gem update brakeman rubocop

# Update Go tools
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest

# Update .NET tools
dotnet tool update --global Microsoft.CST.DevSkim.CLI

# Update Node.js tools
npm update -g eslint retire
```

### Regular Validation
```bash
# Run weekly validation
python scripts/validate-tools.py > validation_$(date +%Y%m%d).md

# Check for tool updates
python -m securecli check-updates
```

## 📚 Documentation

- [Usage Guide](USAGE.md) - How to use SecureCLI
- [Architecture](ARCHITECTURE.md) - System architecture
- [Contributing](CONTRIBUTING.md) - Development guidelines
- [API Reference](docs/api/) - API documentation

## 🤝 Support

### Getting Help
1. Check the validation report: `python scripts/validate-tools.py`
2. Review tool-specific documentation links in the validation output
3. Check the troubleshooting section above
4. Open an issue with the validation report attached

### Reporting Issues
When reporting issues, please include:
- Operating system and version
- Tool validation report
- Error messages and logs
- Steps to reproduce

## 🎯 Next Steps

After successful installation:

1. **Run validation**: `python scripts/validate-tools.py`
2. **Test basic scanning**: `python -m securecli scan --help`
3. **Scan sample code**: Create vulnerable test files and scan them
4. **Configure CI/CD**: Integrate SecureCLI into your development workflow
5. **Customize rules**: Configure tool-specific security rules
6. **Set up monitoring**: Regular security scanning automation

🎉 **Congratulations!** You now have a comprehensive multi-language security analysis platform ready for production use!