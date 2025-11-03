#!/usr/bin/env python3
"""Test metadata store functionality."""

import sys
sys.path.insert(0, '/media/development/projects/meton')

from rag.metadata_store import MetadataStore
import shutil
from pathlib import Path


def main():
    print("=" * 80)
    print("TEST 3: Metadata Store")
    print("=" * 80)

    # Create test directory
    test_dir = Path("./test_rag")
    test_dir.mkdir(exist_ok=True)

    try:
        # Initialize store
        print("\n1. Initializing metadata store...")
        meta = MetadataStore(str(test_dir / "metadata.json"))
        print(f"   Filepath: {meta.filepath}")
        print(f"   Size: {meta.size()}")
        assert meta.size() == 0
        print("   ✓ Store initialized")

        # Add metadata
        print("\n2. Adding metadata...")
        meta.add("chunk-1", {
            "chunk_id": "chunk-1",
            "file_path": "/test/file.py",
            "chunk_type": "function",
            "name": "test_function",
            "start_line": 1,
            "end_line": 10,
            "code": "def test_function():\n    pass",
            "docstring": "Test function"
        })
        print(f"   Added chunk-1")
        print(f"   Store size: {meta.size()}")
        assert meta.size() == 1
        print("   ✓ Add works")

        # Add more metadata
        print("\n3. Adding more metadata...")
        meta.add("chunk-2", {
            "chunk_id": "chunk-2",
            "file_path": "/test/file.py",
            "chunk_type": "class",
            "name": "TestClass",
            "start_line": 12,
            "end_line": 20,
            "code": "class TestClass:\n    pass",
            "docstring": ""
        })
        meta.add("chunk-3", {
            "chunk_id": "chunk-3",
            "file_path": "/test/other.py",
            "chunk_type": "function",
            "name": "another_function",
            "start_line": 1,
            "end_line": 5,
            "code": "def another_function():\n    return 42",
            "docstring": "Returns 42"
        })
        print(f"   Store size: {meta.size()}")
        assert meta.size() == 3
        print("   ✓ Multiple adds work")

        # Test get
        print("\n4. Testing get...")
        data = meta.get("chunk-1")
        print(f"   Retrieved chunk-1")
        print(f"   Name: {data['name']}")
        print(f"   Type: {data['chunk_type']}")
        assert data["name"] == "test_function"
        assert data["chunk_type"] == "function"
        print("   ✓ Get works")

        # Test get non-existent
        print("\n5. Testing get non-existent...")
        result = meta.get("chunk-999")
        print(f"   Result for non-existent chunk: {result}")
        assert result is None
        print("   ✓ Returns None for non-existent chunks")

        # Test get_all
        print("\n6. Testing get_all...")
        all_data = meta.get_all()
        print(f"   Retrieved all metadata: {len(all_data)} chunks")
        assert len(all_data) == 3
        print("   ✓ Get all works")

        # Test search_by_field
        print("\n7. Testing search_by_field...")
        functions = meta.search_by_field("chunk_type", "function")
        print(f"   Found {len(functions)} functions")
        for func in functions:
            print(f"     - {func['name']}")
        assert len(functions) == 2
        assert functions[0]["name"] == "test_function"
        print("   ✓ Search by field works")

        # Test search by file_path
        print("\n8. Testing search by file_path...")
        test_file_chunks = meta.search_by_field("file_path", "/test/file.py")
        print(f"   Found {len(test_file_chunks)} chunks in /test/file.py")
        assert len(test_file_chunks) == 2
        print("   ✓ Search by file_path works")

        # Test save and load
        print("\n9. Testing save and load...")
        meta.save()
        print(f"   Saved to {meta.filepath}")

        # Load into new store
        meta2 = MetadataStore(str(test_dir / "metadata.json"))
        meta2.load()
        print(f"   Loaded from {meta2.filepath}")
        print(f"   Loaded size: {meta2.size()}")
        assert meta2.size() == 3
        print("   ✓ Save and load work")

        # Verify loaded data
        print("\n10. Verifying loaded data...")
        data = meta2.get("chunk-2")
        assert data["name"] == "TestClass"
        assert data["chunk_type"] == "class"
        print("   ✓ Loaded data is correct")

        # Test delete
        print("\n11. Testing delete...")
        result = meta.delete("chunk-2")
        print(f"   Deleted chunk-2: {result}")
        assert result is True
        assert meta.size() == 2
        result = meta.delete("chunk-999")
        print(f"   Tried to delete non-existent chunk: {result}")
        assert result is False
        print("   ✓ Delete works")

        # Test clear
        print("\n12. Testing clear...")
        meta.clear()
        print(f"   Cleared store")
        print(f"   Size after clear: {meta.size()}")
        assert meta.size() == 0
        print("   ✓ Clear works")

        # Test error handling
        print("\n13. Testing error handling...")

        # Missing required field
        try:
            meta3 = MetadataStore(str(test_dir / "test2.json"))
            meta3.add("bad-chunk", {
                "chunk_id": "bad-chunk",
                "file_path": "/test/file.py"
                # Missing other required fields
            })
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"   ✓ Correctly rejected incomplete metadata: {e}")

        # Mismatched chunk_id
        try:
            meta3.add("chunk-1", {
                "chunk_id": "chunk-2",  # Mismatch!
                "file_path": "/test/file.py",
                "chunk_type": "function",
                "name": "test",
                "start_line": 1,
                "end_line": 2,
                "code": "pass",
                "docstring": ""
            })
            assert False, "Should have raised ValueError"
        except ValueError as e:
            print(f"   ✓ Correctly rejected mismatched chunk_id: {e}")

        print("\n" + "=" * 80)
        print("✅ ALL METADATA STORE TESTS PASSED")
        print("=" * 80)

    finally:
        # Cleanup
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("\nCleaned up test directory")


if __name__ == "__main__":
    main()
