"""TUI Widgets."""

from clauxton.tui.widgets.ai_suggestions import AISuggestionPanel, SuggestionCard
from clauxton.tui.widgets.content import ContentWidget
from clauxton.tui.widgets.help_modal import HelpModal
from clauxton.tui.widgets.kb_browser import KBBrowserWidget
from clauxton.tui.widgets.query_modal import QueryModal
from clauxton.tui.widgets.statusbar import StatusBar

__all__ = [
    "AISuggestionPanel",
    "ContentWidget",
    "HelpModal",
    "KBBrowserWidget",
    "QueryModal",
    "StatusBar",
    "SuggestionCard",
]
