"""
TUI Configuration Management.

Manages user preferences for the Textual User Interface including
themes, keybindings, panel visibility, and AI feature settings.
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class TUIConfig(BaseModel):
    """Configuration for Clauxton TUI."""

    # Appearance
    theme: Literal["dark", "light", "high-contrast"] = Field(
        default="dark",
        description="Color theme for TUI",
    )
    show_status_bar: bool = Field(
        default=True,
        description="Show status bar at bottom",
    )
    show_kb_panel: bool = Field(
        default=True,
        description="Show Knowledge Base panel on left",
    )
    show_ai_panel: bool = Field(
        default=True,
        description="Show AI suggestions panel on right",
    )

    # AI Features
    enable_ai_suggestions: bool = Field(
        default=True,
        description="Enable real-time AI suggestions",
    )
    suggestion_refresh_interval: int = Field(
        default=30,
        description="AI suggestion refresh interval (seconds)",
        ge=10,
        le=300,
    )
    ai_confidence_threshold: float = Field(
        default=0.7,
        description="Minimum confidence for AI suggestions",
        ge=0.0,
        le=1.0,
    )

    # Search
    search_mode: Literal["semantic", "tfidf", "hybrid"] = Field(
        default="hybrid",
        description="Default search mode",
    )
    search_limit: int = Field(
        default=20,
        description="Number of search results per page",
        ge=5,
        le=100,
    )

    # Keyboard Navigation
    vim_mode: bool = Field(
        default=True,
        description="Enable vim-style navigation (hjkl)",
    )

    # Performance
    enable_animations: bool = Field(
        default=True,
        description="Enable UI animations and transitions",
    )
    lazy_loading: bool = Field(
        default=True,
        description="Enable lazy loading for large lists",
    )

    @classmethod
    def load(cls, config_path: Path) -> "TUIConfig":
        """
        Load configuration from YAML file.

        Args:
            config_path: Path to config file

        Returns:
            TUIConfig instance

        Raises:
            FileNotFoundError: If config file doesn't exist
            ValueError: If config is invalid
        """
        if not config_path.exists():
            # Return default config if file doesn't exist
            return cls()

        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}

        return cls(**data)

    def save(self, config_path: Path) -> None:
        """
        Save configuration to YAML file.

        Args:
            config_path: Path to config file
        """
        config_path.parent.mkdir(parents=True, exist_ok=True)

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(
                self.model_dump(),
                f,
                default_flow_style=False,
                sort_keys=False,
            )

    def toggle_theme(self) -> None:
        """Cycle through available themes."""
        themes: list[Literal["dark", "light", "high-contrast"]] = [
            "dark",
            "light",
            "high-contrast",
        ]
        current_index = themes.index(self.theme)
        self.theme = themes[(current_index + 1) % len(themes)]
