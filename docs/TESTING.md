# Meton Testing Guide

This guide covers how to test Meton using the comprehensive testing suite.

---

## Overview

Meton includes a comprehensive testing script (`test_meton_comprehensive.py`) that tests all major capabilities against real-world Python projects from GitHub.

### Test Coverage

The testing suite covers:
- ✅ **RAG Indexing** - Code parsing, chunking, embedding, storage
- ✅ **Semantic Search** - Natural language code search
- ✅ **Symbol Lookup** - Exact definition finding (functions, classes, methods)
- ✅ **Import Graph Analysis** - Dependency visualization, cycle detection, coupling metrics
- ✅ **Agent Scenarios** - End-to-end reasoning and tool usage
- ✅ **Skills** - Code explanation, debugging, review

### Test Projects

Three real-world Python projects are used for testing:

1. **FastAPI RealWorld Example** (~3-4K lines)
   - Production FastAPI application with authentication, CRUD operations
   - Tests: Architecture understanding, dependency analysis, symbol lookup

2. **HTTPie CLI** (~10-15K lines, 36K stars)
   - Popular command-line HTTP client
   - Tests: Large codebase handling, complex architecture analysis

3. **FastAPI Todo API** (~500-1K lines)
   - Simple REST API with basic CRUD
   - Tests: Quick indexing, code review, full analysis

---

## Quick Start

### Basic Testing (All Projects)

```bash
# Activate virtual environment
source venv/bin/activate

# Run all tests
python test_meton_comprehensive.py
```

This will:
1. Clone all test projects
2. Index each codebase with RAG
3. Test semantic search, symbol lookup, import graph
4. Run agent scenarios for each project
5. Generate comprehensive report

**Expected duration**: 10-20 minutes (depending on hardware)

### Quick Mode (Skip Large Projects)

```bash
# Test only small/medium projects (faster)
python test_meton_comprehensive.py --quick
```

**Expected duration**: 5-10 minutes

### Test Specific Projects

```bash
# Test only the small Todo API
python test_meton_comprehensive.py --projects fastapi_todo

# Test two projects
python test_meton_comprehensive.py --projects fastapi_todo,fastapi_realworld
```

---

## Command-Line Options

```bash
python test_meton_comprehensive.py [OPTIONS]

Options:
  --quick              Skip large projects (HTTPie)
  --projects LIST      Comma-separated project list
  --output FILE        Results JSON file (default: test_results.json)
  --cleanup            Delete test projects after testing
  -h, --help           Show help message
```

### Examples

```bash
# Quick test with cleanup
python test_meton_comprehensive.py --quick --cleanup

# Test with custom output file
python test_meton_comprehensive.py --output my_results.json

# Test specific project and cleanup
python test_meton_comprehensive.py --projects fastapi_todo --cleanup
```

---

## Understanding Test Results

### Console Output

The script provides real-time progress updates:

```
╔═══════════════════════════════════════════════════════════╗
║     METON COMPREHENSIVE TESTING SUITE                     ║
╚═══════════════════════════════════════════════════════════╝

Testing 3 projects:
  • FastAPI RealWorld Example (medium)
  • HTTPie CLI (large)
  • FastAPI Todo API (small)

============================================================
Testing: FastAPI RealWorld Example
Description: 3-4K lines, production FastAPI application
============================================================

📥 Cloning FastAPI RealWorld Example...
✓ FastAPI RealWorld Example cloned successfully
📇 Indexing FastAPI RealWorld Example...
✓ Indexed in 45.23s: 42 files, 387 chunks
  🔍 Testing semantic search: 'How does authentication work...'
  🎯 Testing symbol lookup: 'User'
  📊 Testing import graph analysis...
  🤖 Testing scenario: Architecture Understanding
  🤖 Testing scenario: Dependency Analysis
  ...
```

### Summary Report

After all tests complete, you'll see a summary:

```
============================================================
TEST SUMMARY
============================================================
Projects Tested:  3
Total Tests:      18
Passed:           16 ✓
Failed:           2 ✗
Pass Rate:        88.9%
Total Time:       487.34s
============================================================

PER-PROJECT RESULTS:

  FastAPI RealWorld Example:
    Indexing:        ✓ (45.23s)
      Files: 42, Chunks: 387
    Semantic Search  ✓ (2.31s)
    Symbol Lookup    ✓ (0.45s)
    Import Graph     ✓ (3.12s)
    Agent Scenarios:
      Architecture Understanding         ✓ (75% match, 12.34s)
      Dependency Analysis                ✓ (100% match, 8.92s)
      Symbol Lookup                      ✓ (80% match, 5.67s)
      Code Explanation                   ✓ (90% match, 15.23s)

  HTTPie CLI:
    ...
```

### Pass Rate Interpretation

- **90%+ pass rate**: 🎉 Excellent! Meton is performing very well
- **70-89% pass rate**: 👍 Good! Meton is working well with minor issues
- **50-69% pass rate**: ⚠️ Fair. Meton needs some improvements
- **<50% pass rate**: ❌ Poor performance. Significant work needed

### JSON Results

Detailed results are saved to `test_results.json` (or custom file):

```json
{
  "start_time": "2025-11-24T10:30:00",
  "end_time": "2025-11-24T10:38:07",
  "projects": {
    "fastapi_realworld": {
      "name": "FastAPI RealWorld Example",
      "description": "3-4K lines, production FastAPI application",
      "size": "medium",
      "tests": {
        "indexing": {
          "success": true,
          "elapsed_time": 45.23,
          "stats": {
            "files_indexed": 42,
            "chunks_created": 387
          }
        },
        "semantic_search": {
          "success": true,
          "elapsed_time": 2.31,
          "result_count": 5
        },
        ...
      }
    }
  },
  "summary": {
    "total_projects": 3,
    "total_tests": 18,
    "passed_tests": 16,
    "failed_tests": 2,
    "pass_rate": 88.9,
    "total_time": 487.34
  }
}
```

---

## Test Scenarios

### FastAPI RealWorld Example

1. **Architecture Understanding**
   - Query: "How does authentication work in this codebase?"
   - Tests: RAG search, symbol lookup integration
   - Success: Finding JWT, token handling, auth patterns

2. **Dependency Analysis**
   - Query: "Analyze import dependencies, find circular dependencies"
   - Tests: Import graph tool, cycle detection
   - Success: Generating graph, identifying modules

3. **Symbol Lookup**
   - Query: "Find the definition of the User model class"
   - Tests: Exact symbol finding
   - Success: Locating User class with line numbers

4. **Code Explanation**
   - Query: "Explain how article CRUD operations work"
   - Tests: Code explainer skill, semantic search
   - Success: Explaining create, read, update, delete flows

### HTTPie CLI

1. **Architecture Overview**
   - Query: "What is the overall architecture of HTTPie?"
   - Tests: Large codebase handling, import graph
   - Success: Understanding CLI structure, plugin system

2. **Complex Symbol Lookup**
   - Query: "Find the main CLI entry point function"
   - Tests: Symbol lookup in large codebase
   - Success: Locating main() with context

3. **Import Graph Analysis**
   - Query: "Analyze core modules, show coupling metrics"
   - Tests: Dependency analysis, metrics calculation
   - Success: Coupling density, fan-in/out metrics

### FastAPI Todo API

1. **Simple Architecture**
   - Query: "How is the todo API structured? What endpoints?"
   - Tests: Quick indexing, semantic search
   - Success: Finding routes, endpoints

2. **Full Analysis**
   - Query: "Analyze entire codebase structure and dependencies"
   - Tests: Complete codebase analysis
   - Success: Full import graph, module relationships

3. **Code Review**
   - Query: "Review main application for best practices"
   - Tests: Code reviewer skill
   - Success: Identifying security issues, improvements

---

## Troubleshooting

### Test Failures

#### "Failed to clone project"
**Cause**: Network issues or invalid repository URL

**Solution**:
```bash
# Manual clone
cd test_projects
git clone https://github.com/nsidnev/fastapi-realworld-example-app.git

# Retry test
cd ..
python test_meton_comprehensive.py --projects fastapi_realworld
```

#### "Indexing failed"
**Cause**: RAG system issues, missing dependencies

**Solution**:
```bash
# Check dependencies
pip install sentence-transformers faiss-cpu numpy scipy

# Verify Ollama is running
ollama list

# Check model
ollama pull qwen2.5-coder:32b
```

#### "Agent timeout"
**Cause**: Query too complex, model taking too long

**Solution**:
1. Check `config.yaml` - increase `agent.timeout` (default: 300s)
2. Use faster model: `qwen2.5-coder:14b` instead of 32b
3. Simplify query in test scenario

#### "Symbol not found"
**Cause**: Symbol doesn't exist or different name

**Solution**:
1. Manual check:
   ```bash
   cd test_projects/fastapi-realworld-example-app
   grep -r "class User" app/
   ```
2. Adjust test symbol in script if needed

#### Low Pass Rate (<70%)
**Causes**:
- Model quality issues (try different model)
- RAG indexing incomplete (check indexing stats)
- Success indicators too strict (review scenarios)

**Debugging**:
```bash
# Check detailed results
cat test_results.json | jq '.projects.fastapi_realworld.tests'

# Test individual components
python -c "
from tools.codebase_search import CodebaseSearchTool
tool = CodebaseSearchTool()
print(tool._run('authentication'))
"
```

---

## Manual Testing

If automated testing fails, you can test manually:

### 1. Start Meton CLI

```bash
source venv/bin/activate
python meton.py
```

### 2. Clone Test Project

```bash
cd test_projects
git clone https://github.com/Youngestdev/fastapi-todo.git
cd ..
```

### 3. Index Codebase

```bash
# In Meton CLI
> /index test_projects/fastapi-todo
```

### 4. Test Capabilities

```bash
# Semantic search
> /csearch todo endpoints

# Symbol lookup
> /find Todo

# Import graph
> Analyze the import dependencies in test_projects/fastapi-todo

# Ask questions
> How does the todo API work?
> What security issues are in the code?
> Generate tests for the create_todo function
```

---

## Performance Benchmarks

Expected performance on reference hardware (AMD Ryzen 9 7950X, 64GB RAM, RTX 3090):

| Operation | Small Project | Medium Project | Large Project |
|-----------|---------------|----------------|---------------|
| Clone | 5-10s | 10-20s | 30-60s |
| Index | 10-20s | 30-60s | 90-180s |
| Semantic Search | 1-2s | 2-3s | 3-5s |
| Symbol Lookup | 0.5-1s | 1-2s | 2-4s |
| Import Graph | 2-5s | 5-10s | 15-30s |
| Agent Scenario | 10-20s | 20-40s | 40-80s |
| **Total Test Time** | **2-4 min** | **5-8 min** | **10-15 min** |

Your results may vary based on:
- CPU/RAM (affects model inference speed)
- GPU (affects embedding generation)
- Disk I/O (affects indexing speed)
- Model size (32B vs 14B vs 7B)

---

## CI/CD Integration

The testing script returns exit codes for CI/CD:

- **Exit 0**: Pass rate ≥ 70% (success)
- **Exit 1**: Pass rate < 70% (failure)

### GitHub Actions Example

```yaml
name: Meton Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Setup Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -r requirements.txt
          curl -fsSL https://ollama.com/install.sh | sh
          ollama pull qwen2.5-coder:14b

      - name: Run tests
        run: python test_meton_comprehensive.py --quick --cleanup

      - name: Upload results
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test_results.json
```

---

## Custom Test Scenarios

You can add custom test scenarios by editing `test_meton_comprehensive.py`:

```python
# Add to TEST_SCENARIOS dictionary
TEST_SCENARIOS['my_project'] = [
    {
        'name': 'Custom Test',
        'query': 'Your query here',
        'expected_tools': ['codebase_search', 'symbol_lookup'],
        'success_indicators': ['keyword1', 'keyword2', 'keyword3']
    }
]

# Add to TEST_PROJECTS
TEST_PROJECTS['my_project'] = {
    'name': 'My Project',
    'url': 'https://github.com/user/repo.git',
    'dir': 'test_projects/my-project',
    'index_path': 'src',
    'size': 'medium',
    'description': 'My project description'
}
```

Then run:
```bash
python test_meton_comprehensive.py --projects my_project
```

---

## Cleanup

### Manual Cleanup

```bash
# Remove test projects
rm -rf test_projects/

# Remove results
rm test_results.json
```

### Automatic Cleanup

```bash
# Clean up after testing
python test_meton_comprehensive.py --cleanup
```

---

## Next Steps

After testing:

1. **Review Results**: Check `test_results.json` for detailed metrics
2. **Identify Issues**: Look at failed tests and error messages
3. **Tune Parameters**: Adjust `config.yaml` for better performance
4. **Try Different Models**: Test with various Ollama models
5. **Optimize**: Use profiling tools to find bottlenecks

See also:
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - Common issues and solutions
- [USER_GUIDE.md](USER_GUIDE.md) - Complete usage guide
- [API_REFERENCE.md](API_REFERENCE.md) - API documentation
- [DEVELOPMENT.md](DEVELOPMENT.md) - Contributing guide

---

**Happy Testing!** 🚀
