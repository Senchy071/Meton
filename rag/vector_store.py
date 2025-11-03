"""FAISS vector database for similarity search."""

from typing import List, Tuple, Dict
import numpy as np
import faiss
import pickle
import os
from pathlib import Path


class VectorStore:
    """FAISS-based vector store for semantic similarity search.

    Uses IndexFlatL2 for exact L2 distance search. Maintains mapping between
    string chunk_ids and integer FAISS indices.

    Example:
        >>> store = VectorStore(dimension=768)
        >>> embedding = np.random.rand(768).astype('float32')
        >>> store.add(embedding, "chunk-1")
        >>> results = store.search(embedding, top_k=5)
        >>> print(results)  # [(chunk_id, distance), ...]
    """

    def __init__(self, dimension: int = 768):
        """Initialize FAISS vector store.

        Args:
            dimension: Dimension of embedding vectors (default: 768)

        Example:
            >>> store = VectorStore()
            >>> store.size()
            0
        """
        self.dimension = dimension
        self.index = faiss.IndexFlatL2(dimension)  # L2 distance for exact search

        # Bidirectional mapping between chunk_ids and FAISS indices
        self.chunk_id_to_idx: Dict[str, int] = {}  # chunk_id -> FAISS index
        self.idx_to_chunk_id: Dict[int, str] = {}  # FAISS index -> chunk_id
        self.next_idx = 0  # Next available FAISS index

    def add(self, embedding: np.ndarray, chunk_id: str) -> None:
        """Add single embedding vector to the index.

        Args:
            embedding: Vector of shape (768,)
            chunk_id: Unique identifier for this chunk

        Raises:
            ValueError: If embedding dimension doesn't match or chunk_id already exists

        Example:
            >>> store = VectorStore()
            >>> vector = np.random.rand(768).astype('float32')
            >>> store.add(vector, "chunk-abc-123")
            >>> store.size()
            1
        """
        if embedding.shape != (self.dimension,):
            raise ValueError(
                f"Embedding dimension {embedding.shape} doesn't match store dimension ({self.dimension},)"
            )

        if chunk_id in self.chunk_id_to_idx:
            raise ValueError(f"Chunk ID {chunk_id} already exists in the index")

        # FAISS requires 2D array of shape (1, dimension)
        embedding_2d = embedding.reshape(1, -1)

        # Add to FAISS index
        self.index.add(embedding_2d)

        # Update mappings
        faiss_idx = self.next_idx
        self.chunk_id_to_idx[chunk_id] = faiss_idx
        self.idx_to_chunk_id[faiss_idx] = chunk_id
        self.next_idx += 1

    def add_batch(self, embeddings: np.ndarray, chunk_ids: List[str]) -> None:
        """Add multiple embedding vectors to the index.

        Args:
            embeddings: Array of shape (N, 768)
            chunk_ids: List of N unique chunk identifiers

        Raises:
            ValueError: If dimensions don't match or any chunk_id already exists

        Example:
            >>> store = VectorStore()
            >>> vectors = np.random.rand(3, 768).astype('float32')
            >>> ids = ["chunk-1", "chunk-2", "chunk-3"]
            >>> store.add_batch(vectors, ids)
            >>> store.size()
            3
        """
        if len(embeddings) != len(chunk_ids):
            raise ValueError(
                f"Number of embeddings ({len(embeddings)}) doesn't match number of chunk_ids ({len(chunk_ids)})"
            )

        if embeddings.ndim != 2 or embeddings.shape[1] != self.dimension:
            raise ValueError(
                f"Embeddings shape {embeddings.shape} invalid. Expected (N, {self.dimension})"
            )

        # Check for duplicate chunk_ids
        for chunk_id in chunk_ids:
            if chunk_id in self.chunk_id_to_idx:
                raise ValueError(f"Chunk ID {chunk_id} already exists in the index")

        # Add to FAISS index (all at once for efficiency)
        self.index.add(embeddings)

        # Update mappings
        for i, chunk_id in enumerate(chunk_ids):
            faiss_idx = self.next_idx + i
            self.chunk_id_to_idx[chunk_id] = faiss_idx
            self.idx_to_chunk_id[faiss_idx] = chunk_id

        self.next_idx += len(chunk_ids)

    def search(self, query_embedding: np.ndarray, top_k: int = 10) -> List[Tuple[str, float]]:
        """Search for similar vectors.

        Args:
            query_embedding: Query vector of shape (768,)
            top_k: Number of results to return

        Returns:
            List of (chunk_id, distance) tuples, sorted by distance (lowest first)

        Example:
            >>> store = VectorStore()
            >>> # ... add some vectors ...
            >>> query = np.random.rand(768).astype('float32')
            >>> results = store.search(query, top_k=5)
            >>> for chunk_id, distance in results:
            ...     print(f"{chunk_id}: {distance:.3f}")
        """
        if self.index.ntotal == 0:
            return []

        if query_embedding.shape != (self.dimension,):
            raise ValueError(
                f"Query embedding dimension {query_embedding.shape} doesn't match store dimension ({self.dimension},)"
            )

        # Limit top_k to number of vectors in index
        k = min(top_k, self.index.ntotal)

        # FAISS requires 2D array of shape (1, dimension)
        query_2d = query_embedding.reshape(1, -1)

        # Search returns distances and FAISS indices
        distances, indices = self.index.search(query_2d, k)

        # Convert FAISS indices to chunk_ids
        results = []
        for i in range(k):
            faiss_idx = int(indices[0][i])
            distance = float(distances[0][i])
            chunk_id = self.idx_to_chunk_id.get(faiss_idx)

            if chunk_id is not None:
                results.append((chunk_id, distance))

        return results

    def save(self, path: str) -> None:
        """Save FAISS index and ID mappings to disk.

        Saves two files:
        - {path}: FAISS index
        - {path}.mappings: Pickled ID mappings

        Args:
            path: Path to save index file

        Example:
            >>> store = VectorStore()
            >>> # ... add vectors ...
            >>> store.save("./rag_index/faiss.index")
        """
        # Create directory if it doesn't exist
        Path(path).parent.mkdir(parents=True, exist_ok=True)

        # Save FAISS index
        faiss.write_index(self.index, path)

        # Save ID mappings
        mappings = {
            "chunk_id_to_idx": self.chunk_id_to_idx,
            "idx_to_chunk_id": self.idx_to_chunk_id,
            "next_idx": self.next_idx,
            "dimension": self.dimension
        }

        with open(f"{path}.mappings", "wb") as f:
            pickle.dump(mappings, f)

    def load(self, path: str) -> None:
        """Load FAISS index and ID mappings from disk.

        Args:
            path: Path to index file

        Raises:
            FileNotFoundError: If index or mappings file doesn't exist

        Example:
            >>> store = VectorStore()
            >>> store.load("./rag_index/faiss.index")
            >>> print(f"Loaded {store.size()} vectors")
        """
        if not os.path.exists(path):
            raise FileNotFoundError(f"Index file not found: {path}")

        if not os.path.exists(f"{path}.mappings"):
            raise FileNotFoundError(f"Mappings file not found: {path}.mappings")

        # Load FAISS index
        self.index = faiss.read_index(path)

        # Load ID mappings
        with open(f"{path}.mappings", "rb") as f:
            mappings = pickle.load(f)

        self.chunk_id_to_idx = mappings["chunk_id_to_idx"]
        self.idx_to_chunk_id = mappings["idx_to_chunk_id"]
        self.next_idx = mappings["next_idx"]
        self.dimension = mappings["dimension"]

    def size(self) -> int:
        """Get number of vectors in the index.

        Returns:
            Number of vectors stored

        Example:
            >>> store = VectorStore()
            >>> store.size()
            0
        """
        return self.index.ntotal
