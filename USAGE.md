# Meton Usage Guide

Complete guide to using Meton, your local AI coding assistant.

---

## Quick Start

```bash
# Launch Meton
./meton

# Or with full path
python meton.py
```

The CLI will initialize all components and present you with an interactive prompt where you can:
- Ask questions about your codebase
- Request file operations
- Get coding assistance
- Maintain conversation context across multiple queries

---

## Launch Options

### CLI Mode (Default)
```bash
# Launch Meton CLI
./meton
# Or with full path
python meton.py
```

### Web UI Mode
```bash
# Launch Gradio-based web interface
python launch_web.py

# With options
python launch_web.py --share # Enable public sharing
python launch_web.py --port 8080 # Custom port
python launch_web.py --auth user:pass # With authentication
```

Web UI Features:
- Chat interface with message history
- File upload and download
- Multi-session management
- Real-time analytics with Plotly visualizations
- Settings management
- Export conversations to JSON/CSV
- Session statistics and performance metrics

---

## Commands Reference

Meton provides 30+ interactive commands to control your session:

### Information Commands

#### `/help` or `/h`
Show the complete list of available commands.

```
You: /help

╔═══════════════════════════════════════╗
║ Available Commands ║
╠═══════════════════════════════════════╣
║ /help, /h Show help ║
║ /status Show current status ║
║ ... ║
╚═══════════════════════════════════════╝
```

#### `/status`
Display current session information including:
- Active model
- Session ID
- Message count
- Available tools
- Max iterations
- Verbose mode status

```
You: /status

╭─── Current Status ────────────────────╮
│ Model: qwen2.5:32b-instruct... │
│ Session: 3c8a9f2d-4b1e... │
│ Messages: 12 │
│ Tools: file_operations │
│ Max Iter: 10 │
│ Verbose: OFF │
╰───────────────────────────────────────╯
```

### Model Management

#### `/models`
List all available Ollama models and show which one is currently active.

```
You: /models

╔════════════════════════════════════════════╗
║ Available Models ║
╠════════════════════════════════════════════╣
║ qwen2.5:32b-instruct-q5_K_M OK Current ║
║ llama3.1:8b ║
║ mistral:latest ║
╠════════════════════════════════════════════╣
║ Aliases: ║
║ primary -> qwen2.5:32b-instruct-q5_K_M ║
║ fallback -> llama3.1:8b ║
║ quick -> mistral:latest ║
╚════════════════════════════════════════════╝
```

#### `/model <name>`
Switch to a different model. Accepts full model names or aliases:
- `primary` -> qwen2.5:32b-instruct-q5_K_M (best quality, reasoning)
- `fallback` -> llama3.1:8b (balanced)
- `quick` -> mistral:latest (fastest)

```
You: /model quick
OK Switched to model: mistral:latest

You: /model primary
OK Switched to model: qwen2.5:32b-instruct-q5_K_M
```

### Conversation Management

#### `/history`
Show all messages in the current conversation with truncated content.

```
You: /history

Conversation History

1. USER: What files can you see?
2. ASSISTANT: I can see the following files in /media/development/projects/meton: ...
3. USER: Read config.yaml
4. ASSISTANT: Here are the contents of config.yaml: ...

Total messages: 4
```

#### `/search <keyword>`
Search conversation history for a specific keyword. Results show context around matches with the keyword highlighted.

```
You: /search agent

Search Results for 'agent' (3 matches)

2. ASSISTANT: The **agent system uses LangGraph for ReAct pattern...
5. USER: How does the **agent loop detection work?
6. ASSISTANT: The **agent detects loops by comparing...

Total matches: 3/12 messages
```

#### `/clear` or `/c`
Clear the entire conversation history. Requires confirmation.

```
You: /clear
Clear conversation history? [y/n] (n): y
OK Conversation history cleared
```

#### `/save`
Manually save the current conversation to disk (auto-save happens on exit if enabled in config).

```
You: /save
 Saving conversation...
OK Conversation saved: conversation_3c8a9f2d.json
```

### Tool Management

#### `/tools`
List all available tools with descriptions and status.

```
You: /tools

╔════════════════════════════════════════════════════════╗
║ Tool Name Status Description ║
╠════════════════════════════════════════════════════════╣
║ file_operations enabled Perform file ops... ║
║ code_executor enabled Execute Python... ║
║ web_search disabled Search the web... ║
║ codebase_search enabled Semantic search... ║
╚════════════════════════════════════════════════════════╝
```

#### `/web [on|off|status]`
Control web search tool (disabled by default for privacy).

```
You: /web status
Web search: disabled

You: /web on
 Web search enabled

You: /web off
 Web search disabled
```

### Codebase Indexing & Search

#### `/index [path]`
Index a Python codebase for semantic code search using FAISS.

```
You: /index /media/development/projects/my_project

 Indexing /media/development/projects/my_project...
Found 45 Python files

Processing files... ━━━━━━━━━━ 100% 45/45 00:08

 Complete! Indexed 45 files, 234 chunks in 8.2s
RAG enabled 
Codebase search enabled 
```

Features:
- AST-based Python file parsing (functions, classes, modules)
- Semantic chunking (one chunk per function/class)
- 768-dimensional embeddings using sentence-transformers
- FAISS vector store for fast similarity search
- Automatic RAG enablement after indexing

#### `/index status`
Show statistics about the current index.

```
You: /index status

╭─── Codebase Index Status ─────────────────╮
│ Indexed Path: /path/to/project │
│ Files: 45 │
│ Chunks: 234 │
│ Last Indexed: 2025-11-04 14:23:15 │
│ RAG Status: enabled │
╰───────────────────────────────────────────╯
```

#### `/index clear`
Delete the current index (requires confirmation).

```
You: /index clear
 This will delete the entire index. Continue? [y/n] (n): y
 Index cleared successfully
```

#### `/index refresh`
Re-index the last indexed path.

```
You: /index refresh
 Re-indexing /path/to/project...
 Complete! Indexed 45 files, 234 chunks in 8.1s
```

#### `/csearch <query>`
Test semantic code search directly without asking the agent.

```
You: /csearch authentication

 Searching for: "authentication"

╔════════════════════════════════════════════════════╗
║ File: auth/login.py ║
║ Type: function | Lines: 45-67 ║
║ Name: authenticate_user ║
║ Similarity: 0.8523 ║
╠════════════════════════════════════════════════════╣
║ def authenticate_user(username, password): ║
║ # Verify user credentials... ║
╚════════════════════════════════════════════════════╝

Found 5 results in 0.3s
```

### Long-Term Memory

Meton maintains a persistent semantic memory system across sessions. Memories are automatically captured from conversations and can be managed manually.

#### `/memory stats`
Show memory system statistics.

```
You: /memory stats

═══ Long-Term Memory Statistics ═══

Total Memories: 42
Average Importance: 0.68

Memories by Type:
 • fact: 23
 • preference: 12
 • skill: 7

Most Accessed:
 • User prefers async/await patterns
 Accessed: 8 times, Importance: 0.85
 • Project uses pytest for testing
 Accessed: 5 times, Importance: 0.72

Recent Memories:
 • [skill] How to implement retry logic with exponential backoff
 2025-11-14T10:23:15
```

#### `/memory search <query>`
Search memories semantically.

```
You: /memory search authentication

 Searching memories for: authentication

1. [preference] (importance: 0.85)
 User prefers JWT tokens over session cookies for API auth
 Accessed: 3 times | 2025-11-12T14:30:22
 Tags: auth, jwt, api

2. [fact] (importance: 0.73)
 Project uses bcrypt for password hashing
 Accessed: 2 times | 2025-11-10T09:15:44
 Tags: auth, security, password

Found 2 memories
```

#### `/memory add <content>`
Manually add a memory.

```
You: /memory add I prefer using type hints for all function parameters

 Adding memory...

 Memory added
ID: mem_abc123... | Type: preference
```

#### `/memory export [json|csv]`
Export all memories to a file.

```
You: /memory export json

 Exporting memories to JSON...

 Memories exported
File: /media/development/projects/meton/memory/memories_export_20251114.json
```

#### `/memory consolidate`
Merge similar or duplicate memories.

```
You: /memory consolidate

 Consolidating similar memories...

 Consolidated 3 duplicate memories
```

#### `/memory decay`
Apply decay to old, rarely accessed memories.

```
You: /memory decay

 Applying decay to old memories...

 Applied decay to 5 memories
```

Memory System Features:
- Automatic capture from conversations
- Semantic similarity search using embeddings
- Importance scoring based on access frequency
- Auto-consolidation of duplicates (threshold: 0.95)
- Time-based decay for old memories
- Type classification: fact, preference, skill
- Tag extraction for easy retrieval
- 10,000 memory capacity

### Cross-Session Learning

Learn patterns across sessions to improve future interactions. Analyzes query types, tool usage, errors, and successes.

#### `/learn analyze`
Analyze recent sessions for patterns and generate insights.

```
You: /learn analyze

 Analyzing recent sessions for patterns...

 Generated 3 new insights

Frequent Testing Queries Detected
 Impact: MEDIUM
 User frequently asks about testing strategies and pytest usage.
 Consider proactively suggesting testing patterns.
 ID: insight_xyz789...

High Error Rate with File Paths
 Impact: HIGH
 Multiple file path errors detected in last 30 days.
 Recommend verifying paths before file operations.
 ID: insight_abc456...
```

#### `/learn insights`
Show all generated insights.

```
You: /learn insights

═══ Learning Insights ═══

High Error Rate with File Paths Pending
 Type: warning | Impact: high
 Multiple file path errors detected. Verify paths first.
 -> Apply with: /learn apply insight_abc456
 ID: insight_abc456 | Created: 2025-11-14T11:20:33

Frequent Testing Queries APPLIED
 Type: improvement | Impact: medium
 User frequently asks about testing. Proactive suggestions enabled.
 ID: insight_xyz789 | Created: 2025-11-13T09:15:22
```

#### `/learn patterns`
Show detected patterns by type.

```
You: /learn patterns

═══ Detected Patterns ═══

QUERY Patterns:
 • User frequently asks about async programming
 Occurrences: 8 | Confidence: 0.85
 Examples: How to handle async errors in Python?...

 • User often requests testing advice
 Occurrences: 6 | Confidence: 0.78
 Examples: Best practices for pytest fixtures...

TOOL_USAGE Patterns:
 • High usage of file_operations tool
 Occurrences: 45 | Confidence: 0.92
 Examples: file_operations called 45 times...
```

#### `/learn apply <id>`
Apply a specific insight.

```
You: /learn apply insight_abc456

 Applying insight...

 Insight applied: High Error Rate with File Paths
Paths will now be verified before file operations.
```

#### `/learn summary`
Show learning summary and statistics.

```
You: /learn summary

═══ Cross-Session Learning Summary ═══

Total Patterns: 12
Insights Generated: 5
Insights Applied: 2
Learning Velocity: 2.4 patterns/week

Top Patterns (by confidence):
 • High usage of file_operations tool
 Confidence: 0.92 | Occurrences: 45
 • User frequently asks about async programming
 Confidence: 0.85 | Occurrences: 8

Recent Insights:
 High Error Rate with File Paths
 Impact: high | Type: warning
 Frequent Testing Queries
 Impact: medium | Type: improvement
```

Learning System Features:
- Pattern detection across 4 types: queries, tool usage, errors, successes
- Confidence scoring based on frequency and consistency
- Impact assessment (high, medium, low)
- Actionable insights with recommendations
- Auto-application of high-confidence, low-risk insights (configurable)
- Learning velocity tracking (patterns/week)
- 30-day lookback window (configurable)
- Minimum 5 occurrences for pattern detection

### Session Control

#### `/verbose on|off`
Toggle verbose mode to show/hide the agent's thought process.

Verbose OFF (default):
```
You: What files can you see?
 Thinking...

 Assistant:
I can see the following files...
```

Verbose ON
```
You: What files can you see?

 THOUGHT: I need to list the current working directory
 ACTION: file_operations
 INPUT: {"action": "list", "path": "/media/development/projects/meton"}

 Executing: file_operations
OK Result: OK Contents of /media/development/projects/meton...

 Assistant:
I can see the following files...
```

#### `/reload`
Reload configuration from config.yaml without restarting Meton. Useful for testing config changes.

```
You: /reload
 Reloading configuration...
OK Configuration reloaded successfully
 Note: Model will switch on next query
```

#### `/exit`, `/quit`, or `/q`
Exit Meton gracefully. Auto-saves conversation if enabled.

```
You: /exit
 Shutting down...
 OK Conversation saved

 Goodbye!
```

---

## Natural Language Queries

Meton understands natural language queries and uses tools to help you. Here are examples:

### File System Operations

List Directory Contents:
```
You: What files can you see?
You: Show me what's in the core directory
You: List all Python files in this project
```

Read Files:
```
You: Read config.yaml
You: Show me the contents of core/agent.py
You: What's in README.md?
```

File Information:
```
You: Check if setup.sh exists
You: How big is core/models.py?
You: Tell me about the core directory
```

### Code Understanding

Explain Code:
```
You: Explain how the agent loop detection works
You: What does the ModelManager class do?
You: Describe the file operations tool
```

Find Patterns:
```
You: Where is the Config class defined?
You: Show me all the error handling in core/agent.py
You: Find the loop detection logic
```

### Semantic Code Search (with Indexing)

First, index your codebase:
```
You: /index /path/to/your/project
```

Then ask natural language questions:
```
You: How does authentication work in this codebase?
You: Find code that handles database connections
You: Show me error handling patterns
You: Where is user input validated?
You: What functions deal with file uploads?
```

The agent automatically uses semantic search:
- Recognizes code understanding questions
- Searches indexed codebase with embeddings
- Returns relevant code chunks with file paths and line numbers
- Provides context-aware explanations

Example workflow:
```
You: How does the login system work?

 THOUGHT: This is a code understanding question - using codebase_search
 ACTION: codebase_search
 INPUT: {"query": "login authentication user credentials"}

 Assistant:
Based on the codebase search results:

1. auth/login.py:45-67 (authenticate_user function):
 - Validates user credentials against database
 - Uses bcrypt for password hashing
 - Returns JWT token on success

2. auth/session.py:23-40 (create_session function):
 - Creates session with 24-hour expiry
 - Stores in Redis cache
 - Returns session token

The login flow: User submits credentials -> authenticate_user validates
-> create_session generates token -> Token returned to client
```

### Code Execution

Run Python Code:
```
You: Run this code: print(2 + 2)
You: Execute: import math; print(math.pi)
You: Test this function: def fib(n): return n if n < 2 else fib(n-1) + fib(n-2); print(fib(10))
```

Features:
- Subprocess isolation for safety
- Timeout protection (5 seconds default)
- Allowed imports: math, json, datetime, collections, itertools, etc.
- Blocked imports: os, sys, subprocess, socket (no file/network access)

### Web Search (opt-in)

Enable web search first:
```
You: /web on
```

Then search:
```
You: Search for Python asyncio best practices
You: Find information about FAISS vector databases
You: Look up LangChain documentation
```

Note: Web search is disabled by default for privacy. Enable only when needed.

### Multi-Step Workflows

Meton can perform multi-step reasoning:

```
You: Find all Python files in core/, read agent.py, and explain the ReAct pattern implementation

 THOUGHT: I need to first list the core directory to find Python files
 ACTION: file_operations
...

 THOUGHT: Now I'll read the agent.py file
 ACTION: file_operations
...

 THOUGHT: Based on the code, I can now explain the ReAct pattern
 ACTION: NONE

 Assistant:
The ReAct pattern in agent.py is implemented using LangGraph's StateGraph...
```

---

## Example Sessions

### Session 1: Exploring a New Codebase

```
You: What files can you see?
 Assistant:
I can see 16 files including core modules (agent.py, models.py, config.py), documentation (README.md, STATUS.md), configuration (config.yaml), and test files.

You: Tell me about the agent system

 Assistant:
The agent system uses LangGraph's ReAct pattern with loop detection. It has reasoning, tool execution, and observation nodes. The system can perform multi-step tasks and includes safeguards against infinite loops.

You: /search loop

Search Results for 'loop' (2 matches)
2. ASSISTANT: ...includes safeguards against infinite **loops**...

You: /save
OK Conversation saved
```

### Session 2: Debugging Configuration

```
You: Read config.yaml

 Assistant:
[Shows config file contents with models, tools, conversation settings...]

You: /model quick
OK Switched to model: mistral:latest

You: test query with quick model

 Assistant:
[Faster response with smaller model]

You: /model primary
OK Switched to model: qwen2.5:32b-instruct-q5_K_M

You: /reload
OK Configuration reloaded successfully
```

### Session 3: Using Long-Term Memory

```
You: /memory stats

═══ Long-Term Memory Statistics ═══
Total Memories: 15
Average Importance: 0.71

You: Show me how to implement authentication

 Assistant:
[Provides authentication implementation guidance]

You: /memory search auth

 Searching memories for: auth

1. [preference] User prefers JWT tokens for API auth
 Importance: 0.82

2. [fact] Project uses bcrypt for password hashing
 Importance: 0.75

You: /memory add I prefer using refresh tokens with 7-day expiry

 Memory added
Type: preference
```

### Session 4: Cross-Session Learning

```
You: /learn analyze

 Analyzing recent sessions for patterns...

 Generated 2 new insights

Frequent Authentication Questions
 Impact: MEDIUM
 Consider creating authentication templates

You: /learn patterns

═══ Detected Patterns ═══

QUERY Patterns:
 • User frequently asks about authentication
 Occurrences: 7 | Confidence: 0.82

 • User often requests async patterns
 Occurrences: 5 | Confidence: 0.75

You: /learn insights

High File Operations Usage Pending
 Type: optimization | Impact: medium
 -> Apply with: /learn apply insight_123

You: /learn apply insight_123

 Insight applied
File operations will be optimized
```

### Session 5: Web UI Workflow

```bash
# Terminal 1: Launch Web UI
python launch_web.py --port 7860

# Terminal 2: Or with authentication
python launch_web.py --auth admin:secretpass --share

# Browser: Navigate to http://localhost:7860
# Features available:
# - Chat with Meton
# - Upload files for analysis
# - View conversation history
# - Export sessions to JSON/CSV
# - Real-time analytics with charts
# - Multi-session management
# - Settings configuration
```

---

## Tips and Tricks

### 1. Use Verbose Mode for Debugging
When agent behavior seems strange, enable verbose mode to see its reasoning:
```
/verbose on
```

### 2. Model Selection Strategy
-qwen2.5:32b-instruct-q5_K_M (primary) - Best quality, reasoning (~10-20s per response)
-llama3.1:8b (fallback) - Good balance (~5-10s per response)
-mistral:latest (quick) - Fastest, adequate quality (~2-5s per response)

### 3. Search Before Re-Asking
If you think you asked something similar before, use `/search` to find it:
```
/search "config"
```

### 4. Clear Context When Changing Topics
If switching to an unrelated task, clear the conversation for better focus:
```
/clear
```

### 5. Save Important Sessions
Before experimenting or if you have valuable context:
```
/save
```

### 6. Use Aliases for Model Switching
Instead of typing full model names:
```
/model quick # Fast testing
/model primary # Production quality
```

---

## Troubleshooting

### Agent Hits Max Iterations

Symptom: "I've reached the maximum number of reasoning steps"

Solution:
1. Try rephrasing your question more specifically
2. Break complex queries into smaller steps
3. Check if the question requires information outside allowed paths

### Agent Doesn't Find Files

Symptom: Agent says it can't access a file you know exists

Solution:
1. Check `/status` to see current working directory
2. Verify file is in an allowed path (see config.yaml)
3. Use explicit paths starting from working directory

### Slow Responses

Symptom: Queries take 15+ seconds

Solution:
1. Switch to faster model: `/model quick`
2. Ensure Ollama is running: `ollama list`
3. Check GPU utilization: `nvidia-smi`
4. Reduce max_tokens in config.yaml

### Loop Detection Triggers

Symptom: " LOOP DETECTED" message appears

Solution:
- This is a feature, not a bug
- Agent tried to repeat the same action
- Loop detection prevented infinite loop
- Result was returned automatically
- Try rephrasing if result isn't satisfactory

### Config Changes Not Taking Effect

Symptom: Modified config.yaml but Meton still uses old settings

Solution:
```
/reload
```
Or restart Meton for complex changes.

---

## Advanced Usage

### Custom Tool Paths

Edit `config.yaml` to add allowed paths:

```yaml
tools:
 file_ops:
 enabled: true
 allowed_paths:
 - /media/development/projects/meton
 - /media/development/projects/your_project # Add this
 blocked_paths:
 - /etc/
 - /sys/
```

Then reload: `/reload`

### Conversation Persistence

Conversations auto-save to `conversations/` directory as JSON files.

Load a previous conversation:
Currently manual - copy JSON file to check session ID, then restart Meton.

Find conversation files:
```bash
ls conversations/
# conversation_3c8a9f2d-4b1e-41e2-8e45-8e9d8f8d8f8d.json
```

### Custom Models

Add new Ollama models to config.yaml:

```yaml
models:
 primary: "deepseek-coder:33b" # Use different model
 fallback: "llama3.1:8b"
 quick: "mistral:latest"
```

Pull the model first:
```bash
ollama pull deepseek-coder:33b
```

Then reload Meton:
```
/reload
```

---

## Keyboard Shortcuts

- Ctrl+C - Interrupts current query (use `/exit` to quit properly)
- Ctrl+D - EOF, exits Meton (same as `/exit`)
- Up/Down arrows - Command history (if terminal supports it)

---

## Best Practices

1. **Start Broad, Then Narrow
 ```
 You: What files can you see?
 You: Tell me about core/
 You: Read core/agent.py
 You: Explain the loop detection in agent.py
 ```

2. **Use Status to Confirm Context
 ```
 /status
 # Check current model and message count
 ```

3. **Search Before Asking Again
 ```
 /search agent
 # Find previous discussion about agents
 ```

4. **Save After Important Findings
 ```
 /save
 # Preserve your work
 ```

5. **Clear When Changing Topics
 ```
 /clear
 # Fresh start for new topic
 ```

6. **Use Verbose Mode for Understanding
 ```
 /verbose on
 # See how agent thinks
 ```

7. **Leverage Long-Term Memory
 ```
 /memory search <topic>
 # Find relevant memories before asking
 ```

8. **Monitor Learning Patterns
 ```
 /learn summary
 # Check what patterns Meton has learned
 ```

9. **Use Web UI for Visualization
 ```bash
 python launch_web.py
 # Visual interface with charts and multi-session support
 ```

10. **Export Your Work
 ```
 /memory export json
 # Save memories for backup or analysis
 ```

---

## Getting Help

- In-session help `/help`
- GitHub Issues Report problems at project repository
- Documentation Check STATUS.md for current features
- Architecture See ARCHITECTURE.md for system design

---

## Next Steps

Now that you know how to use Meton:

1. **Index your codebase - Run `/index /path/to/project` for semantic search
2. **Experiment with models - Try `primary`, `fallback`, and `quick` models
3. **Test multi-step queries - Let Meton break down complex tasks
4. **Explore the Web UI - Launch `python launch_web.py` for visual interface
5. **Build memory - Use Meton regularly to build cross-session intelligence
6. **Monitor learning - Check `/learn summary` to see pattern detection
7. **Export sessions - Save memories and conversations for analysis
8. **Read the docs - Check ARCHITECTURE.md and STATUS.md for details

Advanced Features to Explore:
- Long-Term Memory Builds understanding of your preferences and project patterns
- Cross-Session Learning Improves recommendations based on usage patterns
- Web UI Analytics Visual charts showing tool usage, response times, patterns
- Git Integration AI-powered code review and commit message generation
- Multi-Agent System Coordinate multiple specialized agents (configurable)
- Self-Reflection Automatic quality analysis and improvement (configurable)

Happy coding with Meton! 
