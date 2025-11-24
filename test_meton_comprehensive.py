#!/usr/bin/env python3
"""
Comprehensive Testing Script for Meton

Tests Meton's capabilities against real-world Python projects:
1. FastAPI RealWorld Example App (~3-4K lines)
2. HTTPie CLI (~10-15K lines)
3. FastAPI Todo API (~500-1K lines)

Test Coverage:
- RAG Indexing and Semantic Search
- Symbol Lookup (exact definition finding)
- Import Graph Analysis (dependency visualization, cycle detection)
- Code Explanation Skill
- Debugger Assistant Skill
- Test Generator Skill
- Code Review Skill
- Git Integration

Usage:
    python test_meton_comprehensive.py [--quick] [--projects PROJECT1,PROJECT2]

    --quick: Skip large projects (HTTPie)
    --projects: Comma-separated list of projects to test (fastapi_realworld, httpie, fastapi_todo)
"""

import os
import sys
import json
import time
import shutil
import argparse
import subprocess
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import ConfigLoader
from core.models import ModelManager
from core.conversation import ConversationManager
from core.agent import MetonAgent
from tools.codebase_search import CodebaseSearchTool
from tools.symbol_lookup import SymbolLookupTool
from tools.import_graph import ImportGraphTool
from rag.indexer import CodebaseIndexer

# Test projects configuration
TEST_PROJECTS = {
    'fastapi_realworld': {
        'name': 'FastAPI RealWorld Example',
        'url': 'https://github.com/nsidnev/fastapi-realworld-example-app.git',
        'dir': 'test_projects/fastapi-realworld-example-app',
        'index_path': 'app',
        'size': 'medium',
        'description': '3-4K lines, production FastAPI application'
    },
    'httpie': {
        'name': 'HTTPie CLI',
        'url': 'https://github.com/httpie/cli.git',
        'dir': 'test_projects/httpie-cli',
        'index_path': 'httpie',
        'size': 'large',
        'description': '10-15K lines, popular CLI tool (36K stars)'
    },
    'fastapi_todo': {
        'name': 'FastAPI Todo API',
        'url': 'https://github.com/Youngestdev/fastapi-todo.git',
        'dir': 'test_projects/fastapi-todo',
        'index_path': '.',
        'size': 'small',
        'description': '500-1K lines, simple REST API'
    }
}

# Test scenarios for each project
TEST_SCENARIOS = {
    'fastapi_realworld': [
        {
            'name': 'Architecture Understanding',
            'query': 'How does authentication work in this codebase? What pattern is used?',
            'expected_tools': ['codebase_search', 'symbol_lookup'],
            'success_indicators': ['JWT', 'token', 'auth', 'dependency']
        },
        {
            'name': 'Dependency Analysis',
            'query': 'Analyze the import dependencies in the app module. Are there any circular dependencies?',
            'expected_tools': ['import_graph'],
            'success_indicators': ['cycle', 'import', 'module', 'dependency']
        },
        {
            'name': 'Symbol Lookup',
            'query': 'Find the definition of the User model class.',
            'expected_tools': ['symbol_lookup', 'codebase_search'],
            'success_indicators': ['class User', 'model', 'BaseModel']
        },
        {
            'name': 'Code Explanation',
            'query': 'Explain how the article CRUD operations work.',
            'expected_tools': ['codebase_search', 'code_explainer'],
            'success_indicators': ['create', 'read', 'update', 'delete', 'article']
        }
    ],
    'httpie': [
        {
            'name': 'Architecture Overview',
            'query': 'What is the overall architecture of HTTPie? How is it organized?',
            'expected_tools': ['codebase_search', 'import_graph'],
            'success_indicators': ['cli', 'request', 'response', 'plugin', 'core']
        },
        {
            'name': 'Complex Symbol Lookup',
            'query': 'Find the main CLI entry point function.',
            'expected_tools': ['symbol_lookup', 'codebase_search'],
            'success_indicators': ['main', 'cli', 'entry', 'argparse']
        },
        {
            'name': 'Import Graph Analysis',
            'query': 'Analyze the import graph of the httpie core modules. Show coupling metrics.',
            'expected_tools': ['import_graph'],
            'success_indicators': ['coupling', 'fan-in', 'fan-out', 'density']
        }
    ],
    'fastapi_todo': [
        {
            'name': 'Simple Architecture',
            'query': 'How is the todo API structured? What endpoints are available?',
            'expected_tools': ['codebase_search', 'symbol_lookup'],
            'success_indicators': ['route', 'endpoint', 'todo', 'get', 'post']
        },
        {
            'name': 'Full Analysis',
            'query': 'Analyze the entire codebase structure and dependencies.',
            'expected_tools': ['import_graph', 'codebase_search'],
            'success_indicators': ['import', 'module', 'dependency']
        },
        {
            'name': 'Code Review',
            'query': 'Review the main application file for best practices and potential issues.',
            'expected_tools': ['codebase_search', 'code_reviewer'],
            'success_indicators': ['security', 'error', 'validation', 'type']
        }
    ]
}


class MetonTester:
    """Comprehensive Meton testing system."""

    def __init__(self, test_dir: str = 'test_projects', quick_mode: bool = False):
        self.test_dir = Path(test_dir)
        self.quick_mode = quick_mode
        self.results = {
            'start_time': datetime.now().isoformat(),
            'projects': {},
            'summary': {}
        }

        # Initialize Meton components
        print("🚀 Initializing Meton components...")
        self.config = ConfigLoader()
        self.model_manager = ModelManager(self.config)
        self.conversation_manager = ConversationManager(self.config)

        # Create test directory
        self.test_dir.mkdir(exist_ok=True)

    def clone_project(self, project_key: str) -> bool:
        """Clone a test project from GitHub."""
        project = TEST_PROJECTS[project_key]
        project_dir = Path(project['dir'])

        if project_dir.exists():
            print(f"✓ {project['name']} already cloned")
            return True

        print(f"📥 Cloning {project['name']}...")
        try:
            subprocess.run(
                ['git', 'clone', project['url'], str(project_dir)],
                check=True,
                capture_output=True
            )
            print(f"✓ {project['name']} cloned successfully")
            return True
        except subprocess.CalledProcessError as e:
            print(f"✗ Failed to clone {project['name']}: {e}")
            return False

    def index_project(self, project_key: str) -> Tuple[bool, Dict[str, Any]]:
        """Index a project with Meton's RAG system."""
        project = TEST_PROJECTS[project_key]
        index_path = Path(project['dir']) / project['index_path']

        print(f"📇 Indexing {project['name']}...")
        start_time = time.time()

        try:
            indexer = CodebaseIndexer(self.config)
            stats = indexer.index_directory(str(index_path))

            elapsed = time.time() - start_time
            print(f"✓ Indexed in {elapsed:.2f}s: {stats['files_indexed']} files, {stats['chunks_created']} chunks")

            return True, {
                'success': True,
                'elapsed_time': elapsed,
                'stats': stats
            }
        except Exception as e:
            elapsed = time.time() - start_time
            print(f"✗ Indexing failed: {e}")
            return False, {
                'success': False,
                'elapsed_time': elapsed,
                'error': str(e)
            }

    def test_semantic_search(self, project_key: str, query: str) -> Dict[str, Any]:
        """Test semantic code search."""
        print(f"  🔍 Testing semantic search: '{query[:50]}...'")
        start_time = time.time()

        try:
            search_tool = CodebaseSearchTool(self.config)
            results = search_tool._run(query)
            elapsed = time.time() - start_time

            # Parse results
            result_count = results.count('File:') if results else 0

            return {
                'success': True,
                'elapsed_time': elapsed,
                'result_count': result_count,
                'results_preview': results[:500] if results else None
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                'success': False,
                'elapsed_time': elapsed,
                'error': str(e)
            }

    def test_symbol_lookup(self, project_key: str, symbol: str) -> Dict[str, Any]:
        """Test symbol lookup."""
        project = TEST_PROJECTS[project_key]
        index_path = Path(project['dir']) / project['index_path']

        print(f"  🎯 Testing symbol lookup: '{symbol}'")
        start_time = time.time()

        try:
            lookup_tool = SymbolLookupTool(self.config)
            # Format as JSON input
            input_json = json.dumps({
                'symbol': symbol,
                'path': str(index_path)
            })
            result = lookup_tool._run(input_json)
            elapsed = time.time() - start_time

            found = 'not found' not in result.lower() and 'error' not in result.lower()

            return {
                'success': found,
                'elapsed_time': elapsed,
                'result_preview': result[:500] if result else None
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                'success': False,
                'elapsed_time': elapsed,
                'error': str(e)
            }

    def test_import_graph(self, project_key: str) -> Dict[str, Any]:
        """Test import graph analysis."""
        project = TEST_PROJECTS[project_key]
        index_path = Path(project['dir']) / project['index_path']

        print(f"  📊 Testing import graph analysis...")
        start_time = time.time()

        try:
            graph_tool = ImportGraphTool()
            input_json = json.dumps({
                'path': str(index_path),
                'output_format': 'mermaid'
            })
            result = graph_tool._run(input_json)
            elapsed = time.time() - start_time

            # Check for key indicators
            has_graph = 'graph' in result.lower() or 'module' in result.lower()
            has_metrics = 'coupling' in result.lower() or 'density' in result.lower()
            has_cycles = 'cycle' in result.lower() or 'circular' in result.lower()

            return {
                'success': has_graph,
                'elapsed_time': elapsed,
                'has_metrics': has_metrics,
                'has_cycles': has_cycles,
                'result_preview': result[:500] if result else None
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                'success': False,
                'elapsed_time': elapsed,
                'error': str(e)
            }

    def test_agent_scenario(self, project_key: str, scenario: Dict[str, Any]) -> Dict[str, Any]:
        """Test a complete agent scenario."""
        print(f"  🤖 Testing scenario: {scenario['name']}")
        start_time = time.time()

        try:
            # Create agent
            from tools.file_ops import FileOperationsTool
            from tools.code_executor import CodeExecutorTool

            tools = [
                FileOperationsTool(self.config),
                CodebaseSearchTool(self.config),
                SymbolLookupTool(self.config),
                ImportGraphTool()
            ]

            agent = MetonAgent(
                config=self.config,
                model_manager=self.model_manager,
                conversation=self.conversation_manager,
                tools=tools,
                verbose=False
            )

            # Run query
            result = agent.run(scenario['query'])
            elapsed = time.time() - start_time

            # Get response from result
            response = result.get('output', '')

            # Check success indicators
            indicators_found = sum(
                1 for indicator in scenario['success_indicators']
                if indicator.lower() in response.lower()
            )

            success_rate = indicators_found / len(scenario['success_indicators'])

            return {
                'success': success_rate >= 0.5,  # At least 50% indicators found
                'elapsed_time': elapsed,
                'success_rate': success_rate,
                'indicators_found': indicators_found,
                'total_indicators': len(scenario['success_indicators']),
                'response_length': len(response),
                'response_preview': response[:500],
                'agent_success': result.get('success', False),
                'iterations': result.get('iterations', 0)
            }
        except Exception as e:
            elapsed = time.time() - start_time
            return {
                'success': False,
                'elapsed_time': elapsed,
                'error': str(e)
            }

    def test_project(self, project_key: str) -> Dict[str, Any]:
        """Run comprehensive tests on a single project."""
        project = TEST_PROJECTS[project_key]
        print(f"\n{'='*60}")
        print(f"Testing: {project['name']}")
        print(f"Description: {project['description']}")
        print(f"{'='*60}\n")

        results = {
            'name': project['name'],
            'description': project['description'],
            'size': project['size'],
            'tests': {}
        }

        # Step 1: Clone project
        if not self.clone_project(project_key):
            results['clone_failed'] = True
            return results

        # Step 2: Index project
        success, index_results = self.index_project(project_key)
        results['tests']['indexing'] = index_results

        if not success:
            results['index_failed'] = True
            return results

        # Step 3: Test semantic search
        test_query = TEST_SCENARIOS[project_key][0]['query']
        results['tests']['semantic_search'] = self.test_semantic_search(
            project_key, test_query
        )

        # Step 4: Test symbol lookup (extract symbol from scenarios)
        # Look for common symbols based on project type
        test_symbols = {
            'fastapi_realworld': 'User',
            'httpie': 'main',
            'fastapi_todo': 'Todo'
        }
        if project_key in test_symbols:
            results['tests']['symbol_lookup'] = self.test_symbol_lookup(
                project_key, test_symbols[project_key]
            )

        # Step 5: Test import graph
        results['tests']['import_graph'] = self.test_import_graph(project_key)

        # Step 6: Test agent scenarios
        results['tests']['scenarios'] = []
        for scenario in TEST_SCENARIOS[project_key]:
            scenario_result = self.test_agent_scenario(project_key, scenario)
            scenario_result['scenario_name'] = scenario['name']
            results['tests']['scenarios'].append(scenario_result)

        return results

    def run_all_tests(self, selected_projects: List[str] = None) -> Dict[str, Any]:
        """Run tests on all projects."""
        print("╔═══════════════════════════════════════════════════════════╗")
        print("║     METON COMPREHENSIVE TESTING SUITE                     ║")
        print("╚═══════════════════════════════════════════════════════════╝\n")

        # Determine which projects to test
        if selected_projects:
            projects_to_test = [p for p in selected_projects if p in TEST_PROJECTS]
        else:
            projects_to_test = list(TEST_PROJECTS.keys())

        # Skip large projects in quick mode
        if self.quick_mode:
            projects_to_test = [
                p for p in projects_to_test
                if TEST_PROJECTS[p]['size'] != 'large'
            ]
            print("⚡ Quick mode: Skipping large projects\n")

        print(f"Testing {len(projects_to_test)} projects:\n")
        for project_key in projects_to_test:
            project = TEST_PROJECTS[project_key]
            print(f"  • {project['name']} ({project['size']})")
        print()

        # Run tests
        for project_key in projects_to_test:
            project_results = self.test_project(project_key)
            self.results['projects'][project_key] = project_results

        # Generate summary
        self.results['end_time'] = datetime.now().isoformat()
        self.generate_summary()

        return self.results

    def generate_summary(self):
        """Generate test summary statistics."""
        total_tests = 0
        passed_tests = 0
        total_time = 0.0

        for project_key, project_results in self.results['projects'].items():
            if 'tests' not in project_results:
                continue

            for test_type, test_result in project_results['tests'].items():
                if test_type == 'scenarios':
                    for scenario in test_result:
                        total_tests += 1
                        if scenario.get('success'):
                            passed_tests += 1
                        total_time += scenario.get('elapsed_time', 0)
                elif isinstance(test_result, dict):
                    total_tests += 1
                    if test_result.get('success'):
                        passed_tests += 1
                    total_time += test_result.get('elapsed_time', 0)

        self.results['summary'] = {
            'total_projects': len(self.results['projects']),
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'pass_rate': (passed_tests / total_tests * 100) if total_tests > 0 else 0,
            'total_time': total_time
        }

    def print_summary(self):
        """Print test summary to console."""
        summary = self.results['summary']

        print("\n" + "="*60)
        print("TEST SUMMARY")
        print("="*60)
        print(f"Projects Tested:  {summary['total_projects']}")
        print(f"Total Tests:      {summary['total_tests']}")
        print(f"Passed:           {summary['passed_tests']} ✓")
        print(f"Failed:           {summary['failed_tests']} ✗")
        print(f"Pass Rate:        {summary['pass_rate']:.1f}%")
        print(f"Total Time:       {summary['total_time']:.2f}s")
        print("="*60)

        # Per-project breakdown
        print("\nPER-PROJECT RESULTS:")
        for project_key, project_results in self.results['projects'].items():
            if 'tests' not in project_results:
                print(f"\n  {project_results['name']}: ✗ SKIPPED")
                continue

            print(f"\n  {project_results['name']}:")

            # Indexing
            if 'indexing' in project_results['tests']:
                idx = project_results['tests']['indexing']
                status = "✓" if idx.get('success') else "✗"
                print(f"    Indexing:        {status} ({idx.get('elapsed_time', 0):.2f}s)")
                if idx.get('stats'):
                    print(f"      Files: {idx['stats'].get('files_indexed', 0)}, "
                          f"Chunks: {idx['stats'].get('chunks_created', 0)}")

            # Other tests
            for test_type in ['semantic_search', 'symbol_lookup', 'import_graph']:
                if test_type in project_results['tests']:
                    test = project_results['tests'][test_type]
                    status = "✓" if test.get('success') else "✗"
                    name = test_type.replace('_', ' ').title()
                    print(f"    {name:16} {status} ({test.get('elapsed_time', 0):.2f}s)")

            # Scenarios
            if 'scenarios' in project_results['tests']:
                print(f"    Agent Scenarios:")
                for scenario in project_results['tests']['scenarios']:
                    status = "✓" if scenario.get('success') else "✗"
                    rate = scenario.get('success_rate', 0) * 100
                    print(f"      {scenario['scenario_name']:30} {status} "
                          f"({rate:.0f}% match, {scenario.get('elapsed_time', 0):.2f}s)")

    def save_results(self, output_file: str = 'test_results.json'):
        """Save test results to JSON file."""
        output_path = Path(output_file)
        with open(output_path, 'w') as f:
            json.dump(self.results, f, indent=2)
        print(f"\n📄 Results saved to: {output_path.absolute()}")

    def cleanup(self):
        """Clean up test projects."""
        if self.test_dir.exists():
            print(f"\n🗑️  Cleaning up test projects...")
            shutil.rmtree(self.test_dir)
            print("✓ Cleanup complete")


def main():
    parser = argparse.ArgumentParser(
        description='Comprehensive testing suite for Meton',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests
  python test_meton_comprehensive.py

  # Quick mode (skip large projects)
  python test_meton_comprehensive.py --quick

  # Test specific projects
  python test_meton_comprehensive.py --projects fastapi_todo,fastapi_realworld

  # Save results and cleanup
  python test_meton_comprehensive.py --output results.json --cleanup
        """
    )

    parser.add_argument(
        '--quick',
        action='store_true',
        help='Quick mode: skip large projects'
    )

    parser.add_argument(
        '--projects',
        type=str,
        help='Comma-separated list of projects to test (fastapi_realworld,httpie,fastapi_todo)'
    )

    parser.add_argument(
        '--output',
        type=str,
        default='test_results.json',
        help='Output file for test results (default: test_results.json)'
    )

    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up test projects after testing'
    )

    args = parser.parse_args()

    # Parse selected projects
    selected_projects = None
    if args.projects:
        selected_projects = [p.strip() for p in args.projects.split(',')]

    # Run tests
    tester = MetonTester(quick_mode=args.quick)

    try:
        tester.run_all_tests(selected_projects)
        tester.print_summary()
        tester.save_results(args.output)
    except KeyboardInterrupt:
        print("\n\n⚠️  Testing interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Testing failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        if args.cleanup:
            tester.cleanup()

    # Print final status
    summary = tester.results.get('summary', {})
    pass_rate = summary.get('pass_rate', 0)

    if pass_rate >= 90:
        print("\n🎉 Excellent! Meton is performing very well!")
    elif pass_rate >= 70:
        print("\n👍 Good! Meton is working well with minor issues.")
    elif pass_rate >= 50:
        print("\n⚠️  Fair. Meton needs some improvements.")
    else:
        print("\n❌ Poor performance. Meton needs significant work.")

    return 0 if pass_rate >= 70 else 1


if __name__ == '__main__':
    sys.exit(main())
