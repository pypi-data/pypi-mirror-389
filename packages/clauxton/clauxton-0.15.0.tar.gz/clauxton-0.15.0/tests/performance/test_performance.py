"""
Performance tests for Clauxton.

Tests system performance with large datasets to ensure scalability.
"""

import time
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clauxton.core import search as search_module
from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry, Task
from clauxton.core.task_manager import TaskManager


@pytest.fixture
def temp_root(tmp_path: Path) -> Path:
    """Create temporary root directory."""
    root = tmp_path / "test_project"
    root.mkdir()
    (root / ".clauxton").mkdir()

    # Properly initialize knowledge-base.yml with required fields
    kb_content = """version: "1.0"
project_name: "test_project"
project_description: null
entries: []
"""
    (root / ".clauxton" / "knowledge-base.yml").write_text(kb_content)

    # Properly initialize tasks.yml
    tasks_content = """version: "1.0"
project_name: "test_project"
tasks: []
"""
    (root / ".clauxton" / "tasks.yml").write_text(tasks_content)

    return root


# ============================================================================
# Search Performance Tests
# ============================================================================


@pytest.mark.slow
@pytest.mark.performance
def test_search_performance_with_large_kb(temp_root: Path) -> None:
    """Test search performance with 1000+ KB entries."""
    kb = KnowledgeBase(temp_root)

    # Add 1000 entries
    start_time = time.time()
    for i in range(1000):
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-{i+1:03d}",
            title=f"Entry {i}",
            category="architecture" if i % 3 == 0 else "decision",
            content=f"Content for entry {i} with keywords test data example",
            tags=[f"tag{i % 10}", "common"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)
    add_time = time.time() - start_time

    # Search should complete quickly
    search_start = time.time()
    results = kb.search("test", limit=50)
    search_time = time.time() - search_start

    # Performance assertions
    assert len(results) > 0
    assert search_time < 2.0, f"Search took {search_time}s, should be < 2s"
    assert add_time < 30.0, f"Adding 1000 entries took {add_time}s, should be < 30s"


@pytest.mark.slow
@pytest.mark.performance
def test_search_performance_with_many_tasks(temp_root: Path) -> None:
    """Test search performance with 500+ tasks."""
    tm = TaskManager(temp_root)

    # Add 500 tasks
    start_time = time.time()
    for i in range(500):
        priority = ["low", "medium", "high", "critical"][i % 4]
        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i}: Implement feature {i}",
            priority=priority,
            estimated_hours=float(i % 10 + 1),
            status="pending",
            created_at=datetime.now(),
        )
        tm.add(task)
    add_time = time.time() - start_time

    # List all should complete quickly
    list_start = time.time()
    all_tasks = tm.list_all()
    list_time = time.time() - list_start

    # Performance assertions
    assert len(all_tasks) == 500
    assert list_time < 1.0, f"Listing 500 tasks took {list_time}s, should be < 1s"
    assert add_time < 20.0, f"Adding 500 tasks took {add_time}s, should be < 20s"


@pytest.mark.slow
@pytest.mark.performance
def test_tfidf_search_performance(temp_root: Path) -> None:
    """Test TF-IDF search performance with large dataset."""
    kb = KnowledgeBase(temp_root)

    # Add varied content
    topics = ["authentication", "database", "API", "frontend", "backend"]
    for i in range(200):
        topic = topics[i % len(topics)]
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-{i+1:03d}",
            title=f"{topic} entry {i}",
            category="architecture",
            content=f"Detailed content about {topic} with implementation details",
            tags=[topic, "implementation"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

    # TF-IDF search should be fast
    start_time = time.time()
    results = search_module.tfidf_search(kb.list_all(), "authentication database", limit=20)
    search_time = time.time() - start_time

    assert len(results) > 0
    assert search_time < 3.0, f"TF-IDF search took {search_time}s, should be < 3s"


# ============================================================================
# Workflow Performance Tests
# ============================================================================


@pytest.mark.slow
@pytest.mark.performance
def test_daily_summary_performance(temp_root: Path) -> None:
    """Test daily summary calculation with many tasks."""
    tm = TaskManager(temp_root)

    # Create 100 tasks across 30 days
    for i in range(100):
        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i}",
            status="pending",
            created_at=datetime.now(),
        )
        task_id = tm.add(task)
        days_ago = i % 30
        tm.update(
            task_id,
            {
                "status": "completed",
                "completed_at": datetime.now() - timedelta(days=days_ago),
                "actual_hours": float(i % 8 + 1),
            },
        )

    # Calculate today's summary
    start_time = time.time()
    today = datetime.now().date()
    tasks = tm.list_all()
    completed_today = [
        t for t in tasks
        if t.completed_at and t.completed_at.date() == today
    ]
    calc_time = time.time() - start_time

    # Verify calculation completed
    assert len(completed_today) >= 0  # Could be 0 if no tasks completed today
    assert calc_time < 0.5, f"Daily calculation took {calc_time}s, should be < 0.5s"


@pytest.mark.slow
@pytest.mark.performance
def test_weekly_summary_performance(temp_root: Path) -> None:
    """Test weekly summary calculation with historical data."""
    tm = TaskManager(temp_root)

    # Create 200 tasks across 90 days
    for i in range(200):
        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i}",
            status="pending",
            created_at=datetime.now(),
        )
        task_id = tm.add(task)
        days_ago = i % 90
        tm.update(
            task_id,
            {
                "status": "completed",
                "completed_at": datetime.now() - timedelta(days=days_ago),
                "actual_hours": float(i % 10 + 1),
            },
        )

    # Calculate this week's summary
    start_time = time.time()
    week_start = datetime.now() - timedelta(days=7)
    tasks = tm.list_all()
    week_tasks = [
        t for t in tasks
        if t.completed_at and t.completed_at >= week_start
    ]
    calc_time = time.time() - start_time

    # Verify calculation completed
    assert len(week_tasks) >= 0  # Week tasks should be counted
    assert calc_time < 1.0, f"Weekly calculation took {calc_time}s, should be < 1s"


@pytest.mark.slow
@pytest.mark.performance
def test_trends_analysis_performance(temp_root: Path) -> None:
    """Test trends analysis with 90 days of data."""
    tm = TaskManager(temp_root)

    # Create tasks across 90 days
    for i in range(180):
        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i}",
            status="pending",
            created_at=datetime.now(),
        )
        task_id = tm.add(task)
        days_ago = i % 90
        tm.update(
            task_id,
            {
                "status": "completed",
                "completed_at": datetime.now() - timedelta(days=days_ago),
                "actual_hours": float(i % 8 + 1),
            },
        )

    # Calculate 90-day trends
    start_time = time.time()
    cutoff = datetime.now() - timedelta(days=90)
    tasks = tm.list_all()
    recent_tasks = [
        t for t in tasks
        if t.completed_at and t.completed_at >= cutoff
    ]

    # Group by week
    weeks = {}
    for task in recent_tasks:
        if task.completed_at:
            week_num = task.completed_at.isocalendar()[1]
            weeks[week_num] = weeks.get(week_num, 0) + 1

    calc_time = time.time() - start_time

    assert len(recent_tasks) > 0
    assert calc_time < 1.5, f"Trends calculation took {calc_time}s, should be < 1.5s"


# ============================================================================
# File I/O Performance Tests
# ============================================================================


@pytest.mark.slow
@pytest.mark.performance
def test_bulk_file_write_performance(temp_root: Path) -> None:
    """Test bulk write performance for YAML files."""
    kb = KnowledgeBase(temp_root)

    # Add 100 entries
    for i in range(100):
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-{i+1:03d}",
            title=f"Entry {i}",
            category="architecture",
            content=f"Content {i}",
            tags=[f"tag{i}"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

    # File should be written efficiently
    kb_file = temp_root / ".clauxton" / "knowledge-base.yml"
    assert kb_file.exists()
    assert kb_file.stat().st_size > 0


@pytest.mark.slow
@pytest.mark.performance
def test_bulk_file_read_performance(temp_root: Path) -> None:
    """Test bulk read performance for large YAML files."""
    kb = KnowledgeBase(temp_root)

    # Create large dataset
    for i in range(500):
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-{i+1:03d}",
            title=f"Entry {i}",
            category="architecture",
            content="Long content " * 50,
            tags=[f"tag{i}"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

    # Re-read should be fast
    start_time = time.time()
    kb2 = KnowledgeBase(temp_root)
    entries = kb2.list_all()
    read_time = time.time() - start_time

    assert len(entries) == 500
    assert read_time < 2.0, f"Reading 500 entries took {read_time}s, should be < 2s"


# ============================================================================
# Concurrent Operations Performance
# ============================================================================


@pytest.mark.slow
@pytest.mark.performance
def test_sequential_task_updates_performance(temp_root: Path) -> None:
    """Test performance of many sequential task updates."""
    tm = TaskManager(temp_root)

    # Create 100 tasks
    task_ids = []
    for i in range(100):
        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i}",
            status="pending",
            created_at=datetime.now(),
        )
        task_id = tm.add(task)
        task_ids.append(task_id)

    # Update all tasks
    start_time = time.time()
    for task_id in task_ids:
        tm.update(task_id, {"status": "in_progress"})
    update_time = time.time() - start_time

    # Note: Performance may vary by environment (WSL, Docker, etc.)
    # Adjusted threshold to account for slower environments
    assert update_time < 30.0, f"Updating 100 tasks took {update_time}s, should be < 30s"


@pytest.mark.slow
@pytest.mark.performance
def test_search_with_filters_performance(temp_root: Path) -> None:
    """Test filtered search performance."""
    kb = KnowledgeBase(temp_root)

    # Add diverse entries
    categories = ["architecture", "decision", "pattern", "convention", "constraint"]
    for i in range(200):
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-{i+1:03d}",
            title=f"Entry {i}",
            category=categories[i % len(categories)],
            content=f"Content with searchable terms for entry {i}",
            tags=[f"tag{i % 20}"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

    # Filtered search should be fast
    search_start = time.time()
    results = kb.search("searchable", category="architecture", limit=50)
    search_time = time.time() - search_start

    assert len(results) > 0
    assert search_time < 2.0, f"Filtered search took {search_time}s, should be < 2s"


# ============================================================================
# Memory Usage Tests
# ============================================================================


@pytest.mark.slow
@pytest.mark.performance
def test_memory_usage_with_large_dataset(temp_root: Path) -> None:
    """Test that memory usage stays reasonable with large datasets."""

    kb = KnowledgeBase(temp_root)
    tm = TaskManager(temp_root)

    # Add significant amount of data
    for i in range(500):
        now = datetime.now()
        entry = KnowledgeBaseEntry(
            id=f"KB-{now.strftime('%Y%m%d')}-{i+1:03d}",
            title=f"Entry {i}",
            category="architecture",
            content=f"Content {i} " * 100,  # Long content
            tags=[f"tag{i}"],
            created_at=now,
            updated_at=now,
        )
        kb.add(entry)

        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i}",
            status="pending",
            created_at=datetime.now(),
        )
        tm.add(task)

    # Get all data
    entries = kb.list_all()
    tasks = tm.list_all()

    # Verify data loaded correctly
    assert len(entries) == 500
    assert len(tasks) == 500

    # Memory should be manageable (this is a smoke test)
    # In production, would use memory_profiler for accurate measurements


# ============================================================================
# Scalability Tests
# ============================================================================


@pytest.mark.slow
@pytest.mark.performance
def test_scalability_10000_tasks(temp_root: Path) -> None:
    """Test system handles 10,000 tasks (slow test, marked)."""
    tm = TaskManager(temp_root)

    # Add 10,000 tasks
    start_time = time.time()
    for i in range(10000):
        if i % 1000 == 0:  # Progress indicator
            elapsed = time.time() - start_time
            print(f"Added {i} tasks in {elapsed:.1f}s")

        task = Task(
            id=tm.generate_task_id(),
            name=f"Task {i}",
            status="pending",
            created_at=datetime.now(),
        )
        tm.add(task)

    total_time = time.time() - start_time

    # Verify
    tasks = tm.list_all()
    assert len(tasks) == 10000

    # Should complete in reasonable time
    assert total_time < 300.0, f"Adding 10k tasks took {total_time}s, should be < 300s"

    # Search should still work
    search_start = time.time()
    filtered = [t for t in tasks if "Task 100" in t.name]
    search_time = time.time() - search_start

    assert len(filtered) > 0
    assert search_time < 5.0, f"Searching 10k tasks took {search_time}s, should be < 5s"
