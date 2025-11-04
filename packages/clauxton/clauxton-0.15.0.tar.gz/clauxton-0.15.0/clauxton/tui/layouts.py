"""
TUI Layout System.

Defines the 3-panel layout structure for Clauxton TUI:
- Left panel: Knowledge Base browser
- Center panel: Main content area
- Right panel: AI suggestions
"""

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.widget import Widget
from textual.widgets import Footer, Header, Static


class MainLayout(Container):
    """
    Main layout container with 3-panel design.

    Layout structure:
    ┌─────────────────────────────────────────────┐
    │ Header                                      │
    ├──────────┬───────────────┬──────────────────┤
    │ KB Panel │ Content Panel │ AI Suggestions   │
    │          │               │                  │
    │          │               │                  │
    ├──────────┴───────────────┴──────────────────┤
    │ Status Bar / Footer                         │
    └─────────────────────────────────────────────┘
    """

    def __init__(
        self,
        kb_panel: Widget,
        content_panel: Widget,
        ai_panel: Widget,
        show_kb_panel: bool = True,
        show_ai_panel: bool = True,
    ) -> None:
        """
        Initialize main layout.

        Args:
            kb_panel: Knowledge Base browser widget
            content_panel: Main content widget
            ai_panel: AI suggestions widget
            show_kb_panel: Show KB panel on left
            show_ai_panel: Show AI panel on right
        """
        super().__init__()
        self.kb_panel = kb_panel
        self.content_panel = content_panel
        self.ai_panel = ai_panel
        self.show_kb_panel = show_kb_panel
        self.show_ai_panel = show_ai_panel

    def compose(self) -> ComposeResult:
        """Compose the layout."""
        # Header
        yield Header(show_clock=True)

        # Main content area with 3 panels
        with Horizontal(id="main-content"):
            # Left panel (KB browser)
            if self.show_kb_panel:
                with Vertical(id="kb-panel", classes="panel"):
                    yield self.kb_panel

            # Center panel (main content)
            with Vertical(id="content-panel", classes="panel"):
                yield self.content_panel

            # Right panel (AI suggestions)
            if self.show_ai_panel:
                with Vertical(id="ai-panel", classes="panel"):
                    yield self.ai_panel

        # Footer / Status bar
        yield Footer()


class PanelContainer(Container):
    """
    Container for individual panels with title and content.

    Provides consistent styling and structure for all panels.
    """

    def __init__(
        self,
        title: str,
        content: Widget,
        panel_id: str,
        show_border: bool = True,
    ) -> None:
        """
        Initialize panel container.

        Args:
            title: Panel title
            content: Panel content widget
            panel_id: Unique panel identifier
            show_border: Show panel border
        """
        super().__init__(id=panel_id)
        self.panel_title = title
        self.panel_content = content
        self.show_border = show_border

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        # Panel title
        yield Static(self.panel_title, classes="panel-title")

        # Panel content
        yield self.panel_content


class ResizablePanel(Container):
    """
    Resizable panel with min/max width constraints.

    Allows users to resize panels with mouse or keyboard.
    """

    def __init__(
        self,
        content: Widget,
        panel_id: str,
        min_width: int = 20,
        max_width: int = 60,
        default_width: int = 30,
    ) -> None:
        """
        Initialize resizable panel.

        Args:
            content: Panel content widget
            panel_id: Unique panel identifier
            min_width: Minimum width (columns)
            max_width: Maximum width (columns)
            default_width: Default width (columns)
        """
        super().__init__(id=panel_id)
        self.panel_content = content
        self.min_width = min_width
        self.max_width = max_width
        self.current_width = default_width

    def compose(self) -> ComposeResult:
        """Compose the panel."""
        yield self.panel_content

    def resize(self, delta: int) -> None:
        """
        Resize panel by delta columns.

        Args:
            delta: Width change (positive = wider, negative = narrower)
        """
        new_width = self.current_width + delta
        new_width = max(self.min_width, min(self.max_width, new_width))
        self.current_width = new_width
        self.styles.width = new_width


# CSS for layouts
LAYOUT_STYLES = """
/* Main content area */
#main-content {
    width: 100%;
    height: 100%;
}

/* Left panel (KB browser) */
#kb-panel {
    width: 30%;
    min-width: 20;
    max-width: 50;
    border-right: solid $border;
}

/* Center panel (main content) */
#content-panel {
    width: 1fr;
    padding: 1 2;
}

/* Right panel (AI suggestions) */
#ai-panel {
    width: 30%;
    min-width: 20;
    max-width: 50;
    border-left: solid $border;
}

/* Panel titles */
.panel-title {
    height: 3;
    content-align: center middle;
    text-style: bold;
    background: $surface;
    border-bottom: solid $border;
}

/* Focused panel */
.panel:focus {
    border: solid $primary;
}
"""
