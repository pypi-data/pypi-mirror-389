"""
Security tests for Context Intelligence features.

Tests validate that the system is secure against common vulnerabilities:
- Command injection
- Path traversal
- Denial of Service (timeout)
- Input sanitization
"""

import subprocess
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from clauxton.proactive.context_manager import ContextManager


class TestSecurity:
    """Security validation tests."""

    @patch("subprocess.run")
    def test_security_no_command_injection_git_status(self, mock_run, tmp_path: Path):
        """Test git status command doesn't allow injection."""
        # Create malicious project root path (attempt injection)
        malicious_path = tmp_path / "test; rm -rf /"
        malicious_path.mkdir(parents=True, exist_ok=True)
        (malicious_path / ".git").mkdir()

        manager = ContextManager(malicious_path)

        # Mock subprocess to capture command
        captured_cmd = None
        def capture_command(cmd, **kwargs):
            nonlocal captured_cmd
            captured_cmd = cmd
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            return result

        mock_run.side_effect = capture_command

        # Call method that uses subprocess
        manager._count_uncommitted_changes()

        # Verify command is properly escaped/quoted
        assert captured_cmd is not None
        assert isinstance(captured_cmd, list), "Command should be list (prevents injection)"
        assert "rm" not in str(captured_cmd), "Injected command should not appear"

    @patch("subprocess.run")
    def test_security_timeout_enforced_git_status(self, mock_run, tmp_path: Path):
        """Test subprocess timeout prevents hanging."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        # Mock timeout exception (simpler and faster than actual hang)
        mock_run.side_effect = subprocess.TimeoutExpired("git status", 3)

        # Should handle timeout gracefully
        import time
        start = time.time()
        count = manager._count_uncommitted_changes()
        elapsed = time.time() - start

        # Should complete quickly via exception handling (< 1s)
        assert elapsed < 1.0, f"Took {elapsed:.1f}s, should handle timeout quickly"
        assert count == 0  # Should return default value

    @patch("subprocess.run")
    def test_security_timeout_enforced_git_diff(self, mock_run, tmp_path: Path):
        """Test git diff timeout prevents DoS."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        # Mock timeout exception
        mock_run.side_effect = subprocess.TimeoutExpired("git diff", 5)

        # Should handle timeout gracefully
        stats = manager._get_git_diff_stats()

        # Should return None, not crash
        assert stats is None

    def test_security_path_traversal_active_files(self, tmp_path: Path):
        """Test active file detection doesn't access parent directories."""
        manager = ContextManager(tmp_path)

        # Create file outside project root
        parent_dir = tmp_path.parent
        malicious_file = parent_dir / "secret.txt"
        malicious_file.write_text("SECRET DATA")

        # Try to access via relative path
        symlink = tmp_path / "link"
        try:
            symlink.symlink_to(malicious_file)
        except OSError:
            pytest.skip("Symlink creation not supported")

        # Detect active files
        active_files = manager.detect_active_files(minutes=60)

        # Should not include files outside project root
        for file_path in active_files:
            full_path = manager.project_root / file_path
            # Verify all files are within project root
            assert full_path.resolve().is_relative_to(manager.project_root.resolve()), \
                f"File {file_path} is outside project root"

    def test_security_safe_file_stat_operations(self, tmp_path: Path):
        """Test file operations handle permission errors safely."""
        from datetime import datetime as dt
        manager = ContextManager(tmp_path)

        # Create file
        test_file = tmp_path / "test.py"
        test_file.write_text("print('test')")

        # Make file unreadable (Unix only)
        import os
        import stat
        try:
            os.chmod(test_file, 0o000)

            # Should not crash when accessing
            session_start = manager._estimate_session_start()

            # Should handle gracefully (may return None)
            # The important thing is it doesn't raise exception
            assert session_start is None or isinstance(session_start, dt)

            # Restore permissions for cleanup
            os.chmod(test_file, stat.S_IRUSR | stat.S_IWUSR)
        except (OSError, PermissionError):
            pytest.skip("Permission modification not supported")

    @patch("subprocess.run")
    def test_security_malformed_git_output_handling(self, mock_run, tmp_path: Path):
        """Test handling of malicious/malformed git output."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        # Mock malicious git output (attempt to cause buffer overflow or parsing error)
        malicious_outputs = [
            "A" * 100000,  # Very long line
            "\x00" * 1000,  # Null bytes
            "file changed\n" * 10000,  # Repetitive output
            "../../etc/passwd | 100 ++++",  # Path traversal attempt
        ]

        for malicious_output in malicious_outputs:
            mock_result = MagicMock()
            mock_result.returncode = 0
            mock_result.stdout = malicious_output
            mock_run.return_value = mock_result

            # Should not crash
            stats = manager._get_git_diff_stats()

            # Should either parse safely or return None
            assert stats is None or isinstance(stats, dict)

    @patch("subprocess.run")
    def test_security_git_command_not_found_safe(self, mock_run, tmp_path: Path):
        """Test handling when git is not installed."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        # Mock git not found
        mock_run.side_effect = FileNotFoundError("git command not found")

        # Should handle gracefully, not crash
        count = manager._count_uncommitted_changes()
        assert count == 0

        stats = manager._get_git_diff_stats()
        assert stats is None

    def test_security_special_characters_in_filenames(self, tmp_path: Path):
        """Test handling of files with special characters."""
        manager = ContextManager(tmp_path)

        # Create files with special characters
        special_files = [
            "file with spaces.py",
            "file;semicolon.py",
            "file|pipe.py",
            "file&ampersand.py",
            "file'quote.py",
            'file"doublequote.py',
            "file`backtick.py",
            "file$dollar.py",
        ]

        for filename in special_files:
            try:
                test_file = tmp_path / filename
                test_file.write_text(f"# {filename}")
            except (OSError, ValueError):
                # Skip if OS doesn't support this filename
                continue

        # Should handle all files safely
        active_files = manager.detect_active_files(minutes=60)

        # Should not crash and should handle special chars
        assert isinstance(active_files, list)

    def test_security_large_file_count_no_dos(self, tmp_path: Path):
        """Test system handles very large number of files (no DoS)."""
        manager = ContextManager(tmp_path)

        # Create 10,000 files (stress test)
        for i in range(10000):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text("x")

        # Should not cause DoS (memory exhaustion or infinite loop)
        import time
        start = time.time()

        try:
            # Set a hard timeout
            active_files = manager.detect_active_files(minutes=60)
            elapsed = time.time() - start

            # Should complete in reasonable time (< 10s)
            assert elapsed < 10.0, f"Took {elapsed:.1f}s with 10K files"

            # Should have result (may be truncated/filtered)
            assert isinstance(active_files, list)
        except MemoryError:
            pytest.fail("Memory exhaustion with large file count")

    @patch("subprocess.run")
    def test_security_subprocess_shell_injection_prevented(self, mock_run, tmp_path: Path):
        """Test subprocess doesn't use shell=True (prevents injection)."""
        manager = ContextManager(tmp_path)
        (tmp_path / ".git").mkdir()

        # Track subprocess calls
        calls = []
        def track_call(*args, **kwargs):
            calls.append(kwargs)
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            return result

        mock_run.side_effect = track_call

        # Call various git methods
        manager._count_uncommitted_changes()
        manager._get_git_diff_stats()
        manager._get_current_branch()

        # Verify no calls use shell=True
        for call_kwargs in calls:
            assert call_kwargs.get("shell", False) is False, \
                "subprocess should not use shell=True (security risk)"

    def test_security_regex_no_redos_vulnerability(self, tmp_path: Path):
        """Test regex patterns don't have ReDoS vulnerability."""
        manager = ContextManager(tmp_path)

        # Create pathological input for regex (if vulnerable, causes exponential backtracking)
        # Pattern being tested: r"TASK-\d+" in _infer_current_task()
        pathological_branch = "a" * 10000 + "TASK-"

        # Mock git branch
        with patch.object(manager, "_get_current_branch", return_value=pathological_branch):
            import time
            start = time.time()

            # Should complete quickly even with pathological input
            task_id = manager._infer_current_task()
            elapsed = time.time() - start

            # Should not take exponential time
            assert elapsed < 0.1, f"Regex took {elapsed:.3f}s (possible ReDoS)"

            # Should return None (no match) or valid task ID
            assert task_id is None or task_id.startswith("TASK-")
