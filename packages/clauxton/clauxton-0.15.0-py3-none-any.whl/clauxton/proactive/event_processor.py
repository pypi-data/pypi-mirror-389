"""Process file system events and detect patterns."""

import hashlib
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from clauxton.proactive.models import (
    ActivitySummary,
    ChangeType,
    DetectedPattern,
    FileChange,
    PatternType,
)
from clauxton.utils.yaml_utils import read_yaml, write_yaml


class EventProcessor:
    """Process file system events and detect patterns."""

    # Pattern detection thresholds (configurable constants)
    BULK_EDIT_MIN_FILES = 3
    BULK_EDIT_MAX_FILES = 10  # For 1.0 confidence
    BULK_EDIT_TIME_WINDOW_MINUTES = 5

    NEW_FEATURE_MIN_FILES = 2
    NEW_FEATURE_MAX_FILES = 5  # For 1.0 confidence

    REFACTORING_MIN_FILES = 2
    REFACTORING_MAX_FILES = 5  # For 1.0 confidence

    CLEANUP_MIN_FILES = 2
    CLEANUP_MAX_FILES = 5  # For 1.0 confidence

    CONFIG_CONFIDENCE = 0.9

    MAX_ACTIVITY_HISTORY = 100  # Maximum activities to keep

    # Cache settings
    CACHE_TTL_SECONDS = 60  # Cache validity duration
    MAX_CACHE_ENTRIES = 50  # Maximum cache entries

    def __init__(self, project_root: Path):
        """Initialize event processor."""
        self.project_root = project_root
        self.clauxton_dir = project_root / ".clauxton"
        self.activity_file = self.clauxton_dir / "activity.yml"
        self._pattern_cache: Dict[str, Tuple[datetime, List[DetectedPattern]]] = {}

    def _generate_cache_key(self, changes: List[FileChange]) -> str:
        """Generate cache key from file changes."""
        # Create a stable hash from file paths and change types
        key_data = "|".join(
            sorted(f"{c.path}:{c.change_type.value}" for c in changes)
        )
        return hashlib.md5(key_data.encode(), usedforsecurity=False).hexdigest()

    def _get_cached_patterns(
        self, cache_key: str, confidence_threshold: float
    ) -> Optional[List[DetectedPattern]]:
        """Get cached patterns if still valid."""
        if cache_key not in self._pattern_cache:
            return None

        cached_time, cached_patterns = self._pattern_cache[cache_key]

        # Check if cache is still valid
        if (datetime.now() - cached_time).total_seconds() > self.CACHE_TTL_SECONDS:
            # Cache expired
            del self._pattern_cache[cache_key]
            return None

        # Filter by confidence threshold
        return [p for p in cached_patterns if p.confidence >= confidence_threshold]

    def _cleanup_cache(self) -> None:
        """Remove old cache entries if over limit."""
        if len(self._pattern_cache) <= self.MAX_CACHE_ENTRIES:
            return

        # Remove oldest entries
        sorted_entries = sorted(
            self._pattern_cache.items(), key=lambda x: x[1][0]  # Sort by timestamp
        )

        # Keep only the newest MAX_CACHE_ENTRIES
        self._pattern_cache = dict(sorted_entries[-self.MAX_CACHE_ENTRIES :])

    async def detect_patterns(
        self, changes: List[FileChange], confidence_threshold: float = 0.6
    ) -> List[DetectedPattern]:
        """
        Detect patterns in file changes.

        Args:
            changes: List of file changes
            confidence_threshold: Minimum confidence to return pattern

        Returns:
            List of detected patterns
        """
        if not changes:
            return []

        # Check cache first
        cache_key = self._generate_cache_key(changes)
        cached_result = self._get_cached_patterns(cache_key, confidence_threshold)
        if cached_result is not None:
            return cached_result

        # Detect all patterns without filtering
        all_patterns: List[DetectedPattern] = []

        # Detect bulk edit (many modifications in short time)
        bulk_edit = self._detect_bulk_edit(changes)
        if bulk_edit:
            all_patterns.append(bulk_edit)

        # Detect new feature (new files created)
        new_feature = self._detect_new_feature(changes)
        if new_feature:
            all_patterns.append(new_feature)

        # Detect refactoring (files moved/renamed)
        refactoring = self._detect_refactoring(changes)
        if refactoring:
            all_patterns.append(refactoring)

        # Detect cleanup (files deleted)
        cleanup = self._detect_cleanup(changes)
        if cleanup:
            all_patterns.append(cleanup)

        # Detect configuration changes
        config_change = self._detect_configuration(changes)
        if config_change:
            all_patterns.append(config_change)

        # Store ALL patterns in cache (before filtering by threshold)
        self._pattern_cache[cache_key] = (datetime.now(), all_patterns)
        self._cleanup_cache()

        # Filter by confidence threshold
        patterns = [p for p in all_patterns if p.confidence >= confidence_threshold]

        return patterns

    def _detect_bulk_edit(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect bulk editing pattern."""
        modified = [c for c in changes if c.change_type == ChangeType.MODIFIED]

        if len(modified) < self.BULK_EDIT_MIN_FILES:
            return None

        # Check time span (bulk edit = many files in short time)
        if modified:
            time_span = max(c.timestamp for c in modified) - min(
                c.timestamp for c in modified
            )
            if time_span > timedelta(minutes=self.BULK_EDIT_TIME_WINDOW_MINUTES):
                return None

        # Calculate confidence based on number of files
        confidence = min(1.0, len(modified) / self.BULK_EDIT_MAX_FILES)

        return DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[c.path for c in modified],
            confidence=confidence,
            description=f"Bulk edit: {len(modified)} files modified",
        )

    def _detect_new_feature(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect new feature pattern (new files created)."""
        created = [c for c in changes if c.change_type == ChangeType.CREATED]

        if len(created) < self.NEW_FEATURE_MIN_FILES:
            return None

        # Check if files are in same directory (likely related)
        directories = [c.path.parent for c in created]
        dir_counts = Counter(directories)
        most_common_dir, count = dir_counts.most_common(1)[0]

        if count < self.NEW_FEATURE_MIN_FILES:
            return None

        # Calculate confidence
        confidence = min(1.0, count / self.NEW_FEATURE_MAX_FILES)

        return DetectedPattern(
            pattern_type=PatternType.NEW_FEATURE,
            files=[c.path for c in created if c.path.parent == most_common_dir],
            confidence=confidence,
            description=f"New feature: {count} new files in {most_common_dir.name}/",
        )

    def _detect_refactoring(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect refactoring pattern (files moved/renamed)."""
        moved = [c for c in changes if c.change_type == ChangeType.MOVED]

        if len(moved) < self.REFACTORING_MIN_FILES:
            return None

        # Calculate confidence
        confidence = min(1.0, len(moved) / self.REFACTORING_MAX_FILES)

        return DetectedPattern(
            pattern_type=PatternType.REFACTORING,
            files=[c.path for c in moved],
            confidence=confidence,
            description=f"Refactoring: {len(moved)} files moved/renamed",
        )

    def _detect_cleanup(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect cleanup pattern (files deleted)."""
        deleted = [c for c in changes if c.change_type == ChangeType.DELETED]

        if len(deleted) < self.CLEANUP_MIN_FILES:
            return None

        # Calculate confidence
        confidence = min(1.0, len(deleted) / self.CLEANUP_MAX_FILES)

        return DetectedPattern(
            pattern_type=PatternType.CLEANUP,
            files=[c.path for c in deleted],
            confidence=confidence,
            description=f"Cleanup: {len(deleted)} files deleted",
        )

    def _detect_configuration(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect configuration changes."""
        config_extensions = {
            ".yml",
            ".yaml",
            ".json",
            ".toml",
            ".ini",
            ".conf",
            ".config",
            ".xml",
            ".properties",
            ".cfg",
        }
        config_names = {
            "Dockerfile",
            "Makefile",
            ".env",
            ".gitignore",
            "docker-compose.yml",
            "requirements.txt",
            "package.json",
            "pyproject.toml",
            "Cargo.toml",
            "go.mod",
            "pom.xml",
        }

        config_changes = [
            c
            for c in changes
            if c.path.suffix in config_extensions or c.path.name in config_names
        ]

        if not config_changes:
            return None

        # Calculate confidence (config files are distinctive)
        confidence = self.CONFIG_CONFIDENCE

        return DetectedPattern(
            pattern_type=PatternType.CONFIGURATION,
            files=[c.path for c in config_changes],
            confidence=confidence,
            description=f"Configuration: {len(config_changes)} config files changed",
        )

    async def create_activity_summary(
        self, changes: List[FileChange], time_window_minutes: int
    ) -> ActivitySummary:
        """
        Create activity summary from changes.

        Args:
            changes: File changes
            time_window_minutes: Time window in minutes

        Returns:
            Activity summary
        """
        # Detect patterns
        patterns = await self.detect_patterns(changes)

        # Count total files
        total_files = len({c.path for c in changes})

        # Find most active directory
        most_active_dir = self._find_most_active_directory(changes)

        return ActivitySummary(
            time_window_minutes=time_window_minutes,
            changes=changes,
            patterns=patterns,
            total_files_changed=total_files,
            most_active_directory=most_active_dir,
        )

    def _find_most_active_directory(self, changes: List[FileChange]) -> Optional[Path]:
        """Find directory with most changes."""
        if not changes:
            return None

        dir_counts: Dict[Path, int] = defaultdict(int)

        for change in changes:
            dir_counts[change.path.parent] += 1

        if not dir_counts:
            return None

        most_active = max(dir_counts.items(), key=lambda x: x[1])
        return most_active[0]

    async def save_activity(self, summary: ActivitySummary) -> None:
        """Save activity summary to file."""
        # Load existing activities
        existing_data = {}
        if self.activity_file.exists():
            existing_data = read_yaml(self.activity_file) or {}

        # Add new activity
        activities = existing_data.get("activities", [])

        # Convert to dict
        summary_dict = summary.model_dump()

        # Convert Path objects to strings
        summary_dict["changes"] = [
            {
                "path": str(c.path),
                "change_type": c.change_type.value,
                "timestamp": c.timestamp.isoformat(),
                "src_path": str(c.src_path) if c.src_path else None,
            }
            for c in summary.changes
        ]

        summary_dict["patterns"] = [
            {
                "pattern_type": p.pattern_type.value,
                "files": [str(f) for f in p.files],
                "confidence": p.confidence,
                "description": p.description,
                "timestamp": p.timestamp.isoformat(),
            }
            for p in summary.patterns
        ]

        if summary.most_active_directory:
            summary_dict["most_active_directory"] = str(summary.most_active_directory)

        activities.append(summary_dict)

        # Keep only last N activities
        activities = activities[-self.MAX_ACTIVITY_HISTORY :]

        # Save
        data = {"activities": activities}
        write_yaml(self.activity_file, data)
