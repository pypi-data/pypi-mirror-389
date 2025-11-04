"""
Help Modal Widget.

Displays keyboard shortcuts and help information.
"""

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.screen import ModalScreen
from textual.widgets import Static

from clauxton.tui.keybindings import KeybindingManager


class HelpModal(ModalScreen):
    """
    Help modal screen.

    Displays all keyboard shortcuts organized by category.
    """

    DEFAULT_CSS = """
    HelpModal {
        align: center middle;
    }

    #help-container {
        width: 70;
        height: 35;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }

    #help-title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $primary;
        color: $background;
        margin: 0 0 1 0;
    }

    #help-scroll {
        height: 1fr;
        border: solid $border;
        padding: 1;
    }

    .help-category {
        height: auto;
        text-style: bold;
        color: $accent;
        margin: 1 0 0 0;
    }

    .help-binding {
        height: auto;
        padding: 0 0 0 2;
    }

    #help-footer {
        height: 2;
        content-align: center middle;
        color: $text-muted;
        margin: 1 0 0 0;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Close"),
    ]

    def __init__(self, keybinding_manager: KeybindingManager) -> None:
        """
        Initialize help modal.

        Args:
            keybinding_manager: Keybinding manager instance
        """
        super().__init__()
        self.keybinding_manager = keybinding_manager

    def compose(self) -> ComposeResult:
        """Compose the help modal."""
        with Container(id="help-container"):
            # Title
            yield Static("⌨️  Keyboard Shortcuts", id="help-title")

            # Scrollable content
            with VerticalScroll(id="help-scroll"):
                # Get bindings grouped by category
                categories = self.keybinding_manager.get_bindings_by_category()

                # Sort categories for consistent display
                sorted_categories = sorted(categories.keys())

                for category in sorted_categories:
                    # Category header
                    yield Static(category, classes="help-category")

                    # Bindings in this category
                    bindings = categories[category]
                    for binding in bindings:
                        # Format: "Key  -  Description"
                        key_display = self.keybinding_manager.format_key_for_display(
                            binding.key
                        )
                        binding_text = Text()
                        binding_text.append(f"{key_display:20s}", style="cyan bold")
                        binding_text.append(" - ", style="dim")
                        binding_text.append(binding.description)

                        yield Static(binding_text, classes="help-binding")

            # Footer
            yield Static(
                "Press ESC to close",
                id="help-footer",
            )

    def action_cancel(self) -> None:
        """Close help modal."""
        self.dismiss()
