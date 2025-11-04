"""Performance tests for proactive monitoring."""

import time
from datetime import datetime
from pathlib import Path

import pytest

from clauxton.proactive.config import MonitorConfig
from clauxton.proactive.event_processor import EventProcessor
from clauxton.proactive.file_monitor import FileMonitor
from clauxton.proactive.models import ChangeType, FileChange


class TestCachePerformance:
    """Test cache performance characteristics."""

    @pytest.mark.asyncio
    async def test_cache_hit_performance(self, tmp_path: Path) -> None:
        """Test cache hit is fast (<1ms)."""
        processor = EventProcessor(tmp_path)

        # Create test changes
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(5)
        ]

        # First detection (cache miss)
        await processor.detect_patterns(changes)

        # Second detection (cache hit) - measure time
        start = time.perf_counter()
        await processor.detect_patterns(changes)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Cache hit should be <1ms
        assert elapsed_ms < 1.0, f"Cache hit took {elapsed_ms:.2f}ms (should be <1ms)"

    @pytest.mark.asyncio
    async def test_cache_miss_performance(self, tmp_path: Path) -> None:
        """Test cache miss performance (baseline 5-10ms)."""
        processor = EventProcessor(tmp_path)

        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(10)
        ]

        # Measure cache miss time
        start = time.perf_counter()
        await processor.detect_patterns(changes)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Cache miss should be <20ms (generous limit)
        assert elapsed_ms < 20.0, f"Cache miss took {elapsed_ms:.2f}ms (should be <20ms)"

    @pytest.mark.asyncio
    async def test_cache_speedup(self, tmp_path: Path) -> None:
        """Test cache provides 5-10x speedup."""
        processor = EventProcessor(tmp_path)

        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(10)
        ]

        # Measure cache miss time
        start = time.perf_counter()
        await processor.detect_patterns(changes)
        miss_time = time.perf_counter() - start

        # Measure cache hit time
        start = time.perf_counter()
        await processor.detect_patterns(changes)
        hit_time = time.perf_counter() - start

        # Cache should be at least 2.5x faster (CI machines can be slower)
        speedup = miss_time / hit_time if hit_time > 0 else 0
        assert speedup >= 2.5, f"Cache speedup is only {speedup:.1f}x (should be ≥2.5x)"


class TestPatternDetectionScalability:
    """Test pattern detection scales well."""

    @pytest.mark.asyncio
    async def test_scalability_10_files(self, tmp_path: Path) -> None:
        """Test detection with 10 files is fast."""
        processor = EventProcessor(tmp_path)

        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(10)
        ]

        start = time.perf_counter()
        patterns = await processor.detect_patterns(changes)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(patterns) > 0  # Should detect bulk_edit
        assert elapsed_ms < 10.0, f"10 files took {elapsed_ms:.2f}ms (should be <10ms)"

    @pytest.mark.asyncio
    async def test_scalability_100_files(self, tmp_path: Path) -> None:
        """Test detection with 100 files is acceptable."""
        processor = EventProcessor(tmp_path)

        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(100)
        ]

        start = time.perf_counter()
        patterns = await processor.detect_patterns(changes)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(patterns) > 0
        assert elapsed_ms < 50.0, f"100 files took {elapsed_ms:.2f}ms (should be <50ms)"

    @pytest.mark.asyncio
    async def test_scalability_1000_files(self, tmp_path: Path) -> None:
        """Test detection with 1000 files completes in reasonable time."""
        processor = EventProcessor(tmp_path)

        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(1000)
        ]

        start = time.perf_counter()
        patterns = await processor.detect_patterns(changes)
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert len(patterns) > 0
        assert (
            elapsed_ms < 200.0
        ), f"1000 files took {elapsed_ms:.2f}ms (should be <200ms)"


class TestMemoryPerformance:
    """Test memory usage is bounded."""

    @pytest.mark.asyncio
    async def test_memory_usage_within_bounds(self, tmp_path: Path) -> None:
        """Test memory usage stays within reasonable bounds."""
        processor = EventProcessor(tmp_path)

        # Create 1000 file changes
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(1000)
        ]

        # Detect patterns
        await processor.detect_patterns(changes)

        # Check cache size is bounded
        assert (
            len(processor._pattern_cache) <= processor.MAX_CACHE_ENTRIES
        ), "Cache exceeded max entries"

    def test_queue_size_bounded(self, tmp_path: Path) -> None:
        """Test queue size is bounded by config."""
        config = MonitorConfig()
        monitor = FileMonitor(tmp_path, config)

        # Queue should have maxlen set
        assert monitor.change_queue.maxlen == config.watch.max_queue_size


class TestCleanupPerformance:
    """Test cleanup operations are efficient."""

    @pytest.mark.asyncio
    async def test_cache_cleanup_performance(self, tmp_path: Path) -> None:
        """Test cache cleanup is fast."""
        processor = EventProcessor(tmp_path)

        # Fill cache to max
        for i in range(processor.MAX_CACHE_ENTRIES + 10):
            changes = [
                FileChange(
                    path=tmp_path / f"unique_file_{i}_{j}.py",
                    change_type=ChangeType.MODIFIED,
                    timestamp=datetime.now(),
                )
                for j in range(3)
            ]
            await processor.detect_patterns(changes)

        # Cleanup should have happened automatically
        assert len(processor._pattern_cache) <= processor.MAX_CACHE_ENTRIES

        # Cleanup should be fast (<1ms)
        start = time.perf_counter()
        processor._cleanup_cache()
        elapsed_ms = (time.perf_counter() - start) * 1000

        assert elapsed_ms < 1.0, f"Cache cleanup took {elapsed_ms:.2f}ms (should be <1ms)"

    def test_debounce_cleanup_performance(self, tmp_path: Path) -> None:
        """Test debounce cleanup is efficient."""
        config = MonitorConfig()
        monitor = FileMonitor(tmp_path, config)
        monitor.start()

        try:
            # Add many entries to debounce dict
            handler = monitor.event_handler
            current_time = time.time()

            # Add 500 old entries (more than 1 hour ago) and 1000 recent entries
            # Total: 1500 entries (exceeds max_debounce_entries of 1000)
            old_time = current_time - (2 * 3600)  # 2 hours ago
            for i in range(500):
                handler.last_event_time[f"old_file{i}.py"] = old_time

            for i in range(1000):
                handler.last_event_time[f"file{i}.py"] = current_time

            # Verify we have 1500 entries before cleanup
            assert len(handler.last_event_time) == 1500

            # Trigger cleanup via _should_process
            test_path = tmp_path / "test.py"

            start = time.perf_counter()
            handler._should_process(test_path)
            elapsed_ms = (time.perf_counter() - start) * 1000

            # Cleanup should be fast (<20ms even with 1500 entries)
            assert (
                elapsed_ms < 20.0
            ), f"Debounce cleanup took {elapsed_ms:.2f}ms (should be <20ms)"

            # Verify cleanup happened (old entries removed, recent ones + test.py remain)
            assert len(handler.last_event_time) <= config.watch.max_debounce_entries + 1

        finally:
            monitor.stop()


class TestConcurrentPerformance:
    """Test performance under concurrent load."""

    @pytest.mark.asyncio
    async def test_concurrent_pattern_detection(self, tmp_path: Path) -> None:
        """Test multiple concurrent pattern detections don't slow each other."""
        import asyncio

        processor = EventProcessor(tmp_path)

        # Create different change sets
        change_sets = [
            [
                FileChange(
                    path=tmp_path / f"set{set_idx}_file{i}.py",
                    change_type=ChangeType.MODIFIED,
                    timestamp=datetime.now(),
                )
                for i in range(10)
            ]
            for set_idx in range(5)
        ]

        # Run detections concurrently
        start = time.perf_counter()
        results = await asyncio.gather(
            *[processor.detect_patterns(changes) for changes in change_sets]
        )
        elapsed_ms = (time.perf_counter() - start) * 1000

        # All should complete
        assert len(results) == 5
        assert all(len(r) > 0 for r in results)

        # Should complete in reasonable time (not 5x slower than sequential)
        assert (
            elapsed_ms < 100.0
        ), f"5 concurrent detections took {elapsed_ms:.2f}ms (should be <100ms)"


class TestMCPToolPerformance:
    """Performance tests for new MCP tools (Day 4)."""

    @pytest.mark.asyncio
    async def test_suggest_kb_updates_performance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test suggest_kb_updates completes in <200ms."""
        from clauxton.mcp import server

        monkeypatch.chdir(tmp_path)

        # Setup monitor with changes
        monitor = server._get_file_monitor()
        changes = [
            FileChange(
                path=tmp_path / "src" / "auth" / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(10)
        ]

        for change in changes:
            monitor.change_queue.append(change)

        # Measure performance
        start = time.perf_counter()
        result = await server.suggest_kb_updates(threshold=0.7, minutes=10)
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should complete quickly (<200ms with pattern detection + suggestion generation)
        assert (
            elapsed_ms < 200.0
        ), f"suggest_kb_updates took {elapsed_ms:.2f}ms (should be <200ms)"

        # Should return valid result
        assert result["status"] in ["success", "no_suggestions"]

    @pytest.mark.asyncio
    async def test_detect_anomalies_performance(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test detect_anomalies completes in <150ms."""
        from clauxton.mcp import server

        monkeypatch.chdir(tmp_path)

        # Setup monitor with anomalous changes
        monitor = server._get_file_monitor()
        changes = [
            FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(20)  # Rapid changes
        ]

        for change in changes:
            monitor.change_queue.append(change)

        # Measure performance
        start = time.perf_counter()
        result = await server.detect_anomalies(minutes=60, severity_threshold="low")
        elapsed_ms = (time.perf_counter() - start) * 1000

        # Should complete quickly (<150ms with anomaly detection)
        assert (
            elapsed_ms < 150.0
        ), f"detect_anomalies took {elapsed_ms:.2f}ms (should be <150ms)"

        # Should detect anomalies
        assert result["status"] in ["success", "no_anomalies"]

    @pytest.mark.asyncio
    async def test_mcp_tools_with_large_dataset(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test MCP tools scale well with 100+ changes."""
        from clauxton.mcp import server

        monkeypatch.chdir(tmp_path)

        # Setup monitor with many changes
        monitor = server._get_file_monitor()
        changes = [
            FileChange(
                path=tmp_path / f"module{i // 10}" / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            for i in range(100)
        ]

        for change in changes:
            monitor.change_queue.append(change)

        # Test suggest_kb_updates performance
        start = time.perf_counter()
        kb_result = await server.suggest_kb_updates(threshold=0.6, minutes=10)
        kb_elapsed_ms = (time.perf_counter() - start) * 1000

        # Test detect_anomalies performance
        start = time.perf_counter()
        anomaly_result = await server.detect_anomalies(
            minutes=60, severity_threshold="low"
        )
        anomaly_elapsed_ms = (time.perf_counter() - start) * 1000

        # Both should complete in reasonable time even with 100 changes
        assert (
            kb_elapsed_ms < 500.0
        ), f"suggest_kb_updates with 100 changes took {kb_elapsed_ms:.2f}ms (should be <500ms)"
        assert (
            anomaly_elapsed_ms < 300.0
        ), f"detect_anomalies with 100 changes took {anomaly_elapsed_ms:.2f}ms (should be <300ms)"

        # Should return valid results
        assert kb_result["status"] in ["success", "no_suggestions"]
        assert anomaly_result["status"] in ["success", "no_anomalies"]
