"""Hooks System for Meton.

This package provides pre/post execution hooks for tools, skills, agents, and queries.
Hooks enable event-driven automation and customization of the agent's behavior.

Example:
    >>> from hooks import HookManager, Hook, HookType
    >>>
    >>> manager = HookManager()
    >>> hook = Hook(
    ...     name="log_tool_usage",
    ...     hook_type=HookType.POST_TOOL,
    ...     command="echo 'Tool executed: {tool_name}'"
    ... )
    >>> manager.register(hook)
"""

from hooks.base import Hook, HookType, HookResult, HookContext
from hooks.hook_manager import HookManager
from hooks.hook_loader import HookLoader

__all__ = [
    "Hook",
    "HookType",
    "HookResult",
    "HookContext",
    "HookManager",
    "HookLoader",
]
