"""
Codebase Indexer - Main orchestrator for parsing, chunking, and indexing code.

Walks directory tree, parses Python files, creates chunks, generates embeddings,
and stores in FAISS vector store and metadata store.
"""

import os
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple

from rag.code_parser import CodeParser
from rag.chunker import CodeChunker
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.metadata_store import MetadataStore

logger = logging.getLogger(__name__)


# Directories to exclude from indexing
EXCLUDED_DIRS = {
    "__pycache__",
    ".git",
    "venv",
    "env",
    ".venv",
    ".env",
    "node_modules",
    ".pytest_cache",
    "build",
    "dist",
    "eggs",
    ".eggs",
    "*.egg-info",
    ".tox",
    ".mypy_cache",
    ".ruff_cache",
    ".coverage",
    "htmlcov",
}


class CodebaseIndexer:
    """
    Main orchestrator for codebase indexing.

    Coordinates parsing, chunking, embedding, and storage of code elements
    for semantic search and code intelligence.
    """

    def __init__(
        self,
        embedder: EmbeddingModel,
        vector_store: VectorStore,
        metadata_store: MetadataStore,
        verbose: bool = False
    ):
        """
        Initialize the codebase indexer.

        Args:
            embedder: Embedding model for generating vectors
            vector_store: FAISS vector store for similarity search
            metadata_store: Metadata store for chunk information
            verbose: Enable verbose logging
        """
        self.embedder = embedder
        self.vector_store = vector_store
        self.metadata_store = metadata_store
        self.verbose = verbose

        # Initialize parser and chunker
        self.parser = CodeParser()
        self.chunker = CodeChunker()

        # Statistics
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "chunks_created": 0,
            "errors": []
        }

        self.logger = logger

    def index_file(self, filepath: str) -> int:
        """
        Parse, chunk, embed, and store a single Python file.

        Args:
            filepath: Path to Python file to index

        Returns:
            Number of chunks created from this file

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file is not a Python file
        """
        # Validate file
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File not found: {filepath}")

        if not filepath.endswith(".py"):
            raise ValueError(f"Not a Python file: {filepath}")

        # Skip empty __init__.py files
        if filepath.endswith("__init__.py"):
            file_size = os.path.getsize(filepath)
            if file_size == 0:
                if self.verbose:
                    self.logger.debug(f"Skipping empty __init__.py: {filepath}")
                return 0

        try:
            # Parse the file
            parsed_data = self.parser.parse_file(filepath)
            if parsed_data is None:
                self.logger.warning(f"Failed to parse {filepath}")
                self.stats["files_failed"] += 1
                self.stats["errors"].append({
                    "file": filepath,
                    "error": "Failed to parse (syntax error or encoding issue)"
                })
                return 0

            # Create chunks
            chunks = self.chunker.create_chunks(parsed_data, filepath)

            if not chunks:
                if self.verbose:
                    self.logger.debug(f"No chunks created from {filepath}")
                return 0

            # Generate embeddings for all chunks
            chunk_texts = [self.chunker.get_chunk_text(chunk) for chunk in chunks]
            embeddings = self.embedder.encode_batch(chunk_texts)

            # Store in vector store and metadata store
            chunk_ids = [chunk["chunk_id"] for chunk in chunks]
            self.vector_store.add_batch(embeddings, chunk_ids)

            for chunk in chunks:
                self.metadata_store.add(chunk["chunk_id"], chunk)

            # Update statistics
            self.stats["files_processed"] += 1
            self.stats["chunks_created"] += len(chunks)

            if self.verbose:
                self.logger.info(f"Indexed {filepath}: {len(chunks)} chunks")

            return len(chunks)

        except Exception as e:
            self.logger.error(f"Error indexing {filepath}: {e}")
            self.stats["files_failed"] += 1
            self.stats["errors"].append({
                "file": filepath,
                "error": str(e)
            })
            return 0

    def index_directory(
        self,
        dirpath: str,
        recursive: bool = True,
        file_pattern: str = "*.py"
    ) -> Dict[str, Any]:
        """
        Index all Python files in a directory.

        Args:
            dirpath: Path to directory to index
            recursive: Whether to recursively index subdirectories
            file_pattern: File pattern to match (default: "*.py")

        Returns:
            Dictionary with statistics:
            - files_processed: Number of files successfully indexed
            - files_failed: Number of files that failed
            - chunks_created: Total number of chunks created
            - errors: List of error dictionaries

        Raises:
            FileNotFoundError: If directory doesn't exist
            ValueError: If path is not a directory
        """
        # Validate directory
        if not os.path.exists(dirpath):
            raise FileNotFoundError(f"Directory not found: {dirpath}")

        if not os.path.isdir(dirpath):
            raise ValueError(f"Not a directory: {dirpath}")

        # Reset statistics
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "chunks_created": 0,
            "errors": []
        }

        # Collect all Python files
        python_files = self._find_python_files(dirpath, recursive)

        if not python_files:
            self.logger.warning(f"No Python files found in {dirpath}")
            return self.stats

        self.logger.info(f"Found {len(python_files)} Python files to index")

        # Index each file
        for i, filepath in enumerate(python_files, 1):
            if self.verbose:
                self.logger.info(f"[{i}/{len(python_files)}] Indexing {filepath}")

            try:
                self.index_file(filepath)
            except Exception as e:
                self.logger.error(f"Error indexing {filepath}: {e}")
                self.stats["files_failed"] += 1
                self.stats["errors"].append({
                    "file": filepath,
                    "error": str(e)
                })

        # Log summary
        self.logger.info(
            f"Indexing complete: {self.stats['files_processed']} files, "
            f"{self.stats['chunks_created']} chunks, "
            f"{self.stats['files_failed']} failures"
        )

        return self.stats

    def _find_python_files(self, dirpath: str, recursive: bool) -> List[str]:
        """
        Find all Python files in a directory, excluding excluded directories.

        Args:
            dirpath: Directory path to search
            recursive: Whether to search recursively

        Returns:
            List of absolute paths to Python files
        """
        python_files = []

        if recursive:
            # Use os.walk for recursive search
            for root, dirs, files in os.walk(dirpath):
                # Remove excluded directories from dirs (in-place modification)
                # This prevents os.walk from descending into them
                dirs[:] = [d for d in dirs if d not in EXCLUDED_DIRS]

                # Add Python files
                for filename in files:
                    if filename.endswith(".py"):
                        filepath = os.path.join(root, filename)
                        python_files.append(filepath)
        else:
            # Non-recursive: only check immediate directory
            try:
                for entry in os.scandir(dirpath):
                    if entry.is_file() and entry.name.endswith(".py"):
                        python_files.append(entry.path)
            except PermissionError:
                self.logger.warning(f"Permission denied: {dirpath}")

        return python_files

    def get_stats(self) -> Dict[str, Any]:
        """
        Get indexing statistics.

        Returns:
            Dictionary with statistics:
            - files_processed: Number of files successfully indexed
            - files_failed: Number of files that failed
            - chunks_created: Total number of chunks created
            - errors: List of error dictionaries
            - total_chunks: Total chunks in vector store
            - total_metadata: Total chunks in metadata store
        """
        return {
            **self.stats,
            "total_chunks": self.vector_store.size(),
            "total_metadata": self.metadata_store.size()
        }

    def save(self, vector_store_path: str) -> None:
        """
        Save vector store and metadata store to disk.

        Args:
            vector_store_path: Path to save FAISS index
        """
        self.logger.info("Saving vector store...")
        self.vector_store.save(vector_store_path)

        self.logger.info("Saving metadata store...")
        self.metadata_store.save()

        self.logger.info("Save complete")

    def load(self, vector_store_path: str) -> None:
        """
        Load vector store and metadata store from disk.

        Args:
            vector_store_path: Path to FAISS index

        Raises:
            FileNotFoundError: If index files don't exist
        """
        self.logger.info("Loading vector store...")
        self.vector_store.load(vector_store_path)

        self.logger.info("Loading metadata store...")
        self.metadata_store.load()

        self.logger.info(
            f"Load complete: {self.vector_store.size()} chunks"
        )

    def clear(self) -> None:
        """
        Clear all data from vector store and metadata store.

        Warning: This operation cannot be undone.
        """
        self.logger.warning("Clearing all indexed data...")
        self.vector_store = VectorStore(dimension=self.embedder.get_dimension())
        self.metadata_store.clear()
        self.stats = {
            "files_processed": 0,
            "files_failed": 0,
            "chunks_created": 0,
            "errors": []
        }
        self.logger.info("Clear complete")

    def reindex_file(self, filepath: str) -> int:
        """
        Reindex a single file by removing old chunks and adding new ones.

        Args:
            filepath: Path to file to reindex

        Returns:
            Number of chunks created

        Note:
            This is a simplified implementation that doesn't actually remove
            old chunks. For production use, implement proper chunk removal.
        """
        # TODO: Implement proper removal of old chunks
        # For now, just index the file (may create duplicates)
        return self.index_file(filepath)

    def search(self, query: str, top_k: int = 10) -> List[Tuple[Dict[str, Any], float]]:
        """
        Search for code chunks similar to the query.

        Args:
            query: Search query (natural language or code)
            top_k: Number of results to return

        Returns:
            List of (chunk_metadata, distance) tuples, sorted by relevance
        """
        # Generate query embedding
        query_embedding = self.embedder.encode(query)

        # Search vector store
        results = self.vector_store.search(query_embedding, top_k=top_k)

        # Retrieve metadata for each result
        results_with_metadata = []
        for chunk_id, distance in results:
            metadata = self.metadata_store.get(chunk_id)
            if metadata:
                results_with_metadata.append((metadata, distance))

        return results_with_metadata
