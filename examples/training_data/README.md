# Training Data Examples

This directory contains example training data files for fine-tuning language models with llama.cpp.

## Available Examples

### 1. python_coding_examples.txt

**Format:** Llama-2 instruction format (`<s>[INST] ... [/INST] ... </s>`)

**Content:**
- Python function implementations
- Best practices and modern patterns
- Type hints and documentation
- Async/await examples
- Decorators and context managers

**Use for:**
- Training Python coding assistants
- Learning proper code documentation
- Modern Python patterns (3.10+)

**Size:** 6 examples (~2KB)

### 2. code_explanation_examples.txt

**Format:** Llama-2 instruction format

**Content:**
- Detailed code explanations
- Python concept breakdowns
- Comparisons and analogies
- Common pitfalls and best practices
- Performance considerations

**Use for:**
- Training code explainers
- Teaching-focused models
- Documentation generators

**Size:** 4 examples (~3KB)

## Using These Examples

### 1. Review and Understand

Read through the examples to understand the format and style:

```bash
cat python_coding_examples.txt
```

### 2. Create Your Own

Use these as templates for your own training data:

```bash
# Copy an example
cp python_coding_examples.txt my_examples.txt

# Edit to add your examples
nano my_examples.txt
```

### 3. Combine Multiple Files

Merge different example types:

```bash
cat python_coding_examples.txt \
    code_explanation_examples.txt \
    > combined_training.txt
```

### 4. Add Meton Conversations

Use the utility to extract real conversations:

```bash
python ../../utils/prepare_training_data.py \
    --conversations-dir ../../conversations \
    --output meton_conversations.txt

# Combine with examples
cat combined_training.txt \
    meton_conversations.txt \
    > full_training_dataset.txt
```

### 5. Fine-Tune

Use with llama.cpp:

```bash
cd /path/to/llama.cpp

./finetune \
    --model-base codellama-7b.Q4_K_M.gguf \
    --lora-out custom-lora.gguf \
    --train-data /path/to/full_training_dataset.txt \
    --threads 8 \
    --epochs 3
```

## Format Explanation

### Llama-2 Instruction Format

```
<s>[INST] User instruction or query [/INST] Model response </s>

```

**Components:**
- `<s>` - Beginning of sequence token
- `[INST]` - Instruction start marker
- User query - The input prompt
- `[/INST]` - Instruction end / response start
- Model response - Desired output
- `</s>` - End of sequence token
- Empty line - Separates examples

**Example:**
```
<s>[INST] Write a hello world function [/INST]
```python
def hello_world():
    """Print hello world message."""
    print("Hello, World!")


# Usage
hello_world()
```
</s>

```

### Quality Guidelines

Good training examples have:

**1. Clear Instructions**
- Specific, actionable queries
- Realistic use cases
- Appropriate complexity

**2. High-Quality Responses**
- Correct, working code
- Proper formatting
- Helpful explanations
- Type hints and docstrings

**3. Diversity**
- Various difficulty levels
- Different use cases
- Multiple coding patterns
- Edge cases and best practices

**4. Consistency**
- Same format throughout
- Consistent style (PEP 8, etc.)
- Similar explanation depth
- Uniform documentation style

### Bad Examples to Avoid

**Too vague:**
```
<s>[INST] Write code [/INST] Here is some code </s>
```

**Incorrect code:**
```
<s>[INST] Sort a list [/INST]
list.sort()  # Wrong: missing context
</s>
```

**Too short:**
```
<s>[INST] Explain Python [/INST] It's a language </s>
```

**No explanation:**
```
<s>[INST] Why use type hints? [/INST]
def func(x: int) -> int:
    return x
</s>
```

## Creating Your Own Dataset

### Step 1: Define Your Domain

Choose a specific focus:
- **General Python** - Broad coverage
- **Web Development** - FastAPI, Flask, Django
- **Data Science** - Pandas, NumPy, scikit-learn
- **DevOps** - Docker, Kubernetes, CI/CD
- **ML/AI** - TensorFlow, PyTorch, LangChain

### Step 2: Collect Examples

Sources:
1. **Your own code** - Best practices from your projects
2. **Real questions** - From Stack Overflow, GitHub issues
3. **Documentation** - Official library docs
4. **Meton conversations** - Use the preparation utility

### Step 3: Format Consistently

```python
# Template
<s>[INST] {clear_instruction} [/INST]
```{language}
{well_formatted_code}
```

{helpful_explanation}
</s>

```

### Step 4: Organize by Category

```
examples/
├── basic_syntax.txt         # Variables, loops, functions
├── intermediate_patterns.txt # Decorators, context managers
├── advanced_concepts.txt    # Metaclasses, descriptors
├── framework_specific.txt   # FastAPI, Django, etc.
└── debugging_examples.txt   # Error handling, testing
```

### Step 5: Quality Control

Review each example:
- [ ] Code runs without errors
- [ ] Follows best practices
- [ ] Has clear explanations
- [ ] Uses modern Python
- [ ] Includes type hints
- [ ] Has proper documentation

### Step 6: Balance Dataset

Aim for:
- **100-200 examples** minimum
- **500-1000 examples** optimal
- **Mix of difficulty levels** (30% easy, 50% medium, 20% hard)
- **Diverse scenarios** (avoid repetition)
- **Real-world relevance** (practical use cases)

## Advanced Techniques

### Multi-Turn Conversations

For chat-like fine-tuning:

```
<s>[INST] How do I read a file in Python? [/INST]
You can use the `open()` function with a context manager:

```python
with open('file.txt', 'r') as f:
    content = f.read()
```

This ensures the file is properly closed even if an error occurs.
</s>

<s>[INST] What if I want to read line by line? [/INST]
You can iterate over the file object:

```python
with open('file.txt', 'r') as f:
    for line in f:
        print(line.strip())
```

Or use `readlines()` to get a list of all lines.
</s>
```

### Domain-Specific Vocabulary

Include terminology for your domain:

```
<s>[INST] Explain WSGI in Python web development [/INST]
WSGI (Web Server Gateway Interface) is a specification that describes how web servers communicate with Python web applications.

It acts as a universal interface between:
- **Web servers** (nginx, Apache)
- **Python frameworks** (Django, Flask)

Key components:
1. **Application callable** - Your Python code
2. **Server/Gateway** - Forwards requests
3. **Middleware** - Processing layers

Example WSGI application:
```python
def application(environ, start_response):
    status = '200 OK'
    headers = [('Content-Type', 'text/plain')]
    start_response(status, headers)
    return [b'Hello, WSGI!']
```
</s>
```

### Code Variations

Show multiple approaches:

```
<s>[INST] How to remove duplicates from a list? [/INST]
There are several approaches depending on your requirements:

**Method 1: Using set() (fastest, loses order)**
```python
unique_items = list(set(my_list))
```

**Method 2: Preserve order (Python 3.7+)**
```python
unique_items = list(dict.fromkeys(my_list))
```

**Method 3: List comprehension with tracking**
```python
seen = set()
unique_items = [x for x in my_list if not (x in seen or seen.add(x))]
```

**Method 4: Using itertools**
```python
from itertools import groupby

my_list.sort()
unique_items = [k for k, _ in groupby(my_list)]
```

Choose based on:
- Do you need to preserve order?
- Is the list sorted?
- Are items hashable?
- Performance requirements?
</s>
```

## Testing Your Dataset

Before fine-tuning:

### 1. Validate Format

```bash
# Check for format issues
python -c "
with open('training_data.txt') as f:
    content = f.read()
    # Should find pairs of <s> and </s>
    assert content.count('<s>') == content.count('</s>')
    assert '[INST]' in content
    assert '[/INST]' in content
    print('✓ Format looks good')
"
```

### 2. Check for Duplicates

```bash
# Simple duplicate detection
grep -o '<s>\[INST\].*\[/INST\]' training_data.txt | \
    sort | uniq -d
```

### 3. Review Sample

```bash
# View first few examples
head -n 50 training_data.txt
```

### 4. Size Check

```bash
# Dataset size
wc -l training_data.txt
du -h training_data.txt
```

## Recommended Workflow

1. Start with 50-100 hand-crafted examples
2. Test fine-tuning with small dataset
3. Evaluate model performance
4. Identify weak areas
5. Add 100-200 more targeted examples
6. Retrain and evaluate
7. Extract from Meton conversations
8. Expand to 500-1000 examples
9. Final training and deployment

## Resources

- **llama.cpp finetune docs:** https://github.com/ggerganov/llama.cpp/tree/master/examples/finetune
- **Meton fine-tuning guide:** `../../docs/FINE_TUNING.md`
- **Training data utility:** `../../utils/prepare_training_data.py`
- **Modelfile templates:** `../../templates/modelfiles/`

## Contributing

Have high-quality training examples? Consider contributing:

1. Ensure code is correct and well-documented
2. Follow the format guidelines
3. Include diverse, realistic examples
4. Test with fine-tuning
5. Submit with clear use case description

---

*Quality over quantity - 100 great examples beat 1000 mediocre ones!*
