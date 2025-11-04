"""
Tests for backward compatibility layer (KB and Task Manager).

This test suite ensures that:
1. Legacy KB API works seamlessly with Memory system
2. Legacy Task API works seamlessly with Memory system
3. Conversion between old and new models is accurate
4. Deprecation warnings are properly emitted
5. Integration between KB and Task APIs works correctly
"""

import warnings
from datetime import datetime
from pathlib import Path

import pytest

from clauxton.core.knowledge_base_compat import KnowledgeBaseCompat
from clauxton.core.memory import Memory
from clauxton.core.models import (
    DuplicateError,
    KnowledgeBaseEntry,
    NotFoundError,
    Task,
    ValidationError,
)
from clauxton.core.task_manager_compat import TaskManagerCompat


# ============================================================================
# KnowledgeBaseCompat CRUD Tests (10 tests)
# ============================================================================


def test_kb_compat_initialization_emits_deprecation_warning(tmp_path: Path) -> None:
    """Test that KnowledgeBaseCompat emits deprecation warning on init."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        KnowledgeBaseCompat(tmp_path)

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
        assert "v0.17.0" in str(w[0].message)


def test_kb_compat_add_entry(tmp_path: Path) -> None:
    """Test adding KB entry through compatibility layer."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="API Design Pattern",
        category="architecture",
        content="Use RESTful API design",
        tags=["api", "rest"],
        created_at=now,
        updated_at=now,
    )

    entry_id = kb.add(entry)
    assert entry_id == "KB-20260127-001"

    # Verify entry stored in Memory system
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["knowledge"])
    assert len(memories) == 1
    assert memories[0].legacy_id == "KB-20260127-001"
    assert memories[0].type == "knowledge"
    assert memories[0].title == "API Design Pattern"


def test_kb_compat_add_duplicate_entry_raises_error(tmp_path: Path) -> None:
    """Test that adding duplicate KB entry raises DuplicateError."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="First Entry",
        category="architecture",
        content="Content",
        created_at=now,
        updated_at=now,
    )

    kb.add(entry)

    # Try to add duplicate
    entry2 = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Duplicate Entry",
        category="decision",
        content="Different content",
        created_at=now,
        updated_at=now,
    )

    with pytest.raises(DuplicateError) as exc_info:
        kb.add(entry2)

    assert "KB-20260127-001" in str(exc_info.value)
    assert "already exists" in str(exc_info.value)


def test_kb_compat_get_entry(tmp_path: Path) -> None:
    """Test getting KB entry by ID."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="API Design",
        category="architecture",
        content="Use RESTful APIs",
        tags=["api"],
        created_at=now,
        updated_at=now,
    )

    kb.add(entry)

    retrieved = kb.get("KB-20260127-001")
    assert retrieved.id == "KB-20260127-001"
    assert retrieved.title == "API Design"
    assert retrieved.category == "architecture"
    assert retrieved.content == "Use RESTful APIs"
    assert "api" in retrieved.tags


def test_kb_compat_get_nonexistent_entry_raises_error(tmp_path: Path) -> None:
    """Test that getting nonexistent entry raises NotFoundError."""
    kb = KnowledgeBaseCompat(tmp_path)

    with pytest.raises(NotFoundError) as exc_info:
        kb.get("KB-20260127-999")

    assert "KB-20260127-999" in str(exc_info.value)
    assert "not found" in str(exc_info.value)


def test_kb_compat_search_entries(tmp_path: Path) -> None:
    """Test searching KB entries."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    # Add multiple entries
    entries = [
        KnowledgeBaseEntry(
            id="KB-20260127-001",
            title="API Design",
            category="architecture",
            content="Use RESTful API design",
            tags=["api", "rest"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20260127-002",
            title="Database Schema",
            category="architecture",
            content="Use PostgreSQL database",
            tags=["database", "postgres"],
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20260127-003",
            title="API Versioning",
            category="decision",
            content="Version APIs using URL path",
            tags=["api", "versioning"],
            created_at=now,
            updated_at=now,
        ),
    ]

    for entry in entries:
        kb.add(entry)

    # Search for "api"
    results = kb.search("api")
    assert len(results) >= 2  # At least 2 entries contain "api"

    titles = [e.title for e in results]
    assert "API Design" in titles
    assert "API Versioning" in titles


def test_kb_compat_search_with_category_filter(tmp_path: Path) -> None:
    """Test searching KB entries with category filter."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entries = [
        KnowledgeBaseEntry(
            id="KB-20260127-001",
            title="API Design",
            category="architecture",
            content="Use RESTful API",
            created_at=now,
            updated_at=now,
        ),
        KnowledgeBaseEntry(
            id="KB-20260127-002",
            title="API Decision",
            category="decision",
            content="Decided to use GraphQL",
            created_at=now,
            updated_at=now,
        ),
    ]

    for entry in entries:
        kb.add(entry)

    # Search with category filter
    results = kb.search("api", category="architecture")
    assert len(results) == 1
    assert results[0].title == "API Design"
    assert results[0].category == "architecture"


def test_kb_compat_list_all_entries(tmp_path: Path) -> None:
    """Test listing all KB entries."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    # Add 3 entries
    for i in range(1, 4):
        entry = KnowledgeBaseEntry(
            id=f"KB-20260127-{i:03d}",
            title=f"Entry {i}",
            category="architecture",
            content=f"Content {i}",
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

    all_entries = kb.list_all()
    assert len(all_entries) == 3

    ids = [e.id for e in all_entries]
    assert "KB-20260127-001" in ids
    assert "KB-20260127-002" in ids
    assert "KB-20260127-003" in ids


def test_kb_compat_update_entry(tmp_path: Path) -> None:
    """Test updating KB entry."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Original Title",
        category="architecture",
        content="Original content",
        tags=["old"],
        created_at=now,
        updated_at=now,
    )

    kb.add(entry)

    # Update entry
    updated = kb.update(
        "KB-20260127-001",
        content="Updated content",
        tags=["new", "updated"]
    )

    assert updated.id == "KB-20260127-001"
    assert updated.title == "Original Title"  # Not changed
    assert updated.content == "Updated content"  # Changed
    assert "new" in updated.tags
    assert "updated" in updated.tags


def test_kb_compat_delete_entry(tmp_path: Path) -> None:
    """Test deleting KB entry."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="To Delete",
        category="architecture",
        content="Will be deleted",
        created_at=now,
        updated_at=now,
    )

    kb.add(entry)

    # Verify entry exists
    assert kb.get("KB-20260127-001") is not None

    # Delete entry
    success = kb.delete("KB-20260127-001")
    assert success is True

    # Verify entry is gone
    with pytest.raises(NotFoundError):
        kb.get("KB-20260127-001")


# ============================================================================
# KnowledgeBaseCompat Conversion Tests (5 tests)
# ============================================================================


def test_kb_to_memory_conversion(tmp_path: Path) -> None:
    """Test KB entry to Memory entry conversion."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Test Entry",
        category="architecture",
        content="Test content",
        tags=["test", "conversion"],
        created_at=now,
        updated_at=now,
    )

    kb.add(entry)

    # Check Memory system directly
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["knowledge"])

    assert len(memories) == 1
    mem = memories[0]

    assert mem.type == "knowledge"
    assert mem.legacy_id == "KB-20260127-001"
    assert mem.title == "Test Entry"
    assert mem.content == "Test content"
    assert mem.category == "architecture"
    assert "test" in mem.tags
    assert "conversion" in mem.tags


def test_memory_to_kb_conversion(tmp_path: Path) -> None:
    """Test Memory entry to KB entry conversion."""
    memory = Memory(tmp_path)
    now = datetime.now()

    # Create memory entry directly
    from clauxton.core.memory import MemoryEntry
    mem_entry = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Memory Test",
        content="Memory content",
        category="architecture",
        tags=["memory", "test"],
        created_at=now,
        updated_at=now,
        source="manual",
        confidence=1.0,
        legacy_id="KB-20260127-001",
    )

    memory.add(mem_entry)

    # Access via KB compatibility layer
    kb = KnowledgeBaseCompat(tmp_path)
    entry = kb.get("KB-20260127-001")

    assert entry.id == "KB-20260127-001"
    assert entry.title == "Memory Test"
    assert entry.content == "Memory content"
    assert entry.category == "architecture"
    assert "memory" in entry.tags
    assert "test" in entry.tags


def test_legacy_id_preservation(tmp_path: Path) -> None:
    """Test that legacy KB IDs are preserved."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Legacy Test",
        category="architecture",
        content="Content",
        created_at=now,
        updated_at=now,
    )

    kb.add(entry)

    # Verify legacy_id in Memory system
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["knowledge"])

    assert len(memories) == 1
    assert memories[0].legacy_id == "KB-20260127-001"

    # Verify retrieval by legacy_id
    retrieved = kb.get("KB-20260127-001")
    assert retrieved.id == "KB-20260127-001"


def test_type_filtering_in_memory_system(tmp_path: Path) -> None:
    """Test that KB entries are properly filtered by type in Memory."""
    # Add KB entry via compatibility layer
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    kb_entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="KB Entry",
        category="architecture",
        content="KB content",
        created_at=now,
        updated_at=now,
    )
    kb.add(kb_entry)

    # Add non-knowledge memory directly (using same memory instance from KB)
    from clauxton.core.memory import MemoryEntry
    other_entry = MemoryEntry(
        id="MEM-20260127-001",
        type="decision",
        title="Decision Entry",
        content="Decision content",
        category="technical",
        created_at=now,
        updated_at=now,
        source="manual",
    )
    kb.memory.add(other_entry)

    # KB compat layer should only see knowledge entries
    kb_entries = kb.list_all()
    assert len(kb_entries) == 1
    assert kb_entries[0].id == "KB-20260127-001"

    # Memory system should see both
    all_memories = kb.memory.list_all()
    assert len(all_memories) == 2


def test_kb_category_validation(tmp_path: Path) -> None:
    """Test that KB categories are properly validated."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    valid_categories = ["architecture", "constraint", "decision", "pattern", "convention"]

    for category in valid_categories:
        entry = KnowledgeBaseEntry(
            id=f"KB-20260127-{valid_categories.index(category) + 1:03d}",
            title=f"{category.title()} Entry",
            category=category,  # type: ignore
            content=f"Content for {category}",
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

    # All should be added successfully
    entries = kb.list_all()
    assert len(entries) == len(valid_categories)


# ============================================================================
# TaskManagerCompat CRUD Tests (10 tests)
# ============================================================================


def test_task_compat_initialization_emits_deprecation_warning(tmp_path: Path) -> None:
    """Test that TaskManagerCompat emits deprecation warning on init."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")
        TaskManagerCompat(tmp_path)

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        assert "deprecated" in str(w[0].message).lower()
        assert "v0.17.0" in str(w[0].message)


def test_task_compat_add_task(tmp_path: Path) -> None:
    """Test adding task through compatibility layer."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    task = Task(
        id="TASK-001",
        name="Setup database",
        description="Create PostgreSQL schema",
        status="pending",
        priority="high",
        created_at=now,
    )

    task_id = tm.add(task)
    assert task_id == "TASK-001"

    # Verify task stored in Memory system
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["task"])
    assert len(memories) == 1
    assert memories[0].legacy_id == "TASK-001"
    assert memories[0].type == "task"
    assert memories[0].title == "Setup database"


def test_task_compat_add_duplicate_task_raises_error(tmp_path: Path) -> None:
    """Test that adding duplicate task raises DuplicateError."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    task = Task(
        id="TASK-001",
        name="First Task",
        status="pending",
        created_at=now,
    )

    tm.add(task)

    # Try to add duplicate
    task2 = Task(
        id="TASK-001",
        name="Duplicate Task",
        status="pending",
        created_at=now,
    )

    with pytest.raises(DuplicateError) as exc_info:
        tm.add(task2)

    assert "TASK-001" in str(exc_info.value)
    assert "already exists" in str(exc_info.value)


def test_task_compat_get_task(tmp_path: Path) -> None:
    """Test getting task by ID."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    task = Task(
        id="TASK-001",
        name="Setup database",
        description="Create schema",
        status="pending",
        priority="high",
        created_at=now,
    )

    tm.add(task)

    retrieved = tm.get("TASK-001")
    assert retrieved.id == "TASK-001"
    assert retrieved.name == "Setup database"
    assert retrieved.description == "Create schema"
    assert retrieved.status == "pending"
    assert retrieved.priority == "high"


def test_task_compat_get_nonexistent_task_raises_error(tmp_path: Path) -> None:
    """Test that getting nonexistent task raises NotFoundError."""
    tm = TaskManagerCompat(tmp_path)

    with pytest.raises(NotFoundError) as exc_info:
        tm.get("TASK-999")

    assert "TASK-999" in str(exc_info.value)
    assert "not found" in str(exc_info.value)


def test_task_compat_list_all_tasks(tmp_path: Path) -> None:
    """Test listing all tasks."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    # Add 3 tasks
    for i in range(1, 4):
        task = Task(
            id=f"TASK-{i:03d}",
            name=f"Task {i}",
            status="pending",
            created_at=now,
        )
        tm.add(task)

    all_tasks = tm.list_all()
    assert len(all_tasks) == 3

    ids = [t.id for t in all_tasks]
    assert "TASK-001" in ids
    assert "TASK-002" in ids
    assert "TASK-003" in ids


def test_task_compat_list_with_status_filter(tmp_path: Path) -> None:
    """Test listing tasks with status filter."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    tasks = [
        Task(id="TASK-001", name="Task 1", status="pending", created_at=now),
        Task(id="TASK-002", name="Task 2", status="in_progress", created_at=now),
        Task(id="TASK-003", name="Task 3", status="pending", created_at=now),
    ]

    for task in tasks:
        tm.add(task)

    # Filter by status
    pending_tasks = tm.list_all(status_filter="pending")
    assert len(pending_tasks) == 2

    ids = [t.id for t in pending_tasks]
    assert "TASK-001" in ids
    assert "TASK-003" in ids


def test_task_compat_list_with_priority_filter(tmp_path: Path) -> None:
    """Test listing tasks with priority filter."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    tasks = [
        Task(id="TASK-001", name="Task 1", priority="high", created_at=now),
        Task(id="TASK-002", name="Task 2", priority="medium", created_at=now),
        Task(id="TASK-003", name="Task 3", priority="high", created_at=now),
    ]

    for task in tasks:
        tm.add(task)

    # Filter by priority
    high_tasks = tm.list_all(priority_filter="high")
    assert len(high_tasks) == 2

    ids = [t.id for t in high_tasks]
    assert "TASK-001" in ids
    assert "TASK-003" in ids


def test_task_compat_update_task(tmp_path: Path) -> None:
    """Test updating task."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    task = Task(
        id="TASK-001",
        name="Original Task",
        status="pending",
        priority="medium",
        created_at=now,
    )

    tm.add(task)

    # Update task
    updated = tm.update(
        "TASK-001",
        {"status": "in_progress", "priority": "high"}
    )

    assert updated.id == "TASK-001"
    assert updated.name == "Original Task"  # Not changed
    assert updated.status == "in_progress"  # Changed
    assert updated.priority == "high"  # Changed


def test_task_compat_delete_task(tmp_path: Path) -> None:
    """Test deleting task."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    task = Task(
        id="TASK-001",
        name="To Delete",
        status="pending",
        created_at=now,
    )

    tm.add(task)

    # Verify task exists
    assert tm.get("TASK-001") is not None

    # Delete task
    success = tm.delete("TASK-001")
    assert success is True

    # Verify task is gone
    with pytest.raises(NotFoundError):
        tm.get("TASK-001")


# ============================================================================
# TaskManagerCompat Conversion Tests (5 tests)
# ============================================================================


def test_task_to_memory_conversion(tmp_path: Path) -> None:
    """Test Task to Memory entry conversion."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    task = Task(
        id="TASK-001",
        name="Test Task",
        description="Test description",
        status="pending",
        priority="high",
        depends_on=["TASK-002"],
        created_at=now,
    )

    tm.add(task)

    # Check Memory system directly
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["task"])

    assert len(memories) == 1
    mem = memories[0]

    assert mem.type == "task"
    assert mem.legacy_id == "TASK-001"
    assert mem.title == "Test Task"
    assert mem.content == "Test description"
    assert mem.category == "high"  # Priority as category
    assert "TASK-002" in mem.related_to  # Dependencies


def test_memory_to_task_conversion(tmp_path: Path) -> None:
    """Test Memory entry to Task conversion."""
    memory = Memory(tmp_path)
    now = datetime.now()

    # Create memory entry directly
    from clauxton.core.memory import MemoryEntry
    mem_entry = MemoryEntry(
        id="MEM-20260127-001",
        type="task",
        title="Memory Task",
        content="Memory description",
        category="high",
        tags=["pending", "high"],
        created_at=now,
        updated_at=now,
        source="manual",
        confidence=1.0,
        legacy_id="TASK-001",
        related_to=["TASK-002"],
    )

    memory.add(mem_entry)

    # Access via Task compatibility layer
    tm = TaskManagerCompat(tmp_path)
    task = tm.get("TASK-001")

    assert task.id == "TASK-001"
    assert task.name == "Memory Task"
    assert task.description == "Memory description"
    assert task.status == "pending"
    assert task.priority == "high"
    assert "TASK-002" in task.depends_on


def test_task_dependencies_mapped_to_related_to(tmp_path: Path) -> None:
    """Test that task dependencies are mapped to related_to."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    task = Task(
        id="TASK-001",
        name="Dependent Task",
        status="pending",
        depends_on=["TASK-002", "TASK-003"],
        created_at=now,
    )

    tm.add(task)

    # Check Memory system
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["task"])

    assert len(memories) == 1
    mem = memories[0]

    assert "TASK-002" in mem.related_to
    assert "TASK-003" in mem.related_to


def test_task_priority_mapped_to_category(tmp_path: Path) -> None:
    """Test that task priority is mapped to category."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    priorities = ["low", "medium", "high", "critical"]

    for i, priority in enumerate(priorities, 1):
        task = Task(
            id=f"TASK-{i:03d}",
            name=f"Task {i}",
            status="pending",
            priority=priority,  # type: ignore
            created_at=now,
        )
        tm.add(task)

    # Check Memory system
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["task"])

    assert len(memories) == 4
    categories = [m.category for m in memories]

    for priority in priorities:
        assert priority in categories


def test_task_status_preserved_in_tags(tmp_path: Path) -> None:
    """Test that task status is preserved in tags."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    statuses = ["pending", "in_progress", "completed", "blocked"]

    for i, status in enumerate(statuses, 1):
        task = Task(
            id=f"TASK-{i:03d}",
            name=f"Task {i}",
            status=status,  # type: ignore
            created_at=now,
        )
        tm.add(task)

    # Check Memory system
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["task"])

    assert len(memories) == 4

    for mem, status in zip(memories, statuses):
        assert status in mem.tags


# ============================================================================
# Integration Tests (10 tests)
# ============================================================================


def test_kb_and_task_coexistence(tmp_path: Path) -> None:
    """Test that KB and Task entries can coexist in Memory system."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    # Add KB entry
    kb_entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="KB Entry",
        category="architecture",
        content="KB content",
        created_at=now,
        updated_at=now,
    )
    kb.add(kb_entry)

    # Add Task directly via KB's memory instance
    from clauxton.core.memory import MemoryEntry
    task_mem = MemoryEntry(
        id="MEM-20251103-002",
        type="task",
        title="Task Entry",
        content="Task Entry",
        category="medium",
        tags=["pending", "medium"],
        created_at=now,
        updated_at=now,
        source="manual",
        legacy_id="TASK-001",
    )
    kb.memory.add(task_mem)

    # Check Memory system
    all_memories = kb.memory.list_all()
    assert len(all_memories) == 2

    types = [m.type for m in all_memories]
    assert "knowledge" in types
    assert "task" in types


def test_mixed_memory_types_dont_interfere(tmp_path: Path) -> None:
    """Test that different memory types don't interfere with each other."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    # Add KB entry
    kb_entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="KB Entry",
        category="architecture",
        content="Content",
        created_at=now,
        updated_at=now,
    )
    kb.add(kb_entry)

    # Add Task directly via KB's memory
    from clauxton.core.memory import MemoryEntry
    task_mem = MemoryEntry(
        id="MEM-20251103-002",
        type="task",
        title="Task Entry",
        content="Task Entry",
        category="medium",
        tags=["pending", "medium"],
        created_at=now,
        updated_at=now,
        source="manual",
        legacy_id="TASK-001",
    )
    kb.memory.add(task_mem)

    # Add decision memory directly
    decision = MemoryEntry(
        id="MEM-20260127-001",
        type="decision",
        title="Decision",
        content="Decision content",
        category="technical",
        created_at=now,
        updated_at=now,
        source="manual",
    )
    kb.memory.add(decision)

    # KB layer should only see knowledge entries
    kb_entries = kb.list_all()
    assert len(kb_entries) == 1
    assert kb_entries[0].id == "KB-20260127-001"

    # Create TM using same path - it will see the task via its own Memory instance
    tm = TaskManagerCompat(tmp_path)
    tasks = tm.list_all()
    assert len(tasks) == 1
    assert tasks[0].id == "TASK-001"

    # KB's memory should see all 3
    all_memories = kb.memory.list_all()
    assert len(all_memories) == 3


def test_backward_compatibility_with_existing_code(tmp_path: Path) -> None:
    """Test that existing code patterns still work."""
    # Simulate existing code usage
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    # Old pattern: create entry, add, search, update
    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Old Pattern",
        category="architecture",
        content="Old style code",
        created_at=now,
        updated_at=now,
    )

    entry_id = kb.add(entry)
    results = kb.search("old")
    assert len(results) >= 1

    kb.update(entry_id, content="Updated old style")
    updated = kb.get(entry_id)
    assert updated.content == "Updated old style"


def test_deprecation_warnings_appear_correctly(tmp_path: Path) -> None:
    """Test that deprecation warnings appear for both KB and Task APIs."""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Should emit warning
        KnowledgeBaseCompat(tmp_path)
        assert len(w) == 1
        assert "v0.17.0" in str(w[0].message)

        # Should emit another warning
        TaskManagerCompat(tmp_path)
        assert len(w) == 2
        assert "v0.17.0" in str(w[1].message)


def test_kb_and_task_search_independence(tmp_path: Path) -> None:
    """Test that KB and Task search are independent."""
    kb = KnowledgeBaseCompat(tmp_path)
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    # Add KB entry with "api" keyword
    kb_entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="API Design",
        category="architecture",
        content="API content",
        created_at=now,
        updated_at=now,
    )
    kb.add(kb_entry)

    # Add Task with "api" keyword
    task = Task(
        id="TASK-001",
        name="API Task",
        description="API task description",
        status="pending",
        created_at=now,
    )
    tm.add(task)

    # KB search should only return KB entries
    kb_results = kb.search("api")
    assert len(kb_results) == 1
    assert kb_results[0].id == "KB-20260127-001"

    # Task list should only return tasks
    all_tasks = tm.list_all()
    assert len(all_tasks) == 1
    assert all_tasks[0].id == "TASK-001"


def test_legacy_id_uniqueness_across_types(tmp_path: Path) -> None:
    """Test that legacy IDs are unique within their type."""
    kb = KnowledgeBaseCompat(tmp_path)
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    # KB-001 and TASK-001 should not conflict
    kb_entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="KB Entry",
        category="architecture",
        content="Content",
        created_at=now,
        updated_at=now,
    )
    kb.add(kb_entry)

    task = Task(
        id="TASK-001",
        name="Task Entry",
        status="pending",
        created_at=now,
    )
    tm.add(task)

    # Both should be retrievable
    assert kb.get("KB-20260127-001") is not None
    assert tm.get("TASK-001") is not None


def test_memory_search_finds_both_kb_and_tasks(tmp_path: Path) -> None:
    """Test that Memory search can find both KB and Task entries."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    # Add KB entry
    kb_entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Database Design",
        category="architecture",
        content="Database architecture",
        created_at=now,
        updated_at=now,
    )
    kb.add(kb_entry)

    # Add Task directly via KB's memory
    from clauxton.core.memory import MemoryEntry
    task_mem = MemoryEntry(
        id="MEM-20251103-002",
        type="task",
        title="Database Setup",
        content="Setup database schema",
        category="medium",
        tags=["pending", "medium"],
        created_at=now,
        updated_at=now,
        source="manual",
        legacy_id="TASK-001",
    )
    kb.memory.add(task_mem)

    # Memory search should find both
    results = kb.memory.search("database")
    assert len(results) >= 2

    types = [r.type for r in results]
    assert "knowledge" in types
    assert "task" in types


def test_update_preserves_legacy_id(tmp_path: Path) -> None:
    """Test that updates preserve legacy IDs."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Original",
        category="architecture",
        content="Original content",
        created_at=now,
        updated_at=now,
    )

    kb.add(entry)

    # Update multiple times
    kb.update("KB-20260127-001", title="Updated 1")
    kb.update("KB-20260127-001", title="Updated 2")
    kb.update("KB-20260127-001", title="Updated 3")

    # Legacy ID should still be preserved
    final = kb.get("KB-20260127-001")
    assert final.id == "KB-20260127-001"
    assert final.title == "Updated 3"


def test_delete_only_affects_target_type(tmp_path: Path) -> None:
    """Test that deleting KB entry doesn't affect Tasks and vice versa."""
    kb = KnowledgeBaseCompat(tmp_path)
    now = datetime.now()

    # Add one of each
    kb_entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="KB Entry",
        category="architecture",
        content="Content",
        created_at=now,
        updated_at=now,
    )
    kb.add(kb_entry)

    # Add Task directly via KB's memory
    from clauxton.core.memory import MemoryEntry
    task_mem = MemoryEntry(
        id="MEM-20251103-002",
        type="task",
        title="Task Entry",
        content="Task Entry",
        category="medium",
        tags=["pending", "medium"],
        created_at=now,
        updated_at=now,
        source="manual",
        legacy_id="TASK-001",
    )
    kb.memory.add(task_mem)

    # Delete KB entry
    kb.delete("KB-20260127-001")

    # Task should still exist - check via new TM instance
    tm = TaskManagerCompat(tmp_path)
    assert tm.get("TASK-001") is not None

    # Only 1 memory should remain
    all_memories = kb.memory.list_all()
    assert len(all_memories) == 1
    assert all_memories[0].type == "task"


def test_conversion_handles_empty_fields(tmp_path: Path) -> None:
    """Test that conversion handles empty/optional fields correctly."""
    tm = TaskManagerCompat(tmp_path)
    now = datetime.now()

    # Task with minimal fields
    task = Task(
        id="TASK-001",
        name="Minimal Task",
        status="pending",
        created_at=now,
    )

    tm.add(task)

    # Should convert successfully
    retrieved = tm.get("TASK-001")
    assert retrieved.id == "TASK-001"
    assert retrieved.name == "Minimal Task"
    assert retrieved.description is None or retrieved.description == "Minimal Task"
    assert retrieved.depends_on == []
    assert retrieved.files_to_edit == []
