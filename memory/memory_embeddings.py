#!/usr/bin/env python3
"""
Memory Embeddings Module.

Handles embedding generation for long-term memories using sentence transformers.
"""

from typing import List
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False


class MemoryEmbeddings:
    """Handles embedding generation for memories."""

    def __init__(self, model_name: str = "sentence-transformers/all-mpnet-base-v2"):
        """
        Initialize embeddings model.

        Args:
            model_name: Name of sentence-transformers model to use
        """
        if not SENTENCE_TRANSFORMERS_AVAILABLE:
            raise ImportError(
                "sentence-transformers not installed. "
                "Install with: pip install sentence-transformers"
            )

        self.model_name = model_name
        self.model = SentenceTransformer(model_name)
        self.dimension = self.model.get_sentence_embedding_dimension()

    def encode(self, text: str) -> np.ndarray:
        """
        Generate embedding for single text.

        Args:
            text: Text to encode

        Returns:
            Embedding vector as numpy array
        """
        if not text or not text.strip():
            # Return zero vector for empty text
            return np.zeros(self.dimension, dtype=np.float32)

        return self.model.encode(text, convert_to_numpy=True, show_progress_bar=False)

    def encode_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for multiple texts.

        Args:
            texts: List of texts to encode

        Returns:
            Array of embeddings (shape: [len(texts), dimension])
        """
        if not texts:
            return np.array([]).reshape(0, self.dimension)

        # Filter empty texts, keep track of indices
        valid_texts = []
        valid_indices = []
        for i, text in enumerate(texts):
            if text and text.strip():
                valid_texts.append(text)
                valid_indices.append(i)

        # Create result array
        result = np.zeros((len(texts), self.dimension), dtype=np.float32)

        if valid_texts:
            # Encode valid texts
            embeddings = self.model.encode(
                valid_texts,
                convert_to_numpy=True,
                show_progress_bar=False
            )

            # Place embeddings at correct indices
            for i, idx in enumerate(valid_indices):
                result[idx] = embeddings[i]

        return result

    def similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Calculate cosine similarity between two embeddings.

        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector

        Returns:
            Cosine similarity (0.0 to 1.0)
        """
        # Normalize vectors
        norm1 = np.linalg.norm(embedding1)
        norm2 = np.linalg.norm(embedding2)

        if norm1 == 0 or norm2 == 0:
            return 0.0

        # Cosine similarity
        similarity = np.dot(embedding1, embedding2) / (norm1 * norm2)

        # Clamp to [0, 1]
        return float(max(0.0, min(1.0, (similarity + 1) / 2)))
