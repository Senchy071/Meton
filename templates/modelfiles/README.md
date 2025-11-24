# Modelfile Templates for Meton

This directory contains Modelfile templates for creating custom Ollama models from fine-tuned GGUF files.

## Available Templates

### 1. basic.Modelfile
Minimal template for general-purpose fine-tuned models.

**Use for:**
- General coding assistance
- First-time fine-tuning experiments
- Balanced performance

**Parameters:** Conservative (temp=0.0, top_k=40)

### 2. python-specialist.Modelfile
Template for Python development specialists.

**Use for:**
- Python-heavy projects
- Type-hinted, documented code
- PEP 8 compliance
- Modern Python patterns

**Parameters:** Precise with good documentation (temp=0.1, repeat_penalty=1.15)

### 3. fastapi-expert.Modelfile
Template for FastAPI development.

**Use for:**
- REST API development
- Async/await patterns
- Pydantic models
- Authentication systems

**Parameters:** Precise for production code (temp=0.1, repeat_penalty=1.2)

### 4. langchain-expert.Modelfile
Template for LangChain/LangGraph development.

**Use for:**
- Agent development
- RAG systems
- Tool integration
- LangGraph workflows

**Parameters:** Methodical with Mirostat (temp=0.2, mirostat=2)

### 5. explainer.Modelfile
Template for code explanation and teaching.

**Use for:**
- Code reviews
- Documentation
- Teaching/learning
- Concept explanation

**Parameters:** Balanced for clarity (temp=0.5, repeat_penalty=1.25)

## Usage

### Step 1: Choose a Template

Select the template that matches your fine-tuning goal:

```bash
cp python-specialist.Modelfile my-custom.Modelfile
```

### Step 2: Customize

Edit the Modelfile:

```bash
nano my-custom.Modelfile
```

Update these fields:
- `FROM`: Path to your fine-tuned GGUF model
- `SYSTEM`: Customize the system prompt
- `PARAMETER`: Adjust parameters as needed

### Step 3: Create Ollama Model

```bash
ollama create my-model-name -f my-custom.Modelfile
```

### Step 4: Verify

```bash
# List models
ollama list

# Test model
ollama run my-model-name "Write a Python function"
```

### Step 5: Use in Meton

```bash
./meton.py
> /model my-model-name
> Your query here
```

Or set as primary in config.yaml:

```yaml
models:
  primary: my-model-name
```

## Customization Guide

### System Prompts

The SYSTEM section defines the model's behavior and expertise:

```
SYSTEM """
You are Meton, specialized in [YOUR DOMAIN].

Key behaviors:
- [Behavior 1]
- [Behavior 2]
- [Behavior 3]

When [TASK]:
1. [Step 1]
2. [Step 2]
3. [Step 3]
"""
```

**Tips:**
- Be specific about coding style
- Mention preferred libraries/frameworks
- Define response format expectations
- Include error handling approach

### Parameters

Adjust these based on your use case:

```
# Deterministic (production code)
PARAMETER temperature 0.0
PARAMETER repeat_penalty 1.1

# Balanced (general coding)
PARAMETER temperature 0.3
PARAMETER repeat_penalty 1.15

# Creative (prototyping)
PARAMETER temperature 0.7
PARAMETER repeat_penalty 1.2

# Debugging (methodical)
PARAMETER temperature 0.2
PARAMETER mirostat 2
PARAMETER mirostat_tau 4.0
```

See docs/USER_GUIDE.md for parameter descriptions.

### Template Formats

Different model families use different templates:

**Llama-2 style:**
```
TEMPLATE """
<s>[INST] {{ .Prompt }} [/INST]
{{ .Response }}</s>
"""
```

**ChatML style:**
```
TEMPLATE """
<|im_start|>user
{{ .Prompt }}<|im_end|>
<|im_start|>assistant
{{ .Response }}<|im_end|>
"""
```

**Alpaca style:**
```
TEMPLATE """
### Instruction:
{{ .Prompt }}

### Response:
{{ .Response }}
"""
```

Use the format that matches your base model.

## Advanced Customization

### Multi-Shot Examples

Include examples in system prompt:

```
SYSTEM """
You are Meton.

Example 1:
User: Create a FastAPI endpoint
Assistant: Here's a FastAPI endpoint with...

Example 2:
User: Add authentication
Assistant: I'll add OAuth2 authentication...
"""
```

### Longer Context

For large codebases:

```
PARAMETER num_ctx 32768  # 32K context
```

### Reproducible Outputs

For testing:

```
PARAMETER seed 42  # Fixed seed
PARAMETER temperature 0.0  # Deterministic
```

### Stop Sequences

Define custom stop tokens:

```
PARAMETER stop "<|end|>"
PARAMETER stop "```\n\n"
```

## Troubleshooting

### Model Not Loading

**Problem:** `Error: model not found`

**Solution:**
- Verify GGUF path in FROM directive
- Use absolute path: `FROM /full/path/to/model.gguf`
- Check file permissions

### Poor Quality Outputs

**Problem:** Model outputs are inconsistent or low quality

**Solution:**
- Review fine-tuning loss (should be < 1.0)
- Check training data quality
- Adjust temperature lower (0.0-0.2)
- Increase repeat_penalty (1.2-1.5)

### Model Too Slow

**Problem:** Inference takes too long

**Solution:**
- Use quantized model (Q4_K_M or Q5_K_M)
- Reduce num_ctx (4096 or 8192)
- Use smaller base model (7B instead of 34B)

### Wrong Response Format

**Problem:** Model uses wrong chat format

**Solution:**
- Verify TEMPLATE matches your base model
- Check training data format consistency
- Consult base model documentation

## Best Practices

1. **Version Your Models**
   ```bash
   ollama create meton-python-v1 -f Modelfile
   ollama create meton-python-v2 -f Modelfile  # After improvements
   ```

2. **Document Changes**
   Add comments to Modelfile:
   ```
   # Version: 1.0
   # Training data: conversations 2025-01-01 to 2025-01-15
   # Base model: codellama-13b-Q4_K_M
   # Training loss: 0.87
   ```

3. **Test Before Production**
   ```bash
   ollama run meton-test "Write a test query"
   # Verify quality before setting as primary
   ```

4. **Keep Base Model**
   Always maintain the original base model as fallback

5. **Iterate**
   Fine-tuning is iterative:
   - Start with small dataset
   - Test on real queries
   - Collect more data
   - Retrain with improvements

## Examples

### Creating a Python Specialist

```bash
# 1. Copy template
cp python-specialist.Modelfile meton-python.Modelfile

# 2. Edit (update FROM path)
nano meton-python.Modelfile

# 3. Create model
ollama create meton-python -f meton-python.Modelfile

# 4. Test
ollama run meton-python "Create a dataclass for User"

# 5. Use in Meton
./meton.py
> /model meton-python
```

### Creating a Custom Domain Expert

```bash
# 1. Start from basic template
cp basic.Modelfile meton-devops.Modelfile

# 2. Customize system prompt
nano meton-devops.Modelfile
# Update SYSTEM section for DevOps/Infrastructure

# 3. Adjust parameters
# Set temp=0.1 for precise scripts

# 4. Create and test
ollama create meton-devops -f meton-devops.Modelfile
ollama run meton-devops "Write a Dockerfile"
```

## Further Reading

- [Ollama Modelfile Documentation](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [Meton Fine-Tuning Guide](../docs/FINE_TUNING.md)
- [llama.cpp Documentation](https://github.com/ggerganov/llama.cpp)

## Contributing

Have a useful Modelfile template? Consider contributing:

1. Test thoroughly
2. Document use case
3. Include example system prompt
4. Suggest appropriate parameters
5. Submit via GitHub

---

*Templates are starting points - customize for your specific needs!*
