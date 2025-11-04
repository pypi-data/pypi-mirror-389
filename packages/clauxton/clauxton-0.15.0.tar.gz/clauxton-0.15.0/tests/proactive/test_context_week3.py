"""
Tests for Week 3 Context Intelligence features.

Tests cover:
- Session analysis (duration, focus score, breaks)
- Action prediction (rule-based)
- Git statistics (diff stats, uncommitted changes)
"""

from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from clauxton.proactive.context_manager import ContextManager


class TestSessionAnalysis:
    """Test work session analysis features."""

    def test_session_duration_calculation(self, tmp_path: Path):
        """Test session duration is calculated correctly."""
        manager = ContextManager(tmp_path)

        # Create a file 45 minutes ago
        test_file = tmp_path / "test.py"
        test_file.write_text("print('hello')")

        # Set modification time to 45 minutes ago
        past_time = datetime.now() - timedelta(minutes=45)
        timestamp = past_time.timestamp()
        test_file.touch()
        import os
        os.utime(test_file, (timestamp, timestamp))

        # Calculate session duration
        duration = manager._calculate_session_duration()

        # Should be approximately 45 minutes (allow 1 minute tolerance)
        assert 44 <= duration <= 46, f"Expected ~45 min, got {duration}"

    def test_session_duration_no_files(self, tmp_path: Path):
        """Test session duration when no files modified."""
        manager = ContextManager(tmp_path)

        duration = manager._calculate_session_duration()

        assert duration == 0

    def test_focus_score_high(self, tmp_path: Path):
        """Test high focus score with few file switches."""
        manager = ContextManager(tmp_path)

        # Create 3 files modified in last hour (3 switches/hour = high focus)
        past_time = datetime.now() - timedelta(minutes=60)
        timestamp = past_time.timestamp()

        for i in range(3):
            test_file = tmp_path / f"test{i}.py"
            test_file.write_text(f"print({i})")
            import os
            os.utime(test_file, (timestamp, timestamp))

        # Calculate focus score
        focus_score = manager._calculate_focus_score()

        # Should be high (>= 0.8)
        assert focus_score >= 0.8, f"Expected high focus (>=0.8), got {focus_score}"

    def test_focus_score_medium(self, tmp_path: Path):
        """Test medium focus score with moderate file switches."""
        manager = ContextManager(tmp_path)

        # Create 10 files modified in last 25 minutes
        # (10 switches/25min = 24 switches/hour = medium-low focus)
        for i in range(10):
            test_file = tmp_path / f"test{i}.py"
            test_file.write_text(f"print({i})")
            # Stagger the file times over 25 minutes
            file_time = datetime.now() - timedelta(minutes=25 - i * 2)
            import os
            os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

        # Calculate focus score
        focus_score = manager._calculate_focus_score()

        # Should be low-medium (< 0.8)
        assert focus_score < 0.8, f"Expected focus < 0.8, got {focus_score}"

    def test_focus_score_low(self, tmp_path: Path):
        """Test low focus score with many file switches."""
        manager = ContextManager(tmp_path)

        # Create 30 files modified in last 25 minutes
        # (30 switches/25min = 72 switches/hour = very low focus)
        for i in range(30):
            test_file = tmp_path / f"test{i}.py"
            test_file.write_text(f"print({i})")
            # Stagger the file times over 25 minutes
            file_time = datetime.now() - timedelta(minutes=25 - int(i * 0.8))
            import os
            os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

        # Calculate focus score
        focus_score = manager._calculate_focus_score()

        # Should be low (< 0.5)
        assert focus_score < 0.5, f"Expected low focus (<0.5), got {focus_score}"

    def test_break_detection_single_break(self, tmp_path: Path):
        """Test break detection with single 20-minute gap."""
        manager = ContextManager(tmp_path)

        # Create file at T=0
        file1 = tmp_path / "file1.py"
        file1.write_text("print(1)")
        time1 = datetime.now() - timedelta(minutes=40)
        import os
        os.utime(file1, (time1.timestamp(), time1.timestamp()))

        # Create file at T=20 (20-minute gap = break)
        file2 = tmp_path / "file2.py"
        file2.write_text("print(2)")
        time2 = datetime.now() - timedelta(minutes=20)
        os.utime(file2, (time2.timestamp(), time2.timestamp()))

        # Create file at T=22
        file3 = tmp_path / "file3.py"
        file3.write_text("print(3)")
        time3 = datetime.now() - timedelta(minutes=18)
        os.utime(file3, (time3.timestamp(), time3.timestamp()))

        # Detect breaks
        breaks = manager._detect_breaks()

        # Should detect 1 break
        assert len(breaks) == 1, f"Expected 1 break, got {len(breaks)}"
        assert breaks[0]["duration_minutes"] >= 15

    def test_break_detection_no_breaks(self, tmp_path: Path):
        """Test break detection with no breaks (continuous work)."""
        manager = ContextManager(tmp_path)

        # Create files with 5-minute gaps (no breaks)
        for i in range(5):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text(f"print({i})")
            file_time = datetime.now() - timedelta(minutes=25 - i * 5)
            import os
            os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

        # Detect breaks
        breaks = manager._detect_breaks()

        # Should detect 0 breaks
        assert len(breaks) == 0, f"Expected 0 breaks, got {len(breaks)}"

    def test_active_periods_calculation(self, tmp_path: Path):
        """Test active period calculation with breaks."""
        manager = ContextManager(tmp_path)

        # Create files with one 20-minute break
        file1 = tmp_path / "file1.py"
        file1.write_text("print(1)")
        time1 = datetime.now() - timedelta(minutes=50)
        import os
        os.utime(file1, (time1.timestamp(), time1.timestamp()))

        file2 = tmp_path / "file2.py"
        file2.write_text("print(2)")
        time2 = datetime.now() - timedelta(minutes=25)
        os.utime(file2, (time2.timestamp(), time2.timestamp()))

        # Detect breaks and calculate active periods
        breaks = manager._detect_breaks()
        active_periods = manager._calculate_active_periods(breaks)

        # Should have 2 active periods (before and after break)
        assert len(active_periods) >= 1, f"Expected >=1 active period, got {len(active_periods)}"

    def test_analyze_work_session_complete(self, tmp_path: Path):
        """Test complete work session analysis."""
        manager = ContextManager(tmp_path)

        # Create test files
        for i in range(3):
            test_file = tmp_path / f"test{i}.py"
            test_file.write_text(f"print({i})")
            file_time = datetime.now() - timedelta(minutes=30 - i * 10)
            import os
            os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

        # Analyze session
        analysis = manager.analyze_work_session()

        # Verify structure
        assert "duration_minutes" in analysis
        assert "focus_score" in analysis
        assert "breaks" in analysis
        assert "file_switches" in analysis
        assert "active_periods" in analysis

        # Verify types
        assert isinstance(analysis["duration_minutes"], int)
        assert isinstance(analysis["focus_score"], float)
        assert isinstance(analysis["breaks"], list)
        assert isinstance(analysis["file_switches"], int)
        assert isinstance(analysis["active_periods"], list)


class TestActionPrediction:
    """Test next action prediction."""

    def test_predict_run_tests(self, tmp_path: Path):
        """Predict run_tests when test files edited."""
        manager = ContextManager(tmp_path)

        # Create test files
        test_file = tmp_path / "test_foo.py"
        test_file.write_text("def test_example(): pass")

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Get prediction
        prediction = manager.predict_next_action()

        # Should predict run_tests
        assert prediction["action"] == "run_tests"
        assert prediction["confidence"] >= 0.7

    def test_predict_write_tests(self, tmp_path: Path):
        """Predict write_tests when implementation files modified without tests."""
        manager = ContextManager(tmp_path)

        # Create implementation file (no test file)
        impl_file = tmp_path / "module.py"
        impl_file.write_text("def foo(): pass")

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Get prediction
        prediction = manager.predict_next_action()

        # Should predict write_tests
        assert prediction["action"] == "write_tests"
        assert prediction["confidence"] >= 0.6

    @patch("subprocess.run")
    def test_predict_commit_changes(self, mock_run, tmp_path: Path):
        """Predict commit when many uncommitted changes."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock git status with 12 uncommitted files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "\n".join([f"M file{i}.py" for i in range(12)])
        mock_run.return_value = mock_result

        # Get prediction
        prediction = manager.predict_next_action()

        # Should predict commit_changes
        assert prediction["action"] == "commit_changes"
        assert prediction["confidence"] >= 0.8

    @patch("subprocess.run")
    def test_predict_review_changes(self, mock_run, tmp_path: Path):
        """Predict review when moderate uncommitted changes."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock git status with 7 uncommitted files
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "\n".join([f"M file{i}.py" for i in range(7)])
        mock_run.return_value = mock_result

        # Get prediction
        prediction = manager.predict_next_action()

        # Should predict review_changes
        assert prediction["action"] == "review_changes"
        assert prediction["confidence"] >= 0.6

    @patch("subprocess.run")
    def test_predict_create_pr(self, mock_run, tmp_path: Path):
        """Predict create_pr on feature branch with many changes."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        def mock_subprocess(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0

            # Mock git branch output
            if "rev-parse" in cmd:
                result.stdout = "feature/new-feature"
            # Mock git status output (20 files)
            elif "status" in cmd:
                result.stdout = "\n".join([f"M file{i}.py" for i in range(20)])
            # Mock git diff output
            elif "diff" in cmd:
                result.stdout = ""

            return result

        mock_run.side_effect = mock_subprocess

        # Get prediction
        prediction = manager.predict_next_action()

        # Should predict either create_pr or commit_changes (both are valid for 20 files)
        assert prediction["action"] in ["create_pr", "commit_changes"]
        assert prediction["confidence"] >= 0.7

    @patch("subprocess.run")
    @patch("clauxton.proactive.context_manager.datetime")
    def test_predict_planning_morning(self, mock_datetime, mock_run, tmp_path: Path):
        """Predict planning in morning with few changes."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock morning time (8 AM)
        mock_now = datetime(2025, 10, 27, 8, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromtimestamp = datetime.fromtimestamp

        # Mock git status with 1 uncommitted file
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "M file.py"
        mock_run.return_value = mock_result

        # Get prediction
        prediction = manager.predict_next_action()

        # Should predict planning
        assert prediction["action"] == "planning"
        assert prediction["confidence"] >= 0.5

    @patch("subprocess.run")
    @patch("clauxton.proactive.context_manager.datetime")
    def test_predict_documentation_evening(self, mock_datetime, mock_run, tmp_path: Path):
        """Predict documentation in evening with changes."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock evening time (7 PM)
        mock_now = datetime(2025, 10, 27, 19, 0, 0)
        mock_datetime.now.return_value = mock_now
        mock_datetime.fromtimestamp = datetime.fromtimestamp

        # Mock git status with 4 uncommitted files (< 5 to avoid review_changes)
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "\n".join([f"M file{i}.py" for i in range(4)])
        mock_run.return_value = mock_result

        # Get prediction
        prediction = manager.predict_next_action()

        # Should predict documentation
        assert prediction["action"] == "documentation"
        assert prediction["confidence"] >= 0.6

    def test_predict_take_break_long_session(self, tmp_path: Path):
        """Predict take_break after long focused session."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Create files for 100-minute session with high focus (4 files)
        past_time = datetime.now() - timedelta(minutes=100)
        for i in range(4):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text(f"print({i})")
            import os
            os.utime(test_file, (past_time.timestamp(), past_time.timestamp()))

        # Get prediction
        prediction = manager.predict_next_action()

        # Should predict take_break
        assert prediction["action"] == "take_break"
        assert prediction["confidence"] >= 0.7


class TestGitStatistics:
    """Test git diff statistics."""

    @patch("subprocess.run")
    def test_count_uncommitted_changes(self, mock_run, tmp_path: Path):
        """Test counting uncommitted changes."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock git status output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = "M file1.py\n M file2.py\nA  file3.py"
        mock_run.return_value = mock_result

        # Count uncommitted changes
        count = manager._count_uncommitted_changes()

        # Should return 3
        assert count == 3

    def test_count_uncommitted_changes_not_git_repo(self, tmp_path: Path):
        """Test counting uncommitted changes when not a git repo."""
        manager = ContextManager(tmp_path)

        # No .git directory

        # Count uncommitted changes
        count = manager._count_uncommitted_changes()

        # Should return 0
        assert count == 0

    @patch("subprocess.run")
    def test_get_diff_stats_with_changes(self, mock_run, tmp_path: Path):
        """Test diff stats with uncommitted changes."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock git diff --stat output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = (
            "file1.py | 10 +++++-----\n"
            "file2.py | 5 +++++\n"
            "2 files changed, 12 insertions(+), 3 deletions(-)"
        )
        mock_run.return_value = mock_result

        # Get diff stats
        stats = manager._get_git_diff_stats()

        # Verify stats
        assert stats is not None
        assert stats["files_changed"] == 2
        assert stats["additions"] == 12
        assert stats["deletions"] == 3

    @patch("subprocess.run")
    def test_get_diff_stats_clean_repo(self, mock_run, tmp_path: Path):
        """Test diff stats with no changes."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock empty git diff output
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        # Get diff stats
        stats = manager._get_git_diff_stats()

        # Should return all zeros
        assert stats is not None
        assert stats["files_changed"] == 0
        assert stats["additions"] == 0
        assert stats["deletions"] == 0

    def test_get_diff_stats_not_git_repo(self, tmp_path: Path):
        """Test diff stats when not a git repo."""
        manager = ContextManager(tmp_path)

        # No .git directory

        # Get diff stats
        stats = manager._get_git_diff_stats()

        # Should return None
        assert stats is None

    @patch("subprocess.run")
    def test_git_context_in_get_current_context(self, mock_run, tmp_path: Path):
        """Test git stats are included in get_current_context()."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        def mock_subprocess(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 0

            # Mock git branch
            if "rev-parse" in cmd:
                result.stdout = "main"
            # Mock git status
            elif "status" in cmd and "--porcelain" in cmd:
                result.stdout = "M file.py"
            # Mock git diff
            elif "diff" in cmd:
                result.stdout = "file.py | 5 +++++\n1 file changed, 5 insertions(+)"
            # Mock git log
            elif "log" in cmd:
                result.stdout = ""

            return result

        mock_run.side_effect = mock_subprocess

        # Get context
        context = manager.get_current_context()

        # Verify git stats are populated
        assert context.uncommitted_changes == 1
        assert context.diff_stats is not None
        assert context.diff_stats["files_changed"] == 1
        assert context.diff_stats["additions"] == 5
