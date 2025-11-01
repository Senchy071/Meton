# Meton Architecture

System design documentation for the Meton local AI coding assistant.

---

## System Overview

```
┌──────────────────────────────────────────────────────────┐
│                    User Interface (CLI)                  │
│              Rich Console + Interactive Prompt           │
└────────────────────┬─────────────────────────────────────┘
                     │
       ┌─────────────┴─────────────┐
       │                           │
┌──────▼───────┐          ┌────────▼────────┐
│  Agent Core  │◄─────────┤  Conversation   │
│  (LangGraph) │          │    Manager      │
└──────┬───────┘          └─────────────────┘
       │                           ▲
       │ uses                      │ stores
       │                           │
┌──────▼───────┐          ┌────────┴────────┐
│    Tools     │          │   Persistence   │
│ (File Ops)   │          │  (JSON Files)   │
└──────┬───────┘          └─────────────────┘
       │
┌──────▼───────┐          ┌─────────────────┐
│ Model Manager│◄─────────┤  Configuration  │
│   (Ollama)   │          │   (YAML/Pydantic)│
└──────┬───────┘          └─────────────────┘
       │
┌──────▼───────┐
│   CodeLlama  │
│  (Local LLM) │
└──────────────┘
```

---

## Component Details

### 1. CLI Layer (`cli.py`)

**Purpose:** User-facing interactive interface

**Key Features:**
- Rich console formatting
- 12 interactive commands
- Real-time agent feedback
- Syntax highlighting
- Error handling
- Signal handlers (Ctrl+C)

**Main Class:** `MetonCLI`

**Initialization Flow:**
1. Create Config instance
2. Initialize ModelManager
3. Initialize ConversationManager
4. Create FileOperationsTool
5. Initialize MetonAgent with all components
6. Display welcome banner
7. Enter interactive loop

**Command Flow:**
```python
user_input → starts with '/' ?
    YES → handle_command() → execute command
    NO  → process_query() → agent.run() → display_response()
```

### 2. Configuration Layer (`core/config.py`)

**Purpose:** Type-safe configuration management

**Architecture:**
- Pydantic models for validation
- YAML file loading
- Nested configuration structure
- Default values

**Structure:**
```python
Config
├── models (ModelsConfig)
│   ├── primary_model
│   ├── fallback_model
│   ├── quick_model
│   └── settings (GenerationSettings)
├── conversation (ConversationConfig)
│   ├── max_history
│   └── auto_save
└── tools (ToolsConfig)
    └── file_ops (FileOpsConfig)
        ├── allowed_paths
        └── blocked_paths
```

**Usage:**
```python
config = Config()  # Loads config.yaml
model_name = config.config.models.primary_model
```

### 3. Model Manager (`core/models.py`)

**Purpose:** Ollama LLM integration

**Key Features:**
- Model listing and selection
- Model switching without restart
- LangChain compatibility
- Alias resolution (primary/fallback/quick)
- Streaming and non-streaming generation
- Chat with message history
- LLM instance caching

**Main Class:** `ModelManager`

**Important Methods:**
```python
list_available_models()     # Query Ollama
switch_model(name)          # Change active model
generate(prompt, stream)    # Simple generation
chat(messages)              # Chat with history
get_llm()                   # LangChain OllamaLLM instance
resolve_alias(alias)        # primary → codellama:34b
```

**Flow:**
```
Query → get_llm() → check cache
                    ↓
        cache miss? create OllamaLLM → cache → return
                    ↓
        cache hit?  return cached instance
```

### 4. Conversation Manager (`core/conversation.py`)

**Purpose:** Thread-safe conversation persistence

**Key Features:**
- UUID session IDs
- ISO 8601 timestamps
- Context window management (auto-trim)
- Thread-safe operations (`threading.Lock`)
- Auto-save functionality
- JSON serialization
- LangChain format compatibility

**Main Class:** `ConversationManager`

**Message Structure:**
```python
{
    "role": "user|assistant|system|tool",
    "content": "message text",
    "timestamp": "2025-10-28T10:30:00",
    "metadata": {...}
}
```

**Thread Safety:**
```python
def add_message(self, ...):
    with self._lock:              # Acquire lock
        self.messages.append(...)  # Modify
        if auto_save:
            self._save_internal()  # Save (lock already held)
```

**Context Window:**
- Preserves system messages
- Trims oldest user/assistant messages
- Keeps last N messages (configurable)

### 5. Agent System (`core/agent.py`)

**Purpose:** ReAct pattern orchestration with LangGraph

**Architecture:** LangGraph StateGraph with 3 nodes

```
┌─────────────────────────────────────────────┐
│         Agent State                         │
│  - messages                                 │
│  - thoughts                                 │
│  - tool_calls                               │
│  - iteration                                │
│  - finished                                 │
│  - final_answer                             │
└────────────┬────────────────────────────────┘
             │
    START────┼───► Reasoning Node
             │         │
             │         ▼
             │    Parse Output
             │    (THOUGHT/ACTION/ANSWER)
             │         │
             │         ├──► has tool call?
             │         │         │
             │         │    YES  ▼
             │         │    Tool Execution Node
             │         │         │
             │         │         ▼
             │         │    Execute Tool
             │         │         │
             │         │         ▼
             │         │    Update State
             │         │         │
             │         │         └──► Loop back to Reasoning
             │         │
             │         │    NO
             │         └─────► END (has answer)
             │
             └──► Max iterations? → END
```

**Key Features:**
- Multi-step reasoning (Think → Act → Observe)
- Tool integration via tool_map
- **Loop Detection System**
- Iteration limits
- Verbose mode for debugging
- Path context injection
- Structured output parsing

**Loop Detection:**
```python
# Detects when agent tries same tool with same input
if (current_action == last_action and
    current_input == last_input):
    # Force completion with existing result
    state["finished"] = True
    state["final_answer"] = last_result
```

**System Prompt Structure:**
1. Path context (current working directory, allowed paths)
2. Available tools
3. Examples with complete flows
4. Critical rules (especially ANSWER rules)

### 6. Tools System (`tools/`)

**Base Tool:** `MetonBaseTool` (extends LangChain's `BaseTool`)

**File Operations Tool** (`tools/file_ops.py`):

**Actions:**
- `read` - Read file contents
- `write` - Write to file
- `list` - List directory
- `create_dir` - Create directory
- `exists` - Check existence
- `get_info` - File metadata

**Security:**
```python
1. Path resolution (prevent ../.. attacks)
2. Blocked paths check (/etc/, /sys/, /proc/)
3. Allowed paths validation
4. File size limits
5. Binary file detection
```

**Usage:**
```json
{
    "action": "read",
    "path": "/media/development/projects/meton/config.yaml"
}
```

**Tool Registration:**
```python
# In Agent
self.tool_map = {tool.name: tool for tool in tools}

# LangGraph uses LangChain tools directly
# Agent parses ACTION and looks up tool in tool_map
```

---

## Data Flow

### Query Execution Flow

```
1. User enters query
   ↓
2. CLI.process_query()
   ↓
3. Agent.run(query)
   ↓
4. Create initial state
   ↓
5. LangGraph StateGraph.invoke()
   │
   ├─► Reasoning Node
   │    ├─ Build prompt (system + context + query)
   │    ├─ Get LLM (via ModelManager)
   │    ├─ LLM.invoke(prompt)
   │    ├─ Parse output (THOUGHT/ACTION/INPUT/ANSWER)
   │    └─ Update state
   │
   ├─► Tool Execution Node (if needed)
   │    ├─ Get tool from tool_map
   │    ├─ Parse JSON input
   │    ├─ Execute tool
   │    └─ Store result in state
   │
   ├─► Loop Detection (if repeated)
   │    ├─ Compare with last call
   │    ├─ Force answer if duplicate
   │    └─ Break loop
   │
   └─► Repeat until:
        - Agent provides ANSWER
        - Max iterations reached
        - Error occurs
   ↓
6. Return result
   ↓
7. CLI.display_response()
   ├─ Parse code blocks
   ├─ Apply syntax highlighting
   └─ Display to user
```

### Configuration Reload Flow

```
1. User: /reload
   ↓
2. Create new Config()
   ↓
3. Update config references:
   ├─ self.config = new_config
   ├─ model_manager.config = new_config
   ├─ conversation.config = new_config
   └─ agent.config = new_config
   ↓
4. Next query uses new config
```

### Conversation Persistence Flow

```
On add_message():
├─ Acquire lock
├─ Append message
├─ Trim if over max_history
└─ Auto-save if enabled

On save():
├─ Acquire lock
├─ Serialize to JSON
├─ Write to conversations/<session_id>.json
└─ Release lock

On load():
├─ Read JSON file
├─ Deserialize messages
├─ Restore session_id
└─ Rebuild state
```

---

## Extension Guide

### Adding a New Tool

1. **Create tool class** (`tools/your_tool.py`):

```python
from tools.base import MetonBaseTool
from langchain.pydantic_v1 import Field

class YourTool(MetonBaseTool):
    """Tool description for LLM."""

    name: str = "your_tool"
    description: str = "What your tool does..."

    def __init__(self, config):
        super().__init__(config=config)

    def _run(self, input: str) -> str:
        """Execute tool logic."""
        # Parse input (usually JSON)
        # Perform action
        # Return result string
        return "result"
```

2. **Register in CLI** (`cli.py:initialize()`):

```python
from tools.your_tool import YourTool

# In initialize():
your_tool = YourTool(self.config)

self.agent = MetonAgent(
    config=self.config,
    model_manager=self.model_manager,
    conversation=self.conversation,
    tools=[file_tool, your_tool],  # Add here
    verbose=self.verbose
)
```

3. **Update config** (add to `config.yaml` if needed):

```yaml
tools:
  your_tool:
    enabled: true
    option1: value1
```

4. **Test:**
```bash
python meton.py
You: use your_tool to do something
```

### Adding a New Command

1. **Add to help** (`cli.py:display_help()`):

```python
table.add_row("/newcmd", "Description of command")
```

2. **Add handler** (`cli.py:handle_command()`):

```python
elif cmd == '/newcmd':
    if args:
        self.new_command_handler(args[0])
    else:
        self.console.print("[yellow]Usage: /newcmd <arg>[/yellow]")
```

3. **Implement method:**

```python
def new_command_handler(self, arg: str):
    """Handle /newcmd."""
    try:
        # Implementation
        self.console.print("[green]✓ Success[/green]")
    except Exception as e:
        self.console.print(f"[red]❌ Error: {e}[/red]")
```

### Adding a New Model Provider

Currently Ollama-only. To add OpenAI/Anthropic/etc:

1. **Extend ModelManager**:
```python
class MultiModelManager(ModelManager):
    def __init__(self, config, provider="ollama"):
        self.provider = provider
        if provider == "openai":
            # Initialize OpenAI client
        elif provider == "ollama":
            super().__init__(config)
```

2. **Update config schema**:
```yaml
models:
  provider: "ollama"  # or "openai", "anthropic"
  ollama:
    primary_model: "codellama:34b"
  openai:
    model: "gpt-4"
    api_key: "..."
```

3. **Update get_llm()**:
```python
def get_llm(self):
    if self.provider == "ollama":
        return OllamaLLM(...)
    elif self.provider == "openai":
        return ChatOpenAI(...)
```

---

## Performance Considerations

### Model Selection
- **34B models**: High quality, 8-16GB VRAM, 10-20s latency
- **13B models**: Balanced, 4-8GB VRAM, 5-10s latency
- **7B models**: Fast, 2-4GB VRAM, 2-5s latency

### Caching Strategy
- LLM instances cached per model
- Config loaded once at startup
- Tools instantiated once

### Concurrency
- Conversation operations are thread-safe
- Model manager is stateless (thread-safe)
- Agent runs are isolated (stateful but per-invocation)

### Memory Management
- Context window auto-trims
- Old tool results discarded after state update
- Conversation files written incrementally

---

## Security Model

### File Operations
1. Path resolution prevents traversal attacks
2. Blocked paths list (/etc, /sys, /proc)
3. Allow list enforcement
4. File size limits
5. Binary file rejection for read ops

### LLM Safety
- All operations local (no external API calls)
- No code execution by default
- Tool actions are explicit and validated

### Configuration
- Pydantic validation prevents injection
- YAML parsed safely
- No eval() or exec() usage

---

## Testing Strategy

### Unit Tests
- `test_infrastructure.py` - Config, Logger, Formatting
- `test_models.py` - Model Manager
- `test_conversation.py` - Conversation Manager
- `test_agent.py` - Agent System
- `test_file_ops.py` - File Operations

### Integration Testing
- CLI initialization
- End-to-end query flow
- Multi-step reasoning
- Tool execution

### Manual Testing Checklist
See final testing checklist in STATUS.md

---

## Future Architecture Enhancements

### Phase 2 Possibilities

1. **RAG Integration**
   - FAISS vector store
   - Codebase indexing
   - Semantic search tool

2. **Multi-Agent System**
   - Planner agent
   - Executor agents
   - Reviewer agent

3. **Code Execution**
   - Sandboxed Python execution
   - Test running
   - Linting integration

4. **Web Search Tool**
   - Documentation lookup
   - Stack Overflow search
   - GitHub API integration

5. **Advanced Conversation**
   - Named sessions
   - Session switching
   - Conversation branching

---

## Debugging Tips

### Enable Verbose Mode
```
/verbose on
```
Shows agent's thought process, actions, and tool results.

### Check Logs
```bash
tail -f logs/meton_<date>.log
```

### Inspect State
Add print statements in `core/agent.py:_reasoning_node()`:
```python
if self.verbose:
    print(f"State: {state}")
```

### Test Tool Directly
```python
from tools.file_ops import FileOperationsTool
from core.config import Config

config = Config()
tool = FileOperationsTool(config)
result = tool._run('{"action": "list", "path": "."}')
print(result)
```

### Test Agent Prompt
```python
from core.agent import MetonAgent
# Initialize agent...
prompt = agent._get_system_prompt()
print(prompt)  # See what agent sees
```

---

## Contributing Guidelines

When modifying Meton:

1. **Update tests** for changed components
2. **Update STATUS.md** with implementation details
3. **Update this ARCHITECTURE.md** if adding components
4. **Update USAGE.md** if adding user-facing features
5. **Run test suite** before committing:
   ```bash
   python test_infrastructure.py
   python test_models.py
   python test_conversation.py
   python test_agent.py
   python test_file_ops.py
   ```

---

## Architecture Decisions

### Why LangGraph?
- Explicit state management
- Visual graph structure
- Easy debugging
- Conditional edges for logic
- Industry standard

### Why Ollama?
- Fully local (privacy)
- Easy model management
- Good performance on consumer hardware
- Free and open source

### Why Pydantic?
- Type safety
- Validation at runtime
- Great IDE support
- Documentation generation

### Why Rich?
- Beautiful terminal UI
- Syntax highlighting
- Progress indicators
- Cross-platform

### Why Thread-Safe Conversation?
- Future-proofs for async operations
- Allows background auto-save
- Enables potential multi-threading

---

For usage instructions, see [USAGE.md](USAGE.md).
For project status, see [STATUS.md](STATUS.md).
For quick reference, see [QUICK_REFERENCE.md](QUICK_REFERENCE.md).
