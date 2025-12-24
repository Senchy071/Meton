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
- `/find <symbol>` - Find symbol definition (function/class/method)
 ```
 /find MetonAgent
 /find _run type:method
 ```
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

#### Symbol/Function Lookup

Find exact definitions of functions, classes, and methods:

```bash
# Find class definition
/find MetonAgent

# Find function
/find setup_logger

# Filter by type
/find _run type:method
/find Config type:class
/find validate type:function
```

Features:
- Instant symbol lookup across entire codebase
- Returns file path, line number, signature, and code snippet
- Supports filtering by type (function/class/method)
- Shows docstrings and context
- Results displayed in a formatted table

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

Meton has two types of skills:
- **Python Skills**: 7 built-in skills implemented in Python
- **Markdown Skills**: Claude Code-style skills defined in markdown files with YAML frontmatter

### Python Skills

The following 7 Python-based skills provide high-level coding capabilities:

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

### Markdown Skills

Markdown skills are Claude Code-style skills defined in markdown files with YAML frontmatter. They provide a more declarative way to define skills.

**Built-in Markdown Skills:**

| Skill | Description |
|-------|-------------|
| `code-reviewer` | Review code for quality, security, and best practices |
| `code-explainer` | Explain code functionality and structure |
| `debugger` | Debug error analysis and fix suggestions |

**Skill Definition Format:**

```markdown
---
name: my-skill
description: Description for LLM discovery
allowed-tools: Read, Grep, Glob
model: primary
version: 1.0.0
---

# My Skill Instructions

Detailed instructions for the skill...
```

**Skill Discovery Locations (in precedence order):**

1. **Project**: `.meton/skills/` - Project-specific skills
2. **User**: `~/.meton/skills/` - User-wide skills
3. **Built-in**: `skills/md_skills/` - Built-in markdown skills

**CLI Commands:**

```
/skill list              # List all available skills
/skill info <name>       # Show skill details
/skill load <name>       # Load/enable a skill
/skill unload <name>     # Unload/disable a skill
/skill reload <name>     # Reload a skill
/skill discover          # Refresh skill discovery
```

**Creating Custom Skills:**

1. Create a directory in `.meton/skills/<skill-name>/`
2. Add a `SKILL.md` file with YAML frontmatter
3. Run `/skill discover` to load the skill

Example:
```bash
mkdir -p .meton/skills/my-analyzer
cat > .meton/skills/my-analyzer/SKILL.md << 'EOF'
---
name: my-analyzer
description: Custom code analyzer for project-specific patterns
allowed-tools: Read, Grep, Glob
model: primary
---

# My Custom Analyzer

Analyze code for project-specific patterns...
EOF
```

---

## Sub-Agents

Sub-agents are autonomous specialized agents that can execute tasks with isolated context. They run with their own conversation history and can be restricted to specific tools.

**Built-in Sub-Agents:**

| Agent | Description | Model |
|-------|-------------|-------|
| `explorer` | Fast codebase exploration (read-only) | quick |
| `planner` | Software architect for implementation planning | primary |
| `code-reviewer` | Expert code review for quality/security | primary |
| `debugger` | Debugging specialist for error analysis | primary |

**Agent Definition Format:**

```markdown
---
name: my-agent
description: Description for agent selection
tools: file_operations, codebase_search
model: primary
---

# Agent Instructions

System prompt and behavior instructions...
```

**Agent Discovery Locations (in precedence order):**

1. **Project**: `.meton/agents/` - Project-specific agents
2. **User**: `~/.meton/agents/` - User-wide agents
3. **Built-in**: `agents/builtin/` - Built-in agents

**CLI Commands:**

```
/agent list              # List all available agents
/agent info <name>       # Show agent details
/agent run <name> <task> # Run agent with task
/agent discover          # Refresh agent discovery
/agent history           # Show recent agent runs
```

**Example Usage:**

```
# Fast codebase exploration
> /agent run explorer "Find all authentication-related code"

# Planning a feature
> /agent run planner "Design implementation for user notifications"

# Code review
> /agent run code-reviewer "Review the changes in core/agent.py"

# Debugging
> /agent run debugger "Analyze this error: KeyError in process_data"
```

**Creating Custom Agents:**

1. Create a markdown file in `.meton/agents/<agent-name>.md`
2. Add YAML frontmatter with name, description, tools, and model
3. Run `/agent discover` to load the agent

Example:
```bash
cat > .meton/agents/security-auditor.md << 'EOF'
---
name: security-auditor
description: Security specialist for vulnerability analysis
tools: file_operations, codebase_search, symbol_lookup
model: primary
---

# Security Auditor

You are a security specialist. Analyze code for:
- Injection vulnerabilities
- Authentication issues
- Data exposure risks
...
EOF
```

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

### Model Parameter Configuration

Meton provides 14 configurable parameters for fine-grained control over LLM output quality:

**Core Parameters:**
- `temperature` (0.0-2.0) - Controls randomness. 0.0 = deterministic, higher = more creative
- `max_tokens` - Maximum response length
- `top_p` (0.0-1.0) - Nucleus sampling threshold
- `num_ctx` - Context window size

**Advanced Sampling:**
- `top_k` - Limits token candidates to top K (0 = disabled, 40 = default)
- `min_p` (0.0-1.0) - Adaptive filtering, recommended over top_k for better quality

**Repetition Control:**
- `repeat_penalty` (1.0-2.0) - Penalizes repetitive tokens (1.0 = off, 1.1 = light)
- `repeat_last_n` - Window for repetition analysis (-1 = entire context)
- `presence_penalty` (-2.0 to 2.0) - Penalizes tokens that already appeared
- `frequency_penalty` (-2.0 to 2.0) - Penalizes frequently used tokens

**Mirostat Sampling (alternative to top_k/top_p):**
- `mirostat` (0/1/2) - Enables consistent perplexity mode (0 = off)
- `mirostat_tau` - Target entropy level (default: 5.0)
- `mirostat_eta` (0.0-1.0) - Learning rate (default: 0.1)

**Reproducibility:**
- `seed` - Random seed for deterministic output (-1 = random)

**Example Presets:**

Precise Coding (deterministic):
```yaml
models:
  settings:
    temperature: 0.0
    top_k: 40
    repeat_penalty: 1.1
    seed: -1
```

Creative Coding (exploratory):
```yaml
models:
  settings:
    temperature: 0.7
    top_p: 0.95
    min_p: 0.05
    repeat_penalty: 1.2
```

Debugging (consistent):
```yaml
models:
  settings:
    temperature: 0.2
    mirostat: 2
    mirostat_tau: 4.0
    repeat_penalty: 1.15
```

Testing (reproducible):
```yaml
models:
  settings:
    temperature: 0.0
    seed: 42
    top_k: 40
```

### Runtime Parameter Tuning (Phase 2)

Meton supports dynamic parameter adjustment without restart through CLI commands and presets.

#### Commands

**View Parameters:**
```bash
/param show
```
Displays all 14 parameters in an organized table grouped by category (Core, Advanced Sampling, Repetition Control, Mirostat, Other).

**Set Individual Parameter:**
```bash
/param <name> <value>

# Examples:
/param temperature 0.7
/param top_k 40
/param seed 42
/param repeat_penalty 1.2
```

**Reset to Defaults:**
```bash
/param reset
```
Reloads all parameters from config.yaml.

**List Presets:**
```bash
/preset
```
Shows all available parameter presets with descriptions.

**Apply Preset:**
```bash
/preset <name>

# Examples:
/preset creative
/preset debugging
/preset precise
```

#### Available Presets

**1. precise** - Deterministic output for precise coding tasks
- Best for: Production code, bug fixes, specific implementations
- Settings: `temperature=0.0, top_k=40, repeat_penalty=1.1`

**2. creative** - More exploratory and creative coding
- Best for: Brainstorming, exploring alternatives, prototyping
- Settings: `temperature=0.7, top_p=0.95, repeat_penalty=1.2`

**3. balanced** - Balanced between creativity and precision
- Best for: General coding, refactoring, code reviews
- Settings: `temperature=0.3, top_k=40, repeat_penalty=1.15`

**4. debugging** - Consistent methodical debugging approach
- Best for: Debugging, troubleshooting, systematic analysis
- Settings: `temperature=0.2, mirostat=2, top_k=20`

**5. explanation** - Clear explanations with reduced repetition
- Best for: Code explanations, documentation, teaching
- Settings: `temperature=0.5, repeat_penalty=1.25, presence_penalty=0.1`

#### Example Workflows

**Exploratory Coding Session:**
```bash
1. /preset creative
2. Brainstorm different approaches
3. /param temperature 0.3
4. Refine chosen approach
5. /preset precise
6. Generate final implementation
```

**Debugging Session:**
```bash
1. /preset debugging
2. Analyze error systematically
3. /param show  # Verify settings
4. Debug with consistent responses
5. /param reset  # Return to defaults
```

**Learning/Documentation:**
```bash
1. /preset explanation
2. Ask for explanations
3. /param repeat_penalty 1.3  # Even less repetition
4. Get clearer explanations
```

#### How It Works

- Changes are applied immediately to in-memory configuration
- LLM cache is cleared automatically to ensure new parameters take effect
- Parameters persist for current session only
- Use `/param reset` to reload from config.yaml
- Use `/reload` to reload entire configuration including model selection

#### Tips

- Start with a preset, then fine-tune individual parameters
- Use `/param show` regularly to see current settings
- Different tasks benefit from different parameter combinations
- Temperature is usually the most impactful parameter to adjust
- For reproducible testing, set `seed` to a specific number

### Parameter Profiles (Phase 4)

Phase 4 introduces persistent, user-customizable parameter profiles that can be saved, loaded, and shared.

#### Key Differences from Presets

| Feature | Presets (Phase 2) | Profiles (Phase 4) |
|---------|-------------------|-------------------|
| Storage | Hardcoded in Python | Stored in config.yaml |
| Customizable | No | Yes |
| Runtime Creation | No | Yes |
| Sharing | No | Yes (export/import) |
| Persistence | No | Yes |

#### Commands

**List Profiles:**
```bash
/pprofile
```
Shows all available parameter profiles with descriptions and parameter counts.

**Show Profile Details:**
```bash
/pprofile show <name>

# Example:
/pprofile show creative_coding
```

**Apply Profile:**
```bash
/pprofile apply <name>

# Examples:
/pprofile apply creative_coding
/pprofile apply debugging
```

**Create New Profile:**
```bash
/pprofile create <name>

# Interactive creation:
> /pprofile create api_dev
Description: Settings for API development
temperature [0.0]: 0.3
top_p [0.9]: 0.95
repeat_penalty [1.1]: 1.15
... (press Enter to skip parameters)
```

**Delete Profile:**
```bash
/pprofile delete <name>

# Example:
/pprofile delete my_old_profile
```

**Export Profile:**
```bash
/pprofile export <name> [path]

# Examples:
/pprofile export api_dev                    # Exports to ./api_dev_profile.json
/pprofile export api_dev ./team/shared.json # Exports to specific path
```

**Import Profile:**
```bash
/pprofile import <path>

# Example:
/pprofile import ./team/shared.json
```

#### Default Profiles

Four profiles are included in `config.yaml`:

**1. creative_coding** - High temperature for exploratory coding
- Best for: Brainstorming, exploring alternatives, prototyping
- Settings: `temperature=0.7, top_p=0.95, min_p=0.05, repeat_penalty=1.2`

**2. precise_coding** - Deterministic with mirostat for precision
- Best for: Production code, critical implementations
- Settings: `temperature=0.0, top_p=0.9, repeat_penalty=1.1, mirostat=2`

**3. debugging** - Low temperature for methodical analysis
- Best for: Debugging, troubleshooting, systematic analysis
- Settings: `temperature=0.2, mirostat=2, mirostat_tau=4.0, top_k=20`

**4. explanation** - Moderate temperature for clear explanations
- Best for: Documentation, code explanations, teaching
- Settings: `temperature=0.5, top_p=0.9, repeat_penalty=1.25, presence_penalty=0.1`

#### Example Workflows

**Project-Specific Configuration:**
```bash
# Create profile for your API project
> /pprofile create fastapi_project
Description: Optimized for FastAPI development
temperature [0.0]: 0.3
top_p [0.9]: 0.95
repeat_penalty [1.1]: 1.15
# ... save settings

# Use throughout project
> /pprofile apply fastapi_project
```

**Team Standardization:**
```bash
# Create and test profile
> /pprofile create team_standard
> /pprofile apply team_standard
> # Test and validate...

# Share with team
> /pprofile export team_standard ./shared/team_profile.json
# Commit to git, share via Slack, etc.

# Team members import
> /pprofile import ./shared/team_profile.json
> /pprofile apply team_standard
```

**A/B Testing Parameters:**
```bash
# Save current working settings
> /pprofile create approach_a

# Try different settings
> /param temperature 0.5
> /param top_p 0.85
> /pprofile create approach_b

# Compare both
> /pprofile apply approach_a
> # Test queries...
> /pprofile apply approach_b
> # Test same queries...
```

**Task-Based Switching:**
```bash
# Feature development
> /pprofile apply creative_coding

# Code review
> /pprofile create code_review
> # Set moderate temperature, high repeat_penalty

# Debugging
> /pprofile apply debugging

# Documentation
> /pprofile apply explanation
```

#### Profile Storage

Profiles are stored in `config.yaml`:

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

#### How It Works

- Profiles are loaded from `config.yaml` on startup
- Creating/deleting profiles updates both in-memory config and disk
- Applying a profile updates current parameters and clears LLM cache
- Export creates standalone JSON file with profile data
- Import validates and creates profile from JSON file
- All changes are persistent across sessions

#### Tips

- Start with default profiles, create custom ones as needs arise
- Use descriptive names for profiles (e.g., `python_debugging`, `fastapi_dev`)
- Export profiles before major experiments
- Share profiles with team to standardize settings
- Create project-specific profiles for different codebases
- Use profiles as starting points, then fine-tune with `/param`
- Keep a "working" profile for settings you're currently testing

### Runtime Configuration

Change settings without restart:

```bash
# Reload config after editing config.yaml
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
