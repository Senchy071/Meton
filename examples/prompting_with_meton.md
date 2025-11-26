# Using Meton to Write Prompts

This guide shows how to use Meton with a prompting book to generate high-quality prompts.

## Setup

### 1. Ingest Your Prompting Book

```bash
# Ingest book (supports .txt, .md, .pdf)
python ingest_document.py ~/path/to/prompting_book.pdf
```

### 2. Start Meton and Index

```bash
python meton.py
> /index documents/
```

## Example Prompts

### Request High-Quality Prompts

**Ask**:
```
> Based on the prompting book, write a prompt for [your task]
```

**Example Tasks**:
- "write a prompt for summarizing research papers"
- "create a prompt for code review"
- "design a prompt for creative writing"
- "build a prompt for data analysis"

### Learn from the Book

**Understand Techniques**:
```
> What are the key prompt engineering techniques in the book?
> Explain chain-of-thought prompting from the book
> What does the book say about few-shot learning?
```

### Apply Specific Patterns

**Use Book Patterns**:
```
> Using the structured output pattern from the book, create a prompt for analyzing customer feedback

> Apply the role-playing technique from chapter 3 to write a prompt for system design reviews

> The book mentions prompt templates. Create a template for technical documentation writing.
```

## Sample Workflow

### Scenario: Create a Code Documentation Prompt

```bash
> /index documents/

> I need to write a prompt that generates comprehensive Python docstrings. Based on the book's principles, what should this prompt include?

[Meton searches the book and provides guidance]

> Now write that prompt incorporating those principles

[Meton generates the complete prompt]

> Test this prompt on a sample function and show me the result
```

### Scenario: Build a Prompt Library

```bash
> Based on the book, create 5 different prompt templates for common software development tasks

> For each template, explain which prompting technique it uses

> Save these templates in a format I can reuse
```

## Tips

### 1. Reference Specific Chapters

```
> Using the techniques from chapter 5, write a prompt for...
> What does chapter 2 say about structured outputs?
```

### 2. Combine Multiple Techniques

```
> Create a prompt that combines:
  - Chain-of-thought reasoning
  - Structured JSON output
  - Role-playing as an expert
  Based on the book's guidance
```

### 3. Iterate and Improve

```
> Review this prompt I wrote: [your prompt]
> Compare it against the book's best practices
> Suggest improvements based on the book
```

### 4. Extract Patterns

```
> List all the prompt patterns mentioned in the book
> Create a cheat sheet of the top 10 prompting techniques
> What are the common mistakes the book warns about?
```

## Expected Results

With a good prompting book indexed, Meton can:

✅ **Generate prompts** following proven patterns
✅ **Explain techniques** from the book
✅ **Provide examples** matching the book's style
✅ **Critique prompts** against best practices
✅ **Adapt patterns** to your specific needs

## Example Outputs

### Before (without book):
```
User: Write a prompt for code review
Meton: "Review this code and tell me if it's good"
```

### After (with book indexed):
```
User: Based on the prompting book, write a prompt for code review
Meton:
"
You are a senior software engineer with 15 years of experience.

Review the following code using this framework:

1. **Security Analysis**
   - Identify vulnerabilities
   - Rate severity (Critical/High/Medium/Low)

2. **Performance Review**
   - Spot inefficiencies
   - Suggest optimizations

3. **Code Quality**
   - Check adherence to best practices
   - Evaluate readability and maintainability

4. **Testing Coverage**
   - Assess test completeness
   - Suggest additional test cases

Provide your analysis in this JSON format:
{
  \"overall_score\": 0-100,
  \"findings\": [...],
  \"recommendations\": [...]
}

Think step-by-step through each section.
"
```

## Common Use Cases

1. **Prompt Engineering Practice** - Learn techniques from the book
2. **Template Generation** - Create reusable prompt templates
3. **Quality Improvement** - Refine existing prompts
4. **Pattern Application** - Apply specific techniques to new tasks
5. **Documentation** - Extract and organize prompting knowledge

## Notes

- The more comprehensive your prompting book, the better Meton's outputs
- Meton combines book knowledge with its model's capabilities
- You can index multiple prompting resources for broader coverage
- Ask Meton to explain WHY a prompt is structured a certain way

---

**Start now**: Ingest your prompting book and unlock expert-level prompt writing!
