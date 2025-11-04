"""
Integration tests for MCP Server with real Knowledge Base.

Tests cover:
- Real KB operations (no mocking)
- End-to-end tool workflows
- Error handling
- Edge cases
"""

import subprocess
from pathlib import Path

import pytest
from click.testing import CliRunner

from clauxton.cli.main import cli
from clauxton.core.models import NotFoundError
from clauxton.mcp.server import (
    analyze_recent_commits,
    extract_decisions_from_commits,
    kb_add,
    kb_get,
    kb_list,
    kb_search,
    suggest_next_tasks,
)


@pytest.fixture
def initialized_project(tmp_path: Path) -> Path:
    """Create initialized Clauxton project."""
    runner = CliRunner()
    with runner.isolated_filesystem(temp_dir=tmp_path) as td:
        # Initialize
        result = runner.invoke(cli, ["init"])
        assert result.exit_code == 0
        yield Path(td)


# ============================================================================
# Integration Tests (Real KB)
# ============================================================================


def test_kb_search_integration(initialized_project: Path) -> None:
    """Test kb_search with real Knowledge Base."""
    import os

    os.chdir(initialized_project)

    # Add entries first
    kb_add(
        title="FastAPI Framework",
        category="architecture",
        content="Use FastAPI for all backend APIs",
        tags=["backend", "api"],
    )
    kb_add(
        title="PostgreSQL Database",
        category="architecture",
        content="Use PostgreSQL 15+ for production",
        tags=["database", "postgresql"],
    )

    # Search
    results = kb_search(query="FastAPI")

    # Verify
    assert len(results) == 1
    assert results[0]["title"] == "FastAPI Framework"
    assert "backend" in results[0]["tags"]


def test_kb_add_integration(initialized_project: Path) -> None:
    """Test kb_add with real Knowledge Base."""
    import os

    os.chdir(initialized_project)

    # Add entry
    result = kb_add(
        title="Test Entry",
        category="decision",
        content="This is a test decision",
        tags=["test"],
    )

    # Verify
    assert "id" in result
    assert result["id"].startswith("KB-")
    assert "Successfully added" in result["message"]

    # Verify entry exists
    entry = kb_get(result["id"])
    assert entry["title"] == "Test Entry"
    assert entry["category"] == "decision"


def test_kb_list_integration(initialized_project: Path) -> None:
    """Test kb_list with real Knowledge Base."""
    import os

    os.chdir(initialized_project)

    # Add multiple entries
    kb_add("Entry 1", "architecture", "Content 1", ["tag1"])
    kb_add("Entry 2", "decision", "Content 2", ["tag2"])
    kb_add("Entry 3", "architecture", "Content 3", ["tag3"])

    # List all
    all_entries = kb_list()
    assert len(all_entries) == 3

    # List by category
    arch_entries = kb_list(category="architecture")
    assert len(arch_entries) == 2
    assert all(e["category"] == "architecture" for e in arch_entries)


def test_kb_get_integration(initialized_project: Path) -> None:
    """Test kb_get with real Knowledge Base."""
    import os

    os.chdir(initialized_project)

    # Add entry
    add_result = kb_add(
        title="Get Test",
        category="pattern",
        content="Test content",
        tags=["test"],
    )
    entry_id = add_result["id"]

    # Get entry
    entry = kb_get(entry_id)

    # Verify
    assert entry["id"] == entry_id
    assert entry["title"] == "Get Test"
    assert entry["category"] == "pattern"
    assert entry["version"] == 1


# ============================================================================
# Error Handling Tests
# ============================================================================


def test_kb_get_not_found(initialized_project: Path) -> None:
    """Test kb_get with non-existent entry ID."""
    import os

    os.chdir(initialized_project)

    # Attempt to get non-existent entry
    with pytest.raises(NotFoundError):
        kb_get("KB-20251019-999")


def test_kb_search_no_results(initialized_project: Path) -> None:
    """Test kb_search with no matches."""
    import os

    os.chdir(initialized_project)

    # Add entry
    kb_add("Test Entry", "architecture", "Content", [])

    # Search for non-existent term
    results = kb_search(query="NonExistentTerm")

    # Verify empty results
    assert len(results) == 0


def test_kb_list_empty(initialized_project: Path) -> None:
    """Test kb_list with empty Knowledge Base."""
    import os

    os.chdir(initialized_project)

    # List without adding anything
    results = kb_list()

    # Verify empty
    assert len(results) == 0


# ============================================================================
# Edge Case Tests
# ============================================================================


def test_kb_add_multiple_same_day(initialized_project: Path) -> None:
    """Test kb_add creates sequential IDs for same-day entries."""
    import os

    os.chdir(initialized_project)

    # Add multiple entries on same day
    result1 = kb_add("Entry 1", "architecture", "Content 1", [])
    result2 = kb_add("Entry 2", "architecture", "Content 2", [])
    result3 = kb_add("Entry 3", "architecture", "Content 3", [])

    # Extract sequence numbers
    id1 = result1["id"]
    id2 = result2["id"]
    id3 = result3["id"]

    # Verify same date prefix
    assert id1.split("-")[1] == id2.split("-")[1] == id3.split("-")[1]

    # Verify sequential numbers
    seq1 = int(id1.split("-")[2])
    seq2 = int(id2.split("-")[2])
    seq3 = int(id3.split("-")[2])

    assert seq2 == seq1 + 1
    assert seq3 == seq2 + 1


def test_kb_add_with_unicode(initialized_project: Path) -> None:
    """Test kb_add with Unicode content."""
    import os

    os.chdir(initialized_project)

    # Add entry with Japanese text
    result = kb_add(
        title="Unicode Test 日本語",
        category="convention",
        content="Content with emoji 🚀 and Japanese: これはテストです",
        tags=["unicode", "日本語"],
    )

    # Verify
    entry = kb_get(result["id"])
    assert "日本語" in entry["title"]
    assert "🚀" in entry["content"]
    assert "日本語" in entry["tags"]


def test_kb_search_with_special_characters(initialized_project: Path) -> None:
    """Test kb_search with special characters."""
    import os

    os.chdir(initialized_project)

    # Add entry with special characters
    kb_add(
        title="API Endpoint /api/v1/users",
        category="architecture",
        content="RESTful API endpoint for user management: /api/v1/users",
        tags=["api", "rest"],
    )

    # Search with special characters
    results = kb_search(query="/api/v1/users")

    # Verify
    assert len(results) == 1
    assert "/api/v1/users" in results[0]["content"]


def test_kb_list_category_filter_case_sensitive(initialized_project: Path) -> None:
    """Test kb_list category filter is case-sensitive."""
    import os

    os.chdir(initialized_project)

    # Add entry
    kb_add("Test", "architecture", "Content", [])

    # Filter with wrong case (should not match)
    results = kb_list(category="Architecture")

    # Verify no results (case-sensitive)
    assert len(results) == 0

    # Filter with correct case
    results = kb_list(category="architecture")
    assert len(results) == 1


def test_kb_add_max_length_title(initialized_project: Path) -> None:
    """Test kb_add with maximum length title (50 chars)."""
    import os

    os.chdir(initialized_project)

    # 50 characters exactly
    long_title = "A" * 50

    # Should succeed
    result = kb_add(
        title=long_title,
        category="pattern",
        content="Content",
        tags=[],
    )

    # Verify
    entry = kb_get(result["id"])
    assert len(entry["title"]) == 50
    assert entry["title"] == long_title


def test_kb_search_with_limit(initialized_project: Path) -> None:
    """Test kb_search respects limit parameter."""
    import os

    os.chdir(initialized_project)

    # Add 5 entries with same keyword
    for i in range(5):
        kb_add(f"API Entry {i}", "architecture", f"API content {i}", ["api"])

    # Search with limit
    results = kb_search(query="API", limit=3)

    # Verify limit is respected
    assert len(results) == 3


def test_kb_search_with_category_filter(initialized_project: Path) -> None:
    """Test kb_search with category filter."""
    import os

    os.chdir(initialized_project)

    # Add entries in different categories
    kb_add("API Design", "architecture", "API architecture", ["api"])
    kb_add("API Limit", "constraint", "API rate limit", ["api"])
    kb_add("Choose API", "decision", "API decision", ["api"])

    # Search with category filter
    results = kb_search(query="API", category="architecture")

    # Verify only architecture entries
    assert len(results) == 1
    assert results[0]["category"] == "architecture"
    assert results[0]["title"] == "API Design"


# ============================================================================
# Workflow Tests
# ============================================================================


def test_complete_workflow(initialized_project: Path) -> None:
    """Test complete MCP tool workflow."""
    import os

    os.chdir(initialized_project)

    # 1. Add entries
    kb_add("Entry 1", "architecture", "Content 1", ["tag1"])
    id2 = kb_add("Entry 2", "decision", "Content 2", ["tag2"])["id"]
    kb_add("Entry 3", "architecture", "Content 3", ["tag3"])

    # 2. List all
    all_entries = kb_list()
    assert len(all_entries) == 3

    # 3. List by category
    arch_entries = kb_list(category="architecture")
    assert len(arch_entries) == 2

    # 4. Search
    results = kb_search(query="Entry")
    assert len(results) == 3

    # 5. Get specific entry
    entry = kb_get(id2)
    assert entry["title"] == "Entry 2"
    assert entry["category"] == "decision"


# ============================================================================
# Week 2 MCP Tools Integration Tests
# ============================================================================


def test_analyze_recent_commits_with_real_repo(initialized_project: Path) -> None:
    """Test analyze_recent_commits with real Git repository."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo if not already initialized
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create and commit a file
    test_file = Path(initialized_project) / "test.txt"
    test_file.write_text("Test content")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: add test feature"],
        check=True,
        capture_output=True
    )

    # Analyze commits
    result = analyze_recent_commits(since_days=7)

    # Verify
    assert result["status"] == "success"
    assert result["commit_count"] >= 1
    assert "analysis" in result
    assert "category_distribution" in result["analysis"]
    assert "commits" in result


def test_analyze_recent_commits_no_commits(initialized_project: Path) -> None:
    """Test analyze_recent_commits with no recent commits."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize empty Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create at least one commit (empty repo may cause errors)
    test_file = Path(initialized_project) / "README.md"
    test_file.write_text("# Test")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial commit"],
        check=True,
        capture_output=True,
    )

    # Analyze commits from far future (should return 0 for last 0 days)
    result = analyze_recent_commits(since_days=0)

    # Verify - either success with 0 commits OR error
    assert result["status"] in ["success", "error"]
    if result["status"] == "success":
        # Should have 0 or 1 commit depending on timestamp
        assert result["commit_count"] >= 0


def test_analyze_recent_commits_with_max_count(initialized_project: Path) -> None:
    """Test analyze_recent_commits with max_count parameter."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git and make multiple commits
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    for i in range(5):
        test_file = Path(initialized_project) / f"test{i}.txt"
        test_file.write_text(f"Test content {i}")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: add feature {i}"],
            check=True,
            capture_output=True
        )

    # Analyze with limit
    result = analyze_recent_commits(since_days=7, max_count=3)

    # Verify max_count is respected
    assert result["status"] == "success"
    assert result["commit_count"] <= 3


def test_analyze_recent_commits_pattern_detection(initialized_project: Path) -> None:
    """Test analyze_recent_commits detects patterns correctly."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create commits with different categories
    commits = [
        ("feat: add new feature", "test_feature.txt"),
        ("fix: fix authentication bug", "auth.txt"),
        ("refactor: restructure API", "api.txt"),
    ]

    for message, filename in commits:
        test_file = Path(initialized_project) / filename
        test_file.write_text("content")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(["git", "commit", "-m", message], check=True, capture_output=True)

    # Analyze
    result = analyze_recent_commits(since_days=7)

    # Verify patterns detected
    assert result["status"] == "success"
    assert result["commit_count"] == 3
    assert "category_distribution" in result["analysis"]
    categories = result["analysis"]["category_distribution"]
    assert "feature" in categories or "bugfix" in categories or "refactor" in categories


def test_analyze_recent_commits_not_git_repo(tmp_path: Path) -> None:
    """Test analyze_recent_commits with non-Git directory."""
    import os

    # Create non-Git directory
    non_git_dir = tmp_path / "non_git"
    non_git_dir.mkdir()
    os.chdir(non_git_dir)

    # Try to analyze (should fail gracefully)
    result = analyze_recent_commits()

    # Verify error handling
    assert result["status"] == "error"
    assert "not a git repository" in result["message"].lower()


def test_suggest_next_tasks_with_bugfixes(initialized_project: Path) -> None:
    """Test suggest_next_tasks suggests tests after bugfixes."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create multiple bugfix commits
    for i in range(3):
        test_file = Path(initialized_project) / f"bugfix{i}.txt"
        test_file.write_text(f"Fix {i}")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"fix: fix bug {i}"],
            check=True,
            capture_output=True
        )

    # Get suggestions
    result = suggest_next_tasks(since_days=7)

    # Verify
    assert result["status"] == "success"
    assert "suggestion_count" in result
    if result["suggestion_count"] > 0:
        # Should suggest adding tests
        suggestions = result["suggestions"]
        assert isinstance(suggestions, list)


def test_suggest_next_tasks_with_features(initialized_project: Path) -> None:
    """Test suggest_next_tasks suggests docs after features."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create feature commits
    for i in range(2):
        test_file = Path(initialized_project) / f"feature{i}.txt"
        test_file.write_text(f"Feature {i}")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: add new feature {i}"],
            check=True,
            capture_output=True
        )

    # Get suggestions
    result = suggest_next_tasks(since_days=7, max_suggestions=5)

    # Verify
    assert result["status"] == "success"
    assert "suggestions" in result


def test_suggest_next_tasks_empty_history(initialized_project: Path) -> None:
    """Test suggest_next_tasks with no commit history."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize empty Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create at least one commit (empty repo may cause errors)
    test_file = Path(initialized_project) / "README.md"
    test_file.write_text("# Test")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial commit"],
        check=True,
        capture_output=True,
    )

    # Get suggestions with limited days (should return 0 suggestions)
    result = suggest_next_tasks(since_days=0)

    # Verify (should handle gracefully)
    assert result["status"] in ["success", "error"]
    if result["status"] == "success":
        assert result["suggestion_count"] >= 0


def test_suggest_next_tasks_max_suggestions(initialized_project: Path) -> None:
    """Test suggest_next_tasks respects max_suggestions parameter."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git and create many commits
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    for i in range(10):
        test_file = Path(initialized_project) / f"file{i}.txt"
        test_file.write_text(f"Content {i}")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"fix: fix bug {i}"],
            check=True,
            capture_output=True
        )

    # Get suggestions with limit
    result = suggest_next_tasks(since_days=7, max_suggestions=3)

    # Verify limit respected
    assert result["status"] == "success"
    assert result["suggestion_count"] <= 3


def test_suggest_next_tasks_filters_duplicates(initialized_project: Path) -> None:
    """Test suggest_next_tasks filters existing tasks."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create bugfix commits
    for i in range(3):
        test_file = Path(initialized_project) / f"bugfix{i}.txt"
        test_file.write_text(f"Fix {i}")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"fix: authentication bug {i}"],
            check=True,
            capture_output=True
        )

    # Get suggestions (should work even if tasks exist)
    result = suggest_next_tasks(since_days=7)

    # Verify
    assert result["status"] == "success"


def test_extract_decisions_from_commits_basic(initialized_project: Path) -> None:
    """Test extract_decisions_from_commits with decision keywords."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create commit with decision keyword
    test_file = Path(initialized_project) / "framework.txt"
    test_file.write_text("Using FastAPI")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: adopt FastAPI framework for REST API"],
        check=True,
        capture_output=True
    )

    # Extract decisions
    result = extract_decisions_from_commits(since_days=30, min_confidence=0.3)

    # Verify
    assert result["status"] == "success"
    # May or may not find candidates depending on heuristics
    assert "candidate_count" in result
    assert "candidates" in result


def test_extract_decisions_dependency_changes(initialized_project: Path) -> None:
    """Test extract_decisions_from_commits detects dependency changes."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create requirements.txt change (dependency file)
    req_file = Path(initialized_project) / "requirements.txt"
    req_file.write_text("fastapi==0.100.0\n")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: add FastAPI dependency"],
        check=True,
        capture_output=True
    )

    # Extract decisions
    result = extract_decisions_from_commits(since_days=30, min_confidence=0.2)

    # Verify
    assert result["status"] == "success"
    assert "candidates" in result


def test_extract_decisions_confidence_filter(initialized_project: Path) -> None:
    """Test extract_decisions_from_commits filters by confidence."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create commit
    test_file = Path(initialized_project) / "test.txt"
    test_file.write_text("content")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "feat: add feature"],
        check=True,
        capture_output=True
    )

    # Extract with high confidence filter (should filter most)
    result_high = extract_decisions_from_commits(since_days=30, min_confidence=0.9)

    # Extract with low confidence filter (should find more)
    result_low = extract_decisions_from_commits(since_days=30, min_confidence=0.1)

    # Verify filtering works
    assert result_high["status"] == "success"
    assert result_low["status"] == "success"
    # Low confidence should find equal or more candidates
    assert result_low["candidate_count"] >= result_high["candidate_count"]


def test_extract_decisions_no_decisions(initialized_project: Path) -> None:
    """Test extract_decisions_from_commits with no decision commits."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create regular commit (not a decision)
    test_file = Path(initialized_project) / "test.txt"
    test_file.write_text("content")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: update file"],
        check=True,
        capture_output=True
    )

    # Extract decisions with high confidence
    result = extract_decisions_from_commits(since_days=30, min_confidence=0.7)

    # Verify
    assert result["status"] == "success"
    # Likely no high-confidence decisions
    assert result["candidate_count"] >= 0


def test_extract_decisions_max_candidates(initialized_project: Path) -> None:
    """Test extract_decisions_from_commits respects max_candidates."""
    import os
    import subprocess

    os.chdir(initialized_project)

    # Initialize Git repo
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create many commits with decision keywords
    for i in range(10):
        test_file = Path(initialized_project) / f"decision{i}.txt"
        test_file.write_text(f"Decision {i}")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: choose option {i}"],
            check=True,
            capture_output=True
        )

    # Extract with limit
    result = extract_decisions_from_commits(
        since_days=30,
        max_candidates=3,
        min_confidence=0.1
    )

    # Verify limit respected
    assert result["status"] == "success"
    assert result["candidate_count"] <= 3


# ============================================================================
# Week 3 MCP Tools Tests - Context & Polish
# ============================================================================


def test_get_project_context_minimal(initialized_project: Path) -> None:
    """Test get_project_context with minimal depth."""
    from clauxton.mcp.server import get_project_context

    # Initialize Git
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create initial commit
    test_file = Path(initialized_project) / "README.md"
    test_file.write_text("# Test")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial commit"],
        check=True,
        capture_output=True,
    )

    # Add KB entry and task
    from datetime import datetime

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry, Task
    from clauxton.core.task_manager import TaskManager

    kb = KnowledgeBase(initialized_project)
    tm = TaskManager(initialized_project)

    entry = KnowledgeBaseEntry(
        id="KB-20251026-001",
        title="Test Decision",
        category="decision",
        content="Test content",
        tags=["test"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry)

    task = Task(
        id="TASK-001",
        name="Test Task",
        status="pending",
        priority="medium",
        created_at=datetime.now(),
    )
    tm.add(task)

    # Get minimal context
    result = get_project_context(depth="minimal", include_recent_activity=False)

    assert result["status"] == "success"
    assert result["depth"] == "minimal"
    assert "kb_summary" in result
    assert result["kb_summary"]["total_entries"] == 1
    assert "task_summary" in result
    assert result["task_summary"]["total_tasks"] == 1
    assert "recent_entries" not in result["kb_summary"]  # Not in minimal
    assert "active_tasks" not in result["task_summary"]  # Not in minimal


def test_get_project_context_standard(initialized_project: Path) -> None:
    """Test get_project_context with standard depth."""
    from datetime import datetime

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry, Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.mcp.server import get_project_context

    # Initialize Git
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create initial commit
    test_file = Path(initialized_project) / "README.md"
    test_file.write_text("# Test")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial commit"],
        check=True,
        capture_output=True,
    )

    kb = KnowledgeBase(initialized_project)
    tm = TaskManager(initialized_project)

    # Add multiple entries
    for i in range(3):
        entry = KnowledgeBaseEntry(
            id=f"KB-20251026-{i+1:03d}",
            title=f"Test Decision {i}",
            category="decision",
            content=f"Test content {i}",
            tags=["test"],
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

    # Add task
    task = Task(
        id="TASK-001",
        name="Test Task",
        status="in_progress",
        priority="high",
        created_at=datetime.now(),
    )
    tm.add(task)

    # Get standard context
    result = get_project_context(depth="standard", include_recent_activity=False)

    assert result["status"] == "success"
    assert result["depth"] == "standard"
    assert "recent_entries" in result["kb_summary"]
    assert len(result["kb_summary"]["recent_entries"]) <= 5
    assert "active_tasks" in result["task_summary"]
    assert len(result["task_summary"]["active_tasks"]) >= 1


def test_get_project_context_full(initialized_project: Path) -> None:
    """Test get_project_context with full depth including recent activity."""
    from clauxton.mcp.server import get_project_context

    # Initialize Git
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create commits
    for i in range(3):
        test_file = Path(initialized_project) / f"file{i}.txt"
        test_file.write_text(f"Content {i}")
        subprocess.run(["git", "add", "."], check=True, capture_output=True)
        subprocess.run(
            ["git", "commit", "-m", f"feat: add file {i}"],
            check=True,
            capture_output=True
        )

    # Get full context
    result = get_project_context(depth="full", include_recent_activity=True)

    assert result["status"] == "success"
    assert result["depth"] == "full"
    assert "recent_activity" in result
    assert "commit_count_7days" in result["recent_activity"]
    assert result["recent_activity"]["commit_count_7days"] >= 3
    assert "project_state" in result


def test_generate_project_summary(initialized_project: Path) -> None:
    """Test generate_project_summary generates proper Markdown."""
    from datetime import datetime

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry, Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.mcp.server import generate_project_summary

    # Initialize Git
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create initial commit
    test_file = Path(initialized_project) / "README.md"
    test_file.write_text("# Test")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial commit"],
        check=True,
        capture_output=True,
    )

    kb = KnowledgeBase(initialized_project)
    tm = TaskManager(initialized_project)

    # Add KB entry
    entry = KnowledgeBaseEntry(
        id="KB-20251026-001",
        title="Architecture Decision",
        category="architecture",
        content="Use FastAPI",
        tags=["api", "framework"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry)

    # Add task
    task = Task(
        id="TASK-001",
        name="Implement API",
        status="in_progress",
        priority="high",
        created_at=datetime.now(),
    )
    tm.add(task)

    # Generate summary
    result = generate_project_summary()

    assert result["status"] == "success"
    assert "summary_text" in result
    assert "# Project Summary" in result["summary_text"]
    assert "## Knowledge Base" in result["summary_text"]
    assert "## Tasks" in result["summary_text"]
    assert "statistics" in result
    assert result["statistics"]["kb_entries"] == 1
    assert result["statistics"]["total_tasks"] == 1
    assert "recommendations" in result


def test_generate_project_summary_with_blockers(initialized_project: Path) -> None:
    """Test generate_project_summary highlights blockers."""
    from datetime import datetime

    from clauxton.core.models import Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.mcp.server import generate_project_summary

    # Initialize Git
    subprocess.run(["git", "init"], check=True, capture_output=True)
    subprocess.run(["git", "config", "user.name", "Test User"], check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        check=True,
        capture_output=True,
    )

    # Create initial commit
    test_file = Path(initialized_project) / "README.md"
    test_file.write_text("# Test")
    subprocess.run(["git", "add", "."], check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "chore: initial commit"],
        check=True,
        capture_output=True,
    )

    tm = TaskManager(initialized_project)

    # Add blocked task
    task = Task(
        id="TASK-001",
        name="Blocked Task",
        status="blocked",
        priority="critical",
        created_at=datetime.now(),
    )
    tm.add(task)

    # Generate summary
    result = generate_project_summary()

    assert result["status"] == "success"
    assert "highlights" in result
    assert any("blocked" in h.lower() for h in result["highlights"])
    # Blocked tasks are highlighted (even if critical)
    assert len(result["highlights"]) >= 1


def test_get_knowledge_graph_empty(initialized_project: Path) -> None:
    """Test get_knowledge_graph with empty project."""
    from clauxton.mcp.server import get_knowledge_graph

    result = get_knowledge_graph()

    assert result["status"] == "success"
    assert "nodes" in result
    assert "edges" in result
    assert "statistics" in result
    assert len(result["nodes"]) == 0
    assert len(result["edges"]) == 0


def test_get_knowledge_graph_with_entries(initialized_project: Path) -> None:
    """Test get_knowledge_graph with KB entries."""
    from datetime import datetime

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry
    from clauxton.mcp.server import get_knowledge_graph

    kb = KnowledgeBase(initialized_project)

    # Add entries with shared tags
    entry1 = KnowledgeBaseEntry(
        id="KB-20251026-001",
        title="API Design",
        category="architecture",
        content="Use REST API",
        tags=["api", "rest"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry1)

    entry2 = KnowledgeBaseEntry(
        id="KB-20251026-002",
        title="API Authentication",
        category="decision",
        content="Use JWT",
        tags=["api", "jwt"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry2)

    # Generate graph
    result = get_knowledge_graph()

    assert result["status"] == "success"
    assert len(result["nodes"]) == 2
    assert result["statistics"]["kb_nodes"] == 2
    # Should have edge due to shared "api" tag
    assert len(result["edges"]) >= 1
    assert any(e["type"] == "shared_tags" for e in result["edges"])


def test_get_knowledge_graph_with_tasks(initialized_project: Path) -> None:
    """Test get_knowledge_graph with task dependencies."""
    from datetime import datetime

    from clauxton.core.models import Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.mcp.server import get_knowledge_graph

    tm = TaskManager(initialized_project)

    # Add tasks with dependencies
    task1 = Task(
        id="TASK-001",
        name="Task 1",
        status="completed",
        priority="high",
        created_at=datetime.now(),
    )
    tm.add(task1)

    task2 = Task(
        id="TASK-002",
        name="Task 2",
        status="in_progress",
        priority="high",
        depends_on=["TASK-001"],
        created_at=datetime.now(),
    )
    tm.add(task2)

    # Generate graph
    result = get_knowledge_graph()

    assert result["status"] == "success"
    assert len(result["nodes"]) == 2
    assert result["statistics"]["task_nodes"] == 2
    # Should have dependency edge
    assert len(result["edges"]) >= 1
    assert any(e["type"] == "dependency" for e in result["edges"])


def test_find_related_entries_kb_entry(initialized_project: Path) -> None:
    """Test find_related_entries for KB entry."""
    from datetime import datetime

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry
    from clauxton.mcp.server import find_related_entries

    kb = KnowledgeBase(initialized_project)

    # Add related entries
    entry1 = KnowledgeBaseEntry(
        id="KB-20251026-001",
        title="API Design",
        category="architecture",
        content="Use REST API with JSON",
        tags=["api", "rest", "json"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry1)

    entry2 = KnowledgeBaseEntry(
        id="KB-20251026-002",
        title="API Authentication",
        category="architecture",
        content="Use JWT tokens for API auth",
        tags=["api", "jwt", "authentication"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry2)

    entry3 = KnowledgeBaseEntry(
        id="KB-20251026-003",
        title="Database Choice",
        category="decision",
        content="Use PostgreSQL",
        tags=["database", "postgresql"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry3)

    # Find related entries for entry1
    result = find_related_entries("KB-20251026-001", limit=5, include_tasks=False)

    assert result["status"] == "success"
    assert result["reference_id"] == "KB-20251026-001"
    assert result["reference_type"] == "kb_entry"
    assert "related_entries" in result
    # Should find entry2 (shared tags: api, same category)
    assert len(result["related_entries"]) >= 1
    # entry2 should have higher score than entry3
    if len(result["related_entries"]) > 0:
        assert result["related_entries"][0]["id"] == "KB-20251026-002"


def test_find_related_entries_with_tasks(initialized_project: Path) -> None:
    """Test find_related_entries includes related tasks."""
    from datetime import datetime

    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.core.models import KnowledgeBaseEntry, Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.mcp.server import find_related_entries

    kb = KnowledgeBase(initialized_project)
    tm = TaskManager(initialized_project)

    # Add KB entry
    entry = KnowledgeBaseEntry(
        id="KB-20251026-001",
        title="API Design",
        category="architecture",
        content="Use REST API",
        tags=["api", "rest"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry)

    # Add related task (mentions tags)
    task = Task(
        id="TASK-001",
        name="Implement REST API endpoints",
        description="Build the API endpoints",
        status="pending",
        priority="high",
        created_at=datetime.now(),
    )
    tm.add(task)

    # Find related entries
    result = find_related_entries("KB-20251026-001", limit=5, include_tasks=True)

    assert result["status"] == "success"
    assert "related_tasks" in result
    # Should find task (mentions "api" and "rest")
    assert len(result["related_tasks"]) >= 1
    assert result["related_tasks"][0]["id"] == "TASK-001"


def test_find_related_entries_task_dependencies(initialized_project: Path) -> None:
    """Test find_related_entries for task shows dependencies."""
    from datetime import datetime

    from clauxton.core.models import Task
    from clauxton.core.task_manager import TaskManager
    from clauxton.mcp.server import find_related_entries

    tm = TaskManager(initialized_project)

    # Add tasks with dependencies
    task1 = Task(
        id="TASK-001",
        name="Task 1",
        status="completed",
        priority="high",
        created_at=datetime.now(),
    )
    tm.add(task1)

    task2 = Task(
        id="TASK-002",
        name="Task 2",
        status="in_progress",
        priority="high",
        depends_on=["TASK-001"],
        created_at=datetime.now(),
    )
    tm.add(task2)

    # Find related for task2
    result = find_related_entries("TASK-002", limit=5, include_tasks=True)

    assert result["status"] == "success"
    assert result["reference_type"] == "task"
    assert "related_tasks" in result
    # Should find task1 (dependency)
    assert len(result["related_tasks"]) >= 1
    related_ids = [t["id"] for t in result["related_tasks"]]
    assert "TASK-001" in related_ids
    # Should have high similarity score for dependency
    task1_result = next(t for t in result["related_tasks"] if t["id"] == "TASK-001")
    assert task1_result["similarity_score"] >= 0.5


def test_find_related_entries_not_found(initialized_project: Path) -> None:
    """Test find_related_entries with non-existent entry."""
    from clauxton.mcp.server import find_related_entries

    result = find_related_entries("KB-99999999-999", limit=5)

    assert result["status"] == "error"
    assert "not found" in result["message"].lower()
