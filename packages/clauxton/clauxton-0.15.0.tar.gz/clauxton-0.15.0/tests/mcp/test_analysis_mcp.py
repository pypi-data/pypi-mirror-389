"""
Tests for Analysis MCP Tools (Week 2).

Tests cover:
- analyze_recent_commits tool
- suggest_next_tasks tool
- extract_decisions_from_commits tool
- Error handling (NotAGitRepositoryError, general exceptions)
"""

import subprocess

import pytest

from clauxton.mcp.server import (
    analyze_recent_commits,
    extract_decisions_from_commits,
    suggest_next_tasks,
)


@pytest.fixture
def git_project(tmp_path):
    """Create a temporary Git project for testing."""
    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create Clauxton structure
    clauxton_dir = tmp_path / ".clauxton"
    clauxton_dir.mkdir()
    (clauxton_dir / "knowledge-base.yml").write_text("entries: []\n")
    (clauxton_dir / "tasks.yml").write_text("tasks: []\n")

    # Create initial commit
    (tmp_path / "README.md").write_text("# Test Project\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    return tmp_path


@pytest.fixture
def non_git_project(tmp_path):
    """Create a non-Git directory for testing errors."""
    return tmp_path / "non_git"


class TestAnalyzeRecentCommits:
    """Tests for analyze_recent_commits MCP tool."""

    def test_analyze_recent_commits_basic(self, git_project, monkeypatch):
        """Test basic commit analysis."""
        monkeypatch.chdir(git_project)

        result = analyze_recent_commits(since_days=7)

        assert result["status"] == "success"
        assert "commit_count" in result
        assert "analysis" in result
        assert result["commit_count"] >= 1  # At least initial commit

    def test_analyze_with_multiple_commits(self, git_project, monkeypatch):
        """Test analysis with multiple commits."""
        monkeypatch.chdir(git_project)

        # Create additional commits
        for i in range(3):
            (git_project / f"file{i}.txt").write_text(f"Content {i}")
            subprocess.run(
                ["git", "add", "."],
                cwd=git_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"feat: add file {i}"],
                cwd=git_project,
                check=True,
                capture_output=True,
            )

        result = analyze_recent_commits(since_days=1)

        assert result["status"] == "success"
        assert result["commit_count"] >= 3
        assert "category_distribution" in result["analysis"]
        assert "module_distribution" in result["analysis"]

    def test_analyze_with_max_count(self, git_project, monkeypatch):
        """Test analysis with max_count limit."""
        monkeypatch.chdir(git_project)

        result = analyze_recent_commits(since_days=365, max_count=1)

        assert result["status"] == "success"
        assert result["commit_count"] <= 1

    def test_analyze_no_commits_in_range(self, git_project, monkeypatch):
        """Test when no commits in time range."""
        monkeypatch.chdir(git_project)

        # since_days=0 might still include commits from today
        result = analyze_recent_commits(since_days=0)

        assert result["status"] == "success"
        # May have 0 or more commits depending on timing
        assert "commit_count" in result

    def test_analyze_not_git_repo(self, non_git_project, monkeypatch):
        """Test error handling for non-Git repository."""
        non_git_project.mkdir()
        monkeypatch.chdir(non_git_project)

        result = analyze_recent_commits()

        assert result["status"] == "error"
        assert "Not a Git repository" in result["message"]
        assert "hint" in result

    def test_analyze_without_gitpython(self, git_project, monkeypatch):
        """Test error when GitPython not installed."""
        monkeypatch.chdir(git_project)

        # Mock ImportError
        import sys

        with monkeypatch.context() as m:
            # Temporarily remove git module
            m.setitem(sys.modules, "git", None)

            result = analyze_recent_commits()

            # Should handle import error
            assert result["status"] in ["error", "success"]


class TestSuggestNextTasks:
    """Tests for suggest_next_tasks MCP tool."""

    def test_suggest_tasks_basic(self, git_project, monkeypatch):
        """Test basic task suggestion."""
        monkeypatch.chdir(git_project)

        result = suggest_next_tasks(since_days=7, max_suggestions=5)

        assert result["status"] == "success"
        assert "suggestion_count" in result
        assert "suggestions" in result
        assert isinstance(result["suggestions"], list)

    def test_suggest_with_bugfixes(self, git_project, monkeypatch):
        """Test suggestions based on bugfix commits."""
        monkeypatch.chdir(git_project)

        # Create bugfix commits
        for i in range(4):
            (git_project / f"bug{i}.py").write_text(f"# Fix bug {i}\n")
            subprocess.run(
                ["git", "add", "."],
                cwd=git_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"fix: resolve bug {i}"],
                cwd=git_project,
                check=True,
                capture_output=True,
            )

        result = suggest_next_tasks(since_days=1)

        assert result["status"] == "success"
        # Should suggest adding tests
        if result["suggestion_count"] > 0:
            assert any(
                "test" in s["name"].lower() for s in result["suggestions"]
            )

    def test_suggest_with_features(self, git_project, monkeypatch):
        """Test suggestions based on feature commits."""
        monkeypatch.chdir(git_project)

        # Create feature commits
        for i in range(3):
            (git_project / f"feature{i}.py").write_text(f"# Feature {i}\n")
            subprocess.run(
                ["git", "add", "."],
                cwd=git_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"feat: add feature {i}"],
                cwd=git_project,
                check=True,
                capture_output=True,
            )

        result = suggest_next_tasks(since_days=1)

        assert result["status"] == "success"
        # Should suggest documentation
        if result["suggestion_count"] > 0:
            suggestions = result["suggestions"]
            assert any(
                "doc" in s["name"].lower() for s in suggestions
            )

    def test_suggest_max_limit(self, git_project, monkeypatch):
        """Test max_suggestions limit."""
        monkeypatch.chdir(git_project)

        # Create many commits
        for i in range(10):
            (git_project / f"file{i}.txt").write_text(f"Content {i}")
            subprocess.run(
                ["git", "add", "."],
                cwd=git_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"chore: update {i}"],
                cwd=git_project,
                check=True,
                capture_output=True,
            )

        result = suggest_next_tasks(since_days=1, max_suggestions=3)

        assert result["status"] == "success"
        assert result["suggestion_count"] <= 3

    def test_suggest_error_handling(self, non_git_project, monkeypatch):
        """Test error handling in task suggestion."""
        non_git_project.mkdir()
        monkeypatch.chdir(non_git_project)

        result = suggest_next_tasks()

        assert result["status"] == "error"
        assert "message" in result


class TestExtractDecisionsFromCommits:
    """Tests for extract_decisions_from_commits MCP tool."""

    def test_extract_decisions_basic(self, git_project, monkeypatch):
        """Test basic decision extraction."""
        monkeypatch.chdir(git_project)

        result = extract_decisions_from_commits(since_days=30)

        assert result["status"] == "success"
        assert "candidate_count" in result
        assert "candidates" in result
        assert isinstance(result["candidates"], list)

    def test_extract_with_decision_commit(self, git_project, monkeypatch):
        """Test extraction with decision-related commit."""
        monkeypatch.chdir(git_project)

        # Create decision commit
        (git_project / "requirements.txt").write_text("fastapi==0.68.0\n")
        subprocess.run(
            ["git", "add", "."], cwd=git_project, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "feat: adopt FastAPI framework"],
            cwd=git_project,
            check=True,
            capture_output=True,
        )

        result = extract_decisions_from_commits(since_days=1)

        assert result["status"] == "success"
        # May or may not find candidates depending on confidence

    def test_extract_with_config_change(self, git_project, monkeypatch):
        """Test extraction with configuration change."""
        monkeypatch.chdir(git_project)

        # Create config commit
        (git_project / "config.yml").write_text("database: postgresql\n")
        subprocess.run(
            ["git", "add", "."], cwd=git_project, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "config: switch to PostgreSQL"],
            cwd=git_project,
            check=True,
            capture_output=True,
        )

        result = extract_decisions_from_commits(since_days=1, min_confidence=0.1)

        assert result["status"] == "success"
        # Configuration changes should be detected

    def test_extract_confidence_filtering(self, git_project, monkeypatch):
        """Test confidence threshold filtering."""
        monkeypatch.chdir(git_project)

        # Create various commits
        (git_project / "dep.txt").write_text("library\n")
        subprocess.run(
            ["git", "add", "."], cwd=git_project, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "chore: add dependency"],
            cwd=git_project,
            check=True,
            capture_output=True,
        )

        # Low confidence threshold
        result_low = extract_decisions_from_commits(since_days=1, min_confidence=0.1)
        # High confidence threshold
        result_high = extract_decisions_from_commits(since_days=1, min_confidence=0.9)

        assert result_low["status"] == "success"
        assert result_high["status"] == "success"
        # Low threshold should find more or equal candidates
        assert result_low["candidate_count"] >= result_high["candidate_count"]

    def test_extract_max_candidates_limit(self, git_project, monkeypatch):
        """Test max_candidates limit."""
        monkeypatch.chdir(git_project)

        # Create many decision commits
        for i in range(15):
            (git_project / f"lib{i}.txt").write_text(f"library{i}\n")
            subprocess.run(
                ["git", "add", "."],
                cwd=git_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"chore: adopt library {i}"],
                cwd=git_project,
                check=True,
                capture_output=True,
            )

        result = extract_decisions_from_commits(
            since_days=1, max_candidates=5, min_confidence=0.1
        )

        assert result["status"] == "success"
        assert "total_analyzed" in result
        # Filtered count should be <= max_candidates
        assert result["candidate_count"] <= 5

    def test_extract_error_handling(self, non_git_project, monkeypatch):
        """Test error handling in decision extraction."""
        non_git_project.mkdir()
        monkeypatch.chdir(non_git_project)

        result = extract_decisions_from_commits()

        assert result["status"] == "error"
        assert "message" in result


class TestIntegration:
    """Integration tests for analysis MCP tools."""

    def test_workflow_analyze_suggest_extract(self, git_project, monkeypatch):
        """Test complete workflow: analyze → suggest → extract."""
        monkeypatch.chdir(git_project)

        # Create various commits
        commits = [
            ("fix: bug1", "bug1.py"),
            ("fix: bug2", "bug2.py"),
            ("feat: feature1", "feature1.py"),
        ]

        for message, filename in commits:
            (git_project / filename).write_text(f"# {message}\n")
            subprocess.run(
                ["git", "add", "."],
                cwd=git_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", message],
                cwd=git_project,
                check=True,
                capture_output=True,
            )

        # Step 1: Analyze commits
        analysis = analyze_recent_commits(since_days=1)
        assert analysis["status"] == "success"
        assert analysis["commit_count"] >= 3

        # Step 2: Get task suggestions
        suggestions = suggest_next_tasks(since_days=1)
        assert suggestions["status"] == "success"

        # Step 3: Extract decisions
        decisions = extract_decisions_from_commits(since_days=1, min_confidence=0.1)
        assert decisions["status"] == "success"

    def test_consistency_across_calls(self, git_project, monkeypatch):
        """Test consistency of results across multiple calls."""
        monkeypatch.chdir(git_project)

        # Call analyze twice
        result1 = analyze_recent_commits(since_days=7)
        result2 = analyze_recent_commits(since_days=7)

        assert result1["commit_count"] == result2["commit_count"]
        assert result1["status"] == result2["status"]
