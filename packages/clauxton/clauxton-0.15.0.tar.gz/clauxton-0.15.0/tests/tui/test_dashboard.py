"""Tests for Dashboard Screen (screens/dashboard.py)."""

from pathlib import Path

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.tui.screens.dashboard import DashboardScreen
from clauxton.tui.widgets.content import ContentWidget
from clauxton.tui.widgets.kb_browser import KBBrowserWidget
from clauxton.tui.widgets.statusbar import StatusBar


class TestDashboardScreen:
    """Test suite for DashboardScreen."""

    def test_dashboard_initialization(self, tmp_path: Path) -> None:
        """Test dashboard initializes correctly."""
        # Initialize .clauxton directory
        (tmp_path / ".clauxton").mkdir()

        screen = DashboardScreen(project_root=tmp_path)

        assert screen.project_root == tmp_path
        assert screen.show_ai_panel is True

    def test_dashboard_without_ai_panel(self, tmp_path: Path) -> None:
        """Test dashboard can hide AI panel."""
        (tmp_path / ".clauxton").mkdir()

        screen = DashboardScreen(project_root=tmp_path, show_ai_panel=False)

        assert screen.show_ai_panel is False

    def test_dashboard_has_compose_method(self, tmp_path: Path) -> None:
        """Test dashboard has compose method."""
        (tmp_path / ".clauxton").mkdir()

        screen = DashboardScreen(project_root=tmp_path)

        # Should have compose method
        assert hasattr(screen, "compose")
        assert callable(screen.compose)

    def test_dashboard_keybindings(self, tmp_path: Path) -> None:
        """Test dashboard keyboard shortcuts."""
        (tmp_path / ".clauxton").mkdir()

        screen = DashboardScreen(project_root=tmp_path)

        # BINDINGS is a list of Binding objects or tuples
        binding_keys = []
        for binding in screen.BINDINGS:
            if hasattr(binding, "key"):
                binding_keys.append(binding.key)
            elif isinstance(binding, tuple):
                binding_keys.append(binding[0])

        assert "ctrl+k" in binding_keys
        assert "ctrl+l" in binding_keys
        assert "ctrl+j" in binding_keys
        assert "r" in binding_keys

    def test_dashboard_action_focus_kb(self, tmp_path: Path) -> None:
        """Test action_focus_kb is available."""
        (tmp_path / ".clauxton").mkdir()

        screen = DashboardScreen(project_root=tmp_path)

        assert hasattr(screen, "action_focus_kb")
        assert callable(screen.action_focus_kb)

    def test_dashboard_action_focus_content(self, tmp_path: Path) -> None:
        """Test action_focus_content is available."""
        (tmp_path / ".clauxton").mkdir()

        screen = DashboardScreen(project_root=tmp_path)

        assert hasattr(screen, "action_focus_content")
        assert callable(screen.action_focus_content)

    def test_dashboard_action_focus_ai(self, tmp_path: Path) -> None:
        """Test action_focus_ai is available."""
        (tmp_path / ".clauxton").mkdir()

        screen = DashboardScreen(project_root=tmp_path)

        assert hasattr(screen, "action_focus_ai")
        assert callable(screen.action_focus_ai)

    def test_dashboard_action_refresh(self, tmp_path: Path) -> None:
        """Test action_refresh is available."""
        (tmp_path / ".clauxton").mkdir()

        screen = DashboardScreen(project_root=tmp_path)

        assert hasattr(screen, "action_refresh")
        assert callable(screen.action_refresh)


class TestKBBrowserWidget:
    """Test suite for KBBrowserWidget."""

    def test_kb_browser_initialization(self, tmp_path: Path) -> None:
        """Test KB browser initializes correctly."""
        (tmp_path / ".clauxton").mkdir()

        widget = KBBrowserWidget(project_root=tmp_path)

        assert widget.project_root == tmp_path
        assert isinstance(widget.kb, KnowledgeBase)

    def test_kb_browser_loads_entries(self, tmp_path: Path) -> None:
        """Test KB browser has load_entries method."""
        (tmp_path / ".clauxton").mkdir()

        widget = KBBrowserWidget(project_root=tmp_path)

        # Method should exist and be callable
        assert hasattr(widget, "load_entries")
        assert callable(widget.load_entries)

        # Should load without error (even if empty)
        widget.load_entries()
        assert isinstance(widget.entries, list)

    def test_kb_browser_category_emoji(self, tmp_path: Path) -> None:
        """Test category emoji mapping."""
        (tmp_path / ".clauxton").mkdir()

        widget = KBBrowserWidget(project_root=tmp_path)

        assert widget._get_category_emoji("architecture") == "🏗️"
        assert widget._get_category_emoji("constraint") == "⚠️"
        assert widget._get_category_emoji("decision") == "✅"
        assert widget._get_category_emoji("pattern") == "🎨"
        assert widget._get_category_emoji("convention") == "📝"
        assert widget._get_category_emoji("unknown") == "📄"


class TestContentWidget:
    """Test suite for ContentWidget."""

    def test_content_widget_initialization(self) -> None:
        """Test content widget initializes correctly."""
        widget = ContentWidget()

        assert widget.current_entry is None

    def test_content_widget_has_clear_method(self) -> None:
        """Test content widget has clear method."""
        widget = ContentWidget()

        # Method should exist and be callable
        assert hasattr(widget, "clear")
        assert callable(widget.clear)


class TestStatusBar:
    """Test suite for StatusBar."""

    def test_statusbar_initialization(self) -> None:
        """Test status bar initializes correctly."""
        statusbar = StatusBar()

        assert statusbar.mode == "NORMAL"
        assert statusbar.info_text == "Ready"
        assert statusbar.focus_widget == "KB Browser"

    def test_statusbar_has_set_mode_method(self) -> None:
        """Test status bar has set_mode method."""
        statusbar = StatusBar()

        assert hasattr(statusbar, "set_mode")
        assert callable(statusbar.set_mode)

    def test_statusbar_has_set_info_method(self) -> None:
        """Test status bar has set_info method."""
        statusbar = StatusBar()

        assert hasattr(statusbar, "set_info")
        assert callable(statusbar.set_info)

    def test_statusbar_has_set_focus_widget_method(self) -> None:
        """Test status bar has set_focus_widget method."""
        statusbar = StatusBar()

        assert hasattr(statusbar, "set_focus_widget")
        assert callable(statusbar.set_focus_widget)
