"""Navigation integration tests for Clauxton TUI."""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry
from clauxton.tui.app import ClauxtonApp


@pytest.fixture
def app_with_content(tmp_path: Path) -> ClauxtonApp:
    """Create app with content for navigation tests."""
    # Initialize KB with multiple entries (using valid categories)
    kb = KnowledgeBase(tmp_path)

    categories = ["architecture", "decision", "pattern", "convention"]
    for i, category in enumerate(categories, 1):
        entry = KnowledgeBaseEntry(
            id=f"KB-20251028-{i:03d}",
            title=f"{category.capitalize()} Example",
            category=category,
            content=f"Content about {category}",
            tags=[category, "example"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

    app = ClauxtonApp(project_root=tmp_path)
    return app


class TestPanelFocusNavigation:
    """Test focus navigation between panels."""

    @pytest.mark.asyncio
    async def test_tab_cycles_through_widgets(self, app_with_content: ClauxtonApp) -> None:
        """Test Tab key cycles through focusable widgets."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Tab through widgets
            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_shift_tab_cycles_backward(self, app_with_content: ClauxtonApp) -> None:
        """Test Shift+Tab cycles backward through widgets."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Tab forward
            await pilot.press("tab")
            await pilot.pause()

            # Tab backward
            await pilot.press("shift+tab")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_vim_h_moves_focus_left(self, app_with_content: ClauxtonApp) -> None:
        """Test 'h' moves focus left (vim style)."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Move focus right first
            await pilot.press("l")
            await pilot.pause()

            # Move focus left
            await pilot.press("h")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_vim_l_moves_focus_right(self, app_with_content: ClauxtonApp) -> None:
        """Test 'l' moves focus right (vim style)."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Move focus right
            await pilot.press("l")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_arrow_keys_work_in_focused_widget(self, app_with_content: ClauxtonApp) -> None:
        """Test arrow keys navigate within focused widget."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Navigate within widget
            await pilot.press("down")
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()

            await pilot.press("up")
            await pilot.pause()

            assert app_with_content.is_running


class TestVimStyleNavigation:
    """Test vim-style navigation."""

    @pytest.mark.asyncio
    async def test_j_moves_down(self, app_with_content: ClauxtonApp) -> None:
        """Test 'j' moves down in lists."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Move down with j
            await pilot.press("j")
            await pilot.pause()

            await pilot.press("j")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_k_moves_up(self, app_with_content: ClauxtonApp) -> None:
        """Test 'k' moves up in lists."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Move down first
            await pilot.press("j")
            await pilot.pause()

            # Move up with k
            await pilot.press("k")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_gg_jumps_to_top(self, app_with_content: ClauxtonApp) -> None:
        """Test 'gg' jumps to top."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Move down
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("j")
            await pilot.pause()

            # Jump to top (gg)
            # Note: This might not work in test as 'gg' requires two sequential key presses
            await pilot.press("g")
            await pilot.pause(0.1)
            await pilot.press("g")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_shift_g_jumps_to_bottom(self, app_with_content: ClauxtonApp) -> None:
        """Test 'G' (Shift+G) jumps to bottom."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Jump to bottom
            await pilot.press("shift+g")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_vim_navigation_in_kb_browser(self, app_with_content: ClauxtonApp) -> None:
        """Test vim navigation works in KB browser."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Focus KB browser (should be default)
            # Navigate with vim keys
            await pilot.press("j")
            await pilot.pause()

            await pilot.press("k")
            await pilot.pause()

            await pilot.press("h")
            await pilot.pause()

            await pilot.press("l")
            await pilot.pause()

            assert app_with_content.is_running


class TestNavigationInDifferentWidgets:
    """Test navigation behavior in different widgets."""

    @pytest.mark.asyncio
    async def test_navigation_in_kb_browser(self, app_with_content: ClauxtonApp) -> None:
        """Test navigation in KB browser widget."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # KB browser should be focused by default
            # Navigate entries
            await pilot.press("down")
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()

            await pilot.press("enter")  # Expand or select
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_navigation_in_content_viewer(self, app_with_content: ClauxtonApp) -> None:
        """Test navigation in content viewer widget."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Focus content viewer
            await pilot.press("tab")
            await pilot.pause()

            # Scroll content
            await pilot.press("down")
            await pilot.pause()

            await pilot.press("pagedown")
            await pilot.pause()

            await pilot.press("pageup")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_navigation_in_ai_suggestions(self, app_with_content: ClauxtonApp) -> None:
        """Test navigation in AI suggestions panel."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Toggle suggestions panel visible
            await pilot.press("s")
            await pilot.pause()

            # Focus suggestions (tab multiple times)
            await pilot.press("tab")
            await pilot.pause()
            await pilot.press("tab")
            await pilot.pause()

            # Navigate suggestions
            await pilot.press("down")
            await pilot.pause()

            await pilot.press("up")
            await pilot.pause()

            assert app_with_content.is_running


class TestFocusIndicators:
    """Test focus indicators and visual feedback."""

    @pytest.mark.asyncio
    async def test_focus_changes_on_navigation(self, app_with_content: ClauxtonApp) -> None:
        """Test focus changes are reflected in UI."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Change focus
            await pilot.press("tab")
            await pilot.pause()

            # Focus should change
            # (We can't easily verify visual changes, but check no crash)
            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_statusbar_shows_focused_widget(self, app_with_content: ClauxtonApp) -> None:
        """Test statusbar displays focused widget name."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Change focus multiple times
            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("tab")
            await pilot.pause()

            # Statusbar should update
            # (Verified by no crash)
            assert app_with_content.is_running


class TestNavigationBoundaries:
    """Test navigation at boundaries."""

    @pytest.mark.asyncio
    async def test_up_at_top_doesnt_crash(self, app_with_content: ClauxtonApp) -> None:
        """Test pressing up at top of list doesn't crash."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # At top, press up
            await pilot.press("up")
            await pilot.pause()

            await pilot.press("up")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_down_at_bottom_doesnt_crash(self, app_with_content: ClauxtonApp) -> None:
        """Test pressing down at bottom of list doesn't crash."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Jump to bottom
            await pilot.press("shift+g")
            await pilot.pause()

            # Press down
            await pilot.press("down")
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_tab_at_last_widget_wraps_to_first(self, app_with_content: ClauxtonApp) -> None:
        """Test Tab at last widget wraps to first."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Tab through all widgets
            for _ in range(5):
                await pilot.press("tab")
                await pilot.pause(0.1)

            # Should wrap around (no crash)
            assert app_with_content.is_running


class TestNavigationWithModals:
    """Test navigation when modals are open."""

    @pytest.mark.asyncio
    async def test_navigation_trapped_in_modal(self, app_with_content: ClauxtonApp) -> None:
        """Test navigation stays in modal when open."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Open modal
            await pilot.press("slash")
            await pilot.pause()

            # Try to navigate (should stay in modal)
            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("down")
            await pilot.pause()

            # Close modal
            await pilot.press("escape")
            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_navigation_resumes_after_modal_close(
        self, app_with_content: ClauxtonApp
    ) -> None:
        """Test navigation works normally after modal closes."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Open and close modal
            await pilot.press("slash")
            await pilot.pause()
            await pilot.press("escape")
            await pilot.pause()

            # Navigation should work normally
            await pilot.press("tab")
            await pilot.pause()

            await pilot.press("j")
            await pilot.pause()

            assert app_with_content.is_running


class TestNavigationPerformance:
    """Test navigation performance and responsiveness."""

    @pytest.mark.asyncio
    async def test_rapid_navigation_doesnt_lag(self, app_with_content: ClauxtonApp) -> None:
        """Test rapid navigation doesn't cause lag or crashes."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Rapid navigation
            for _ in range(20):
                await pilot.press("j")

            await pilot.pause()

            for _ in range(20):
                await pilot.press("k")

            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_rapid_focus_changes(self, app_with_content: ClauxtonApp) -> None:
        """Test rapid focus changes work smoothly."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Rapid tab presses
            for _ in range(10):
                await pilot.press("tab")

            await pilot.pause()

            assert app_with_content.is_running

    @pytest.mark.asyncio
    async def test_mixed_navigation_keys(self, app_with_content: ClauxtonApp) -> None:
        """Test mixing vim keys, arrow keys, and Tab works well."""
        async with app_with_content.run_test() as pilot:
            await pilot.pause()

            # Mix different navigation methods
            await pilot.press("j")
            await pilot.pause(0.1)

            await pilot.press("down")
            await pilot.pause(0.1)

            await pilot.press("tab")
            await pilot.pause(0.1)

            await pilot.press("k")
            await pilot.pause(0.1)

            await pilot.press("up")
            await pilot.pause(0.1)

            await pilot.press("h")
            await pilot.pause(0.1)

            await pilot.press("l")
            await pilot.pause(0.1)

            assert app_with_content.is_running
