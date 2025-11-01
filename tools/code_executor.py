"""Code execution tools for Meton.

This module provides safe Python code execution using subprocess isolation,
AST-based import validation, and timeout protection.

Example:
    >>> from core.config import Config
    >>> from tools.code_executor import CodeExecutorTool
    >>>
    >>> config = Config()
    >>> tool = CodeExecutorTool(config)
    >>>
    >>> # Execute simple code
    >>> import json
    >>> input_json = json.dumps({"code": "print(2 + 2)"})
    >>> result = tool._run(input_json)
"""

import os
import ast
import json
import time
import subprocess
import tempfile
from pathlib import Path
from typing import List, Dict, Any, Set
from pydantic import Field

from tools.base import MetonBaseTool, ToolConfig, ToolError, ToolExecutionError, ToolValidationError
from utils.logger import setup_logger


# Custom Exceptions
class CodeExecutionError(ToolError):
    """Base exception for code execution errors."""
    pass


class ImportValidationError(CodeExecutionError):
    """Code contains blocked imports."""
    pass


class TimeoutError(CodeExecutionError):
    """Code execution timed out."""
    pass


class CodeExecutorConfig(ToolConfig):
    """Configuration for code executor tool."""
    enabled: bool = True
    timeout: int = Field(default=5, ge=1)
    max_output_length: int = Field(default=10000, ge=100)


class ImportValidator:
    """Validates Python imports using AST parsing.

    Checks code for dangerous imports before execution.
    """

    # Dangerous imports that can compromise system security
    BLOCKED_IMPORTS = {
        'os', 'sys', 'subprocess', 'socket', 'requests', 'urllib',
        'http', 'ftplib', 'telnetlib', 'poplib', 'imaplib', 'smtplib',
        'multiprocessing', 'threading', 'concurrent', 'asyncio',
        '__import__', 'eval', 'exec', 'compile', 'globals', 'locals',
        'importlib', 'pkgutil', 'runpy', 'pdb', 'code',
        'pty', 'tty', 'termios', 'fcntl', 'select',
        'ctypes', 'cffi', 'resource', 'signal',
    }

    # Safe imports that are allowed
    ALLOWED_IMPORTS = {
        'math', 'json', 'datetime', 'random', 'itertools', 'collections',
        're', 'string', 'decimal', 'fractions', 'statistics',
        'time', 'calendar', 'hashlib', 'hmac', 'secrets',
        'base64', 'binascii', 'struct', 'codecs',
        'copy', 'functools', 'operator', 'typing',
        'dataclasses', 'enum', 'abc',
    }

    # Built-in functions to block
    BLOCKED_BUILTINS = {
        'open', '__import__', 'eval', 'exec', 'compile',
        'globals', 'locals', 'vars', 'dir', 'breakpoint',
    }

    def __init__(self):
        """Initialize validator."""
        pass

    def validate(self, code: str) -> tuple[bool, List[str]]:
        """Validate code for dangerous imports.

        Args:
            code: Python code to validate

        Returns:
            Tuple of (is_valid, list_of_violations)

        Example:
            >>> validator = ImportValidator()
            >>> valid, violations = validator.validate("import os")
            >>> print(valid)  # False
            >>> print(violations)  # ['Blocked import: os']
        """
        violations = []

        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return False, [f"Syntax error: {str(e)}"]

        # Check for imports
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    module_name = alias.name.split('.')[0]
                    if module_name in self.BLOCKED_IMPORTS:
                        violations.append(f"Blocked import: {alias.name}")
                    elif module_name not in self.ALLOWED_IMPORTS:
                        violations.append(f"Unknown/unsafe import: {alias.name}")

            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    module_name = node.module.split('.')[0]
                    if module_name in self.BLOCKED_IMPORTS:
                        violations.append(f"Blocked import: from {node.module}")
                    elif module_name not in self.ALLOWED_IMPORTS:
                        violations.append(f"Unknown/unsafe import: from {node.module}")

            # Check for blocked builtin calls
            elif isinstance(node, ast.Call):
                if isinstance(node.func, ast.Name):
                    if node.func.id in self.BLOCKED_BUILTINS:
                        violations.append(f"Blocked builtin function: {node.func.id}()")

        return len(violations) == 0, violations

    def get_allowed_imports(self) -> Set[str]:
        """Get set of allowed imports.

        Returns:
            Set of allowed module names
        """
        return self.ALLOWED_IMPORTS.copy()

    def get_blocked_imports(self) -> Set[str]:
        """Get set of blocked imports.

        Returns:
            Set of blocked module names
        """
        return self.BLOCKED_IMPORTS.copy()


class CodeExecutorTool(MetonBaseTool):
    """Tool for safe Python code execution.

    Features:
    - Subprocess isolation for safety
    - AST-based import validation
    - Timeout protection
    - Output capture (stdout/stderr)
    - Execution time tracking

    All code is validated before execution to prevent dangerous operations.

    Example:
        >>> tool = CodeExecutorTool(config)
        >>> input_json = json.dumps({
        ...     "code": "import math\\nprint(math.pi)"
        ... })
        >>> result = tool._run(input_json)
    """

    name: str = "code_executor"
    description: str = """Execute Python code safely in isolated subprocess.

Input format: JSON string with 'code' parameter:

Example:
{"code": "import math\\nprint(math.pi)"}

Returns: JSON with execution result:
{
    "success": true/false,
    "output": "stdout output",
    "error": "error message if any",
    "execution_time": 0.123
}

Allowed imports: math, json, datetime, random, itertools, collections, re, string, etc.
Blocked imports: os, sys, subprocess, socket, requests, urllib, etc.
Blocked builtins: open, eval, exec, compile, __import__, etc.
"""

    def __init__(self, config):
        """Initialize with configuration.

        Args:
            config: ConfigLoader instance with tools.code_executor settings
        """
        super().__init__()

        # Get config values
        executor_config = config.config.tools.code_executor
        object.__setattr__(self, '_timeout', executor_config.timeout)
        object.__setattr__(self, '_max_output_length', executor_config.max_output_length)
        object.__setattr__(self, '_validator', ImportValidator())

        # Setup logger
        object.__setattr__(self, 'logger', setup_logger("code_executor"))

        self._log_execution("initialized", f"timeout={self._timeout}s")

    def _run(self, input_str: str) -> str:
        """Execute Python code.

        Args:
            input_str: JSON string with code parameter

        Returns:
            JSON string with execution result

        Raises:
            ToolExecutionError: If execution fails
        """
        try:
            # Parse input
            try:
                input_data = json.loads(input_str)
            except json.JSONDecodeError as e:
                return self._handle_error(e, "parsing JSON input")

            if 'code' not in input_data:
                return json.dumps({
                    "success": False,
                    "output": "",
                    "error": "Missing required 'code' parameter",
                    "execution_time": 0.0
                })

            code = input_data['code']

            # Validate code
            is_valid, violations = self._validator.validate(code)
            if not is_valid:
                self._log_execution("validation_failed", f"violations={len(violations)}")
                return json.dumps({
                    "success": False,
                    "output": "",
                    "error": "Security validation failed:\n" + "\n".join(f"  - {v}" for v in violations),
                    "execution_time": 0.0
                })

            # Execute code
            result = self._execute_code(code)
            return json.dumps(result, indent=2)

        except Exception as e:
            return self._handle_error(e, "executing code")

    def _execute_code(self, code: str) -> Dict[str, Any]:
        """Execute code in subprocess.

        Args:
            code: Python code to execute

        Returns:
            Dict with success, output, error, and execution_time
        """
        start_time = time.time()

        # Create temporary file for code
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(code)
            temp_file = f.name

        try:
            # Execute in subprocess with timeout
            self._log_execution("executing", f"timeout={self._timeout}s")

            process = subprocess.Popen(
                ['python3', temp_file],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )

            try:
                stdout, stderr = process.communicate(timeout=self._timeout)
                execution_time = time.time() - start_time

                # Truncate output if too long
                if len(stdout) > self._max_output_length:
                    stdout = stdout[:self._max_output_length] + "\n... (output truncated)"
                if len(stderr) > self._max_output_length:
                    stderr = stderr[:self._max_output_length] + "\n... (output truncated)"

                success = process.returncode == 0

                self._log_execution(
                    "completed" if success else "failed",
                    f"time={execution_time:.3f}s, returncode={process.returncode}"
                )

                return {
                    "success": success,
                    "output": stdout.strip(),
                    "error": stderr.strip() if stderr else "",
                    "execution_time": round(execution_time, 3)
                }

            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                execution_time = time.time() - start_time

                self._log_execution("timeout", f"exceeded {self._timeout}s")

                return {
                    "success": False,
                    "output": "",
                    "error": f"Code execution timed out after {self._timeout} seconds",
                    "execution_time": round(execution_time, 3)
                }

        finally:
            # Clean up temp file
            try:
                os.unlink(temp_file)
            except Exception:
                pass

    def get_info(self) -> Dict[str, Any]:
        """Get tool information.

        Returns:
            Dictionary with tool metadata including import restrictions
        """
        base_info = super().get_info()
        base_info.update({
            "timeout": self._timeout,
            "max_output_length": self._max_output_length,
            "allowed_imports": sorted(list(self._validator.get_allowed_imports())),
            "blocked_imports": sorted(list(self._validator.get_blocked_imports())),
        })
        return base_info
