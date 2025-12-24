# Meton Software Architecture Diagram

## High-Level System Architecture

```mermaid
graph TB
    subgraph "User Interface Layer"
        CLI[CLI Interface<br/>cli.py]
        Commands[Commands<br/>/model, /web, /index, etc.]
    end

    subgraph "Core Components"
        Agent[Agent System<br/>LangGraph ReAct]
        Models[Model Manager<br/>Ollama Integration]
        Config[Configuration<br/>Pydantic + YAML]
        Conv[Conversation Manager<br/>Thread-safe Storage]
    end

    subgraph "Tools Layer"
        FileOps[File Operations<br/>read/write/list]
        CodeExec[Code Executor<br/>subprocess isolation]
        WebSearch[Web Search<br/>DuckDuckGo]
        CodebaseSearch[Codebase Search<br/>RAG semantic search]
        SymbolLookup[Symbol Lookup<br/>AST-based definitions]
        ImportGraph[Import Graph<br/>dependency analysis]
    end

    subgraph "Skills Layer"
        CodeExplainer[Code Explainer<br/>intelligent explanations]
        Debugger[Debugger Assistant<br/>debug guidance]
        Refactoring[Refactoring Engine<br/>code improvements]
    end

    subgraph "RAG System"
        CodeParser[Code Parser<br/>AST extraction]
        Chunker[Code Chunker<br/>semantic chunks]
        Embeddings[Embedding Model<br/>sentence-transformers]
        VectorStore[Vector Store<br/>FAISS]
        MetadataStore[Metadata Store<br/>JSON]
        Indexer[Codebase Indexer<br/>orchestration]
    end

    subgraph "External Systems"
        Ollama[Ollama<br/>Local LLM Server]
        FileSystem[File System<br/>conversations, config]
    end

    %% User Interface connections
    CLI --> Agent
    Commands --> Config
    Commands --> Conv
    CLI --> Models

    %% Agent connections
    Agent --> Models
    Agent --> Config
    Agent --> FileOps
    Agent --> CodeExec
    Agent --> WebSearch
    Agent --> CodebaseSearch
    Agent --> SymbolLookup
    Agent --> ImportGraph

    %% Skills connections
    Agent -.-> CodeExplainer
    Agent -.-> Debugger
    Agent -.-> Refactoring
    CodeExplainer --> FileOps
    Debugger --> FileOps
    Debugger --> CodeExec
    Refactoring --> FileOps

    %% RAG connections
    Indexer --> CodeParser
    Indexer --> Chunker
    Indexer --> Embeddings
    Indexer --> VectorStore
    Indexer --> MetadataStore
    CodebaseSearch --> VectorStore
    CodebaseSearch --> MetadataStore
    CodebaseSearch --> Embeddings

    %% External connections
    Models --> Ollama
    Conv --> FileSystem
    Config --> FileSystem
    MetadataStore --> FileSystem

    %% Styling
    classDef coreClass fill:#4A90E2,stroke:#2E5C8A,color:#fff
    classDef toolClass fill:#50C878,stroke:#2E7D4E,color:#fff
    classDef skillClass fill:#9B59B6,stroke:#6C3483,color:#fff
    classDef ragClass fill:#E67E22,stroke:#A04000,color:#fff
    classDef externalClass fill:#95A5A6,stroke:#5D6D7E,color:#fff
    classDef uiClass fill:#F39C12,stroke:#B9770E,color:#fff

    class Agent,Models,Config,Conv coreClass
    class FileOps,CodeExec,WebSearch,CodebaseSearch,SymbolLookup,ImportGraph toolClass
    class CodeExplainer,Debugger,Refactoring skillClass
    class CodeParser,Chunker,Embeddings,VectorStore,MetadataStore,Indexer ragClass
    class Ollama,FileSystem externalClass
    class CLI,Commands uiClass
```

## Agent Execution Flow

```mermaid
sequenceDiagram
    participant User
    participant CLI
    participant Agent
    participant LLM
    participant Tools
    participant Skills

    User->>CLI: Query
    CLI->>Agent: run(query)

    loop ReAct Loop (max 10 iterations)
        Agent->>Agent: Build system prompt
        Agent->>LLM: Reasoning request
        LLM-->>Agent: THOUGHT + ACTION/ANSWER

        alt Has ACTION
            Agent->>Tools: Execute tool
            Tools-->>Agent: OBSERVATION
            Agent->>Agent: Check loop detection
        else Has ANSWER
            Agent->>Agent: Set finished=True
        end
    end

    Agent-->>CLI: Final answer
    CLI-->>User: Formatted response
```

## RAG Indexing Flow

```mermaid
flowchart LR
    Start[User: /index path] --> Walk[Walk Directory Tree]
    Walk --> Filter{Filter Files}
    Filter -->|.py files| Parse[AST Parse]
    Filter -->|Skip| Skip[__pycache__, .git, venv]

    Parse --> Extract[Extract Functions<br/>Classes, Imports]
    Extract --> Chunk[Create Semantic Chunks<br/>1 per function/class]
    Chunk --> Batch[Batch Chunks]
    Batch --> Embed[Generate Embeddings<br/>768-dim vectors]
    Embed --> Store[Store in FAISS<br/>IndexFlatL2]
    Store --> Meta[Save Metadata<br/>file:line mappings]
    Meta --> ConfigUpdate[Update config.yaml<br/>enable RAG]
    ConfigUpdate --> Done[Index Complete]
```

## RAG Query Flow

```mermaid
flowchart TD
    Query[Natural Language Query] --> Encode[Encode to 768-dim vector]
    Encode --> Search[FAISS k-NN search<br/>k=5, L2 distance]
    Search --> Results[Retrieve top-k vectors]
    Results --> Metadata[Load metadata<br/>file, line, code]
    Metadata --> Filter{Similarity > 0.3?}
    Filter -->|Yes| Format[Format results<br/>with context]
    Filter -->|No| Discard[Discard]
    Format --> Return[Return to Agent]
    Return --> LLM[Agent synthesizes answer]
```

## Component Interaction Layers

```mermaid
graph TD
    subgraph "Layer 1: Interface"
        L1[CLI + Commands]
    end

    subgraph "Layer 2: Orchestration"
        L2A[Agent System<br/>LangGraph]
        L2B[Model Manager]
        L2C[Configuration]
        L2D[Conversation]
    end

    subgraph "Layer 3: Execution"
        L3A[Tools<br/>6 tools]
        L3B[Skills<br/>3 skills]
    end

    subgraph "Layer 4: Infrastructure"
        L4A[RAG System<br/>5 components]
        L4B[Ollama LLM]
        L4C[File System]
    end

    L1 --> L2A
    L1 --> L2C
    L1 --> L2D
    L2A --> L2B
    L2A --> L3A
    L2A --> L3B
    L3A --> L4A
    L3A --> L4C
    L3B --> L4A
    L2B --> L4B
    L2C --> L4C
    L2D --> L4C
```

## Tool Dependency Graph

```mermaid
graph LR
    Agent((Agent))

    Agent -->|basic ops| FileOps[File Operations]
    Agent -->|execution| CodeExec[Code Executor]
    Agent -->|search web| WebSearch[Web Search]
    Agent -->|semantic search| CodebaseSearch[Codebase Search]
    Agent -->|find definitions| SymbolLookup[Symbol Lookup]
    Agent -->|analyze deps| ImportGraph[Import Graph]

    CodebaseSearch -->|uses| RAG[RAG System]
    SymbolLookup -->|uses| AST[AST Parser]
    ImportGraph -->|uses| Grimp[Grimp Library]

    FileOps -.->|required by| Skills[All Skills]
    CodeExec -.->|used by| Debugger[Debugger Skill]
```

## Configuration System

```mermaid
classDiagram
    class ConfigLoader {
        +load() Config
        +save() void
        +reload() Config
    }

    class Config {
        +ModelSettings models
        +ToolsConfig tools
        +ConversationConfig conversation
        +RAGConfig rag
        +List~ParameterProfile~ parameter_profiles
    }

    class ModelSettings {
        +str primary_model
        +str fallback_model
        +str quick_model
        +float temperature
        +int max_tokens
        +float top_p
        +int context_window
        ... 10 more params
    }

    class ToolsConfig {
        +FileOpsConfig file_operations
        +CodeExecutorConfig code_executor
        +WebSearchConfig web_search
        +CodebaseSearchConfig codebase_search
        +SymbolLookupConfig symbol_lookup
        +ImportGraphConfig import_graph
    }

    class RAGConfig {
        +bool enabled
        +str index_path
        +str embedding_model
        +int chunk_size
        +int top_k
        +float similarity_threshold
    }

    class ParameterProfile {
        +str name
        +str description
        +Dict settings
    }

    ConfigLoader --> Config
    Config --> ModelSettings
    Config --> ToolsConfig
    Config --> RAGConfig
    Config --> ParameterProfile
```

## State Management in Agent

```mermaid
stateDiagram-v2
    [*] --> START
    START --> ReasoningNode: Initialize state

    state ReasoningNode {
        [*] --> BuildPrompt
        BuildPrompt --> CallLLM
        CallLLM --> ParseOutput
        ParseOutput --> [*]
    }

    ReasoningNode --> CheckOutput: LLM response

    state CheckOutput <<choice>>
    CheckOutput --> ToolExecution: Has ACTION
    CheckOutput --> END: Has ANSWER
    CheckOutput --> END: Max iterations

    state ToolExecution {
        [*] --> LookupTool
        LookupTool --> ExecuteTool
        ExecuteTool --> CaptureResult
        CaptureResult --> [*]
    }

    ToolExecution --> LoopDetection: Tool result

    state LoopDetection <<choice>>
    LoopDetection --> END: Repeated call
    LoopDetection --> ReasoningNode: Continue

    END --> [*]
```

## Key Design Patterns

### 1. ReAct Pattern (Reasoning + Acting)

```text
THOUGHT → ACTION → OBSERVATION → THOUGHT → ... → ANSWER
```

### 2. Tool Pattern

```text
User Query → Agent → Tool Selection → Tool Execution → Result Integration
```

### 3. RAG Pattern

```text
Index: Code → Parse → Chunk → Embed → Store
Query: Question → Embed → Search → Retrieve → Synthesize
```

### 4. Loop Detection

```text
Track: (tool_name, input) pairs
Detect: If current == last, force completion
```

### 5. Configuration Persistence

```text
Runtime Change → Update Memory → Save to Disk → Reload on Restart
```

## Technology Stack

| Layer | Technologies |
|-------|-------------|
| **LLM** | Ollama (Qwen 2.5 32B, Llama 3.1 8B, Mistral) |
| **Agent Framework** | LangGraph (StateGraph, ReAct pattern) |
| **Embeddings** | sentence-transformers (all-mpnet-base-v2) |
| **Vector Store** | FAISS (IndexFlatL2) |
| **AST Parsing** | Python `ast` module |
| **Import Analysis** | grimp + NetworkX |
| **Web Search** | ddgs (DuckDuckGo) |
| **Config** | Pydantic + PyYAML |
| **CLI** | Rich (formatting and display) |
| **Storage** | JSON (conversations, metadata) |
| **Execution** | subprocess (isolated code execution) |

## Security Architecture

```mermaid
graph TD
    subgraph "Security Layers"
        A[Input Validation]
        B[Path Resolution]
        C[Subprocess Isolation]
        D[Import Validation]
        E[Local-Only Execution]
    end

    A -->|Pydantic schemas| B
    B -->|Blocked/allowed paths| C
    C -->|5s timeout| D
    D -->|AST whitelist| E
    E -->|No external APIs| Safe[Secure Execution]

    FileOps --> B
    CodeExec --> C
    CodeExec --> D
    All[All Components] --> E
```

## Performance Optimizations

1. **LLM Caching**: Models cached per-name to avoid recreation
2. **Lazy Loading**: RAG indexer loaded only when needed
3. **Batch Embeddings**: Process chunks in batches (32)
4. **Symbol Lookup Cache**: 60-second TTL for symbol index
5. **Conversation Trimming**: Auto-trim to max_history (20)
6. **Context Window**: 32K tokens for large file support
7. **FAISS**: Exact L2 distance (fast, no approximation)

## Extension Points

| Extension Type | Base Class | Location |
|---------------|------------|----------|
| **New Tool** | `MetonBaseTool` | `tools/base.py` |
| **New Skill** | `BaseSkill` | `skills/base.py` |
| **New Command** | N/A (function in CLI) | `cli.py` |
| **New Config** | `BaseModel` (Pydantic) | `core/config.py` |
| **New Model** | N/A (Ollama integration) | `core/models.py` |

## Data Flow Summary

```text
┌─────────────────────────────────────────────────────────────┐
│                         User Input                           │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    CLI Processing                            │
│  • Parse command/query                                       │
│  • Route to handler                                          │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    Agent System                              │
│  • Build system prompt (path + tools + examples)             │
│  • ReAct loop (max 10 iterations)                            │
│  • Loop detection                                            │
└────────────┬───────────────────────────┬────────────────────┘
             │                           │
             ▼                           ▼
┌─────────────────────────┐   ┌──────────────────────────────┐
│    Tool Execution       │   │    Skill Execution           │
│  • File operations      │   │  • Code explainer            │
│  • Code execution       │   │  • Debugger                  │
│  • Web search           │   │  • Refactoring               │
│  • Codebase search      │   │                              │
│  • Symbol lookup        │   │                              │
│  • Import analysis      │   │                              │
└────────────┬────────────┘   └──────────────┬───────────────┘
             │                               │
             │         ┌─────────────────────┘
             │         │
             ▼         ▼
┌─────────────────────────────────────────────────────────────┐
│                    LLM (via Ollama)                          │
│  • Generate reasoning                                        │
│  • Select actions                                            │
│  • Synthesize answers                                        │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                 Response Formatting                          │
│  • Rich console output                                       │
│  • Code highlighting                                         │
│  • Tables and panels                                         │
└────────────────────────┬────────────────────────────────────┘
                         │
                         ▼
┌─────────────────────────────────────────────────────────────┐
│                    User Output                               │
└─────────────────────────────────────────────────────────────┘
```

## File Reference Map

```text
Core System
├── meton.py ........................... Entry point
├── cli.py ............................. Main CLI interface
├── config.yaml ........................ Configuration
├── core/
│   ├── agent.py ....................... LangGraph ReAct agent
│   ├── config.py ...................... Pydantic configuration
│   ├── models.py ...................... Ollama model manager
│   └── conversation.py ................ Conversation manager

Tools & Skills
├── tools/
│   ├── base.py ........................ MetonBaseTool base class
│   ├── file_ops.py .................... File operations
│   ├── code_executor.py ............... Code execution
│   ├── web_search.py .................. Web search (ddgs)
│   ├── codebase_search.py ............. RAG semantic search
│   ├── symbol_lookup.py ............... AST symbol definitions
│   └── import_graph.py ................ Import dependency analysis
├── skills/
│   ├── base.py ........................ BaseSkill abstract class
│   ├── code_explainer.py .............. Code explanation
│   ├── debugger.py .................... Debug assistance
│   └── refactoring_engine.py .......... Code refactoring

RAG System
├── rag/
│   ├── code_parser.py ................. AST-based parsing
│   ├── chunker.py ..................... Semantic chunking
│   ├── embeddings.py .................. Sentence transformers
│   ├── vector_store.py ................ FAISS vector store
│   ├── metadata_store.py .............. JSON metadata storage
│   └── indexer.py ..................... Indexing orchestration

Utilities & Documentation
├── utils/
│   ├── logger.py ...................... Logging setup
│   ├── formatting.py .................. CLI formatting
│   └── prepare_training_data.py ....... Fine-tuning data prep
├── docs/
│   ├── ARCHITECTURE.md ................ Detailed architecture
│   ├── STATUS.md ...................... Development status
│   ├── QUICK_REFERENCE.md ............. Command cheat sheet
│   └── FINE_TUNING.md ................. Fine-tuning guide
└── templates/
    └── modelfiles/ .................... Ollama Modelfile templates
```
