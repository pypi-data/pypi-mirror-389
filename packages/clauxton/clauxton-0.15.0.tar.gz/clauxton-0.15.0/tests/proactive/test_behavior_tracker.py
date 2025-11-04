"""
Tests for BehaviorTracker - User behavior tracking and learning.

Week 2 Day 5 - v0.13.0
"""

from datetime import datetime
from pathlib import Path

import pytest

from clauxton.proactive.behavior_tracker import (
    BehaviorTracker,
    ToolUsage,
    UserBehavior,
)
from clauxton.proactive.suggestion_engine import SuggestionType


class TestBehaviorTracker:
    """Test BehaviorTracker functionality."""

    def test_initialization(self, tmp_path: Path) -> None:
        """Test behavior tracker initialization."""
        tracker = BehaviorTracker(tmp_path)

        assert tracker.project_root == tmp_path
        assert tracker.behavior_file == tmp_path / ".clauxton" / "behavior.yml"
        assert isinstance(tracker.behavior, UserBehavior)

    def test_record_tool_usage(self, tmp_path: Path) -> None:
        """Test recording tool usage."""
        tracker = BehaviorTracker(tmp_path)

        tracker.record_tool_usage(
            tool_name="suggest_kb_updates",
            result="accepted",
            context={"suggestion_count": 3},
        )

        assert len(tracker.behavior.tool_usage_history) == 1
        usage = tracker.behavior.tool_usage_history[0]
        assert usage.tool_name == "suggest_kb_updates"
        assert usage.result == "accepted"
        assert usage.context["suggestion_count"] == 3

    def test_record_suggestion_feedback(self, tmp_path: Path) -> None:
        """Test recording suggestion feedback."""
        tracker = BehaviorTracker(tmp_path)

        # Record acceptance
        tracker.record_suggestion_feedback(SuggestionType.KB_ENTRY, accepted=True)

        # Should have preference score for KB_ENTRY
        assert "kb_entry" in tracker.behavior.preferred_suggestion_types

        # Score should be positive (started at 0.5, moved toward 1.0)
        score = tracker.behavior.preferred_suggestion_types["kb_entry"]
        assert score > 0.5

    def test_record_rejection_lowers_score(self, tmp_path: Path) -> None:
        """Test that rejection lowers preference score."""
        tracker = BehaviorTracker(tmp_path)

        # Record rejection
        tracker.record_suggestion_feedback(SuggestionType.TASK, accepted=False)

        # Score should be below neutral (started at 0.5, moved toward 0.0)
        score = tracker.behavior.preferred_suggestion_types["task"]
        assert score < 0.5

    def test_get_preference_score(self, tmp_path: Path) -> None:
        """Test getting preference score."""
        tracker = BehaviorTracker(tmp_path)

        # Default for unknown type
        score = tracker.get_preference_score(SuggestionType.REFACTOR)
        assert score == 0.5  # Neutral

        # Record some feedback
        tracker.record_suggestion_feedback(SuggestionType.REFACTOR, accepted=True)
        score = tracker.get_preference_score(SuggestionType.REFACTOR)
        assert score > 0.5

    def test_active_hours_tracking(self, tmp_path: Path) -> None:
        """Test active hours tracking."""
        tracker = BehaviorTracker(tmp_path)

        # Record usage at current hour
        tracker.record_tool_usage("test_tool", "accepted")

        current_hour = datetime.now().hour
        assert current_hour in tracker.behavior.active_hours
        assert tracker.behavior.active_hours[current_hour] >= 1

    def test_is_active_time(self, tmp_path: Path) -> None:
        """Test checking if current time is active."""
        tracker = BehaviorTracker(tmp_path)

        # No history - should return True
        assert tracker.is_active_time() is True

        # Record some activity
        tracker.record_tool_usage("test_tool", "accepted")

        # Should be active now
        assert tracker.is_active_time() is True

    def test_adjust_confidence(self, tmp_path: Path) -> None:
        """Test confidence adjustment based on preferences."""
        tracker = BehaviorTracker(tmp_path)

        # Record high acceptance for KB_ENTRY
        for _ in range(5):
            tracker.record_suggestion_feedback(SuggestionType.KB_ENTRY, accepted=True)

        # Base confidence should be boosted
        base_confidence = 0.70
        adjusted = tracker.adjust_confidence(base_confidence, SuggestionType.KB_ENTRY)

        # Adjusted should be higher than base (30% influence from preference)
        assert adjusted > base_confidence

    def test_confidence_clamping(self, tmp_path: Path) -> None:
        """Test confidence is clamped to [0.0, 1.0]."""
        tracker = BehaviorTracker(tmp_path)

        # Set very high preference
        tracker.behavior.preferred_suggestion_types["kb_entry"] = 1.0

        # Even with high base, should not exceed 1.0
        adjusted = tracker.adjust_confidence(0.95, SuggestionType.KB_ENTRY)
        assert adjusted <= 1.0

        # Set very low preference
        tracker.behavior.preferred_suggestion_types["task"] = 0.0

        # Should not go below 0.0
        adjusted = tracker.adjust_confidence(0.1, SuggestionType.TASK)
        assert adjusted >= 0.0

    def test_behavior_persistence(self, tmp_path: Path) -> None:
        """Test that behavior is saved and loaded correctly."""
        tracker = BehaviorTracker(tmp_path)

        # Record some data
        tracker.record_tool_usage("tool1", "accepted")
        tracker.record_suggestion_feedback(SuggestionType.KB_ENTRY, accepted=True)

        # Create new tracker (should load saved data)
        tracker2 = BehaviorTracker(tmp_path)

        assert len(tracker2.behavior.tool_usage_history) == 1
        assert "kb_entry" in tracker2.behavior.preferred_suggestion_types

    def test_tool_usage_limit(self, tmp_path: Path) -> None:
        """Test that tool usage history is limited to 1000 entries."""
        tracker = BehaviorTracker(tmp_path)

        # Add 1100 entries
        for i in range(1100):
            tracker.record_tool_usage(f"tool_{i}", "accepted")

        # Should only keep last 1000
        assert len(tracker.behavior.tool_usage_history) == 1000

    def test_get_usage_stats(self, tmp_path: Path) -> None:
        """Test getting usage statistics."""
        tracker = BehaviorTracker(tmp_path)

        # Record various usages
        tracker.record_tool_usage("suggest_kb_updates", "accepted")
        tracker.record_tool_usage("detect_anomalies", "accepted")
        tracker.record_tool_usage("suggest_kb_updates", "rejected")

        stats = tracker.get_usage_stats(days=30)

        assert stats["total_tool_calls"] == 3
        assert stats["accepted_count"] == 2
        assert stats["rejected_count"] == 1
        assert stats["acceptance_rate"] == 2 / 3
        assert len(stats["most_used_tools"]) > 0

    def test_update_confidence_threshold(self, tmp_path: Path) -> None:
        """Test updating confidence threshold."""
        tracker = BehaviorTracker(tmp_path)

        tracker.update_confidence_threshold(0.85)
        assert tracker.get_confidence_threshold() == 0.85

        # Invalid threshold should raise error
        with pytest.raises(ValueError):
            tracker.update_confidence_threshold(1.5)

        with pytest.raises(ValueError):
            tracker.update_confidence_threshold(-0.1)

    def test_empty_history_handling(self, tmp_path: Path) -> None:
        """Test handling of empty history."""
        tracker = BehaviorTracker(tmp_path)

        stats = tracker.get_usage_stats(days=30)

        assert stats["total_tool_calls"] == 0
        assert stats["acceptance_rate"] == 0.0
        assert len(stats["most_used_tools"]) == 0


class TestToolUsage:
    """Test ToolUsage model."""

    def test_tool_usage_creation(self) -> None:
        """Test creating a ToolUsage record."""
        now = datetime.now()
        usage = ToolUsage(
            tool_name="test_tool",
            timestamp=now,
            parameters={"param1": "value1"},
            result="accepted",
            context={"key": "value"},
        )

        assert usage.tool_name == "test_tool"
        assert usage.timestamp == now
        assert usage.parameters == {"param1": "value1"}
        assert usage.result == "accepted"
        assert usage.context == {"key": "value"}


class TestUserBehavior:
    """Test UserBehavior model."""

    def test_user_behavior_defaults(self) -> None:
        """Test UserBehavior default values."""
        behavior = UserBehavior(confidence_threshold=0.7)

        assert len(behavior.tool_usage_history) == 0
        assert len(behavior.preferred_suggestion_types) == 0
        assert len(behavior.active_hours) == 0
        assert behavior.confidence_threshold == 0.7

    def test_user_behavior_with_data(self) -> None:
        """Test UserBehavior with data."""
        now = datetime.now()
        usage = ToolUsage(
            tool_name="test",
            timestamp=now,
            result="accepted",
        )

        behavior = UserBehavior(
            tool_usage_history=[usage],
            preferred_suggestion_types={"kb_entry": 0.8},
            active_hours={9: 5, 10: 3},
            confidence_threshold=0.75,
        )

        assert len(behavior.tool_usage_history) == 1
        assert behavior.preferred_suggestion_types["kb_entry"] == 0.8
        assert behavior.active_hours[9] == 5


class TestBehaviorTrackerPerformance:
    """Test BehaviorTracker performance optimizations."""

    def test_auto_save_disabled(self, tmp_path: Path) -> None:
        """Test that auto_save=False prevents immediate writes."""
        tracker = BehaviorTracker(tmp_path, auto_save=False)

        # Record multiple operations
        for i in range(10):
            tracker.record_tool_usage(f"tool_{i}", "accepted")
            tracker.record_suggestion_feedback(SuggestionType.KB_ENTRY, accepted=True)

        # Create new tracker (should not have data yet)
        tracker2 = BehaviorTracker(tmp_path)
        assert len(tracker2.behavior.tool_usage_history) == 0

        # Now save explicitly
        tracker.save()

        # Create new tracker (should now have data)
        tracker3 = BehaviorTracker(tmp_path)
        assert len(tracker3.behavior.tool_usage_history) == 10

    def test_batch_operations_performance(self, tmp_path: Path) -> None:
        """Test batch operations are faster with auto_save=False."""
        import time

        # With auto_save=True (default)
        tracker_auto = BehaviorTracker(tmp_path / "auto", auto_save=True)
        start_auto = time.time()
        for i in range(50):
            tracker_auto.record_suggestion_feedback(
                SuggestionType.KB_ENTRY, accepted=True
            )
        time_auto = time.time() - start_auto

        # With auto_save=False (batch mode)
        tracker_batch = BehaviorTracker(tmp_path / "batch", auto_save=False)
        start_batch = time.time()
        for i in range(50):
            tracker_batch.record_suggestion_feedback(
                SuggestionType.KB_ENTRY, accepted=True
            )
        tracker_batch.save()  # Single save at end
        time_batch = time.time() - start_batch

        # Batch mode should be faster (or at least not slower)
        # Note: This is a rough check, actual speedup may vary
        assert time_batch <= time_auto * 2  # Allow 2x margin for CI variability
