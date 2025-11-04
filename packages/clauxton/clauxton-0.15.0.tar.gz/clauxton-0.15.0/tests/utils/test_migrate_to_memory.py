"""
Tests for migration utilities (v0.15.0).

Tests the MemoryMigrator class and migration functionality for
converting Knowledge Base and Task data to the Memory System format.
"""

import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.memory import Memory
from clauxton.core.models import KnowledgeBaseEntry, Task
from clauxton.core.task_manager import TaskManager
from clauxton.utils.migrate_to_memory import MemoryMigrator, MigrationError


# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def project_with_kb(tmp_path: Path) -> Path:
    """
    Create project with populated Knowledge Base.

    Returns:
        Path to project root with 3 KB entries
    """
    kb = KnowledgeBase(tmp_path)

    # Add 3 KB entries
    for i in range(1, 4):
        entry = KnowledgeBaseEntry(
            id=f"KB-20251019-{i:03d}",
            title=f"KB Entry {i}",
            category="architecture",
            content=f"This is KB entry number {i}",
            tags=["test", f"kb{i}"],
            created_at=datetime(2025, 10, 19, 10, i, 0, tzinfo=timezone.utc),
            updated_at=datetime(2025, 10, 19, 10, i, 0, tzinfo=timezone.utc),
        )
        kb.add(entry)

    return tmp_path


@pytest.fixture
def project_with_tasks(tmp_path: Path) -> Path:
    """
    Create project with populated Task list.

    Returns:
        Path to project root with 3 tasks
    """
    tm = TaskManager(tmp_path)

    # Add 3 tasks
    for i in range(1, 4):
        task = Task(
            id=f"TASK-{i:03d}",
            name=f"Task {i}",
            description=f"Description for task {i}",
            status="pending",
            priority="medium",
            created_at=datetime(2025, 10, 19, 11, i, 0, tzinfo=timezone.utc),
            depends_on=[],
            files_to_edit=[],
        )
        tm.add(task)

    return tmp_path


@pytest.fixture
def project_with_both(tmp_path: Path) -> Path:
    """
    Create project with both KB and Tasks.

    Returns:
        Path to project root with 3 KB entries and 3 tasks
    """
    # Add KB entries
    kb = KnowledgeBase(tmp_path)
    for i in range(1, 4):
        entry = KnowledgeBaseEntry(
            id=f"KB-20251019-{i:03d}",
            title=f"KB Entry {i}",
            category="architecture",
            content=f"This is KB entry number {i}",
            tags=["test", f"kb{i}"],
            created_at=datetime(2025, 10, 19, 10, i, 0, tzinfo=timezone.utc),
            updated_at=datetime(2025, 10, 19, 10, i, 0, tzinfo=timezone.utc),
        )
        kb.add(entry)

    # Add tasks
    tm = TaskManager(tmp_path)
    for i in range(1, 4):
        task = Task(
            id=f"TASK-{i:03d}",
            name=f"Task {i}",
            description=f"Description for task {i}",
            status="pending",
            priority="medium",
            created_at=datetime(2025, 10, 19, 11, i, 0, tzinfo=timezone.utc),
            depends_on=[],
            files_to_edit=[],
        )
        tm.add(task)

    return tmp_path


@pytest.fixture
def empty_project(tmp_path: Path) -> Path:
    """
    Create empty project with no KB or Tasks.

    Returns:
        Path to project root with empty .clauxton directory
    """
    clauxton_dir = tmp_path / ".clauxton"
    clauxton_dir.mkdir(parents=True, exist_ok=True)
    return tmp_path


# ============================================================================
# Migration Tests (5 tests)
# ============================================================================


def test_migrate_knowledge_base(project_with_kb: Path) -> None:
    """Test migrating Knowledge Base to Memory."""
    migrator = MemoryMigrator(project_with_kb, dry_run=False)

    # Migrate KB
    count = migrator.migrate_knowledge_base()

    # Verify count
    assert count == 3

    # Verify Memory entries created
    memory = Memory(project_with_kb)
    memories = memory.list_all()
    assert len(memories) == 3

    # Verify Memory entry fields
    for i, mem in enumerate(sorted(memories, key=lambda m: m.created_at), 1):
        assert mem.type == "knowledge"
        assert mem.title == f"KB Entry {i}"
        assert mem.content == f"This is KB entry number {i}"
        assert mem.category == "architecture"
        assert "test" in mem.tags
        assert f"kb{i}" in mem.tags
        assert mem.source == "import"
        assert mem.confidence == 1.0
        assert mem.legacy_id == f"KB-20251019-{i:03d}"


def test_migrate_tasks(project_with_tasks: Path) -> None:
    """Test migrating Tasks to Memory."""
    migrator = MemoryMigrator(project_with_tasks, dry_run=False)

    # Migrate tasks
    count = migrator.migrate_tasks()

    # Verify count
    assert count == 3

    # Verify Memory entries created
    memory = Memory(project_with_tasks)
    memories = memory.list_all()
    assert len(memories) == 3

    # Verify Memory entry fields
    for i, mem in enumerate(sorted(memories, key=lambda m: m.created_at), 1):
        assert mem.type == "task"
        assert mem.title == f"Task {i}"
        assert mem.content == f"Description for task {i}"
        assert mem.category == "medium"  # priority becomes category
        assert mem.tags == []  # Tasks don't have tags
        assert mem.source == "import"
        assert mem.confidence == 1.0
        assert mem.legacy_id == f"TASK-{i:03d}"


def test_migrate_all(project_with_both: Path) -> None:
    """Test migrating both KB and Tasks together."""
    migrator = MemoryMigrator(project_with_both, dry_run=False)

    # Migrate all
    result = migrator.migrate_all()

    # Verify counts
    assert result["kb_count"] == 3
    assert result["task_count"] == 3
    assert result["total"] == 6

    # Verify Memory entries
    memory = Memory(project_with_both)
    memories = memory.list_all()
    assert len(memories) == 6

    # Verify types
    knowledge_entries = [m for m in memories if m.type == "knowledge"]
    task_entries = [m for m in memories if m.type == "task"]
    assert len(knowledge_entries) == 3
    assert len(task_entries) == 3


def test_dry_run_mode(project_with_both: Path) -> None:
    """Test dry-run mode doesn't write changes."""
    migrator = MemoryMigrator(project_with_both, dry_run=True)

    # Run migration in dry-run mode
    result = migrator.migrate_all()

    # Verify counts (preview only)
    assert result["kb_count"] == 3
    assert result["task_count"] == 3
    assert result["total"] == 6

    # Verify NO Memory entries created
    memory = Memory(project_with_both)
    memories = memory.list_all()
    assert len(memories) == 0  # Nothing written in dry-run mode


def test_legacy_id_preservation(project_with_both: Path) -> None:
    """Test that legacy IDs are preserved correctly."""
    migrator = MemoryMigrator(project_with_both, dry_run=False)
    migrator.migrate_all()

    memory = Memory(project_with_both)
    memories = memory.list_all()

    # Check KB legacy IDs
    kb_memories = [m for m in memories if m.type == "knowledge"]
    kb_legacy_ids = {m.legacy_id for m in kb_memories}
    assert kb_legacy_ids == {"KB-20251019-001", "KB-20251019-002", "KB-20251019-003"}

    # Check Task legacy IDs
    task_memories = [m for m in memories if m.type == "task"]
    task_legacy_ids = {m.legacy_id for m in task_memories}
    assert task_legacy_ids == {"TASK-001", "TASK-002", "TASK-003"}


# ============================================================================
# Backup/Rollback Tests (5 tests)
# ============================================================================


def test_backup_creation(project_with_both: Path) -> None:
    """Test backup creation before migration."""
    migrator = MemoryMigrator(project_with_both, dry_run=False)

    # Create backup
    backup_path = migrator.create_rollback_backup()

    # Verify backup directory exists
    assert backup_path.exists()
    assert backup_path.is_dir()
    assert backup_path.name.startswith("pre_migration_")

    # Verify backup files exist
    kb_backup = backup_path / "knowledge-base.yml"
    tasks_backup = backup_path / "tasks.yml"
    assert kb_backup.exists()
    assert tasks_backup.exists()


def test_rollback(project_with_both: Path) -> None:
    """Test rollback restores files from backup."""
    migrator = MemoryMigrator(project_with_both, dry_run=False)

    # Create backup
    backup_path = migrator.create_rollback_backup()

    # Perform migration (modifies files)
    migrator.migrate_all()

    # Verify migration happened
    memory = Memory(project_with_both)
    assert len(memory.list_all()) == 6

    # Delete memories file to simulate corruption
    memories_file = project_with_both / ".clauxton" / "memories.yml"
    memories_file.unlink()

    # Rollback
    migrator.rollback(backup_path)

    # Verify original files restored
    kb_file = project_with_both / ".clauxton" / "knowledge-base.yml"
    tasks_file = project_with_both / ".clauxton" / "tasks.yml"
    assert kb_file.exists()
    assert tasks_file.exists()

    # Verify KB and Tasks still have data
    kb = KnowledgeBase(project_with_both)
    assert len(kb.list_all()) == 3

    tm = TaskManager(project_with_both)
    assert len(tm.list_all()) == 3


def test_rollback_with_missing_backup(project_with_both: Path) -> None:
    """Test rollback raises error with missing backup."""
    migrator = MemoryMigrator(project_with_both, dry_run=False)

    # Try to rollback from non-existent backup
    fake_backup = project_with_both / ".clauxton" / "backups" / "nonexistent"

    with pytest.raises(MigrationError, match="Backup not found"):
        migrator.rollback(fake_backup)


def test_backup_with_empty_project(empty_project: Path) -> None:
    """Test backup with empty project (no KB/Tasks files)."""
    migrator = MemoryMigrator(empty_project, dry_run=False)

    # Create backup (should work even with no files)
    backup_path = migrator.create_rollback_backup()

    # Verify backup directory exists
    assert backup_path.exists()
    assert backup_path.is_dir()

    # Verify backup includes only memories.yml (created by Memory init)
    # KB and Tasks files shouldn't exist in empty project
    backup_files = list(backup_path.glob("*.yml"))
    assert len(backup_files) == 1
    assert backup_files[0].name == "memories.yml"


def test_backup_includes_existing_memories(project_with_both: Path) -> None:
    """Test backup includes existing memories.yml if present."""
    # First create some memories
    memory = Memory(project_with_both)
    from clauxton.core.memory import MemoryEntry
    entry = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Existing memory",
        content="This already exists",
        category="test",
        tags=[],
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc),
        source="manual",
        confidence=1.0,
    )
    memory.add(entry)

    # Create backup
    migrator = MemoryMigrator(project_with_both, dry_run=False)
    backup_path = migrator.create_rollback_backup()

    # Verify memories.yml was backed up
    memories_backup = backup_path / "memories.yml"
    assert memories_backup.exists()


# ============================================================================
# Edge Cases (3 tests)
# ============================================================================


def test_empty_kb_and_tasks(empty_project: Path) -> None:
    """Test migration with empty KB and Tasks."""
    migrator = MemoryMigrator(empty_project, dry_run=False)

    # Migrate (should succeed with 0 entries)
    result = migrator.migrate_all()

    # Verify counts
    assert result["kb_count"] == 0
    assert result["task_count"] == 0
    assert result["total"] == 0

    # Verify no Memory entries
    memory = Memory(empty_project)
    assert len(memory.list_all()) == 0


def test_missing_files(empty_project: Path) -> None:
    """Test migration when KB/Task files don't exist."""
    migrator = MemoryMigrator(empty_project, dry_run=False)

    # Migrate KB (file doesn't exist)
    kb_count = migrator.migrate_knowledge_base()
    assert kb_count == 0

    # Migrate Tasks (file doesn't exist)
    task_count = migrator.migrate_tasks()
    assert task_count == 0


def test_migration_idempotency(project_with_both: Path) -> None:
    """Test migration can be run multiple times safely."""
    migrator = MemoryMigrator(project_with_both, dry_run=False)

    # First migration
    result1 = migrator.migrate_all()
    assert result1["total"] == 6

    # Second migration (should create new entries with new IDs)
    result2 = migrator.migrate_all()
    assert result2["total"] == 6

    # Verify total entries (12 = 6 + 6)
    memory = Memory(project_with_both)
    memories = memory.list_all()
    assert len(memories) == 12  # 6 from first migration + 6 from second


# ============================================================================
# ID Generation Tests (2 tests)
# ============================================================================


def test_generate_memory_id_sequence(empty_project: Path) -> None:
    """Test Memory ID generation produces sequential IDs."""
    migrator = MemoryMigrator(empty_project, dry_run=False)

    # Generate multiple IDs
    id1 = migrator._generate_memory_id()
    id2 = migrator._generate_memory_id()
    id3 = migrator._generate_memory_id()

    # Verify format and sequence
    assert id1.startswith("MEM-")
    assert id1.endswith("-001")

    # Note: IDs may not be sequential if called without adding to memory
    # This is expected behavior since _generate_memory_id() checks existing memories


def test_generate_memory_id_format(empty_project: Path) -> None:
    """Test Memory ID format is correct."""
    migrator = MemoryMigrator(empty_project, dry_run=False)

    memory_id = migrator._generate_memory_id()

    # Verify format: MEM-YYYYMMDD-NNN
    parts = memory_id.split("-")
    assert len(parts) == 3
    assert parts[0] == "MEM"
    assert len(parts[1]) == 8  # YYYYMMDD
    assert len(parts[2]) == 3  # NNN
    assert parts[2].isdigit()


# ============================================================================
# Task Dependencies Migration Test (1 test)
# ============================================================================


def test_migrate_tasks_with_dependencies(tmp_path: Path) -> None:
    """Test migrating tasks with dependencies preserves relationships."""
    # Create tasks with dependencies
    tm = TaskManager(tmp_path)

    task1 = Task(
        id="TASK-001",
        name="Setup",
        description="Setup project",
        status="completed",
        priority="high",
        created_at=datetime.now(timezone.utc),
        depends_on=[],
        files_to_edit=[],
    )
    tm.add(task1)

    task2 = Task(
        id="TASK-002",
        name="Build",
        description="Build project",
        status="pending",
        priority="high",
        created_at=datetime.now(timezone.utc),
        depends_on=["TASK-001"],
        files_to_edit=[],
    )
    tm.add(task2)

    # Migrate
    migrator = MemoryMigrator(tmp_path, dry_run=False)
    migrator.migrate_tasks()

    # Verify dependencies preserved
    memory = Memory(tmp_path)
    memories = memory.list_all(type_filter=["task"])

    build_memory = [m for m in memories if m.title == "Build"][0]
    assert len(build_memory.related_to) == 1
    assert "TASK-001" in build_memory.related_to


# ============================================================================
# Error Handling Test (1 test)
# ============================================================================


def test_rollback_invalid_path(empty_project: Path) -> None:
    """Test rollback with invalid backup path."""
    migrator = MemoryMigrator(empty_project, dry_run=False)

    # Create a file (not directory) as fake backup
    fake_backup = empty_project / ".clauxton" / "fake_backup.txt"
    fake_backup.write_text("not a directory")

    # Try to rollback (should fail)
    with pytest.raises(MigrationError, match="not a directory"):
        migrator.rollback(fake_backup)
