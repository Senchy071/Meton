#!/usr/bin/env python3
"""Test improved parameter validation in file_operations tool."""

import json
import sys
sys.path.insert(0, '/media/development/projects/meton')

from core.config import Config
from tools.file_ops import FileOperationsTool


def test_missing_path_parameter():
    """Test error when 'path' parameter is missing."""
    print("=" * 80)
    print("TEST 1: Missing 'path' parameter (using 'directory' instead)")
    print("=" * 80)

    config = Config()
    tool = FileOperationsTool(config)

    # Simulate the agent's mistake: using 'directory' instead of 'path'
    input_json = json.dumps({
        "action": "find",
        "directory": "/media/development/projects/meton",  # Wrong parameter name
        "pattern": "*.py"
    })

    result = tool._run(input_json)
    print(result)
    print()


def test_empty_path():
    """Test error when 'path' is empty."""
    print("=" * 80)
    print("TEST 2: Empty 'path' parameter")
    print("=" * 80)

    config = Config()
    tool = FileOperationsTool(config)

    input_json = json.dumps({
        "action": "find",
        "path": "",
        "pattern": "*.py"
    })

    result = tool._run(input_json)
    print(result)
    print()


def test_valid_find():
    """Test that valid find still works."""
    print("=" * 80)
    print("TEST 3: Valid find with correct parameters")
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


if __name__ == "__main__":
    test_missing_path_parameter()
    test_empty_path()
    test_valid_find()

    print("=" * 80)
    print("Validation tests completed!")
    print("=" * 80)
