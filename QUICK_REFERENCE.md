# Meton Quick Reference

One-page cheat sheet for Meton commands and common operations.

---

## Launch

```bash
./meton                    # Using convenience script
python meton.py            # Direct launch
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` or `/h` | Show all commands |
| `/status` | Show current session info |
| `/models` | List available models |
| `/model <name>` | Switch model (primary/fallback/quick) |
| `/tools` | List available tools with status |
| `/verbose on\|off` | Toggle verbose mode |
| `/history` | Show conversation history |
| `/search <keyword>` | Search conversation history |
| `/clear` or `/c` | Clear conversation |
| `/save` | Save conversation |
| `/reload` | Reload configuration |
| `/index [path]` | Index codebase for semantic search |
| `/index status` | Show indexing statistics |
| `/index clear` | Delete current index |
| `/index refresh` | Re-index last path |
| `/csearch <query>` | Test semantic code search |
| `/web on\|off\|status` | Control web search tool |
| `/exit` or `/quit` or `/q` | Exit Meton |

---

## Model Aliases

| Alias | Model | Use Case |
|-------|-------|----------|
| `primary` | codellama:34b | Best quality (~15s) |
| `fallback` | codellama:13b | Balanced (~7s) |
| `quick` | codellama:7b | Fastest (~3s) |

```bash
/model quick        # Switch to fast model
/model primary      # Switch to quality model
```

---

## Common Queries

### File Operations

```
What files can you see?
List files in core/
Read config.yaml
Show me core/agent.py
Check if setup.sh exists
How big is README.md?
```

### Code Understanding

```
Explain the agent loop detection
What does ModelManager do?
Describe the file operations tool
Where is Config defined?
Find error handling in agent.py
```

### Semantic Code Search (with /index)

```
/index /path/to/project                    # Index first
How does authentication work?              # Natural language query
Find database connection code
Show me error handling patterns
Where is user input validated?
/csearch authentication                    # Direct search test
```

### Code Execution

```
Run this code: print(2 + 2)
Execute: import math; print(math.pi)
Calculate fibonacci of 10
```

### Web Search

```
/web on                                    # Enable first
Search for Python asyncio best practices
Find FAISS documentation
```

### Multi-Step

```
List Python files, read agent.py, explain ReAct pattern
Find all classes in core/ and describe each one
Read config.yaml and explain the settings
```

---

## Workflow Patterns

### Exploring Codebase

```
1. What files can you see?
2. Tell me about core/
3. Read core/agent.py
4. Explain the loop detection
5. /save
```

### Debugging

```
1. /verbose on
2. Read the error log
3. Find the function that failed
4. Explain what might be wrong
5. /verbose off
```

### Quick Testing

```
1. /model quick
2. Test some queries
3. /model primary
4. Get detailed answer
```

---

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `Ctrl+C` | Interrupt query (use `/exit` to quit) |
| `Ctrl+D` | Exit Meton |
| `↑` `↓` | Command history (if supported) |

---

## Configuration Quick Edit

```bash
# Edit config
nano config.yaml

# In Meton
/reload
```

### Common Config Changes

```yaml
# Change primary model
models:
  primary_model: "deepseek-coder:33b"

# Add allowed path
tools:
  file_ops:
    allowed_paths:
      - /your/project/path

# Change context window
conversation:
  max_history: 20  # default: 10
```

---

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Slow responses | `/model quick` |
| Agent loops | Loop detection handles it automatically |
| Can't find file | Check `/status` for working directory |
| Wrong answers | `/verbose on` to see reasoning |
| Config not updating | `/reload` |

---

## File Locations

```
meton/
├── config.yaml              # Configuration
├── logs/                    # Daily log files
├── conversations/           # Saved conversations
├── venv/                    # Python environment
└── meton                    # Convenience launcher
```

---

## Status Output

```
╭─── Current Status ────────────────────╮
│ Model:        codellama:34b           │  ← Active model
│ Session:      3c8a9f2d...             │  ← Current session ID
│ Messages:     12                      │  ← Conversation length
│ Tools:        file_operations         │  ← Available tools
│ Max Iter:     10                      │  ← Loop limit
│ Verbose:      OFF                     │  ← Debug mode
╰───────────────────────────────────────╯
```

---

## Verbose Mode Output

```
💭 THOUGHT: I need to list the directory
🎯 ACTION: file_operations
📥 INPUT: {"action": "list", "path": "/path"}
🔧 Executing: file_operations
✓ Result: [files listed]
```

---

## Best Practices

1. **Start broad**: `What files can you see?`
2. **Check status**: `/status` to confirm context
3. **Search first**: `/search keyword` before re-asking
4. **Save work**: `/save` after important findings
5. **Clear context**: `/clear` when changing topics
6. **Use verbose**: `/verbose on` to understand agent
7. **Choose model**: `quick` for testing, `primary` for quality

---

## Example Session

```
$ ./meton

🧠 METON - Local Coding Assistant
Model: codellama:34b
Tools: file_operations

You: What files can you see?
💬 Assistant: I can see 16 files...

You: /search agent
Search Results for 'agent' (3 matches)
2. ASSISTANT: ...agent system...

You: /model quick
✓ Switched to model: codellama:7b

You: quick test query
💬 Assistant: [faster response]

You: /save
✓ Conversation saved

You: /exit
👋 Goodbye!
```

---

## Getting Help

- **In-session**: `/help`
- **Usage Guide**: See [USAGE.md](USAGE.md)
- **Architecture**: See [ARCHITECTURE.md](ARCHITECTURE.md)
- **Project Status**: See [STATUS.md](STATUS.md)

---

**Quick Start:** `./meton` → `/help` → Ask questions!

**Pro Tip:** Use `/verbose on` when learning how Meton thinks.

---

*Meton - Wisdom in Action* 🧠⚡
