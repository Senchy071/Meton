# How to Query Ingested Books in Meton

Quick reference for making Meton use your ingested books instead of listing files.

---

## ✅ DO THIS (Works)

### 1. Use `/csearch` Command Directly

```bash
> /csearch prompting techniques principles
> /csearch chain-of-thought examples
> /csearch few-shot learning patterns
> /csearch structured output JSON
```

**Why it works**: Directly invokes semantic search tool

---

### 2. Explicitly Mention "Indexed Book/Documents"

```bash
> According to the indexed book, what are the main prompting rules?
> Based on the indexed documents, explain chain-of-thought prompting
> The indexed prompting guide describes several techniques. List them.
> Search the indexed content for information about few-shot learning
```

**Why it works**: Keywords "indexed book/documents" trigger semantic search

---

### 3. Be Very Explicit About Using Search

```bash
> Use semantic search on the indexed documents to find the main prompting principles

> Search through the indexed book content and tell me about prompt patterns

> Query the indexed documents for information about structured outputs
```

**Why it works**: Explicitly instructs to use search

---

### 4. Reference "The Book"

```bash
> What does the book say about prompting techniques?
> The book mentions several patterns. What are they?
> According to the book, how should I structure prompts?
> Summarize chapter 3 from the book
```

**Why it works**: "The book" implies indexed content

---

## ❌ DON'T DO THIS (Doesn't Work)

### Generic Questions (Triggers File Listing)

```bash
❌ > List the main prompting rules
❌ > What are prompting techniques?
❌ > Tell me about few-shot learning
❌ > How do I write good prompts?
```

**Why it fails**: Too generic, agent doesn't know to search indexed content

---

## 🎯 Perfect Query Examples

### Example 1: Learning Techniques

```bash
# Step 1: Direct search
> /csearch prompting techniques patterns methods

# Step 2: Ask for summary
> Based on the search results above, summarize the main prompting techniques from the book
```

### Example 2: Finding Specific Content

```bash
> According to the indexed prompting book, what does it say about chain-of-thought reasoning? Include examples if mentioned.
```

### Example 3: Getting Lists

```bash
> Search the indexed documents and create a numbered list of all prompt engineering techniques mentioned in the book
```

### Example 4: Chapter-Specific

```bash
> /csearch chapter 3 advanced techniques

> Based on the indexed content, what are the key points from chapter 3?
```

### Example 5: Comparing Techniques

```bash
> The indexed book discusses multiple prompting patterns. Compare few-shot vs zero-shot prompting based on what the book says.
```

---

## 🔧 Troubleshooting

### Problem: Meton lists files instead of searching

**Solution**: Make your query more explicit:

```bash
Before: > What are the prompting rules?
After:  > According to the indexed book, what are the prompting rules?
```

### Problem: "I don't have information about the book"

**Solutions**:
1. Check indexing: `> /index status`
2. Re-index if needed: `> /index documents/`
3. Use `/csearch` directly: `> /csearch prompting techniques`

### Problem: Only getting partial information

**Solution**: Search first, then ask:

```bash
# Step 1: Search
> /csearch [your topic]

# Step 2: Ask for details
> Expand on the information about [specific point from results]
```

---

## 📋 Quick Reference

| Goal | Command |
|------|---------|
| Direct search | `/csearch your search terms` |
| Ask about book | `According to the indexed book, ...` |
| List techniques | `Search indexed docs and list all [topic]` |
| Find examples | `The book mentions [topic]. Show examples.` |
| Chapter content | `/csearch chapter X` then ask specifics |
| Compare concepts | `Based on indexed book, compare X vs Y` |

---

## 🚀 Workflow Template

```bash
# 1. Verify indexed
> /index status

# 2. Search for topic
> /csearch [your topic keywords]

# 3. Ask specific question based on results
> Based on the search results, [your question]

# 4. Get deeper details
> The book mentioned [specific point]. Explain that in more detail.
```

---

## 💡 Pro Tips

1. **Start with `/csearch`**: Most reliable way to search
2. **Use "indexed"**: Always mention "indexed book/documents"
3. **Be specific**: Include keywords from your book
4. **Chain queries**: Search first, then ask follow-up questions
5. **Reference results**: "Based on the above search results..."

---

## Examples for Prompting Books

```bash
# Get overview
> /csearch prompting techniques principles patterns
> According to the indexed book, what are the core prompting principles?

# Learn specific technique
> /csearch chain-of-thought reasoning step-by-step
> Explain chain-of-thought prompting based on the indexed book

# Get templates
> The book provides prompt templates. Search for and list them.

# Find best practices
> /csearch best practices mistakes avoid
> What prompting mistakes does the book warn about?

# Get examples
> Search the indexed book for examples of few-shot prompting

# Apply techniques
> Based on the book's structured output pattern, create a prompt for code review
```

---

**Remember**: Meton needs clear instructions to use semantic search instead of file operations. Always mention "indexed book/documents" or use `/csearch` directly!
