"""Base classes and types for the Hooks System.

This module defines the core data structures for hooks:
- HookType: Enum of hook execution points
- HookContext: Context passed to hooks during execution
- HookResult: Result of hook execution
- Hook: Hook definition dataclass

Example:
    >>> from hooks.base import Hook, HookType
    >>>
    >>> hook = Hook(
    ...     name="notify_on_error",
    ...     hook_type=HookType.POST_TOOL,
    ...     command="notify-send 'Tool failed: {error}'",
    ...     condition="{success} == false"
    ... )
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, Any, Optional, List, Callable
import time


class HookType(Enum):
    """Types of hooks based on execution point.

    Hooks are executed at different points in the agent's lifecycle:
    - PRE_* hooks run before an action and can modify input
    - POST_* hooks run after an action and receive the result
    """

    # Query hooks - wrap the entire query processing
    PRE_QUERY = "pre_query"         # Before processing user query
    POST_QUERY = "post_query"       # After generating response

    # Tool hooks - wrap individual tool executions
    PRE_TOOL = "pre_tool"           # Before tool execution
    POST_TOOL = "post_tool"         # After tool execution

    # Skill hooks - wrap skill invocations
    PRE_SKILL = "pre_skill"         # Before skill execution
    POST_SKILL = "post_skill"       # After skill execution

    # Agent hooks - wrap sub-agent spawning
    PRE_AGENT = "pre_agent"         # Before sub-agent execution
    POST_AGENT = "post_agent"       # After sub-agent execution

    # Session hooks - lifecycle events
    SESSION_START = "session_start" # When a new session begins
    SESSION_END = "session_end"     # When a session ends


@dataclass
class HookContext:
    """Context passed to hooks during execution.

    This provides all relevant information about the current action
    that the hook can use for conditional logic or templating.

    Attributes:
        hook_type: The type of hook being executed
        name: Name of the tool/skill/agent (if applicable)
        input_data: Input to the tool/skill/agent
        output_data: Output from the tool/skill/agent (for POST hooks)
        success: Whether the action succeeded (for POST hooks)
        error: Error message if action failed
        duration_seconds: How long the action took (for POST hooks)
        metadata: Additional context-specific metadata
        timestamp: When this context was created
        session_id: Current session identifier
    """
    hook_type: HookType
    name: Optional[str] = None
    input_data: Optional[Any] = None
    output_data: Optional[Any] = None
    success: bool = True
    error: Optional[str] = None
    duration_seconds: float = 0.0
    metadata: Dict[str, Any] = field(default_factory=dict)
    timestamp: float = field(default_factory=time.time)
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for templating."""
        return {
            "hook_type": self.hook_type.value,
            "name": self.name or "",
            "input": self.input_data,
            "output": self.output_data,
            "success": self.success,
            "error": self.error or "",
            "duration": self.duration_seconds,
            "timestamp": self.timestamp,
            "session_id": self.session_id or "",
            **self.metadata
        }

    def format_template(self, template: str) -> str:
        """Format a template string with context values.

        Supports {variable} syntax for substitution.

        Args:
            template: Template string with {variable} placeholders

        Returns:
            Formatted string with placeholders replaced
        """
        context_dict = self.to_dict()
        try:
            # Handle nested access like {metadata.key}
            result = template
            for key, value in context_dict.items():
                placeholder = "{" + key + "}"
                if placeholder in result:
                    result = result.replace(placeholder, str(value))
            return result
        except Exception:
            return template


@dataclass
class HookResult:
    """Result of executing a hook.

    Attributes:
        success: Whether the hook executed successfully
        output: Any output from the hook (stdout for shell commands)
        error: Error message if hook failed
        modified_input: Modified input data (for PRE hooks that transform input)
        should_skip: If True, skip the wrapped action (for PRE hooks)
        duration_seconds: How long the hook took to execute
    """
    success: bool = True
    output: Optional[str] = None
    error: Optional[str] = None
    modified_input: Optional[Any] = None
    should_skip: bool = False
    duration_seconds: float = 0.0


@dataclass
class Hook:
    """A hook definition.

    Hooks can be defined as:
    1. Shell commands - executed via subprocess
    2. Python functions - called directly

    Attributes:
        name: Unique identifier for the hook
        hook_type: When this hook should execute
        command: Shell command to execute (mutually exclusive with func)
        func: Python function to call (mutually exclusive with command)
        condition: Optional condition for execution (template string evaluates to bool)
        timeout: Maximum execution time in seconds
        enabled: Whether this hook is active
        blocking: If True, wait for hook completion before continuing
        target_names: List of specific tool/skill/agent names to trigger on (empty = all)
        description: Human-readable description
        source: Where this hook was loaded from (config, file path, etc.)
    """
    name: str
    hook_type: HookType
    command: Optional[str] = None
    func: Optional[Callable[[HookContext], HookResult]] = None
    condition: Optional[str] = None
    timeout: float = 30.0
    enabled: bool = True
    blocking: bool = True
    target_names: List[str] = field(default_factory=list)
    description: str = ""
    source: str = "unknown"

    def __post_init__(self):
        """Validate hook configuration."""
        if not self.command and not self.func:
            raise ValueError(f"Hook '{self.name}' must have either 'command' or 'func'")
        if self.command and self.func:
            raise ValueError(f"Hook '{self.name}' cannot have both 'command' and 'func'")

    def matches_target(self, target_name: Optional[str]) -> bool:
        """Check if this hook should run for the given target.

        Args:
            target_name: Name of the tool/skill/agent

        Returns:
            True if hook should run for this target
        """
        if not self.target_names:
            # No filter - run for all targets
            return True
        if not target_name:
            return False
        return target_name in self.target_names

    def evaluate_condition(self, context: HookContext) -> bool:
        """Evaluate the condition string against the context.

        The condition is a simple expression that supports:
        - {variable} == value
        - {variable} != value
        - {variable} (truthy check)
        - not {variable} (falsy check)

        Args:
            context: Current hook context

        Returns:
            True if condition is met or no condition exists
        """
        if not self.condition:
            return True

        try:
            # Format template variables
            formatted = context.format_template(self.condition)

            # Simple condition evaluation
            if "==" in formatted:
                left, right = formatted.split("==", 1)
                return left.strip().lower() == right.strip().lower()
            elif "!=" in formatted:
                left, right = formatted.split("!=", 1)
                return left.strip().lower() != right.strip().lower()
            elif formatted.startswith("not "):
                value = formatted[4:].strip().lower()
                return value in ("", "false", "none", "0", "null")
            else:
                # Truthy check
                value = formatted.strip().lower()
                return value not in ("", "false", "none", "0", "null")
        except Exception:
            # On error, assume condition is met
            return True

    def to_dict(self) -> Dict[str, Any]:
        """Convert hook to dictionary for serialization."""
        return {
            "name": self.name,
            "hook_type": self.hook_type.value,
            "command": self.command,
            "condition": self.condition,
            "timeout": self.timeout,
            "enabled": self.enabled,
            "blocking": self.blocking,
            "target_names": self.target_names,
            "description": self.description,
            "source": self.source,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Hook":
        """Create a Hook from a dictionary.

        Args:
            data: Dictionary with hook configuration

        Returns:
            Hook instance
        """
        hook_type_str = data.get("hook_type", "post_tool")
        try:
            hook_type = HookType(hook_type_str)
        except ValueError:
            hook_type = HookType.POST_TOOL

        return cls(
            name=data.get("name", "unnamed"),
            hook_type=hook_type,
            command=data.get("command"),
            condition=data.get("condition"),
            timeout=data.get("timeout", 30.0),
            enabled=data.get("enabled", True),
            blocking=data.get("blocking", True),
            target_names=data.get("target_names", []),
            description=data.get("description", ""),
            source=data.get("source", "dict"),
        )
