"""Configuration management for Meton.

Example usage:
    >>> from core.config import Config
    >>> config = Config()
    >>> print(config.models.primary)  # "codellama:34b"
    >>> print(config.agent.max_iterations)  # 10
    >>> config.reload()  # Reload from file
"""

import warnings
import yaml
from pathlib import Path
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field, field_validator, model_validator


class ModelSettings(BaseModel):
    """LLM model settings."""
    # Core sampling parameters
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)
    max_tokens: int = Field(default=2048, ge=1)
    top_p: float = Field(default=0.9, ge=0.0, le=1.0)
    num_ctx: int = Field(default=4096, ge=1)

    # Advanced sampling parameters
    top_k: int = Field(default=40, ge=0)  # 0 = disabled
    min_p: float = Field(default=0.1, ge=0.0, le=1.0)  # Adaptive filtering

    # Repetition control
    repeat_penalty: float = Field(default=1.1, ge=0.0, le=2.0)
    repeat_last_n: int = Field(default=64, ge=-1)  # -1 = ctx_size, 0 = disabled
    presence_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)
    frequency_penalty: float = Field(default=0.0, ge=-2.0, le=2.0)

    # Mirostat sampling (alternative to top_k/top_p)
    mirostat: int = Field(default=0, ge=0, le=2)  # 0 = disabled, 1 = Mirostat, 2 = Mirostat 2.0
    mirostat_tau: float = Field(default=5.0, ge=0.0)  # Target entropy
    mirostat_eta: float = Field(default=0.1, ge=0.0, le=1.0)  # Learning rate

    # Reproducibility
    seed: int = Field(default=-1, ge=-1)  # -1 = random


class ParameterPreset(BaseModel):
    """Parameter preset configuration."""
    name: str
    description: str
    settings: Dict[str, Any]


class ParameterProfile(BaseModel):
    """User-defined parameter profile configuration.

    Profiles are persistent user-created parameter configurations
    stored in config.yaml. Unlike presets (which are hardcoded),
    profiles can be created, modified, and deleted at runtime.
    """
    name: str
    description: str
    settings: Dict[str, Any]

    @field_validator('settings')
    @classmethod
    def validate_settings(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Validate that profile settings contain valid parameter names and values."""
        valid_params = {
            'temperature', 'max_tokens', 'top_p', 'num_ctx',
            'top_k', 'min_p', 'repeat_penalty', 'repeat_last_n',
            'presence_penalty', 'frequency_penalty', 'mirostat',
            'mirostat_tau', 'mirostat_eta', 'seed'
        }

        for key in v.keys():
            if key not in valid_params:
                raise ValueError(f"Invalid parameter name: {key}. Must be one of {valid_params}")

        return v


# Predefined parameter presets
PARAMETER_PRESETS = {
    "precise": ParameterPreset(
        name="precise",
        description="Deterministic output for precise coding tasks",
        settings={
            "temperature": 0.0,
            "top_k": 40,
            "min_p": 0.1,
            "repeat_penalty": 1.1,
            "mirostat": 0,
            "seed": -1,
        }
    ),
    "creative": ParameterPreset(
        name="creative",
        description="More exploratory and creative coding",
        settings={
            "temperature": 0.7,
            "top_p": 0.95,
            "min_p": 0.05,
            "repeat_penalty": 1.2,
            "mirostat": 0,
            "seed": -1,
        }
    ),
    "balanced": ParameterPreset(
        name="balanced",
        description="Balanced between creativity and precision",
        settings={
            "temperature": 0.3,
            "top_k": 40,
            "top_p": 0.9,
            "min_p": 0.1,
            "repeat_penalty": 1.15,
            "mirostat": 0,
            "seed": -1,
        }
    ),
    "debugging": ParameterPreset(
        name="debugging",
        description="Consistent methodical debugging approach",
        settings={
            "temperature": 0.2,
            "top_k": 20,
            "mirostat": 2,
            "mirostat_tau": 4.0,
            "mirostat_eta": 0.1,
            "repeat_penalty": 1.15,
            "seed": -1,
        }
    ),
    "explanation": ParameterPreset(
        name="explanation",
        description="Clear explanations with reduced repetition",
        settings={
            "temperature": 0.5,
            "top_p": 0.9,
            "repeat_penalty": 1.25,
            "presence_penalty": 0.1,
            "mirostat": 0,
            "seed": -1,
        }
    ),
}


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
                warnings.warn(f"Allowed path does not exist: {path_str}", UserWarning)
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


class MultiAgentConfig(BaseModel):
    """Multi-agent configuration."""
    enabled: bool = False
    max_subtasks: int = Field(default=10, ge=1)
    max_revisions: int = Field(default=2, ge=1)
    parallel_execution: bool = False


class ReflectionConfig(BaseModel):
    """Self-reflection configuration."""
    enabled: bool = False
    min_quality_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_iterations: int = Field(default=2, ge=1)
    auto_reflect_on: Dict[str, bool] = Field(default_factory=lambda: {
        "complex_queries": True,
        "multi_tool_usage": True,
        "long_responses": True
    })


class IterativeImprovementConfig(BaseModel):
    """Iterative improvement configuration."""
    enabled: bool = False
    max_iterations: int = Field(default=3, ge=1)
    quality_threshold: float = Field(default=0.85, ge=0.0, le=1.0)
    convergence_threshold: float = Field(default=0.05, ge=0.0, le=1.0)
    convergence_window: int = Field(default=2, ge=1)


class FeedbackLearningConfig(BaseModel):
    """Feedback learning configuration."""
    enabled: bool = True
    use_for_improvement: bool = False
    similarity_threshold: float = Field(default=0.7, ge=0.0, le=1.0)
    max_relevant_feedback: int = Field(default=5, ge=1)
    storage_path: str = "./feedback_data"


class ParallelExecutionConfig(BaseModel):
    """Parallel execution configuration (for tools)."""
    enabled: bool = False
    max_parallel_tools: int = Field(default=3, ge=1)
    timeout_per_tool: int = Field(default=30, ge=1)
    fallback_to_sequential: bool = True


class ChainOfThoughtConfig(BaseModel):
    """Chain-of-thought reasoning configuration."""
    enabled: bool = False
    min_complexity_threshold: str = "medium"
    include_in_response: bool = False
    max_reasoning_steps: int = Field(default=10, ge=1)


class TaskPlanningConfig(BaseModel):
    """Task planning configuration."""
    enabled: bool = False
    auto_plan_threshold: str = "medium"
    visualize_plan: bool = True
    allow_user_approval: bool = False
    max_subtasks: int = Field(default=15, ge=1)


class WebUISessionsConfig(BaseModel):
    """Web UI sessions configuration."""
    storage_path: str = "./web_sessions"
    max_age_hours: int = Field(default=24, ge=1)
    auto_cleanup: bool = True


class WebUIAnalyticsConfig(BaseModel):
    """Web UI analytics configuration."""
    enabled: bool = True
    refresh_interval: int = Field(default=30, ge=1)
    max_chart_points: int = Field(default=50, ge=1)


class WebUIConfig(BaseModel):
    """Web UI configuration."""
    enabled: bool = True
    host: str = "127.0.0.1"
    port: int = Field(default=7860, ge=1, le=65535)
    share: bool = False
    auth: Optional[str] = None
    theme: str = "soft"
    max_file_size_mb: int = Field(default=10, ge=1)
    sessions: WebUISessionsConfig = Field(default_factory=WebUISessionsConfig)
    analytics: WebUIAnalyticsConfig = Field(default_factory=WebUIAnalyticsConfig)


class AnalyticsConfig(BaseModel):
    """Analytics configuration."""
    enabled: bool = True
    storage_path: str = "./analytics_data"
    auto_export_interval: int = Field(default=100, ge=1)
    retention_days: int = Field(default=90, ge=1)


class LongTermMemoryConfig(BaseModel):
    """Long-term memory configuration."""
    enabled: bool = True
    storage_path: str = "./memory"
    max_memories: int = Field(default=10000, ge=1)
    consolidation_threshold: float = Field(default=0.95, ge=0.0, le=1.0)
    decay_rate: float = Field(default=0.1, ge=0.0, le=1.0)
    auto_consolidate: bool = True
    auto_decay: bool = True
    min_importance_for_retrieval: float = Field(default=0.3, ge=0.0, le=1.0)


class CrossSessionLearningConfig(BaseModel):
    """Cross-session learning configuration."""
    enabled: bool = True
    analysis_interval_hours: int = Field(default=24, ge=1)
    min_occurrences_for_pattern: int = Field(default=5, ge=1)
    min_confidence: float = Field(default=0.7, ge=0.0, le=1.0)
    auto_apply_insights: bool = False
    lookback_days: int = Field(default=30, ge=1)


class TemplatesConfig(BaseModel):
    """Templates configuration."""
    enabled: bool = True
    templates_dir: str = "templates/templates"
    default_author: Optional[str] = None
    default_email: Optional[str] = None
    auto_setup: bool = True


class ProfilesConfig(BaseModel):
    """Profiles configuration."""
    enabled: bool = True
    profiles_dir: str = "config/profiles"
    default_profile: Optional[str] = None
    auto_switch: bool = False


class ExportConfig(BaseModel):
    """Export/import configuration."""
    export_dir: str = "./exports"
    backup_dir: str = "./backups"


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
    multi_agent: MultiAgentConfig = Field(default_factory=MultiAgentConfig)
    reflection: ReflectionConfig = Field(default_factory=ReflectionConfig)
    iterative_improvement: IterativeImprovementConfig = Field(default_factory=IterativeImprovementConfig)
    feedback_learning: FeedbackLearningConfig = Field(default_factory=FeedbackLearningConfig)
    parallel_execution: ParallelExecutionConfig = Field(default_factory=ParallelExecutionConfig)
    chain_of_thought: ChainOfThoughtConfig = Field(default_factory=ChainOfThoughtConfig)
    task_planning: TaskPlanningConfig = Field(default_factory=TaskPlanningConfig)
    analytics: AnalyticsConfig = Field(default_factory=AnalyticsConfig)
    web_ui: WebUIConfig = Field(default_factory=WebUIConfig)
    long_term_memory: LongTermMemoryConfig = Field(default_factory=LongTermMemoryConfig)
    cross_session_learning: CrossSessionLearningConfig = Field(default_factory=CrossSessionLearningConfig)
    templates: TemplatesConfig = Field(default_factory=TemplatesConfig)
    profiles: ProfilesConfig = Field(default_factory=ProfilesConfig)
    export: ExportConfig = Field(default_factory=ExportConfig)
    optimization: OptimizationConfig = Field(default_factory=OptimizationConfig)
    parameter_profiles: Optional[Dict[str, ParameterProfile]] = Field(default_factory=dict)


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
