"""Tests for Navigation and Focus Management."""

from pathlib import Path

from clauxton.tui.app import ClauxtonApp
from clauxton.tui.screens.dashboard import DashboardScreen
from clauxton.tui.widgets.help_modal import HelpModal


class TestDashboardNavigation:
    """Test suite for dashboard navigation."""

    def test_dashboard_has_focus_kb_action(self, tmp_path: Path) -> None:
        """Test dashboard has focus_kb action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_focus_kb")
        assert callable(dashboard.action_focus_kb)

    def test_dashboard_has_focus_content_action(self, tmp_path: Path) -> None:
        """Test dashboard has focus_content action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_focus_content")
        assert callable(dashboard.action_focus_content)

    def test_dashboard_has_focus_ai_action(self, tmp_path: Path) -> None:
        """Test dashboard has focus_ai action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_focus_ai")
        assert callable(dashboard.action_focus_ai)

    def test_dashboard_has_vim_navigation_actions(self, tmp_path: Path) -> None:
        """Test dashboard has vim-style navigation actions."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_focus_left")
        assert hasattr(dashboard, "action_focus_right")
        assert callable(dashboard.action_focus_left)
        assert callable(dashboard.action_focus_right)


class TestQuickActions:
    """Test suite for quick actions."""

    def test_dashboard_has_ask_ai_action(self, tmp_path: Path) -> None:
        """Test dashboard has ask_ai action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_ask_ai")
        assert callable(dashboard.action_ask_ai)

    def test_dashboard_has_show_suggestions_action(self, tmp_path: Path) -> None:
        """Test dashboard has show_suggestions action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_show_suggestions")
        assert callable(dashboard.action_show_suggestions)

    def test_dashboard_has_new_task_action(self, tmp_path: Path) -> None:
        """Test dashboard has new_task action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_new_task")
        assert callable(dashboard.action_new_task)

    def test_dashboard_has_new_kb_entry_action(self, tmp_path: Path) -> None:
        """Test dashboard has new_kb_entry action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_new_kb_entry")
        assert callable(dashboard.action_new_kb_entry)

    def test_dashboard_has_open_task_list_action(self, tmp_path: Path) -> None:
        """Test dashboard has open_task_list action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_open_task_list")
        assert callable(dashboard.action_open_task_list)

    def test_dashboard_has_search_current_action(self, tmp_path: Path) -> None:
        """Test dashboard has search_current action."""
        (tmp_path / ".clauxton").mkdir()
        dashboard = DashboardScreen(project_root=tmp_path)

        assert hasattr(dashboard, "action_search_current")
        assert callable(dashboard.action_search_current)


class TestHelpModal:
    """Test suite for help modal."""

    def test_help_modal_initialization(self, tmp_path: Path) -> None:
        """Test help modal initializes correctly."""
        (tmp_path / ".clauxton").mkdir()
        app = ClauxtonApp(project_root=tmp_path)
        modal = HelpModal(app.keybinding_manager)

        assert modal.keybinding_manager is not None

    def test_help_modal_has_compose_method(self, tmp_path: Path) -> None:
        """Test help modal has compose method."""
        (tmp_path / ".clauxton").mkdir()
        app = ClauxtonApp(project_root=tmp_path)
        modal = HelpModal(app.keybinding_manager)

        assert hasattr(modal, "compose")
        assert callable(modal.compose)

    def test_help_modal_has_cancel_action(self, tmp_path: Path) -> None:
        """Test help modal has cancel action."""
        (tmp_path / ".clauxton").mkdir()
        app = ClauxtonApp(project_root=tmp_path)
        modal = HelpModal(app.keybinding_manager)

        assert hasattr(modal, "action_cancel")
        assert callable(modal.action_cancel)

    def test_app_has_keybinding_manager(self, tmp_path: Path) -> None:
        """Test app initializes keybinding manager."""
        (tmp_path / ".clauxton").mkdir()
        app = ClauxtonApp(project_root=tmp_path)

        assert hasattr(app, "keybinding_manager")
        assert app.keybinding_manager is not None
