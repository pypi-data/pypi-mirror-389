"""
TUI Theme System.

Defines color schemes and styling for the Textual User Interface.
Supports dark, light, and high-contrast themes with WCAG 2.1 AA compliance.
"""

from typing import Literal

from rich.style import Style
from rich.theme import Theme


class ClauxtonTheme:
    """Color theme for Clauxton TUI."""

    # Dark Theme (Default)
    DARK = Theme(
        {
            # Primary colors
            "primary": Style(color="#4A9EFF", bold=True),
            "secondary": Style(color="#7B8FB5"),
            "success": Style(color="#4AFF88", bold=True),
            "warning": Style(color="#FFD24A", bold=True),
            "error": Style(color="#FF4A4A", bold=True),
            "ai": Style(color="#B84AFF", bold=True),
            # Background and text
            "background": Style(bgcolor="#1E1E2E"),
            "surface": Style(bgcolor="#2A2A3E"),
            "text": Style(color="#CDD6F4"),
            "text-muted": Style(color="#7B8FB5"),
            # UI Elements
            "border": Style(color="#3A3A4E"),
            "border-focus": Style(color="#4A9EFF", bold=True),
            "panel-title": Style(color="#4A9EFF", bold=True),
            "status-bar": Style(bgcolor="#2A2A3E", color="#CDD6F4"),
            # Confidence indicators
            "confidence-high": Style(color="#4AFF88"),
            "confidence-medium": Style(color="#FFD24A"),
            "confidence-low": Style(color="#FF4A4A"),
            # Special
            "highlight": Style(bgcolor="#3A3A4E", color="#FFD24A"),
            "selection": Style(bgcolor="#4A9EFF", color="#1E1E2E"),
        }
    )

    # Light Theme
    LIGHT = Theme(
        {
            # Primary colors
            "primary": Style(color="#0066CC", bold=True),
            "secondary": Style(color="#4A5568"),
            "success": Style(color="#00A36C", bold=True),
            "warning": Style(color="#FFA500", bold=True),
            "error": Style(color="#CC0000", bold=True),
            "ai": Style(color="#8B00FF", bold=True),
            # Background and text
            "background": Style(bgcolor="#FFFFFF"),
            "surface": Style(bgcolor="#F7F9FC"),
            "text": Style(color="#1A202C"),
            "text-muted": Style(color="#718096"),
            # UI Elements
            "border": Style(color="#CBD5E0"),
            "border-focus": Style(color="#0066CC", bold=True),
            "panel-title": Style(color="#0066CC", bold=True),
            "status-bar": Style(bgcolor="#F7F9FC", color="#1A202C"),
            # Confidence indicators
            "confidence-high": Style(color="#00A36C"),
            "confidence-medium": Style(color="#FFA500"),
            "confidence-low": Style(color="#CC0000"),
            # Special
            "highlight": Style(bgcolor="#FFF9E6", color="#FFA500"),
            "selection": Style(bgcolor="#0066CC", color="#FFFFFF"),
        }
    )

    # High Contrast Theme (Accessibility)
    HIGH_CONTRAST = Theme(
        {
            # Primary colors (enhanced contrast)
            "primary": Style(color="#00FFFF", bold=True),
            "secondary": Style(color="#AAAAAA"),
            "success": Style(color="#00FF00", bold=True),
            "warning": Style(color="#FFFF00", bold=True),
            "error": Style(color="#FF0000", bold=True),
            "ai": Style(color="#FF00FF", bold=True),
            # Background and text (maximum contrast)
            "background": Style(bgcolor="#000000"),
            "surface": Style(bgcolor="#1A1A1A"),
            "text": Style(color="#FFFFFF"),
            "text-muted": Style(color="#CCCCCC"),
            # UI Elements
            "border": Style(color="#FFFFFF"),
            "border-focus": Style(color="#00FFFF", bold=True),
            "panel-title": Style(color="#00FFFF", bold=True),
            "status-bar": Style(bgcolor="#1A1A1A", color="#FFFFFF"),
            # Confidence indicators
            "confidence-high": Style(color="#00FF00"),
            "confidence-medium": Style(color="#FFFF00"),
            "confidence-low": Style(color="#FF0000"),
            # Special
            "highlight": Style(bgcolor="#333333", color="#FFFF00"),
            "selection": Style(bgcolor="#00FFFF", color="#000000"),
        }
    )

    @classmethod
    def get_theme(cls, theme_name: Literal["dark", "light", "high-contrast"]) -> Theme:
        """
        Get theme by name.

        Args:
            theme_name: Theme name

        Returns:
            Rich Theme object

        Raises:
            ValueError: If theme name is invalid
        """
        themes = {
            "dark": cls.DARK,
            "light": cls.LIGHT,
            "high-contrast": cls.HIGH_CONTRAST,
        }

        if theme_name not in themes:
            raise ValueError(
                f"Invalid theme: {theme_name}. "
                f"Valid themes: {', '.join(themes.keys())}"
            )

        return themes[theme_name]


# CSS-like styles for Textual widgets
TUI_STYLES = """
/* Global styles */
Screen {
    background: $background;
}

/* Panel styles */
.panel {
    border: solid $border;
    background: $surface;
}

.panel:focus {
    border: solid $primary;
}

.panel-title {
    color: $primary;
    text-style: bold;
}

/* Button styles */
Button {
    background: $primary;
    color: $background;
    border: none;
    margin: 0 1;
}

Button:hover {
    background: $secondary;
}

Button:focus {
    border: solid $primary;
}

/* Input styles */
Input {
    border: solid $border;
    background: $surface;
    color: $text;
}

Input:focus {
    border: solid $primary;
}

/* Status bar */
.status-bar {
    background: $surface;
    color: $text;
    height: 1;
}

/* Confidence indicators */
.confidence-high {
    color: $success;
}

.confidence-medium {
    color: $warning;
}

.confidence-low {
    color: $error;
}

/* AI elements */
.ai-suggestion {
    border: solid $accent;
    background: $surface;
    padding: 1;
}

.ai-badge {
    color: $accent;
    text-style: bold;
}

/* Selection */
.selected {
    background: $primary;
}

.highlight {
    background: $boost;
}
"""
