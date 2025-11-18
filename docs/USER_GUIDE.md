# User Guide

Complete guide to using Meton local AI coding assistant.

---

## Table of Contents
1. [Getting Started](#getting-started)
2. [Interfaces](#interfaces)
3. [Core Features](#core-features)
4. [Skills](#skills)
5. [Tools](#tools)
6. [Advanced Usage](#advanced-usage)
7. [Configuration](#configuration)
8. [Tips & Best Practices](#tips--best-practices)

---

## Getting Started

### First Launch

#### CLI Mode
```bash
# Activate virtual environment
source venv/bin/activate

# Start Meton
python meton.py
```

You'll see:
```
 Meton - Local AI Coding Assistant
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Metis + Ergon = Wisdom in Action

Model: qwen2.5-coder:32b
Type /help for commands
```

#### Web UI Mode
```bash
python launch_web.py

# With options
python launch_web.py --share --port 8080
```

Navigate to: `http://localhost:7860`

### Basic Workflow

1. **Index your project (optional but recommended)
 ```
 /index /path/to/your/project
 ```

2. **Ask questions
 ```
 > How does authentication work in this codebase?
 > Explain this function: [paste code]
 > Find all files related to database connections
 ```

3. **Get code reviews
 ```
 > Review this code:
 def process_data(data):
 return eval(data["query"])
 ```

4. **Generate tests
 ```
 > Generate pytest tests for the authenticate_user function
 ```

---

## Interfaces

### CLI Interface

#### Essential Commands

Help & Status:
- `/help`, `/h` - Show all commands
- `/status` - System status
- `/models` - List available models
- `/tools` - List tools and their status

Model Management:
- `/model <name>` - Switch model
 ```
 /model llama3.1:8b
 /model primary
 /model quick
 ```

Conversation:
- `/history` - Show conversation history
- `/search <keyword>` - Search history
- `/clear`, `/c` - Clear conversation
- `/save` - Save conversation

RAG/Code Search:
- `/index [path]` - Index codebase
 ```
 /index /media/development/projects/myapp
 /index . # Current directory
 ```
- `/csearch "query"` - Test semantic search
- `/index status` - Show index stats
- `/index clear` - Delete index
- `/index refresh` - Re-index last path

Memory & Learning:
- `/memory stats` - Memory statistics
- `/memory search <query>` - Search memories
- `/memory add <content>` - Add manual memory
- `/memory export [json|csv]` - Export memories
- `/learn analyze` - Analyze sessions for patterns
- `/learn insights` - Show generated insights
- `/learn patterns` - Show detected patterns
- `/learn summary` - Learning statistics

Configuration:
- `/profile list [category]` - List profiles
- `/profile use <id>` - Activate profile
- `/profile current` - Show active profile
- `/profile save <name>` - Save current config
- `/profile compare <id1> <id2>` - Compare profiles
- `/reload` - Reload configuration

Export/Import:
- `/export all [file]` - Export complete state
- `/export config [file]` - Export configuration
- `/export memories [file]` - Export memories
- `/export conversations [file]` - Export conversations
- `/export backup [name]` - Create backup archive
- `/import all <file>` - Import complete state
- `/import config <file>` - Import configuration
- `/import backup <file>` - Restore from backup
- `/import validate <file>` - Validate import file

Tools:
- `/web on/off/status` - Control web search
- `/skills list` - List available skills
- `/git status` - Git status
- `/git review` - AI code review

Exit:
- `/exit`, `/quit`, `/q` - Exit Meton

#### Command Examples

```bash
# Check what model you're using
> /status

# Switch to faster model
> /model mistral:7b

# Index your project
> /index /home/user/myproject

# Search indexed code
> /csearch "database connection setup"

# Enable web search
> /web on

# Get memory stats
> /memory stats

# Use a different profile
> /profile use code-review
```

### Web UI

#### Tabs

1. **Chat Tab
 - Main conversation interface
 - Code syntax highlighting
 - File upload (drag & drop)
 - Model selection dropdown
 - Tool toggle switches

2. **Analytics Tab
 - Performance metrics
 - Tool usage statistics
 - Response time charts
 - Error rate tracking

3. **Sessions Tab
 - Session management
 - Load previous sessions
 - Export conversations
 - Clear sessions

4. **Settings Tab
 - Configuration editor
 - Profile management
 - Tool settings
 - Import/Export

#### Features

File Upload:
- Drag & drop files into chat
- Automatically reads file content
- Supports code files, text, JSON, etc.

Model Switching:
- Dropdown menu for model selection
- Real-time switching without restart
- Shows current model in status bar

Tool Toggles:
- Enable/disable tools on the fly
- Web search toggle
- Code executor toggle
- File operations toggle

Conversation Export:
- Export as JSON or Markdown
- Download conversations
- Share analysis results

Keyboard Shortcuts:
- `Ctrl+Enter` - Send message
- `Ctrl+K` - Clear conversation
- `Ctrl+E` - Export conversation
- `Ctrl+/` - Focus search

### VS Code Extension

#### Installation

```bash
cd vscode-extension
npm install
npm run compile
npm run package
code --install-extension meton-0.1.0.vsix
```

#### Commands

Command Palette (`Ctrl+Shift+P`):
- `Meton: Explain Selected Code`
- `Meton: Review Selected Code`
- `Meton: Generate Tests`
- `Meton: Suggest Refactorings`
- `Meton: Open Chat`
- `Meton: Index Workspace`

Keyboard Shortcuts:
- `Ctrl+Shift+E` - Explain selected code
- `Ctrl+Shift+M` - Open chat sidebar

Context Menu:
- Right-click on selected code
- Choose Meton action from menu

#### LSP Features

Code Actions ( lightbulb):
- Quick fixes for common issues
- Refactoring suggestions
- Extract method
- Simplify code

Diagnostics:
- Real-time code review
- Security warnings
- Best practice violations
- Style issues

Hover Documentation:
- Hover over functions/variables
- Get AI-powered explanations
- See usage examples

Code Completions:
- Context-aware suggestions
- AI-powered completions
- Smart imports

Chat Sidebar:
- Persistent chat panel
- Ask questions about code
- Get instant help
- Send code snippets

---

## Core Features

### 1. Semantic Code Search

Index your codebase for intelligent search:

```bash
# Index project
/index /path/to/project

# Search with natural language
> Show me the authentication implementation
> Find all database queries
> Where is the API rate limiting configured?
> Locate error handling code
```

How it works:
- AST-based code parsing
- Semantic chunking (1 chunk per function/class)
- FAISS vector search
- Returns ranked results with file:line references

Search Tips:
- Be specific: "JWT token validation" > "authentication"
- Use technical terms: "REST endpoint" > "API thing"
- Ask for locations: "Where is..." / "Find..."
- Ask for explanations: "How does..."

### 2. Code Review

Get comprehensive code analysis:

```python
> Review this code:
def process_payment(amount, user_id):
 query = f"SELECT * FROM users WHERE id = {user_id}"
 db.execute(query)
 return amount * 1.1
```

Output includes:
- Security issues (SQL injection detected!)
- Best practices violations
- Style recommendations
- Improvement suggestions
- Complexity analysis

Review Modes:
- Quick Basic security and syntax
- Standard Security + best practices + style
- Thorough Full analysis + refactoring suggestions

### 3. Test Generation

Generate comprehensive tests:

```python
> Generate tests for this function:
def calculate_discount(price, percentage, min_price=0):
 if price < min_price:
 return price
 return price * (1 - percentage / 100)
```

Output:
- Normal flow tests
- Edge case tests (0, negative, boundaries)
- Error case tests (invalid input)
- Property-based tests (optional)

Test Frameworks:
- `pytest` (default)
- `unittest`
- `hypothesis` (property-based)

### 4. Refactoring

Get refactoring suggestions:

```python
> Suggest refactorings for this code:
def complex_function(a, b, c, d, e):
 if a > 0:
 if b > 0:
 if c > 0:
 result = a * b * c
 if d > 0:
 result += d
 if e > 0:
 result += e
 return result
 return 0
```

Refactoring Patterns:
- Extract method
- Simplify conditionals
- Reduce nesting
- Eliminate magic numbers
- Improve naming
- Apply design patterns

### 5. Documentation

Generate documentation:

```python
> Generate Google-style docstring for this function:
def authenticate_user(username, password, remember_me=False):
 user = User.query.filter_by(username=username).first()
 if user and user.check_password(password):
 login_user(user, remember=remember_me)
 return True
 return False
```

Output:
```python
def authenticate_user(username: str, password: str, remember_me: bool = False) -> bool:
 """Authenticate a user with username and password.

 Args:
 username: The username to authenticate.
 password: The password to verify.
 remember_me: Whether to persist the session. Defaults to False.

 Returns:
 True if authentication successful, False otherwise.

 Raises:
 DatabaseError: If database query fails.
 """
```

Documentation Types:
- Docstrings Google, NumPy, Sphinx styles
- README Project overview
- API Docs Module/function documentation

---

## Skills

Meton has 7 built-in skills for high-level tasks.

### 1. Code Explainer

Purpose: Detailed code analysis with complexity metrics.

Usage:
```
> Explain this code:
[paste code]
```

Output:
- Purpose and functionality
- Control flow analysis
- Complexity metrics (cyclomatic, cognitive)
- Dependencies and imports
- Potential issues
- Improvement suggestions

Example:
```
> Explain this code:
def fibonacci(n):
 if n <= 1:
 return n
 return fibonacci(n-1) + fibonacci(n-2)

 Analysis:
- Recursive Fibonacci implementation
- Time complexity: O(2^n) - exponential
- Space complexity: O(n) - call stack
- Issue: Very slow for large n (>30)
- Suggestion: Use dynamic programming or memoization
```

### 2. Debugger Assistant

Purpose: Error analysis and fix suggestions.

Usage:
```
> Debug this error:
Traceback (most recent call last):
 File "app.py", line 45, in process
 result = data["key"]
KeyError: 'key'
```

Output:
- Error explanation
- Root cause analysis
- Fix suggestions (multiple options)
- Prevention strategies
- Test cases to add

Example:
```
 Error: KeyError accessing dictionary key

Root Cause:
- Dictionary doesn't contain 'key'
- No validation before access

Fixes:
1. Use .get() with default:
 result = data.get("key", default_value)

2. Check key existence:
 if "key" in data:
 result = data["key"]

3. Use try/except:
 try:
 result = data["key"]
 except KeyError:
 result = handle_missing_key()

Prevention:
- Validate input schema
- Use TypedDict or Pydantic
- Add unit tests for missing keys
```

### 3. Refactoring Engine

Purpose: Identify code smells and suggest refactorings.

Usage:
```
> Refactor this code:
[paste code]
```

Detects:
- Long methods (>50 lines)
- Complex conditionals
- Duplicate code
- Magic numbers
- Poor naming
- Tight coupling
- Violations of SOLID principles

Suggests:
- Extract method
- Replace conditional with polymorphism
- Introduce parameter object
- Extract class
- Replace magic number with named constant

### 4. Test Generator

Purpose: Generate comprehensive test suites.

Usage:
```
> Generate tests for:
[paste code or function name]
```

Generates:
- Normal flow tests
- Edge cases (boundaries, empty, null)
- Error cases (invalid input, exceptions)
- Integration tests (if dependencies detected)
- Property-based tests (optional)

Example:
```
> Generate tests for calculate_total(items, tax_rate=0.1)

Generated 8 tests:
 test_calculate_total_normal() - Standard case
 test_calculate_total_empty_list() - Edge: empty
 test_calculate_total_zero_items() - Edge: zero
 test_calculate_total_large_list() - Edge: many items
 test_calculate_total_custom_tax() - Variation: custom tax
 test_calculate_total_zero_tax() - Edge: no tax
 test_calculate_total_invalid_tax() - Error: negative tax
 test_calculate_total_non_numeric() - Error: bad input
```

### 5. Documentation Generator

Purpose: Generate documentation in multiple formats.

Usage:
```
> Generate documentation for this module

> Add Google-style docstrings to this code

> Create a README for this project
```

Formats:
- Docstrings Google, NumPy, Sphinx
- README Project overview, installation, usage
- API Reference Module/class/function docs

Example:
```
> Generate NumPy-style docstring for:
def train_model(X, y, epochs=100, learning_rate=0.01):
 # training code...

Output:
\"\"\"Train a machine learning model.

Parameters
----------
X : array-like
 Training features
y : array-like
 Training labels
epochs : int, optional
 Number of training iterations (default=100)
learning_rate : float, optional
 Learning rate for optimization (default=0.01)

Returns
-------
model : Model
 Trained model instance

Raises
------
ValueError
 If X and y have incompatible shapes
\"\"\"
```

### 6. Code Reviewer

Purpose: Comprehensive code quality analysis.

Usage:
```
> Review this pull request

> Analyze this module for security issues

> Check this code for best practices
```

Checks:
- Security vulnerabilities
- Best practices compliance
- Code style (PEP 8 for Python)
- Performance issues
- Maintainability concerns
- Documentation quality

Categories:
- **CRITICAL Security issues, major bugs
- **WARNING Best practice violations, style issues
- INFO Suggestions, optimizations

### 7. Task Planner

Purpose: Decompose complex tasks into subtasks.

Usage:
```
> Plan implementation of user authentication system

> Break down this feature into steps:
 Add real-time notifications to the app
```

Output:
- Task breakdown (hierarchical)
- Estimated complexity
- Dependencies
- Suggested order
- Potential issues
- Testing strategy

---

## Tools

### File Operations

Capabilities:
- Read files
- Write files
- List directories
- Create directories
- Check file existence
- Get file info

Security:
- Path validation
- Blocked paths (/etc, /sys, /proc)
- Allowed paths configuration

Example:
```
> Read the config.yaml file

> List all Python files in the src directory

> Create a new file called test.py with a hello world function
```

### Code Executor

Capabilities:
- Execute Python code
- Capture stdout/stderr
- Track execution time
- Isolate execution

Security:
- Subprocess isolation
- 5-second timeout
- Import validation (allowed/blocked lists)
- No eval()/exec() in agent code

Example:
```
> Execute this code:
import requests
response = requests.get("https://api.github.com")
print(response.status_code)

 Execution result (0.45s):
200
```

### Web Search

Capabilities:
- DuckDuckGo search
- No API key required
- Configurable result count

Usage:
```
# Enable web search
/web on

> Search for "Python async best practices 2024"

> What are the latest features in Python 3.12?
```

Note: Disabled by default. Enable with `/web on`.

### Codebase Search (RAG)

Capabilities:
- Semantic code search
- Natural language queries
- Returns ranked results
- Shows file paths and line numbers

Usage:
```
# Index first
/index /path/to/project

# Then search
> Find authentication logic
> Where is the database configured?
> Show me error handling code
```

### Git Integration

Capabilities:
- Git status
- Diff analysis
- Commit message generation
- Code review
- Branch suggestions
- History analysis

Usage:
```
/git status
/git review
/git commit-msg
/git history auth.py
/git suggest-branch
```

---

## Advanced Usage

### Multi-Agent Mode

Use multiple specialized agents for complex tasks:

```bash
/multiagent on

> Compare our API performance with FastAPI's approach and suggest optimizations

# Agents used:
# - Planner: Breaks down task
# - Researcher: Gathers information
# - Executor: Performs analysis
# - Reviewer: Validates results
```

### Chain-of-Thought Reasoning

Enable explicit reasoning display:

```bash
/cot on

> Analyze the security implications of our authentication system

# Shows step-by-step reasoning:
# 1. Identifying authentication mechanisms...
# 2. Analyzing token storage...
# 3. Checking for common vulnerabilities...
# 4. Evaluating password policies...
```

### Self-Reflection

Enable automatic quality improvement:

```yaml
# In config.yaml
reflection:
 enabled: true
 quality_threshold: 0.7
 max_iterations: 2
```

Agent automatically reflects on responses and improves them if quality score < threshold.

### Custom Profiles

Create profiles for specific workflows:

```bash
# Save current config as profile
/profile save my-ml-profile "Machine learning workflow" development

# Profile includes:
# - Model selection
# - Tool configuration
# - Skill preferences
# - Memory settings
```

### Project Templates

Quick project scaffolding:

```bash
# List available templates
/template list

# Create project from template
/template create fastapi-api my-new-api

# Templates available:
# - fastapi-api: FastAPI REST API
# - cli-tool: Click-based CLI
# - data-science: Jupyter + pandas + scikit-learn
# - flask-web: Flask web application
# - general: Basic Python project
```

### Parallel Tool Execution

Execute multiple tools simultaneously:

```python
# Automatic when agent detects independent tools
> Analyze both the frontend and backend code for security issues

# Executes in parallel:
# - codebase_search for frontend
# - codebase_search for backend
# - Merges results
```

### Long-Term Memory

Persistent memory across sessions:

```bash
# Check memory stats
/memory stats

# Search memories
/memory search "authentication patterns"

# Add manual memory
/memory add "Always use bcrypt for password hashing with cost factor 12"

# Export memories
/memory export json memories_backup.json
```

Memory Types:
- Semantic Automatically stored concepts
- Episodic Session interactions
- Manual User-added memories

### Cross-Session Learning

Learn patterns from usage:

```bash
# Analyze sessions for patterns
/learn analyze

# View insights
/learn insights

# See detected patterns
/learn patterns

# Apply specific insight
/learn apply insight_123
```

Learns from:
- Query types
- Tool usage patterns
- Common errors
- Successful approaches

---

## Configuration

### Configuration File

Edit `config.yaml`:

```yaml
models:
 primary: "qwen2.5-coder:32b"
 fallback: "llama3.1:8b"
 quick: "mistral:7b"
 temperature: 0.0
 max_tokens: 2048
 top_p: 0.9

agent:
 max_iterations: 10
 verbose: true
 timeout: 300

tools:
 file_operations:
 enabled: true
 allowed_paths:
 - "/home/user/projects"
 - "/media/development"
 blocked_paths:
 - "/etc"
 - "/sys"
 - "/proc"

 code_executor:
 enabled: true
 timeout: 5

 web_search:
 enabled: false
 max_results: 5

 codebase_search:
 enabled: true

rag:
 enabled: true
 top_k: 10
 similarity_threshold: 0.7
 max_chunks: 1000

skills:
 enabled: true
 auto_load: true

multiagent:
 enabled: false

reflection:
 enabled: true
 quality_threshold: 0.7
 max_iterations: 2

analytics:
 enabled: true
 retention_days: 90

memory:
 max_memories: 10000
 auto_consolidate: true
 auto_decay: true

learning:
 enabled: true
 min_pattern_occurrences: 5
 confidence_threshold: 0.7
 lookback_days: 30
```

### Runtime Configuration

Change settings without restart:

```bash
# Reload config
/reload

# Change model
/model llama3.1:8b

# Toggle tools
/web on
/web off

# Switch profiles
/profile use quick
```

---

## Tips & Best Practices

### General Tips

1. **Index before asking - Better semantic search results
 ```
 /index /path/to/project
 > How does X work?
 ```

2. **Be specific - Better than vague questions
 - "Show me JWT token validation in auth.py"
 - "Tell me about authentication"

3. **Use appropriate models
 - Quick queries: `mistral:7b`
 - Code tasks: `qwen2.5-coder:32b`
 - Complex reasoning: `llama3.1:70b` (if available)

4. **Enable reflection for important tasks
 ```yaml
 reflection:
 enabled: true
 ```

5. **Review analytics - Identify bottlenecks
 ```
 /analytics dashboard
 ```

### Code Review Tips

1. **Paste complete context - Include imports and dependencies
2. **Specify what to focus on - "Check for security" vs "general review"
3. **Review in chunks - Don't paste 1000 lines at once
4. **Ask follow-up questions - "Explain that SQL injection risk"

### Search Tips

1. **Use technical terms - "REST endpoint" > "API"
2. **Ask for specific locations - "Where is..." / "Show me..."
3. **Combine search with questions - "Find auth code and explain it"

### Performance Tips

1. **Close verbose mode for faster responses
 ```
 /verbose off
 ```

2. **Use quick profile for simple queries
 ```
 /profile use quick
 ```

3. **Clear conversation when changing topics
 ```
 /clear
 ```

4. **Limit RAG results if searches are slow
 ```yaml
 rag:
 top_k: 5 # Instead of 10
 ```

### Memory Tips

1. **Add important patterns manually
 ```
 /memory add "Use dependency injection for testability"
 ```

2. **Export memories periodically
 ```
 /memory export json backup.json
 ```

3. **Search memories before asking
 ```
 /memory search "testing patterns"
 ```

### Keyboard Shortcuts (Web UI)

- `Ctrl+Enter` - Send message
- `Ctrl+K` - Clear conversation
- `Ctrl+E` - Export conversation
- `Ctrl+/` - Focus search
- `Esc` - Cancel input

---

## Next Steps

- Try Examples See [EXAMPLES.md](EXAMPLES.md)
- Explore API Check [API_REFERENCE.md](API_REFERENCE.md)
- Extend Meton Read [DEVELOPMENT.md](DEVELOPMENT.md)
- Get Help See [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

Happy coding with Meton! 
