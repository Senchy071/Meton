"""Configuration management for Meton.

Example usage:
    >>> from core.config import Config
    >>> config = Config()
    >>> print(config.models.primary)  # "codellama:34b"
    >>> print(config.agent.max_iterations)  # 10
    >>> config.reload()  # Reload from file
"""

import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ModelSettings(BaseModel):
    """LLM model settings."""
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    num_ctx: int = Field(default=4096, ge=1)


class ModelsConfig(BaseModel):
    """Models configuration."""
    primary: str = "codellama:34b"
    fallback: str = "codellama:13b"
    quick: str = "codellama:7b"
    settings: ModelSettings = Field(default_factory=ModelSettings)


class AgentConfig(BaseModel):
    """Agent configuration."""
    max_iterations: int = Field(default=10, ge=1)
    verbose: bool = True
    show_reasoning: bool = True
    timeout: int = Field(default=300, ge=1)


class FileOpsToolConfig(BaseModel):
    """File operations tool configuration."""
    enabled: bool = True
    allowed_paths: List[str] = Field(default_factory=list)
    blocked_paths: List[str] = Field(default_factory=list)
    max_file_size_mb: int = Field(default=10, ge=1)

    @model_validator(mode='after')
    def validate_paths(self) -> 'FileOpsToolConfig':
        """Validate that allowed paths exist and are directories."""
        for path_str in self.allowed_paths:
            path = Path(path_str)
            if not path.exists():
                print(f"Warning: Allowed path does not exist: {path_str}")
            elif not path.is_dir():
                raise ValueError(f"Allowed path is not a directory: {path_str}")
        return self


class CodeExecutorToolConfig(BaseModel):
    """Code executor tool configuration."""
    enabled: bool = True
    timeout: int = Field(default=5, ge=1)
    max_output_length: int = Field(default=10000, ge=100)


class WebSearchToolConfig(BaseModel):
    """Web search tool configuration."""
    enabled: bool = False  # DISABLED BY DEFAULT
    max_results: int = Field(default=5, ge=1, le=20)
    timeout: int = Field(default=10, ge=1)


class CodebaseSearchToolConfig(BaseModel):
    """Codebase search tool configuration."""
    enabled: bool = False  # DISABLED BY DEFAULT (enable after indexing)
    top_k: int = Field(default=5, ge=1, le=50)
    similarity_threshold: float = Field(default=0.3, ge=0.0, le=1.0)
    max_code_length: int = Field(default=500, ge=100, le=10000)


class ToolsConfig(BaseModel):
    """Tools configuration."""
    file_ops: FileOpsToolConfig = Field(default_factory=FileOpsToolConfig)
    code_executor: CodeExecutorToolConfig = Field(default_factory=CodeExecutorToolConfig)
    web_search: WebSearchToolConfig = Field(default_factory=WebSearchToolConfig)
    codebase_search: CodebaseSearchToolConfig = Field(default_factory=CodebaseSearchToolConfig)


class ConversationConfig(BaseModel):
    """Conversation configuration."""
    max_history: int = Field(default=20, ge=1)
    save_path: str = "./conversations/"
    auto_save: bool = True


class CLIConfig(BaseModel):
    """CLI configuration."""
    theme: str = "monokai"
    show_timestamps: bool = True
    syntax_highlight: bool = True
    show_tool_output: bool = True


class RAGConfig(BaseModel):
    """RAG (Retrieval-Augmented Generation) configuration."""
    enabled: bool = False
    embedding_model: str = "sentence-transformers/all-mpnet-base-v2"
    index_path: str = "./rag_index/"
    metadata_path: str = "./rag_index/metadata.json"
    dimensions: int = Field(default=768, ge=1)
    top_k: int = Field(default=10, ge=1, le=100)
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)


class SkillsConfig(BaseModel):
    """Skills configuration."""
    enabled: bool = True
    auto_load: bool = True
    directory: str = "./skills/"


class CacheConfig(BaseModel):
    """Cache configuration."""
    enabled: bool = True
    cache_dir: str = "./cache"
    ttl_seconds: int = 3600
    max_memory_items: int = 1000


class ProfilingConfig(BaseModel):
    """Profiling configuration."""
    enabled: bool = True
    auto_profile_queries: bool = True
    bottleneck_threshold_seconds: float = 5.0


class QueryOptimizationConfig(BaseModel):
    """Query optimization configuration."""
    enabled: bool = True
    auto_optimize_tools: bool = True
    auto_optimize_rag: bool = True


class ParallelConfig(BaseModel):
    """Parallel execution configuration."""
    enabled: bool = True
    max_workers: int = 3


class LazyLoadingConfig(BaseModel):
    """Lazy loading configuration."""
    enabled: bool = True
    preload_skills: List[str] = ["code_explainer"]


class ResourceMonitoringConfig(BaseModel):
    """Resource monitoring configuration."""
    enabled: bool = True
    sample_interval: int = 5
    alert_cpu_threshold: int = 90
    alert_memory_threshold: int = 90


class OptimizationConfig(BaseModel):
    """Optimization configuration."""
    enabled: bool = True
    cache: CacheConfig = Field(default_factory=CacheConfig)
    profiling: ProfilingConfig = Field(default_factory=ProfilingConfig)
    query_optimization: QueryOptimizationConfig = Field(default_factory=QueryOptimizationConfig)
    parallel: ParallelConfig = Field(default_factory=ParallelConfig)
    lazy_loading: LazyLoadingConfig = Field(default_factory=LazyLoadingConfig)
    resource_monitoring: ResourceMonitoringConfig = Field(default_factory=ResourceMonitoringConfig)


class ProjectConfig(BaseModel):
    """Project metadata."""
    name: str = "Meton"
    version: str = "0.1.0"
    description: str = "Local AI Coding Assistant"


class MetonConfig(BaseModel):
    """Main Meton configuration."""
    project: ProjectConfig = Field(default_factory=ProjectConfig)
    models: ModelsConfig = Field(default_factory=ModelsConfig)
    agent: AgentConfig = Field(default_factory=AgentConfig)
    tools: ToolsConfig = Field(default_factory=ToolsConfig)
    conversation: ConversationConfig = Field(default_factory=ConversationConfig)
    cli: CLIConfig = Field(default_factory=CLIConfig)
    rag: RAGConfig = Field(default_factory=RAGConfig)
    skills: SkillsConfig = Field(default_factory=SkillsConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)


class ConfigLoader:
    """Configuration loader and manager."""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize config loader.

        Args:
            config_path: Path to config YAML file
        """
        self.config_path = Path(config_path)
        self.config: MetonConfig = self._load_config()

    def _load_config(self) -> MetonConfig:
        """Load configuration from YAML file.

        Returns:
            Parsed configuration object
        """
        if not self.config_path.exists():
            raise FileNotFoundError(f"Config file not found: {self.config_path}")

        with open(self.config_path, 'r') as f:
            config_dict = yaml.safe_load(f)

        return MetonConfig(**config_dict)

    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value by dot-notation key.

        Args:
            key: Dot-notation key (e.g., 'models.primary')
            default: Default value if key not found

        Returns:
            Configuration value
        """
        parts = key.split('.')
        value = self.config

        for part in parts:
            if hasattr(value, part):
                value = getattr(value, part)
            else:
                return default

        return value

    def reload(self) -> None:
        """Reload configuration from file."""
        self.config = self._load_config()

    def save(self) -> None:
        """Save current configuration to file.

        This writes the in-memory config object back to the YAML file,
        preserving any runtime changes made during the session.
        """
        config_dict = self.to_dict()

        with open(self.config_path, 'w') as f:
            yaml.safe_dump(config_dict, f, default_flow_style=False, sort_keys=False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary.

        Returns:
            Configuration as dictionary
        """
        return self.config.model_dump()


# Simple alias for easier imports
Config = ConfigLoader
