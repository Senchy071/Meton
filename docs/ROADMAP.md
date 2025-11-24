# Future Improvements for Meton

## Goal: Make Meton as close in abilities to online models as possible

This document outlines a comprehensive plan to enhance Meton's parameter control and fine-tuning capabilities while maintaining Ollama's advantages.

## Key Insight

**Ollama is built on top of llama.cpp** - it uses the same inference engine underneath but adds optimizations and convenience layers. This means:
- We already have llama.cpp's power
- Ollama exposes all advanced parameters - they just need to be added to our config
- Fine-tuning can be done offline with llama.cpp, then loaded into Ollama
- We keep model management simple without manually handling GGUF files

## Current State

**Currently exposed parameters** (core/models.py:266-276):
- `temperature`: 0.0
- `max_tokens`: 2048 (num_predict)
- `top_p`: 0.9
- `num_ctx`: 32768 (context window)

**Missing advanced parameters available in Ollama**:
- `top_k` - Sampling diversity control
- `min_p` - Adaptive token filtering (better than top_k)
- `repeat_penalty` - Penalize token repetition
- `repeat_last_n` - Window for repeat penalty
- `presence_penalty` - Penalize already-used tokens
- `frequency_penalty` - Penalize frequently-used tokens
- `mirostat` - Perplexity-based sampling (modes 0/1/2)
- `mirostat_tau` - Target entropy (default 5.0)
- `mirostat_eta` - Learning rate (default 0.1)
- `tfs_z` - Tail free sampling
- `typical_p` - Locally typical sampling
- `seed` - Reproducibility control

## Recommendation: Enhance Ollama, Don't Replace

### Why Stay with Ollama:
1. **You already have llama.cpp power** - Ollama uses it underneath
2. **Ollama exposes all these parameters** - They just need to be added to your config
3. **Fine-tuning is separate** - llama.cpp's LoRA fine-tuning can be done offline, then loaded into Ollama
4. **Model management stays simple** - No need to manually handle GGUF files

---

## Implementation Plan

### Phase 1: Expand Parameter Control (Quick wins)

**Add to config.yaml:**

```yaml
models:
  settings:
    # Current
    temperature: 0.0
    max_tokens: 2048
    top_p: 0.9
    num_ctx: 32768

    # Add these for better control
    top_k: 40              # Sampling diversity
    min_p: 0.1             # Adaptive filtering (recommended over top_k)
    repeat_penalty: 1.1    # Penalize repetition
    repeat_last_n: 64      # Window for penalties
    presence_penalty: 0.0  # Penalize already-used tokens
    frequency_penalty: 0.0 # Penalize frequent tokens

    # Mirostat (alternative sampling)
    mirostat: 0            # 0=disabled, 1=Mirostat, 2=Mirostat 2.0
    mirostat_tau: 5.0      # Target entropy
    mirostat_eta: 0.1      # Learning rate

    seed: -1               # -1=random, set for reproducibility
```

**Code Changes Needed:**
1. Update core/models.py:256-276 to include all parameters
2. Update config schema in core/config.py (Pydantic models)
3. Update core/models.py:525-531 (get_llm method) to pass new parameters

---

### Phase 2: Runtime Parameter Tuning (New CLI commands)

**New Commands:**

```bash
/param temperature 0.7    # Adjust single parameter
/param show               # Show all current parameters
/preset creative          # Load preset (creative/precise/balanced)
/param reset              # Reset to config defaults
```

**Code Changes Needed:**
1. Add CLI commands in cli.py
2. Add parameter validation and updating logic
3. Display current parameters in formatted table
4. Implement preset loading system

---

### Phase 3: Fine-Tuning Workflow (Advanced)

**Workflow:**

```bash
# Offline: Use llama.cpp to fine-tune with LoRA
./llama-finetune --model base.gguf --lora-out meton-tuned.gguf --train-data coding-data.txt

# Then: Create Ollama model from fine-tuned GGUF
ollama create meton-custom -f Modelfile

# Use in Meton
/model meton-custom
```

**Implementation:**
1. Document fine-tuning process in ARCHITECTURE.md
2. Create example training data formats
3. Add utilities for preparing training data from conversation history
4. Create Modelfile templates for common fine-tuning scenarios

---

### Phase 4: Parameter Profiles (UX enhancement)

**Add to config.yaml:**

```yaml
parameter_profiles:
  creative_coding:
    temperature: 0.7
    top_p: 0.95
    repeat_penalty: 1.2
    min_p: 0.05

  precise_coding:
    temperature: 0.0
    top_p: 0.9
    repeat_penalty: 1.1
    mirostat: 2
    mirostat_tau: 5.0

  debugging:
    temperature: 0.2
    mirostat: 2
    mirostat_tau: 4.0
    top_k: 20

  explanation:
    temperature: 0.5
    top_p: 0.9
    repeat_penalty: 1.15
    presence_penalty: 0.1
```

**Code Changes Needed:**
1. Add profile system to config.py
2. Add /profile command to cli.py
3. Allow runtime switching between profiles
4. Create default profiles based on task type

---

## Expected Benefits

✅ **Better output quality** - Fine-grained control over sampling
✅ **Reproducibility** - Seed parameter for consistent results
✅ **Less repetition** - Proper repeat penalty configuration
✅ **Adaptive quality** - Mirostat for consistent perplexity
✅ **Context-aware tuning** - Different settings for different tasks
✅ **Keeps Ollama's benefits** - Model management, performance optimizations

---

## Fine-Tuning Strategy

For domain-specific improvements:

1. **Collect coding data** - Your project's patterns, common tasks
2. **Use llama.cpp offline** - CPU-based LoRA fine-tuning
3. **Import to Ollama** - Create custom model from GGUF
4. **A/B test** - Compare base vs fine-tuned on your tasks

### Example Fine-Tuning Use Cases:
- Fine-tune on your coding style and patterns
- Train on common debugging scenarios
- Specialize for specific frameworks (LangChain, LangGraph, etc.)
- Optimize for code explanation quality
- Enhance refactoring suggestions

---

## Performance Considerations (2025 Data)

**Ollama Advantages:**
- 3x faster than raw llama.cpp in many scenarios
- Enhanced matrix multiplication algorithms
- Better memory management optimizations
- AMD GPU optimizations upstreamed in July 2025

**llama.cpp Improvements (we get via Ollama):**
- Multimodal support added (April 2025)
- New quantization levels (1.5-bit to 8-bit)
- AMD Instinct GPU wavefront size optimization (64 vs 32)
- Active development (85k+ GitHub stars, 4000+ releases)

---

## Implementation Priority

1. **Phase 1** (Highest priority) - Immediate quality improvements
2. **Phase 2** (High priority) - Better UX and experimentation
3. **Phase 4** (Medium priority) - Task-specific optimization
4. **Phase 3** (Lower priority) - Advanced customization

Start with Phase 1 for quickest impact, then iterate based on user feedback and usage patterns.

---

## References

- [Ollama Modelfile Documentation](https://docs.ollama.com/modelfile)
- [llama.cpp GitHub](https://github.com/ggml-org/llama.cpp)
- [Comprehensive Guide to LLM Sampling Parameters](https://smcleod.net/2025/04/comprehensive-guide-to-llm-sampling-parameters/)
- [llama-cpp-python Documentation](https://github.com/abetlen/llama-cpp-python)
