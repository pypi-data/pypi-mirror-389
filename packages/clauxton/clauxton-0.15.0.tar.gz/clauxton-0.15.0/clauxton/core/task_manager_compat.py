"""
Backward compatibility layer for Task Management operations.

This module provides a compatibility wrapper that maps the legacy Task Management API
to the new unified Memory system. This allows existing code to continue working
while internally using the new Memory infrastructure.

DEPRECATED: This module is deprecated and will be removed in v0.17.0.
New code should use the Memory class directly with type='task'.

Example:
    >>> from pathlib import Path
    >>> tm = TaskManagerCompat(Path("."))
    >>> task = Task(...)
    >>> tm.add(task)
    'TASK-001'
"""

import warnings
from pathlib import Path
from typing import Any, Dict, List, Optional

from clauxton.core.memory import Memory, MemoryEntry
from clauxton.core.models import (
    DuplicateError,
    NotFoundError,
    Task,
    TaskPriorityType,
    TaskStatusType,
    ValidationError,
)


class TaskManagerCompat:
    """
    Backward compatibility layer for Task Management operations.

    Maps Task API to Memory system internally. All operations create
    Memory entries with type='task' and preserve legacy Task IDs.

    DEPRECATED: This class is deprecated and will be removed in v0.17.0.
    Please use the Memory class directly with type='task':

        # Old way (deprecated):
        tm = TaskManagerCompat(project_root)
        tm.add(task)

        # New way (recommended):
        memory = Memory(project_root)
        memory_entry = MemoryEntry(type="task", ...)
        memory.add(memory_entry)

    Attributes:
        memory: Unified Memory instance
        project_root: Project root directory

    Example:
        >>> tm = TaskManagerCompat(Path("."))
        >>> task = Task(
        ...     id="TASK-001",
        ...     name="Setup database",
        ...     description="Create PostgreSQL schema",
        ...     status="pending",
        ...     priority="high",
        ...     created_at=datetime.now()
        ... )
        >>> tm.add(task)
        'TASK-001'
    """

    def __init__(self, project_root: Path | str) -> None:
        """
        Initialize Task Manager compatibility layer.

        Args:
            project_root: Project root directory (Path or str)

        Warnings:
            DeprecationWarning: Always emitted on initialization

        Example:
            >>> tm = TaskManagerCompat(Path("."))
            >>> tm = TaskManagerCompat(".")  # str also works
        """
        self.project_root: Path = (
            Path(project_root) if isinstance(project_root, str) else project_root
        )
        self.memory = Memory(self.project_root)

        # Emit deprecation warning
        warnings.warn(
            "TaskManager API is deprecated and will be removed in v0.17.0. "
            "Please migrate to the Memory class with type='task'. "
            "See documentation: docs/v0.15.0_MIGRATION_GUIDE.md",
            DeprecationWarning,
            stacklevel=2
        )

    def add(self, task: Task) -> str:
        """
        Add task (maps to Memory entry with type=task).

        Args:
            task: Task to add

        Returns:
            Task ID (original Task ID for compatibility)

        Raises:
            DuplicateError: If task ID already exists
            ValidationError: If task validation fails

        Example:
            >>> task = Task(
            ...     id="TASK-001",
            ...     name="Setup database",
            ...     description="Create PostgreSQL schema",
            ...     status="pending",
            ...     created_at=datetime.now()
            ... )
            >>> tm.add(task)
            'TASK-001'
        """
        # Check if legacy_id already exists
        existing = self.memory.list_all(type_filter=["task"])
        for mem in existing:
            if mem.legacy_id == task.id:
                raise DuplicateError(
                    f"Task with ID '{task.id}' already exists. "
                    "Use update() to modify existing tasks."
                )

        # Build tags from status and priority
        tags: List[str] = [task.status, task.priority]
        if task.files_to_edit:
            tags.append("has-files")
        if task.depends_on:
            tags.append("has-dependencies")

        # Convert Task to Memory entry
        memory_entry = MemoryEntry(
            id=self.memory._generate_memory_id(),
            type="task",
            title=task.name,
            content=task.description or task.name,
            category=task.priority,  # Use priority as category
            tags=tags,
            created_at=task.created_at,
            updated_at=task.created_at,
            related_to=task.depends_on,  # Map dependencies to related_to
            source="manual",
            confidence=1.0,
            legacy_id=task.id,  # Store original Task ID
        )

        self.memory.add(memory_entry)
        return task.id  # Return original Task ID for compatibility

    def get(self, task_id: str) -> Task:
        """
        Get task by ID.

        Args:
            task_id: Task ID (e.g., "TASK-001")

        Returns:
            Task object

        Raises:
            NotFoundError: If task not found

        Example:
            >>> task = tm.get("TASK-001")
            >>> print(task.name)
            Setup database
        """
        # Find by legacy_id
        memories = self.memory.list_all(type_filter=["task"])
        for mem in memories:
            if mem.legacy_id == task_id:
                return self._to_task(mem)

        raise NotFoundError(
            f"Task with ID '{task_id}' not found. "
            "Use list_all() to see available tasks."
        )

    def list_all(
        self,
        status_filter: Optional[TaskStatusType] = None,
        priority_filter: Optional[TaskPriorityType] = None,
    ) -> List[Task]:
        """
        List all tasks with optional filters.

        Args:
            status_filter: Filter by status (e.g., "pending")
            priority_filter: Filter by priority (e.g., "high")

        Returns:
            List of Task objects

        Example:
            >>> tasks = tm.list_all(status_filter="pending")
            >>> len(tasks)
            5
        """
        # Get all task memories
        memories = self.memory.list_all(type_filter=["task"])
        tasks = [self._to_task(m) for m in memories]

        # Apply filters
        if status_filter:
            tasks = [t for t in tasks if t.status == status_filter]
        if priority_filter:
            tasks = [t for t in tasks if t.priority == priority_filter]

        return tasks

    def update(self, task_id: str, updates: Dict[str, Any]) -> Task:
        """
        Update task fields.

        Args:
            task_id: Task ID to update
            updates: Dictionary of fields to update

        Returns:
            Updated Task

        Raises:
            NotFoundError: If task not found
            ValidationError: If update validation fails

        Example:
            >>> updated = tm.update(
            ...     "TASK-001",
            ...     {"status": "in_progress", "started_at": datetime.now()}
            ... )
            >>> updated.status
            'in_progress'
        """
        # Find memory by legacy_id
        memories = self.memory.list_all(type_filter=["task"])
        memory_id = None
        for mem in memories:
            if mem.legacy_id == task_id:
                memory_id = mem.id
                break

        if memory_id is None:
            raise NotFoundError(
                f"Task with ID '{task_id}' not found."
            )

        # Convert task updates to memory updates
        mem_updates = self._task_updates_to_memory(updates)

        # Update memory
        success = self.memory.update(memory_id, **mem_updates)
        if not success:
            raise ValidationError(f"Failed to update task '{task_id}'")

        # Return updated task
        return self.get(task_id)

    def delete(self, task_id: str) -> bool:
        """
        Delete task.

        Args:
            task_id: Task ID to delete

        Returns:
            True if successful, False if not found

        Example:
            >>> success = tm.delete("TASK-001")
            >>> success
            True
        """
        # Find memory by legacy_id
        memories = self.memory.list_all(type_filter=["task"])
        for mem in memories:
            if mem.legacy_id == task_id:
                return self.memory.delete(mem.id)

        return False

    def _to_task(self, memory: MemoryEntry) -> Task:
        """
        Convert Memory entry to Task.

        Args:
            memory: MemoryEntry to convert

        Returns:
            Task object

        Raises:
            ValidationError: If conversion fails
        """
        # Use legacy_id if available, otherwise use memory ID
        task_id = memory.legacy_id or memory.id

        # Extract status and priority from tags
        status = "pending"
        priority = "medium"

        for tag in memory.tags:
            if tag in ["pending", "in_progress", "completed", "blocked"]:
                status = tag
            elif tag in ["low", "medium", "high", "critical"]:
                priority = tag

        # Also check category for priority (fallback)
        if memory.category in ["low", "medium", "high", "critical"]:
            priority = memory.category

        try:
            return Task(
                id=task_id,
                name=memory.title,
                description=memory.content if memory.content != memory.title else None,
                status=status,  # type: ignore  # Validated by Task model
                priority=priority,  # type: ignore  # Validated by Task model
                depends_on=memory.related_to,
                files_to_edit=[],  # Not stored in memory
                related_kb=[],  # Not stored in memory
                estimated_hours=None,  # Not stored in memory
                actual_hours=None,  # Not stored in memory
                created_at=memory.created_at,
                started_at=None,  # Not stored in memory
                completed_at=None,  # Not stored in memory
            )
        except Exception as e:
            raise ValidationError(
                f"Failed to convert Memory entry to Task: {e}"
            ) from e

    def _task_updates_to_memory(self, task_updates: Dict[str, Any]) -> Dict[str, Any]:
        """
        Convert task update kwargs to memory kwargs.

        Args:
            task_updates: Task field updates

        Returns:
            Memory field updates
        """
        mem_updates: Dict[str, Any] = {}

        # Map task fields to memory fields
        if "name" in task_updates:
            mem_updates["title"] = task_updates["name"]

        if "description" in task_updates:
            mem_updates["content"] = task_updates["description"]

        if "priority" in task_updates:
            mem_updates["category"] = task_updates["priority"]
            # Also update tags
            if "tags" not in mem_updates:
                mem_updates["tags"] = []
            mem_updates["tags"].append(task_updates["priority"])

        if "status" in task_updates:
            # Update tags to include status
            if "tags" not in mem_updates:
                mem_updates["tags"] = []
            mem_updates["tags"].append(task_updates["status"])

        if "depends_on" in task_updates:
            mem_updates["related_to"] = task_updates["depends_on"]

        return mem_updates

    def _generate_task_id(self) -> str:
        """
        Generate legacy Task ID.

        Returns:
            Task ID in format "TASK-NNN"

        Example:
            >>> tm._generate_task_id()
            'TASK-001'
        """
        # Find highest Task ID
        memories = self.memory.list_all(type_filter=["task"])
        task_ids = [
            m.legacy_id
            for m in memories
            if m.legacy_id and m.legacy_id.startswith("TASK-")
        ]

        if not task_ids:
            seq = 1
        else:
            seqs = [int(task_id.split("-")[-1]) for task_id in task_ids]
            seq = max(seqs) + 1

        return f"TASK-{seq:03d}"
