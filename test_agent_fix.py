#!/usr/bin/env python3
"""Test script to verify agent error handling fixes."""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from core.agent import MetonAgent
from core.config import ConfigLoader
from core.models import ModelManager
from core.conversation import ConversationManager
from tools.file_ops import FileOperationsTool
from tools.code_executor import CodeExecutorTool
from tools.codebase_search import CodebaseSearchTool

def test_agent_error_recovery():
    """Test that agent handles invalid tool names gracefully and retries."""
    print("="*60)
    print("TESTING: Agent Error Recovery")
    print("="*60)
    print("\nThis test verifies:")
    print("1. Agent detects invalid tool names")
    print("2. Agent sees helpful error messages with available tools")
    print("3. Agent retries with correct tool name")
    print("4. Agent eventually completes the task or provides helpful answer")
    print("\n" + "="*60 + "\n")

    # Setup
    config = ConfigLoader()
    model_manager = ModelManager(config)
    conversation = ConversationManager(config)

    # Create tools
    tools = [
        FileOperationsTool(config),
        CodeExecutorTool(config),
        CodebaseSearchTool(config)
    ]

    # Create agent with verbose output
    agent = MetonAgent(config, model_manager, conversation, tools, verbose=True)

    # Test query that previously failed
    test_query = "How does an AI agent work?"
    print(f"Query: {test_query}\n")

    result = agent.run(test_query)

    print("\n" + "="*60)
    print("TEST RESULTS ANALYSIS:")
    print("="*60)
    print(f"✓ Success: {result['success']}")
    print(f"✓ Iterations used: {result['iterations']}/{agent.max_iterations}")
    print(f"✓ Thoughts generated: {len(result['thoughts'])}")
    print(f"✓ Tool calls made: {len(result['tool_calls'])}")

    # Analyze tool calls
    print("\n" + "-"*60)
    print("TOOL CALL ANALYSIS:")
    print("-"*60)

    error_calls = []
    success_calls = []

    for i, tc in enumerate(result['tool_calls'], 1):
        output = tc.get('output', '')
        is_error = output.startswith('✗')

        if is_error:
            error_calls.append(tc)
            print(f"{i}. ✗ ERROR: {tc['tool_name']}")
            print(f"   Input: {tc['input'][:80]}...")
            print(f"   Error: {output[:100]}...")
        else:
            success_calls.append(tc)
            print(f"{i}. ✓ SUCCESS: {tc['tool_name']}")
            print(f"   Input: {tc['input'][:80]}...")

    # Check recovery behavior
    print("\n" + "-"*60)
    print("ERROR RECOVERY CHECK:")
    print("-"*60)

    if error_calls:
        print(f"⚠ Found {len(error_calls)} error(s)")

        # Check if agent recovered
        if success_calls:
            print(f"✓ Agent recovered! Made {len(success_calls)} successful call(s) after error(s)")
            print("✓ ERROR RECOVERY: WORKING")
        else:
            print("✗ Agent did NOT recover - no successful tool calls")
            print("✗ ERROR RECOVERY: FAILED")
    else:
        print("✓ No errors encountered (agent used correct tool names from start)")
        print("✓ TOOL NAME LEARNING: WORKING")

    # Check if agent read the main implementation file
    print("\n" + "-"*60)
    print("COMPLETE INVESTIGATION CHECK:")
    print("-"*60)

    read_core_agent = False
    for tc in result['tool_calls']:
        if tc['tool_name'] == 'file_operations' and 'core/agent.py' in tc.get('input', ''):
            output = tc.get('output', '')
            if output.startswith('✓ Read'):
                read_core_agent = True
                print("✓ Agent read core/agent.py (main implementation)")
                break

    if not read_core_agent:
        print("✗ Agent did NOT read core/agent.py")
        print("  This is the main implementation file and should have been read!")

    # Check answer quality
    print("\n" + "-"*60)
    print("ANSWER QUALITY CHECK:")
    print("-"*60)
    print(f"Answer length: {len(result['output'])} characters")
    print(f"\nAnswer preview:\n{result['output'][:400]}...")

    # Quality indicators
    quality_indicators = {
        'read_implementation': read_core_agent,
        'mentions_react': 'react' in result['output'].lower(),
        'mentions_langgraph': 'langgraph' in result['output'].lower(),
        'mentions_nodes': 'node' in result['output'].lower(),
        'mentions_stategraph': 'stategraph' in result['output'].lower(),
        'has_line_numbers': any(char.isdigit() for char in result['output']) and 'line' in result['output'].lower(),
        'has_details': len(result['output']) > 300,
    }

    print("\nQuality indicators:")
    for indicator, present in quality_indicators.items():
        status = "✓" if present else "✗"
        print(f"  {status} {indicator}: {present}")

    quality_score = sum(quality_indicators.values()) / len(quality_indicators) * 100
    print(f"\nQuality score: {quality_score:.0f}%")

    # Overall assessment
    print("\n" + "-"*60)
    print("OVERALL ASSESSMENT:")
    print("-"*60)

    if quality_score >= 80:
        print("✓ EXCELLENT: Agent performed thorough investigation with detailed answer")
    elif quality_score >= 60:
        print("⚠ GOOD: Agent completed task but could be more thorough")
    elif quality_score >= 40:
        print("⚠ FAIR: Agent needs improvement in investigation depth")
    else:
        print("✗ POOR: Agent did not complete thorough investigation")

    print("\n" + "="*60)
    print("TEST COMPLETED")
    print("="*60)

    return result

if __name__ == "__main__":
    test_agent_error_recovery()
