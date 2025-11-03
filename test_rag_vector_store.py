#!/usr/bin/env python3
"""Test FAISS vector store functionality."""

import sys
sys.path.insert(0, '/media/development/projects/meton')

import numpy as np
from rag.vector_store import VectorStore
import shutil
from pathlib import Path


def main():
    print("=" * 80)
    print("TEST 2: Vector Store")
    print("=" * 80)

    # Create test directory
    test_dir = Path("./test_rag")
    test_dir.mkdir(exist_ok=True)

    try:
        # Initialize store
        print("\n1. Initializing vector store...")
        store = VectorStore(dimension=768)
        print(f"   Dimension: {store.dimension}")
        print(f"   Size: {store.size()}")
        assert store.size() == 0
        print("   ✓ Store initialized")

        # Add single vector
        print("\n2. Adding single vector...")
        v1 = np.random.rand(768).astype('float32')
        store.add(v1, "chunk-1")
        print(f"   Added chunk-1")
        print(f"   Store size: {store.size()}")
        assert store.size() == 1
        print("   ✓ Single add works")

        # Add more vectors
        print("\n3. Adding multiple vectors individually...")
        v2 = np.random.rand(768).astype('float32')
        v3 = np.random.rand(768).astype('float32')
        store.add(v2, "chunk-2")
        store.add(v3, "chunk-3")
        print(f"   Store size: {store.size()}")
        assert store.size() == 3
        print("   ✓ Multiple adds work")

        # Test batch add
        print("\n4. Testing batch add...")
        store2 = VectorStore(dimension=768)
        vectors = np.random.rand(5, 768).astype('float32')
        ids = [f"batch-{i}" for i in range(5)]
        store2.add_batch(vectors, ids)
        print(f"   Added {len(ids)} vectors in batch")
        print(f"   Store size: {store2.size()}")
        assert store2.size() == 5
        print("   ✓ Batch add works")

        # Test search
        print("\n5. Testing search...")
        results = store.search(v1, top_k=2)
        print(f"   Query: chunk-1's vector")
        print(f"   Results: {len(results)}")
        for chunk_id, distance in results:
            print(f"     - {chunk_id}: distance={distance:.6f}")
        assert len(results) == 2
        assert results[0][0] == "chunk-1", "Should find itself first"
        assert results[0][1] < 0.001, "Distance to itself should be near 0"
        print("   ✓ Search works correctly")

        # Test search with top_k > size
        print("\n6. Testing search with top_k > size...")
        results = store.search(v1, top_k=100)
        print(f"   Requested top_k=100, store has {store.size()} vectors")
        print(f"   Got {len(results)} results")
        assert len(results) == store.size()
        print("   ✓ Handles top_k > size correctly")

        # Test save and load
        print("\n7. Testing save and load...")
        save_path = str(test_dir / "faiss.index")
        store.save(save_path)
        print(f"   Saved to {save_path}")
        print(f"   Files created: faiss.index, faiss.index.mappings")

        # Load into new store
        store3 = VectorStore()
        store3.load(save_path)
        print(f"   Loaded from {save_path}")
        print(f"   Loaded size: {store3.size()}")
        assert store3.size() == 3
        print("   ✓ Save and load work")

        # Verify loaded data works
        print("\n8. Verifying loaded data...")
        results = store3.search(v1, top_k=2)
        print(f"   Search results after load: {len(results)}")
        assert results[0][0] == "chunk-1"
        print("   ✓ Loaded data works correctly")

        # Test error handling
        print("\n9. Testing error handling...")

        # Wrong dimension
        try:
            wrong_vec = np.random.rand(512).astype('float32')
            store.add(wrong_vec, "wrong")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"   ✓ Correctly rejected wrong dimension: {e}")

        # Duplicate ID
        try:
            store.add(v1, "chunk-1")
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"   ✓ Correctly rejected duplicate ID: {e}")

        # Mismatched batch sizes
        try:
            store4 = VectorStore(dimension=768)
            vecs = np.random.rand(3, 768).astype('float32')
            ids_wrong = ["a", "b"]  # Only 2 IDs for 3 vectors
            store4.add_batch(vecs, ids_wrong)
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"   ✓ Correctly rejected mismatched batch sizes: {e}")

        print("\n" + "=" * 80)
        print("✅ ALL VECTOR STORE TESTS PASSED")
        print("=" * 80)

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("\nCleaned up test directory")


if __name__ == "__main__":
    main()
