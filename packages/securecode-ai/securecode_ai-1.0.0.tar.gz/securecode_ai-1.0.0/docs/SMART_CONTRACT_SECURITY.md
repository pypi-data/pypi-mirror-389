# Smart Contract Security Analysis with SecureCLI

SecureCLI provides comprehensive security analysis for smart contracts across multiple blockchain platforms and programming languages.

## 🔗 Supported Smart Contract Languages

### Solidity (Ethereum & EVM-Compatible Chains)
**File Extensions:** `.sol`

**Analysis Tools:**
- **Slither** - Advanced static analysis framework by Trail of Bits
- **Solidity Compiler (solc)** - Built-in compiler warnings and errors
- **Pattern-based Analysis** - Custom security pattern detection

**Key Security Checks:**
- Reentrancy vulnerabilities
- Integer overflow/underflow (pre-0.8.0)
- Unchecked low-level calls (`call`, `delegatecall`, `send`)
- Weak randomness using block properties
- `tx.origin` usage for authorization
- Missing access controls
- Uninitialized storage pointers
- Deprecated function usage
- Gas-related vulnerabilities
- Timestamp dependence

### Vyper (Ethereum & EVM-Compatible Chains)
**File Extensions:** `.vy`

**Analysis Tools:**
- **Vyper Compiler** - Official Vyper compiler with security checks
- **Pattern-based Analysis** - Vyper-specific security patterns

**Key Security Checks:**
- Reentrancy vulnerabilities
- Unchecked external calls
- Integer arithmetic issues
- Weak randomness sources
- Access control bypasses
- Gas limit DoS vulnerabilities
- Front-running susceptibility

## 🔧 Installation

### Prerequisites
- Python 3.8+
- Node.js (for Solidity tools)
- Git

### Quick Installation
```bash
# Install SecureCLI
pip install -e .

# Install smart contract analysis tools
./scripts/install-security-tools.sh  # Linux/WSL
# OR
.\scripts\install-security-tools.ps1  # Windows PowerShell (as admin)
```

### Manual Installation

#### Solidity Tools
```bash
# Install Solidity compiler
npm install -g solc

# Install Slither
pip install slither-analyzer crytic-compile

# Verify installation
solc --version
slither --version
```

#### Vyper Tools
```bash
# Install Vyper compiler
pip install vyper

# Verify installation
vyper --version
```

## 🚀 Usage

### Basic Smart Contract Scanning

```bash
# Scan a single smart contract
securecli scan contract.sol

# Scan all smart contracts in a directory
securecli scan ./contracts/

# Scan specific smart contract languages
securecli scan . --include="*.sol,*.vy"

# Generate detailed report
securecli scan ./contracts/ --format=json --output=security-report.json
```

### Advanced Analysis Options

```bash
# High-severity findings only
securecli scan contract.sol --severity-min HIGH

# Verbose output with detailed explanations
securecli scan contract.sol --verbose

# Custom configuration
securecli scan contract.sol --config=smart-contract-config.yml
```

### Language-Specific Analysis

#### Solidity Analysis
```bash
# Basic Solidity scan
securecli scan Token.sol

# With Slither integration
securecli scan Token.sol --tool=slither

# Pattern-based analysis only
securecli scan Token.sol --tool=solidity_patterns
```

#### Vyper Analysis
```bash
# Basic Vyper scan
securecli scan token.vy

# With compiler validation
securecli scan token.vy --compiler-checks

# Custom severity levels
securecli scan token.vy --config=vyper-config.yml
```

## 📋 Security Patterns Detected

### Critical Vulnerabilities

#### Reentrancy Attacks
**Solidity Example:**
```solidity
function withdraw(uint amount) public {
    require(balances[msg.sender] >= amount);
    (bool success, ) = msg.sender.call{value: amount}("");  // ❌ External call
    balances[msg.sender] -= amount;  // ❌ State change after call
}
```

**SecureCLI Detection:**
- Rule: `solidity_reentrancy_vulnerability`
- Severity: HIGH
- CWE: CWE-841

**Recommended Fix:**
```solidity
function withdraw(uint amount) public nonReentrant {
    require(balances[msg.sender] >= amount);
    balances[msg.sender] -= amount;  // ✅ State change first
    (bool success, ) = msg.sender.call{value: amount}("");
    require(success);
}
```

#### Unchecked External Calls
**Solidity Example:**
```solidity
function transfer(address to, uint amount) public {
    to.call{value: amount}("");  // ❌ Unchecked return value
}
```

**SecureCLI Detection:**
- Rule: `solidity_unchecked_low_level_call`
- Severity: HIGH
- CWE: CWE-252

#### Unsafe Delegatecall
**Solidity Example:**
```solidity
function proxy(address target, bytes calldata data) external {
    target.delegatecall(data);  // ❌ Unsafe delegatecall
}
```

**SecureCLI Detection:**
- Rule: `solidity_unsafe_delegatecall`
- Severity: HIGH
- CWE: CWE-470

### Medium Severity Issues

#### Weak Randomness
**Example:**
```solidity
function randomNumber() public view returns (uint) {
    return uint(keccak256(abi.encodePacked(block.timestamp))) % 100;  // ❌ Predictable
}
```

#### tx.origin Usage
**Example:**
```solidity
function authenticate() public view returns (bool) {
    return tx.origin == owner;  // ❌ Phishing vulnerability
}
```

#### Missing Access Controls
**Example:**
```solidity
function setOwner(address newOwner) public {  // ❌ No access control
    owner = newOwner;
}
```

### Low Severity Issues

#### Floating Pragma
**Example:**
```solidity
pragma solidity ^0.8.0;  // ❌ Floating version
```

#### Hardcoded Gas Limits
**Example:**
```solidity
target.call{gas: 2300}("");  // ❌ Fixed gas limit
```

## ⚙️ Configuration

### Smart Contract Configuration File
Create `smart-contract-config.yml`:

```yaml
tools:
  solidity:
    enabled: true
    use_slither: true
    enabled_patterns:
      - reentrancy_vulnerability
      - unchecked_low_level_call
      - unsafe_delegatecall
      - weak_randomness
      - tx_origin_usage
      - missing_access_control
    severity_override:
      floating_pragma: LOW
      hardcoded_gas_limit: MEDIUM
    compiler_checks: true
  
  vyper:
    enabled: true
    enabled_patterns:
      - reentrancy_vulnerability
      - unchecked_send
      - unsafe_raw_call
      - weak_randomness
    compiler_checks: true

reporting:
  include_code_snippets: true
  include_recommendations: true
  group_by_severity: true
```

### Tool-Specific Configuration

#### Slither Configuration
```yaml
tools:
  slither:
    detectors:
      - reentrancy-eth
      - reentrancy-no-eth
      - uninitialized-state
      - suicidal
      - tx-origin
    exclude_detectors:
      - solc-version
    json_output: true
```

## 📊 Report Formats

### JSON Report Example
```json
{
  "summary": {
    "total_files": 5,
    "total_findings": 12,
    "critical": 2,
    "high": 4,
    "medium": 4,
    "low": 2
  },
  "findings": [
    {
      "tool": "solidity",
      "rule_id": "solidity_reentrancy_vulnerability",
      "title": "Potential reentrancy vulnerability",
      "severity": "HIGH",
      "file_path": "contracts/Token.sol",
      "line_number": 45,
      "code_snippet": "(bool success, ) = msg.sender.call{value: amount}(\"\");",
      "cwe_id": "CWE-841",
      "recommendation": "Use checks-effects-interactions pattern"
    }
  ]
}
```

### Markdown Report Example
```markdown
# Smart Contract Security Analysis Report

## Summary
- **Total Files Analyzed:** 5
- **Total Findings:** 12
- **Critical:** 2 🔴
- **High:** 4 🟠
- **Medium:** 4 🟡
- **Low:** 2 🟢

## Critical Issues

### Reentrancy Vulnerability in Token.sol
- **Line:** 45
- **Code:** `(bool success, ) = msg.sender.call{value: amount}("");`
- **Risk:** External call before state changes allows reentrancy attacks
- **Fix:** Implement checks-effects-interactions pattern
```

## 🧪 Testing Smart Contract Security

### Create Test Contract
```solidity
// test-contract.sol
pragma solidity ^0.8.0;

contract TestContract {
    mapping(address => uint) balances;
    
    function withdraw(uint amount) public {
        require(balances[msg.sender] >= amount);
        msg.sender.call{value: amount}("");  // Vulnerable
        balances[msg.sender] -= amount;
    }
}
```

### Run Analysis
```bash
securecli scan test-contract.sol
```

### Expected Output
```
🔍 Analyzing test-contract.sol...

❌ HIGH: Potential reentrancy vulnerability
   Line 7: msg.sender.call{value: amount}("");
   Rule: solidity_reentrancy_vulnerability
   CWE: CWE-841
   
   Recommendation: Use checks-effects-interactions pattern and reentrancy guards

📊 Summary: 1 file, 1 finding (1 HIGH)
```

## 🔍 Advanced Features

### Custom Rule Development
Create custom smart contract security rules:

```python
# custom_rules.py
from securecli.tools.base import SecurityTool
from securecli.schemas.findings import Finding, Severity

class CustomSolidityRules(SecurityTool):
    def analyze_file(self, file_path):
        findings = []
        
        # Custom rule: Check for missing events
        if "function transfer" in content and "emit Transfer" not in content:
            findings.append(Finding(
                rule_id="missing_transfer_event",
                title="Missing Transfer event",
                severity=Severity.MEDIUM,
                # ... other fields
            ))
        
        return findings
```

### Integration with CI/CD

#### GitHub Actions
```yaml
name: Smart Contract Security
on: [push, pull_request]

jobs:
  security:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.10'
      
      - name: Install SecureCLI
        run: |
          pip install securecli
          ./scripts/install-security-tools.sh
      
      - name: Security Analysis
        run: |
          securecli scan contracts/ --format=json --output=security-report.json
          
      - name: Upload Results
        uses: actions/upload-artifact@v3
        with:
          name: security-report
          path: security-report.json
```

#### GitLab CI
```yaml
security_scan:
  image: python:3.10
  before_script:
    - pip install securecli
    - ./scripts/install-security-tools.sh
  script:
    - securecli scan contracts/ --format=json --output=security-report.json
  artifacts:
    reports:
      junit: security-report.json
```

## 🛡️ Best Practices

### Development Workflow
1. **Pre-commit Scanning:** Scan contracts before committing
2. **Continuous Integration:** Automated security checks in CI/CD
3. **Regular Audits:** Periodic comprehensive security reviews
4. **Tool Updates:** Keep analysis tools updated

### Security Guidelines
- Use latest Solidity version (0.8.x) for built-in overflow protection
- Implement reentrancy guards for external calls
- Use `msg.sender` instead of `tx.origin` for authorization
- Validate all external inputs and return values
- Implement proper access controls
- Use secure randomness sources
- Test edge cases and failure scenarios

### Performance Optimization
- Use `.securecliignore` to exclude test files and dependencies
- Enable parallel scanning for large codebases
- Configure tool-specific optimizations
- Use incremental scanning in CI for changed files only

## 📚 Resources

### Documentation
- [Solidity Security Considerations](https://docs.soliditylang.org/en/latest/security-considerations.html)
- [Vyper Security Guidelines](https://docs.vyperlang.org/en/stable/security_considerations.html)
- [Slither Documentation](https://github.com/crytic/slither)

### Security References
- [Smart Contract Weakness Classification (SWC)](https://swcregistry.io/)
- [OWASP Smart Contract Top 10](https://owasp.org/www-project-smart-contract-top-10/)
- [ConsenSys Smart Contract Best Practices](https://consensys.github.io/smart-contract-best-practices/)

### Tools and Libraries
- [OpenZeppelin Contracts](https://openzeppelin.com/contracts/) - Secure contract libraries
- [Mythril](https://github.com/ConsenSys/mythril) - Additional Ethereum security analyzer
- [Echidna](https://github.com/crytic/echidna) - Property-based fuzzing
- [Manticore](https://github.com/trailofbits/manticore) - Symbolic execution

## 🤝 Contributing

We welcome contributions to improve smart contract security analysis:

1. **New Security Patterns:** Add detection for additional vulnerabilities
2. **Tool Integrations:** Integrate with more analysis tools
3. **Language Support:** Add support for new smart contract languages
4. **Documentation:** Improve examples and best practices

See [CONTRIBUTING.md](../CONTRIBUTING.md) for development guidelines.

## 🔧 Troubleshooting

### Common Issues

#### Slither Installation Problems
```bash
# Fix Python path issues
pip install --upgrade pip setuptools wheel
pip install slither-analyzer --force-reinstall

# macOS specific fix
export CFLAGS=-I$(brew --prefix)/include
export LDFLAGS=-L$(brew --prefix)/lib
```

#### Solidity Compiler Version Issues
```bash
# Install specific solc version
npm install -g solc@0.8.21

# Or use solc-select for version management
pip install solc-select
solc-select install 0.8.21
solc-select use 0.8.21
```

#### Vyper Compilation Errors
```bash
# Update Vyper to latest version
pip install --upgrade vyper

# Clear Python cache
python -c "import vyper; print(vyper.__file__)"
rm -rf $(python -c "import vyper; print(vyper.__file__)")/../__pycache__
```

For additional help, run the validation script:
```bash
python scripts/validate-tools.py
```

This will check all tool installations and provide specific troubleshooting guidance.