#!/usr/bin/env python3
"""Test script for the new find action in file_operations tool."""

import json
import sys
sys.path.insert(0, '/media/development/projects/meton')

from core.config import Config
from tools.file_ops import FileOperationsTool


def test_find_all_py_files():
    """Test finding all .py files recursively."""
    print("=" * 80)
    print("TEST 1: Find all .py files recursively")
    print("=" * 80)

    config = Config()
    tool = FileOperationsTool(config)

    input_json = json.dumps({
        "action": "find",
        "path": "/media/development/projects/meton",
        "pattern": "*.py",
        "recursive": True
    })

    result = tool._run(input_json)
    print(result)
    print()


def test_find_test_files():
    """Test finding test_*.py files."""
    print("=" * 80)
    print("TEST 2: Find test_*.py files recursively")
    print("=" * 80)

    config = Config()
    tool = FileOperationsTool(config)

    input_json = json.dumps({
        "action": "find",
        "path": "/media/development/projects/meton",
        "pattern": "test_*.py",
        "recursive": True
    })

    result = tool._run(input_json)
    print(result)
    print()


def test_find_non_recursive():
    """Test non-recursive search (only root directory)."""
    print("=" * 80)
    print("TEST 3: Find .py files in root only (non-recursive)")
    print("=" * 80)

    config = Config()
    tool = FileOperationsTool(config)

    input_json = json.dumps({
        "action": "find",
        "path": "/media/development/projects/meton",
        "pattern": "*.py",
        "recursive": False
    })

    result = tool._run(input_json)
    print(result)
    print()


def test_find_md_files():
    """Test finding markdown files."""
    print("=" * 80)
    print("TEST 4: Find all .md files recursively")
    print("=" * 80)

    config = Config()
    tool = FileOperationsTool(config)

    input_json = json.dumps({
        "action": "find",
        "path": "/media/development/projects/meton",
        "pattern": "*.md",
        "recursive": True
    })

    result = tool._run(input_json)
    print(result)
    print()


def test_find_no_matches():
    """Test finding files that don't exist."""
    print("=" * 80)
    print("TEST 5: Find .rs files (should find none)")
    print("=" * 80)

    config = Config()
    tool = FileOperationsTool(config)

    input_json = json.dumps({
        "action": "find",
        "path": "/media/development/projects/meton",
        "pattern": "*.rs",
        "recursive": True
    })

    result = tool._run(input_json)
    print(result)
    print()


if __name__ == "__main__":
    test_find_all_py_files()
    test_find_test_files()
    test_find_non_recursive()
    test_find_md_files()
    test_find_no_matches()

    print("=" * 80)
    print("All tests completed!")
    print("=" * 80)
