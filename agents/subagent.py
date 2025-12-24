"""Sub-Agent Definition for Meton.

This module provides support for Claude Code-style sub-agent definitions.
Sub-agents are specialized AI assistants that can be delegated to for
specific tasks, with their own tools, model, and instructions.

File Format:
    ---
    name: agent-name
    description: When to use this agent
    tools: Read, Grep, Glob  # optional, comma-separated
    model: primary  # optional: primary, fallback, quick, or inherit
    ---

    System prompt and instructions for the agent...

Example:
    >>> from agents.subagent import SubAgent
    >>>
    >>> agent = SubAgent.from_file(".meton/agents/code-reviewer.md")
    >>> print(agent.name)
    'code-reviewer'
"""

import re
import yaml
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional, Set
from dataclasses import dataclass, field
from enum import Enum


class SubAgentParseError(Exception):
    """Error parsing a sub-agent definition."""
    pass


class SubAgentValidationError(Exception):
    """Error validating sub-agent metadata."""
    pass


class ModelChoice(Enum):
    """Available model choices for sub-agents."""
    PRIMARY = "primary"
    FALLBACK = "fallback"
    QUICK = "quick"
    INHERIT = "inherit"


@dataclass
class SubAgent:
    """Represents a sub-agent definition.

    Sub-agents are specialized agents that can be delegated to for
    specific tasks. They run with their own context and can have
    restricted tools and specific models.

    Attributes:
        name: Unique agent identifier (lowercase, hyphens, max 64 chars)
        description: When/why to use this agent (critical for auto-delegation)
        system_prompt: Full instructions for the agent
        tools: Optional list of allowed tool names (None = inherit all)
        model: Model to use (primary, fallback, quick, inherit)
        version: Agent version (default: 1.0.0)
        enabled: Whether the agent is enabled
        source_path: Path to the source .md file
    """

    name: str
    description: str
    system_prompt: str
    tools: Optional[List[str]] = None
    model: str = "inherit"
    version: str = "1.0.0"
    enabled: bool = True
    source_path: Optional[Path] = None

    # Class-level constants
    MAX_NAME_LENGTH = 64
    MAX_DESCRIPTION_LENGTH = 1024
    NAME_PATTERN = re.compile(r'^[a-z0-9][a-z0-9-]*[a-z0-9]$|^[a-z0-9]$')
    VALID_MODELS = {"primary", "fallback", "quick", "inherit"}

    def __post_init__(self):
        """Validate agent after initialization."""
        self._validate()

    def _validate(self) -> None:
        """Validate agent metadata.

        Raises:
            SubAgentValidationError: If validation fails
        """
        # Validate name
        if not self.name:
            raise SubAgentValidationError("Agent name is required")

        if len(self.name) > self.MAX_NAME_LENGTH:
            raise SubAgentValidationError(
                f"Agent name exceeds {self.MAX_NAME_LENGTH} characters"
            )

        if not self.NAME_PATTERN.match(self.name):
            raise SubAgentValidationError(
                f"Invalid agent name '{self.name}'. Must be lowercase with "
                "hyphens only, cannot start or end with hyphen"
            )

        # Validate description
        if not self.description:
            raise SubAgentValidationError("Agent description is required")

        if len(self.description) > self.MAX_DESCRIPTION_LENGTH:
            raise SubAgentValidationError(
                f"Agent description exceeds {self.MAX_DESCRIPTION_LENGTH} characters"
            )

        # Validate system prompt
        if not self.system_prompt or not self.system_prompt.strip():
            raise SubAgentValidationError("Agent system prompt is required")

        # Validate model
        if self.model and self.model not in self.VALID_MODELS:
            raise SubAgentValidationError(
                f"Invalid model '{self.model}'. Must be one of: {', '.join(self.VALID_MODELS)}"
            )

    @classmethod
    def from_file(cls, file_path: str | Path) -> "SubAgent":
        """Load a sub-agent from a markdown file.

        Args:
            file_path: Path to the agent definition .md file

        Returns:
            SubAgent instance

        Raises:
            SubAgentParseError: If file cannot be parsed
            SubAgentValidationError: If agent metadata is invalid
            FileNotFoundError: If file doesn't exist

        Example:
            >>> agent = SubAgent.from_file(".meton/agents/reviewer.md")
        """
        path = Path(file_path)

        if not path.exists():
            raise FileNotFoundError(f"Agent file not found: {path}")

        content = path.read_text(encoding='utf-8')
        agent = cls.from_string(content)
        agent.source_path = path

        return agent

    @classmethod
    def from_string(cls, content: str) -> "SubAgent":
        """Parse a sub-agent from markdown string content.

        Args:
            content: Markdown content with YAML frontmatter

        Returns:
            SubAgent instance

        Raises:
            SubAgentParseError: If content cannot be parsed
            SubAgentValidationError: If agent metadata is invalid

        Example:
            >>> content = '''---
            ... name: my-agent
            ... description: Does something useful
            ... ---
            ... You are a helpful agent...
            ... '''
            >>> agent = SubAgent.from_string(content)
        """
        # Parse YAML frontmatter
        frontmatter, system_prompt = cls._parse_frontmatter(content)

        # Extract required fields
        name = frontmatter.get('name')
        description = frontmatter.get('description')

        if not name:
            raise SubAgentParseError("Missing required field 'name' in frontmatter")
        if not description:
            raise SubAgentParseError("Missing required field 'description' in frontmatter")

        # Extract optional fields
        tools = cls._parse_tools(frontmatter.get('tools'))
        model = frontmatter.get('model', 'inherit')
        version = frontmatter.get('version', '1.0.0')

        return cls(
            name=name,
            description=description,
            system_prompt=system_prompt,
            tools=tools,
            model=str(model),
            version=str(version),
        )

    @staticmethod
    def _parse_frontmatter(content: str) -> tuple[Dict[str, Any], str]:
        """Parse YAML frontmatter from markdown content.

        Args:
            content: Full markdown content

        Returns:
            Tuple of (frontmatter dict, remaining content)

        Raises:
            SubAgentParseError: If frontmatter is missing or invalid
        """
        # Match YAML frontmatter between --- delimiters
        pattern = r'^---\s*\n(.*?)\n---\s*\n(.*)$'
        match = re.match(pattern, content, re.DOTALL)

        if not match:
            raise SubAgentParseError(
                "Invalid agent format. Expected YAML frontmatter between --- delimiters"
            )

        yaml_content = match.group(1)
        markdown_content = match.group(2).strip()

        try:
            frontmatter = yaml.safe_load(yaml_content)
        except yaml.YAMLError as e:
            raise SubAgentParseError(f"Invalid YAML in frontmatter: {e}")

        if not isinstance(frontmatter, dict):
            raise SubAgentParseError("Frontmatter must be a YAML mapping")

        return frontmatter, markdown_content

    @staticmethod
    def _parse_tools(tools_value: Optional[str | List[str]]) -> Optional[List[str]]:
        """Parse tools field.

        Args:
            tools_value: String (comma-separated) or list of tool names

        Returns:
            List of tool names or None (None means inherit all tools)
        """
        if tools_value is None:
            return None

        if isinstance(tools_value, list):
            return [t.strip() for t in tools_value if t.strip()]

        if isinstance(tools_value, str):
            return [t.strip() for t in tools_value.split(',') if t.strip()]

        return None

    def get_info(self) -> Dict[str, Any]:
        """Return agent metadata.

        Returns:
            Dictionary with agent information
        """
        return {
            "name": self.name,
            "description": self.description,
            "version": self.version,
            "enabled": self.enabled,
            "tools": self.tools,
            "model": self.model,
            "source_path": str(self.source_path) if self.source_path else None,
        }

    def get_effective_tools(self, available_tools: List[str]) -> List[str]:
        """Get the effective list of tools for this agent.

        Args:
            available_tools: List of all available tool names

        Returns:
            List of tool names this agent can use
        """
        if self.tools is None:
            # Inherit all tools
            return available_tools

        # Filter to only allowed tools that exist
        return [t for t in self.tools if t in available_tools]

    def enable(self) -> None:
        """Enable the agent."""
        self.enabled = True

    def disable(self) -> None:
        """Disable the agent."""
        self.enabled = False

    def __repr__(self) -> str:
        """String representation."""
        status = "enabled" if self.enabled else "disabled"
        tools = f", tools={self.tools}" if self.tools else ", tools=inherit"
        return f"<SubAgent(name='{self.name}', model='{self.model}', {status}{tools})>"


class SubAgentLoader:
    """Discovers and loads sub-agents from multiple directories.

    Discovery Order (highest to lowest precedence):
    1. Project agents: .meton/agents/
    2. User agents: ~/.meton/agents/
    3. Built-in agents: agents/builtin/

    Example:
        >>> loader = SubAgentLoader()
        >>> loader.discover()
        >>> agents = loader.load_all()
        >>> print([a.name for a in agents])
        ['explorer', 'code-reviewer', 'debugger']
    """

    def __init__(
        self,
        project_dir: Optional[Path] = None,
        user_dir: Optional[Path] = None,
        builtin_dir: Optional[Path] = None
    ):
        """Initialize the agent loader.

        Args:
            project_dir: Project agents directory (default: .meton/agents/)
            user_dir: User agents directory (default: ~/.meton/agents/)
            builtin_dir: Built-in agents directory (default: agents/builtin/)
        """
        self.project_dir = project_dir or Path(".meton/agents")
        self.user_dir = user_dir or Path.home() / ".meton" / "agents"
        self.builtin_dir = builtin_dir or Path("agents/builtin")

        self.logger = logging.getLogger("meton.subagent_loader")

        # Discovered agent paths (name -> path)
        self.discovered: Dict[str, Path] = {}

        # Loaded agents (name -> SubAgent)
        self.loaded: Dict[str, SubAgent] = {}

    def discover(self) -> Dict[str, Path]:
        """Discover all available sub-agents.

        Scans all agent directories in precedence order.
        Higher precedence directories override lower ones.

        Returns:
            Dictionary mapping agent names to their file paths
        """
        self.discovered.clear()

        # Scan in reverse precedence order (builtin first, project last)
        for agent_dir in [self.builtin_dir, self.user_dir, self.project_dir]:
            self._scan_directory(agent_dir)

        self.logger.info(f"Discovered {len(self.discovered)} sub-agents")
        return self.discovered.copy()

    def _scan_directory(self, base_dir: Path) -> None:
        """Scan a directory for agent definitions.

        Args:
            base_dir: Directory to scan
        """
        if not base_dir.exists() or not base_dir.is_dir():
            self.logger.debug(f"Agent directory not found: {base_dir}")
            return

        # Look for .md files in the directory
        for item in base_dir.glob("*.md"):
            if item.name.lower() == "readme.md":
                continue

            # Use filename (without extension) as agent identifier
            agent_name = item.stem
            self.discovered[agent_name] = item
            self.logger.debug(f"Found agent: {agent_name} at {item}")

    def load_agent(self, name: str) -> Optional[SubAgent]:
        """Load a specific agent by name.

        Args:
            name: Agent name to load

        Returns:
            SubAgent instance or None if not found/failed
        """
        if name in self.loaded:
            return self.loaded[name]

        if name not in self.discovered:
            self.logger.warning(f"Agent '{name}' not discovered")
            return None

        try:
            agent = SubAgent.from_file(self.discovered[name])
            self.loaded[name] = agent
            self.logger.info(f"Loaded sub-agent: {name}")
            return agent
        except (SubAgentParseError, SubAgentValidationError, FileNotFoundError) as e:
            self.logger.error(f"Failed to load agent '{name}': {e}")
            return None

    def load_all(self) -> List[SubAgent]:
        """Load all discovered agents.

        Returns:
            List of successfully loaded SubAgent instances
        """
        if not self.discovered:
            self.discover()

        agents = []
        for name in self.discovered:
            agent = self.load_agent(name)
            if agent:
                agents.append(agent)

        self.logger.info(f"Loaded {len(agents)}/{len(self.discovered)} sub-agents")
        return agents

    def unload_agent(self, name: str) -> bool:
        """Unload an agent.

        Args:
            name: Agent name to unload

        Returns:
            True if unloaded, False if wasn't loaded
        """
        if name in self.loaded:
            del self.loaded[name]
            self.logger.info(f"Unloaded agent: {name}")
            return True
        return False

    def reload_agent(self, name: str) -> Optional[SubAgent]:
        """Reload an agent from disk.

        Args:
            name: Agent name to reload

        Returns:
            Reloaded agent or None if failed
        """
        self.unload_agent(name)
        return self.load_agent(name)

    def get_agent(self, name: str) -> Optional[SubAgent]:
        """Get a loaded agent by name.

        Args:
            name: Agent name

        Returns:
            SubAgent instance or None
        """
        return self.loaded.get(name)

    def list_discovered(self) -> List[str]:
        """List all discovered agent names.

        Returns:
            List of agent names
        """
        return list(self.discovered.keys())

    def list_loaded(self) -> List[str]:
        """List all loaded agent names.

        Returns:
            List of loaded agent names
        """
        return list(self.loaded.keys())

    def get_agent_descriptions(self) -> Dict[str, str]:
        """Get descriptions of all loaded agents.

        Useful for injecting into system prompts for auto-delegation.

        Returns:
            Dictionary mapping agent names to descriptions
        """
        return {
            name: agent.description
            for name, agent in self.loaded.items()
        }

    def generate_agents_prompt_section(self) -> str:
        """Generate a prompt section listing available agents.

        This is injected into the main agent's system prompt for
        automatic delegation decisions.

        Returns:
            Formatted string describing available sub-agents
        """
        if not self.loaded:
            return ""

        lines = ["## Available Sub-Agents", ""]
        lines.append("You can delegate tasks to these specialized agents:")
        lines.append("")

        for name, agent in sorted(self.loaded.items()):
            lines.append(f"### {name}")
            lines.append(f"**When to use:** {agent.description}")
            if agent.tools:
                lines.append(f"**Tools:** {', '.join(agent.tools)}")
            else:
                lines.append("**Tools:** All available tools")
            lines.append(f"**Model:** {agent.model}")
            lines.append("")

        return "\n".join(lines)

    def __repr__(self) -> str:
        """String representation."""
        return (
            f"<SubAgentLoader("
            f"discovered={len(self.discovered)}, "
            f"loaded={len(self.loaded)})>"
        )
