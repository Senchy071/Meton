"""Sub-Agent Tool for Meton.

This tool allows the main agent to spawn sub-agents for specialized tasks.
Sub-agents run with isolated context and can have restricted tools.

Example:
    >>> from tools.subagent_tool import SubAgentTool
    >>> from agents.subagent_spawner import SubAgentManager
    >>>
    >>> manager = SubAgentManager(config, model_manager, tools)
    >>> tool = SubAgentTool(manager)
    >>> result = tool._run('{"agent": "explorer", "task": "Find authentication code"}')
"""

import json
import logging
from typing import Dict, Any, Optional, List

from pydantic import Field

from tools.base import MetonBaseTool, ToolConfig

# Import SubAgentManager for type hints only, accept Any at runtime for testability
try:
    from agents.subagent_spawner import SubAgentManager, SubAgentResult
except ImportError:
    SubAgentManager = None
    SubAgentResult = None


class SubAgentToolConfig(ToolConfig):
    """Configuration for sub-agent tool."""
    enabled: bool = True
    verbose: bool = False


class SubAgentTool(MetonBaseTool):
    """Tool for spawning sub-agents.

    This tool allows the main agent to delegate specialized tasks to
    sub-agents. Each sub-agent runs with its own isolated context
    and can have specific tools and models.

    Use cases:
    - Delegate code exploration to the explorer agent (fast, read-only)
    - Delegate implementation planning to the planner agent
    - Delegate code review to the code-reviewer agent
    - Delegate debugging tasks to the debugger agent

    Input Format:
        {"agent": "agent-name", "task": "task description", "context": "optional context"}

    Example:
        >>> tool = SubAgentTool(manager)
        >>> result = tool._run('{"agent": "explorer", "task": "Find all API endpoints"}')
    """

    name: str = "spawn_agent"
    description: str = (
        "Spawn a sub-agent for specialized tasks. Sub-agents run with isolated context. "
        "Use 'explorer' for fast codebase exploration, 'planner' for implementation planning, "
        "'code-reviewer' for code review, 'debugger' for error analysis. "
        "Input: {\"agent\": \"agent-name\", \"task\": \"description\", \"context\": \"optional\"}."
    )

    agent_manager: Any = Field(...)
    config: SubAgentToolConfig = Field(default_factory=SubAgentToolConfig)
    logger: Optional[logging.Logger] = Field(default=None)

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    def __init__(self, agent_manager: SubAgentManager, **kwargs):
        """Initialize the sub-agent tool.

        Args:
            agent_manager: SubAgentManager instance
            **kwargs: Additional configuration options
        """
        super().__init__(agent_manager=agent_manager, **kwargs)
        self.logger = logging.getLogger("meton.subagent_tool")

    def _run(self, input_str: str) -> str:
        """Spawn a sub-agent and execute a task.

        Args:
            input_str: JSON string with agent name and task
                      Format: {"agent": "agent-name", "task": "...", "context": "..."}

        Returns:
            JSON string with sub-agent execution result
        """
        # Check if enabled
        if not self.config.enabled:
            return json.dumps({
                "success": False,
                "error": "Sub-agent spawning is disabled.",
                "result": None
            })

        # Parse input
        success, data = self._parse_json_input(input_str, ["agent", "task"])
        if not success:
            return json.dumps({
                "success": False,
                "error": data,  # data is error message
                "result": None
            })

        agent_name = data.get("agent", "").strip()
        task = data.get("task", "").strip()
        context = data.get("context", "")

        if not agent_name:
            return json.dumps({
                "success": False,
                "error": "Agent name is required",
                "result": None
            })

        if not task:
            return json.dumps({
                "success": False,
                "error": "Task description is required",
                "result": None
            })

        # Check if agent exists
        available = self.agent_manager.list_agents()
        if agent_name not in available:
            return json.dumps({
                "success": False,
                "error": f"Agent '{agent_name}' not found. Available: {', '.join(available)}",
                "result": None
            })

        # Execute the sub-agent
        try:
            self._log_execution("spawn_agent", f"agent={agent_name}, task={task[:50]}...")

            result = self.agent_manager.run_agent(
                agent_name=agent_name,
                task=task,
                context=context if context else None
            )

            if result.success:
                return json.dumps({
                    "success": True,
                    "agent": agent_name,
                    "agent_id": result.agent_id,
                    "task": task,
                    "output": result.output,
                    "iterations": result.iterations,
                    "duration_seconds": round(result.duration_seconds, 2),
                    "model_used": result.model_used
                }, indent=2)
            else:
                return json.dumps({
                    "success": False,
                    "agent": agent_name,
                    "error": result.error or "Unknown error",
                    "result": None
                })

        except Exception as e:
            self.logger.error(f"Sub-agent execution error: {e}")
            return json.dumps({
                "success": False,
                "error": str(e),
                "result": None
            })

    def get_available_agents(self) -> List[Dict[str, str]]:
        """Get list of available sub-agents with descriptions.

        Returns:
            List of agent info dicts with name, model, and description
        """
        agents = []
        for name in self.agent_manager.list_agents():
            agent = self.agent_manager.get_agent(name)
            if agent:
                agents.append({
                    "name": name,
                    "model": agent.model,
                    "tools": agent.tools or [],
                    "description": agent.description
                })

        return agents

    def generate_prompt_section(self) -> str:
        """Generate a system prompt section describing available sub-agents.

        Returns:
            Formatted string for inclusion in agent system prompt
        """
        agents = self.get_available_agents()
        if not agents:
            return ""

        lines = [
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            "AVAILABLE SUB-AGENTS (spawn with spawn_agent tool):",
            "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━",
            ""
        ]

        for agent in agents:
            tools_str = ", ".join(agent["tools"][:3]) if agent["tools"] else "all"
            if len(agent["tools"]) > 3:
                tools_str += f" (+{len(agent['tools'])-3} more)"
            lines.append(f"- {agent['name']} (model: {agent['model']}, tools: {tools_str})")
            lines.append(f"  {agent['description']}")
            lines.append("")

        lines.append("When to use sub-agents:")
        lines.append("- Use 'explorer' for quick codebase searches (uses fast model)")
        lines.append("- Use 'planner' when you need to design an implementation approach")
        lines.append("- Use 'code-reviewer' when code needs quality/security review")
        lines.append("- Use 'debugger' when analyzing errors or unexpected behavior")
        lines.append("")
        lines.append("To spawn a sub-agent:")
        lines.append('ACTION: spawn_agent')
        lines.append('ACTION_INPUT: {"agent": "explorer", "task": "Find all API endpoints"}')
        lines.append("")

        return "\n".join(lines)
