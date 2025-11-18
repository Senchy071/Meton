# Installation Guide

Complete installation instructions for Meton local AI coding assistant.

---

## Table of Contents
1. [System Requirements](#system-requirements)
2. [Installation Steps](#installation-steps)
3. [Model Installation](#model-installation)
4. [Configuration](#configuration)
5. [Verification](#verification)
6. [Optional Components](#optional-components)
7. [Troubleshooting](#troubleshooting)

---

## System Requirements

### Minimum Requirements
- CPU: 8 cores (Intel i7 or AMD Ryzen 7)
- RAM: 32GB DDR4
- Storage: 50GB free space (SSD recommended)
- OS: Linux (Ubuntu 20.04+), macOS (10.15+), Windows 10/11 (WSL2)
- Python: 3.10 or higher

### Recommended Requirements
- CPU: 16+ cores (AMD Ryzen 9 7950X or Intel i9-13900K)
- RAM: 128GB DDR5 (for 70B models)
- GPU: NVIDIA RTX 3090 (24GB) or better
- Storage: 100GB+ NVMe SSD
- OS: Linux (Ubuntu 22.04+ or Pop!_OS)
- Python: 3.11+

### Software Prerequisites
- Git: For cloning the repository
- Python 3.10+: With pip and venv
- CUDA 12.0+: Optional, for GPU acceleration
- Ollama: For running local LLMs

---

## Installation Steps

### 1. Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y \
 python3.10 \
 python3-pip \
 python3-venv \
 git \
 build-essential \
 curl
```

#### macOS
```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install dependencies
brew install python@3.10 git
```

#### Windows (WSL2)
```bash
# Install WSL2 first (PowerShell as Administrator)
wsl --install -d Ubuntu-22.04

# Then follow Ubuntu instructions inside WSL
```

---

### 2. Clone Repository

```bash
# Clone from GitHub (replace with actual repository URL)
git clone https://github.com/Senchy071/Meton.git
cd meton

# Verify you're in the right directory
pwd # Should show: /path/to/meton
```

---

### 3. Create Virtual Environment

```bash
# Create virtual environment
python3.10 -m venv venv

# Activate virtual environment
source venv/bin/activate # Linux/macOS
# OR
venv\Scripts\activate # Windows (PowerShell)

# Verify activation (should show venv path)
which python
```

---

### 4. Install Python Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install requirements
pip install -r requirements.txt

# This will install:
# - langchain
# - langchain-community
# - langgraph
# - sentence-transformers
# - faiss-cpu
# - rich
# - gradio
# - gitpython
# - plotly
# - pandas
# - pydantic
# - pyyaml
# - and more...
```

Expected installation time: 5-10 minutes depending on internet speed.

---

### 5. Install Ollama

Ollama is required for running local LLMs.

#### Linux
```bash
curl -fsSL https://ollama.com/install.sh | sh

# Verify installation
ollama --version
```

#### macOS
```bash
# Download from website or use Homebrew
brew install ollama

# Start Ollama service
ollama serve
```

#### Windows
Download installer from [ollama.com/download](https://ollama.com/download) and run it.

---

### 6. Download Models

Download at least one model to get started.

```bash
# Recommended: Qwen 2.5 Coder (32B parameters, ~32GB RAM)
ollama pull qwen2.5-coder:32b

# Alternative: Llama 3.1 (8B parameters, ~8GB RAM)
ollama pull llama3.1:8b

# Lightweight: Mistral (7B parameters, ~7GB RAM)
ollama pull mistral:7b

# Advanced: Llama 3.1 (70B parameters, ~128GB RAM)
# Only if you have 128GB+ RAM
ollama pull llama3.1:70b
```

Model sizes:
- `mistral:7b`: ~4.1GB download
- `llama3.1:8b`: ~4.7GB download
- `qwen2.5-coder:32b`: ~18GB download
- `llama3.1:70b`: ~40GB download

Download time: 10-60 minutes depending on model and internet speed.

---

### 7. Configure Meton

```bash
# Copy example config
cp config.yaml config.yaml.backup # Backup existing config if any

# Edit config.yaml
nano config.yaml # or vim, code, etc.
```

Key configuration options:

```yaml
models:
 primary: "qwen2.5-coder:32b" # Change based on your downloaded models
 fallback: "llama3.1:8b"
 quick: "mistral:7b"
 temperature: 0.0
 max_tokens: 2048

tools:
 file_operations:
 enabled: true
 code_executor:
 enabled: true
 web_search:
 enabled: false # Enable if you want web search
 codebase_search:
 enabled: true

rag:
 enabled: true
 top_k: 10
 similarity_threshold: 0.7

skills:
 enabled: true
 auto_load: true
```

Important paths to configure:
- `allowed_paths`: Add directories you want Meton to access
- `blocked_paths`: Keep default blocked paths for security

---

### 8. Verify Installation

```bash
# Ensure virtual environment is activated
source venv/bin/activate

# Test CLI
python meton.py

# You should see:
# Meton - Local AI Coding Assistant
# ...
# Type /help for commands
```

Test basic functionality:
```
> /status
> /models
> /tools
> Hello, can you introduce yourself?
> /exit
```

---

## Model Installation

### Choosing the Right Model

| Model | Parameters | RAM Required | Speed | Use Case |
|-------|-----------|--------------|-------|----------|
| Mistral | 7B | 8GB | Fast | Quick queries |
| Llama 3.1 | 8B | 8GB | Fast | General purpose |
| Qwen 2.5 Coder | 32B | 32GB | Medium | Code-focused |
| Llama 3.1 | 70B | 128GB | Slow | Advanced reasoning |

### Installing Multiple Models

```bash
# Install all recommended models
ollama pull mistral:7b
ollama pull llama3.1:8b
ollama pull qwen2.5-coder:32b

# Verify installations
ollama list
```

### Updating Models

```bash
# Update a specific model
ollama pull qwen2.5-coder:32b

# Remove old models
ollama rm old-model:tag
```

---

## Configuration

### Configuration Profiles

Meton comes with 5 built-in profiles:

```bash
# List available profiles
/profile list

# Activate a profile
/profile use development # For coding tasks
/profile use research # For deep analysis
/profile use writing # For documentation
/profile use quick # For fast responses
/profile use code-review # For thorough reviews
```

### Custom Configuration

Create custom profiles:
```bash
# In Meton CLI
/profile save my-profile "My custom setup" development
```

Or edit `config.yaml` directly:
```yaml
# Add under config.profiles section
my_profile:
 name: "My Profile"
 description: "Custom configuration"
 category: "custom"
 settings:
 model: "qwen2.5-coder:32b"
 temperature: 0.1
 # ...more settings
```

---

## Verification

### Run Test Suite

```bash
# Basic infrastructure tests
python test_infrastructure.py

# Model manager tests
python test_models.py

# Agent tests
python test_agent.py

# RAG tests
python test_rag_indexer.py

# Skills tests
python test_skills.py
```

Expected output: All tests should pass with .

### Verify Web UI

```bash
# Launch web interface
python launch_web.py

# Open browser to:
# http://localhost:7860
```

Check:
- Chat interface loads
- Can send messages
- Model selection works
- File upload works

---

## Optional Components

### VS Code Extension

```bash
cd vscode-extension

# Install Node.js dependencies
npm install

# Compile TypeScript
npm run compile

# Package extension
npm run package

# Install in VS Code
code --install-extension meton-0.1.0.vsix
```

### GPU Acceleration

#### NVIDIA GPU (CUDA)
```bash
# Install CUDA toolkit (Ubuntu)
wget https://developer.download.nvidia.com/compute/cuda/repos/ubuntu2204/x86_64/cuda-keyring_1.0-1_all.deb
sudo dpkg -i cuda-keyring_1.0-1_all.deb
sudo apt-get update
sudo apt-get -y install cuda

# Verify
nvidia-smi
nvcc --version
```

#### AMD GPU (ROCm)
```bash
# Follow ROCm installation guide
# https://rocm.docs.amd.com/en/latest/deploy/linux/quick_start.html
```

### Additional Tools

```bash
# Install additional development tools
pip install black flake8 mypy pytest-cov

# Install Jupyter for notebooks
pip install jupyter ipykernel
```

---

## Troubleshooting

### Issue: Command not found: python3.10

Solution:
```bash
# Ubuntu - add deadsnakes PPA
sudo add-apt-repository ppa:deadsnakes/ppa
sudo apt update
sudo apt install python3.10 python3.10-venv

# macOS - install via Homebrew
brew install python@3.10
```

### Issue: Out of memory when running models

Solution:
- Use smaller model (mistral:7b instead of llama3.1:70b)
- Close other applications
- Increase swap space:
```bash
# Add 32GB swap (Linux)
sudo fallocate -l 32G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
```

### Issue: Ollama not found

Solution:
```bash
# Ensure Ollama is in PATH
which ollama

# If not found, restart terminal or add to PATH
export PATH=$PATH:/usr/local/bin

# Start Ollama service
ollama serve &
```

### Issue: Import errors (ModuleNotFoundError)

Solution:
```bash
# Ensure venv is activated
source venv/bin/activate

# Reinstall requirements
pip install --upgrade -r requirements.txt

# If still failing, try clean install
rm -rf venv
python3.10 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### Issue: Permission denied errors

Solution:
```bash
# Fix file permissions
chmod +x setup.sh meton.py launch_web.py

# Fix directory permissions
chmod 755 ~/.meton
```

### Issue: Web UI not loading

Solution:
```bash
# Check if port 7860 is in use
lsof -i :7860

# Use different port
python launch_web.py --port 8080

# Check firewall
sudo ufw allow 7860
```

---

## Next Steps

After successful installation:

1. **Read the User Guide [USER_GUIDE.md](USER_GUIDE.md)
2. **Try Examples [EXAMPLES.md](EXAMPLES.md)
3. **Index a Project `/index /path/to/your/code`
4. **Explore Skills `/skills list`
5. **Check Analytics `/analytics dashboard`

---

## Getting Help

- Documentation Check [docs/](.)
- Troubleshooting See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- GitHub Issues Report bugs or ask questions
- Discussions Join the community

---

## Uninstallation

To remove Meton:

```bash
# Deactivate virtual environment
deactivate

# Remove Meton directory
cd ..
rm -rf meton

# Remove Ollama models (optional)
ollama rm qwen2.5-coder:32b
ollama rm llama3.1:8b

# Uninstall Ollama (optional)
# Linux
sudo rm -rf /usr/local/bin/ollama /usr/share/ollama

# macOS
brew uninstall ollama
```

---

Installation complete! You're ready to use Meton. 
