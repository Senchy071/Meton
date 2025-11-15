#!/usr/bin/env python3
"""
Cross-Session Learning System.

Learns patterns across sessions to improve future interactions by analyzing
recurring queries, tool usage patterns, errors, and successes.
"""

import json
import uuid
import threading
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
from collections import defaultdict, Counter
import re

try:
    from memory.long_term_memory import LongTermMemory
    MEMORY_AVAILABLE = True
except ImportError:
    MEMORY_AVAILABLE = False
    LongTermMemory = None


@dataclass
class Pattern:
    """Represents a detected pattern across sessions."""

    id: str  # UUID
    pattern_type: str  # query, tool_usage, error, success
    description: str
    occurrences: int
    confidence: float  # 0.0-1.0
    examples: List[str] = field(default_factory=list)  # Example queries/situations
    recommendation: str = ""  # What to do when pattern detected
    created_at: str = ""  # ISO 8601
    last_seen: str = ""  # ISO 8601

    def __post_init__(self):
        """Initialize timestamps if not set."""
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.last_seen:
            self.last_seen = now

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Pattern':
        """Create Pattern from dictionary."""
        return cls(**data)


@dataclass
class Insight:
    """Represents an actionable insight from pattern analysis."""

    id: str  # UUID
    insight_type: str  # improvement, warning, optimization
    title: str
    description: str
    impact: str  # high, medium, low
    actionable: bool
    applied: bool = False
    created_at: str = ""  # ISO 8601

    def __post_init__(self):
        """Initialize timestamp if not set."""
        if not self.created_at:
            self.created_at = datetime.now().isoformat()

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict) -> 'Insight':
        """Create Insight from dictionary."""
        return cls(**data)


class CrossSessionLearning:
    """Learns patterns across sessions to improve future interactions."""

    VALID_PATTERN_TYPES = {'query', 'tool_usage', 'error', 'success'}
    VALID_INSIGHT_TYPES = {'improvement', 'warning', 'optimization'}
    VALID_IMPACTS = {'high', 'medium', 'low'}

    def __init__(
        self,
        long_term_memory=None,
        feedback_system=None,
        analytics=None,
        storage_path: str = "./memory",
        min_occurrences: int = 5,
        min_confidence: float = 0.7,
        auto_apply_insights: bool = False
    ):
        """
        Initialize cross-session learning system.

        Args:
            long_term_memory: LongTermMemory instance (optional)
            feedback_system: FeedbackLearningSystem instance (optional)
            analytics: PerformanceAnalytics instance (optional)
            storage_path: Directory to store patterns and insights
            min_occurrences: Minimum occurrences to consider a pattern
            min_confidence: Minimum confidence threshold
            auto_apply_insights: Automatically apply high-confidence insights
        """
        self.long_term_memory = long_term_memory
        self.feedback_system = feedback_system
        self.analytics = analytics

        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)

        self.min_occurrences = min_occurrences
        self.min_confidence = min_confidence
        self.auto_apply_insights = auto_apply_insights

        self.patterns: Dict[str, Pattern] = {}  # id -> Pattern
        self.insights: Dict[str, Insight] = {}  # id -> Insight
        self.lock = threading.Lock()

        self._load_patterns()
        self._load_insights()

    def analyze_sessions(self, lookback_days: int = 30) -> List[Insight]:
        """
        Analyze recent sessions for patterns.

        Args:
            lookback_days: Number of days to look back

        Returns:
            List of new insights generated
        """
        with self.lock:
            new_insights = []

            # Detect all pattern types
            query_patterns = self.detect_query_patterns(lookback_days)
            tool_patterns = self.detect_tool_patterns(lookback_days)
            error_patterns = self.detect_error_patterns(lookback_days)
            success_patterns = self.detect_success_patterns(lookback_days)

            all_patterns = query_patterns + tool_patterns + error_patterns + success_patterns

            # Store patterns
            for pattern in all_patterns:
                self.patterns[pattern.id] = pattern

            # Generate insights from patterns
            generated_insights = self.generate_insights(all_patterns)

            for insight in generated_insights:
                if insight.id not in self.insights:
                    self.insights[insight.id] = insight
                    new_insights.append(insight)

                    # Auto-apply if enabled and meets criteria
                    if self.auto_apply_insights and self._should_auto_apply(insight):
                        self.apply_insight(insight.id)

            # Persist
            self._save_patterns()
            self._save_insights()

            return new_insights

    def detect_query_patterns(self, lookback_days: int = 30) -> List[Pattern]:
        """
        Find recurring query types.

        Args:
            lookback_days: Number of days to analyze

        Returns:
            List of detected query patterns
        """
        patterns = []

        if not self.long_term_memory:
            return patterns

        # Get recent conversation memories
        cutoff = datetime.now() - timedelta(days=lookback_days)
        all_memories = list(self.long_term_memory.memories.values())

        recent_conversations = [
            m for m in all_memories
            if m.memory_type == "conversation" and
            datetime.fromisoformat(m.timestamp) > cutoff
        ]

        if not recent_conversations:
            return patterns

        # Extract queries (Q: prefix)
        queries = []
        for mem in recent_conversations:
            if mem.content.startswith("Q:"):
                query_line = mem.content.split("\n")[0][3:].strip()  # Remove "Q: "
                queries.append(query_line)

        # Analyze topics using keyword extraction
        topic_queries = defaultdict(list)

        # Define topic keywords
        topics = {
            'async': ['async', 'await', 'asyncio', 'coroutine', 'asynchronous'],
            'type_hints': ['type hint', 'typing', 'annotation', 'mypy'],
            'authentication': ['auth', 'login', 'password', 'jwt', 'token', 'session'],
            'testing': ['test', 'pytest', 'unittest', 'mock', 'fixture'],
            'database': ['database', 'sql', 'query', 'orm', 'postgres', 'mysql'],
            'api': ['api', 'endpoint', 'rest', 'http', 'request', 'response'],
            'docker': ['docker', 'container', 'dockerfile', 'compose'],
            'git': ['git', 'commit', 'branch', 'merge', 'pull request'],
            'performance': ['performance', 'optimize', 'speed', 'slow', 'cache'],
            'error_handling': ['error', 'exception', 'try', 'catch', 'handle'],
        }

        for query in queries:
            query_lower = query.lower()
            for topic, keywords in topics.items():
                if any(keyword in query_lower for keyword in keywords):
                    topic_queries[topic].append(query)

        # Generate patterns for frequent topics
        total_queries = len(queries)
        for topic, topic_queries_list in topic_queries.items():
            occurrences = len(topic_queries_list)

            if occurrences >= self.min_occurrences:
                # Calculate confidence
                frequency = occurrences / max(total_queries, 1)
                consistency = min(occurrences / 10, 1.0)  # More occurrences = higher consistency
                confidence = self._calculate_confidence(occurrences, total_queries, consistency)

                if confidence >= self.min_confidence:
                    pattern = Pattern(
                        id=str(uuid.uuid4()),
                        pattern_type="query",
                        description=f"User frequently asks about {topic}",
                        occurrences=occurrences,
                        confidence=confidence,
                        examples=topic_queries_list[:5],  # Keep top 5 examples
                        recommendation=f"Provide comprehensive {topic} guidance proactively"
                    )
                    patterns.append(pattern)

        return patterns

    def detect_tool_patterns(self, lookback_days: int = 30) -> List[Pattern]:
        """
        Analyze tool usage patterns.

        Args:
            lookback_days: Number of days to analyze

        Returns:
            List of detected tool usage patterns
        """
        patterns = []

        if not self.analytics:
            return patterns

        try:
            # Get analytics dashboard
            dashboard = self.analytics.get_dashboard()

            # Analyze tool usage
            tool_usage = dashboard.get('metrics', {}).get('tool_usage', {})

            if tool_usage:
                total_uses = sum(tool_usage.values())

                # Detect heavily used tools
                for tool_name, count in tool_usage.items():
                    if count >= self.min_occurrences:
                        frequency = count / max(total_uses, 1)
                        if frequency > 0.3:  # Used in >30% of cases
                            pattern = Pattern(
                                id=str(uuid.uuid4()),
                                pattern_type="tool_usage",
                                description=f"{tool_name} is heavily used ({frequency*100:.1f}% of tool calls)",
                                occurrences=count,
                                confidence=min(frequency, 1.0),
                                examples=[f"Used {count} times"],
                                recommendation=f"Optimize {tool_name} for better performance"
                            )
                            patterns.append(pattern)

                # Detect underutilized tools
                for tool_name, count in tool_usage.items():
                    frequency = count / max(total_uses, 1)
                    if frequency < 0.05 and total_uses > 20:  # <5% usage with significant data
                        pattern = Pattern(
                            id=str(uuid.uuid4()),
                            pattern_type="tool_usage",
                            description=f"{tool_name} is rarely used ({frequency*100:.1f}% of tool calls)",
                            occurrences=count,
                            confidence=0.7,
                            examples=[f"Used only {count} times"],
                            recommendation=f"Consider if {tool_name} should be more proactive or removed"
                        )
                        patterns.append(pattern)

        except Exception:
            pass  # Analytics not available or failed

        return patterns

    def detect_error_patterns(self, lookback_days: int = 30) -> List[Pattern]:
        """
        Find recurring errors/failures.

        Args:
            lookback_days: Number of days to analyze

        Returns:
            List of detected error patterns
        """
        patterns = []

        if not self.feedback_system:
            return patterns

        try:
            # Get negative feedback
            all_feedback = list(self.feedback_system.feedback_store.values())

            cutoff = datetime.now() - timedelta(days=lookback_days)
            recent_negative = [
                f for f in all_feedback
                if f.sentiment == "negative" and
                datetime.fromisoformat(f.timestamp) > cutoff
            ]

            if len(recent_negative) >= self.min_occurrences:
                # Analyze error reasons
                error_reasons = Counter()
                error_examples = defaultdict(list)

                for feedback in recent_negative:
                    reason = feedback.reason or "Unknown error"
                    error_reasons[reason] += 1
                    if len(error_examples[reason]) < 3:
                        error_examples[reason].append(feedback.query[:100])

                # Create patterns for common errors
                for reason, count in error_reasons.most_common(5):
                    if count >= self.min_occurrences:
                        pattern = Pattern(
                            id=str(uuid.uuid4()),
                            pattern_type="error",
                            description=f"Recurring error: {reason}",
                            occurrences=count,
                            confidence=min(count / len(recent_negative), 1.0),
                            examples=error_examples[reason],
                            recommendation=f"Investigate and fix: {reason}"
                        )
                        patterns.append(pattern)

        except Exception:
            pass  # Feedback system not available

        return patterns

    def detect_success_patterns(self, lookback_days: int = 30) -> List[Pattern]:
        """
        Identify what works well.

        Args:
            lookback_days: Number of days to analyze

        Returns:
            List of detected success patterns
        """
        patterns = []

        if not self.feedback_system:
            return patterns

        try:
            # Get positive feedback
            all_feedback = list(self.feedback_system.feedback_store.values())

            cutoff = datetime.now() - timedelta(days=lookback_days)
            recent_positive = [
                f for f in all_feedback
                if f.sentiment == "positive" and
                datetime.fromisoformat(f.timestamp) > cutoff
            ]

            if len(recent_positive) >= self.min_occurrences:
                # Analyze success factors
                total_feedback = len([f for f in all_feedback if datetime.fromisoformat(f.timestamp) > cutoff])

                if total_feedback > 0:
                    success_rate = len(recent_positive) / total_feedback

                    if success_rate > 0.7:  # >70% positive feedback
                        pattern = Pattern(
                            id=str(uuid.uuid4()),
                            pattern_type="success",
                            description=f"High success rate: {success_rate*100:.1f}% positive feedback",
                            occurrences=len(recent_positive),
                            confidence=success_rate,
                            examples=[f.query[:100] for f in recent_positive[:3]],
                            recommendation="Continue current approach - it's working well"
                        )
                        patterns.append(pattern)

        except Exception:
            pass  # Feedback system not available

        return patterns

    def generate_insights(self, patterns: List[Pattern]) -> List[Insight]:
        """
        Convert patterns into actionable insights.

        Args:
            patterns: List of detected patterns

        Returns:
            List of generated insights
        """
        insights = []

        for pattern in patterns:
            insight = self._pattern_to_insight(pattern)
            if insight:
                insights.append(insight)

        return insights

    def _pattern_to_insight(self, pattern: Pattern) -> Optional[Insight]:
        """Convert a pattern to an insight."""
        if pattern.pattern_type == "query":
            # Query patterns suggest improvements
            return Insight(
                id=str(uuid.uuid4()),
                insight_type="improvement",
                title=f"Proactive Guidance: {pattern.description.split('about ')[-1].title()}",
                description=f"{pattern.description} ({pattern.occurrences} times). {pattern.recommendation}.",
                impact="medium" if pattern.confidence > 0.8 else "low",
                actionable=True
            )

        elif pattern.pattern_type == "tool_usage":
            if "heavily used" in pattern.description:
                return Insight(
                    id=str(uuid.uuid4()),
                    insight_type="optimization",
                    title=f"Optimize Popular Tool",
                    description=pattern.description + ". " + pattern.recommendation,
                    impact="high" if pattern.confidence > 0.5 else "medium",
                    actionable=True
                )
            elif "rarely used" in pattern.description:
                return Insight(
                    id=str(uuid.uuid4()),
                    insight_type="warning",
                    title=f"Underutilized Tool",
                    description=pattern.description + ". " + pattern.recommendation,
                    impact="low",
                    actionable=True
                )

        elif pattern.pattern_type == "error":
            return Insight(
                id=str(uuid.uuid4()),
                insight_type="warning",
                title=f"Recurring Error Detected",
                description=pattern.description + ". " + pattern.recommendation,
                impact="high",
                actionable=True
            )

        elif pattern.pattern_type == "success":
            return Insight(
                id=str(uuid.uuid4()),
                insight_type="optimization",
                title="High Success Rate",
                description=pattern.description + ". " + pattern.recommendation,
                impact="medium",
                actionable=False  # Just informational
            )

        return None

    def apply_insight(self, insight_id: str) -> bool:
        """
        Apply an insight to agent behavior.

        Args:
            insight_id: Insight UUID

        Returns:
            True if applied successfully
        """
        with self.lock:
            if insight_id not in self.insights:
                return False

            insight = self.insights[insight_id]

            if insight.applied:
                return True  # Already applied

            # Mark as applied
            insight.applied = True

            # Save updated insights
            self._save_insights()

            return True

    def get_recommendations(self, query: str, context: Dict) -> List[str]:
        """
        Get real-time recommendations based on patterns.

        Args:
            query: Current user query
            context: Query context (tool usage, etc.)

        Returns:
            List of recommendations
        """
        recommendations = []
        query_lower = query.lower()

        # Match against existing patterns
        for pattern in self.patterns.values():
            if pattern.pattern_type == "query":
                # Check if query matches pattern topic
                topic = pattern.description.split("about ")[-1].lower()
                if topic in query_lower:
                    recommendations.append(pattern.recommendation)

        return recommendations

    def track_pattern_occurrence(self, pattern_id: str, example: str) -> None:
        """
        Record pattern occurrence.

        Args:
            pattern_id: Pattern UUID
            example: Example of pattern occurrence
        """
        with self.lock:
            if pattern_id not in self.patterns:
                return

            pattern = self.patterns[pattern_id]

            # Update occurrences
            pattern.occurrences += 1

            # Add example if not too many
            if len(pattern.examples) < 10:
                pattern.examples.append(example[:200])

            # Update last_seen
            pattern.last_seen = datetime.now().isoformat()

            # Recalculate confidence
            pattern.confidence = min(pattern.confidence * 1.05, 1.0)  # Slight boost

            self._save_patterns()

    def get_learning_summary(self) -> Dict:
        """
        Get summary of cross-session learning.

        Returns:
            Dictionary with learning metrics
        """
        with self.lock:
            # Calculate learning velocity (patterns per week)
            if self.patterns:
                pattern_ages = []
                now = datetime.now()

                for pattern in self.patterns.values():
                    created = datetime.fromisoformat(pattern.created_at)
                    age_days = (now - created).days
                    pattern_ages.append(age_days)

                avg_age_days = sum(pattern_ages) / len(pattern_ages)
                learning_velocity = len(self.patterns) / max(avg_age_days / 7, 1)  # Patterns per week
            else:
                learning_velocity = 0.0

            # Top patterns by confidence
            top_patterns = sorted(
                self.patterns.values(),
                key=lambda p: p.confidence,
                reverse=True
            )[:5]

            # Recent insights
            recent_insights = sorted(
                self.insights.values(),
                key=lambda i: i.created_at,
                reverse=True
            )[:5]

            return {
                "total_patterns": len(self.patterns),
                "insights_generated": len(self.insights),
                "insights_applied": len([i for i in self.insights.values() if i.applied]),
                "top_patterns": [p.to_dict() for p in top_patterns],
                "recent_insights": [i.to_dict() for i in recent_insights],
                "learning_velocity": learning_velocity
            }

    def _calculate_confidence(self, occurrences: int, total_samples: int, consistency: float) -> float:
        """
        Calculate pattern confidence.

        Args:
            occurrences: How many times pattern seen
            total_samples: Total queries/sessions analyzed
            consistency: How consistent the pattern is (0-1)

        Returns:
            Confidence score (0.0 to 1.0)
        """
        frequency = occurrences / max(total_samples, 1)

        # Confidence increases with frequency and consistency
        confidence = (frequency * 0.5 + consistency * 0.5)

        # Require minimum occurrences
        if occurrences < self.min_occurrences:
            confidence *= 0.5

        return min(confidence, 1.0)

    def _should_auto_apply(self, insight: Insight) -> bool:
        """Determine if insight should be auto-applied."""
        # Only auto-apply high-confidence, low-risk insights
        if not insight.actionable:
            return False

        # Only improvements and optimizations (not warnings)
        if insight.insight_type == "warning":
            return False

        # Only high impact
        if insight.impact != "high":
            return False

        return True

    def _save_patterns(self):
        """Persist patterns to disk."""
        patterns_file = self.storage_path / "patterns.json"
        data = [p.to_dict() for p in self.patterns.values()]

        with open(patterns_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_patterns(self):
        """Load patterns from disk."""
        patterns_file = self.storage_path / "patterns.json"

        if not patterns_file.exists():
            return

        try:
            with open(patterns_file, 'r') as f:
                data = json.load(f)

            for pattern_dict in data:
                pattern = Pattern.from_dict(pattern_dict)
                self.patterns[pattern.id] = pattern
        except Exception:
            pass  # Failed to load, start fresh

    def _save_insights(self):
        """Persist insights to disk."""
        insights_file = self.storage_path / "insights.json"
        data = [i.to_dict() for i in self.insights.values()]

        with open(insights_file, 'w') as f:
            json.dump(data, f, indent=2)

    def _load_insights(self):
        """Load insights from disk."""
        insights_file = self.storage_path / "insights.json"

        if not insights_file.exists():
            return

        try:
            with open(insights_file, 'r') as f:
                data = json.load(f)

            for insight_dict in data:
                insight = Insight.from_dict(insight_dict)
                self.insights[insight.id] = insight
        except Exception:
            pass  # Failed to load, start fresh
