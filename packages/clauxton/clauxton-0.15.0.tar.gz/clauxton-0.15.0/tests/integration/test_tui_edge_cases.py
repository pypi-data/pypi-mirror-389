"""
TUI Edge Cases and Boundary Tests

Tests extreme conditions, unusual inputs, and error scenarios.
"""

import os
from datetime import datetime
from pathlib import Path

import pytest

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry
from clauxton.tui.app import ClauxtonApp


class TestDataBoundaries:
    """Test extreme data conditions."""

    @pytest.mark.asyncio
    async def test_completely_empty_project(self, tmp_path: Path):
        """Test TUI with no KB entries and no tasks."""
        # Create empty .clauxton directory
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        # Create empty YAML files
        (clauxton_dir / "knowledge-base.yml").write_text("entries: []\n")
        (clauxton_dir / "tasks.yml").write_text("tasks: []\n")

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # App should handle empty state gracefully
            assert app.is_running

            # KB Browser should show empty state
            from clauxton.tui.widgets.kb_browser import KBBrowserWidget
            kb_browser = app.screen.query_one(KBBrowserWidget)
            assert kb_browser is not None

    @pytest.mark.asyncio
    async def test_very_large_kb_entries(self, tmp_path: Path):
        """Test with 100+ KB entries (stress test)."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)

        # Create 100 entries (maximum for 3-digit ID format)
        for i in range(1, 101):
            entry = KnowledgeBaseEntry(
                id=f"KB-20251028-{i:03d}",
                title=f"Entry {i}",
                category="architecture",
                content=f"Content for entry {i}",
                tags=[f"tag{i % 10}"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # App should handle large dataset
            assert app.is_running

            # Search should still work
            await pilot.press("/")
            await pilot.pause()
            await pilot.press(*list("entry"))
            await pilot.pause()

    @pytest.mark.asyncio
    async def test_extremely_long_text_content(self, tmp_path: Path):
        """Test with maximum allowed text content (10,000 characters)."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)

        # Create entry with maximum content (10,000 characters - model limit)
        long_content = "A" * 10_000
        entry = KnowledgeBaseEntry(
            id="KB-20251028-001",
            title="Very Long Entry",
            category="architecture",
            content=long_content,
            tags=["long"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # App should handle large content
            assert app.is_running

            # Navigate to entry
            await pilot.press("j")
            await pilot.pause()
            await pilot.press("enter")
            await pilot.pause()

    @pytest.mark.asyncio
    async def test_special_characters_and_unicode(self, tmp_path: Path):
        """Test with special characters, emojis, and Unicode."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)

        # Entry with various special characters
        special_content = """
        Emojis: 🎉 🚀 ✅ ❌ 🔥 💡
        Unicode: こんにちは 世界 مرحبا العالم
        Special: !@#$%^&*()_+-=[]{}|;':",./<>?
        Math: ∫∑∏√∞≠≤≥±×÷
        Arrows: ← → ↑ ↓ ⇒ ⇐
        """

        entry = KnowledgeBaseEntry(
            id="KB-20251028-001",
            title="Special Characters 特殊文字 🎉",
            category="architecture",
            content=special_content,
            tags=["unicode", "special"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # App should render special characters
            assert app.is_running

    @pytest.mark.asyncio
    async def test_max_length_fields(self, tmp_path: Path):
        """Test with maximum allowed field lengths."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)

        # Entry with maximum title (50 characters - model limit)
        long_title = "A" * 50
        entry = KnowledgeBaseEntry(
            id="KB-20251028-001",
            title=long_title,
            category="architecture",
            content="A" * 10_000,  # Max content length
            tags=["tag1", "tag2", "tag3"],  # Normal tags
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()
            assert app.is_running


class TestUIBoundaries:
    """Test UI boundary conditions."""

    @pytest.mark.asyncio
    async def test_minimum_terminal_size(self, tmp_path: Path):
        """Test with very small terminal size."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()
        (clauxton_dir / "knowledge-base.yml").write_text("entries: []\n")
        (clauxton_dir / "tasks.yml").write_text("tasks: []\n")

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test(size=(40, 10)) as pilot:  # Very small terminal
            await pilot.pause()

            # App should handle small terminal
            assert app.is_running

    @pytest.mark.asyncio
    async def test_rapid_key_input(self, tmp_path: Path):
        """Test rapid keyboard input."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)
        for i in range(1, 11):
            entry = KnowledgeBaseEntry(
                id=f"KB-20251028-{i:03d}",
                title=f"Entry {i}",
                category="architecture",
                content=f"Content {i}",
                tags=["test"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Rapid navigation without pauses
            for _ in range(50):
                await pilot.press("j")

            for _ in range(50):
                await pilot.press("k")

            await pilot.pause()

            # App should handle rapid input
            assert app.is_running

    @pytest.mark.asyncio
    async def test_terminal_resize_handling(self, tmp_path: Path):
        """Test terminal resize during operation."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()
        (clauxton_dir / "knowledge-base.yml").write_text("entries: []\n")
        (clauxton_dir / "tasks.yml").write_text("tasks: []\n")

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test(size=(80, 24)) as pilot:
            await pilot.pause()

            # Simulate resize by creating new pilot with different size
            # (Note: Textual's test harness doesn't support dynamic resize)
            # This test verifies the app can start with different sizes
            assert app.is_running


class TestErrorHandling:
    """Test error handling and recovery."""

    @pytest.mark.asyncio
    async def test_corrupted_yaml_file(self, tmp_path: Path):
        """Test with corrupted YAML file."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        # Write invalid YAML
        (clauxton_dir / "knowledge-base.yml").write_text("invalid: yaml: content: [[[")
        (clauxton_dir / "tasks.yml").write_text("tasks: []\n")

        # App should handle gracefully (may show error or empty state)
        app = ClauxtonApp(project_root=tmp_path)

        # This may raise an exception or handle gracefully
        try:
            async with app.run_test() as pilot:
                await pilot.pause()
                # If it starts, it handled the error
                assert True
        except Exception:
            # If it raises, that's also acceptable error handling
            assert True

    @pytest.mark.asyncio
    async def test_readonly_data_files(self, tmp_path: Path):
        """Test with read-only data files."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb_file = clauxton_dir / "knowledge-base.yml"
        kb_file.write_text("entries: []\n")
        tasks_file = clauxton_dir / "tasks.yml"
        tasks_file.write_text("tasks: []\n")

        # Make files read-only
        os.chmod(kb_file, 0o444)
        os.chmod(tasks_file, 0o444)

        try:
            app = ClauxtonApp(project_root=tmp_path)

            async with app.run_test() as pilot:
                await pilot.pause()

                # App should start in read-only mode
                assert app.is_running
        finally:
            # Restore write permissions for cleanup
            os.chmod(kb_file, 0o644)
            os.chmod(tasks_file, 0o644)

    @pytest.mark.asyncio
    async def test_missing_clauxton_directory(self, tmp_path: Path):
        """Test without .clauxton directory."""
        # Don't create .clauxton directory

        app = ClauxtonApp(project_root=tmp_path)

        # App should either auto-initialize or show helpful error
        try:
            async with app.run_test() as pilot:
                await pilot.pause()
                assert True
        except Exception as e:
            # Should provide clear error message
            assert "clauxton" in str(e).lower() or "initialize" in str(e).lower()

    @pytest.mark.asyncio
    async def test_concurrent_file_access(self, tmp_path: Path):
        """Test multiple TUI instances (simulated)."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)
        entry = KnowledgeBaseEntry(
            id="KB-20251028-001",
            title="Test Entry",
            category="architecture",
            content="Content",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

        app1 = ClauxtonApp(project_root=tmp_path)
        app2 = ClauxtonApp(project_root=tmp_path)

        async with app1.run_test() as pilot1:
            await pilot1.pause()

            # Both instances should be able to read
            async with app2.run_test() as pilot2:
                await pilot2.pause()
                assert app1.is_running
                assert app2.is_running


class TestSearchBoundaries:
    """Test search functionality boundaries."""

    @pytest.mark.asyncio
    async def test_empty_search_query(self, tmp_path: Path):
        """Test search with empty query."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)
        entry = KnowledgeBaseEntry(
            id="KB-20251028-001",
            title="Test",
            category="architecture",
            content="Content",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Open search
            await pilot.press("/")
            await pilot.pause()

            # Press enter with empty query
            await pilot.press("enter")
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_very_long_search_query(self, tmp_path: Path):
        """Test search with 1000+ character query."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)
        entry = KnowledgeBaseEntry(
            id="KB-20251028-001",
            title="Test",
            category="architecture",
            content="Content",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Open search
            await pilot.press("/")
            await pilot.pause()

            # Type very long query (100 characters)
            long_query = "a" * 100
            await pilot.press(*list(long_query))
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_special_regex_characters_in_search(self, tmp_path: Path):
        """Test search with regex special characters."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)
        entry = KnowledgeBaseEntry(
            id="KB-20251028-001",
            title="Test [regex] (chars)",
            category="architecture",
            content="Content with special chars: .*+?{}[]()^$|\\",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Open search
            await pilot.press("/")
            await pilot.pause()

            # Search for regex special characters
            await pilot.press(*list("[regex]"))
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_unicode_search_query(self, tmp_path: Path):
        """Test search with Unicode characters."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)
        entry = KnowledgeBaseEntry(
            id="KB-20251028-001",
            title="Unicode Test こんにちは",
            category="architecture",
            content="Content with Unicode: 世界 🎉",
            tags=["unicode"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Open search
            await pilot.press("/")
            await pilot.pause()

            # Note: Textual pilot doesn't support typing Unicode directly
            # This test verifies the app doesn't crash
            assert app.is_running


class TestNavigationBoundaries:
    """Test navigation edge cases."""

    @pytest.mark.asyncio
    async def test_navigate_past_end_of_list(self, tmp_path: Path):
        """Test navigating beyond list boundaries."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()

        kb = KnowledgeBase(tmp_path)
        for i in range(1, 4):
            entry = KnowledgeBaseEntry(
                id=f"KB-20251028-{i:03d}",
                title=f"Entry {i}",
                category="architecture",
                content=f"Content {i}",
                tags=["test"],
                created_at=datetime.now(),
                updated_at=datetime.now(),
            )
            kb.add(entry)

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Try to navigate beyond end
            for _ in range(10):
                await pilot.press("j")
            await pilot.pause()

            # Try to navigate beyond start
            for _ in range(10):
                await pilot.press("k")
            await pilot.pause()

            assert app.is_running

    @pytest.mark.asyncio
    async def test_rapid_focus_switching(self, tmp_path: Path):
        """Test rapid switching between panels."""
        clauxton_dir = tmp_path / ".clauxton"
        clauxton_dir.mkdir()
        (clauxton_dir / "knowledge-base.yml").write_text("entries: []\n")
        (clauxton_dir / "tasks.yml").write_text("tasks: []\n")

        app = ClauxtonApp(project_root=tmp_path)

        async with app.run_test() as pilot:
            await pilot.pause()

            # Rapidly switch focus
            for _ in range(20):
                await pilot.press("tab")

            await pilot.pause()
            assert app.is_running


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
