# Example Workflows for Meton

Complete multi-turn conversation examples showing effective use of Meton.

---

## Workflow 1: Understanding a New Codebase

**Scenario:** You just cloned Meton and want to understand how it works.

```
$ ./meton

You: What files can you see?

💬 Assistant:
I can see 16 files and 7 directories in /media/development/projects/meton:

Files:
- config.yaml (configuration)
- README.md, STATUS.md, USAGE.md (documentation)
- meton.py (entry point)
- cli.py (interactive interface)
- setup.sh (installation script)
- requirements.txt (dependencies)
- test files (test_*.py)

Directories:
- core/ (main modules)
- tools/ (tool implementations)
- utils/ (utilities)
- conversations/ (saved sessions)
- logs/ (log files)

You: Tell me about the core directory

💬 Assistant:
The core/ directory contains the main system modules:
- agent.py - LangGraph ReAct agent implementation
- models.py - Ollama model manager
- conversation.py - Thread-safe conversation persistence
- config.py - Pydantic-based configuration

You: Read core/agent.py and explain the loop detection feature

💬 Assistant:
[Reads file and explains loop detection system]
The loop detection prevents infinite loops by:
1. Comparing current tool call with previous call
2. If action and input match, it forces completion
3. Returns the existing tool result automatically
4. Shows "🚫 LOOP DETECTED" in verbose mode

You: /save
✓ Conversation saved: conversation_abc123.json

You: /exit
```

**Key Techniques:**
- Started broad (What files?)
- Drilled down (Tell me about core/)
- Specific deep dive (Read and explain loop detection)
- Saved for later reference

---

## Workflow 2: Debugging Configuration

**Scenario:** Your Meton isn't using the right model.

```
You: /status

╭─── Current Status ───────────────────╮
│ Model:        codellama:13b          │  ← Wrong model!
│ Session:      def456...              │
│ Messages:     1                      │
╰──────────────────────────────────────╯

You: Read config.yaml and show me the model settings

💬 Assistant:
The config.yaml shows:
```yaml
models:
  primary_model: "codellama:34b"
  fallback_model: "codellama:13b"
  quick_model: "codellama:7b"
```

The system is configured for codellama:34b as primary, but you're using the fallback model.

You: /models

╔════════════════════════════════════╗
║  Available Models                  ║
╠════════════════════════════════════╣
║  codellama:34b                     ║
║  codellama:13b    ✓ Current        ║
║  codellama:7b                      ║
╚════════════════════════════════════╝

You: /model primary
✓ Switched to model: codellama:34b

You: /status

╭─── Current Status ───────────────────╮
│ Model:        codellama:34b          │  ← Fixed!
│ ...                                  │
╰──────────────────────────────────────╯
```

**Key Techniques:**
- Used `/status` to diagnose
- Read config to understand expected behavior
- Listed models to see available options
- Switched to correct model
- Verified with `/status` again

---

## Workflow 3: Feature Development Planning

**Scenario:** Planning to add a new tool to Meton.

```
You: Read ARCHITECTURE.md and explain how to add a new tool

💬 Assistant:
To add a new tool to Meton:

1. Create tool class in tools/ inheriting from MetonBaseTool
2. Implement _run() method with tool logic
3. Register in cli.py initialization
4. Update config.yaml if needed
5. Test the integration

[Shows code examples from ARCHITECTURE.md]

You: Show me how FileOperationsTool is implemented

💬 Assistant:
[Reads tools/file_ops.py and explains structure]
FileOperationsTool:
- Has 6 actions (read, write, list, create_dir, exists, get_info)
- Uses JSON input parsing
- Implements security checks (path validation)
- Returns formatted strings
- Handles errors gracefully

You: Read tools/base.py

💬 Assistant:
[Reads base tool class]
MetonBaseTool provides:
- Config integration
- Logger setup
- LangChain BaseTool inheritance
- Common initialization pattern

You: Based on these examples, outline what a WebSearchTool would look like

💬 Assistant:
A WebSearchTool following Meton patterns would:

1. Inherit from MetonBaseTool
2. Parse JSON with {"query": "search term", "max_results": 5}
3. Implement search using requests library
4. Return formatted results
5. Add to config.yaml:
```yaml
tools:
  web_search:
    enabled: true
    max_results: 5
    timeout: 10
```
6. Register in CLI with other tools

[Provides detailed code outline]

You: /save
✓ Conversation saved
```

**Key Techniques:**
- Read architecture documentation first
- Examined existing implementation
- Looked at base class pattern
- Asked agent to synthesize knowledge into new feature plan
- Saved for implementation reference

---

## Workflow 4: Performance Optimization

**Scenario:** Responses are too slow, need to optimize.

```
You: /status

╭─── Current Status ───────────────────╮
│ Model:        codellama:34b          │  ← Slow model
│ Messages:     15                     │  ← Long context
│ Max Iter:     10                     │
╰──────────────────────────────────────╯

You: Read config.yaml and show conversation settings

💬 Assistant:
```yaml
conversation:
  max_history: 10
  auto_save: true
```

Your context window is set to 10 messages (20 with user+assistant pairs).
With 15 messages, some are being trimmed.

You: /model quick
✓ Switched to model: codellama:7b

You: test query - what files can you see?

💬 Assistant:
[Much faster response - ~3 seconds instead of ~15 seconds]
I can see 16 files in the current directory...

You: That was much faster! What's the trade-off?

💬 Assistant:
Using codellama:7b (quick model) provides:
- 5-8x faster responses
- Lower memory usage (2-4GB vs 8-16GB VRAM)
- Adequate quality for simple queries
- May struggle with complex reasoning

Trade-offs:
- Less detailed explanations
- Shorter responses
- May need more explicit prompting
- Better for exploration, worse for analysis

You: /model primary
✓ Switched to model: codellama:34b

You: For important analysis use primary, for quick checks use quick - got it!
```

**Key Techniques:**
- Checked status to diagnose slow performance
- Read config to understand settings
- Tested with quick model
- Asked agent to explain trade-offs
- Learned when to use which model

---

## Workflow 5: Error Investigation

**Scenario:** Something went wrong, need to investigate.

```
You: /verbose on
✓ Verbose mode ON

You: Read the latest log file in logs/

💬 Assistant:
💭 THOUGHT: I need to list the logs directory first to find the latest file
🎯 ACTION: file_operations
📥 INPUT: {"action": "list", "path": "/media/development/projects/meton/logs"}

[Finds latest log file]

💭 THOUGHT: Now I'll read the latest log file
🎯 ACTION: file_operations
📥 INPUT: {"action": "read", "path": "/media/development/projects/meton/logs/meton_2025-10-28.log"}

[Reads and shows log contents with errors highlighted]

You: /search error

Search Results for 'error' (3 matches)
2. ASSISTANT: Found 3 errors in log file...
...

You: Explain the first error you found

💬 Assistant:
The first error at 10:45:23 was:
"FileNotFoundError: config.yaml not found"

This suggests:
1. Config file missing or misnamed
2. Wrong working directory
3. Permissions issue

To fix:
1. Check if config.yaml exists: `ls config.yaml`
2. Verify working directory with `/status`
3. Ensure file permissions allow reading

You: /verbose off
✓ Verbose mode OFF
```

**Key Techniques:**
- Enabled verbose mode to see agent reasoning
- Used multi-step approach (list dir, then read file)
- Used `/search` to find all error mentions
- Asked for specific error explanation
- Got actionable debugging steps

---

## Workflow 6: Documentation Review

**Scenario:** Reviewing project documentation before release.

```
You: List all markdown files in this directory

💬 Assistant:
Found 8 markdown files:
1. README.md - Project overview
2. STATUS.md - Development status
3. USAGE.md - Usage guide
4. ARCHITECTURE.md - System design
5. QUICK_REFERENCE.md - Command cheat sheet
6. CONVERSATION_MANAGER.md - Conversation manager docs
7. INFRASTRUCTURE.md - Infrastructure docs
8. MODEL_MANAGER.md - Model manager docs

You: Read README.md and check if it mentions all these docs

💬 Assistant:
[Reads README.md]
The README mentions:
✓ INFRASTRUCTURE.md
✓ MODEL_MANAGER.md
✓ CONVERSATION_MANAGER.md
✗ USAGE.md - Missing!
✗ ARCHITECTURE.md - Missing!
✗ QUICK_REFERENCE.md - Missing!

Recommendation: Add links to the new documentation files.

You: What section of README.md should I update?

💬 Assistant:
The README has a "Documentation" section around line 164.
You should add:
- USAGE.md - Complete usage guide with examples
- ARCHITECTURE.md - System design and extension guide
- QUICK_REFERENCE.md - One-page command reference

You: Perfect, I'll update it. /save
✓ Conversation saved
```

**Key Techniques:**
- Listed all docs to get overview
- Used agent to cross-reference
- Asked for specific location to update
- Agent provided actionable recommendations

---

## Workflow 7: Quick Testing Across Models

**Scenario:** Testing how different models handle the same query.

```
You: /model quick
✓ Switched to model: codellama:7b

You: Explain the ReAct pattern in one sentence

💬 Assistant:
ReAct combines reasoning and action by having the agent think before acting and observe results before deciding next steps.

You: /model fallback
✓ Switched to model: codellama:13b

You: Explain the ReAct pattern in one sentence

💬 Assistant:
ReAct is an agent pattern that interleaves reasoning traces (thoughts) with action execution and observations, enabling systematic problem-solving through explicit step-by-step decision making.

You: /model primary
✓ Switched to model: codellama:34b

You: Explain the ReAct pattern in one sentence

💬 Assistant:
ReAct (Reasoning and Acting) is an AI agent paradigm that synergistically combines chain-of-thought reasoning with action execution, creating an iterative loop where the agent explicitly articulates its thought process, takes actions using available tools, observes the results, and incorporates those observations into subsequent reasoning steps to solve complex tasks.

You: Interesting - 7B gave basics, 13B gave details, 34B gave comprehensive explanation
```

**Key Techniques:**
- Same query across multiple models
- Observed quality/detail differences
- Understood model selection trade-offs

---

## Tips for Effective Workflows

1. **Use /status frequently** - Know your context
2. **Enable /verbose for debugging** - See agent's thinking
3. **Save important sessions** - `/save` preserves your work
4. **Search before asking** - `/search` finds previous answers
5. **Clear between topics** - `/clear` for fresh context
6. **Choose right model** - quick for exploration, primary for analysis
7. **Multi-step is powerful** - "List files then read agent.py"
8. **Follow-up questions work** - Agent remembers conversation

---

For more query examples, see [example_queries.md](example_queries.md).
For command reference, see [QUICK_REFERENCE.md](../QUICK_REFERENCE.md).
