#!/usr/bin/env python3
"""Test codebase indexer functionality."""

import sys
sys.path.insert(0, '/media/development/projects/meton')

import tempfile
import os
import shutil
from pathlib import Path
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.metadata_store import MetadataStore
from rag.indexer import CodebaseIndexer


def main():
    print("=" * 80)
    print("TEST: Codebase Indexer")
    print("=" * 80)

    # Initialize components
    embedder = EmbeddingModel()
    vector_store = VectorStore(dimension=embedder.get_dimension())

    # Create temporary metadata file
    temp_metadata_file = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_metadata_file.close()
    metadata_store = MetadataStore(temp_metadata_file.name)

    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=True)

    # Test 1: Index single file
    print("\n1. Testing single file indexing...")
    test_code = '''
def hello_world():
    """Say hello to the world."""
    print("Hello, World!")

def goodbye_world():
    """Say goodbye to the world."""
    print("Goodbye, World!")
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        num_chunks = indexer.index_file(temp_file)
        assert num_chunks == 2, f"Expected 2 chunks, got {num_chunks}"
        assert vector_store.size() == 2, f"Expected 2 vectors, got {vector_store.size()}"
        assert metadata_store.size() == 2, f"Expected 2 metadata entries, got {metadata_store.size()}"
        print(f"   Indexed {num_chunks} chunks")
        print("   ✓ Single file indexed correctly")
    finally:
        os.unlink(temp_file)

    # Test 2: Index file with syntax error
    print("\n2. Testing syntax error handling...")
    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store.clear()
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    test_code = '''
def broken_function(:
    print("This has a syntax error"
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        num_chunks = indexer.index_file(temp_file)
        assert num_chunks == 0, f"Expected 0 chunks from syntax error, got {num_chunks}"
        stats = indexer.get_stats()
        assert stats["files_failed"] == 1, "Should have 1 failed file"
        assert len(stats["errors"]) == 1, "Should have 1 error recorded"
        print(f"   Syntax error handled: {stats['errors'][0]['error']}")
        print("   ✓ Syntax errors handled gracefully")
    finally:
        os.unlink(temp_file)

    # Test 3: Index directory (single level)
    print("\n3. Testing directory indexing (non-recursive)...")
    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store.clear()
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    # Create temporary directory with Python files
    temp_dir = tempfile.mkdtemp()
    try:
        # Create file 1
        with open(os.path.join(temp_dir, "file1.py"), "w") as f:
            f.write("def func1(): pass\n")

        # Create file 2
        with open(os.path.join(temp_dir, "file2.py"), "w") as f:
            f.write("def func2(): pass\n")

        # Create file 3
        with open(os.path.join(temp_dir, "file3.py"), "w") as f:
            f.write("def func3(): pass\n")

        # Index directory (non-recursive)
        stats = indexer.index_directory(temp_dir, recursive=False)

        assert stats["files_processed"] == 3, f"Expected 3 files, got {stats['files_processed']}"
        assert stats["chunks_created"] == 3, f"Expected 3 chunks, got {stats['chunks_created']}"
        assert stats["files_failed"] == 0, f"Expected 0 failures, got {stats['files_failed']}"
        print(f"   Files processed: {stats['files_processed']}")
        print(f"   Chunks created: {stats['chunks_created']}")
        print("   ✓ Directory indexed correctly")
    finally:
        shutil.rmtree(temp_dir)

    # Test 4: Index directory recursively
    print("\n4. Testing recursive directory indexing...")
    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store.clear()
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    temp_dir = tempfile.mkdtemp()
    try:
        # Create root level file
        with open(os.path.join(temp_dir, "root.py"), "w") as f:
            f.write("def root_func(): pass\n")

        # Create subdirectory
        sub_dir = os.path.join(temp_dir, "subdir")
        os.makedirs(sub_dir)

        # Create file in subdirectory
        with open(os.path.join(sub_dir, "sub.py"), "w") as f:
            f.write("def sub_func(): pass\n")

        # Create nested subdirectory
        nested_dir = os.path.join(sub_dir, "nested")
        os.makedirs(nested_dir)

        # Create file in nested directory
        with open(os.path.join(nested_dir, "nested.py"), "w") as f:
            f.write("def nested_func(): pass\n")

        # Index directory recursively
        stats = indexer.index_directory(temp_dir, recursive=True)

        assert stats["files_processed"] == 3, f"Expected 3 files, got {stats['files_processed']}"
        assert stats["chunks_created"] == 3, f"Expected 3 chunks, got {stats['chunks_created']}"
        print(f"   Files processed (recursive): {stats['files_processed']}")
        print(f"   Chunks created: {stats['chunks_created']}")
        print("   ✓ Recursive indexing works correctly")
    finally:
        shutil.rmtree(temp_dir)

    # Test 5: Skip excluded directories
    print("\n5. Testing exclusion of __pycache__ and venv...")
    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store.clear()
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    temp_dir = tempfile.mkdtemp()
    try:
        # Create normal file
        with open(os.path.join(temp_dir, "normal.py"), "w") as f:
            f.write("def normal_func(): pass\n")

        # Create __pycache__ directory with file
        pycache_dir = os.path.join(temp_dir, "__pycache__")
        os.makedirs(pycache_dir)
        with open(os.path.join(pycache_dir, "cached.py"), "w") as f:
            f.write("def cached_func(): pass\n")

        # Create venv directory with file
        venv_dir = os.path.join(temp_dir, "venv")
        os.makedirs(venv_dir)
        with open(os.path.join(venv_dir, "venv.py"), "w") as f:
            f.write("def venv_func(): pass\n")

        # Index directory
        stats = indexer.index_directory(temp_dir, recursive=True)

        # Should only index the normal file, skip __pycache__ and venv
        assert stats["files_processed"] == 1, f"Expected 1 file, got {stats['files_processed']}"
        assert stats["chunks_created"] == 1, f"Expected 1 chunk, got {stats['chunks_created']}"
        print(f"   Files processed: {stats['files_processed']} (excluded __pycache__ and venv)")
        print("   ✓ Excluded directories skipped correctly")
    finally:
        shutil.rmtree(temp_dir)

    # Test 6: Skip empty __init__.py files
    print("\n6. Testing empty __init__.py file handling...")
    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store.clear()
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    temp_dir = tempfile.mkdtemp()
    try:
        # Create normal file
        with open(os.path.join(temp_dir, "module.py"), "w") as f:
            f.write("def module_func(): pass\n")

        # Create empty __init__.py
        with open(os.path.join(temp_dir, "__init__.py"), "w") as f:
            pass  # Empty file

        # Index directory
        stats = indexer.index_directory(temp_dir, recursive=False)

        # Should only index the module file, skip empty __init__.py
        assert stats["files_processed"] == 1, f"Expected 1 file, got {stats['files_processed']}"
        print(f"   Files processed: {stats['files_processed']} (skipped empty __init__.py)")
        print("   ✓ Empty __init__.py files skipped correctly")
    finally:
        shutil.rmtree(temp_dir)

    # Test 7: Get statistics
    print("\n7. Testing statistics retrieval...")
    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store.clear()
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    temp_dir = tempfile.mkdtemp()
    try:
        # Create files
        with open(os.path.join(temp_dir, "file1.py"), "w") as f:
            f.write("def func1(): pass\n")
        with open(os.path.join(temp_dir, "file2.py"), "w") as f:
            f.write("def func2(): pass\ndef func3(): pass\n")

        # Index directory
        indexer.index_directory(temp_dir, recursive=False)

        # Get stats
        stats = indexer.get_stats()
        assert stats["files_processed"] == 2, f"Expected 2 files"
        assert stats["chunks_created"] == 3, f"Expected 3 chunks"
        assert stats["total_chunks"] == 3, f"Expected 3 total chunks in vector store"
        assert stats["total_metadata"] == 3, f"Expected 3 total metadata entries"
        print(f"   Stats: {stats['files_processed']} files, {stats['chunks_created']} chunks")
        print("   ✓ Statistics retrieved correctly")
    finally:
        shutil.rmtree(temp_dir)

    # Test 8: Save and load index
    print("\n8. Testing save and load...")
    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store.clear()
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    # Create temporary directory for index files
    index_dir = tempfile.mkdtemp()
    vector_store_path = os.path.join(index_dir, "faiss.index")

    try:
        # Create and index a file
        test_code = "def test_func(): pass\n"
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name

        try:
            indexer.index_file(temp_file)
            original_size = vector_store.size()
            assert original_size == 1, "Should have 1 chunk"

            # Save
            indexer.save(vector_store_path)
            assert os.path.exists(vector_store_path), "Vector store file should exist"
            assert os.path.exists(f"{vector_store_path}.mappings"), "Mappings file should exist"

            # Create new stores and indexer for loading
            vector_store = VectorStore(dimension=embedder.get_dimension())
            metadata_store = MetadataStore(temp_metadata_file.name)
            indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)
            assert vector_store.size() == 0, "Vector store should be empty before load"

            indexer.load(vector_store_path)
            assert vector_store.size() == original_size, "Should have reloaded 1 chunk"
            print(f"   Saved and loaded {vector_store.size()} chunks")
            print("   ✓ Save and load work correctly")
        finally:
            os.unlink(temp_file)
    finally:
        shutil.rmtree(index_dir)
        os.unlink(temp_metadata_file.name)

    # Test 9: Search functionality
    print("\n9. Testing search functionality...")
    # Create new stores for this test
    temp_metadata_file2 = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_metadata_file2.close()

    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store = MetadataStore(temp_metadata_file2.name)
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    try:
        test_code = '''
def authenticate_user(username, password):
    """Authenticate a user with username and password."""
    return True

def calculate_fibonacci(n):
    """Calculate fibonacci number."""
    return n
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name

        try:
            indexer.index_file(temp_file)

            # Search for authentication-related code
            results = indexer.search("user authentication", top_k=2)
            assert len(results) > 0, "Should have search results"

            # Results should be list of (metadata, distance) tuples
            metadata, distance = results[0]
            assert "chunk_id" in metadata, "Should have chunk_id in metadata"
            assert "name" in metadata, "Should have name in metadata"
            assert isinstance(distance, float), "Distance should be float"

            print(f"   Search returned {len(results)} results")
            print(f"   Top result: {metadata['name']} (distance: {distance:.4f})")
            print("   ✓ Search works correctly")
        finally:
            os.unlink(temp_file)
    finally:
        os.unlink(temp_metadata_file2.name)

    # Test 10: Mixed content file
    print("\n10. Testing complex file with mixed content...")
    temp_metadata_file3 = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
    temp_metadata_file3.close()

    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store = MetadataStore(temp_metadata_file3.name)
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    try:
        test_code = '''"""User authentication module."""

import hashlib
from typing import Optional

class User:
    """Represents a user."""

    def __init__(self, username: str):
        self.username = username

def hash_password(password: str) -> str:
    """Hash a password."""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate(username: str, password: str) -> bool:
    """Authenticate a user."""
    return True
'''
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(test_code)
            temp_file = f.name

        try:
            num_chunks = indexer.index_file(temp_file)
            # Should have: module doc + imports + class + 2 functions = 5 chunks
            assert num_chunks == 5, f"Expected 5 chunks, got {num_chunks}"

            stats = indexer.get_stats()
            assert stats["chunks_created"] == 5, f"Expected 5 chunks in stats"

            # Verify all chunks are stored
            all_metadata = metadata_store.get_all()
            chunk_types = [m["chunk_type"] for m in all_metadata.values()]
            assert "module" in chunk_types, "Should have module chunk"
            assert "imports" in chunk_types, "Should have imports chunk"
            assert "class" in chunk_types, "Should have class chunk"
            assert chunk_types.count("function") == 2, "Should have 2 function chunks"

            print(f"   Indexed {num_chunks} chunks from complex file")
            print(f"   Chunk types: {chunk_types}")
            print("   ✓ Complex file indexed correctly")
        finally:
            os.unlink(temp_file)
    finally:
        os.unlink(temp_metadata_file3.name)

    print("\n" + "=" * 80)
    print("✅ ALL CODEBASE INDEXER TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
