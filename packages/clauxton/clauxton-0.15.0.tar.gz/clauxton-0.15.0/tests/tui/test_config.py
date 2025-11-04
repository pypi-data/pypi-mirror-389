"""Tests for TUI configuration (config.py)."""

from pathlib import Path

import pytest
import yaml

from clauxton.tui.config import TUIConfig


class TestTUIConfig:
    """Test suite for TUIConfig."""

    def test_default_config(self) -> None:
        """Test default configuration values."""
        config = TUIConfig()

        # Appearance
        assert config.theme == "dark"
        assert config.show_status_bar is True
        assert config.show_kb_panel is True
        assert config.show_ai_panel is True

        # AI Features
        assert config.enable_ai_suggestions is True
        assert config.suggestion_refresh_interval == 30
        assert config.ai_confidence_threshold == 0.7

        # Search
        assert config.search_mode == "hybrid"
        assert config.search_limit == 20

        # Keyboard
        assert config.vim_mode is True

        # Performance
        assert config.enable_animations is True
        assert config.lazy_loading is True

    def test_custom_config(self) -> None:
        """Test custom configuration values."""
        config = TUIConfig(
            theme="light",
            enable_ai_suggestions=False,
            suggestion_refresh_interval=60,
            ai_confidence_threshold=0.8,
            search_mode="semantic",
            vim_mode=False,
        )

        assert config.theme == "light"
        assert config.enable_ai_suggestions is False
        assert config.suggestion_refresh_interval == 60
        assert config.ai_confidence_threshold == 0.8
        assert config.search_mode == "semantic"
        assert config.vim_mode is False

    def test_config_validation_refresh_interval_min(self) -> None:
        """Test refresh interval minimum validation."""
        with pytest.raises(ValueError):
            TUIConfig(suggestion_refresh_interval=5)  # Less than 10

    def test_config_validation_refresh_interval_max(self) -> None:
        """Test refresh interval maximum validation."""
        with pytest.raises(ValueError):
            TUIConfig(suggestion_refresh_interval=500)  # More than 300

    def test_config_validation_confidence_min(self) -> None:
        """Test confidence threshold minimum validation."""
        with pytest.raises(ValueError):
            TUIConfig(ai_confidence_threshold=-0.1)  # Less than 0.0

    def test_config_validation_confidence_max(self) -> None:
        """Test confidence threshold maximum validation."""
        with pytest.raises(ValueError):
            TUIConfig(ai_confidence_threshold=1.5)  # More than 1.0

    def test_config_validation_search_limit_min(self) -> None:
        """Test search limit minimum validation."""
        with pytest.raises(ValueError):
            TUIConfig(search_limit=2)  # Less than 5

    def test_config_validation_search_limit_max(self) -> None:
        """Test search limit maximum validation."""
        with pytest.raises(ValueError):
            TUIConfig(search_limit=200)  # More than 100

    def test_config_save(self, tmp_path: Path) -> None:
        """Test saving configuration to file."""
        config_path = tmp_path / "tui.yml"
        config = TUIConfig(theme="light", vim_mode=False)

        config.save(config_path)

        assert config_path.exists()

        # Check file contents
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)

        assert data["theme"] == "light"
        assert data["vim_mode"] is False

    def test_config_load_existing(self, tmp_path: Path) -> None:
        """Test loading configuration from existing file."""
        config_path = tmp_path / "tui.yml"

        # Create config file
        config_data = {
            "theme": "high-contrast",
            "enable_ai_suggestions": False,
            "vim_mode": False,
        }

        with open(config_path, "w", encoding="utf-8") as f:
            yaml.safe_dump(config_data, f)

        # Load config
        config = TUIConfig.load(config_path)

        assert config.theme == "high-contrast"
        assert config.enable_ai_suggestions is False
        assert config.vim_mode is False

    def test_config_load_nonexistent_returns_default(self, tmp_path: Path) -> None:
        """Test loading non-existent config returns default."""
        config_path = tmp_path / "nonexistent.yml"

        config = TUIConfig.load(config_path)

        # Should return default config
        assert config.theme == "dark"
        assert config.vim_mode is True

    def test_config_toggle_theme(self) -> None:
        """Test theme toggle cycles correctly."""
        config = TUIConfig()

        # Start with dark
        assert config.theme == "dark"

        # Cycle through themes
        config.toggle_theme()
        assert config.theme == "light"

        config.toggle_theme()
        assert config.theme == "high-contrast"

        config.toggle_theme()
        assert config.theme == "dark"

    def test_config_save_creates_directory(self, tmp_path: Path) -> None:
        """Test save creates parent directories if needed."""
        config_path = tmp_path / "nested" / "dir" / "tui.yml"
        config = TUIConfig()

        config.save(config_path)

        assert config_path.exists()
        assert config_path.parent.exists()

    def test_config_roundtrip(self, tmp_path: Path) -> None:
        """Test config save and load roundtrip."""
        config_path = tmp_path / "tui.yml"

        # Create custom config
        original = TUIConfig(
            theme="light",
            show_status_bar=False,
            enable_ai_suggestions=False,
            suggestion_refresh_interval=60,
            ai_confidence_threshold=0.85,
            search_mode="semantic",
            search_limit=50,
            vim_mode=False,
            enable_animations=False,
            lazy_loading=False,
        )

        # Save and load
        original.save(config_path)
        loaded = TUIConfig.load(config_path)

        # Verify all fields match
        assert loaded.theme == original.theme
        assert loaded.show_status_bar == original.show_status_bar
        assert loaded.enable_ai_suggestions == original.enable_ai_suggestions
        assert loaded.suggestion_refresh_interval == original.suggestion_refresh_interval
        assert loaded.ai_confidence_threshold == original.ai_confidence_threshold
        assert loaded.search_mode == original.search_mode
        assert loaded.search_limit == original.search_limit
        assert loaded.vim_mode == original.vim_mode
        assert loaded.enable_animations == original.enable_animations
        assert loaded.lazy_loading == original.lazy_loading
