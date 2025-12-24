# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Meton is a fully local AI coding assistant powered by LangChain, LangGraph, and Ollama. Everything runs on local hardware - no external API calls, no data leaving the machine. The name comes from Metis (wisdom) + Ergon (action).

Core Architecture:

- Agent System LangGraph-based ReAct agent with multi-step reasoning (Think -> Act -> Observe loop)
- Tools File operations, code execution, web search, semantic code search (RAG)
- Skills High-level capabilities (code explainer, debugger, refactoring engine)
- RAG System FAISS-based semantic code search using AST parsing and sentence-transformers embeddings
- Models Ollama integration with Qwen 2.5 32B (primary), Llama 3.1 8B (fallback), Mistral (quick)

## Development Commands

### Running Meton

```bash
# Activate virtual environment
source venv/bin/activate

# Run Meton
python meton.py
# or
./meton.py
```

### Testing

```bash
# Run specific test suites
python test_infrastructure.py # Core config, logger, formatting
python test_models.py # Model Manager
python test_conversation.py # Conversation Manager
python test_agent.py # Agent System
python test_file_ops.py # File Operations Tool

# Run RAG/indexing tests
python test_rag_code_parser.py # AST-based code parsing
python test_rag_chunker.py # Semantic chunking
python test_rag_indexer.py # Codebase indexing
python test_codebase_search.py # Semantic search tool
python test_rag_agent_integration.py # Agent RAG integration

# Run tool tests
python test_code_executor.py # Code execution tool
python test_web_search.py # Web search tool
python test_agent_integration.py # Agent + tools integration

# Run skills tests
python test_skills.py # Skills framework
python test_code_explainer.py # Code explainer skill
python test_debugger.py # Debugger skill
python test_refactoring_engine.py # Refactoring engine skill

# Note: Tests use executable scripts, not pytest
# Tests are standalone Python scripts that import and test components
```

### Building/Installing

```bash
# Initial setup
chmod +x setup.sh
./setup.sh

# Install/update dependencies
pip install -r requirements.txt

# Activate environment
source venv/bin/activate
```

## Architecture Overview

### Core Components

1. Agent System (`core/agent.py`)

- LangGraph StateGraph with ReAct pattern implementation
- Three-node architecture: Reasoning -> Tool Execution -> Loop Detection
- Critical Loop detection system prevents infinite tool calls by tracking (tool_name, input) pairs
- System prompt structure: Path context + Available tools + Examples + Critical rules
- Max iterations: 10 (configurable in `config.yaml`)

2. Configuration (`core/config.py`)

- Pydantic-based type-safe configuration with YAML persistence
- Important ConfigLoader has `save()` method at core/config.py:164-173 for persisting runtime changes
- When CLI commands change settings (like `/web on`), must update three locations:

 1. Tool runtime state (`tool._enabled`)
 2. In-memory config (`config.config.tools.<tool>.enabled`)
 3. Disk persistence via `config.save()`

3. Model Manager (`core/models.py`)

- Ollama integration with LangChain compatibility
- LLM instance caching per model for performance
- Alias resolution: `primary`/`fallback`/`quick` -> actual model names
- Supports model switching without restart via `/model` command

4. Conversation Manager (`core/conversation.py`)

- Thread-safe with `threading.Lock` for all operations
- JSON-based persistence in `conversations/` directory
- Auto-trimming based on `max_history` (preserves system messages)
- UUID session IDs with ISO 8601 timestamps

5. RAG System (`rag/` directory)

- CodeParser AST-based Python parsing extracting functions, classes, imports with full metadata
- CodeChunker Semantic chunking (1 chunk per function/class, preserves code structure)
- EmbeddingModel sentence-transformers/all-mpnet-base-v2 (768-dim vectors)
- VectorStore FAISS IndexFlatL2 for exact L2 distance search
- MetadataStore JSON storage mapping chunk IDs to file paths, line numbers, code snippets
- CodebaseIndexer Orchestrates parsing -> chunking -> embedding -> storage

6. Skills System (`skills/` directory)

- High-level intelligent capabilities built on top of tools
- Two types: Python skills (BaseSkill) and Markdown skills (MarkdownSkill)
- Python skills: Code Explainer, Debugger Assistant, Refactoring Engine, Test Generator, Documentation Generator, Code Reviewer, Task Planner
- Markdown skills: Claude Code-style with YAML frontmatter (code-reviewer, code-explainer, debugger)
- Auto-loaded from `skills/` directory when `skills.enabled: true`
- Markdown skills discovered from: `.meton/skills/` (project) > `~/.meton/skills/` (user) > `skills/md_skills/` (builtin)

7. Sub-Agents System (`agents/` directory)

- Autonomous specialized agents with isolated execution context
- `SubAgent` dataclass for agent definition
- `SubAgentLoader` discovers agents from markdown files with YAML frontmatter
- `SubAgentSpawner` creates isolated agent instances with separate conversation context
- `SubAgentManager` high-level management and execution history
- Built-in agents: explorer (quick model), planner, code-reviewer, debugger
- Discovery order: `.meton/agents/` (project) > `~/.meton/agents/` (user) > `agents/builtin/` (builtin)

8. Hooks System (`hooks/` directory)

- Pre/post execution hooks for tools, skills, agents, and queries
- `Hook` dataclass with shell command or Python function support
- `HookManager` manages registration, execution, and history tracking
- `HookLoader` discovers hooks from markdown files with YAML frontmatter
- Hook types: pre_query, post_query, pre_tool, post_tool, pre_skill, post_skill, pre_agent, post_agent
- Conditional execution with template variable support (e.g., `{success} == false`)
- Built-in hooks: log-tool-usage, notify-on-error (disabled by default)
- Discovery order: `.meton/hooks/` (project) > `~/.meton/hooks/` (user) > `hooks/builtin/` (builtin)

### Tools (`tools/` directory)

All tools inherit from `MetonBaseTool` (extends LangChain's `BaseTool`).

FileOperationsTool

- Actions: read, write, list, create_dir, exists, get_info
- Security: Path resolution, blocked paths (/etc, /sys, /proc), allowed paths validation
- JSON input: `{"action": "read", "path": "/path/to/file"}`

CodeExecutorTool

- Subprocess isolation with 5-second timeout
- AST-based import validation (27 allowed, 36 blocked standard libraries)
- Captures stdout + stderr with execution time tracking

WebSearchTool

- DuckDuckGo integration via `ddgs` library (no API key needed)
- Note Library migrated from `duckduckgo_search` -> `ddgs` (October 2025)
- Disabled by default, runtime toggle via `/web on/off`
- Config persistence required (see Configuration section)

CodebaseSearchTool

- Semantic code search using RAG system
- Natural language queries -> vector similarity search
- Returns ranked results with file paths, line numbers, similarity scores
- Lazy-loads indexer for performance

SymbolLookupTool

- Fast exact symbol definition lookup (functions, classes, methods, variables)
- AST-based parsing using CodeParser (imported via importlib to avoid dependency issues)
- In-memory indexing with 60-second cache TTL
- Returns file path, line number, signature, docstring, code snippet with context
- Filtering by type (function/class/method) and scope (public/private)
- Enabled by default
- CLI command: `/find <symbol> [type:function|class|method]`
- Example: `/find MetonAgent` or `/find _run type:method`

ImportGraphTool

- Analyzes import dependencies in Python codebases using grimp library
- Detects circular dependencies (cycles) between modules
- Calculates coupling metrics (density, fan-in, fan-out)
- Identifies orphan modules (not imported by anything)
- Generates Mermaid diagrams and text visualizations
- Uses NetworkX for graph analysis algorithms
- Enabled by default
- JSON input: `{"path": "core", "output_format": "mermaid"}`
- Example: Analyze project architecture, find tightly coupled modules, detect import cycles

### Data Flow Patterns

Query Execution Flow:

```
User input -> CLI.process_query() -> Agent.run(query) -> LangGraph.invoke()
 -> Reasoning Node (builds prompt, calls LLM, parses THOUGHT/ACTION/INPUT/ANSWER)
 -> Tool Execution Node (looks up tool, executes, captures result)
 -> Loop Detection (prevents repeated tool calls)
 -> Repeat until ANSWER or max iterations
 -> Return result -> CLI.display_response()
```

RAG Indexing Flow:

```
/index [path] -> CodebaseIndexer.index_directory()
 -> Walk tree (exclude __pycache__, .git, venv, etc.)
 -> For each .py file: CodeParser.parse() -> CodeChunker.chunk()
 -> Batch generate embeddings -> VectorStore.add()
 -> Save metadata -> MetadataStore.save()
 -> Update config (enable RAG) -> config.save()
```

RAG Query Flow:

```
Natural language query -> EmbeddingModel.encode(query)
 -> FAISS.search(query_vector, k=5)
 -> Retrieve metadata for top-k results
 -> Format with file paths, line numbers, code snippets
 -> Return to agent for synthesis
```

## Key Implementation Details

### Agent System Prompt Structure

The agent's effectiveness depends heavily on the system prompt (core/agent.py). Structure:

1. **Path context** Current working directory and allowed paths
2. **Available tools** Each tool's name, description, input format
3. **Examples** Complete Think -> Act -> Observe -> Answer flows
4. **Critical rules** ANSWER format rules are critical - agent must end with ANSWER to complete
5. **Multi-part question rules** Identifies and addresses all question components (comparison, usage guidance)
6. **Answer validation** Self-check checklist ensuring completeness before responding

### Loop Detection Algorithm

Located in agent.py reasoning node:

```python
if (current_action == last_action and current_input == last_input):
 # Force completion with existing result
 state["finished"] = True
 state["final_answer"] = last_result
```

This prevents infinite loops when agent repeats same tool call.

### RAG Integration with Agent

The agent automatically uses `codebase_search` when:

- User asks "how does X work?"
- User asks "where is X?"
- Questions about THIS project's code

Tool selection is driven by examples in system prompt showing when to use each tool.

### Security Model

- File Operations Path resolution prevents traversal attacks, blocked/allowed path lists
- Code Execution Subprocess isolation, AST import validation, timeout protection
- LLM Fully local (no external API calls), no eval()/exec() usage
- Config Pydantic validation prevents injection

## Common Development Tasks

### Adding a New Tool

1. Create `tools/your_tool.py` inheriting from `MetonBaseTool`
2. Implement `_run(self, input: str) -> str` method
3. Register in `cli.py:initialize()` tools list
4. Add configuration section to `config.yaml` if needed
5. Update agent system prompt with tool examples (optional but recommended)

### Adding a New Skill (Python)

1. Create `skills/your_skill.py` inheriting from `BaseSkill`
2. Set `name`, `description`, `version` class attributes
3. Implement `execute(self, input_data: Dict) -> Dict` method
4. Skills are auto-loaded if `skills.enabled: true` and in `skills/` directory
5. Follow pattern from existing skills (code_explainer.py, debugger.py, refactoring_engine.py)

### Adding a New Skill (Markdown)

1. Create directory `.meton/skills/<skill-name>/` (project-specific) or `skills/md_skills/<skill-name>/` (builtin)
2. Create `SKILL.md` file with YAML frontmatter:
   ```yaml
   ---
   name: my-skill
   description: Description for LLM discovery
   allowed-tools: Read, Grep, Glob
   model: primary
   version: 1.0.0
   ---

   # Skill Instructions

   Detailed instructions...
   ```
3. Run `/skill discover` to load the skill
4. Use `/skill info <name>` to verify

### Adding a New Sub-Agent

1. Create `<agent-name>.md` in `.meton/agents/` (project) or `agents/builtin/` (builtin)
2. Add YAML frontmatter:
   ```yaml
   ---
   name: my-agent
   description: Description for agent selection
   tools: file_operations, codebase_search
   model: primary
   ---

   # Agent System Prompt

   You are a specialist in...
   ```
3. Run `/agent discover` to load the agent
4. Execute with `/agent run <name> "task description"`

### Adding a New CLI Command

1. Add to help display in `cli.py:display_help()`
2. Add handler in `cli.py:handle_command()` elif chain
3. Implement handler method following naming pattern `handle_<command>()`
4. Use Rich console for formatted output (`self.console.print()`)

### Modifying Configuration Schema

1. Update Pydantic models in `core/config.py`
2. Add corresponding fields to `config.yaml`
3. Update default values if adding new optional fields
4. Remember: Changes require `config.save()` for persistence

## Problem-Solving Guidelines

### When to Search for Solutions

When debugging or fixing issues in Meton:

**Rule**: After **two unsuccessful attempts** to solve an issue, search the web for solutions.

**Why**:

- Prevents spending excessive time on approaches that aren't working
- Leverages existing solutions and best practices from the community
- Helps identify if the problem is a known issue with dependencies (LangChain, LangGraph, etc.)

**What to search for**:

- Error messages (exact error text + library name)
- Best practices for the specific pattern or architecture (e.g., "ReAct agent loop detection")
- Known issues or workarounds for the libraries being used
- Recent discussions (include year: "2024" or "2025" for current solutions)

**Example workflow**:

1. Attempt 1: Try initial fix based on code analysis
2. Attempt 2: Try alternative approach or refinement
3. **Attempt 3**: Search web for solutions before trying a third code approach
4. Apply researched solution with understanding of why it works

This guideline prevents:

- Infinite debugging loops
- Over-engineering solutions
- Missing simple, well-known fixes
- Wasting time reinventing solutions

## Testing Patterns

Tests are standalone Python scripts (not pytest-based). Pattern:

```python
#!/usr/bin/env python3
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.component import ComponentClass

def test_feature():
 """Test description."""
 component = ComponentClass()
 result = component.method()
 assert result == expected, f"Expected {expected}, got {result}"

if __name__ == "__main__":
 test_feature()
 print(" All tests passed")
```

Run directly: `python test_component.py`

## Critical Files Reference

- `config.yaml` - Main configuration (models, tools, conversation, RAG settings)
- `core/agent.py` - ReAct agent implementation with LangGraph
- `core/config.py` - Type-safe configuration with Pydantic (has save() method!)
- `cli.py` - Main CLI interface with Rich formatting
- `meton.py` - Entry point
- `tools/base.py` - Base tool class
- `skills/base.py` - Base skill class
- `rag/indexer.py` - Codebase indexing orchestration
- `docs/ARCHITECTURE.md` - Detailed system design documentation
- `docs/STATUS.md` - Development status and progress tracking
- `docs/QUICK_REFERENCE.md` - Command reference cheat sheet

## Known Limitations & Gotchas

### Configuration Persistence

Critical When CLI commands modify settings, must update three locations:

1. Tool runtime state (`tool._enabled`)
2. In-memory config object
3. Call `config.save()` to persist to disk

Example from cli.py:288-312 for `/web on` command.

### Large File Handling

Multi-step queries with files >30KB may timeout because ReAct pattern passes full content through each iteration. Workaround: Ask specific questions or use RAG indexing for semantic search.

### Library Migration

The web search tool uses `ddgs` library (not `duckduckgo_search` which was deprecated). Import: `from ddgs import DDGS`. API: `ddgs.text(query, max_results=N)`.

### Test Execution

Tests are NOT using pytest. They are standalone executable Python scripts. Run directly: `python test_<component>.py`.

### Virtual Environment

Always activate venv before running: `source venv/bin/activate`. The project uses Python 3.11+ with specific versions of LangChain, LangGraph, sentence-transformers, FAISS.

## File Structure Quick Reference

```
meton/
├── core/ # Core components
│ ├── agent.py # LangGraph ReAct agent
│ ├── config.py # Pydantic configuration
│ ├── conversation.py # Thread-safe conversation manager
│ └── models.py # Ollama model manager
├── tools/ # LangChain tools
│ ├── base.py # MetonBaseTool base class
│ ├── file_ops.py # File operations
│ ├── code_executor.py # Python code execution
│ ├── web_search.py # DuckDuckGo search
│ └── codebase_search.py # RAG semantic search
├── skills/ # High-level skills
│ ├── base.py # BaseSkill abstract class
│ ├── skill_manager.py # Manages Python + Markdown skills
│ ├── markdown_skill.py # MarkdownSkill + MarkdownSkillLoader
│ ├── code_explainer.py # Code explanation (Python)
│ ├── debugger.py # Debug assistance (Python)
│ ├── refactoring_engine.py # Code refactoring (Python)
│ └── md_skills/ # Markdown skills
│   ├── code-reviewer/ # Code review skill
│   ├── code-explainer/ # Code explanation skill
│   └── debugger/ # Debugging skill
├── agents/ # Sub-agents system
│ ├── __init__.py # Package init
│ ├── subagent.py # SubAgent dataclass + loader
│ ├── subagent_loader.py # SubAgentLoader for discovery
│ ├── subagent_spawner.py # SubAgentSpawner + SubAgentManager
│ └── builtin/ # Built-in agents
│   ├── explorer.md # Fast exploration agent
│   ├── planner.md # Implementation planning
│   ├── code-reviewer.md # Code review agent
│   └── debugger.md # Debugging agent
├── hooks/ # Hooks system
│ ├── __init__.py # Package init
│ ├── base.py # Hook, HookType, HookContext, HookResult
│ ├── hook_manager.py # HookManager for registration/execution
│ ├── hook_loader.py # HookLoader for discovery
│ └── builtin/ # Built-in hooks
│   ├── log-tool-usage/ # Logs all tool executions
│   └── notify-on-error/ # Desktop notification on errors
├── rag/ # RAG system
│ ├── code_parser.py # AST-based parsing
│ ├── chunker.py # Semantic chunking
│ ├── embeddings.py # Sentence transformers
│ ├── vector_store.py # FAISS vector store
│ ├── metadata_store.py # JSON metadata storage
│ └── indexer.py # Indexing orchestration
├── utils/ # Utilities
│ ├── logger.py # Logging setup
│ └── formatting.py # CLI formatting helpers
├── cli.py # Main CLI interface
├── meton.py # Entry point
├── config.yaml # Configuration file
├── requirements.txt # Python dependencies
└── test_*.py # Test scripts
```

## LangGraph Agent State Management

The agent uses a `StateGraph` with `AgentState` TypedDict:

- `messages`: Conversation history
- `thoughts`: Agent's reasoning steps
- `tool_calls`: List of (tool_name, input, output) tuples
- `iteration`: Current iteration count
- `finished`: Boolean completion flag
- `final_answer`: Final response string

State flows through nodes: `START` -> `reasoning_node` -> `tool_execution_node` -> (loop or `END`)

Conditional edges based on:

- `state["finished"]` - Has agent provided ANSWER?
- `state["iteration"] >= max_iterations` - Hit limit?
- Tool call required? - Parse ACTION from LLM output

## RAG System Details

### Indexing Strategy

- AST Parsing Uses Python's `ast` module to extract functions, classes, imports
- Semantic Chunks One chunk per function/class (not arbitrary text splitting)
- Metadata File path, start/end line numbers, docstrings, decorators, arguments
- Embeddings sentence-transformers/all-mpnet-base-v2 (768 dimensions)
- Storage FAISS IndexFlatL2 (exact L2 distance) + JSON metadata

### Search Process

1. Encode natural language query to 768-dim vector
2. FAISS finds k-nearest vectors (default k=5)
3. Retrieve metadata for matching chunks
4. Filter by similarity threshold (default 0.3)
5. Return ranked results with file:line references

### CLI Integration

- `/index [path]` - Index Python codebase
- `/index status` - Show stats (files, chunks, last indexed)
- `/index clear` - Delete index
- `/index refresh` - Re-index last path
- `/csearch <query>` - Direct semantic search test

After successful indexing, both `rag.enabled` and `tools.codebase_search.enabled` are set to `true` in config.yaml.

## Model Configuration

Default models (configurable in config.yaml):

- Primary qwen2.5:32b-instruct-q5_K_M (main reasoning)
- Fallback llama3.1:8b (backup)
- Quick mistral:latest (fast responses)

### Generation Parameters

Meton provides comprehensive control over LLM sampling and output quality through 14 configurable parameters:

**Core Parameters:**

- Temperature: 0.0-2.0 (default: 0.0 for deterministic output)
- Max tokens: 2048 (maximum generation length)
- Top-p: 0.9 (nucleus sampling)
- Context window: 32768 tokens (increased for large files)

**Advanced Sampling:**

- Top-k: 40 (sampling diversity, 0 = disabled)
- Min-p: 0.1 (adaptive filtering, recommended over top-k)

**Repetition Control:**

- Repeat penalty: 1.1 (penalize repetition, 1.0 = disabled)
- Repeat last n: 64 (window for repetition analysis)
- Presence penalty: 0.0 (penalize already-used tokens)
- Frequency penalty: 0.0 (penalize frequently-used tokens)

**Mirostat Sampling (alternative to top-k/top-p):**

- Mirostat: 0 (0 = disabled, 1 = v1, 2 = v2)
- Mirostat tau: 5.0 (target entropy)
- Mirostat eta: 0.1 (learning rate)

**Reproducibility:**

- Seed: -1 (random seed, -1 = random, set for deterministic output)

All parameters are defined in `core/config.py` (ModelSettings), configured in `config.yaml`, and automatically passed to Ollama. Edit `config.yaml` and run `/reload` to apply changes.

Switch models at runtime: `/model <name>` or `/model primary|fallback|quick`

### Runtime Parameter Tuning (Phase 2)

Meton supports dynamic parameter adjustment without restart through CLI commands:

**Commands:**

- `/param show` - Display all current parameters in organized table
- `/param <name> <value>` - Set individual parameter at runtime
- `/param reset` - Reset all parameters to config.yaml defaults
- `/preset` - List available parameter presets
- `/preset <name>` - Apply a preset configuration

**Parameter Presets:**

Five predefined presets for common use cases:

1. **precise** - Deterministic output for precise coding tasks

   ```
   temperature: 0.0, top_k: 40, repeat_penalty: 1.1
   ```

2. **creative** - More exploratory and creative coding

   ```
   temperature: 0.7, top_p: 0.95, repeat_penalty: 1.2
   ```

3. **balanced** - Balanced between creativity and precision

   ```
   temperature: 0.3, top_k: 40, repeat_penalty: 1.15
   ```

4. **debugging** - Consistent methodical debugging approach

   ```
   temperature: 0.2, mirostat: 2, top_k: 20
   ```

5. **explanation** - Clear explanations with reduced repetition

   ```
   temperature: 0.5, repeat_penalty: 1.25, presence_penalty: 0.1
   ```

**Example Workflow:**

```bash
# View current parameters
/param show

# Adjust for creative exploration
/preset creative

# Fine-tune specific parameter
/param temperature 0.5

# Reset to config defaults
/param reset
```

**Implementation Details:**

- Changes are applied immediately to in-memory config
- LLM cache is cleared to ensure new parameters take effect on next query
- Use `/param reset` to reload from config.yaml
- Use `/reload` to reload entire configuration including model selection

### Fine-Tuning Workflow (Phase 3)

Meton supports using custom fine-tuned models created with llama.cpp and Ollama.

**Quick Start:**

```bash
# 1. Prepare training data from conversations
python utils/prepare_training_data.py \
    --conversations-dir ./conversations \
    --output training_data.txt

# 2. Fine-tune with llama.cpp (offline)
cd /path/to/llama.cpp
./finetune --model-base base.gguf --train-data training_data.txt

# 3. Create Ollama model
ollama create meton-custom -f templates/modelfiles/basic.Modelfile

# 4. Use in Meton
./meton.py
> /model meton-custom
```

**Resources:**

- **Complete Guide:** `docs/FINE_TUNING.md` - Comprehensive fine-tuning documentation
- **Training Data Utility:** `utils/prepare_training_data.py` - Extract and format conversations
- **Modelfile Templates:** `templates/modelfiles/` - Ready-to-use templates for different use cases
- **Example Data:** `examples/training_data/` - Sample training data formats

**Use Cases:**

1. **Style Transfer** - Train model to match your coding conventions and patterns
2. **Domain Specialization** - Focus on specific frameworks (FastAPI, LangChain, etc.)
3. **Behavior Tuning** - Adjust response style, explanation depth, documentation format
4. **Multi-Task** - Combine multiple objectives into one specialized model

**Training Data Preparation:**

The `prepare_training_data.py` utility extracts high-quality examples from Meton conversations:

```bash
# Basic usage
python utils/prepare_training_data.py \
    --conversations-dir ./conversations \
    --output training.txt

# With filters
python utils/prepare_training_data.py \
    --conversations-dir ./conversations \
    --output python_training.txt \
    --filter-keyword "Python" \
    --min-length 100 \
    --quality-threshold 0.7 \
    --deduplicate
```

**Modelfile Templates:**

Five pre-configured templates for common use cases:

- `basic.Modelfile` - General-purpose
- `python-specialist.Modelfile` - Python development
- `fastapi-expert.Modelfile` - FastAPI/web APIs
- `langchain-expert.Modelfile` - LangChain/LangGraph agents
- `explainer.Modelfile` - Code explanation and teaching

Each template includes:

- Optimized system prompts
- Task-appropriate parameters
- Proper chat format templates

See `docs/FINE_TUNING.md` for complete workflow documentation and best practices.

### Parameter Profiles (Phase 4)

Phase 4 introduces user-customizable parameter profiles for persistent parameter configurations.

**Key Difference from Presets:**

- **Presets** (Phase 2): Hardcoded in Python, cannot be modified at runtime
- **Profiles** (Phase 4): Stored in `config.yaml`, fully customizable by users

**Quick Start:**

```bash
# List available profiles
> /pprofile

# Apply a profile
> /pprofile apply creative_coding

# Create custom profile
> /pprofile create my_profile

# Export for sharing
> /pprofile export my_profile ./my_settings.json

# Import on another machine
> /pprofile import ./my_settings.json
```

**CLI Commands:**

- `/pprofile` - List all parameter profiles
- `/pprofile apply <name>` - Apply a profile
- `/pprofile show <name>` - Show profile details
- `/pprofile create <name>` - Create new profile (interactive)
- `/pprofile delete <name>` - Delete a profile
- `/pprofile export <name> [path]` - Export profile to JSON
- `/pprofile import <path>` - Import profile from JSON

**Default Profiles:**

Four profiles included in `config.yaml`:

- `creative_coding` - High temperature (0.7) for exploratory coding
- `precise_coding` - Deterministic (0.0) with mirostat for precision
- `debugging` - Low temperature (0.2) for methodical analysis
- `explanation` - Moderate temperature (0.5) for clear explanations

**Implementation Details:**

Configuration Model (`core/config.py`):

```python
class ParameterProfile(BaseModel):
    name: str
    description: str
    settings: Dict[str, Any]  # Validated parameter names
```

Model Manager Methods (`core/models.py`):

- `list_profiles()` - Dict of all profiles
- `get_profile(name)` - Get specific profile
- `apply_profile(name)` - Apply settings and clear cache
- `create_profile(name, desc, settings)` - Create and persist
- `delete_profile(name)` - Remove and save config
- `export_profile(name, path)` - Export to JSON
- `import_profile(path)` - Import from JSON

Storage (`config.yaml`):

```yaml
parameter_profiles:
  my_custom_profile:
    name: my_custom_profile
    description: Custom settings for API development
    settings:
      temperature: 0.3
      top_p: 0.95
      repeat_penalty: 1.15
```

**Use Cases:**

- Project-specific parameter tuning
- Task-based configurations (debugging vs feature dev)
- Team standardization (share profiles)
- A/B testing different parameter combinations
- Building a library of tested configurations

**Example Workflow:**

```bash
# Working on a new feature - use creative profile
> /pprofile apply creative_coding

# Switching to debugging - use debugging profile
> /pprofile apply debugging

# Found good settings - save as profile
> /pprofile create api_dev
Description: Settings optimized for API development
temperature [0.0]: 0.3
top_p [0.9]: 0.95
...

# Share with team
> /pprofile export api_dev ./team_profiles/api_dev.json
```

## Conversation Management

- Auto-save Enabled by default in config.yaml
- Max history 20 messages (auto-trims older messages)
- Storage JSON files in `conversations/` directory
- Format `session_<timestamp>_<uuid>.json`
- Thread-safe All operations use `threading.Lock`
- Context window Preserves system messages during trimming

CLI commands:

- `/save` - Manual save
- `/history` - Show conversation
- `/search <keyword>` - Search history
- `/clear` - Clear current conversation
