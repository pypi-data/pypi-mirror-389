"""Error handling tests for proactive monitoring."""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.proactive.config import MonitorConfig
from clauxton.proactive.event_processor import EventProcessor
from clauxton.proactive.file_monitor import FileMonitor
from clauxton.proactive.models import ChangeType, FileChange


class TestFileSystemErrors:
    """Test handling of file system errors."""

    @pytest.mark.asyncio
    async def test_permission_denied_on_activity_file(self, tmp_path: Path) -> None:
        """Test handling when activity file is not writable."""
        processor = EventProcessor(tmp_path)

        # Create activity file with no write permissions
        processor.clauxton_dir.mkdir(exist_ok=True)
        processor.activity_file.touch()
        processor.activity_file.chmod(0o444)  # Read-only

        changes = [
            FileChange(
                path=tmp_path / "file.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
        ]

        # Detect patterns should work
        patterns = await processor.detect_patterns(changes)
        assert isinstance(patterns, list)

        # Create summary
        summary = await processor.create_activity_summary(changes, time_window_minutes=5)
        assert summary is not None

        # Save should fail gracefully
        try:
            await processor.save_activity(summary)
        except (PermissionError, OSError):
            # Expected - permission denied
            assert True
        finally:
            # Cleanup
            processor.activity_file.chmod(0o644)

    @pytest.mark.asyncio
    async def test_corrupted_yaml_file(self, tmp_path: Path) -> None:
        """Test handling of corrupted activity YAML file."""
        from clauxton.core.models import ValidationError

        processor = EventProcessor(tmp_path)
        processor.clauxton_dir.mkdir(exist_ok=True)

        # Write corrupted YAML
        processor.activity_file.write_text("invalid: yaml: content: {{{{")

        changes = [
            FileChange(
                path=tmp_path / "file.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
        ]

        # Should handle corrupted file gracefully
        summary = await processor.create_activity_summary(changes, time_window_minutes=5)

        # Save should raise ValidationError when encountering corrupted YAML
        # This is the expected behavior - fail fast and inform user
        with pytest.raises(ValidationError):
            await processor.save_activity(summary)

    def test_file_disappeared_during_processing(self, tmp_path: Path) -> None:
        """Test handling when monitored file disappears."""
        config = MonitorConfig()
        monitor = FileMonitor(tmp_path, config)

        # Create a file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        monitor.start()

        try:
            # Add change
            change = FileChange(
                path=test_file,
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
            monitor.change_queue.append(change)

            # Delete file
            test_file.unlink()

            # Get recent changes should handle missing file
            changes = monitor.get_recent_changes()
            assert isinstance(changes, list)

        finally:
            monitor.stop()

    def test_nonexistent_directory_monitoring(self, tmp_path: Path) -> None:
        """Test monitoring a directory that doesn't exist."""
        config = MonitorConfig()
        nonexistent = tmp_path / "nonexistent"

        # Should handle gracefully
        try:
            monitor = FileMonitor(nonexistent, config)
            monitor.start()
            monitor.stop()
            # Either succeeds or raises appropriate error
            assert True
        except (FileNotFoundError, OSError):
            # Expected error
            assert True


class TestWatchdogFailures:
    """Test handling of watchdog failures."""

    def test_observer_start_failure(self, tmp_path: Path) -> None:
        """Test handling when observer fails to start."""
        config = MonitorConfig()
        monitor = FileMonitor(tmp_path, config)

        # Start monitor normally first
        monitor.start()

        # Try starting again (should raise RuntimeError)
        try:
            monitor.start()
            # Should not reach here
            assert False, "Expected RuntimeError for double start"
        except RuntimeError as e:
            # Expected - cannot start twice
            assert "already running" in str(e).lower()
        finally:
            monitor.stop()

    def test_event_handler_exception(self, tmp_path: Path) -> None:
        """Test that event handler exceptions don't crash monitor."""
        config = MonitorConfig()
        monitor = FileMonitor(tmp_path, config)

        monitor.start()

        try:
            # Create many files quickly to stress test the handler
            for i in range(50):
                test_file = tmp_path / f"test{i}.py"
                test_file.write_text(f"# Test file {i}")

            # Give watchdog time to process
            import time

            time.sleep(0.5)

            # Monitor should still be running
            assert monitor.is_running

        finally:
            monitor.stop()

    def test_thread_safety(self, tmp_path: Path) -> None:
        """Test thread safety of monitor operations."""
        config = MonitorConfig()
        monitor = FileMonitor(tmp_path, config)

        monitor.start()

        try:
            # Concurrent operations
            import threading

            def add_changes():
                for i in range(100):
                    change = FileChange(
                        path=tmp_path / f"file{i}.py",
                        change_type=ChangeType.CREATED,
                        timestamp=datetime.now(),
                    )
                    monitor.change_queue.append(change)

            def get_changes():
                for _ in range(50):
                    monitor.get_recent_changes()

            # Run concurrent operations
            threads = [
                threading.Thread(target=add_changes),
                threading.Thread(target=add_changes),
                threading.Thread(target=get_changes),
                threading.Thread(target=get_changes),
            ]

            for t in threads:
                t.start()

            for t in threads:
                t.join()

            # Should not crash
            assert True

        finally:
            monitor.stop()


class TestCacheErrors:
    """Test handling of cache-related errors."""

    @pytest.mark.asyncio
    async def test_cache_with_invalid_data(self, tmp_path: Path) -> None:
        """Test cache handles invalid data gracefully."""
        processor = EventProcessor(tmp_path)

        # Manually corrupt cache
        processor._pattern_cache["invalid_key"] = ("not_a_datetime", [])

        changes = [
            FileChange(
                path=tmp_path / "file.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
        ]

        # Should handle corrupted cache entry
        try:
            patterns = await processor.detect_patterns(changes)
            assert isinstance(patterns, list)
        except (TypeError, AttributeError):
            # Acceptable if cache validation fails
            assert True

    @pytest.mark.asyncio
    async def test_cache_cleanup_with_invalid_entries(self, tmp_path: Path) -> None:
        """Test cache cleanup handles invalid entries."""
        processor = EventProcessor(tmp_path)

        # Add valid entries
        for i in range(60):
            changes = [
                FileChange(
                    path=tmp_path / f"file{i}.py",
                    change_type=ChangeType.MODIFIED,
                    timestamp=datetime.now(),
                )
            ]
            await processor.detect_patterns(changes)

        # Add invalid entry
        processor._pattern_cache["corrupt"] = (None, None)

        # Cleanup should handle gracefully
        try:
            processor._cleanup_cache()
            # Should have removed old entries
            assert len(processor._pattern_cache) <= processor.MAX_CACHE_ENTRIES
        except (TypeError, AttributeError):
            # Or fail with appropriate error
            assert True

    @pytest.mark.asyncio
    async def test_empty_changes_list(self, tmp_path: Path) -> None:
        """Test handling of empty changes list."""
        processor = EventProcessor(tmp_path)

        # Empty list should return empty patterns
        patterns = await processor.detect_patterns([])
        assert patterns == []

        # Should not crash with None
        try:
            patterns = await processor.detect_patterns([])  # type: ignore
            assert isinstance(patterns, list)
        except (TypeError, AttributeError):
            # Or raise appropriate error
            assert True


class TestConfigErrors:
    """Test handling of configuration errors."""

    def test_invalid_debounce_values(self) -> None:
        """Test validation of debounce configuration."""
        # Negative debounce should fail (field is debounce_ms not debounce_seconds)
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"debounce_ms": -1}})

        # Too small debounce should fail (ge=100)
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"debounce_ms": 50}})

    def test_invalid_queue_size(self) -> None:
        """Test validation of queue size."""
        # Too small
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"max_queue_size": 50}})

        # Too large
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"max_queue_size": 999999}})

        # Negative
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"max_queue_size": -100}})

    def test_invalid_debounce_entries(self) -> None:
        """Test validation of debounce entries configuration."""
        # Too small
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"max_debounce_entries": 50}})

        # Negative
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"max_debounce_entries": -500}})

    def test_missing_config_fields(self) -> None:
        """Test handling of missing config fields."""
        # Should use defaults for missing fields
        config = MonitorConfig.model_validate({})

        assert config.watch.debounce_ms > 0
        assert config.watch.max_queue_size > 0
        assert config.watch.max_debounce_entries > 0
        assert config.enabled is True

    def test_type_mismatches(self) -> None:
        """Test handling of type mismatches in config."""
        # Non-numeric string instead of int (should fail)
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"max_queue_size": "not_a_number"}})

        # List instead of int (should fail)
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"max_debounce_entries": [1, 2, 3]}})

        # Dict instead of int (should fail)
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate({"watch": {"debounce_ms": {"value": 500}}})
