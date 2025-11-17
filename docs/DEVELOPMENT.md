# Development Guide

Guide for contributing to and extending Meton.

---

## Table of Contents
1. [Development Setup](#development-setup)
2. [Project Structure](#project-structure)
3. [Contributing](#contributing)
4. [Adding Features](#adding-features)
5. [Testing](#testing)
6. [Code Style](#code-style)
7. [Documentation](#documentation)
8. [Release Process](#release-process)

---

## Development Setup

### Prerequisites

- Python 3.10+
- Git
- Virtual environment
- Code editor (VS Code, PyCharm, Vim, etc.)

### Setup Steps

```bash
# Clone repository
git clone https://github.com/yourusername/meton.git
cd meton

# Create development environment
python3.10 -m venv venv
source venv/bin/activate

# Install dependencies (including dev dependencies)
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists

# Install pre-commit hooks (optional)
pip install pre-commit
pre-commit install

# Verify setup
python test_infrastructure.py
```

### Development Tools

**Recommended:**
- **Editor**: VS Code with Python extension
- **Linting**: flake8, pylint
- **Formatting**: black
- **Type Checking**: mypy
- **Testing**: pytest

**Install dev tools:**
```bash
pip install black flake8 mypy pytest pytest-cov ipython
```

---

## Project Structure

```
meton/
├── core/                    # Core components
│   ├── agent.py            # LangGraph ReAct agent
│   ├── config.py           # Configuration management
│   ├── conversation.py     # Conversation manager
│   └── models.py           # Model manager (Ollama)
│
├── tools/                   # LangChain tools
│   ├── base.py             # Base tool class
│   ├── file_ops.py         # File operations
│   ├── code_executor.py    # Code execution
│   ├── web_search.py       # Web search
│   ├── codebase_search.py  # RAG search
│   └── git_ops.py          # Git operations
│
├── skills/                  # High-level skills
│   ├── base.py             # Base skill class
│   ├── code_explainer.py   # Code explanation
│   ├── debugger.py         # Debug assistance
│   ├── refactoring_engine.py # Refactoring
│   ├── test_generator.py   # Test generation
│   ├── documentation_generator.py # Doc generation
│   └── code_reviewer.py    # Code review
│
├── rag/                     # RAG system
│   ├── code_parser.py      # AST parsing
│   ├── chunker.py          # Semantic chunking
│   ├── embeddings.py       # Embedding model
│   ├── vector_store.py     # FAISS store
│   ├── metadata_store.py   # Metadata storage
│   └── indexer.py          # Indexing orchestration
│
├── multiagent/             # Multi-agent system
│   ├── coordinator.py      # Agent coordinator
│   └── agents/             # Specialized agents
│       ├── planner.py
│       ├── researcher.py
│       ├── executor.py
│       └── reviewer.py
│
├── memory/                 # Memory systems
│   └── long_term_memory.py # Long-term memory
│
├── learning/               # Learning systems
│   └── cross_session_learning.py # Cross-session learning
│
├── analytics/              # Analytics
│   ├── performance.py      # Performance tracking
│   └── visualizations.py   # Plotly visualizations
│
├── web/                    # Web UI
│   ├── app.py              # Gradio app
│   ├── components.py       # UI components
│   ├── session_manager.py  # Session management
│   └── utils.py            # Utilities
│
├── api/                    # HTTP API (for VS Code extension)
│   └── server.py           # FastAPI server
│
├── vscode-extension/       # VS Code extension
│   ├── src/                # TypeScript source
│   │   ├── extension.ts
│   │   ├── lsp/            # LSP features
│   │   └── webview/        # Chat panel
│   └── package.json        # Extension manifest
│
├── utils/                  # Utilities
│   ├── logger.py           # Logging
│   └── formatting.py       # CLI formatting
│
├── tests/                  # Test files
│   ├── test_agent.py
│   ├── test_skills.py
│   └── ...
│
├── conversations/          # Saved conversations
├── rag_index/             # RAG index storage
├── memories/              # Memory storage
│
├── cli.py                 # Main CLI interface
├── meton.py               # Entry point
├── launch_web.py          # Web UI launcher
├── config.yaml            # Configuration
├── requirements.txt       # Python dependencies
└── setup.sh               # Setup script
```

---

## Contributing

### Getting Started

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/your-feature-name
   ```
3. **Make your changes**
4. **Write tests**
5. **Run tests**
   ```bash
   python -m pytest tests/
   ```
6. **Commit your changes**
   ```bash
   git commit -m "Add feature: your feature description"
   ```
7. **Push to your fork**
   ```bash
   git push origin feature/your-feature-name
   ```
8. **Create a Pull Request**

### Contribution Guidelines

**Do:**
- ✅ Write clear, concise commit messages
- ✅ Add tests for new features
- ✅ Update documentation
- ✅ Follow code style guidelines
- ✅ Keep PRs focused (one feature per PR)
- ✅ Add type hints to functions
- ✅ Handle errors gracefully

**Don't:**
- ❌ Submit untested code
- ❌ Break existing functionality
- ❌ Ignore code style
- ❌ Include unrelated changes
- ❌ Commit commented-out code
- ❌ Add large binary files

### Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Formatting
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance

**Examples:**
```
feat(skills): Add code complexity analyzer skill

Implemented new skill that calculates cyclomatic and cognitive
complexity for Python functions. Includes McCabe complexity metric.

Closes #123
```

```
fix(rag): Fix indexing crash with empty files

Handle edge case where files have no functions or classes.
Added validation before chunking.

Fixes #456
```

---

## Adding Features

### Adding a New Tool

1. **Create tool file**: `tools/my_tool.py`

```python
from tools.base import MetonBaseTool
import json

class MyTool(MetonBaseTool):
    """Description of what the tool does."""

    name = "my_tool"
    description = """
    Tool description for the agent.
    Input: {"param1": "value1", "param2": "value2"}
    """

    def _run(self, input: str) -> str:
        """Execute the tool.

        Args:
            input: JSON string with parameters

        Returns:
            Tool execution result
        """
        try:
            params = json.loads(input)
            # Your tool logic here
            result = self.do_something(params)
            return f"Success: {result}"
        except Exception as e:
            return f"Error: {str(e)}"

    def do_something(self, params: dict) -> str:
        """Implement tool logic."""
        return "Result"
```

2. **Register in CLI**: `cli.py`

```python
from tools.my_tool import MyTool

def initialize(self):
    # ... existing tools ...
    self.tools.append(MyTool())
```

3. **Add configuration**: `config.yaml`

```yaml
tools:
  my_tool:
    enabled: true
    # tool-specific settings
```

4. **Write tests**: `tests/test_my_tool.py`

```python
def test_my_tool():
    tool = MyTool()
    result = tool._run('{"param1": "value"}')
    assert "Success" in result
```

5. **Update documentation**: Add to `docs/API_REFERENCE.md`

### Adding a New Skill

1. **Create skill file**: `skills/my_skill.py`

```python
from skills.base import BaseSkill
from typing import Dict, Any

class MySkill(BaseSkill):
    """Skill description."""

    name = "my_skill"
    description = "What this skill does"
    version = "1.0.0"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill.

        Args:
            input_data: Skill parameters

        Returns:
            Skill execution result
        """
        try:
            # Validate input
            required_keys = ["param1"]
            if not all(k in input_data for k in required_keys):
                return {"success": False, "error": "Missing required parameters"}

            # Execute skill logic
            result = self.process(input_data)

            return {
                "success": True,
                "result": result,
                "metadata": {}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def process(self, input_data: Dict[str, Any]) -> str:
        """Skill logic implementation."""
        return "Processed result"
```

2. **Auto-loaded** if saved in `skills/` directory and `skills.auto_load: true`

3. **Write tests**: `tests/test_my_skill.py`

```python
from skills.my_skill import MySkill

def test_my_skill_success():
    skill = MySkill()
    result = skill.execute({"param1": "value"})
    assert result["success"] is True

def test_my_skill_missing_params():
    skill = MySkill()
    result = skill.execute({})
    assert result["success"] is False
```

### Adding a CLI Command

1. **Add to help**: `cli.py` in `display_help()` method

```python
console.print("/mycommand [args]", style="cyan")
console.print("  Description of command", style="dim")
```

2. **Add handler**: `cli.py` in `handle_command()` method

```python
elif command == "/mycommand":
    self.handle_mycommand(parts)
```

3. **Implement handler**: `cli.py`

```python
def handle_mycommand(self, parts: List[str]) -> None:
    """Handle /mycommand.

    Args:
        parts: Command arguments
    """
    if len(parts) < 2:
        self.console.print("Usage: /mycommand <arg>", style="red")
        return

    arg = parts[1]
    # Command logic here
    self.console.print(f"Result: {result}", style="green")
```

---

## Testing

### Running Tests

```bash
# Run all tests
python -m pytest tests/

# Run specific test file
python tests/test_agent.py

# Run with coverage
python -m pytest --cov=. --cov-report=html tests/

# Run specific test
python -m pytest tests/test_skills.py::test_code_explainer
```

### Writing Tests

**Test File Structure:**

```python
#!/usr/bin/env python3
"""Tests for my_module."""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from my_module import MyClass

def test_basic_functionality():
    """Test basic functionality."""
    obj = MyClass()
    result = obj.method()
    assert result == expected_value, f"Expected {expected_value}, got {result}"

def test_edge_case():
    """Test edge case."""
    obj = MyClass()
    result = obj.method(edge_case_input)
    assert result is not None

def test_error_handling():
    """Test error handling."""
    obj = MyClass()
    try:
        obj.method(invalid_input)
        assert False, "Should have raised exception"
    except ValueError as e:
        assert "error message" in str(e)

if __name__ == "__main__":
    # Run tests
    test_basic_functionality()
    test_edge_case()
    test_error_handling()
    print("✅ All tests passed")
```

### Test Coverage

Aim for:
- **Core components**: 90%+ coverage
- **Tools**: 80%+ coverage
- **Skills**: 80%+ coverage
- **Utilities**: 70%+ coverage

---

## Code Style

### Python Style Guide

Follow PEP 8 with these specifics:

**Formatting:**
- Line length: 100 characters
- Indentation: 4 spaces
- Quotes: Double quotes for strings
- Trailing commas: Yes for multi-line structures

**Example:**
```python
def my_function(
    param1: str,
    param2: int,
    param3: Optional[Dict[str, Any]] = None,
) -> Tuple[str, bool]:
    """Function docstring.

    Args:
        param1: Description
        param2: Description
        param3: Description. Defaults to None.

    Returns:
        Tuple of (result, success)
    """
    result = f"Processed {param1} {param2} times"
    return result, True
```

**Imports:**
```python
# Standard library
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional

# Third-party
import numpy as np
from langchain.tools import BaseTool

# Local
from core.config import ConfigLoader
from utils.logger import get_logger
```

### Type Hints

Always use type hints:

```python
from typing import Dict, List, Any, Optional, Union, Tuple

def process_data(
    data: Dict[str, Any],
    filters: Optional[List[str]] = None
) -> Tuple[List[Dict], int]:
    """Process data with optional filters."""
    pass
```

### Docstrings

Use Google style docstrings:

```python
def function(param1: str, param2: int = 0) -> Dict[str, Any]:
    """Short description.

    Longer description if needed. Can span multiple lines
    and include examples.

    Args:
        param1: Description of param1.
        param2: Description of param2. Defaults to 0.

    Returns:
        Dictionary with keys:
            - "result": Processing result
            - "success": Whether operation succeeded

    Raises:
        ValueError: If param1 is empty.
        RuntimeError: If processing fails.

    Example:
        >>> result = function("test", param2=5)
        >>> print(result["success"])
        True
    """
    pass
```

### Formatting Tools

**Black** (code formatter):
```bash
black meton.py core/ tools/ skills/

# Check without modifying
black --check .

# Format entire project
black .
```

**Flake8** (linter):
```bash
flake8 meton.py core/ tools/ skills/

# With specific rules
flake8 --max-line-length=100 --ignore=E203,W503 .
```

**MyPy** (type checker):
```bash
mypy meton.py core/ tools/ skills/

# Strict mode
mypy --strict meton.py
```

---

## Documentation

### Code Documentation

- **All modules**: Module-level docstring
- **All classes**: Class docstring with description
- **All public methods**: Docstring with Args/Returns/Raises
- **Complex logic**: Inline comments explaining why

### README Updates

When adding features, update:
- `README.md` - Main README with feature list
- `docs/USER_GUIDE.md` - Usage instructions
- `docs/API_REFERENCE.md` - API documentation
- `docs/EXAMPLES.md` - Usage examples

### Changelog

Update `docs/CHANGELOG.md` with every change:

```markdown
## [Unreleased]

### Added
- New feature X that does Y
- New CLI command /mycommand

### Changed
- Improved performance of Z by 30%
- Updated dependency X to version Y

### Fixed
- Bug in skill execution (#123)
- Memory leak in indexer (#456)
```

---

## Release Process

### Version Numbering

Semantic versioning: `MAJOR.MINOR.PATCH`

- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes

### Release Steps

1. **Update version** in `__version__` variables
2. **Update CHANGELOG.md**
3. **Run full test suite**
   ```bash
   python -m pytest tests/
   ```
4. **Create release branch**
   ```bash
   git checkout -b release/v0.2.0
   ```
5. **Commit changes**
   ```bash
   git commit -m "Release v0.2.0"
   ```
6. **Tag release**
   ```bash
   git tag -a v0.2.0 -m "Version 0.2.0"
   ```
7. **Push to remote**
   ```bash
   git push origin release/v0.2.0
   git push origin v0.2.0
   ```
8. **Create GitHub release** with changelog

---

## Development Workflow

### Feature Development

```bash
# 1. Create feature branch
git checkout -b feature/my-feature

# 2. Develop feature (with tests!)
# ... code ...

# 3. Run tests
python -m pytest tests/

# 4. Format code
black .

# 5. Commit
git add .
git commit -m "feat: Add my feature"

# 6. Push and create PR
git push origin feature/my-feature
```

### Bug Fix Workflow

```bash
# 1. Create bugfix branch
git checkout -b fix/issue-123

# 2. Write failing test
# tests/test_bug.py

# 3. Fix bug
# ... code ...

# 4. Verify test passes
python tests/test_bug.py

# 5. Commit
git commit -m "fix: Fix issue with X (#123)"

# 6. Push and create PR
git push origin fix/issue-123
```

---

## Getting Help

### Resources

- **Documentation**: Read `docs/` directory
- **Issues**: Check [GitHub Issues](https://github.com/yourusername/meton/issues)
- **Discussions**: Join [GitHub Discussions](https://github.com/yourusername/meton/discussions)
- **Code**: Read source code with extensive docstrings

### Contact

- **Maintainer**: Senad Arifhodzic
- **Email**: [your-email]
- **GitHub**: [@yourusername](https://github.com/yourusername)

---

## License

MIT License - see [LICENSE](../LICENSE) for details.

---

**Thank you for contributing to Meton!** 🎉
