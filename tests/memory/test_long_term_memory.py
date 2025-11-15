#!/usr/bin/env python3
"""
Tests for Long-Term Memory System.

Tests cover:
- Memory storage and retrieval
- Semantic search
- CRUD operations
- Consolidation
- Decay mechanism
- Importance scoring
- Access tracking
- Export/import
- Vector store operations
- Edge cases
- Integration
"""

import sys
import tempfile
import shutil
import time
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from memory.long_term_memory import LongTermMemory, Memory
    from memory.memory_embeddings import MemoryEmbeddings
    MEMORY_AVAILABLE = True
except ImportError as e:
    MEMORY_AVAILABLE = False
    print(f"Warning: Memory system not available: {e}")


def create_test_memory():
    """Create test memory with temp storage."""
    temp_dir = tempfile.mkdtemp()
    memory = LongTermMemory(storage_path=temp_dir)
    return memory, temp_dir


def cleanup_test_memory(memory, temp_dir):
    """Clean up test memory."""
    shutil.rmtree(temp_dir, ignore_errors=True)


# Memory Storage Tests

def test_store_memory_basic():
    """Test basic memory storage."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_store_memory_basic (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory_id = memory.store_memory(
        content="User prefers Python over JavaScript",
        memory_type="preference",
        importance=0.8
    )

    assert memory_id is not None
    assert len(memory_id) == 36  # UUID length
    assert memory_id in memory.memories

    mem = memory.memories[memory_id]
    assert mem.content == "User prefers Python over JavaScript"
    assert mem.memory_type == "preference"
    assert mem.importance == 0.8

    cleanup_test_memory(memory, temp_dir)


def test_store_memory_with_metadata():
    """Test storing memory with context and tags."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_store_memory_with_metadata (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory_id = memory.store_memory(
        content="FastAPI uses Pydantic for validation",
        memory_type="fact",
        context={"source": "documentation", "confidence": 0.95},
        importance=0.7,
        tags=["python", "fastapi", "validation"]
    )

    mem = memory.get_memory(memory_id)
    assert mem.context["source"] == "documentation"
    assert mem.context["confidence"] == 0.95
    assert "fastapi" in mem.tags

    cleanup_test_memory(memory, temp_dir)


def test_store_invalid_memory_type():
    """Test storing with invalid memory type."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_store_invalid_memory_type (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    try:
        memory.store_memory(
            content="Test",
            memory_type="invalid_type"
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Invalid memory_type" in str(e)

    cleanup_test_memory(memory, temp_dir)


def test_store_invalid_importance():
    """Test storing with invalid importance score."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_store_invalid_importance (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    try:
        memory.store_memory(
            content="Test",
            memory_type="fact",
            importance=1.5  # Out of range
        )
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "between 0.0 and 1.0" in str(e)

    cleanup_test_memory(memory, temp_dir)


# Retrieval Tests

def test_retrieve_relevant_memories():
    """Test semantic search for relevant memories."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_retrieve_relevant_memories (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    # Store related memories
    memory.store_memory("Python is a programming language", "fact")
    memory.store_memory("FastAPI is a Python web framework", "fact")
    memory.store_memory("User prefers dark mode", "preference")

    # Search for Python-related
    results = memory.retrieve_relevant("Python web development", top_k=2)

    assert len(results) > 0
    assert any("Python" in m.content for m in results)

    cleanup_test_memory(memory, temp_dir)


def test_retrieve_by_type():
    """Test filtering retrieval by memory type."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_retrieve_by_type (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory.store_memory("Python fact", "fact")
    memory.store_memory("User prefers Python", "preference")
    memory.store_memory("Python skill learned", "skill")

    # Retrieve only preferences
    results = memory.retrieve_relevant(
        "Python",
        top_k=5,
        memory_type="preference"
    )

    assert all(m.memory_type == "preference" for m in results)

    cleanup_test_memory(memory, temp_dir)


def test_retrieve_by_importance():
    """Test filtering by minimum importance."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_retrieve_by_importance (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory.store_memory("Low importance", "fact", importance=0.2)
    memory.store_memory("High importance", "fact", importance=0.9)

    results = memory.retrieve_relevant(
        "importance",
        top_k=10,
        min_importance=0.5
    )

    assert all(m.importance >= 0.5 for m in results)

    cleanup_test_memory(memory, temp_dir)


def test_retrieve_empty():
    """Test retrieval from empty memory."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_retrieve_empty (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    results = memory.retrieve_relevant("test query")

    assert results == []

    cleanup_test_memory(memory, temp_dir)


# CRUD Tests

def test_get_memory_by_id():
    """Test retrieving memory by ID."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_get_memory_by_id (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory_id = memory.store_memory("Test memory", "fact")

    retrieved = memory.get_memory(memory_id)

    assert retrieved.id == memory_id
    assert retrieved.content == "Test memory"

    cleanup_test_memory(memory, temp_dir)


def test_get_nonexistent_memory():
    """Test retrieving non-existent memory."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_get_nonexistent_memory (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    try:
        memory.get_memory("nonexistent-id")
        assert False, "Should have raised KeyError"
    except KeyError as e:
        assert "not found" in str(e)

    cleanup_test_memory(memory, temp_dir)


def test_update_memory():
    """Test updating memory fields."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_update_memory (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory_id = memory.store_memory("Original content", "fact", importance=0.5)

    memory.update_memory(
        memory_id,
        content="Updated content",
        importance=0.8,
        tags=["updated"]
    )

    mem = memory.get_memory(memory_id)
    assert mem.content == "Updated content"
    assert mem.importance == 0.8
    assert "updated" in mem.tags

    cleanup_test_memory(memory, temp_dir)


def test_update_nonexistent_memory():
    """Test updating non-existent memory."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_update_nonexistent_memory (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    try:
        memory.update_memory("nonexistent-id", importance=0.5)
        assert False, "Should have raised KeyError"
    except KeyError:
        pass

    cleanup_test_memory(memory, temp_dir)


def test_delete_memory():
    """Test deleting memory."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_delete_memory (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory_id = memory.store_memory("To be deleted", "fact")
    assert memory_id in memory.memories

    result = memory.delete_memory(memory_id)

    assert result is True
    assert memory_id not in memory.memories

    cleanup_test_memory(memory, temp_dir)


def test_delete_nonexistent_memory():
    """Test deleting non-existent memory."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_delete_nonexistent_memory (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    result = memory.delete_memory("nonexistent-id")

    assert result is False

    cleanup_test_memory(memory, temp_dir)


# Consolidation Tests

def test_consolidate_similar_memories():
    """Test consolidating similar memories."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_consolidate_similar_memories (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    # Store very similar memories
    memory.store_memory("Python is great for web development", "fact")
    memory.store_memory("Python is excellent for web development", "fact")

    initial_count = len(memory.memories)

    consolidated = memory.consolidate_memories(similarity_threshold=0.9)

    assert consolidated > 0
    assert len(memory.memories) < initial_count

    cleanup_test_memory(memory, temp_dir)


def test_consolidate_no_duplicates():
    """Test consolidation with no duplicates."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_consolidate_no_duplicates (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory.store_memory("Python programming", "fact")
    memory.store_memory("Java programming", "fact")
    memory.store_memory("Rust programming", "fact")

    initial_count = len(memory.memories)

    consolidated = memory.consolidate_memories(similarity_threshold=0.95)

    assert consolidated == 0
    assert len(memory.memories) == initial_count

    cleanup_test_memory(memory, temp_dir)


# Decay Tests

def test_decay_memories():
    """Test memory decay mechanism."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_decay_memories (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    # Store memory and manually age it
    memory_id = memory.store_memory("Old memory", "fact", importance=0.9)

    mem = memory.memories[memory_id]
    old_time = (datetime.now() - timedelta(days=60)).isoformat()
    mem.timestamp = old_time

    decayed = memory.decay_memories(decay_rate=0.2)

    assert decayed > 0
    assert mem.importance < 0.9

    cleanup_test_memory(memory, temp_dir)


def test_decay_preserves_accessed():
    """Test decay preserves frequently accessed memories."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_decay_preserves_accessed (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    # Create old but frequently accessed memory
    memory_id = memory.store_memory("Accessed memory", "fact", importance=0.9)

    mem = memory.memories[memory_id]
    mem.timestamp = (datetime.now() - timedelta(days=60)).isoformat()
    mem.access_count = 20  # High access count

    original_importance = mem.importance

    memory.decay_memories(decay_rate=0.2)

    # Should decay less due to high access count
    assert mem.importance > original_importance * 0.5

    cleanup_test_memory(memory, temp_dir)


# Access Tracking Tests

def test_access_count_increments():
    """Test that access count increments on retrieval."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_access_count_increments (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory_id = memory.store_memory("Test memory", "fact")

    mem = memory.memories[memory_id]
    initial_count = mem.access_count

    memory.get_memory(memory_id)
    memory.get_memory(memory_id)

    assert mem.access_count == initial_count + 2

    cleanup_test_memory(memory, temp_dir)


def test_last_accessed_updates():
    """Test that last_accessed timestamp updates."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_last_accessed_updates (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory_id = memory.store_memory("Test memory", "fact")

    mem = memory.memories[memory_id]
    original_time = mem.last_accessed

    time.sleep(0.1)
    memory.get_memory(memory_id)

    assert mem.last_accessed > original_time

    cleanup_test_memory(memory, temp_dir)


# Statistics Tests

def test_get_memory_stats():
    """Test retrieving memory statistics."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_get_memory_stats (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory.store_memory("Fact 1", "fact")
    memory.store_memory("Fact 2", "fact")
    memory.store_memory("Preference 1", "preference")

    stats = memory.get_memory_stats()

    assert stats["total_memories"] == 3
    assert stats["by_type"]["fact"] == 2
    assert stats["by_type"]["preference"] == 1
    assert "avg_importance" in stats
    assert "most_accessed" in stats
    assert "recent_memories" in stats

    cleanup_test_memory(memory, temp_dir)


def test_stats_empty_memory():
    """Test statistics on empty memory."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_stats_empty_memory (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    stats = memory.get_memory_stats()

    assert stats["total_memories"] == 0
    assert stats["avg_importance"] == 0.0

    cleanup_test_memory(memory, temp_dir)


# Export/Import Tests

def test_export_json():
    """Test exporting memories to JSON."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_export_json (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory.store_memory("Test memory 1", "fact")
    memory.store_memory("Test memory 2", "preference")

    export_path = memory.export_memories(format="json")

    assert Path(export_path).exists()
    assert export_path.endswith(".json")

    cleanup_test_memory(memory, temp_dir)


def test_export_csv():
    """Test exporting memories to CSV."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_export_csv (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    memory.store_memory("Test memory 1", "fact")
    memory.store_memory("Test memory 2", "preference")

    export_path = memory.export_memories(format="csv")

    assert Path(export_path).exists()
    assert export_path.endswith(".csv")

    cleanup_test_memory(memory, temp_dir)


def test_export_invalid_format():
    """Test exporting with invalid format."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_export_invalid_format (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    try:
        memory.export_memories(format="xml")
        assert False, "Should have raised ValueError"
    except ValueError as e:
        assert "Unsupported format" in str(e)

    cleanup_test_memory(memory, temp_dir)


def test_import_json():
    """Test importing memories from JSON."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_import_json (memory system not available)")
        return

    memory1, temp_dir1 = create_test_memory()

    memory1.store_memory("Memory 1", "fact")
    memory1.store_memory("Memory 2", "preference")

    export_path = memory1.export_memories(format="json")

    # Import into new memory system
    memory2, temp_dir2 = create_test_memory()
    imported = memory2.import_memories(export_path)

    assert imported == 2
    assert len(memory2.memories) == 2

    cleanup_test_memory(memory1, temp_dir1)
    cleanup_test_memory(memory2, temp_dir2)


def test_import_nonexistent_file():
    """Test importing from non-existent file."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_import_nonexistent_file (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    try:
        memory.import_memories("/nonexistent/file.json")
        assert False, "Should have raised FileNotFoundError"
    except FileNotFoundError:
        pass

    cleanup_test_memory(memory, temp_dir)


# Persistence Tests

def test_save_and_load():
    """Test saving and loading memories."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_save_and_load (memory system not available)")
        return

    temp_dir = tempfile.mkdtemp()

    # Create and populate
    memory1 = LongTermMemory(storage_path=temp_dir)
    memory1.store_memory("Persistent memory", "fact", importance=0.8)

    memory_id = list(memory1.memories.keys())[0]

    # Create new instance (should load)
    memory2 = LongTermMemory(storage_path=temp_dir)

    assert len(memory2.memories) == 1
    assert memory_id in memory2.memories
    assert memory2.memories[memory_id].content == "Persistent memory"

    cleanup_test_memory(memory2, temp_dir)


# Edge Cases

def test_max_memories_limit():
    """Test that max memories limit is enforced."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_max_memories_limit (memory system not available)")
        return

    memory, temp_dir = create_test_memory()
    memory.max_memories = 5

    # Store more than max
    for i in range(10):
        memory.store_memory(f"Memory {i}", "fact", importance=0.5)

    assert len(memory.memories) <= memory.max_memories

    cleanup_test_memory(memory, temp_dir)


def test_empty_content():
    """Test storing memory with empty content."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_empty_content (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    # Should still work (embedding will be zero vector)
    memory_id = memory.store_memory("", "fact")

    assert memory_id in memory.memories

    cleanup_test_memory(memory, temp_dir)


def test_large_content():
    """Test storing memory with large content."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_large_content (memory system not available)")
        return

    memory, temp_dir = create_test_memory()

    large_content = "Test " * 1000

    memory_id = memory.store_memory(large_content, "fact")

    mem = memory.get_memory(memory_id)
    assert mem.content == large_content

    cleanup_test_memory(memory, temp_dir)


# Memory Dataclass Tests

def test_memory_dataclass():
    """Test Memory dataclass."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_memory_dataclass (memory system not available)")
        return

    mem = Memory(
        id="test-id",
        timestamp="2025-11-15T00:00:00",
        memory_type="fact",
        content="Test content"
    )

    assert mem.id == "test-id"
    assert mem.importance == 0.5  # Default
    assert mem.access_count == 0  # Default
    assert mem.tags == []  # Default


def test_memory_to_dict():
    """Test Memory serialization."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_memory_to_dict (memory system not available)")
        return

    mem = Memory(
        id="test-id",
        timestamp="2025-11-15T00:00:00",
        memory_type="fact",
        content="Test content",
        tags=["test"]
    )

    data = mem.to_dict()

    assert data["id"] == "test-id"
    assert data["content"] == "Test content"
    assert "embedding" not in data  # Should not be serialized


def test_memory_from_dict():
    """Test Memory deserialization."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_memory_from_dict (memory system not available)")
        return

    data = {
        "id": "test-id",
        "timestamp": "2025-11-15T00:00:00",
        "memory_type": "fact",
        "content": "Test content",
        "importance": 0.7,
        "tags": ["test"]
    }

    mem = Memory.from_dict(data)

    assert mem.id == "test-id"
    assert mem.content == "Test content"
    assert mem.importance == 0.7


# MemoryEmbeddings Tests

def test_embeddings_encode():
    """Test encoding single text."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_embeddings_encode (memory system not available)")
        return

    embeddings = MemoryEmbeddings()

    embedding = embeddings.encode("Test text")

    assert embedding is not None
    assert len(embedding) == embeddings.dimension


def test_embeddings_encode_batch():
    """Test encoding multiple texts."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_embeddings_encode_batch (memory system not available)")
        return

    embeddings = MemoryEmbeddings()

    texts = ["Text 1", "Text 2", "Text 3"]
    embeddings_array = embeddings.encode_batch(texts)

    assert embeddings_array.shape == (3, embeddings.dimension)


def test_embeddings_similarity():
    """Test similarity calculation."""
    if not MEMORY_AVAILABLE:
        print("⏭️  test_embeddings_similarity (memory system not available)")
        return

    embeddings = MemoryEmbeddings()

    emb1 = embeddings.encode("Python programming")
    emb2 = embeddings.encode("Python programming")  # Identical
    emb3 = embeddings.encode("Java programming")  # Similar

    sim_identical = embeddings.similarity(emb1, emb2)
    sim_similar = embeddings.similarity(emb1, emb3)

    assert 0.0 <= sim_identical <= 1.0
    assert 0.0 <= sim_similar <= 1.0
    assert sim_identical >= sim_similar  # Identical should be more similar


def run_all_tests():
    """Run all tests and report results."""
    tests = [
        test_store_memory_basic,
        test_store_memory_with_metadata,
        test_store_invalid_memory_type,
        test_store_invalid_importance,
        test_retrieve_relevant_memories,
        test_retrieve_by_type,
        test_retrieve_by_importance,
        test_retrieve_empty,
        test_get_memory_by_id,
        test_get_nonexistent_memory,
        test_update_memory,
        test_update_nonexistent_memory,
        test_delete_memory,
        test_delete_nonexistent_memory,
        test_consolidate_similar_memories,
        test_consolidate_no_duplicates,
        test_decay_memories,
        test_decay_preserves_accessed,
        test_access_count_increments,
        test_last_accessed_updates,
        test_get_memory_stats,
        test_stats_empty_memory,
        test_export_json,
        test_export_csv,
        test_export_invalid_format,
        test_import_json,
        test_import_nonexistent_file,
        test_save_and_load,
        test_max_memories_limit,
        test_empty_content,
        test_large_content,
        test_memory_dataclass,
        test_memory_to_dict,
        test_memory_from_dict,
        test_embeddings_encode,
        test_embeddings_encode_batch,
        test_embeddings_similarity,
    ]

    print(f"Running {len(tests)} tests...\n")

    passed = 0
    failed = 0
    skipped = 0

    for test in tests:
        try:
            test()
            print(f"✅ {test.__name__}")
            passed += 1
        except AssertionError as e:
            print(f"❌ {test.__name__}: {e}")
            failed += 1
        except Exception as e:
            if "not available" in str(e):
                skipped += 1
            else:
                print(f"❌ {test.__name__}: {type(e).__name__}: {e}")
                failed += 1

    print(f"\n{'='*60}")
    print(f"Results: {passed} passed, {failed} failed, {skipped} skipped out of {len(tests)} tests")
    if passed > 0 and failed == 0:
        print(f"Success rate: 100%")
    elif passed > 0:
        print(f"Success rate: {passed/(passed+failed)*100:.1f}% (of non-skipped)")

    if failed == 0:
        print("✅ All tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == "__main__":
    if not MEMORY_AVAILABLE:
        print("⚠️  Memory system not available.")
        print("Install dependencies: pip install sentence-transformers faiss-cpu")
        print("Tests will be skipped.")
        exit(0)

    exit(run_all_tests())
