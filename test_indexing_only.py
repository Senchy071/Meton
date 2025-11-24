#!/usr/bin/env python3
"""
Quick Indexing Test for Meton

Tests only the RAG indexing pipeline without agent scenarios.
Faster alternative to comprehensive test for validating indexing.

Usage:
    python test_indexing_only.py [--project PROJECT_NAME]

Expected duration: 2-5 minutes per project
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
from typing import Dict, Any, Tuple

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from core.config import ConfigLoader

# Test projects
TEST_PROJECTS = {
    'fastapi_example': {
        'name': 'FastAPI Framework',
        'url': 'https://github.com/tiangolo/fastapi.git',
        'dir': 'test_projects/fastapi',
        'index_path': 'fastapi',
        'description': '~2K lines, FastAPI core framework'
    },
    'fastapi_realworld': {
        'name': 'FastAPI RealWorld',
        'url': 'https://github.com/nsidnev/fastapi-realworld-example-app.git',
        'dir': 'test_projects/fastapi-realworld-example-app',
        'index_path': 'app',
        'description': '~3-4K lines, production app'
    }
}


def clone_project(project_key: str) -> bool:
    """Clone a test project from GitHub."""
    project = TEST_PROJECTS[project_key]
    project_dir = Path(project['dir'])

    if project_dir.exists():
        print(f"✓ {project['name']} already cloned")
        return True

    print(f"📥 Cloning {project['name']}...")
    try:
        subprocess.run(
            ['git', 'clone', '--depth', '1', project['url'], str(project_dir)],
            check=True,
            capture_output=True,
            timeout=60
        )
        print(f"✓ Cloned successfully")
        return True
    except Exception as e:
        print(f"✗ Failed to clone: {e}")
        return False


def test_indexing(project_key: str) -> Dict[str, Any]:
    """Test RAG indexing on a project."""
    project = TEST_PROJECTS[project_key]
    index_path = Path(project['dir']) / project['index_path']

    print(f"\n{'='*60}")
    print(f"Testing: {project['name']}")
    print(f"Description: {project['description']}")
    print(f"{'='*60}\n")

    # Clone project
    if not clone_project(project_key):
        return {'success': False, 'error': 'Clone failed'}

    # Count Python files
    py_files = list(index_path.rglob("*.py")) if index_path.exists() else []
    print(f"Found {len(py_files)} Python files")

    if not py_files:
        return {'success': False, 'error': 'No Python files found'}

    # Test indexing
    print(f"\n📇 Indexing {index_path}...\n")
    start_time = time.time()

    try:
        # Import RAG components
        from rag.embeddings import EmbeddingModel
        from rag.vector_store import VectorStore
        from rag.metadata_store import MetadataStore
        from rag.indexer import CodebaseIndexer

        # Load config
        config = ConfigLoader()

        # Initialize components
        print("  Initializing embedding model...")
        embedder = EmbeddingModel()

        print("  Creating vector store...")
        vector_store = VectorStore(dimension=config.config.rag.dimensions)

        print("  Setting up metadata store...")
        import tempfile
        temp_metadata = tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False)
        temp_metadata.close()
        metadata_store = MetadataStore(temp_metadata.name)

        # Create indexer
        print("  Indexing codebase...")
        indexer = CodebaseIndexer(
            embedder=embedder,
            vector_store=vector_store,
            metadata_store=metadata_store,
            verbose=True  # Show progress
        )

        # Index
        stats = indexer.index_directory(
            dirpath=str(index_path),
            recursive=True
        )

        elapsed = time.time() - start_time

        # Display results
        print(f"\n{'='*60}")
        print("INDEXING RESULTS")
        print(f"{'='*60}")
        print(f"Files processed: {stats.get('files_processed', 0)}")
        print(f"Chunks created:  {stats.get('chunks_created', 0)}")
        print(f"Time taken:      {elapsed:.2f}s")
        print(f"{'='*60}\n")

        # Test semantic search
        print("🔍 Testing semantic search...")
        from tools.codebase_search import CodebaseSearchTool

        # Manually set up the search tool with our indexer
        search_tool = CodebaseSearchTool(config)
        search_tool._indexer = indexer  # Inject our indexer
        search_tool._rag_enabled = True

        query = "main application"
        print(f"  Query: '{query}'")
        try:
            results = search_tool._run(query)
            result_count = results.count('File:') if results else 0
            print(f"  Results: {result_count} matches found")
            if result_count > 0:
                print(f"  Preview: {results[:200]}...")
        except Exception as e:
            print(f"  Search failed: {e}")

        return {
            'success': True,
            'files_processed': stats.get('files_processed', 0),
            'chunks_created': stats.get('chunks_created', 0),
            'elapsed_time': elapsed,
            'files_per_second': stats.get('files_processed', 0) / elapsed if elapsed > 0 else 0
        }

    except Exception as e:
        elapsed = time.time() - start_time
        print(f"\n✗ Indexing failed: {e}")
        import traceback
        traceback.print_exc()

        return {
            'success': False,
            'error': str(e),
            'elapsed_time': elapsed
        }


def main():
    parser = argparse.ArgumentParser(
        description='Quick indexing test for Meton (no agent scenarios)',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        '--project',
        type=str,
        choices=list(TEST_PROJECTS.keys()),
        default='fastapi_example',
        help='Project to test (default: fastapi_example)'
    )

    parser.add_argument(
        '--cleanup',
        action='store_true',
        help='Clean up test projects after testing'
    )

    args = parser.parse_args()

    print("╔════════════════════════════════════════════════════════════╗")
    print("║     METON INDEXING TEST                                    ║")
    print("╚════════════════════════════════════════════════════════════╝\n")

    # Run test
    result = test_indexing(args.project)

    # Summary
    print("\n" + "="*60)
    if result['success']:
        print("✅ TEST PASSED")
        print(f"Processed {result['files_processed']} files in {result['elapsed_time']:.2f}s")
        print(f"Speed: {result['files_per_second']:.1f} files/second")
    else:
        print("❌ TEST FAILED")
        if 'error' in result:
            print(f"Error: {result['error']}")
    print("="*60)

    # Cleanup
    if args.cleanup:
        print("\n🗑️  Cleaning up test projects...")
        test_dir = Path('test_projects')
        if test_dir.exists():
            shutil.rmtree(test_dir)
            print("✓ Cleanup complete")

    return 0 if result['success'] else 1


if __name__ == '__main__':
    sys.exit(main())
