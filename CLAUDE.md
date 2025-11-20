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
- `BaseSkill` abstract class requiring `execute()` implementation
- Current skills: Code Explainer, Debugger Assistant, Refactoring Engine
- Auto-loaded from `skills/` directory when `skills.enabled: true`

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
1. **Path context Current working directory and allowed paths
2. **Available tools Each tool's name, description, input format
3. **Examples Complete Think -> Act -> Observe -> Answer flows
4. **Critical rules ANSWER format rules are critical - agent must end with ANSWER to complete

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

### Adding a New Skill
1. Create `skills/your_skill.py` inheriting from `BaseSkill`
2. Set `name`, `description`, `version` class attributes
3. Implement `execute(self, input_data: Dict) -> Dict` method
4. Skills are auto-loaded if `skills.enabled: true` and in `skills/` directory
5. Follow pattern from existing skills (code_explainer.py, debugger.py, refactoring_engine.py)

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
- `ARCHITECTURE.md` - Detailed system design documentation
- `STATUS.md` - Development status and progress tracking

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
│ ├── code_explainer.py # Code explanation
│ ├── debugger.py # Debug assistance
│ └── refactoring_engine.py # Code refactoring
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

Generation settings:
- Temperature: 0.0 (deterministic)
- Max tokens: 2048
- Top-p: 0.9
- Context window: 4096 tokens

Switch models at runtime: `/model <name>` or `/model primary|fallback|quick`

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
