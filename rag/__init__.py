"""RAG (Retrieval-Augmented Generation) infrastructure for semantic code search.

This package provides:
- Embedding model wrapper for sentence-transformers
- FAISS vector store for similarity search
- Metadata store for code chunk information
"""

from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.metadata_store import MetadataStore

__all__ = ["EmbeddingModel", "VectorStore", "MetadataStore"]
