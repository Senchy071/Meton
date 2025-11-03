"""JSON-based metadata storage for code chunks."""

from typing import Dict, List, Any, Optional
import json
from pathlib import Path


class MetadataStore:
    """JSON-based storage for code chunk metadata.

    Stores metadata for each code chunk including file path, chunk type,
    name, line numbers, code content, and docstring.

    Example:
        >>> store = MetadataStore("./rag_index/metadata.json")
        >>> store.add("chunk-1", {
        ...     "chunk_id": "chunk-1",
        ...     "file_path": "/path/to/file.py",
        ...     "chunk_type": "function",
        ...     "name": "authenticate_user",
        ...     "start_line": 10,
        ...     "end_line": 25,
        ...     "code": "def authenticate_user(): pass",
        ...     "docstring": "Authenticate user"
        ... })
        >>> store.save()
    """

    def __init__(self, filepath: str = "./rag_index/metadata.json"):
        """Initialize metadata store.

        Args:
            filepath: Path to JSON file for storing metadata

        Example:
            >>> store = MetadataStore()
            >>> store.size()
            0
        """
        self.filepath = filepath
        self.metadata: Dict[str, dict] = {}

        # Try to load existing metadata
        if Path(filepath).exists():
            try:
                self.load()
            except (json.JSONDecodeError, IOError):
                # If file is corrupted or empty, start fresh
                self.metadata = {}

    def add(self, chunk_id: str, metadata: dict) -> None:
        """Add or update metadata for a chunk.

        Args:
            chunk_id: Unique chunk identifier
            metadata: Dictionary containing chunk metadata

        Example:
            >>> store = MetadataStore()
            >>> store.add("chunk-1", {
            ...     "chunk_id": "chunk-1",
            ...     "file_path": "/test/file.py",
            ...     "chunk_type": "function",
            ...     "name": "test_func",
            ...     "start_line": 1,
            ...     "end_line": 10,
            ...     "code": "def test_func(): pass",
            ...     "docstring": ""
            ... })
            >>> store.size()
            1
        """
        # Validate required fields
        required_fields = ["chunk_id", "file_path", "chunk_type", "name", "start_line", "end_line", "code", "docstring"]
        for field in required_fields:
            if field not in metadata:
                raise ValueError(f"Missing required field: {field}")

        # Ensure chunk_id matches
        if metadata["chunk_id"] != chunk_id:
            raise ValueError(f"chunk_id mismatch: {metadata['chunk_id']} != {chunk_id}")

        self.metadata[chunk_id] = metadata

    def get(self, chunk_id: str) -> Optional[dict]:
        """Get metadata for a specific chunk.

        Args:
            chunk_id: Chunk identifier

        Returns:
            Metadata dictionary or None if not found

        Example:
            >>> store = MetadataStore()
            >>> # ... add metadata ...
            >>> metadata = store.get("chunk-1")
            >>> print(metadata["name"])
            test_func
        """
        return self.metadata.get(chunk_id)

    def get_all(self) -> Dict[str, dict]:
        """Get all metadata.

        Returns:
            Dictionary mapping chunk_id to metadata

        Example:
            >>> store = MetadataStore()
            >>> all_metadata = store.get_all()
            >>> print(f"Total chunks: {len(all_metadata)}")
        """
        return self.metadata.copy()

    def search_by_field(self, field: str, value: Any) -> List[dict]:
        """Find all chunks where field matches value.

        Args:
            field: Field name to search (e.g., "chunk_type", "file_path")
            value: Value to match

        Returns:
            List of metadata dictionaries matching the criteria

        Example:
            >>> store = MetadataStore()
            >>> # ... add metadata ...
            >>> functions = store.search_by_field("chunk_type", "function")
            >>> print(f"Found {len(functions)} functions")
        """
        results = []
        for metadata in self.metadata.values():
            if metadata.get(field) == value:
                results.append(metadata)
        return results

    def save(self) -> None:
        """Save metadata to JSON file.

        Creates parent directories if they don't exist.

        Example:
            >>> store = MetadataStore("./rag_index/metadata.json")
            >>> # ... add metadata ...
            >>> store.save()
        """
        # Create parent directories if needed
        Path(self.filepath).parent.mkdir(parents=True, exist_ok=True)

        # Write to JSON with pretty formatting
        with open(self.filepath, "w", encoding="utf-8") as f:
            json.dump(self.metadata, f, indent=2, ensure_ascii=False)

    def load(self) -> None:
        """Load metadata from JSON file.

        Raises:
            FileNotFoundError: If file doesn't exist
            json.JSONDecodeError: If file is not valid JSON

        Example:
            >>> store = MetadataStore("./rag_index/metadata.json")
            >>> store.load()
            >>> print(f"Loaded {store.size()} chunks")
        """
        if not Path(self.filepath).exists():
            raise FileNotFoundError(f"Metadata file not found: {self.filepath}")

        with open(self.filepath, "r", encoding="utf-8") as f:
            self.metadata = json.load(f)

    def size(self) -> int:
        """Get number of chunks in the store.

        Returns:
            Number of chunks

        Example:
            >>> store = MetadataStore()
            >>> store.size()
            0
        """
        return len(self.metadata)

    def delete(self, chunk_id: str) -> bool:
        """Delete metadata for a chunk.

        Args:
            chunk_id: Chunk identifier to delete

        Returns:
            True if deleted, False if not found

        Example:
            >>> store = MetadataStore()
            >>> # ... add metadata ...
            >>> store.delete("chunk-1")
            True
        """
        if chunk_id in self.metadata:
            del self.metadata[chunk_id]
            return True
        return False

    def clear(self) -> None:
        """Clear all metadata.

        Example:
            >>> store = MetadataStore()
            >>> store.clear()
            >>> store.size()
            0
        """
        self.metadata = {}
