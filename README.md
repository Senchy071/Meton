# 🧠 Meton

**Local AI Coding Assistant** - Wisdom in Action (Metis + Ergon)

A fully local coding assistant powered by LangChain, LangGraph, and Ollama.
Everything runs on your hardware - no external API calls, no data leaving your machine.

## Features

### Core Capabilities
- 🏠 **Fully Local** - All processing happens on your machine
- 🤖 **Intelligent Agent** - Uses ReAct pattern for multi-step reasoning
- 🔍 **Semantic Code Search** - Natural language queries on indexed codebases (RAG with FAISS)
- 📁 **File Operations** - Read, write, and navigate your codebase
- ⚙️ **Code Execution** - Safe Python code execution with sandboxing
- 🌐 **Web Search** - DuckDuckGo integration for external information (opt-in)
- 💬 **Conversation Memory** - Maintains context across interactions
- 🔀 **Multi-Model** - Switch between models easily (Qwen, Llama, Mistral)

### Advanced Features
- 🧠 **Long-Term Memory** - Persistent semantic memory across sessions (10k capacity)
- 📊 **Cross-Session Learning** - Pattern detection and insight generation
- 🌐 **Web UI** - Gradio-based browser interface with analytics
- 🎨 **Beautiful CLI** - Rich terminal interface with syntax highlighting
- 🔧 **7 Production Skills** - Code explainer, debugger, refactoring, testing, docs, review
- 📈 **Performance Analytics** - Real-time monitoring and bottleneck detection
- 🔄 **Git Integration** - AI-powered code review and commit analysis

## Requirements

- Python 3.11+
- Ollama installed and running
- NVIDIA GPU with 20GB+ VRAM (for CodeLlama 34B)
- Linux (tested on Pop!_OS/Ubuntu)

## Hardware

Designed for:
- AMD Ryzen 9 7950X (16C/32T)
- 128GB DDR5 RAM
- RTX 3090 24GB

## Installation

```bash
# Clone or create project
cd /media/development/projects/meton

# Run setup
chmod +x setup.sh
./setup.sh

# Activate environment
source venv/bin/activate
```

## Usage

### CLI Mode
```bash
# Start Meton CLI
python meton.py

# Or use the shortcut
./meton
```

### Web UI Mode
```bash
# Launch Gradio web interface
python launch_web.py

# With options
python launch_web.py --share --port 8080 --auth user:pass
```

### Interactive Commands (30+)

**Basic:**
- `/help, /h` - Show available commands
- `/status` - Show current configuration and session info
- `/models` - List available models
- `/model <name>` - Switch model (primary/fallback/quick or full name)
- `/tools` - List available tools
- `/verbose on/off` - Toggle verbose mode (show agent thinking)

**Conversation:**
- `/history` - Show conversation history
- `/search <keyword>` - Search conversation history
- `/clear, /c` - Clear conversation history
- `/save` - Save current conversation

**Code Search (RAG):**
- `/index [path]` - Index a codebase for semantic search
- `/index status` - Show indexing statistics
- `/index clear` - Delete the current index
- `/index refresh` - Re-index the last path
- `/csearch <query>` - Test semantic code search directly

**Memory & Learning:**
- `/memory stats` - Show memory statistics
- `/memory search <query>` - Search memories semantically
- `/memory add <content>` - Add manual memory
- `/memory export [json|csv]` - Export memories
- `/learn analyze` - Analyze sessions for patterns
- `/learn insights` - Show generated insights
- `/learn patterns` - Show detected patterns
- `/learn summary` - Learning statistics

**Tools:**
- `/web on/off` - Enable/disable web search tool
- `/reload` - Reload configuration without restart
- `/exit, /quit, /q` - Exit Meton

### Example Session

```
You: /index /media/development/projects/meton

🔍 Indexing /media/development/projects/meton...
Found 23 Python files

Processing files... ━━━━━━━━━━ 100% 23/23 00:04

✅ Complete! Indexed 23 files, 127 chunks in 4.8s
RAG enabled ✅
Codebase search enabled ✅

You: How does authentication work in this codebase?

💭 THOUGHT: This is a code understanding question, using codebase_search
🔧 ACTION: codebase_search
📥 INPUT: {"query": "authentication login user verify"}

💬 Assistant:
Based on auth/login.py:45-67, the system uses token-based
authentication with JWT...

You: /status

╭─── Current Status ───────────────────────────────╮
│ Model:        qwen2.5:32b-instruct-q5_K_M        │
│ Session:      3c8a9f2d-4b1e...                   │
│ Messages:     4                                  │
│ Tools:        file_operations, code_executor,    │
│               web_search, codebase_search, git   │
│ RAG:          ✅ enabled (127 chunks)            │
╰──────────────────────────────────────────────────╯

You: /exit
👋 Goodbye!
```

## Architecture

```
CLI (Rich) → Agent (LangGraph) → Models (Ollama) → Tools
                                                     ├─ File Operations
                                                     ├─ Code Executor
                                                     ├─ Web Search
                                                     └─ Codebase Search (RAG)
                                                         └─ FAISS Vector Store
```

## Configuration

Edit `config.yaml` to customize:
- Model selection and parameters
- Tool permissions and paths
- Conversation settings
- CLI appearance

## Current Status

**Progress:** 81.2% complete (39/48 tasks) | **Phase 5:** Integration & Polish (5/12 complete)

### ✅ Completed Phases

**Phase 1: Foundation** (8/8 tasks)
- Core agent with ReAct pattern and loop detection
- Model Manager (Ollama: Qwen 2.5 32B, Llama 3.1, Mistral)
- Conversation Manager (thread-safe, auto-save)
- File Operations Tool (security, validation)
- CLI Interface (Rich, 30+ commands)
- 74/74 tests passing

**Phase 1.5: Execution & Search** (4/4 tasks)
- Code Execution Tool (subprocess isolation, AST validation)
- Web Search Tool (DuckDuckGo, opt-in)
- Agent integration
- Runtime tool control

**Phase 2: Codebase Intelligence** (5/8 tasks)
- RAG infrastructure (FAISS, sentence-transformers)
- Code Parser (AST-based extraction)
- Code Chunker (semantic chunking)
- Codebase Indexer (orchestration)
- Semantic Code Search Tool (natural language queries)

**Phase 3: Advanced Skills** (8/8 tasks)
- Skill Framework (BaseSkill, auto-loading)
- Code Explainer, Debugger Assistant, Refactoring Engine
- Test Generator, Documentation Generator, Code Review
- Skill Manager (load/unload dynamically)
- 194 tests passing (100% success rate)

**Phase 4: Agent Intelligence** (8/8 tasks)
- Multi-Agent Coordinator (task decomposition)
- Self-Reflection Module (quality analysis)
- Iterative Improvement Loop (convergence detection)
- Feedback Learning System (pattern matching)
- Parallel Tool Execution, Chain-of-Thought Reasoning
- Task Planning & Decomposition
- Performance Analytics (metrics, bottleneck detection)
- 163 tests passing

**Phase 5: Integration & Polish** (5/12 tasks) - IN PROGRESS
- ✅ Gradio Web UI (chat, file upload, analytics)
- ✅ Multi-Session & Visualization (Plotly charts)
- ✅ Git Integration (AI review, commit analysis)
- ✅ Long-Term Memory (semantic storage, 10k capacity)
- ✅ Cross-Session Learning (pattern detection, insights)
- ⬜ VS Code Extension, LSP Integration
- ⬜ Export/Import, Analytics Dashboard
- ⬜ Documentation, Optimization, Final Testing

### Key Achievements
- 25,000+ lines of production Python
- 194+ comprehensive tests (100% pass rate)
- 7 production-ready skills
- 8 integrated tools
- Dual interface (CLI + Web UI)
- Cross-session intelligence with pattern learning
- Semantic memory system

## Documentation

### User Guides
- [USAGE.md](USAGE.md) - Complete usage guide with examples and troubleshooting
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - One-page command cheat sheet

### Technical Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and extension guide
- [STATUS.md](STATUS.md) - Development status and features (updated)
- [CLAUDE.md](CLAUDE.md) - Development guidance for Claude Code

## License

Personal project - use as you wish

## Author

Senad Arifhodzic w/ Claude Code⚡
