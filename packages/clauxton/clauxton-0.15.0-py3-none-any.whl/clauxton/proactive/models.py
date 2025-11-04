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


class ActivitySummary(BaseModel):
    """Summary of recent activity."""

    time_window_minutes: int = Field(..., description="Time window in minutes")
    changes: List[FileChange] = Field(..., description="File changes")
    patterns: List[DetectedPattern] = Field(..., description="Detected patterns")
    total_files_changed: int = Field(..., description="Total files changed")
    most_active_directory: Optional[Path] = Field(
        None, description="Most active directory"
    )
