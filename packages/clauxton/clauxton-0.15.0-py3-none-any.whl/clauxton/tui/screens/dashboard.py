"""
Dashboard Screen.

Main screen with 3-panel layout (KB Browser, Content, AI Suggestions).
"""

from pathlib import Path
from typing import Any

from textual.app import ComposeResult
from textual.containers import Horizontal
from textual.screen import Screen
from textual.widgets import Header

from clauxton.tui.widgets.ai_suggestions import AISuggestionPanel
from clauxton.tui.widgets.content import ContentWidget
from clauxton.tui.widgets.kb_browser import KBBrowserWidget
from clauxton.tui.widgets.query_modal import QueryModal
from clauxton.tui.widgets.statusbar import StatusBar


class DashboardScreen(Screen):
    """
    Main dashboard screen.

    Features:
    - Left panel: KB Browser with tree view
    - Center panel: Content display
    - Right panel: AI Suggestions (placeholder for now)
    - Bottom: Status bar
    """

    CSS = """
    #main-container {
        width: 100%;
        height: 100%;
    }

    #kb-browser {
        width: 30%;
        border-right: solid $border;
        padding: 0;
    }

    #content-panel {
        width: 1fr;
        padding: 0;
    }

    #ai-panel {
        width: 30%;
        border-left: solid $border;
        padding: 1;
    }

    #kb-browser:focus-within {
        border-right: solid $primary;
    }

    #content-panel:focus-within {
        border: solid $primary;
    }

    #ai-panel:focus-within {
        border-left: solid $primary;
    }

    .panel-title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $surface;
        border-bottom: solid $border;
    }

    #kb-tree-container {
        height: 1fr;
        overflow-y: auto;
    }

    #content-scroll {
        height: 1fr;
    }
    """

    BINDINGS = [
        ("ctrl+k", "focus_kb", "KB Browser"),
        ("ctrl+l", "focus_content", "Content"),
        ("ctrl+j", "focus_ai", "AI Panel"),
        ("ctrl+p", "command_palette", "Query"),
        ("r", "refresh", "Refresh"),
        # Quick Actions
        ("a", "ask_ai", "Ask AI"),
        ("s", "show_suggestions", "Suggestions"),
        ("n", "new_task", "New Task"),
        ("e", "new_kb_entry", "New Entry"),
        ("t", "open_task_list", "Tasks"),
        # Navigation
        ("h", "focus_left", "Left"),
        ("l", "focus_right", "Right"),
        ("slash", "search_current", "Search"),
    ]

    def __init__(
        self,
        project_root: Path,
        show_ai_panel: bool = True,
    ) -> None:
        """
        Initialize dashboard screen.

        Args:
            project_root: Project root directory
            show_ai_panel: Show AI suggestions panel
        """
        super().__init__()
        self.project_root = project_root
        self.show_ai_panel = show_ai_panel

    def compose(self) -> ComposeResult:
        """Compose the dashboard."""
        # Header
        yield Header(show_clock=True)

        # Main content area with 3 panels
        with Horizontal(id="main-container"):
            # Left: KB Browser
            self.kb_browser = KBBrowserWidget(
                project_root=self.project_root,
                widget_id="kb-browser",
            )
            yield self.kb_browser

            # Center: Main Content
            self.content_widget = ContentWidget(widget_id="content-panel")
            yield self.content_widget

            # Right: AI Suggestions
            if self.show_ai_panel:
                self.ai_panel = AISuggestionPanel(
                    project_root=self.project_root,
                    widget_id="ai-panel",
                    refresh_interval=30,
                )
                yield self.ai_panel

        # Status bar
        self.status_bar = StatusBar()
        yield self.status_bar

    def on_mount(self) -> None:
        """Handle mount event."""
        # Focus KB browser by default
        self.query_one("#kb-browser").focus()
        self.status_bar.set_focus_widget("KB Browser")

        # Event handler on_kb_browser_widget_entry_selected is automatically registered

    def on_kb_browser_widget_entry_selected(
        self, message: KBBrowserWidget.EntrySelected
    ) -> None:
        """
        Handle KB entry selection.

        Args:
            message: Entry selected message
        """
        # Display entry in content panel
        self.content_widget.display_entry(message.entry)

        # Update status bar
        self.status_bar.set_info(f"Viewing: {message.entry.title}")

    # Action handlers

    def action_focus_kb(self) -> None:
        """Focus KB browser panel."""
        self.query_one("#kb-browser").focus()
        self.status_bar.set_focus_widget("KB Browser")

    def action_focus_content(self) -> None:
        """Focus content panel."""
        self.query_one("#content-panel").focus()
        self.status_bar.set_focus_widget("Content")

    def action_focus_ai(self) -> None:
        """Focus AI suggestions panel."""
        if self.show_ai_panel:
            self.query_one("#ai-panel").focus()
            self.status_bar.set_focus_widget("AI Suggestions")

    def action_refresh(self) -> None:
        """Refresh dashboard data."""
        # Reload KB entries
        self.kb_browser.load_entries()
        self.kb_browser.populate_tree()

        # Refresh AI suggestions
        if self.show_ai_panel and hasattr(self, "ai_panel"):
            self.ai_panel.refresh_suggestions()

        # Show message
        self.status_bar.show_message("✓ Refreshed", duration=2.0)

    def action_command_palette(self) -> None:
        """Open query modal (command palette)."""
        # Push modal screen
        self.app.push_screen(
            QueryModal(project_root=self.project_root),
            callback=self._handle_query_result,
        )

    def _handle_query_result(self, result: Any) -> None:
        """
        Handle query modal result.

        Args:
            result: Selected QueryResult or None if cancelled
        """
        from clauxton.tui.services.query_executor import QueryResult

        if result is None:
            # Cancelled
            self.status_bar.show_message("Query cancelled", duration=1.5)
            return

        if isinstance(result, QueryResult):
            # Display result in content panel
            content = (
                f"[bold]{result.title}[/bold]\n\n"
                f"[dim]Type:[/dim] {result.result_type.upper()}\n"
                f"[dim]Relevance:[/dim] {result.score:.0%}\n\n"
                f"{result.content}\n"
            )

            self.content_widget.display_markdown(
                content, title=f"Query Result: {result.title}"
            )

            # Update status
            self.status_bar.show_message(
                f"✓ Opened: {result.title}", duration=2.0
            )

    # Quick Actions

    def action_ask_ai(self) -> None:
        """Open query modal in AI mode."""
        from clauxton.tui.services.query_executor import QueryMode

        modal = QueryModal(project_root=self.project_root)
        modal.current_mode = QueryMode.AI
        self.app.push_screen(modal, callback=self._handle_query_result)
        self.status_bar.show_message("Ask AI mode activated", duration=1.5)

    def action_show_suggestions(self) -> None:
        """Focus AI suggestions panel."""
        if self.show_ai_panel:
            self.action_focus_ai()
            self.status_bar.show_message("Showing AI suggestions", duration=1.5)
        else:
            self.status_bar.show_message("AI panel is disabled", duration=2.0)

    def action_new_task(self) -> None:
        """Create new task (placeholder)."""
        self.status_bar.show_message("Create task - Coming soon!", duration=2.0)

    def action_new_kb_entry(self) -> None:
        """Create new KB entry (placeholder)."""
        self.status_bar.show_message("Create KB entry - Coming soon!", duration=2.0)

    def action_open_task_list(self) -> None:
        """Open task list (placeholder)."""
        self.status_bar.show_message("Task list - Coming soon!", duration=2.0)

    # Vim-style navigation

    def action_focus_left(self) -> None:
        """Focus left panel (vim-style)."""
        self.action_focus_kb()

    def action_focus_right(self) -> None:
        """Focus right panel (vim-style)."""
        if self.show_ai_panel:
            self.action_focus_ai()
        else:
            self.action_focus_content()

    def action_search_current(self) -> None:
        """Search in current panel (placeholder)."""
        self.status_bar.show_message("Search - Coming soon!", duration=2.0)

    def on_ai_suggestion_panel_suggestion_accepted(
        self, message: AISuggestionPanel.SuggestionAccepted
    ) -> None:
        """
        Handle suggestion acceptance.

        Args:
            message: Suggestion accepted message
        """
        # Show confirmation
        self.status_bar.show_message(
            f"✓ Accepted: {message.suggestion.title}", duration=3.0
        )
        # TODO: Implement actual action (e.g., create task, add KB entry)

    def on_ai_suggestion_panel_suggestion_rejected(
        self, message: AISuggestionPanel.SuggestionRejected
    ) -> None:
        """
        Handle suggestion rejection.

        Args:
            message: Suggestion rejected message
        """
        # Show confirmation
        self.status_bar.show_message(
            f"✗ Rejected: {message.suggestion.title}", duration=3.0
        )

    def on_ai_suggestion_panel_suggestion_details_requested(
        self, message: AISuggestionPanel.SuggestionDetailsRequested
    ) -> None:
        """
        Handle suggestion details request.

        Args:
            message: Suggestion details requested message
        """
        # Display details in content panel
        details = (
            f"[bold]{message.suggestion.emoji} {message.suggestion.title}[/bold]\n\n"
            f"[dim]Type:[/dim] {message.suggestion.type.value}\n"
            f"[dim]Confidence:[/dim] {message.suggestion.confidence:.0%} "
            f"({message.suggestion.confidence_level})\n\n"
            f"{message.suggestion.description}\n\n"
        )

        if message.suggestion.metadata:
            details += "[bold]Metadata:[/bold]\n"
            for key, value in message.suggestion.metadata.items():
                details += f"  • {key}: {value}\n"

        self.content_widget.display_markdown(
            details, title=f"Suggestion Details: {message.suggestion.id}"
        )
