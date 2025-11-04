"""
AI Suggestions Panel Widget.

Displays real-time AI-generated suggestions with confidence indicators.
"""

from pathlib import Path
from typing import List

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Vertical, VerticalScroll
from textual.message import Message
from textual.widgets import Button, Label, ProgressBar, Static

from clauxton.tui.models.suggestion import Suggestion, SuggestionType


class SuggestionCard(Container):
    """
    Individual suggestion card widget.

    Displays a single suggestion with type, title, description,
    confidence indicator, and action buttons.
    """

    DEFAULT_CSS = """
    SuggestionCard {
        height: auto;
        border: solid $border;
        padding: 1;
        margin: 0 0 1 0;
        background: $surface;
    }

    SuggestionCard:focus-within {
        border: solid $primary;
    }

    SuggestionCard .suggestion-header {
        height: auto;
        margin: 0 0 1 0;
    }

    SuggestionCard .suggestion-description {
        height: auto;
        margin: 0 0 1 0;
        color: $text-muted;
    }

    SuggestionCard .confidence-bar {
        width: 100%;
        margin: 0 0 1 0;
    }

    SuggestionCard .action-buttons {
        height: auto;
        layout: horizontal;
    }

    SuggestionCard Button {
        margin: 0 1 0 0;
    }
    """

    def __init__(self, suggestion: Suggestion) -> None:
        """
        Initialize suggestion card.

        Args:
            suggestion: Suggestion to display
        """
        super().__init__(classes="suggestion-card")
        self.suggestion = suggestion

    def compose(self) -> ComposeResult:
        """Compose the card."""
        # Header with emoji and title
        header_text = Text()
        header_text.append(self.suggestion.emoji, style="bold")
        header_text.append(" ")
        header_text.append(self.suggestion.title, style="bold")
        yield Static(header_text, classes="suggestion-header")

        # Description
        yield Static(
            self.suggestion.description[:150] + "..."
            if len(self.suggestion.description) > 150
            else self.suggestion.description,
            classes="suggestion-description",
        )

        # Confidence indicator
        confidence_label = (
            f"Confidence: {self.suggestion.confidence:.0%} "
            f"({self.suggestion.confidence_level})"
        )
        yield Label(confidence_label)

        # Progress bar for confidence
        progress = ProgressBar(
            total=100,
            show_eta=False,
            classes="confidence-bar",
        )
        progress.advance(self.suggestion.confidence * 100)
        yield progress

        # Action buttons
        with Vertical(classes="action-buttons"):
            yield Button("✓ Accept", id=f"accept-{self.suggestion.id}", variant="success")
            yield Button("✗ Reject", id=f"reject-{self.suggestion.id}", variant="error")
            yield Button(
                "📄 Details", id=f"details-{self.suggestion.id}", variant="default"
            )

    def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        button_id = event.button.id or ""

        if button_id.startswith("accept-"):
            self.post_message(self.SuggestionAccepted(self.suggestion))
        elif button_id.startswith("reject-"):
            self.post_message(self.SuggestionRejected(self.suggestion))
        elif button_id.startswith("details-"):
            self.post_message(self.SuggestionDetailsRequested(self.suggestion))

    # Custom messages
    class SuggestionAccepted(Message):
        """Message when suggestion is accepted."""

        def __init__(self, suggestion: Suggestion) -> None:
            super().__init__()
            self.suggestion = suggestion

    class SuggestionRejected(Message):
        """Message when suggestion is rejected."""

        def __init__(self, suggestion: Suggestion) -> None:
            super().__init__()
            self.suggestion = suggestion

    class SuggestionDetailsRequested(Message):
        """Message when details are requested."""

        def __init__(self, suggestion: Suggestion) -> None:
            super().__init__()
            self.suggestion = suggestion


class AISuggestionPanel(Container):
    """
    AI Suggestions panel widget.

    Displays a list of AI-generated suggestions with real-time updates.
    """

    DEFAULT_CSS = """
    AISuggestionPanel {
        width: 100%;
        height: 100%;
    }

    AISuggestionPanel .panel-title {
        height: 3;
        content-align: center middle;
        text-style: bold;
        background: $surface;
        border-bottom: solid $border;
    }

    AISuggestionPanel .suggestions-scroll {
        height: 1fr;
    }

    AISuggestionPanel .empty-message {
        height: auto;
        padding: 2;
        color: $text-muted;
        text-align: center;
    }

    AISuggestionPanel .refresh-info {
        height: 1;
        padding: 0 1;
        color: $text-muted;
        text-align: center;
    }
    """

    def __init__(
        self,
        project_root: Path,
        widget_id: str = "ai-suggestions",
        refresh_interval: int = 30,
    ) -> None:
        """
        Initialize AI suggestions panel.

        Args:
            project_root: Project root directory
            widget_id: Widget ID
            refresh_interval: Refresh interval in seconds
        """
        super().__init__(id=widget_id)
        self.project_root = project_root
        self.refresh_interval = refresh_interval
        self.suggestions: List[Suggestion] = []

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        # Title
        yield Static("💡 AI Suggestions", classes="panel-title")

        # Scrollable suggestions area
        with VerticalScroll(classes="suggestions-scroll"):
            yield Static(
                "Loading suggestions...",
                id="suggestions-container",
                classes="empty-message",
            )

        # Refresh info
        yield Static(
            f"Auto-refresh every {self.refresh_interval}s",
            classes="refresh-info",
        )

    def on_mount(self) -> None:
        """Handle mount event."""
        # Load initial suggestions
        self.refresh_suggestions()

        # Set up auto-refresh
        self.set_interval(self.refresh_interval, self.refresh_suggestions)

    def refresh_suggestions(self) -> None:
        """Refresh suggestions from backend."""
        # TODO: Integrate with SuggestionService
        # For now, use placeholder suggestions
        self.suggestions = self._get_placeholder_suggestions()
        self._update_display()

    def _get_placeholder_suggestions(self) -> List[Suggestion]:
        """Get placeholder suggestions for testing."""
        return [
            Suggestion(
                id="SUGG-001",
                type=SuggestionType.TASK,
                title="Add authentication middleware",
                description="Consider adding authentication middleware to protect API endpoints",
                confidence=0.85,
                metadata={"files": ["api/routes.py"]},
            ),
            Suggestion(
                id="SUGG-002",
                type=SuggestionType.KB,
                title="Document error handling pattern",
                description=(
                    "Found consistent error handling pattern. "
                    "Consider documenting it in KB"
                ),
                confidence=0.72,
                metadata={"pattern": "try-except with logging"},
            ),
            Suggestion(
                id="SUGG-003",
                type=SuggestionType.REVIEW,
                title="Optimize database query",
                description="Database query in get_users() could be optimized with select_related",
                confidence=0.68,
                metadata={"file": "models.py", "line": 45},
            ),
        ]

    def _update_display(self) -> None:
        """Update suggestions display."""
        container = self.query_one("#suggestions-container", Static)

        if not self.suggestions:
            container.update("No suggestions available")
            return

        # Create suggestion cards
        # Note: In actual implementation, we'd remove old cards and add new ones
        # For now, just update the container text
        summary = f"{len(self.suggestions)} suggestions available"
        container.update(summary)

    def on_suggestion_card_suggestion_accepted(
        self, message: SuggestionCard.SuggestionAccepted
    ) -> None:
        """Handle suggestion acceptance."""
        message.suggestion.accept()
        self.post_message(self.SuggestionAccepted(message.suggestion))
        # Remove from list
        self.suggestions = [s for s in self.suggestions if s.id != message.suggestion.id]
        self._update_display()

    def on_suggestion_card_suggestion_rejected(
        self, message: SuggestionCard.SuggestionRejected
    ) -> None:
        """Handle suggestion rejection."""
        message.suggestion.reject()
        self.post_message(self.SuggestionRejected(message.suggestion))
        # Remove from list
        self.suggestions = [s for s in self.suggestions if s.id != message.suggestion.id]
        self._update_display()

    def on_suggestion_card_suggestion_details_requested(
        self, message: SuggestionCard.SuggestionDetailsRequested
    ) -> None:
        """Handle details request."""
        self.post_message(self.SuggestionDetailsRequested(message.suggestion))

    # Custom messages
    class SuggestionAccepted(Message):
        """Message when suggestion is accepted."""

        def __init__(self, suggestion: Suggestion) -> None:
            super().__init__()
            self.suggestion = suggestion

    class SuggestionRejected(Message):
        """Message when suggestion is rejected."""

        def __init__(self, suggestion: Suggestion) -> None:
            super().__init__()
            self.suggestion = suggestion

    class SuggestionDetailsRequested(Message):
        """Message when details are requested."""

        def __init__(self, suggestion: Suggestion) -> None:
            super().__init__()
            self.suggestion = suggestion
