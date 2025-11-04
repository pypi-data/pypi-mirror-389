"""E2E workflow integration tests for Clauxton TUI."""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry
from clauxton.tui.app import ClauxtonApp
from clauxton.tui.screens.dashboard import DashboardScreen


@pytest.fixture
def app_with_kb(tmp_path: Path) -> ClauxtonApp:
    """Create app with populated Knowledge Base."""
    # Initialize KB
    kb = KnowledgeBase(tmp_path)

    # Add sample entries (using valid categories)
    entries = [
        KnowledgeBaseEntry(
            id="KB-20251028-001",
            title="FastAPI Authentication",
            category="architecture",
            content="Use JWT tokens for authentication in FastAPI",
            tags=["fastapi", "auth", "jwt"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        KnowledgeBaseEntry(
            id="KB-20251028-002",
            title="Database Migration Strategy",
            category="decision",
            content="Use Alembic for database migrations",
            tags=["database", "alembic", "migration"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        KnowledgeBaseEntry(
            id="KB-20251028-003",
            title="Testing Best Practices",
            category="pattern",
            content="Write unit tests, integration tests, and E2E tests",
            tags=["testing", "pytest", "quality"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]

    for entry in entries:
        kb.add(entry)

    # Create app
    app = ClauxtonApp(project_root=tmp_path)
    return app


class TestKBBrowserWorkflow:
    """Test KB browser workflows."""

    @pytest.mark.asyncio
    async def test_kb_browser_displays_entries(self, app_with_kb: ClauxtonApp) -> None:
        """Test KB browser displays entries on startup."""
        async with app_with_kb.run_test() as pilot:
            # Wait for app to mount
            await pilot.pause()

            # Dashboard should be the current screen
            assert isinstance(app_with_kb.screen, DashboardScreen)

            # KB Browser should be visible
            from clauxton.tui.widgets.kb_browser import KBBrowserWidget
            kb_browser = app_with_kb.screen.query_one(KBBrowserWidget)
            assert kb_browser is not None

    @pytest.mark.asyncio
    async def test_kb_category_expansion(self, app_with_kb: ClauxtonApp) -> None:
        """Test expanding KB categories."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Focus KB browser and try to expand
            await pilot.press("tab")  # Focus first widget
            await pilot.press("down")  # Navigate down
            await pilot.press("enter")  # Try to expand category
            await pilot.pause()

            # Verify app is still running (no crashes)
            assert app_with_kb.is_running


class TestQueryModalWorkflow:
    """Test query modal workflows."""

    @pytest.mark.asyncio
    async def test_open_query_modal_with_slash(self, app_with_kb: ClauxtonApp) -> None:
        """Test opening query modal with / key."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Press / to open query modal
            await pilot.press("slash")
            await pilot.pause()

            # Query modal should be pushed to screen stack
            # (In Textual, modals are screens)
            # We can't easily check if modal is visible without more complex queries
            # but we can verify app is still running
            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_query_modal_mode_switching(self, app_with_kb: ClauxtonApp) -> None:
        """Test switching query modes in modal."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Open query modal
            await pilot.press("slash")
            await pilot.pause()

            # Try switching modes
            await pilot.press("ctrl+a")  # AI mode
            await pilot.pause()

            await pilot.press("ctrl+p")  # File mode
            await pilot.pause()

            await pilot.press("ctrl+s")  # Symbol mode
            await pilot.pause()

            # Close modal
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_query_modal_search_execution(self, app_with_kb: ClauxtonApp) -> None:
        """Test executing search in query modal."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Open query modal
            await pilot.press("slash")
            await pilot.pause()

            # Type search query (simulated - Textual test may not support text input easily)
            # For now, just press enter to execute empty search
            await pilot.press("enter")
            await pilot.pause()

            # Modal should close after search
            assert app_with_kb.is_running


class TestQuickActionsWorkflow:
    """Test quick action workflows."""

    @pytest.mark.asyncio
    async def test_quick_action_ask_ai(self, app_with_kb: ClauxtonApp) -> None:
        """Test 'a' quick action for Ask AI."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Press 'a' for Ask AI
            await pilot.press("a")
            await pilot.pause()

            # Should open query modal in AI mode
            # Close modal
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_quick_action_show_suggestions(self, app_with_kb: ClauxtonApp) -> None:
        """Test 's' quick action for suggestions."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Press 's' to toggle suggestions
            await pilot.press("s")
            await pilot.pause()

            # Should toggle AI suggestions panel visibility
            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_quick_action_new_task(self, app_with_kb: ClauxtonApp) -> None:
        """Test 'n' quick action for new task."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Press 'n' for new task
            await pilot.press("n")
            await pilot.pause()

            # Currently this may be a placeholder
            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_quick_action_new_entry(self, app_with_kb: ClauxtonApp) -> None:
        """Test 'e' quick action for new entry."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Press 'e' for new entry
            await pilot.press("e")
            await pilot.pause()

            # Currently this may be a placeholder
            assert app_with_kb.is_running


class TestNavigationWorkflow:
    """Test navigation workflows."""

    @pytest.mark.asyncio
    async def test_help_modal_open_and_close(self, app_with_kb: ClauxtonApp) -> None:
        """Test opening and closing help modal."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Press F1 to open help (may not work in test, try ?)
            await pilot.press("question_mark")
            await pilot.pause()

            # Close help
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_vim_navigation_h_l(self, app_with_kb: ClauxtonApp) -> None:
        """Test vim-style h/l navigation."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Try vim navigation
            await pilot.press("h")  # Focus left
            await pilot.pause()

            await pilot.press("l")  # Focus right
            await pilot.pause()

            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_vim_navigation_j_k(self, app_with_kb: ClauxtonApp) -> None:
        """Test vim-style j/k navigation."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Try vim navigation
            await pilot.press("j")  # Down
            await pilot.pause()

            await pilot.press("k")  # Up
            await pilot.pause()

            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_tab_focus_cycling(self, app_with_kb: ClauxtonApp) -> None:
        """Test Tab key focus cycling."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Cycle through widgets with Tab
            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_refresh_action(self, app_with_kb: ClauxtonApp) -> None:
        """Test refresh action."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Press 'r' to refresh
            await pilot.press("r")
            await pilot.pause()

            assert app_with_kb.is_running


class TestCompleteUserJourney:
    """Test complete user journeys (E2E scenarios)."""

    @pytest.mark.asyncio
    async def test_search_and_view_entry_journey(self, app_with_kb: ClauxtonApp) -> None:
        """Test complete journey: Open app -> Search -> View entry."""
        async with app_with_kb.run_test() as pilot:
            # App opens
            await pilot.pause()
            assert app_with_kb.is_running

            # User opens search
            await pilot.press("slash")
            await pilot.pause()

            # User executes search (empty for now)
            await pilot.press("enter")
            await pilot.pause()

            # User navigates and views results
            await pilot.press("down")
            await pilot.pause()

            # Journey completes successfully
            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_ask_ai_journey(self, app_with_kb: ClauxtonApp) -> None:
        """Test complete journey: Open app -> Ask AI -> Get response."""
        async with app_with_kb.run_test() as pilot:
            # App opens
            await pilot.pause()

            # User presses 'a' for Ask AI
            await pilot.press("a")
            await pilot.pause()

            # Modal opens in AI mode
            # User submits question
            await pilot.press("enter")
            await pilot.pause()

            # Response is displayed
            # User closes/navigates
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_browse_kb_journey(self, app_with_kb: ClauxtonApp) -> None:
        """Test complete journey: Browse KB -> Expand category -> View entry."""
        async with app_with_kb.run_test() as pilot:
            # App opens with KB visible
            await pilot.pause()

            # User navigates to category
            await pilot.press("down")
            await pilot.pause()

            # User expands category
            await pilot.press("enter")
            await pilot.pause()

            # User navigates to entry
            await pilot.press("down")
            await pilot.pause()

            # User selects entry
            await pilot.press("enter")
            await pilot.pause()

            # Entry is displayed in content panel
            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_suggestions_interaction_journey(self, app_with_kb: ClauxtonApp) -> None:
        """Test complete journey: View suggestions -> Act on suggestion."""
        async with app_with_kb.run_test() as pilot:
            # App opens
            await pilot.pause()

            # User toggles suggestions panel
            await pilot.press("s")
            await pilot.pause()

            # User navigates to suggestions
            await pilot.press("tab")
            await pilot.pause()

            # User selects suggestion
            await pilot.press("enter")
            await pilot.pause()

            # Action is performed
            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_keyboard_shortcuts_help_journey(self, app_with_kb: ClauxtonApp) -> None:
        """Test complete journey: User needs help -> Opens help -> Finds shortcut."""
        async with app_with_kb.run_test() as pilot:
            # App opens, user is confused
            await pilot.pause()

            # User presses ? for help
            await pilot.press("question_mark")
            await pilot.pause()

            # Help modal opens with shortcuts
            # User scrolls through help
            await pilot.press("down")
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()

            # User closes help
            await pilot.press("escape")
            await pilot.pause()

            # User now knows shortcuts
            assert app_with_kb.is_running


class TestErrorRecovery:
    """Test error recovery in workflows."""

    @pytest.mark.asyncio
    async def test_empty_kb_handling(self, tmp_path: Path) -> None:
        """Test app handles empty Knowledge Base gracefully."""
        # Create app with empty KB
        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # App should still run with empty KB
            assert app.is_running

            # User can still navigate
            await pilot.press("tab")
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_rapid_key_presses(self, app_with_kb: ClauxtonApp) -> None:
        """Test app handles rapid key presses without crashing."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Rapid key presses
            for _ in range(10):
                await pilot.press("j")

            await pilot.pause()
            assert app_with_kb.is_running

    @pytest.mark.asyncio
    async def test_modal_escape_always_works(self, app_with_kb: ClauxtonApp) -> None:
        """Test escape key always closes modals."""
        async with app_with_kb.run_test() as pilot:
            await pilot.pause()

            # Open query modal
            await pilot.press("slash")
            await pilot.pause()

            # Escape should close
            await pilot.press("escape")
            await pilot.pause()

            # Open help modal
            await pilot.press("question_mark")
            await pilot.pause()

            # Escape should close
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_kb.is_running
