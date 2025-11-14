#!/usr/bin/env python3
"""
Task Planning System for Meton.

Creates detailed execution plans for complex tasks through:
- Query decomposition into atomic subtasks
- Dependency detection and resolution
- Execution order optimization (topological sort)
- Parallel execution where possible
- Progress tracking and error handling
- Plan visualization

Example:
    planner = TaskPlanner(model_manager, config, tools)

    # Create plan
    plan = planner.create_plan("Index FastAPI project and analyze routing")

    # Execute plan
    results = planner.execute_plan(plan)
"""

import uuid
import json
import re
import time
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, field, asdict
from datetime import datetime
from collections import defaultdict, deque


@dataclass
class SubTask:
    """Single atomic task in a plan.

    Attributes:
        id: Unique identifier within the plan
        description: Human-readable description
        tool: Tool to use for execution
        args: Arguments for the tool
        depends_on: IDs of prerequisite subtasks
        estimated_time: Estimated execution time (seconds)
        status: Current status (pending, in_progress, completed, failed)
        result: Result after execution
    """
    id: int
    description: str
    tool: str
    args: Dict
    depends_on: List[int] = field(default_factory=list)
    estimated_time: int = 10
    status: str = "pending"
    result: Any = None


@dataclass
class TaskPlan:
    """Complete execution plan for a query.

    Attributes:
        id: Unique plan identifier (UUID)
        query: Original query
        subtasks: List of subtasks to execute
        estimated_time: Total estimated time (seconds)
        complexity: Plan complexity (simple, medium, complex)
        dependencies: Mapping of subtask dependencies
        created_at: When the plan was created
    """
    id: str
    query: str
    subtasks: List[SubTask]
    estimated_time: int
    complexity: str
    dependencies: Dict[int, List[int]]
    created_at: str = field(default_factory=lambda: datetime.now().isoformat())


class TaskPlanner:
    """Creates detailed execution plans for complex tasks.

    Features:
    - LLM-based plan generation from queries
    - Dependency detection and resolution
    - Topological sort for execution order
    - Circular dependency detection
    - Plan validation before execution
    - Parallel execution of independent subtasks
    - Progress tracking with callbacks
    - Error handling with partial results
    - Plan visualization
    - Statistics tracking

    The planner decomposes complex queries into atomic subtasks,
    determines dependencies, and executes them in optimal order.
    """

    # Planning prompt template
    PLANNING_PROMPT = """Create a detailed execution plan for this query:

Query: {query}
Context: {context}

Generate a plan with:
1. List of subtasks (atomic, executable steps)
2. Tool to use for each subtask
3. Arguments for each tool
4. Dependencies between subtasks (by subtask ID)
5. Estimated time per subtask (seconds)

Available tools: {tools}

Output ONLY valid JSON (no markdown, no extra text):
{{
  "subtasks": [
    {{
      "id": 1,
      "description": "Description of what this subtask does",
      "tool": "tool_name",
      "args": {{}},
      "depends_on": [],
      "estimated_time": 10
    }}
  ]
}}

Rules:
- Each subtask must be atomic and executable
- IDs start from 1 and increment
- depends_on lists subtask IDs that must complete first
- Use realistic time estimates
- Keep subtasks focused and simple
"""

    def __init__(self, model_manager, config: Dict, tools: Dict[str, Any]):
        """Initialize task planner.

        Args:
            model_manager: Model manager for LLM access
            config: Configuration dictionary
            tools: Available tools for execution
        """
        self.model_manager = model_manager
        self.config = config
        self.tools = tools

        # Get planning config
        planning_config = config.get("task_planning", {})
        self.auto_plan_threshold = planning_config.get("auto_plan_threshold", "medium")
        self.visualize_plan_config = planning_config.get("visualize_plan", True)
        self.max_subtasks = planning_config.get("max_subtasks", 15)

        # Statistics tracking
        self.plan_history: List[Dict] = []
        self.total_plans = 0
        self.total_execution_time = 0.0
        self.successful_plans = 0

    def create_plan(self, query: str, context: Dict = None) -> TaskPlan:
        """Generate execution plan from query.

        Args:
            query: User query to plan for
            context: Optional context (previous results, etc.)

        Returns:
            TaskPlan object with subtasks and dependencies
        """
        if context is None:
            context = {}

        # Estimate complexity
        complexity = self.estimate_complexity(query)

        # Generate plan using LLM
        llm = self.model_manager.get_model("primary")

        # Format prompt
        context_str = self._format_context(context)
        tools_str = ", ".join(self.tools.keys())
        prompt = self.PLANNING_PROMPT.format(
            query=query,
            context=context_str,
            tools=tools_str
        )

        # Get LLM response
        try:
            response = llm.invoke(prompt)
            plan_json = response.content
        except Exception as e:
            # Fallback to simple plan
            return self._create_fallback_plan(query, complexity)

        # Parse plan
        subtasks = self._parse_plan_json(plan_json)

        # Limit subtasks
        if len(subtasks) > self.max_subtasks:
            subtasks = subtasks[:self.max_subtasks]

        # Build dependencies map
        dependencies = {st.id: st.depends_on for st in subtasks}

        # Calculate total estimated time
        estimated_time = sum(st.estimated_time for st in subtasks)

        # Create plan
        plan = TaskPlan(
            id=str(uuid.uuid4()),
            query=query,
            subtasks=subtasks,
            estimated_time=estimated_time,
            complexity=complexity,
            dependencies=dependencies
        )

        self.total_plans += 1

        return plan

    def execute_plan(
        self,
        plan: TaskPlan,
        progress_callback: Optional[Callable] = None
    ) -> Dict:
        """Execute plan respecting dependencies.

        Args:
            plan: TaskPlan to execute
            progress_callback: Optional callback after each subtask

        Returns:
            Dictionary with:
            - results: Dict mapping subtask ID to result
            - success: Whether all subtasks succeeded
            - failed_subtasks: List of failed subtask IDs
        """
        start_time = time.time()

        # Validate plan first
        validation = self.validate_plan(plan)
        if not validation["valid"]:
            return {
                "results": {},
                "success": False,
                "failed_subtasks": [],
                "validation_errors": validation["issues"]
            }

        # Resolve execution order
        execution_batches = self._resolve_execution_order(plan.subtasks)

        results = {}
        failed_subtasks = []

        # Execute batches
        for batch in execution_batches:
            batch_results = {}

            # Execute subtasks in batch (could be parallel)
            for subtask_id in batch:
                subtask = self._get_subtask_by_id(plan.subtasks, subtask_id)

                # Skip if dependency failed
                if any(dep in failed_subtasks for dep in subtask.depends_on):
                    subtask.status = "failed"
                    failed_subtasks.append(subtask_id)
                    continue

                # Execute subtask
                subtask.status = "in_progress"

                try:
                    result = self._execute_subtask(subtask, results)
                    subtask.status = "completed"
                    subtask.result = result
                    results[subtask_id] = result
                    batch_results[subtask_id] = result

                    # Call progress callback
                    if progress_callback:
                        progress_callback(subtask, result)

                except Exception as e:
                    subtask.status = "failed"
                    subtask.result = {"error": str(e)}
                    failed_subtasks.append(subtask_id)
                    results[subtask_id] = {"error": str(e)}

            # If all tasks in batch failed, stop execution
            if batch_results and all(sid in failed_subtasks for sid in batch):
                break

        # Record statistics
        execution_time = time.time() - start_time
        self.total_execution_time += execution_time

        success = len(failed_subtasks) == 0
        if success:
            self.successful_plans += 1

        # Store in history
        self.plan_history.append({
            "plan_id": plan.id,
            "query": plan.query,
            "subtasks_count": len(plan.subtasks),
            "execution_time": execution_time,
            "success": success,
            "failed_count": len(failed_subtasks)
        })

        return {
            "results": results,
            "success": success,
            "failed_subtasks": failed_subtasks
        }

    def validate_plan(self, plan: TaskPlan) -> Dict:
        """Check plan validity.

        Args:
            plan: TaskPlan to validate

        Returns:
            Dictionary with:
            - valid: Boolean indicating validity
            - issues: List of validation issues
        """
        issues = []

        # Check for circular dependencies
        if self._has_circular_dependency(plan.subtasks):
            issues.append("Circular dependency detected in plan")

        # Check for missing tools
        for subtask in plan.subtasks:
            if subtask.tool not in self.tools:
                issues.append(f"Tool '{subtask.tool}' not available for subtask {subtask.id}")

        # Check for invalid dependencies
        subtask_ids = {st.id for st in plan.subtasks}
        for subtask in plan.subtasks:
            for dep_id in subtask.depends_on:
                if dep_id not in subtask_ids:
                    issues.append(f"Subtask {subtask.id} depends on non-existent subtask {dep_id}")

        return {
            "valid": len(issues) == 0,
            "issues": issues
        }

    def estimate_complexity(self, query: str) -> str:
        """Determine task complexity.

        Args:
            query: Query to analyze

        Returns:
            Complexity level: "simple", "medium", or "complex"
        """
        query_lower = query.lower()

        # Count complexity indicators
        complexity_score = 0

        # Multi-step indicators
        multi_step_words = ["and then", "after", "first", "second", "finally"]
        complexity_score += sum(2 for word in multi_step_words if word in query_lower)

        # Analysis indicators
        analysis_words = ["analyze", "compare", "evaluate", "review", "assess"]
        complexity_score += sum(2 for word in analysis_words if word in query_lower)

        # Conjunction count
        complexity_score += query_lower.count(" and ")

        # Length (longer queries tend to be more complex)
        if len(query) > 100:
            complexity_score += 2
        elif len(query) > 50:
            complexity_score += 1

        # Classify based on score
        if complexity_score >= 5:
            return "complex"
        elif complexity_score >= 2:
            return "medium"
        else:
            return "simple"

    def visualize_plan(self, plan: TaskPlan) -> str:
        """Create text visualization of plan.

        Args:
            plan: TaskPlan to visualize

        Returns:
            Formatted plan visualization
        """
        lines = []

        # Header
        lines.append(f"Task Plan: {plan.query}")
        lines.append("─" * 60)
        lines.append(f"Complexity: {plan.complexity.upper()}")
        lines.append(f"Estimated Time: {plan.estimated_time} seconds")
        lines.append("")
        lines.append("Subtasks:")

        # Subtasks
        for subtask in plan.subtasks:
            lines.append(f"  {subtask.id}. [{subtask.tool}] {subtask.description} ({subtask.estimated_time}s)")

            if subtask.depends_on:
                deps_str = ", ".join(f"Task {dep}" for dep in subtask.depends_on)
                lines.append(f"     └─ Depends on: {deps_str}")
            else:
                lines.append("     └─ No dependencies")

        # Execution order
        lines.append("")
        batches = self._resolve_execution_order(plan.subtasks)
        execution_order = " → ".join(
            f"[{', '.join(map(str, batch))}]" if len(batch) > 1 else str(batch[0])
            for batch in batches
        )
        lines.append(f"Execution Order: {execution_order}")

        return "\n".join(lines)

    def get_plan_stats(self) -> Dict:
        """Get planning statistics.

        Returns:
            Dictionary with statistics:
            - total_plans: Total plans created
            - avg_subtasks: Average subtasks per plan
            - avg_execution_time: Average execution time
            - success_rate: Percentage of successful plans
        """
        if not self.plan_history:
            return {
                "total_plans": 0,
                "avg_subtasks": 0.0,
                "avg_execution_time": 0.0,
                "success_rate": 0.0
            }

        total = len(self.plan_history)
        total_subtasks = sum(p["subtasks_count"] for p in self.plan_history)
        avg_subtasks = total_subtasks / total if total > 0 else 0.0

        avg_exec_time = self.total_execution_time / total if total > 0 else 0.0
        success_rate = (self.successful_plans / total * 100) if total > 0 else 0.0

        return {
            "total_plans": total,
            "avg_subtasks": avg_subtasks,
            "avg_execution_time": avg_exec_time,
            "success_rate": success_rate
        }

    def _resolve_execution_order(self, subtasks: List[SubTask]) -> List[List[int]]:
        """Resolve execution order using topological sort.

        Args:
            subtasks: List of subtasks

        Returns:
            List of batches (each batch can execute in parallel)
        """
        # Build adjacency list and in-degree map
        graph = defaultdict(list)
        in_degree = {st.id: 0 for st in subtasks}

        for subtask in subtasks:
            for dep in subtask.depends_on:
                graph[dep].append(subtask.id)
                in_degree[subtask.id] += 1

        # Topological sort using Kahn's algorithm
        batches = []
        queue = deque([sid for sid, deg in in_degree.items() if deg == 0])

        while queue:
            # Current batch (all nodes with in-degree 0)
            batch = list(queue)
            batches.append(batch)
            queue.clear()

            # Process batch
            for node in batch:
                for neighbor in graph[node]:
                    in_degree[neighbor] -= 1
                    if in_degree[neighbor] == 0:
                        queue.append(neighbor)

        return batches

    def _has_circular_dependency(self, subtasks: List[SubTask]) -> bool:
        """Detect circular dependencies using DFS.

        Args:
            subtasks: List of subtasks

        Returns:
            True if circular dependency exists
        """
        # Build adjacency list
        graph = defaultdict(list)
        for subtask in subtasks:
            for dep in subtask.depends_on:
                graph[dep].append(subtask.id)

        # DFS with recursion stack
        visited = set()
        rec_stack = set()

        def dfs(node):
            visited.add(node)
            rec_stack.add(node)

            for neighbor in graph[node]:
                if neighbor not in visited:
                    if dfs(neighbor):
                        return True
                elif neighbor in rec_stack:
                    return True

            rec_stack.remove(node)
            return False

        # Check all nodes
        for subtask in subtasks:
            if subtask.id not in visited:
                if dfs(subtask.id):
                    return True

        return False

    def _execute_subtask(self, subtask: SubTask, previous_results: Dict) -> Any:
        """Execute a single subtask.

        Args:
            subtask: SubTask to execute
            previous_results: Results from previous subtasks

        Returns:
            Execution result
        """
        tool = self.tools.get(subtask.tool)

        if not tool:
            raise RuntimeError(f"Tool '{subtask.tool}' not found")

        # Execute tool
        if hasattr(tool, "run"):
            result = tool.run(subtask.args)
        else:
            result = tool(subtask.args)

        return result

    def _parse_plan_json(self, json_str: str) -> List[SubTask]:
        """Parse plan JSON from LLM.

        Args:
            json_str: JSON string from LLM

        Returns:
            List of SubTask objects
        """
        # Remove markdown code blocks if present
        json_str = re.sub(r'```json\s*', '', json_str)
        json_str = re.sub(r'```\s*', '', json_str)

        # Try to find JSON object
        json_match = re.search(r'\{.*\}', json_str, re.DOTALL)
        if json_match:
            json_str = json_match.group(0)

        try:
            data = json.loads(json_str)
            subtasks_data = data.get("subtasks", [])

            subtasks = []
            for st_data in subtasks_data:
                subtask = SubTask(
                    id=st_data.get("id", len(subtasks) + 1),
                    description=st_data.get("description", ""),
                    tool=st_data.get("tool", ""),
                    args=st_data.get("args", {}),
                    depends_on=st_data.get("depends_on", []),
                    estimated_time=st_data.get("estimated_time", 10)
                )
                subtasks.append(subtask)

            return subtasks

        except json.JSONDecodeError:
            # Fallback to empty list
            return []

    def _create_fallback_plan(self, query: str, complexity: str) -> TaskPlan:
        """Create fallback plan when LLM fails.

        Args:
            query: Original query
            complexity: Detected complexity

        Returns:
            Simple TaskPlan
        """
        # Create single subtask
        subtask = SubTask(
            id=1,
            description=query,
            tool="codebase_search" if "code" in query.lower() else "web_search",
            args={"query": query},
            depends_on=[],
            estimated_time=10
        )

        return TaskPlan(
            id=str(uuid.uuid4()),
            query=query,
            subtasks=[subtask],
            estimated_time=10,
            complexity=complexity,
            dependencies={1: []}
        )

    def _format_context(self, context: Dict) -> str:
        """Format context for prompt.

        Args:
            context: Context dictionary

        Returns:
            Formatted context string
        """
        if not context:
            return "No additional context"

        parts = []
        for key, value in context.items():
            parts.append(f"{key}: {value}")

        return "; ".join(parts) if parts else "No additional context"

    def _get_subtask_by_id(self, subtasks: List[SubTask], subtask_id: int) -> Optional[SubTask]:
        """Get subtask by ID.

        Args:
            subtasks: List of subtasks
            subtask_id: ID to find

        Returns:
            SubTask if found, None otherwise
        """
        for subtask in subtasks:
            if subtask.id == subtask_id:
                return subtask
        return None
