"""Sub-Agent Spawner for Meton.

This module handles the execution of sub-agents in isolated contexts.
Sub-agents run with their own conversation history and can have
restricted tools and specific models.

Example:
    >>> from agents.subagent_spawner import SubAgentSpawner
    >>> from agents.subagent import SubAgent
    >>>
    >>> spawner = SubAgentSpawner(config, model_manager, tools)
    >>> agent = SubAgent.from_file(".meton/agents/code-reviewer.md")
    >>> result = spawner.spawn(agent, "Review the authentication module")
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from pathlib import Path
from datetime import datetime

from langchain.tools import BaseTool

from core.config import ConfigLoader
from core.models import ModelManager
from core.conversation import ConversationManager
from agents.subagent import SubAgent, SubAgentLoader


class SubAgentError(Exception):
    """Base exception for sub-agent errors."""
    pass


class SubAgentSpawnError(SubAgentError):
    """Error spawning a sub-agent."""
    pass


class SubAgentExecutionError(SubAgentError):
    """Error during sub-agent execution."""
    pass


class SubAgentResult:
    """Result from a sub-agent execution.

    Attributes:
        agent_id: Unique ID for this execution
        agent_name: Name of the sub-agent
        task: The task that was given
        output: The final output/answer
        success: Whether execution succeeded
        error: Error message if failed
        tool_calls: List of tools called
        iterations: Number of reasoning iterations
        duration_seconds: Execution time
        model_used: Model that was used
    """

    def __init__(
        self,
        agent_id: str,
        agent_name: str,
        task: str,
        output: str = "",
        success: bool = True,
        error: Optional[str] = None,
        tool_calls: Optional[List[Dict[str, Any]]] = None,
        iterations: int = 0,
        duration_seconds: float = 0.0,
        model_used: str = ""
    ):
        self.agent_id = agent_id
        self.agent_name = agent_name
        self.task = task
        self.output = output
        self.success = success
        self.error = error
        self.tool_calls = tool_calls or []
        self.iterations = iterations
        self.duration_seconds = duration_seconds
        self.model_used = model_used
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "agent_id": self.agent_id,
            "agent_name": self.agent_name,
            "task": self.task,
            "output": self.output,
            "success": self.success,
            "error": self.error,
            "tool_calls": self.tool_calls,
            "iterations": self.iterations,
            "duration_seconds": self.duration_seconds,
            "model_used": self.model_used,
            "timestamp": self.timestamp.isoformat(),
        }

    def __repr__(self) -> str:
        status = "success" if self.success else "failed"
        return (
            f"<SubAgentResult(agent={self.agent_name}, {status}, "
            f"iterations={self.iterations}, duration={self.duration_seconds:.2f}s)>"
        )


class SubAgentSpawner:
    """Spawns and manages sub-agent executions.

    The spawner creates isolated agent instances for each sub-agent
    execution, with their own conversation context and optionally
    restricted tools.

    Example:
        >>> spawner = SubAgentSpawner(config, model_manager, tools)
        >>> result = spawner.spawn_by_name("code-reviewer", "Review my code")
        >>> print(result.output)
    """

    def __init__(
        self,
        config: ConfigLoader,
        model_manager: ModelManager,
        tools: List[BaseTool],
        verbose: bool = False
    ):
        """Initialize the sub-agent spawner.

        Args:
            config: Configuration loader
            model_manager: Model manager instance
            tools: List of all available tools
            verbose: Whether to show agent reasoning
        """
        self.config = config
        self.model_manager = model_manager
        self.all_tools = tools
        self.verbose = verbose

        self.logger = logging.getLogger("meton.subagent_spawner")

        # Create tool name -> tool mapping
        self.tool_map = {tool.name: tool for tool in tools}

        # Agent loader
        self.loader = SubAgentLoader()
        self.loader.discover()

        # Track active and completed executions
        self.active_agents: Dict[str, SubAgentResult] = {}
        self.completed_agents: Dict[str, SubAgentResult] = {}

    def spawn(
        self,
        agent: SubAgent,
        task: str,
        context: Optional[str] = None
    ) -> SubAgentResult:
        """Spawn a sub-agent to execute a task.

        Creates an isolated agent instance with its own context and
        executes the given task.

        Args:
            agent: SubAgent definition to use
            task: The task/query to execute
            context: Optional additional context to provide

        Returns:
            SubAgentResult with execution results

        Raises:
            SubAgentSpawnError: If agent cannot be spawned
            SubAgentExecutionError: If execution fails
        """
        import time

        # Generate unique agent ID
        agent_id = str(uuid.uuid4())[:8]

        self.logger.info(f"Spawning sub-agent '{agent.name}' (id={agent_id})")

        start_time = time.time()

        try:
            # Determine which model to use
            model_name = self._resolve_model(agent.model)

            # Get effective tools for this agent
            effective_tools = self._get_effective_tools(agent)

            # Create isolated conversation
            isolated_conversation = self._create_isolated_conversation(agent)

            # Create the agent instance
            from core.agent import MetonAgent

            sub_agent_instance = MetonAgent(
                config=self.config,
                model_manager=self.model_manager,
                conversation=isolated_conversation,
                tools=effective_tools,
                verbose=self.verbose
            )

            # Override the system prompt with sub-agent's prompt
            original_get_system_prompt = sub_agent_instance._get_system_prompt

            def custom_system_prompt():
                base_prompt = original_get_system_prompt()
                # Prepend the sub-agent's custom instructions
                return f"""# Sub-Agent: {agent.name}

{agent.system_prompt}

---

{base_prompt}
"""

            sub_agent_instance._get_system_prompt = custom_system_prompt

            # Build full task with context
            full_task = task
            if context:
                full_task = f"Context:\n{context}\n\nTask:\n{task}"

            # Execute the task
            result = sub_agent_instance.run(full_task)

            duration = time.time() - start_time

            # Build result
            agent_result = SubAgentResult(
                agent_id=agent_id,
                agent_name=agent.name,
                task=task,
                output=result.get("output", ""),
                success=True,
                tool_calls=result.get("tool_calls", []),
                iterations=result.get("iterations", 0),
                duration_seconds=duration,
                model_used=model_name
            )

            self.completed_agents[agent_id] = agent_result
            self.logger.info(
                f"Sub-agent '{agent.name}' completed (id={agent_id}, "
                f"iterations={agent_result.iterations}, duration={duration:.2f}s)"
            )

            return agent_result

        except Exception as e:
            duration = time.time() - start_time
            self.logger.error(f"Sub-agent '{agent.name}' failed: {e}")

            agent_result = SubAgentResult(
                agent_id=agent_id,
                agent_name=agent.name,
                task=task,
                output="",
                success=False,
                error=str(e),
                duration_seconds=duration,
                model_used=self._resolve_model(agent.model)
            )

            self.completed_agents[agent_id] = agent_result
            return agent_result

    def spawn_by_name(
        self,
        agent_name: str,
        task: str,
        context: Optional[str] = None
    ) -> SubAgentResult:
        """Spawn a sub-agent by name.

        Args:
            agent_name: Name of the agent to spawn
            task: The task to execute
            context: Optional additional context

        Returns:
            SubAgentResult with execution results

        Raises:
            SubAgentSpawnError: If agent not found
        """
        # Load agent if not already loaded
        agent = self.loader.get_agent(agent_name)
        if not agent:
            agent = self.loader.load_agent(agent_name)

        if not agent:
            raise SubAgentSpawnError(f"Sub-agent not found: {agent_name}")

        if not agent.enabled:
            raise SubAgentSpawnError(f"Sub-agent is disabled: {agent_name}")

        return self.spawn(agent, task, context)

    def _resolve_model(self, model_choice: str) -> str:
        """Resolve model choice to actual model name.

        Args:
            model_choice: Model choice (primary, fallback, quick, inherit)

        Returns:
            Actual model name
        """
        if model_choice == "inherit" or not model_choice:
            return self.model_manager.current_model

        if model_choice == "primary":
            return self.config.config.models.primary
        elif model_choice == "fallback":
            return self.config.config.models.fallback
        elif model_choice == "quick":
            return self.config.config.models.quick
        else:
            # Assume it's a direct model name
            return model_choice

    def _get_effective_tools(self, agent: SubAgent) -> List[BaseTool]:
        """Get the effective tools for a sub-agent.

        Args:
            agent: SubAgent definition

        Returns:
            List of tools the agent can use
        """
        if agent.tools is None:
            # Inherit all tools
            return self.all_tools

        # Filter to only allowed tools
        effective_tools = []
        for tool_name in agent.tools:
            if tool_name in self.tool_map:
                effective_tools.append(self.tool_map[tool_name])
            else:
                self.logger.warning(
                    f"Tool '{tool_name}' not found for agent '{agent.name}'"
                )

        return effective_tools

    def _create_isolated_conversation(self, agent: SubAgent) -> ConversationManager:
        """Create an isolated conversation manager for a sub-agent.

        Args:
            agent: SubAgent definition

        Returns:
            Fresh ConversationManager instance
        """
        # Create a new conversation manager with isolated state
        isolated_conversation = ConversationManager(
            self.config,
            logger=self.logger
        )

        # Start fresh session
        isolated_conversation.clear()

        return isolated_conversation

    def list_available(self) -> List[str]:
        """List all available sub-agents.

        Returns:
            List of agent names
        """
        return self.loader.list_discovered()

    def list_loaded(self) -> List[str]:
        """List all loaded sub-agents.

        Returns:
            List of loaded agent names
        """
        return self.loader.list_loaded()

    def get_agent_info(self, name: str) -> Optional[Dict[str, Any]]:
        """Get information about a sub-agent.

        Args:
            name: Agent name

        Returns:
            Agent info dictionary or None
        """
        agent = self.loader.get_agent(name)
        if not agent:
            agent = self.loader.load_agent(name)

        if agent:
            return agent.get_info()
        return None

    def get_completed_results(self) -> Dict[str, SubAgentResult]:
        """Get all completed agent results.

        Returns:
            Dictionary of agent_id -> SubAgentResult
        """
        return self.completed_agents.copy()

    def get_result(self, agent_id: str) -> Optional[SubAgentResult]:
        """Get result for a specific agent execution.

        Args:
            agent_id: Agent execution ID

        Returns:
            SubAgentResult or None
        """
        return self.completed_agents.get(agent_id)

    def rediscover(self) -> int:
        """Rediscover available sub-agents.

        Returns:
            Number of newly discovered agents
        """
        old_count = len(self.loader.discovered)
        self.loader.discover()
        return len(self.loader.discovered) - old_count

    def generate_delegation_prompt(self) -> str:
        """Generate prompt section for delegation decisions.

        Returns:
            Formatted string for system prompt
        """
        return self.loader.generate_agents_prompt_section()

    def __repr__(self) -> str:
        return (
            f"<SubAgentSpawner("
            f"available={len(self.loader.discovered)}, "
            f"completed={len(self.completed_agents)})>"
        )


class SubAgentManager:
    """High-level manager for sub-agents.

    Combines loading, spawning, and management into a single interface.

    Example:
        >>> manager = SubAgentManager(config, model_manager, tools)
        >>> result = manager.delegate("code-reviewer", "Review my code")
        >>> print(result.output)
    """

    def __init__(
        self,
        config: ConfigLoader,
        model_manager: ModelManager,
        tools: List[BaseTool],
        verbose: bool = False
    ):
        """Initialize the sub-agent manager.

        Args:
            config: Configuration loader
            model_manager: Model manager instance
            tools: List of all available tools
            verbose: Whether to show agent reasoning
        """
        self.spawner = SubAgentSpawner(config, model_manager, tools, verbose)
        self.logger = logging.getLogger("meton.subagent_manager")

    def delegate(
        self,
        agent_name: str,
        task: str,
        context: Optional[str] = None
    ) -> SubAgentResult:
        """Delegate a task to a sub-agent.

        Args:
            agent_name: Name of the agent to use
            task: The task to execute
            context: Optional context to provide

        Returns:
            SubAgentResult with execution results
        """
        return self.spawner.spawn_by_name(agent_name, task, context)

    def auto_delegate(
        self,
        task: str,
        context: Optional[str] = None
    ) -> Optional[SubAgentResult]:
        """Automatically select and delegate to the best sub-agent.

        Uses the task description to match against agent descriptions.

        Args:
            task: The task to execute
            context: Optional context to provide

        Returns:
            SubAgentResult or None if no suitable agent found
        """
        # Load all agents to check descriptions
        self.spawner.loader.load_all()

        best_agent = None
        best_score = 0

        task_lower = task.lower()

        for name, agent in self.spawner.loader.loaded.items():
            if not agent.enabled:
                continue

            # Simple keyword matching (could be enhanced with embeddings)
            desc_lower = agent.description.lower()
            score = sum(1 for word in task_lower.split() if word in desc_lower)

            if score > best_score:
                best_score = score
                best_agent = agent

        if best_agent and best_score > 0:
            self.logger.info(
                f"Auto-delegating to '{best_agent.name}' (score={best_score})"
            )
            return self.spawner.spawn(best_agent, task, context)

        self.logger.info("No suitable sub-agent found for auto-delegation")
        return None

    def list_agents(self) -> List[Dict[str, Any]]:
        """List all available agents with their info.

        Returns:
            List of agent info dictionaries
        """
        self.spawner.loader.load_all()
        return [
            agent.get_info()
            for agent in self.spawner.loader.loaded.values()
        ]

    def reload_agents(self) -> int:
        """Reload all agents from disk.

        Returns:
            Number of agents loaded
        """
        self.spawner.loader.discover()
        agents = self.spawner.loader.load_all()
        return len(agents)

    def __repr__(self) -> str:
        return f"<SubAgentManager({self.spawner})>"
