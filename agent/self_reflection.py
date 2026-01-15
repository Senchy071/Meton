"""Self-Reflection Module for Meton.

This module enables agents to reflect on their responses, identify weaknesses,
and generate improved versions. Uses LLM-based analysis to score response quality
and suggest improvements.

Example:
    >>> from agent.self_reflection import SelfReflectionModule
    >>> from core.models import ModelManager
    >>>
    >>> config = {"enabled": True, "min_quality_threshold": 0.7, "max_iterations": 2}
    >>> reflection = SelfReflectionModule(model_manager, config)
    >>>
    >>> # Reflect on a response
    >>> result = reflection.reflect_on_response(query, response, context)
    >>> if result["should_improve"]:
    >>>     improved = reflection.improve_response(query, response, result)
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from core.models import ModelManager
from utils.logger import setup_logger


@dataclass
class ReflectionRecord:
    """Record of a single reflection event.

    Attributes:
        query: Original user query
        response: Agent's response
        quality_score: Calculated quality score (0.0-1.0)
        issues: List of identified issues
        suggestions: List of improvement suggestions
        improved: Whether response was improved
        timestamp: When reflection occurred
    """
    query: str
    response: str
    quality_score: float
    issues: List[str]
    suggestions: List[str]
    improved: bool = False
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


class SelfReflectionModule:
    """Enables agent to reflect on and improve its responses.

    The reflection module analyzes agent responses for quality issues,
    identifies specific problems, and generates improved responses when needed.

    Quality evaluation criteria:
    - Completeness: Addresses all parts of query
    - Clarity: Well-structured and easy to understand
    - Correctness: Proper use of tool results
    - Conciseness: Appropriate detail without verbosity

    Attributes:
        model_manager: Model manager instance
        config: Reflection configuration dictionary
        reflection_history: List of past reflections
        min_quality_threshold: Minimum acceptable quality score
        max_iterations: Maximum improvement attempts

    Example:
        >>> reflection = SelfReflectionModule(model_manager, config)
        >>> if reflection.should_reflect(query, response):
        >>>     result = reflection.reflect_on_response(query, response, context)
        >>>     if result["should_improve"]:
        >>>         improved = reflection.improve_response(query, response, result)
    """

    # Reflection prompt template
    REFLECTION_PROMPT = """Analyze this response for quality:

Query: {query}

Response: {response}

Context: {context}

Evaluate the response on these criteria:
1. Completeness - Does it fully address all parts of the query?
2. Clarity - Is it well-structured and easy to understand?
3. Correctness - Are tool results used properly? Is information accurate?
4. Conciseness - Is it appropriately detailed without unnecessary verbosity?

Output ONLY valid JSON in this exact format (no additional text):
{{
  "quality_score": 0.85,
  "issues": ["issue1", "issue2"],
  "suggestions": ["suggestion1", "suggestion2"]
}}

Possible issues: "incomplete_answer", "unclear_explanation", "unused_context", "too_verbose", "missing_code", "no_sources", "incorrect_info"

Quality score:
- 0.9-1.0: Excellent
- 0.7-0.9: Good
- 0.5-0.7: Needs improvement
- 0.0-0.5: Poor"""

    # Improvement prompt template
    IMPROVEMENT_PROMPT = """Improve this response based on reflection feedback:

Original Query: {query}

Original Response: {response}

Issues Found: {issues}

Suggestions: {suggestions}

Generate an improved response that:
1. Addresses all identified issues
2. Maintains the same information while improving presentation
3. Incorporates all suggestions
4. Is clear, complete, correct, and concise

Provide ONLY the improved response, no explanations or meta-commentary."""

    def __init__(self, model_manager: ModelManager, config: Dict, logging_config: Optional[Dict] = None):
        """Initialize the self-reflection module.

        Args:
            model_manager: Model manager instance
            config: Reflection configuration dictionary with:
                - enabled: Whether reflection is active
                - min_quality_threshold: Score below which to improve (default 0.7)
                - max_iterations: Maximum improvement attempts (default 2)
                - auto_reflect_on: Conditions for automatic reflection
            logging_config: Optional logging configuration dictionary
        """
        self.model_manager = model_manager
        self.config = config

        # Configuration parameters
        self.min_quality_threshold = config.get("min_quality_threshold", 0.7)
        self.max_iterations = config.get("max_iterations", 2)
        self.auto_reflect_on = config.get("auto_reflect_on", {})

        # Reflection history
        self.reflection_history: List[ReflectionRecord] = []

        # Logger
        self.logger = setup_logger(name="self_reflection", config=logging_config)

        if self.logger:
            self.logger.info("SelfReflectionModule initialized")
            self.logger.debug(f"Quality threshold: {self.min_quality_threshold}")
            self.logger.debug(f"Max iterations: {self.max_iterations}")

    def reflect_on_response(
        self,
        query: str,
        response: str,
        context: Dict
    ) -> Dict:
        """Analyze response quality and identify issues.

        Uses LLM to evaluate response on completeness, clarity,
        correctness, and conciseness. Identifies specific issues
        and generates improvement suggestions.

        Args:
            query: Original user query
            response: Agent's response to analyze
            context: Additional context (tool calls, conversation history, etc.)

        Returns:
            Dictionary with:
            - quality_score: float (0.0-1.0)
            - issues: List[str] of identified problems
            - suggestions: List[str] of improvement suggestions
            - should_improve: bool indicating if improvement needed

        Example:
            >>> result = reflection.reflect_on_response(query, response, context)
            >>> if result["should_improve"]:
            >>>     print(f"Score: {result['quality_score']}, Issues: {result['issues']}")
        """
        if self.logger:
            self.logger.debug(f"Reflecting on response for query: {query[:50]}...")

        # Format context for reflection
        context_str = self._format_context(context)

        # Build reflection prompt
        reflection_prompt = self.REFLECTION_PROMPT.format(
            query=query,
            response=response,
            context=context_str
        )

        try:
            # Get LLM analysis
            llm = self.model_manager.get_model("primary")
            llm_response = llm.invoke(reflection_prompt)

            # Parse JSON output
            reflection_data = self._parse_reflection_output(llm_response.content)

            # Determine if improvement needed
            quality_score = reflection_data.get("quality_score", 0.5)
            issues = reflection_data.get("issues", [])
            suggestions = reflection_data.get("suggestions", [])

            should_improve = (
                quality_score < self.min_quality_threshold or
                any(issue in ["incomplete_answer", "incorrect_info"] for issue in issues)
            )

            # Record reflection
            record = ReflectionRecord(
                query=query,
                response=response,
                quality_score=quality_score,
                issues=issues,
                suggestions=suggestions,
                improved=False
            )
            self.reflection_history.append(record)

            if self.logger:
                self.logger.info(f"Reflection complete: score={quality_score:.2f}, improve={should_improve}")

            return {
                "quality_score": quality_score,
                "issues": issues,
                "suggestions": suggestions,
                "should_improve": should_improve
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Reflection failed: {e}")

            # Fallback: assume decent quality, no improvement
            return {
                "quality_score": 0.75,
                "issues": [],
                "suggestions": [],
                "should_improve": False
            }

    def improve_response(
        self,
        query: str,
        original_response: str,
        reflection: Dict
    ) -> str:
        """Generate improved response based on reflection feedback.

        Uses LLM to rewrite response addressing identified issues
        and incorporating suggestions.

        Args:
            query: Original user query
            original_response: Original agent response
            reflection: Reflection results from reflect_on_response()

        Returns:
            Improved response string

        Example:
            >>> improved = reflection.improve_response(query, response, reflection_result)
        """
        if self.logger:
            self.logger.debug(f"Improving response with {len(reflection['issues'])} issues")

        # Build improvement prompt
        issues_str = ", ".join(reflection["issues"])
        suggestions_str = "\n".join([f"- {s}" for s in reflection["suggestions"]])

        improvement_prompt = self.IMPROVEMENT_PROMPT.format(
            query=query,
            response=original_response,
            issues=issues_str,
            suggestions=suggestions_str
        )

        try:
            # Get improved response from LLM
            llm = self.model_manager.get_model("primary")
            llm_response = llm.invoke(improvement_prompt)

            improved_response = llm_response.content.strip()

            # Update reflection history
            if self.reflection_history:
                self.reflection_history[-1].improved = True

            if self.logger:
                self.logger.info("Response improved successfully")

            return improved_response

        except Exception as e:
            if self.logger:
                self.logger.error(f"Improvement failed: {e}")

            # Fallback: return original
            return original_response

    def should_reflect(self, query: str, response: str, context: Optional[Dict] = None) -> bool:
        """Determine if reflection should be performed on this response.

        Criteria for reflection:
        - Complex queries (multiple parts, analysis needed)
        - Long responses (>500 words)
        - Multiple tool usage (>2 tools)
        - Specific query types (analyze, review, compare)
        - Auto-reflect config conditions

        Args:
            query: User query
            response: Agent response
            context: Optional context with tool usage info

        Returns:
            True if reflection should be performed, False otherwise

        Example:
            >>> if reflection.should_reflect(query, response, context):
            >>>     result = reflection.reflect_on_response(query, response, context)
        """
        query_lower = query.lower()

        # Check for complex queries (multiple parts)
        complex_indicators = ["and", "or", "then"]
        complex_count = sum(query_lower.count(word) for word in complex_indicators)
        if complex_count > 3:
            if self.logger:
                self.logger.debug("Should reflect: complex query detected")
            return True

        # Check for analysis queries
        analysis_keywords = ["analyze", "review", "compare", "evaluate", "investigate"]
        if any(query_lower.startswith(keyword) for keyword in analysis_keywords):
            if self.logger:
                self.logger.debug("Should reflect: analysis query detected")
            return True

        # Check response length (>500 words)
        word_count = len(response.split())
        if word_count > 500:
            if self.logger:
                self.logger.debug(f"Should reflect: long response ({word_count} words)")
            return True

        # Check tool usage (if context provided)
        if context:
            tool_calls = context.get("tool_calls", [])
            if len(tool_calls) > 2:
                if self.logger:
                    self.logger.debug(f"Should reflect: multiple tool usage ({len(tool_calls)} tools)")
                return True

        # Check auto-reflect config
        if self.auto_reflect_on.get("complex_queries") and complex_count > 0:
            return True
        if self.auto_reflect_on.get("multi_tool_usage") and context:
            if len(context.get("tool_calls", [])) > 1:
                return True
        if self.auto_reflect_on.get("long_responses") and word_count > 300:
            return True

        return False

    def get_reflection_stats(self) -> Dict:
        """Get statistics about reflection history.

        Returns:
            Dictionary with:
            - total_reflections: Total number of reflections
            - average_quality_score: Mean quality score
            - common_issues: Most frequent issues
            - improvement_rate: Percentage of responses improved
            - score_distribution: Quality score ranges

        Example:
            >>> stats = reflection.get_reflection_stats()
            >>> print(f"Average quality: {stats['average_quality_score']:.2f}")
        """
        if not self.reflection_history:
            return {
                "total_reflections": 0,
                "average_quality_score": 0.0,
                "common_issues": {},
                "improvement_rate": 0.0,
                "score_distribution": {}
            }

        # Calculate statistics
        total = len(self.reflection_history)
        avg_score = sum(r.quality_score for r in self.reflection_history) / total
        improved_count = sum(1 for r in self.reflection_history if r.improved)
        improvement_rate = (improved_count / total) * 100

        # Count issues
        issue_counts: Dict[str, int] = {}
        for record in self.reflection_history:
            for issue in record.issues:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1

        # Sort by frequency
        common_issues = dict(sorted(issue_counts.items(), key=lambda x: x[1], reverse=True))

        # Score distribution
        score_ranges = {
            "excellent (0.9-1.0)": 0,
            "good (0.7-0.9)": 0,
            "needs_improvement (0.5-0.7)": 0,
            "poor (0.0-0.5)": 0
        }
        for record in self.reflection_history:
            score = record.quality_score
            if score >= 0.9:
                score_ranges["excellent (0.9-1.0)"] += 1
            elif score >= 0.7:
                score_ranges["good (0.7-0.9)"] += 1
            elif score >= 0.5:
                score_ranges["needs_improvement (0.5-0.7)"] += 1
            else:
                score_ranges["poor (0.0-0.5)"] += 1

        return {
            "total_reflections": total,
            "average_quality_score": avg_score,
            "common_issues": common_issues,
            "improvement_rate": improvement_rate,
            "score_distribution": score_ranges
        }

    def _format_context(self, context: Dict) -> str:
        """Format context dictionary for reflection prompt.

        Args:
            context: Context dictionary with tool calls, etc.

        Returns:
            Formatted context string
        """
        if not context:
            return "No additional context"

        parts = []

        # Tool calls
        if "tool_calls" in context:
            tool_calls = context["tool_calls"]
            if tool_calls:
                parts.append(f"Tools used: {len(tool_calls)}")
                for i, call in enumerate(tool_calls[:3], 1):  # Limit to 3
                    tool_name = call.get("tool", "unknown")
                    parts.append(f"  {i}. {tool_name}")

        # Other context
        for key, value in context.items():
            if key != "tool_calls" and isinstance(value, (str, int, float)):
                parts.append(f"{key}: {value}")

        return "\n".join(parts) if parts else "No additional context"

    def _parse_reflection_output(self, output: str) -> Dict:
        """Parse JSON output from LLM reflection.

        Handles various formats:
        - Pure JSON
        - JSON in markdown code blocks
        - JSON with extra text

        Args:
            output: LLM output string

        Returns:
            Parsed dictionary with quality_score, issues, suggestions

        Raises:
            ValueError: If no valid JSON found
        """
        # Try to extract JSON from output
        # Look for JSON object pattern
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', output, re.DOTALL)

        if json_match:
            json_str = json_match.group(0)
            try:
                data = json.loads(json_str)

                # Validate required fields
                if "quality_score" not in data:
                    data["quality_score"] = 0.5
                if "issues" not in data:
                    data["issues"] = []
                if "suggestions" not in data:
                    data["suggestions"] = []

                # Validate quality score range
                data["quality_score"] = max(0.0, min(1.0, data["quality_score"]))

                return data

            except json.JSONDecodeError:
                pass

        # Fallback: return default values
        if self.logger:
            self.logger.warning("Failed to parse reflection output, using defaults")

        return {
            "quality_score": 0.5,
            "issues": ["parsing_error"],
            "suggestions": ["Unable to parse reflection output"]
        }

    def clear_history(self) -> None:
        """Clear reflection history."""
        self.reflection_history = []
        if self.logger:
            self.logger.info("Reflection history cleared")

    def __repr__(self) -> str:
        """String representation of SelfReflectionModule.

        Returns:
            Module info with reflection count
        """
        return (
            f"<SelfReflectionModule("
            f"reflections={len(self.reflection_history)}, "
            f"threshold={self.min_quality_threshold})>"
        )
