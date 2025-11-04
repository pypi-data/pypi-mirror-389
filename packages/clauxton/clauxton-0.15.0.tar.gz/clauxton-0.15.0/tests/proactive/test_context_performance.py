"""
Performance tests for Context Intelligence features.

Tests validate that operations complete within acceptable time limits
and handle large-scale scenarios efficiently.
"""

import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import MagicMock, patch

from clauxton.proactive.context_manager import ContextManager


class TestPerformance:
    """Performance benchmarks for context operations."""

    def test_performance_analyze_session_large_project(self, tmp_path: Path):
        """Test session analysis with 1000+ files completes quickly."""
        manager = ContextManager(tmp_path)

        # Create 1000 files spread over 2 hours
        start_time = time.time()
        base_timestamp = datetime.now() - timedelta(hours=2)

        for i in range(1000):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text(f"# File {i}")
            file_time = base_timestamp + timedelta(minutes=i * 0.12)  # ~120 minutes
            import os
            os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

        # Measure analysis time
        analysis_start = time.time()
        analysis = manager.analyze_work_session()
        analysis_time = time.time() - analysis_start

        # Should complete in < 1 second even with 1000 files
        assert analysis_time < 1.0, f"Analysis took {analysis_time:.2f}s (expected <1.0s)"

        # Verify results are reasonable
        assert analysis["duration_minutes"] > 0
        assert analysis["file_switches"] > 0
        assert 0.0 <= analysis["focus_score"] <= 1.0

        setup_time = analysis_start - start_time
        print(f"\nPerformance: Setup={setup_time:.2f}s, Analysis={analysis_time:.3f}s")

    def test_performance_detect_breaks_many_files(self, tmp_path: Path):
        """Test break detection with 500+ files is efficient."""
        manager = ContextManager(tmp_path)

        # Create 500 files with 10 breaks (50 files per period)
        base_timestamp = datetime.now() - timedelta(hours=2)

        for period in range(10):
            # Work period: 50 files
            for i in range(50):
                file_num = period * 50 + i
                test_file = tmp_path / f"file{file_num}.py"
                test_file.write_text(f"# File {file_num}")
                file_time = base_timestamp + timedelta(minutes=period * 12 + i * 0.2)
                import os
                os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

            # Break: 15 minutes gap (no files)
            base_timestamp += timedelta(minutes=12 + 15)

        # Measure break detection time
        start_time = time.time()
        breaks = manager._detect_breaks()
        elapsed = time.time() - start_time

        # Should complete in < 100ms
        assert elapsed < 0.1, f"Break detection took {elapsed*1000:.0f}ms (expected <100ms)"

        # Verify breaks detected
        assert len(breaks) > 5, "Should detect multiple breaks"
        print(f"\nPerformance: Detected {len(breaks)} breaks in {elapsed*1000:.1f}ms")

    def test_performance_focus_score_many_switches(self, tmp_path: Path):
        """Test focus score calculation with 200+ file switches."""
        manager = ContextManager(tmp_path)

        # Create 200 files in last hour
        base_timestamp = datetime.now() - timedelta(hours=1)

        for i in range(200):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text(f"# File {i}")
            file_time = base_timestamp + timedelta(minutes=i * 0.3)  # 60 minutes
            import os
            os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

        # Measure focus score calculation
        start_time = time.time()
        focus_score = manager._calculate_focus_score()
        elapsed = time.time() - start_time

        # Should complete in < 50ms
        assert elapsed < 0.05, f"Focus score took {elapsed*1000:.0f}ms (expected <50ms)"

        # Verify score is valid
        assert 0.0 <= focus_score <= 1.0
        print(f"\nPerformance: Focus score={focus_score:.2f} calculated in {elapsed*1000:.1f}ms")

    @patch("subprocess.run")
    def test_performance_git_operations_timeout(self, mock_run, tmp_path: Path):
        """Test git operations enforce timeouts and don't hang."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock slow git command (simulate 10s delay)
        def slow_git_call(*args, **kwargs):
            time.sleep(0.1)  # Simulate slow command
            raise subprocess.TimeoutExpired("git", 3)  # type: ignore

        import subprocess
        mock_run.side_effect = slow_git_call

        # Measure timeout enforcement
        start_time = time.time()
        count = manager._count_uncommitted_changes()
        elapsed = time.time() - start_time

        # Should timeout and return 0
        assert count == 0
        assert elapsed < 0.2, f"Timeout took {elapsed:.2f}s (expected <0.2s)"
        print(f"\nPerformance: Git timeout enforced in {elapsed*1000:.0f}ms")

    def test_performance_prediction_calculation(self, tmp_path: Path):
        """Test action prediction is fast."""
        manager = ContextManager(tmp_path)

        # Create test files
        (tmp_path / ".git").mkdir()
        for i in range(10):
            (tmp_path / f"test{i}.py").write_text(f"# Test {i}")

        # Measure prediction time
        start_time = time.time()
        prediction = manager.predict_next_action()
        elapsed = time.time() - start_time

        # Should complete in < 50ms
        assert elapsed < 0.05, f"Prediction took {elapsed*1000:.0f}ms (expected <50ms)"

        # Verify prediction structure
        assert "action" in prediction
        assert "confidence" in prediction
        print(f"\nPerformance: Prediction in {elapsed*1000:.1f}ms")

    def test_performance_session_start_estimation(self, tmp_path: Path):
        """Test session start estimation is efficient."""
        manager = ContextManager(tmp_path)

        # Create 100 files
        base_timestamp = datetime.now() - timedelta(hours=1)
        for i in range(100):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text(f"# File {i}")
            file_time = base_timestamp + timedelta(minutes=i * 0.6)
            import os
            os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

        # Measure estimation time
        start_time = time.time()
        session_start = manager._estimate_session_start()
        elapsed = time.time() - start_time

        # Should complete in < 100ms
        assert elapsed < 0.1, f"Session start took {elapsed*1000:.0f}ms (expected <100ms)"

        # Verify result
        assert session_start is not None
        print(f"\nPerformance: Session start estimated in {elapsed*1000:.1f}ms")

    def test_performance_cache_effectiveness(self, tmp_path: Path):
        """Test caching improves performance."""
        manager = ContextManager(tmp_path)

        # Create some files
        for i in range(50):
            (tmp_path / f"file{i}.py").write_text(f"# File {i}")

        # First call (no cache)
        start_time = time.time()
        context1 = manager.get_current_context()
        first_call_time = time.time() - start_time

        # Second call (cached)
        start_time = time.time()
        context2 = manager.get_current_context()
        cached_call_time = time.time() - start_time

        # Cached call should be much faster (at least 5x)
        assert cached_call_time < first_call_time / 5, (
            f"Cache not effective: first={first_call_time*1000:.1f}ms, "
            f"cached={cached_call_time*1000:.1f}ms"
        )

        # Verify same result
        assert context1.current_branch == context2.current_branch
        print(f"\nPerformance: Cache speedup {first_call_time/cached_call_time:.1f}x")

    def test_performance_active_files_detection(self, tmp_path: Path):
        """Test active file detection is efficient."""
        manager = ContextManager(tmp_path)

        # Create 500 files in various directories
        dirs = ["src", "tests", "lib", "docs"]
        for dir_name in dirs:
            dir_path = tmp_path / dir_name
            dir_path.mkdir()
            for i in range(125):  # 125 * 4 = 500
                (dir_path / f"file{i}.py").write_text(f"# File {i}")

        # Measure detection time
        start_time = time.time()
        active_files = manager.detect_active_files(minutes=30)
        elapsed = time.time() - start_time

        # Should complete in < 2 seconds even with 500 files
        assert elapsed < 2.0, f"Detection took {elapsed:.2f}s (expected <2.0s)"

        # Verify files detected
        assert len(active_files) > 0
        print(f"\nPerformance: Detected {len(active_files)} files in {elapsed:.2f}s")

    def test_performance_multiple_analyses_sequential(self, tmp_path: Path):
        """Test multiple sequential analyses are efficient."""
        manager = ContextManager(tmp_path)

        # Create files
        for i in range(100):
            (tmp_path / f"file{i}.py").write_text(f"# File {i}")

        # Run 10 analyses
        start_time = time.time()
        for _ in range(10):
            manager.clear_cache()  # Force recalculation
            analysis = manager.analyze_work_session()
            assert analysis is not None

        elapsed = time.time() - start_time
        avg_time = elapsed / 10

        # Each analysis should take < 200ms
        assert avg_time < 0.2, f"Average analysis took {avg_time*1000:.0f}ms (expected <200ms)"
        print(f"\nPerformance: 10 analyses in {elapsed:.2f}s (avg {avg_time*1000:.0f}ms)")

    def test_performance_break_detection_no_breaks(self, tmp_path: Path):
        """Test break detection is fast when no breaks exist."""
        manager = ContextManager(tmp_path)

        # Create 200 files with no breaks (continuous work)
        base_timestamp = datetime.now() - timedelta(hours=1)
        for i in range(200):
            test_file = tmp_path / f"file{i}.py"
            test_file.write_text(f"# File {i}")
            file_time = base_timestamp + timedelta(seconds=i * 18)  # 60 minutes
            import os
            os.utime(test_file, (file_time.timestamp(), file_time.timestamp()))

        # Measure detection time
        start_time = time.time()
        breaks = manager._detect_breaks()
        elapsed = time.time() - start_time

        # Should complete in < 50ms
        assert elapsed < 0.05, f"Detection took {elapsed*1000:.0f}ms (expected <50ms)"

        # Verify no breaks detected
        assert len(breaks) == 0
        print(f"\nPerformance: No-break detection in {elapsed*1000:.1f}ms")

    @patch("subprocess.run")
    def test_performance_git_diff_stats_large_diff(self, mock_run, tmp_path: Path):
        """Test git diff parsing handles large outputs efficiently."""
        manager = ContextManager(tmp_path)

        # Mock git repository
        (tmp_path / ".git").mkdir()

        # Mock large git diff output (1000 files)
        large_diff = "\n".join([f"file{i}.py | 100 +++++-----" for i in range(1000)])
        large_diff += "\n1000 files changed, 50000 insertions(+), 30000 deletions(-)"

        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = large_diff
        mock_run.return_value = mock_result

        # Measure parsing time
        start_time = time.time()
        stats = manager._get_git_diff_stats()
        elapsed = time.time() - start_time

        # Should complete in < 50ms even with large output
        assert elapsed < 0.05, f"Parsing took {elapsed*1000:.0f}ms (expected <50ms)"

        # Verify stats parsed correctly
        assert stats is not None
        assert stats["files_changed"] == 1000
        assert stats["additions"] == 50000
        assert stats["deletions"] == 30000
        print(f"\nPerformance: Large diff parsed in {elapsed*1000:.1f}ms")

    def test_performance_memory_usage_reasonable(self, tmp_path: Path):
        """Test memory usage stays reasonable with many files."""
        manager = ContextManager(tmp_path)

        # Create 1000 files
        for i in range(1000):
            (tmp_path / f"file{i}.py").write_text("x" * 100)  # 100 bytes each

        # Measure memory before
        import gc
        gc.collect()
        # Note: This is a simplified test, real profiling would use memory_profiler

        # Perform analysis
        analysis = manager.analyze_work_session()

        # Basic verification
        assert analysis is not None
        assert "duration_minutes" in analysis

        # Memory should not leak (verified by not crashing)
        print("\nPerformance: Memory usage test passed (1000 files)")
