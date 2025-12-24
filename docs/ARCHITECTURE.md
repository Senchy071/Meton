# Meton Architecture

System design documentation for the Meton local AI coding assistant.

---

## System Overview

```
┌──────────────────────────────────────────────────────────┐
│ User Interface (CLI) │
│ Rich Console + Interactive Prompt │
└────────────────────┬─────────────────────────────────────┘
 │
 ┌─────────────┴─────────────┐
 │ │
┌──────▼───────┐ ┌────────▼────────┐
│ Agent Core │◄─────────┤ Conversation │
│ (LangGraph) │ │ Manager │
└──────┬───────┘ └─────────────────┘
 │ ▲
 │ uses │ stores
 │ │
┌──────▼───────┐ ┌────────┴────────┐
│ Tools │ │ Persistence │
│ (File Ops) │ │ (JSON Files) │
└──────┬───────┘ └─────────────────┘
 │
┌──────▼───────┐ ┌─────────────────┐
│ Model Manager│◄─────────┤ Configuration │
│ (Ollama) │ │ (YAML/Pydantic)│
└──────┬───────┘ └─────────────────┘
 │
┌──────▼───────┐
│ CodeLlama │
│ (Local LLM) │
└──────────────┘
```

---

## Component Details

### 1. CLI Layer (`cli.py`)

Purpose: User-facing interactive interface

Key Features:
- Rich console formatting
- 12 interactive commands
- Real-time agent feedback
- Syntax highlighting
- Error handling
- Signal handlers (Ctrl+C)

Main Class: `MetonCLI`

Initialization Flow:
1. Create Config instance
2. Initialize ModelManager
3. Initialize ConversationManager
4. Create FileOperationsTool
5. Initialize MetonAgent with all components
6. Display welcome banner
7. Enter interactive loop

Command Flow:
```python
user_input -> starts with '/' ?
 YES -> handle_command() -> execute command
 NO -> process_query() -> agent.run() -> display_response()
```

### 2. Configuration Layer (`core/config.py`)

Purpose: Type-safe configuration management

Architecture:
- Pydantic models for validation
- YAML file loading
- Nested configuration structure
- Default values

Structure:
```python
Config
├── models (ModelsConfig)
│ ├── primary_model
│ ├── fallback_model
│ ├── quick_model
│ └── settings (GenerationSettings)
├── conversation (ConversationConfig)
│ ├── max_history
│ └── auto_save
└── tools (ToolsConfig)
 └── file_ops (FileOpsConfig)
 ├── allowed_paths
 └── blocked_paths
```

Usage:
```python
config = Config() # Loads config.yaml
model_name = config.config.models.primary_model
```

### 3. Model Manager (`core/models.py`)

Purpose: Ollama LLM integration

Key Features:
- Model listing and selection
- Model switching without restart
- LangChain compatibility
- Alias resolution (primary/fallback/quick)
- Streaming and non-streaming generation
- Chat with message history
- LLM instance caching

Main Class: `ModelManager`

Important Methods:
```python
list_available_models() # Query Ollama
switch_model(name) # Change active model
generate(prompt, stream) # Simple generation
chat(messages) # Chat with history
get_llm() # LangChain OllamaLLM instance
resolve_alias(alias) # primary -> codellama:34b
```

Flow:
```
Query -> get_llm() -> check cache
 ↓
 cache miss? create OllamaLLM -> cache -> return
 ↓
 cache hit? return cached instance
```

#### Model Parameters & Sampling Control

Meton exposes comprehensive sampling parameters for fine-grained control over LLM output quality:

**Core Parameters:**
- `temperature` (0.0-2.0): Randomness control (0 = deterministic, higher = more creative)
- `max_tokens` (int): Maximum generation length
- `top_p` (0.0-1.0): Nucleus sampling threshold
- `num_ctx` (int): Context window size

**Advanced Sampling:**
- `top_k` (int): Limits token candidates to top K (0 = disabled)
- `min_p` (0.0-1.0): Adaptive filtering, recommended over top_k for better quality

**Repetition Control:**
- `repeat_penalty` (0.0-2.0): Penalizes repetitive tokens (1.0 = disabled, 1.1 = light penalty)
- `repeat_last_n` (int): Window size for repetition analysis (-1 = ctx_size, 0 = disabled)
- `presence_penalty` (-2.0 to 2.0): Penalizes tokens that already appeared
- `frequency_penalty` (-2.0 to 2.0): Penalizes frequently used tokens

**Mirostat Sampling:**
- `mirostat` (0/1/2): Alternative sampling method for consistent perplexity
  - 0 = disabled (use top_k/top_p)
  - 1 = Mirostat v1
  - 2 = Mirostat v2 (recommended)
- `mirostat_tau` (float): Target entropy/perplexity (default: 5.0)
- `mirostat_eta` (0.0-1.0): Learning rate for perplexity control (default: 0.1)

**Reproducibility:**
- `seed` (int): Random seed for deterministic output (-1 = random)

These parameters are defined in `core/config.py` (ModelSettings Pydantic model), configured in `config.yaml`, and passed to Ollama via `core/models.py`.

Example configuration:
```yaml
models:
  settings:
    temperature: 0.0        # Deterministic
    top_k: 40              # Moderate diversity
    min_p: 0.1             # Adaptive filtering
    repeat_penalty: 1.1    # Light repetition penalty
    mirostat: 0            # Disabled (using top_k/top_p)
    seed: -1               # Random
```

#### Runtime Parameter Tuning (Phase 2)

Meton supports dynamic parameter modification without restart through CLI commands and parameter presets.

**CLI Commands:**
- `/param show` - Display all current parameters in organized table
- `/param <name> <value>` - Set individual parameter at runtime
- `/param reset` - Reset to config.yaml defaults
- `/preset` - List available presets
- `/preset <name>` - Apply preset configuration

**ModelManager Methods (core/models.py):**

```python
def update_parameter(param_name: str, value: Any) -> bool
    # Updates single parameter with type/range validation
    # Clears LLM cache to ensure new settings take effect

def get_current_parameters() -> Dict[str, Any]
    # Returns dictionary of all 14 current parameter values

def apply_preset(preset_name: str) -> bool
    # Applies predefined parameter preset
    # Available presets: precise, creative, balanced, debugging, explanation

def reset_parameters() -> bool
    # Reloads parameters from config.yaml
```

**Parameter Presets (core/config.py):**

Five predefined presets for common use cases:

1. **precise** - Deterministic output for precise coding tasks
   - `temperature: 0.0, top_k: 40, repeat_penalty: 1.1`

2. **creative** - More exploratory and creative coding
   - `temperature: 0.7, top_p: 0.95, repeat_penalty: 1.2`

3. **balanced** - Balanced between creativity and precision
   - `temperature: 0.3, top_k: 40, repeat_penalty: 1.15`

4. **debugging** - Consistent methodical debugging approach
   - `temperature: 0.2, mirostat: 2, top_k: 20`

5. **explanation** - Clear explanations with reduced repetition
   - `temperature: 0.5, repeat_penalty: 1.25, presence_penalty: 0.1`

**Implementation:**
- Presets defined as `ParameterPreset` Pydantic models in `PARAMETER_PRESETS` dict
- Runtime updates clear LLM cache (`_llm_cache.clear()`) to force recreation with new parameters
- Validation includes type checking (int/float) and range validation (min/max bounds)
- Changes are in-memory only; use `/param reset` to reload from config file

#### Fine-Tuning Workflow (Phase 3)

Meton supports using fine-tuned models created with llama.cpp and imported into Ollama.

**Workflow:**
1. **Prepare training data** - Use `utils/prepare_training_data.py` to extract from conversations
2. **Fine-tune with llama.cpp** - Create LoRA adapter from base GGUF model
3. **Create Ollama model** - Import using Modelfile template
4. **Use in Meton** - Switch with `/model` command or set as primary

**Components:**

**Training Data Preparation (`utils/prepare_training_data.py`):**
- Extracts user-assistant exchanges from conversation JSON files
- Filters by length, keyword, quality score
- Deduplicates similar exchanges
- Formats for llama.cpp training (Llama-2, Alpaca, ChatML)
- Supports quality thresholds and keyword filtering

**Modelfile Templates (`templates/modelfiles/`):**
- `basic.Modelfile` - General-purpose template
- `python-specialist.Modelfile` - Python development focus
- `fastapi-expert.Modelfile` - FastAPI/web development
- `langchain-expert.Modelfile` - LangChain/LangGraph agents
- `explainer.Modelfile` - Code explanation and teaching

**Example Training Data (`examples/training_data/`):**
- Python coding examples with best practices
- Code explanation examples for teaching
- Demonstrates proper format and style

**Documentation (`docs/FINE_TUNING.md`):**
- Complete guide to fine-tuning workflow
- llama.cpp setup and usage
- Training data preparation strategies
- Modelfile customization
- Troubleshooting and best practices
- Example workflows for different use cases

**Typical Fine-Tuning Process:**

1. Collect training data:
   ```bash
   python utils/prepare_training_data.py \
       --conversations-dir ./conversations \
       --output training_data.txt \
       --min-length 100 \
       --deduplicate
   ```

2. Fine-tune with llama.cpp:
   ```bash
   cd /path/to/llama.cpp
   ./finetune \
       --model-base codellama-13b.gguf \
       --lora-out meton-custom-lora.gguf \
       --train-data training_data.txt \
       --epochs 3
   ```

3. Export full model:
   ```bash
   ./export-lora \
       --model-base codellama-13b.gguf \
       --lora meton-custom-lora.gguf \
       --model-out meton-custom-13b.gguf
   ```

4. Create Ollama model:
   ```bash
   ollama create meton-custom -f templates/modelfiles/basic.Modelfile
   ```

5. Use in Meton:
   ```bash
   ./meton.py
   > /model meton-custom
   ```

**Benefits:**
- Specialize models for specific domains
- Learn your coding style and preferences
- Improve performance on frequent tasks
- Maintain full local control (no cloud fine-tuning services)

See `docs/FINE_TUNING.md` for complete documentation.

#### Parameter Profiles (Phase 4)

Phase 4 adds user-customizable parameter profiles that can be saved, loaded, and shared. Unlike Phase 2 presets (which are hardcoded), profiles are persistent and fully customizable.

**Key Differences from Presets:**
- **Presets** (Phase 2): Hardcoded in `core/config.py`, cannot be modified at runtime
- **Profiles** (Phase 4): Stored in `config.yaml`, can be created/modified/deleted by users

**Implementation:**

**Configuration (`core/config.py`):**
- `ParameterProfile` class with validation
- Validates parameter names and types
- Stored as `Dict[str, ParameterProfile]` in config
- Automatically persisted to `config.yaml`

**Model Manager Methods (`core/models.py`):**
- `list_profiles()` - List all available profiles
- `get_profile(name)` - Get specific profile details
- `apply_profile(name)` - Apply profile settings
- `create_profile(name, description, settings)` - Create new profile
- `delete_profile(name)` - Remove profile
- `export_profile(name, path)` - Export to JSON file
- `import_profile(path)` - Import from JSON file

**CLI Commands:**
- `/pprofile` - List all parameter profiles
- `/pprofile apply <name>` - Apply a profile
- `/pprofile show <name>` - Show profile details
- `/pprofile create <name>` - Create new profile (interactive)
- `/pprofile delete <name>` - Delete a profile
- `/pprofile export <name> [path]` - Export profile to JSON
- `/pprofile import <path>` - Import profile from JSON

**Default Profiles (in `config.yaml`):**
- `creative_coding` - High temperature (0.7) for exploratory coding
- `precise_coding` - Deterministic (0.0) with mirostat for precision
- `debugging` - Low temperature (0.2) for methodical analysis
- `explanation` - Moderate temperature (0.5) for clear explanations

**Example Workflow:**

1. List available profiles:
   ```bash
   > /pprofile
   ```

2. Apply a profile:
   ```bash
   > /pprofile apply creative_coding
   ```

3. Create custom profile:
   ```bash
   > /pprofile create my_profile
   Description: Custom settings for API development
   temperature [0.0]: 0.3
   top_p [0.9]: 0.95
   repeat_penalty [1.1]: 1.15
   ...
   ```

4. Export for sharing:
   ```bash
   > /pprofile export my_profile ./my_settings.json
   ```

5. Import on another machine:
   ```bash
   > /pprofile import ./my_settings.json
   ```

**Use Cases:**
- **Project-specific settings** - Different profiles for different projects
- **Task-specific tuning** - Debugging vs feature development vs documentation
- **Team sharing** - Export/import profiles to standardize settings across team
- **A/B testing** - Compare different parameter combinations
- **Experimentation** - Save working configurations for later reuse

**Profile Storage:**

Profiles are stored in `config.yaml` under `parameter_profiles`:

```yaml
parameter_profiles:
  my_custom_profile:
    name: my_custom_profile
    description: Custom settings for API development
    settings:
      temperature: 0.3
      top_p: 0.95
      repeat_penalty: 1.15
      mirostat: 0
```

**Benefits:**
- Persistent configuration across sessions
- Share settings with team members
- Quick switching between tested configurations
- Experiment without fear of losing settings
- Build a library of profiles for different scenarios

### 4. Conversation Manager (`core/conversation.py`)

Purpose: Thread-safe conversation persistence

Key Features:
- UUID session IDs
- ISO 8601 timestamps
- Context window management (auto-trim)
- Thread-safe operations (`threading.Lock`)
- Auto-save functionality
- JSON serialization
- LangChain format compatibility

Main Class: `ConversationManager`

Message Structure:
```python
{
 "role": "user|assistant|system|tool",
 "content": "message text",
 "timestamp": "2025-10-28T10:30:00",
 "metadata": {...}
}
```

Thread Safety:
```python
def add_message(self, ...):
 with self._lock: # Acquire lock
 self.messages.append(...) # Modify
 if auto_save:
 self._save_internal() # Save (lock already held)
```

Context Window:
- Preserves system messages
- Trims oldest user/assistant messages
- Keeps last N messages (configurable)

### 5. Agent System (`core/agent.py`)

Purpose: ReAct pattern orchestration with LangGraph

Architecture: LangGraph StateGraph with 3 nodes

```
┌─────────────────────────────────────────────┐
│ Agent State │
│ - messages │
│ - thoughts │
│ - tool_calls │
│ - iteration │
│ - finished │
│ - final_answer │
└────────────┬────────────────────────────────┘
 │
 START────┼─── Reasoning Node
 │ │
 │ ▼
 │ Parse Output
 │ (THOUGHT/ACTION/ANSWER)
 │ │
 │ ├── has tool call?
 │ │ │
 │ │ YES ▼
 │ │ Tool Execution Node
 │ │ │
 │ │ ▼
 │ │ Execute Tool
 │ │ │
 │ │ ▼
 │ │ Update State
 │ │ │
 │ │ └── Loop back to Reasoning
 │ │
 │ │ NO
 │ └───── END (has answer)
 │
 └── Max iterations? -> END
```

Key Features:
- Multi-step reasoning (Think -> Act -> Observe)
- Tool integration via tool_map
- Loop Detection System
- Iteration limits
- Verbose mode for debugging
- Path context injection
- Structured output parsing

Loop Detection:
```python
# Detects when agent tries same tool with same input
if (current_action == last_action and
 current_input == last_input):
 # Force completion with existing result
 state["finished"] = True
 state["final_answer"] = last_result
```

System Prompt Structure:
1. Path context (current working directory, allowed paths)
2. Available tools
3. Examples with complete flows
4. Critical rules (especially ANSWER rules)
5. Multi-part question handling rules (comparison questions, usage guidance)
6. Answer completeness validation checklist

### 6. Tools System (`tools/`)

Base Tool: `MetonBaseTool` (extends LangChain's `BaseTool`)

File Operations Tool (`tools/file_ops.py`):

Actions:
- `read` - Read file contents
- `write` - Write to file
- `list` - List directory
- `create_dir` - Create directory
- `exists` - Check existence
- `get_info` - File metadata

Security:
```python
1. Path resolution (prevent ../.. attacks)
2. Blocked paths check (/etc/, /sys/, /proc/)
3. Allowed paths validation
4. File size limits
5. Binary file detection
```

Usage:
```json
{
 "action": "read",
 "path": "/media/development/projects/meton/config.yaml"
}
```

Tool Registration:
```python
# In Agent
self.tool_map = {tool.name: tool for tool in tools}

# LangGraph uses LangChain tools directly
# Agent parses ACTION and looks up tool in tool_map
```

Code Executor Tool (`tools/code_executor.py`):

Features:
- Subprocess isolation for safety
- AST-based import validation (27 allowed, 36 blocked)
- Timeout protection (5 seconds default)
- Output capture (stdout + stderr)
- Execution time tracking

Web Search Tool (`tools/web_search.py`):

Features:
- DuckDuckGo integration (no API key needed)
- Disabled by default (explicit opt-in required)
- Configurable max results (1-20)
- Timeout protection
- Runtime enable/disable via `/web on/off`

Codebase Search Tool (`tools/codebase_search.py`):

Features:
- Semantic code search using RAG
- Natural language queries
- Returns ranked results with similarity scores
- Lazy-loads indexer for performance
- Configurable top_k, similarity_threshold, max_code_length

Symbol Lookup Tool (`tools/symbol_lookup.py`):

Features:
- Fast exact symbol definition lookup (functions, classes, methods)
- AST-based parsing using CodeParser
- In-memory indexing with 60-second cache
- Returns file path, line number, signature, docstring, code snippet
- Filtering by symbol type (function/class/method) and scope (public/private)
- Configurable max_results, context_lines
- Enabled by default

Usage:
```json
{
  "symbol": "MetonAgent",
  "type": "class"  // Optional: "function", "class", "method", "all"
}
```

CLI Command:
```bash
/find MetonAgent          # Find any symbol
/find _run type:method    # Find methods only
```

Implementation Details:
- Uses importlib to load CodeParser directly (avoids rag/__init__.py dependency issues)
- Builds symbol index on first use (walks Python files, parses AST)
- Index refreshes automatically after 60 seconds
- Returns public/private scope based on naming conventions (_prefix)
- Case-insensitive fallback for fuzzy matching

Import Graph Analyzer Tool (`tools/import_graph.py`):

Features:
- Analyzes import dependencies in Python codebases using grimp library
- Detects circular dependencies (cycles) between modules
- Calculates coupling metrics (density, fan-in, fan-out)
- Identifies orphan modules (not imported by anything)
- Generates Mermaid diagrams and text visualizations
- Uses NetworkX for graph analysis algorithms
- Enabled by default

Usage:
```json
{
  "path": "core",                  // Required: package to analyze
  "include_external": false,       // Optional: include external packages
  "output_format": "mermaid",      // Optional: "mermaid" or "text"
  "max_nodes": 50                  // Optional: max nodes in visualization
}
```

Output:
- Graph structure (modules and edges)
- Circular dependencies with severity classification
- Metrics: coupling coefficient, fan-in, fan-out, orphan count
- Mermaid diagram or text tree visualization

Implementation Details:
- Built on grimp library (battle-tested, powers import-linter)
- NetworkX integration for cycle detection (`simple_cycles()`)
- Module classification (internal/external/stdlib)
- Smart visualization limiting for large graphs
- Cycle highlighting in Mermaid diagrams

---

## Skills System (`skills/`)

Purpose: High-level coding capabilities with both Python and Markdown implementations

Architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                      SkillManager                           │
│   (Orchestrates Python and Markdown skill discovery)        │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┴─────────────┐
        │                           │
┌───────▼───────┐         ┌─────────▼─────────┐
│ Python Skills │         │  Markdown Skills  │
│ (BaseSkill)   │         │ (MarkdownSkill)   │
└───────────────┘         └───────────────────┘
        │                           │
        │                 ┌─────────▼─────────┐
        │                 │MarkdownSkillLoader│
        │                 │  (YAML parsing)   │
        │                 └───────────────────┘
        │                           │
        └───────────┬───────────────┘
                    │
        ┌───────────▼───────────────┐
        │    Skill Execution        │
        │  (via Agent + Tools)      │
        └───────────────────────────┘
```

### Python Skills (`skills/*.py`)

Traditional skill implementation using Python classes.

Key Classes:
- `BaseSkill`: Abstract base class with `execute()` method
- `SkillManager`: Loads and manages all skills

Example Skills:
- `CodeExplainerSkill`: Complexity analysis and explanation
- `DebuggerSkill`: Error analysis and fix suggestions
- `RefactoringEngineSkill`: Code smell detection and refactoring

### Markdown Skills (`skills/md_skills/`)

Claude Code-style skills defined in markdown with YAML frontmatter.

File Structure:
```
skills/md_skills/
├── code-reviewer/
│   └── SKILL.md
├── code-explainer/
│   └── SKILL.md
└── debugger/
    └── SKILL.md
```

Skill Definition Format:
```yaml
---
name: code-reviewer
description: Review code for quality, security, and best practices
allowed-tools: Read, Grep, Glob
model: primary
version: 1.0.0
---

# Skill Instructions

Detailed instructions for the skill behavior...
```

Key Classes (`skills/markdown_skill.py`):
- `MarkdownSkill`: Dataclass holding parsed skill data
- `MarkdownSkillLoader`: Discovers and loads markdown skills

Discovery Precedence:
1. Project: `.meton/skills/` - Project-specific skills
2. User: `~/.meton/skills/` - User-wide skills
3. Built-in: `skills/md_skills/` - Default skills

Features:
- YAML frontmatter for metadata (name, description, tools, model)
- Tool restrictions per skill
- Model selection (primary, fallback, quick)
- Hot-reload via `/skill reload <name>`

---

## Sub-Agents System (`agents/`)

Purpose: Autonomous specialized agents with isolated execution context

Architecture:

```
┌─────────────────────────────────────────────────────────────┐
│                    SubAgentManager                          │
│        (High-level agent management and execution)          │
└─────────────────────┬───────────────────────────────────────┘
                      │
        ┌─────────────┼─────────────┐
        │             │             │
┌───────▼───────┐ ┌───▼───┐ ┌───────▼───────┐
│SubAgentLoader │ │Spawner│ │ Result Store  │
│(Discovery)    │ │       │ │ (History)     │
└───────────────┘ └───┬───┘ └───────────────┘
                      │
              ┌───────▼───────┐
              │ SubAgent      │
              │ (Isolated)    │
              │ - Own context │
              │ - Tool subset │
              │ - Own model   │
              └───────────────┘
```

### SubAgent Definition (`agents/builtin/*.md`)

Markdown files with YAML frontmatter defining agent behavior.

Example Agent Definition:
```yaml
---
name: explorer
description: Fast codebase exploration agent
tools: file_operations, codebase_search, symbol_lookup
model: quick
---

# Explorer Agent

You are a fast codebase exploration specialist...
```

### Key Classes

**`SubAgent`** (`agents/subagent.py`):
```python
@dataclass
class SubAgent:
    name: str
    description: str
    system_prompt: str
    tools: Optional[List[str]] = None
    model: str = "inherit"
    enabled: bool = True
    source_path: Optional[Path] = None
```

**`SubAgentLoader`** (`agents/subagent_loader.py`):
- Discovers agents from multiple directories
- Parses YAML frontmatter
- Validates agent definitions

**`SubAgentSpawner`** (`agents/subagent_spawner.py`):
- Creates isolated agent instances
- Manages separate conversation context
- Handles tool restrictions
- Captures execution results

**`SubAgentManager`** (`agents/subagent_spawner.py`):
- High-level API for agent management
- Execution history tracking
- Discovery refresh

### Built-in Agents

| Agent | Model | Tools | Purpose |
|-------|-------|-------|---------|
| `explorer` | quick | file_ops, search, symbol | Fast read-only exploration |
| `planner` | primary | file_ops, search, symbol, import | Implementation planning |
| `code-reviewer` | primary | file_ops, search, symbol | Code review |
| `debugger` | primary | file_ops, search, symbol, executor | Error analysis |

### Discovery Precedence

1. Project: `.meton/agents/` - Project-specific agents
2. User: `~/.meton/agents/` - User-wide agents
3. Built-in: `agents/builtin/` - Default agents

### Execution Flow

```
/agent run <name> <task>
        │
        ▼
┌───────────────────┐
│ SubAgentManager   │
│ .run_agent()      │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ SubAgentSpawner   │
│ .spawn()          │
│ - Create context  │
│ - Filter tools    │
│ - Select model    │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ MetonAgent        │
│ (Isolated)        │
│ .run(task)        │
└─────────┬─────────┘
          │
          ▼
┌───────────────────┐
│ SubAgentResult    │
│ - success         │
│ - result          │
│ - execution_time  │
│ - iterations      │
└───────────────────┘
```

---

## RAG System (`rag/`)

Purpose: Semantic code understanding via vector embeddings and retrieval

Architecture:

```
┌──────────────────────────────────────────────────┐
│ Indexing Pipeline │
└──────────────────────────────────────────────────┘
 │
 Python Files ─────┤
 │
 ┌────────────▼────────────┐
 │ CodeParser (AST) │
 │ - Parse Python files │
 │ - Extract functions │
 │ - Extract classes │
 │ - Extract imports │
 │ - Capture docstrings │
 └────────────┬────────────┘
 │
 ┌────────────▼────────────┐
 │ CodeChunker │
 │ - 1 chunk per function │
 │ - 1 chunk per class │
 │ - 1 chunk for imports │
 │ - 1 chunk for module │
 └────────────┬────────────┘
 │
 ┌────────────▼────────────┐
 │ EmbeddingModel │
 │ - sentence-transformers│
 │ - all-mpnet-base-v2 │
 │ - 768-dim vectors │
 └────────────┬────────────┘
 │
 ┌────────────▼────────────┐
 │ Storage Layer │
 │ ├─ VectorStore (FAISS) │
 │ │ - IndexFlatL2 │
 │ │ - L2 distance │
 │ └─ MetadataStore (JSON)│
 │ - File paths │
 │ - Line numbers │
 │ - Chunk types │
 │ - Code snippets │
 └─────────────────────────┘


┌──────────────────────────────────────────────────┐
│ Query Pipeline │
└──────────────────────────────────────────────────┘
 │
Natural Language ────┤
Query │
 ┌────────────▼────────────┐
 │ EmbeddingModel │
 │ - Encode query │
 │ - 768-dim vector │
 └────────────┬────────────┘
 │
 ┌────────────▼────────────┐
 │ FAISS Search │
 │ - Find nearest vectors │
 │ - Calculate similarity │
 │ - Return top-k │
 └────────────┬────────────┘
 │
 ┌────────────▼────────────┐
 │ Retrieve Metadata │
 │ - Get file paths │
 │ - Get line numbers │
 │ - Get code snippets │
 │ - Calculate scores │
 └────────────┬────────────┘
 │
 ▼
 Return Results
```

### RAG Components

#### 1. EmbeddingModel (`rag/embeddings.py`)

Purpose: Generate vector embeddings for code

Features:
- Sentence-transformers integration
- Model: `all-mpnet-base-v2`
- 768-dimensional vectors
- Batch processing for efficiency
- Local model (no API calls)

Usage:
```python
model = EmbeddingModel()
vectors = model.encode(["def hello(): pass", "class Foo: pass"])
# Returns: numpy array of shape (2, 768)
```

#### 2. CodeParser (`rag/code_parser.py`)

Purpose: AST-based Python code parsing

Features:
- Extracts functions with full metadata
- Extracts classes with methods
- Captures imports (standard, third-party)
- Preserves docstrings
- Tracks line numbers
- Graceful error handling (syntax errors)

Metadata Extracted:
```python
{
 "name": "authenticate_user",
 "type": "function",
 "start_line": 45,
 "end_line": 67,
 "docstring": "Authenticate user credentials",
 "code": "def authenticate_user(...)...",
 "decorators": ["@require_auth"],
 "args": ["username", "password"],
 "returns": "bool"
}
```

AST Traversal:
```python
1. Parse file with ast.parse()
2. Walk AST tree with ast.walk()
3. Identify FunctionDef, ClassDef, Import nodes
4. Extract source code using ast.unparse() or direct slicing
5. Capture metadata (decorators, args, docstrings)
6. Handle nested structures (class methods)
```

#### 3. CodeChunker (`rag/chunker.py`)

Purpose: Create semantic chunks for indexing

Chunking Strategy:
- 1 chunk per function - Complete function with context
- 1 chunk per class - Class definition + methods
- 1 chunk for imports - All imports in file
- 1 chunk for module - Module-level docstring

Chunk Structure:
```python
{
 "id": "uuid4",
 "file_path": "/path/to/file.py",
 "chunk_type": "function|class|import|module",
 "name": "function_name",
 "start_line": 45,
 "end_line": 67,
 "code": "def authenticate_user(...)...",
 "docstring": "Docstring text",
 "metadata": {...}
}
```

Why Semantic Chunking?
- Each chunk is a logical unit (function/class)
- Preserves code context and structure
- Better search results than arbitrary splitting
- Line numbers enable precise navigation

#### 4. CodebaseIndexer (`rag/indexer.py`)

Purpose: Orchestrate the indexing process

Features:
- Recursive directory traversal
- Exclusion patterns (`__pycache__`, `.git`, `venv`, etc.)
- Python file detection (`.py` extension)
- Batch embedding generation
- Progress tracking
- Error handling per-file (continues on failure)

Indexing Flow:
```python
1. Walk directory tree (exclude patterns)
2. Filter Python files
3. For each file:
 a. CodeParser.parse(file) -> elements
 b. CodeChunker.chunk(elements) -> chunks
 c. Collect chunks
4. Batch generate embeddings (all chunks)
5. Store vectors in VectorStore
6. Store metadata in MetadataStore
7. Return statistics (files, chunks, time)
```

Statistics Tracked:
```python
{
 "total_files": 127,
 "total_chunks": 834,
 "indexing_time": 18.2,
 "last_indexed_path": "/path/to/project",
 "timestamp": "2025-11-04T14:23:15"
}
```

#### 5. VectorStore (`rag/vector_store.py`)

Purpose: FAISS-based vector similarity search

Features:
- FAISS `IndexFlatL2` (exact L2 distance)
- Fast nearest neighbor search
- Persistent storage (saves to disk)
- Index mapping (vector ID -> chunk ID)

FAISS Configuration:
```python
dimension = 768 # Embedding size
index = faiss.IndexFlatL2(dimension) # Exact search
index.add(vectors) # Add all embeddings
```

Search:
```python
distances, indices = index.search(query_vector, k=5)
# distances: similarity scores (lower = more similar)
# indices: vector IDs in the index
```

Persistence:
```
rag_index/
├── faiss.index # FAISS index file
└── faiss.index.mappings # Vector ID -> Chunk ID mappings
```

#### 6. MetadataStore (`rag/metadata_store.py`)

Purpose: Store chunk metadata as JSON

Features:
- JSON-based storage
- Fast lookup by chunk ID
- File path, line numbers, code snippets
- Chunk type and name

Storage Format:
```json
{
 "chunk_uuid": {
 "file_path": "auth/login.py",
 "chunk_type": "function",
 "name": "authenticate_user",
 "start_line": 45,
 "end_line": 67,
 "code": "def authenticate_user(...)...",
 "docstring": "Authenticate user credentials"
 }
}
```

Persistence:
```
rag_index/
└── metadata.json # All chunk metadata
```

### RAG Integration with Agent

Tool Selection Rules:

The agent automatically uses `codebase_search` when:
- User asks "how does X work?"
- User asks "where is X?"
- User asks "find code that does X"
- Questions about THIS project's code

System Prompt Examples:
```
Example: Semantic Code Search

USER: How does authentication work in this codebase?

THOUGHT: This is a code understanding question about the indexed
codebase. I should use codebase_search to find relevant code.

ACTION: codebase_search
ACTION_INPUT: {"query": "authentication login user credentials"}

[Tool returns ranked results with file paths and line numbers]

ANSWER: Based on auth/login.py:45-67, the authentication system
uses bcrypt for password hashing and JWT tokens...
```

Configuration Integration:
```yaml
rag:
 enabled: true # Auto-enabled after indexing
 last_indexed_path: /path/to/project
 last_indexed_at: "2025-11-04T14:23:15"
 index_stats:
 total_files: 127
 total_chunks: 834

tools:
 codebase_search:
 enabled: true # Auto-enabled with RAG
 top_k: 5 # Return top 5 results
 similarity_threshold: 0.3 # Minimum similarity score
 max_code_length: 500 # Truncate long code snippets
```

### CLI Index Management

Commands:
- `/index [path]` - Index a codebase
- `/index status` - Show statistics
- `/index clear` - Delete index
- `/index refresh` - Re-index last path
- `/csearch <query>` - Test semantic search

Indexing Process:
1. Validate path (exists, contains Python files)
2. Initialize RAG components
3. Call indexer with progress display
4. Update configuration (enable RAG)
5. Persist config to disk
6. Display statistics

Auto-enablement:
After successful indexing:
- `rag.enabled` -> `true`
- `tools.codebase_search.enabled` -> `true`
- Config saved to `config.yaml`
- Agent gains semantic search capability

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
 ├─ Reasoning Node
 │ ├─ Build prompt (system + context + query)
 │ ├─ Get LLM (via ModelManager)
 │ ├─ LLM.invoke(prompt)
 │ ├─ Parse output (THOUGHT/ACTION/INPUT/ANSWER)
 │ └─ Update state
 │
 ├─ Tool Execution Node (if needed)
 │ ├─ Get tool from tool_map
 │ ├─ Parse JSON input
 │ ├─ Execute tool
 │ └─ Store result in state
 │
 ├─ Loop Detection (if repeated)
 │ ├─ Compare with last call
 │ ├─ Force answer if duplicate
 │ └─ Break loop
 │
 └─ Repeat until:
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

1. **Create tool class (`tools/your_tool.py`):

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

2. **Register in CLI (`cli.py:initialize()`):

```python
from tools.your_tool import YourTool

# In initialize():
your_tool = YourTool(self.config)

self.agent = MetonAgent(
 config=self.config,
 model_manager=self.model_manager,
 conversation=self.conversation,
 tools=[file_tool, your_tool], # Add here
 verbose=self.verbose
)
```

3. **Update config (add to `config.yaml` if needed):

```yaml
tools:
 your_tool:
 enabled: true
 option1: value1
```

4. **Test:
```bash
python meton.py
You: use your_tool to do something
```

### Adding a New Command

1. **Add to help (`cli.py:display_help()`):

```python
table.add_row("/newcmd", "Description of command")
```

2. **Add handler (`cli.py:handle_command()`):

```python
elif cmd == '/newcmd':
 if args:
 self.new_command_handler(args[0])
 else:
 self.console.print("[yellow]Usage: /newcmd <arg>[/yellow]")
```

3. **Implement method:

```python
def new_command_handler(self, arg: str):
 """Handle /newcmd."""
 try:
 # Implementation
 self.console.print("[green]OK Success[/green]")
 except Exception as e:
 self.console.print(f"[red] Error: {e}[/red]")
```

### Adding a New Model Provider

Currently Ollama-only. To add OpenAI/Anthropic/etc:

1. **Extend ModelManager
```python
class MultiModelManager(ModelManager):
 def __init__(self, config, provider="ollama"):
 self.provider = provider
 if provider == "openai":
 # Initialize OpenAI client
 elif provider == "ollama":
 super().__init__(config)
```

2. **Update config schema
```yaml
models:
 provider: "ollama" # or "openai", "anthropic"
 ollama:
 primary_model: "codellama:34b"
 openai:
 model: "gpt-4"
 api_key: "..."
```

3. **Update get_llm()
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
- 34B models High quality, 8-16GB VRAM, 10-20s latency
- 13B models Balanced, 4-8GB VRAM, 5-10s latency
- 7B models Fast, 2-4GB VRAM, 2-5s latency

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

1. **RAG Integration
 - FAISS vector store
 - Codebase indexing
 - Semantic search tool

2. **Multi-Agent System
 - Planner agent
 - Executor agents
 - Reviewer agent

3. **Code Execution
 - Sandboxed Python execution
 - Test running
 - Linting integration

4. **Web Search Tool
 - Documentation lookup
 - Stack Overflow search
 - GitHub API integration

5. **Advanced Conversation
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
print(prompt) # See what agent sees
```

---

## Contributing Guidelines

When modifying Meton:

1. **Update tests for changed components
2. **Update STATUS.md with implementation details
3. **Update this ARCHITECTURE.md if adding components
4. **Update USAGE.md if adding user-facing features
5. **Run test suite before committing:
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
