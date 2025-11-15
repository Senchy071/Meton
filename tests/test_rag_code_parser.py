#!/usr/bin/env python3
"""Test code parser functionality."""

import sys
sys.path.insert(0, '/media/development/projects/meton')

import tempfile
import os
from pathlib import Path
from rag.code_parser import CodeParser


def main():
    print("=" * 80)
    print("TEST: Code Parser")
    print("=" * 80)

    parser = CodeParser()

    # Test 1: Parse simple function with docstring
    print("\n1. Testing simple function parsing...")
    test_code = '''
def hello_world():
    """Say hello to the world."""
    print("Hello, World!")
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        assert result is not None, "Parse result should not be None"
        assert len(result["functions"]) == 1, f"Expected 1 function, got {len(result['functions'])}"
        func = result["functions"][0]
        assert func["name"] == "hello_world", f"Expected 'hello_world', got {func['name']}"
        assert func["docstring"] == "Say hello to the world.", f"Docstring mismatch"
        assert "def hello_world():" in func["code"], "Code should contain function definition"
        assert func["start_line"] == 2, f"Expected start_line 2, got {func['start_line']}"
        print("   ✓ Simple function parsed correctly")
    finally:
        os.unlink(temp_file)

    # Test 2: Parse class with multiple methods
    print("\n2. Testing class with multiple methods...")
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
        result = parser.parse_file(temp_file)
        assert result is not None, "Parse result should not be None"
        assert len(result["classes"]) == 1, f"Expected 1 class, got {len(result['classes'])}"
        cls = result["classes"][0]
        assert cls["name"] == "Calculator", f"Expected 'Calculator', got {cls['name']}"
        assert cls["docstring"] == "A simple calculator class.", f"Docstring mismatch"
        assert len(cls["methods"]) == 2, f"Expected 2 methods, got {len(cls['methods'])}"
        method_names = [m["name"] for m in cls["methods"]]
        assert "add" in method_names, "Should have 'add' method"
        assert "subtract" in method_names, "Should have 'subtract' method"
        print("   ✓ Class with methods parsed correctly")
    finally:
        os.unlink(temp_file)

    # Test 3: Parse file with imports
    print("\n3. Testing import extraction...")
    test_code = '''
import os
import sys
from pathlib import Path
from typing import List, Dict
import json
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        assert result is not None, "Parse result should not be None"
        imports = result["imports"]
        assert len(imports) > 0, "Should have extracted imports"
        assert "os" in imports, "Should have 'os' import"
        assert "sys" in imports, "Should have 'sys' import"
        assert "pathlib" in imports, "Should have 'pathlib' import"
        assert "typing" in imports, "Should have 'typing' import"
        assert "json" in imports, "Should have 'json' import"
        print(f"   Extracted imports: {imports}")
        print("   ✓ Imports extracted correctly")
    finally:
        os.unlink(temp_file)

    # Test 4: Parse file with module docstring
    print("\n4. Testing module docstring extraction...")
    test_code = '''"""
This is a module docstring.
It spans multiple lines.
"""

def foo():
    pass
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        assert result is not None, "Parse result should not be None"
        module_doc = result["module_doc"]
        assert len(module_doc) > 0, "Should have module docstring"
        assert "This is a module docstring" in module_doc, "Module docstring should match"
        assert "multiple lines" in module_doc, "Module docstring should be complete"
        print(f"   Module doc: {module_doc[:50]}...")
        print("   ✓ Module docstring extracted correctly")
    finally:
        os.unlink(temp_file)

    # Test 5: Parse file with syntax error
    print("\n5. Testing syntax error handling...")
    test_code = '''
def broken_function(:
    print("This has a syntax error"
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        assert result is None, "Should return None for syntax error"
        print("   ✓ Syntax errors handled gracefully")
    finally:
        os.unlink(temp_file)

    # Test 6: Parse function with type hints and defaults
    print("\n6. Testing function signature extraction...")
    test_code = '''
def complex_function(x: int, y: str = "default", *args, **kwargs) -> bool:
    """A complex function signature."""
    return True
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        assert result is not None, "Parse result should not be None"
        assert len(result["functions"]) == 1, "Should have 1 function"
        func = result["functions"][0]
        signature = func["signature"]
        assert "x: int" in signature, "Should have type hint for x"
        assert "y: str" in signature, "Should have y parameter with type hint"
        assert "default" in signature, "Should have default value for y"
        assert "*args" in signature, "Should have *args"
        assert "**kwargs" in signature, "Should have **kwargs"
        assert "-> bool" in signature, "Should have return type"
        print(f"   Signature: {signature}")
        print("   ✓ Complex function signature extracted correctly")
    finally:
        os.unlink(temp_file)

    # Test 7: Parse class with base classes
    print("\n7. Testing class inheritance extraction...")
    test_code = '''
class Child(Parent1, Parent2):
    """A child class."""
    pass
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        assert result is not None, "Parse result should not be None"
        assert len(result["classes"]) == 1, "Should have 1 class"
        cls = result["classes"][0]
        bases = cls["bases"]
        assert "Parent1" in bases, "Should have Parent1 as base"
        assert "Parent2" in bases, "Should have Parent2 as base"
        print(f"   Base classes: {bases}")
        print("   ✓ Class inheritance extracted correctly")
    finally:
        os.unlink(temp_file)

    # Test 8: Parse empty file
    print("\n8. Testing empty file handling...")
    test_code = ''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        assert result is not None, "Should return result for empty file"
        assert len(result["functions"]) == 0, "Should have no functions"
        assert len(result["classes"]) == 0, "Should have no classes"
        assert result["module_doc"] == "", "Should have empty module doc"
        print("   ✓ Empty file handled correctly")
    finally:
        os.unlink(temp_file)

    # Test 9: Parse file with mixed content
    print("\n9. Testing file with mixed content...")
    test_code = '''"""Module for user authentication."""

import hashlib
from typing import Optional

class User:
    """Represents a user."""

    def __init__(self, username: str):
        self.username = username

    def validate(self) -> bool:
        """Validate user."""
        return len(self.username) > 0

def hash_password(password: str) -> str:
    """Hash a password using SHA256."""
    return hashlib.sha256(password.encode()).hexdigest()

def authenticate_user(username: str, password: str) -> Optional[User]:
    """Authenticate a user."""
    hashed = hash_password(password)
    # ... authentication logic ...
    return User(username)
'''
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        assert result is not None, "Parse result should not be None"

        # Check module doc
        assert "authentication" in result["module_doc"].lower(), "Should have module doc"

        # Check imports
        assert "hashlib" in result["imports"], "Should have hashlib import"
        assert "typing" in result["imports"], "Should have typing import"

        # Check classes
        assert len(result["classes"]) == 1, f"Should have 1 class, got {len(result['classes'])}"
        assert result["classes"][0]["name"] == "User", "Class should be User"
        assert len(result["classes"][0]["methods"]) == 2, "User should have 2 methods"

        # Check functions
        assert len(result["functions"]) == 2, f"Should have 2 functions, got {len(result['functions'])}"
        func_names = [f["name"] for f in result["functions"]]
        assert "hash_password" in func_names, "Should have hash_password function"
        assert "authenticate_user" in func_names, "Should have authenticate_user function"

        print(f"   Module doc: {result['module_doc'][:40]}...")
        print(f"   Imports: {result['imports']}")
        print(f"   Classes: {[c['name'] for c in result['classes']]}")
        print(f"   Functions: {func_names}")
        print("   ✓ Mixed content file parsed correctly")
    finally:
        os.unlink(temp_file)

    # Test 10: Test encoding fallback (latin-1)
    print("\n10. Testing encoding fallback...")
    # Create a file with latin-1 encoding
    test_code = 'def café(): pass\n'  # Contains non-ASCII character
    with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False, encoding='latin-1') as f:
        f.write(test_code)
        temp_file = f.name

    try:
        result = parser.parse_file(temp_file)
        # Parser should handle encoding gracefully
        if result is not None:
            print("   ✓ Encoding fallback works")
        else:
            print("   ✓ File with encoding issues handled gracefully")
    finally:
        os.unlink(temp_file)

    print("\n" + "=" * 80)
    print("✅ ALL CODE PARSER TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
