"""Embedding model wrapper for sentence-transformers."""

from typing import List, Union
import numpy as np
from sentence_transformers import SentenceTransformer


class EmbeddingModel:
    """Wrapper for sentence-transformers embedding model.

    Converts text to fixed-dimensional vector representations for semantic search.
    Model is cached in memory after first load.

    Example:
        >>> embedder = EmbeddingModel()
        >>> vector = embedder.encode("def hello(): print('world')")
        >>> vector.shape
        (768,)
    """

    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """Initialize embedding model.

        Args:
            model_name: HuggingFace model identifier

        Example:
            >>> embedder = EmbeddingModel()
            >>> embedder.get_dimension()
            768
        """
        self.model_name = model_name
        self._model = None
        self._dimension = 768  # all-mpnet-base-v2 produces 768-dim vectors

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the model on first use.

        Returns:
            Loaded SentenceTransformer model
        """
        if self._model is None:
            self._model = SentenceTransformer(self.model_name)
        return self._model

    def encode(self, text: str) -> np.ndarray:
        """Convert single text to embedding vector.

        Args:
            text: Text to encode (code snippet, docstring, etc.)

        Returns:
            768-dimensional numpy array (float32)

        Example:
            >>> embedder = EmbeddingModel()
            >>> vector = embedder.encode("def authenticate_user(): pass")
            >>> vector.shape
            (768,)
        """
        # Handle empty strings
        if not text or not text.strip():
            return np.zeros(self._dimension, dtype=np.float32)

        # SentenceTransformer returns shape (768,) for single string
        embedding = self.model.encode(text, convert_to_numpy=True)
        return embedding.astype(np.float32)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """Convert multiple texts to embedding vectors.

        Args:
            texts: List of texts to encode

        Returns:
            (N, 768) numpy array where N = len(texts)

        Example:
            >>> embedder = EmbeddingModel()
            >>> vectors = embedder.encode_batch(["code 1", "code 2", "code 3"])
            >>> vectors.shape
            (3, 768)
        """
        if not texts:
            return np.empty((0, self._dimension), dtype=np.float32)

        # Replace empty strings with placeholder to avoid model issues
        processed_texts = [text if text and text.strip() else " " for text in texts]

        # SentenceTransformer returns shape (N, 768) for list of strings
        embeddings = self.model.encode(processed_texts, convert_to_numpy=True, show_progress_bar=False)
        return embeddings.astype(np.float32)

    def get_dimension(self) -> int:
        """Get embedding dimension.

        Returns:
            Dimension of embedding vectors (768 for all-mpnet-base-v2)

        Example:
            >>> embedder = EmbeddingModel()
            >>> embedder.get_dimension()
            768
        """
        return self._dimension
