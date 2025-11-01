# 🧠 Meton

**Local AI Coding Assistant** - Wisdom in Action (Metis + Ergon)

A fully local coding assistant powered by LangChain, LangGraph, and CodeLlama.
Everything runs on your hardware - no external API calls, no data leaving your machine.

## Features

- 🏠 **Fully Local** - All processing happens on your machine
- 🤖 **Intelligent Agent** - Uses ReAct pattern for multi-step reasoning
- 📁 **File Operations** - Read, write, and navigate your codebase
- 💬 **Conversation Memory** - Maintains context across interactions
- 🔀 **Multi-Model** - Switch between CodeLlama models easily
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
- `/exit, /quit, /q` - Exit Meton

### Example Session

```
You: Read the README.md file and summarize it

💭 THOUGHT: I need to read the README.md file first
🔧 ACTION: file_operations
📥 INPUT: {"action": "read", "path": "README.md"}

💬 Assistant:
The README describes Meton, a local AI coding assistant...

You: /status

╭─── Current Status ───────────────────────────────╮
│ Model:        codellama:34b                      │
│ Session:      3c8a9f2d-4b1e...                   │
│ Messages:     4                                  │
│ Tools:        file_operations                    │
╰──────────────────────────────────────────────────╯

You: /exit
👋 Goodbye!
```

## Architecture

```
CLI (Rich) → Agent (LangGraph) → Models (Ollama) → Tools
                                                     └─ File Operations
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

**📋 Phase 6: Advanced Features** (Future)
- Codebase RAG with FAISS
- Code execution tool
- Web search tool
- Advanced skills (debugger, refactoring, test generation)
- Multi-agent planning
- Self-reflection

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
