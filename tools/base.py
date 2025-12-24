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

import json
import time
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Tuple, Union, TYPE_CHECKING
from langchain.tools import BaseTool as LangChainBaseTool
from pydantic import BaseModel, Field
import logging

if TYPE_CHECKING:
    from hooks import HookManager


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
    - Hook integration (pre/post execution hooks)

    Subclasses must implement _run() method.
    """

    config: ToolConfig = Field(default_factory=ToolConfig)
    logger: Optional[logging.Logger] = Field(default=None)
    hook_manager: Optional[Any] = Field(default=None)

    class Config:
        """Pydantic config."""
        arbitrary_types_allowed = True

    def set_hook_manager(self, manager: "HookManager") -> None:
        """Set the hook manager for this tool.

        Args:
            manager: HookManager instance to use for hook execution
        """
        self.hook_manager = manager

    def run(self, tool_input: str, *args, **kwargs) -> str:
        """Execute the tool with hook support.

        Wraps the _run method with pre/post hooks execution.

        Args:
            tool_input: Input for the tool
            *args: Additional positional arguments
            **kwargs: Additional keyword arguments

        Returns:
            Tool output as string
        """
        from hooks.base import HookType, HookContext

        # Execute pre-tool hooks
        if self.hook_manager:
            pre_context = HookContext(
                hook_type=HookType.PRE_TOOL,
                name=self.name,
                input_data=tool_input,
            )
            pre_results = self.hook_manager.execute(pre_context, self.name)

            # Check if any hook wants to skip execution
            for result in pre_results:
                if result.should_skip:
                    return result.output or "Tool execution skipped by hook"

                # Allow hooks to modify input
                if result.modified_input is not None:
                    tool_input = result.modified_input

        # Execute the tool
        start_time = time.time()
        success = True
        error_msg = None
        output = None

        try:
            output = self._run(tool_input, *args, **kwargs)
        except Exception as e:
            success = False
            error_msg = str(e)
            output = self._handle_error(e)

        duration = time.time() - start_time

        # Execute post-tool hooks
        if self.hook_manager:
            post_context = HookContext(
                hook_type=HookType.POST_TOOL,
                name=self.name,
                input_data=tool_input,
                output_data=output,
                success=success,
                error=error_msg,
                duration_seconds=duration,
            )
            self.hook_manager.execute(post_context, self.name)

        return output

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

    def _parse_json_input(
        self,
        input_str: str,
        required_fields: Optional[List[str]] = None
    ) -> Tuple[bool, Union[Dict[str, Any], str]]:
        """Parse JSON input and validate required fields.

        Provides consistent JSON parsing across all tools.

        Args:
            input_str: JSON string to parse
            required_fields: Optional list of required field names

        Returns:
            Tuple of (success: bool, result: dict or error_message: str)
            - On success: (True, parsed_dict)
            - On failure: (False, error_message)

        Example:
            >>> success, data = self._parse_json_input(input_str, ["query"])
            >>> if not success:
            ...     return data  # data is error message
            >>> query = data["query"]  # data is parsed dict
        """
        try:
            data = json.loads(input_str)
        except json.JSONDecodeError as e:
            return False, f"✗ Invalid JSON input: {str(e)}"

        if not isinstance(data, dict):
            return False, "✗ Input must be a JSON object"

        if required_fields:
            missing = [f for f in required_fields if f not in data]
            if missing:
                return False, f"✗ Missing required field(s): {', '.join(missing)}"

        return True, data

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
