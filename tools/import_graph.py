"""Import Graph Analyzer Tool for Meton.

This tool analyzes import dependencies in Python codebases using the grimp library.
It can detect circular dependencies, calculate coupling metrics, and generate
visualizations of the import graph.

Example:
    >>> from tools.import_graph import analyze_imports
    >>> result = analyze_imports('core')
    >>> print(result['metrics']['total_modules'])
    5
"""

from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import json

try:
    import grimp
    GRIMP_AVAILABLE = True
except ImportError:
    GRIMP_AVAILABLE = False

try:
    import networkx as nx
    NETWORKX_AVAILABLE = True
except ImportError:
    NETWORKX_AVAILABLE = False

from pydantic import Field
from tools.base import MetonBaseTool, ToolConfig
from utils.logger import setup_logger


class ImportGraphTool(MetonBaseTool):
    """Tool for analyzing import dependencies in Python codebases.

    Uses grimp library to build dependency graphs and NetworkX for analysis.
    Detects circular dependencies, calculates metrics, and generates visualizations.
    """

    name: str = "import_graph"
    description: str = """Analyze import dependencies in a Python codebase.

    Use this when you need to:
    - Understand project architecture and module relationships
    - Detect circular dependencies between modules
    - Find tightly coupled modules (high coupling)
    - Identify the most imported modules (high fan-in)
    - Identify modules with many dependencies (high fan-out)
    - Generate dependency visualizations (Mermaid diagrams)
    - Navigate complex codebases

    Input should be a JSON string with these fields:
    - path (required): Package or directory to analyze (e.g., "core", "tools")
    - include_external (optional): Include external packages (default: False)
    - output_format (optional): "text" or "mermaid" (default: "mermaid")
    - max_nodes (optional): Maximum nodes in visualization (default: 50)

    Example: {"path": "core", "output_format": "mermaid"}

    Returns JSON with graph structure, circular dependencies, metrics, and visualization.
    """

    # Enable/disable state
    _enabled: bool = True

    def __init__(self, config=None, **kwargs):
        """Initialize ImportGraphTool with optional configuration."""
        super().__init__(**kwargs)
        self.logger = setup_logger("import_graph")
        if config:
            self._enabled = config.get('tools.import_graph.enabled', True)

    def _run(self, input_str: str) -> str:
        """Analyze import dependencies.

        Args:
            input_str: JSON string with analysis parameters

        Returns:
            JSON string with analysis results
        """
        # Check if tool is enabled
        if not self._enabled:
            return json.dumps({
                'success': False,
                'error': 'import_graph tool is disabled'
            })

        if not GRIMP_AVAILABLE:
            error_msg = 'grimp library not installed. Run: pip install grimp'
            if self.logger:
                self.logger.error(error_msg)
            return json.dumps({
                'success': False,
                'error': error_msg
            })

        if not NETWORKX_AVAILABLE:
            error_msg = 'networkx library not installed. Run: pip install networkx'
            if self.logger:
                self.logger.error(error_msg)
            return json.dumps({
                'success': False,
                'error': error_msg
            })

        try:
            # Parse input using base class helper
            success, data = self._parse_json_input(input_str, required_fields=['path'])
            if not success:
                return json.dumps({
                    'success': False,
                    'error': data  # data is error message
                })

            path = data['path']
            include_external = data.get('include_external', False)
            output_format = data.get('output_format', 'mermaid')
            max_nodes = data.get('max_nodes', 50)

            if self.logger:
                self.logger.info(f"Analyzing imports for: {path}")

            # Analyze imports
            result = analyze_imports(
                path=path,
                include_external=include_external,
                output_format=output_format,
                max_nodes=max_nodes
            )

            return json.dumps(result, indent=2)

        except Exception as e:
            error_msg = f'Analysis failed: {str(e)}'
            if self.logger:
                self.logger.error(error_msg)
            return json.dumps({
                'success': False,
                'error': error_msg
            })

    async def _arun(self, input_str: str) -> str:
        """Async version (delegates to sync implementation)."""
        return self._run(input_str)


def analyze_imports(
    path: str,
    include_external: bool = False,
    output_format: str = 'mermaid',
    max_nodes: int = 50
) -> Dict[str, Any]:
    """Analyze import dependencies in a Python package.

    Args:
        path: Package or directory to analyze (e.g., 'core', 'tools')
        include_external: Include external package dependencies
        output_format: Output format ('text' or 'mermaid')
        max_nodes: Maximum nodes to show in visualization

    Returns:
        Dictionary with analysis results including:
        - success: Whether analysis succeeded
        - graph: Graph structure (modules and edges)
        - cycles: List of circular dependencies
        - metrics: Coupling metrics and statistics
        - visualization: Graph visualization in requested format
        - error: Error message if failed

    Example:
        >>> result = analyze_imports('core')
        >>> print(result['metrics']['total_modules'])
        5
        >>> print(len(result['cycles']))
        0
    """
    try:
        # Build graph using grimp
        graph = grimp.build_graph(path, include_external_packages=include_external)

        # Get module list
        modules = list(graph.modules)

        if not modules:
            return {
                'success': False,
                'error': f'No modules found in path: {path}'
            }

        # Convert to NetworkX for analysis
        nx_graph = _convert_to_networkx(graph)

        # Detect circular dependencies
        cycles = _detect_cycles(nx_graph)

        # Calculate metrics
        metrics = _calculate_metrics(nx_graph, modules)

        # Generate visualization
        visualization = _generate_visualization(
            nx_graph,
            output_format=output_format,
            max_nodes=max_nodes,
            cycles=cycles
        )

        # Build graph structure for output
        graph_data = {
            'modules': modules,
            'edges': _get_edges(graph),
            'total_modules': len(modules),
            'total_edges': len(_get_edges(graph))
        }

        return {
            'success': True,
            'graph': graph_data,
            'cycles': cycles,
            'metrics': metrics,
            'visualization': visualization,
            'error': ''
        }

    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def _convert_to_networkx(graph: 'grimp.Graph') -> nx.DiGraph:
    """Convert grimp graph to NetworkX DiGraph.

    Args:
        graph: Grimp graph object

    Returns:
        NetworkX directed graph
    """
    nx_graph = nx.DiGraph()

    # Add all modules as nodes
    for module in graph.modules:
        nx_graph.add_node(module)

    # Add all import relationships as edges
    for importer in graph.modules:
        imported = graph.find_modules_directly_imported_by(importer)
        for imported_module in imported:
            nx_graph.add_edge(importer, imported_module)

    return nx_graph


def _get_edges(graph: 'grimp.Graph') -> List[Tuple[str, str]]:
    """Extract all edges from grimp graph.

    Args:
        graph: Grimp graph object

    Returns:
        List of (from, to) tuples
    """
    edges = []
    for importer in graph.modules:
        imported = graph.find_modules_directly_imported_by(importer)
        for imported_module in imported:
            edges.append((importer, imported_module))
    return edges


def _detect_cycles(nx_graph: nx.DiGraph) -> List[Dict[str, Any]]:
    """Detect circular dependencies in the graph.

    Args:
        nx_graph: NetworkX directed graph

    Returns:
        List of cycles with metadata
    """
    cycles = []

    try:
        # Find all simple cycles
        for cycle in nx.simple_cycles(nx_graph):
            if len(cycle) > 1:  # Ignore self-loops
                # Classify severity
                severity = 'error' if len(cycle) == 2 else 'warning'

                cycles.append({
                    'cycle': cycle,
                    'length': len(cycle),
                    'severity': severity
                })
    except Exception:
        pass

    # Sort by length (shorter cycles are typically more problematic)
    return sorted(cycles, key=lambda x: x['length'])


def _calculate_metrics(nx_graph: nx.DiGraph, modules: List[str]) -> Dict[str, Any]:
    """Calculate graph metrics.

    Args:
        nx_graph: NetworkX directed graph
        modules: List of module names

    Returns:
        Dictionary of metrics
    """
    num_modules = len(modules)
    num_edges = nx_graph.number_of_edges()

    metrics = {
        'total_modules': num_modules,
        'total_imports': num_edges,
    }

    # Average imports per module
    if num_modules > 0:
        metrics['average_imports_per_module'] = round(num_edges / num_modules, 2)
    else:
        metrics['average_imports_per_module'] = 0.0

    # Coupling coefficient (density)
    if num_modules > 1:
        max_possible_edges = num_modules * (num_modules - 1)
        metrics['coupling_coefficient'] = round(num_edges / max_possible_edges, 3)
    else:
        metrics['coupling_coefficient'] = 0.0

    # Fan-out (modules with most outgoing dependencies)
    out_degrees = dict(nx_graph.out_degree())
    if out_degrees:
        max_out = max(out_degrees.values())
        metrics['max_fan_out'] = max_out
        metrics['highest_fan_out'] = [
            {'module': m, 'count': c}
            for m, c in sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
    else:
        metrics['max_fan_out'] = 0
        metrics['highest_fan_out'] = []

    # Fan-in (modules with most incoming dependencies)
    in_degrees = dict(nx_graph.in_degree())
    if in_degrees:
        max_in = max(in_degrees.values())
        metrics['max_fan_in'] = max_in
        metrics['most_imported'] = [
            {'module': m, 'count': c}
            for m, c in sorted(in_degrees.items(), key=lambda x: x[1], reverse=True)[:10]
        ]
    else:
        metrics['max_fan_in'] = 0
        metrics['most_imported'] = []

    # Orphans (modules not imported by anything)
    orphans = [node for node, degree in in_degrees.items() if degree == 0]
    metrics['orphan_count'] = len(orphans)
    metrics['orphans'] = orphans[:10]  # Limit to first 10

    return metrics


def _generate_visualization(
    nx_graph: nx.DiGraph,
    output_format: str = 'mermaid',
    max_nodes: int = 50,
    cycles: List[Dict[str, Any]] = None
) -> str:
    """Generate graph visualization.

    Args:
        nx_graph: NetworkX directed graph
        output_format: 'text' or 'mermaid'
        max_nodes: Maximum nodes to include
        cycles: List of detected cycles

    Returns:
        Visualization string
    """
    if output_format == 'mermaid':
        return _generate_mermaid(nx_graph, max_nodes, cycles or [])
    else:
        return _generate_text(nx_graph, max_nodes)


def _generate_mermaid(
    nx_graph: nx.DiGraph,
    max_nodes: int = 50,
    cycles: List[Dict[str, Any]] = None
) -> str:
    """Generate Mermaid diagram.

    Args:
        nx_graph: NetworkX directed graph
        max_nodes: Maximum nodes to include
        cycles: List of detected cycles

    Returns:
        Mermaid diagram syntax
    """
    lines = ["graph TD"]

    # Get nodes to display
    if nx_graph.number_of_nodes() > max_nodes:
        # Prioritize most connected nodes
        degrees = dict(nx_graph.degree())
        top_nodes = sorted(degrees.items(), key=lambda x: x[1], reverse=True)[:max_nodes]
        nodes = [node for node, _ in top_nodes]
        subgraph = nx_graph.subgraph(nodes)
    else:
        nodes = list(nx_graph.nodes())
        subgraph = nx_graph

    # Find nodes in cycles
    cycle_nodes = set()
    if cycles:
        for cycle_info in cycles:
            cycle_nodes.update(cycle_info['cycle'])

    # Add nodes
    for node in subgraph.nodes():
        safe_id = _safe_id(node)
        display_name = node.split('.')[-1] if '.' in node else node

        if node in cycle_nodes:
            lines.append(f'    {safe_id}["{display_name}"]:::cycle')
        else:
            lines.append(f'    {safe_id}["{display_name}"]')

    # Add edges
    for source, target in subgraph.edges():
        safe_source = _safe_id(source)
        safe_target = _safe_id(target)

        # Check if this edge is part of a cycle
        is_cycle_edge = False
        if cycles:
            for cycle_info in cycles:
                cycle = cycle_info['cycle']
                for i in range(len(cycle)):
                    if cycle[i] == source and cycle[(i + 1) % len(cycle)] == target:
                        is_cycle_edge = True
                        break

        if is_cycle_edge:
            lines.append(f'    {safe_source} -.->|cycle| {safe_target}')
        else:
            lines.append(f'    {safe_source} --> {safe_target}')

    # Add styling
    lines.append("    classDef cycle fill:#ff6b6b,stroke:#c92a2a")

    if nx_graph.number_of_nodes() > max_nodes:
        lines.append(f"\n    %% Showing {max_nodes} of {nx_graph.number_of_nodes()} modules")

    return '\n'.join(lines)


def _generate_text(nx_graph: nx.DiGraph, max_nodes: int = 50) -> str:
    """Generate text tree visualization.

    Args:
        nx_graph: NetworkX directed graph
        max_nodes: Maximum nodes to include

    Returns:
        ASCII tree visualization
    """
    lines = ["Import Dependency Graph:"]
    lines.append("=" * 60)

    # Find entry points (nodes with no incoming edges)
    in_degrees = dict(nx_graph.in_degree())
    entry_points = [node for node, degree in in_degrees.items() if degree == 0]

    if not entry_points:
        # If no entry points, use most imported modules
        out_degrees = dict(nx_graph.out_degree())
        entry_points = sorted(out_degrees.items(), key=lambda x: x[1], reverse=True)[:5]
        entry_points = [node for node, _ in entry_points]

    # Limit entry points
    entry_points = entry_points[:5]

    displayed = 0
    for entry in entry_points:
        if displayed >= max_nodes:
            break
        lines.append(f"\n{entry}")
        _print_tree(entry, nx_graph, lines, visited=set(), level=1, max_display=max_nodes - displayed)
        displayed += 1

    return '\n'.join(lines)


def _print_tree(
    node: str,
    graph: nx.DiGraph,
    lines: List[str],
    visited: set,
    level: int = 0,
    prefix: str = '',
    max_display: int = 100
) -> int:
    """Recursively print import tree.

    Args:
        node: Current node
        graph: NetworkX graph
        lines: Output lines list
        visited: Set of visited nodes
        level: Current depth level
        prefix: Line prefix for formatting
        max_display: Maximum nodes to display

    Returns:
        Number of nodes displayed
    """
    if len(lines) - 2 >= max_display:  # -2 for header lines
        return 0

    if node in visited:
        return 0

    visited.add(node)
    displayed = 0

    # Get successors
    successors = list(graph.successors(node))

    for i, succ in enumerate(successors):
        if len(lines) - 2 >= max_display:
            break

        is_last = (i == len(successors) - 1)
        connector = "└── " if is_last else "├── "
        lines.append(f"{prefix}{connector}{succ}")
        displayed += 1

        new_prefix = prefix + ("    " if is_last else "│   ")
        displayed += _print_tree(succ, graph, lines, visited, level + 1, new_prefix, max_display - displayed)

    return displayed


def _safe_id(name: str) -> str:
    """Convert module name to safe Mermaid ID.

    Args:
        name: Module name

    Returns:
        Safe identifier
    """
    return name.replace('.', '_').replace('-', '_').replace('/', '_')
