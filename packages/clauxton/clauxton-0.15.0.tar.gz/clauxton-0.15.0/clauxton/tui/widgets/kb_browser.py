"""
Knowledge Base Browser Widget.

Displays KB entries in a tree view with category filtering and search.
"""

from pathlib import Path
from typing import List, Optional

from rich.text import Text
from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.message import Message
from textual.widgets import Input, Static, Tree

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry


class KBBrowserWidget(Container):
    """
    Knowledge Base browser widget.

    Displays KB entries in a tree view organized by category.
    Supports filtering, search, and entry preview.
    """

    def __init__(
        self,
        project_root: Path,
        widget_id: str = "kb-browser",
    ) -> None:
        """
        Initialize KB browser widget.

        Args:
            project_root: Project root directory
            widget_id: Widget ID
        """
        super().__init__(id=widget_id)
        self.project_root = project_root
        self.kb = KnowledgeBase(project_root)
        self.entries: List[KnowledgeBaseEntry] = []
        self.selected_entry: Optional[KnowledgeBaseEntry] = None

    def compose(self) -> ComposeResult:
        """Compose the widget."""
        # Title
        yield Static("📚 Knowledge Base", classes="panel-title")

        # Search box
        yield Input(
            placeholder="Search KB...",
            id="kb-search",
        )

        # Tree view
        with Vertical(id="kb-tree-container"):
            tree: Tree[str] = Tree("Knowledge Base", id="kb-tree")
            tree.show_root = False
            yield tree

        # Entry count
        yield Static("0 entries", id="kb-count", classes="text-muted")

    def on_mount(self) -> None:
        """Handle mount event."""
        self.load_entries()
        self.populate_tree()

    def load_entries(self) -> None:
        """Load KB entries from storage."""
        try:
            self.entries = self.kb.list_all()
        except Exception:
            self.entries = []

    def populate_tree(self) -> None:
        """Populate tree view with KB entries."""
        tree = self.query_one("#kb-tree", Tree)
        tree.clear()

        # Group entries by category
        from typing import Any
        categories: dict[Any, List[KnowledgeBaseEntry]] = {}
        for entry in self.entries:
            category = entry.category
            if category not in categories:
                categories[category] = []
            categories[category].append(entry)

        # Add category nodes
        for category, cat_entries in sorted(categories.items()):
            # Create category node with emoji
            category_emoji = self._get_category_emoji(category)
            category_label = f"{category_emoji} {category.title()} ({len(cat_entries)})"
            category_node = tree.root.add(category_label, data=f"category:{category}")

            # Add entries under category
            for entry in sorted(cat_entries, key=lambda e: e.title):
                entry_label = Text()
                entry_label.append("  ")
                entry_label.append(entry.title, style="bold")
                if entry.tags:
                    entry_label.append(f" [{', '.join(entry.tags[:2])}]", style="dim")

                category_node.add_leaf(entry_label, data=f"entry:{entry.id}")

        # Expand first category by default
        if tree.root.children:
            tree.root.children[0].expand()

        # Update count
        count_widget = self.query_one("#kb-count", Static)
        count_widget.update(f"{len(self.entries)} entries")

    def _get_category_emoji(self, category: str) -> str:
        """Get emoji for category."""
        emoji_map = {
            "architecture": "🏗️",
            "constraint": "⚠️",
            "decision": "✅",
            "pattern": "🎨",
            "convention": "📝",
        }
        return emoji_map.get(category, "📄")

    def on_tree_node_selected(self, event: Tree.NodeSelected) -> None:
        """Handle tree node selection."""
        node = event.node
        if node.data and isinstance(node.data, str):
            if node.data.startswith("entry:"):
                entry_id = node.data.split(":", 1)[1]
                self.select_entry(entry_id)

    def select_entry(self, entry_id: str) -> None:
        """
        Select and display KB entry.

        Args:
            entry_id: Entry ID
        """
        try:
            entry = self.kb.get(entry_id)
            self.selected_entry = entry
            # Post message to update content panel
            self.post_message(self.EntrySelected(entry))
        except Exception:
            self.selected_entry = None

    def filter_entries(self, query: str) -> None:
        """
        Filter entries by search query.

        Args:
            query: Search query
        """
        if not query:
            self.load_entries()
        else:
            # Simple case-insensitive search
            query_lower = query.lower()
            self.entries = [
                e
                for e in self.kb.list_all()
                if query_lower in e.title.lower()
                or query_lower in e.content.lower()
                or any(query_lower in tag.lower() for tag in e.tags)
            ]

        self.populate_tree()

    def on_input_changed(self, event: Input.Changed) -> None:
        """Handle search input changes."""
        if event.input.id == "kb-search":
            self.filter_entries(event.value)

    # Custom messages
    class EntrySelected(Message):
        """Message sent when an entry is selected."""

        def __init__(self, entry: KnowledgeBaseEntry) -> None:
            """
            Initialize message.

            Args:
                entry: Selected entry
            """
            super().__init__()
            self.entry = entry
