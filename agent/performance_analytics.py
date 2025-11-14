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
