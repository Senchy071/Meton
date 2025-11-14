#!/usr/bin/env python3
"""
Tests for Chain-of-Thought Reasoning.

Tests cover:
- Query decomposition (simple, complex, multi-part)
- Requirement analysis (tool selection)
- Reasoning chain generation
- Reasoning quality evaluation
- Complexity detection
- Statistics tracking
- Should use CoT logic
- Reasoning output parsing
- Edge cases
"""

import sys
from pathlib import Path
from unittest.mock import Mock

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.chain_of_thought import ChainOfThoughtReasoning, ReasoningRecord


def create_mock_model_manager():
    """Create mock model manager for testing."""
    manager = Mock()

    # Mock LLM that returns structured reasoning
    mock_llm = Mock()
    mock_response = Mock()
    mock_response.content = """
REASONING: This query requires finding authentication code and analyzing it for security issues.
STEPS:
- Search codebase for authentication implementation
- Review code for common security vulnerabilities
- Research best practices for fixes
TOOLS: codebase_search, code_reviewer, web_search
CONFIDENCE: 0.85
"""
    mock_llm.invoke = Mock(return_value=mock_response)
    manager.get_model = Mock(return_value=mock_llm)

    return manager


def test_detect_complexity_simple():
    """Test complexity detection for simple queries."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    assert cot.detect_complexity("What is Python?") == "simple"
    assert cot.detect_complexity("Show me file.py") == "simple"
    assert cot.detect_complexity("Display the config") == "simple"


def test_detect_complexity_medium():
    """Test complexity detection for medium queries."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    assert cot.detect_complexity("Explain how async works") == "medium"
    assert cot.detect_complexity("Why does this error occur?") == "medium"
    assert cot.detect_complexity("Find the authentication code") == "medium"


def test_detect_complexity_high():
    """Test complexity detection for high queries."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    assert cot.detect_complexity("Compare FastAPI and Flask") == "high"
    assert cot.detect_complexity("Analyze the codebase for bugs") == "high"
    assert cot.detect_complexity("Find and fix authentication issues") == "high"
    assert cot.detect_complexity("Suggest improvements to the code") == "high"


def test_decompose_simple_query():
    """Test decomposition of simple query."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    parts = cot.decompose_query("What is Python?")

    assert len(parts) == 1
    assert parts[0] == "What is Python?"


def test_decompose_and_query():
    """Test decomposition of 'and' query."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    parts = cot.decompose_query("Find bugs and suggest fixes")

    assert len(parts) == 2
    assert "bugs" in parts[0].lower()
    assert "fixes" in parts[1].lower()


def test_decompose_comparison_query():
    """Test decomposition of comparison query."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    parts = cot.decompose_query("Compare FastAPI and Flask")

    assert len(parts) == 3
    assert "FastAPI" in parts[0]
    assert "Flask" in parts[1]
    assert "differ" in parts[2]


def test_analyze_requirements_code_search():
    """Test requirement analysis for code search."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    reqs = cot.analyze_requirements("Find the authentication implementation")

    assert "source code" in reqs["information_needed"]
    assert "codebase_search" in reqs["tools_required"]
    assert reqs["complexity"] in ["simple", "medium", "high"]


def test_analyze_requirements_debug():
    """Test requirement analysis for debugging."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    reqs = cot.analyze_requirements("Debug the authentication error")

    assert "error information" in reqs["information_needed"]
    assert "debugger" in reqs["tools_required"]


def test_analyze_requirements_research():
    """Test requirement analysis for research."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    reqs = cot.analyze_requirements("Research best practices for async programming")

    assert "external information" in reqs["information_needed"]
    assert "web_search" in reqs["tools_required"]


def test_analyze_requirements_review():
    """Test requirement analysis for code review."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    reqs = cot.analyze_requirements("Review this code for security issues")

    assert "code quality metrics" in reqs["information_needed"]
    assert "code_reviewer" in reqs["tools_required"]


def test_generate_reasoning_chain():
    """Test reasoning chain generation."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    chain = cot.generate_reasoning_chain("Find and fix authentication bugs")

    assert len(chain) > 0
    assert chain[0]["step"] == 1
    assert "thought" in chain[0]
    assert "action" in chain[0]
    assert "justification" in chain[0]


def test_generate_reasoning_chain_max_steps():
    """Test reasoning chain respects max steps."""
    config = {"chain_of_thought": {"max_reasoning_steps": 5}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    chain = cot.generate_reasoning_chain("Very complex multi-step query with many parts")

    assert len(chain) <= 5


def test_evaluate_reasoning_quality_high():
    """Test quality evaluation for high-quality reasoning."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    reasoning = {
        "reasoning": "This is a detailed step-by-step reasoning process that explains the approach clearly.",
        "steps": ["Step 1", "Step 2", "Step 3"],
        "recommended_tools": ["codebase_search", "code_reviewer"],
        "confidence": 0.8
    }

    quality = cot.evaluate_reasoning_quality(reasoning)

    assert quality > 0.7  # High quality


def test_evaluate_reasoning_quality_low():
    """Test quality evaluation for low-quality reasoning."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    reasoning = {
        "reasoning": "Short",
        "steps": [],
        "recommended_tools": [],
        "confidence": 0.1
    }

    quality = cot.evaluate_reasoning_quality(reasoning)

    assert quality < 0.5  # Low quality


def test_should_use_cot_simple_threshold():
    """Test should_use_cot with simple threshold."""
    config = {"chain_of_thought": {"min_complexity_threshold": "simple"}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    # Simple queries should not use CoT with simple threshold
    assert cot.should_use_cot("What is Python?") == False

    # High queries should use CoT
    assert cot.should_use_cot("Compare X and Y") == True


def test_should_use_cot_medium_threshold():
    """Test should_use_cot with medium threshold."""
    config = {"chain_of_thought": {"min_complexity_threshold": "medium"}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    # Simple queries should not use CoT
    assert cot.should_use_cot("Show me file.py") == False

    # Medium and high should use CoT
    assert cot.should_use_cot("Explain async") == True
    assert cot.should_use_cot("Analyze bugs") == True


def test_should_use_cot_all_threshold():
    """Test should_use_cot with 'all' threshold."""
    config = {"chain_of_thought": {"min_complexity_threshold": "all"}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    # All queries should use CoT
    assert cot.should_use_cot("What is Python?") == True
    assert cot.should_use_cot("Explain async") == True
    assert cot.should_use_cot("Compare X and Y") == True


def test_parse_reasoning_output():
    """Test parsing of reasoning output."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    output = """
REASONING: This requires searching the codebase and reviewing code.
STEPS:
- Search for authentication code
- Review for vulnerabilities
- Generate recommendations
TOOLS: codebase_search, code_reviewer
CONFIDENCE: 0.85
"""

    parsed = cot._parse_reasoning_output(output)

    assert "codebase" in parsed["reasoning"].lower()
    assert len(parsed["steps"]) == 3
    assert "codebase_search" in parsed["tools"]
    assert "code_reviewer" in parsed["tools"]
    assert parsed["confidence"] == 0.85


def test_parse_reasoning_output_incomplete():
    """Test parsing of incomplete reasoning output."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    output = "REASONING: Just some text without proper structure"

    parsed = cot._parse_reasoning_output(output)

    # Should have defaults for missing sections
    assert "reasoning" in parsed
    assert isinstance(parsed["steps"], list)
    assert isinstance(parsed["tools"], list)
    assert isinstance(parsed["confidence"], float)


def test_reason_about_query():
    """Test full reasoning about a query."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    reasoning = cot.reason_about_query("Find authentication bugs and suggest fixes")

    assert "reasoning" in reasoning
    assert "steps" in reasoning
    assert "recommended_tools" in reasoning
    assert "confidence" in reasoning
    assert "complexity" in reasoning
    assert 0.0 <= reasoning["confidence"] <= 1.0


def test_reason_about_query_stores_history():
    """Test that reasoning is stored in history."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    assert len(cot.reasoning_history) == 0

    cot.reason_about_query("Test query")

    assert len(cot.reasoning_history) == 1
    assert cot.reasoning_history[0].query == "Test query"


def test_get_reasoning_stats_empty():
    """Test statistics with no reasoning history."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    stats = cot.get_reasoning_stats()

    assert stats["total_reasonings"] == 0
    assert stats["avg_steps_per_reasoning"] == 0.0
    assert stats["avg_confidence"] == 0.0
    assert stats["complexity_distribution"] == {}
    assert stats["tool_recommendations"] == {}


def test_get_reasoning_stats():
    """Test statistics after multiple reasonings."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    # Perform multiple reasonings
    cot.reason_about_query("Simple query")
    cot.reason_about_query("Compare X and Y")
    cot.reason_about_query("Analyze bugs")

    stats = cot.get_reasoning_stats()

    assert stats["total_reasonings"] == 3
    assert stats["avg_steps_per_reasoning"] > 0
    assert 0.0 <= stats["avg_confidence"] <= 1.0
    assert len(stats["complexity_distribution"]) > 0
    assert len(stats["tool_recommendations"]) > 0


def test_fallback_reasoning():
    """Test fallback reasoning when LLM fails."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    fallback = cot._fallback_reasoning("Find authentication code", "medium")

    assert "reasoning" in fallback
    assert "steps" in fallback
    assert "recommended_tools" in fallback
    assert "confidence" in fallback
    assert fallback["complexity"] == "medium"


def test_format_context_empty():
    """Test context formatting with empty context."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    formatted = cot._format_context({})

    assert "No additional context" in formatted


def test_format_context_with_data():
    """Test context formatting with data."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    context = {
        "tools_used": ["web_search", "codebase_search"],
        "reflection_score": 0.75
    }

    formatted = cot._format_context(context)

    assert "web_search" in formatted
    assert "0.75" in formatted


def test_reset_history():
    """Test resetting reasoning history."""
    config = {"chain_of_thought": {}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    # Add some history
    cot.reason_about_query("Test query 1")
    cot.reason_about_query("Test query 2")

    assert len(cot.reasoning_history) == 2

    # Reset
    cot.reset_history()

    assert len(cot.reasoning_history) == 0


def test_reasoning_record_dataclass():
    """Test ReasoningRecord dataclass."""
    record = ReasoningRecord(
        query="Test query",
        reasoning="Test reasoning",
        steps=["Step 1", "Step 2"],
        recommended_tools=["tool1", "tool2"],
        confidence=0.8,
        complexity="high"
    )

    assert record.query == "Test query"
    assert record.confidence == 0.8
    assert len(record.steps) == 2
    assert len(record.recommended_tools) == 2


def test_config_include_in_response():
    """Test include_in_response configuration."""
    config = {"chain_of_thought": {"include_in_response": True}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    assert cot.include_in_response == True


def test_config_max_reasoning_steps():
    """Test max_reasoning_steps configuration."""
    config = {"chain_of_thought": {"max_reasoning_steps": 7}}
    cot = ChainOfThoughtReasoning(create_mock_model_manager(), config)

    assert cot.max_steps == 7


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_detect_complexity_simple,
        test_detect_complexity_medium,
        test_detect_complexity_high,
        test_decompose_simple_query,
        test_decompose_and_query,
        test_decompose_comparison_query,
        test_analyze_requirements_code_search,
        test_analyze_requirements_debug,
        test_analyze_requirements_research,
        test_analyze_requirements_review,
        test_generate_reasoning_chain,
        test_generate_reasoning_chain_max_steps,
        test_evaluate_reasoning_quality_high,
        test_evaluate_reasoning_quality_low,
        test_should_use_cot_simple_threshold,
        test_should_use_cot_medium_threshold,
        test_should_use_cot_all_threshold,
        test_parse_reasoning_output,
        test_parse_reasoning_output_incomplete,
        test_reason_about_query,
        test_reason_about_query_stores_history,
        test_get_reasoning_stats_empty,
        test_get_reasoning_stats,
        test_fallback_reasoning,
        test_format_context_empty,
        test_format_context_with_data,
        test_reset_history,
        test_reasoning_record_dataclass,
        test_config_include_in_response,
        test_config_max_reasoning_steps,
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
