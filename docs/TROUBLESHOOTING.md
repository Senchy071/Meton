# Troubleshooting Guide

Common issues and solutions for Meton.

---

## Table of Contents
1. [Installation Issues](#installation-issues)
2. [Runtime Errors](#runtime-errors)
3. [Performance Issues](#performance-issues)
4. [Configuration Problems](#configuration-problems)
5. [Tool-Specific Issues](#tool-specific-issues)
6. [Web UI Issues](#web-ui-issues)
7. [VS Code Extension Issues](#vs-code-extension-issues)
8. [Getting Help](#getting-help)

---

## Installation Issues

### Python Version Errors

Symptom:
```
ERROR: Python 3.10+ required, but found 3.9
```

Solution:
```bash
# Ubuntu - Install Python 3.10
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv python3.10-dev

# macOS - Install via Homebrew
brew install python@3.10

# Verify installation
python3.10 --version
```

### Virtual Environment Issues

Symptom:
```
Command 'python' not found after activating venv
```

Solution:
```bash
# Recreate virtual environment
rm -rf venv
python3.10 -m venv venv

# Activate
source venv/bin/activate # Linux/macOS
# OR
venv\Scripts\activate # Windows

# Verify
which python # Should show venv path
```

### Dependency Installation Failures

Symptom:
```
ERROR: Could not build wheels for faiss-cpu
```

Solution:
```bash
# Install build dependencies
sudo apt install build-essential python3-dev

# Install FAISS separately
pip install faiss-cpu --no-cache-dir

# Then install rest of requirements
pip install -r requirements.txt
```

Symptom:
```
ERROR: sentence-transformers installation failed
```

Solution:
```bash
# Install PyTorch first
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cpu

# Then install sentence-transformers
pip install sentence-transformers
```

### Ollama Installation Issues

Symptom:
```
bash: ollama: command not found
```

Solution:
```bash
# Linux - Install Ollama
curl -fsSL https://ollama.com/install.sh | sh

# Add to PATH if needed
export PATH=$PATH:/usr/local/bin

# Verify
ollama --version

# Start Ollama service
ollama serve &
```

### Model Download Issues

Symptom:
```
Error: model not found
```

Solution:
```bash
# Check available models
ollama list

# Pull specific model
ollama pull qwen2.5-coder:32b

# If download fails, retry
ollama pull qwen2.5-coder:32b --insecure-skip-tls-verify

# Check disk space
df -h

# Check Ollama status
curl http://localhost:11434/api/tags
```

---

## Runtime Errors

### Out of Memory

Symptom:
```
RuntimeError: CUDA out of memory
# OR
Killed (Out of memory)
```

Solution:

Option 1: Use smaller model
```yaml
# config.yaml
models:
 primary: "mistral:7b" # Instead of llama3.1:70b
```

Option 2: Increase swap space
```bash
# Add 32GB swap (Linux)
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile

# Make permanent
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
```

Option 3: Close other applications
```bash
# Check memory usage
free -h

# Kill memory-hungry processes
top # Press 'k' to kill processes
```

### Connection Refused

Symptom:
```
ConnectionRefusedError: [Errno 111] Connection refused
```

Solution:
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama
ollama serve &

# Verify it's listening
curl http://localhost:11434/api/tags

# Check firewall
sudo ufw status
sudo ufw allow 11434
```

### Import Errors

Symptom:
```
ModuleNotFoundError: No module named 'langchain'
```

Solution:
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall dependencies
pip install --upgrade -r requirements.txt

# If still failing, clean install
pip freeze | xargs pip uninstall -y
pip install -r requirements.txt
```

### Agent Timeout

Symptom:
```
ERROR: Agent timeout after 300 seconds
```

Solution:
```yaml
# config.yaml - Increase timeout
agent:
 timeout: 600 # 10 minutes

# OR use faster model
models:
 primary: "mistral:7b"
```

### Loop Detection

Symptom:
```
WARNING: Loop detected, forcing completion
```

Solution:
This is expected behavior preventing infinite loops. If happening too often:

```yaml
# config.yaml - Increase max iterations
agent:
 max_iterations: 15 # Default is 10
```

Or rephrase query to be more specific:
```
# Instead of:
> Tell me about authentication

# Use:
> Show me the JWT token validation function in auth.py
```

---

## Performance Issues

### Slow Response Times

Symptom:
Queries taking >30 seconds

Solution:

1. Use faster model
```bash
/model mistral:7b
# OR
/profile use quick
```

2. Disable verbose mode
```bash
/verbose off
```

3. Reduce RAG results
```yaml
# config.yaml
rag:
 top_k: 5 # Instead of 10
```

4. Disable unnecessary tools
```bash
/web off
```

### Slow Indexing

Symptom:
Codebase indexing takes >10 minutes

Solution:

1. Index specific directories
```bash
# Instead of entire project
/index /path/to/specific/module
```

2. Exclude large directories
```python
# Modify rag/indexer.py
EXCLUDE_DIRS = [
 "__pycache__", ".git", "node_modules",
 "venv", "build", "dist",
 "large_data_dir" # Add your directories
]
```

3. Check disk I/O
```bash
iostat -x 1 # Linux

# If high I/O wait, consider:
# - Using SSD instead of HDD
# - Closing other disk-intensive apps
```

### High CPU Usage

Symptom:
CPU at 100% during queries

Expected CPU usage is high during LLM inference (normal)

If excessive:
```bash
# Check process CPU
top

# Limit Ollama threads
OLLAMA_NUM_THREADS=8 ollama serve

# Use smaller model
/model mistral:7b
```

---

## Configuration Problems

### Config Not Loading

Symptom:
```
ERROR: Could not load config.yaml
```

Solution:
```bash
# Check file exists
ls -la config.yaml

# Validate YAML syntax
python3 -c "import yaml; yaml.safe_load(open('config.yaml'))"

# If corrupt, restore from backup
cp config.yaml.backup config.yaml

# Or recreate by re-running setup
./setup.sh
```

### Invalid Configuration

Symptom:
```
ValidationError: Invalid model configuration
```

Solution:
```yaml
# Check required fields in config.yaml
models:
 primary: "qwen2.5-coder:32b" # Must be valid model name
 fallback: "llama3.1:8b"
 quick: "mistral:7b"
 temperature: 0.0 # Must be float between 0 and 1
 max_tokens: 2048 # Must be positive integer
```

### Permission Denied

Symptom:
```
PermissionError: [Errno 13] Permission denied: 'config.yaml'
```

Solution:
```bash
# Fix file permissions
chmod 644 config.yaml

# Fix directory permissions
chmod 755 ~/.meton

# Check ownership
ls -la config.yaml
chown $USER:$USER config.yaml
```

---

## Tool-Specific Issues

### File Operations Errors

Symptom:
```
ERROR: Path /etc/passwd is blocked
```

Solution:
This is expected security behavior. Blocked paths include `/etc`, `/sys`, `/proc`.

To allow specific paths:
```yaml
# config.yaml
tools:
 file_operations:
 allowed_paths:
 - "/home/user/projects"
 - "/media/development"
```

Symptom:
```
ERROR: File not found
```

Solution:
```bash
# Use absolute paths
> Read /home/user/project/file.py

# Not relative paths
> Read file.py # May fail
```

### Code Executor Issues

Symptom:
```
ERROR: Import 'os' is blocked
```

Solution:
This is expected security. Blocked imports include `os`, `subprocess`, `eval`.

Allowed imports are in `tools/code_executor.py:ALLOWED_IMPORTS`:
```python
ALLOWED_IMPORTS = [
 'math', 'random', 'datetime', 'json',
 'typing', 'collections', 're', ...
]
```

To add allowed import (use caution!):
```python
# tools/code_executor.py
ALLOWED_IMPORTS = [
 # ... existing ...
 'your_safe_library',
]
```

Symptom:
```
ERROR: Execution timeout after 5 seconds
```

Solution:
```yaml
# config.yaml - Increase timeout (be careful!)
tools:
 code_executor:
 timeout: 10 # seconds
```

### Web Search Not Working

Symptom:
```
ERROR: Web search tool is disabled
```

Solution:
```bash
# Enable web search
/web on

# Verify
/tools
```

Symptom:
```
ERROR: DuckDuckGo search failed
```

Solution:
```bash
# Check internet connection
ping -c 3 duckduckgo.com

# Update ddgs library
pip install --upgrade ddgs

# If still failing, may be rate-limited
# Wait a few minutes and try again
```

### RAG Search Not Working

Symptom:
```
ERROR: No index found, please run /index first
```

Solution:
```bash
# Index your codebase
/index /path/to/project

# Check index status
/index status
```

Symptom:
```
ERROR: FAISS index corrupted
```

Solution:
```bash
# Clear and rebuild index
/index clear
/index /path/to/project

# If still failing, delete index files
rm -rf rag_index/
/index /path/to/project
```

---

## Web UI Issues

### Web UI Not Loading

Symptom:
Browser shows "Connection refused" at http://localhost:7860

Solution:
```bash
# Check if server is running
ps aux | grep launch_web

# Start server
python launch_web.py

# Check port availability
lsof -i :7860

# Use different port if 7860 is taken
python launch_web.py --port 8080
```

### Gradio Errors

Symptom:
```
ERROR: Gradio version mismatch
```

Solution:
```bash
# Update Gradio
pip install --upgrade gradio

# Check version
pip show gradio # Should be 4.0+
```

### File Upload Fails

Symptom:
File upload doesn't work in web UI

Solution:
```bash
# Check file size limit (default: 10MB)
# Increase in launch_web.py if needed

# Check file permissions
chmod 644 your_file.py

# Try smaller file first
```

### Analytics Not Displaying

Symptom:
Analytics tab shows errors or blank charts

Solution:
```bash
# Install/update visualization dependencies
pip install --upgrade plotly pandas

# Check analytics data exists
ls -la analytics/

# Enable analytics if disabled
# config.yaml
analytics:
 enabled: true
```

---

## VS Code Extension Issues

### Extension Not Loading

Symptom:
VS Code shows "Extension activation failed"

Solution:
```bash
# Rebuild extension
cd vscode-extension
npm install
npm run compile

# Reinstall
npm run package
code --install-extension meton-0.1.0.vsix --force

# Check VS Code logs
# View -> Output -> Meton
```

### Server Connection Failed

Symptom:
"Cannot connect to Meton server"

Solution:
```bash
# Start Meton API server
python api/server.py

# Or start with uvicorn
uvicorn api.server:app --host 0.0.0.0 --port 8000

# Check server URL in VS Code settings
# Should match: http://localhost:8000
```

### LSP Features Not Working

Symptom:
No code actions, diagnostics, or completions

Solution:
1. Check Meton server is running
2. Reload VS Code window (Ctrl+Shift+P -> "Reload Window")
3. Check Output panel for errors
4. Verify extension is activated (bottom status bar should show Meton icon)

---

## Getting Help

### Diagnostic Information

When reporting issues, include:

```bash
# System information
python --version
pip freeze
ollama list

# Meton status
/status
/tools
/memory stats

# Error logs
tail -n 50 meton.log

# Configuration (sanitized)
cat config.yaml
```

### Debug Mode

Enable debug logging:

```yaml
# config.yaml
logging:
 level: "DEBUG"
 file: "meton_debug.log"
```

Run with verbose:
```bash
python meton.py --verbose
```

### Log Files

Check logs for errors:

```bash
# Meton logs
tail -f meton.log

# Ollama logs
journalctl -u ollama -f

# Web UI logs
tail -f web_ui.log

# System logs
dmesg | tail
```

### Common Log Patterns

Out of memory:
```
kernel: Out of memory: Killed process
```

Port in use:
```
OSError: [Errno 98] Address already in use
```

Permission denied:
```
PermissionError: [Errno 13] Permission denied
```

Module not found:
```
ModuleNotFoundError: No module named 'X'
```

---

## Reporting Bugs

### Before Reporting

1. Check this troubleshooting guide
2. Search existing [GitHub Issues](https://github.com/Senchy071/Meton/issues)
3. Try with latest version
4. Try with clean configuration
5. Collect diagnostic information

### Bug Report Template

```markdown
Environment:
- OS: Ubuntu 22.04
- Python: 3.10.12
- Meton version: 0.1.0
- Ollama version: 0.1.17

Description:
Clear description of the issue

Steps to Reproduce:
1. Step one
2. Step two
3. Step three

Expected Behavior:
What should happen

Actual Behavior:
What actually happens

Logs:
```
Relevant log output
```

Configuration:
```yaml
Relevant config.yaml sections
```
```

### Where to Report

- Bugs [GitHub Issues](https://github.com/Senchy071/Meton/issues)
- Questions [GitHub Discussions](https://github.com/Senchy071/Meton/discussions)
- Security Email security@yourdomain.com

---

## Still Need Help?

1. **Read Documentation
 - [User Guide](USER_GUIDE.md)
 - [Installation Guide](INSTALLATION.md)
 - [API Reference](API_REFERENCE.md)

2. **Search Issues
 - [Open Issues](https://github.com/Senchy071/Meton/issues)
 - [Closed Issues](https://github.com/Senchy071/Meton/issues?q=is%3Aissue+is%3Aclosed)

3. **Ask Community
 - [GitHub Discussions](https://github.com/Senchy071/Meton/discussions)

4. **Contact Maintainers
 - Create detailed issue with template above

---

Most issues can be resolved by:
- Reinstalling dependencies
- Using smaller models
- Checking logs
- Verifying configuration
- Ensuring services are running
