#!/usr/bin/env python3
"""Test script for CLI commands.

Tests that CLI commands work correctly:
- /web status
- /web on
- /web off
- /tools (showing status)
"""

import sys
from pathlib import Path
from io import StringIO

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import MetonCLI
from utils.formatting import *


def test_cli_initialization():
    """Test CLI and tool initialization."""
    print_section("Test 1: CLI Initialization")

    try:
        print_thinking("Initializing Meton CLI...")
        cli = MetonCLI()

        # Initialize components
        success = cli.initialize()

        if success:
            print_success("✓ CLI initialized successfully")

            # Verify tools are loaded
            if cli.file_tool and cli.code_tool and cli.web_tool:
                print_success(f"✓ All 3 tools loaded: file_tool, code_tool, web_tool")
                return cli
            else:
                print_error("✗ Tools not loaded properly")
                return None
        else:
            print_error("✗ CLI initialization failed")
            return None

    except Exception as e:
        print_error(f"Initialization failed: {e}")
        import traceback
        traceback.print_exc()
        return None


def test_web_status_disabled(cli: MetonCLI):
    """Test /web status when disabled (default)."""
    print_section("Test 2: Web Status (Default - Disabled)")

    try:
        print_thinking("Checking web search status...")

        # Check directly
        enabled = cli.web_tool.is_enabled()
        console.print(f"  Web search enabled: {enabled}")

        if not enabled:
            print_success("✓ Web search is correctly disabled by default")

            # Show the command works
            print_thinking("Testing /web command...")
            cli.show_web_status()

            return True
        else:
            print_error("✗ Web search should be disabled by default")
            return False

    except Exception as e:
        print_error(f"Web status test failed: {e}")
        return False


def test_web_enable(cli: MetonCLI):
    """Test enabling web search."""
    print_section("Test 3: Enable Web Search")

    try:
        print_thinking("Enabling web search with /web on...")

        # Enable web search
        cli.control_web_search('on')

        # Verify it's enabled
        enabled = cli.web_tool.is_enabled()
        console.print(f"  Web search enabled: {enabled}")

        if enabled:
            print_success("✓ Web search enabled successfully")
            return True
        else:
            print_error("✗ Web search should be enabled")
            return False

    except Exception as e:
        print_error(f"Web enable test failed: {e}")
        return False


def test_web_disable(cli: MetonCLI):
    """Test disabling web search."""
    print_section("Test 4: Disable Web Search")

    try:
        print_thinking("Disabling web search with /web off...")

        # Disable web search
        cli.control_web_search('off')

        # Verify it's disabled
        enabled = cli.web_tool.is_enabled()
        console.print(f"  Web search enabled: {enabled}")

        if not enabled:
            print_success("✓ Web search disabled successfully")
            return True
        else:
            print_error("✗ Web search should be disabled")
            return False

    except Exception as e:
        print_error(f"Web disable test failed: {e}")
        return False


def test_tools_command(cli: MetonCLI):
    """Test /tools command shows correct status."""
    print_section("Test 5: Tools Command with Status")

    try:
        print_thinking("Testing /tools command...")

        # Disable web search first
        cli.web_tool.disable()

        console.print("\nTools list (web_search should be disabled):")
        cli.list_tools()

        # Enable web search
        cli.web_tool.enable()

        console.print("\nTools list (all should be enabled):")
        cli.list_tools()

        print_success("✓ Tools command displays correctly")
        return True

    except Exception as e:
        print_error(f"Tools command test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_web_command_variations(cli: MetonCLI):
    """Test different /web command variations."""
    print_section("Test 6: Web Command Variations")

    try:
        print_thinking("Testing /web command variations...")

        # Test 'enable' alias
        console.print("\n/web enable:")
        cli.control_web_search('enable')
        if not cli.web_tool.is_enabled():
            print_error("✗ 'enable' alias didn't work")
            return False

        # Test 'disable' alias
        console.print("\n/web disable:")
        cli.control_web_search('disable')
        if cli.web_tool.is_enabled():
            print_error("✗ 'disable' alias didn't work")
            return False

        # Test 'status' subcommand
        console.print("\n/web status:")
        cli.control_web_search('status')

        print_success("✓ All web command variations work")
        return True

    except Exception as e:
        print_error(f"Web command variations test failed: {e}")
        return False


def main():
    """Run all CLI command tests."""
    print_header("🧪 CLI Commands Test Suite")
    console.print("[dim]Testing /web and /tools commands[/dim]\n")

    tests_passed = 0
    tests_failed = 0

    # Test 1: Initialize CLI
    cli = test_cli_initialization()
    if cli:
        tests_passed += 1
    else:
        tests_failed += 1
        print_error("\n❌ Cannot continue without CLI initialization")
        return

    console.print()

    # Test 2: Web status (disabled)
    if test_web_status_disabled(cli):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 3: Enable web
    if test_web_enable(cli):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 4: Disable web
    if test_web_disable(cli):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 5: Tools command
    if test_tools_command(cli):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Test 6: Web command variations
    if test_web_command_variations(cli):
        tests_passed += 1
    else:
        tests_failed += 1
    console.print()

    # Summary
    print_header("📊 Test Summary")
    console.print(f"✅ Tests passed: [green]{tests_passed}[/green]")
    console.print(f"❌ Tests failed: [red]{tests_failed}[/red]")
    console.print(f"📈 Success rate: {tests_passed}/{tests_passed + tests_failed} ({100 * tests_passed // (tests_passed + tests_failed)}%)\n")

    if tests_failed == 0:
        console.print("🎉 [bold green]All CLI Command tests passed![/bold green]\n")
    else:
        console.print(f"⚠️  [yellow]{tests_failed} test(s) need attention[/yellow]\n")


if __name__ == "__main__":
    main()
