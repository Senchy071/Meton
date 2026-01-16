# Meton - Local AI Coding Assistant

<p align="center">
 <strong>Metis + Ergon = Wisdom in Action</strong>
</p>

<p align="center">
 A fully local AI coding assistant powered by LLMs, designed for privacy and performance.
</p>

<p align="center">
 <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+"/>
 <img src="https://img.shields.io/badge/Version-1.0.0-brightgreen" alt="Version 1.0.0"/>
 <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
 <img src="https://img.shields.io/badge/Status-Production-success" alt="Production Ready"/>
 <img src="https://img.shields.io/badge/Tests-510%2B-blue" alt="510+ Tests"/>
 <img src="https://img.shields.io/badge/Coverage-95%25-brightgreen" alt="95% Coverage"/>
</p>

---

## Features

### Core Capabilities
- 100% Local Execution - No external API calls (web search disabled by default), complete privacy
- Semantic Code Search - FAISS-based RAG for intelligent codebase understanding
- Symbol Lookup - Fast exact definition lookup for functions, classes, methods with `/find` command
- Import Graph Analysis - Dependency visualization, cycle detection, coupling metrics with Mermaid diagrams
- Advanced Skills - 7 specialized skills for code analysis and generation
- Multi-Agent Coordination - Sophisticated task decomposition and execution
- Self-Reflection - Iterative improvement of responses with quality synthesis
- Performance Analytics - Track and optimize agent performance
- Git Integration - Intelligent commit messages and code review
- Long-Term Memory - Cross-session learning and pattern detection
- Performance Optimization - Intelligent caching, profiling, and resource monitoring
- Comprehensive Testing - 510+ tests with 95%+ pass rate, CI/CD pipeline

### Skills Available
1. Code Explainer - Detailed code analysis with complexity metrics
2. Debugger Assistant - Error analysis and fix suggestions
3. Refactoring Engine - 10+ refactoring patterns
4. Test Generator - Pytest/unittest generation with edge cases
5. Documentation Generator - Docstrings, README, API docs (Google/NumPy/Sphinx styles)
6. Code Reviewer - Best practices, security, style compliance
7. Task Planner - Complex task decomposition with visualization

### Interfaces
- Web UI - Gradio-based browser interface with chat, analytics, session management
- CLI - Rich terminal interface with 30+ commands
- VS Code Extension - LSP integration, code actions, inline assistance

---

## Quick Start

### Prerequisites
- Python 3.10+
- 32GB+ RAM (64GB+ recommended for 32B models, 128GB+ for 70B models)
- Linux/macOS/Windows (WSL2)
- Optional: CUDA-capable GPU for performance

### Installation

```bash
# Clone repository
git clone https://github.com/Senchy071/Meton.git
cd Meton

# Run setup script
chmod +x setup.sh
./setup.sh

# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Download models
ollama pull qwen2.5-coder:32b
ollama pull llama3.1:8b
ollama pull mistral:7b

# Launch CLI
source venv/bin/activate
python meton.py

# OR Launch in offline mode (disables library telemetry)
./meton_offline.sh

# OR Launch Web UI
python launch_web.py
```

Access web UI at: http://localhost:7860

**Note**: For completely offline operation (no internet required after setup), use `./meton_offline.sh`. See [Privacy & Offline Operation](#privacy--offline-operation) below

---

## Documentation

- [Installation Guide](docs/INSTALLATION.md) - Detailed setup instructions
- [User Guide](docs/USER_GUIDE.md) - Complete usage guide
- [API Reference](docs/API_REFERENCE.md) - Agent and tool APIs
- [Development Guide](docs/DEVELOPMENT.md) - Contributing and extending
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [Testing Guide](docs/TESTING.md) - Comprehensive testing instructions
- [Examples](docs/EXAMPLES.md) - Usage examples and workflows
- [Architecture](docs/ARCHITECTURE.md) - System design details
- [Status](docs/STATUS.md) - Current development status
- [Quick Reference](docs/QUICK_REFERENCE.md) - Command cheat sheet

---

## Privacy & Offline Operation

Meton is designed for **complete privacy** with 100% local execution:

### ✅ Fully Local Components
- **LLM Processing**: All AI inference runs on your machine via Ollama
- **Code Analysis**: RAG pipeline (parsing, embeddings, search) runs locally
- **Data Storage**: All conversations, indexes, and memories stored locally
- **File Operations**: No file uploads to external services
- **Embeddings**: sentence-transformers runs on CPU, models cached locally

### 🌐 Optional External Tool
- **Web Search**: Disabled by default, makes external calls to DuckDuckGo when enabled
  - Enable only when needed: `/web on`
  - Disable for complete privacy: `/web off`
  - Your code is never sent to external services

### 🔒 Privacy Guarantee
**Your code never leaves your machine** (unless you explicitly enable web search). All processing happens locally on your hardware.

### ⚠️ Important: Dependency Library Telemetry

While **Meton itself makes no external calls**, some Python libraries it depends on (HuggingFace, LangChain, Gradio) may attempt to send telemetry or check for updates.

**To ensure 100% offline operation:**

```bash
# Use the offline launcher (disables all library telemetry)
./meton_offline.sh
```

This is required if you want to:
- Work completely offline after initial setup
- Ensure no data leaves your machine (even library telemetry)
- Use Meton in air-gapped environments

**First-time setup requires internet once** to download:
- Ollama models
- Sentence-transformers embedding model
- Python packages

After setup, `./meton_offline.sh` allows 100% offline operation.

See [docs/PRIVACY.md](docs/PRIVACY.md) for complete privacy and security documentation

---

## Use Cases

### Software Development
- Understand large codebases quickly
- Get intelligent code reviews
- Generate tests automatically
- Debug complex issues
- Refactor legacy code

### Learning & Research
- Explore unfamiliar codebases
- Understand design patterns
- Compare implementations
- Research best practices

### Documentation
- Generate comprehensive docs
- Create API references
- Write project READMEs

---

## Architecture

```
┌─────────────────────────────────────────────┐
│ User Interfaces │
│ (Web UI │ CLI │ VS Code Extension) │
└─────────────────┬───────────────────────────┘
 │
┌─────────────────▼───────────────────────────┐
│ Meton Agent (ReAct) │
│ ┌──────────┬──────────┬──────────────┐ │
│ │ Planning │Execution │ Reflection │ │
│ │ (CoT) │(Tools) │(Self-improve)│ │
│ └──────────┴──────────┴──────────────┘ │
└─────────────────┬───────────────────────────┘
 │
┌─────────────────▼───────────────────────────┐
│ Tools & Skills │
│ ┌────────┬────────┬────────┬────────┐ │
│ │ RAG │ Git │ Skills │ Exec │ │
│ │ Search │ Ops │ (7) │ Code │ │
│ └────────┴────────┴────────┴────────┘ │
└─────────────────┬───────────────────────────┘
 │
┌─────────────────▼───────────────────────────┐
│ Local LLM (Ollama) │
│ Qwen 2.5 32B │ Llama 3.1 8B │ Mistral 7B │
└─────────────────────────────────────────────┘
```

Key Components:
- ReAct Agent: Think -> Act -> Observe loop with loop detection
- RAG System: FAISS vector store with semantic code search
- Skills Framework: High-level capabilities (7 production skills)
- Multi-Agent: Task decomposition with specialized agents
- Memory System: Long-term semantic memory (10k capacity)
- Analytics: Performance tracking and bottleneck detection

---

## Example Usage

### CLI Mode

```bash
# Start Meton
python meton.py

# Index a codebase
/index /path/to/your/project

# Ask questions
> How does authentication work in this codebase?

THOUGHT: Using codebase_search to find authentication logic
ACTION: codebase_search
INPUT: {"query": "authentication login user verify"}

Based on auth/login.py:45-67, the system uses JWT tokens...

# Get code review
> Review this code:
def process_data(data):
 return eval(data["query"])

CRITICAL: Never use eval() with untrusted input...

# Generate tests
> Generate pytest tests for the authenticate_user function

Generated 5 test cases covering normal flow, edge cases, and errors...
```

### Web UI Mode

```bash
python launch_web.py --port 7860
```

Features:
- Interactive chat with code syntax highlighting
- File upload (drag & drop)
- Real-time analytics dashboards
- Session management
- Model switching
- Conversation export

### VS Code Extension

Install extension, then:
- `Ctrl+Shift+E` - Explain selected code
- `Ctrl+Shift+M` - Open chat sidebar
- Right-click -> Meton menu for code actions

---

## Configuration

Meton uses configuration profiles for different use cases:

- Development - Optimized for coding tasks (reflection enabled, all skills)
- Research - Deep analysis and information gathering (web search, memory)
- Writing - Content creation (simplified tools, documentation focus)
- Quick Response - Fast answers, minimal overhead (smaller models)
- Code Review - Thorough code analysis (review skill, git integration)

Switch profiles:
```bash
/profile list
/profile use development
```

Edit `config.yaml` to customize models, tools, and settings.

---

## Performance

Benchmark Results (AMD Ryzen 9 7950X, RTX 3090):
- Simple queries: ~2-5 seconds
- Complex analysis: ~10-30 seconds
- Codebase indexing (FastAPI, 1087 files): ~60 seconds
- Semantic search: <1 second
- Test generation: ~15 seconds
- Code review: ~20 seconds

Resource Usage:
- Qwen 2.5 32B: ~32GB RAM, ~8GB VRAM
- Llama 3.1 8B: ~8GB RAM, ~4GB VRAM
- Mistral 7B: ~7GB RAM, ~3GB VRAM

---

## Testing

Meton includes comprehensive testing infrastructure for validating all capabilities against real-world Python projects.

### Quick Smoke Test (30-60 seconds)

```bash
# Fast sanity check of all core components
python test_quick.py
```

### Indexing Test (2-5 minutes)

```bash
# Test RAG indexing pipeline only (no agent scenarios)
python test_indexing_only.py

# Test with different project
python test_indexing_only.py --project fastapi_realworld
```

### Comprehensive Test Suite (requires manual run)

```bash
# Test against real-world GitHub projects with agent scenarios
# NOTE: Requires Ollama running and can take 20+ minutes
# Best run interactively to monitor progress

python test_meton_comprehensive.py --quick

# Test specific projects
python test_meton_comprehensive.py --projects fastapi_example
```

### Unit and Integration Tests (510+ tests)

```bash
# Run all unit tests
python test_runner.py

# Run with pytest
python -m pytest tests/ -v

# Run specific test suites
python tests/integration/test_end_to_end.py
python tests/performance/test_benchmarks.py
python tests/optimization/test_optimizations.py
```

**Current status**: 95%+ pass rate across all test suites

See [Testing Guide](docs/TESTING.md) for detailed testing instructions, troubleshooting, and CI/CD integration.

---

## Contributing

Contributions welcome! See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for guidelines.

Ways to contribute:
- Report bugs
- Suggest features
- Improve documentation
- Add new skills or tools
- Write tests

---

## License

MIT License - see [LICENSE](LICENSE) for details.

---

## Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - Agent framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration
- [Ollama](https://ollama.com/) - Local LLM serving
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [Gradio](https://gradio.app/) - Web UI
- [Rich](https://rich.readthedocs.io/) - CLI formatting
- [sentence-transformers](https://www.sbert.net/) - Embeddings

---

## Contact

- GitHub Issues: [Report bugs or request features](https://github.com/Senchy071/Meton/issues)
- Discussions: [Join the conversation](https://github.com/Senchy071/Meton/discussions)

---

## Project Status

VERSION 1.1.0 - PRODUCTION READY

Overall Progress: 100% COMPLETE (54/54 tasks)
All 6 Phases: Complete
Total Tests: 510+ comprehensive tests (95%+ pass rate)
Code Coverage: 95%+
Status: Production Ready

### Achievements
- All 54 tasks completed - 100% project completion
- 10 production-ready skills - 7 Python + 3 Markdown (code analysis, debugging, refactoring, testing, documentation, review, planning)
- Triple interface - CLI + Web UI + VS Code Extension with LSP
- Performance optimization - Caching, profiling, query optimization, resource monitoring
- Comprehensive testing - 510+ tests with CI/CD pipeline
- Advanced AI features - Multi-agent coordination, self-reflection, long-term memory, cross-session learning
- Git integration - AI-powered code review, commit messages, branch suggestions
- Complete documentation - Installation, user guide, API reference, troubleshooting, examples
- Export/Import system - Full state backup and restore
- Configuration profiles - 5 built-in profiles for different use cases
- Claude Code-style extensions - Markdown skills, sub-agents, hooks system
- Configurable logging - Daily rotating logs with library suppression

See [STATUS.md](docs/STATUS.md) for complete project history and [CHANGELOG.md](docs/CHANGELOG.md) for version details.

---

Built by developers, for developers who value privacy and performance

*Meton is a fully local AI coding assistant - your code never leaves your machine.*
