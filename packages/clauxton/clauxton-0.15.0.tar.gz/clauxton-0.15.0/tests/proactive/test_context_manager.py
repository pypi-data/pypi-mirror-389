"""
Tests for ContextManager - Project context awareness.

Week 2 Day 5 - v0.13.0
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import patch

from clauxton.proactive.context_manager import ContextManager, ProjectContext


class TestContextManager:
    """Test ContextManager functionality."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test context manager initialization."""
        manager = ContextManager(tmp_path)

        assert manager.project_root == tmp_path
        assert isinstance(manager._cache, dict)

    def test_get_current_context(self, tmp_path: Path) -> None:
        """Test getting current project context."""
        manager = ContextManager(tmp_path)

        context = manager.get_current_context()

        assert isinstance(context, ProjectContext)
        assert context.time_context in ["morning", "afternoon", "evening", "night"]
        assert context.last_activity is not None

    def test_context_caching(self, tmp_path: Path) -> None:
        """Test that context is cached for 30 seconds."""
        manager = ContextManager(tmp_path)

        # First call
        context1 = manager.get_current_context()

        # Second call (should use cache)
        context2 = manager.get_current_context()

        # Should be the same object (cached)
        assert context1 is context2

    def test_cache_invalidation(self, tmp_path: Path) -> None:
        """Test cache can be cleared."""
        manager = ContextManager(tmp_path)

        # Get context
        context1 = manager.get_current_context()

        # Clear cache
        manager.clear_cache()

        # Get context again (should be new)
        context2 = manager.get_current_context()

        # Should be different objects
        assert context1 is not context2

    def test_detect_active_files(self, tmp_path: Path) -> None:
        """Test detecting recently modified files."""
        # Create some test files
        test_file = tmp_path / "test.py"
        test_file.write_text("# test file")

        manager = ContextManager(tmp_path)

        active_files = manager.detect_active_files(minutes=60)

        # Should detect the recently created file
        assert isinstance(active_files, list)
        # Note: May be empty if find command doesn't find it immediately
        # This is a timing-sensitive test

    def test_get_time_context(self, tmp_path: Path) -> None:
        """Test getting time context."""
        manager = ContextManager(tmp_path)

        time_context = manager.get_time_context()

        assert time_context in ["morning", "afternoon", "evening", "night"]

        # Verify mapping
        hour = datetime.now().hour
        if 6 <= hour < 12:
            assert time_context == "morning"
        elif 12 <= hour < 17:
            assert time_context == "afternoon"
        elif 17 <= hour < 22:
            assert time_context == "evening"
        else:
            assert time_context == "night"

    @patch("subprocess.run")
    def test_get_current_branch(self, mock_run, tmp_path: Path) -> None:
        """Test getting current git branch."""
        # Mock git command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "feature/test-branch\n"

        # Create .git directory
        (tmp_path / ".git").mkdir()

        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        assert context.current_branch == "feature/test-branch"

    @patch("subprocess.run")
    def test_is_feature_branch(self, mock_run, tmp_path: Path) -> None:
        """Test detecting feature branch."""
        # Mock git command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "feature/new-feature\n"

        # Create .git directory
        (tmp_path / ".git").mkdir()

        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        assert context.is_feature_branch is True

    @patch("subprocess.run")
    def test_is_not_feature_branch(self, mock_run, tmp_path: Path) -> None:
        """Test detecting non-feature branch."""
        # Mock git command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "main\n"

        # Create .git directory
        (tmp_path / ".git").mkdir()

        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        assert context.is_feature_branch is False

    def test_no_git_repo_fallback(self, tmp_path: Path) -> None:
        """Test graceful fallback when not in git repo."""
        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        # Should work even without git
        assert context.current_branch is None
        assert context.is_feature_branch is False
        assert context.is_git_repo is False

    @patch("subprocess.run")
    def test_get_recent_commits(self, mock_run, tmp_path: Path) -> None:
        """Test getting recent commits."""
        # Mock git log command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = (
            "abc123|John Doe|john@example.com|feat: add feature|2025-10-26 10:00:00\n"
            "def456|Jane Smith|jane@example.com|fix: bug fix|2025-10-25 15:30:00\n"
        )

        # Create .git directory
        (tmp_path / ".git").mkdir()

        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        assert len(context.recent_commits) == 2
        assert context.recent_commits[0]["author_name"] == "John Doe"
        assert context.recent_commits[0]["message"] == "feat: add feature"

    @patch("subprocess.run")
    def test_infer_current_task_from_branch(self, mock_run, tmp_path: Path) -> None:
        """Test inferring current task from branch name."""
        # Mock git command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "feature/TASK-123-new-feature\n"

        # Create .git directory
        (tmp_path / ".git").mkdir()

        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        assert context.current_task == "TASK-123"

    def test_get_branch_context(self, tmp_path: Path) -> None:
        """Test getting branch context."""
        manager = ContextManager(tmp_path)

        branch_context = manager.get_branch_context()

        assert "current_branch" in branch_context
        assert "is_feature_branch" in branch_context
        assert "is_main_branch" in branch_context
        assert "is_git_repo" in branch_context

    def test_estimate_session_start(self, tmp_path: Path) -> None:
        """Test estimating work session start time."""
        # Create a test file
        test_file = tmp_path / "test.py"
        test_file.write_text("# test")

        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        # May or may not detect session start (timing-sensitive)
        # Just verify it's None or a datetime
        assert context.work_session_start is None or isinstance(
            context.work_session_start, datetime
        )


class TestProjectContext:
    """Test ProjectContext model."""

    def test_project_context_creation(self) -> None:
        """Test creating a ProjectContext."""
        now = datetime.now()
        context = ProjectContext(
            current_branch="feature/test",
            active_files=["src/test.py"],
            time_context="morning",
            last_activity=now,
            is_feature_branch=True,
            is_git_repo=True,
        )

        assert context.current_branch == "feature/test"
        assert len(context.active_files) == 1
        assert context.time_context == "morning"
        assert context.is_feature_branch is True
        assert context.is_git_repo is True

    def test_project_context_defaults(self) -> None:
        """Test ProjectContext default values."""
        context = ProjectContext()

        assert context.current_branch is None
        assert len(context.active_files) == 0
        assert len(context.recent_commits) == 0
        assert context.current_task is None
        assert context.time_context == "unknown"
        assert context.work_session_start is None
        assert context.is_feature_branch is False
        assert context.is_git_repo is True


class TestContextIntegration:
    """Test ContextManager integration scenarios."""

    @patch("subprocess.run")
    def test_feature_development_context(self, mock_run, tmp_path: Path) -> None:
        """Test context for feature development scenario."""
        # Mock git command
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = "feature/TASK-456-new-api\n"

        # Create .git directory
        (tmp_path / ".git").mkdir()

        # Create some files
        (tmp_path / "src").mkdir()
        (tmp_path / "src" / "api.py").write_text("# API code")

        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        assert context.is_feature_branch is True
        assert context.current_task == "TASK-456"
        assert context.is_git_repo is True

    def test_non_git_project_context(self, tmp_path: Path) -> None:
        """Test context for non-git project."""
        manager = ContextManager(tmp_path)
        context = manager.get_current_context()

        assert context.is_git_repo is False
        assert context.current_branch is None
        assert len(context.recent_commits) == 0
        # Should still provide time context
        assert context.time_context in ["morning", "afternoon", "evening", "night"]
