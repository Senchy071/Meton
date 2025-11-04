# Example Queries for Meton

Common useful queries to get you started with Meton.

---

## File System Exploration

### Basic Listing
```
What files can you see?
Show me all files in the current directory
List everything here
```

### Directory-Specific
```
What's in the core directory?
List files in core/
Show me the contents of tools/
What Python files are in this project?
```

### File Reading
```
Read config.yaml
Show me the contents of README.md
What's in core/agent.py?
Display the setup script
```

### File Information
```
Does config.yaml exist?
How big is core/models.py?
Tell me about the conversations directory
Check if test_agent.py exists
```

---

## Code Understanding

### Architecture Questions
```
Explain how the agent system works
What is the ReAct pattern?
How does loop detection prevent infinite loops?
Describe the conversation management system
```

### Class/Function Understanding
```
What does the ModelManager class do?
Explain the FileOperationsTool
How does the Config class work?
What is MetonAgent responsible for?
```

### Implementation Details
```
How is thread safety implemented in ConversationManager?
Where is path validation done?
What happens when the agent hits max iterations?
How does model switching work?
```

---

## Configuration Questions

```
Read config.yaml and explain the settings
What models are configured?
What paths am I allowed to access?
Show me the conversation settings
What's the maximum context window?
```

---

## Debugging & Troubleshooting

```
Read logs/meton_<today>.log and find errors
What errors occurred today?
Show me the last 10 log entries
Find warnings in the log file
```

---

## Documentation Queries

```
Read README.md and summarize the project
What's in STATUS.md?
Explain USAGE.md
Show me the quick reference
Read ARCHITECTURE.md and describe the system design
```

---

## Multi-Step Workflows

### Codebase Overview
```
List all Python files in core/, then describe each module's purpose
```

### Deep Dive
```
Find all classes in core/agent.py and explain each one
```

### Configuration Audit
```
Read config.yaml, check if referenced paths exist, and verify settings
```

### Documentation Check
```
List all markdown files, then summarize each one
```

---

## Testing & Validation

```
Read test_agent.py and explain what it tests
What test files exist?
Show me the test results in STATUS.md
```

---

## Comparison Queries

```
Compare core/models.py and core/conversation.py - what patterns do they share?
What's the difference between primary and fallback models?
```

---

## Search & Find

```
Find where loop detection is implemented
Search for error handling in core/agent.py
Where is the Config class defined?
Find all TODO comments in the codebase
```

---

## Planning & Analysis

```
Based on the codebase, what would be good next features to add?
What security measures are in place?
Analyze the error handling strategy
```

---

## Tips for Effective Queries

1. **Start Broad**: Begin with "What files can you see?" to understand context
2. **Be Specific**: "Read core/agent.py" is better than "show me some code"
3. **Multi-Step**: Combine actions - "List Python files and describe each"
4. **Use Context**: Follow-up questions work well - agent remembers conversation
5. **Verify First**: Check if files exist before reading
6. **Search History**: Use `/search` to find previous answers

---

## Advanced Patterns

### Conditional Queries
```
If config.yaml exists, read it and explain the model settings
```

### Sequential Analysis
```
First list all test files, then read test_agent.py, then explain what it tests
```

### Comparative Analysis
```
Read both test_models.py and test_conversation.py and compare their testing approaches
```

---

## Semantic Code Search (After Indexing)

### Index Your Codebase First
```
/index /path/to/your/project
```

### Natural Language Code Queries
```
How does authentication work in this codebase?
Find all database connection code
Show me error handling patterns
Where is user input validated?
What functions handle file uploads?
Explain the caching mechanism
Find all API endpoint definitions
Where are database migrations defined?
Show me the logging implementation
```

### Direct Search Testing
```
/csearch authentication
/csearch database connection
/csearch error handling
/csearch validation
```

### Architecture Questions
```
How is the database layer structured?
What's the request/response flow?
Explain the middleware stack
How does dependency injection work here?
```

---

## Code Execution

### Simple Calculations
```
Run this code: print(2 + 2)
Execute: print(sum([1, 2, 3, 4, 5]))
Calculate fibonacci of 10
```

### With Imports
```
Run: import math; print(math.pi)
Execute: import json; print(json.dumps({"key": "value"}))
Test: from datetime import datetime; print(datetime.now())
```

### Function Testing
```
Run this: def factorial(n): return 1 if n <= 1 else n * factorial(n-1); print(factorial(5))
```

---

## Web Search (Opt-in)

### Enable First
```
/web on
```

### Search Queries
```
Search for Python asyncio best practices
Find information about FAISS vector databases
Look up LangChain documentation
Search for pytest fixtures guide
Find SQLAlchemy relationship patterns
```

### Library Documentation
```
Search for FastAPI query parameters
Find Pydantic validation examples
Look up Rich table formatting docs
```

---

## What NOT to Ask

### Out of Scope
- ❌ "Install package X..." (no package management)
- ❌ "Make an API call to..." (local only, no network from code execution)
- ❌ "Deploy this to production..." (local development tool)
- ❌ "Modify system files..." (restricted for security)

### Better Alternatives
- ✓ "Read README.md and find installation instructions"
- ✓ "Show me the code in core/models.py that handles model loading"
- ✓ "What packages are listed in requirements.txt?"
- ✓ "Search for FastAPI documentation" (with /web on)

---

## Example Complete Workflows

See [example_workflows.md](example_workflows.md) for full multi-turn conversation examples.

---

*These queries work best with the agent in default mode. Enable `/verbose on` to see detailed reasoning.*
