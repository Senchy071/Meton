"""Hook Manager for Meton.

This module provides the HookManager class which handles:
- Registration of hooks
- Execution of hooks at appropriate points
- Hook lifecycle management

Example:
    >>> from hooks import HookManager, Hook, HookType, HookContext
    >>>
    >>> manager = HookManager()
    >>> manager.register(Hook(
    ...     name="log_tools",
    ...     hook_type=HookType.POST_TOOL,
    ...     command="echo 'Used tool: {name}'"
    ... ))
    >>>
    >>> context = HookContext(hook_type=HookType.POST_TOOL, name="file_operations")
    >>> results = manager.execute(context)
"""

import logging
import subprocess
import threading
import time
from typing import Dict, List, Optional, Any, Callable
from collections import defaultdict

from hooks.base import Hook, HookType, HookContext, HookResult


class HookManager:
    """Manages hook registration and execution.

    The HookManager is the central coordinator for all hooks in Meton.
    It maintains a registry of hooks organized by type and handles
    execution with proper error handling and timeout management.

    Attributes:
        hooks: Dictionary mapping HookType to list of registered hooks
        enabled: Global enable/disable switch for all hooks
        logger: Logger instance for hook events
    """

    def __init__(self, enabled: bool = True):
        """Initialize the hook manager.

        Args:
            enabled: Whether hooks are globally enabled
        """
        self.hooks: Dict[HookType, List[Hook]] = defaultdict(list)
        self.enabled = enabled
        self.logger = logging.getLogger("meton.hooks")
        self._lock = threading.Lock()
        self._execution_history: List[Dict[str, Any]] = []
        self._max_history = 100

    def register(self, hook: Hook) -> bool:
        """Register a hook.

        Args:
            hook: Hook to register

        Returns:
            True if registration succeeded
        """
        with self._lock:
            # Check for duplicate names
            for existing in self.hooks[hook.hook_type]:
                if existing.name == hook.name:
                    self.logger.warning(f"Hook '{hook.name}' already registered, replacing")
                    self.hooks[hook.hook_type].remove(existing)
                    break

            self.hooks[hook.hook_type].append(hook)
            self.logger.debug(f"Registered hook: {hook.name} ({hook.hook_type.value})")
            return True

    def unregister(self, name: str, hook_type: Optional[HookType] = None) -> bool:
        """Unregister a hook by name.

        Args:
            name: Name of hook to remove
            hook_type: Specific type to search in (None = search all)

        Returns:
            True if hook was found and removed
        """
        with self._lock:
            types_to_search = [hook_type] if hook_type else list(HookType)

            for ht in types_to_search:
                hooks = self.hooks.get(ht, [])
                for hook in hooks:
                    if hook.name == name:
                        hooks.remove(hook)
                        self.logger.debug(f"Unregistered hook: {name}")
                        return True

            return False

    def get_hook(self, name: str) -> Optional[Hook]:
        """Get a hook by name.

        Args:
            name: Hook name to find

        Returns:
            Hook instance or None if not found
        """
        with self._lock:
            for hooks in self.hooks.values():
                for hook in hooks:
                    if hook.name == name:
                        return hook
            return None

    def list_hooks(self, hook_type: Optional[HookType] = None) -> List[Hook]:
        """List all registered hooks.

        Args:
            hook_type: Filter by type (None = all types)

        Returns:
            List of hooks
        """
        with self._lock:
            if hook_type:
                return list(self.hooks.get(hook_type, []))
            else:
                result = []
                for hooks in self.hooks.values():
                    result.extend(hooks)
                return result

    def execute(
        self,
        context: HookContext,
        target_name: Optional[str] = None
    ) -> List[HookResult]:
        """Execute all matching hooks for a context.

        Args:
            context: The hook context with current state
            target_name: Name of tool/skill/agent (for filtering)

        Returns:
            List of results from each hook execution
        """
        if not self.enabled:
            return []

        results = []
        hooks = self.get_matching_hooks(context.hook_type, target_name)

        for hook in hooks:
            if not hook.enabled:
                continue

            if not hook.evaluate_condition(context):
                self.logger.debug(f"Hook '{hook.name}' condition not met, skipping")
                continue

            result = self._execute_hook(hook, context)
            results.append(result)

            # Record in history
            self._record_execution(hook, context, result)

            # If hook failed and is blocking, log warning
            if not result.success and hook.blocking:
                self.logger.warning(
                    f"Blocking hook '{hook.name}' failed: {result.error}"
                )

        return results

    def get_matching_hooks(
        self,
        hook_type: HookType,
        target_name: Optional[str] = None
    ) -> List[Hook]:
        """Get hooks that match the type and target.

        Args:
            hook_type: Type of hook to find
            target_name: Name of tool/skill/agent to filter by

        Returns:
            List of matching hooks
        """
        with self._lock:
            hooks = self.hooks.get(hook_type, [])
            return [h for h in hooks if h.matches_target(target_name)]

    def _execute_hook(self, hook: Hook, context: HookContext) -> HookResult:
        """Execute a single hook.

        Args:
            hook: Hook to execute
            context: Execution context

        Returns:
            Result of hook execution
        """
        start_time = time.time()

        try:
            if hook.func:
                # Python function hook
                result = hook.func(context)
                result.duration_seconds = time.time() - start_time
                return result
            elif hook.command:
                # Shell command hook
                return self._execute_shell_hook(hook, context)
            else:
                return HookResult(
                    success=False,
                    error="Hook has no command or function",
                    duration_seconds=time.time() - start_time
                )
        except Exception as e:
            self.logger.error(f"Hook '{hook.name}' execution error: {e}")
            return HookResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )

    def _execute_shell_hook(self, hook: Hook, context: HookContext) -> HookResult:
        """Execute a shell command hook.

        Args:
            hook: Hook with shell command
            context: Execution context

        Returns:
            Result of shell execution
        """
        start_time = time.time()

        try:
            # Format command with context
            command = context.format_template(hook.command)

            self.logger.debug(f"Executing hook '{hook.name}': {command}")

            # Prepare environment with context
            env = {
                "HOOK_NAME": hook.name,
                "HOOK_TYPE": context.hook_type.value,
                "TARGET_NAME": context.name or "",
                "SUCCESS": str(context.success).lower(),
                "DURATION": str(context.duration_seconds),
            }

            # Run command
            process = subprocess.run(
                command,
                shell=True,
                capture_output=True,
                text=True,
                timeout=hook.timeout,
                env={**subprocess.os.environ, **env}
            )

            duration = time.time() - start_time

            if process.returncode == 0:
                return HookResult(
                    success=True,
                    output=process.stdout.strip(),
                    duration_seconds=duration
                )
            else:
                return HookResult(
                    success=False,
                    output=process.stdout.strip(),
                    error=process.stderr.strip() or f"Exit code: {process.returncode}",
                    duration_seconds=duration
                )

        except subprocess.TimeoutExpired:
            return HookResult(
                success=False,
                error=f"Hook timed out after {hook.timeout}s",
                duration_seconds=hook.timeout
            )
        except Exception as e:
            return HookResult(
                success=False,
                error=str(e),
                duration_seconds=time.time() - start_time
            )

    def _record_execution(
        self,
        hook: Hook,
        context: HookContext,
        result: HookResult
    ):
        """Record hook execution in history.

        Args:
            hook: Executed hook
            context: Execution context
            result: Execution result
        """
        with self._lock:
            self._execution_history.append({
                "hook_name": hook.name,
                "hook_type": hook.hook_type.value,
                "target_name": context.name,
                "success": result.success,
                "duration": result.duration_seconds,
                "timestamp": time.time(),
                "error": result.error,
            })

            # Trim history
            if len(self._execution_history) > self._max_history:
                self._execution_history = self._execution_history[-self._max_history:]

    def get_history(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Get recent hook execution history.

        Args:
            limit: Maximum number of entries to return

        Returns:
            List of execution records
        """
        with self._lock:
            return list(self._execution_history[-limit:])

    def clear_history(self):
        """Clear execution history."""
        with self._lock:
            self._execution_history.clear()

    def enable_all(self):
        """Enable all hooks globally."""
        self.enabled = True
        self.logger.info("Hooks globally enabled")

    def disable_all(self):
        """Disable all hooks globally."""
        self.enabled = False
        self.logger.info("Hooks globally disabled")

    def enable_hook(self, name: str) -> bool:
        """Enable a specific hook.

        Args:
            name: Hook name to enable

        Returns:
            True if hook was found and enabled
        """
        hook = self.get_hook(name)
        if hook:
            hook.enabled = True
            return True
        return False

    def disable_hook(self, name: str) -> bool:
        """Disable a specific hook.

        Args:
            name: Hook name to disable

        Returns:
            True if hook was found and disabled
        """
        hook = self.get_hook(name)
        if hook:
            hook.enabled = False
            return True
        return False

    def clear(self):
        """Remove all registered hooks."""
        with self._lock:
            self.hooks.clear()
            self.logger.info("All hooks cleared")

    def get_stats(self) -> Dict[str, Any]:
        """Get hook statistics.

        Returns:
            Dictionary with hook counts and execution stats
        """
        with self._lock:
            total_hooks = sum(len(hooks) for hooks in self.hooks.values())
            enabled_hooks = sum(
                1 for hooks in self.hooks.values()
                for h in hooks if h.enabled
            )

            # Execution stats
            total_executions = len(self._execution_history)
            successful = sum(1 for e in self._execution_history if e["success"])

            return {
                "total_hooks": total_hooks,
                "enabled_hooks": enabled_hooks,
                "disabled_hooks": total_hooks - enabled_hooks,
                "globally_enabled": self.enabled,
                "hooks_by_type": {
                    ht.value: len(hooks) for ht, hooks in self.hooks.items()
                },
                "total_executions": total_executions,
                "successful_executions": successful,
                "failed_executions": total_executions - successful,
            }


# Convenience functions for creating common hooks

def create_logging_hook(
    name: str,
    hook_type: HookType,
    log_message: str,
    target_names: Optional[List[str]] = None
) -> Hook:
    """Create a hook that logs a message.

    Args:
        name: Hook name
        hook_type: When to execute
        log_message: Message template to log
        target_names: Optional filter for specific targets

    Returns:
        Configured Hook instance
    """
    def log_func(context: HookContext) -> HookResult:
        message = context.format_template(log_message)
        logging.getLogger("meton.hooks.user").info(message)
        return HookResult(success=True, output=message)

    return Hook(
        name=name,
        hook_type=hook_type,
        func=log_func,
        target_names=target_names or [],
        description=f"Logs: {log_message}",
        source="create_logging_hook()",
    )


def create_notification_hook(
    name: str,
    hook_type: HookType,
    title: str,
    message: str,
    condition: Optional[str] = None
) -> Hook:
    """Create a hook that sends a desktop notification.

    Args:
        name: Hook name
        hook_type: When to execute
        title: Notification title template
        message: Notification message template
        condition: Optional condition for execution

    Returns:
        Configured Hook instance
    """
    # Use notify-send on Linux
    command = f"notify-send '{title}' '{message}'"

    return Hook(
        name=name,
        hook_type=hook_type,
        command=command,
        condition=condition,
        blocking=False,  # Don't wait for notification
        description=f"Desktop notification: {title}",
        source="create_notification_hook()",
    )
