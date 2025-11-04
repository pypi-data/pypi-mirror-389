"""
Status Bar Widget.

Displays current mode, keyboard shortcuts, and connection status.
"""

from typing import Literal

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.widgets import Static


class StatusBar(Horizontal):
    """
    Status bar widget.

    Shows current mode, keyboard shortcuts, and system status.
    """

    DEFAULT_CSS = """
    StatusBar {
        dock: bottom;
        height: 1;
        background: $surface;
        color: $text;
    }

    StatusBar > .status-mode {
        width: 15;
        background: $primary;
        color: $background;
        content-align: center middle;
        text-style: bold;
    }

    StatusBar > .status-info {
        width: 1fr;
        padding: 0 2;
    }

    StatusBar > .status-shortcuts {
        width: auto;
        padding: 0 2;
        color: $text-muted;
    }
    """

    def __init__(self) -> None:
        """Initialize status bar."""
        super().__init__(id="statusbar")
        self.mode: Literal["NORMAL", "INSERT", "AI", "COMMAND"] = "NORMAL"
        self.info_text: str = "Ready"
        self.focus_widget: str = "KB Browser"

    def compose(self) -> ComposeResult:
        """Compose the status bar."""
        yield Static("NORMAL", classes="status-mode", id="status-mode")
        yield Static("Ready", classes="status-info", id="status-info")
        yield Static(
            "Ctrl+P: Commands | ?: Help | Q: Quit",
            classes="status-shortcuts",
            id="status-shortcuts",
        )

    def set_mode(self, mode: Literal["NORMAL", "INSERT", "AI", "COMMAND"]) -> None:
        """
        Set current mode.

        Args:
            mode: Mode name
        """
        self.mode = mode
        mode_widget = self.query_one("#status-mode", Static)
        mode_widget.update(mode)

        # Update mode widget style based on mode
        if mode == "INSERT":
            mode_widget.styles.background = "#4AFF88"  # Green
        elif mode == "AI":
            mode_widget.styles.background = "#B84AFF"  # Purple
        elif mode == "COMMAND":
            mode_widget.styles.background = "#FFD24A"  # Yellow
        else:  # NORMAL
            mode_widget.styles.background = "#4A9EFF"  # Blue

    def set_info(self, text: str) -> None:
        """
        Set info text.

        Args:
            text: Info text to display
        """
        self.info_text = text
        info_widget = self.query_one("#status-info", Static)

        # Build info string with focus indicator
        info_parts = [f"Focus: {self.focus_widget}"]
        if text:
            info_parts.append(text)

        info_widget.update(" | ".join(info_parts))

    def set_focus_widget(self, widget_name: str) -> None:
        """
        Set currently focused widget name.

        Args:
            widget_name: Widget name
        """
        self.focus_widget = widget_name
        self.set_info(self.info_text)

    def set_shortcuts(self, shortcuts: str) -> None:
        """
        Set keyboard shortcuts hint.

        Args:
            shortcuts: Shortcuts text
        """
        shortcuts_widget = self.query_one("#status-shortcuts", Static)
        shortcuts_widget.update(shortcuts)

    def show_message(self, message: str, duration: float = 3.0) -> None:
        """
        Show temporary message in status bar.

        Args:
            message: Message to display
            duration: Display duration in seconds
        """
        original_info = self.info_text
        self.set_info(message)

        # Reset after duration
        self.set_timer(duration, lambda: self.set_info(original_info))
