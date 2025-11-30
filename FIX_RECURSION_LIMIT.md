# Fix: Agent Recursion Limit & Tool Hallucination

## Problem

When asking: "The book mentions structured formats. What formats are recommended?"

Meton would:
1. ✅ Successfully search with `codebase_search` and get relevant results
2. ❌ Read the entire 15,514-line file instead of using search results
3. ❌ Try to use a non-existent tool "SEARCH_DOCUMENT_FOR_SECTIONS"
4. ❌ Get stuck in a loop trying to fix the error
5. ❌ Hit recursion limit of 30 and fail

```
❌ Error: Recursion limit of 30 reached without hitting a stop condition.
```

## Root Causes

### 1. **No Guidance for Using Search Results**
The agent system prompt had examples for `codebase_search`, but no explicit rule about:
- Using search result snippets directly
- NOT reading entire files after getting good search results
- The code snippets in search results ARE the answer

### 2. **Tool Hallucination**
No explicit warning against inventing non-existent tools:
- Agent hallucinated "SEARCH_DOCUMENT_FOR_SECTIONS" tool
- No validation that tool names must match exactly from available list

### 3. **Low Iteration Limit for Complex Queries**
- `max_iterations: 10` → `recursion_limit: 30` (3 nodes per iteration)
- Complex queries with multiple search/read steps could hit this limit

## Solution

### 1. Added Codebase Search Usage Rules (`core/agent.py:834-849`)

```python
⚠️  CODEBASE_SEARCH RESULT USAGE - CRITICAL:
   - When codebase_search returns successful results with code snippets, ANSWER DIRECTLY from those snippets
   - DO NOT read the entire source file after getting search results - the snippets ARE the answer
   - Search results contain: file path, function/class name, line numbers, similarity score, code snippet
   - These code snippets are specifically selected as relevant to the query - use them directly
   - WRONG pattern: codebase_search → gets results → reads entire 15,000-line file → gets lost
   - CORRECT pattern: codebase_search → gets results with snippets → answers from snippets
   - Only read the full file if:
     1. Search results don't contain enough detail, OR
     2. User explicitly asks to read the file, OR
     3. You need to see context around the snippet
```

### 2. Added Tool Hallucination Prevention (`core/agent.py:851-860`)

```python
⚠️  TOOL HALLUCINATION PREVENTION - ABSOLUTELY CRITICAL:
   - ONLY use tools from this exact list: {list of available tools}
   - NEVER invent or hallucinate tools that don't exist
   - If you think you need a tool that's not in the list, use an existing tool instead
   - WRONG: Using "SEARCH_DOCUMENT_FOR_SECTIONS" (doesn't exist)
   - WRONG: Using "Extract" tool (doesn't exist)
   - WRONG: Using "AnalyzeCode" tool (doesn't exist)
   - CORRECT: Use file_operations for reading, codebase_search for searching, code_executor for running code
```

### 3. Increased Max Iterations (`config.yaml:25`)

```yaml
agent:
  max_iterations: 15  # Increased from 10 to handle complex queries
```

This gives recursion_limit of 45 (15 * 3), providing more buffer for complex queries.

## Expected Behavior After Fix

Query: "The book mentions structured formats. What formats are recommended?"

**New Flow**:
1. ✅ Call `codebase_search` with query "structured formats"
2. ✅ Receive results with code snippets from `documents/prompt-eng.py`
3. ✅ **Extract answer directly from search result snippets**
4. ✅ Provide answer: "XML, YAML, JSON, and Markdown are recommended..."
5. ✅ Complete in ~3-5 iterations (well under limit of 15)

**No more**:
- Reading entire 15,514-line files
- Hallucinating non-existent tools
- Hitting recursion limits

## Testing

```bash
# Test the fix
python meton.py

# Then ask:
> The book mentions structured formats. What formats are recommended?
```

**Expected**: Agent successfully answers with XML, YAML, JSON, Markdown recommendations from the indexed book, using search result snippets directly.

## Files Modified

1. `core/agent.py` - Added critical rules for search result usage and tool validation
2. `config.yaml` - Increased max_iterations from 10 to 15

## Impact

This fix improves:
- **Efficiency**: No more reading massive files unnecessarily
- **Reliability**: No more tool hallucination errors
- **Success Rate**: Higher iteration limit handles complex queries
- **User Experience**: Faster, more accurate responses to book-related queries

## Related Issues

This fix addresses the class of issues where:
- Agent finds correct information via search
- But then over-complicates by reading entire source files
- Gets overwhelmed with context and starts hallucinating
- Hits recursion limits trying to recover

**Pattern**: Search → Read massive file → Hallucinate → Loop → Fail
**Fixed Pattern**: Search → Use snippets → Answer → Success
