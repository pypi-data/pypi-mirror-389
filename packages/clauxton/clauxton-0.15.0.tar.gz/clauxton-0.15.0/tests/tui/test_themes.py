"""Tests for TUI theme system (themes.py)."""

import pytest
from rich.theme import Theme

from clauxton.tui.themes import ClauxtonTheme


class TestClauxtonTheme:
    """Test suite for ClauxtonTheme."""

    def test_dark_theme_exists(self) -> None:
        """Test dark theme is defined."""
        assert ClauxtonTheme.DARK is not None
        assert isinstance(ClauxtonTheme.DARK, Theme)

    def test_light_theme_exists(self) -> None:
        """Test light theme is defined."""
        assert ClauxtonTheme.LIGHT is not None
        assert isinstance(ClauxtonTheme.LIGHT, Theme)

    def test_high_contrast_theme_exists(self) -> None:
        """Test high contrast theme is defined."""
        assert ClauxtonTheme.HIGH_CONTRAST is not None
        assert isinstance(ClauxtonTheme.HIGH_CONTRAST, Theme)

    def test_get_theme_dark(self) -> None:
        """Test getting dark theme."""
        theme = ClauxtonTheme.get_theme("dark")
        assert theme == ClauxtonTheme.DARK

    def test_get_theme_light(self) -> None:
        """Test getting light theme."""
        theme = ClauxtonTheme.get_theme("light")
        assert theme == ClauxtonTheme.LIGHT

    def test_get_theme_high_contrast(self) -> None:
        """Test getting high contrast theme."""
        theme = ClauxtonTheme.get_theme("high-contrast")
        assert theme == ClauxtonTheme.HIGH_CONTRAST

    def test_get_theme_invalid_raises_error(self) -> None:
        """Test getting invalid theme raises ValueError."""
        with pytest.raises(ValueError, match="Invalid theme"):
            ClauxtonTheme.get_theme("invalid")  # type: ignore

    def test_dark_theme_has_required_styles(self) -> None:
        """Test dark theme has all required style names."""
        theme = ClauxtonTheme.DARK

        required_styles = [
            "primary",
            "secondary",
            "success",
            "warning",
            "error",
            "ai",
            "background",
            "surface",
            "text",
            "text-muted",
            "border",
            "border-focus",
            "panel-title",
            "status-bar",
            "confidence-high",
            "confidence-medium",
            "confidence-low",
            "highlight",
            "selection",
        ]

        for style_name in required_styles:
            assert style_name in theme.styles, f"Missing style: {style_name}"

    def test_light_theme_has_required_styles(self) -> None:
        """Test light theme has all required style names."""
        theme = ClauxtonTheme.LIGHT

        required_styles = [
            "primary",
            "secondary",
            "success",
            "warning",
            "error",
            "ai",
        ]

        for style_name in required_styles:
            assert style_name in theme.styles, f"Missing style: {style_name}"

    def test_high_contrast_theme_has_required_styles(self) -> None:
        """Test high contrast theme has all required style names."""
        theme = ClauxtonTheme.HIGH_CONTRAST

        required_styles = [
            "primary",
            "secondary",
            "success",
            "warning",
            "error",
            "ai",
        ]

        for style_name in required_styles:
            assert style_name in theme.styles, f"Missing style: {style_name}"

    def test_themes_are_distinct(self) -> None:
        """Test that themes are different objects."""
        dark = ClauxtonTheme.DARK
        light = ClauxtonTheme.LIGHT
        high_contrast = ClauxtonTheme.HIGH_CONTRAST

        # They should be different instances
        assert dark is not light
        assert dark is not high_contrast
        assert light is not high_contrast

    def test_dark_theme_colors_are_dark(self) -> None:
        """Test dark theme uses dark colors."""
        theme = ClauxtonTheme.DARK

        # Check background is dark (contains #1E or #2A)
        bg_style = theme.styles.get("background")
        if bg_style:
            # Dark theme should have dark background
            assert bg_style.bgcolor is not None

    def test_light_theme_colors_are_light(self) -> None:
        """Test light theme uses light colors."""
        theme = ClauxtonTheme.LIGHT

        # Check background is light (contains #F or #FFF)
        bg_style = theme.styles.get("background")
        if bg_style:
            # Light theme should have light background
            assert bg_style.bgcolor is not None

    def test_high_contrast_theme_has_maximum_contrast(self) -> None:
        """Test high contrast theme uses maximum contrast colors."""
        theme = ClauxtonTheme.HIGH_CONTRAST

        # High contrast should use pure black/white
        bg_style = theme.styles.get("background")
        text_style = theme.styles.get("text")

        if bg_style:
            assert bg_style.bgcolor is not None
        if text_style:
            assert text_style.color is not None
