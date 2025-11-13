"""Iterative Improvement Loop for Meton.

This module enables multi-iteration refinement of responses through continuous
reflection and improvement cycles. Uses the self-reflection module to analyze
quality and generate progressively better responses until satisfaction.

Example:
    >>> from agent.iterative_improvement import IterativeImprovementLoop
    >>> from agent.self_reflection import SelfReflectionModule
    >>> from core.models import ModelManager
    >>>
    >>> config = {"enabled": True, "max_iterations": 3, "quality_threshold": 0.85}
    >>> loop = IterativeImprovementLoop(model_manager, reflection_module, config)
    >>>
    >>> # Iteratively improve a response
    >>> result = loop.iterate_until_satisfied(query, initial_response, context)
    >>> print(f"Final quality: {result['final_score']}, Iterations: {result['iterations']}")
"""

from typing import Dict, List, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

from core.models import ModelManager
from agent.self_reflection import SelfReflectionModule
from utils.logger import setup_logger


@dataclass
class IterationRecord:
    """Record of a single iteration in the improvement loop.

    Attributes:
        iteration: Iteration number (0-indexed)
        response: Response text at this iteration
        quality_score: Quality score from reflection
        issues: Issues identified at this iteration
        suggestions: Improvement suggestions
        timestamp: When iteration occurred
    """
    iteration: int
    response: str
    quality_score: float
    issues: List[str]
    suggestions: List[str]
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())


@dataclass
class ImprovementSession:
    """Complete record of an improvement session.

    Attributes:
        query: Original user query
        initial_response: Starting response
        final_response: Final improved response
        iterations: Number of iterations performed
        improvement_path: List of iteration records
        converged: Whether loop converged (vs hitting limits)
        initial_score: Starting quality score
        final_score: Final quality score
        improvement: Total improvement (final - initial)
    """
    query: str
    initial_response: str
    final_response: str
    iterations: int
    improvement_path: List[IterationRecord]
    converged: bool
    initial_score: float
    final_score: float
    improvement: float


class IterativeImprovementLoop:
    """Enables multi-iteration refinement of responses.

    The improvement loop continuously refines responses through reflection
    and improvement cycles until reaching satisfactory quality or convergence.

    Stop conditions (in priority order):
    1. Max iterations reached (hard limit)
    2. Quality excellent (score > threshold, default 0.85)
    3. Converged (improvement < convergence_threshold)
    4. No issues remaining
    5. Quality declining (current < previous)

    Attributes:
        model_manager: Model manager instance
        reflection_module: Self-reflection module instance
        config: Iterative improvement configuration
        improvement_history: List of past improvement sessions
        max_iterations: Maximum iterations allowed
        quality_threshold: Quality score to reach
        convergence_threshold: Min improvement to continue
        convergence_window: Number of scores to compare

    Example:
        >>> loop = IterativeImprovementLoop(model_manager, reflection, config)
        >>> result = loop.iterate_until_satisfied(query, response, context)
        >>> print(f"Improved from {result['initial_score']:.2f} to {result['final_score']:.2f}")
    """

    # Iteration prompt template
    ITERATION_PROMPT = """This is iteration {iteration} of improving the response.

Original Query: {query}

Current Response:
{response}

Previous Issues Identified: {issues}

Suggestions for Improvement:
{suggestions}

Generate an improved response that specifically addresses these issues.

Focus Areas for This Iteration:
{focus_areas}

Important:
- Maintain all correct information from the current response
- Fix only the identified issues
- Ensure completeness, clarity, correctness, and conciseness
- Do not add unnecessary verbosity

Provide ONLY the improved response, no meta-commentary."""

    def __init__(
        self,
        model_manager: ModelManager,
        reflection_module: SelfReflectionModule,
        config: Dict
    ):
        """Initialize the iterative improvement loop.

        Args:
            model_manager: Model manager instance
            reflection_module: Self-reflection module instance
            config: Configuration dictionary with:
                - enabled: Whether iterative improvement is active
                - max_iterations: Maximum iterations (default 3)
                - quality_threshold: Score to reach (default 0.85)
                - convergence_threshold: Min improvement (default 0.05)
                - convergence_window: Scores to compare (default 2)
        """
        self.model_manager = model_manager
        self.reflection_module = reflection_module
        self.config = config

        # Configuration parameters
        self.max_iterations = config.get("max_iterations", 3)
        self.quality_threshold = config.get("quality_threshold", 0.85)
        self.convergence_threshold = config.get("convergence_threshold", 0.05)
        self.convergence_window = config.get("convergence_window", 2)

        # Improvement history
        self.improvement_history: List[ImprovementSession] = []

        # Logger
        self.logger = setup_logger(name="iterative_improvement", console_output=False)

        if self.logger:
            self.logger.info("IterativeImprovementLoop initialized")
            self.logger.debug(f"Max iterations: {self.max_iterations}")
            self.logger.debug(f"Quality threshold: {self.quality_threshold}")
            self.logger.debug(f"Convergence threshold: {self.convergence_threshold}")

    def iterate_until_satisfied(
        self,
        query: str,
        initial_response: str,
        context: Dict,
        max_iterations: Optional[int] = None
    ) -> Dict:
        """Iteratively improve response until satisfied.

        Main entry point for the improvement loop. Continuously refines
        the response through reflection and improvement cycles.

        Args:
            query: Original user query
            initial_response: Initial response to improve
            context: Additional context (tool calls, etc.)
            max_iterations: Optional override for max iterations

        Returns:
            Dictionary with:
            - final_response: str - Final improved response
            - iterations: int - Number of iterations performed
            - improvement_path: List[Dict] - Details of each iteration
            - converged: bool - Whether loop converged naturally
            - initial_score: float - Starting quality score
            - final_score: float - Final quality score
            - improvement: float - Total quality improvement

        Example:
            >>> result = loop.iterate_until_satisfied(query, response, context)
            >>> print(f"Iterations: {result['iterations']}, Improvement: +{result['improvement']:.2f}")
        """
        if max_iterations is None:
            max_iterations = self.max_iterations

        if self.logger:
            self.logger.info(f"Starting improvement loop for query: {query[:50]}...")

        # Track iterations
        iteration_path: List[IterationRecord] = []
        quality_scores: List[float] = []
        current_response = initial_response
        converged = False

        # Iteration 0: Analyze initial response
        initial_reflection = self.reflection_module.reflect_on_response(
            query, current_response, context
        )
        initial_score = initial_reflection["quality_score"]
        quality_scores.append(initial_score)

        iteration_path.append(IterationRecord(
            iteration=0,
            response=current_response,
            quality_score=initial_score,
            issues=initial_reflection["issues"],
            suggestions=initial_reflection["suggestions"]
        ))

        if self.logger:
            self.logger.debug(f"Initial quality: {initial_score:.2f}")

        # Check if already excellent
        if initial_score >= self.quality_threshold:
            if self.logger:
                self.logger.info("Initial response already excellent, no improvement needed")

            session = ImprovementSession(
                query=query,
                initial_response=initial_response,
                final_response=current_response,
                iterations=0,
                improvement_path=iteration_path,
                converged=True,
                initial_score=initial_score,
                final_score=initial_score,
                improvement=0.0
            )
            self.improvement_history.append(session)

            return {
                "final_response": current_response,
                "iterations": 0,
                "improvement_path": [self._iteration_to_dict(rec) for rec in iteration_path],
                "converged": True,
                "initial_score": initial_score,
                "final_score": initial_score,
                "improvement": 0.0
            }

        # Improvement loop
        for iteration in range(1, max_iterations + 1):
            if self.logger:
                self.logger.debug(f"Starting iteration {iteration}")

            # Check if should continue
            last_reflection = initial_reflection if iteration == 1 else reflection
            if not self._should_continue_iteration(iteration, last_reflection, quality_scores):
                converged = True
                if self.logger:
                    self.logger.info(f"Stopping at iteration {iteration}: conditions met")
                break

            # Generate improvement
            improved_response = self._improve_iteration(
                query, current_response, last_reflection, iteration
            )

            # Reflect on improved response
            reflection = self.reflection_module.reflect_on_response(
                query, improved_response, context
            )
            current_score = reflection["quality_score"]
            quality_scores.append(current_score)

            # Track iteration
            iteration_path.append(IterationRecord(
                iteration=iteration,
                response=improved_response,
                quality_score=current_score,
                issues=reflection["issues"],
                suggestions=reflection["suggestions"]
            ))

            if self.logger:
                self.logger.debug(f"Iteration {iteration} quality: {current_score:.2f}")

            # Check for quality decline
            if current_score < quality_scores[-2]:
                if self.logger:
                    self.logger.warning(f"Quality declined at iteration {iteration}, reverting")
                # Revert to previous iteration
                iteration_path.pop()
                quality_scores.pop()
                break

            # Update current response
            current_response = improved_response

            # Check if reached threshold
            if current_score >= self.quality_threshold:
                converged = True
                if self.logger:
                    self.logger.info(f"Quality threshold reached at iteration {iteration}")
                break

        # Final scores
        final_score = quality_scores[-1]
        improvement = final_score - initial_score

        # Create session record
        session = ImprovementSession(
            query=query,
            initial_response=initial_response,
            final_response=current_response,
            iterations=len(iteration_path) - 1,  # Don't count iteration 0
            improvement_path=iteration_path,
            converged=converged,
            initial_score=initial_score,
            final_score=final_score,
            improvement=improvement
        )
        self.improvement_history.append(session)

        if self.logger:
            self.logger.info(
                f"Improvement loop complete: {session.iterations} iterations, "
                f"+{improvement:.2f} improvement"
            )

        return {
            "final_response": current_response,
            "iterations": session.iterations,
            "improvement_path": [self._iteration_to_dict(rec) for rec in iteration_path],
            "converged": converged,
            "initial_score": initial_score,
            "final_score": final_score,
            "improvement": improvement
        }

    def _should_continue_iteration(
        self,
        iteration: int,
        reflection: Dict,
        previous_scores: List[float]
    ) -> bool:
        """Determine if another iteration is needed.

        Stop conditions (checked in order):
        1. Max iterations reached
        2. Quality excellent (> threshold)
        3. Converged (no meaningful improvement)
        4. No issues remaining

        Args:
            iteration: Current iteration number
            reflection: Last reflection result
            previous_scores: List of previous quality scores

        Returns:
            True if should continue, False if should stop
        """
        # Check max iterations (will be checked before calling, but safety check)
        if iteration > self.max_iterations:
            if self.logger:
                self.logger.debug("Stop: max iterations reached")
            return False

        # Check quality threshold
        current_score = previous_scores[-1]
        if current_score >= self.quality_threshold:
            if self.logger:
                self.logger.debug(f"Stop: quality threshold reached ({current_score:.2f})")
            return False

        # Check convergence
        if self._detect_convergence(previous_scores):
            if self.logger:
                self.logger.debug("Stop: converged")
            return False

        # Check if issues remain
        if not reflection.get("issues", []):
            if self.logger:
                self.logger.debug("Stop: no issues remaining")
            return False

        # Continue iterating
        return True

    def _detect_convergence(self, scores: List[float], window: Optional[int] = None) -> bool:
        """Check if quality scores have plateaued.

        Compares the most recent improvement to detect if progress
        has stalled (< convergence_threshold).

        Args:
            scores: List of quality scores
            window: Number of scores to check (default: convergence_window)

        Returns:
            True if converged, False if still improving

        Example:
            >>> scores = [0.65, 0.72, 0.74]
            >>> _detect_convergence(scores)  # 0.74 - 0.72 = 0.02 < 0.05
            True
        """
        if window is None:
            window = self.convergence_window

        # Need at least 2 scores to compare
        if len(scores) < 2:
            return False

        # Calculate most recent improvement (last step)
        improvement = scores[-1] - scores[-2]

        # Check if improvement is below threshold
        converged = improvement < self.convergence_threshold

        if self.logger and converged:
            self.logger.debug(
                f"Convergence detected: improvement {improvement:.3f} < threshold {self.convergence_threshold}"
            )

        return converged

    def _improve_iteration(
        self,
        query: str,
        response: str,
        reflection: Dict,
        iteration: int
    ) -> str:
        """Generate improved response for current iteration.

        Args:
            query: Original user query
            response: Current response to improve
            reflection: Reflection results with issues/suggestions
            iteration: Current iteration number

        Returns:
            Improved response string
        """
        # Generate iteration-specific prompt
        prompt = self._generate_improvement_prompt(query, response, reflection, iteration)

        try:
            # Get improved response from LLM
            llm = self.model_manager.get_model("primary")
            llm_response = llm.invoke(prompt)

            improved = llm_response.content.strip()

            if self.logger:
                self.logger.debug(f"Generated improved response for iteration {iteration}")

            return improved

        except Exception as e:
            if self.logger:
                self.logger.error(f"Improvement generation failed: {e}")

            # Fallback: return current response
            return response

    def _generate_improvement_prompt(
        self,
        query: str,
        response: str,
        reflection: Dict,
        iteration: int
    ) -> str:
        """Create iteration-specific improvement prompt.

        Args:
            query: Original user query
            response: Current response
            reflection: Reflection with issues/suggestions
            iteration: Current iteration number

        Returns:
            Formatted prompt string
        """
        issues = reflection.get("issues", [])
        suggestions = reflection.get("suggestions", [])

        # Format issues and suggestions
        issues_str = ", ".join(issues) if issues else "None"
        suggestions_str = "\n".join([f"- {s}" for s in suggestions])

        # Determine focus areas based on issues
        focus_areas = []
        if "incomplete_answer" in issues:
            focus_areas.append("Address all parts of the query completely")
        if "unclear_explanation" in issues:
            focus_areas.append("Improve structure and clarity")
        if "unused_context" in issues:
            focus_areas.append("Incorporate all relevant context")
        if "too_verbose" in issues:
            focus_areas.append("Be more concise")
        if "missing_code" in issues:
            focus_areas.append("Add code examples")
        if "no_sources" in issues:
            focus_areas.append("Cite sources")
        if "incorrect_info" in issues:
            focus_areas.append("Correct factual errors")

        focus_str = "\n".join([f"- {f}" for f in focus_areas]) if focus_areas else "- General quality improvement"

        # Build prompt
        prompt = self.ITERATION_PROMPT.format(
            iteration=iteration,
            query=query,
            response=response,
            issues=issues_str,
            suggestions=suggestions_str,
            focus_areas=focus_str
        )

        return prompt

    def _iteration_to_dict(self, record: IterationRecord) -> Dict:
        """Convert IterationRecord to dictionary.

        Args:
            record: IterationRecord instance

        Returns:
            Dictionary representation
        """
        return {
            "iteration": record.iteration,
            "quality_score": record.quality_score,
            "issues": record.issues,
            "suggestions": record.suggestions,
            "timestamp": record.timestamp
        }

    def get_improvement_stats(self) -> Dict:
        """Get statistics about improvement sessions.

        Returns:
            Dictionary with:
            - total_sessions: Total improvement sessions
            - average_iterations: Mean iterations per session
            - average_improvement: Mean quality improvement
            - convergence_rate: Percentage of sessions that converged
            - max_improvement: Largest quality improvement seen
            - sessions_by_iterations: Distribution of iteration counts

        Example:
            >>> stats = loop.get_improvement_stats()
            >>> print(f"Avg iterations: {stats['average_iterations']:.1f}")
        """
        if not self.improvement_history:
            return {
                "total_sessions": 0,
                "average_iterations": 0.0,
                "average_improvement": 0.0,
                "convergence_rate": 0.0,
                "max_improvement": 0.0,
                "sessions_by_iterations": {}
            }

        total = len(self.improvement_history)
        avg_iterations = sum(s.iterations for s in self.improvement_history) / total
        avg_improvement = sum(s.improvement for s in self.improvement_history) / total
        converged_count = sum(1 for s in self.improvement_history if s.converged)
        convergence_rate = (converged_count / total) * 100
        max_improvement = max(s.improvement for s in self.improvement_history)

        # Distribution of iterations
        iteration_counts: Dict[int, int] = {}
        for session in self.improvement_history:
            count = session.iterations
            iteration_counts[count] = iteration_counts.get(count, 0) + 1

        return {
            "total_sessions": total,
            "average_iterations": avg_iterations,
            "average_improvement": avg_improvement,
            "convergence_rate": convergence_rate,
            "max_improvement": max_improvement,
            "sessions_by_iterations": dict(sorted(iteration_counts.items()))
        }

    def clear_history(self) -> None:
        """Clear improvement history."""
        self.improvement_history = []
        if self.logger:
            self.logger.info("Improvement history cleared")

    def __repr__(self) -> str:
        """String representation of IterativeImprovementLoop.

        Returns:
            Loop info with session count
        """
        return (
            f"<IterativeImprovementLoop("
            f"sessions={len(self.improvement_history)}, "
            f"max_iterations={self.max_iterations}, "
            f"threshold={self.quality_threshold})>"
        )
