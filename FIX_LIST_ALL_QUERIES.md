# Fix: "List All" Queries - Tool Selection & Format Issues

## Problem

When asking: **"What are all the prompting techniques mentioned in the book?"**

Meton exhibited multiple critical failures:

1. ❌ **Wrong Tool Selection**: Used `file_operations` to read entire 15,514-line file
2. ❌ **Tool Hallucination**: Invented "SEARCH_FILE_CONTENTS" tool (doesn't exist)
3. ❌ **Invalid JSON**: Used malformed input `"prompting techniques" in the book` instead of proper JSON
4. ❌ **Follow-up Failure**: Listed sections instead of techniques on second query

**Result**: Grade D+ (5/10) - Process failures, mediocre output, complete follow-up failure

```
❌ Agent pattern:
   file_operations (read 15,514 lines)
   → hallucinate "SEARCH_FILE_CONTENTS"
   → invalid JSON for codebase_search
   → eventually produce partial list
   → fail on follow-up
```

---

## Root Cause Analysis

### **Issue #1: Tool Selection Logic**

Agent thought: "I should read this file to extract all prompting techniques"
→ Used `file_operations` to read entire massive file
→ Should have used `codebase_search` with semantic search

**Why it failed**:
- No explicit rule for "list all X" type queries
- General "prioritize codebase_search" rule too vague
- No specific guidance against reading massive files for enumeration

---

### **Issue #2: Tool Hallucination Regression**

Despite previous fixes, agent still invented:
- "SEARCH_FILE_CONTENTS" (doesn't exist)
- "SEARCH_DOCUMENTS" (doesn't exist in earlier attempts)

**Why previous fix didn't work**:
- Rule was too general
- Not enough explicit forbidden examples
- No pre-action checklist
- No recovery guidance

---

### **Issue #3: JSON Format Errors**

Agent used invalid JSON:
```
❌ ACTION_INPUT: "prompting techniques" in the book
❌ ACTION_INPUT: prompting techniques
```

Should be:
```
✅ ACTION_INPUT: {"query": "prompting techniques"}
```

**Why it failed**:
- No explicit JSON format rules for tools
- No examples of common JSON mistakes
- No validation guidance

---

## Solution Implemented

### **1. Added "LIST ALL" Query Rules** (`core/agent.py:744-772`)

```
🚨 CRITICAL RULE - "LIST ALL" QUERIES MUST USE SEARCH, NOT FILE READ:

When user asks "What are ALL X", "List all Y", "Give me all Z":

ABSOLUTELY FORBIDDEN:
❌ NEVER use file_operations to read the entire file (especially if >1000 lines)
❌ NEVER read documents/prompt-eng.py (15,514 lines!)
❌ NEVER think "I should read this file to extract all X"

REQUIRED APPROACH:
✅ ALWAYS use codebase_search with a query about the items
✅ ALWAYS use PROPER JSON FORMAT: {"query": "your search terms"}
✅ Get snippets from multiple search results
✅ Synthesize complete list from snippets

Example WRONG pattern (DO NOT DO THIS):
  User: "What are all the prompting techniques?"
  ❌ WRONG: file_operations {"action": "read", "path": "documents/prompt-eng.py"}
  WHY WRONG: Reads 15,514 lines, overwhelms context

Example CORRECT pattern (DO THIS):
  User: "What are all the prompting techniques?"
  ✅ CORRECT: codebase_search {"query": "prompting techniques few-shot chain-of-thought"}
  WHY CORRECT: Returns 5-8 relevant snippets
  THEN: Extract ALL techniques from ALL snippets
```

**Impact**: Explicitly forbids reading massive files for enumeration queries

---

### **2. Strengthened Tool Hallucination Prevention** (`core/agent.py:944-981`)

```
⚠️ TOOL HALLUCINATION PREVENTION - ABSOLUTELY CRITICAL:

🚨 BEFORE EVERY ACTION, CHECK THIS LIST 🚨

The ONLY valid tools are:
[exact list of 6 tools]

That's it. No other tools exist. These are the ONLY 6 tools available.

FORBIDDEN TOOLS (these DON'T EXIST - NEVER use them):
❌ SEARCH_DOCUMENT_FOR_SECTIONS (doesn't exist!)
❌ SEARCH_FILE_CONTENTS (doesn't exist!)
❌ Extract (doesn't exist!)
❌ AnalyzeCode (doesn't exist!)
❌ FindPatterns (doesn't exist!)
❌ ParseJSON (doesn't exist!)
❌ SearchText (doesn't exist!)
❌ ReadDocument (doesn't exist!)

CORRECT TOOL MAPPING (use these instead):
• Want to search? → Use codebase_search
• Want to read file? → Use file_operations
• Want to run code? → Use code_executor
• Want web info? → Use web_search
• Want to find symbol? → Use symbol_lookup
• Want import graph? → Use import_graph

PRE-ACTION CHECK (do this BEFORE writing ACTION):
1. Look at the tool name you're about to use
2. Check if it's in the valid tools list above
3. If NO → Map it to a valid tool from the CORRECT TOOL MAPPING
4. If YES → Proceed with that tool
```

**Impact**:
- Explicit pre-action checklist
- 8 forbidden tool examples (not just 3)
- Clear mapping from intent to correct tool
- Recovery procedure for errors

---

### **3. Added JSON Format Rules** (`core/agent.py:830-863`)

```
🚨 TOOL INPUT JSON FORMAT - ABSOLUTELY CRITICAL:

ALL tools require VALID JSON format for ACTION_INPUT. Common mistakes:

❌ WRONG: codebase_search
          ACTION_INPUT: "prompting techniques" in the book
          ERROR: This is NOT valid JSON!

❌ WRONG: codebase_search
          ACTION_INPUT: prompting techniques
          ERROR: This is NOT valid JSON!

✅ CORRECT: codebase_search
            ACTION_INPUT: {"query": "prompting techniques"}
            SUCCESS: Proper JSON with required "query" field

CRITICAL JSON RULES:
1. ACTION_INPUT must ALWAYS be valid JSON
2. Use double braces {{}} in examples (gets unescaped to {})
3. Use double quotes " for strings, not single quotes '
4. Include ALL required fields for each tool
5. Check the tool's description at the top to see required format
```

**Impact**:
- Concrete examples of WRONG vs CORRECT JSON
- Explicit rules for JSON formatting
- References to tool descriptions for formats

---

## Expected Behavior After Fix

Query: **"What are all the prompting techniques mentioned in the book?"**

### **New Flow:**

```
1. ✅ Recognize "What are ALL X" pattern
2. ✅ Use codebase_search (not file_operations)
3. ✅ Proper JSON: {"query": "prompting techniques few-shot chain-of-thought"}
4. ✅ Get 5-8 relevant snippets about different techniques
5. ✅ Extract ALL techniques from ALL snippets (complete extraction)
6. ✅ Provide comprehensive list with descriptions
7. ✅ Complete in 2-3 iterations (not 4+ with errors)
```

**Expected Grade**: **A (9/10)** - Efficient, complete, accurate

---

## Improvements Summary

| Aspect | Before | After |
|--------|--------|-------|
| **Tool Selection** | file_operations (reads entire file) | codebase_search (gets snippets) |
| **Tool Existence Check** | Vague warning | Explicit pre-action checklist |
| **Forbidden Tools** | 3 examples | 8 examples with clear alternatives |
| **JSON Validation** | None | Explicit format rules with examples |
| **Efficiency** | 15,514 lines read | 5-8 snippets (~800 chars each) |
| **Error Rate** | 3 errors (hallucination, JSON, tool) | Expected: 0 errors |
| **Follow-up Handling** | Complete failure | Should maintain context |
| **Expected Grade** | D+ (5/10) | A (9/10) |

---

## Files Modified

1. **`core/agent.py`**:
   - Added "LIST ALL" query rules (lines 744-772)
   - Added JSON format rules (lines 830-863)
   - Strengthened tool hallucination prevention (lines 944-981)

2. **`FIX_LIST_ALL_QUERIES.md`** (this file):
   - Complete documentation of issues and fixes

---

## Testing

```bash
# Restart Meton to load new rules
python meton.py

# Test the exact query that failed before
> What are all the prompting techniques mentioned in the book? List each one with a brief description.
```

**Expected**:
1. Agent uses `codebase_search` with proper JSON
2. Gets multiple snippets about different techniques
3. Extracts ALL techniques from ALL snippets
4. Lists 10-15 techniques with accurate descriptions
5. No tool hallucination errors
6. No JSON format errors
7. Completes in 2-3 iterations

---

## Impact Analysis

### **Before These Fixes**:
- **Tool Selection**: Wrong (file_operations)
- **Efficiency**: Terrible (reads 15,514 lines)
- **Errors**: 3+ errors per query
- **Grade**: D+ (5/10)
- **User Experience**: Frustrating

### **After These Fixes**:
- **Tool Selection**: Correct (codebase_search)
- **Efficiency**: Excellent (5-8 small snippets)
- **Errors**: 0 expected
- **Grade**: A (9/10)
- **User Experience**: Smooth, fast, accurate

---

## Relation to Previous Fixes

This builds on two previous fixes:

1. **Recursion Limit Fix** (commit 630e6ad):
   - Don't read massive files after search
   - Use search result snippets
   - **This fix**: Use search in the FIRST PLACE

2. **Incomplete Extraction Fix** (commit f67895d):
   - Extract ALL items from snippets
   - Check multiple search results
   - **This fix**: Get those snippets correctly

**Combined Effect**:
- Fix #1: Don't read files after searching ✅
- Fix #2: Extract completely from snippets ✅
- **Fix #3**: Use search (not files) for "list all" ✅

**Pattern**: Search → Get snippets → Extract completely → Success

---

## Key Learnings

1. **Tool Selection Rules Must Come FIRST**: General guidance isn't enough - need explicit rules for specific query types

2. **Forbidden Examples Are Powerful**: Listing 8 forbidden tools is more effective than saying "don't hallucinate"

3. **Pre-Action Checklists Work**: Explicit step-by-step validation helps prevent errors

4. **JSON Format Needs Explicit Rules**: Showing WRONG vs CORRECT examples prevents common mistakes

5. **Specificity Beats Generality**: "Use codebase_search for enumeration" beats "prefer codebase_search generally"

---

## Success Metrics

Test the fix with these queries:

| Query | Expected Tool | Expected Result |
|-------|--------------|-----------------|
| "List all prompting techniques" | codebase_search | 10-15 techniques |
| "What are all the formats mentioned?" | codebase_search | 4 formats (Markdown, XML, YAML, JSON) |
| "Give me all the anti-patterns from the book" | codebase_search | 5+ anti-patterns |
| "Enumerate the evaluation methods" | codebase_search | 6+ methods |

**Success**: All use codebase_search, no file reads, no hallucinated tools, proper JSON, comprehensive answers

---

## Conclusion

The "list all X" query type requires special handling:
- ❌ Don't read entire files
- ✅ Use semantic search
- ✅ Validate tool existence
- ✅ Use proper JSON format
- ✅ Extract completely from snippets

With these fixes, Meton should reliably handle enumeration queries from indexed books, achieving A-level performance (9/10) instead of D+ (5/10).
