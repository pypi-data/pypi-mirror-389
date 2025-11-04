"""
Query Modal Widget.

Interactive query modal with autocomplete and multi-mode search.
"""

from pathlib import Path
from typing import List

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, VerticalScroll
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Input, Static

from clauxton.tui.services.autocomplete import CompositeAutocompleteProvider
from clauxton.tui.services.query_executor import QueryExecutor, QueryMode, QueryResult


class QueryResultItem(Container):
    """Individual query result item."""

    DEFAULT_CSS = """
    QueryResultItem {
        height: auto;
        padding: 1;
        border: solid $border;
        margin: 0 0 1 0;
        background: $surface;
    }

    QueryResultItem:hover {
        background: $highlight;
    }

    QueryResultItem .result-title {
        text-style: bold;
    }

    QueryResultItem .result-content {
        color: $text-muted;
    }

    QueryResultItem .result-meta {
        color: $text-muted;
        text-style: dim;
    }
    """

    def __init__(self, result: QueryResult) -> None:
        """
        Initialize result item.

        Args:
            result: Query result
        """
        super().__init__()
        self.result = result

    def compose(self) -> ComposeResult:
        """Compose the result item."""
        # Title with type badge
        title_text = Text()
        title_text.append(f"[{self.result.result_type.upper()}] ", style="cyan")
        title_text.append(self.result.title, style="bold")
        yield Static(title_text, classes="result-title")

        # Content preview
        yield Static(self.result.content, classes="result-content")

        # Score indicator
        score_text = f"Relevance: {self.result.score:.0%}"
        yield Static(score_text, classes="result-meta")

    def on_click(self) -> None:
        """Handle click."""
        self.post_message(self.ResultSelected(self.result))

    class ResultSelected(Message):
        """Message when result is selected."""

        def __init__(self, result: QueryResult) -> None:
            super().__init__()
            self.result = result


class QueryModal(ModalScreen):
    """
    Query modal screen.

    Provides interactive search with autocomplete and multiple modes.
    """

    DEFAULT_CSS = """
    QueryModal {
        align: center middle;
    }

    #query-container {
        width: 80;
        height: 30;
        background: $surface;
        border: thick $primary;
        padding: 1;
    }

    #query-title {
        height: 1;
        content-align: center middle;
        text-style: bold;
        background: $primary;
        color: $background;
        margin: 0 0 1 0;
    }

    #query-input {
        margin: 0 0 1 0;
    }

    #query-mode {
        height: 1;
        margin: 0 0 1 0;
        color: $text-muted;
    }

    #autocomplete-list {
        height: 5;
        border: solid $border;
        padding: 1;
        margin: 0 0 1 0;
        background: $background;
    }

    #results-scroll {
        height: 1fr;
        border: solid $border;
    }

    #results-count {
        height: 1;
        margin: 1 0 0 0;
        text-align: center;
        color: $text-muted;
    }
    """

    BINDINGS = [
        ("escape", "cancel", "Cancel"),
        ("ctrl+n", "next_mode", "Next Mode"),
    ]

    def __init__(self, project_root: Path) -> None:
        """
        Initialize query modal.

        Args:
            project_root: Project root directory
        """
        super().__init__()
        self.project_root = project_root
        self.current_mode = QueryMode.NORMAL
        self.autocomplete_provider = CompositeAutocompleteProvider(project_root)
        self.query_executor = QueryExecutor(project_root)
        self.results: List[QueryResult] = []
        self.autocomplete_suggestions: List[str] = []

    def compose(self) -> ComposeResult:
        """Compose the modal."""
        with Container(id="query-container"):
            # Title
            yield Static("🔍 Query", id="query-title")

            # Input
            yield Input(
                placeholder="Type to search...",
                id="query-input",
            )

            # Mode indicator
            yield Static(
                f"Mode: {self.current_mode.value.upper()}",
                id="query-mode",
            )

            # Autocomplete suggestions
            yield Static(
                "Type to see suggestions...",
                id="autocomplete-list",
            )

            # Results
            with VerticalScroll(id="results-scroll"):
                yield Static("Enter a query to search", id="results-container")

            # Results count
            yield Static("0 results", id="results-count")

    def on_mount(self) -> None:
        """Handle mount."""
        # Focus input
        self.query_one("#query-input", Input).focus()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle input changes."""
        if event.input.id == "query-input":
            query = event.value

            # Update autocomplete
            if query:
                self.autocomplete_suggestions = self.autocomplete_provider.get_suggestions(
                    query, limit=5
                )
                autocomplete_text = "\n".join(
                    f"  • {s}" for s in self.autocomplete_suggestions
                )
                self.query_one("#autocomplete-list", Static).update(
                    autocomplete_text or "No suggestions"
                )
            else:
                self.query_one("#autocomplete-list", Static).update(
                    "Type to see suggestions..."
                )

    def on_input_submitted(self, event: Input.Submitted) -> None:
        """Handle query submission."""
        if event.input.id == "query-input":
            query = event.value
            self._execute_query(query)

    def _execute_query(self, query: str) -> None:
        """Execute query and display results."""
        if not query:
            return

        # Execute query
        self.results = self.query_executor.execute(
            query, mode=self.current_mode, limit=20
        )

        # Update results display
        results_container = self.query_one("#results-container", Static)

        if not self.results:
            results_container.update("No results found")
        else:
            # Create result text
            result_lines = []
            for i, result in enumerate(self.results[:10], 1):
                result_lines.append(
                    f"{i}. [{result.result_type.upper()}] {result.title}"
                )
                result_lines.append(f"   {result.content[:80]}...")
                result_lines.append("")

            results_container.update("\n".join(result_lines))

        # Update count
        self.query_one("#results-count", Static).update(
            f"{len(self.results)} results"
        )

    def action_cancel(self) -> None:
        """Cancel and close modal."""
        self.dismiss(None)

    def action_next_mode(self) -> None:
        """Cycle to next query mode."""
        modes = list(QueryMode)
        current_index = modes.index(self.current_mode)
        self.current_mode = modes[(current_index + 1) % len(modes)]

        # Update mode display
        self.query_one("#query-mode", Static).update(
            f"Mode: {self.current_mode.value.upper()}"
        )

        # Re-execute query if we have one
        query_input = self.query_one("#query-input", Input)
        if query_input.value:
            self._execute_query(query_input.value)

    def on_query_result_item_result_selected(
        self, message: QueryResultItem.ResultSelected
    ) -> None:
        """Handle result selection."""
        self.dismiss(message.result)
