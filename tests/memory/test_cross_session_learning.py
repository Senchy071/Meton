#!/usr/bin/env python3
"""
Tests for Cross-Session Learning System.

Tests cover:
- Pattern and Insight dataclasses
- Pattern detection (query, tool, error, success)
- Insight generation
- Insight application
- Recommendations
- Pattern tracking
- Learning summary
- Persistence
- Edge cases
"""

import sys
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from memory.cross_session_learning import (
        CrossSessionLearning,
        Pattern,
        Insight
    )
    LEARNING_AVAILABLE = True
except ImportError as e:
    LEARNING_AVAILABLE = False
    print(f"Warning: Cross-session learning not available: {e}")


def create_test_learning():
    """Create test learning system with temp storage."""
    temp_dir = tempfile.mkdtemp()
    learning = CrossSessionLearning(storage_path=temp_dir, min_occurrences=3)
    return learning, temp_dir


def cleanup_test_learning(learning, temp_dir):
    """Clean up test learning system."""
    shutil.rmtree(temp_dir, ignore_errors=True)


# Dataclass Tests

def test_pattern_dataclass():
    """Test Pattern dataclass."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_pattern_dataclass (learning not available)")
        return

    pattern = Pattern(
        id="test-id",
        pattern_type="query",
        description="Test pattern",
        occurrences=10,
        confidence=0.8
    )

    assert pattern.id == "test-id"
    assert pattern.pattern_type == "query"
    assert pattern.occurrences == 10
    assert pattern.confidence == 0.8
    assert pattern.examples == []


def test_pattern_to_dict():
    """Test Pattern serialization."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_pattern_to_dict (learning not available)")
        return

    pattern = Pattern(
        id="test-id",
        pattern_type="query",
        description="Test pattern",
        occurrences=10,
        confidence=0.8,
        examples=["example1"]
    )

    data = pattern.to_dict()

    assert data["id"] == "test-id"
    assert data["occurrences"] == 10
    assert "examples" in data


def test_pattern_from_dict():
    """Test Pattern deserialization."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_pattern_from_dict (learning not available)")
        return

    data = {
        "id": "test-id",
        "pattern_type": "query",
        "description": "Test pattern",
        "occurrences": 10,
        "confidence": 0.8,
        "examples": [],
        "recommendation": "",
        "created_at": "2025-11-15T00:00:00",
        "last_seen": "2025-11-15T00:00:00"
    }

    pattern = Pattern.from_dict(data)

    assert pattern.id == "test-id"
    assert pattern.occurrences == 10


def test_insight_dataclass():
    """Test Insight dataclass."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_insight_dataclass (learning not available)")
        return

    insight = Insight(
        id="test-id",
        insight_type="improvement",
        title="Test Insight",
        description="Test description",
        impact="high",
        actionable=True
    )

    assert insight.id == "test-id"
    assert insight.insight_type == "improvement"
    assert insight.applied is False
    assert insight.actionable is True


def test_insight_to_dict():
    """Test Insight serialization."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_insight_to_dict (learning not available)")
        return

    insight = Insight(
        id="test-id",
        insight_type="improvement",
        title="Test Insight",
        description="Test description",
        impact="high",
        actionable=True
    )

    data = insight.to_dict()

    assert data["id"] == "test-id"
    assert data["impact"] == "high"


# Initialization Tests

def test_initialization():
    """Test CrossSessionLearning initialization."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_initialization (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    assert learning is not None
    assert learning.min_occurrences == 3
    assert len(learning.patterns) == 0
    assert len(learning.insights) == 0

    cleanup_test_learning(learning, temp_dir)


def test_initialization_with_components():
    """Test initialization with memory/feedback/analytics."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_initialization_with_components (learning not available)")
        return

    # Create with None components (should work)
    learning, temp_dir = create_test_learning()

    assert learning.long_term_memory is None
    assert learning.feedback_system is None
    assert learning.analytics is None

    cleanup_test_learning(learning, temp_dir)


# Pattern Detection Tests

def test_detect_query_patterns_no_memory():
    """Test query pattern detection without memory."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_detect_query_patterns_no_memory (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    patterns = learning.detect_query_patterns()

    # Should return empty list without memory
    assert patterns == []

    cleanup_test_learning(learning, temp_dir)


def test_detect_tool_patterns_no_analytics():
    """Test tool pattern detection without analytics."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_detect_tool_patterns_no_analytics (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    patterns = learning.detect_tool_patterns()

    # Should return empty list without analytics
    assert patterns == []

    cleanup_test_learning(learning, temp_dir)


def test_detect_error_patterns_no_feedback():
    """Test error pattern detection without feedback."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_detect_error_patterns_no_feedback (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    patterns = learning.detect_error_patterns()

    # Should return empty list without feedback
    assert patterns == []

    cleanup_test_learning(learning, temp_dir)


def test_detect_success_patterns_no_feedback():
    """Test success pattern detection without feedback."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_detect_success_patterns_no_feedback (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    patterns = learning.detect_success_patterns()

    # Should return empty list without feedback
    assert patterns == []

    cleanup_test_learning(learning, temp_dir)


# Insight Generation Tests

def test_generate_insights_from_patterns():
    """Test generating insights from patterns."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_generate_insights_from_patterns (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # Create test patterns
    patterns = [
        Pattern(
            id="pattern-1",
            pattern_type="query",
            description="User frequently asks about async",
            occurrences=10,
            confidence=0.9,
            recommendation="Provide async guidance proactively"
        ),
        Pattern(
            id="pattern-2",
            pattern_type="error",
            description="Recurring error: timeout",
            occurrences=5,
            confidence=0.7,
            recommendation="Investigate timeout"
        )
    ]

    insights = learning.generate_insights(patterns)

    assert len(insights) > 0
    assert all(isinstance(i, Insight) for i in insights)

    cleanup_test_learning(learning, temp_dir)


def test_pattern_to_insight_query():
    """Test converting query pattern to insight."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_pattern_to_insight_query (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    pattern = Pattern(
        id="test-id",
        pattern_type="query",
        description="User frequently asks about testing",
        occurrences=8,
        confidence=0.85,
        recommendation="Provide testing guidance"
    )

    insight = learning._pattern_to_insight(pattern)

    assert insight is not None
    assert insight.insight_type == "improvement"
    assert "testing" in insight.title.lower()

    cleanup_test_learning(learning, temp_dir)


def test_pattern_to_insight_error():
    """Test converting error pattern to insight."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_pattern_to_insight_error (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    pattern = Pattern(
        id="test-id",
        pattern_type="error",
        description="Recurring error: network timeout",
        occurrences=5,
        confidence=0.8,
        recommendation="Check network config"
    )

    insight = learning._pattern_to_insight(pattern)

    assert insight is not None
    assert insight.insight_type == "warning"
    assert insight.impact == "high"

    cleanup_test_learning(learning, temp_dir)


# Insight Application Tests

def test_apply_insight():
    """Test applying an insight."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_apply_insight (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # Create and add insight
    insight = Insight(
        id="test-id",
        insight_type="improvement",
        title="Test Insight",
        description="Test description",
        impact="high",
        actionable=True
    )
    learning.insights[insight.id] = insight

    # Apply it
    result = learning.apply_insight(insight.id)

    assert result is True
    assert learning.insights[insight.id].applied is True

    cleanup_test_learning(learning, temp_dir)


def test_apply_nonexistent_insight():
    """Test applying non-existent insight."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_apply_nonexistent_insight (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    result = learning.apply_insight("nonexistent-id")

    assert result is False

    cleanup_test_learning(learning, temp_dir)


def test_apply_already_applied_insight():
    """Test applying already-applied insight."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_apply_already_applied_insight (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # Create applied insight
    insight = Insight(
        id="test-id",
        insight_type="improvement",
        title="Test Insight",
        description="Test description",
        impact="high",
        actionable=True,
        applied=True
    )
    learning.insights[insight.id] = insight

    result = learning.apply_insight(insight.id)

    # Should return True (already applied)
    assert result is True

    cleanup_test_learning(learning, temp_dir)


# Recommendations Tests

def test_get_recommendations():
    """Test getting recommendations for query."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_get_recommendations (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # Add pattern
    pattern = Pattern(
        id="test-id",
        pattern_type="query",
        description="User frequently asks about async",
        occurrences=10,
        confidence=0.9,
        recommendation="Provide async examples proactively"
    )
    learning.patterns[pattern.id] = pattern

    # Get recommendations for async query
    recommendations = learning.get_recommendations("How do I use async await?", {})

    assert len(recommendations) > 0
    assert any("async" in rec.lower() for rec in recommendations)

    cleanup_test_learning(learning, temp_dir)


def test_get_recommendations_no_match():
    """Test recommendations with no matching patterns."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_get_recommendations_no_match (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    recommendations = learning.get_recommendations("unrelated query", {})

    assert recommendations == []

    cleanup_test_learning(learning, temp_dir)


# Pattern Tracking Tests

def test_track_pattern_occurrence():
    """Test tracking pattern occurrence."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_track_pattern_occurrence (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # Add pattern
    pattern = Pattern(
        id="test-id",
        pattern_type="query",
        description="Test pattern",
        occurrences=5,
        confidence=0.7
    )
    learning.patterns[pattern.id] = pattern

    initial_count = pattern.occurrences

    # Track occurrence
    learning.track_pattern_occurrence(pattern.id, "New example")

    # Should increment
    assert learning.patterns[pattern.id].occurrences == initial_count + 1
    assert "New example" in learning.patterns[pattern.id].examples

    cleanup_test_learning(learning, temp_dir)


def test_track_nonexistent_pattern():
    """Test tracking non-existent pattern."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_track_nonexistent_pattern (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # Should not crash
    learning.track_pattern_occurrence("nonexistent-id", "Example")

    cleanup_test_learning(learning, temp_dir)


# Learning Summary Tests

def test_get_learning_summary_empty():
    """Test learning summary with no data."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_get_learning_summary_empty (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    summary = learning.get_learning_summary()

    assert summary["total_patterns"] == 0
    assert summary["insights_generated"] == 0
    assert summary["insights_applied"] == 0
    assert summary["learning_velocity"] == 0.0

    cleanup_test_learning(learning, temp_dir)


def test_get_learning_summary_with_data():
    """Test learning summary with data."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_get_learning_summary_with_data (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # Add patterns
    pattern1 = Pattern(
        id="pattern-1",
        pattern_type="query",
        description="Pattern 1",
        occurrences=10,
        confidence=0.9
    )
    pattern2 = Pattern(
        id="pattern-2",
        pattern_type="query",
        description="Pattern 2",
        occurrences=5,
        confidence=0.7
    )
    learning.patterns[pattern1.id] = pattern1
    learning.patterns[pattern2.id] = pattern2

    # Add insights
    insight = Insight(
        id="insight-1",
        insight_type="improvement",
        title="Insight 1",
        description="Description",
        impact="high",
        actionable=True,
        applied=True
    )
    learning.insights[insight.id] = insight

    summary = learning.get_learning_summary()

    assert summary["total_patterns"] == 2
    assert summary["insights_generated"] == 1
    assert summary["insights_applied"] == 1
    assert len(summary["top_patterns"]) > 0
    assert len(summary["recent_insights"]) > 0

    cleanup_test_learning(learning, temp_dir)


# Persistence Tests

def test_save_and_load_patterns():
    """Test saving and loading patterns."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_save_and_load_patterns (learning not available)")
        return

    temp_dir = tempfile.mkdtemp()

    # Create and populate
    learning1 = CrossSessionLearning(storage_path=temp_dir)
    pattern = Pattern(
        id="test-id",
        pattern_type="query",
        description="Test pattern",
        occurrences=10,
        confidence=0.8
    )
    learning1.patterns[pattern.id] = pattern
    learning1._save_patterns()

    # Create new instance (should load)
    learning2 = CrossSessionLearning(storage_path=temp_dir)

    assert len(learning2.patterns) == 1
    assert "test-id" in learning2.patterns
    assert learning2.patterns["test-id"].occurrences == 10

    cleanup_test_learning(learning2, temp_dir)


def test_save_and_load_insights():
    """Test saving and loading insights."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_save_and_load_insights (learning not available)")
        return

    temp_dir = tempfile.mkdtemp()

    # Create and populate
    learning1 = CrossSessionLearning(storage_path=temp_dir)
    insight = Insight(
        id="test-id",
        insight_type="improvement",
        title="Test Insight",
        description="Description",
        impact="high",
        actionable=True
    )
    learning1.insights[insight.id] = insight
    learning1._save_insights()

    # Create new instance (should load)
    learning2 = CrossSessionLearning(storage_path=temp_dir)

    assert len(learning2.insights) == 1
    assert "test-id" in learning2.insights

    cleanup_test_learning(learning2, temp_dir)


# Analysis Tests

def test_analyze_sessions():
    """Test analyzing sessions."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_analyze_sessions (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # Analyze (should work even without data)
    insights = learning.analyze_sessions(lookback_days=30)

    # Should return list (possibly empty)
    assert isinstance(insights, list)

    cleanup_test_learning(learning, temp_dir)


# Helper Method Tests

def test_calculate_confidence():
    """Test confidence calculation."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_calculate_confidence (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # High frequency and consistency
    confidence1 = learning._calculate_confidence(10, 20, 0.9)
    assert 0.0 <= confidence1 <= 1.0
    assert confidence1 > 0.5  # Should be high

    # Low occurrences (penalty)
    confidence2 = learning._calculate_confidence(2, 20, 0.9)
    assert confidence2 < confidence1  # Lower than high occurrences

    cleanup_test_learning(learning, temp_dir)


def test_should_auto_apply():
    """Test auto-apply criteria."""
    if not LEARNING_AVAILABLE:
        print("⏭️  test_should_auto_apply (learning not available)")
        return

    learning, temp_dir = create_test_learning()

    # High impact, actionable improvement
    insight1 = Insight(
        id="id1",
        insight_type="improvement",
        title="Test",
        description="Desc",
        impact="high",
        actionable=True
    )
    assert learning._should_auto_apply(insight1) is True

    # Warning (should not auto-apply)
    insight2 = Insight(
        id="id2",
        insight_type="warning",
        title="Test",
        description="Desc",
        impact="high",
        actionable=True
    )
    assert learning._should_auto_apply(insight2) is False

    # Low impact
    insight3 = Insight(
        id="id3",
        insight_type="improvement",
        title="Test",
        description="Desc",
        impact="low",
        actionable=True
    )
    assert learning._should_auto_apply(insight3) is False

    cleanup_test_learning(learning, temp_dir)


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_pattern_dataclass,
        test_pattern_to_dict,
        test_pattern_from_dict,
        test_insight_dataclass,
        test_insight_to_dict,
        test_initialization,
        test_initialization_with_components,
        test_detect_query_patterns_no_memory,
        test_detect_tool_patterns_no_analytics,
        test_detect_error_patterns_no_feedback,
        test_detect_success_patterns_no_feedback,
        test_generate_insights_from_patterns,
        test_pattern_to_insight_query,
        test_pattern_to_insight_error,
        test_apply_insight,
        test_apply_nonexistent_insight,
        test_apply_already_applied_insight,
        test_get_recommendations,
        test_get_recommendations_no_match,
        test_track_pattern_occurrence,
        test_track_nonexistent_pattern,
        test_get_learning_summary_empty,
        test_get_learning_summary_with_data,
        test_save_and_load_patterns,
        test_save_and_load_insights,
        test_analyze_sessions,
        test_calculate_confidence,
        test_should_auto_apply,
    ]

    print(f"Running {len(tests)} tests...\n")

    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            if "not available" in str(e):
                skipped += 1
            else:
                print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
                failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped out of {len(tests)} tests")
    if passed > 0 and failed == 0:
        print(f"Success rate: 100%")
    elif passed > 0:
        print(f"Success rate: {passed/(passed+failed)*100:.1f}% (of non-skipped)")

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    if not LEARNING_AVAILABLE:
        print("⚠️  Cross-session learning not available.")
        print("Tests will be skipped.")
        exit(0)

    exit(run_all_tests())
