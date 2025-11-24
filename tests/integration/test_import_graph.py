#!/usr/bin/env python3
"""Integration tests for Import Graph Analyzer.

Tests the import graph tool's ability to analyze dependencies,
detect circular imports, calculate metrics, and generate visualizations.
"""

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from tools.import_graph import (
    ImportGraphTool,
    analyze_imports,
    _convert_to_networkx,
    _detect_cycles,
    _calculate_metrics,
    _generate_mermaid,
    _safe_id
)
import json


def test_analyze_core_package():
    """Test analyzing the core package."""
    print("\n1. Testing core package analysis...")

    result = analyze_imports('core')

    assert result['success'], f"Analysis failed: {result.get('error')}"
    assert result['metrics']['total_modules'] > 0, "No modules found"
    assert 'core.agent' in result['graph']['modules'], "core.agent not found"
    assert 'core.config' in result['graph']['modules'], "core.config not found"

    print(f"   ✓ Found {result['metrics']['total_modules']} modules")
    print(f"   ✓ Found {result['metrics']['total_imports']} imports")
    print(f"   ✓ Coupling: {result['metrics']['coupling_coefficient']}")


def test_analyze_tools_package():
    """Test analyzing the tools package."""
    print("\n2. Testing tools package analysis...")

    result = analyze_imports('tools')

    assert result['success'], f"Analysis failed: {result.get('error')}"
    assert result['metrics']['total_modules'] > 0, "No modules found"
    assert 'tools.base' in result['graph']['modules'], "tools.base not found"

    print(f"   ✓ Found {result['metrics']['total_modules']} modules")
    print(f"   ✓ tools.base has {result['metrics']['most_imported'][0]['count']} imports")


def test_circular_dependency_detection():
    """Test circular dependency detection."""
    print("\n3. Testing circular dependency detection...")

    # Test on core package (should have no cycles)
    result = analyze_imports('core')

    assert 'cycles' in result, "Missing cycles field in result"
    cycles = result['cycles']
    print(f"   ✓ Found {len(cycles)} circular dependencies")

    if cycles:
        for cycle in cycles[:3]:  # Show first 3
            print(f"   → {' → '.join(cycle['cycle'])} (severity: {cycle['severity']})")
    else:
        print(f"   ✓ No cycles detected (clean architecture)")


def test_metrics_calculation():
    """Test metrics calculation."""
    print("\n4. Testing metrics calculation...")

    result = analyze_imports('core')
    metrics = result['metrics']

    # Check all expected metrics
    assert 'total_modules' in metrics
    assert 'total_imports' in metrics
    assert 'average_imports_per_module' in metrics
    assert 'coupling_coefficient' in metrics
    assert 'most_imported' in metrics
    assert 'highest_fan_out' in metrics
    assert 'orphan_count' in metrics

    print(f"   ✓ Total modules: {metrics['total_modules']}")
    print(f"   ✓ Average imports/module: {metrics['average_imports_per_module']}")
    print(f"   ✓ Coupling coefficient: {metrics['coupling_coefficient']}")
    print(f"   ✓ Orphan count: {metrics['orphan_count']}")

    # Coupling should be between 0 and 1
    assert 0 <= metrics['coupling_coefficient'] <= 1, "Invalid coupling coefficient"


def test_mermaid_visualization():
    """Test Mermaid diagram generation."""
    print("\n5. Testing Mermaid visualization...")

    result = analyze_imports('core', output_format='mermaid', max_nodes=10)

    viz = result['visualization']

    assert 'graph TD' in viz, "Missing Mermaid header"
    assert '-->' in viz, "Missing edges"
    assert viz.count('\n') > 5, "Visualization too short"

    print(f"   ✓ Generated Mermaid diagram ({len(viz)} chars)")
    print(f"   ✓ Contains {viz.count('-->') + viz.count('-.->')} edges")


def test_text_visualization():
    """Test text tree visualization."""
    print("\n6. Testing text visualization...")

    result = analyze_imports('core', output_format='text', max_nodes=20)

    viz = result['visualization']

    assert 'Import Dependency Graph:' in viz, "Missing header"
    assert len(viz) > 50, "Visualization too short"

    print(f"   ✓ Generated text visualization ({len(viz)} chars)")


def test_langchain_tool_integration():
    """Test LangChain tool wrapper."""
    print("\n7. Testing LangChain tool integration...")

    tool = ImportGraphTool()

    # Test with JSON input
    input_json = json.dumps({
        'path': 'core',
        'output_format': 'mermaid'
    })

    result_str = tool._run(input_json)
    result = json.loads(result_str)

    assert result['success'], f"Tool execution failed: {result.get('error')}"
    assert 'metrics' in result
    assert 'visualization' in result

    print(f"   ✓ Tool executed successfully")
    print(f"   ✓ Returned valid JSON")


def test_invalid_path():
    """Test handling of invalid path."""
    print("\n8. Testing invalid path handling...")

    result = analyze_imports('nonexistent_package_xyz')

    assert not result['success'], "Should fail for invalid path"
    assert 'error' in result
    assert len(result['error']) > 0, "Error message should not be empty"

    print(f"   ✓ Correctly handled invalid path")
    print(f"   ✓ Error: {result['error']}")


def test_max_nodes_limit():
    """Test max_nodes visualization limit."""
    print("\n9. Testing max_nodes limit...")

    # Test with very small limit
    result = analyze_imports('tools', output_format='mermaid', max_nodes=3)

    viz = result['visualization']

    # Count nodes in Mermaid (lines with brackets)
    node_count = sum(1 for line in viz.split('\n') if '[' in line and ']' in line)

    assert node_count <= 3, f"Too many nodes displayed: {node_count}"

    print(f"   ✓ Limited to {node_count} nodes")


def test_external_packages():
    """Test including external packages."""
    print("\n10. Testing external package inclusion...")

    # Without external packages
    result1 = analyze_imports('core', include_external=False)
    count1 = result1['metrics']['total_modules']

    # With external packages (should have more modules)
    result2 = analyze_imports('core', include_external=True)
    count2 = result2['metrics']['total_modules']

    print(f"   ✓ Without external: {count1} modules")
    print(f"   ✓ With external: {count2} modules")

    # External packages should add modules
    assert count2 >= count1, "External packages should not reduce module count"


def test_safe_id_conversion():
    """Test module name to safe ID conversion."""
    print("\n11. Testing safe ID conversion...")

    test_cases = [
        ('core.agent', 'core_agent'),
        ('tools.file-ops', 'tools_file_ops'),
        ('utils/formatting', 'utils_formatting'),
        ('core.models', 'core_models')
    ]

    for input_name, expected in test_cases:
        result = _safe_id(input_name)
        assert result == expected, f"Expected {expected}, got {result}"

    print(f"   ✓ All {len(test_cases)} conversions passed")


def test_graph_structure():
    """Test graph structure output."""
    print("\n12. Testing graph structure...")

    result = analyze_imports('core')

    graph = result['graph']

    assert 'modules' in graph
    assert 'edges' in graph
    assert 'total_modules' in graph
    assert 'total_edges' in graph

    assert isinstance(graph['modules'], list)
    assert isinstance(graph['edges'], list)

    # Edges should be tuples of (from, to)
    if graph['edges']:
        edge = graph['edges'][0]
        assert isinstance(edge, (list, tuple))
        assert len(edge) == 2

    print(f"   ✓ Graph structure valid")
    print(f"   ✓ {len(graph['modules'])} modules, {len(graph['edges'])} edges")


def test_cycle_severity_classification():
    """Test cycle severity classification."""
    print("\n13. Testing cycle severity...")

    # Test on core package
    result = analyze_imports('core')

    assert 'cycles' in result, "Missing cycles field in result"
    cycles = result['cycles']

    if cycles:
        for cycle in cycles:
            assert 'severity' in cycle
            assert cycle['severity'] in ['warning', 'error']
            assert 'length' in cycle

            # Direct cycles (length 2) should be errors
            if cycle['length'] == 2:
                assert cycle['severity'] == 'error', "Direct cycles should be errors"

        print(f"   ✓ Found {len(cycles)} cycles")
        print(f"   ✓ All cycles have severity classification")
    else:
        print(f"   ✓ No cycles found (clean codebase!)")


def test_fan_in_fan_out():
    """Test fan-in and fan-out metrics."""
    print("\n14. Testing fan-in/fan-out metrics...")

    result = analyze_imports('tools')
    metrics = result['metrics']

    # Check fan-out metrics
    assert 'highest_fan_out' in metrics
    assert 'max_fan_out' in metrics
    assert isinstance(metrics['highest_fan_out'], list)

    # Check fan-in metrics
    assert 'most_imported' in metrics
    assert 'max_fan_in' in metrics
    assert isinstance(metrics['most_imported'], list)

    if metrics['most_imported']:
        top_module = metrics['most_imported'][0]
        print(f"   ✓ Most imported: {top_module['module']} ({top_module['count']} imports)")

    if metrics['highest_fan_out']:
        top_module = metrics['highest_fan_out'][0]
        print(f"   ✓ Highest fan-out: {top_module['module']} ({top_module['count']} dependencies)")


def run_all_tests():
    """Run all integration tests."""
    print("=" * 70)
    print("IMPORT GRAPH ANALYZER - INTEGRATION TESTS")
    print("=" * 70)

    tests = [
        test_analyze_core_package,
        test_analyze_tools_package,
        test_circular_dependency_detection,
        test_metrics_calculation,
        test_mermaid_visualization,
        test_text_visualization,
        test_langchain_tool_integration,
        test_invalid_path,
        test_max_nodes_limit,
        test_external_packages,
        test_safe_id_conversion,
        test_graph_structure,
        test_cycle_severity_classification,
        test_fan_in_fan_out
    ]

    passed = 0
    failed = 0

    for test in tests:
        try:
            test()
            passed += 1
        except AssertionError as e:
            print(f"   ✗ FAILED: {e}")
            failed += 1
        except Exception as e:
            print(f"   ✗ ERROR: {e}")
            failed += 1

    print("\n" + "=" * 70)
    print(f"RESULTS: {passed} passed, {failed} failed out of {len(tests)} total")
    print("=" * 70)

    if failed == 0:
        print("✅ All import graph tests passed!")
        return 0
    else:
        print(f"❌ {failed} test(s) failed")
        return 1


if __name__ == '__main__':
    exit_code = run_all_tests()
    sys.exit(exit_code)
