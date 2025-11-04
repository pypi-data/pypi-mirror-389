# v0.13.0 Week 1 Implementation Guide: File Monitoring & Event System

## Overview

**Goal**: Implement real-time file monitoring with intelligent change detection

**Duration**: Nov 25 - Dec 1 (5 working days)

**Deliverables**:
- File monitoring system using watchdog
- Event processing with pattern detection
- 2 new MCP tools: `watch_project_changes()`, `get_recent_changes()`
- 47+ tests (15 + 20 + 12)
- Documentation

---

## Setup (Before Starting)

### 1. Create Feature Branch

```bash
git checkout -b feature/proactive-intelligence-v0.13.0
```

### 2. Create Directory Structure

```bash
# Create directories
mkdir -p clauxton/proactive
mkdir -p tests/proactive

# Create __init__.py files
touch clauxton/proactive/__init__.py
touch tests/proactive/__init__.py

# Create module files
touch clauxton/proactive/file_monitor.py
touch clauxton/proactive/event_processor.py
touch clauxton/proactive/config.py
touch clauxton/proactive/models.py

# Create test files
touch tests/proactive/test_file_monitor.py
touch tests/proactive/test_event_processor.py
touch tests/proactive/test_mcp_monitoring.py
```

### 3. Install Dependencies

```bash
# Add watchdog to pyproject.toml first, then:
pip install watchdog>=3.0.0
pip install -e .
```

### 4. Update pyproject.toml

Add to `[project.dependencies]`:
```toml
dependencies = [
    # ... existing dependencies ...
    "watchdog>=3.0.0",
]
```

---

## Day 1-2: Watchdog Integration (Nov 25-26)

### Tasks

1. ✅ Implement `MonitorConfig` Pydantic model
2. ✅ Implement `FileMonitor` class with watchdog
3. ✅ Add ignore patterns configuration
4. ✅ Implement debouncing logic
5. ✅ Add thread safety
6. ✅ Write 15+ unit tests

---

### Step 1: Configuration Models (`clauxton/proactive/config.py`)

Create Pydantic models for configuration:

```python
"""Configuration models for proactive intelligence."""

from datetime import datetime
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class WatchConfig(BaseModel):
    """File watching configuration."""

    ignore_patterns: List[str] = Field(
        default=[
            "*.pyc",
            "*.pyo",
            "__pycache__/**",
            ".git/**",
            "node_modules/**",
            ".venv/**",
            "venv/**",
            "*.egg-info/**",
            ".mypy_cache/**",
            ".pytest_cache/**",
            ".coverage",
            "coverage.json",
            "*.log",
            "*.tmp",
            ".DS_Store",
            "Thumbs.db",
        ],
        description="Glob patterns to ignore",
    )

    debounce_ms: int = Field(
        default=500,
        ge=100,
        le=5000,
        description="Debounce interval in milliseconds",
    )


class SuggestionConfig(BaseModel):
    """Suggestion configuration."""

    enabled: bool = Field(default=True, description="Enable suggestions")
    min_confidence: float = Field(
        default=0.65,
        ge=0.0,
        le=1.0,
        description="Minimum confidence threshold",
    )
    max_per_context: int = Field(
        default=5,
        ge=1,
        le=20,
        description="Maximum suggestions per context",
    )
    notify_threshold: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Notify after N file changes",
    )


class LearningConfig(BaseModel):
    """Learning configuration."""

    enabled: bool = Field(default=True, description="Enable learning")
    update_frequency: str = Field(
        default="immediate",
        pattern="^(immediate|hourly|daily)$",
        description="Learning update frequency",
    )
    min_interactions: int = Field(
        default=10,
        ge=1,
        le=100,
        description="Min interactions before personalizing",
    )


class ContextConfig(BaseModel):
    """Context tracking configuration."""

    track_sessions: bool = Field(default=True, description="Track work sessions")
    track_time_patterns: bool = Field(
        default=True, description="Track time-based patterns"
    )
    session_timeout_minutes: int = Field(
        default=15,
        ge=5,
        le=60,
        description="Session timeout (no activity)",
    )


class MonitorConfig(BaseModel):
    """Complete monitoring configuration."""

    enabled: bool = Field(default=True, description="Enable monitoring")
    watch: WatchConfig = Field(default_factory=WatchConfig)
    suggestions: SuggestionConfig = Field(default_factory=SuggestionConfig)
    learning: LearningConfig = Field(default_factory=LearningConfig)
    context: ContextConfig = Field(default_factory=ContextConfig)

    @classmethod
    def load_from_file(cls, path: Path) -> "MonitorConfig":
        """Load configuration from YAML file."""
        from clauxton.utils.yaml_utils import read_yaml

        if not path.exists():
            return cls()

        data = read_yaml(path)
        return cls(**data.get("monitoring", {}))

    def save_to_file(self, path: Path) -> None:
        """Save configuration to YAML file."""
        from clauxton.utils.yaml_utils import write_yaml

        data = {"monitoring": self.model_dump()}
        write_yaml(path, data)
```

**Test File**: `tests/proactive/test_config.py`

```python
"""Tests for configuration models."""

from pathlib import Path

import pytest

from clauxton.proactive.config import (
    ContextConfig,
    LearningConfig,
    MonitorConfig,
    SuggestionConfig,
    WatchConfig,
)


def test_watch_config_defaults():
    """Test WatchConfig default values."""
    config = WatchConfig()

    assert "*.pyc" in config.ignore_patterns
    assert ".git/**" in config.ignore_patterns
    assert config.debounce_ms == 500


def test_watch_config_custom():
    """Test WatchConfig with custom values."""
    config = WatchConfig(
        ignore_patterns=["*.log", "temp/**"],
        debounce_ms=1000,
    )

    assert config.ignore_patterns == ["*.log", "temp/**"]
    assert config.debounce_ms == 1000


def test_watch_config_validation():
    """Test WatchConfig validation."""
    # Debounce too low
    with pytest.raises(ValueError):
        WatchConfig(debounce_ms=50)

    # Debounce too high
    with pytest.raises(ValueError):
        WatchConfig(debounce_ms=10000)


def test_suggestion_config_defaults():
    """Test SuggestionConfig defaults."""
    config = SuggestionConfig()

    assert config.enabled is True
    assert config.min_confidence == 0.65
    assert config.max_per_context == 5
    assert config.notify_threshold == 3


def test_monitor_config_defaults():
    """Test MonitorConfig with all defaults."""
    config = MonitorConfig()

    assert config.enabled is True
    assert isinstance(config.watch, WatchConfig)
    assert isinstance(config.suggestions, SuggestionConfig)
    assert isinstance(config.learning, LearningConfig)
    assert isinstance(config.context, ContextConfig)


def test_monitor_config_save_load(tmp_path: Path):
    """Test saving and loading configuration."""
    config_path = tmp_path / "monitoring_config.yml"

    # Create custom config
    config = MonitorConfig(
        enabled=True,
        watch=WatchConfig(debounce_ms=1000),
        suggestions=SuggestionConfig(min_confidence=0.75),
    )

    # Save
    config.save_to_file(config_path)
    assert config_path.exists()

    # Load
    loaded = MonitorConfig.load_from_file(config_path)
    assert loaded.enabled is True
    assert loaded.watch.debounce_ms == 1000
    assert loaded.suggestions.min_confidence == 0.75


def test_monitor_config_load_nonexistent(tmp_path: Path):
    """Test loading from non-existent file returns defaults."""
    config_path = tmp_path / "nonexistent.yml"

    config = MonitorConfig.load_from_file(config_path)

    # Should return defaults
    assert config.enabled is True
    assert config.watch.debounce_ms == 500
```

---

### Step 2: Data Models (`clauxton/proactive/models.py`)

Create models for file changes and events:

```python
"""Data models for proactive intelligence."""

from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List, Optional

from pydantic import BaseModel, Field


class ChangeType(str, Enum):
    """Type of file system change."""

    CREATED = "created"
    MODIFIED = "modified"
    DELETED = "deleted"
    MOVED = "moved"


class FileChange(BaseModel):
    """Represents a file system change."""

    path: Path = Field(..., description="File path")
    change_type: ChangeType = Field(..., description="Type of change")
    timestamp: datetime = Field(default_factory=datetime.now)
    src_path: Optional[Path] = Field(
        None, description="Source path for move operations"
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat(),
        }


class PatternType(str, Enum):
    """Type of detected pattern."""

    BULK_EDIT = "bulk_edit"  # Many files modified quickly
    NEW_FEATURE = "new_feature"  # New files created
    REFACTORING = "refactoring"  # Files renamed/moved
    CLEANUP = "cleanup"  # Files deleted
    CONFIGURATION = "configuration"  # Config files changed


class DetectedPattern(BaseModel):
    """Represents a detected pattern in file changes."""

    pattern_type: PatternType = Field(..., description="Type of pattern")
    files: List[Path] = Field(..., description="Files involved")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence score")
    description: str = Field(..., description="Human-readable description")
    timestamp: datetime = Field(default_factory=datetime.now)

    class Config:
        """Pydantic config."""

        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat(),
        }


class ActivitySummary(BaseModel):
    """Summary of recent activity."""

    time_window_minutes: int = Field(..., description="Time window in minutes")
    changes: List[FileChange] = Field(..., description="File changes")
    patterns: List[DetectedPattern] = Field(..., description="Detected patterns")
    total_files_changed: int = Field(..., description="Total files changed")
    most_active_directory: Optional[Path] = Field(
        None, description="Most active directory"
    )

    class Config:
        """Pydantic config."""

        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat(),
        }
```

---

### Step 3: File Monitor (`clauxton/proactive/file_monitor.py`)

Implement the core file monitoring system:

```python
"""Real-time file monitoring using watchdog."""

import threading
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Deque, List, Optional

from watchdog.events import (
    DirCreatedEvent,
    DirDeletedEvent,
    DirModifiedEvent,
    DirMovedEvent,
    FileCreatedEvent,
    FileDeletedEvent,
    FileModifiedEvent,
    FileMovedEvent,
    FileSystemEvent,
    FileSystemEventHandler,
)
from watchdog.observers import Observer

from clauxton.proactive.config import MonitorConfig, WatchConfig
from clauxton.proactive.models import ActivitySummary, ChangeType, FileChange


class IgnorePatternMatcher:
    """Match file paths against ignore patterns."""

    def __init__(self, patterns: List[str]):
        """Initialize with ignore patterns."""
        self.patterns = patterns

    def should_ignore(self, path: Path) -> bool:
        """Check if path matches any ignore pattern."""
        path_str = str(path)

        for pattern in self.patterns:
            # Simple wildcard matching
            if pattern.startswith("*"):
                # *.pyc pattern
                if path_str.endswith(pattern[1:]):
                    return True
            elif pattern.endswith("/**"):
                # .git/** pattern
                directory = pattern[:-3]
                if f"/{directory}/" in path_str or path_str.endswith(f"/{directory}"):
                    return True
            elif pattern in path_str:
                # Substring match
                return True

        return False


class ChangeEventHandler(FileSystemEventHandler):
    """Handle file system events from watchdog."""

    def __init__(
        self,
        project_root: Path,
        ignore_matcher: IgnorePatternMatcher,
        change_queue: Deque[FileChange],
        debounce_ms: int,
    ):
        """Initialize event handler."""
        super().__init__()
        self.project_root = project_root
        self.ignore_matcher = ignore_matcher
        self.change_queue = change_queue
        self.debounce_ms = debounce_ms
        self.last_event_time: dict = {}
        self.lock = threading.Lock()

    def _should_process(self, path: Path) -> bool:
        """Check if event should be processed."""
        # Ignore if matches patterns
        if self.ignore_matcher.should_ignore(path):
            return False

        # Debounce: ignore if event for same file within debounce window
        path_str = str(path)
        current_time = time.time()

        with self.lock:
            last_time = self.last_event_time.get(path_str, 0)
            time_diff_ms = (current_time - last_time) * 1000

            if time_diff_ms < self.debounce_ms:
                return False

            self.last_event_time[path_str] = current_time

        return True

    def _add_change(self, path: Path, change_type: ChangeType, src_path: Optional[Path] = None):
        """Add change to queue."""
        if not self._should_process(path):
            return

        change = FileChange(
            path=path,
            change_type=change_type,
            timestamp=datetime.now(),
            src_path=src_path,
        )

        with self.lock:
            self.change_queue.append(change)

    def on_created(self, event: FileSystemEvent) -> None:
        """Handle file/directory creation."""
        if isinstance(event, (FileCreatedEvent, DirCreatedEvent)):
            self._add_change(Path(event.src_path), ChangeType.CREATED)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file/directory modification."""
        if isinstance(event, (FileModifiedEvent, DirModifiedEvent)):
            # Ignore directory modifications (too noisy)
            if isinstance(event, DirModifiedEvent):
                return
            self._add_change(Path(event.src_path), ChangeType.MODIFIED)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file/directory deletion."""
        if isinstance(event, (FileDeletedEvent, DirDeletedEvent)):
            self._add_change(Path(event.src_path), ChangeType.DELETED)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file/directory move/rename."""
        if isinstance(event, (FileMovedEvent, DirMovedEvent)):
            self._add_change(
                Path(event.dest_path),
                ChangeType.MOVED,
                src_path=Path(event.src_path),
            )


class FileMonitor:
    """Monitor file system changes in real-time."""

    def __init__(self, project_root: Path, config: Optional[MonitorConfig] = None):
        """
        Initialize file monitor.

        Args:
            project_root: Project root directory
            config: Monitoring configuration (defaults if None)
        """
        self.project_root = project_root.resolve()
        self.config = config or MonitorConfig()
        self.is_running = False

        # Change queue (thread-safe deque)
        self.change_queue: Deque[FileChange] = deque(maxlen=1000)

        # Ignore pattern matcher
        self.ignore_matcher = IgnorePatternMatcher(self.config.watch.ignore_patterns)

        # Event handler
        self.event_handler = ChangeEventHandler(
            project_root=self.project_root,
            ignore_matcher=self.ignore_matcher,
            change_queue=self.change_queue,
            debounce_ms=self.config.watch.debounce_ms,
        )

        # Watchdog observer
        self.observer: Optional[Observer] = None

    def start(self) -> None:
        """Start monitoring file system."""
        if self.is_running:
            raise RuntimeError("FileMonitor is already running")

        self.observer = Observer()
        self.observer.schedule(
            self.event_handler,
            str(self.project_root),
            recursive=True,
        )
        self.observer.start()
        self.is_running = True

    def stop(self) -> None:
        """Stop monitoring file system."""
        if not self.is_running:
            return

        if self.observer:
            self.observer.stop()
            self.observer.join(timeout=5.0)
            self.observer = None

        self.is_running = False

    def get_recent_changes(self, minutes: int = 10) -> List[FileChange]:
        """
        Get file changes from last N minutes.

        Args:
            minutes: Time window in minutes

        Returns:
            List of FileChange objects
        """
        cutoff_time = datetime.now() - timedelta(minutes=minutes)

        with self.event_handler.lock:
            recent_changes = [
                change for change in self.change_queue if change.timestamp >= cutoff_time
            ]

        return recent_changes

    def clear_history(self) -> None:
        """Clear change history."""
        with self.event_handler.lock:
            self.change_queue.clear()
            self.event_handler.last_event_time.clear()
```

---

### Step 4: Tests for File Monitor (`tests/proactive/test_file_monitor.py`)

Create comprehensive tests:

```python
"""Tests for file monitoring."""

import time
from pathlib import Path

import pytest

from clauxton.proactive.config import MonitorConfig, WatchConfig
from clauxton.proactive.file_monitor import FileMonitor, IgnorePatternMatcher
from clauxton.proactive.models import ChangeType


class TestIgnorePatternMatcher:
    """Tests for IgnorePatternMatcher."""

    def test_ignore_pyc_files(self):
        """Test ignoring .pyc files."""
        matcher = IgnorePatternMatcher(["*.pyc"])

        assert matcher.should_ignore(Path("test.pyc"))
        assert matcher.should_ignore(Path("foo/bar/test.pyc"))
        assert not matcher.should_ignore(Path("test.py"))

    def test_ignore_git_directory(self):
        """Test ignoring .git directory."""
        matcher = IgnorePatternMatcher([".git/**"])

        assert matcher.should_ignore(Path(".git/config"))
        assert matcher.should_ignore(Path(".git/objects/abc"))
        assert matcher.should_ignore(Path("foo/.git/config"))
        assert not matcher.should_ignore(Path("foo/bar.py"))

    def test_ignore_multiple_patterns(self):
        """Test multiple ignore patterns."""
        matcher = IgnorePatternMatcher(["*.pyc", ".git/**", "node_modules/**"])

        assert matcher.should_ignore(Path("test.pyc"))
        assert matcher.should_ignore(Path(".git/config"))
        assert matcher.should_ignore(Path("node_modules/package.json"))
        assert not matcher.should_ignore(Path("src/main.py"))


class TestFileMonitor:
    """Tests for FileMonitor."""

    def test_init(self, tmp_path: Path):
        """Test FileMonitor initialization."""
        monitor = FileMonitor(tmp_path)

        assert monitor.project_root == tmp_path.resolve()
        assert not monitor.is_running
        assert isinstance(monitor.config, MonitorConfig)

    def test_init_with_config(self, tmp_path: Path):
        """Test FileMonitor with custom config."""
        config = MonitorConfig(
            watch=WatchConfig(debounce_ms=1000, ignore_patterns=["*.log"])
        )
        monitor = FileMonitor(tmp_path, config=config)

        assert monitor.config.watch.debounce_ms == 1000
        assert "*.log" in monitor.config.watch.ignore_patterns

    def test_start_stop(self, tmp_path: Path):
        """Test starting and stopping monitor."""
        monitor = FileMonitor(tmp_path)

        assert not monitor.is_running

        monitor.start()
        assert monitor.is_running
        assert monitor.observer is not None

        monitor.stop()
        assert not monitor.is_running
        assert monitor.observer is None

    def test_start_already_running(self, tmp_path: Path):
        """Test starting monitor when already running."""
        monitor = FileMonitor(tmp_path)
        monitor.start()

        with pytest.raises(RuntimeError, match="already running"):
            monitor.start()

        monitor.stop()

    def test_detect_file_creation(self, tmp_path: Path):
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

    def test_detect_file_modification(self, tmp_path: Path):
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
            modified_changes = [c for c in changes if c.change_type == ChangeType.MODIFIED]

            assert len(modified_changes) > 0
            assert any("test.txt" in str(c.path) for c in modified_changes)

        finally:
            monitor.stop()

    def test_detect_file_deletion(self, tmp_path: Path):
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

    def test_ignore_patterns(self, tmp_path: Path):
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

    def test_debouncing(self, tmp_path: Path):
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

    def test_get_recent_changes_time_window(self, tmp_path: Path):
        """Test time window filtering."""
        monitor = FileMonitor(tmp_path)

        # Manually add changes with different timestamps
        from datetime import datetime, timedelta

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

    def test_clear_history(self, tmp_path: Path):
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
```

---

## Day 3-4: Event Processing & Pattern Detection (Nov 27-28)

### Tasks

1. ✅ Implement `EventProcessor` class
2. ✅ Pattern detection algorithms
3. ✅ Activity timeline storage
4. ✅ Integration with FileMonitor
5. ✅ Write 20+ unit tests

---

### Implementation: Event Processor (`clauxton/proactive/event_processor.py`)

```python
"""Process file system events and detect patterns."""

import asyncio
from collections import Counter, defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

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

    def __init__(self, project_root: Path):
        """Initialize event processor."""
        self.project_root = project_root
        self.clauxton_dir = project_root / ".clauxton"
        self.activity_file = self.clauxton_dir / "activity.yml"

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

        patterns: List[DetectedPattern] = []

        # Detect bulk edit (many modifications in short time)
        bulk_edit = self._detect_bulk_edit(changes)
        if bulk_edit and bulk_edit.confidence >= confidence_threshold:
            patterns.append(bulk_edit)

        # Detect new feature (new files created)
        new_feature = self._detect_new_feature(changes)
        if new_feature and new_feature.confidence >= confidence_threshold:
            patterns.append(new_feature)

        # Detect refactoring (files moved/renamed)
        refactoring = self._detect_refactoring(changes)
        if refactoring and refactoring.confidence >= confidence_threshold:
            patterns.append(refactoring)

        # Detect cleanup (files deleted)
        cleanup = self._detect_cleanup(changes)
        if cleanup and cleanup.confidence >= confidence_threshold:
            patterns.append(cleanup)

        # Detect configuration changes
        config_change = self._detect_configuration(changes)
        if config_change and config_change.confidence >= confidence_threshold:
            patterns.append(config_change)

        return patterns

    def _detect_bulk_edit(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect bulk editing pattern."""
        modified = [c for c in changes if c.change_type == ChangeType.MODIFIED]

        if len(modified) < 3:
            return None

        # Check time span (bulk edit = many files in short time)
        if modified:
            time_span = max(c.timestamp for c in modified) - min(
                c.timestamp for c in modified
            )
            if time_span > timedelta(minutes=5):
                return None

        # Calculate confidence based on number of files
        confidence = min(1.0, len(modified) / 10.0)

        return DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[c.path for c in modified],
            confidence=confidence,
            description=f"Bulk edit: {len(modified)} files modified",
        )

    def _detect_new_feature(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect new feature pattern (new files created)."""
        created = [c for c in changes if c.change_type == ChangeType.CREATED]

        if len(created) < 2:
            return None

        # Check if files are in same directory (likely related)
        directories = [c.path.parent for c in created]
        dir_counts = Counter(directories)
        most_common_dir, count = dir_counts.most_common(1)[0]

        if count < 2:
            return None

        # Calculate confidence
        confidence = min(1.0, count / 5.0)

        return DetectedPattern(
            pattern_type=PatternType.NEW_FEATURE,
            files=[c.path for c in created if c.path.parent == most_common_dir],
            confidence=confidence,
            description=f"New feature: {count} new files in {most_common_dir.name}/",
        )

    def _detect_refactoring(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect refactoring pattern (files moved/renamed)."""
        moved = [c for c in changes if c.change_type == ChangeType.MOVED]

        if len(moved) < 2:
            return None

        # Calculate confidence
        confidence = min(1.0, len(moved) / 5.0)

        return DetectedPattern(
            pattern_type=PatternType.REFACTORING,
            files=[c.path for c in moved],
            confidence=confidence,
            description=f"Refactoring: {len(moved)} files moved/renamed",
        )

    def _detect_cleanup(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect cleanup pattern (files deleted)."""
        deleted = [c for c in changes if c.change_type == ChangeType.DELETED]

        if len(deleted) < 2:
            return None

        # Calculate confidence
        confidence = min(1.0, len(deleted) / 5.0)

        return DetectedPattern(
            pattern_type=PatternType.CLEANUP,
            files=[c.path for c in deleted],
            confidence=confidence,
            description=f"Cleanup: {len(deleted)} files deleted",
        )

    def _detect_configuration(self, changes: List[FileChange]) -> Optional[DetectedPattern]:
        """Detect configuration changes."""
        config_extensions = {".yml", ".yaml", ".json", ".toml", ".ini", ".conf", ".config"}
        config_names = {"Dockerfile", "Makefile", ".env", ".gitignore"}

        config_changes = [
            c
            for c in changes
            if c.path.suffix in config_extensions or c.path.name in config_names
        ]

        if not config_changes:
            return None

        # Calculate confidence (config files are distinctive)
        confidence = 0.9

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

        # Keep only last 100 activities
        activities = activities[-100:]

        # Save
        data = {"activities": activities}
        write_yaml(self.activity_file, data)
```

**Day 3-4 Tests**: See `tests/proactive/test_event_processor.py` (20+ tests for pattern detection)

---

## Day 5: MCP Tools (Nov 29)

### Tasks

1. ✅ Implement `watch_project_changes()` MCP tool
2. ✅ Implement `get_recent_changes()` MCP tool
3. ✅ Integration tests
4. ✅ Update MCP server documentation

---

### Implementation: MCP Tools (`clauxton/mcp/server.py`)

Add to existing MCP server:

```python
# Add to imports
from clauxton.proactive.file_monitor import FileMonitor
from clauxton.proactive.event_processor import EventProcessor
from clauxton.proactive.config import MonitorConfig

# Global monitor instance (initialized when needed)
_file_monitor: Optional[FileMonitor] = None
_event_processor: Optional[EventProcessor] = None


def _get_file_monitor() -> FileMonitor:
    """Get or create FileMonitor instance."""
    global _file_monitor

    if _file_monitor is None:
        project_root = _get_project_root()
        config_path = project_root / ".clauxton" / "monitoring_config.yml"
        config = MonitorConfig.load_from_file(config_path)
        _file_monitor = FileMonitor(project_root, config=config)

    return _file_monitor


def _get_event_processor() -> EventProcessor:
    """Get or create EventProcessor instance."""
    global _event_processor

    if _event_processor is None:
        project_root = _get_project_root()
        _event_processor = EventProcessor(project_root)

    return _event_processor


@server.call_tool()
async def watch_project_changes(
    enabled: bool, config: Optional[dict] = None
) -> dict:
    """
    Enable or disable real-time file monitoring.

    Args:
        enabled: True to enable monitoring, False to disable
        config: Optional configuration overrides

    Returns:
        Status and current configuration
    """
    try:
        monitor = _get_file_monitor()

        if enabled:
            if not monitor.is_running:
                # Update config if provided
                if config:
                    # Merge with existing config
                    monitor.config = MonitorConfig(**config)

                monitor.start()

                return {
                    "status": "enabled",
                    "message": "File monitoring started",
                    "config": monitor.config.model_dump(),
                }
            else:
                return {
                    "status": "already_enabled",
                    "message": "File monitoring already running",
                    "config": monitor.config.model_dump(),
                }
        else:
            if monitor.is_running:
                monitor.stop()

                return {
                    "status": "disabled",
                    "message": "File monitoring stopped",
                }
            else:
                return {
                    "status": "already_disabled",
                    "message": "File monitoring not running",
                }

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }


@server.call_tool()
async def get_recent_changes(
    minutes: int = 10, include_patterns: bool = True
) -> dict:
    """
    Get recent file changes and detected patterns.

    Args:
        minutes: Time window in minutes (default: 10)
        include_patterns: Include detected patterns (default: True)

    Returns:
        Recent changes and activity summary
    """
    try:
        monitor = _get_file_monitor()

        # Get recent changes
        changes = monitor.get_recent_changes(minutes=minutes)

        if not changes:
            return {
                "status": "no_changes",
                "message": f"No changes in last {minutes} minutes",
                "changes": [],
                "patterns": [],
            }

        # Create activity summary
        processor = _get_event_processor()
        summary = await processor.create_activity_summary(changes, minutes)

        # Save activity
        await processor.save_activity(summary)

        # Build response
        response = {
            "status": "success",
            "time_window_minutes": minutes,
            "total_files_changed": summary.total_files_changed,
            "changes": [
                {
                    "path": str(c.path),
                    "change_type": c.change_type.value,
                    "timestamp": c.timestamp.isoformat(),
                    "src_path": str(c.src_path) if c.src_path else None,
                }
                for c in changes
            ],
        }

        if include_patterns and summary.patterns:
            response["patterns"] = [
                {
                    "pattern_type": p.pattern_type.value,
                    "files": [str(f) for f in p.files],
                    "confidence": p.confidence,
                    "description": p.description,
                }
                for p in summary.patterns
            ]

        if summary.most_active_directory:
            response["most_active_directory"] = str(summary.most_active_directory)

        return response

    except Exception as e:
        return {
            "status": "error",
            "error": str(e),
        }
```

---

## Testing Checklist

### Unit Tests (47 total)

**Configuration (7 tests)**:
- [x] Default values
- [x] Custom values
- [x] Validation
- [x] Save/load from file

**File Monitor (15 tests)**:
- [x] Initialization
- [x] Start/stop
- [x] Detect file creation
- [x] Detect file modification
- [x] Detect file deletion
- [x] Detect file move
- [x] Ignore patterns
- [x] Debouncing
- [x] Time window filtering
- [x] Thread safety
- [x] Clear history

**Event Processor (20 tests)**:
- [x] Detect bulk edit
- [x] Detect new feature
- [x] Detect refactoring
- [x] Detect cleanup
- [x] Detect configuration
- [x] Pattern confidence scoring
- [x] Activity summary creation
- [x] Most active directory
- [x] Save/load activity

**MCP Tools (12 tests)**:
- [x] Enable monitoring
- [x] Disable monitoring
- [x] Get recent changes
- [x] Include/exclude patterns
- [x] Error handling
- [x] Configuration updates

---

## Documentation

### Update README.md

Add to Features section:
```markdown
- **Proactive Intelligence** (v0.13.0)
  - 📁 Real-time file monitoring with pattern detection
  - 💡 Contextual suggestions based on your work
  - 🧠 Learns from your behavior (100% local)
  - 🎯 Enhanced context awareness
```

### Create User Guide

Create `docs/proactive-intelligence.md` with:
- How to enable monitoring
- Understanding suggestions
- Privacy guarantees
- Configuration options

---

## Success Criteria

Week 1 is complete when:

- [x] All 47+ tests passing
- [x] Coverage >85% for new modules
- [x] File monitoring works in real project
- [x] MCP tools callable from Claude Code
- [x] Documentation complete
- [x] No performance issues (CPU <5%, memory <50MB)

---

## Command Reference

```bash
# Run Week 1 tests
pytest tests/proactive/test_config.py -v
pytest tests/proactive/test_file_monitor.py -v
pytest tests/proactive/test_event_processor.py -v
pytest tests/proactive/test_mcp_monitoring.py -v

# Run all tests
pytest tests/proactive/ -v

# Coverage report
pytest tests/proactive/ --cov=clauxton.proactive --cov-report=term

# Type checking
mypy clauxton/proactive/

# Linting
ruff check clauxton/proactive/
```

---

## Next Steps (Week 2)

After Week 1 is complete, move to Week 2:
- Suggestion engine (relevance scoring)
- User behavior learning
- MCP tools for suggestions

---

**Ready to start implementation! 🚀**
