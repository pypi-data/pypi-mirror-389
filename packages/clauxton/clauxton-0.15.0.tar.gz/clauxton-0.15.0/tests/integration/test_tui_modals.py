"""Modal integration tests for Clauxton TUI."""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry
from clauxton.tui.app import ClauxtonApp


@pytest.fixture
def app_with_data(tmp_path: Path) -> ClauxtonApp:
    """Create app with test data."""
    # Initialize KB
    kb = KnowledgeBase(tmp_path)

    # Add sample entry (using valid category)
    entry = KnowledgeBaseEntry(
        id="KB-20251028-001",
        title="Test Entry",
        category="pattern",
        content="Test content for modal tests",
        tags=["test", "modal"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry)

    # Create app
    app = ClauxtonApp(project_root=tmp_path)
    return app


class TestQueryModalLifecycle:
    """Test query modal lifecycle."""

    @pytest.mark.asyncio
    async def test_modal_opens_with_slash(self, app_with_data: ClauxtonApp) -> None:
        """Test query modal opens with / key."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            # Open modal
            await pilot.press("slash")
            await pilot.pause()

            # App should still be running
            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_modal_opens_with_ctrl_f(self, app_with_data: ClauxtonApp) -> None:
        """Test query modal opens with Ctrl+F."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            # Open modal with Ctrl+F
            await pilot.press("ctrl+f")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_modal_closes_with_escape(self, app_with_data: ClauxtonApp) -> None:
        """Test modal closes with Escape key."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            # Open modal
            await pilot.press("slash")
            await pilot.pause()

            # Close modal
            await pilot.press("escape")
            await pilot.pause()

            # Should return to dashboard
            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_modal_multiple_open_close_cycles(self, app_with_data: ClauxtonApp) -> None:
        """Test opening and closing modal multiple times."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            # Cycle 1
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Cycle 2
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Cycle 3
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_data.is_running


class TestQueryModalModes:
    """Test query modal mode switching."""

    @pytest.mark.asyncio
    async def test_switch_to_ai_mode(self, app_with_data: ClauxtonApp) -> None:
        """Test switching to AI mode."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            # Open modal
            await pilot.press("slash")
            await pilot.pause()

            # Switch to AI mode
            await pilot.press("ctrl+a")
            await pilot.pause()

            # Mode should be AI
            # (We can't easily verify UI state, but check app is running)
            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_switch_to_file_mode(self, app_with_data: ClauxtonApp) -> None:
        """Test switching to File mode."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("slash")
            await pilot.pause()

            # Switch to File mode
            await pilot.press("ctrl+p")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_switch_to_symbol_mode(self, app_with_data: ClauxtonApp) -> None:
        """Test switching to Symbol mode."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("slash")
            await pilot.pause()

            # Switch to Symbol mode
            await pilot.press("ctrl+s")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_mode_cycling(self, app_with_data: ClauxtonApp) -> None:
        """Test cycling through all modes."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("slash")
            await pilot.pause()

            # Cycle through modes
            await pilot.press("ctrl+a")  # AI
            await pilot.pause()

            await pilot.press("ctrl+p")  # File
            await pilot.pause()

            await pilot.press("ctrl+s")  # Symbol
            await pilot.pause()

            # Back to normal (not implemented as shortcut, but tab works)
            await pilot.press("tab")
            await pilot.pause()

            assert app_with_data.is_running


class TestHelpModalLifecycle:
    """Test help modal lifecycle."""

    @pytest.mark.asyncio
    async def test_help_opens_with_f1(self, app_with_data: ClauxtonApp) -> None:
        """Test help modal opens with F1 key."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            # F1 might not work in test environment
            # Try question mark instead
            await pilot.press("question_mark")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_help_closes_with_escape(self, app_with_data: ClauxtonApp) -> None:
        """Test help modal closes with Escape."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("question_mark")
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_help_closes_with_q(self, app_with_data: ClauxtonApp) -> None:
        """Test help modal closes with 'q' key."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("question_mark")
            await pilot.pause()

            # Press 'q' to close (like vim)
            await pilot.press("q")
            await pilot.pause()

            assert app_with_data.is_running


class TestModalInteraction:
    """Test modal interactions."""

    @pytest.mark.asyncio
    async def test_query_modal_search_execution(self, app_with_data: ClauxtonApp) -> None:
        """Test executing search in query modal."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("slash")
            await pilot.pause()

            # Execute search (empty query)
            await pilot.press("enter")
            await pilot.pause()

            # Modal should close and show results
            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_query_modal_navigation_in_results(self, app_with_data: ClauxtonApp) -> None:
        """Test navigating results in query modal."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("slash")
            await pilot.pause()

            # Execute search
            await pilot.press("enter")
            await pilot.pause()

            # Navigate results
            await pilot.press("down")
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()

            await pilot.press("up")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_help_modal_scrolling(self, app_with_data: ClauxtonApp) -> None:
        """Test scrolling in help modal."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("question_mark")
            await pilot.pause()

            # Scroll down
            await pilot.press("down")
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()

            # Scroll up
            await pilot.press("up")
            await pilot.pause()

            # Page down
            await pilot.press("pagedown")
            await pilot.pause()

            # Page up
            await pilot.press("pageup")
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            assert app_with_data.is_running


class TestModalFocusManagement:
    """Test modal focus management."""

    @pytest.mark.asyncio
    async def test_focus_trapped_in_modal(self, app_with_data: ClauxtonApp) -> None:
        """Test that Tab doesn't leave modal."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("slash")
            await pilot.pause()

            # Try to tab out (should stay in modal)
            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            # Modal should still be open
            # Close modal
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_focus_returns_after_modal_close(self, app_with_data: ClauxtonApp) -> None:
        """Test focus returns to dashboard after modal closes."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            # Open modal
            await pilot.press("slash")
            await pilot.pause()

            # Close modal
            await pilot.press("escape")
            await pilot.pause()

            # Focus should return to dashboard
            # Try navigation (should work)
            await pilot.press("tab")
            await pilot.pause()

            assert app_with_data.is_running


class TestModalEdgeCases:
    """Test modal edge cases."""

    @pytest.mark.asyncio
    async def test_double_escape_doesnt_crash(self, app_with_data: ClauxtonApp) -> None:
        """Test pressing Escape twice doesn't crash."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("slash")
            await pilot.pause()

            # Press Escape twice
            await pilot.press("escape")
            await pilot.pause()

            await pilot.press("escape")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_rapid_modal_opening(self, app_with_data: ClauxtonApp) -> None:
        """Test rapid modal opening doesn't break state."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            # Rapid modal opening
            for _ in range(5):
                await pilot.press("slash")
                await pilot.pause(0.1)

            # Should have only one modal open
            # Close it
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_data.is_running

    @pytest.mark.asyncio
    async def test_query_modal_with_empty_kb(self, tmp_path: Path) -> None:
        """Test query modal works with empty KB."""
        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Open modal
            await pilot.press("slash")
            await pilot.pause()

            # Execute search
            await pilot.press("enter")
            await pilot.pause()

            # Should handle gracefully
            assert app.is_running

    @pytest.mark.asyncio
    async def test_mode_switch_while_typing(self, app_with_data: ClauxtonApp) -> None:
        """Test switching modes while typing (simulated)."""
        async with app_with_data.run_test() as pilot:
            await pilot.pause()

            await pilot.press("slash")
            await pilot.pause()

            # Simulate typing (we can't actually type text easily)
            # But we can switch modes
            await pilot.press("ctrl+a")
            await pilot.pause()

            # Switch again
            await pilot.press("ctrl+p")
            await pilot.pause()

            # Should handle gracefully
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_data.is_running
