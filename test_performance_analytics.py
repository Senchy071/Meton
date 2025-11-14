#!/usr/bin/env python3
"""
Tests for Performance Analytics System.

Tests cover:
- Metric recording (single, multiple)
- Persistence (save, load, atomic writes)
- Dashboard generation (overview, query types, tools, reflection, trends)
- Tool performance analysis
- Time-based analysis (hour, day, week, month)
- Bottleneck detection (slow tools, failures, long queries, iterations)
- Export functionality (JSON, CSV, date filtering)
- Query comparison
- Edge cases (no metrics, single metric, all success, all failure)
- Statistics calculations
- Metric pruning
"""

import sys
import json
import tempfile
import shutil
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from agent.performance_analytics import PerformanceAnalytics, MetricRecord


def create_test_analytics():
    """Create analytics instance with temporary storage."""
    temp_dir = tempfile.mkdtemp()
    config = {
        "retention_days": 90,
        "auto_export_interval": 100
    }
    return PerformanceAnalytics(storage_path=temp_dir, config=config), temp_dir


def cleanup_test_analytics(temp_dir):
    """Clean up temporary storage."""
    shutil.rmtree(temp_dir, ignore_errors=True)


def test_record_single_metric():
    """Test recording single metric."""
    analytics, temp_dir = create_test_analytics()

    metric_id = analytics.record_query(
        query="Test query",
        query_type="simple",
        response_time=1.5,
        tool_calls=["tool1"],
        tool_times={"tool1": 1.0}
    )

    assert metric_id is not None
    assert len(analytics.metrics) == 1
    assert analytics.metrics[0].query == "Test query"

    cleanup_test_analytics(temp_dir)


def test_record_multiple_metrics():
    """Test recording multiple metrics."""
    analytics, temp_dir = create_test_analytics()

    for i in range(5):
        analytics.record_query(
            query=f"Query {i}",
            query_type="medium",
            response_time=2.0,
            tool_calls=["tool1", "tool2"],
            tool_times={"tool1": 1.0, "tool2": 0.5}
        )

    assert len(analytics.metrics) == 5

    cleanup_test_analytics(temp_dir)


def test_metric_persistence():
    """Test metrics are saved and loaded correctly."""
    temp_dir = tempfile.mkdtemp()

    # Create and record metrics
    analytics1 = PerformanceAnalytics(storage_path=temp_dir)
    analytics1.record_query(
        query="Persistent query",
        query_type="complex",
        response_time=5.0,
        tool_calls=["tool1"],
        tool_times={"tool1": 3.0}
    )

    # Create new instance (should load metrics)
    analytics2 = PerformanceAnalytics(storage_path=temp_dir)

    assert len(analytics2.metrics) == 1
    assert analytics2.metrics[0].query == "Persistent query"

    cleanup_test_analytics(temp_dir)


def test_dashboard_overview():
    """Test dashboard overview section."""
    analytics, temp_dir = create_test_analytics()

    # Record test metrics
    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5}, success=True)
    analytics.record_query("Q2", "medium", 2.0, ["tool2"], {"tool2": 1.0}, success=True)
    analytics.record_query("Q3", "complex", 3.0, ["tool1", "tool2"], {"tool1": 1.0, "tool2": 1.5}, success=False)

    dashboard = analytics.get_dashboard()

    assert dashboard["overview"]["total_queries"] == 3
    assert abs(dashboard["overview"]["success_rate"] - 0.667) < 0.01
    assert dashboard["overview"]["avg_response_time"] == 2.0
    assert dashboard["overview"]["total_tool_calls"] == 4

    cleanup_test_analytics(temp_dir)


def test_dashboard_query_types():
    """Test dashboard query types analysis."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})
    analytics.record_query("Q2", "simple", 2.0, ["tool1"], {"tool1": 1.0})
    analytics.record_query("Q3", "complex", 5.0, ["tool1"], {"tool1": 3.0})

    dashboard = analytics.get_dashboard()

    assert dashboard["query_types"]["simple"]["count"] == 2
    assert dashboard["query_types"]["simple"]["avg_time"] == 1.5
    assert dashboard["query_types"]["complex"]["count"] == 1
    assert dashboard["query_types"]["complex"]["avg_time"] == 5.0

    cleanup_test_analytics(temp_dir)


def test_dashboard_tools():
    """Test dashboard tool performance section."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5}, success=True)
    analytics.record_query("Q2", "simple", 2.0, ["tool1"], {"tool1": 1.0}, success=True)
    analytics.record_query("Q3", "simple", 3.0, ["tool2"], {"tool2": 2.0}, success=False)

    dashboard = analytics.get_dashboard()

    assert "tool1" in dashboard["tools"]
    assert dashboard["tools"]["tool1"]["usage_count"] == 2
    assert dashboard["tools"]["tool1"]["avg_time"] == 0.75
    assert dashboard["tools"]["tool1"]["success_rate"] == 1.0

    assert "tool2" in dashboard["tools"]
    assert dashboard["tools"]["tool2"]["usage_count"] == 1
    assert dashboard["tools"]["tool2"]["success_rate"] == 0.0

    cleanup_test_analytics(temp_dir)


def test_dashboard_reflection():
    """Test dashboard reflection analysis."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5}, reflection_score=0.8)
    analytics.record_query("Q2", "simple", 2.0, ["tool1"], {"tool1": 1.0}, reflection_score=0.9)
    analytics.record_query("Q3", "simple", 3.0, ["tool1"], {"tool1": 1.0}, reflection_score=0.6)

    dashboard = analytics.get_dashboard()

    assert abs(dashboard["reflection"]["avg_score"] - 0.767) < 0.01
    assert abs(dashboard["reflection"]["improvement_rate"] - 0.667) < 0.01
    assert dashboard["reflection"]["count"] == 3

    cleanup_test_analytics(temp_dir)


def test_dashboard_trends():
    """Test dashboard trend analysis."""
    analytics, temp_dir = create_test_analytics()

    for i in range(10):
        analytics.record_query(f"Q{i}", "simple", i + 1.0, ["tool1"], {"tool1": 0.5}, success=True)

    dashboard = analytics.get_dashboard()

    assert len(dashboard["trends"]["response_time_trend"]) == 10
    assert dashboard["trends"]["response_time_trend"][0] == 1.0
    assert dashboard["trends"]["response_time_trend"][-1] == 10.0

    cleanup_test_analytics(temp_dir)


def test_tool_performance_all():
    """Test tool performance for all tools."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})
    analytics.record_query("Q2", "simple", 2.0, ["tool2"], {"tool2": 1.5})

    perf = analytics.get_tool_performance()

    assert "tool1" in perf
    assert "tool2" in perf
    assert perf["tool1"]["usage_count"] == 1
    assert perf["tool2"]["usage_count"] == 1

    cleanup_test_analytics(temp_dir)


def test_tool_performance_specific():
    """Test tool performance for specific tool."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})
    analytics.record_query("Q2", "simple", 2.0, ["tool1"], {"tool1": 1.5})

    perf = analytics.get_tool_performance(tool_name="tool1")

    assert perf["usage_count"] == 2
    assert perf["avg_time"] == 1.0
    assert perf["min_time"] == 0.5
    assert perf["max_time"] == 1.5

    cleanup_test_analytics(temp_dir)


def test_time_analysis_day():
    """Test time-based analysis by day."""
    analytics, temp_dir = create_test_analytics()

    # Record metrics with different timestamps
    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})
    analytics.record_query("Q2", "simple", 2.0, ["tool1"], {"tool1": 1.0})

    analysis = analytics.get_time_analysis(period="day")

    today = datetime.now().strftime("%Y-%m-%d")
    assert today in analysis
    assert analysis[today]["query_count"] == 2

    cleanup_test_analytics(temp_dir)


def test_time_analysis_hour():
    """Test time-based analysis by hour."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})

    analysis = analytics.get_time_analysis(period="hour")

    current_hour = datetime.now().strftime("%Y-%m-%d %H:00")
    assert current_hour in analysis

    cleanup_test_analytics(temp_dir)


def test_bottleneck_slow_tool():
    """Test bottleneck detection for slow tools."""
    analytics, temp_dir = create_test_analytics()

    # Create slow tool (> 10s average)
    analytics.record_query("Q1", "simple", 15.0, ["slow_tool"], {"slow_tool": 15.0})

    bottlenecks = analytics.get_bottlenecks()

    slow_tool_issues = [b for b in bottlenecks if b["type"] == "slow_tool"]
    assert len(slow_tool_issues) > 0
    assert "slow_tool" in slow_tool_issues[0]["message"]

    cleanup_test_analytics(temp_dir)


def test_bottleneck_high_failure():
    """Test bottleneck detection for high failure rate."""
    analytics, temp_dir = create_test_analytics()

    # Create tool with high failure rate
    analytics.record_query("Q1", "simple", 1.0, ["failing_tool"], {"failing_tool": 0.5}, success=False)
    analytics.record_query("Q2", "simple", 1.0, ["failing_tool"], {"failing_tool": 0.5}, success=False)
    analytics.record_query("Q3", "simple", 1.0, ["failing_tool"], {"failing_tool": 0.5}, success=True)

    bottlenecks = analytics.get_bottlenecks()

    failure_issues = [b for b in bottlenecks if b["type"] == "high_failure_rate"]
    assert len(failure_issues) > 0

    cleanup_test_analytics(temp_dir)


def test_bottleneck_long_query():
    """Test bottleneck detection for long queries."""
    analytics, temp_dir = create_test_analytics()

    # Create long query (> 30s)
    analytics.record_query("Long query", "complex", 45.0, ["tool1"], {"tool1": 20.0})

    bottlenecks = analytics.get_bottlenecks()

    long_query_issues = [b for b in bottlenecks if b["type"] == "long_query"]
    assert len(long_query_issues) > 0
    assert "45.00s" in long_query_issues[0]["message"]

    cleanup_test_analytics(temp_dir)


def test_bottleneck_excessive_iterations():
    """Test bottleneck detection for excessive iterations."""
    analytics, temp_dir = create_test_analytics()

    # Create query with many iterations (> 3)
    analytics.record_query("Q1", "complex", 5.0, ["tool1"], {"tool1": 2.0}, iterations=5)

    bottlenecks = analytics.get_bottlenecks()

    iteration_issues = [b for b in bottlenecks if b["type"] == "excessive_iterations"]
    assert len(iteration_issues) > 0
    assert "5 improvement iterations" in iteration_issues[0]["message"]

    cleanup_test_analytics(temp_dir)


def test_export_json():
    """Test JSON export."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})
    analytics.record_query("Q2", "medium", 2.0, ["tool2"], {"tool2": 1.0})

    filepath = analytics.export_metrics(format="json")

    assert Path(filepath).exists()
    with open(filepath, 'r') as f:
        data = json.load(f)
    assert len(data) == 2

    cleanup_test_analytics(temp_dir)


def test_export_csv():
    """Test CSV export."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})

    filepath = analytics.export_metrics(format="csv")

    assert Path(filepath).exists()
    with open(filepath, 'r') as f:
        lines = f.readlines()
    assert len(lines) == 2  # Header + 1 data row

    cleanup_test_analytics(temp_dir)


def test_export_date_filtering():
    """Test export with date filtering."""
    analytics, temp_dir = create_test_analytics()

    # Record metric
    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})

    # Filter to future dates (should export nothing)
    future_date = datetime.now() + timedelta(days=1)
    filepath = analytics.export_metrics(format="json", start_date=future_date)

    with open(filepath, 'r') as f:
        data = json.load(f)
    assert len(data) == 0

    cleanup_test_analytics(temp_dir)


def test_query_comparison():
    """Test query comparison."""
    analytics, temp_dir = create_test_analytics()

    id1 = analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})
    id2 = analytics.record_query("Q2", "complex", 3.0, ["tool2"], {"tool2": 2.0})

    comparison = analytics.get_comparison(id1, id2)

    assert comparison["metric1"]["query"] == "Q1"
    assert comparison["metric2"]["query"] == "Q2"
    assert comparison["differences"]["response_time_diff"] == 2.0

    cleanup_test_analytics(temp_dir)


def test_comparison_not_found():
    """Test comparison with invalid IDs."""
    analytics, temp_dir = create_test_analytics()

    comparison = analytics.get_comparison("invalid1", "invalid2")

    assert "error" in comparison

    cleanup_test_analytics(temp_dir)


def test_empty_dashboard():
    """Test dashboard with no metrics."""
    analytics, temp_dir = create_test_analytics()

    dashboard = analytics.get_dashboard()

    assert dashboard["overview"]["total_queries"] == 0
    assert dashboard["overview"]["success_rate"] == 0.0

    cleanup_test_analytics(temp_dir)


def test_single_metric_stats():
    """Test statistics with single metric."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})

    dashboard = analytics.get_dashboard()

    assert dashboard["overview"]["total_queries"] == 1
    assert dashboard["overview"]["avg_response_time"] == 1.0

    cleanup_test_analytics(temp_dir)


def test_all_successes():
    """Test metrics with all successful queries."""
    analytics, temp_dir = create_test_analytics()

    for i in range(5):
        analytics.record_query(f"Q{i}", "simple", 1.0, ["tool1"], {"tool1": 0.5}, success=True)

    dashboard = analytics.get_dashboard()

    assert dashboard["overview"]["success_rate"] == 1.0

    cleanup_test_analytics(temp_dir)


def test_all_failures():
    """Test metrics with all failed queries."""
    analytics, temp_dir = create_test_analytics()

    for i in range(5):
        analytics.record_query(f"Q{i}", "simple", 1.0, ["tool1"], {"tool1": 0.5}, success=False)

    dashboard = analytics.get_dashboard()

    assert dashboard["overview"]["success_rate"] == 0.0

    cleanup_test_analytics(temp_dir)


def test_metric_pruning():
    """Test automatic pruning of old metrics."""
    temp_dir = tempfile.mkdtemp()

    # Create analytics with short retention (1 day)
    config = {"retention_days": 1}
    analytics = PerformanceAnalytics(storage_path=temp_dir, config=config)

    # Record a metric
    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})

    # Manually set timestamp to old date
    analytics.metrics[0].timestamp = (datetime.now() - timedelta(days=2)).isoformat()
    analytics._save_metrics()

    # Create new instance (should prune old metric)
    analytics2 = PerformanceAnalytics(storage_path=temp_dir, config=config)

    assert len(analytics2.metrics) == 0

    cleanup_test_analytics(temp_dir)


def test_atomic_write():
    """Test atomic file writes."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})

    # Verify file exists and is valid JSON
    assert analytics.metrics_file.exists()

    with open(analytics.metrics_file, 'r') as f:
        data = json.load(f)
    assert len(data) == 1

    cleanup_test_analytics(temp_dir)


def test_reflection_without_scores():
    """Test reflection analysis when no scores available."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})

    dashboard = analytics.get_dashboard()

    assert dashboard["reflection"]["avg_score"] == 0.0
    assert dashboard["reflection"]["count"] == 0

    cleanup_test_analytics(temp_dir)


def test_tool_performance_min_max():
    """Test tool performance min/max times."""
    analytics, temp_dir = create_test_analytics()

    analytics.record_query("Q1", "simple", 1.0, ["tool1"], {"tool1": 0.5})
    analytics.record_query("Q2", "simple", 2.0, ["tool1"], {"tool1": 2.0})
    analytics.record_query("Q3", "simple", 3.0, ["tool1"], {"tool1": 1.0})

    perf = analytics.get_tool_performance(tool_name="tool1")

    assert perf["min_time"] == 0.5
    assert perf["max_time"] == 2.0

    cleanup_test_analytics(temp_dir)


def test_trend_direction_degrading():
    """Test trend direction detection (degrading)."""
    analytics, temp_dir = create_test_analytics()

    # Create degrading trend (times increasing)
    for i in range(10):
        analytics.record_query(f"Q{i}", "simple", i * 2 + 1.0, ["tool1"], {"tool1": 0.5})

    dashboard = analytics.get_dashboard()

    assert dashboard["trends"]["trend_direction"] == "degrading"

    cleanup_test_analytics(temp_dir)


def test_trend_direction_improving():
    """Test trend direction detection (improving)."""
    analytics, temp_dir = create_test_analytics()

    # Create improving trend (times decreasing)
    for i in range(10):
        analytics.record_query(f"Q{i}", "simple", 10.0 - i, ["tool1"], {"tool1": 0.5})

    dashboard = analytics.get_dashboard()

    assert dashboard["trends"]["trend_direction"] == "improving"

    cleanup_test_analytics(temp_dir)


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_record_single_metric,
        test_record_multiple_metrics,
        test_metric_persistence,
        test_dashboard_overview,
        test_dashboard_query_types,
        test_dashboard_tools,
        test_dashboard_reflection,
        test_dashboard_trends,
        test_tool_performance_all,
        test_tool_performance_specific,
        test_time_analysis_day,
        test_time_analysis_hour,
        test_bottleneck_slow_tool,
        test_bottleneck_high_failure,
        test_bottleneck_long_query,
        test_bottleneck_excessive_iterations,
        test_export_json,
        test_export_csv,
        test_export_date_filtering,
        test_query_comparison,
        test_comparison_not_found,
        test_empty_dashboard,
        test_single_metric_stats,
        test_all_successes,
        test_all_failures,
        test_metric_pruning,
        test_atomic_write,
        test_reflection_without_scores,
        test_tool_performance_min_max,
        test_trend_direction_degrading,
        test_trend_direction_improving,
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
