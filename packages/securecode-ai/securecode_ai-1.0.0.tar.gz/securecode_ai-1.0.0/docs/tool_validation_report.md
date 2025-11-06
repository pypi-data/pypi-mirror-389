
# SecureCLI Tool Validation Report

## Summary
- Total tools checked: 24
- Tools installed: 13
- Tools functional: 7
- Success rate: 29.2%

## Tool Status

### ✅ Fully Functional Tools
- **Semgrep**: 1.136.0
- **CppCheck**: Cppcheck 2.13.0
- **Brakeman**: brakeman 7.1.0
- **.NET CLI**: 8.0.119
- **Solidity Compiler**: solc, the solidity compiler commandline interface
Version: 0.8.30+commit.73712a01.Linux.g++
- **npm audit**: 9.2.0
- **ESLint**: v9.35.0

### ⚠️ Installed but Non-Functional Tools
- **Bandit**: bandit 1.8.6
  python version = 3.13.5 | packaged by Anaconda, Inc. | (main, Jun 12 2025, 16:09:02)  - [main]	INFO	profile include tests: None
[main]	INFO	profile exclude tests: None
[main]	INFO	cli include tests: None
[main]	INFO	cli exclude tests: None
[main]	INFO	running on Python 3.13.5

- **RuboCop**: 1.80.2 - The following cops were added to RuboCop, but are not configured. Please set Enabled to either `true` or `false` in your `.rubocop.yml` file.

Please also note that you can opt-in to new cops by defau
- **Slither**: 0.11.3 - 'solc --version' running
'solc VulnerableApp.sol --combined-json abi,ast,bin,bin-runtime,srcmap,srcmap-runtime,userdoc,devdoc,hashes --allow-paths .,/tmp/securecli_validation_o72av87h' running
Compila
- **Vyper**: 0.4.3+commit.bff19ea2 - vyper.exceptions.VersionException: Version specification "~=0.3.0" is not compatible with compiler version "0.4.3"

  contract "lib.vy:2", line 2:0 
       1
  ---> 2 # @version ^0.3.0
  -------^
    
- **Gitleaks**: 8.18.4 - 
    ○
    │╲
    │ ○
    ○ ░
    ░    gitleaks

[90m11:37AM[0m [32mINF[0m scan completed in 1.86ms
[90m11:37AM[0m [31mWRN[0m leaks found: 1

- **npm audit (functionality)**: npm 9.2.0 - npm ERR! code ENOLOCK
npm ERR! audit This command requires an existing lockfile.
npm ERR! audit Try creating one first with: npm i --package-lock-only
npm ERR! audit Original error: loadVirtual requir

### ❌ Missing Tools
- **Safety**: Command not found: safety
- **Clang Static Analyzer**: Command not found: clang-tidy
- **Clippy**: Command not found: cargo
- **Cargo Audit**: Command not found: cargo
- **SpotBugs**: [Errno 13] Permission denied: 'spotbugs'
- **PMD**: Error: Could not find or load main class 
Caused by: java.lang.ClassNotFoundException: 

- **bundler-audit**: Command not found: bundle
- **Gosec**: Command not found: gosec
- **Staticcheck**: Command not found: staticcheck
- **Go-critic**: Command not found: gocritic
- **DevSkim**: Command not found: devskim


## Installation Instructions

### For missing tools, run the appropriate installation script:

**Linux/WSL:**
```bash
./scripts/install-security-tools.sh
```

**Windows PowerShell (as Administrator):**
```powershell
.\scripts\install-security-tools.ps1
```

### Manual installation commands:

**Python tools:**
```bash
pip install bandit semgrep safety pip-audit
```

**Rust tools:**
```bash
rustup component add clippy
cargo install cargo-audit
```

**Ruby tools:**
```bash
gem install brakeman rubocop rubocop-security bundler-audit
```

**Go tools:**
```bash
go install github.com/securecodewarrior/gosec/v2/cmd/gosec@latest
go install honnef.co/go/tools/cmd/staticcheck@latest
go install github.com/go-critic/go-critic/cmd/gocritic@latest
```

**.NET tools:**
```bash
dotnet tool install --global Microsoft.CST.DevSkim.CLI
```

**Node.js tools:**
```bash
npm install -g eslint @microsoft/eslint-plugin-security retire audit-ci
```

## Testing SecureCLI

After installing missing tools, test SecureCLI:

```bash
# Test basic functionality
python -m securecli scan --help

# Test with sample vulnerable code
python -m securecli scan /tmp/securecli_validation_o72av87h

# Test specific language
python -m securecli scan /tmp/securecli_validation_o72av87h --language python
```

## Notes

- Some tools may require additional setup (e.g., cargo projects for Rust tools)
- Tools marked as "non-functional" may still work in their intended context
- Ensure all tools are in your system PATH
- Some tools may require specific project structures to function properly

Validation completed at: /mnt/c/Users/Stephen/Documents/SecureCLI
Temporary test files created in: /tmp/securecli_validation_o72av87h
