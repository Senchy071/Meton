#!/usr/bin/env python3
"""
Performance Analytics System for Meton.

Tracks and analyzes agent performance metrics including:
- Query response times
- Tool usage and performance
- Success rates
- Reflection scores
- Iterative improvement iterations
- Bottleneck detection
- Trend analysis
"""

import json
import csv
import uuid
import time
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from collections import defaultdict
import tempfile
import shutil


@dataclass
class MetricRecord:
    """Record of a single query's performance metrics."""
    id: str  # UUID
    timestamp: str  # ISO 8601 format
    query: str
    query_type: str  # simple, medium, complex
    response_time: float  # seconds
    tool_calls: List[str]  # Tools used
    tool_times: Dict[str, float]  # Tool execution times
    reflection_score: Optional[float] = None  # If reflection used
    iterations: int = 1  # Iterative improvement count
    tokens_used: Optional[int] = None  # If available
    success: bool = True
    error: Optional[str] = None


class PerformanceAnalytics:
    """Tracks and analyzes agent performance metrics."""

    def __init__(self, storage_path: str = "./analytics_data", config: Dict = None):
        """
        Initialize performance analytics.

        Args:
            storage_path: Directory for storing metrics
            config: Analytics configuration
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)

        self.config = config or {}
        self.retention_days = self.config.get("retention_days", 90)
        self.auto_export_interval = self.config.get("auto_export_interval", 100)

        self.metrics: List[MetricRecord] = []
        self.session_start = datetime.now()
        self.metrics_file = self.storage_path / "metrics_db.json"

        self._load_metrics()
        self._prune_old_metrics()

    def record_query(
        self,
        query: str,
        query_type: str,
        response_time: float,
        tool_calls: List[str],
        tool_times: Dict[str, float],
        reflection_score: Optional[float] = None,
        iterations: int = 1,
        tokens_used: Optional[int] = None,
        success: bool = True,
        error: Optional[str] = None
    ) -> str:
        """
        Record query metrics.

        Args:
            query: Query text
            query_type: simple, medium, or complex
            response_time: Total response time in seconds
            tool_calls: List of tools used
            tool_times: Dict mapping tool names to execution times
            reflection_score: Quality score from reflection (0.0-1.0)
            iterations: Number of improvement iterations
            tokens_used: Tokens used (if available)
            success: Whether query succeeded
            error: Error message if failed

        Returns:
            Metric ID (UUID)
        """
        metric_id = str(uuid.uuid4())

        record = MetricRecord(
            id=metric_id,
            timestamp=datetime.now().isoformat(),
            query=query,
            query_type=query_type,
            response_time=response_time,
            tool_calls=tool_calls,
            tool_times=tool_times,
            reflection_score=reflection_score,
            iterations=iterations,
            tokens_used=tokens_used,
            success=success,
            error=error
        )

        self.metrics.append(record)
        self._save_metrics()

        # Auto-export if threshold reached
        if len(self.metrics) % self.auto_export_interval == 0:
            self._auto_export()

        return metric_id

    def get_dashboard(self) -> Dict:
        """
        Get comprehensive analytics dashboard.

        Returns:
            Dashboard with overview, query types, tools, reflection, trends
        """
        if not self.metrics:
            return self._empty_dashboard()

        total_queries = len(self.metrics)
        successful_queries = sum(1 for m in self.metrics if m.success)
        total_tool_calls = sum(len(m.tool_calls) for m in self.metrics)

        # Overview
        overview = {
            "total_queries": total_queries,
            "success_rate": successful_queries / total_queries if total_queries > 0 else 0.0,
            "avg_response_time": sum(m.response_time for m in self.metrics) / total_queries,
            "total_tool_calls": total_tool_calls
        }

        # Query types analysis
        query_types = self._analyze_query_types()

        # Tool performance
        tools = self._analyze_tool_performance()

        # Reflection analysis
        reflection = self._analyze_reflection()

        # Trends
        trends = self._analyze_trends()

        return {
            "overview": overview,
            "query_types": query_types,
            "tools": tools,
            "reflection": reflection,
            "trends": trends
        }

    def get_tool_performance(self, tool_name: Optional[str] = None) -> Dict:
        """
        Get detailed tool statistics.

        Args:
            tool_name: Specific tool to analyze (None for all)

        Returns:
            Tool performance statistics
        """
        if not self.metrics:
            return {}

        tools_data = defaultdict(lambda: {
            "usage_count": 0,
            "total_time": 0.0,
            "successes": 0,
            "failures": 0,
            "times": []
        })

        for metric in self.metrics:
            for tool in metric.tool_calls:
                tools_data[tool]["usage_count"] += 1

                if tool in metric.tool_times:
                    exec_time = metric.tool_times[tool]
                    tools_data[tool]["total_time"] += exec_time
                    tools_data[tool]["times"].append(exec_time)

                if metric.success:
                    tools_data[tool]["successes"] += 1
                else:
                    tools_data[tool]["failures"] += 1

        # Calculate statistics
        result = {}
        for tool, data in tools_data.items():
            if tool_name and tool != tool_name:
                continue

            usage_count = data["usage_count"]
            avg_time = data["total_time"] / len(data["times"]) if data["times"] else 0.0
            success_rate = data["successes"] / usage_count if usage_count > 0 else 0.0

            result[tool] = {
                "usage_count": usage_count,
                "avg_time": avg_time,
                "success_rate": success_rate,
                "min_time": min(data["times"]) if data["times"] else 0.0,
                "max_time": max(data["times"]) if data["times"] else 0.0
            }

        return result if not tool_name else result.get(tool_name, {})

    def get_time_analysis(self, period: str = "day") -> Dict:
        """
        Analyze performance over time.

        Args:
            period: Time period - hour, day, week, month

        Returns:
            Metrics grouped by time period
        """
        if not self.metrics:
            return {}

        # Group metrics by time period
        grouped = defaultdict(list)

        for metric in self.metrics:
            timestamp = datetime.fromisoformat(metric.timestamp)

            if period == "hour":
                key = timestamp.strftime("%Y-%m-%d %H:00")
            elif period == "day":
                key = timestamp.strftime("%Y-%m-%d")
            elif period == "week":
                # ISO week
                key = timestamp.strftime("%Y-W%W")
            elif period == "month":
                key = timestamp.strftime("%Y-%m")
            else:
                key = timestamp.strftime("%Y-%m-%d")

            grouped[key].append(metric)

        # Calculate statistics for each period
        result = {}
        for key, metrics in sorted(grouped.items()):
            total = len(metrics)
            successes = sum(1 for m in metrics if m.success)

            result[key] = {
                "query_count": total,
                "success_rate": successes / total if total > 0 else 0.0,
                "avg_response_time": sum(m.response_time for m in metrics) / total,
                "total_tool_calls": sum(len(m.tool_calls) for m in metrics)
            }

        return result

    def get_bottlenecks(self) -> List[Dict]:
        """
        Identify performance bottlenecks.

        Returns:
            List of detected issues
        """
        bottlenecks = []

        if not self.metrics:
            return bottlenecks

        # Check slow tools (> 10s average)
        tool_perf = self.get_tool_performance()
        for tool, stats in tool_perf.items():
            if stats["avg_time"] > 10.0:
                bottlenecks.append({
                    "type": "slow_tool",
                    "severity": "high" if stats["avg_time"] > 30.0 else "medium",
                    "message": f"Tool '{tool}' averages {stats['avg_time']:.2f}s",
                    "details": stats
                })

        # Check high failure rates (< 90% success)
        for tool, stats in tool_perf.items():
            if stats["success_rate"] < 0.9:
                bottlenecks.append({
                    "type": "high_failure_rate",
                    "severity": "high" if stats["success_rate"] < 0.5 else "medium",
                    "message": f"Tool '{tool}' has {stats['success_rate']*100:.1f}% success rate",
                    "details": stats
                })

        # Check long queries (> 30s)
        long_queries = [m for m in self.metrics if m.response_time > 30.0]
        for metric in long_queries:
            bottlenecks.append({
                "type": "long_query",
                "severity": "high" if metric.response_time > 60.0 else "medium",
                "message": f"Query took {metric.response_time:.2f}s (complexity: {metric.query_type})",
                "details": {
                    "query": metric.query[:100],
                    "response_time": metric.response_time,
                    "query_type": metric.query_type
                }
            })

        # Check excessive iterations (> 3)
        high_iterations = [m for m in self.metrics if m.iterations > 3]
        for metric in high_iterations:
            bottlenecks.append({
                "type": "excessive_iterations",
                "severity": "medium",
                "message": f"Query required {metric.iterations} improvement iterations",
                "details": {
                    "query": metric.query[:100],
                    "iterations": metric.iterations
                }
            })

        return sorted(bottlenecks, key=lambda x: {"high": 0, "medium": 1, "low": 2}[x["severity"]])

    def export_metrics(
        self,
        format: str = "json",
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> str:
        """
        Export metrics data.

        Args:
            format: json or csv
            start_date: Optional start date filter
            end_date: Optional end date filter

        Returns:
            Path to exported file
        """
        # Filter metrics by date range
        filtered_metrics = self.metrics

        if start_date or end_date:
            filtered_metrics = []
            for metric in self.metrics:
                timestamp = datetime.fromisoformat(metric.timestamp)

                if start_date and timestamp < start_date:
                    continue
                if end_date and timestamp > end_date:
                    continue

                filtered_metrics.append(metric)

        # Generate filename
        timestamp_str = datetime.now().strftime("%Y%m%d_%H%M%S")

        if format == "json":
            filename = f"metrics_export_{timestamp_str}.json"
            filepath = self.storage_path / filename

            data = [asdict(m) for m in filtered_metrics]

            with open(filepath, 'w') as f:
                json.dump(data, f, indent=2)

        elif format == "csv":
            filename = f"metrics_export_{timestamp_str}.csv"
            filepath = self.storage_path / filename

            if filtered_metrics:
                fieldnames = [
                    "id", "timestamp", "query", "query_type", "response_time",
                    "tool_calls", "tool_times", "reflection_score", "iterations", "tokens_used",
                    "success", "error"
                ]

                with open(filepath, 'w', newline='') as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()

                    for metric in filtered_metrics:
                        row = asdict(metric)
                        # Convert lists/dicts to strings for CSV
                        row["tool_calls"] = ",".join(metric.tool_calls)
                        row["tool_times"] = str(metric.tool_times)
                        writer.writerow(row)
        else:
            raise ValueError(f"Unsupported format: {format}")

        return str(filepath)

    def get_comparison(self, metric_id1: str, metric_id2: str) -> Dict:
        """
        Compare two queries.

        Args:
            metric_id1: First metric ID
            metric_id2: Second metric ID

        Returns:
            Comparison highlighting differences
        """
        metric1 = next((m for m in self.metrics if m.id == metric_id1), None)
        metric2 = next((m for m in self.metrics if m.id == metric_id2), None)

        if not metric1 or not metric2:
            return {"error": "One or both metrics not found"}

        comparison = {
            "metric1": {
                "id": metric1.id,
                "query": metric1.query,
                "query_type": metric1.query_type,
                "response_time": metric1.response_time,
                "tool_calls": metric1.tool_calls,
                "success": metric1.success
            },
            "metric2": {
                "id": metric2.id,
                "query": metric2.query,
                "query_type": metric2.query_type,
                "response_time": metric2.response_time,
                "tool_calls": metric2.tool_calls,
                "success": metric2.success
            },
            "differences": {
                "response_time_diff": metric2.response_time - metric1.response_time,
                "tool_calls_diff": list(set(metric2.tool_calls) - set(metric1.tool_calls)),
                "complexity_diff": metric1.query_type != metric2.query_type
            }
        }

        return comparison

    def _load_metrics(self) -> None:
        """Load metrics from disk."""
        if not self.metrics_file.exists():
            self.metrics = []
            return

        try:
            with open(self.metrics_file, 'r') as f:
                data = json.load(f)

            self.metrics = [
                MetricRecord(**record) for record in data
            ]
        except (json.JSONDecodeError, IOError) as e:
            print(f"Warning: Failed to load metrics: {e}")
            self.metrics = []

    def _save_metrics(self) -> None:
        """Persist metrics to disk with atomic write."""
        data = [asdict(m) for m in self.metrics]

        # Atomic write using temp file + rename
        with tempfile.NamedTemporaryFile(
            mode='w',
            dir=self.storage_path,
            delete=False
        ) as tmp_file:
            json.dump(data, tmp_file, indent=2)
            tmp_path = tmp_file.name

        # Atomic rename
        shutil.move(tmp_path, self.metrics_file)

    def _prune_old_metrics(self) -> None:
        """Delete metrics older than retention_days."""
        if self.retention_days <= 0:
            return

        cutoff = datetime.now() - timedelta(days=self.retention_days)

        original_count = len(self.metrics)
        self.metrics = [
            m for m in self.metrics
            if datetime.fromisoformat(m.timestamp) > cutoff
        ]

        if len(self.metrics) < original_count:
            self._save_metrics()

    def _auto_export(self) -> None:
        """Auto-export metrics when threshold reached."""
        try:
            self.export_metrics(format="json")
        except Exception as e:
            print(f"Warning: Auto-export failed: {e}")

    def _analyze_query_types(self) -> Dict:
        """Analyze metrics by query type."""
        types_data = defaultdict(lambda: {"count": 0, "total_time": 0.0})

        for metric in self.metrics:
            types_data[metric.query_type]["count"] += 1
            types_data[metric.query_type]["total_time"] += metric.response_time

        result = {}
        for qtype, data in types_data.items():
            result[qtype] = {
                "count": data["count"],
                "avg_time": data["total_time"] / data["count"] if data["count"] > 0 else 0.0
            }

        return result

    def _analyze_tool_performance(self) -> Dict:
        """Analyze tool performance for dashboard."""
        return self.get_tool_performance()

    def _analyze_reflection(self) -> Dict:
        """Analyze reflection metrics."""
        reflection_scores = [
            m.reflection_score for m in self.metrics
            if m.reflection_score is not None
        ]

        if not reflection_scores:
            return {
                "avg_score": 0.0,
                "improvement_rate": 0.0,
                "count": 0
            }

        # Calculate improvement rate (queries with score > 0.7)
        high_quality = sum(1 for score in reflection_scores if score > 0.7)

        return {
            "avg_score": sum(reflection_scores) / len(reflection_scores),
            "improvement_rate": high_quality / len(reflection_scores),
            "count": len(reflection_scores)
        }

    def _analyze_trends(self) -> Dict:
        """Analyze performance trends."""
        # Response time trend (last 10)
        recent_metrics = self.metrics[-10:] if len(self.metrics) > 10 else self.metrics
        response_time_trend = [m.response_time for m in recent_metrics]

        # Success rate trend (last 20)
        recent_20 = self.metrics[-20:] if len(self.metrics) > 20 else self.metrics
        if recent_20:
            successes = sum(1 for m in recent_20 if m.success)
            success_rate_trend = [successes / len(recent_20)]
        else:
            success_rate_trend = []

        # Detect trend direction
        trend_direction = "stable"
        if len(response_time_trend) >= 5:
            first_half_avg = sum(response_time_trend[:len(response_time_trend)//2]) / (len(response_time_trend)//2)
            second_half_avg = sum(response_time_trend[len(response_time_trend)//2:]) / (len(response_time_trend) - len(response_time_trend)//2)

            if second_half_avg > first_half_avg * 1.2:
                trend_direction = "degrading"
            elif second_half_avg < first_half_avg * 0.8:
                trend_direction = "improving"

        return {
            "response_time_trend": response_time_trend,
            "success_rate_trend": success_rate_trend,
            "trend_direction": trend_direction
        }

    def get_advanced_metrics(self) -> Dict:
        """
        Get advanced performance metrics.

        Returns:
            Advanced metrics including efficiency, quality, and resource usage
        """
        if not self.metrics:
            return {
                "efficiency": {},
                "quality": {},
                "resource_usage": {}
            }

        total_queries = len(self.metrics)
        total_tool_calls = sum(len(m.tool_calls) for m in self.metrics)

        # Efficiency metrics
        avg_tools_per_query = total_tool_calls / total_queries if total_queries > 0 else 0.0

        # Calculate parallel execution rate (queries using multiple tools)
        parallel_queries = sum(1 for m in self.metrics if len(m.tool_calls) > 1)
        parallel_execution_rate = parallel_queries / total_queries if total_queries > 0 else 0.0

        # Reflection trigger rate
        reflection_queries = sum(1 for m in self.metrics if m.reflection_score is not None)
        reflection_trigger_rate = reflection_queries / total_queries if total_queries > 0 else 0.0

        # Iteration distribution
        iteration_distribution = defaultdict(int)
        for metric in self.metrics:
            iteration_distribution[metric.iterations] += 1

        # Quality metrics
        reflection_scores = [m.reflection_score for m in self.metrics if m.reflection_score is not None]
        avg_reflection_score = sum(reflection_scores) / len(reflection_scores) if reflection_scores else 0.0

        # Improvement rate (scores improving over time)
        improvement_count = 0
        if len(reflection_scores) >= 2:
            for i in range(1, len(reflection_scores)):
                if reflection_scores[i] > reflection_scores[i-1]:
                    improvement_count += 1
        improvement_rate = improvement_count / (len(reflection_scores) - 1) if len(reflection_scores) > 1 else 0.0

        # User satisfaction (based on success rate and reflection scores)
        success_rate = sum(1 for m in self.metrics if m.success) / total_queries if total_queries > 0 else 0.0
        user_satisfaction = (success_rate * 0.6 + avg_reflection_score * 0.4)

        # Resource usage
        tokens_data = [m.tokens_used for m in self.metrics if m.tokens_used is not None]
        avg_tokens_per_query = sum(tokens_data) / len(tokens_data) if tokens_data else 0

        # Estimate peak memory (based on tokens and model size)
        peak_memory_mb = max(tokens_data) * 0.004 if tokens_data else 0  # Rough estimate

        # Cache hit rate (placeholder - would need actual cache implementation)
        cache_hit_rate = 0.0

        return {
            "efficiency": {
                "avg_tools_per_query": round(avg_tools_per_query, 2),
                "parallel_execution_rate": round(parallel_execution_rate, 3),
                "reflection_trigger_rate": round(reflection_trigger_rate, 3),
                "iteration_distribution": dict(iteration_distribution)
            },
            "quality": {
                "avg_reflection_score": round(avg_reflection_score, 3),
                "improvement_rate": round(improvement_rate, 3),
                "user_satisfaction": round(user_satisfaction, 3)
            },
            "resource_usage": {
                "avg_tokens_per_query": int(avg_tokens_per_query),
                "peak_memory_mb": int(peak_memory_mb),
                "cache_hit_rate": round(cache_hit_rate, 3)
            }
        }

    def compare_time_periods(
        self,
        period1_start: datetime,
        period1_end: datetime,
        period2_start: datetime,
        period2_end: datetime
    ) -> Dict:
        """
        Compare metrics between two time periods.

        Args:
            period1_start: Start of first period
            period1_end: End of first period
            period2_start: Start of second period
            period2_end: End of second period

        Returns:
            Comparison showing changes between periods
        """
        def get_period_metrics(start: datetime, end: datetime) -> Dict:
            """Get metrics for a specific time period."""
            period_metrics = [
                m for m in self.metrics
                if start <= datetime.fromisoformat(m.timestamp) <= end
            ]

            if not period_metrics:
                return {
                    "query_count": 0,
                    "avg_response_time": 0.0,
                    "success_rate": 0.0,
                    "tool_usage": {}
                }

            total = len(period_metrics)
            successes = sum(1 for m in period_metrics if m.success)

            tool_usage = defaultdict(int)
            for metric in period_metrics:
                for tool in metric.tool_calls:
                    tool_usage[tool] += 1

            return {
                "query_count": total,
                "avg_response_time": sum(m.response_time for m in period_metrics) / total,
                "success_rate": successes / total if total > 0 else 0.0,
                "tool_usage": dict(tool_usage)
            }

        period1 = get_period_metrics(period1_start, period1_end)
        period2 = get_period_metrics(period2_start, period2_end)

        # Calculate changes
        response_time_change = 0.0
        if period1["avg_response_time"] > 0:
            response_time_change = (
                (period2["avg_response_time"] - period1["avg_response_time"]) /
                period1["avg_response_time"] * 100
            )

        success_rate_change = (period2["success_rate"] - period1["success_rate"]) * 100

        # Tool usage changes
        tool_usage_changes = {}
        all_tools = set(list(period1["tool_usage"].keys()) + list(period2["tool_usage"].keys()))
        for tool in all_tools:
            count1 = period1["tool_usage"].get(tool, 0)
            count2 = period2["tool_usage"].get(tool, 0)
            change = ((count2 - count1) / count1 * 100) if count1 > 0 else (100 if count2 > 0 else 0)
            tool_usage_changes[tool] = round(change, 1)

        # Quality trend
        if abs(response_time_change) < 10 and abs(success_rate_change) < 5:
            quality_trend = "stable"
        elif response_time_change < 0 and success_rate_change > 0:
            quality_trend = "improving"
        else:
            quality_trend = "declining"

        return {
            "period1": {
                "start": period1_start.isoformat(),
                "end": period1_end.isoformat(),
                "metrics": period1
            },
            "period2": {
                "start": period2_start.isoformat(),
                "end": period2_end.isoformat(),
                "metrics": period2
            },
            "changes": {
                "response_time_change": round(response_time_change, 2),
                "success_rate_change": round(success_rate_change, 2),
                "query_count_change": period2["query_count"] - period1["query_count"],
                "tool_usage_changes": tool_usage_changes,
                "quality_trend": quality_trend
            }
        }

    def predict_performance(self, query: str) -> Dict:
        """
        Predict performance metrics for a query.

        Args:
            query: Query text to analyze

        Returns:
            Predicted performance metrics
        """
        if not self.metrics:
            return {
                "estimated_time": 5.0,
                "estimated_tools": [],
                "complexity": "unknown",
                "confidence": 0.0
            }

        # Simple heuristics for prediction
        query_lower = query.lower()

        # Estimate complexity based on keywords
        complexity_keywords = {
            "simple": ["what", "show", "list", "get"],
            "medium": ["explain", "how", "analyze", "find"],
            "complex": ["compare", "optimize", "refactor", "implement", "debug"]
        }

        complexity = "medium"  # default
        for comp, keywords in complexity_keywords.items():
            if any(kw in query_lower for kw in keywords):
                complexity = comp
                break

        # Get average time for similar complexity queries
        similar_metrics = [m for m in self.metrics if m.query_type == complexity]
        if similar_metrics:
            estimated_time = sum(m.response_time for m in similar_metrics) / len(similar_metrics)
        else:
            # Fallback estimates
            complexity_times = {"simple": 3.0, "medium": 10.0, "complex": 30.0}
            estimated_time = complexity_times.get(complexity, 10.0)

        # Predict tools based on query content
        estimated_tools = []
        tool_keywords = {
            "file_operations": ["file", "read", "write", "directory"],
            "codebase_search": ["find", "search", "locate", "where"],
            "code_executor": ["execute", "run", "calculate"],
            "git_operations": ["git", "commit", "branch", "diff"]
        }

        for tool, keywords in tool_keywords.items():
            if any(kw in query_lower for kw in keywords):
                estimated_tools.append(tool)

        # Calculate confidence based on historical data similarity
        confidence = min(len(similar_metrics) / 10.0, 1.0)  # Max confidence at 10 similar queries

        return {
            "estimated_time": round(estimated_time, 2),
            "estimated_tools": estimated_tools if estimated_tools else ["unknown"],
            "complexity": complexity,
            "confidence": round(confidence, 2)
        }

    def generate_report(self, period: str = "week") -> str:
        """
        Generate comprehensive analytics report.

        Args:
            period: Time period - day, week, month, all

        Returns:
            Markdown formatted report
        """
        # Determine date range
        now = datetime.now()
        if period == "day":
            start_date = now - timedelta(days=1)
            period_name = "Last 24 Hours"
        elif period == "week":
            start_date = now - timedelta(days=7)
            period_name = "Last 7 Days"
        elif period == "month":
            start_date = now - timedelta(days=30)
            period_name = "Last 30 Days"
        else:  # all
            start_date = datetime.min
            period_name = "All Time"

        # Filter metrics
        period_metrics = [
            m for m in self.metrics
            if datetime.fromisoformat(m.timestamp) >= start_date
        ]

        if not period_metrics:
            return f"# Meton Performance Report - {period_name}\n\nNo data available for this period.\n"

        # Calculate statistics
        total = len(period_metrics)
        successes = sum(1 for m in period_metrics if m.success)
        success_rate = successes / total * 100 if total > 0 else 0

        avg_time = sum(m.response_time for m in period_metrics) / total
        min_time = min(m.response_time for m in period_metrics)
        max_time = max(m.response_time for m in period_metrics)

        # Tool statistics
        tool_usage = defaultdict(int)
        for metric in period_metrics:
            for tool in metric.tool_calls:
                tool_usage[tool] += 1

        # Build report
        report = f"""# Meton Performance Report - {period_name}

**Generated:** {now.strftime("%Y-%m-%d %H:%M:%S")}

---

## 📊 Overview

- **Total Queries:** {total}
- **Success Rate:** {success_rate:.1f}%
- **Avg Response Time:** {avg_time:.2f}s
- **Min/Max Time:** {min_time:.2f}s / {max_time:.2f}s

---

## 🔧 Tool Performance

"""

        for tool, count in sorted(tool_usage.items(), key=lambda x: x[1], reverse=True):
            report += f"- **{tool}:** {count} uses\n"

        # Quality metrics
        reflection_scores = [m.reflection_score for m in period_metrics if m.reflection_score is not None]
        if reflection_scores:
            avg_reflection = sum(reflection_scores) / len(reflection_scores)
            report += f"\n---\n\n## ⭐ Quality Metrics\n\n- **Avg Reflection Score:** {avg_reflection:.3f}\n"
            report += f"- **Reflection Usage:** {len(reflection_scores)}/{total} queries\n"

        # Bottlenecks
        bottlenecks = self.get_bottlenecks()
        if bottlenecks:
            report += "\n---\n\n## ⚠️ Detected Issues\n\n"
            for bottleneck in bottlenecks[:5]:  # Top 5
                severity_emoji = {"high": "🔴", "medium": "🟡", "low": "🟢"}[bottleneck["severity"]]
                report += f"{severity_emoji} **{bottleneck['type'].replace('_', ' ').title()}:** {bottleneck['message']}\n\n"
        else:
            report += "\n---\n\n## ✅ All Systems Nominal\n\nNo performance issues detected.\n"

        # Recommendations
        report += "\n---\n\n## 💡 Recommendations\n\n"

        if avg_time > 15.0:
            report += "- Consider using faster models for simple queries\n"

        if success_rate < 90.0:
            report += "- Investigate and fix recurring failures\n"

        if len(tool_usage) < 3:
            report += "- Explore using more tools for better results\n"

        if not reflection_scores:
            report += "- Enable self-reflection for quality improvement\n"

        report += "\n---\n\n*Report generated by Meton Performance Analytics*\n"

        return report

    def check_performance_alerts(self) -> List[Dict]:
        """
        Check for performance degradation and generate alerts.

        Returns:
            List of alerts
        """
        alerts = []

        if not self.metrics or len(self.metrics) < 10:
            return alerts  # Need enough data for meaningful alerts

        # Get recent metrics (last 20)
        recent = self.metrics[-20:]
        older = self.metrics[-40:-20] if len(self.metrics) >= 40 else []

        if not older:
            return alerts  # Need comparison data

        # Check response time trend
        recent_avg_time = sum(m.response_time for m in recent) / len(recent)
        older_avg_time = sum(m.response_time for m in older) / len(older)

        time_increase = ((recent_avg_time - older_avg_time) / older_avg_time * 100) if older_avg_time > 0 else 0

        if time_increase > 20:
            alerts.append({
                "type": "performance_degradation",
                "severity": "high" if time_increase > 50 else "medium",
                "message": f"Response time increased by {time_increase:.1f}%",
                "details": {
                    "recent_avg": recent_avg_time,
                    "older_avg": older_avg_time,
                    "increase_pct": time_increase
                },
                "timestamp": datetime.now().isoformat()
            })

        # Check success rate
        recent_success_rate = sum(1 for m in recent if m.success) / len(recent)

        if recent_success_rate < 0.8:
            alerts.append({
                "type": "low_success_rate",
                "severity": "high" if recent_success_rate < 0.6 else "medium",
                "message": f"Success rate dropped to {recent_success_rate*100:.1f}%",
                "details": {
                    "success_rate": recent_success_rate,
                    "failures": sum(1 for m in recent if not m.success)
                },
                "timestamp": datetime.now().isoformat()
            })

        # Check tool failure rates
        tool_failures = defaultdict(lambda: {"total": 0, "failures": 0})
        for metric in recent:
            for tool in metric.tool_calls:
                tool_failures[tool]["total"] += 1
                if not metric.success:
                    tool_failures[tool]["failures"] += 1

        for tool, stats in tool_failures.items():
            failure_rate = stats["failures"] / stats["total"] if stats["total"] > 0 else 0
            if failure_rate > 0.1:
                alerts.append({
                    "type": "tool_failure",
                    "severity": "high" if failure_rate > 0.3 else "medium",
                    "message": f"Tool '{tool}' has {failure_rate*100:.1f}% failure rate",
                    "details": {
                        "tool": tool,
                        "failure_rate": failure_rate,
                        "failures": stats["failures"],
                        "total": stats["total"]
                    },
                    "timestamp": datetime.now().isoformat()
                })

        return alerts

    def _empty_dashboard(self) -> Dict:
        """Return empty dashboard structure."""
        return {
            "overview": {
                "total_queries": 0,
                "success_rate": 0.0,
                "avg_response_time": 0.0,
                "total_tool_calls": 0
            },
            "query_types": {},
            "tools": {},
            "reflection": {
                "avg_score": 0.0,
                "improvement_rate": 0.0,
                "count": 0
            },
            "trends": {
                "response_time_trend": [],
                "success_rate_trend": [],
                "trend_direction": "stable"
            }
        }
