# Task 14: Codebase Indexer - COMPLETED ✅

## Overview
Built a complete codebase indexing system for Meton that parses Python files using AST, extracts functions/classes/modules, creates semantic embeddings, and stores them in FAISS for semantic code search.

## Components Created

### 1. rag/code_parser.py (377 lines)
AST-based Python file parser that extracts:
- **Functions**: name, signature, docstring, code, line numbers
- **Classes**: name, methods, bases, docstring, code, line numbers
- **Module docstrings**: top-level documentation
- **Imports**: all imported modules

**Features**:
- Handles syntax errors gracefully
- Encoding fallback (UTF-8 → latin-1)
- Extracts complete function signatures with type hints and defaults
- Recursively extracts class methods

### 2. rag/chunker.py (228 lines)
Code-aware chunking strategy that creates:
- **1 chunk per function** (signature + docstring + body)
- **1 chunk per class** (all methods included)
- **1 chunk for module docstring** (if exists)
- **1 chunk for imports section** (all imports)

**Chunk Metadata**:
```python
{
    "chunk_id": "uuid",
    "file_path": "/absolute/path",
    "chunk_type": "function|class|module|imports",
    "name": "element_name",
    "start_line": 10,
    "end_line": 25,
    "code": "source code",
    "docstring": "docstring or empty",
    "imports": ["list", "of", "imports"]
}
```

**Helper Methods**:
- `get_chunk_text()`: Creates embedding-optimized text representation
- `get_chunk_summary()`: Creates brief summary for display

### 3. rag/indexer.py (349 lines)
Main orchestrator that coordinates parsing, chunking, embedding, and storage.

**Core Methods**:
- `index_file(filepath)`: Index single Python file
- `index_directory(dirpath, recursive=True)`: Index entire directory
- `search(query, top_k=10)`: Semantic search for code chunks
- `save(path)` / `load(path)`: Persist index to disk
- `get_stats()`: Get indexing statistics

**Features**:
- Recursive directory walking with `os.walk()`
- Excludes: `__pycache__`, `.git`, `venv`, `env`, `node_modules`, etc.
- Skips empty `__init__.py` files
- Handles errors gracefully (continues indexing on failure)
- Batch embedding generation for efficiency
- Returns detailed statistics

## Test Coverage

### test_rag_code_parser.py (10 tests - ALL PASSED ✅)
1. ✅ Simple function with docstring
2. ✅ Class with multiple methods
3. ✅ Import extraction
4. ✅ Module docstring extraction
5. ✅ Syntax error handling
6. ✅ Complex function signatures (type hints, defaults, *args, **kwargs)
7. ✅ Class inheritance (base classes)
8. ✅ Empty file handling
9. ✅ Mixed content file
10. ✅ Encoding fallback (latin-1)

### test_rag_chunker.py (10 tests - ALL PASSED ✅)
1. ✅ Function chunk creation
2. ✅ Class chunk creation
3. ✅ Module docstring chunk
4. ✅ Imports chunk
5. ✅ Mixed content chunking (5 chunks from complex file)
6. ✅ Chunk text generation for embeddings
7. ✅ Chunk summary generation
8. ✅ Empty file handling
9. ✅ Chunk ID uniqueness (UUID)
10. ✅ Chunk metadata completeness

### test_rag_indexer.py (10 tests - ALL PASSED ✅)
1. ✅ Single file indexing (2 functions → 2 chunks)
2. ✅ Syntax error handling (logs error, continues)
3. ✅ Directory indexing (non-recursive)
4. ✅ Recursive directory indexing
5. ✅ Exclusion of `__pycache__` and `venv` directories
6. ✅ Skip empty `__init__.py` files
7. ✅ Statistics retrieval
8. ✅ Save and load index persistence
9. ✅ Search functionality (semantic similarity)
10. ✅ Complex file with mixed content (5 chunks)

## Test Results Summary
```
Code Parser:    10/10 tests passed ✅
Chunker:        10/10 tests passed ✅
Indexer:        10/10 tests passed ✅
------------------------------------
TOTAL:          30/30 tests passed (100% success rate)
```

## Success Criteria - All Met ✅
- ✅ Can parse Python files with AST
- ✅ Extracts functions with names, docstrings, code, line numbers
- ✅ Extracts classes with all methods
- ✅ Creates proper chunks (one per function/class)
- ✅ Generates embeddings for each chunk
- ✅ Stores in vector_store and metadata_store
- ✅ Can index entire directory recursively
- ✅ Handles errors gracefully
- ✅ Returns statistics (files processed, chunks created, errors)
- ✅ Skips excluded directories
- ✅ All tests pass

## Example Usage

```python
from rag.embeddings import EmbeddingModel
from rag.vector_store import VectorStore
from rag.metadata_store import MetadataStore
from rag.indexer import CodebaseIndexer

# Initialize components
embedder = EmbeddingModel()
vector_store = VectorStore(dimension=768)
metadata_store = MetadataStore("./rag_index/metadata.json")
indexer = CodebaseIndexer(embedder, vector_store, metadata_store, verbose=True)

# Index a directory
stats = indexer.index_directory("/path/to/project", recursive=True)
print(f"Indexed {stats['files_processed']} files, {stats['chunks_created']} chunks")

# Save the index
indexer.save("./rag_index/faiss.index")

# Search for code
results = indexer.search("user authentication", top_k=5)
for metadata, distance in results:
    print(f"{metadata['name']} in {metadata['file_path']} (distance: {distance:.4f})")
```

## Integration Notes

The indexer is now ready for integration with the Meton agent in Phase 2. Next steps:
1. Create semantic code search tool that wraps the indexer
2. Add index management commands to CLI (`/index`, `/search`)
3. Integrate with agent's tool set
4. Add automatic re-indexing on file changes (optional)

## Files Created
- `rag/code_parser.py` (377 lines)
- `rag/chunker.py` (228 lines)
- `rag/indexer.py` (349 lines)
- `test_rag_code_parser.py` (309 lines)
- `test_rag_chunker.py` (246 lines)
- `test_rag_indexer.py` (394 lines)

**Total**: 1,903 lines of production code and tests

## Performance Characteristics
- **Parsing**: Fast (AST-based, no regex)
- **Chunking**: O(n) where n = number of functions/classes
- **Embedding**: Batched for efficiency (processes multiple chunks at once)
- **Storage**: FAISS IndexFlatL2 (exact L2 distance search)
- **Exclusions**: Efficient (uses os.walk() in-place directory filtering)

---

**Status**: COMPLETE ✅
**Date**: 2025-11-03
**Test Pass Rate**: 100% (30/30 tests)
