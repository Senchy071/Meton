#!/usr/bin/env python3
"""
Tests for Task Planning System.

Tests cover:
- Plan creation (simple, medium, complex)
- Subtask decomposition
- Dependency detection and resolution
- Execution order (topological sort)
- Plan validation (circular deps, invalid tools)
- Plan execution (sequential, parallel)
- Progress tracking
- Error handling
- Complexity estimation
- Plan visualization
- Statistics tracking
"""

import sys
from pathlib import Path
from unittest.mock import Mock
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.task_planner import TaskPlanner, TaskPlan, SubTask


def create_mock_model_manager():
    """Create mock model manager for testing."""
    manager = Mock()
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = json.dumps({
        "subtasks": [
            {"id": 1, "description": "First task", "tool": "tool1", "args": {}, "depends_on": [], "estimated_time": 10},
            {"id": 2, "description": "Second task", "tool": "tool2", "args": {}, "depends_on": [1], "estimated_time": 5}
        ]
    })
    mock_llm.invoke = Mock(return_value=mock_response)
    manager.get_model = Mock(return_value=mock_llm)
    return manager


def create_mock_tools():
    """Create mock tools for testing."""
    def tool1_run(args):
        return {"result": "tool1_executed"}

    def tool2_run(args):
        return {"result": "tool2_executed"}

    tool1 = Mock()
    tool1.run = tool1_run

    tool2 = Mock()
    tool2.run = tool2_run

    return {"tool1": tool1, "tool2": tool2, "codebase_search": tool1, "web_search": tool2}


def test_estimate_complexity_simple():
    """Test complexity estimation for simple queries."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    assert planner.estimate_complexity("What is Python?") == "simple"
    assert planner.estimate_complexity("Show me the code") == "simple"


def test_estimate_complexity_medium():
    """Test complexity estimation for medium queries."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    assert planner.estimate_complexity("Find and analyze the authentication code") == "medium"


def test_estimate_complexity_complex():
    """Test complexity estimation for complex queries."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    complexity = planner.estimate_complexity("First analyze the code, then compare it with best practices, and finally suggest improvements")
    assert complexity == "complex"


def test_create_plan():
    """Test plan creation."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    plan = planner.create_plan("Test query")

    assert plan.query == "Test query"
    assert len(plan.subtasks) > 0
    assert plan.id is not None


def test_create_plan_with_dependencies():
    """Test plan creation includes dependencies."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    plan = planner.create_plan("Test query")

    assert len(plan.dependencies) > 0


def test_validate_plan_valid():
    """Test validation of valid plan."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [], 10),
        SubTask(2, "Task 2", "tool2", {}, [1], 5)
    ]

    plan = TaskPlan("id", "query", subtasks, 15, "simple", {1: [], 2: [1]})

    validation = planner.validate_plan(plan)

    assert validation["valid"] is True
    assert len(validation["issues"]) == 0


def test_validate_plan_circular_dependency():
    """Test validation detects circular dependencies."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [2], 10),
        SubTask(2, "Task 2", "tool2", {}, [1], 5)
    ]

    plan = TaskPlan("id", "query", subtasks, 15, "simple", {1: [2], 2: [1]})

    validation = planner.validate_plan(plan)

    assert validation["valid"] is False
    assert "Circular dependency" in validation["issues"][0]


def test_validate_plan_missing_tool():
    """Test validation detects missing tools."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [
        SubTask(1, "Task 1", "nonexistent_tool", {}, [], 10)
    ]

    plan = TaskPlan("id", "query", subtasks, 10, "simple", {1: []})

    validation = planner.validate_plan(plan)

    assert validation["valid"] is False
    assert "not available" in validation["issues"][0]


def test_validate_plan_invalid_dependency():
    """Test validation detects invalid dependencies."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [99], 10)  # Depends on non-existent task
    ]

    plan = TaskPlan("id", "query", subtasks, 10, "simple", {1: [99]})

    validation = planner.validate_plan(plan)

    assert validation["valid"] is False


def test_resolve_execution_order_sequential():
    """Test execution order resolution for sequential tasks."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [], 10),
        SubTask(2, "Task 2", "tool2", {}, [1], 5),
        SubTask(3, "Task 3", "tool1", {}, [2], 5)
    ]

    batches = planner._resolve_execution_order(subtasks)

    assert len(batches) == 3
    assert batches[0] == [1]
    assert batches[1] == [2]
    assert batches[2] == [3]


def test_resolve_execution_order_parallel():
    """Test execution order resolution for parallel tasks."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [], 10),
        SubTask(2, "Task 2", "tool2", {}, [], 5),
        SubTask(3, "Task 3", "tool1", {}, [], 5)
    ]

    batches = planner._resolve_execution_order(subtasks)

    assert len(batches) == 1
    assert set(batches[0]) == {1, 2, 3}


def test_resolve_execution_order_mixed():
    """Test execution order resolution for mixed dependencies."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [], 10),
        SubTask(2, "Task 2", "tool2", {}, [], 5),
        SubTask(3, "Task 3", "tool1", {}, [1, 2], 5)
    ]

    batches = planner._resolve_execution_order(subtasks)

    assert len(batches) == 2
    assert set(batches[0]) == {1, 2}
    assert batches[1] == [3]


def test_has_circular_dependency_none():
    """Test circular dependency detection with no cycles."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [], 10),
        SubTask(2, "Task 2", "tool2", {}, [1], 5)
    ]

    assert planner._has_circular_dependency(subtasks) is False


def test_has_circular_dependency_detected():
    """Test circular dependency detection with cycle."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [2], 10),
        SubTask(2, "Task 2", "tool2", {}, [1], 5)
    ]

    assert planner._has_circular_dependency(subtasks) is True


def test_execute_plan_success():
    """Test successful plan execution."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [], 10),
        SubTask(2, "Task 2", "tool2", {}, [1], 5)
    ]

    plan = TaskPlan("id", "query", subtasks, 15, "simple", {1: [], 2: [1]})

    result = planner.execute_plan(plan)

    assert result["success"] is True
    assert len(result["results"]) == 2
    assert len(result["failed_subtasks"]) == 0


def test_execute_plan_with_progress_callback():
    """Test plan execution with progress callback."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [
        SubTask(1, "Task 1", "tool1", {}, [], 10)
    ]

    plan = TaskPlan("id", "query", subtasks, 10, "simple", {1: []})

    callback_called = []

    def progress_callback(subtask, result):
        callback_called.append(subtask.id)

    result = planner.execute_plan(plan, progress_callback)

    assert len(callback_called) == 1


def test_execute_plan_validation_failure():
    """Test plan execution with validation failure."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [
        SubTask(1, "Task 1", "nonexistent_tool", {}, [], 10)
    ]

    plan = TaskPlan("id", "query", subtasks, 10, "simple", {1: []})

    result = planner.execute_plan(plan)

    assert result["success"] is False
    assert "validation_errors" in result


def test_visualize_plan():
    """Test plan visualization."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    subtasks = [
        SubTask(1, "First task", "tool1", {}, [], 10),
        SubTask(2, "Second task", "tool2", {}, [1], 5)
    ]

    plan = TaskPlan("id", "Test query", subtasks, 15, "medium", {1: [], 2: [1]})

    visualization = planner.visualize_plan(plan)

    assert "Test query" in visualization
    assert "First task" in visualization
    assert "Second task" in visualization
    assert "Depends on" in visualization


def test_get_plan_stats_empty():
    """Test statistics with no plans."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    stats = planner.get_plan_stats()

    assert stats["total_plans"] == 0
    assert stats["avg_subtasks"] == 0.0


def test_get_plan_stats():
    """Test statistics after execution."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [SubTask(1, "Task 1", "tool1", {}, [], 10)]
    plan = TaskPlan("id", "query", subtasks, 10, "simple", {1: []})

    planner.execute_plan(plan)

    stats = planner.get_plan_stats()

    assert stats["total_plans"] == 1
    assert stats["avg_subtasks"] > 0


def test_parse_plan_json():
    """Test JSON parsing for plan."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    json_str = json.dumps({
        "subtasks": [
            {"id": 1, "description": "Test", "tool": "tool1", "args": {}, "depends_on": [], "estimated_time": 10}
        ]
    })

    subtasks = planner._parse_plan_json(json_str)

    assert len(subtasks) == 1
    assert subtasks[0].description == "Test"


def test_parse_plan_json_with_markdown():
    """Test JSON parsing with markdown code blocks."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    json_str = """```json
{
  "subtasks": [
    {"id": 1, "description": "Test", "tool": "tool1", "args": {}, "depends_on": [], "estimated_time": 10}
  ]
}
```"""

    subtasks = planner._parse_plan_json(json_str)

    assert len(subtasks) == 1


def test_fallback_plan():
    """Test fallback plan creation."""
    config = {"task_planning": {}}
    planner = TaskPlanner(create_mock_model_manager(), config, create_mock_tools())

    plan = planner._create_fallback_plan("Find code in project", "medium")

    assert len(plan.subtasks) == 1
    assert plan.complexity == "medium"


def test_single_subtask_plan():
    """Test plan with single subtask."""
    config = {"task_planning": {}}
    tools = create_mock_tools()
    planner = TaskPlanner(create_mock_model_manager(), config, tools)

    subtasks = [SubTask(1, "Task 1", "tool1", {}, [], 10)]
    plan = TaskPlan("id", "query", subtasks, 10, "simple", {1: []})

    result = planner.execute_plan(plan)

    assert result["success"] is True


def test_max_subtasks_limit():
    """Test max subtasks limit is enforced."""
    config = {"task_planning": {"max_subtasks": 3}}

    manager = Mock()
    mock_llm = Mock()
    mock_response = Mock()
    # Create plan with 5 subtasks
    mock_response.content = json.dumps({
        "subtasks": [
            {"id": i, "description": f"Task {i}", "tool": "tool1", "args": {}, "depends_on": [], "estimated_time": 10}
            for i in range(1, 6)
        ]
    })
    mock_llm.invoke = Mock(return_value=mock_response)
    manager.get_model = Mock(return_value=mock_llm)

    planner = TaskPlanner(manager, config, create_mock_tools())
    plan = planner.create_plan("Complex query")

    assert len(plan.subtasks) <= 3


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_estimate_complexity_simple,
        test_estimate_complexity_medium,
        test_estimate_complexity_complex,
        test_create_plan,
        test_create_plan_with_dependencies,
        test_validate_plan_valid,
        test_validate_plan_circular_dependency,
        test_validate_plan_missing_tool,
        test_validate_plan_invalid_dependency,
        test_resolve_execution_order_sequential,
        test_resolve_execution_order_parallel,
        test_resolve_execution_order_mixed,
        test_has_circular_dependency_none,
        test_has_circular_dependency_detected,
        test_execute_plan_success,
        test_execute_plan_with_progress_callback,
        test_execute_plan_validation_failure,
        test_visualize_plan,
        test_get_plan_stats_empty,
        test_get_plan_stats,
        test_parse_plan_json,
        test_parse_plan_json_with_markdown,
        test_fallback_plan,
        test_single_subtask_plan,
        test_max_subtasks_limit,
    ]

    print(f"Running {len(tests)} tests...\n")

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed out of {len(tests)} tests")
    print(f"Success rate: {passed/len(tests)*100:.1f}%")

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    exit(run_all_tests())
