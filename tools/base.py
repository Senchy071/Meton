"""Base tool interface for Meton tools.

This module provides the base class that all Meton tools inherit from,
ensuring consistent error handling, logging, and LangChain integration.

Example:
    >>> from tools.base import MetonBaseTool
    >>> class MyTool(MetonBaseTool):
    ...     name = "my_tool"
    ...     description = "Does something useful"
    ...     def _run(self, input_str: str) -> str:
    ...         return "Result"
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from langchain.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field
import logging


# Custom Exceptions
class ToolError(Exception):
    """Base exception for tool-related errors."""
    pass


class ToolExecutionError(ToolError):
    """Tool execution failed."""
    pass


class ToolValidationError(ToolError):
    """Tool input validation failed."""
    pass


class ToolConfig(BaseModel):
    """Base configuration for tools."""
    enabled: bool = True
    verbose: bool = False


class MetonBaseTool(LangChainBaseTool, ABC):
    """Base class for Meton tools with additional functionality.

    Provides:
    - Consistent error handling
    - Logging integration
    - Enable/disable functionality
    - Tool validation
    - LangChain compatibility

    Subclasses must implement _run() method.
    """

    config: ToolConfig = Field(default_factory=ToolConfig)
    logger: Optional[logging.Logger] = Field(default=None)

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    @abstractmethod
    def _run(self, *args, **kwargs) -> str:
        """Execute the tool (must be implemented by subclasses).

        Args:
            *args: Tool-specific positional arguments
            **kwargs: Tool-specific keyword arguments

        Returns:
            Tool output as string

        Raises:
            ToolExecutionError: If execution fails
        """
        pass

    async def _arun(self, *args, **kwargs) -> str:
        """Async execution (defaults to sync implementation).

        Args:
            *args: Tool-specific positional arguments
            **kwargs: Tool-specific keyword arguments

        Returns:
            Tool output as string
        """
        return self._run(*args, **kwargs)

    def _handle_error(self, error: Exception, context: str = "") -> str:
        """Handle tool execution errors consistently.

        Args:
            error: The exception that occurred
            context: Optional context about what was being attempted

        Returns:
            User-friendly error message

        Example:
            >>> try:
            ...     # some operation
            ... except Exception as e:
            ...     return self._handle_error(e, "reading file")
        """
        error_msg = f"✗ {self.name} error"
        if context:
            error_msg += f" while {context}"
        error_msg += f": {str(error)}"

        if self.logger:
            # Log error message
            self.logger.error(error_msg)

        return error_msg

    def _log_execution(self, action: str, details: str = "") -> None:
        """Log tool execution for debugging.

        Args:
            action: Action being performed
            details: Additional details about the action

        Example:
            >>> self._log_execution("read_file", "path=/home/user/file.txt")
        """
        if self.logger:
            log_msg = f"[{self.name}] {action}"
            if details:
                log_msg += f" - {details}"
            self.logger.debug(log_msg)

    def is_enabled(self) -> bool:
        """Check if tool is enabled.

        Returns:
            True if enabled

        Example:
            >>> tool.is_enabled()
            True
        """
        return self.config.enabled

    def enable(self) -> None:
        """Enable the tool.

        Example:
            >>> tool.enable()
        """
        self.config.enabled = True
        if self.logger:
            self.logger.info(f"Tool '{self.name}' enabled")

    def disable(self) -> None:
        """Disable the tool.

        Example:
            >>> tool.disable()
        """
        self.config.enabled = False
        if self.logger:
            self.logger.info(f"Tool '{self.name}' disabled")

    def get_info(self) -> Dict[str, Any]:
        """Get tool information.

        Returns:
            Dictionary with tool metadata

        Example:
            >>> info = tool.get_info()
            >>> print(info['name'])
        """
        return {
            "name": self.name,
            "description": self.description,
            "enabled": self.config.enabled,
            "verbose": self.config.verbose,
        }

    def validate_execution(self) -> bool:
        """Validate if tool can be executed.

        Returns:
            True if tool can execute

        Raises:
            RuntimeError: If tool is disabled or validation fails

        Example:
            >>> tool.validate_execution()
            True
        """
        if not self.is_enabled():
            raise RuntimeError(f"Tool '{self.name}' is disabled")

        return True


# Alias for convenience
MetonTool = MetonBaseTool
