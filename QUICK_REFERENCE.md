# Meton Quick Reference

One-page cheat sheet for Meton commands and common operations.

---

## Launch

```bash
# CLI Mode
./meton # Using convenience script
python meton.py # Direct launch

# Web UI Mode
python launch_web.py # Gradio interface
python launch_web.py --share --port 8080 # With options
```

---

## Commands

| Command | Description |
|---------|-------------|
| `/help` or `/h` | Show all commands |
| `/status` | Show current session info |
| `/models` | List available models |
| `/model <name>` | Switch model (primary/fallback/quick) |
| `/param show` | Display all current parameters |
| `/param <name> <value>` | Set parameter value at runtime |
| `/param reset` | Reset parameters to config defaults |
| `/preset` | List available parameter presets |
| `/preset <name>` | Apply parameter preset |
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
| `/memory stats` | Show memory statistics |
| `/memory search <query>` | Search memories semantically |
| `/memory add <content>` | Manually add memory |
| `/memory export [json\|csv]` | Export memories to file |
| `/learn analyze` | Analyze sessions for patterns |
| `/learn insights` | Show generated insights |
| `/learn patterns` | Show detected patterns |
| `/learn summary` | Learning statistics |
| `/optimize profile` | Show performance profile |
| `/optimize cache stats` | Display cache statistics |
| `/optimize cache clear` | Clear all caches |
| `/optimize report` | Show optimization report |
| `/optimize benchmark` | Run performance benchmarks |
| `/optimize resources` | Show resource usage |
| `/exit` or `/quit` or `/q` | Exit Meton |

---

## Model Aliases

| Alias | Model | Use Case |
|-------|-------|----------|
| `primary` | qwen2.5:32b-instruct-q5_K_M | Best quality (~15s) |
| `fallback` | llama3.1:8b | Balanced (~7s) |
| `quick` | mistral:latest | Fastest (~3s) |

```bash
/model quick # Switch to fast model
/model primary # Switch to quality model
```

---

## Model Parameters

### Available Parameters (config.yaml)

**Core:**
- `temperature` (0.0-2.0) - Randomness (0 = deterministic)
- `max_tokens` (int) - Max generation length
- `top_p` (0.0-1.0) - Nucleus sampling
- `num_ctx` (int) - Context window size

**Advanced Sampling:**
- `top_k` (int) - Token diversity (0 = disabled)
- `min_p` (0.0-1.0) - Adaptive filtering

**Repetition Control:**
- `repeat_penalty` (0.0-2.0) - Penalize repetition (1.0 = off)
- `repeat_last_n` (int) - Repetition window
- `presence_penalty` (-2.0 to 2.0) - Penalize used tokens
- `frequency_penalty` (-2.0 to 2.0) - Penalize common tokens

**Mirostat (alternative sampling):**
- `mirostat` (0/1/2) - Mode (0 = off)
- `mirostat_tau` (float) - Target entropy (5.0)
- `mirostat_eta` (0.0-1.0) - Learning rate (0.1)

**Reproducibility:**
- `seed` (int) - Random seed (-1 = random)

### Parameter Presets

```yaml
# Precise coding (deterministic)
temperature: 0.0
top_k: 40
repeat_penalty: 1.1
seed: -1

# Creative coding (exploratory)
temperature: 0.7
top_p: 0.95
min_p: 0.05
repeat_penalty: 1.2

# Debugging (consistent)
temperature: 0.2
mirostat: 2
mirostat_tau: 4.0
repeat_penalty: 1.15

# Reproducible (testing)
temperature: 0.0
seed: 42
top_k: 40
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
/index /path/to/project # Index first
How does authentication work? # Natural language query
Find database connection code
Show me error handling patterns
Where is user input validated?
/csearch authentication # Direct search test
```

### Code Execution

```
Run this code: print(2 + 2)
Execute: import math; print(math.pi)
Calculate fibonacci of 10
```

### Web Search

```
/web on # Enable first
Search for Python asyncio best practices
Find FAISS documentation
```

### Long-Term Memory

```
/memory stats # View statistics
/memory search authentication # Search memories
/memory add I prefer type hints # Add manual memory
/memory export json # Export to file
```

### Cross-Session Learning

```
/learn analyze # Analyze for patterns
/learn insights # View insights
/learn patterns # Show detected patterns
/learn apply insight_123 # Apply insight
/learn summary # Statistics
```

### Parameter Tuning (Phase 2)

```
/param show # View all current parameters
/preset creative # Apply creative preset
/param temperature 0.5 # Fine-tune specific parameter
/preset debugging # Switch to debugging mode
/param reset # Reset to config defaults
```

**Available Presets:**
- `precise` - Deterministic output (temp=0.0)
- `creative` - Exploratory coding (temp=0.7)
- `balanced` - Balanced approach (temp=0.3)
- `debugging` - Methodical debugging (temp=0.2, mirostat=2)
- `explanation` - Clear explanations (temp=0.5)

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

### Parameter Tuning

```
1. /param show
2. /preset creative
3. Ask exploratory questions
4. /param temperature 0.3
5. /param reset
```

### Memory & Learning

```
1. /memory stats
2. /learn analyze
3. /learn insights
4. /learn apply <id>
5. /memory export json
```

### Web UI Workflow

```
1. python launch_web.py
2. Open http://localhost:7860
3. Chat, upload files, view analytics
4. Export session data
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
 primary: "deepseek-coder:33b"

# Adjust sampling parameters
models:
 settings:
  temperature: 0.7      # More creative (0.0 = deterministic)
  top_k: 40            # Sampling diversity
  min_p: 0.1           # Adaptive filtering
  repeat_penalty: 1.1  # Reduce repetition
  mirostat: 0          # Alternative sampling (0/1/2)
  seed: 42             # Reproducible output (-1 = random)

# Add allowed path
tools:
 file_ops:
  allowed_paths:
   - /your/project/path

# Change context window
conversation:
 max_history: 20 # default: 10
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
├── config.yaml # Configuration
├── logs/ # Daily log files
├── conversations/ # Saved conversations
├── memory/ # Long-term memory storage
├── analytics_data/ # Performance analytics
├── web_sessions/ # Web UI session data
├── venv/ # Python environment
└── meton # Convenience launcher
```

---

## Status Output

```
╭─── Current Status ────────────────────╮
│ Model: qwen2.5:32b-instruct... │ ← Active model
│ Session: 3c8a9f2d... │ ← Current session ID
│ Messages: 12 │ ← Conversation length
│ Tools: file_operations │ ← Available tools
│ Max Iter: 10 │ ← Loop limit
│ Verbose: OFF │ ← Debug mode
╰───────────────────────────────────────╯
```

---

## Verbose Mode Output

```
 THOUGHT: I need to list the directory
 ACTION: file_operations
 INPUT: {"action": "list", "path": "/path"}
 Executing: file_operations
OK Result: [files listed]
```

---

## Best Practices

1. **Start broad `What files can you see?`
2. **Check status `/status` to confirm context
3. **Search first `/search keyword` or `/memory search` before re-asking
4. **Save work `/save` after important findings
5. **Clear context `/clear` when changing topics
6. **Use verbose `/verbose on` to understand agent
7. **Choose model `quick` for testing, `primary` for quality
8. **Build memory Regular use builds cross-session intelligence
9. **Monitor learning `/learn summary` to see patterns
10. **Use Web UI `python launch_web.py` for visual analytics

---

## Example Session

```
$ ./meton

 METON - Local Coding Assistant
Model: qwen2.5:32b-instruct-q5_K_M
Tools: file_operations, codebase_search

You: What files can you see?
 Assistant: I can see 16 files...

You: /memory search testing
 Found 2 memories about testing patterns

You: /learn summary
Total Patterns: 5 | Learning Velocity: 1.2/week

You: /model quick
OK Switched to model: mistral:latest

You: quick test query
 Assistant: [faster response]

You: /save
OK Conversation saved

You: /exit
 Goodbye!
```

---

## Getting Help

- In-session `/help`
- Usage Guide See [USAGE.md](USAGE.md)
- Architecture See [ARCHITECTURE.md](ARCHITECTURE.md)
- Project Status See [STATUS.md](STATUS.md)

---

Quick Start: `./meton` -> `/help` -> Ask questions!

Pro Tip: Use `/verbose on` when learning how Meton thinks.

---

*Meton - Wisdom in Action* 
