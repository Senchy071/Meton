#!/usr/bin/env python3
"""Test counting Python files in each subdirectory."""

import json
import sys
sys.path.insert(0, '/media/development/projects/meton')

from core.config import Config
from tools.file_ops import FileOperationsTool


def main():
    config = Config()
    tool = FileOperationsTool(config)

    # First, list all subdirectories
    print("=" * 80)
    print("Step 1: List all items in /media/development/projects/meton")
    print("=" * 80)

    input_json = json.dumps({
        "action": "list",
        "path": "/media/development/projects/meton"
    })

    result = tool._run(input_json)
    print(result)
    print("\n")

    # Now test finding Python files in each known subdirectory
    subdirs = ["core", "tools", "utils", "examples"]

    for subdir in subdirs:
        print("=" * 80)
        print(f"Step 2.{subdirs.index(subdir)+1}: Find Python files in {subdir}/")
        print("=" * 80)

        # Try recursive search in subdirectory
        input_json = json.dumps({
            "action": "find",
            "path": f"/media/development/projects/meton/{subdir}",
            "pattern": "*.py",
            "recursive": True
        })

        result = tool._run(input_json)
        print(result)
        print("\n")

    # Also test non-recursive to see what's in each directory directly
    print("=" * 80)
    print("Step 3: Find Python files directly in core/ (non-recursive)")
    print("=" * 80)

    input_json = json.dumps({
        "action": "find",
        "path": "/media/development/projects/meton/core",
        "pattern": "*.py",
        "recursive": False
    })

    result = tool._run(input_json)
    print(result)
    print("\n")


if __name__ == "__main__":
    main()
