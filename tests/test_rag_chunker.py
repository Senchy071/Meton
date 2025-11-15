#!/usr/bin/env python3
"""Test code chunker functionality."""

import sys
sys.path.insert(0, '/media/development/projects/meton')

import tempfile
import os
from rag.code_parser import CodeParser
from rag.chunker import CodeChunker


def main():
    print("=" * 80)
    print("TEST: Code Chunker")
    print("=" * 80)

    parser = CodeParser()
    chunker = CodeChunker()

    # Test 1: Create chunks from simple function
    print("\n1. Testing function chunk creation...")
    test_code = '''
def hello_world():
    """Say hello to the world."""
    print("Hello, World!")
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)

        # Should have 1 function chunk (no module doc, no imports)
        assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
        chunk = chunks[0]

        assert chunk["chunk_type"] == "function", f"Expected 'function', got {chunk['chunk_type']}"
        assert chunk["name"] == "hello_world", f"Expected 'hello_world', got {chunk['name']}"
        assert chunk["docstring"] == "Say hello to the world."
        assert "chunk_id" in chunk, "Should have chunk_id"
        assert "file_path" in chunk, "Should have file_path"
        assert chunk["start_line"] == 2
        assert "def hello_world():" in chunk["code"]
        print(f"   Chunk ID: {chunk['chunk_id']}")
        print(f"   Chunk type: {chunk['chunk_type']}")
        print(f"   Name: {chunk['name']}")
        print("   ✓ Function chunk created correctly")
    finally:
        os.unlink(temp_file)

    # Test 2: Create chunks from class
    print("\n2. Testing class chunk creation...")
    test_code = '''
class Calculator:
    """A simple calculator class."""

    def add(self, a, b):
        """Add two numbers."""
        return a + b

    def subtract(self, a, b):
        """Subtract two numbers."""
        return a - b
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)

        # Should have 1 class chunk (includes all methods)
        assert len(chunks) == 1, f"Expected 1 chunk, got {len(chunks)}"
        chunk = chunks[0]

        assert chunk["chunk_type"] == "class", f"Expected 'class', got {chunk['chunk_type']}"
        assert chunk["name"] == "Calculator", f"Expected 'Calculator', got {chunk['name']}"
        assert chunk["docstring"] == "A simple calculator class."
        assert "methods" in chunk, "Should have methods list"
        assert len(chunk["methods"]) == 2, f"Expected 2 methods, got {len(chunk['methods'])}"
        assert "add" in chunk["methods"], "Should have 'add' method"
        assert "subtract" in chunk["methods"], "Should have 'subtract' method"
        print(f"   Chunk type: {chunk['chunk_type']}")
        print(f"   Name: {chunk['name']}")
        print(f"   Methods: {chunk['methods']}")
        print("   ✓ Class chunk created correctly")
    finally:
        os.unlink(temp_file)

    # Test 3: Create module docstring chunk
    print("\n3. Testing module docstring chunk...")
    test_code = '''"""
This is a module docstring.
It describes what the module does.
"""

def foo():
    pass
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)

        # Should have 2 chunks: module doc + function
        assert len(chunks) == 2, f"Expected 2 chunks, got {len(chunks)}"

        # Find module chunk
        module_chunk = [c for c in chunks if c["chunk_type"] == "module"][0]
        assert module_chunk is not None, "Should have module chunk"
        assert "This is a module docstring" in module_chunk["docstring"]
        assert module_chunk["start_line"] == 1
        print(f"   Module chunk created: {module_chunk['name']}")
        print(f"   Docstring: {module_chunk['docstring'][:40]}...")
        print("   ✓ Module docstring chunk created correctly")
    finally:
        os.unlink(temp_file)

    # Test 4: Create imports chunk
    print("\n4. Testing imports chunk...")
    test_code = '''
import os
import sys
from pathlib import Path

def foo():
    pass
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)

        # Should have 2 chunks: imports + function
        assert len(chunks) >= 2, f"Expected at least 2 chunks, got {len(chunks)}"

        # Find imports chunk
        imports_chunk = [c for c in chunks if c["chunk_type"] == "imports"][0]
        assert imports_chunk is not None, "Should have imports chunk"
        assert len(imports_chunk["imports"]) > 0, "Should have imports list"
        assert "os" in imports_chunk["imports"], "Should have 'os' import"
        assert "sys" in imports_chunk["imports"], "Should have 'sys' import"
        assert "pathlib" in imports_chunk["imports"], "Should have 'pathlib' import"
        print(f"   Imports: {imports_chunk['imports']}")
        print("   ✓ Imports chunk created correctly")
    finally:
        os.unlink(temp_file)

    # Test 5: Create chunks from mixed content
    print("\n5. Testing mixed content chunking...")
    test_code = '''"""Module for user authentication."""

import hashlib
from typing import Optional

class User:
    """Represents a user."""

    def __init__(self, username: str):
        self.username = username

def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    return User(username)
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)

        # Should have: module doc + imports + 1 class + 2 functions = 5 chunks
        assert len(chunks) == 5, f"Expected 5 chunks, got {len(chunks)}"

        chunk_types = [c["chunk_type"] for c in chunks]
        assert "module" in chunk_types, "Should have module chunk"
        assert "imports" in chunk_types, "Should have imports chunk"
        assert "class" in chunk_types, "Should have class chunk"
        assert chunk_types.count("function") == 2, "Should have 2 function chunks"

        print(f"   Total chunks: {len(chunks)}")
        print(f"   Chunk types: {chunk_types}")
        print("   ✓ Mixed content chunked correctly")
    finally:
        os.unlink(temp_file)

    # Test 6: Test get_chunk_text() method
    print("\n6. Testing chunk text generation...")
    test_code = '''
def greet(name: str) -> str:
    """Greet a person by name."""
    return f"Hello, {name}!"
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)
        chunk = chunks[0]

        # Get text representation
        text = chunker.get_chunk_text(chunk)
        assert len(text) > 0, "Chunk text should not be empty"
        assert "function: greet" in text, "Should contain chunk type and name"
        assert "Greet a person by name" in text, "Should contain docstring"
        assert "def greet" in text, "Should contain code"
        print(f"   Text length: {len(text)} chars")
        print(f"   Text preview: {text[:100]}...")
        print("   ✓ Chunk text generated correctly")
    finally:
        os.unlink(temp_file)

    # Test 7: Test get_chunk_summary() method
    print("\n7. Testing chunk summary generation...")
    test_code = '''
def example():
    """Example function."""
    pass
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)
        chunk = chunks[0]

        # Get summary
        summary = chunker.get_chunk_summary(chunk)
        assert len(summary) > 0, "Summary should not be empty"
        assert "function" in summary, "Summary should contain chunk type"
        assert "example" in summary, "Summary should contain name"
        assert ".py" in summary, "Summary should contain filename"
        print(f"   Summary: {summary}")
        print("   ✓ Chunk summary generated correctly")
    finally:
        os.unlink(temp_file)

    # Test 8: Test empty file (no chunks)
    print("\n8. Testing empty file...")
    test_code = ''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)
        assert len(chunks) == 0, f"Expected 0 chunks from empty file, got {len(chunks)}"
        print("   ✓ Empty file handled correctly")
    finally:
        os.unlink(temp_file)

    # Test 9: Test chunk uniqueness (each chunk should have unique ID)
    print("\n9. Testing chunk ID uniqueness...")
    test_code = '''
def func1():
    pass

def func2():
    pass

def func3():
    pass
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)

        chunk_ids = [c["chunk_id"] for c in chunks]
        assert len(chunk_ids) == len(set(chunk_ids)), "All chunk IDs should be unique"
        print(f"   Created {len(chunk_ids)} chunks with unique IDs")
        print("   ✓ Chunk IDs are unique")
    finally:
        os.unlink(temp_file)

    # Test 10: Test chunk metadata completeness
    print("\n10. Testing chunk metadata completeness...")
    test_code = '''
def complete_test():
    """Test function."""
    pass
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        parsed_data = parser.parse_file(temp_file)
        chunks = chunker.create_chunks(parsed_data, temp_file)
        chunk = chunks[0]

        # Check required fields
        required_fields = ["chunk_id", "file_path", "chunk_type", "name",
                          "start_line", "end_line", "code", "docstring", "imports"]
        for field in required_fields:
            assert field in chunk, f"Missing required field: {field}"

        print(f"   All required fields present: {required_fields}")
        print("   ✓ Chunk metadata is complete")
    finally:
        os.unlink(temp_file)

    print("\n" + "=" * 80)
    print("✅ ALL CODE CHUNKER TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
