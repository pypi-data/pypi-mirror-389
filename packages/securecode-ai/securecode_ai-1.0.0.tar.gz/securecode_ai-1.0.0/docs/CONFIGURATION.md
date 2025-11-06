# SecureCLI Configuration Reference

## Overview

SecureCLI uses a hierarchical configuration system that supports multiple sources:

1. **Default Configuration** - Built-in defaults
2. **User Configuration** - `~/.securecli/config.yml`
3. **Workspace Configuration** - `<workspace>/config.yml`
4. **Environment Variables** - `SECURE_*` prefix

Configuration precedence: Environment Variables > Workspace Config > User Config > Defaults

## Usage

```bash
# Set configuration option
set <option> <value>

# Remove configuration option  
unset <option>

# View current configuration
show options

# Get detailed help
help config
```

## Command Reference

SecureCLI provides comprehensive security analysis commands for various scenarios:

### Core Analysis Commands

```bash
# Analyze local project/directory
analyze <path>                    # Comprehensive analysis
analyze <path> --mode quick       # Fast static analysis
analyze <path> --mode deep        # Extended analysis + AI
analyze <path> --mode comprehensive # Full analysis + RAG + reporting

# Analyze GitHub repositories
github <github_url>               # Analyze main branch
github <github_url> <branch>      # Analyze specific branch  
github <github_url> <branch> <mode> # With specific scan mode

# Quick scans
scan quick                        # Fast reconnaissance
scan deep                         # Deep security scan
scan comprehensive               # Full security audit
```

### Analysis Examples

```bash
# Local project analysis
analyze ./myproject --mode deep
analyze /path/to/webapp --mode comprehensive

# GitHub repository analysis
github https://github.com/microsoft/vscode
github https://github.com/facebook/react main deep
github https://github.com/ethereum/solidity develop

# Language detection
languages ./project              # Detect project technologies
```

### Workspace Management

```bash
# Workspace operations
workspace list                   # List all workspaces
workspace create <name>          # Create new workspace
workspace use <name>             # Switch to workspace
workspace delete <name>          # Delete workspace
```

### AI Integration Commands

```bash
# AI management
ai status                        # Check AI integration status
ai test                          # Test API connectivity
ai test-local                    # Test local model
ai enable                        # Enable AI features
ai disable                       # Disable AI features
ai switch <provider>             # Switch AI provider (auto/openai/local)
ai-status                        # Show detailed AI status

# Local model management
ai local enable                  # Enable local model inference
ai local disable                 # Disable local models
ai local info                    # Show local model configuration
ai local setup                   # Interactive setup guide
```

### Configuration Commands

```bash
# Configuration management
set <option> <value>             # Set configuration option
unset <option>                   # Remove configuration option
show options                     # View current configuration
show modules                     # Display available modules
show info                        # Show system information

# Module operations
use <module_name>                # Select module for engagement
run                              # Execute current module
back                             # Deselect current module
modules                          # List available scanners
```

### Utility Commands

```bash
# System utilities
status                           # Show system status
script <script_file>             # Execute script file
clear                            # Clear terminal screen
cls                              # Clear terminal screen (alias)
exit                             # Terminate session
quit                             # Terminate session (alias)
q                                # Terminate session (alias)
help                             # Show command reference
```

## Repository Settings

### `repo.path`
**Type:** String  
**Default:** `null`  
**Description:** Target repository path for analysis

```bash
set repo.path /path/to/your/project
set repo.path https://github.com/owner/repo
```

### `repo.exclude`
**Type:** Array of Strings  
**Default:** `["node_modules/", "__pycache__/", ".git/", "build/", "dist/", "vendor/", ".pytest_cache/", "coverage/", ".next/", ".nuxt/"]`  
**Description:** Directories and file patterns to exclude from scanning

```bash
set repo.exclude node_modules/,dist/,build/
```

### `repo.max_file_size`
**Type:** Integer  
**Default:** `1048576` (1MB)  
**Description:** Maximum file size to scan in bytes

```bash
set repo.max_file_size 2097152  # 2MB
```

## GitHub Integration

SecureCLI provides direct GitHub repository analysis capabilities with comprehensive language support and automated cloning.

### GitHub Analysis Command

```bash
# Basic repository analysis
github <github_url>

# Analyze specific branch
github <github_url> <branch>

# Analyze with specific scan mode
github <github_url> <branch> <mode>
```

### GitHub Command Options

**URL Formats Supported:**
- `https://github.com/owner/repo`
- `https://github.com/owner/repo.git`
- `git@github.com:owner/repo.git`

**Branch Options:**
- `main` (default)
- `master`
- `develop`
- Any valid branch name

**Scan Modes:**
- `quick` - Fast static analysis
- `deep` - Extended analysis + AI insights
- `comprehensive` - Full analysis + RAG + reporting (default)

### GitHub Configuration Settings

### `github.clone_depth`
**Type:** Integer  
**Default:** `1`  
**Description:** Git clone depth for repository analysis

```bash
set github.clone_depth 5  # Clone last 5 commits
set github.clone_depth 0  # Full clone (all history)
```

### `github.temp_dir`
**Type:** String  
**Default:** `"/tmp/securecli"`  
**Description:** Temporary directory for cloned repositories

```bash
set github.temp_dir /custom/temp/path
```

### `github.cleanup_after`
**Type:** Boolean  
**Default:** `true`  
**Description:** Automatically cleanup cloned repositories after analysis

```bash
set github.cleanup_after false  # Keep cloned repos
```

### `github.max_repo_size`
**Type:** String  
**Default:** `"100MB"`  
**Description:** Maximum repository size to analyze

```bash
set github.max_repo_size 500MB
set github.max_repo_size 1GB
```

### `github.timeout`
**Type:** Integer  
**Default:** `300`  
**Description:** Clone and analysis timeout in seconds

```bash
set github.timeout 600  # 10 minutes
```

### GitHub Token Configuration

For private repositories and higher rate limits:

```bash
# Environment variable (recommended)
export GITHUB_TOKEN=ghp_your_token_here

# OR configuration setting
set api_keys.github ghp_your_token_here
```

### GitHub Analysis Features

**Supported Languages:**
- **Web2:** JavaScript, TypeScript, React, Vue, Angular, HTML/CSS
- **Web3:** Solidity, Vyper, Move, Cairo, Rust (blockchain)
- **Backend:** Python, Java, C#, Go, Ruby, PHP, Node.js
- **Mobile:** Swift, Kotlin, Dart (Flutter), React Native
- **Systems:** C, C++, Rust, Assembly
- **Data:** R, MATLAB, Jupyter Notebooks
- **DevOps:** Dockerfile, YAML, Terraform, Ansible

**Security Analysis:**
- Static code analysis across all supported languages
- Dependency vulnerability scanning
- Secrets and API key detection
- Infrastructure as Code security
- Container security analysis
- Smart contract security (Web3)

**AI Integration:**
- Contextual vulnerability analysis
- Code fix recommendations
- Security best practices
- OWASP and CWE mapping

### GitHub Usage Examples

```bash
# Analyze popular repositories
github https://github.com/microsoft/vscode
github https://github.com/facebook/react main comprehensive
github https://github.com/ethereum/solidity develop

# Private repository (requires GITHUB_TOKEN)
github https://github.com/yourorg/private-repo

# Quick scan for CI/CD
github https://github.com/owner/repo main quick

# Deep analysis for security audit
github https://github.com/owner/repo main deep
```

### GitHub Integration Workflow

1. **Repository Detection**
   - Validates GitHub URL format
   - Checks repository accessibility
   - Detects default branch if not specified

2. **Smart Cloning**
   - Shallow clone for performance (configurable depth)
   - Temporary directory management
   - Authentication handling for private repos

3. **Language Detection**
   - Automatic language and framework detection
   - Technology stack analysis
   - Security-relevant file identification

4. **Comprehensive Analysis**
   - Multi-tool security scanning
   - AI-powered vulnerability analysis
   - Contextual risk assessment

5. **Report Generation**
   - Detailed findings with file paths
   - Repository metadata and statistics
   - Language-specific recommendations

### GitHub Rate Limiting

**Without Token:**
- 60 requests per hour
- Public repositories only

**With GitHub Token:**
- 5,000 requests per hour
- Access to private repositories
- Enhanced metadata access

**Best Practices:**
- Configure GITHUB_TOKEN for regular use
- Use shallow clones for large repositories
- Enable cleanup to manage disk space

## Scan Modes & Tools

### `mode`
**Type:** String  
**Default:** `"quick"`  
**Options:** `quick | deep | comprehensive`  
**Description:** Scan intensity level

- **quick** - Fast static analysis (5-15 tools)
- **deep** - Extended analysis + AI insights  
- **comprehensive** - Full analysis + RAG + reporting

```bash
set mode comprehensive
```

### `tools.enabled`
**Type:** Array of Strings  
**Default:** `["semgrep", "gitleaks", "bandit", "gosec"]`  
**Description:** Active security scanning tools

```bash
set tools.enabled semgrep,bandit,gitleaks,gosec
```

## AI & LLM Settings

### `llm.model`
**Type:** String  
**Default:** `"gpt-4"`  
**Options:** `gpt-4 | gpt-3.5-turbo | claude-3-sonnet | claude-3-opus | deepseek-coder`  
**Description:** Language model to use for AI analysis

```bash
set llm.model gpt-4
set llm.model claude-3-sonnet
set llm.model deepseek-coder  # For local models
```

### `llm.provider`
**Type:** String  
**Default:** `"auto"`  
**Options:** `auto | openai | anthropic | local`  
**Description:** AI provider for model inference

```bash
set llm.provider auto      # Smart provider selection (recommended)
set llm.provider openai    # Use OpenAI API
set llm.provider anthropic # Use Anthropic Claude
set llm.provider local     # Use local models only
```

**Provider Selection Strategy:**
- **`auto`** - Intelligently selects based on system capabilities and availability
- **`openai`** - Reliable cloud-based inference, requires API key
- **`anthropic`** - Alternative cloud provider for Claude models
- **`local`** - Privacy-first local inference, requires model setup

### `llm.max_tokens`
**Type:** Integer  
**Default:** `2000`  
**Description:** Maximum tokens per AI request

```bash
set llm.max_tokens 4000
```

### `llm.temperature`
**Type:** Float  
**Default:** `0.1`  
**Range:** `0.0 - 1.0`  
**Description:** AI creativity level (lower = more deterministic)

```bash
set llm.temperature 0.1
```

### `llm.timeout`
**Type:** Integer  
**Default:** `60`  
**Description:** AI request timeout in seconds

```bash
set llm.timeout 120
```

## Local Model Settings

### `local_model.enabled`
**Type:** Boolean  
**Default:** `false`  
**Description:** Enable local model inference

```bash
set local_model.enabled true
```

### `local_model.engine`
**Type:** String  
**Default:** `"ollama"`  
**Options:** `ollama | llamacpp | transformers`  
**Description:** Local inference engine

```bash
set local_model.engine ollama      # Recommended
set local_model.engine llamacpp    # High performance
set local_model.engine transformers # HuggingFace models
```

### `local_model.model_name`
**Type:** String  
**Default:** `"deepseek-coder"`  
**Description:** Local model name or identifier

```bash
set local_model.model_name deepseek-coder
set local_model.model_name codellama
set local_model.model_name wizardcoder
```

### `local_model.base_url`
**Type:** String  
**Default:** `"http://localhost:11434"`  
**Description:** Base URL for Ollama server

```bash
set local_model.base_url http://localhost:11434
set local_model.base_url http://your-server:11434
```

### `local_model.model_path`
**Type:** String  
**Default:** `null`  
**Description:** Local path to model file (for llamacpp/transformers)

```bash
set local_model.model_path /path/to/model.gguf
set local_model.model_path deepseek-ai/deepseek-coder-1.3b-instruct
```

### `local_model.context_length`
**Type:** Integer  
**Default:** `4096`  
**Description:** Model context window size

```bash
set local_model.context_length 8192
```

### `local_model.gpu_layers`
**Type:** Integer  
**Default:** `35`  
**Description:** Number of model layers to run on GPU

```bash
set local_model.gpu_layers 35  # Most layers on GPU
set local_model.gpu_layers 0   # CPU only
```

### `local_model.threads`
**Type:** Integer  
**Default:** `8`  
**Description:** CPU threads for inference

```bash
set local_model.threads 16
```

### `local_model.batch_size`
**Type:** Integer  
**Default:** `512`  
**Description:** Batch size for inference

```bash
set local_model.batch_size 1024
```

### `local_model.quantization`
**Type:** String  
**Default:** `"q4_k_m"`  
**Options:** `q4_k_m | q5_k_m | q8_0 | f16 | f32`  
**Description:** Model quantization level

```bash
set local_model.quantization q4_k_m  # Balanced
set local_model.quantization q8_0    # Higher quality
set local_model.quantization f16     # Full precision
```

## RAG & Knowledge Base

### `rag.enabled`
**Type:** Boolean  
**Default:** `true`  
**Description:** Enable Retrieval-Augmented Generation for enhanced analysis

```bash
set rag.enabled true
```

### `rag.k`
**Type:** Integer  
**Default:** `5`  
**Description:** Number of context chunks to retrieve

```bash
set rag.k 10
```

### `rag.chunk_size`
**Type:** Integer  
**Default:** `1000`  
**Description:** Size of text chunks for indexing

```bash
set rag.chunk_size 1500
```

### `rag.chunk_overlap`
**Type:** Integer  
**Default:** `200`  
**Description:** Overlap between chunks

```bash
set rag.chunk_overlap 300
```

## Domain & Profiles

### `domain.profiles`
**Type:** Array of Strings  
**Default:** `[]`  
**Options:** `web | api | mobile | iot | blockchain | cloud`  
**Description:** Security testing profiles for domain-specific checks

```bash
set domain.profiles web,api
set domain.profiles mobile,iot
```

## CVSS & CI/CD Integration

### `cvss.policy`
**Type:** String  
**Default:** `"block_high"`  
**Options:** `block_critical | block_high | block_medium | warn_only`  
**Description:** CVSS severity blocking policy

```bash
set cvss.policy block_critical
```

### `ci.block_on`
**Type:** Array of Strings  
**Default:** `["critical", "high"]`  
**Options:** `critical | high | medium | low`  
**Description:** CI/CD pipeline blocking criteria

```bash
set ci.block_on critical,high,medium
```

### `ci.changed_files_only`
**Type:** Boolean  
**Default:** `false`  
**Description:** Only scan changed files in CI/CD

```bash
set ci.changed_files_only true
```

## Output & Reporting

### `output.dir`
**Type:** String  
**Default:** `"./output"`  
**Description:** Output directory for reports

```bash
set output.dir ./security-reports
```

### `output.format`
**Type:** String  
**Default:** `"md"`  
**Options:** `md | json | sarif | html`  
**Description:** Primary report output format

```bash
set output.format json
```

## Security & Redaction

### `redact.enabled`
**Type:** Boolean  
**Default:** `true`  
**Description:** Enable sensitive data redaction in reports

```bash
set redact.enabled true
```

### `redact.patterns`
**Type:** Array of Strings  
**Default:** Built-in patterns for secrets, API keys, etc.  
**Description:** Regex patterns for sensitive data detection

```bash
# Advanced usage - add custom patterns
set redact.patterns "(?i)(custom_secret)\s*[:=]\s*['\"][^'\"]+['\"]"
```

### `sandbox.enabled`
**Type:** Boolean  
**Default:** `true`  
**Description:** Enable sandbox execution for dynamic analysis

```bash
set sandbox.enabled false
```

### `sandbox.timeout`
**Type:** Integer  
**Default:** `300`  
**Description:** Sandbox execution timeout in seconds

```bash
set sandbox.timeout 600
```

### `sandbox.memory_limit`
**Type:** String  
**Default:** `"512MB"`  
**Description:** Memory limit for sandbox execution

```bash
set sandbox.memory_limit 1GB
```

## Logging

### `logging.level`
**Type:** String  
**Default:** `"INFO"`  
**Options:** `DEBUG | INFO | WARNING | ERROR | CRITICAL`  
**Description:** Logging verbosity level

```bash
set logging.level DEBUG
```

### `logging.file`
**Type:** String  
**Default:** `null`  
**Description:** Log file path (console if null)

```bash
set logging.file ./logs/securecli.log
```

## Provider Management

### Quick Provider Switching
```bash
# Switch to auto-selection (recommended)
ai switch auto

# Switch to OpenAI for reliability
ai switch openai

# Switch to local for privacy
ai switch local

# Switch to Anthropic Claude
ai switch anthropic
```

### Provider Status & Testing
```bash
# Check all provider availability
ai status

# Test current provider
ai test

# Test local model specifically
ai test-local

# Test with specific model
set llm.model gpt-4 && ai test
```

### Provider Selection Logic
When using `llm.provider: auto`, SecureCLI intelligently selects providers based on:

1. **Hardware Capabilities**
   - GPU memory (8GB+ prefers local)
   - CPU cores (16+ cores enables local fallback)
   - Available RAM

2. **Provider Availability**
   - Local model status and performance
   - API key configuration
   - Network connectivity

3. **Use Case Optimization**
   - Privacy-sensitive tasks → Local models
   - Large-scale analysis → API models
   - Quick scans → Best available

### Environment Variables

All configuration options can be set via environment variables using the `SECURE_` prefix:

```bash
export SECURE_LLM_MODEL=gpt-4
export SECURE_RAG_ENABLED=true
export SECURE_OUTPUT_DIR=./reports
export SECURE_CVSS_POLICY=block_high
```

## API Keys

### OpenAI
```bash
export OPENAI_API_KEY=sk-...
# or
set api_keys.openai sk-...
```

### Anthropic
```bash
export ANTHROPIC_API_KEY=sk-ant-...
# or  
set api_keys.anthropic sk-ant-...
```

### GitHub
```bash
export GITHUB_TOKEN=ghp_...
# or
set api_keys.github ghp_...
```

## Configuration Files

### User Configuration
Location: `~/.securecli/config.yml`

```yaml
llm:
  model: gpt-4
  max_tokens: 4000
  temperature: 0.1

rag:
  enabled: true
  k: 10

output:
  dir: ./security-reports
  format: json

cvss:
  policy: block_high
```

### Workspace Configuration
Location: `<workspace>/config.yml`

```yaml
repo:
  path: .
  exclude:
    - node_modules/
    - dist/
    - .git/

mode: comprehensive

domain:
  profiles:
    - web
    - api
```

## Examples

### Hybrid Setup (Recommended)
```bash
# Enable auto-selection for best of both worlds
set llm.provider auto

# Configure OpenAI as backup/fallback
export OPENAI_API_KEY=your_key_here

# Set up local model for privacy-sensitive work
set local_model.enabled true
set local_model.engine ollama
set local_model.model_name deepseek-coder

# System will automatically choose:
# - Local model for privacy/performance (if GPU available)
# - OpenAI API for reliability/speed (if local unavailable)
```

### API-Only Setup (No GPU)
```bash
# For users without powerful hardware
set llm.provider openai

# Set target repository
set repo.path /path/to/project

# Configure AI model and limits
set llm.model gpt-4
set llm.max_tokens 4000

# Set output preferences
set output.dir ./reports
set output.format json
```

### Privacy-First Setup (Local Only)
```bash
# Complete offline operation
set llm.provider local
set local_model.enabled true

# Use local model only - no API calls
set local_model.engine ollama
set local_model.model_name deepseek-coder

# Enhanced privacy settings
set rag.enabled true      # Local knowledge base
set redact.enabled true   # Redact sensitive data
set sandbox.enabled true  # Isolated execution
```

### Performance-Optimized Setup
```bash
# Auto-selection with performance tuning
set llm.provider auto

# Local model optimizations
set local_model.gpu_layers 35        # Use GPU acceleration
set local_model.context_length 8192  # Larger context window
set local_model.quantization q5_k_m  # Higher quality quantization
set local_model.threads 16           # More CPU threads

# API model optimizations
set llm.max_tokens 4000
set llm.temperature 0.1
```

### CI/CD Configuration
```bash
# Only scan changed files
set ci.changed_files_only true

# Block on critical and high severity
set ci.block_on critical,high

# Set strict CVSS policy
set cvss.policy block_critical
```

### Domain-Specific Setup
```bash
# Web application security
set domain.profiles web,api
set tools.enabled semgrep,gitleaks,bandit

# Mobile app security
set domain.profiles mobile
set tools.enabled semgrep,gitleaks,bandit,gosec
```

### Local Model Setup
```bash
# Quick Ollama + DeepSeek setup
# 1. Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# 2. Pull DeepSeek model
ollama pull deepseek-coder

# 3. Configure SecureCLI
set llm.provider local
set local_model.enabled true
set local_model.engine ollama
set local_model.model_name deepseek-coder

# 4. Test setup
ai test-local

# Alternative: GPU-optimized setup
set local_model.gpu_layers 35
set local_model.context_length 8192
set local_model.quantization q5_k_m
```

### Privacy-First Configuration
```bash
# Use only local models (no API calls)
set llm.provider local
set local_model.enabled true
set rag.enabled true  # Local knowledge base
set redact.enabled true  # Redact sensitive data
set sandbox.enabled true  # Isolated execution
```

## Validation

The configuration system automatically validates settings:

- Required fields (e.g., `llm.model`)
- File/directory existence (e.g., `repo.path`)
- Valid enum values (e.g., `cvss.policy`)
- Type checking (integers, booleans, arrays)

Invalid configurations will show helpful error messages with suggestions for fixes.

---

**Created by 5m477**  
**Contact:** [x.com/5m477](https://x.com/5m477)

check local llm


secureᶜˡⁱ(test)› set llm.provider local
llm.provider => local
secureᶜˡⁱ(test)› set local_model.enabled true
local_model.enabled => True
secureᶜˡⁱ(test)› set local_model.engine ollama
local_model.engine => ollama
secureᶜˡⁱ(test)› set local_model.model_name deepseek-coder-v2:16b
local_model.model_name => deepseek-coder-v2:16b
secureᶜˡⁱ(test)› 
secureᶜˡⁱ(test)› ai-status
analyze examples/vulnerable-webapp/ --mode deep
