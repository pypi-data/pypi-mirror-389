"""Tests for file monitoring."""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clauxton.proactive.config import MonitorConfig, WatchConfig
from clauxton.proactive.file_monitor import FileMonitor, IgnorePatternMatcher
from clauxton.proactive.models import ChangeType, FileChange


class TestIgnorePatternMatcher:
    """Tests for IgnorePatternMatcher."""

    def test_ignore_pyc_files(self) -> None:
        """Test ignoring .pyc files."""
        matcher = IgnorePatternMatcher(["*.pyc"])

        assert matcher.should_ignore(Path("test.pyc"))
        assert matcher.should_ignore(Path("foo/bar/test.pyc"))
        assert not matcher.should_ignore(Path("test.py"))

    def test_ignore_git_directory(self) -> None:
        """Test ignoring .git directory."""
        matcher = IgnorePatternMatcher([".git/**"])

        assert matcher.should_ignore(Path(".git/config"))
        assert matcher.should_ignore(Path(".git/objects/abc"))
        assert matcher.should_ignore(Path("foo/.git/config"))
        assert not matcher.should_ignore(Path("foo/bar.py"))

    def test_ignore_multiple_patterns(self) -> None:
        """Test multiple ignore patterns."""
        matcher = IgnorePatternMatcher(["*.pyc", ".git/**", "node_modules/**"])

        assert matcher.should_ignore(Path("test.pyc"))
        assert matcher.should_ignore(Path(".git/config"))
        assert matcher.should_ignore(Path("node_modules/package.json"))
        assert not matcher.should_ignore(Path("src/main.py"))


class TestFileMonitor:
    """Tests for FileMonitor."""

    def test_init(self, tmp_path: Path) -> None:
        """Test FileMonitor initialization."""
        monitor = FileMonitor(tmp_path)

        assert monitor.project_root == tmp_path.resolve()
        assert not monitor.is_running
        assert isinstance(monitor.config, MonitorConfig)

    def test_init_with_config(self, tmp_path: Path) -> None:
        """Test FileMonitor with custom config."""
        config = MonitorConfig(
            watch=WatchConfig(debounce_ms=1000, ignore_patterns=["*.log"])
        )
        monitor = FileMonitor(tmp_path, config=config)

        assert monitor.config.watch.debounce_ms == 1000
        assert "*.log" in monitor.config.watch.ignore_patterns

    def test_start_stop(self, tmp_path: Path) -> None:
        """Test starting and stopping monitor."""
        monitor = FileMonitor(tmp_path)

        assert not monitor.is_running

        monitor.start()
        assert monitor.is_running
        assert monitor.observer is not None

        monitor.stop()
        assert not monitor.is_running
        assert monitor.observer is None

    def test_start_already_running(self, tmp_path: Path) -> None:
        """Test starting monitor when already running."""
        monitor = FileMonitor(tmp_path)
        monitor.start()

        with pytest.raises(RuntimeError, match="already running"):
            monitor.start()

        monitor.stop()

    def test_detect_file_creation(self, tmp_path: Path) -> None:
        """Test detecting file creation."""
        monitor = FileMonitor(tmp_path)
        monitor.start()

        try:
            # Create file
            test_file = tmp_path / "test.txt"
            test_file.write_text("hello")

            # Wait for event processing
            time.sleep(0.2)

            # Check changes
            changes = monitor.get_recent_changes(minutes=1)
            assert len(changes) > 0

            created_changes = [c for c in changes if c.change_type == ChangeType.CREATED]
            assert len(created_changes) > 0
            assert any("test.txt" in str(c.path) for c in created_changes)

        finally:
            monitor.stop()

    def test_detect_file_modification(self, tmp_path: Path) -> None:
        """Test detecting file modification."""
        # Create file before monitoring
        test_file = tmp_path / "test.txt"
        test_file.write_text("initial")

        monitor = FileMonitor(tmp_path)
        monitor.start()

        try:
            # Modify file
            test_file.write_text("modified")

            # Wait for event processing
            time.sleep(0.2)

            # Check changes
            changes = monitor.get_recent_changes(minutes=1)
            modified_changes = [
                c for c in changes if c.change_type == ChangeType.MODIFIED
            ]

            assert len(modified_changes) > 0
            assert any("test.txt" in str(c.path) for c in modified_changes)

        finally:
            monitor.stop()

    def test_detect_file_deletion(self, tmp_path: Path) -> None:
        """Test detecting file deletion."""
        # Create file
        test_file = tmp_path / "test.txt"
        test_file.write_text("content")

        monitor = FileMonitor(tmp_path)
        monitor.start()

        try:
            # Delete file
            test_file.unlink()

            # Wait for event processing
            time.sleep(0.2)

            # Check changes
            changes = monitor.get_recent_changes(minutes=1)
            deleted_changes = [c for c in changes if c.change_type == ChangeType.DELETED]

            assert len(deleted_changes) > 0
            assert any("test.txt" in str(c.path) for c in deleted_changes)

        finally:
            monitor.stop()

    def test_ignore_patterns(self, tmp_path: Path) -> None:
        """Test that ignored files are not tracked."""
        config = MonitorConfig(watch=WatchConfig(ignore_patterns=["*.pyc", "temp/**"]))
        monitor = FileMonitor(tmp_path, config=config)
        monitor.start()

        try:
            # Create ignored file
            pyc_file = tmp_path / "test.pyc"
            pyc_file.write_text("bytecode")

            # Wait
            time.sleep(0.2)

            # Should not be tracked
            changes = monitor.get_recent_changes(minutes=1)
            assert not any("test.pyc" in str(c.path) for c in changes)

        finally:
            monitor.stop()

    def test_debouncing(self, tmp_path: Path) -> None:
        """Test that rapid changes are debounced."""
        config = MonitorConfig(watch=WatchConfig(debounce_ms=500))
        monitor = FileMonitor(tmp_path, config=config)
        monitor.start()

        try:
            test_file = tmp_path / "test.txt"

            # Rapid writes (within debounce window)
            for i in range(5):
                test_file.write_text(f"content {i}")
                time.sleep(0.05)  # 50ms between writes

            # Wait for debounce
            time.sleep(0.6)

            # Should only have 1-2 changes (not 5)
            changes = monitor.get_recent_changes(minutes=1)
            file_changes = [c for c in changes if "test.txt" in str(c.path)]

            assert len(file_changes) < 5  # Debounced

        finally:
            monitor.stop()

    def test_get_recent_changes_time_window(self, tmp_path: Path) -> None:
        """Test time window filtering."""
        monitor = FileMonitor(tmp_path)

        # Manually add changes with different timestamps
        old_change = FileChange(
            path=tmp_path / "old.txt",
            change_type=ChangeType.CREATED,
            timestamp=datetime.now() - timedelta(minutes=20),
        )

        recent_change = FileChange(
            path=tmp_path / "recent.txt",
            change_type=ChangeType.CREATED,
            timestamp=datetime.now(),
        )

        monitor.change_queue.append(old_change)
        monitor.change_queue.append(recent_change)

        # Get changes from last 10 minutes
        changes = monitor.get_recent_changes(minutes=10)

        # Should only include recent change
        assert len(changes) == 1
        assert "recent.txt" in str(changes[0].path)

    def test_clear_history(self, tmp_path: Path) -> None:
        """Test clearing change history."""
        monitor = FileMonitor(tmp_path)

        # Add some changes
        change = FileChange(
            path=tmp_path / "test.txt",
            change_type=ChangeType.CREATED,
        )
        monitor.change_queue.append(change)

        assert len(monitor.change_queue) > 0

        # Clear
        monitor.clear_history()

        assert len(monitor.change_queue) == 0
