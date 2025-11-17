# 🧠 Meton - Local AI Coding Assistant

<p align="center">
  <strong>Metis + Ergon = Wisdom in Action</strong>
</p>

<p align="center">
  A fully local AI coding assistant powered by LLMs, designed for privacy and performance.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python 3.10+"/>
  <img src="https://img.shields.io/badge/License-MIT-green" alt="MIT License"/>
  <img src="https://img.shields.io/badge/Status-Production-success" alt="Production Ready"/>
</p>

---

## ✨ Features

### Core Capabilities
- 🤖 **100% Local Execution** - No external API calls, complete privacy
- 🔍 **Semantic Code Search** - FAISS-based RAG for intelligent codebase understanding
- 🛠️ **Advanced Skills** - 7 specialized skills for code analysis and generation
- 🧠 **Multi-Agent Coordination** - Sophisticated task decomposition and execution
- 💭 **Self-Reflection** - Iterative improvement of responses
- 📊 **Performance Analytics** - Track and optimize agent performance
- 🔄 **Git Integration** - Intelligent commit messages and code review
- 💾 **Long-Term Memory** - Cross-session learning and pattern detection

### Skills Available
1. **Code Explainer** - Detailed code analysis with complexity metrics
2. **Debugger Assistant** - Error analysis and fix suggestions
3. **Refactoring Engine** - 10+ refactoring patterns
4. **Test Generator** - Pytest/unittest generation with edge cases
5. **Documentation Generator** - Docstrings, README, API docs (Google/NumPy/Sphinx styles)
6. **Code Reviewer** - Best practices, security, style compliance
7. **Task Planner** - Complex task decomposition with visualization

### Interfaces
- 🌐 **Web UI** - Gradio-based browser interface with chat, analytics, session management
- 💻 **CLI** - Rich terminal interface with 30+ commands
- 🔌 **VS Code Extension** - LSP integration, code actions, inline assistance

---

## 🚀 Quick Start

### Prerequisites
- Python 3.10+
- 32GB+ RAM (64GB+ recommended for 32B models, 128GB+ for 70B models)
- Linux/macOS/Windows (WSL2)
- Optional: CUDA-capable GPU for performance

### Installation

```bash
# Clone repository
git clone https://github.com/yourusername/meton.git
cd meton

# Run setup script
chmod +x setup.sh
./setup.sh

# Install Ollama (if not already installed)
curl -fsSL https://ollama.com/install.sh | sh

# Download models
ollama pull qwen2.5-coder:32b
ollama pull llama3.1:8b
ollama pull mistral:7b

# Configure (edit config.yaml as needed)
cp config.yaml.example config.yaml

# Launch CLI
source venv/bin/activate
python meton.py

# OR Launch Web UI
python launch_web.py
```

Access web UI at: **http://localhost:7860**

---

## 📖 Documentation

- **[Installation Guide](docs/INSTALLATION.md)** - Detailed setup instructions
- **[User Guide](docs/USER_GUIDE.md)** - Complete usage guide
- **[API Reference](docs/API_REFERENCE.md)** - Agent and tool APIs
- **[Development Guide](docs/DEVELOPMENT.md)** - Contributing and extending
- **[Troubleshooting](docs/TROUBLESHOOTING.md)** - Common issues and solutions
- **[Examples](docs/EXAMPLES.md)** - Usage examples and workflows
- **[Architecture](ARCHITECTURE.md)** - System design details
- **[Status](STATUS.md)** - Current development status

---

## 🎯 Use Cases

### Software Development
- 📚 Understand large codebases quickly
- 🔍 Get intelligent code reviews
- ✅ Generate tests automatically
- 🐛 Debug complex issues
- ♻️ Refactor legacy code

### Learning & Research
- 🎓 Explore unfamiliar codebases
- 📖 Understand design patterns
- 🔬 Compare implementations
- 💡 Research best practices

### Documentation
- 📝 Generate comprehensive docs
- 📚 Create API references
- 📄 Write project READMEs

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────┐
│           User Interfaces                    │
│  (Web UI │ CLI │ VS Code Extension)         │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│           Meton Agent (ReAct)                │
│  ┌──────────┬──────────┬──────────────┐    │
│  │ Planning │Execution │ Reflection   │    │
│  │  (CoT)   │(Tools)   │(Self-improve)│    │
│  └──────────┴──────────┴──────────────┘    │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│              Tools & Skills                  │
│  ┌────────┬────────┬────────┬────────┐     │
│  │ RAG    │ Git    │ Skills │ Exec   │     │
│  │ Search │ Ops    │ (7)    │ Code   │     │
│  └────────┴────────┴────────┴────────┘     │
└─────────────────┬───────────────────────────┘
                  │
┌─────────────────▼───────────────────────────┐
│         Local LLM (Ollama)                   │
│  Qwen 2.5 32B │ Llama 3.1 8B │ Mistral 7B  │
└─────────────────────────────────────────────┘
```

**Key Components:**
- **ReAct Agent**: Think → Act → Observe loop with loop detection
- **RAG System**: FAISS vector store with semantic code search
- **Skills Framework**: High-level capabilities (7 production skills)
- **Multi-Agent**: Task decomposition with specialized agents
- **Memory System**: Long-term semantic memory (10k capacity)
- **Analytics**: Performance tracking and bottleneck detection

---

## 💻 Example Usage

### CLI Mode

```bash
# Start Meton
python meton.py

# Index a codebase
/index /path/to/your/project

# Ask questions
> How does authentication work in this codebase?

💭 THOUGHT: Using codebase_search to find authentication logic
🔧 ACTION: codebase_search
📥 INPUT: {"query": "authentication login user verify"}

💬 Based on auth/login.py:45-67, the system uses JWT tokens...

# Get code review
> Review this code:
def process_data(data):
    return eval(data["query"])

🚨 CRITICAL: Never use eval() with untrusted input...

# Generate tests
> Generate pytest tests for the authenticate_user function

✅ Generated 5 test cases covering normal flow, edge cases, and errors...
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
- Right-click → Meton menu for code actions

---

## 🔧 Configuration

Meton uses **configuration profiles** for different use cases:

- **Development** - Optimized for coding tasks (reflection enabled, all skills)
- **Research** - Deep analysis and information gathering (web search, memory)
- **Writing** - Content creation (simplified tools, documentation focus)
- **Quick Response** - Fast answers, minimal overhead (smaller models)
- **Code Review** - Thorough code analysis (review skill, git integration)

Switch profiles:
```bash
/profile list
/profile use development
```

Edit `config.yaml` to customize models, tools, and settings.

---

## 📊 Performance

**Benchmark Results** (AMD Ryzen 9 7950X, RTX 3090):
- Simple queries: ~2-5 seconds
- Complex analysis: ~10-30 seconds
- Codebase indexing (FastAPI, 1087 files): ~60 seconds
- Semantic search: <1 second
- Test generation: ~15 seconds
- Code review: ~20 seconds

**Resource Usage:**
- Qwen 2.5 32B: ~32GB RAM, ~8GB VRAM
- Llama 3.1 8B: ~8GB RAM, ~4GB VRAM
- Mistral 7B: ~7GB RAM, ~3GB VRAM

---

## 🧪 Testing

```bash
# Run all tests (305+ tests)
python -m pytest tests/

# Run specific test suites
python test_agent.py
python test_rag_indexer.py
python test_skills.py

# Current status: 92%+ pass rate
```

---

## 🤝 Contributing

Contributions welcome! See [DEVELOPMENT.md](docs/DEVELOPMENT.md) for guidelines.

**Ways to contribute:**
- 🐛 Report bugs
- 💡 Suggest features
- 📝 Improve documentation
- 🔧 Add new skills or tools
- ✅ Write tests

---

## 📝 License

MIT License - see [LICENSE](LICENSE) for details.

---

## 🙏 Acknowledgments

Built with:
- [LangChain](https://langchain.com/) - Agent framework
- [LangGraph](https://langchain-ai.github.io/langgraph/) - Agent orchestration
- [Ollama](https://ollama.com/) - Local LLM serving
- [FAISS](https://github.com/facebookresearch/faiss) - Vector search
- [Gradio](https://gradio.app/) - Web UI
- [Rich](https://rich.readthedocs.io/) - CLI formatting
- [sentence-transformers](https://www.sbert.net/) - Embeddings

---

## 📧 Contact

- **GitHub Issues**: [Report bugs or request features](https://github.com/yourusername/meton/issues)
- **Discussions**: [Join the conversation](https://github.com/yourusername/meton/discussions)

---

## 🎉 Project Status

**Overall Progress:** 85.4% complete (41/48 tasks)
**Current Phase:** Phase 5 - Integration & Polish (11/15 tasks)

### Recent Achievements
- ✅ 7 production-ready skills implemented
- ✅ Web UI with analytics and session management
- ✅ VS Code extension with LSP integration
- ✅ Long-term memory and cross-session learning
- ✅ Git integration with AI-powered code review
- ✅ 305+ comprehensive tests (92%+ pass rate)

See [STATUS.md](STATUS.md) for detailed progress.

---

**Built with ❤️ by developers, for developers who value privacy and performance**

*Meton is a fully local AI coding assistant - your code never leaves your machine.*
