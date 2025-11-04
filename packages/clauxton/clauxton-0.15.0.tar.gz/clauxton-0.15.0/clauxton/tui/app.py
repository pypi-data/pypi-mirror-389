"""
Main Textual Application.

Entry point for Clauxton TUI. Manages screens, keybindings,
and application lifecycle.
"""

import logging
from pathlib import Path
from typing import Optional

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.driver import Driver

from clauxton.tui.config import TUIConfig
from clauxton.tui.keybindings import KeybindingManager
from clauxton.tui.layouts import LAYOUT_STYLES
from clauxton.tui.screens.dashboard import DashboardScreen
from clauxton.tui.themes import TUI_STYLES
from clauxton.tui.widgets.help_modal import HelpModal

# Set up logging for TUI events
logger = logging.getLogger(__name__)


class ClauxtonApp(App):
    """
    Main Textual application for Clauxton.

    Provides an interactive terminal UI for knowledge base management,
    task tracking, and AI-powered suggestions.
    """

    CSS = TUI_STYLES + "\n" + LAYOUT_STYLES

    TITLE = "Clauxton v0.14.0"
    SUB_TITLE = "AI-Powered Context Management"

    BINDINGS = [
        Binding("ctrl+c,q", "quit", "Quit", priority=True),
        Binding("ctrl+p", "command_palette", "Commands", show=True),
        Binding("ctrl+k", "focus_kb", "KB Browser", show=True),
        Binding("ctrl+l", "focus_content", "Content", show=True),
        Binding("ctrl+j", "focus_ai", "AI Panel", show=True),
        Binding("ctrl+t", "toggle_theme", "Theme", show=False),
        Binding("?", "help", "Help", show=True),
    ]

    def __init__(
        self,
        project_root: Path,
        config_path: Optional[Path] = None,
        driver_class: Optional[type[Driver]] = None,
        css_path: Optional[Path] = None,
        watch_css: bool = False,
    ):
        """
        Initialize Clauxton TUI application.

        Args:
            project_root: Project root directory
            config_path: Path to TUI config file
            driver_class: Textual driver class
            css_path: Path to custom CSS file
            watch_css: Watch CSS file for changes
        """
        super().__init__(
            driver_class=driver_class,
            css_path=css_path,
            watch_css=watch_css,
        )

        self.project_root = project_root

        # Load configuration
        if config_path is None:
            config_path = project_root / ".clauxton" / "tui.yml"
        self.config_path = config_path
        self.config = TUIConfig.load(config_path)

        # Initialize keybinding manager
        self.keybinding_manager = KeybindingManager()

        # Register themes - Textual uses Theme objects directly
        # For now, we'll handle theme switching differently
        self._current_theme_name = self.config.theme

        logger.info(
            f"Initialized Clauxton TUI for project: {project_root} "
            f"(theme: {self.config.theme})"
        )

    def compose(self) -> ComposeResult:
        """
        Compose initial UI.

        Pushes the dashboard screen as the main interface.
        """
        # Dashboard is pushed in on_mount
        return []

    def on_mount(self) -> None:
        """Handle app mount event."""
        logger.info("Clauxton TUI mounted successfully")

        # Apply theme
        self._apply_theme()

        # Push dashboard screen
        dashboard = DashboardScreen(
            project_root=self.project_root,
            show_ai_panel=self.config.show_ai_panel,
        )
        self.push_screen(dashboard)

    def _apply_theme(self) -> None:
        """Apply current theme to the app."""
        # This will be expanded when we implement full theming
        logger.debug(f"Applied theme: {self.config.theme}")

    # Action handlers

    def action_quit(self) -> None:  # type: ignore[override]
        """Quit the application."""
        logger.info("Quitting Clauxton TUI")
        self.exit()

    def action_command_palette(self) -> None:
        """Open command palette."""
        logger.debug("Command palette requested")
        # TODO: Implement command palette in Week 1 Day 4
        super().notify("Command palette coming soon!")

    def action_focus_kb(self) -> None:
        """Focus Knowledge Base panel."""
        logger.debug("KB panel focus requested")
        # TODO: Implement in Week 1 Day 2
        super().notify("KB panel coming soon!")

    def action_focus_content(self) -> None:
        """Focus main content panel."""
        logger.debug("Content panel focus requested")
        # TODO: Implement in Week 1 Day 2
        super().notify("Content panel coming soon!")

    def action_focus_ai(self) -> None:
        """Focus AI suggestions panel."""
        logger.debug("AI panel focus requested")
        # TODO: Implement in Week 1 Day 3
        super().notify("AI panel coming soon!")

    def action_toggle_theme(self) -> None:
        """Toggle between dark/light/high-contrast themes."""
        self.config.toggle_theme()
        self._current_theme_name = self.config.theme
        self._apply_theme()

        logger.info(f"Switched to {self.config.theme} theme")
        super().notify(f"Theme: {self.config.theme}")

        # Save config
        self.config.save(self.config_path)

    def action_help(self) -> None:
        """Show help modal."""
        logger.debug("Help requested")
        self.push_screen(HelpModal(self.keybinding_manager))


def run_tui(project_root: Path, config_path: Optional[Path] = None) -> None:
    """
    Run Clauxton TUI application.

    Args:
        project_root: Project root directory
        config_path: Path to TUI config file
    """
    # Set up logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        filename=project_root / ".clauxton" / "tui.log",
    )

    logger.info("=" * 60)
    logger.info("Starting Clauxton TUI")
    logger.info(f"Project root: {project_root}")
    logger.info("=" * 60)

    # Create and run app
    app = ClauxtonApp(
        project_root=project_root,
        config_path=config_path,
    )

    try:
        app.run()
    except Exception as e:
        logger.exception(f"TUI crashed: {e}")
        raise
    finally:
        logger.info("Clauxton TUI exited")
