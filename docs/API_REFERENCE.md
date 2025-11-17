# API Reference

Complete API documentation for Meton's core components, tools, and skills.

---

## Table of Contents
1. [Core Agent](#core-agent)
2. [Configuration](#configuration)
3. [Tools](#tools)
4. [Skills](#skills)
5. [RAG System](#rag-system)
6. [Memory System](#memory-system)
7. [Multi-Agent System](#multi-agent-system)
8. [Analytics](#analytics)

---

## Core Agent

### MetonAgent

Main agent class using LangGraph ReAct pattern.

#### Location
`core/agent.py`

#### Class Definition

```python
class MetonAgent:
    """LangGraph-based ReAct agent with multi-step reasoning."""

    def __init__(
        self,
        model_manager: ModelManager,
        conversation_manager: ConversationManager,
        tools: List[BaseTool],
        config: MetonConfig,
        verbose: bool = False
    ):
        """Initialize Meton agent.

        Args:
            model_manager: Model manager instance
            conversation_manager: Conversation manager instance
            tools: List of available tools
            config: Configuration object
            verbose: Enable verbose output
        """
```

#### Methods

**run(query: str) -> Dict[str, Any]**

Execute a query with ReAct pattern.

```python
result = agent.run("How does authentication work?")

# Returns:
{
    "output": "Authentication uses JWT tokens...",
    "thoughts": ["THOUGHT: Need to search codebase...", ...],
    "tool_calls": [("codebase_search", {...}, "Found 5 files...")],
    "iteration": 3,
    "success": True
}
```

**Parameters:**
- `query` (str): User query to process

**Returns:**
- Dict with keys:
  - `output` (str): Final answer
  - `thoughts` (List[str]): Agent's reasoning steps
  - `tool_calls` (List[Tuple]): Tool executions (name, input, output)
  - `iteration` (int): Number of iterations used
  - `success` (bool): Whether query succeeded

**get_available_tools() -> List[str]**

Get list of enabled tool names.

```python
tools = agent.get_available_tools()
# ['file_operations', 'code_executor', 'codebase_search', ...]
```

**enable_tool(tool_name: str) -> bool**

Enable a tool at runtime.

```python
agent.enable_tool('web_search')
# Returns: True if successful
```

**disable_tool(tool_name: str) -> bool**

Disable a tool at runtime.

```python
agent.disable_tool('code_executor')
# Returns: True if successful
```

---

## Configuration

### ConfigLoader

Manages configuration with Pydantic validation.

#### Location
`core/config.py`

#### Class Definition

```python
class ConfigLoader:
    """Type-safe configuration management."""

    def __init__(self, config_path: str = "config.yaml"):
        """Load configuration from YAML file.

        Args:
            config_path: Path to configuration file
        """
```

#### Methods

**save() -> None**

Save current configuration to disk.

```python
config.config.tools.web_search.enabled = True
config.save()  # Persist to config.yaml
```

**reload() -> None**

Reload configuration from disk.

```python
config.reload()
```

**get(key: str, default: Any = None) -> Any**

Get configuration value by dot notation.

```python
value = config.get('models.primary')
# 'qwen2.5-coder:32b'

value = config.get('nonexistent.key', 'default')
# 'default'
```

#### Configuration Schema

```python
class MetonConfig(BaseModel):
    """Root configuration model."""

    models: ModelsConfig
    agent: AgentConfig
    conversation: ConversationConfig
    tools: ToolsConfig
    rag: RAGConfig
    skills: SkillsConfig
    multiagent: MultiAgentConfig
    reflection: ReflectionConfig
    analytics: AnalyticsConfig
    memory: MemoryConfig
    learning: LearningConfig
    profiles: Dict[str, ProfileConfig]
```

---

## Tools

### BaseTool

Base class for all Meton tools.

#### Location
`tools/base.py`

#### Class Definition

```python
class MetonBaseTool(BaseTool):
    """Base class for Meton tools extending LangChain BaseTool."""

    name: str
    description: str
    _enabled: bool = True

    def _run(self, input: str) -> str:
        """Execute the tool (must be implemented by subclass).

        Args:
            input: JSON string with tool parameters

        Returns:
            Tool execution result as string
        """
        raise NotImplementedError
```

#### Creating a Custom Tool

```python
from tools.base import MetonBaseTool
import json

class MyCustomTool(MetonBaseTool):
    """Custom tool example."""

    name = "my_custom_tool"
    description = "Does something custom. Input: {\"param\": \"value\"}"

    def _run(self, input: str) -> str:
        """Execute custom logic."""
        try:
            params = json.loads(input)
            param_value = params.get("param")

            # Your custom logic here
            result = self.do_something(param_value)

            return f"Success: {result}"
        except Exception as e:
            return f"Error: {str(e)}"

    def do_something(self, param: str) -> str:
        """Custom logic implementation."""
        return param.upper()

# Register tool
from cli import MetonCLI
cli = MetonCLI()
custom_tool = MyCustomTool()
cli.agent.tools.append(custom_tool)
```

### FileOperationsTool

File system operations with security.

#### Location
`tools/file_ops.py`

#### Actions

```python
# Read file
input = json.dumps({"action": "read", "path": "/path/to/file.py"})
result = tool._run(input)

# Write file
input = json.dumps({
    "action": "write",
    "path": "/path/to/file.py",
    "content": "print('hello')"
})
result = tool._run(input)

# List directory
input = json.dumps({"action": "list", "path": "/path/to/dir"})
result = tool._run(input)

# Create directory
input = json.dumps({"action": "create_dir", "path": "/path/to/new/dir"})
result = tool._run(input)

# Check existence
input = json.dumps({"action": "exists", "path": "/path/to/file"})
result = tool._run(input)

# Get file info
input = json.dumps({"action": "get_info", "path": "/path/to/file"})
result = tool._run(input)
```

### CodeExecutorTool

Execute Python code in isolated subprocess.

#### Location
`tools/code_executor.py`

#### Usage

```python
input = json.dumps({
    "code": "import math\nprint(math.pi)"
})
result = tool._run(input)
# "3.141592653589793\nExecution time: 0.02s"
```

#### Security Features
- Subprocess isolation
- 5-second timeout
- Import allowlist/blocklist
- No eval()/exec() in agent

### WebSearchTool

DuckDuckGo web search.

#### Location
`tools/web_search.py`

#### Usage

```python
input = json.dumps({
    "query": "Python async best practices",
    "max_results": 5
})
result = tool._run(input)
```

### CodebaseSearchTool

Semantic code search using RAG.

#### Location
`tools/codebase_search.py`

#### Usage

```python
input = json.dumps({
    "query": "authentication implementation",
    "top_k": 5
})
result = tool._run(input)
# Returns: "Found 5 results:\n1. auth.py:45-67 (score: 0.89)..."
```

---

## Skills

### BaseSkill

Base class for all skills.

#### Location
`skills/base.py`

#### Class Definition

```python
class BaseSkill(ABC):
    """Abstract base class for all skills."""

    name: str
    description: str
    version: str

    @abstractmethod
    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute the skill.

        Args:
            input_data: Skill-specific input parameters

        Returns:
            Skill execution result
        """
        pass
```

#### Creating a Custom Skill

```python
from skills.base import BaseSkill
from typing import Dict, Any

class MyCustomSkill(BaseSkill):
    """Custom skill example."""

    name = "my_custom_skill"
    description = "Does something custom"
    version = "1.0.0"

    def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Execute custom skill logic.

        Args:
            input_data: {
                "param1": str,
                "param2": int
            }

        Returns:
            {
                "success": bool,
                "result": str,
                "details": Dict
            }
        """
        try:
            param1 = input_data.get("param1")
            param2 = input_data.get("param2", 0)

            # Your skill logic here
            result = self.process(param1, param2)

            return {
                "success": True,
                "result": result,
                "details": {"processed": True}
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

    def process(self, param1: str, param2: int) -> str:
        """Custom processing logic."""
        return f"{param1} processed {param2} times"

# Save to skills/my_custom_skill.py
# Auto-loaded if skills.auto_load: true in config
```

### CodeExplainerSkill

Analyze and explain code.

#### Location
`skills/code_explainer.py`

#### API

```python
from skills.code_explainer import CodeExplainerSkill

skill = CodeExplainerSkill()
result = skill.execute({
    "code": "def factorial(n):\n    return 1 if n <= 1 else n * factorial(n-1)",
    "language": "python"
})

# Returns:
{
    "success": True,
    "explanation": "Recursive factorial implementation...",
    "complexity": {
        "cyclomatic": 2,
        "cognitive": 3,
        "time": "O(n)",
        "space": "O(n)"
    },
    "suggestions": ["Consider iterative approach for large n"]
}
```

### TestGeneratorSkill

Generate test suites.

#### Location
`skills/test_generator.py`

#### API

```python
from skills.test_generator import TestGeneratorSkill

skill = TestGeneratorSkill()
result = skill.execute({
    "code": "def add(a, b):\n    return a + b",
    "framework": "pytest",  # or "unittest"
    "include_edge_cases": True
})

# Returns:
{
    "success": True,
    "tests": "import pytest\n\ndef test_add_normal():\n    ...",
    "test_count": 5,
    "coverage_estimate": 0.95
}
```

### DocumentationGeneratorSkill

Generate documentation.

#### Location
`skills/documentation_generator.py`

#### API

```python
from skills.documentation_generator import DocumentationGeneratorSkill

skill = DocumentationGeneratorSkill()
result = skill.execute({
    "code": "def authenticate(username, password): ...",
    "style": "google",  # or "numpy", "sphinx"
    "doc_type": "docstring"  # or "readme", "api"
})

# Returns:
{
    "success": True,
    "documentation": "\"\"\"Authenticate user...",
    "style": "google"
}
```

---

## RAG System

### CodebaseIndexer

Orchestrates codebase indexing.

#### Location
`rag/indexer.py`

#### API

```python
from rag.indexer import CodebaseIndexer

indexer = CodebaseIndexer()

# Index directory
files_indexed = indexer.index_directory("/path/to/project")
# Returns: 127

# Get statistics
stats = indexer.get_stats()
# Returns: {"files": 127, "chunks": 543, "last_indexed": "2024-11-15..."}

# Search
results = indexer.search("authentication logic", top_k=5)
# Returns: List[Dict] with file paths, line numbers, scores

# Clear index
indexer.clear()
```

### EmbeddingModel

Generate embeddings for text.

#### Location
`rag/embeddings.py`

#### API

```python
from rag.embeddings import EmbeddingModel

model = EmbeddingModel()

# Encode single text
embedding = model.encode("authentication function")
# Returns: np.ndarray shape (768,)

# Encode batch
embeddings = model.encode_batch([
    "function one",
    "function two"
])
# Returns: np.ndarray shape (2, 768)

# Get dimension
dim = model.dimension
# 768
```

### VectorStore

FAISS-based vector storage.

#### Location
`rag/vector_store.py`

#### API

```python
from rag.vector_store import VectorStore
import numpy as np

store = VectorStore(dimension=768)

# Add vectors
vectors = np.random.rand(10, 768).astype('float32')
ids = store.add(vectors)
# Returns: List[int] [0, 1, 2, ..., 9]

# Search
query_vector = np.random.rand(768).astype('float32')
results = store.search(query_vector, k=5)
# Returns: (distances, indices)

# Save/load
store.save("index.faiss")
store.load("index.faiss")

# Get count
count = store.count()
# Returns: 10
```

---

## Memory System

### LongTermMemory

Persistent semantic memory across sessions.

#### Location
`memory/long_term_memory.py`

#### API

```python
from memory.long_term_memory import LongTermMemory

memory = LongTermMemory(max_memories=10000)

# Add memory
memory_id = memory.add_memory(
    content="Always use bcrypt for password hashing",
    importance=0.9,
    tags=["security", "authentication"]
)

# Search memories
results = memory.search("password security", top_k=5)
# Returns: List[Dict] with content, importance, timestamp

# Get statistics
stats = memory.get_statistics()
# Returns: {"total": 1234, "by_tag": {...}, "avg_importance": 0.7}

# Consolidate old memories
memory.consolidate()

# Apply decay
memory.apply_decay()
```

### CrossSessionLearning

Learn patterns from usage history.

#### Location
`learning/cross_session_learning.py`

#### API

```python
from learning.cross_session_learning import CrossSessionLearning

learning = CrossSessionLearning()

# Analyze sessions
patterns = learning.analyze_sessions(lookback_days=30)
# Returns: List[Pattern] detected patterns

# Generate insights
insights = learning.generate_insights()
# Returns: List[Insight] actionable insights

# Apply insight
success = learning.apply_insight(insight_id="insight_123")
# Returns: bool

# Get recommendations
recommendations = learning.get_recommendations()
# Returns: List[str] personalized recommendations
```

---

## Multi-Agent System

### MultiAgentCoordinator

Coordinate multiple specialized agents.

#### Location
`multiagent/coordinator.py`

#### API

```python
from multiagent.coordinator import MultiAgentCoordinator

coordinator = MultiAgentCoordinator(
    model_manager=model_manager,
    config=config
)

# Execute with multiple agents
result = coordinator.execute(
    query="Compare our API with FastAPI and suggest improvements",
    agents=["planner", "researcher", "executor", "reviewer"]
)

# Returns:
{
    "success": True,
    "result": "Comparison and suggestions...",
    "agents_used": ["planner", "researcher", "executor", "reviewer"],
    "execution_time": 45.2
}

# Get agent status
status = coordinator.get_agent_status("researcher")
# Returns: {"active": True, "tasks_completed": 12, ...}
```

### Specialized Agents

**PlannerAgent**: Decomposes tasks into subtasks

```python
from multiagent.agents.planner import PlannerAgent

agent = PlannerAgent(model_manager)
plan = agent.plan("Implement user authentication")
# Returns: {"subtasks": [...], "dependencies": {...}, "estimates": {...}}
```

**ResearcherAgent**: Gathers information

```python
from multiagent.agents.researcher import ResearcherAgent

agent = ResearcherAgent(model_manager, tools)
research = agent.research("FastAPI authentication patterns")
# Returns: {"findings": [...], "sources": [...], "summary": "..."}
```

**ExecutorAgent**: Performs tasks

```python
from multiagent.agents.executor import ExecutorAgent

agent = ExecutorAgent(model_manager, tools)
result = agent.execute({"task": "Write function", "spec": {...}})
# Returns: {"success": True, "output": "...", "artifacts": [...]}
```

**ReviewerAgent**: Validates results

```python
from multiagent.agents.reviewer import ReviewerAgent

agent = ReviewerAgent(model_manager)
review = agent.review({"code": "...", "criteria": [...]})
# Returns: {"approved": True, "issues": [...], "suggestions": [...]}
```

---

## Analytics

### PerformanceAnalytics

Track and analyze agent performance.

#### Location
`analytics/performance.py`

#### API

```python
from analytics.performance import PerformanceAnalytics

analytics = PerformanceAnalytics()

# Record metric
analytics.record_metric(
    metric_type="query_time",
    value=2.5,
    tags={"model": "qwen2.5-coder:32b", "tool": "codebase_search"}
)

# Get statistics
stats = analytics.get_statistics(days=7)
# Returns: {
#     "avg_query_time": 3.2,
#     "total_queries": 145,
#     "tool_usage": {...},
#     "error_rate": 0.02
# }

# Detect bottlenecks
bottlenecks = analytics.detect_bottlenecks()
# Returns: List[Dict] with bottleneck descriptions

# Generate dashboard
dashboard_html = analytics.generate_dashboard()
# Returns: str (HTML with Plotly charts)

# Export metrics
analytics.export_metrics("metrics.json", format="json")
```

---

## Error Handling

All API methods follow consistent error handling:

```python
try:
    result = agent.run(query)
    if result.get("success"):
        output = result["output"]
    else:
        error = result.get("error", "Unknown error")
        handle_error(error)
except MetonException as e:
    # Meton-specific exceptions
    logger.error(f"Meton error: {e}")
except Exception as e:
    # General exceptions
    logger.error(f"Unexpected error: {e}")
```

### Custom Exceptions

```python
from core.exceptions import (
    MetonException,
    ConfigurationError,
    ToolExecutionError,
    ModelError,
    SkillExecutionError
)

# Raise custom exception
raise ToolExecutionError("File not found", tool_name="file_operations")
```

---

## Type Hints

All APIs use type hints for better IDE support:

```python
from typing import Dict, List, Any, Optional, Union
from pathlib import Path

def my_function(
    query: str,
    top_k: int = 5,
    filters: Optional[Dict[str, Any]] = None
) -> List[Dict[str, Union[str, float]]]:
    """Type-hinted function example."""
    pass
```

---

## Next Steps

- **Extend Meton**: See [DEVELOPMENT.md](DEVELOPMENT.md)
- **View Examples**: Check [EXAMPLES.md](EXAMPLES.md)
- **Get Help**: Read [TROUBLESHOOTING.md](TROUBLESHOOTING.md)

---

**For more details, see source code with extensive docstrings.**
