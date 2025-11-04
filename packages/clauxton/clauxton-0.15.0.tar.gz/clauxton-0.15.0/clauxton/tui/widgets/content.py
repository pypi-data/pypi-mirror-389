"""
Main Content Widget.

Displays KB entry details with markdown rendering and syntax highlighting.
"""

from typing import Optional

from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.widgets import Static

from clauxton.core.models import KnowledgeBaseEntry


class ContentWidget(Container):
    """
    Main content display widget.

    Shows KB entry details with markdown rendering,
    syntax highlighting for code blocks, and smooth scrolling.
    """

    def __init__(self, widget_id: str = "content-widget") -> None:
        """
        Initialize content widget.

        Args:
            widget_id: Widget ID
        """
        super().__init__(id=widget_id)
        self.current_entry: Optional[KnowledgeBaseEntry] = None

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # Scrollable content area
        with VerticalScroll(id="content-scroll"):
            yield Static(
                self._get_welcome_message(),
                id="content-display",
                markup=True,
            )

    def _get_welcome_message(self) -> str:
        """Get welcome message when no entry is selected."""
        return (
            "[bold cyan]Welcome to Clauxton TUI[/bold cyan]\n\n"
            "Select a Knowledge Base entry from the left panel to view details.\n\n"
            "[dim]Keyboard shortcuts:[/dim]\n"
            "  [bold]Ctrl+K[/bold] - Focus KB Browser\n"
            "  [bold]Ctrl+L[/bold] - Focus Content\n"
            "  [bold]Ctrl+J[/bold] - Focus AI Suggestions\n"
            "  [bold]Ctrl+P[/bold] - Command Palette\n"
            "  [bold]?[/bold] - Help\n"
            "  [bold]Q[/bold] - Quit"
        )

    def display_entry(self, entry: KnowledgeBaseEntry) -> None:
        """
        Display KB entry content.

        Args:
            entry: KB entry to display
        """
        self.current_entry = entry

        # Build content
        content_parts = []

        # Title
        content_parts.append(f"[bold cyan]{entry.title}[/bold cyan]")
        content_parts.append("")

        # Metadata
        metadata = []
        metadata.append(f"[dim]ID:[/dim] {entry.id}")
        metadata.append(f"[dim]Category:[/dim] {entry.category}")
        if entry.tags:
            tags_str = ", ".join(f"[cyan]{tag}[/cyan]" for tag in entry.tags)
            metadata.append(f"[dim]Tags:[/dim] {tags_str}")
        metadata.append(
            f"[dim]Updated:[/dim] {entry.updated_at.strftime('%Y-%m-%d %H:%M')}"
        )

        content_parts.append(" | ".join(metadata))
        content_parts.append("")
        content_parts.append("─" * 60)
        content_parts.append("")

        # Content (with markdown-like rendering)
        content_parts.append(entry.content)

        # Related entries (if any)
        if hasattr(entry, "related_entries") and entry.related_entries:
            content_parts.append("")
            content_parts.append("─" * 60)
            content_parts.append("[bold]Related Entries:[/bold]")
            for related_id in entry.related_entries:
                content_parts.append(f"  • {related_id}")

        # Update display
        content_display = self.query_one("#content-display", Static)
        content_display.update("\n".join(content_parts))

        # Scroll to top
        scroll_container = self.query_one("#content-scroll", VerticalScroll)
        scroll_container.scroll_home(animate=False)

    def display_markdown(self, content: str, title: str = "") -> None:
        """
        Display markdown content.

        Args:
            content: Markdown content
            title: Optional title
        """
        content_parts = []

        if title:
            content_parts.append(f"[bold cyan]{title}[/bold cyan]")
            content_parts.append("")

        content_parts.append(content)

        content_display = self.query_one("#content-display", Static)
        content_display.update("\n".join(content_parts))

    def clear(self) -> None:
        """Clear content and show welcome message."""
        self.current_entry = None
        content_display = self.query_one("#content-display", Static)
        content_display.update(self._get_welcome_message())
