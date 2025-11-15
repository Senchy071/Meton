#!/usr/bin/env python3
"""
Long-Term Memory System.

Persistent memory system for cross-session learning with semantic search,
consolidation, and decay mechanisms.
"""

import json
import math
import uuid
import threading
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Optional, Tuple
import numpy as np

from .memory_embeddings import MemoryEmbeddings

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False


@dataclass
class Memory:
    """Represents a single memory entry."""

    id: str  # UUID
    timestamp: str  # ISO 8601 format
    memory_type: str  # fact, preference, skill, conversation, code_pattern
    content: str  # The actual memory
    context: Dict = field(default_factory=dict)  # Additional metadata
    importance: float = 0.5  # 0.0-1.0 importance score
    access_count: int = 0  # How many times retrieved
    last_accessed: str = ""  # ISO 8601 format
    tags: List[str] = field(default_factory=list)
    embedding: Optional[np.ndarray] = None  # Not persisted directly

    def __post_init__(self):
        """Initialize last_accessed if not set."""
        if not self.last_accessed:
            self.last_accessed = self.timestamp

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization (without embedding)."""
        data = asdict(self)
        data.pop('embedding', None)  # Don't serialize embedding
        return data

    @classmethod
    def from_dict(cls, data: Dict) -> 'Memory':
        """Create Memory from dictionary."""
        # Remove embedding if present
        data.pop('embedding', None)
        return cls(**data)

    def update_access(self):
        """Update access count and timestamp."""
        self.access_count += 1
        self.last_accessed = datetime.now().isoformat()


class LongTermMemory:
    """Persistent memory system for cross-session learning."""

    VALID_MEMORY_TYPES = {'fact', 'preference', 'skill', 'conversation', 'code_pattern'}

    def __init__(
        self,
        storage_path: str = "./memory",
        max_memories: int = 10000,
        consolidation_threshold: float = 0.95,
        decay_rate: float = 0.1,
        auto_consolidate: bool = True,
        auto_decay: bool = True,
        min_importance_for_retrieval: float = 0.3
    ):
        """
        Initialize long-term memory system.

        Args:
            storage_path: Directory to store memory files
            max_memories: Maximum number of memories to keep
            consolidation_threshold: Similarity threshold for consolidation (0.0-1.0)
            decay_rate: Monthly decay rate for importance
            auto_consolidate: Automatically consolidate on store
            auto_decay: Automatically apply decay on retrieval
            min_importance_for_retrieval: Minimum importance to retrieve
        """
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(exist_ok=True, parents=True)

        self.max_memories = max_memories
        self.consolidation_threshold = consolidation_threshold
        self.decay_rate = decay_rate
        self.auto_consolidate = auto_consolidate
        self.auto_decay = auto_decay
        self.min_importance_for_retrieval = min_importance_for_retrieval

        self.memories: Dict[str, Memory] = {}  # id -> Memory
        self.memory_id_list: List[str] = []  # Maintains order for FAISS
        self.vector_store = None
        self.embeddings_model = None
        self.lock = threading.Lock()

        self._initialize()

    def _initialize(self):
        """Initialize embeddings model, vector store, and load memories."""
        # Initialize embeddings
        try:
            self.embeddings_model = MemoryEmbeddings()
        except ImportError:
            raise ImportError(
                "Memory system requires sentence-transformers. "
                "Install with: pip install sentence-transformers"
            )

        # Initialize FAISS vector store
        if not FAISS_AVAILABLE:
            raise ImportError(
                "Memory system requires faiss-cpu. "
                "Install with: pip install faiss-cpu"
            )

        dimension = self.embeddings_model.dimension
        # Use HNSW index for better performance with large datasets
        self.vector_store = faiss.IndexHNSWFlat(dimension, 32)

        # Load existing memories
        self._load_memories()

    def store_memory(
        self,
        content: str,
        memory_type: str,
        context: Dict = None,
        importance: float = 0.5,
        tags: List[str] = None
    ) -> str:
        """
        Store new memory.

        Args:
            content: The memory content
            memory_type: Type of memory (fact, preference, skill, conversation, code_pattern)
            context: Additional metadata
            importance: Importance score (0.0-1.0)
            tags: List of tags for categorization

        Returns:
            Memory ID (UUID)

        Raises:
            ValueError: If memory_type is invalid or importance out of range
        """
        if memory_type not in self.VALID_MEMORY_TYPES:
            raise ValueError(
                f"Invalid memory_type: {memory_type}. "
                f"Must be one of {self.VALID_MEMORY_TYPES}"
            )

        if not 0.0 <= importance <= 1.0:
            raise ValueError(f"Importance must be between 0.0 and 1.0, got {importance}")

        with self.lock:
            # Create memory
            memory_id = str(uuid.uuid4())
            timestamp = datetime.now().isoformat()

            memory = Memory(
                id=memory_id,
                timestamp=timestamp,
                memory_type=memory_type,
                content=content,
                context=context or {},
                importance=importance,
                tags=tags or [],
                last_accessed=timestamp
            )

            # Generate embedding
            memory.embedding = self.embeddings_model.encode(content)

            # Add to storage
            self.memories[memory_id] = memory
            self.memory_id_list.append(memory_id)

            # Add to vector store
            self._add_to_vector_store(memory)

            # Auto-consolidate if enabled
            if self.auto_consolidate:
                self._check_and_consolidate(memory)

            # Prune if exceeding max
            if len(self.memories) > self.max_memories:
                self._prune_memories()

            # Persist
            self._save_memories()

            return memory_id

    def retrieve_relevant(
        self,
        query: str,
        top_k: int = 5,
        memory_type: str = None,
        min_importance: float = None
    ) -> List[Memory]:
        """
        Retrieve relevant memories using semantic search.

        Args:
            query: Search query
            top_k: Number of memories to retrieve
            memory_type: Filter by memory type (optional)
            min_importance: Minimum importance threshold (optional)

        Returns:
            List of relevant memories, sorted by relevance
        """
        if min_importance is None:
            min_importance = self.min_importance_for_retrieval

        with self.lock:
            # Apply decay if enabled
            if self.auto_decay:
                self._apply_decay()

            # Search vector store
            if len(self.memories) == 0:
                return []

            query_embedding = self.embeddings_model.encode(query)

            # Search more than needed for filtering
            search_k = min(len(self.memories), top_k * 3)
            distances, indices = self.vector_store.search(
                query_embedding.reshape(1, -1), search_k
            )

            # Get memories
            relevant_memories = []
            for idx in indices[0]:
                if idx < 0 or idx >= len(self.memory_id_list):
                    continue

                memory_id = self.memory_id_list[idx]
                memory = self.memories.get(memory_id)

                if not memory:
                    continue

                # Apply filters
                if memory_type and memory.memory_type != memory_type:
                    continue

                if memory.importance < min_importance:
                    continue

                # Update access
                memory.update_access()
                relevant_memories.append(memory)

                if len(relevant_memories) >= top_k:
                    break

            # Save updated access counts
            if relevant_memories:
                self._save_memories()

            return relevant_memories

    def get_memory(self, memory_id: str) -> Memory:
        """
        Retrieve specific memory by ID.

        Args:
            memory_id: Memory UUID

        Returns:
            Memory object

        Raises:
            KeyError: If memory not found
        """
        with self.lock:
            if memory_id not in self.memories:
                raise KeyError(f"Memory not found: {memory_id}")

            memory = self.memories[memory_id]
            memory.update_access()
            self._save_memories()

            return memory

    def update_memory(self, memory_id: str, **kwargs) -> None:
        """
        Update memory fields.

        Args:
            memory_id: Memory UUID
            **kwargs: Fields to update (content, importance, tags, etc.)

        Raises:
            KeyError: If memory not found
        """
        with self.lock:
            if memory_id not in self.memories:
                raise KeyError(f"Memory not found: {memory_id}")

            memory = self.memories[memory_id]
            content_changed = False

            # Update fields
            for key, value in kwargs.items():
                if key == 'content' and value != memory.content:
                    content_changed = True
                    memory.content = value
                elif key == 'importance':
                    if not 0.0 <= value <= 1.0:
                        raise ValueError(f"Importance must be 0.0-1.0, got {value}")
                    memory.importance = value
                elif key == 'memory_type':
                    if value not in self.VALID_MEMORY_TYPES:
                        raise ValueError(f"Invalid memory_type: {value}")
                    memory.memory_type = value
                elif key == 'tags':
                    memory.tags = value
                elif key == 'context':
                    memory.context = value

            # Re-generate embedding if content changed
            if content_changed:
                memory.embedding = self.embeddings_model.encode(memory.content)
                # Rebuild vector store (simple approach - could be optimized)
                self._rebuild_vector_store()

            self._save_memories()

    def delete_memory(self, memory_id: str) -> bool:
        """
        Remove memory from system.

        Args:
            memory_id: Memory UUID

        Returns:
            True if deleted, False if not found
        """
        with self.lock:
            if memory_id not in self.memories:
                return False

            # Remove from storage
            del self.memories[memory_id]
            self.memory_id_list.remove(memory_id)

            # Rebuild vector store
            self._rebuild_vector_store()

            self._save_memories()
            return True

    def consolidate_memories(self, similarity_threshold: float = None) -> int:
        """
        Merge similar/duplicate memories.

        Args:
            similarity_threshold: Similarity threshold (0.0-1.0)

        Returns:
            Count of memories consolidated
        """
        if similarity_threshold is None:
            similarity_threshold = self.consolidation_threshold

        with self.lock:
            consolidated_count = 0
            memories_to_remove = set()

            # Compare all pairs (could be optimized with clustering)
            memory_list = list(self.memories.values())

            for i, mem1 in enumerate(memory_list):
                if mem1.id in memories_to_remove:
                    continue

                for mem2 in memory_list[i+1:]:
                    if mem2.id in memories_to_remove:
                        continue

                    # Check similarity
                    similarity = self.embeddings_model.similarity(
                        mem1.embedding, mem2.embedding
                    )

                    if similarity >= similarity_threshold:
                        # Consolidate: keep more important one
                        if mem1.importance >= mem2.importance:
                            keeper, removed = mem1, mem2
                        else:
                            keeper, removed = mem2, mem1

                        # Merge information
                        keeper.importance = min(1.0, keeper.importance * 1.1)
                        keeper.access_count += removed.access_count
                        keeper.tags = list(set(keeper.tags + removed.tags))

                        # Mark for removal
                        memories_to_remove.add(removed.id)
                        consolidated_count += 1

            # Remove consolidated memories
            for memory_id in memories_to_remove:
                del self.memories[memory_id]
                self.memory_id_list.remove(memory_id)

            if consolidated_count > 0:
                self._rebuild_vector_store()
                self._save_memories()

            return consolidated_count

    def decay_memories(self, decay_rate: float = None) -> int:
        """
        Reduce importance of old, unused memories.

        Args:
            decay_rate: Monthly decay rate (default: use configured rate)

        Returns:
            Count of memories decayed
        """
        if decay_rate is None:
            decay_rate = self.decay_rate

        with self.lock:
            decayed_count = 0
            now = datetime.now()

            for memory in self.memories.values():
                old_importance = memory.importance

                # Calculate decayed importance
                timestamp = datetime.fromisoformat(memory.timestamp)
                days_old = (now - timestamp).days

                # Age factor: exponential decay over months
                age_factor = math.exp(-decay_rate * days_old / 30)

                # Access factor: cap at 10 accesses
                access_factor = min(memory.access_count / 10, 1.0)

                # Combined decay
                new_importance = old_importance * age_factor * (0.5 + 0.5 * access_factor)

                if new_importance < old_importance:
                    memory.importance = max(0.0, new_importance)
                    decayed_count += 1

            if decayed_count > 0:
                self._save_memories()

            return decayed_count

    def get_memory_stats(self) -> Dict:
        """
        Get statistics about memory system.

        Returns:
            Dictionary with statistics
        """
        with self.lock:
            memories_list = list(self.memories.values())

            # Group by type
            by_type = {}
            for memory in memories_list:
                by_type[memory.memory_type] = by_type.get(memory.memory_type, 0) + 1

            # Average importance
            avg_importance = (
                sum(m.importance for m in memories_list) / len(memories_list)
                if memories_list else 0.0
            )

            # Most accessed
            most_accessed = sorted(
                memories_list, key=lambda m: m.access_count, reverse=True
            )[:5]

            # Recent memories
            recent_memories = sorted(
                memories_list, key=lambda m: m.timestamp, reverse=True
            )[:5]

            return {
                "total_memories": len(self.memories),
                "by_type": by_type,
                "avg_importance": avg_importance,
                "most_accessed": [
                    {
                        "id": m.id,
                        "content": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                        "access_count": m.access_count,
                        "importance": m.importance
                    }
                    for m in most_accessed
                ],
                "recent_memories": [
                    {
                        "id": m.id,
                        "content": m.content[:100] + "..." if len(m.content) > 100 else m.content,
                        "timestamp": m.timestamp,
                        "type": m.memory_type
                    }
                    for m in recent_memories
                ]
            }

    def export_memories(self, format: str = "json") -> str:
        """
        Export all memories to file.

        Args:
            format: Export format (json or csv)

        Returns:
            Path to exported file

        Raises:
            ValueError: If format is not supported
        """
        if format not in {"json", "csv"}:
            raise ValueError(f"Unsupported format: {format}. Use 'json' or 'csv'")

        with self.lock:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            export_path = self.storage_path / f"export_{timestamp}.{format}"

            if format == "json":
                data = [m.to_dict() for m in self.memories.values()]
                with open(export_path, 'w') as f:
                    json.dump(data, f, indent=2)

            elif format == "csv":
                import csv
                with open(export_path, 'w', newline='') as f:
                    if self.memories:
                        # Get fieldnames from first memory
                        fieldnames = list(next(iter(self.memories.values())).to_dict().keys())
                        writer = csv.DictWriter(f, fieldnames=fieldnames)
                        writer.writeheader()
                        for memory in self.memories.values():
                            writer.writerow(memory.to_dict())

            return str(export_path)

    def import_memories(self, file_path: str) -> int:
        """
        Import memories from file.

        Args:
            file_path: Path to import file (JSON or CSV)

        Returns:
            Count of memories imported

        Raises:
            ValueError: If file format is invalid
            FileNotFoundError: If file doesn't exist
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"Import file not found: {file_path}")

        with self.lock:
            imported_count = 0

            if file_path.suffix == '.json':
                with open(file_path, 'r') as f:
                    data = json.load(f)

                for mem_dict in data:
                    try:
                        # Create Memory object
                        memory = Memory.from_dict(mem_dict)

                        # Generate embedding
                        memory.embedding = self.embeddings_model.encode(memory.content)

                        # Add to storage
                        self.memories[memory.id] = memory
                        self.memory_id_list.append(memory.id)

                        imported_count += 1
                    except Exception as e:
                        print(f"Warning: Failed to import memory: {e}")
                        continue

            elif file_path.suffix == '.csv':
                import csv
                with open(file_path, 'r') as f:
                    reader = csv.DictReader(f)
                    for row in reader:
                        try:
                            # Convert strings to correct types
                            if 'context' in row:
                                row['context'] = json.loads(row['context']) if row['context'] else {}
                            if 'tags' in row:
                                row['tags'] = json.loads(row['tags']) if row['tags'] else []
                            if 'importance' in row:
                                row['importance'] = float(row['importance'])
                            if 'access_count' in row:
                                row['access_count'] = int(row['access_count'])

                            memory = Memory.from_dict(row)
                            memory.embedding = self.embeddings_model.encode(memory.content)

                            self.memories[memory.id] = memory
                            self.memory_id_list.append(memory.id)

                            imported_count += 1
                        except Exception as e:
                            print(f"Warning: Failed to import memory: {e}")
                            continue
            else:
                raise ValueError(f"Unsupported file format: {file_path.suffix}")

            # Rebuild vector store
            if imported_count > 0:
                self._rebuild_vector_store()
                self._save_memories()

            return imported_count

    # Private helper methods

    def _add_to_vector_store(self, memory: Memory):
        """Add memory embedding to FAISS index."""
        if memory.embedding is not None:
            self.vector_store.add(memory.embedding.reshape(1, -1))

    def _rebuild_vector_store(self):
        """Rebuild FAISS index from all memories."""
        dimension = self.embeddings_model.dimension
        self.vector_store = faiss.IndexHNSWFlat(dimension, 32)

        if self.memories:
            # Rebuild memory_id_list in order
            self.memory_id_list = list(self.memories.keys())

            # Add all embeddings
            embeddings = np.array([
                self.memories[mid].embedding for mid in self.memory_id_list
            ])
            self.vector_store.add(embeddings)

    def _check_and_consolidate(self, new_memory: Memory):
        """Check if new memory should be consolidated with existing ones."""
        for existing_memory in self.memories.values():
            if existing_memory.id == new_memory.id:
                continue

            similarity = self.embeddings_model.similarity(
                new_memory.embedding, existing_memory.embedding
            )

            if similarity >= self.consolidation_threshold:
                # Merge into existing
                existing_memory.importance = min(1.0, existing_memory.importance * 1.1)
                existing_memory.tags = list(set(existing_memory.tags + new_memory.tags))

                # Remove new memory
                del self.memories[new_memory.id]
                self.memory_id_list.remove(new_memory.id)
                self._rebuild_vector_store()
                break

    def _prune_memories(self):
        """Remove lowest importance memories when exceeding max."""
        if len(self.memories) <= self.max_memories:
            return

        # Sort by importance
        sorted_memories = sorted(
            self.memories.values(),
            key=lambda m: m.importance
        )

        # Remove lowest importance
        to_remove = len(self.memories) - self.max_memories
        for memory in sorted_memories[:to_remove]:
            del self.memories[memory.id]
            self.memory_id_list.remove(memory.id)

        self._rebuild_vector_store()

    def _apply_decay(self):
        """Apply time-based decay to all memories."""
        # Only apply decay periodically (every 100 retrievals)
        if not hasattr(self, '_retrieval_count'):
            self._retrieval_count = 0

        self._retrieval_count += 1
        if self._retrieval_count % 100 == 0:
            self.decay_memories()

    def _save_memories(self):
        """Persist memories to disk."""
        memories_file = self.storage_path / "memories.json"
        embeddings_file = self.storage_path / "embeddings.npy"

        # Save memories (without embeddings)
        data = [m.to_dict() for m in self.memories.values()]
        with open(memories_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Save embeddings separately
        if self.memory_id_list:
            embeddings = np.array([
                self.memories[mid].embedding for mid in self.memory_id_list
            ])
            np.save(embeddings_file, embeddings)

    def _load_memories(self):
        """Load memories from disk."""
        memories_file = self.storage_path / "memories.json"
        embeddings_file = self.storage_path / "embeddings.npy"

        if not memories_file.exists():
            return

        # Load memories
        with open(memories_file, 'r') as f:
            data = json.load(f)

        # Load embeddings
        if embeddings_file.exists():
            embeddings = np.load(embeddings_file)
        else:
            embeddings = None

        # Reconstruct memory objects
        for i, mem_dict in enumerate(data):
            memory = Memory.from_dict(mem_dict)

            # Attach embedding
            if embeddings is not None and i < len(embeddings):
                memory.embedding = embeddings[i]
            else:
                # Generate if missing
                memory.embedding = self.embeddings_model.encode(memory.content)

            self.memories[memory.id] = memory
            self.memory_id_list.append(memory.id)

        # Rebuild vector store
        if self.memories:
            self._rebuild_vector_store()
