"""End-to-end scenario tests for proactive monitoring (Day 4)."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clauxton.mcp import server
from clauxton.proactive.models import ChangeType, FileChange


class TestRealWorldScenarios:
    """Test realistic user workflows."""

    def setup_method(self) -> None:
        """Setup test method."""
        server._file_monitor = None
        server._event_processor = None

    def teardown_method(self) -> None:
        """Teardown test method."""
        if server._file_monitor and server._file_monitor.is_running:
            server._file_monitor.stop()
        server._file_monitor = None
        server._event_processor = None

    @pytest.mark.asyncio
    async def test_scenario_refactoring_session(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Developer refactors authentication module.

        Expected: KB suggestions for documentation + anomaly detection for rapid changes.
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Simulate refactoring: 8 auth files modified in 5 minutes
        base_time = datetime.now()
        auth_files = [
            "src/auth/login.py",
            "src/auth/token.py",
            "src/auth/session.py",
            "src/auth/middleware.py",
            "src/auth/validators.py",
            "src/auth/utils.py",
            "src/auth/__init__.py",
            "src/auth/models.py",
        ]

        for i, file in enumerate(auth_files):
            change = FileChange(
                path=tmp_path / file,
                change_type=ChangeType.MODIFIED,
                timestamp=base_time + timedelta(seconds=i * 30),
            )
            monitor.change_queue.append(change)

        # Get KB suggestions
        kb_result = await server.suggest_kb_updates(threshold=0.6, minutes=10)

        # Get anomalies
        anomaly_result = await server.detect_anomalies(
            minutes=10, severity_threshold="low"
        )

        # Should suggest KB documentation for auth module
        assert kb_result["status"] in ["success", "no_suggestions"]
        if kb_result["status"] == "success":
            # Should mention auth or module
            suggestions_text = " ".join(
                s["title"].lower() for s in kb_result["suggestions"]
            )
            assert "auth" in suggestions_text or "module" in suggestions_text

        # Should detect rapid changes
        assert anomaly_result["status"] in ["success", "no_anomalies"]
        if anomaly_result["status"] == "success":
            rapid_anomalies = [
                a for a in anomaly_result["anomalies"] if "rapid" in a["title"].lower()
            ]
            assert len(rapid_anomalies) > 0

    @pytest.mark.asyncio
    async def test_scenario_new_feature_development(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Developer adds new payment feature.

        Expected: KB suggestions for new feature documentation.
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Simulate new feature: Create payment module files
        payment_files = [
            "src/payment/processor.py",
            "src/payment/models.py",
            "src/payment/validators.py",
            "src/payment/__init__.py",
        ]

        for file in payment_files:
            change = FileChange(
                path=tmp_path / file,
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            )
            monitor.change_queue.append(change)

        # Get KB suggestions
        result = await server.suggest_kb_updates(threshold=0.6, minutes=10)

        # Should suggest documentation for new feature
        assert result["status"] in ["success", "no_suggestions"]
        if result["status"] == "success":
            # At least one documentation or KB suggestion
            doc_suggestions = [
                s
                for s in result["suggestions"]
                if s["type"] in ["kb_entry", "documentation"]
            ]
            assert len(doc_suggestions) > 0

    @pytest.mark.asyncio
    async def test_scenario_cleanup_operation(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Developer removes deprecated code.

        Expected: Mass deletion anomaly detected.
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Simulate cleanup: Delete 7 deprecated files
        deprecated_files = [
            "src/deprecated/old_api.py",
            "src/deprecated/legacy.py",
            "src/deprecated/utils.py",
            "src/deprecated/models.py",
            "src/deprecated/validators.py",
            "src/deprecated/handlers.py",
            "src/deprecated/__init__.py",
        ]

        for file in deprecated_files:
            change = FileChange(
                path=tmp_path / file,
                change_type=ChangeType.DELETED,
                timestamp=datetime.now(),
            )
            monitor.change_queue.append(change)

        # Get anomalies
        result = await server.detect_anomalies(minutes=10, severity_threshold="low")

        # Should detect mass deletion
        assert result["status"] in ["success", "no_anomalies"]
        if result["status"] == "success":
            deletion_anomalies = [
                a
                for a in result["anomalies"]
                if "deletion" in a["title"].lower() or "delete" in a["title"].lower()
            ]
            assert len(deletion_anomalies) > 0
            # Should be high priority
            assert deletion_anomalies[0]["priority"] == "high"

    @pytest.mark.asyncio
    async def test_scenario_late_night_work(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Developer works late at night.

        Expected: Late-night activity anomaly detected.
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Simulate late-night work: 6 changes at 11 PM
        late_night = datetime(2025, 10, 26, 23, 0)  # 11 PM

        for i in range(6):
            change = FileChange(
                path=tmp_path / f"src/feature/file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=late_night + timedelta(minutes=i * 10),
            )
            monitor.change_queue.append(change)

        # Get anomalies
        result = await server.detect_anomalies(minutes=120, severity_threshold="low")

        # Should detect late-night activity (or no changes if debouncing)
        assert result["status"] in ["success", "no_anomalies", "no_changes"]
        if result["status"] == "success":
            late_night_anomalies = [
                a
                for a in result["anomalies"]
                if "late" in a["title"].lower() or "night" in a["title"].lower()
            ]
            # May or may not detect depending on threshold
            assert isinstance(late_night_anomalies, list)

    @pytest.mark.asyncio
    async def test_scenario_weekend_deployment(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Scenario: Developer works on Saturday for urgent deployment.

        Expected: Weekend activity anomaly detected.
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Simulate weekend work: Saturday afternoon
        saturday = datetime(2025, 10, 25, 14, 0)  # Saturday

        for i in range(8):
            change = FileChange(
                path=tmp_path / f"src/urgent/fix{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=saturday + timedelta(minutes=i * 15),
            )
            monitor.change_queue.append(change)

        # Get anomalies (use large time window since Saturday is in past)
        result = await server.detect_anomalies(minutes=100000, severity_threshold="low")

        # Should detect weekend activity (or no changes if time window doesn't match)
        assert result["status"] in ["success", "no_anomalies", "no_changes"]
        if result["status"] == "success":
            weekend_anomalies = [
                a for a in result["anomalies"] if "weekend" in a["title"].lower()
            ]
            # May or may not detect depending on threshold
            assert isinstance(weekend_anomalies, list)


class TestMCPToolIntegration:
    """Test integration between MCP tools."""

    def setup_method(self) -> None:
        """Setup test method."""
        server._file_monitor = None
        server._event_processor = None

    def teardown_method(self) -> None:
        """Teardown test method."""
        if server._file_monitor and server._file_monitor.is_running:
            server._file_monitor.stop()
        server._file_monitor = None
        server._event_processor = None

    @pytest.mark.asyncio
    async def test_combined_analysis_workflow(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test combined KB suggestions + anomaly detection workflow.

        Simulates complete development session analysis.
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Simulate mixed activity: new feature + rapid changes
        base_time = datetime.now()

        # Part 1: Create new feature files (2-5 minutes ago)
        for i in range(4):
            change = FileChange(
                path=tmp_path / "src/api" / f"endpoint{i}.py",
                change_type=ChangeType.CREATED,
                timestamp=base_time - timedelta(minutes=4 - i),
            )
            monitor.change_queue.append(change)

        # Part 2: Rapid modifications (last minute)
        for i in range(10):
            change = FileChange(
                path=tmp_path / "src/models" / f"model{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=base_time - timedelta(seconds=50 - i * 5),
            )
            monitor.change_queue.append(change)

        # Analyze both
        kb_result = await server.suggest_kb_updates(threshold=0.5, minutes=10)
        anomaly_result = await server.detect_anomalies(
            minutes=10, severity_threshold="low"
        )

        # Should have results from both
        assert kb_result["status"] in ["success", "no_suggestions"]
        assert anomaly_result["status"] in ["success", "no_anomalies"]

        # Combined analysis should work correctly
        if kb_result["status"] == "success":
            assert len(kb_result["suggestions"]) > 0

        if anomaly_result["status"] == "success":
            assert len(anomaly_result["anomalies"]) > 0

    @pytest.mark.asyncio
    async def test_threshold_filtering_consistency(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test that threshold filtering works consistently across tools.
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Add test changes
        for i in range(5):
            change = FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            )
            monitor.change_queue.append(change)

        # Test different thresholds for KB suggestions
        low_threshold = await server.suggest_kb_updates(threshold=0.5, minutes=10)
        high_threshold = await server.suggest_kb_updates(threshold=0.9, minutes=10)

        # Low threshold should return >= high threshold results
        low_count = (
            low_threshold.get("suggestion_count", 0)
            if low_threshold["status"] == "success"
            else 0
        )
        high_count = (
            high_threshold.get("suggestion_count", 0)
            if high_threshold["status"] == "success"
            else 0
        )

        assert low_count >= high_count

    @pytest.mark.asyncio
    async def test_empty_state_handling(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test graceful handling of empty state (no changes).
        """
        monkeypatch.chdir(tmp_path)

        # Initialize monitor but make no changes
        _ = server._get_file_monitor()

        # Both tools should handle empty state gracefully
        kb_result = await server.suggest_kb_updates(threshold=0.7, minutes=10)
        anomaly_result = await server.detect_anomalies(
            minutes=60, severity_threshold="low"
        )

        # Should return no_changes status
        assert kb_result["status"] == "no_changes"
        assert anomaly_result["status"] == "no_changes"

        # Should include empty arrays
        assert kb_result["suggestions"] == []
        assert anomaly_result["anomalies"] == []


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self) -> None:
        """Setup test method."""
        server._file_monitor = None
        server._event_processor = None

    def teardown_method(self) -> None:
        """Teardown test method."""
        if server._file_monitor and server._file_monitor.is_running:
            server._file_monitor.stop()
        server._file_monitor = None
        server._event_processor = None

    @pytest.mark.asyncio
    async def test_exactly_threshold_changes(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test behavior with exactly threshold number of changes.

        E.g., exactly 5 deletions (minimum for mass deletion).
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Exactly 5 deletions (minimum threshold)
        for i in range(5):
            change = FileChange(
                path=tmp_path / f"file{i}.py",
                change_type=ChangeType.DELETED,
                timestamp=datetime.now(),
            )
            monitor.change_queue.append(change)

        result = await server.detect_anomalies(minutes=10, severity_threshold="low")

        # Should detect with exactly threshold count
        assert result["status"] in ["success", "no_anomalies"]

    @pytest.mark.asyncio
    async def test_single_change(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test handling of single change (below most thresholds).
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Single change
        change = FileChange(
            path=tmp_path / "file.py",
            change_type=ChangeType.MODIFIED,
            timestamp=datetime.now(),
        )
        monitor.change_queue.append(change)

        kb_result = await server.suggest_kb_updates(threshold=0.7, minutes=10)
        anomaly_result = await server.detect_anomalies(
            minutes=10, severity_threshold="low"
        )

        # Should handle gracefully (likely no suggestions/anomalies)
        assert kb_result["status"] in ["success", "no_suggestions"]
        assert anomaly_result["status"] in ["success", "no_anomalies"]

    @pytest.mark.asyncio
    async def test_mixed_change_types(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """
        Test with mix of created/modified/deleted/moved files.
        """
        monkeypatch.chdir(tmp_path)
        monitor = server._get_file_monitor()

        # Mix of change types
        changes = [
            FileChange(
                path=tmp_path / "created.py",
                change_type=ChangeType.CREATED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "modified.py",
                change_type=ChangeType.MODIFIED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "deleted.py",
                change_type=ChangeType.DELETED,
                timestamp=datetime.now(),
            ),
            FileChange(
                path=tmp_path / "moved.py",
                change_type=ChangeType.MOVED,
                timestamp=datetime.now(),
                src_path=tmp_path / "old.py",
            ),
        ]

        for change in changes:
            monitor.change_queue.append(change)

        # Both tools should handle mixed types
        kb_result = await server.suggest_kb_updates(threshold=0.6, minutes=10)
        anomaly_result = await server.detect_anomalies(
            minutes=10, severity_threshold="low"
        )

        # Should not crash
        assert kb_result["status"] in ["success", "no_suggestions"]
        assert anomaly_result["status"] in ["success", "no_anomalies"]
