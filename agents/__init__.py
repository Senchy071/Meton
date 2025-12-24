"""Sub-agents module for Meton.

This module provides Claude Code-style sub-agents that can be delegated
to for specialized tasks with isolated context.
"""

from agents.subagent import SubAgent, SubAgentParseError, SubAgentValidationError, SubAgentLoader
from agents.subagent_spawner import (
    SubAgentSpawner,
    SubAgentManager,
    SubAgentResult,
    SubAgentError,
    SubAgentSpawnError,
    SubAgentExecutionError,
)

__all__ = [
    "SubAgent",
    "SubAgentParseError",
    "SubAgentValidationError",
    "SubAgentLoader",
    "SubAgentSpawner",
    "SubAgentManager",
    "SubAgentResult",
    "SubAgentError",
    "SubAgentSpawnError",
    "SubAgentExecutionError",
]
