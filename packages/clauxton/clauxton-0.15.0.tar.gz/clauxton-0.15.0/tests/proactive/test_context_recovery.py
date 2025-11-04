"""
Error recovery tests for Context Intelligence features.

Tests validate graceful degradation and fallback behaviors
when errors occur or dependencies are unavailable.
"""

import subprocess
from datetime import datetime
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clauxton.proactive.context_manager import ContextManager


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""

    @patch("subprocess.run")
    def test_recovery_git_unavailable_full_degradation(self, mock_run, tmp_path: Path):
        """Test all features work when git is completely unavailable."""
        manager = ContextManager(tmp_path)

        # Mock git not found
        mock_run.side_effect = FileNotFoundError("git not found")

        # Git operations should return safe defaults
        assert manager._count_uncommitted_changes() == 0
        assert manager._get_git_diff_stats() is None
        assert manager._get_current_branch() is None
        assert not manager._is_feature_branch()

        # Non-git features should still work
        active_files = manager.detect_active_files(minutes=30)
        assert isinstance(active_files, list)

        # Analysis should still work (with degraded info)
        analysis = manager.analyze_work_session()
        assert isinstance(analysis, dict)
        assert "duration_minutes" in analysis

    @patch("subprocess.run")
    def test_recovery_partial_git_failure(self, mock_run, tmp_path: Path):
        """Test recovery when some git commands fail."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        call_count = [0]

        def partial_failure(*args, **kwargs):
            call_count[0] += 1
            if call_count[0] % 2 == 0:  # Fail every other call
                raise subprocess.CalledProcessError(1, "git")
            result = MagicMock()
            result.returncode = 0
            result.stdout = "main"
            return result

        mock_run.side_effect = partial_failure

        # Should handle failures gracefully
        for _ in range(4):
            branch = manager._get_current_branch()
            # Should return None on failure, "main" on success
            assert branch is None or branch == "main"

    def test_recovery_corrupted_file_timestamps(self, tmp_path: Path):
        """Test handling of files with invalid timestamps."""
        manager = ContextManager(tmp_path)

        # Create file with future timestamp
        future_file = tmp_path / "future.py"
        future_file.write_text("# Future")
        future_time = datetime.now().timestamp() + 86400  # Tomorrow
        import os
        os.utime(future_file, (future_time, future_time))

        # Create file with very old timestamp
        old_file = tmp_path / "old.py"
        old_file.write_text("# Old")
        old_time = 0  # Epoch
        os.utime(old_file, (old_time, old_time))

        # Should handle gracefully
        session_start = manager._estimate_session_start()
        assert session_start is None or isinstance(session_start, datetime)

        breaks = manager._detect_breaks()
        assert isinstance(breaks, list)

    def test_recovery_filesystem_permission_denied(self, tmp_path: Path):
        """Test handling when file permissions prevent access."""
        manager = ContextManager(tmp_path)

        # Create accessible file
        good_file = tmp_path / "good.py"
        good_file.write_text("# Good")

        # Create inaccessible file
        bad_file = tmp_path / "bad.py"
        bad_file.write_text("# Bad")

        import os
        import stat
        try:
            os.chmod(bad_file, 0o000)

            # Should skip bad file, process good file
            session_start = manager._estimate_session_start()
            # Should not crash
            assert session_start is None or isinstance(session_start, datetime)

            # Restore permissions for cleanup
            os.chmod(bad_file, stat.S_IRUSR | stat.S_IWUSR)
        except (OSError, PermissionError):
            pytest.skip("Permission modification not supported")

    @patch("subprocess.run")
    def test_recovery_malformed_git_output_diff(self, mock_run, tmp_path: Path):
        """Test recovery from malformed git diff output."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        malformed_outputs = [
            "",  # Empty
            "garbage output",  # No stats
            "file.py | 10 +++++\nincomplete",  # Missing summary
            "500 files",  # Only partial stats
        ]

        for output in malformed_outputs:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = output
            mock_run.return_value = mock_result

            # Should not crash
            stats = manager._get_git_diff_stats()

            # Should return None or safe defaults
            if stats is not None:
                assert isinstance(stats, dict)
                assert "additions" in stats
                assert "deletions" in stats
                assert "files_changed" in stats

    @patch("subprocess.run")
    def test_recovery_git_timeout_continues(self, mock_run, tmp_path: Path):
        """Test system continues when git times out."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired("git", 5)

        # Should handle timeout gracefully
        analysis = manager.analyze_work_session()

        # Analysis should work (with degraded git info)
        assert isinstance(analysis, dict)
        assert analysis["duration_minutes"] >= 0
        assert 0.0 <= analysis["focus_score"] <= 1.0

    def test_recovery_empty_project_directory(self, tmp_path: Path):
        """Test handling of completely empty project."""
        manager = ContextManager(tmp_path)

        # Empty directory
        assert len(list(tmp_path.iterdir())) == 0

        # Should return empty/default values, not crash
        context = manager.get_current_context()
        assert context.active_files == []
        assert context.current_branch is None
        assert context.session_duration_minutes == 0 or context.session_duration_minutes is None

    @patch("subprocess.run")
    def test_recovery_git_stderr_output(self, mock_run, tmp_path: Path):
        """Test handling of git commands that output to stderr."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        # Mock git with stderr output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "M file.py"
        mock_result.stderr = "warning: some warning"
        mock_run.return_value = mock_result

        # Should handle stderr, not crash
        count = manager._count_uncommitted_changes()
        assert isinstance(count, int)
        assert count >= 0

    def test_recovery_cache_with_none_values(self, tmp_path: Path):
        """Test caching handles None values correctly."""
        manager = ContextManager(tmp_path)

        # Get context with no git, no files (many None values)
        context1 = manager.get_current_context()
        context2 = manager.get_current_context()  # Should use cache

        # Should handle None values in cache
        assert context1.current_branch == context2.current_branch
        assert context1.active_files == context2.active_files

    def test_recovery_concurrent_file_modifications(self, tmp_path: Path):
        """Test handling when files are modified during analysis."""
        import time
        manager = ContextManager(tmp_path)

        # Create initial file
        test_file = tmp_path / "test.py"
        test_file.write_text("# Version 1")

        # Start analysis
        session_start = manager._estimate_session_start()

        # Modify file during analysis
        time.sleep(0.01)
        test_file.write_text("# Version 2")

        # Continue analysis
        focus_score = manager._calculate_focus_score()

        # Should handle gracefully (no crashes or exceptions)
        assert session_start is None or isinstance(session_start, datetime)
        assert 0.0 <= focus_score <= 1.0
