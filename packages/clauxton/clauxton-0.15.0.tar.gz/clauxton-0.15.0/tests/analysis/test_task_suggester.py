"""Tests for TaskSuggester."""

from datetime import datetime
from unittest.mock import patch

import pytest

from clauxton.analysis.git_analyzer import CommitInfo
from clauxton.analysis.task_suggester import TaskSuggester, TaskSuggestion


@pytest.fixture
def tmp_project(tmp_path):
    """Create temporary project directory with Clauxton structure."""
    clauxton_dir = tmp_path / ".clauxton"
    clauxton_dir.mkdir()

    # Create empty YAML files
    (clauxton_dir / "knowledge-base.yml").write_text("entries: []\n")
    (clauxton_dir / "tasks.yml").write_text("tasks: []\n")

    # Initialize git repo
    import subprocess

    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test"],
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

    # Initial commit
    (tmp_path / "README.md").write_text("# Test\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    return tmp_path


@pytest.fixture
def suggester(tmp_project):
    """Create TaskSuggester instance."""
    return TaskSuggester(tmp_project)


@pytest.fixture
def sample_commits():
    """Create sample commits for testing."""
    return [
        CommitInfo(
            sha="abc123",
            message="fix: resolve authentication bug",
            author="Author",
            date=datetime.now(),
            files=["src/auth.py"],
            diff="",
            stats={"insertions": 10, "deletions": 5, "files_changed": 1},
        ),
        CommitInfo(
            sha="def456",
            message="fix: fix login error",
            author="Author",
            date=datetime.now(),
            files=["src/auth.py"],
            diff="",
            stats={"insertions": 5, "deletions": 3, "files_changed": 1},
        ),
        CommitInfo(
            sha="ghi789",
            message="fix: resolve session timeout",
            author="Author",
            date=datetime.now(),
            files=["src/session.py"],
            diff="",
            stats={"insertions": 15, "deletions": 10, "files_changed": 1},
        ),
    ]


class TestTaskSuggestion:
    """Tests for TaskSuggestion class."""

    def test_task_suggestion_creation(self):
        """Test creating TaskSuggestion."""
        suggestion = TaskSuggestion(
            name="Add tests",
            description="Add unit tests",
            priority="high",
            reasoning="Multiple bugs found",
            related_commits=["abc123"],
            confidence=0.85,
        )

        assert suggestion.name == "Add tests"
        assert suggestion.priority == "high"
        assert suggestion.confidence == 0.85

    def test_task_suggestion_to_dict(self):
        """Test TaskSuggestion to_dict."""
        suggestion = TaskSuggestion(
            name="Add tests",
            description="Add unit tests",
            priority="high",
            reasoning="Multiple bugs",
            related_commits=["abc123"],
            confidence=0.85,
        )

        result = suggestion.to_dict()

        assert isinstance(result, dict)
        assert result["name"] == "Add tests"
        assert result["priority"] == "high"
        assert result["confidence"] == 0.85
        assert "abc123" in result["related_commits"]


class TestAnalyzePatterns:
    """Tests for analyze_patterns."""

    def test_analyze_patterns_basic(self, suggester, sample_commits):
        """Test basic pattern analysis."""
        analysis = suggester.analyze_patterns(sample_commits)

        assert isinstance(analysis, dict)
        assert "category_counts" in analysis
        assert "module_counts" in analysis
        assert "keyword_counts" in analysis
        assert "impact_counts" in analysis
        assert "total_commits" in analysis

    def test_analyze_patterns_bugfix_detection(self, suggester, sample_commits):
        """Test bugfix pattern detection."""
        analysis = suggester.analyze_patterns(sample_commits)

        # All sample commits are bugfixes
        assert analysis["category_counts"].get("bugfix", 0) == 3
        assert analysis["total_commits"] == 3

    def test_analyze_patterns_module_detection(self, suggester, sample_commits):
        """Test module detection in patterns."""
        analysis = suggester.analyze_patterns(sample_commits)

        # Should detect "src" as most common module
        assert "src" in analysis["module_counts"]
        assert analysis["module_counts"]["src"] >= 2


class TestGenerateSuggestions:
    """Tests for generate_suggestions."""

    def test_suggestion_for_multiple_bugfixes(self, suggester, sample_commits):
        """Test suggestion generation for multiple bugfixes."""
        analysis = suggester.analyze_patterns(sample_commits)
        suggestions = suggester.generate_suggestions(analysis, sample_commits)

        # Should suggest adding tests
        test_suggestions = [
            s for s in suggestions if "test" in s.name.lower()
        ]

        assert len(test_suggestions) > 0
        assert any(s.priority == "high" for s in test_suggestions)

    def test_suggestion_for_features(self, suggester):
        """Test suggestion for new features."""
        feature_commits = [
            CommitInfo(
                sha=f"feat{i}",
                message=f"feat: add feature {i}",
                author="Author",
                date=datetime.now(),
                files=[f"src/feature{i}.py"],
                diff="",
                stats={"insertions": 50, "deletions": 0, "files_changed": 1},
            )
            for i in range(3)
        ]

        analysis = suggester.analyze_patterns(feature_commits)
        suggestions = suggester.generate_suggestions(analysis, feature_commits)

        # Should suggest documentation update
        doc_suggestions = [
            s for s in suggestions if "doc" in s.name.lower()
        ]

        assert len(doc_suggestions) > 0

    def test_suggestion_for_high_impact(self, suggester):
        """Test suggestion for high-impact changes."""
        high_impact_commits = [
            CommitInfo(
                sha="high1",
                message="refactor: major refactoring",
                author="Author",
                date=datetime.now(),
                files=[f"file{i}.py" for i in range(15)],
                diff="",
                stats={"insertions": 600, "deletions": 400, "files_changed": 15},
            ),
            CommitInfo(
                sha="high2",
                message="refactor: restructure modules",
                author="Author",
                date=datetime.now(),
                files=[f"module{i}.py" for i in range(12)],
                diff="",
                stats={"insertions": 500, "deletions": 300, "files_changed": 12},
            ),
        ]

        analysis = suggester.analyze_patterns(high_impact_commits)
        suggestions = suggester.generate_suggestions(analysis, high_impact_commits)

        # Should suggest review/testing
        review_suggestions = [
            s for s in suggestions
            if "review" in s.name.lower() or "test" in s.name.lower()
        ]

        assert len(review_suggestions) > 0


class TestFilterDuplicates:
    """Tests for filter_duplicates."""

    def test_filter_existing_tasks(self, suggester, tmp_project):
        """Test filtering suggestions that match existing tasks."""
        # Add a task via YAML
        tasks_yml = tmp_project / ".clauxton" / "tasks.yml"
        tasks_yml.write_text("""
tasks:
  - id: TASK-001
    name: Add comprehensive tests
    status: pending
    priority: high
    created_at: 2025-10-26T00:00:00
""")

        suggestions = [
            TaskSuggestion(
                name="Add comprehensive tests to prevent regressions",
                description="...",
                priority="high",
                reasoning="...",
                related_commits=[],
                confidence=0.8,
            ),
            TaskSuggestion(
                name="Update documentation",
                description="...",
                priority="medium",
                reasoning="...",
                related_commits=[],
                confidence=0.7,
            ),
        ]

        filtered = suggester.filter_duplicates(suggestions)

        # First suggestion should be filtered out
        assert len(filtered) < len(suggestions)
        assert all("doc" in s.name.lower() for s in filtered)

    def test_no_filtering_for_unique(self, suggester):
        """Test no filtering when suggestions are unique."""
        suggestions = [
            TaskSuggestion(
                name="Unique task 1",
                description="...",
                priority="high",
                reasoning="...",
                related_commits=[],
                confidence=0.8,
            ),
            TaskSuggestion(
                name="Unique task 2",
                description="...",
                priority="medium",
                reasoning="...",
                related_commits=[],
                confidence=0.7,
            ),
        ]

        filtered = suggester.filter_duplicates(suggestions)

        assert len(filtered) == len(suggestions)


class TestSuggestTasks:
    """Tests for suggest_tasks (integration)."""

    def test_suggest_tasks_with_recent_commits(self, suggester, tmp_project):
        """Test task suggestion with recent commits."""
        import subprocess

        # Create multiple bugfix commits
        for i in range(4):
            (tmp_project / f"bug{i}.py").write_text(f"# Bug fix {i}\n")
            subprocess.run(
                ["git", "add", "."],
                cwd=tmp_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"fix: resolve bug {i}"],
                cwd=tmp_project,
                check=True,
                capture_output=True,
            )

        suggestions = suggester.suggest_tasks(since_days=1, max_suggestions=5)

        assert isinstance(suggestions, list)
        # Should have at least one suggestion for tests
        assert len(suggestions) > 0
        assert all(isinstance(s, TaskSuggestion) for s in suggestions)

    def test_suggest_tasks_empty_history(self, suggester):
        """Test task suggestion with no recent commits."""
        suggestions = suggester.suggest_tasks(since_days=0, max_suggestions=5)

        assert isinstance(suggestions, list)
        assert len(suggestions) == 0

    def test_suggest_tasks_sorting_by_confidence(self, suggester, sample_commits):
        """Test that suggestions are sorted by confidence."""
        with patch.object(
            suggester.git_analyzer, "get_recent_commits", return_value=sample_commits
        ):
            suggestions = suggester.suggest_tasks(since_days=7, max_suggestions=10)

            if len(suggestions) > 1:
                # Verify descending order
                confidences = [s.confidence for s in suggestions]
                assert confidences == sorted(confidences, reverse=True)


class TestGetTaskStatistics:
    """Tests for get_task_statistics."""

    def test_get_statistics_basic(self, suggester, tmp_project):
        """Test getting task statistics."""
        import subprocess

        # Create some commits
        for i in range(3):
            (tmp_project / f"file{i}.py").write_text(f"content {i}\n")
            subprocess.run(
                ["git", "add", "."],
                cwd=tmp_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"feat: add feature {i}"],
                cwd=tmp_project,
                check=True,
                capture_output=True,
            )

        stats = suggester.get_task_statistics(since_days=1)

        assert isinstance(stats, dict)
        assert "total_commits" in stats
        assert "commits_per_day" in stats
        assert "category_distribution" in stats
        assert "module_distribution" in stats
        assert "impact_distribution" in stats
        assert "top_keywords" in stats

    def test_statistics_accuracy(self, suggester, tmp_project):
        """Test statistics calculation accuracy."""
        import subprocess

        # Create exactly 2 commits
        for i in range(2):
            (tmp_project / f"stat{i}.py").write_text(f"stats {i}\n")
            subprocess.run(
                ["git", "add", "."],
                cwd=tmp_project,
                check=True,
                capture_output=True,
            )
            subprocess.run(
                ["git", "commit", "-m", f"test: add test {i}"],
                cwd=tmp_project,
                check=True,
                capture_output=True,
            )

        stats = suggester.get_task_statistics(since_days=1)

        assert stats["total_commits"] >= 2
        assert stats["commits_per_day"] >= 0
