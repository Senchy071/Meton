# Fine-Tuning Guide for Meton

This guide explains how to fine-tune language models for use with Meton using llama.cpp and LoRA (Low-Rank Adaptation).

---

## Overview

Fine-tuning allows you to specialize a base model for your specific coding patterns, domain knowledge, or preferred response style. Meton supports using fine-tuned models through Ollama.

**Workflow:**
1. Prepare training data (from conversations or custom datasets)
2. Fine-tune with llama.cpp using LoRA
3. Create Ollama model from fine-tuned GGUF
4. Use in Meton like any other model

**Benefits:**
- Models learn your coding style and preferences
- Better performance on domain-specific tasks
- Consistent responses aligned with your patterns
- No need for cloud API fine-tuning services

**Requirements:**
- llama.cpp installed and compiled
- Base model in GGUF format
- Training data in text format
- Sufficient disk space (~10-50GB depending on model size)

---

## Step 1: Prepare Training Data

### Training Data Format

llama.cpp expects training data in plain text format with examples separated by special tokens.

**Basic format:**
```
<s>[INST] User query or prompt [/INST] Desired response </s>
```

**For coding tasks:**
```
<s>[INST] Write a Python function to validate email addresses [/INST]
```python
import re

def validate_email(email: str) -> bool:
    """Validate email address format.

    Args:
        email: Email address to validate

    Returns:
        True if valid, False otherwise
    """
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))
```
</s>

<s>[INST] Explain this code [/INST] This function validates email addresses using a regular expression pattern... </s>
```

### Using Meton's Conversation History

Meton automatically saves conversations in `conversations/` directory. You can use these to create training data:

**Extract conversations:**
```bash
python utils/prepare_training_data.py \
    --conversations-dir ./conversations \
    --output training_data.txt \
    --min-quality 0.7 \
    --format llama
```

This utility (see utils/ directory) will:
- Parse all conversation JSON files
- Filter by quality/length
- Format for llama.cpp training
- Remove system messages
- Combine into single training file

### Custom Training Data

Create your own training data focusing on:

**1. Your Coding Style:**
```
<s>[INST] Create a REST API endpoint [/INST]
@app.route('/api/users', methods=['GET'])
def get_users():
    """Get all users with pagination."""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)

    users = User.query.paginate(page=page, per_page=per_page)
    return jsonify({
        'users': [u.to_dict() for u in users.items],
        'total': users.total,
        'page': page
    })
</s>
```

**2. Domain-Specific Knowledge:**
```
<s>[INST] How do I implement a ReAct agent in LangGraph? [/INST]
A ReAct agent in LangGraph uses a StateGraph with reasoning and action nodes:

```python
from langgraph.graph import StateGraph

def reasoning_node(state):
    # Agent thinks about what to do
    thought = llm.invoke(state["messages"])
    return {"thoughts": thought}

def action_node(state):
    # Execute tools based on reasoning
    result = execute_tool(state["thoughts"])
    return {"result": result}

graph = StateGraph(AgentState)
graph.add_node("reason", reasoning_node)
graph.add_node("act", action_node)
```
</s>
```

**3. Preferred Response Patterns:**
```
<s>[INST] Debug this code [/INST]
I'll analyze this systematically:

1. **Issue Identification:** The error occurs at line 42
2. **Root Cause:** Variable 'x' is undefined in this scope
3. **Fix:** Initialize x before the loop
4. **Verification:** Added test to prevent regression

Here's the corrected code:
```python
# Fixed version...
```
</s>
```

### Data Quality Guidelines

**Good training examples:**
- Clear, specific queries
- High-quality responses
- Diverse scenarios
- Realistic use cases
- Well-formatted code

**Avoid:**
- Ambiguous queries
- Incorrect code
- Very short exchanges
- Repetitive patterns
- Off-topic content

**Recommended dataset size:**
- Minimum: 100-200 examples
- Optimal: 500-1000 examples
- Large: 2000+ examples

---

## Step 2: Fine-Tune with llama.cpp

### Install llama.cpp

```bash
# Clone repository
git clone https://github.com/ggerganov/llama.cpp
cd llama.cpp

# Build
make

# Verify installation
./main --version
```

### Obtain Base Model

Download a GGUF model or convert from Hugging Face:

```bash
# Option 1: Download GGUF directly
wget https://huggingface.co/TheBloke/CodeLlama-7B-GGUF/resolve/main/codellama-7b.Q4_K_M.gguf

# Option 2: Convert from Hugging Face
python convert.py /path/to/huggingface/model
```

**Recommended base models for coding:**
- CodeLlama 7B/13B/34B
- DeepSeek Coder 6.7B/33B
- Qwen2.5-Coder 7B/14B/32B
- Llama 3.1 8B/70B

### Run Fine-Tuning

**Basic fine-tuning command:**
```bash
./finetune \
    --model-base codellama-7b.Q4_K_M.gguf \
    --lora-out meton-coding-lora.gguf \
    --train-data training_data.txt \
    --threads 8 \
    --ctx-size 2048 \
    --batch-size 8 \
    --epochs 3
```

**Advanced options:**
```bash
./finetune \
    --model-base codellama-7b.Q4_K_M.gguf \
    --lora-out meton-custom-lora.gguf \
    --train-data training_data.txt \
    --threads 16 \
    --ctx-size 4096 \
    --batch-size 16 \
    --epochs 5 \
    --learning-rate 1e-4 \
    --lora-rank 16 \
    --lora-alpha 32 \
    --sample-start "Below is an instruction"
```

**Parameter explanations:**
- `--model-base`: Base GGUF model file
- `--lora-out`: Output LoRA adapter filename
- `--train-data`: Your training data file
- `--threads`: CPU threads to use (more = faster)
- `--ctx-size`: Context window size
- `--batch-size`: Training batch size
- `--epochs`: Number of training passes
- `--learning-rate`: Fine-tuning learning rate (default: 1e-4)
- `--lora-rank`: LoRA rank (higher = more parameters, default: 8)
- `--lora-alpha`: LoRA scaling factor (default: 16)

**Typical training time:**
- 7B model, 500 examples, 8 threads: ~2-4 hours
- 13B model, 1000 examples, 16 threads: ~6-10 hours
- 34B model, 2000 examples, 32 threads: ~24-48 hours

### Monitor Training

llama.cpp outputs training loss during fine-tuning:

```
epoch 1/3
step 100/500 - loss: 2.345
step 200/500 - loss: 1.876
step 300/500 - loss: 1.432
...
```

**Good training indicators:**
- Loss consistently decreases
- Final loss < 1.0 for good quality
- No sudden spikes in loss

### Export Final Model

After fine-tuning, you have a LoRA adapter. Export it as a full model:

```bash
./export-lora \
    --model-base codellama-7b.Q4_K_M.gguf \
    --lora meton-coding-lora.gguf \
    --model-out meton-custom-7b.gguf
```

This creates a complete GGUF model with LoRA weights merged.

---

## Step 3: Create Ollama Model

### Create Modelfile

Create a `Modelfile` for your custom model:

**Basic Modelfile:**
```
FROM ./meton-custom-7b.gguf

# System prompt
SYSTEM """
You are Meton, a local AI coding assistant. You provide clear, well-formatted code with explanations.
"""

# Parameters
PARAMETER temperature 0.0
PARAMETER top_k 40
PARAMETER top_p 0.9
PARAMETER repeat_penalty 1.1

# Template
TEMPLATE """
{{ if .System }}<s>[INST] <<SYS>>
{{ .System }}
<</SYS>>

{{ end }}{{ if .Prompt }}{{ .Prompt }} [/INST]{{ end }}
{{ .Response }}</s>
"""
```

**Advanced Modelfile with custom parameters:**
```
FROM ./meton-custom-7b.gguf

SYSTEM """
You are Meton, specialized in Python development with FastAPI, LangChain, and modern async patterns.
You write type-hinted, well-documented code following PEP 8 standards.
"""

PARAMETER temperature 0.1
PARAMETER top_k 40
PARAMETER top_p 0.95
PARAMETER repeat_penalty 1.15
PARAMETER num_ctx 8192

TEMPLATE """
<s>[INST] {{ .Prompt }} [/INST]
{{ .Response }}</s>
"""
```

See `templates/modelfiles/` directory for more examples.

### Import to Ollama

```bash
# Create model in Ollama
ollama create meton-custom -f Modelfile

# Verify creation
ollama list
```

You should see your custom model listed.

### Test the Model

```bash
# Test with Ollama directly
ollama run meton-custom "Write a Python function to merge two sorted lists"

# Test in Meton
./meton.py
> /model meton-custom
> Write a function to validate JSON schema
```

---

## Step 4: Use in Meton

### Add to Configuration

Edit `config.yaml`:

```yaml
models:
  primary: meton-custom  # Your fine-tuned model
  fallback: qwen2.5-coder:32b
  quick: mistral:latest
```

Or use it temporarily:

```bash
/model meton-custom
```

### Evaluate Performance

Compare base vs fine-tuned model:

```bash
# Test with base model
/model codellama:7b
> Write a REST API endpoint for user authentication

# Test with fine-tuned model
/model meton-custom
> Write a REST API endpoint for user authentication
```

**Evaluation criteria:**
- Code quality and correctness
- Adherence to your style
- Completeness of response
- Appropriate use of libraries
- Documentation quality

---

## Fine-Tuning Strategies

### 1. Style Transfer

Train model to match your coding conventions:

**Training data focus:**
- Your actual project code
- Preferred patterns and idioms
- Naming conventions
- Documentation style

**Example use case:**
- You prefer FastAPI over Flask
- You always use type hints
- You follow specific error handling patterns

### 2. Domain Specialization

Specialize for specific frameworks or domains:

**Training data focus:**
- LangChain/LangGraph patterns
- React hooks and components
- DevOps/Infrastructure code
- Specific API documentation

**Example use case:**
- Building agents with LangChain
- Working with specific ML libraries
- Domain-specific terminology

### 3. Behavior Tuning

Adjust response style and format:

**Training data focus:**
- Preferred explanation style
- Code comment density
- Error handling approach
- Testing patterns

**Example use case:**
- Always include docstrings
- Explain reasoning before code
- Provide multiple approaches

### 4. Multi-Task Fine-Tuning

Combine multiple objectives:

**Training data focus:**
- Mix of coding styles
- Different frameworks
- Various explanation depths

**Example use case:**
- General-purpose coding assistant
- Multi-framework development
- Balanced versatility

---

## Troubleshooting

### Training Issues

**Problem: Loss not decreasing**
- Solution: Reduce learning rate, increase epochs, check data quality

**Problem: Loss decreases then spikes**
- Solution: Reduce learning rate, increase batch size, check for duplicate examples

**Problem: Out of memory**
- Solution: Reduce batch size, reduce context size, use smaller model

**Problem: Very slow training**
- Solution: Increase threads, reduce context size, use quantized model

### Model Quality Issues

**Problem: Model outputs gibberish**
- Solution: Training diverged - reduce learning rate, retrain with better data

**Problem: Model too conservative/repetitive**
- Solution: Adjust repeat_penalty, add more diverse examples

**Problem: Model ignores fine-tuning**
- Solution: Increase LoRA rank, train for more epochs, verify data format

**Problem: Model forgets general knowledge**
- Solution: Mix general examples with specialized ones, reduce epochs

### Ollama Integration Issues

**Problem: Ollama won't load model**
- Solution: Verify GGUF format, check file permissions, try smaller model

**Problem: Slow inference**
- Solution: Use quantized model, adjust num_ctx, enable GPU acceleration

**Problem: Incorrect output format**
- Solution: Fix TEMPLATE in Modelfile, verify prompt format

---

## Best Practices

### Training Data

1. **Quality over quantity** - 500 good examples > 5000 poor ones
2. **Diversity** - Cover different scenarios and edge cases
3. **Balance** - Don't over-represent specific patterns
4. **Validation** - Hold out 10-20% of data for testing
5. **Iteration** - Start small, evaluate, expand gradually

### Fine-Tuning Parameters

1. **Start conservative** - Low learning rate (1e-5), few epochs (3)
2. **Monitor loss** - Should steadily decrease without spikes
3. **Checkpoint** - Save checkpoints during long training runs
4. **Compare** - Always compare against base model
5. **Document** - Track what worked and what didn't

### Model Management

1. **Version control** - Name models with version/date: `meton-coding-v1-2025-01`
2. **Document changes** - Keep notes on training data and parameters used
3. **A/B testing** - Compare old vs new versions on test queries
4. **Backup** - Keep base models and LoRA adapters separately
5. **Iterate** - Fine-tuning is iterative - expect multiple attempts

### Production Use

1. **Gradual rollout** - Test thoroughly before making primary model
2. **Fallback** - Keep base model as fallback option
3. **Monitor** - Track response quality over time
4. **Refresh** - Periodically retrain with new conversation data
5. **Resource management** - Larger models need more RAM/VRAM

---

## Example: Complete Workflow

### Scenario: Fine-tune for Python/FastAPI development

**Step 1: Collect data**
```bash
# Export Meton conversations (30 days of FastAPI work)
python utils/prepare_training_data.py \
    --conversations-dir ./conversations \
    --output fastapi_training.txt \
    --filter-keyword "FastAPI" \
    --min-length 100 \
    --format llama

# Result: 450 examples, ~200KB
```

**Step 2: Add custom examples**
```bash
# Add 50 handcrafted examples for edge cases
cat custom_fastapi_examples.txt >> fastapi_training.txt

# Final: 500 examples
```

**Step 3: Fine-tune**
```bash
cd llama.cpp
./finetune \
    --model-base codellama-13b.Q4_K_M.gguf \
    --lora-out meton-fastapi-lora.gguf \
    --train-data ../fastapi_training.txt \
    --threads 16 \
    --batch-size 8 \
    --epochs 5 \
    --learning-rate 5e-5

# Training time: ~8 hours
# Final loss: 0.87
```

**Step 4: Export model**
```bash
./export-lora \
    --model-base codellama-13b.Q4_K_M.gguf \
    --lora meton-fastapi-lora.gguf \
    --model-out meton-fastapi-13b.gguf
```

**Step 5: Create Ollama model**
```bash
cat > Modelfile <<EOF
FROM ./meton-fastapi-13b.gguf
SYSTEM "You are a FastAPI expert assistant."
PARAMETER temperature 0.1
PARAMETER top_k 40
EOF

ollama create meton-fastapi -f Modelfile
```

**Step 6: Test and deploy**
```bash
# Test
./meton.py
> /model meton-fastapi
> Create a FastAPI endpoint with OAuth2 authentication

# If satisfied, update config.yaml
models:
  primary: meton-fastapi
```

**Step 7: Monitor and iterate**
```bash
# After 2 weeks, collect new conversations
# Add them to training data
# Retrain as meton-fastapi-v2
```

---

## Advanced Topics

### Continual Fine-Tuning

Start from previous fine-tuned model:

```bash
./finetune \
    --model-base meton-custom-v1.gguf \
    --lora-out meton-custom-v2-lora.gguf \
    --train-data new_examples.txt
```

### Multi-Dataset Training

Combine multiple datasets:

```bash
cat coding_patterns.txt \
    debugging_examples.txt \
    documentation_examples.txt \
    > combined_training.txt

./finetune --train-data combined_training.txt ...
```

### Quantization After Fine-Tuning

Reduce model size for faster inference:

```bash
./quantize meton-custom-7b.gguf meton-custom-7b.Q4_K_M.gguf Q4_K_M
```

### Parameter Sweeps

Find optimal hyperparameters:

```bash
for lr in 1e-5 5e-5 1e-4; do
  ./finetune \
    --model-base base.gguf \
    --lora-out lora-lr${lr}.gguf \
    --learning-rate ${lr} \
    --train-data data.txt
done
```

---

## Resources

### Documentation
- [llama.cpp GitHub](https://github.com/ggerganov/llama.cpp)
- [Ollama Documentation](https://github.com/ollama/ollama/blob/main/docs/modelfile.md)
- [LoRA Paper](https://arxiv.org/abs/2106.09685)

### Tools
- Meton's training data utilities: `utils/prepare_training_data.py`
- Modelfile templates: `templates/modelfiles/`
- Example datasets: `examples/training_data/`

### Community
- Share your fine-tuned model approaches
- Contribute training datasets (anonymized)
- Report issues and improvements

---

## Appendix: Training Data Preparation Utility

See `utils/prepare_training_data.py` for the complete utility.

**Basic usage:**
```bash
python utils/prepare_training_data.py \
    --conversations-dir ./conversations \
    --output training_data.txt
```

**With filters:**
```bash
python utils/prepare_training_data.py \
    --conversations-dir ./conversations \
    --output training_data.txt \
    --min-length 50 \
    --max-length 2000 \
    --filter-keyword "Python" \
    --exclude-system \
    --deduplicate
```

**Options:**
- `--conversations-dir`: Directory containing conversation JSON files
- `--output`: Output training data file
- `--format`: Output format (llama/alpaca/chat)
- `--min-length`: Minimum message length
- `--max-length`: Maximum message length
- `--filter-keyword`: Only include conversations mentioning keyword
- `--exclude-system`: Remove system messages
- `--deduplicate`: Remove duplicate exchanges
- `--quality-threshold`: Minimum quality score (0.0-1.0)

---

**Remember:** Fine-tuning is iterative. Start small, evaluate carefully, and refine based on real-world performance.
