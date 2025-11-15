#!/usr/bin/env python3
"""Test script to verify /web on persists to config.yaml.

This test demonstrates that:
1. /web on updates runtime state
2. /web on updates in-memory config
3. /web on persists to config.yaml file
4. Agent reading config.yaml sees the correct state
"""

import sys
from pathlib import Path
import yaml

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from cli import MetonCLI
from utils.formatting import *


def test_web_persistence():
    """Test that /web on persists to config.yaml."""
    print_header("🧪 Web Search Persistence Test")
    console.print("[dim]Testing /web on command persistence to config.yaml[/dim]\n")

    # Initialize CLI
    print_section("Step 1: Initialize CLI")
    print_thinking("Creating MetonCLI instance...")
    cli = MetonCLI()
    success = cli.initialize()

    if not success:
        print_error("Failed to initialize CLI")
        return False

    print_success("✓ CLI initialized")
    console.print()

    # Check initial state
    print_section("Step 2: Check Initial State")
    print_thinking("Reading config.yaml...")

    with open('config.yaml', 'r') as f:
        data = yaml.safe_load(f)
        initial_state = data['tools']['web_search']['enabled']

    console.print(f"  config.yaml: web_search.enabled = {initial_state}")
    console.print(f"  Runtime: tool.is_enabled() = {cli.web_tool.is_enabled()}")
    console.print(f"  Memory: config.tools.web_search.enabled = {cli.config.config.tools.web_search.enabled}")

    if not initial_state:
        print_success("✓ Initial state is disabled (as expected)")
    console.print()

    # Enable web search
    print_section("Step 3: Enable Web Search")
    print_thinking("Executing /web on command...")
    cli.control_web_search('on')
    console.print()

    # Verify all three states are updated
    print_section("Step 4: Verify State After /web on")
    print_thinking("Checking all three state locations...")

    # Read file again
    with open('config.yaml', 'r') as f:
        data = yaml.safe_load(f)
        file_state = data['tools']['web_search']['enabled']

    runtime_state = cli.web_tool.is_enabled()
    memory_state = cli.config.config.tools.web_search.enabled

    console.print(f"  config.yaml file: {file_state}")
    console.print(f"  Runtime tool state: {runtime_state}")
    console.print(f"  Memory config state: {memory_state}")

    if file_state and runtime_state and memory_state:
        print_success("✓ All three states are ENABLED (synchronized)")
        all_enabled = True
    else:
        print_error(f"✗ States not synchronized: file={file_state}, runtime={runtime_state}, memory={memory_state}")
        all_enabled = False
    console.print()

    # Simulate agent reading config file
    print_section("Step 5: Simulate Agent Reading Config")
    print_thinking("Simulating what agent sees when reading config.yaml...")

    with open('config.yaml', 'r') as f:
        data = yaml.safe_load(f)
        agent_sees = data['tools']['web_search']['enabled']

    console.print(f"  Agent reads config.yaml: web_search.enabled = {agent_sees}")

    if agent_sees:
        print_success("✓ Agent correctly sees web search as ENABLED")
        agent_correct = True
    else:
        print_error("✗ Agent incorrectly sees web search as DISABLED")
        agent_correct = False
    console.print()

    # Disable to restore initial state
    print_section("Step 6: Restore Initial State")
    print_thinking("Disabling web search to restore config...")
    cli.control_web_search('off')
    console.print()

    # Final summary
    print_header("📊 Test Results")

    if all_enabled and agent_correct:
        console.print("[bold green]✅ ALL TESTS PASSED[/bold green]")
        console.print()
        console.print("[green]The /web on command now:[/green]")
        console.print("  1. ✓ Updates tool runtime state")
        console.print("  2. ✓ Updates in-memory config")
        console.print("  3. ✓ Persists to config.yaml file")
        console.print("  4. ✓ Agent can read correct state from file")
        console.print()
        return True
    else:
        console.print("[bold red]❌ TESTS FAILED[/bold red]")
        console.print()
        if not all_enabled:
            console.print("[red]✗ States not synchronized after /web on[/red]")
        if not agent_correct:
            console.print("[red]✗ Agent cannot see correct state from file[/red]")
        console.print()
        return False


if __name__ == "__main__":
    success = test_web_persistence()
    sys.exit(0 if success else 1)
