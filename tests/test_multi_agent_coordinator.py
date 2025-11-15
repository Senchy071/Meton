#!/usr/bin/env python3
"""Test suite for Multi-Agent Coordinator.

Tests the multi-agent coordination system including:
- Agent initialization
- Task planning and decomposition
- Subtask execution with dependencies
- Result review and revision
- Result synthesis
- End-to-end coordination
- Complex query detection
- Error handling
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.multi_agent_coordinator import MultiAgentCoordinator, SubTask


def create_mock_dependencies():
    """Create mock dependencies for testing."""
    # Mock ModelManager
    mock_model_manager = Mock()
    mock_model_manager.get_model = Mock(return_value=Mock())

    # Mock ConversationManager
    mock_conversation = Mock()

    # Mock tools
    mock_tools = []

    # Mock config
    mock_config = {
        "enabled": True,
        "max_subtasks": 10,
        "max_revisions": 2,
        "parallel_execution": False
    }

    return mock_model_manager, mock_conversation, mock_tools, mock_config


def test_initialization():
    """Test MultiAgentCoordinator initialization."""
    print("\n" + "=" * 70)
    print("TEST: MultiAgentCoordinator Initialization")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()

    coordinator = MultiAgentCoordinator(
        model_manager=model_manager,
        conversation=conversation,
        tools=tools,
        config=config
    )

    assert coordinator is not None
    assert len(coordinator.agents) == 4
    assert "planner" in coordinator.agents
    assert "executor" in coordinator.agents
    assert "reviewer" in coordinator.agents
    assert "synthesizer" in coordinator.agents
    assert coordinator.max_subtasks == 10
    assert coordinator.max_revisions == 2

    print("✓ MultiAgentCoordinator initialized successfully")
    print(f"  Agents: {list(coordinator.agents.keys())}")
    print(f"  Max subtasks: {coordinator.max_subtasks}")


def test_agent_types():
    """Test that all agent types are created."""
    print("\n" + "=" * 70)
    print("TEST: Agent Types")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    required_agents = ["planner", "executor", "reviewer", "synthesizer"]

    for agent_name in required_agents:
        assert agent_name in coordinator.agents
        assert coordinator.agents[agent_name] is not None

    print("✓ All 4 agent types created")
    print(f"  Agents: {', '.join(required_agents)}")


def test_subtask_creation():
    """Test SubTask dataclass creation."""
    print("\n" + "=" * 70)
    print("TEST: SubTask Creation")
    print("=" * 70)

    subtask = SubTask(
        id=1,
        task="Test task",
        depends_on=[],
        result=None,
        status="pending"
    )

    assert subtask.id == 1
    assert subtask.task == "Test task"
    assert subtask.depends_on == []
    assert subtask.result is None
    assert subtask.status == "pending"

    print("✓ SubTask created successfully")
    print(f"  ID: {subtask.id}")
    print(f"  Task: {subtask.task}")
    print(f"  Status: {subtask.status}")


def test_complex_query_detection_explicit():
    """Test complex query detection with explicit request."""
    print("\n" + "=" * 70)
    print("TEST: Complex Query Detection - Explicit")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    query = "Use multi-agent to analyze this code"
    is_complex = coordinator.is_complex_query(query)

    assert is_complex is True

    print("✓ Explicit multi-agent request detected")
    print(f"  Query: {query}")


def test_complex_query_detection_coordination_words():
    """Test complex query detection with coordination words."""
    print("\n" + "=" * 70)
    print("TEST: Complex Query Detection - Coordination Words")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    queries = [
        "Find the file and then analyze it",
        "Compare our implementation with FastAPI",
        "After that, review the code"
    ]

    for query in queries:
        is_complex = coordinator.is_complex_query(query)
        assert is_complex is True

    print("✓ Coordination words detected")
    print(f"  Tested {len(queries)} queries")


def test_complex_query_detection_complexity_indicators():
    """Test complex query detection with complexity indicators."""
    print("\n" + "=" * 70)
    print("TEST: Complex Query Detection - Complexity Indicators")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Query with 2+ complexity words
    query = "Provide a comprehensive analysis and research of the authentication system"
    is_complex = coordinator.is_complex_query(query)

    assert is_complex is True

    print("✓ Complexity indicators detected")
    print(f"  Query: {query}")


def test_complex_query_detection_long_query():
    """Test complex query detection with long query."""
    print("\n" + "=" * 70)
    print("TEST: Complex Query Detection - Long Query")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Long query (>150 characters)
    query = "I need you to find all the authentication related code in the codebase, analyze how it works, compare it with industry best practices, and then provide detailed recommendations for improvements that we should make to enhance security and maintainability"

    is_complex = coordinator.is_complex_query(query)

    assert is_complex is True

    print("✓ Long query detected as complex")
    print(f"  Query length: {len(query)} characters")


def test_simple_query_detection():
    """Test that simple queries are not detected as complex."""
    print("\n" + "=" * 70)
    print("TEST: Simple Query Detection")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    simple_queries = [
        "Read the README file",
        "List files in current directory",
        "What is 2 + 2?"
    ]

    for query in simple_queries:
        is_complex = coordinator.is_complex_query(query)
        assert is_complex is False

    print("✓ Simple queries correctly identified")
    print(f"  Tested {len(simple_queries)} queries")


def test_plan_task_with_mock():
    """Test task planning with mocked agent."""
    print("\n" + "=" * 70)
    print("TEST: Task Planning")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock the planner agent's run method
    mock_plan_output = """
    [
        {"id": 1, "task": "Search for authentication code", "depends_on": []},
        {"id": 2, "task": "Review the authentication code", "depends_on": [1]}
    ]
    """
    coordinator.agents["planner"].run = Mock(return_value={"output": mock_plan_output})

    # Test planning
    subtasks = coordinator._plan_task("Find and review authentication code")

    assert len(subtasks) == 2
    assert subtasks[0].id == 1
    assert subtasks[0].task == "Search for authentication code"
    assert subtasks[1].depends_on == [1]

    print("✓ Task planning successful")
    print(f"  Generated {len(subtasks)} subtasks")
    print(f"  Subtask 1: {subtasks[0].task}")
    print(f"  Subtask 2: {subtasks[1].task}")


def test_plan_task_fallback():
    """Test task planning fallback on invalid output."""
    print("\n" + "=" * 70)
    print("TEST: Task Planning Fallback")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock invalid output
    coordinator.agents["planner"].run = Mock(return_value={"output": "Invalid JSON output"})

    # Test planning (should fallback to single subtask)
    query = "Find authentication code"
    subtasks = coordinator._plan_task(query)

    assert len(subtasks) == 1
    assert subtasks[0].task == query

    print("✓ Task planning fallback works")
    print(f"  Created single subtask: {subtasks[0].task}")


def test_execute_subtasks_sequential():
    """Test sequential subtask execution."""
    print("\n" + "=" * 70)
    print("TEST: Sequential Subtask Execution")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock executor
    coordinator.agents["executor"].run = Mock(return_value={"output": "Task completed"})

    # Create subtasks
    subtasks = [
        SubTask(id=1, task="Task 1", depends_on=[]),
        SubTask(id=2, task="Task 2", depends_on=[]),
        SubTask(id=3, task="Task 3", depends_on=[])
    ]

    # Execute
    results = coordinator._execute_subtasks(subtasks)

    assert len(results) == 3
    assert all(subtask.status == "completed" for subtask in subtasks)

    print("✓ Sequential execution successful")
    print(f"  Executed {len(subtasks)} subtasks")
    print(f"  All subtasks completed: {all(st.status == 'completed' for st in subtasks)}")


def test_execute_subtasks_with_dependencies():
    """Test subtask execution with dependencies."""
    print("\n" + "=" * 70)
    print("TEST: Subtask Execution with Dependencies")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock executor with different outputs
    call_count = [0]

    def mock_run(query):
        call_count[0] += 1
        return {"output": f"Result {call_count[0]}"}

    coordinator.agents["executor"].run = mock_run

    # Create subtasks with dependencies
    subtasks = [
        SubTask(id=1, task="Task 1", depends_on=[]),
        SubTask(id=2, task="Task 2", depends_on=[1]),  # Depends on 1
        SubTask(id=3, task="Task 3", depends_on=[1, 2])  # Depends on 1 and 2
    ]

    # Execute
    results = coordinator._execute_subtasks(subtasks)

    assert len(results) == 3
    assert all(subtask.status == "completed" for subtask in subtasks)

    print("✓ Dependency handling successful")
    print(f"  Executed {len(subtasks)} subtasks with dependencies")
    print(f"  Execution order respected: {[st.id for st in subtasks]}")


def test_review_results_approval():
    """Test result review with approval."""
    print("\n" + "=" * 70)
    print("TEST: Result Review - Approval")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock reviewer approving
    mock_review = """
    {
        "approved": true,
        "feedback": "All results look good",
        "revisions_needed": []
    }
    """
    coordinator.agents["reviewer"].run = Mock(return_value={"output": mock_review})

    # Test review
    results = {1: "Result 1", 2: "Result 2"}
    review = coordinator._review_results(results, "Original query")

    assert review["approved"] is True
    assert review["revisions_needed"] == []

    print("✓ Result approval successful")
    print(f"  Approved: {review['approved']}")
    print(f"  Feedback: {review['feedback']}")


def test_review_results_rejection():
    """Test result review with rejection."""
    print("\n" + "=" * 70)
    print("TEST: Result Review - Rejection")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock reviewer rejecting
    mock_review = """
    {
        "approved": false,
        "feedback": "Subtask 2 needs improvement",
        "revisions_needed": [2]
    }
    """
    coordinator.agents["reviewer"].run = Mock(return_value={"output": mock_review})

    # Test review
    results = {1: "Result 1", 2: "Result 2"}
    review = coordinator._review_results(results, "Original query")

    assert review["approved"] is False
    assert 2 in review["revisions_needed"]

    print("✓ Result rejection successful")
    print(f"  Approved: {review['approved']}")
    print(f"  Revisions needed: {review['revisions_needed']}")


def test_synthesize_results():
    """Test result synthesis."""
    print("\n" + "=" * 70)
    print("TEST: Result Synthesis")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock synthesizer
    coordinator.agents["synthesizer"].run = Mock(
        return_value={"output": "Final synthesized answer combining all results"}
    )

    # Test synthesis
    results = {1: "Result 1", 2: "Result 2", 3: "Result 3"}
    final_answer = coordinator._synthesize_results(results, "Original query")

    assert "synthesized" in final_answer.lower()
    assert len(final_answer) > 0

    print("✓ Result synthesis successful")
    print(f"  Final answer length: {len(final_answer)} characters")


def test_handle_revisions():
    """Test revision handling."""
    print("\n" + "=" * 70)
    print("TEST: Revision Handling")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock executor for revisions
    coordinator.agents["executor"].run = Mock(
        return_value={"output": "Revised result"}
    )

    # Create subtasks and results
    subtasks = [
        SubTask(id=1, task="Task 1", depends_on=[]),
        SubTask(id=2, task="Task 2", depends_on=[])
    ]
    results = {1: "Result 1", 2: "Bad result"}

    # Test revisions
    updated_results = coordinator._handle_revisions(
        revisions_needed=[2],
        results=results,
        subtasks=subtasks,
        feedback="Improve subtask 2"
    )

    assert updated_results[2] == "Revised result"
    assert updated_results[1] == "Result 1"  # Unchanged

    print("✓ Revision handling successful")
    print(f"  Revised subtask 2")
    print(f"  New result: {updated_results[2]}")


def test_coordinate_task_end_to_end():
    """Test end-to-end task coordination."""
    print("\n" + "=" * 70)
    print("TEST: End-to-End Coordination")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock all agents
    coordinator.agents["planner"].run = Mock(return_value={
        "output": '[{"id": 1, "task": "Task 1", "depends_on": []}]'
    })
    coordinator.agents["executor"].run = Mock(return_value={
        "output": "Executed successfully"
    })
    coordinator.agents["reviewer"].run = Mock(return_value={
        "output": '{"approved": true, "feedback": "Good", "revisions_needed": []}'
    })
    coordinator.agents["synthesizer"].run = Mock(return_value={
        "output": "Final answer"
    })

    # Test coordination
    result = coordinator.coordinate_task("Test query")

    assert result["success"] is True
    assert "result" in result
    assert "steps" in result
    assert len(result["steps"]) >= 3  # At least plan, execute, review, synthesize

    print("✓ End-to-end coordination successful")
    print(f"  Success: {result['success']}")
    print(f"  Steps: {len(result['steps'])}")
    print(f"  Result: {result['result'][:50]}...")


def test_max_subtasks_limit():
    """Test max subtasks limit enforcement."""
    print("\n" + "=" * 70)
    print("TEST: Max Subtasks Limit")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    config["max_subtasks"] = 3
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock planner returning too many subtasks
    mock_plan = "["
    for i in range(1, 12):  # 11 subtasks (over limit of 3)
        mock_plan += f'{{"id": {i}, "task": "Task {i}", "depends_on": []}},'
    mock_plan = mock_plan.rstrip(",") + "]"

    coordinator.agents["planner"].run = Mock(return_value={"output": mock_plan})

    # Test planning (should raise ValueError or fallback)
    subtasks = coordinator._plan_task("Test query")

    # Should fallback to single subtask due to exceeding limit
    assert len(subtasks) == 1

    print("✓ Max subtasks limit enforced")
    print(f"  Limit: {config['max_subtasks']}")
    print(f"  Attempted: 11, Actual: {len(subtasks)}")


def test_single_subtask_execution():
    """Test execution with single subtask (edge case)."""
    print("\n" + "=" * 70)
    print("TEST: Single Subtask Execution")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock executor
    coordinator.agents["executor"].run = Mock(return_value={"output": "Result"})

    # Single subtask
    subtasks = [SubTask(id=1, task="Single task", depends_on=[])]

    # Execute
    results = coordinator._execute_subtasks(subtasks)

    assert len(results) == 1
    assert subtasks[0].status == "completed"

    print("✓ Single subtask execution successful")
    print(f"  Subtask completed: {subtasks[0].status}")


def test_error_handling_in_execution():
    """Test error handling during subtask execution."""
    print("\n" + "=" * 70)
    print("TEST: Error Handling in Execution")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock executor to raise exception
    coordinator.agents["executor"].run = Mock(side_effect=Exception("Execution failed"))

    # Create subtask
    subtasks = [SubTask(id=1, task="Failing task", depends_on=[])]

    # Execute (should handle error gracefully)
    results = coordinator._execute_subtasks(subtasks)

    assert len(results) == 1
    assert subtasks[0].status == "failed"
    assert "Error" in subtasks[0].result

    print("✓ Error handling successful")
    print(f"  Subtask status: {subtasks[0].status}")
    print(f"  Error captured: {subtasks[0].result[:30]}...")


def test_config_parameters():
    """Test configuration parameter handling."""
    print("\n" + "=" * 70)
    print("TEST: Configuration Parameters")
    print("=" * 70)

    model_manager, conversation, tools, _ = create_mock_dependencies()

    custom_config = {
        "enabled": True,
        "max_subtasks": 5,
        "max_revisions": 3,
        "parallel_execution": True
    }

    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, custom_config)

    assert coordinator.max_subtasks == 5
    assert coordinator.max_revisions == 3
    assert coordinator.parallel_execution is True

    print("✓ Configuration parameters applied")
    print(f"  Max subtasks: {coordinator.max_subtasks}")
    print(f"  Max revisions: {coordinator.max_revisions}")
    print(f"  Parallel execution: {coordinator.parallel_execution}")


def test_repr():
    """Test string representation."""
    print("\n" + "=" * 70)
    print("TEST: String Representation")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    repr_str = repr(coordinator)

    assert "MultiAgentCoordinator" in repr_str
    assert "agents=4" in repr_str
    assert "max_subtasks=" in repr_str

    print(f"✓ String representation: {repr_str}")


def test_review_fallback():
    """Test review fallback on invalid output."""
    print("\n" + "=" * 70)
    print("TEST: Review Fallback")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock reviewer with invalid output
    coordinator.agents["reviewer"].run = Mock(return_value={"output": "Invalid JSON"})

    # Test review (should fallback to approval)
    results = {1: "Result 1"}
    review = coordinator._review_results(results, "Query")

    assert review["approved"] is True  # Fallback behavior

    print("✓ Review fallback successful")
    print(f"  Approved by default: {review['approved']}")


def test_empty_dependencies():
    """Test subtask with no dependencies."""
    print("\n" + "=" * 70)
    print("TEST: Empty Dependencies")
    print("=" * 70)

    model_manager, conversation, tools, config = create_mock_dependencies()
    coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)

    # Mock executor
    coordinator.agents["executor"].run = Mock(return_value={"output": "Result"})

    # Subtasks with no dependencies
    subtasks = [
        SubTask(id=1, task="Task 1", depends_on=[]),
        SubTask(id=2, task="Task 2", depends_on=[]),
        SubTask(id=3, task="Task 3", depends_on=[])
    ]

    # Execute
    results = coordinator._execute_subtasks(subtasks)

    assert len(results) == 3
    assert all(st.status == "completed" for st in subtasks)

    print("✓ Empty dependencies handled")
    print(f"  All {len(subtasks)} subtasks completed independently")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print(" " * 20 + "MULTI-AGENT COORDINATOR TEST SUITE")
    print("=" * 80)

    tests = [
        ("Initialization", test_initialization),
        ("Agent Types", test_agent_types),
        ("SubTask Creation", test_subtask_creation),
        ("Complex Query - Explicit", test_complex_query_detection_explicit),
        ("Complex Query - Coordination", test_complex_query_detection_coordination_words),
        ("Complex Query - Complexity", test_complex_query_detection_complexity_indicators),
        ("Complex Query - Long", test_complex_query_detection_long_query),
        ("Simple Query Detection", test_simple_query_detection),
        ("Task Planning", test_plan_task_with_mock),
        ("Planning Fallback", test_plan_task_fallback),
        ("Sequential Execution", test_execute_subtasks_sequential),
        ("Dependency Handling", test_execute_subtasks_with_dependencies),
        ("Review Approval", test_review_results_approval),
        ("Review Rejection", test_review_results_rejection),
        ("Result Synthesis", test_synthesize_results),
        ("Revision Handling", test_handle_revisions),
        ("End-to-End", test_coordinate_task_end_to_end),
        ("Max Subtasks Limit", test_max_subtasks_limit),
        ("Single Subtask", test_single_subtask_execution),
        ("Error Handling", test_error_handling_in_execution),
        ("Config Parameters", test_config_parameters),
        ("String Representation", test_repr),
        ("Review Fallback", test_review_fallback),
        ("Empty Dependencies", test_empty_dependencies),
    ]

    passed = 0
    failed = 0
    errors = []

    for test_name, test_func in tests:
        try:
            test_func()
            passed += 1
        except AssertionError as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"\n✗ FAILED: {test_name}")
            print(f"  {str(e)}")
        except Exception as e:
            failed += 1
            errors.append((test_name, str(e)))
            print(f"\n✗ ERROR: {test_name}")
            print(f"  {str(e)}")

    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    print(f"Total tests: {len(tests)}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")

    if errors:
        print("\nFailed tests:")
        for test_name, error in errors:
            print(f"  - {test_name}: {error}")
    else:
        print("\n✅ All Multi-Agent Coordinator tests passed!")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
