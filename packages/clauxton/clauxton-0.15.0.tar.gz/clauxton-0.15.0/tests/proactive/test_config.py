"""Tests for configuration models."""

from pathlib import Path

import pytest

from clauxton.proactive.config import (
    ContextConfig,
    LearningConfig,
    MonitorConfig,
    SuggestionConfig,
    WatchConfig,
)


def test_watch_config_defaults() -> None:
    """Test WatchConfig default values."""
    config = WatchConfig()

    assert "*.pyc" in config.ignore_patterns
    assert ".git/**" in config.ignore_patterns
    assert config.debounce_ms == 500


def test_watch_config_custom() -> None:
    """Test WatchConfig with custom values."""
    config = WatchConfig(
        ignore_patterns=["*.log", "temp/**"],
        debounce_ms=1000,
    )

    assert config.ignore_patterns == ["*.log", "temp/**"]
    assert config.debounce_ms == 1000


def test_watch_config_validation() -> None:
    """Test WatchConfig validation."""
    # Debounce too low
    with pytest.raises(ValueError):
        WatchConfig(debounce_ms=50)

    # Debounce too high
    with pytest.raises(ValueError):
        WatchConfig(debounce_ms=10000)


def test_suggestion_config_defaults() -> None:
    """Test SuggestionConfig defaults."""
    config = SuggestionConfig()

    assert config.enabled is True
    assert config.min_confidence == 0.65
    assert config.max_per_context == 5
    assert config.notify_threshold == 3


def test_monitor_config_defaults() -> None:
    """Test MonitorConfig with all defaults."""
    config = MonitorConfig()

    assert config.enabled is True
    assert isinstance(config.watch, WatchConfig)
    assert isinstance(config.suggestions, SuggestionConfig)
    assert isinstance(config.learning, LearningConfig)
    assert isinstance(config.context, ContextConfig)


def test_monitor_config_save_load(tmp_path: Path) -> None:
    """Test saving and loading configuration."""
    config_path = tmp_path / "monitoring_config.yml"

    # Create custom config
    config = MonitorConfig(
        enabled=True,
        watch=WatchConfig(debounce_ms=1000),
        suggestions=SuggestionConfig(min_confidence=0.75),
    )

    # Save
    config.save_to_file(config_path)
    assert config_path.exists()

    # Load
    loaded = MonitorConfig.load_from_file(config_path)
    assert loaded.enabled is True
    assert loaded.watch.debounce_ms == 1000
    assert loaded.suggestions.min_confidence == 0.75


def test_monitor_config_load_nonexistent(tmp_path: Path) -> None:
    """Test loading from non-existent file returns defaults."""
    config_path = tmp_path / "nonexistent.yml"

    config = MonitorConfig.load_from_file(config_path)

    # Should return defaults
    assert config.enabled is True
    assert config.watch.debounce_ms == 500
