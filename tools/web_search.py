"""Web search tools for Meton.

This module provides web search capabilities using DuckDuckGo.
The tool is DISABLED BY DEFAULT and must be explicitly enabled by the user.

Example:
    >>> from core.config import Config
    >>> from tools.web_search import WebSearchTool
    >>>
    >>> config = Config()
    >>> tool = WebSearchTool(config)
    >>>
    >>> # Search (only works if enabled in config)
    >>> import json
    >>> input_json = json.dumps({"query": "Python programming"})
    >>> result = tool._run(input_json)
"""

import json
import time
from typing import List, Dict, Any, Optional
from pydantic import Field

from tools.base import MetonBaseTool, ToolConfig, ToolError, ToolExecutionError
from utils.logger import setup_logger


# Custom Exceptions
class WebSearchError(ToolError):
    """Base exception for web search errors."""
    pass


class WebSearchDisabledError(WebSearchError):
    """Web search is disabled."""
    pass


class WebSearchTimeoutError(WebSearchError):
    """Web search timed out."""
    pass


class WebSearchConfig(ToolConfig):
    """Configuration for web search tool."""
    enabled: bool = False  # DISABLED BY DEFAULT
    max_results: int = Field(default=5, ge=1, le=20)
    timeout: int = Field(default=10, ge=1)


class WebSearchTool(MetonBaseTool):
    """Tool for web search using DuckDuckGo.

    Features:
    - Search the web using DuckDuckGo (no API key required)
    - DISABLED BY DEFAULT - must be explicitly enabled
    - Configurable max results (1-20)
    - Timeout protection
    - Graceful error handling

    IMPORTANT: This tool checks if it's enabled before running. If disabled,
    it returns an error message telling the user to enable it.

    Example:
        >>> tool = WebSearchTool(config)
        >>> input_json = json.dumps({
        ...     "query": "Python web frameworks"
        ... })
        >>> result = tool._run(input_json)
    """

    name: str = "web_search"
    description: str = """Search the web using DuckDuckGo.

Input format: JSON string with 'query' parameter:

Example:
{"query": "Python programming tutorials"}

Returns: JSON with search results:
{
    "success": true/false,
    "results": [
        {
            "title": "Result title",
            "url": "https://example.com",
            "snippet": "Description of the result..."
        },
        ...
    ],
    "count": 5,
    "error": "error message if any"
}

Note: This tool is DISABLED BY DEFAULT. Enable it in config.yaml or via CLI command.
"""

    def __init__(self, config):
        """Initialize with configuration.

        Args:
            config: ConfigLoader instance with tools.web_search settings
        """
        super().__init__()

        # Get config values
        search_config = config.config.tools.web_search
        object.__setattr__(self, '_enabled', search_config.enabled)
        object.__setattr__(self, '_max_results', search_config.max_results)
        object.__setattr__(self, '_timeout', search_config.timeout)

        # Setup logger
        object.__setattr__(self, 'logger', setup_logger(
            name="web_search",
            config=config.config.logging.model_dump()
        ))

        self._log_execution(
            "initialized",
            f"enabled={self._enabled}, max_results={self._max_results}, timeout={self._timeout}s"
        )

    def _run(self, input_str: str) -> str:
        """Search the web.

        Args:
            input_str: JSON string with query parameter

        Returns:
            JSON string with search results

        Raises:
            ToolExecutionError: If execution fails
        """
        try:
            # CHECK IF ENABLED FIRST - This is the key difference from code_executor
            if not self._enabled:
                self._log_execution("search_blocked", "tool is disabled")
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Web search is disabled. Enable with /web on command or set tools.web_search.enabled=true in config.yaml"
                })

            # Parse input
            try:
                input_data = json.loads(input_str)
            except json.JSONDecodeError as e:
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": f"Invalid JSON input: {str(e)}"
                })

            if 'query' not in input_data:
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Missing required 'query' parameter"
                })

            query = input_data['query']

            if not query or not query.strip():
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Query cannot be empty"
                })

            # Perform search
            result = self._search(query)
            return json.dumps(result, indent=2)

        except Exception as e:
            return self._handle_error(e, "searching web")

    def _search(self, query: str) -> Dict[str, Any]:
        """Perform web search using DuckDuckGo.

        Args:
            query: Search query string

        Returns:
            Dict with success, results, count, and optional error
        """
        start_time = time.time()

        try:
            # Import here to avoid import errors if library not installed
            from ddgs import DDGS

            self._log_execution("searching", f"query='{query}', max_results={self._max_results}")

            # Perform search with timeout
            results = []
            with DDGS() as ddgs:
                # Use text search (ddgs API uses 'query' as first positional arg)
                search_results = ddgs.text(
                    query,
                    max_results=self._max_results
                )

                # Format results
                for idx, result in enumerate(search_results):
                    if idx >= self._max_results:
                        break

                    results.append({
                        "title": result.get("title", ""),
                        "url": result.get("href", result.get("link", "")),
                        "snippet": result.get("body", result.get("snippet", ""))
                    })

            execution_time = time.time() - start_time

            self._log_execution(
                "completed",
                f"found {len(results)} results in {execution_time:.2f}s"
            )

            return {
                "success": True,
                "results": results,
                "count": len(results),
                "error": ""
            }

        except ImportError:
            self._log_execution("import_error", "ddgs not installed")
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": "ddgs library not installed. Install with: pip install ddgs>=4.0.0"
            }

        except TimeoutError:
            execution_time = time.time() - start_time
            self._log_execution("timeout", f"exceeded {self._timeout}s")
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": f"Search timed out after {self._timeout} seconds"
            }

        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = str(e)
            self._log_execution("error", f"search failed: {error_msg}")
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": f"Search failed: {error_msg}"
            }

    def enable(self) -> None:
        """Enable web search.

        This allows the tool to perform searches.
        """
        object.__setattr__(self, '_enabled', True)
        if self.logger:
            self.logger.info("Web search enabled")

    def disable(self) -> None:
        """Disable web search.

        This prevents the tool from performing searches.
        """
        object.__setattr__(self, '_enabled', False)
        if self.logger:
            self.logger.info("Web search disabled")

    def is_enabled(self) -> bool:
        """Check if web search is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self._enabled

    def get_info(self) -> Dict[str, Any]:
        """Get tool information.

        Returns:
            Dictionary with tool metadata including search settings
        """
        base_info = super().get_info()
        base_info.update({
            "enabled": self._enabled,
            "max_results": self._max_results,
            "timeout": self._timeout,
        })
        return base_info
