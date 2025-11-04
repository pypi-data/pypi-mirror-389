# Clauxton Test Writing Guide

**Version**: 1.0
**Date**: October 22, 2025
**Target Audience**: Contributors, developers adding features
**Status**: Production Ready (v0.10.0, 758 tests, 91% coverage)

---

## Table of Contents

1. [Testing Philosophy](#1-testing-philosophy)
2. [Test Structure](#2-test-structure)
3. [Coverage Requirements](#3-coverage-requirements)
4. [Writing Unit Tests](#4-writing-unit-tests)
5. [Writing Integration Tests](#5-writing-integration-tests)
6. [Testing CLI Commands](#6-testing-cli-commands)
7. [Testing MCP Tools](#7-testing-mcp-tools)
8. [Testing Edge Cases](#8-testing-edge-cases)
9. [Coverage Analysis](#9-coverage-analysis)
10. [Common Patterns](#10-common-patterns)

---

## 1. Testing Philosophy

### 1.1 Why We Test

Tests serve three critical purposes in Clauxton:

1. **Correctness**: Ensure code works as expected
2. **Documentation**: Tests demonstrate how to use APIs
3. **Refactoring Safety**: Confidently modify code without breaking functionality

### 1.2 Tests as Documentation

Every test should be **self-explanatory**:

```python
# ✅ Good: Clear test name and structure
def test_knowledge_base_rejects_duplicate_ids():
    """Test that adding entry with duplicate ID raises DuplicateError."""
    kb = KnowledgeBase(tmp_path)

    # Add first entry
    entry1 = KnowledgeBaseEntry(id="KB-20251022-001", ...)
    kb.add(entry1)

    # Attempt to add second entry with same ID
    entry2 = KnowledgeBaseEntry(id="KB-20251022-001", ...)

    # Should raise DuplicateError
    with pytest.raises(DuplicateError) as exc_info:
        kb.add(entry2)

    assert "KB-20251022-001" in str(exc_info.value)
```

```python
# ❌ Bad: Unclear test name and purpose
def test_kb_add():
    kb = KnowledgeBase(tmp_path)
    entry = KnowledgeBaseEntry(id="KB-20251022-001", ...)
    kb.add(entry)
    assert True  # What are we testing?
```

### 1.3 Testing Mindset

**Think like an adversary**: How can this code break?

- Empty inputs
- Extremely long inputs
- Unicode characters (日本語, emoji 🔥)
- Circular dependencies
- File system errors
- Concurrent modifications

---

## 2. Test Structure

### 2.1 Arrange-Act-Assert (AAA)

All tests follow the **Arrange-Act-Assert** pattern:

```python
def test_task_manager_calculates_next_task():
    """Test that next_task returns task with satisfied dependencies."""

    # ARRANGE: Set up test data
    tm = TaskManager(tmp_path)
    task1 = Task(id="TASK-001", name="Setup", status="completed")
    task2 = Task(id="TASK-002", name="API", depends_on=["TASK-001"], status="pending")
    task3 = Task(id="TASK-003", name="Tests", depends_on=["TASK-002"], status="pending")

    tm.add(task1)
    tm.add(task2)
    tm.add(task3)

    # ACT: Execute the operation
    next_task = tm.next_task()

    # ASSERT: Verify the result
    assert next_task is not None
    assert next_task.id == "TASK-002"  # Only TASK-002 is executable
```

### 2.2 Given-When-Then (Alternative)

For complex scenarios, use **Given-When-Then**:

```python
def test_conflict_detector_warns_high_risk():
    """
    Given two tasks editing the same file
    When I detect conflicts
    Then risk level should be HIGH
    """
    # Given
    cd = ConflictDetector(tmp_path)
    task1 = Task(id="TASK-001", files_to_edit=["src/main.py"])
    task2 = Task(id="TASK-002", files_to_edit=["src/main.py"])

    # When
    result = cd.detect_conflicts("TASK-001")

    # Then
    assert result["risk"] == "HIGH"
    assert "src/main.py" in result["files"]
```

### 2.3 Test Naming Convention

**Pattern**: `test_<component>_<action>_<expected_outcome>`

**Examples**:
- `test_knowledge_base_search_returns_relevant_entries`
- `test_task_manager_rejects_circular_dependencies`
- `test_mcp_server_handles_invalid_tool_name`

---

## 3. Coverage Requirements

### 3.1 Coverage Targets

| Module Type | Target Coverage | Rationale |
|-------------|-----------------|-----------|
| **Core modules** | 95%+ | Critical business logic |
| **CLI commands** | 90%+ | User-facing interface |
| **MCP server** | 95%+ | AI integration layer |
| **Utilities** | 80%+ | Support functions |
| **Overall** | 90%+ | Production readiness |

### 3.2 Current Status (v0.10.0)

```
Module                          Stmts   Miss  Cover
---------------------------------------------------
clauxton/core/knowledge_base.py   217     12   94%
clauxton/core/task_manager.py     351     18   95%
clauxton/mcp/server.py            206      2   99%
---------------------------------------------------
TOTAL                            2316    208   91%
```

### 3.3 Acceptable Gaps

**Not every line needs testing**:

- **Defensive error handling**: Rare edge cases (e.g., OS errors)
- **Logging statements**: Already tested indirectly
- **Type validation**: Pydantic handles this

**Focus on**:
- **Business logic**: Core algorithms (search, DAG validation, conflict detection)
- **Data integrity**: CRUD operations, atomic writes
- **Error paths**: Invalid inputs, constraint violations

---

## 4. Writing Unit Tests

### 4.1 Basic Unit Test

```python
from pathlib import Path
import pytest
from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry
from datetime import datetime


@pytest.fixture
def kb(tmp_path: Path) -> KnowledgeBase:
    """Create a KnowledgeBase instance for testing."""
    return KnowledgeBase(tmp_path)


def test_knowledge_base_add(kb):
    """Test adding entry to Knowledge Base."""
    entry = KnowledgeBaseEntry(
        id="KB-20251022-001",
        title="Test entry",
        category="architecture",
        content="Test content",
        tags=["test"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    entry_id = kb.add(entry)

    assert entry_id == "KB-20251022-001"
    assert kb.get(entry_id) is not None
    assert kb.get(entry_id).title == "Test entry"
```

### 4.2 Testing with Fixtures

**Use fixtures for reusable test data**:

```python
@pytest.fixture
def sample_tasks() -> list[Task]:
    """Create sample tasks with dependencies."""
    return [
        Task(
            id="TASK-001",
            name="Setup",
            status="completed",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Task(
            id="TASK-002",
            name="API",
            depends_on=["TASK-001"],
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
        Task(
            id="TASK-003",
            name="Tests",
            depends_on=["TASK-002"],
            status="pending",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        ),
    ]


def test_task_manager_list_by_status(sample_tasks):
    """Test filtering tasks by status."""
    tm = TaskManager(tmp_path)

    for task in sample_tasks:
        tm.add(task)

    pending_tasks = tm.list_tasks(status="pending")

    assert len(pending_tasks) == 2
    assert all(t.status == "pending" for t in pending_tasks)
```

### 4.3 Parametrized Tests

**Test multiple scenarios with `@pytest.mark.parametrize`**:

```python
@pytest.mark.parametrize("query, expected_count", [
    ("architecture", 3),  # Should find 3 architecture entries
    ("api", 2),           # Should find 2 entries with "api" keyword
    ("nonexistent", 0),   # Should find nothing
])
def test_knowledge_base_search_various_queries(kb, query, expected_count):
    """Test search with various queries."""
    # Add test entries
    add_sample_entries(kb)

    # Search
    results = kb.search(query)

    # Verify
    assert len(results) == expected_count
```

---

## 5. Writing Integration Tests

### 5.1 End-to-End Workflow Test

```python
def test_complete_task_workflow(tmp_path):
    """Test complete task workflow: add → start → complete."""
    tm = TaskManager(tmp_path)

    # 1. Add task
    task = Task(
        id="TASK-001",
        name="Implement feature",
        status="pending",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    tm.add(task)

    # 2. Start task
    tm.update("TASK-001", status="in_progress")
    task_in_progress = tm.get("TASK-001")
    assert task_in_progress.status == "in_progress"

    # 3. Complete task
    tm.update("TASK-001", status="completed")
    task_completed = tm.get("TASK-001")
    assert task_completed.status == "completed"

    # 4. Verify not in next_task queue
    next_task = tm.next_task()
    assert next_task is None  # No pending tasks
```

### 5.2 Cross-Module Integration

```python
def test_operation_history_with_knowledge_base(tmp_path):
    """Test that KB operations are recorded in operation history."""
    kb = KnowledgeBase(tmp_path)
    history = OperationHistory(tmp_path)

    # Add entry
    entry = KnowledgeBaseEntry(
        id="KB-20251022-001",
        title="Test",
        category="architecture",
        content="Content",
        tags=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry)

    # Check operation history
    operations = history.get_recent_operations(limit=10)
    assert len(operations) >= 1
    assert operations[0]["operation_type"] == "kb_add"
    assert operations[0]["target_id"] == "KB-20251022-001"
```

---

## 6. Testing CLI Commands

### 6.1 Click CLI Test

```python
from click.testing import CliRunner
from clauxton.cli.main import cli


def test_cli_kb_add():
    """Test 'clauxton kb add' command."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Run command
        result = runner.invoke(cli, [
            "kb", "add",
            "--title", "Test Entry",
            "--category", "architecture",
            "--content", "Test content",
            "--tags", "test,demo"
        ])

        # Verify success
        assert result.exit_code == 0
        assert "KB-" in result.output

        # Verify entry was added
        result_list = runner.invoke(cli, ["kb", "list"])
        assert "Test Entry" in result_list.output
```

### 6.2 Testing Error Handling

```python
def test_cli_kb_add_missing_required_field():
    """Test that missing required field shows error."""
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, [
            "kb", "add",
            "--title", "Test"
            # Missing --category and --content
        ])

        assert result.exit_code != 0
        assert "Missing option" in result.output or "required" in result.output.lower()
```

---

## 7. Testing MCP Tools

### 7.1 MCP Tool Test

```python
import pytest
from clauxton.mcp.server import server


@pytest.mark.asyncio
async def test_mcp_kb_search():
    """Test MCP kb_search tool."""
    # Add entry first
    await server.call_tool(
        name="kb_add",
        arguments={
            "title": "Test Entry",
            "category": "architecture",
            "content": "Test content",
            "tags": ["test"]
        }
    )

    # Search
    response = await server.call_tool(
        name="kb_search",
        arguments={"query": "test", "limit": 10}
    )

    # Verify
    assert response[0].type == "text"
    assert "Found" in response[0].text
    assert "Test Entry" in response[0].text
```

### 7.2 Testing Tool Error Handling

```python
@pytest.mark.asyncio
async def test_mcp_kb_get_nonexistent_entry():
    """Test that getting nonexistent entry returns error."""
    response = await server.call_tool(
        name="kb_get",
        arguments={"entry_id": "KB-20251022-999"}
    )

    assert response[0].type == "text"
    assert "not found" in response[0].text.lower()
```

---

## 8. Testing Edge Cases

### 8.1 Empty Inputs

```python
def test_knowledge_base_search_empty_query(kb):
    """Test that empty query raises ValidationError."""
    with pytest.raises(ValueError) as exc_info:
        kb.search(query="")

    assert "empty" in str(exc_info.value).lower()
```

### 8.2 Unicode Characters

```python
def test_knowledge_base_handles_unicode(kb):
    """Test that KB handles Japanese characters correctly."""
    entry = KnowledgeBaseEntry(
        id="KB-20251022-001",
        title="日本語のタイトル",
        category="architecture",
        content="日本語のコンテンツ 🔥",
        tags=["日本語", "unicode"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    entry_id = kb.add(entry)
    retrieved = kb.get(entry_id)

    assert retrieved.title == "日本語のタイトル"
    assert "🔥" in retrieved.content
```

### 8.3 Extremely Long Inputs

```python
def test_knowledge_base_rejects_long_title(kb):
    """Test that title exceeding max length is rejected."""
    entry = KnowledgeBaseEntry(
        id="KB-20251022-001",
        title="A" * 300,  # Exceeds 200 char limit
        category="architecture",
        content="Content",
        tags=[],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )

    with pytest.raises(ValidationError):
        kb.add(entry)
```

### 8.4 Circular Dependencies

```python
def test_task_manager_detects_circular_dependency(tmp_path):
    """Test that circular dependencies are detected and rejected."""
    tm = TaskManager(tmp_path)

    task1 = Task(id="TASK-001", name="Task 1", depends_on=["TASK-002"])
    task2 = Task(id="TASK-002", name="Task 2", depends_on=["TASK-001"])

    tm.add(task1)

    with pytest.raises(CycleDetectedError) as exc_info:
        tm.add(task2)

    assert "cycle" in str(exc_info.value).lower()
```

---

## 9. Coverage Analysis

### 9.1 Running Tests with Coverage

```bash
# Run all tests with coverage
pytest --cov=clauxton --cov-report=html --cov-report=term

# Output:
# Name                           Stmts   Miss  Cover
# --------------------------------------------------
# clauxton/core/knowledge_base.py  217     12   94%
# clauxton/core/task_manager.py    351     18   95%
# ...
# --------------------------------------------------
# TOTAL                           2316    208   91%
#
# Coverage HTML written to dir htmlcov
```

### 9.2 Viewing HTML Report

```bash
# Open HTML report in browser
open htmlcov/index.html  # macOS
xdg-open htmlcov/index.html  # Linux
start htmlcov/index.html  # Windows
```

**HTML report shows**:
- Line-by-line coverage (green = covered, red = uncovered)
- Branch coverage (if enabled)
- Missing lines

### 9.3 Targeting Uncovered Lines

```bash
# Show uncovered lines in terminal
pytest --cov=clauxton --cov-report=term-missing

# Output:
# Name                           Stmts   Miss  Cover   Missing
# ----------------------------------------------------------------
# clauxton/core/knowledge_base.py  217     12   94%   45-47, 102, 156-159
```

**Write tests for missing lines**:
```python
# Lines 45-47 are error handling for file corruption
def test_knowledge_base_handles_corrupted_yaml(tmp_path):
    """Test that corrupted YAML file is handled gracefully."""
    kb_file = tmp_path / ".clauxton" / "knowledge-base.yml"
    kb_file.write_text("invalid: yaml: [content")

    kb = KnowledgeBase(tmp_path)
    # Should initialize empty KB instead of crashing
    assert kb.list_entries() == []
```

---

## 10. Common Patterns

### 10.1 Testing File Operations

```python
def test_atomic_write_preserves_data_on_crash(tmp_path):
    """Test that atomic write prevents data loss on crash."""
    kb = KnowledgeBase(tmp_path)

    # Add initial entry
    entry1 = KnowledgeBaseEntry(id="KB-20251022-001", ...)
    kb.add(entry1)

    # Simulate crash during write
    with patch("clauxton.utils.yaml_utils.write_yaml", side_effect=IOError("Disk full")):
        entry2 = KnowledgeBaseEntry(id="KB-20251022-002", ...)

        with pytest.raises(IOError):
            kb.add(entry2)

    # Original entry should still exist
    kb_reloaded = KnowledgeBase(tmp_path)
    assert kb_reloaded.get("KB-20251022-001") is not None
    assert kb_reloaded.get("KB-20251022-002") is None  # Not added
```

### 10.2 Testing with Mocks

```python
from unittest.mock import patch


def test_task_manager_logs_operations(tmp_path):
    """Test that task operations are logged."""
    tm = TaskManager(tmp_path)

    with patch("clauxton.utils.logger.info") as mock_log:
        task = Task(id="TASK-001", name="Test")
        tm.add(task)

        mock_log.assert_called_once()
        assert "TASK-001" in str(mock_log.call_args)
```

### 10.3 Testing Async Code

```python
@pytest.mark.asyncio
async def test_mcp_server_handles_concurrent_requests():
    """Test that MCP server handles concurrent requests."""
    import asyncio

    # Send 10 concurrent requests
    tasks = [
        server.call_tool(name="kb_list", arguments={})
        for _ in range(10)
    ]

    responses = await asyncio.gather(*tasks)

    # All requests should succeed
    assert len(responses) == 10
    assert all(r[0].type == "text" for r in responses)
```

---

## Appendix

### A. Pytest Configuration

**pyproject.toml**:
```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--tb=short",
    "--cov=clauxton",
    "--cov-report=term-missing",
]
markers = [
    "slow: marks tests as slow (deselect with '-m \"not slow\"')",
    "integration: marks tests as integration tests",
]
```

### B. Common pytest Commands

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/core/test_knowledge_base.py

# Run specific test function
pytest tests/core/test_knowledge_base.py::test_add_entry

# Run tests by keyword
pytest -k "search"

# Run tests with verbose output
pytest -v

# Run tests and stop on first failure
pytest -x

# Run only failed tests from last run
pytest --lf

# Run tests in parallel (requires pytest-xdist)
pytest -n auto
```

### C. Coverage Best Practices

1. **Aim for high coverage, not 100%**: 90%+ is excellent
2. **Focus on critical paths**: Business logic > boilerplate
3. **Test behavior, not implementation**: Don't test private methods directly
4. **Use coverage to find gaps**: Not as a target itself
5. **Refactor for testability**: Pure functions are easier to test

### D. Test Anti-Patterns to Avoid

**❌ Testing implementation details**:
```python
def test_internal_cache_structure():  # BAD
    kb = KnowledgeBase(tmp_path)
    assert kb._entries_cache == []  # Testing internal state
```

**✅ Testing behavior**:
```python
def test_knowledge_base_search_returns_cached_results():  # GOOD
    kb = KnowledgeBase(tmp_path)
    kb.add(entry)

    # First search builds cache
    results1 = kb.search("test")

    # Second search should be fast (cached)
    import time
    start = time.time()
    results2 = kb.search("test")
    elapsed = time.time() - start

    assert elapsed < 0.01  # Should be fast due to caching
    assert results1 == results2
```

**❌ Overly complex tests**:
```python
def test_everything():  # BAD
    # Tests 10 different scenarios in one test
    ...
```

**✅ Focused tests**:
```python
def test_knowledge_base_add():  # GOOD
    # Tests one thing: adding an entry
    ...

def test_knowledge_base_search():  # GOOD
    # Tests one thing: searching entries
    ...
```

---

**Happy Testing!** 🧪

For more information, see:
- [pytest documentation](https://docs.pytest.org/)
- [Clauxton technical design](technical-design.md)
- [Clauxton quick start](quick-start.md)
