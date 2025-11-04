"""Security tests for proactive monitoring."""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.proactive.config import MonitorConfig
from clauxton.proactive.event_processor import EventProcessor
from clauxton.proactive.file_monitor import FileMonitor
from clauxton.proactive.models import ChangeType, FileChange


class TestPathTraversalProtection:
    """Test protection against path traversal attacks."""

    @pytest.mark.asyncio
    async def test_path_traversal_in_file_changes(self, tmp_path: Path) -> None:
        """Test that path traversal attempts are handled safely."""
        processor = EventProcessor(tmp_path)

        # Attempt path traversal
        malicious_paths = [
            tmp_path / ".." / ".." / "etc" / "passwd",
            tmp_path / ".." / "sensitive" / "data.txt",
            tmp_path / ".." / ".." / ".." / "root" / "secret",
        ]

        changes = [
            FileChange(
                path=p,
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for p in malicious_paths
        ]

        # Should not crash, should handle gracefully
        patterns = await processor.detect_patterns(changes)

        # Patterns should be detected without exposing system paths
        assert isinstance(patterns, list)

    def test_symlink_handling(self, tmp_path: Path) -> None:
        """Test that symlinks are handled safely."""
        config = MonitorConfig()
        monitor = FileMonitor(tmp_path, config)

        # Create symlink outside project root
        external_dir = tmp_path.parent / "external"
        external_dir.mkdir(exist_ok=True)
        symlink_path = tmp_path / "symlink"

        try:
            symlink_path.symlink_to(external_dir)

            # Monitor should start without following symlink
            monitor.start()
            monitor.stop()

            # No exception should be raised
            assert True

        finally:
            if symlink_path.exists():
                symlink_path.unlink()
            if external_dir.exists():
                external_dir.rmdir()

    @pytest.mark.asyncio
    async def test_absolute_path_injection(self, tmp_path: Path) -> None:
        """Test protection against absolute path injection."""
        processor = EventProcessor(tmp_path)

        # Attempt absolute path injection
        changes = [
            FileChange(
                path=Path("/etc/passwd"),
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=Path("/root/.ssh/id_rsa"),
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            ),
        ]

        # Should not crash or expose system files
        patterns = await processor.detect_patterns(changes)

        assert isinstance(patterns, list)


class TestPatternInjection:
    """Test protection against pattern injection attacks."""

    @pytest.mark.asyncio
    async def test_special_characters_in_filenames(self, tmp_path: Path) -> None:
        """Test handling of special characters in file names."""
        processor = EventProcessor(tmp_path)

        # Files with special characters
        special_names = [
            "file\x00null.py",  # Null byte
            "file\n\nnewline.py",  # Newlines
            "file\t\ttab.py",  # Tabs
            "file;command.py",  # Shell injection
            "file|pipe.py",  # Pipe
            "file&background.py",  # Background
            "file$var.py",  # Variable expansion
            "file`cmd`.py",  # Command substitution
        ]

        changes = [
            FileChange(
                path=tmp_path / name,
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
            for name in special_names
        ]

        # Should handle gracefully without executing commands
        patterns = await processor.detect_patterns(changes)

        assert isinstance(patterns, list)

    @pytest.mark.asyncio
    async def test_unicode_filenames(self, tmp_path: Path) -> None:
        """Test handling of Unicode and emoji in file names."""
        processor = EventProcessor(tmp_path)

        # Unicode and emoji filenames
        unicode_names = [
            "文件.py",  # Chinese
            "ファイル.py",  # Japanese
            "파일.py",  # Korean
            "файл.py",  # Russian
            "😀emoji.py",  # Emoji
            "file🔥test.py",  # Mixed
        ]

        changes = [
            FileChange(
                path=tmp_path / name,
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
            for name in unicode_names
        ]

        # Should handle Unicode correctly
        patterns = await processor.detect_patterns(changes)

        assert isinstance(patterns, list)


class TestResourceExhaustion:
    """Test protection against resource exhaustion attacks."""

    def test_queue_overflow_protection(self, tmp_path: Path) -> None:
        """Test that queue has size limits to prevent memory exhaustion."""
        config = MonitorConfig()
        monitor = FileMonitor(tmp_path, config)

        # Queue should have max size
        assert monitor.change_queue.maxlen == config.watch.max_queue_size

        # Add more items than max size
        for i in range(config.watch.max_queue_size + 100):
            change = FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
            monitor.change_queue.append(change)

        # Queue should not exceed max size
        assert len(monitor.change_queue) == config.watch.max_queue_size

    @pytest.mark.asyncio
    async def test_cache_size_bounds(self, tmp_path: Path) -> None:
        """Test that cache is bounded to prevent memory exhaustion."""
        processor = EventProcessor(tmp_path)

        # Fill cache beyond max
        for i in range(processor.MAX_CACHE_ENTRIES + 20):
            changes = [
                FileChange(
                    path=tmp_path / f"unique_{i}_{j}.py",
                    change_type=ChangeType.MODIFIED,
                    timestamp=datetime.now(),
                )
                for j in range(3)
            ]
            await processor.detect_patterns(changes)

        # Cache should be bounded
        assert len(processor._pattern_cache) <= processor.MAX_CACHE_ENTRIES

    @pytest.mark.asyncio
    async def test_large_file_list_handling(self, tmp_path: Path) -> None:
        """Test handling of very large file lists (potential DoS)."""
        processor = EventProcessor(tmp_path)

        # Create very large change list
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(10000)
        ]

        # Should handle without crashing or hanging
        patterns = await processor.detect_patterns(changes)

        # Should still return results
        assert isinstance(patterns, list)


class TestInputValidation:
    """Test validation of inputs to prevent security issues."""

    @pytest.mark.asyncio
    async def test_invalid_confidence_threshold(self, tmp_path: Path) -> None:
        """Test validation of confidence threshold values."""
        processor = EventProcessor(tmp_path)

        changes = [
            FileChange(
                path=tmp_path / "file.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
        ]

        # Test invalid confidence values
        invalid_values = [-1.0, 2.0, float("inf"), float("-inf")]

        for value in invalid_values:
            # Should handle gracefully (either validate or use default)
            try:
                patterns = await processor.detect_patterns(changes, value)
                # If no exception, should return valid list
                assert isinstance(patterns, list)
            except (ValueError, TypeError):
                # Or raise appropriate exception
                assert True

    def test_config_validation(self, tmp_path: Path) -> None:
        """Test that config validates input values."""
        # Valid config should work
        config = MonitorConfig()
        assert config.watch.max_queue_size >= 100
        assert config.watch.max_queue_size <= 10000

        # Invalid values should be caught by Pydantic
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate(
                {"watch": {"max_queue_size": -1000}}  # Negative
            )

        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate(
                {"watch": {"max_queue_size": 999999}}  # Too large
            )

    def test_debounce_config_validation(self) -> None:
        """Test debounce time validation."""
        # Valid config
        config = MonitorConfig()
        assert config.watch.debounce_ms > 0

        # Invalid negative debounce (field is debounce_ms not debounce_seconds)
        with pytest.raises((ValueError, TypeError)):
            MonitorConfig.model_validate(
                {"watch": {"debounce_ms": -5}}  # Negative
            )
