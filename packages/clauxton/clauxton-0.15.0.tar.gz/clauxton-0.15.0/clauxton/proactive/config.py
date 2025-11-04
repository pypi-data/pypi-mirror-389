"""Configuration models for proactive intelligence."""

from pathlib import Path
from typing import List

from pydantic import BaseModel, Field


class WatchConfig(BaseModel):
    """File watching configuration."""

    ignore_patterns: List[str] = Field(
        default=[
            "*.pyc",
            "*.pyo",
            "__pycache__/**",
            ".git/**",
            "node_modules/**",
            ".venv/**",
            "venv/**",
            "*.egg-info/**",
            ".mypy_cache/**",
            ".pytest_cache/**",
            ".coverage",
            "coverage.json",
            "*.log",
            "*.tmp",
            ".DS_Store",
            "Thumbs.db",
        ],
        description="Glob patterns to ignore",
    )

    debounce_ms: int = Field(
        default=500,
        ge=100,
        le=5000,
        description="Debounce interval in milliseconds",
    )

    max_queue_size: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Maximum number of events to keep in queue",
    )

    max_debounce_entries: int = Field(
        default=1000,
        ge=100,
        le=10000,
        description="Maximum debounce tracking entries before cleanup",
    )

    debounce_cleanup_hours: int = Field(
        default=1,
        ge=1,
        le=24,
        description="Remove debounce entries older than N hours",
    )


class SuggestionConfig(BaseModel):
    """Suggestion configuration."""

    enabled: bool = Field(default=True, description="Enable suggestions")
    min_confidence: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold",
    )
    max_per_context: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum suggestions per context",
    )
    notify_threshold: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Notify after N file changes",
    )


class LearningConfig(BaseModel):
    """Learning configuration."""

    enabled: bool = Field(default=True, description="Enable learning")
    update_frequency: str = Field(
        default="immediate",
        pattern="^(immediate|hourly|daily)$",
        description="Learning update frequency",
    )
    min_interactions: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Min interactions before personalizing",
    )


class ContextConfig(BaseModel):
    """Context tracking configuration."""

    track_sessions: bool = Field(default=True, description="Track work sessions")
    track_time_patterns: bool = Field(
        default=True, description="Track time-based patterns"
    )
    session_timeout_minutes: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Session timeout (no activity)",
    )


class MonitorConfig(BaseModel):
    """Complete monitoring configuration."""

    enabled: bool = Field(default=True, description="Enable monitoring")
    watch: WatchConfig = Field(default_factory=WatchConfig)
    suggestions: SuggestionConfig = Field(default_factory=SuggestionConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)

    @classmethod
    def load_from_file(cls, path: Path) -> "MonitorConfig":
        """Load configuration from YAML file."""
        from clauxton.utils.yaml_utils import read_yaml

        if not path.exists():
            return cls()

        data = read_yaml(path)
        return cls(**data.get("monitoring", {}))

    def save_to_file(self, path: Path) -> None:
        """Save configuration to YAML file."""
        from clauxton.utils.yaml_utils import write_yaml

        data = {"monitoring": self.model_dump()}
        write_yaml(path, data)
