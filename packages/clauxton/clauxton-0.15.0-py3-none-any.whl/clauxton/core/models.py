"""
Pydantic data models for Clauxton.

This module defines all core data structures using Pydantic v2 for:
- Type safety and validation
- JSON serialization/deserialization
- AI-friendly, declarative code
"""

from datetime import datetime
from enum import Enum
from typing import List, Literal, Optional

from pydantic import BaseModel, Field, field_validator

# ============================================================================
# Enums
# ============================================================================


class Priority(str, Enum):
    """Task priority levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class TaskStatus(str, Enum):
    """Task status values."""

    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    BLOCKED = "blocked"


# ============================================================================
# Custom Exceptions
# ============================================================================


class ClauxtonError(Exception):
    """
    Base exception for all Clauxton errors.

    All Clauxton exceptions inherit from this class for easy catching.
    """

    pass


class ValidationError(ClauxtonError):
    """
    Raised when data validation fails.

    This includes:
    - Invalid KB entry or task data
    - Malformed YAML files
    - Schema validation failures
    - Field constraint violations

    Example:
        >>> raise ValidationError(
        ...     "Task name cannot be empty.\\n\\n"
        ...     "Suggestion: Provide a descriptive task name.\\n"
        ...     "  Example: --name 'Setup database schema'"
        ... )
    """

    pass


class NotFoundError(ClauxtonError):
    """
    Raised when an entity (KB entry, task, etc.) is not found.

    Best Practice: Include suggestion with available IDs or how to list them.

    Example:
        >>> available_ids = ["TASK-001", "TASK-002"]
        >>> raise NotFoundError(
        ...     "Task with ID 'TASK-999' not found.\\n\\n"
        ...     "Suggestion: Check if the task ID is correct.\\n"
        ...     f"  Available task IDs: {', '.join(available_ids)}\\n"
        ...     "  List all tasks: clauxton task list"
        ... )
    """

    pass


class DuplicateError(ClauxtonError):
    """
    Raised when attempting to create a duplicate entity.

    Best Practice: Include suggestion to update existing entity or use different ID.

    Example:
        >>> raise DuplicateError(
        ...     "Task with ID 'TASK-001' already exists.\\n\\n"
        ...     "Suggestion: Use a different task ID or update existing task.\\n"
        ...     "  Update existing: clauxton task update TASK-001 --name 'New name'\\n"
        ...     "  View existing: clauxton task get TASK-001"
        ... )
    """

    pass


class CycleDetectedError(ClauxtonError):
    """
    Raised when a circular dependency is detected in task graph.

    Best Practice: Include the cycle path and suggestion to break it.

    Example:
        >>> raise CycleDetectedError(
        ...     "Circular dependency detected: TASK-001 → TASK-002 → TASK-001\\n\\n"
        ...     "Suggestion: Remove one of the dependencies to break the cycle.\\n"
        ...     "  - Remove dependency: clauxton task update TASK-002 --remove-dep TASK-001\\n"
        ...     "  - View dependencies: clauxton task get TASK-001"
        ... )
    """

    pass


# ============================================================================
# Knowledge Base Models
# ============================================================================


class KnowledgeBaseEntry(BaseModel):
    """
    A single entry in the Knowledge Base.

    Knowledge Base entries capture persistent project context such as:
    - Architecture decisions (e.g., "We use FastAPI for all APIs")
    - Constraints (e.g., "Must support Python 3.11+")
    - Decisions (e.g., "Use PostgreSQL for production")
    - Patterns (e.g., "Repository pattern for data access")
    - Conventions (e.g., "Use Google-style docstrings")

    Attributes:
        id: Unique identifier (format: KB-YYYYMMDD-NNN)
        title: Short, descriptive title (max 50 chars)
        category: Type of knowledge (architecture, constraint, decision, pattern, convention)
        content: Detailed description (max 10,000 chars)
        tags: Optional tags for categorization
        created_at: Timestamp when entry was created
        updated_at: Timestamp when entry was last updated
        author: Optional author name (defaults to None for privacy)
        version: Entry version number (incremented on updates)

    Example:
        >>> entry = KnowledgeBaseEntry(
        ...     id="KB-20251019-001",
        ...     title="API uses FastAPI",
        ...     category="architecture",
        ...     content="All backend APIs use FastAPI framework with async endpoints.",
        ...     tags=["backend", "api"],
        ...     created_at=datetime.now(),
        ...     updated_at=datetime.now()
        ... )
        >>> entry.title
        'API uses FastAPI'
    """

    id: str = Field(
        ...,
        pattern=r"^KB-\d{8}-\d{3}$",
        description="Unique ID (format: KB-YYYYMMDD-NNN)",
    )
    title: str = Field(
        ..., min_length=1, max_length=50, description="Short entry title"
    )
    category: Literal[
        "architecture", "constraint", "decision", "pattern", "convention"
    ] = Field(..., description="Knowledge category")
    content: str = Field(
        ..., min_length=1, max_length=10000, description="Entry content"
    )
    tags: List[str] = Field(
        default_factory=list, description="Tags for categorization"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    updated_at: datetime = Field(..., description="Last update timestamp")
    author: Optional[str] = Field(None, description="Author name (optional)")
    version: int = Field(default=1, ge=1, description="Entry version number")

    @field_validator("content")
    @classmethod
    def sanitize_content(cls, v: str) -> str:
        """Remove leading/trailing whitespace from content."""
        sanitized = v.strip()
        if not sanitized:
            raise ValueError("Content cannot be empty or only whitespace")
        return sanitized

    @field_validator("title")
    @classmethod
    def sanitize_title(cls, v: str) -> str:
        """Remove leading/trailing whitespace from title."""
        sanitized = v.strip()
        if not sanitized:
            raise ValueError("Title cannot be empty or only whitespace")
        return sanitized

    @field_validator("tags")
    @classmethod
    def sanitize_tags(cls, v: List[str]) -> List[str]:
        """Remove empty tags and duplicates."""
        cleaned = [tag.strip().lower() for tag in v if tag.strip()]
        return list(dict.fromkeys(cleaned))  # Remove duplicates, preserve order


class KnowledgeBaseConfig(BaseModel):
    """
    Configuration for Knowledge Base.

    Stored at the top of knowledge-base.yml file.

    Attributes:
        version: KB schema version (for future migrations)
        project_name: Name of the project
        project_description: Optional project description

    Example:
        >>> config = KnowledgeBaseConfig(
        ...     version="1.0",
        ...     project_name="my-project",
        ...     project_description="E-commerce platform"
        ... )
        >>> config.project_name
        'my-project'
    """

    version: str = Field(default="1.0", description="KB schema version")
    project_name: str = Field(..., description="Project name")
    project_description: Optional[str] = Field(
        None, description="Project description"
    )


# ============================================================================
# Task Models (for Phase 1, defined here for forward compatibility)
# ============================================================================


class Task(BaseModel):
    """
    A single task in the task management system.

    Tasks represent units of work with dependencies forming a DAG.
    This model is defined in Phase 0 for forward compatibility but
    will be fully implemented in Phase 1.

    Attributes:
        id: Unique identifier (format: TASK-NNN)
        name: Short task name
        description: Detailed description
        status: Current status (pending, in_progress, completed, blocked)
        priority: Task priority level
        depends_on: List of task IDs this task depends on
        files_to_edit: List of files this task will modify
        related_kb: List of related KB entry IDs
        estimated_hours: Estimated time to complete
        actual_hours: Actual time spent
        created_at: Creation timestamp
        started_at: When task was started
        completed_at: When task was completed

    Example:
        >>> task = Task(
        ...     id="TASK-001",
        ...     name="Setup database",
        ...     description="Create PostgreSQL schema",
        ...     status="pending",
        ...     priority="high",
        ...     created_at=datetime.now()
        ... )
        >>> task.status
        'pending'
    """

    id: str = Field(..., pattern=r"^TASK-\d{3}$", description="Unique task ID")
    name: str = Field(..., min_length=1, max_length=100, description="Task name")
    description: Optional[str] = Field(None, description="Task description")
    status: Literal["pending", "in_progress", "completed", "blocked"] = Field(
        default="pending", description="Task status"
    )
    priority: Literal["low", "medium", "high", "critical"] = Field(
        default="medium", description="Task priority"
    )
    depends_on: List[str] = Field(
        default_factory=list, description="Task IDs this task depends on"
    )
    files_to_edit: List[str] = Field(
        default_factory=list, description="Files this task will modify"
    )
    related_kb: List[str] = Field(
        default_factory=list, description="Related KB entry IDs"
    )
    estimated_hours: Optional[float] = Field(
        None, ge=0, description="Estimated hours to complete"
    )
    actual_hours: Optional[float] = Field(
        None, ge=0, description="Actual hours spent"
    )
    created_at: datetime = Field(..., description="Creation timestamp")
    started_at: Optional[datetime] = Field(None, description="Start timestamp")
    completed_at: Optional[datetime] = Field(None, description="Completion timestamp")


# ============================================================================
# Conflict Detection Models (Phase 2)
# ============================================================================


class ConflictReport(BaseModel):
    """
    Report of a detected conflict between tasks.

    Conflicts occur when multiple tasks attempt to modify the same files,
    creating potential merge conflicts or coordination issues.

    Attributes:
        task_a_id: ID of first task involved in conflict
        task_b_id: ID of second task involved in conflict
        conflict_type: Type of conflict (file_overlap, dependency_violation)
        risk_level: Risk severity (low, medium, high)
        risk_score: Numerical risk score (0.0-1.0)
        overlapping_files: Files modified by both tasks
        details: Human-readable conflict description
        recommendation: Suggested action to resolve conflict

    Example:
        >>> conflict = ConflictReport(
        ...     task_a_id="TASK-001",
        ...     task_b_id="TASK-003",
        ...     conflict_type="file_overlap",
        ...     risk_level="high",
        ...     risk_score=0.85,
        ...     overlapping_files=["src/api/auth.py"],
        ...     details="Both tasks edit src/api/auth.py",
        ...     recommendation="Complete TASK-001 before starting TASK-003"
        ... )
        >>> conflict.risk_level
        'high'
    """

    task_a_id: str = Field(
        ..., pattern=r"^TASK-\d{3}$", description="First task ID"
    )
    task_b_id: str = Field(
        ..., pattern=r"^TASK-\d{3}$", description="Second task ID"
    )
    conflict_type: Literal["file_overlap", "dependency_violation"] = Field(
        ..., description="Type of conflict"
    )
    risk_level: Literal["low", "medium", "high"] = Field(
        ..., description="Risk severity level"
    )
    risk_score: float = Field(
        ..., ge=0.0, le=1.0, description="Numerical risk score (0.0-1.0)"
    )
    overlapping_files: List[str] = Field(
        default_factory=list, description="Files modified by both tasks"
    )
    details: str = Field(..., min_length=1, description="Conflict description")
    recommendation: str = Field(
        ..., min_length=1, description="Suggested resolution"
    )


# ============================================================================
# Helper Types
# ============================================================================


CategoryType = Literal["architecture", "constraint", "decision", "pattern", "convention"]
TaskStatusType = Literal["pending", "in_progress", "completed", "blocked"]
TaskPriorityType = Literal["low", "medium", "high", "critical"]
ConflictTypeType = Literal["file_overlap", "dependency_violation"]
RiskLevelType = Literal["low", "medium", "high"]


# ============================================================================
# MCP Response Models (v0.13.0 Week 3)
# ============================================================================


class MCPErrorResponse(BaseModel):
    """
    Standardized error response for MCP tools.

    Provides consistent error handling across all MCP tools with:
    - Categorized error types for programmatic handling
    - Human-readable messages for user feedback
    - Optional detailed information for debugging

    Error Types:
        - import_error: Required module/dependency not available
        - validation_error: Invalid input parameters or data
        - runtime_error: Unexpected exception during execution
        - filesystem_error: File system operations failed
        - git_error: Git operations failed

    Usage:
        Always check status field first. If "error", inspect error_type
        for programmatic handling and message for user display.
    """

    status: Literal["error"] = Field("error", description="Response status")
    error_type: str = Field(
        ...,
        description="Error category (import_error, validation_error, runtime_error)",
    )
    message: str = Field(..., min_length=1, description="Human-readable error message")
    details: Optional[str] = Field(None, description="Detailed error information")


class BreakPeriod(BaseModel):
    """Represents a break in work session."""

    start: str = Field(..., description="Break start timestamp (ISO format)")
    end: str = Field(..., description="Break end timestamp (ISO format)")
    duration_minutes: int = Field(..., ge=0, description="Break duration in minutes")


class ActivePeriod(BaseModel):
    """Represents an active work period."""

    start: str = Field(..., description="Period start timestamp (ISO format)")
    end: str = Field(..., description="Period end timestamp (ISO format)")
    duration_minutes: int = Field(..., ge=0, description="Period duration in minutes")


class WorkSessionAnalysis(BaseModel):
    """
    Response model for work session analysis.

    Provides comprehensive analysis of current work session including:
    - Session duration tracking
    - Focus score based on file switching patterns
    - Break detection (15+ minute gaps)
    - Active work periods
    - File modification statistics

    Status Values:
        - "success": Session analysis completed successfully
        - "no_session": No recent activity detected (no files modified)
        - "error": Analysis failed (check error field for details)

    Focus Score Interpretation:
        - 0.8-1.0: High focus (few context switches, deep work)
        - 0.5-0.8: Medium focus (moderate switching, normal work)
        - 0.0-0.5: Low focus (frequent switching, scattered work)

    Validation:
        - duration_minutes: Must be >= 0
        - focus_score: Must be in range [0.0, 1.0] or None
        - file_switches: Must be >= 0
    """

    status: Literal["success", "error", "no_session"] = Field(..., description="Response status")
    duration_minutes: int = Field(0, ge=0, description="Session duration in minutes")
    focus_score: Optional[float] = Field(None, ge=0.0, le=1.0, description="Focus score (0.0-1.0)")
    breaks: List[dict] = Field(default_factory=list, description="Detected breaks")
    file_switches: int = Field(0, ge=0, description="Number of unique files modified")
    active_periods: List[dict] = Field(default_factory=list, description="Active work periods")
    message: Optional[str] = Field(None, description="Status message (for no_session/error)")
    error: Optional[str] = Field(None, description="Error details (for error status)")


class NextActionPrediction(BaseModel):
    """
    Response model for next action prediction.

    Provides intelligent prediction of developer's likely next action based on:
    - File change patterns (tests vs implementation)
    - Git context (commits, branch status, uncommitted changes)
    - Time context (morning, afternoon, evening)
    - Work session patterns (duration, focus, breaks)

    Possible Actions:
        - "run_tests": Tests needed after implementation changes
        - "write_tests": Implementation complete, tests missing
        - "commit_changes": Changes ready to commit
        - "create_pr": Feature complete, ready for pull request
        - "take_break": Long session without breaks
        - "morning_planning": Start of day planning
        - "resume_work": Return from break
        - "review_code": Changes need review before commit
        - "no_clear_action": No strong pattern detected

    Confidence Levels:
        - 0.8-1.0: High confidence (strong pattern match)
        - 0.5-0.8: Medium confidence (moderate evidence)
        - 0.0-0.5: Low confidence (weak or conflicting signals)

    Validation:
        - confidence: Must be in range [0.0, 1.0] or None
        - action: Must be non-empty string if status="success"
    """

    status: Literal["success", "error"] = Field(..., description="Response status")
    action: Optional[str] = Field(None, description="Predicted action name")
    task_id: Optional[str] = Field(None, description="Related task ID")
    confidence: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Prediction confidence (0.0-1.0)"
    )
    reasoning: Optional[str] = Field(None, description="Explanation of prediction")
    message: Optional[str] = Field(None, description="Error message (for error status)")
    error: Optional[str] = Field(None, description="Error details (for error status)")


class CurrentContextResponse(BaseModel):
    """
    Response model for current context retrieval.

    Provides comprehensive real-time project context including:
    - Git information (branch, commits, uncommitted changes)
    - Active files and recent activity
    - Work session analysis (duration, focus, breaks)
    - Next action prediction (optional)
    - Time context for time-aware suggestions

    Context Categories:
        **Git Context**:
            - current_branch: Active git branch
            - is_feature_branch: Whether on feature branch
            - uncommitted_changes: Count of modified/staged files
            - recent_commits: Recent commit history

        **Session Context**:
            - session_duration_minutes: How long working
            - focus_score: Focus quality (0.0-1.0)
            - breaks_detected: Number of breaks taken
            - last_activity: Most recent file modification

        **Prediction Context**:
            - predicted_next_action: AI-suggested next step
            - prediction_error: Error if prediction failed

    Performance:
        - Cached for 30 seconds for fast response
        - Typical response time: <100ms
        - Prediction adds ~20ms overhead

    Validation:
        - focus_score: Must be in [0.0, 1.0] or None
        - session_duration_minutes: Must be >= 0 or None
        - breaks_detected: Must be >= 0
    """

    status: Literal["success", "error"] = Field(..., description="Response status")
    current_branch: Optional[str] = Field(None, description="Git branch name")
    active_files: List[str] = Field(
        default_factory=list, description="Recently modified files"
    )
    recent_commits: List[dict] = Field(
        default_factory=list, description="Recent commit information"
    )
    current_task: Optional[str] = Field(None, description="Current task ID")
    time_context: Optional[str] = Field(
        None, description="Time context (morning/afternoon/evening/night)"
    )
    work_session_start: Optional[str] = Field(
        None, description="Session start timestamp (ISO format)"
    )
    last_activity: Optional[str] = Field(
        None, description="Last activity timestamp (ISO format)"
    )
    is_feature_branch: bool = Field(
        False, description="Whether current branch is a feature branch"
    )
    is_git_repo: bool = Field(True, description="Whether project is a git repository")
    session_duration_minutes: Optional[int] = Field(
        None, ge=0, description="Current session duration"
    )
    focus_score: Optional[float] = Field(
        None, ge=0.0, le=1.0, description="Focus score (0.0-1.0)"
    )
    breaks_detected: int = Field(0, ge=0, description="Number of breaks detected")
    predicted_next_action: Optional[dict] = Field(
        None, description="Predicted next action (if enabled)"
    )
    uncommitted_changes: int = Field(0, ge=0, description="Number of uncommitted changes")
    diff_stats: Optional[dict] = Field(None, description="Git diff statistics")
    message: Optional[str] = Field(None, description="Error message (for error status)")
    error: Optional[str] = Field(None, description="Error details (for error status)")
