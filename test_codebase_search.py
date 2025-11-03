#!/usr/bin/env python3
"""Test codebase search tool functionality."""

import sys
sys.path.insert(0, '/media/development/projects/meton')

import json
import tempfile
import os
import shutil
from pathlib import Path

from core.config import ConfigLoader
from tools.codebase_search import CodebaseSearchTool
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.metadata_store import MetadataStore
from rag.indexer import CodebaseIndexer


def setup_test_index():
    """Create a test index with some sample code."""
    # Create temporary directory for test files
    temp_dir = tempfile.mkdtemp()

    # Create test Python files
    test_file1 = os.path.join(temp_dir, "auth.py")
    with open(test_file1, "w") as f:
        f.write('''"""User authentication module."""

def authenticate_user(username: str, password: str) -> bool:
    """Authenticate a user with username and password.

    Args:
        username: The username to authenticate
        password: The password to verify

    Returns:
        True if authentication succeeds, False otherwise
    """
    # Hash password and check against database
    return True

def logout_user(user_id: int) -> None:
    """Log out a user by invalidating their session.

    Args:
        user_id: The ID of the user to log out
    """
    # Invalidate session
    pass
''')

    test_file2 = os.path.join(temp_dir, "calculator.py")
    with open(test_file2, "w") as f:
        f.write('''"""Calculator utilities."""

def add(a: int, b: int) -> int:
    """Add two numbers.

    Args:
        a: First number
        b: Second number

    Returns:
        Sum of a and b
    """
    return a + b

def fibonacci(n: int) -> int:
    """Calculate the nth Fibonacci number.

    Args:
        n: The position in the Fibonacci sequence

    Returns:
        The nth Fibonacci number
    """
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)
''')

    # Create index directory
    index_dir = tempfile.mkdtemp()
    metadata_path = os.path.join(index_dir, "metadata.json")
    vector_store_path = os.path.join(index_dir, "faiss.index")

    # Initialize indexer
    embedder = EmbeddingModel()
    vector_store = VectorStore(dimension=embedder.get_dimension())
    metadata_store = MetadataStore(metadata_path)
    indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)

    # Index the test files
    indexer.index_directory(temp_dir, recursive=False)

    # Save the index
    indexer.save(vector_store_path)

    # Clean up temp files
    shutil.rmtree(temp_dir)

    return index_dir, metadata_path, vector_store_path


def create_test_config(index_path, metadata_path, rag_enabled=True, tool_enabled=True):
    """Create a test configuration."""
    config_content = f"""project:
  name: Meton Test
  version: 0.1.0
  description: Test Configuration
models:
  primary: qwen2.5:32b-instruct-q5_K_M
  fallback: llama3.1:8b
  quick: mistral:latest
  settings:
    temperature: 0.0
    max_tokens: 2048
    top_p: 0.9
    num_ctx: 4096
agent:
  max_iterations: 10
  verbose: true
  show_reasoning: true
  timeout: 300
tools:
  file_ops:
    enabled: true
    allowed_paths:
    - /media/development/projects/
    blocked_paths:
    - /etc/
    - /sys/
    - /proc/
    max_file_size_mb: 10
  code_executor:
    enabled: true
    timeout: 5
    max_output_length: 10000
  web_search:
    enabled: false
    max_results: 5
    timeout: 10
  codebase_search:
    enabled: {str(tool_enabled).lower()}
    top_k: 5
    similarity_threshold: 0.0
    max_code_length: 200
conversation:
  max_history: 20
  save_path: ./conversations/
  auto_save: true
cli:
  theme: monokai
  show_timestamps: true
  syntax_highlight: true
  show_tool_output: true
rag:
  enabled: {str(rag_enabled).lower()}
  embedding_model: sentence-transformers/all-mpnet-base-v2
  index_path: {index_path}
  metadata_path: {metadata_path}
  dimensions: 768
  top_k: 10
  similarity_threshold: 0.7
"""

    # Create temporary config file
    config_file = tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False)
    config_file.write(config_content)
    config_file.close()

    return config_file.name


def main():
    print("=" * 80)
    print("TEST: Codebase Search Tool")
    print("=" * 80)

    # Test 1: RAG disabled - should return error
    print("\n1. Testing with RAG disabled...")
    config_path = create_test_config("./test_index", "./test_index/metadata.json",
                                      rag_enabled=False, tool_enabled=True)
    try:
        config = ConfigLoader(config_path)
        tool = CodebaseSearchTool(config)

        input_json = json.dumps({"query": "user authentication"})
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] is False, "Should fail when RAG is disabled"
        assert "RAG is disabled" in result["error"], "Should mention RAG is disabled"
        print(f"   Error message: {result['error']}")
        print("   ✓ RAG disabled check works correctly")
    finally:
        os.unlink(config_path)

    # Test 2: Tool disabled - should return error
    print("\n2. Testing with tool disabled...")
    config_path = create_test_config("./test_index", "./test_index/metadata.json",
                                      rag_enabled=True, tool_enabled=False)
    try:
        config = ConfigLoader(config_path)
        tool = CodebaseSearchTool(config)

        input_json = json.dumps({"query": "user authentication"})
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] is False, "Should fail when tool is disabled"
        assert "disabled" in result["error"].lower(), "Should mention tool is disabled"
        print(f"   Error message: {result['error']}")
        print("   ✓ Tool disabled check works correctly")
    finally:
        os.unlink(config_path)

    # Test 3: No index loaded - should return error
    print("\n3. Testing with no index loaded...")
    empty_index_dir = tempfile.mkdtemp()
    metadata_path = os.path.join(empty_index_dir, "metadata.json")
    config_path = create_test_config(empty_index_dir, metadata_path,
                                      rag_enabled=True, tool_enabled=True)
    try:
        config = ConfigLoader(config_path)
        tool = CodebaseSearchTool(config)

        input_json = json.dumps({"query": "user authentication"})
        result_str = tool._run(input_json)
        result = json.loads(result_str)

        assert result["success"] is False, "Should fail when no index exists"
        assert "No index found" in result["error"] or "Index is empty" in result["error"], \
            "Should mention missing index"
        print(f"   Error message: {result['error']}")
        print("   ✓ No index check works correctly")
    finally:
        os.unlink(config_path)
        shutil.rmtree(empty_index_dir)

    # Setup test index for remaining tests
    print("\n4. Setting up test index...")
    index_dir, metadata_path, vector_store_path = setup_test_index()
    print(f"   Created test index at {index_dir}")

    try:
        # Test 4: Invalid JSON input
        print("\n5. Testing invalid JSON input...")
        config_path = create_test_config(index_dir, metadata_path,
                                          rag_enabled=True, tool_enabled=True)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            result_str = tool._run("not valid json")
            result = json.loads(result_str)

            assert result["success"] is False, "Should fail on invalid JSON"
            assert "Invalid JSON" in result["error"], "Should mention invalid JSON"
            print(f"   Error message: {result['error']}")
            print("   ✓ Invalid JSON handling works correctly")
        finally:
            os.unlink(config_path)

        # Test 5: Missing query parameter
        print("\n6. Testing missing query parameter...")
        config_path = create_test_config(index_dir, metadata_path,
                                          rag_enabled=True, tool_enabled=True)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            input_json = json.dumps({"wrong_key": "value"})
            result_str = tool._run(input_json)
            result = json.loads(result_str)

            assert result["success"] is False, "Should fail on missing query"
            assert "Missing required 'query'" in result["error"], "Should mention missing query"
            print(f"   Error message: {result['error']}")
            print("   ✓ Missing query parameter check works correctly")
        finally:
            os.unlink(config_path)

        # Test 6: Empty query
        print("\n7. Testing empty query...")
        config_path = create_test_config(index_dir, metadata_path,
                                          rag_enabled=True, tool_enabled=True)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            input_json = json.dumps({"query": ""})
            result_str = tool._run(input_json)
            result = json.loads(result_str)

            assert result["success"] is False, "Should fail on empty query"
            assert "cannot be empty" in result["error"], "Should mention empty query"
            print(f"   Error message: {result['error']}")
            print("   ✓ Empty query check works correctly")
        finally:
            os.unlink(config_path)

        # Test 7: Successful search with results
        print("\n8. Testing successful search with results...")
        config_path = create_test_config(index_dir, metadata_path,
                                          rag_enabled=True, tool_enabled=True)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            input_json = json.dumps({"query": "user authentication and login"})
            result_str = tool._run(input_json)
            result = json.loads(result_str)

            assert result["success"] is True, f"Search should succeed: {result.get('error', '')}"
            assert len(result["results"]) > 0, "Should have at least one result"
            assert result["count"] == len(result["results"]), "Count should match results length"

            # Check result structure
            first_result = result["results"][0]
            assert "file" in first_result, "Should have file field"
            assert "type" in first_result, "Should have type field"
            assert "name" in first_result, "Should have name field"
            assert "lines" in first_result, "Should have lines field"
            assert "similarity" in first_result, "Should have similarity field"
            assert "code_snippet" in first_result, "Should have code_snippet field"

            # Check that authentication-related result is first (most relevant)
            assert "auth" in first_result["name"].lower(), \
                "Most relevant result should be authentication-related"

            print(f"   Found {len(result['results'])} results")
            print(f"   Top result: {first_result['name']} (similarity: {first_result['similarity']:.4f})")
            print("   ✓ Successful search returns results correctly")
        finally:
            os.unlink(config_path)

        # Test 8: Results sorted by similarity (highest first)
        print("\n9. Testing results sorted by similarity...")
        config_path = create_test_config(index_dir, metadata_path,
                                          rag_enabled=True, tool_enabled=True)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            input_json = json.dumps({"query": "authentication"})
            result_str = tool._run(input_json)
            result = json.loads(result_str)

            if len(result["results"]) >= 2:
                # Check that results are sorted by similarity (descending)
                for i in range(len(result["results"]) - 1):
                    curr_sim = result["results"][i]["similarity"]
                    next_sim = result["results"][i + 1]["similarity"]
                    assert curr_sim >= next_sim, \
                        f"Results should be sorted by similarity (descending): {curr_sim} >= {next_sim}"

                print(f"   Results are properly sorted by similarity")
                print("   ✓ Sorting works correctly")
            else:
                print("   ✓ Not enough results to test sorting (need at least 2)")
        finally:
            os.unlink(config_path)

        # Test 9: Code snippet truncation
        print("\n10. Testing code snippet truncation...")
        # Create a file with very long code
        temp_dir = tempfile.mkdtemp()
        long_file = os.path.join(temp_dir, "long_code.py")
        long_code = "def very_long_function():\n" + "    # " + ("x" * 1000) + "\n    pass\n"
        with open(long_file, "w") as f:
            f.write(long_code)

        # Create new index with long code
        long_index_dir = tempfile.mkdtemp()
        long_metadata_path = os.path.join(long_index_dir, "metadata.json")
        long_vector_store_path = os.path.join(long_index_dir, "faiss.index")

        embedder = EmbeddingModel()
        vector_store = VectorStore(dimension=embedder.get_dimension())
        metadata_store = MetadataStore(long_metadata_path)
        indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=False)
        indexer.index_directory(temp_dir, recursive=False)
        indexer.save(long_vector_store_path)

        # Test with max_code_length = 200
        config_path = create_test_config(long_index_dir, long_metadata_path,
                                          rag_enabled=True, tool_enabled=True)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            input_json = json.dumps({"query": "very long function"})
            result_str = tool._run(input_json)
            result = json.loads(result_str)

            if len(result["results"]) > 0:
                code_snippet = result["results"][0]["code_snippet"]
                # Code should be truncated to max_code_length (200) + truncation message
                assert len(code_snippet) <= 220, \
                    f"Code snippet should be truncated (got {len(code_snippet)} chars)"
                assert "truncated" in code_snippet, "Should have truncation message"
                print(f"   Code snippet length: {len(code_snippet)} chars (original: {len(long_code)})")
                print("   ✓ Code truncation works correctly")
            else:
                print("   ✓ No results to test truncation")
        finally:
            os.unlink(config_path)
            shutil.rmtree(temp_dir)
            shutil.rmtree(long_index_dir)

        # Test 10: Top K limit
        print("\n11. Testing top_k limit...")
        config_path = create_test_config(index_dir, metadata_path,
                                          rag_enabled=True, tool_enabled=True)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            # Search with a generic query that should match multiple chunks
            input_json = json.dumps({"query": "function"})
            result_str = tool._run(input_json)
            result = json.loads(result_str)

            # Should return at most top_k (5) results
            assert len(result["results"]) <= 5, \
                f"Should return at most 5 results, got {len(result['results'])}"
            print(f"   Returned {len(result['results'])} results (max: 5)")
            print("   ✓ Top K limit works correctly")
        finally:
            os.unlink(config_path)

        # Test 11: Enable/disable methods
        print("\n12. Testing enable/disable methods...")
        config_path = create_test_config(index_dir, metadata_path,
                                          rag_enabled=True, tool_enabled=False)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            # Initially disabled
            assert not tool.is_enabled(), "Tool should be disabled initially"

            # Enable
            tool.enable()
            assert tool.is_enabled(), "Tool should be enabled after enable()"

            # Disable
            tool.disable()
            assert not tool.is_enabled(), "Tool should be disabled after disable()"

            print("   ✓ Enable/disable methods work correctly")
        finally:
            os.unlink(config_path)

        # Test 12: Get info method
        print("\n13. Testing get_info method...")
        config_path = create_test_config(index_dir, metadata_path,
                                          rag_enabled=True, tool_enabled=True)
        try:
            config = ConfigLoader(config_path)
            tool = CodebaseSearchTool(config)

            info = tool.get_info()
            assert "name" in info, "Info should have name"
            assert "enabled" in info, "Info should have enabled status"
            assert "rag_enabled" in info, "Info should have rag_enabled status"
            assert "top_k" in info, "Info should have top_k"
            assert "similarity_threshold" in info, "Info should have similarity_threshold"
            assert "max_code_length" in info, "Info should have max_code_length"
            assert "index_exists" in info, "Info should have index_exists"
            assert "index_path" in info, "Info should have index_path"

            print(f"   Tool name: {info['name']}")
            print(f"   Enabled: {info['enabled']}")
            print(f"   Index exists: {info['index_exists']}")
            print("   ✓ get_info method works correctly")
        finally:
            os.unlink(config_path)

    finally:
        # Clean up test index
        shutil.rmtree(index_dir)

    print("\n" + "=" * 80)
    print("✅ ALL CODEBASE SEARCH TOOL TESTS PASSED")
    print("=" * 80)


if __name__ == "__main__":
    main()
