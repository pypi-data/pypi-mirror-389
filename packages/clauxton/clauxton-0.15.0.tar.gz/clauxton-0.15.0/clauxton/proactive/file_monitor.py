"""Real-time file monitoring using watchdog."""

import threading
import time
from collections import deque
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Deque, Dict, List, Optional

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

from clauxton.proactive.config import MonitorConfig
from clauxton.proactive.models import ChangeType, FileChange


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
                # .git/** pattern - matches directory and all contents
                directory = pattern[:-3]
                # Match if path starts with directory/ or contains /directory/
                if path_str.startswith(f"{directory}/") or f"/{directory}/" in path_str:
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
        max_debounce_entries: int,
        debounce_cleanup_hours: int,
    ):
        """Initialize event handler."""
        super().__init__()
        self.project_root = project_root
        self.ignore_matcher = ignore_matcher
        self.change_queue = change_queue
        self.debounce_ms = debounce_ms
        self.max_debounce_entries = max_debounce_entries
        self.debounce_cleanup_hours = debounce_cleanup_hours
        self.last_event_time: Dict[str, float] = {}
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
            # Cleanup old entries if threshold reached
            if len(self.last_event_time) > self.max_debounce_entries:
                cutoff_time = current_time - (self.debounce_cleanup_hours * 3600)
                self.last_event_time = {
                    k: v
                    for k, v in self.last_event_time.items()
                    if v >= cutoff_time
                }

            last_time = self.last_event_time.get(path_str, 0)
            time_diff_ms = (current_time - last_time) * 1000

            if time_diff_ms < self.debounce_ms:
                return False

            self.last_event_time[path_str] = current_time

        return True

    def _add_change(
        self, path: Path, change_type: ChangeType, src_path: Optional[Path] = None
    ) -> None:
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
            self._add_change(Path(str(event.src_path)), ChangeType.CREATED)

    def on_modified(self, event: FileSystemEvent) -> None:
        """Handle file/directory modification."""
        if isinstance(event, (FileModifiedEvent, DirModifiedEvent)):
            # Ignore directory modifications (too noisy)
            if isinstance(event, DirModifiedEvent):
                return
            self._add_change(Path(str(event.src_path)), ChangeType.MODIFIED)

    def on_deleted(self, event: FileSystemEvent) -> None:
        """Handle file/directory deletion."""
        if isinstance(event, (FileDeletedEvent, DirDeletedEvent)):
            self._add_change(Path(str(event.src_path)), ChangeType.DELETED)

    def on_moved(self, event: FileSystemEvent) -> None:
        """Handle file/directory move/rename."""
        if isinstance(event, (FileMovedEvent, DirMovedEvent)):
            self._add_change(
                Path(str(event.dest_path)),
                ChangeType.MOVED,
                src_path=Path(str(event.src_path)),
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

        # Change queue (thread-safe deque with configurable size)
        self.change_queue: Deque[FileChange] = deque(
            maxlen=self.config.watch.max_queue_size
        )

        # Ignore pattern matcher
        self.ignore_matcher = IgnorePatternMatcher(self.config.watch.ignore_patterns)

        # Event handler
        self.event_handler = ChangeEventHandler(
            project_root=self.project_root,
            ignore_matcher=self.ignore_matcher,
            change_queue=self.change_queue,
            debounce_ms=self.config.watch.debounce_ms,
            max_debounce_entries=self.config.watch.max_debounce_entries,
            debounce_cleanup_hours=self.config.watch.debounce_cleanup_hours,
        )

        # Watchdog observer (type: ignore due to watchdog type stubs issue)
        self.observer: Optional[Any] = None

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
                change
                for change in self.change_queue
                if change.timestamp >= cutoff_time
            ]

        return recent_changes

    def clear_history(self) -> None:
        """Clear change history."""
        with self.event_handler.lock:
            self.change_queue.clear()
            self.event_handler.last_event_time.clear()
