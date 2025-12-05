"""Codebase search tool for Meton.

This module provides semantic code search capabilities using the RAG indexer.
The tool is DISABLED BY DEFAULT and must be explicitly enabled after indexing.

Example:
    >>> from core.config import Config
    >>> from tools.codebase_search import CodebaseSearchTool
    >>>
    >>> config = Config()
    >>> tool = CodebaseSearchTool(config)
    >>>
    >>> # Search (only works if enabled and index exists)
    >>> import json
    >>> input_json = json.dumps({"query": "how does authentication work"})
    >>> result = tool._run(input_json)
"""

import json
import os
from typing import Dict, Any, List, Optional
from pydantic import Field

from tools.base import MetonBaseTool, ToolConfig, ToolError
from utils.logger import setup_logger


# Custom Exceptions
class CodebaseSearchError(ToolError):
    """Base exception for codebase search errors."""
    pass


class CodebaseSearchDisabledError(CodebaseSearchError):
    """Codebase search is disabled."""
    pass


class IndexNotLoadedError(CodebaseSearchError):
    """No index has been loaded."""
    pass


class CodebaseSearchConfig(ToolConfig):
    """Configuration for codebase search tool."""
    enabled: bool = False  # DISABLED BY DEFAULT
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_code_length: int = Field(default=500, ge=100, le=10000)


class CodebaseSearchTool(MetonBaseTool):
    """Tool for semantic code search using RAG indexer.

    Features:
    - Search indexed codebase using natural language queries
    - DISABLED BY DEFAULT - must be explicitly enabled after indexing
    - Configurable number of results (top_k)
    - Similarity threshold filtering
    - Automatic code snippet truncation
    - Sorted results by relevance

    IMPORTANT: This tool requires:
    1. RAG must be enabled in config
    2. Codebase must be indexed first
    3. Tool must be explicitly enabled

    Example:
        >>> tool = CodebaseSearchTool(config)
        >>> input_json = json.dumps({
        ...     "query": "user authentication functions"
        ... })
        >>> result = tool._run(input_json)
    """

    name: str = "codebase_search"
    description: str = """Search the indexed codebase semantically using natural language.

Input format: JSON string with 'query' parameter:

Example:
{"query": "how does authentication work"}

Returns: JSON with search results:
{
    "success": true/false,
    "results": [
        {
            "file": "auth/login.py",
            "type": "function",
            "name": "authenticate_user",
            "lines": "45-67",
            "similarity": 0.89,
            "code_snippet": "def authenticate_user(username, password):\\n    ..."
        },
        ...
    ],
    "count": 5,
    "error": "error message if any"
}

Note: This tool is DISABLED BY DEFAULT. You must:
1. Index the codebase first using /index command
2. Enable the tool via config or CLI command
"""

    def __init__(self, config):
        """Initialize with configuration.

        Args:
            config: ConfigLoader instance with tools.codebase_search settings
        """
        super().__init__()

        # Get config values
        self._config = config

        # Get codebase_search config (if exists, otherwise use defaults)
        if hasattr(config.config.tools, 'codebase_search'):
            search_config = config.config.tools.codebase_search
        else:
            # Use default config if not in config file yet
            search_config = CodebaseSearchConfig()

        object.__setattr__(self, '_enabled', search_config.enabled)
        object.__setattr__(self, '_top_k', search_config.top_k)
        object.__setattr__(self, '_similarity_threshold', search_config.similarity_threshold)
        object.__setattr__(self, '_max_code_length', search_config.max_code_length)

        # Get RAG config
        rag_config = config.config.rag
        object.__setattr__(self, '_rag_enabled', rag_config.enabled)
        object.__setattr__(self, '_index_path', rag_config.index_path)
        object.__setattr__(self, '_metadata_path', rag_config.metadata_path)
        object.__setattr__(self, '_embedding_dimension', rag_config.dimensions)

        # Setup logger
        object.__setattr__(self, 'logger', setup_logger("codebase_search", console_output=False))

        # Lazy-loaded indexer (only load when needed)
        object.__setattr__(self, '_indexer', None)

        self._log_execution(
            "initialized",
            f"enabled={self._enabled}, rag_enabled={self._rag_enabled}, "
            f"top_k={self._top_k}, threshold={self._similarity_threshold}"
        )

    def _run(self, input_str: str) -> str:
        """Search the codebase.

        Args:
            input_str: JSON string with query parameter

        Returns:
            JSON string with search results

        Raises:
            ToolExecutionError: If execution fails
        """
        try:
            # CHECK IF RAG IS ENABLED FIRST
            if not self._rag_enabled:
                self._log_execution("search_blocked", "RAG is disabled")
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "RAG is disabled. Enable with rag.enabled=true in config.yaml"
                }, indent=2)

            # CHECK IF TOOL IS ENABLED
            if not self._enabled:
                self._log_execution("search_blocked", "tool is disabled")
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Codebase search is disabled. Index your codebase first, then enable with tools.codebase_search.enabled=true in config.yaml"
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

            if 'query' not in input_data:
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Missing required 'query' parameter"
                }, indent=2)

            query = input_data['query']

            if not query or not query.strip():
                return json.dumps({
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Query cannot be empty"
                }, indent=2)

            # Perform search
            result = self._search(query)
            return json.dumps(result, indent=2)

        except Exception as e:
            return self._handle_error(e, "searching codebase")

    def _load_indexer(self):
        """Lazy-load the indexer when first needed.

        Returns:
            CodebaseIndexer instance or None if loading fails
        """
        if self._indexer is not None:
            return self._indexer

        try:
            # Import here to avoid circular dependencies
            from rag.embeddings import EmbeddingModel
            from rag.vector_store import VectorStore
            from rag.metadata_store import MetadataStore
            from rag.indexer import CodebaseIndexer

            # Initialize components
            embedder = EmbeddingModel()
            vector_store = VectorStore(dimension=self._embedding_dimension)
            metadata_store = MetadataStore(self._metadata_path)

            # Create indexer
            indexer = CodebaseIndexer(
                embedder=embedder,
                vector_store=vector_store,
                metadata_store=metadata_store,
                verbose=False
            )

            # Try to load existing index
            vector_store_path = os.path.join(self._index_path, "faiss.index")
            if os.path.exists(vector_store_path):
                indexer.load(vector_store_path)
                self._log_execution("index_loaded", f"loaded {vector_store.size()} chunks")
            else:
                self._log_execution("index_not_found", f"no index at {vector_store_path}")
                return None

            object.__setattr__(self, '_indexer', indexer)
            return indexer

        except Exception as e:
            self._log_execution("indexer_load_error", str(e))
            return None

    def _search(self, query: str) -> Dict[str, Any]:
        """Perform semantic code search.

        Args:
            query: Natural language search query

        Returns:
            Dict with success, results, count, and optional error
        """
        try:
            # Load indexer if not already loaded
            indexer = self._load_indexer()

            if indexer is None:
                return {
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": f"No index found at {self._index_path}. Index your codebase first using the indexer."
                }

            # Check if index has any chunks
            stats = indexer.get_stats()
            if stats["total_chunks"] == 0:
                return {
                    "success": False,
                    "results": [],
                    "count": 0,
                    "error": "Index is empty. Index your codebase first."
                }

            self._log_execution("searching", f"query='{query}', top_k={self._top_k}")

            # Perform search
            raw_results = indexer.search(query, top_k=self._top_k)

            # Format and filter results
            formatted_results = []
            for metadata, distance in raw_results:
                # Convert distance to similarity score (lower distance = higher similarity)
                # Using inverse formula: similarity = 1 / (1 + distance)
                # This provides a more gradual decay than exponential
                similarity = 1.0 / (1.0 + distance)

                # Filter by similarity threshold
                if similarity < self._similarity_threshold:
                    continue

                # Format code snippet (truncate if needed)
                code = metadata.get("code", "")
                if len(code) > self._max_code_length:
                    code_snippet = code[:self._max_code_length] + "\n... (truncated)"
                else:
                    code_snippet = code

                # Extract file name from path
                file_path = metadata.get("file_path", "")

                # Format result
                formatted_results.append({
                    "file": file_path,
                    "type": metadata.get("chunk_type", "unknown"),
                    "name": metadata.get("name", "unnamed"),
                    "lines": f"{metadata.get('start_line', 0)}-{metadata.get('end_line', 0)}",
                    "similarity": round(similarity, 4),
                    "code_snippet": code_snippet
                })

            self._log_execution(
                "completed",
                f"found {len(formatted_results)} results (filtered from {len(raw_results)})"
            )

            return {
                "success": True,
                "results": formatted_results,
                "count": len(formatted_results),
                "error": ""
            }

        except Exception as e:
            error_msg = str(e)
            self._log_execution("error", f"search failed: {error_msg}")
            return {
                "success": False,
                "results": [],
                "count": 0,
                "error": f"Search failed: {error_msg}"
            }

    def enable(self) -> None:
        """Enable codebase search.

        This allows the tool to perform searches.
        """
        object.__setattr__(self, '_enabled', True)
        if self.logger:
            self.logger.info("Codebase search enabled")

    def disable(self) -> None:
        """Disable codebase search.

        This prevents the tool from performing searches.
        """
        object.__setattr__(self, '_enabled', False)
        if self.logger:
            self.logger.info("Codebase search disabled")

    def is_enabled(self) -> bool:
        """Check if codebase search is enabled.

        Returns:
            True if enabled, False otherwise
        """
        return self._enabled

    def reload_index(self) -> bool:
        """Reload the index from disk.

        Returns:
            True if successful, False otherwise
        """
        try:
            object.__setattr__(self, '_indexer', None)
            indexer = self._load_indexer()
            return indexer is not None
        except Exception as e:
            self._log_execution("reload_error", str(e))
            return False

    def get_info(self) -> Dict[str, Any]:
        """Get tool information.

        Returns:
            Dictionary with tool metadata including search settings
        """
        base_info = super().get_info()

        # Check if index exists and get size
        index_exists = False
        index_size = 0
        vector_store_path = os.path.join(self._index_path, "faiss.index")

        if os.path.exists(vector_store_path):
            index_exists = True
            if self._indexer is not None:
                stats = self._indexer.get_stats()
                index_size = stats["total_chunks"]

        base_info.update({
            "enabled": self._enabled,
            "rag_enabled": self._rag_enabled,
            "top_k": self._top_k,
            "similarity_threshold": self._similarity_threshold,
            "max_code_length": self._max_code_length,
            "index_exists": index_exists,
            "index_size": index_size,
            "index_path": self._index_path
        })
        return base_info
