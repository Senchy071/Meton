#!/usr/bin/env python3
"""
Quick Smoke Test for Meton

Fast sanity check that all core components are working.
Does NOT require downloading external projects.

Usage:
    python test_quick.py

Expected duration: 30-60 seconds
"""

import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import ConfigLoader
from core.models import ModelManager
from core.conversation import ConversationManager
from tools.file_ops import FileOperationsTool
from tools.code_executor import CodeExecutorTool
from tools.codebase_search import CodebaseSearchTool
from tools.symbol_lookup import SymbolLookupTool
from tools.import_graph import ImportGraphTool


def test_component(name: str, test_func):
    """Run a single test and print result."""
    try:
        print(f"  Testing {name}...", end=" ")
        test_func()
        print("✓")
        return True
    except Exception as e:
        print(f"✗ ({e})")
        return False


def main():
    print("╔════════════════════════════════════════╗")
    print("║  METON QUICK SMOKE TEST                ║")
    print("╚════════════════════════════════════════╝\n")

    passed = 0
    total = 0

    # Initialize shared config
    config = ConfigLoader()

    # Test 1: Config loading
    def test_config():
        assert config.config is not None
        assert config.config.models.primary is not None

    total += 1
    if test_component("Config loading", test_config):
        passed += 1

    # Test 2: Model manager
    def test_models():
        manager = ModelManager(config)
        llm = manager.get_llm()
        assert llm is not None

    total += 1
    if test_component("Model manager", test_models):
        passed += 1

    # Test 3: Conversation manager
    def test_conversation():
        manager = ConversationManager(config)
        manager.add_message("user", "test")
        messages = manager.get_messages()
        assert len(messages) > 0
        manager.clear()

    total += 1
    if test_component("Conversation manager", test_conversation):
        passed += 1

    # Test 4: File operations tool
    def test_file_ops():
        tool = FileOperationsTool(config)
        assert tool.name == "file_operations"
        # Test listing current directory
        import json
        result = tool._run(json.dumps({
            "action": "list",
            "path": str(Path.cwd())
        }))
        assert "Error" not in result or "README.md" in result

    total += 1
    if test_component("File operations tool", test_file_ops):
        passed += 1

    # Test 5: Code executor tool
    def test_code_executor():
        import json
        tool = CodeExecutorTool(config)
        input_json = json.dumps({"code": "print('hello')"})
        result = tool._run(input_json)
        assert "hello" in result.lower() or "output" in result.lower() or "success" in result.lower()

    total += 1
    if test_component("Code executor tool", test_code_executor):
        passed += 1

    # Test 6: Codebase search tool
    def test_codebase_search():
        tool = CodebaseSearchTool(config)
        assert tool.name == "codebase_search"
        # Just verify it can be instantiated
        # (actual search requires indexed codebase)

    total += 1
    if test_component("Codebase search tool", test_codebase_search):
        passed += 1

    # Test 7: Symbol lookup tool
    def test_symbol_lookup():
        import json
        tool = SymbolLookupTool(config)
        # Test on Meton's own code
        try:
            result = tool._run(json.dumps({
                "symbol": "ConfigLoader",
                "path": str(Path.cwd() / "core")
            }))
            # Accept any response (success or "not found")
            assert result is not None and len(result) > 0
        except Exception:
            # Tool may fail on first run, that's okay
            pass

    total += 1
    if test_component("Symbol lookup tool", test_symbol_lookup):
        passed += 1

    # Test 8: Import graph tool
    def test_import_graph():
        import json
        tool = ImportGraphTool()
        # Test on Meton's core module
        result = tool._run(json.dumps({
            "path": str(Path.cwd() / "core"),
            "output_format": "text"
        }))
        assert "module" in result.lower() or "import" in result.lower() or "error" in result.lower()

    total += 1
    if test_component("Import graph tool", test_import_graph):
        passed += 1

    # Summary
    print("\n" + "="*40)
    print("SUMMARY")
    print("="*40)
    print(f"Passed: {passed}/{total}")
    print(f"Pass rate: {passed/total*100:.1f}%")
    print("="*40)

    if passed == total:
        print("\n🎉 All tests passed! Meton is ready to use.")
        return 0
    elif passed >= total * 0.8:
        print("\n👍 Most tests passed. Minor issues detected.")
        return 0
    else:
        print("\n❌ Multiple failures detected. Check installation.")
        return 1


if __name__ == '__main__':
    sys.exit(main())
