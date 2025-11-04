"""
Integration tests for API error handling scenarios.

Tests that verify proper error messages when using the API incorrectly,
based on the improvements made to API documentation and error handling.
"""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry, Task
from clauxton.core.task_manager import TaskManager


@pytest.fixture
def initialized_project(tmp_path: Path) -> Path:
    """Create initialized project directory."""
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()
    (project_dir / ".clauxton").mkdir()

    # Initialize with proper YAML structure
    kb_content = """version: "1.0"
project_name: "test_project"
project_description: null
entries: []
"""
    (project_dir / ".clauxton" / "knowledge-base.yml").write_text(kb_content)

    tasks_content = """version: "1.0"
project_name: "test_project"
tasks: []
"""
    (project_dir / ".clauxton" / "tasks.yml").write_text(tasks_content)

    return project_dir


# ============================================================================
# API Error Handling Tests
# ============================================================================


def test_kb_add_with_incorrect_keyword_arguments(initialized_project: Path) -> None:
    """
    Test that KB.add() with keyword arguments raises clear TypeError.

    This test verifies the documentation example of incorrect usage.
    """
    kb = KnowledgeBase(initialized_project)

    # ❌ WRONG: Passing keyword arguments directly
    with pytest.raises(TypeError) as exc_info:
        kb.add(  # type: ignore[call-arg]
            title="API Design",
            category="architecture",
            content="REST API design",
            tags=["api"],
        )

    # Verify error message is informative (mentions unexpected keyword argument)
    error_msg = str(exc_info.value)
    assert "unexpected keyword argument" in error_msg or "title" in error_msg


def test_task_manager_add_with_incorrect_keyword_arguments(
    initialized_project: Path,
) -> None:
    """
    Test that TaskManager.add() with keyword arguments raises clear TypeError.

    This test verifies the documentation example of incorrect usage.
    """
    tm = TaskManager(initialized_project)

    # ❌ WRONG: Passing keyword arguments directly
    with pytest.raises(TypeError) as exc_info:
        tm.add(  # type: ignore[call-arg]
            name="Implement feature",
            priority="high",
            status="pending",
        )

    # Verify error message is informative
    error_msg = str(exc_info.value)
    assert "Task" in error_msg or "missing" in error_msg


def test_correct_kb_add_usage_works(initialized_project: Path) -> None:
    """
    Test that correct KB.add() usage works as documented.

    This test verifies the documentation example of correct usage.
    """
    kb = KnowledgeBase(initialized_project)
    now = datetime.now()

    # ✅ CORRECT: Create KnowledgeBaseEntry object first
    entry = KnowledgeBaseEntry(
        id=f"KB-{now.strftime('%Y%m%d')}-001",
        title="API Design Pattern",
        category="architecture",
        content="Use RESTful API design",
        tags=["api", "rest"],
        created_at=now,
        updated_at=now,
    )

    # This should work
    entry_id = kb.add(entry)
    assert entry_id == entry.id

    # Verify entry was added
    entries = kb.list_all()
    assert len(entries) == 1
    assert entries[0].title == "API Design Pattern"


def test_correct_task_add_usage_works(initialized_project: Path) -> None:
    """
    Test that correct TaskManager.add() usage works as documented.

    This test verifies the documentation example of correct usage.
    """
    tm = TaskManager(initialized_project)

    # ✅ CORRECT: Create Task object first
    task = Task(
        id=tm.generate_task_id(),
        name="Implement authentication",
        priority="high",
        status="pending",
        estimated_hours=5.0,
        created_at=datetime.now(),
    )

    # This should work
    task_id = tm.add(task)
    assert task_id == task.id

    # Verify task was added
    tasks = tm.list_all()
    assert len(tasks) == 1
    assert tasks[0].name == "Implement authentication"


def test_kb_add_with_missing_required_fields(initialized_project: Path) -> None:
    """
    Test that KB.add() validates required fields.

    Verifies that Pydantic validation catches missing required fields.
    """
    now = datetime.now()

    # Missing required fields should raise ValidationError
    with pytest.raises(Exception):  # Pydantic ValidationError
        _ = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-001",
            # Missing title
            category="architecture",
            content="Content",
            tags=["test"],
            created_at=now,
            updated_at=now,
        )  # type: ignore[call-arg]


def test_task_add_with_invalid_priority(initialized_project: Path) -> None:
    """
    Test that TaskManager.add() validates priority values.

    Verifies that invalid priority values are caught by Pydantic.
    """
    tm = TaskManager(initialized_project)

    # Invalid priority should raise ValidationError
    with pytest.raises(Exception):  # Pydantic ValidationError
        _ = Task(
            id=tm.generate_task_id(),
            name="Test task",
            priority="ultra-mega-high",  # Invalid priority  # type: ignore[arg-type]
            status="pending",
            created_at=datetime.now(),
        )


# ============================================================================
# YAML Corruption Recovery Tests
# ============================================================================


def test_kb_handles_corrupted_yaml_gracefully(initialized_project: Path) -> None:
    """
    Test that KB handles corrupted YAML files gracefully.

    Verifies improved error recovery after YAML corruption.
    """
    kb_file = initialized_project / ".clauxton" / "knowledge-base.yml"
    kb_file.write_text("invalid: yaml: content: [[[")

    # Should handle corruption gracefully
    with pytest.raises(Exception) as exc_info:
        _ = KnowledgeBase(initialized_project)

    # Error message should be informative
    error_msg = str(exc_info.value)
    assert "yaml" in error_msg.lower() or "parse" in error_msg.lower()


def test_task_manager_handles_corrupted_yaml_gracefully(
    initialized_project: Path,
) -> None:
    """
    Test that TaskManager handles corrupted YAML files gracefully.

    Verifies improved error recovery after YAML corruption.
    """
    tasks_file = initialized_project / ".clauxton" / "tasks.yml"
    tasks_file.write_text("invalid: yaml: content: [[[")

    # Should handle corruption gracefully
    tm = TaskManager(initialized_project)

    # Error should be raised when trying to access the data
    with pytest.raises(Exception) as exc_info:
        tm.list_all()

    # Error message should be informative
    error_msg = str(exc_info.value)
    assert "yaml" in error_msg.lower() or "parse" in error_msg.lower()


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_kb_add_with_unicode_content(initialized_project: Path) -> None:
    """
    Test that KB.add() handles Unicode content correctly.

    Verifies that the improved API handles international characters.
    """
    kb = KnowledgeBase(initialized_project)
    now = datetime.now()

    entry = KnowledgeBaseEntry(
        id=f"KB-{now.strftime('%Y%m%d')}-001",
        title="日本語テスト",
        category="architecture",
        content="これはUnicode文字のテストです。🎉",
        tags=["unicode", "日本語"],
        created_at=now,
        updated_at=now,
    )

    entry_id = kb.add(entry)
    assert entry_id == entry.id

    # Verify entry was added with Unicode preserved
    entries = kb.list_all()
    assert len(entries) == 1
    assert entries[0].title == "日本語テスト"
    assert "🎉" in entries[0].content


def test_task_add_with_special_characters_in_name(
    initialized_project: Path,
) -> None:
    """
    Test that TaskManager.add() handles special characters in task names.

    Verifies robustness of the improved API.
    """
    tm = TaskManager(initialized_project)

    task = Task(
        id=tm.generate_task_id(),
        name="Task with 'quotes' and \"double quotes\" & symbols!",
        status="pending",
        created_at=datetime.now(),
    )

    task_id = tm.add(task)
    assert task_id == task.id

    # Verify task was added with special characters preserved
    tasks = tm.list_all()
    assert len(tasks) == 1
    assert "quotes" in tasks[0].name
    assert "&" in tasks[0].name


def test_multiple_rapid_additions(initialized_project: Path) -> None:
    """
    Test rapid successive additions of KB entries and tasks.

    Verifies that the improved API handles concurrent-like operations.
    """
    kb = KnowledgeBase(initialized_project)
    tm = TaskManager(initialized_project)

    # Rapidly add 10 KB entries
    for i in range(10):
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-{i+1:03d}",
            title=f"Entry {i+1}",
            category="architecture",
            content=f"Content {i+1}",
            tags=[f"tag{i+1}"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

    # Rapidly add 10 tasks
    for i in range(10):
        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i+1}",
            status="pending",
            created_at=datetime.now(),
        )
        tm.add(task)

    # Verify all were added
    assert len(kb.list_all()) == 10
    assert len(tm.list_all()) == 10
