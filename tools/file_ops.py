"""File operations tools for Meton.

This module provides safe, validated file system operations for the Meton agent.
All operations are constrained by allowed/blocked paths and size limits.

Example:
    >>> from core.config import Config
    >>> from tools.file_ops import FileOperationsTool
    >>>
    >>> config = Config()
    >>> tool = FileOperationsTool(config)
    >>>
    >>> # Read a file
    >>> import json
    >>> input_json = json.dumps({"action": "read", "path": "/path/to/file.py"})
    >>> result = tool._run(input_json)
"""

import os
import json
import fnmatch
from pathlib import Path
from typing import List, Optional, Dict, Any
from pydantic import Field

from tools.base import MetonBaseTool, ToolConfig, ToolError, ToolExecutionError, ToolValidationError
from utils.logger import setup_logger


# Custom Exceptions
class FileOperationError(ToolError):
    """Base exception for file operation errors."""
    pass


class PathNotAllowedError(FileOperationError):
    """Path is outside allowed directories."""
    pass


class FileSizeLimitError(FileOperationError):
    """File exceeds size limit."""
    pass


class FileOpsConfig(ToolConfig):
    """Configuration for file operations tools."""
    allowed_paths: List[str] = Field(default_factory=lambda: ["/media/development/projects/"])
    blocked_paths: List[str] = Field(default_factory=lambda: ["/etc/", "/sys/", "/proc/"])
    max_file_size_mb: int = 10


class FileOperationsTool(MetonBaseTool):
    """Tool for safe file system operations.

    Supports:
    - Reading files (text only)
    - Writing files
    - Listing directory contents
    - Creating directories
    - Checking file existence
    - Getting file information

    All operations are validated against allowed_paths from config.

    Example:
        >>> tool = FileOperationsTool(config)
        >>> input_json = json.dumps({
        ...     "action": "read",
        ...     "path": "/path/to/file.txt"
        ... })
        >>> result = tool._run(input_json)
    """

    name: str = "file_operations"
    description: str = """Perform file system operations safely.

Input format: JSON string with 'action' and parameters:

Actions:
- read: {"action": "read", "path": "/path/to/file"}
- write: {"action": "write", "path": "/path/to/file", "content": "text"}
- list: {"action": "list", "path": "/path/to/directory"}
- find: {"action": "find", "path": "/path/to/directory", "pattern": "*.py", "recursive": true}
- create_dir: {"action": "create_dir", "path": "/path/to/directory"}
- exists: {"action": "exists", "path": "/path/to/file"}
- get_info: {"action": "get_info", "path": "/path/to/file"}

Returns: Operation result or error message."""

    def __init__(self, config):
        """Initialize with configuration.

        Args:
            config: ConfigLoader instance with tools.file_ops settings
        """
        super().__init__()

        # Get config values - store in private attributes to avoid Pydantic validation
        file_ops_config = config.config.tools.file_ops
        object.__setattr__(self, '_allowed_paths', [Path(p) for p in file_ops_config.allowed_paths])
        object.__setattr__(self, '_blocked_paths', [Path(p) for p in file_ops_config.blocked_paths])
        object.__setattr__(self, '_max_file_size', file_ops_config.max_file_size_mb * 1024 * 1024)

        # Setup logger
        object.__setattr__(self, 'logger', setup_logger(
            name="meton_file_ops",
            config=config.config.logging.model_dump()
        ))

        if self.logger:
            self.logger.info("FileOperationsTool initialized")
            self.logger.debug(f"Allowed paths: {self._allowed_paths}")
            self.logger.debug(f"Blocked paths: {self._blocked_paths}")
            self.logger.debug(f"Max file size: {self._max_file_size / (1024*1024)}MB")

    def _run(self, tool_input: str) -> str:
        """Execute file operation based on JSON input.

        Args:
            tool_input: JSON string with action and parameters

        Returns:
            Operation result or error message

        Example:
            >>> input_json = json.dumps({"action": "read", "path": "/path/to/file"})
            >>> result = tool._run(input_json)
        """
        try:
            # Parse JSON input
            try:
                params = json.loads(tool_input)
            except json.JSONDecodeError as e:
                return self._handle_error(e, "parsing JSON input")

            # Validate input structure
            if not isinstance(params, dict):
                return "✗ Input must be a JSON object with 'action' key"

            if "action" not in params:
                return "✗ Missing 'action' in input"

            action = params.get("action")

            # Validate that 'path' is provided for all actions
            if "path" not in params:
                return f"✗ Missing required parameter 'path' for action '{action}'"

            path_str = params.get("path", "")

            # Validate path is not empty
            if not path_str or not path_str.strip():
                return f"✗ Parameter 'path' cannot be empty for action '{action}'"

            # Route to appropriate method
            if action == "read":
                return self._read_file(Path(path_str))
            elif action == "write":
                content = params.get("content", "")
                return self._write_file(Path(path_str), content)
            elif action == "list":
                return self._list_directory(Path(path_str))
            elif action == "find":
                pattern = params.get("pattern", "*")
                recursive = params.get("recursive", True)
                return self._find_files(Path(path_str), pattern, recursive)
            elif action == "create_dir":
                return self._create_directory(Path(path_str))
            elif action == "exists":
                return self._check_exists(Path(path_str))
            elif action == "get_info":
                return self._get_info(Path(path_str))
            else:
                return f"✗ Unknown action: {action}. Valid actions: read, write, list, find, create_dir, exists, get_info"

        except Exception as e:
            return self._handle_error(e, "executing file operation")

    def _validate_path(self, path: Path) -> None:
        """Validate path is safe to access.

        Args:
            path: Path to validate

        Raises:
            PathNotAllowedError: If path is not safe
            ValueError: If path validation fails

        Example:
            >>> self._validate_path(Path("/media/development/projects/meton/file.py"))
        """
        try:
            # Resolve to absolute path
            resolved_path = path.resolve()

            # Check if path is blocked
            for blocked in self._blocked_paths:
                if str(resolved_path).startswith(str(blocked.resolve())):
                    raise PathNotAllowedError(
                        f"✗ Path {path} is blocked for security reasons"
                    )

            # Check if path is in allowed directories
            if self._allowed_paths:
                is_allowed = False
                for allowed in self._allowed_paths:
                    try:
                        # Check if path is within allowed directory
                        resolved_path.relative_to(allowed.resolve())
                        is_allowed = True
                        break
                    except ValueError:
                        # Not relative to this allowed path
                        continue

                if not is_allowed:
                    raise PathNotAllowedError(
                        f"✗ Path {path} is not in allowed directories"
                    )

        except PathNotAllowedError:
            raise
        except Exception as e:
            raise ValueError(f"Path validation failed: {e}")

    def _read_file(self, path: Path) -> str:
        """Read and return file contents.

        Args:
            path: Path to file

        Returns:
            File contents or error message

        Example:
            >>> content = self._read_file(Path("/path/to/file.py"))
        """
        try:
            self._log_execution("read_file", f"path={path}")

            # Validate path
            self._validate_path(path)

            # Check if file exists
            if not path.exists():
                return f"✗ File does not exist: {path}"

            if not path.is_file():
                return f"✗ Path is not a file: {path}"

            # Check file size
            file_size = path.stat().st_size
            if file_size > self._max_file_size:
                size_mb = file_size / (1024 * 1024)
                limit_mb = self._max_file_size / (1024 * 1024)
                raise FileSizeLimitError(
                    f"✗ File is {size_mb:.1f}MB, exceeds limit of {limit_mb:.0f}MB"
                )

            # Try to read as text
            try:
                with open(path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Count lines
                line_count = content.count('\n') + 1

                if self.logger:
                    self.logger.info(f"Read {line_count} lines from {path}")

                return f"✓ Read {line_count} lines from {path}\n\n{content}"

            except UnicodeDecodeError:
                return f"✗ File {path} appears to be binary (not text)"

        except (PathNotAllowedError, FileSizeLimitError) as e:
            return str(e)
        except Exception as e:
            return self._handle_error(e, f"reading file {path}")

    def _write_file(self, path: Path, content: str) -> str:
        """Write content to file.

        Args:
            path: Path to file
            content: Content to write

        Returns:
            Success message or error

        Example:
            >>> result = self._write_file(Path("/path/to/file.py"), "print('hello')")
        """
        try:
            self._log_execution("write_file", f"path={path}, size={len(content)}")

            # Validate path
            self._validate_path(path)

            # Create parent directories if needed
            path.parent.mkdir(parents=True, exist_ok=True)

            # Check content size
            content_size = len(content.encode('utf-8'))
            if content_size > self._max_file_size:
                size_mb = content_size / (1024 * 1024)
                limit_mb = self._max_file_size / (1024 * 1024)
                raise FileSizeLimitError(
                    f"✗ Content is {size_mb:.1f}MB, exceeds limit of {limit_mb:.0f}MB"
                )

            # Write file
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Count lines
            line_count = content.count('\n') + 1

            if self.logger:
                self.logger.info(f"Wrote {line_count} lines to {path}")

            return f"✓ Wrote {line_count} lines ({len(content)} characters) to {path}"

        except (PathNotAllowedError, FileSizeLimitError) as e:
            return str(e)
        except Exception as e:
            return self._handle_error(e, f"writing file {path}")

    def _list_directory(self, path: Path) -> str:
        """List directory contents.

        Args:
            path: Path to directory

        Returns:
            Directory listing or error message

        Example:
            >>> listing = self._list_directory(Path("/path/to/directory"))
        """
        try:
            self._log_execution("list_directory", f"path={path}")

            # Validate path
            self._validate_path(path)

            # Check if directory exists
            if not path.exists():
                return f"✗ Directory does not exist: {path}"

            if not path.is_dir():
                return f"✗ Path is not a directory: {path}"

            # List contents
            items = []
            dir_count = 0
            file_count = 0

            for item in sorted(path.iterdir()):
                # Skip hidden files
                if item.name.startswith('.'):
                    continue

                if item.is_dir():
                    items.append(f"  📁 {item.name}/")
                    dir_count += 1
                else:
                    size = item.stat().st_size
                    if size < 1024:
                        size_str = f"{size}B"
                    elif size < 1024 * 1024:
                        size_str = f"{size/1024:.1f}KB"
                    else:
                        size_str = f"{size/(1024*1024):.1f}MB"

                    items.append(f"  📄 {item.name} ({size_str})")
                    file_count += 1

            if not items:
                return f"✓ Directory {path} is empty"

            if self.logger:
                self.logger.info(f"Listed {len(items)} items in {path}")

            header = f"✓ Contents of {path}\n"
            header += f"  {dir_count} directories, {file_count} files\n\n"
            return header + "\n".join(items)

        except PathNotAllowedError as e:
            return str(e)
        except Exception as e:
            return self._handle_error(e, f"listing directory {path}")

    def _find_files(self, path: Path, pattern: str = "*", recursive: bool = True) -> str:
        """Find files matching a pattern, optionally recursively.

        Args:
            path: Root directory to search from
            pattern: Glob pattern to match (e.g., "*.py", "test_*.py")
            recursive: If True, search recursively; if False, search only in path

        Returns:
            List of matching file paths (absolute) or error message

        Example:
            >>> result = self._find_files(Path("/path/to/dir"), "*.py", True)
        """
        # Directories to skip during recursive search
        EXCLUDED_DIRS = {
            '__pycache__',
            'venv',
            '.venv',
            'env',
            'ENV',
            '.git',
            'node_modules',
            '.idea',
            '.vscode',
            'build',
            'dist',
            '.eggs',
            '*.egg-info'
        }

        try:
            self._log_execution("find_files", f"path={path}, pattern={pattern}, recursive={recursive}")

            # Validate path
            self._validate_path(path)

            # Check if directory exists
            if not path.exists():
                return f"✗ Directory does not exist: {path}"

            if not path.is_dir():
                return f"✗ Path is not a directory: {path}"

            matching_files = []

            if recursive:
                # Recursive search using os.walk
                for root, dirs, files in os.walk(path):
                    # Skip excluded directories (modify dirs in-place to prevent descent)
                    dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS and not d.startswith('.')]

                    # Find matching files in current directory
                    for filename in files:
                        if fnmatch.fnmatch(filename, pattern):
                            full_path = Path(root) / filename
                            matching_files.append(str(full_path.resolve()))
            else:
                # Non-recursive search (only immediate children)
                for item in path.iterdir():
                    if item.is_file() and fnmatch.fnmatch(item.name, pattern):
                        matching_files.append(str(item.resolve()))

            # Sort results for consistent output
            matching_files.sort()

            if not matching_files:
                search_type = "recursively" if recursive else "in directory"
                return f"✗ No files matching '{pattern}' found {search_type} in {path}"

            if self.logger:
                self.logger.info(f"Found {len(matching_files)} files matching '{pattern}' in {path}")

            # Format output
            header = f"✓ Found {len(matching_files)} file(s) matching '{pattern}'"
            if recursive:
                header += f" (recursive search from {path})"
            else:
                header += f" (in {path})"
            header += "\n\n"

            file_list = "\n".join(matching_files)
            return header + file_list

        except PathNotAllowedError as e:
            return str(e)
        except Exception as e:
            return self._handle_error(e, f"finding files matching '{pattern}' in {path}")

    def _create_directory(self, path: Path) -> str:
        """Create directory (and parents if needed).

        Args:
            path: Path to directory

        Returns:
            Success message or error

        Example:
            >>> result = self._create_directory(Path("/path/to/new/directory"))
        """
        try:
            self._log_execution("create_directory", f"path={path}")

            # Validate path
            self._validate_path(path)

            # Check if already exists
            if path.exists():
                if path.is_dir():
                    return f"✓ Directory already exists: {path}"
                else:
                    return f"✗ Path exists but is not a directory: {path}"

            # Create directory
            path.mkdir(parents=True, exist_ok=True)

            if self.logger:
                self.logger.info(f"Created directory {path}")

            return f"✓ Created directory: {path}"

        except PathNotAllowedError as e:
            return str(e)
        except Exception as e:
            return self._handle_error(e, f"creating directory {path}")

    def _check_exists(self, path: Path) -> str:
        """Check if path exists.

        Args:
            path: Path to check

        Returns:
            Existence status

        Example:
            >>> result = self._check_exists(Path("/path/to/file"))
        """
        try:
            self._log_execution("check_exists", f"path={path}")

            # Validate path
            self._validate_path(path)

            if path.exists():
                if path.is_file():
                    return f"✓ File exists: {path}"
                elif path.is_dir():
                    return f"✓ Directory exists: {path}"
                else:
                    return f"✓ Path exists (special file): {path}"
            else:
                return f"✗ Path does not exist: {path}"

        except PathNotAllowedError as e:
            return str(e)
        except Exception as e:
            return self._handle_error(e, f"checking existence of {path}")

    def _get_info(self, path: Path) -> str:
        """Get file/directory information.

        Args:
            path: Path to inspect

        Returns:
            File/directory information or error

        Example:
            >>> info = self._get_info(Path("/path/to/file"))
        """
        try:
            self._log_execution("get_info", f"path={path}")

            # Validate path
            self._validate_path(path)

            # Check if exists
            if not path.exists():
                return f"✗ Path does not exist: {path}"

            # Get stats
            stats = path.stat()

            # Build info
            info_lines = [f"✓ Information for {path}\n"]

            # Type
            if path.is_file():
                info_lines.append(f"  Type: File")
            elif path.is_dir():
                info_lines.append(f"  Type: Directory")
            else:
                info_lines.append(f"  Type: Special")

            # Size
            size = stats.st_size
            if size < 1024:
                size_str = f"{size}B"
            elif size < 1024 * 1024:
                size_str = f"{size/1024:.1f}KB"
            else:
                size_str = f"{size/(1024*1024):.1f}MB"
            info_lines.append(f"  Size: {size_str}")

            # Permissions
            import stat
            mode = stats.st_mode
            perms = stat.filemode(mode)
            info_lines.append(f"  Permissions: {perms}")

            # Modified time
            from datetime import datetime
            mtime = datetime.fromtimestamp(stats.st_mtime)
            info_lines.append(f"  Modified: {mtime.strftime('%Y-%m-%d %H:%M:%S')}")

            # For files, add line count
            if path.is_file():
                try:
                    with open(path, 'r', encoding='utf-8') as f:
                        line_count = sum(1 for _ in f)
                    info_lines.append(f"  Lines: {line_count}")
                except (UnicodeDecodeError, IOError):
                    # Binary file or read error - skip line count
                    pass

            if self.logger:
                self.logger.info(f"Got info for {path}")

            return "\n".join(info_lines)

        except PathNotAllowedError as e:
            return str(e)
        except Exception as e:
            return self._handle_error(e, f"getting info for {path}")
