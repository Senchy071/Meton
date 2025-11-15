#!/usr/bin/env python3
"""Test suite for Iterative Improvement Loop.

Tests the iterative improvement capabilities including:
- Single and multi-iteration improvement
- Max iterations enforcement
- Quality threshold stopping
- Convergence detection
- Should continue logic
- Improvement tracking
- Statistics calculation
- Error handling
- Edge cases
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from agent.iterative_improvement import IterativeImprovementLoop, IterationRecord, ImprovementSession


def create_mock_dependencies():
    """Create mock dependencies for testing."""
    # Mock ModelManager
    mock_model_manager = Mock()
    mock_llm = Mock()
    mock_model_manager.get_model = Mock(return_value=mock_llm)

    # Mock SelfReflectionModule
    mock_reflection = Mock()

    # Mock config
    mock_config = {
        "enabled": True,
        "max_iterations": 3,
        "quality_threshold": 0.85,
        "convergence_threshold": 0.05,
        "convergence_window": 2
    }

    return mock_model_manager, mock_llm, mock_reflection, mock_config


def test_initialization():
    """Test IterativeImprovementLoop initialization."""
    print("\n" + "=" * 70)
    print("TEST: IterativeImprovementLoop Initialization")
    print("=" * 70)

    model_manager, _, reflection, config = create_mock_dependencies()

    loop = IterativeImprovementLoop(model_manager, reflection, config)

    assert loop is not None
    assert loop.max_iterations == 3
    assert loop.quality_threshold == 0.85
    assert loop.convergence_threshold == 0.05
    assert len(loop.improvement_history) == 0

    print("✓ IterativeImprovementLoop initialized successfully")
    print(f"  Max iterations: {loop.max_iterations}")
    print(f"  Quality threshold: {loop.quality_threshold}")
    print(f"  Convergence threshold: {loop.convergence_threshold}")


def test_iteration_record_creation():
    """Test IterationRecord dataclass creation."""
    print("\n" + "=" * 70)
    print("TEST: IterationRecord Creation")
    print("=" * 70)

    record = IterationRecord(
        iteration=1,
        response="Test response",
        quality_score=0.75,
        issues=["issue1"],
        suggestions=["suggestion1"]
    )

    assert record.iteration == 1
    assert record.quality_score == 0.75
    assert len(record.issues) == 1
    assert record.timestamp is not None

    print("✓ IterationRecord created successfully")
    print(f"  Iteration: {record.iteration}")
    print(f"  Quality: {record.quality_score}")


def test_already_excellent_no_iteration():
    """Test that already excellent responses don't iterate."""
    print("\n" + "=" * 70)
    print("TEST: Already Excellent - No Iteration")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock high quality initial response
    reflection.reflect_on_response = Mock(return_value={
        "quality_score": 0.92,
        "issues": [],
        "suggestions": [],
        "should_improve": False
    })

    query = "Test query"
    response = "Already excellent response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    assert result["iterations"] == 0
    assert result["converged"] is True
    assert result["final_response"] == response
    assert result["final_score"] == 0.92

    print("✓ No iteration for excellent response")
    print(f"  Initial score: {result['initial_score']}")
    print(f"  Iterations: {result['iterations']}")


def test_single_iteration_improvement():
    """Test single iteration improvement."""
    print("\n" + "=" * 70)
    print("TEST: Single Iteration Improvement")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection: initial low, then excellent after improvement
    reflection_responses = [
        {"quality_score": 0.65, "issues": ["incomplete"], "suggestions": ["add more"], "should_improve": True},
        {"quality_score": 0.88, "issues": [], "suggestions": [], "should_improve": False}
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM improvement
    llm_response = Mock()
    llm_response.content = "Improved response with more detail"
    llm.invoke = Mock(return_value=llm_response)

    query = "Test query"
    response = "Initial incomplete response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    assert result["iterations"] == 1
    assert result["final_score"] == 0.88
    assert result["improvement"] > 0
    assert result["converged"] is True

    print("✓ Single iteration improvement successful")
    print(f"  Initial score: {result['initial_score']}")
    print(f"  Final score: {result['final_score']}")
    print(f"  Improvement: +{result['improvement']:.2f}")


def test_multi_iteration_improvement():
    """Test multi-iteration improvement."""
    print("\n" + "=" * 70)
    print("TEST: Multi-Iteration Improvement")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection: gradual improvement over 3 iterations
    reflection_responses = [
        {"quality_score": 0.55, "issues": ["incomplete", "unclear"], "suggestions": ["add detail", "clarify"], "should_improve": True},
        {"quality_score": 0.70, "issues": ["missing_code"], "suggestions": ["add examples"], "should_improve": True},
        {"quality_score": 0.82, "issues": ["too_verbose"], "suggestions": ["be concise"], "should_improve": True},
        {"quality_score": 0.90, "issues": [], "suggestions": [], "should_improve": False}
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM improvement
    llm_response = Mock()
    llm_response.content = "Improved response"
    llm.invoke = Mock(return_value=llm_response)

    query = "Test query"
    response = "Initial poor response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    assert result["iterations"] == 3
    assert result["final_score"] == 0.90
    assert result["improvement"] > 0.3
    assert len(result["improvement_path"]) == 4  # Initial + 3 iterations

    print("✓ Multi-iteration improvement successful")
    print(f"  Iterations: {result['iterations']}")
    print(f"  Initial: {result['initial_score']}, Final: {result['final_score']}")
    print(f"  Total improvement: +{result['improvement']:.2f}")


def test_max_iterations_reached():
    """Test max iterations limit is enforced."""
    print("\n" + "=" * 70)
    print("TEST: Max Iterations Reached")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    config["max_iterations"] = 2
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection: never reaches threshold, always improving slightly (avoid convergence)
    reflection_responses = [
        {"quality_score": 0.65, "issues": ["issue1"], "suggestions": ["fix1"], "should_improve": True},
        {"quality_score": 0.72, "issues": ["issue2"], "suggestions": ["fix2"], "should_improve": True},
        {"quality_score": 0.78, "issues": ["issue3"], "suggestions": ["fix3"], "should_improve": True}
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM improvement
    llm_response = Mock()
    llm_response.content = "Slightly improved"
    llm.invoke = Mock(return_value=llm_response)

    query = "Test query"
    response = "Initial response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    assert result["iterations"] == 2
    assert result["final_score"] == 0.78

    print("✓ Max iterations limit enforced")
    print(f"  Max allowed: {config['max_iterations']}")
    print(f"  Iterations: {result['iterations']}")


def test_quality_threshold_reached():
    """Test stopping when quality threshold reached."""
    print("\n" + "=" * 70)
    print("TEST: Quality Threshold Reached")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection: reaches threshold on iteration 2
    reflection_responses = [
        {"quality_score": 0.65, "issues": ["incomplete"], "suggestions": ["add more"], "should_improve": True},
        {"quality_score": 0.78, "issues": ["minor"], "suggestions": ["small fix"], "should_improve": True},
        {"quality_score": 0.88, "issues": [], "suggestions": [], "should_improve": False}  # Above 0.85 threshold
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM
    llm_response = Mock()
    llm_response.content = "Improved"
    llm.invoke = Mock(return_value=llm_response)

    query = "Test query"
    response = "Initial response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    assert result["iterations"] == 2
    assert result["final_score"] >= loop.quality_threshold
    assert result["converged"] is True

    print("✓ Stopped when quality threshold reached")
    print(f"  Threshold: {loop.quality_threshold}")
    print(f"  Final score: {result['final_score']}")
    print(f"  Iterations: {result['iterations']}")


def test_convergence_detection():
    """Test convergence detection when improvement plateaus."""
    print("\n" + "=" * 70)
    print("TEST: Convergence Detection")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection: plateaus at 0.74 (improvement < 0.05)
    reflection_responses = [
        {"quality_score": 0.65, "issues": ["issue1"], "suggestions": ["fix1"], "should_improve": True},
        {"quality_score": 0.72, "issues": ["issue2"], "suggestions": ["fix2"], "should_improve": True},
        {"quality_score": 0.74, "issues": ["issue3"], "suggestions": ["fix3"], "should_improve": True}  # +0.02, below 0.05 threshold
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM
    llm_response = Mock()
    llm_response.content = "Improved"
    llm.invoke = Mock(return_value=llm_response)

    query = "Test query"
    response = "Initial response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    # Should detect convergence and stop
    assert result["converged"] is True
    print("✓ Convergence detected when improvement plateaued")
    print(f"  Scores: {[result['improvement_path'][i]['quality_score'] for i in range(len(result['improvement_path']))]}")


def test_detect_convergence_method():
    """Test _detect_convergence method directly."""
    print("\n" + "=" * 70)
    print("TEST: Detect Convergence Method")
    print("=" * 70)

    model_manager, _, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Test converged (improvement < 0.05)
    scores_converged = [0.65, 0.72, 0.74]  # 0.74 - 0.72 = 0.02
    assert loop._detect_convergence(scores_converged) is True

    # Test not converged (still improving)
    scores_improving = [0.60, 0.70, 0.82]  # 0.82 - 0.70 = 0.12
    assert loop._detect_convergence(scores_improving) is False

    # Test insufficient scores
    scores_few = [0.65, 0.72]
    assert loop._detect_convergence(scores_few) is False

    print("✓ Convergence detection logic correct")
    print(f"  Converged: {scores_converged}")
    print(f"  Still improving: {scores_improving}")


def test_should_continue_iteration():
    """Test _should_continue_iteration logic."""
    print("\n" + "=" * 70)
    print("TEST: Should Continue Iteration")
    print("=" * 70)

    model_manager, _, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Should continue: low quality, issues present
    reflection1 = {"quality_score": 0.65, "issues": ["incomplete"], "should_improve": True}
    scores1 = [0.60, 0.65]
    assert loop._should_continue_iteration(2, reflection1, scores1) is True

    # Should stop: quality threshold reached
    reflection2 = {"quality_score": 0.90, "issues": [], "should_improve": False}
    scores2 = [0.60, 0.75, 0.90]
    assert loop._should_continue_iteration(2, reflection2, scores2) is False

    # Should stop: no issues
    reflection3 = {"quality_score": 0.75, "issues": [], "should_improve": False}
    scores3 = [0.60, 0.70, 0.75]
    assert loop._should_continue_iteration(2, reflection3, scores3) is False

    print("✓ Should continue logic correct")


def test_quality_decline_reverts():
    """Test that quality decline causes reversion."""
    print("\n" + "=" * 70)
    print("TEST: Quality Decline Reverts")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection: quality declines on iteration 2
    reflection_responses = [
        {"quality_score": 0.65, "issues": ["issue1"], "suggestions": ["fix1"], "should_improve": True},
        {"quality_score": 0.78, "issues": ["issue2"], "suggestions": ["fix2"], "should_improve": True},
        {"quality_score": 0.70, "issues": ["issue3"], "suggestions": ["fix3"], "should_improve": True}  # Declined!
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM
    llm_response = Mock()
    llm_response.content = "Improved (or not)"
    llm.invoke = Mock(return_value=llm_response)

    query = "Test query"
    response = "Initial response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    # Should revert to iteration 1 (score 0.78)
    assert result["final_score"] == 0.78
    assert result["iterations"] == 1

    print("✓ Quality decline detected and reverted")
    print(f"  Peak score: 0.78, Declined to: 0.70")
    print(f"  Reverted to iteration: 1")


def test_no_issues_stops_iteration():
    """Test that no issues remaining stops iteration."""
    print("\n" + "=" * 70)
    print("TEST: No Issues Stops Iteration")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection: no issues after first improvement
    reflection_responses = [
        {"quality_score": 0.70, "issues": ["incomplete"], "suggestions": ["add detail"], "should_improve": True},
        {"quality_score": 0.82, "issues": [], "suggestions": [], "should_improve": False}  # No issues, below threshold
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM
    llm_response = Mock()
    llm_response.content = "Improved"
    llm.invoke = Mock(return_value=llm_response)

    query = "Test query"
    response = "Initial response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    assert result["iterations"] == 1
    assert len(result["improvement_path"][1]["issues"]) == 0

    print("✓ Stopped when no issues remaining")
    print(f"  Final score: {result['final_score']}")
    print(f"  Issues: {result['improvement_path'][-1]['issues']}")


def test_generate_improvement_prompt():
    """Test improvement prompt generation."""
    print("\n" + "=" * 70)
    print("TEST: Generate Improvement Prompt")
    print("=" * 70)

    model_manager, _, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    query = "Test query"
    response = "Test response"
    reflection_data = {
        "issues": ["incomplete_answer", "missing_code"],
        "suggestions": ["Add more detail", "Include code examples"]
    }
    iteration = 2

    prompt = loop._generate_improvement_prompt(query, response, reflection_data, iteration)

    assert "iteration 2" in prompt.lower()
    assert query in prompt
    assert response in prompt
    assert "incomplete_answer" in prompt
    assert "Add more detail" in prompt

    print("✓ Improvement prompt generated")
    print(f"  Prompt length: {len(prompt)} chars")


def test_improvement_tracking():
    """Test that improvements are tracked correctly."""
    print("\n" + "=" * 70)
    print("TEST: Improvement Tracking")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection
    reflection_responses = [
        {"quality_score": 0.60, "issues": ["issue1"], "suggestions": ["fix1"], "should_improve": True},
        {"quality_score": 0.90, "issues": [], "suggestions": [], "should_improve": False}
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM
    llm_response = Mock()
    llm_response.content = "Improved"
    llm.invoke = Mock(return_value=llm_response)

    query = "Test query"
    response = "Initial response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    # Check improvement path
    assert len(result["improvement_path"]) == 2  # Initial + 1 iteration
    assert result["improvement_path"][0]["iteration"] == 0
    assert result["improvement_path"][1]["iteration"] == 1

    # Check history
    assert len(loop.improvement_history) == 1
    session = loop.improvement_history[0]
    assert session.iterations == 1
    assert session.initial_score == 0.60
    assert session.final_score == 0.90

    print("✓ Improvement tracking works")
    print(f"  Tracked {len(result['improvement_path'])} iterations")
    print(f"  History: {len(loop.improvement_history)} sessions")


def test_get_improvement_stats_empty():
    """Test getting stats with no history."""
    print("\n" + "=" * 70)
    print("TEST: Get Improvement Stats - Empty")
    print("=" * 70)

    model_manager, _, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    stats = loop.get_improvement_stats()

    assert stats["total_sessions"] == 0
    assert stats["average_iterations"] == 0.0
    assert stats["average_improvement"] == 0.0

    print("✓ Empty stats returned correctly")


def test_get_improvement_stats_with_data():
    """Test getting stats with improvement history."""
    print("\n" + "=" * 70)
    print("TEST: Get Improvement Stats - With Data")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Run 3 improvement sessions
    for i in range(3):
        reflection_responses = [
            {"quality_score": 0.60, "issues": ["issue"], "suggestions": ["fix"], "should_improve": True},
            {"quality_score": 0.85 + i * 0.02, "issues": [], "suggestions": [], "should_improve": False}
        ]
        reflection.reflect_on_response = Mock(side_effect=reflection_responses)

        llm_response = Mock()
        llm_response.content = "Improved"
        llm.invoke = Mock(return_value=llm_response)

        loop.iterate_until_satisfied("Query", "Response", {})

    stats = loop.get_improvement_stats()

    assert stats["total_sessions"] == 3
    assert stats["average_iterations"] == 1.0  # Each session: 1 iteration
    assert stats["average_improvement"] > 0.20
    assert stats["convergence_rate"] == 100.0  # All converged

    print("✓ Stats calculated correctly")
    print(f"  Total sessions: {stats['total_sessions']}")
    print(f"  Avg iterations: {stats['average_iterations']}")
    print(f"  Avg improvement: +{stats['average_improvement']:.2f}")


def test_sessions_by_iterations_distribution():
    """Test sessions_by_iterations distribution in stats."""
    print("\n" + "=" * 70)
    print("TEST: Sessions By Iterations Distribution")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Session 1: 0 iterations (already excellent)
    reflection.reflect_on_response = Mock(return_value={
        "quality_score": 0.95, "issues": [], "suggestions": [], "should_improve": False
    })
    loop.iterate_until_satisfied("Query1", "Excellent response", {})

    # Session 2: 1 iteration
    reflection_responses = [
        {"quality_score": 0.70, "issues": ["issue"], "suggestions": ["fix"], "should_improve": True},
        {"quality_score": 0.88, "issues": [], "suggestions": [], "should_improve": False}
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)
    llm_response = Mock()
    llm_response.content = "Improved"
    llm.invoke = Mock(return_value=llm_response)
    loop.iterate_until_satisfied("Query2", "Good response", {})

    # Session 3: 2 iterations
    reflection_responses = [
        {"quality_score": 0.60, "issues": ["issue1"], "suggestions": ["fix1"], "should_improve": True},
        {"quality_score": 0.75, "issues": ["issue2"], "suggestions": ["fix2"], "should_improve": True},
        {"quality_score": 0.90, "issues": [], "suggestions": [], "should_improve": False}
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)
    llm.invoke = Mock(return_value=llm_response)
    loop.iterate_until_satisfied("Query3", "Poor response", {})

    stats = loop.get_improvement_stats()
    dist = stats["sessions_by_iterations"]

    assert dist[0] == 1  # One session with 0 iterations
    assert dist[1] == 1  # One session with 1 iteration
    assert dist[2] == 1  # One session with 2 iterations

    print("✓ Iteration distribution calculated")
    for iterations, count in dist.items():
        print(f"  {iterations} iterations: {count} session(s)")


def test_clear_history():
    """Test clearing improvement history."""
    print("\n" + "=" * 70)
    print("TEST: Clear History")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Add a session
    reflection.reflect_on_response = Mock(return_value={
        "quality_score": 0.90, "issues": [], "suggestions": [], "should_improve": False
    })
    loop.iterate_until_satisfied("Query", "Response", {})

    assert len(loop.improvement_history) == 1

    loop.clear_history()

    assert len(loop.improvement_history) == 0

    print("✓ History cleared")


def test_config_custom_values():
    """Test custom configuration values."""
    print("\n" + "=" * 70)
    print("TEST: Custom Configuration Values")
    print("=" * 70)

    model_manager, _, reflection, _ = create_mock_dependencies()

    custom_config = {
        "enabled": True,
        "max_iterations": 5,
        "quality_threshold": 0.90,
        "convergence_threshold": 0.03,
        "convergence_window": 3
    }

    loop = IterativeImprovementLoop(model_manager, reflection, custom_config)

    assert loop.max_iterations == 5
    assert loop.quality_threshold == 0.90
    assert loop.convergence_threshold == 0.03
    assert loop.convergence_window == 3

    print("✓ Custom config applied")
    print(f"  Max iterations: {loop.max_iterations}")
    print(f"  Quality threshold: {loop.quality_threshold}")


def test_repr():
    """Test string representation."""
    print("\n" + "=" * 70)
    print("TEST: String Representation")
    print("=" * 70)

    model_manager, _, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    repr_str = repr(loop)

    assert "IterativeImprovementLoop" in repr_str
    assert "sessions=0" in repr_str
    assert "max_iterations=3" in repr_str
    assert "threshold=0.85" in repr_str

    print(f"✓ String representation: {repr_str}")


def test_error_handling_in_improvement():
    """Test error handling during improvement generation."""
    print("\n" + "=" * 70)
    print("TEST: Error Handling in Improvement")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Mock reflection
    reflection_responses = [
        {"quality_score": 0.65, "issues": ["issue"], "suggestions": ["fix"], "should_improve": True},
        {"quality_score": 0.65, "issues": ["issue"], "suggestions": ["fix"], "should_improve": True}  # Same (no improvement due to error)
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    # Mock LLM to raise exception
    llm.invoke = Mock(side_effect=Exception("LLM failed"))

    query = "Test query"
    response = "Initial response"
    context = {}

    result = loop.iterate_until_satisfied(query, response, context)

    # Should handle error gracefully (return original response)
    assert result["final_response"] == response
    assert result["iterations"] == 1  # Tried one iteration

    print("✓ Error handled gracefully")
    print("  Returned original response on LLM failure")


def test_max_improvement_stat():
    """Test max_improvement statistic."""
    print("\n" + "=" * 70)
    print("TEST: Max Improvement Stat")
    print("=" * 70)

    model_manager, llm, reflection, config = create_mock_dependencies()
    loop = IterativeImprovementLoop(model_manager, reflection, config)

    # Session with large improvement
    reflection_responses = [
        {"quality_score": 0.50, "issues": ["many issues"], "suggestions": ["many fixes"], "should_improve": True},
        {"quality_score": 0.95, "issues": [], "suggestions": [], "should_improve": False}
    ]
    reflection.reflect_on_response = Mock(side_effect=reflection_responses)

    llm_response = Mock()
    llm_response.content = "Much improved"
    llm.invoke = Mock(return_value=llm_response)

    loop.iterate_until_satisfied("Query", "Response", {})

    stats = loop.get_improvement_stats()

    # Use approximate comparison for floating point
    assert abs(stats["max_improvement"] - 0.45) < 0.01

    print("✓ Max improvement tracked")
    print(f"  Max improvement: +{stats['max_improvement']:.2f}")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print(" " * 20 + "ITERATIVE IMPROVEMENT TEST SUITE")
    print("=" * 80)

    tests = [
        ("Initialization", test_initialization),
        ("IterationRecord Creation", test_iteration_record_creation),
        ("Already Excellent - No Iteration", test_already_excellent_no_iteration),
        ("Single Iteration", test_single_iteration_improvement),
        ("Multi-Iteration", test_multi_iteration_improvement),
        ("Max Iterations Reached", test_max_iterations_reached),
        ("Quality Threshold Reached", test_quality_threshold_reached),
        ("Convergence Detection", test_convergence_detection),
        ("Detect Convergence Method", test_detect_convergence_method),
        ("Should Continue Logic", test_should_continue_iteration),
        ("Quality Decline Reverts", test_quality_decline_reverts),
        ("No Issues Stops", test_no_issues_stops_iteration),
        ("Generate Prompt", test_generate_improvement_prompt),
        ("Improvement Tracking", test_improvement_tracking),
        ("Stats - Empty", test_get_improvement_stats_empty),
        ("Stats - With Data", test_get_improvement_stats_with_data),
        ("Sessions Distribution", test_sessions_by_iterations_distribution),
        ("Clear History", test_clear_history),
        ("Custom Config", test_config_custom_values),
        ("String Representation", test_repr),
        ("Error Handling", test_error_handling_in_improvement),
        ("Max Improvement Stat", test_max_improvement_stat),
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
        print("\n✅ All Iterative Improvement tests passed!")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
