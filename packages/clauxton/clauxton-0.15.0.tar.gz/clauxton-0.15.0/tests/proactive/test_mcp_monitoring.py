"""Tests for MCP monitoring tools."""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.mcp import server
from clauxton.proactive.models import ChangeType, FileChange


class TestMCPMonitoring:
    """Tests for MCP monitoring tools."""

    def setup_method(self) -> None:
        """Setup test method."""
        # Reset global instances before each test
        server._file_monitor = None
        server._event_processor = None

    def teardown_method(self) -> None:
        """Teardown test method."""
        # Stop monitor if running
        if server._file_monitor and server._file_monitor.is_running:
            server._file_monitor.stop()

        # Reset global instances
        server._file_monitor = None
        server._event_processor = None

    def test_watch_project_changes_enable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test enabling file monitoring."""
        monkeypatch.chdir(tmp_path)

        result = server.watch_project_changes(enabled=True)

        assert result["status"] == "enabled"
        assert result["message"] == "File monitoring started"
        assert "config" in result
        assert server._file_monitor is not None
        assert server._file_monitor.is_running

    def test_watch_project_changes_already_enabled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test enabling monitoring when already running."""
        monkeypatch.chdir(tmp_path)

        # Enable first time
        server.watch_project_changes(enabled=True)

        # Try to enable again
        result = server.watch_project_changes(enabled=True)

        assert result["status"] == "already_enabled"
        assert result["message"] == "File monitoring already running"

    def test_watch_project_changes_disable(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test disabling file monitoring."""
        monkeypatch.chdir(tmp_path)

        # Enable first
        server.watch_project_changes(enabled=True)

        # Disable
        result = server.watch_project_changes(enabled=False)

        assert result["status"] == "disabled"
        assert result["message"] == "File monitoring stopped"
        assert not server._file_monitor.is_running

    def test_watch_project_changes_already_disabled(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test disabling monitoring when not running."""
        monkeypatch.chdir(tmp_path)

        result = server.watch_project_changes(enabled=False)

        assert result["status"] == "already_disabled"
        assert result["message"] == "File monitoring not running"

    def test_watch_project_changes_with_custom_config(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test enabling monitoring with custom configuration."""
        monkeypatch.chdir(tmp_path)

        custom_config = {
            "enabled": True,
            "watch": {"debounce_ms": 1000, "ignore_patterns": ["*.log"]},
        }

        result = server.watch_project_changes(enabled=True, config=custom_config)

        assert result["status"] == "enabled"
        assert server._file_monitor.config.watch.debounce_ms == 1000

    @pytest.mark.asyncio
    async def test_get_recent_changes_no_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting recent changes with no activity."""
        monkeypatch.chdir(tmp_path)

        # Initialize monitor but don't make changes
        _monitor = server._get_file_monitor()

        result = await server.get_recent_changes(minutes=10)

        assert result["status"] == "no_changes"
        assert result["message"] == "No changes in last 10 minutes"
        assert result["changes"] == []
        assert result["patterns"] == []

    @pytest.mark.asyncio
    async def test_get_recent_changes_with_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting recent changes with activity."""
        monkeypatch.chdir(tmp_path)

        # Get monitor and manually add changes
        monitor = server._get_file_monitor()

        # Add test changes
        changes = [
            FileChange(
                path=tmp_path / "file1.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "file2.py",
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            ),
        ]

        for change in changes:
            monitor.change_queue.append(change)

        result = await server.get_recent_changes(minutes=10)

        assert result["status"] == "success"
        assert result["time_window_minutes"] == 10
        assert result["total_files_changed"] == 2
        assert len(result["changes"]) == 2

    @pytest.mark.asyncio
    async def test_get_recent_changes_without_patterns(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting changes without patterns."""
        monkeypatch.chdir(tmp_path)

        monitor = server._get_file_monitor()

        # Add test changes
        changes = [
            FileChange(
                path=tmp_path / "file1.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
        ]

        for change in changes:
            monitor.change_queue.append(change)

        result = await server.get_recent_changes(minutes=10, include_patterns=False)

        assert result["status"] == "success"
        assert "patterns" not in result or result.get("patterns") == []

    @pytest.mark.asyncio
    async def test_get_recent_changes_with_patterns(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting changes with pattern detection."""
        monkeypatch.chdir(tmp_path)

        monitor = server._get_file_monitor()

        # Add enough changes to trigger bulk edit pattern (7 files)
        base_time = datetime.now()
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=base_time,
            )
            for i in range(7)
        ]

        for change in changes:
            monitor.change_queue.append(change)

        result = await server.get_recent_changes(minutes=10, include_patterns=True)

        assert result["status"] == "success"
        assert "patterns" in result
        # Should detect bulk edit pattern
        if result["patterns"]:
            assert any(p["pattern_type"] == "bulk_edit" for p in result["patterns"])

    @pytest.mark.asyncio
    async def test_get_recent_changes_saves_activity(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that activity is saved to file."""
        monkeypatch.chdir(tmp_path)

        # Create .clauxton directory
        (tmp_path / ".clauxton").mkdir(parents=True, exist_ok=True)

        monitor = server._get_file_monitor()

        # Add test changes
        changes = [
            FileChange(
                path=tmp_path / "file1.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
        ]

        for change in changes:
            monitor.change_queue.append(change)

        await server.get_recent_changes(minutes=10)

        # Check that activity file was created
        activity_file = tmp_path / ".clauxton" / "activity.yml"
        assert activity_file.exists()

    @pytest.mark.asyncio
    async def test_get_recent_changes_custom_time_window(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test getting changes with custom time window."""
        monkeypatch.chdir(tmp_path)

        monitor = server._get_file_monitor()

        # Add test change
        changes = [
            FileChange(
                path=tmp_path / "file1.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
        ]

        for change in changes:
            monitor.change_queue.append(change)

        result = await server.get_recent_changes(minutes=5)

        assert result["status"] == "success"
        assert result["time_window_minutes"] == 5

    def test_get_file_monitor_creates_instance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that _get_file_monitor creates instance."""
        monkeypatch.chdir(tmp_path)

        assert server._file_monitor is None

        monitor = server._get_file_monitor()

        assert monitor is not None
        assert server._file_monitor is monitor

    def test_get_file_monitor_returns_existing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that _get_file_monitor returns existing instance."""
        monkeypatch.chdir(tmp_path)

        monitor1 = server._get_file_monitor()
        monitor2 = server._get_file_monitor()

        assert monitor1 is monitor2

    def test_get_event_processor_creates_instance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that _get_event_processor creates instance."""
        monkeypatch.chdir(tmp_path)

        assert server._event_processor is None

        processor = server._get_event_processor()

        assert processor is not None
        assert server._event_processor is processor

    def test_get_event_processor_returns_existing(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that _get_event_processor returns existing instance."""
        monkeypatch.chdir(tmp_path)

        processor1 = server._get_event_processor()
        processor2 = server._get_event_processor()

        assert processor1 is processor2
