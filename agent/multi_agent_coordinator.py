"""Multi-Agent Coordinator for Meton.

This module coordinates multiple specialized agents to handle complex tasks through:
- Task decomposition (Planner agent)
- Subtask execution (Executor agent)
- Result validation (Reviewer agent)
- Result synthesis (Synthesizer agent)

Example:
    >>> from agent.multi_agent_coordinator import MultiAgentCoordinator
    >>> from core.config import ConfigLoader
    >>> from core.models import ModelManager
    >>> from core.conversation import ConversationManager
    >>>
    >>> config = ConfigLoader()
    >>> model_manager = ModelManager(config)
    >>> conversation = ConversationManager(config)
    >>> tools = [...]
    >>>
    >>> coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config.config.multi_agent)
    >>> result = coordinator.coordinate_task("Find and review authentication code")
"""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from copy import deepcopy

from core.agent import MetonAgent
from core.models import ModelManager
from core.conversation import ConversationManager
from langchain.tools import BaseTool
from utils.logger import setup_logger


@dataclass
class SubTask:
    """Represents a subtask in the execution plan.

    Attributes:
        id: Unique subtask identifier
        task: Task description
        depends_on: List of subtask IDs this depends on
        result: Execution result (populated after execution)
        status: Execution status (pending, executing, completed, failed)
    """
    id: int
    task: str
    depends_on: List[int]
    result: Optional[Any] = None
    status: str = "pending"


class MultiAgentCoordinator:
    """Coordinates multiple specialized agents for complex tasks.

    The coordinator manages four types of agents:
    - Planner: Decomposes tasks into subtasks
    - Executor: Executes individual subtasks
    - Reviewer: Validates results
    - Synthesizer: Combines results into final answer

    Attributes:
        model_manager: Model manager instance
        conversation: Conversation manager instance
        tools: List of available tools
        config: Multi-agent configuration dictionary
        agents: Dictionary of specialized agent instances
        max_subtasks: Maximum number of subtasks allowed
        max_revisions: Maximum revision attempts per subtask

    Example:
        >>> coordinator = MultiAgentCoordinator(model_manager, conversation, tools, config)
        >>> result = coordinator.coordinate_task("Compare our API with FastAPI")
        >>> print(result["result"])
    """

    def __init__(
        self,
        model_manager: ModelManager,
        conversation: ConversationManager,
        tools: List[BaseTool],
        config: Dict
    ):
        """Initialize the multi-agent coordinator.

        Args:
            model_manager: Model manager instance
            conversation: Conversation manager instance
            tools: List of available tools
            config: Multi-agent configuration dictionary
        """
        self.model_manager = model_manager
        self.conversation = conversation
        self.tools = tools
        self.config = config

        # Configuration parameters
        self.max_subtasks = config.get("max_subtasks", 10)
        self.max_revisions = config.get("max_revisions", 2)
        self.parallel_execution = config.get("parallel_execution", False)

        # Initialize specialized agents
        self.agents: Dict[str, MetonAgent] = {}
        self.logger = setup_logger(name="multi_agent_coordinator", console_output=False)

        self._initialize_agents()

        if self.logger:
            self.logger.info("MultiAgentCoordinator initialized")
            self.logger.debug(f"Max subtasks: {self.max_subtasks}")
            self.logger.debug(f"Max revisions: {self.max_revisions}")

    def _initialize_agents(self) -> None:
        """Initialize the four specialized agents.

        Creates:
        - Planner: Task decomposition specialist
        - Executor: Task execution specialist
        - Reviewer: Result validation specialist
        - Synthesizer: Result aggregation specialist
        """
        # For multi-agent coordination, we need separate conversation contexts
        # to prevent agents from seeing each other's reasoning
        from core.config import ConfigLoader

        # Get the main config
        config_loader = ConfigLoader()

        # Planner Agent - Task decomposition
        planner_prompt = """You are a task planning specialist. Your role is to break down complex tasks into concrete, executable subtasks.

When given a task, analyze it and create a detailed execution plan.

Output ONLY valid JSON in this exact format (no additional text):
[
  {"id": 1, "task": "description of first subtask", "depends_on": []},
  {"id": 2, "task": "description of second subtask", "depends_on": [1]},
  {"id": 3, "task": "description of third subtask", "depends_on": [1, 2]}
]

Rules:
- Each subtask must be concrete and actionable
- Use depends_on to specify dependencies (subtask IDs that must complete first)
- Keep subtasks focused and specific
- Maximum 10 subtasks
- Output ONLY the JSON array, nothing else"""

        # Executor Agent - Task execution
        executor_prompt = """You are a task execution specialist. Your role is to execute specific subtasks using available tools.

When given a subtask:
1. Understand exactly what needs to be done
2. Use the appropriate tools to complete it
3. Provide a clear, concise result

Focus on completing the specific task accurately. Do not plan or decompose - just execute."""

        # Reviewer Agent - Result validation
        reviewer_prompt = """You are a quality reviewer. Your role is to validate task results for correctness and completeness.

When given results to review:
1. Check if the results fully address the requirements
2. Identify any errors, omissions, or quality issues
3. Decide if revisions are needed

Output ONLY valid JSON in this exact format (no additional text):
{
  "approved": true/false,
  "feedback": "detailed feedback about the results",
  "revisions_needed": [list of subtask IDs that need revision]
}

Be thorough but fair in your assessment."""

        # Synthesizer Agent - Result aggregation
        synthesizer_prompt = """You are a result synthesizer. Your role is to combine subtask results into a coherent final answer.

When given subtask results:
1. Integrate all results logically
2. Create a comprehensive response
3. Ensure the answer directly addresses the original query

Provide a well-structured, complete response that synthesizes all information."""

        # Create agent instances
        # Note: We use verbose=False to avoid cluttering output
        self.agents["planner"] = MetonAgent(
            config=config_loader,
            model_manager=self.model_manager,
            conversation=self.conversation,
            tools=[],  # Planner doesn't use tools, only reasoning
            verbose=False
        )

        self.agents["executor"] = MetonAgent(
            config=config_loader,
            model_manager=self.model_manager,
            conversation=self.conversation,
            tools=self.tools,  # Executor has full tool access
            verbose=False
        )

        self.agents["reviewer"] = MetonAgent(
            config=config_loader,
            model_manager=self.model_manager,
            conversation=self.conversation,
            tools=[],  # Reviewer doesn't use tools, only reasoning
            verbose=False
        )

        self.agents["synthesizer"] = MetonAgent(
            config=config_loader,
            model_manager=self.model_manager,
            conversation=self.conversation,
            tools=[],  # Synthesizer doesn't use tools, only reasoning
            verbose=False
        )

        # Store specialized prompts for later injection
        self._agent_prompts = {
            "planner": planner_prompt,
            "executor": executor_prompt,
            "reviewer": reviewer_prompt,
            "synthesizer": synthesizer_prompt
        }

        if self.logger:
            self.logger.info("Initialized 4 specialized agents")

    def coordinate_task(self, user_query: str) -> Dict:
        """Coordinate multiple agents to complete a complex task.

        Workflow:
        1. Plan: Decompose task into subtasks
        2. Execute: Run subtasks respecting dependencies
        3. Review: Validate results
        4. Revise: Re-execute failed subtasks (if needed)
        5. Synthesize: Combine results into final answer

        Args:
            user_query: The user's original query

        Returns:
            Dictionary with:
            - result: Final synthesized answer
            - steps: List of execution steps
            - success: Whether coordination succeeded
            - subtasks: List of subtasks (for debugging)

        Example:
            >>> result = coordinator.coordinate_task("Find auth code and review it")
            >>> print(result["result"])
        """
        if self.logger:
            self.logger.info(f"Coordinating task: {user_query}")

        execution_steps = []

        try:
            # Step 1: Plan the task
            if self.logger:
                self.logger.debug("Step 1: Planning task")

            subtasks = self._plan_task(user_query)
            execution_steps.append({
                "step": "planning",
                "subtask_count": len(subtasks),
                "subtasks": [{"id": st.id, "task": st.task} for st in subtasks]
            })

            # Step 2: Execute subtasks
            if self.logger:
                self.logger.debug(f"Step 2: Executing {len(subtasks)} subtasks")

            results = self._execute_subtasks(subtasks)
            execution_steps.append({
                "step": "execution",
                "completed": len([r for r in results.values() if r is not None])
            })

            # Step 3: Review results
            if self.logger:
                self.logger.debug("Step 3: Reviewing results")

            review = self._review_results(results, user_query)
            execution_steps.append({
                "step": "review",
                "approved": review["approved"],
                "revisions_needed": len(review["revisions_needed"])
            })

            # Step 4: Handle revisions if needed
            if not review["approved"] and review["revisions_needed"]:
                if self.logger:
                    self.logger.debug(f"Step 4: Handling {len(review['revisions_needed'])} revisions")

                results = self._handle_revisions(
                    review["revisions_needed"],
                    results,
                    subtasks,
                    review["feedback"]
                )
                execution_steps.append({
                    "step": "revision",
                    "revised": len(review["revisions_needed"])
                })

            # Step 5: Synthesize final answer
            if self.logger:
                self.logger.debug("Step 5: Synthesizing results")

            final_answer = self._synthesize_results(results, user_query)
            execution_steps.append({
                "step": "synthesis",
                "success": True
            })

            return {
                "result": final_answer,
                "steps": execution_steps,
                "success": True,
                "subtasks": [
                    {"id": st.id, "task": st.task, "status": st.status}
                    for st in subtasks
                ]
            }

        except Exception as e:
            if self.logger:
                self.logger.error(f"Coordination failed: {e}")

            return {
                "result": f"Multi-agent coordination failed: {str(e)}",
                "steps": execution_steps,
                "success": False,
                "error": str(e)
            }

    def _plan_task(self, query: str) -> List[SubTask]:
        """Use Planner agent to decompose task into subtasks.

        Args:
            query: User's original query

        Returns:
            List of SubTask objects

        Raises:
            ValueError: If planning fails or produces invalid output
        """
        planner = self.agents["planner"]

        # Inject specialized prompt
        planning_query = f"{self._agent_prompts['planner']}\n\nTask to decompose:\n{query}"

        # Run planner agent
        result = planner.run(planning_query)
        output = result.get("output", "")

        if self.logger:
            self.logger.debug(f"Planner output: {output[:200]}...")

        # Parse JSON output
        try:
            # Extract JSON from output (in case there's extra text)
            json_match = re.search(r'\[.*\]', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                subtask_dicts = json.loads(json_str)
            else:
                raise ValueError("No JSON array found in planner output")

            # Validate and create SubTask objects
            if len(subtask_dicts) > self.max_subtasks:
                raise ValueError(f"Too many subtasks: {len(subtask_dicts)} (max: {self.max_subtasks})")

            subtasks = []
            for st_dict in subtask_dicts:
                subtask = SubTask(
                    id=st_dict["id"],
                    task=st_dict["task"],
                    depends_on=st_dict.get("depends_on", [])
                )
                subtasks.append(subtask)

            if self.logger:
                self.logger.info(f"Planned {len(subtasks)} subtasks")

            return subtasks

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            if self.logger:
                self.logger.error(f"Failed to parse planner output: {e}")

            # Fallback: Create a single subtask
            return [SubTask(id=1, task=query, depends_on=[])]

    def _execute_subtasks(self, subtasks: List[SubTask]) -> Dict[int, Any]:
        """Execute subtasks respecting dependencies.

        Executes subtasks in order, ensuring dependencies are completed first.
        Uses Executor agent for each subtask.

        Args:
            subtasks: List of SubTask objects to execute

        Returns:
            Dictionary mapping subtask ID to result
        """
        results: Dict[int, Any] = {}
        executor = self.agents["executor"]

        # Track completed subtasks
        completed = set()

        # Execute in dependency order
        max_iterations = len(subtasks) * 2  # Prevent infinite loops
        iteration = 0

        while len(completed) < len(subtasks) and iteration < max_iterations:
            iteration += 1

            for subtask in subtasks:
                # Skip if already completed
                if subtask.id in completed:
                    continue

                # Check if dependencies are met
                deps_met = all(dep_id in completed for dep_id in subtask.depends_on)

                if deps_met:
                    if self.logger:
                        self.logger.debug(f"Executing subtask {subtask.id}: {subtask.task}")

                    subtask.status = "executing"

                    # Build context from dependencies
                    context = ""
                    if subtask.depends_on:
                        context = "\n\nPrevious results:\n"
                        for dep_id in subtask.depends_on:
                            context += f"Subtask {dep_id}: {results.get(dep_id, 'N/A')}\n"

                    # Execute subtask
                    execution_query = f"{self._agent_prompts['executor']}\n\nSubtask: {subtask.task}{context}"

                    try:
                        result = executor.run(execution_query)
                        subtask.result = result.get("output", "")
                        subtask.status = "completed"
                        results[subtask.id] = subtask.result
                        completed.add(subtask.id)

                        if self.logger:
                            self.logger.debug(f"Subtask {subtask.id} completed")

                    except Exception as e:
                        if self.logger:
                            self.logger.error(f"Subtask {subtask.id} failed: {e}")

                        subtask.status = "failed"
                        subtask.result = f"Error: {str(e)}"
                        results[subtask.id] = subtask.result
                        completed.add(subtask.id)  # Mark as completed (with error)

        return results

    def _review_results(self, results: Dict[int, Any], original_query: str) -> Dict:
        """Use Reviewer agent to validate results.

        Args:
            results: Dictionary of subtask results
            original_query: Original user query for context

        Returns:
            Dictionary with:
            - approved: bool
            - feedback: str
            - revisions_needed: List[int]
        """
        reviewer = self.agents["reviewer"]

        # Format results for review
        results_str = "\n".join([
            f"Subtask {id}: {result}"
            for id, result in results.items()
        ])

        review_query = f"""{self._agent_prompts['reviewer']}

Original query: {original_query}

Results to review:
{results_str}"""

        # Run reviewer agent
        result = reviewer.run(review_query)
        output = result.get("output", "")

        if self.logger:
            self.logger.debug(f"Reviewer output: {output[:200]}...")

        # Parse JSON output
        try:
            # Extract JSON from output
            json_match = re.search(r'\{.*\}', output, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
                review_dict = json.loads(json_str)
            else:
                # Fallback: Approve if no valid JSON
                review_dict = {
                    "approved": True,
                    "feedback": "Review completed",
                    "revisions_needed": []
                }

            return {
                "approved": review_dict.get("approved", True),
                "feedback": review_dict.get("feedback", ""),
                "revisions_needed": review_dict.get("revisions_needed", [])
            }

        except (json.JSONDecodeError, KeyError) as e:
            if self.logger:
                self.logger.error(f"Failed to parse reviewer output: {e}")

            # Fallback: Approve
            return {
                "approved": True,
                "feedback": "Review parsing failed, approving by default",
                "revisions_needed": []
            }

    def _synthesize_results(self, results: Dict[int, Any], original_query: str) -> str:
        """Use Synthesizer agent to create final answer.

        Args:
            results: Dictionary of subtask results
            original_query: Original user query

        Returns:
            Final synthesized answer string
        """
        synthesizer = self.agents["synthesizer"]

        # Format results for synthesis
        results_str = "\n".join([
            f"Subtask {id}: {result}"
            for id, result in results.items()
        ])

        synthesis_query = f"""{self._agent_prompts['synthesizer']}

Original query: {original_query}

Subtask results:
{results_str}

Synthesize these results into a comprehensive final answer."""

        # Run synthesizer agent
        result = synthesizer.run(synthesis_query)
        final_answer = result.get("output", "")

        if self.logger:
            self.logger.info("Results synthesized")

        return final_answer

    def _handle_revisions(
        self,
        revisions_needed: List[int],
        results: Dict[int, Any],
        subtasks: List[SubTask],
        feedback: str
    ) -> Dict[int, Any]:
        """Re-execute failed subtasks based on reviewer feedback.

        Args:
            revisions_needed: List of subtask IDs to revise
            results: Current results dictionary
            subtasks: List of SubTask objects
            feedback: Reviewer's feedback

        Returns:
            Updated results dictionary
        """
        executor = self.agents["executor"]

        for subtask_id in revisions_needed:
            # Find the subtask
            subtask = next((st for st in subtasks if st.id == subtask_id), None)
            if not subtask:
                continue

            if self.logger:
                self.logger.debug(f"Revising subtask {subtask_id}")

            # Re-execute with feedback
            revision_query = f"""{self._agent_prompts['executor']}

Subtask: {subtask.task}

Previous attempt result: {results.get(subtask_id, 'N/A')}

Reviewer feedback: {feedback}

Please revise and improve the result based on the feedback."""

            try:
                result = executor.run(revision_query)
                revised_result = result.get("output", "")
                results[subtask_id] = revised_result
                subtask.result = revised_result
                subtask.status = "completed (revised)"

                if self.logger:
                    self.logger.debug(f"Subtask {subtask_id} revised")

            except Exception as e:
                if self.logger:
                    self.logger.error(f"Revision of subtask {subtask_id} failed: {e}")

        return results

    def is_complex_query(self, query: str) -> bool:
        """Determine if a query is complex enough to warrant multi-agent coordination.

        Heuristics for complexity:
        - Contains coordination words: "and", "then", "after", "compare"
        - Contains complexity indicators: "comprehensive", "analyze", "research"
        - User explicitly requests: "use multi-agent"
        - Query is long (>100 characters)

        Args:
            query: User query to analyze

        Returns:
            True if query is complex, False otherwise
        """
        query_lower = query.lower()

        # Explicit multi-agent request
        if "multi-agent" in query_lower or "multi agent" in query_lower:
            return True

        # Coordination words
        coordination_words = ["and then", "after that", "compare", "analyze and"]
        if any(word in query_lower for word in coordination_words):
            return True

        # Complexity indicators
        complexity_words = ["comprehensive", "analyze", "research", "investigate", "compare"]
        word_count = sum(1 for word in complexity_words if word in query_lower)
        if word_count >= 2:
            return True

        # Long queries
        if len(query) > 150:
            return True

        return False

    def __repr__(self) -> str:
        """String representation of MultiAgentCoordinator.

        Returns:
            Coordinator info with agent count
        """
        return f"<MultiAgentCoordinator(agents={len(self.agents)}, max_subtasks={self.max_subtasks})>"
