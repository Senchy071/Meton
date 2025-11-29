# Meton Privacy & Security

Complete privacy and security documentation for Meton.

---

## Privacy Guarantee

**Your code never leaves your machine** (with default configuration).

Meton is designed for **100% local execution** with zero external API calls in its default state.

---

## ⚠️ Important: True Offline Operation

While **Meton itself makes no external calls**, some Python libraries it depends on (HuggingFace, LangChain) may try to contact external servers for telemetry or update checks.

### The Issue

If you disconnect from the internet after initial setup, Meton may fail to start because:
- **HuggingFace Transformers**: Checks for model updates on import
- **LangChain/LangGraph**: May send telemetry data
- **Gradio** (Web UI only): Analytics and update checks

### The Solution

Use the provided offline launcher script:

```bash
./meton_offline.sh
```

This script disables all external calls by setting these environment variables:
- `HF_HUB_OFFLINE=1` - Forces HuggingFace offline mode
- `TRANSFORMERS_OFFLINE=1` - Disables transformer library updates
- `LANGCHAIN_TRACING_V2=false` - Disables LangChain telemetry
- `GRADIO_ANALYTICS_ENABLED=False` - Disables Gradio analytics

**After using this script, Meton will work completely offline** with no internet dependency.

### First-Time Setup Required

You need internet **once** to download:
1. Ollama models (`ollama pull qwen2.5-coder:32b`)
2. Sentence-transformers embedding model (auto-downloads on first use)
3. Python packages (`pip install -r requirements.txt`)

**After this one-time setup, you can disconnect from internet and use `./meton_offline.sh`**

---

## Component-by-Component Analysis

### ✅ 100% Local Components (Default)

#### 1. LLM Processing (Ollama)
- **What**: All AI model inference
- **Where**: Local Ollama server (`localhost:11434`)
- **Data Flow**: Your prompts → Local CPU/GPU → Responses
- **External Calls**: None
- **Models**: Stored in `~/.ollama/models/`

#### 2. Embeddings (sentence-transformers)
- **What**: Text to vector conversion for semantic search
- **Where**: Local CPU (forced CPU mode to avoid CUDA OOM)
- **Data Flow**: Code snippets → Local embedding model → 768-dim vectors
- **External Calls**:
  - ✅ First time only: Downloads model from HuggingFace (~420MB)
  - ❌ After download: Zero external calls
- **Model Cache**: `~/.cache/torch/sentence_transformers/`

#### 3. Vector Search (FAISS)
- **What**: Semantic code search
- **Where**: Local in-memory + disk storage
- **Data Flow**: Vectors stored in `rag_index/faiss.index`
- **External Calls**: None
- **Privacy**: All code embeddings stay local

#### 4. Code Analysis (RAG Pipeline)
- **What**: Parsing, chunking, indexing
- **Where**: 100% local Python code
- **Components**:
  - AST parsing (Python stdlib)
  - Semantic chunking (local logic)
  - Metadata storage (local JSON files)
- **External Calls**: None

#### 5. File Operations
- **What**: Read/write/list files
- **Where**: Local filesystem only
- **Security**: Path validation, blocked paths (`/etc`, `/sys`, `/proc`)
- **External Calls**: None

#### 6. Code Execution
- **What**: Python code execution in subprocess
- **Where**: Local subprocess isolation
- **Security**:
  - AST validation
  - Import allowlist/blocklist
  - 5-second timeout
- **External Calls**: None

#### 7. Data Storage
- **Conversations**: `conversations/` (local JSON)
- **Indexes**: `rag_index/` (local FAISS + JSON)
- **Memories**: `memory/` (local FAISS + JSON)
- **Logs**: `logs/` (local text files)
- **Analytics**: `analytics_data/` (local JSON)
- **All Storage**: 100% local filesystem

---

### 🌐 Optional External Component (Disabled by Default)

#### Web Search Tool

**Status**: Disabled by default

**Configuration**:
```yaml
tools:
  web_search:
    enabled: false  # ✅ Default
```

**When Enabled**:
- Makes HTTP requests to DuckDuckGo search API
- Sends your search queries (not your code) to DuckDuckGo
- Receives search results from the internet

**How to Enable** (if you need it):
```bash
# In Meton CLI:
> /web on

# Or edit config.yaml:
tools:
  web_search:
    enabled: true
```

**Privacy Impact**:
- ✅ Your **code** is never sent to DuckDuckGo
- ⚠️ Your **search queries** are sent to DuckDuckGo
- ⚠️ Your IP address is visible to DuckDuckGo

**When to Enable**:
- Looking up documentation
- Researching error messages
- Finding library versions
- General information gathering

**When to Keep Disabled** (default):
- Working with proprietary code
- Analyzing sensitive codebases
- Operating in air-gapped environments
- Privacy-critical work

---

## Data Flow Diagrams

### Default Configuration (100% Local)

```
┌─────────────┐
│  Your Code  │
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Meton (All Local)                  │
│                                     │
│  ┌─────────────┐  ┌──────────────┐│
│  │ Ollama LLM  │  │ Embeddings   ││
│  │ (localhost) │  │ (CPU-local)  ││
│  └─────────────┘  └──────────────┘│
│                                     │
│  ┌─────────────┐  ┌──────────────┐│
│  │ FAISS Index │  │ File Storage ││
│  │ (local)     │  │ (local disk) ││
│  └─────────────┘  └──────────────┘│
└─────────────────────────────────────┘
       │
       ▼
┌──────────────┐
│  Local Disk  │  (conversations/, rag_index/, memory/)
└──────────────┘

❌ NO INTERNET CONNECTION
```

### With Web Search Enabled (Optional)

```
┌─────────────┐
│  Your Code  │  ─────→  Stays Local ✅
└──────┬──────┘
       │
       ▼
┌─────────────────────────────────────┐
│  Meton                              │
│                                     │
│  [All local processing as above]   │
│                                     │
│  ┌──────────────┐                  │
│  │ Web Search   │  ────┐           │
│  │ (if enabled) │      │           │
│  └──────────────┘      │           │
└────────────────────────┼───────────┘
                         │
                         ▼
                  ┌─────────────┐
                  │ DuckDuckGo  │  ⚠️ Internet
                  │ (external)  │
                  └─────────────┘

⚠️ Only search queries go to internet
✅ Your code stays local
```

---

## Security Features

### 1. **Filesystem Security**
- Path validation prevents directory traversal
- Blocked paths: `/etc/`, `/sys/`, `/proc/`
- Allowed paths configurable in `config.yaml`
- Maximum file size limits (default 10MB)

### 2. **Code Execution Security**
- Subprocess isolation (not `eval()`)
- AST-based import validation
- Allowlist: 27 safe standard libraries
- Blocklist: 36 dangerous modules (os, sys, subprocess, etc.)
- 5-second timeout
- Output length limits

### 3. **Network Security**
- No network connections by default
- Web search explicitly opt-in only
- No telemetry or analytics sent externally
- No update checks to external servers

### 4. **Data Security**
- All data stored locally
- No cloud sync
- No external backups
- User controls all data

---

## Privacy Checklist

Use this checklist to ensure maximum privacy:

### Default Configuration (Recommended)
- [ ] Web search disabled: `tools.web_search.enabled: false`
- [ ] Ollama running locally: `ollama list` shows models
- [ ] No proxy/VPN required for Meton to work
- [ ] All data in local directories (`conversations/`, `rag_index/`, etc.)

### Air-Gapped/Offline Usage
- [ ] Web search disabled
- [ ] Sentence-transformers model already downloaded
- [ ] Ollama models already pulled
- [ ] No internet connection required

### Proprietary Code Analysis
- [ ] Web search disabled
- [ ] Verify no external monitoring tools
- [ ] Code stays in allowed paths only
- [ ] Regular backups to local storage

---

## Common Questions

### Q: Does Meton send telemetry?
**A**: No. Zero telemetry, analytics, or usage data is sent externally.

### Q: Does Meton check for updates?
**A**: No. No automatic update checks. Updates are manual via git pull.

### Q: Where are my conversations stored?
**A**: Locally in `conversations/` directory as JSON files.

### Q: Can I use Meton completely offline?
**A**: Yes! But requires initial setup:

**First-Time Setup (requires internet once):**
```bash
# 1. Download Ollama models
ollama pull qwen2.5-coder:32b
ollama pull llama3.1:8b

# 2. Pre-download sentence-transformers model
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('sentence-transformers/all-mpnet-base-v2')"

# 3. Install all Python packages
pip install -r requirements.txt
```

**After Setup - Run Offline:**
```bash
# Use the offline launcher script
./meton_offline.sh

# This sets environment variables:
# - HF_HUB_OFFLINE=1 (disable HuggingFace checks)
# - TRANSFORMERS_OFFLINE=1 (disable model updates)
# - LANGCHAIN_TRACING_V2=false (disable telemetry)
# - GRADIO_ANALYTICS_ENABLED=False (disable analytics)
```

**Manual offline mode (if script doesn't work):**
```bash
export HF_HUB_OFFLINE=1
export TRANSFORMERS_OFFLINE=1
export LANGCHAIN_TRACING_V2=false
python meton.py
```

### Q: What data does DuckDuckGo see (if I enable web search)?
**A**: Only your search queries and IP address. Never your code.

### Q: Can I delete all Meton data?
**A**: Yes. Simply delete:
- Project directory
- `~/.ollama/` (Ollama models)
- `~/.cache/torch/sentence_transformers/` (embeddings)

### Q: Does Meton work in corporate firewalls?
**A**: Yes, with web search disabled (default). No external connections needed.

### Q: What about the Python packages I install?
**A**: Standard packages (numpy, etc.) may make one-time external calls to download. After installation, all local.

---

## Audit & Verification

### Verify No External Calls

1. **Monitor Network Traffic**:
```bash
# On Linux:
sudo tcpdump -i any -n host not 127.0.0.1 and host not ::1

# Then run Meton and verify no traffic
python meton.py
```

2. **Check Web Search Status**:
```bash
python meton.py
> /web status

# Should show: ❌ Disabled
```

3. **Verify Ollama is Local**:
```bash
# Ollama runs on localhost
lsof -i :11434

# Should show ollama listening on 127.0.0.1
```

### Code Review

All source code is available for audit:
- `core/models.py` - Ollama integration (local only)
- `tools/web_search.py` - DuckDuckGo integration (disabled by default)
- `rag/embeddings.py` - sentence-transformers (local after download)

Search for external calls:
```bash
grep -r "http://" --include="*.py" | grep -v "localhost"
grep -r "https://" --include="*.py" | grep -v "localhost"
```

Should only find:
- Comments and documentation
- Web search tool (disabled by default)
- Test URLs

---

## Compliance & Regulations

### GDPR Compliance
- ✅ No personal data sent to external services (default)
- ✅ User has full control over data
- ✅ Data stored locally, user-deletable
- ✅ No profiling or tracking

### Corporate/Enterprise Use
- ✅ No data leakage to external services
- ✅ Works behind corporate firewalls
- ✅ No cloud dependencies
- ✅ Audit trail in local logs

### Air-Gapped Environments
- ✅ Works completely offline after setup
- ✅ No phone-home functionality
- ✅ Self-contained operation

---

## Recommendations

### Maximum Privacy Configuration

```yaml
# config.yaml
tools:
  web_search:
    enabled: false  # ✅ Keep disabled

  file_ops:
    allowed_paths:
      - /your/project/path  # ✅ Restrict to specific paths
    blocked_paths:
      - /etc/
      - /sys/
      - /proc/
      - /root/  # ✅ Add sensitive paths
```

### Security Best Practices

1. **Keep web search disabled** unless actively needed
2. **Restrict allowed_paths** to project directories only
3. **Regular backups** of local data (conversations/, memory/)
4. **Review logs** periodically: `logs/meton.log`
5. **Use separate Ollama models** for sensitive vs general work
6. **Monitor network** if working with highly sensitive code

---

## Contact & Issues

If you discover any privacy or security issues:
- Open an issue: https://github.com/Senchy071/Meton/issues
- Tag with `security` or `privacy`
- Do NOT include sensitive information in the report

---

**Bottom Line**: Meton is designed for complete privacy. With default settings, your code never leaves your machine. All AI processing happens locally on your hardware.

---

*Last Updated: 2025-11-24*
