"""Tests for event processor."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clauxton.proactive.event_processor import EventProcessor
from clauxton.proactive.models import ChangeType, FileChange, PatternType


class TestEventProcessor:
    """Tests for EventProcessor."""

    def test_init(self, tmp_path: Path) -> None:
        """Test EventProcessor initialization."""
        processor = EventProcessor(tmp_path)

        assert processor.project_root == tmp_path
        assert processor.clauxton_dir == tmp_path / ".clauxton"
        assert processor.activity_file == tmp_path / ".clauxton" / "activity.yml"

    @pytest.mark.asyncio
    async def test_detect_patterns_empty(self, tmp_path: Path) -> None:
        """Test pattern detection with empty changes."""
        processor = EventProcessor(tmp_path)
        patterns = await processor.detect_patterns([])

        assert patterns == []

    @pytest.mark.asyncio
    async def test_detect_bulk_edit(self, tmp_path: Path) -> None:
        """Test detecting bulk edit pattern."""
        processor = EventProcessor(tmp_path)

        # Create 7 modified files in short time span (confidence = 0.7 >= 0.6)
        base_time = datetime.now()
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=base_time + timedelta(seconds=i),
            )
            for i in range(7)
        ]

        patterns = await processor.detect_patterns(changes)

        # Should detect bulk edit
        bulk_edits = [p for p in patterns if p.pattern_type == PatternType.BULK_EDIT]
        assert len(bulk_edits) == 1

        bulk_edit = bulk_edits[0]
        assert len(bulk_edit.files) == 7
        assert bulk_edit.confidence == 0.7  # 7/10
        assert "Bulk edit" in bulk_edit.description

    @pytest.mark.asyncio
    async def test_detect_bulk_edit_too_few_files(self, tmp_path: Path) -> None:
        """Test that bulk edit requires at least 3 files."""
        processor = EventProcessor(tmp_path)

        # Only 2 modified files
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(2)
        ]

        patterns = await processor.detect_patterns(changes)

        # Should not detect bulk edit
        bulk_edits = [p for p in patterns if p.pattern_type == PatternType.BULK_EDIT]
        assert len(bulk_edits) == 0

    @pytest.mark.asyncio
    async def test_detect_bulk_edit_time_span_too_long(self, tmp_path: Path) -> None:
        """Test that bulk edit requires short time span."""
        processor = EventProcessor(tmp_path)

        # 5 files but spread over 10 minutes
        base_time = datetime.now()
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=base_time + timedelta(minutes=i * 2),
            )
            for i in range(5)
        ]

        patterns = await processor.detect_patterns(changes)

        # Should not detect bulk edit (time span > 5 minutes)
        bulk_edits = [p for p in patterns if p.pattern_type == PatternType.BULK_EDIT]
        assert len(bulk_edits) == 0

    @pytest.mark.asyncio
    async def test_detect_new_feature(self, tmp_path: Path) -> None:
        """Test detecting new feature pattern."""
        processor = EventProcessor(tmp_path)

        # Create 3 new files in same directory
        feature_dir = tmp_path / "src" / "features" / "auth"
        changes = [
            FileChange(
                path=feature_dir / f"file{i}.py",
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
            for i in range(3)
        ]

        patterns = await processor.detect_patterns(changes)

        # Should detect new feature
        new_features = [p for p in patterns if p.pattern_type == PatternType.NEW_FEATURE]
        assert len(new_features) == 1

        new_feature = new_features[0]
        assert len(new_feature.files) == 3
        assert new_feature.confidence == 0.6  # 3/5
        assert "New feature" in new_feature.description
        assert "auth" in new_feature.description

    @pytest.mark.asyncio
    async def test_detect_new_feature_too_few_files(self, tmp_path: Path) -> None:
        """Test that new feature requires at least 2 files."""
        processor = EventProcessor(tmp_path)

        # Only 1 created file
        changes = [
            FileChange(
                path=tmp_path / "file.py",
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
        ]

        patterns = await processor.detect_patterns(changes)

        # Should not detect new feature
        new_features = [p for p in patterns if p.pattern_type == PatternType.NEW_FEATURE]
        assert len(new_features) == 0

    @pytest.mark.asyncio
    async def test_detect_refactoring(self, tmp_path: Path) -> None:
        """Test detecting refactoring pattern."""
        processor = EventProcessor(tmp_path)

        # Move 3 files
        changes = [
            FileChange(
                path=tmp_path / "new" / f"file{i}.py",
                change_type=ChangeType.MOVED,
                timestamp=datetime.now(),
                src_path=tmp_path / "old" / f"file{i}.py",
            )
            for i in range(3)
        ]

        patterns = await processor.detect_patterns(changes)

        # Should detect refactoring
        refactorings = [p for p in patterns if p.pattern_type == PatternType.REFACTORING]
        assert len(refactorings) == 1

        refactoring = refactorings[0]
        assert len(refactoring.files) == 3
        assert refactoring.confidence == 0.6  # 3/5
        assert "Refactoring" in refactoring.description

    @pytest.mark.asyncio
    async def test_detect_cleanup(self, tmp_path: Path) -> None:
        """Test detecting cleanup pattern."""
        processor = EventProcessor(tmp_path)

        # Delete 4 files
        changes = [
            FileChange(
                path=tmp_path / f"old_file{i}.py",
                change_type=ChangeType.DELETED,
                timestamp=datetime.now(),
            )
            for i in range(4)
        ]

        patterns = await processor.detect_patterns(changes)

        # Should detect cleanup
        cleanups = [p for p in patterns if p.pattern_type == PatternType.CLEANUP]
        assert len(cleanups) == 1

        cleanup = cleanups[0]
        assert len(cleanup.files) == 4
        assert cleanup.confidence == 0.8  # 4/5
        assert "Cleanup" in cleanup.description

    @pytest.mark.asyncio
    async def test_detect_configuration(self, tmp_path: Path) -> None:
        """Test detecting configuration changes."""
        processor = EventProcessor(tmp_path)

        # Modify config files
        changes = [
            FileChange(
                path=tmp_path / "config.yml",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "package.json",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "Dockerfile",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
        ]

        patterns = await processor.detect_patterns(changes)

        # Should detect configuration
        configs = [p for p in patterns if p.pattern_type == PatternType.CONFIGURATION]
        assert len(configs) == 1

        config = configs[0]
        assert len(config.files) == 3
        assert config.confidence == 0.9  # High confidence for config files
        assert "Configuration" in config.description

    @pytest.mark.asyncio
    async def test_detect_configuration_by_extension(self, tmp_path: Path) -> None:
        """Test configuration detection by file extension."""
        processor = EventProcessor(tmp_path)

        config_files = [
            "config.yml",
            "settings.yaml",
            "package.json",
            "pyproject.toml",
            "setup.ini",
            "app.conf",
            "database.config",
        ]

        changes = [
            FileChange(
                path=tmp_path / filename,
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for filename in config_files
        ]

        patterns = await processor.detect_patterns(changes)

        configs = [p for p in patterns if p.pattern_type == PatternType.CONFIGURATION]
        assert len(configs) == 1
        assert len(configs[0].files) == len(config_files)

    @pytest.mark.asyncio
    async def test_detect_configuration_by_name(self, tmp_path: Path) -> None:
        """Test configuration detection by filename."""
        processor = EventProcessor(tmp_path)

        config_files = ["Dockerfile", "Makefile", ".env", ".gitignore"]

        changes = [
            FileChange(
                path=tmp_path / filename,
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for filename in config_files
        ]

        patterns = await processor.detect_patterns(changes)

        configs = [p for p in patterns if p.pattern_type == PatternType.CONFIGURATION]
        assert len(configs) == 1
        assert len(configs[0].files) == len(config_files)

    @pytest.mark.asyncio
    async def test_detect_multiple_patterns(self, tmp_path: Path) -> None:
        """Test detecting multiple patterns simultaneously."""
        processor = EventProcessor(tmp_path)

        # Mix of changes
        changes = [
            # Bulk edit (6 modifications for confidence >= 0.6)
            FileChange(
                path=tmp_path / "file1.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "file2.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "file3.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "file4.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "file5.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "file6.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            # Configuration (1 config file)
            FileChange(
                path=tmp_path / "config.yml",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            # Cleanup (3 deletions for confidence >= 0.6)
            FileChange(
                path=tmp_path / "old1.py",
                change_type=ChangeType.DELETED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "old2.py",
                change_type=ChangeType.DELETED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "old3.py",
                change_type=ChangeType.DELETED,
                timestamp=datetime.now(),
            ),
        ]

        patterns = await processor.detect_patterns(changes)

        # Should detect bulk edit, configuration, and cleanup
        pattern_types = {p.pattern_type for p in patterns}
        assert PatternType.BULK_EDIT in pattern_types
        assert PatternType.CONFIGURATION in pattern_types
        assert PatternType.CLEANUP in pattern_types

    @pytest.mark.asyncio
    async def test_confidence_threshold(self, tmp_path: Path) -> None:
        """Test filtering patterns by confidence threshold."""
        processor = EventProcessor(tmp_path)

        # Create 3 modified files (confidence = 0.3)
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(3)
        ]

        # With default threshold (0.6), should not detect
        patterns_default = await processor.detect_patterns(changes)
        bulk_edits = [p for p in patterns_default if p.pattern_type == PatternType.BULK_EDIT]
        assert len(bulk_edits) == 0

        # With lower threshold (0.2), should detect
        patterns_low = await processor.detect_patterns(changes, confidence_threshold=0.2)
        bulk_edits_low = [
            p for p in patterns_low if p.pattern_type == PatternType.BULK_EDIT
        ]
        assert len(bulk_edits_low) == 1

    @pytest.mark.asyncio
    async def test_create_activity_summary(self, tmp_path: Path) -> None:
        """Test creating activity summary."""
        processor = EventProcessor(tmp_path)

        changes = [
            FileChange(
                path=tmp_path / "src" / "file1.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "src" / "file2.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "src" / "file3.py",
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "config.yml",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
        ]

        summary = await processor.create_activity_summary(changes, time_window_minutes=10)

        assert summary.time_window_minutes == 10
        assert len(summary.changes) == 4
        assert summary.total_files_changed == 4
        assert summary.most_active_directory == tmp_path / "src"
        assert len(summary.patterns) > 0  # Should detect some patterns

    @pytest.mark.asyncio
    async def test_find_most_active_directory(self, tmp_path: Path) -> None:
        """Test finding most active directory."""
        processor = EventProcessor(tmp_path)

        changes = [
            # 3 changes in src/
            FileChange(
                path=tmp_path / "src" / "file1.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "src" / "file2.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "src" / "file3.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            # 1 change in tests/
            FileChange(
                path=tmp_path / "tests" / "test_file.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
        ]

        most_active = processor._find_most_active_directory(changes)

        assert most_active == tmp_path / "src"

    @pytest.mark.asyncio
    async def test_find_most_active_directory_empty(self, tmp_path: Path) -> None:
        """Test finding most active directory with empty changes."""
        processor = EventProcessor(tmp_path)

        most_active = processor._find_most_active_directory([])

        assert most_active is None

    @pytest.mark.asyncio
    async def test_save_activity(self, tmp_path: Path) -> None:
        """Test saving activity summary."""
        processor = EventProcessor(tmp_path)
        processor.clauxton_dir.mkdir(parents=True, exist_ok=True)

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

        summary = await processor.create_activity_summary(changes, time_window_minutes=10)

        # Save activity
        await processor.save_activity(summary)

        # Verify file exists
        assert processor.activity_file.exists()

        # Verify content
        from clauxton.utils.yaml_utils import read_yaml

        data = read_yaml(processor.activity_file)
        assert "activities" in data
        assert len(data["activities"]) == 1

        activity = data["activities"][0]
        assert activity["time_window_minutes"] == 10
        assert len(activity["changes"]) == 2
        assert activity["total_files_changed"] == 2

    @pytest.mark.asyncio
    async def test_save_activity_appends(self, tmp_path: Path) -> None:
        """Test that saving activity appends to existing activities."""
        processor = EventProcessor(tmp_path)
        processor.clauxton_dir.mkdir(parents=True, exist_ok=True)

        # Save first activity
        changes1 = [
            FileChange(
                path=tmp_path / "file1.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
        ]
        summary1 = await processor.create_activity_summary(changes1, time_window_minutes=5)
        await processor.save_activity(summary1)

        # Save second activity
        changes2 = [
            FileChange(
                path=tmp_path / "file2.py",
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
        ]
        summary2 = await processor.create_activity_summary(changes2, time_window_minutes=10)
        await processor.save_activity(summary2)

        # Verify both activities are saved
        from clauxton.utils.yaml_utils import read_yaml

        data = read_yaml(processor.activity_file)
        assert len(data["activities"]) == 2

    @pytest.mark.asyncio
    async def test_save_activity_limits_history(self, tmp_path: Path) -> None:
        """Test that activity history is limited to 100 entries."""
        processor = EventProcessor(tmp_path)
        processor.clauxton_dir.mkdir(parents=True, exist_ok=True)

        # Save 105 activities
        for i in range(105):
            changes = [
                FileChange(
                    path=tmp_path / f"file{i}.py",
                    change_type=ChangeType.MODIFIED,
                    timestamp=datetime.now(),
                )
            ]
            summary = await processor.create_activity_summary(changes, time_window_minutes=1)
            await processor.save_activity(summary)

        # Verify only last 100 are kept
        from clauxton.utils.yaml_utils import read_yaml

        data = read_yaml(processor.activity_file)
        assert len(data["activities"]) == 100
