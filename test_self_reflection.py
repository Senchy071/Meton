#!/usr/bin/env python3
"""Test suite for Self-Reflection Module.

Tests the self-reflection capabilities including:
- Quality score calculation
- Issue identification
- Suggestion generation
- Response improvement
- Reflection triggering logic
- Statistics tracking
- JSON parsing
- Integration patterns
"""

import sys
from pathlib import Path
from unittest.mock import Mock, MagicMock

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

from agent.self_reflection import SelfReflectionModule, ReflectionRecord


def create_mock_dependencies():
    """Create mock dependencies for testing."""
    # Mock ModelManager
    mock_model_manager = Mock()
    mock_llm = Mock()
    mock_model_manager.get_model = Mock(return_value=mock_llm)

    # Mock config
    mock_config = {
        "enabled": True,
        "min_quality_threshold": 0.7,
        "max_iterations": 2,
        "auto_reflect_on": {
            "complex_queries": True,
            "multi_tool_usage": True,
            "long_responses": True
        }
    }

    return mock_model_manager, mock_llm, mock_config


def test_initialization():
    """Test SelfReflectionModule initialization."""
    print("\n" + "=" * 70)
    print("TEST: SelfReflectionModule Initialization")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()

    reflection = SelfReflectionModule(model_manager, config)

    assert reflection is not None
    assert reflection.min_quality_threshold == 0.7
    assert reflection.max_iterations == 2
    assert len(reflection.reflection_history) == 0

    print("✓ SelfReflectionModule initialized successfully")
    print(f"  Quality threshold: {reflection.min_quality_threshold}")
    print(f"  Max iterations: {reflection.max_iterations}")


def test_reflection_record_creation():
    """Test ReflectionRecord dataclass creation."""
    print("\n" + "=" * 70)
    print("TEST: ReflectionRecord Creation")
    print("=" * 70)

    record = ReflectionRecord(
        query="Test query",
        response="Test response",
        quality_score=0.85,
        issues=["issue1"],
        suggestions=["suggestion1"],
        improved=False
    )

    assert record.query == "Test query"
    assert record.quality_score == 0.85
    assert len(record.issues) == 1
    assert record.improved is False
    assert record.timestamp is not None

    print("✓ ReflectionRecord created successfully")
    print(f"  Quality score: {record.quality_score}")
    print(f"  Issues: {record.issues}")


def test_should_reflect_complex_query():
    """Test should_reflect with complex query."""
    print("\n" + "=" * 70)
    print("TEST: Should Reflect - Complex Query")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    query = "Find the file and then analyze it and review the code and suggest improvements"
    response = "Short response"

    should_reflect = reflection.should_reflect(query, response)

    assert should_reflect is True

    print("✓ Complex query detected for reflection")
    print(f"  Query: {query[:50]}...")


def test_should_reflect_analysis_query():
    """Test should_reflect with analysis keywords."""
    print("\n" + "=" * 70)
    print("TEST: Should Reflect - Analysis Query")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    queries = [
        "Analyze the authentication system",
        "Review the code quality",
        "Compare FastAPI and Flask",
        "Evaluate the performance"
    ]

    for query in queries:
        should_reflect = reflection.should_reflect(query, "Response")
        assert should_reflect is True

    print("✓ Analysis queries detected")
    print(f"  Tested {len(queries)} query types")


def test_should_reflect_long_response():
    """Test should_reflect with long response."""
    print("\n" + "=" * 70)
    print("TEST: Should Reflect - Long Response")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    query = "Simple query"
    # Create response with >500 words
    response = " ".join(["word"] * 600)

    should_reflect = reflection.should_reflect(query, response)

    assert should_reflect is True

    print("✓ Long response detected")
    print(f"  Response length: {len(response.split())} words")


def test_should_reflect_multi_tool_usage():
    """Test should_reflect with multiple tool usage."""
    print("\n" + "=" * 70)
    print("TEST: Should Reflect - Multi-Tool Usage")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    query = "Simple query"
    response = "Short response"
    context = {
        "tool_calls": [
            {"tool": "file_ops"},
            {"tool": "code_executor"},
            {"tool": "web_search"}
        ]
    }

    should_reflect = reflection.should_reflect(query, response, context)

    assert should_reflect is True

    print("✓ Multi-tool usage detected")
    print(f"  Tools used: {len(context['tool_calls'])}")


def test_should_not_reflect_simple_query():
    """Test should_reflect returns False for simple cases."""
    print("\n" + "=" * 70)
    print("TEST: Should Not Reflect - Simple Query")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    query = "Read the file"
    response = "File contents here"
    context = {"tool_calls": [{"tool": "file_ops"}]}

    should_reflect = reflection.should_reflect(query, response, context)

    assert should_reflect is False

    print("✓ Simple query correctly identified")


def test_reflect_on_response_good_quality():
    """Test reflection on good quality response."""
    print("\n" + "=" * 70)
    print("TEST: Reflect on Good Quality Response")
    print("=" * 70)

    model_manager, mock_llm, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Mock LLM response with high quality score
    mock_response = Mock()
    mock_response.content = """
    {
        "quality_score": 0.9,
        "issues": [],
        "suggestions": []
    }
    """
    mock_llm.invoke = Mock(return_value=mock_response)

    query = "Test query"
    response = "High quality response"
    context = {}

    result = reflection.reflect_on_response(query, response, context)

    assert result["quality_score"] == 0.9
    assert len(result["issues"]) == 0
    assert result["should_improve"] is False

    print("✓ Good quality response reflected")
    print(f"  Quality score: {result['quality_score']}")
    print(f"  Should improve: {result['should_improve']}")


def test_reflect_on_response_poor_quality():
    """Test reflection on poor quality response."""
    print("\n" + "=" * 70)
    print("TEST: Reflect on Poor Quality Response")
    print("=" * 70)

    model_manager, mock_llm, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Mock LLM response with low quality score
    mock_response = Mock()
    mock_response.content = """
    {
        "quality_score": 0.5,
        "issues": ["incomplete_answer", "unclear_explanation"],
        "suggestions": ["Address all parts", "Improve structure"]
    }
    """
    mock_llm.invoke = Mock(return_value=mock_response)

    query = "Test query"
    response = "Poor quality response"
    context = {}

    result = reflection.reflect_on_response(query, response, context)

    assert result["quality_score"] == 0.5
    assert len(result["issues"]) == 2
    assert result["should_improve"] is True

    print("✓ Poor quality response reflected")
    print(f"  Quality score: {result['quality_score']}")
    print(f"  Issues: {result['issues']}")
    print(f"  Should improve: {result['should_improve']}")


def test_reflect_with_critical_issues():
    """Test reflection with critical issues triggers improvement."""
    print("\n" + "=" * 70)
    print("TEST: Reflect with Critical Issues")
    print("=" * 70)

    model_manager, mock_llm, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Mock LLM response with critical issue
    mock_response = Mock()
    mock_response.content = """
    {
        "quality_score": 0.75,
        "issues": ["incorrect_info"],
        "suggestions": ["Verify facts"]
    }
    """
    mock_llm.invoke = Mock(return_value=mock_response)

    query = "Test query"
    response = "Response with incorrect info"
    context = {}

    result = reflection.reflect_on_response(query, response, context)

    # Even though score is above threshold, critical issue triggers improvement
    assert result["should_improve"] is True
    assert "incorrect_info" in result["issues"]

    print("✓ Critical issues detected")
    print(f"  Quality score: {result['quality_score']}")
    print(f"  Critical issue: incorrect_info")


def test_improve_response():
    """Test response improvement."""
    print("\n" + "=" * 70)
    print("TEST: Improve Response")
    print("=" * 70)

    model_manager, mock_llm, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Mock LLM improvement response
    mock_response = Mock()
    mock_response.content = "This is the improved response with all issues addressed."
    mock_llm.invoke = Mock(return_value=mock_response)

    query = "Test query"
    original_response = "Original poor response"
    reflection_result = {
        "quality_score": 0.5,
        "issues": ["incomplete_answer"],
        "suggestions": ["Add more detail"]
    }

    # Add a reflection to history first
    reflection.reflection_history.append(ReflectionRecord(
        query=query,
        response=original_response,
        quality_score=0.5,
        issues=["incomplete_answer"],
        suggestions=["Add more detail"],
        improved=False
    ))

    improved = reflection.improve_response(query, original_response, reflection_result)

    assert improved == "This is the improved response with all issues addressed."
    assert reflection.reflection_history[-1].improved is True

    print("✓ Response improved")
    print(f"  Improved response length: {len(improved)} chars")


def test_parse_reflection_output_pure_json():
    """Test parsing pure JSON output."""
    print("\n" + "=" * 70)
    print("TEST: Parse Pure JSON Output")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    json_output = '{"quality_score": 0.85, "issues": ["test"], "suggestions": ["improve"]}'

    result = reflection._parse_reflection_output(json_output)

    assert result["quality_score"] == 0.85
    assert result["issues"] == ["test"]
    assert result["suggestions"] == ["improve"]

    print("✓ Pure JSON parsed successfully")


def test_parse_reflection_output_with_markdown():
    """Test parsing JSON in markdown code blocks."""
    print("\n" + "=" * 70)
    print("TEST: Parse JSON in Markdown")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    markdown_output = """
    Here's the analysis:
    ```json
    {"quality_score": 0.7, "issues": [], "suggestions": []}
    ```
    """

    result = reflection._parse_reflection_output(markdown_output)

    assert result["quality_score"] == 0.7

    print("✓ Markdown JSON parsed successfully")


def test_parse_reflection_output_with_extra_text():
    """Test parsing JSON with extra text around it."""
    print("\n" + "=" * 70)
    print("TEST: Parse JSON with Extra Text")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    mixed_output = """
    After analyzing the response, here's my evaluation:
    {"quality_score": 0.6, "issues": ["verbose"], "suggestions": ["be concise"]}
    I hope this helps!
    """

    result = reflection._parse_reflection_output(mixed_output)

    assert result["quality_score"] == 0.6
    assert "verbose" in result["issues"]

    print("✓ JSON with extra text parsed successfully")


def test_parse_reflection_output_invalid():
    """Test parsing invalid JSON falls back gracefully."""
    print("\n" + "=" * 70)
    print("TEST: Parse Invalid JSON - Fallback")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    invalid_output = "This is not JSON at all"

    result = reflection._parse_reflection_output(invalid_output)

    # Should fallback to defaults
    assert result["quality_score"] == 0.5
    assert "parsing_error" in result["issues"]

    print("✓ Invalid JSON handled with fallback")
    print(f"  Fallback score: {result['quality_score']}")


def test_quality_score_validation():
    """Test quality score is clamped to 0.0-1.0 range."""
    print("\n" + "=" * 70)
    print("TEST: Quality Score Validation")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Test score > 1.0
    output1 = '{"quality_score": 1.5, "issues": [], "suggestions": []}'
    result1 = reflection._parse_reflection_output(output1)
    assert result1["quality_score"] == 1.0

    # Test score < 0.0
    output2 = '{"quality_score": -0.5, "issues": [], "suggestions": []}'
    result2 = reflection._parse_reflection_output(output2)
    assert result2["quality_score"] == 0.0

    print("✓ Quality scores validated")
    print(f"  1.5 clamped to: {result1['quality_score']}")
    print(f"  -0.5 clamped to: {result2['quality_score']}")


def test_format_context():
    """Test context formatting."""
    print("\n" + "=" * 70)
    print("TEST: Format Context")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    context = {
        "tool_calls": [
            {"tool": "file_ops"},
            {"tool": "code_executor"}
        ],
        "iteration": 3
    }

    formatted = reflection._format_context(context)

    assert "Tools used: 2" in formatted
    assert "file_ops" in formatted

    print("✓ Context formatted")
    print(f"  Formatted output:\n{formatted}")


def test_format_context_empty():
    """Test formatting empty context."""
    print("\n" + "=" * 70)
    print("TEST: Format Empty Context")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    formatted = reflection._format_context({})

    assert "No additional context" in formatted

    print("✓ Empty context handled")


def test_get_reflection_stats_empty():
    """Test getting stats with no reflections."""
    print("\n" + "=" * 70)
    print("TEST: Get Reflection Stats - Empty")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    stats = reflection.get_reflection_stats()

    assert stats["total_reflections"] == 0
    assert stats["average_quality_score"] == 0.0
    assert stats["improvement_rate"] == 0.0

    print("✓ Empty stats returned correctly")


def test_get_reflection_stats_with_data():
    """Test getting stats with reflection history."""
    print("\n" + "=" * 70)
    print("TEST: Get Reflection Stats - With Data")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Add some reflections
    reflection.reflection_history.append(ReflectionRecord(
        query="Q1", response="R1", quality_score=0.9,
        issues=[], suggestions=[], improved=False
    ))
    reflection.reflection_history.append(ReflectionRecord(
        query="Q2", response="R2", quality_score=0.6,
        issues=["incomplete_answer"], suggestions=["add more"], improved=True
    ))
    reflection.reflection_history.append(ReflectionRecord(
        query="Q3", response="R3", quality_score=0.7,
        issues=["unclear_explanation"], suggestions=["clarify"], improved=True
    ))

    stats = reflection.get_reflection_stats()

    assert stats["total_reflections"] == 3
    assert abs(stats["average_quality_score"] - 0.733) < 0.01
    assert abs(stats["improvement_rate"] - 66.67) < 0.1
    assert "incomplete_answer" in stats["common_issues"]

    print("✓ Stats calculated correctly")
    print(f"  Total: {stats['total_reflections']}")
    print(f"  Avg score: {stats['average_quality_score']:.2f}")
    print(f"  Improvement rate: {stats['improvement_rate']:.1f}%")


def test_score_distribution():
    """Test score distribution in stats."""
    print("\n" + "=" * 70)
    print("TEST: Score Distribution")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Add reflections with different scores
    reflection.reflection_history.append(ReflectionRecord(
        query="Q1", response="R1", quality_score=0.95,  # Excellent
        issues=[], suggestions=[]
    ))
    reflection.reflection_history.append(ReflectionRecord(
        query="Q2", response="R2", quality_score=0.75,  # Good
        issues=[], suggestions=[]
    ))
    reflection.reflection_history.append(ReflectionRecord(
        query="Q3", response="R3", quality_score=0.55,  # Needs improvement
        issues=[], suggestions=[]
    ))
    reflection.reflection_history.append(ReflectionRecord(
        query="Q4", response="R4", quality_score=0.3,  # Poor
        issues=[], suggestions=[]
    ))

    stats = reflection.get_reflection_stats()
    dist = stats["score_distribution"]

    assert dist["excellent (0.9-1.0)"] == 1
    assert dist["good (0.7-0.9)"] == 1
    assert dist["needs_improvement (0.5-0.7)"] == 1
    assert dist["poor (0.0-0.5)"] == 1

    print("✓ Score distribution calculated")
    for range_name, count in dist.items():
        print(f"  {range_name}: {count}")


def test_common_issues_ranking():
    """Test common issues are ranked by frequency."""
    print("\n" + "=" * 70)
    print("TEST: Common Issues Ranking")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Add reflections with various issues
    reflection.reflection_history.append(ReflectionRecord(
        query="Q1", response="R1", quality_score=0.6,
        issues=["unclear_explanation"], suggestions=[]
    ))
    reflection.reflection_history.append(ReflectionRecord(
        query="Q2", response="R2", quality_score=0.5,
        issues=["unclear_explanation", "too_verbose"], suggestions=[]
    ))
    reflection.reflection_history.append(ReflectionRecord(
        query="Q3", response="R3", quality_score=0.65,
        issues=["unclear_explanation"], suggestions=[]
    ))

    stats = reflection.get_reflection_stats()
    common_issues = stats["common_issues"]

    # unclear_explanation should be most common (3 occurrences)
    issues_list = list(common_issues.items())
    assert issues_list[0][0] == "unclear_explanation"
    assert issues_list[0][1] == 3

    print("✓ Issues ranked by frequency")
    for issue, count in common_issues.items():
        print(f"  {issue}: {count}")


def test_clear_history():
    """Test clearing reflection history."""
    print("\n" + "=" * 70)
    print("TEST: Clear History")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Add some reflections
    reflection.reflection_history.append(ReflectionRecord(
        query="Q1", response="R1", quality_score=0.8,
        issues=[], suggestions=[]
    ))

    assert len(reflection.reflection_history) == 1

    reflection.clear_history()

    assert len(reflection.reflection_history) == 0

    print("✓ History cleared")


def test_config_custom_threshold():
    """Test custom quality threshold from config."""
    print("\n" + "=" * 70)
    print("TEST: Custom Quality Threshold")
    print("=" * 70)

    model_manager, _, _ = create_mock_dependencies()

    custom_config = {
        "enabled": True,
        "min_quality_threshold": 0.8,  # Higher threshold
        "max_iterations": 3
    }

    reflection = SelfReflectionModule(model_manager, custom_config)

    assert reflection.min_quality_threshold == 0.8
    assert reflection.max_iterations == 3

    print("✓ Custom config applied")
    print(f"  Threshold: {reflection.min_quality_threshold}")
    print(f"  Max iterations: {reflection.max_iterations}")


def test_repr():
    """Test string representation."""
    print("\n" + "=" * 70)
    print("TEST: String Representation")
    print("=" * 70)

    model_manager, _, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    repr_str = repr(reflection)

    assert "SelfReflectionModule" in repr_str
    assert "reflections=0" in repr_str
    assert "threshold=0.7" in repr_str

    print(f"✓ String representation: {repr_str}")


def test_reflection_error_handling():
    """Test error handling during reflection."""
    print("\n" + "=" * 70)
    print("TEST: Reflection Error Handling")
    print("=" * 70)

    model_manager, mock_llm, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Mock LLM to raise exception
    mock_llm.invoke = Mock(side_effect=Exception("LLM failed"))

    query = "Test query"
    response = "Test response"
    context = {}

    result = reflection.reflect_on_response(query, response, context)

    # Should fallback to defaults
    assert result["quality_score"] == 0.75
    assert result["should_improve"] is False

    print("✓ Reflection error handled gracefully")
    print(f"  Fallback score: {result['quality_score']}")


def test_improvement_error_handling():
    """Test error handling during improvement."""
    print("\n" + "=" * 70)
    print("TEST: Improvement Error Handling")
    print("=" * 70)

    model_manager, mock_llm, config = create_mock_dependencies()
    reflection = SelfReflectionModule(model_manager, config)

    # Mock LLM to raise exception
    mock_llm.invoke = Mock(side_effect=Exception("LLM failed"))

    query = "Test query"
    original = "Original response"
    reflection_result = {
        "quality_score": 0.5,
        "issues": ["test"],
        "suggestions": ["improve"]
    }

    improved = reflection.improve_response(query, original, reflection_result)

    # Should fallback to original
    assert improved == original

    print("✓ Improvement error handled gracefully")
    print("  Returned original response")


def run_all_tests():
    """Run all tests and report results."""
    print("\n" + "=" * 80)
    print(" " * 22 + "SELF-REFLECTION TEST SUITE")
    print("=" * 80)

    tests = [
        ("Initialization", test_initialization),
        ("ReflectionRecord Creation", test_reflection_record_creation),
        ("Should Reflect - Complex", test_should_reflect_complex_query),
        ("Should Reflect - Analysis", test_should_reflect_analysis_query),
        ("Should Reflect - Long", test_should_reflect_long_response),
        ("Should Reflect - Multi-Tool", test_should_reflect_multi_tool_usage),
        ("Should Not Reflect - Simple", test_should_not_reflect_simple_query),
        ("Reflect - Good Quality", test_reflect_on_response_good_quality),
        ("Reflect - Poor Quality", test_reflect_on_response_poor_quality),
        ("Reflect - Critical Issues", test_reflect_with_critical_issues),
        ("Improve Response", test_improve_response),
        ("Parse Pure JSON", test_parse_reflection_output_pure_json),
        ("Parse Markdown JSON", test_parse_reflection_output_with_markdown),
        ("Parse JSON Extra Text", test_parse_reflection_output_with_extra_text),
        ("Parse Invalid JSON", test_parse_reflection_output_invalid),
        ("Quality Score Validation", test_quality_score_validation),
        ("Format Context", test_format_context),
        ("Format Empty Context", test_format_context_empty),
        ("Stats - Empty", test_get_reflection_stats_empty),
        ("Stats - With Data", test_get_reflection_stats_with_data),
        ("Score Distribution", test_score_distribution),
        ("Common Issues Ranking", test_common_issues_ranking),
        ("Clear History", test_clear_history),
        ("Custom Threshold", test_config_custom_threshold),
        ("String Representation", test_repr),
        ("Reflection Error Handling", test_reflection_error_handling),
        ("Improvement Error Handling", test_improvement_error_handling),
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
        print("\n✅ All Self-Reflection tests passed!")

    return failed == 0


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
