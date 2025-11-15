#!/usr/bin/env python3
"""Test end-to-end RAG integration."""

import sys
sys.path.insert(0, '/media/development/projects/meton')

from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.metadata_store import MetadataStore
import shutil
from pathlib import Path


def main():
    print("=" * 80)
    print("TEST 4: End-to-End Integration")
    print("=" * 80)

    # Create test directory
    test_dir = Path("./test_rag")
    test_dir.mkdir(exist_ok=True)

    try:
        # Initialize components
        print("\n1. Initializing RAG components...")
        embedder = EmbeddingModel()
        vector_store = VectorStore()
        meta_store = MetadataStore(str(test_dir / "metadata.json"))
        print("   ✓ All components initialized")

        # Prepare test code samples
        print("\n2. Preparing test code samples...")
        code_samples = [
            ("def authenticate_user(username, password): return True", "authenticate_user", "function"),
            ("class UserModel: pass", "UserModel", "class"),
            ("def get_database_connection(): return db", "get_database_connection", "function"),
            ("def login_handler(request): return authenticate_user(request.user, request.pwd)", "login_handler", "function"),
            ("class DatabaseConnection: pass", "DatabaseConnection", "class"),
        ]
        print(f"   {len(code_samples)} code samples ready")

        # Index all samples
        print("\n3. Indexing code samples...")
        for idx, (code, name, chunk_type) in enumerate(code_samples):
            chunk_id = f"chunk-{idx}"

            # Create embedding
            embedding = embedder.encode(code)

            # Add to vector store
            vector_store.add(embedding, chunk_id)

            # Add metadata
            meta_store.add(chunk_id, {
                "chunk_id": chunk_id,
                "file_path": f"/test/file{idx}.py",
                "chunk_type": chunk_type,
                "name": name,
                "start_line": 1,
                "end_line": 10,
                "code": code,
                "docstring": ""
            })

            print(f"   Indexed: {name} ({chunk_type})")

        print(f"   ✓ Indexed {vector_store.size()} chunks")

        # Test semantic search
        print("\n4. Testing semantic search for 'user login authentication'...")
        query = "user login authentication"
        query_embedding = embedder.encode(query)
        results = vector_store.search(query_embedding, top_k=3)

        print(f"   Found {len(results)} results:")
        for rank, (chunk_id, distance) in enumerate(results, 1):
            metadata = meta_store.get(chunk_id)
            print(f"   {rank}. {metadata['name']} (distance: {distance:.3f})")
            print(f"      Code: {metadata['code'][:50]}...")

        # Verify authenticate_user is in top results
        top_chunk_id = results[0][0]
        top_metadata = meta_store.get(top_chunk_id)
        assert "authenticate" in top_metadata["name"].lower() or "login" in top_metadata["name"].lower()
        print("   ✓ Semantic search works correctly")

        # Test search for database-related code
        print("\n5. Testing semantic search for 'database connection'...")
        query = "database connection"
        query_embedding = embedder.encode(query)
        results = vector_store.search(query_embedding, top_k=3)

        print(f"   Found {len(results)} results:")
        for rank, (chunk_id, distance) in enumerate(results, 1):
            metadata = meta_store.get(chunk_id)
            print(f"   {rank}. {metadata['name']} (distance: {distance:.3f})")

        # Verify database-related chunks are in top results
        top_chunk_id = results[0][0]
        top_metadata = meta_store.get(top_chunk_id)
        assert "database" in top_metadata["name"].lower() or "database" in top_metadata["code"].lower()
        print("   ✓ Database search works correctly")

        # Test filtering by chunk type
        print("\n6. Testing metadata filtering by chunk type...")
        all_functions = meta_store.search_by_field("chunk_type", "function")
        all_classes = meta_store.search_by_field("chunk_type", "class")
        print(f"   Functions: {len(all_functions)}")
        print(f"   Classes: {len(all_classes)}")
        assert len(all_functions) == 3
        assert len(all_classes) == 2
        print("   ✓ Filtering works correctly")

        # Test persistence
        print("\n7. Testing persistence (save and reload)...")
        vector_store.save(str(test_dir / "faiss.index"))
        meta_store.save()
        print("   Saved all components")

        # Create new instances and load
        new_vector_store = VectorStore()
        new_meta_store = MetadataStore(str(test_dir / "metadata.json"))

        new_vector_store.load(str(test_dir / "faiss.index"))
        new_meta_store.load()

        print(f"   Loaded vector store: {new_vector_store.size()} vectors")
        print(f"   Loaded metadata store: {new_meta_store.size()} chunks")

        # Verify search still works
        query = "authenticate user"
        query_embedding = embedder.encode(query)
        results = new_vector_store.search(query_embedding, top_k=2)

        print(f"   Search results after reload: {len(results)}")
        for chunk_id, distance in results:
            metadata = new_meta_store.get(chunk_id)
            print(f"     - {metadata['name']} (distance: {distance:.3f})")

        assert len(results) > 0
        print("   ✓ Persistence works correctly")

        # Test combined workflow: search + filter
        print("\n8. Testing combined workflow (search + filter)...")
        query = "user authentication"
        query_embedding = embedder.encode(query)
        results = vector_store.search(query_embedding, top_k=10)

        # Filter to only functions
        function_results = []
        for chunk_id, distance in results:
            metadata = meta_store.get(chunk_id)
            if metadata["chunk_type"] == "function":
                function_results.append((chunk_id, distance, metadata))

        print(f"   Found {len(function_results)} function results:")
        for chunk_id, distance, metadata in function_results:
            print(f"     - {metadata['name']} (distance: {distance:.3f})")

        assert len(function_results) > 0
        print("   ✓ Combined workflow works correctly")

        print("\n" + "=" * 80)
        print("✅ ALL INTEGRATION TESTS PASSED")
        print("=" * 80)

        # Summary
        print("\n" + "=" * 80)
        print("TASK 13 COMPLETE - RAG INFRASTRUCTURE READY")
        print("=" * 80)
        print("\nSummary:")
        print(f"  • Embedding model: {embedder.model_name}")
        print(f"  • Vector dimension: {embedder.get_dimension()}")
        print(f"  • Indexed chunks: {vector_store.size()}")
        print(f"  • Metadata entries: {meta_store.size()}")
        print(f"  • All components tested and working")
        print("\nComponents are ready for codebase indexing (Task 14)")
        print("=" * 80)

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("\nCleaned up test directory")


if __name__ == "__main__":
    main()
