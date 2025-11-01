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

## Commands Reference

Meton provides 12 interactive commands to control your session:

### Information Commands

#### `/help` or `/h`
Show the complete list of available commands.

```
You: /help

╔═══════════════════════════════════════╗
║  Available Commands                   ║
╠═══════════════════════════════════════╣
║  /help, /h        Show help           ║
║  /status          Show current status ║
║  ...                                  ║
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
│ Model:        codellama:34b           │
│ Session:      3c8a9f2d-4b1e...        │
│ Messages:     12                      │
│ Tools:        file_operations         │
│ Max Iter:     10                      │
│ Verbose:      OFF                     │
╰───────────────────────────────────────╯
```

### Model Management

#### `/models`
List all available Ollama models and show which one is currently active.

```
You: /models

╔════════════════════════════════════╗
║  Available Models                  ║
╠════════════════════════════════════╣
║  codellama:34b    ✓ Current        ║
║  codellama:13b                     ║
║  codellama:7b                      ║
╚════════════════════════════════════╝
```

#### `/model <name>`
Switch to a different model. Accepts full model names or aliases:
- `primary` → codellama:34b (best quality)
- `fallback` → codellama:13b (balanced)
- `quick` → codellama:7b (fastest)

```
You: /model quick
✓ Switched to model: codellama:7b

You: /model codellama:34b
✓ Switched to model: codellama:34b
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

2. ASSISTANT: The **agent** system uses LangGraph for ReAct pattern...
5. USER: How does the **agent** loop detection work?
6. ASSISTANT: The **agent** detects loops by comparing...

Total matches: 3/12 messages
```

#### `/clear` or `/c`
Clear the entire conversation history. Requires confirmation.

```
You: /clear
Clear conversation history? [y/n] (n): y
✓ Conversation history cleared
```

#### `/save`
Manually save the current conversation to disk (auto-save happens on exit if enabled in config).

```
You: /save
💾 Saving conversation...
✓ Conversation saved: conversation_3c8a9f2d.json
```

### Tool Management

#### `/tools`
List all available tools with descriptions.

```
You: /tools

╔═══════════════════════════════════════════════╗
║  Available Tools                              ║
╠═══════════════════════════════════════════════╣
║  file_operations  Perform file operations...  ║
╚═══════════════════════════════════════════════╝
```

### Session Control

#### `/verbose on|off`
Toggle verbose mode to show/hide the agent's thought process.

**Verbose OFF** (default):
```
You: What files can you see?
🤔 Thinking...

💬 Assistant:
I can see the following files...
```

**Verbose ON**:
```
You: What files can you see?

💭 THOUGHT: I need to list the current working directory
🎯 ACTION: file_operations
📥 INPUT: {"action": "list", "path": "/media/development/projects/meton"}

🔧 Executing: file_operations
✓ Result: ✓ Contents of /media/development/projects/meton...

💬 Assistant:
I can see the following files...
```

#### `/reload`
Reload configuration from config.yaml without restarting Meton. Useful for testing config changes.

```
You: /reload
🔄 Reloading configuration...
✓ Configuration reloaded successfully
  Note: Model will switch on next query
```

#### `/exit`, `/quit`, or `/q`
Exit Meton gracefully. Auto-saves conversation if enabled.

```
You: /exit
🔄 Shutting down...
  ✓ Conversation saved

👋 Goodbye!
```

---

## Natural Language Queries

Meton understands natural language queries and uses tools to help you. Here are examples:

### File System Operations

**List Directory Contents:**
```
You: What files can you see?
You: Show me what's in the core directory
You: List all Python files in this project
```

**Read Files:**
```
You: Read config.yaml
You: Show me the contents of core/agent.py
You: What's in README.md?
```

**File Information:**
```
You: Check if setup.sh exists
You: How big is core/models.py?
You: Tell me about the core directory
```

### Code Understanding

**Explain Code:**
```
You: Explain how the agent loop detection works
You: What does the ModelManager class do?
You: Describe the file operations tool
```

**Find Patterns:**
```
You: Where is the Config class defined?
You: Show me all the error handling in core/agent.py
You: Find the loop detection logic
```

### Multi-Step Workflows

Meton can perform multi-step reasoning:

```
You: Find all Python files in core/, read agent.py, and explain the ReAct pattern implementation

💭 THOUGHT: I need to first list the core directory to find Python files
🎯 ACTION: file_operations
...

💭 THOUGHT: Now I'll read the agent.py file
🎯 ACTION: file_operations
...

💭 THOUGHT: Based on the code, I can now explain the ReAct pattern
🎯 ACTION: NONE

💬 Assistant:
The ReAct pattern in agent.py is implemented using LangGraph's StateGraph...
```

---

## Example Sessions

### Session 1: Exploring a New Codebase

```
You: What files can you see?
💬 Assistant:
I can see 16 files including core modules (agent.py, models.py, config.py), documentation (README.md, STATUS.md), configuration (config.yaml), and test files.

You: Tell me about the agent system

💬 Assistant:
The agent system uses LangGraph's ReAct pattern with loop detection. It has reasoning, tool execution, and observation nodes. The system can perform multi-step tasks and includes safeguards against infinite loops.

You: /search loop

Search Results for 'loop' (2 matches)
2. ASSISTANT: ...includes safeguards against infinite **loops**...

You: /save
✓ Conversation saved
```

### Session 2: Debugging Configuration

```
You: Read config.yaml

💬 Assistant:
[Shows config file contents with models, tools, conversation settings...]

You: /model quick
✓ Switched to model: codellama:7b

You: test query with quick model

💬 Assistant:
[Faster response with smaller model]

You: /model primary
✓ Switched to model: codellama:34b

You: /reload
✓ Configuration reloaded successfully
```

---

## Tips and Tricks

### 1. Use Verbose Mode for Debugging
When agent behavior seems strange, enable verbose mode to see its reasoning:
```
/verbose on
```

### 2. Model Selection Strategy
- **codellama:34b** (primary) - Best quality, slower (~10-20s per response)
- **codellama:13b** (fallback) - Good balance (~5-10s per response)
- **codellama:7b** (quick) - Fastest, adequate quality (~2-5s per response)

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
/model quick      # Fast testing
/model primary    # Production quality
```

---

## Troubleshooting

### Agent Hits Max Iterations

**Symptom:** "I've reached the maximum number of reasoning steps"

**Solution:**
1. Try rephrasing your question more specifically
2. Break complex queries into smaller steps
3. Check if the question requires information outside allowed paths

### Agent Doesn't Find Files

**Symptom:** Agent says it can't access a file you know exists

**Solution:**
1. Check `/status` to see current working directory
2. Verify file is in an allowed path (see config.yaml)
3. Use explicit paths starting from working directory

### Slow Responses

**Symptom:** Queries take 15+ seconds

**Solution:**
1. Switch to faster model: `/model quick`
2. Ensure Ollama is running: `ollama list`
3. Check GPU utilization: `nvidia-smi`
4. Reduce max_tokens in config.yaml

### Loop Detection Triggers

**Symptom:** "🚫 LOOP DETECTED" message appears

**Solution:**
- This is a feature, not a bug
- Agent tried to repeat the same action
- Loop detection prevented infinite loop
- Result was returned automatically
- Try rephrasing if result isn't satisfactory

### Config Changes Not Taking Effect

**Symptom:** Modified config.yaml but Meton still uses old settings

**Solution:**
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
      - /media/development/projects/your_project  # Add this
    blocked_paths:
      - /etc/
      - /sys/
```

Then reload: `/reload`

### Conversation Persistence

Conversations auto-save to `conversations/` directory as JSON files.

**Load a previous conversation:**
Currently manual - copy JSON file to check session ID, then restart Meton.

**Find conversation files:**
```bash
ls conversations/
# conversation_3c8a9f2d-4b1e-41e2-8e45-8e9d8f8d8f8d.json
```

### Custom Models

Add new Ollama models to config.yaml:

```yaml
models:
  primary_model: "deepseek-coder:33b"     # Use different model
  fallback_model: "codellama:13b"
  quick_model: "codellama:7b"
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

- **Ctrl+C** - Interrupts current query (use `/exit` to quit properly)
- **Ctrl+D** - EOF, exits Meton (same as `/exit`)
- **Up/Down arrows** - Command history (if terminal supports it)

---

## Best Practices

1. **Start Broad, Then Narrow**
   ```
   You: What files can you see?
   You: Tell me about core/
   You: Read core/agent.py
   You: Explain the loop detection in agent.py
   ```

2. **Use Status to Confirm Context**
   ```
   /status
   # Check current model and message count
   ```

3. **Search Before Asking Again**
   ```
   /search agent
   # Find previous discussion about agents
   ```

4. **Save After Important Findings**
   ```
   /save
   # Preserve your work
   ```

5. **Clear When Changing Topics**
   ```
   /clear
   # Fresh start for new topic
   ```

6. **Use Verbose Mode for Understanding**
   ```
   /verbose on
   # See how agent thinks
   ```

---

## Getting Help

- **In-session help**: `/help`
- **GitHub Issues**: Report problems at project repository
- **Documentation**: Check STATUS.md for current features
- **Architecture**: See ARCHITECTURE.md for system design

---

## Next Steps

Now that you know how to use Meton:

1. Try exploring your own codebase
2. Experiment with different models
3. Test multi-step queries
4. Check out example workflows in examples/
5. Read ARCHITECTURE.md to understand the system

Happy coding with Meton! 🧠⚡
