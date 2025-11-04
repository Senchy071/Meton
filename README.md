# 🧠 Meton

**Local AI Coding Assistant** - Wisdom in Action (Metis + Ergon)

A fully local coding assistant powered by LangChain, LangGraph, and CodeLlama.
Everything runs on your hardware - no external API calls, no data leaving your machine.

## Features

- 🏠 **Fully Local** - All processing happens on your machine
- 🤖 **Intelligent Agent** - Uses ReAct pattern for multi-step reasoning
- 🔍 **Semantic Code Search** - Natural language queries on indexed codebases (RAG with FAISS)
- 📁 **File Operations** - Read, write, and navigate your codebase
- ⚙️ **Code Execution** - Safe Python code execution with sandboxing
- 🌐 **Web Search** - DuckDuckGo integration for external information
- 💬 **Conversation Memory** - Maintains context across interactions
- 🔀 **Multi-Model** - Switch between models easily (CodeLlama, Qwen, Llama, Mistral)
- 🎨 **Beautiful CLI** - Rich terminal interface with syntax highlighting

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

```bash
# Start Meton
python meton.py

# Or use the shortcut
./meton.py
```

### Interactive Commands

- `/help, /h` - Show available commands
- `/clear, /c` - Clear conversation history
- `/model <name>` - Switch model (primary/fallback/quick or full name)
- `/models` - List available models
- `/status` - Show current configuration and session info
- `/verbose on/off` - Toggle verbose mode (show agent thinking)
- `/save` - Save current conversation
- `/history` - Show conversation history
- `/search <keyword>` - Search conversation history
- `/reload` - Reload configuration without restart
- `/tools` - List available tools
- `/index [path]` - Index a codebase for semantic search
- `/index status` - Show indexing statistics
- `/index clear` - Delete the current index
- `/index refresh` - Re-index the last path
- `/csearch <query>` - Test semantic code search directly
- `/web on/off` - Enable/disable web search tool
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
│ Model:        codellama:34b                      │
│ Session:      3c8a9f2d-4b1e...                   │
│ Messages:     4                                  │
│ Tools:        file_operations, code_executor,    │
│               web_search, codebase_search        │
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

**✅ Phase 0: Infrastructure** (Complete)
- Core configuration system with validation
- Rich-integrated logging with color-coded levels
- 22 formatting helpers for consistent CLI output
- All infrastructure tests passing

**✅ Phase 1: Model Manager** (Complete)
- Full Ollama integration with CodeLlama 34B/13B/7B
- Streaming and non-streaming generation
- Chat with message history
- Model switching without restart
- Comprehensive error handling
- All 9 tests passing

**✅ Phase 2: Conversation Manager** (Complete)
- Thread-safe message storage
- Context window management with auto-trimming
- Conversation persistence (save/load)
- UUID-based session management
- LangChain integration
- All 11 tests passing

**✅ Phase 3: Agent System** (Complete)
- LangGraph ReAct agent with StateGraph architecture
- Multi-step reasoning (Think → Act → Observe loop)
- Tool integration and orchestration
- Verbose mode for debugging
- Iteration limits and error handling
- 7/8 tests passing

**✅ Phase 4: File Operations Tool** (Complete)
- Safe file system operations (read/write/list)
- Path validation and security constraints
- Directory management
- JSON-based tool input routing
- All 13 tests passing

**✅ Phase 5: Interactive CLI** (Complete)
- Beautiful Rich-based terminal interface
- Real-time agent feedback display
- Command system with 10+ commands
- Syntax highlighting for code blocks
- Model switching and conversation management
- Graceful error handling and shutdown
- Working integration with all components

**✅ Phase 6: RAG & Advanced Tools** (Complete)
- Codebase indexer with AST-based parsing (Task 14)
- Semantic code search with FAISS vector store (Task 15)
- RAG agent integration with automatic tool selection (Task 19)
- CLI index management commands (/index, /csearch) (Task 20)
- Code execution tool with subprocess isolation
- Web search tool with DuckDuckGo integration
- All 30+ tests passing

**📋 Phase 7: Advanced Skills** (Future)
- Advanced coding skills (debugger integration, refactoring engine)
- Test generation and execution automation
- Multi-agent collaboration and planning
- Self-reflection and improvement loops

## Documentation

### User Guides
- [USAGE.md](USAGE.md) - Complete usage guide with examples and troubleshooting
- [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - One-page command cheat sheet
- [examples/](examples/) - Example queries and workflows

### Technical Documentation
- [ARCHITECTURE.md](ARCHITECTURE.md) - System design and extension guide
- [STATUS.md](STATUS.md) - Development status and features
- [INFRASTRUCTURE.md](INFRASTRUCTURE.md) - Configuration, logging, and formatting systems
- [MODEL_MANAGER.md](MODEL_MANAGER.md) - Complete Model Manager API and usage guide
- [CONVERSATION_MANAGER.md](CONVERSATION_MANAGER.md) - Conversation Manager API and persistence guide

## License

Personal project - use as you wish

## Author

Built with wisdom and action 🧠⚡
