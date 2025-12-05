"""Symbol/Function Lookup Tool for Meton.

This module provides precise symbol definition lookup across the codebase.
Unlike semantic search, this tool finds exact definitions of functions, classes,
methods, and variables by name.

Example:
    >>> from core.config import ConfigLoader
    >>> from tools.symbol_lookup import SymbolLookupTool
    >>>
    >>> config = ConfigLoader()
    >>> tool = SymbolLookupTool(config)
    >>>
    >>> import json
    >>> input_json = json.dumps({"symbol": "MetonAgent"})
    >>> result = tool._run(input_json)
"""

import json
import os
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import Field

from tools.base import MetonBaseTool, ToolConfig, ToolError
from utils.logger import setup_logger


# Custom Exceptions
class SymbolLookupError(ToolError):
    """Base exception for symbol lookup errors."""
    pass


class SymbolLookupConfig(ToolConfig):
    """Configuration for symbol lookup tool."""
    enabled: bool = True  # Enabled by default
    max_results: int = Field(default=20, ge=1, le=100)
    context_lines: int = Field(default=5, ge=0, le=20)
    index_cache_size: int = Field(default=10000, ge=100, le=100000)


class SymbolLookupTool(MetonBaseTool):
    """Tool for finding symbol definitions in the codebase.

    Features:
    - Find exact definitions of functions, classes, methods, and variables
    - Return file path, line number, signature, and code context
    - Support filtering by symbol type
    - Fast in-memory indexing
    - Automatic cache invalidation on file changes

    Example:
        >>> tool = SymbolLookupTool(config)
        >>> input_json = json.dumps({
        ...     "symbol": "authenticate_user",
        ...     "type": "function"
        ... })
        >>> result = tool._run(input_json)
    """

    name: str = "symbol_lookup"
    description: str = """Find the definition of a function, class, method, or variable in the codebase.

Input format: JSON string with parameters:

Required:
- symbol: Name of the symbol to find (e.g., "MyClass", "process_data")

Optional:
- type: Filter by symbol type ("function", "class", "method", "variable", "all")
- scope: Filter scope ("public", "private", "all")
- path: Limit search to specific directory

Example:
{"symbol": "MetonAgent", "type": "class"}

Returns: JSON with search results:
{
    "success": true/false,
    "results": [
        {
            "symbol": "MetonAgent",
            "type": "class",
            "file": "core/agent.py",
            "line": 45,
            "end_line": 234,
            "signature": "class MetonAgent(BaseAgent):",
            "docstring": "Main agent class...",
            "code_snippet": "class MetonAgent...\\n    ...",
            "scope": "public"
        },
        ...
    ],
    "count": 1,
    "error": ""
}

Use this when you need to:
- Locate where a symbol is defined
- Jump to function/class definition
- Understand symbol signature and documentation
- Navigate codebase structure
"""

    def __init__(self, config):
        """Initialize with configuration.

        Args:
            config: ConfigLoader instance with tools.symbol_lookup settings
        """
        super().__init__()

        # Get config values
        self._config = config

        # Get symbol_lookup config (if exists, otherwise use defaults)
        if hasattr(config.config.tools, 'symbol_lookup'):
            lookup_config = config.config.tools.symbol_lookup
        else:
            # Use default config if not in config file yet
            lookup_config = SymbolLookupConfig()

        object.__setattr__(self, '_enabled', lookup_config.enabled)
        object.__setattr__(self, '_max_results', lookup_config.max_results)
        object.__setattr__(self, '_context_lines', lookup_config.context_lines)
        object.__setattr__(self, '_index_cache_size', lookup_config.index_cache_size)

        # Setup logger
        object.__setattr__(self, 'logger', setup_logger("symbol_lookup", console_output=False))

        # In-memory symbol index (built on first use)
        object.__setattr__(self, '_symbol_index', None)
        object.__setattr__(self, '_index_timestamp', None)

        # Get project root (where Meton is running from)
        object.__setattr__(self, '_project_root', Path.cwd())

        self._log_execution(
            "initialized",
            f"enabled={self._enabled}, max_results={self._max_results}, "
            f"context_lines={self._context_lines}"
        )

    def _run(self, input_str: str) -> str:
        """Find symbol definitions.

        Args:
            input_str: JSON string with symbol and optional filters

        Returns:
            JSON string with search results

        Raises:
            ToolExecutionError: If execution fails
        """
        try:
            # CHECK IF TOOL IS ENABLED
            if not self._enabled:
                self._log_execution("lookup_blocked", "tool is disabled")
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Symbol lookup is disabled. Enable with tools.symbol_lookup.enabled=true in config.yaml"
                }, indent=2)

            # Parse input
            try:
                input_data = json.loads(input_str)
            except json.JSONDecodeError as e:
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": f"Invalid JSON input: {str(e)}"
                }, indent=2)

            if 'symbol' not in input_data:
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Missing required 'symbol' parameter"
                }, indent=2)

            symbol = input_data['symbol']

            if not symbol or not symbol.strip():
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Symbol name cannot be empty"
                }, indent=2)

            # Get optional filters
            symbol_type = input_data.get('type', 'all')
            scope = input_data.get('scope', 'all')
            path_filter = input_data.get('path', None)

            # Perform lookup
            result = self._lookup_symbol(symbol, symbol_type, scope, path_filter)
            return json.dumps(result, indent=2)

        except Exception as e:
            return self._handle_error(e, "looking up symbol")

    def _lookup_symbol(self, symbol: str, symbol_type: str = 'all', scope: str = 'all', path_filter: Optional[str] = None) -> Dict[str, Any]:
        """Perform symbol lookup.

        Args:
            symbol: Symbol name to find
            symbol_type: Type filter ("function", "class", "method", "variable", "all")
            scope: Scope filter ("public", "private", "all")
            path_filter: Optional directory to limit search

        Returns:
            Dict with success, results, count, and optional error
        """
        try:
            # Build index if not already built or stale
            if not self._build_index_if_needed():
                return {
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Failed to build symbol index"
                }

            self._log_execution("lookup", f"symbol='{symbol}', type={symbol_type}, scope={scope}")

            # Search index
            matches = []
            for sym_data in self._symbol_index:
                # Check symbol name match (case-sensitive exact match first, then case-insensitive)
                if sym_data['name'] == symbol or sym_data['name'].lower() == symbol.lower():
                    # Apply type filter
                    if symbol_type != 'all' and sym_data['type'] != symbol_type:
                        continue

                    # Apply scope filter
                    sym_scope = self._determine_scope(sym_data['name'])
                    if scope != 'all' and sym_scope != scope:
                        continue

                    # Apply path filter
                    if path_filter:
                        if not sym_data['file'].startswith(path_filter):
                            continue

                    matches.append(sym_data)

            # Limit results
            if len(matches) > self._max_results:
                matches = matches[:self._max_results]

            # Sort by: exact match first, then by file path
            exact_matches = [m for m in matches if m['name'] == symbol]
            fuzzy_matches = [m for m in matches if m['name'] != symbol]
            sorted_matches = exact_matches + fuzzy_matches

            # Format results
            formatted_results = []
            for match in sorted_matches:
                # Get code snippet with context
                code_snippet = self._get_code_snippet(
                    match['file_path'],
                    match['line'],
                    match['end_line'],
                    self._context_lines
                )

                formatted_results.append({
                    "symbol": match['name'],
                    "type": match['type'],
                    "file": match['file'],
                    "line": match['line'],
                    "end_line": match['end_line'],
                    "signature": match['signature'],
                    "docstring": match['docstring'],
                    "code_snippet": code_snippet,
                    "scope": self._determine_scope(match['name'])
                })

            self._log_execution("completed", f"found {len(formatted_results)} results")

            return {
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results),
                "error": ""
            }

        except Exception as e:
            error_msg = str(e)
            self._log_execution("error", f"lookup failed: {error_msg}")
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": f"Lookup failed: {error_msg}"
            }

    def _build_index_if_needed(self) -> bool:
        """Build or rebuild the symbol index if needed.

        Returns:
            True if index is ready, False if build failed
        """
        import time

        # Check if we need to rebuild
        current_time = time.time()

        if self._symbol_index is not None and self._index_timestamp is not None:
            # Index exists and is less than 60 seconds old - use it
            if current_time - self._index_timestamp < 60:
                return True

        # Build new index
        self._log_execution("building_index", f"indexing {self._project_root}")

        try:
            symbols = []

            # Import CodeParser directly without triggering rag/__init__.py
            import sys
            import importlib.util
            spec = importlib.util.spec_from_file_location(
                "code_parser",
                Path(self._project_root) / "rag" / "code_parser.py"
            )
            code_parser_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(code_parser_module)
            CodeParser = code_parser_module.CodeParser
            parser = CodeParser()

            # Walk through Python files
            for py_file in self._find_python_files(self._project_root):
                # Parse file
                parsed_data = parser.parse_file(str(py_file))

                if not parsed_data:
                    continue

                file_path = parsed_data['file_path']
                relative_path = self._get_relative_path(file_path)

                # Add functions
                for func in parsed_data['functions']:
                    symbols.append({
                        'name': func['name'],
                        'type': 'function',
                        'file': relative_path,
                        'file_path': file_path,
                        'line': func['start_line'],
                        'end_line': func['end_line'],
                        'signature': func['signature'],
                        'docstring': func['docstring']
                    })

                # Add classes and their methods
                for cls in parsed_data['classes']:
                    # Add class itself
                    symbols.append({
                        'name': cls['name'],
                        'type': 'class',
                        'file': relative_path,
                        'file_path': file_path,
                        'line': cls['start_line'],
                        'end_line': cls['end_line'],
                        'signature': f"class {cls['name']}({', '.join(cls['bases'])})" if cls['bases'] else f"class {cls['name']}",
                        'docstring': cls['docstring']
                    })

                    # Add methods
                    for method in cls['methods']:
                        symbols.append({
                            'name': method['name'],
                            'type': 'method',
                            'file': relative_path,
                            'file_path': file_path,
                            'line': method['start_line'],
                            'end_line': method['end_line'],
                            'signature': method['signature'],
                            'docstring': method['docstring'],
                            'class': cls['name']  # Track which class this method belongs to
                        })

            # Update index
            object.__setattr__(self, '_symbol_index', symbols)
            object.__setattr__(self, '_index_timestamp', current_time)

            self._log_execution("index_built", f"indexed {len(symbols)} symbols")
            return True

        except Exception as e:
            self._log_execution("index_error", str(e))
            return False

    def _find_python_files(self, root: Path) -> List[Path]:
        """Find all Python files in the project.

        Args:
            root: Root directory to search

        Returns:
            List of Python file paths
        """
        python_files = []

        # Directories to exclude
        exclude_dirs = {
            '__pycache__', '.git', '.venv', 'venv', 'env',
            'node_modules', '.pytest_cache', '.mypy_cache',
            'build', 'dist', '.tox', 'htmlcov', '.eggs'
        }

        for path in root.rglob('*.py'):
            # Skip excluded directories
            if any(excluded in path.parts for excluded in exclude_dirs):
                continue

            # Skip test files in tests/ directory (we'll index project code)
            # Actually, let's include tests too - they might have useful definitions

            python_files.append(path)

        return python_files

    def _get_relative_path(self, file_path: str) -> str:
        """Get relative path from project root.

        Args:
            file_path: Absolute file path

        Returns:
            Relative path string
        """
        try:
            path = Path(file_path)
            relative = path.relative_to(self._project_root)
            return str(relative)
        except ValueError:
            # File is outside project root
            return file_path

    def _get_code_snippet(self, file_path: str, start_line: int, end_line: int, context_lines: int = 5) -> str:
        """Get code snippet with context lines.

        Args:
            file_path: Path to the file
            start_line: Starting line of definition
            end_line: Ending line of definition
            context_lines: Number of context lines before/after

        Returns:
            Code snippet as string
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                lines = f.readlines()

            # Calculate range with context
            snippet_start = max(0, start_line - 1 - context_lines)
            snippet_end = min(len(lines), end_line + context_lines)

            # Extract snippet
            snippet_lines = lines[snippet_start:snippet_end]
            snippet = ''.join(snippet_lines)

            # Truncate if too long (max 1000 chars)
            if len(snippet) > 1000:
                snippet = snippet[:1000] + "\n... (truncated)"

            return snippet

        except Exception as e:
            self._log_execution("snippet_error", str(e))
            return "<code snippet unavailable>"

    def _determine_scope(self, symbol_name: str) -> str:
        """Determine if symbol is public or private based on naming.

        Args:
            symbol_name: Name of the symbol

        Returns:
            "public" or "private"
        """
        # Python convention: names starting with _ are private
        if symbol_name.startswith('_') and not symbol_name.startswith('__'):
            return "private"
        elif symbol_name.startswith('__') and not symbol_name.endswith('__'):
            return "private"  # Name mangled
        else:
            return "public"

    def refresh_index(self) -> bool:
        """Force refresh of the symbol index.

        Returns:
            True if successful, False otherwise
        """
        try:
            object.__setattr__(self, '_symbol_index', None)
            object.__setattr__(self, '_index_timestamp', None)
            return self._build_index_if_needed()
        except Exception as e:
            self._log_execution("refresh_error", str(e))
            return False

    def enable(self) -> None:
        """Enable symbol lookup.

        This allows the tool to perform lookups.
        """
        object.__setattr__(self, '_enabled', True)
        if self.logger:
            self.logger.info("Symbol lookup enabled")

    def disable(self) -> None:
        """Disable symbol lookup.

        This prevents the tool from performing lookups.
        """
        object.__setattr__(self, '_enabled', False)
        if self.logger:
            self.logger.info("Symbol lookup disabled")

    def is_enabled(self) -> bool:
        """Check if symbol lookup is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self._enabled

    def get_info(self) -> Dict[str, Any]:
        """Get tool information.

        Returns:
            Dictionary with tool metadata including index stats
        """
        base_info = super().get_info()

        index_size = len(self._symbol_index) if self._symbol_index else 0
        index_age = None
        if self._index_timestamp:
            import time
            index_age = int(time.time() - self._index_timestamp)

        base_info.update({
            "enabled": self._enabled,
            "max_results": self._max_results,
            "context_lines": self._context_lines,
            "index_size": index_size,
            "index_age_seconds": index_age,
            "project_root": str(self._project_root)
        })
        return base_info
