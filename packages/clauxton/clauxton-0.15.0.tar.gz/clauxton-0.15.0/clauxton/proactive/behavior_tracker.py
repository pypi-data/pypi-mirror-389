"""
User behavior tracking for learning preferences and improving suggestions.

This module tracks how users interact with Clauxton's MCP tools and suggestions,
learning patterns to personalize and improve the quality of future suggestions.
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from clauxton.utils.yaml_utils import read_yaml, write_yaml

# Import from suggestion_engine to avoid circular dependency
if TYPE_CHECKING:
    from clauxton.proactive.suggestion_engine import SuggestionType

logger = logging.getLogger(__name__)


class ToolUsage(BaseModel):
    """Record of MCP tool usage."""

    tool_name: str = Field(..., description="Name of MCP tool used")
    timestamp: datetime = Field(..., description="When tool was called")
    parameters: Dict[str, Any] = Field(
        default_factory=dict, description="Tool parameters"
    )
    result: str = Field(..., description="Result: accepted, rejected, or ignored")
    context: Dict[str, Any] = Field(
        default_factory=dict, description="Contextual information"
    )


class UserBehavior(BaseModel):
    """User behavior patterns and preferences."""

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    tool_usage_history: List[ToolUsage] = Field(
        default_factory=list, description="Tool usage history"
    )
    preferred_suggestion_types: Dict[str, float] = Field(
        default_factory=dict,
        description="Acceptance rates by suggestion type (0.0-1.0)",
    )
    active_hours: Dict[int, int] = Field(
        default_factory=dict, description="Active hours histogram (hour -> count)"
    )
    preferred_file_patterns: List[str] = Field(
        default_factory=list, description="File patterns user frequently works with"
    )
    confidence_threshold: float = Field(
        0.7, ge=0.0, le=1.0, description="User's preferred confidence threshold"
    )
    last_updated: datetime = Field(
        default_factory=datetime.now, description="Last update timestamp"
    )


class BehaviorTracker:
    """Track user behavior to personalize suggestions."""

    def __init__(self, project_root: Path, auto_save: bool = True):
        """
        Initialize behavior tracker.

        Args:
            project_root: Root directory of the project
            auto_save: Whether to auto-save after each change (default: True)
                      Set to False for batch operations, then call save() manually
        """
        self.project_root = Path(project_root)
        self.clauxton_dir = self.project_root / ".clauxton"
        self.behavior_file = self.clauxton_dir / "behavior.yml"
        self.auto_save = auto_save

        # Ensure .clauxton directory exists
        self.clauxton_dir.mkdir(parents=True, exist_ok=True)

        # Load existing behavior or create new
        self.behavior = self._load_behavior()

    def _load_behavior(self) -> UserBehavior:
        """
        Load user behavior from YAML file.

        Returns:
            UserBehavior instance
        """
        if not self.behavior_file.exists():
            return UserBehavior(confidence_threshold=0.7)

        try:
            data = read_yaml(self.behavior_file)
            if not data:
                return UserBehavior(confidence_threshold=0.7)

            # Convert tool_usage_history
            if "tool_usage_history" in data:
                data["tool_usage_history"] = [
                    ToolUsage(**usage) for usage in data["tool_usage_history"]
                ]

            # Ensure confidence_threshold has a default if not present
            if "confidence_threshold" not in data:
                data["confidence_threshold"] = 0.7

            return UserBehavior(**data)
        except Exception as e:
            # If loading fails, start fresh
            logger.warning(f"Failed to load behavior data: {e}. Starting fresh.")
            return UserBehavior(confidence_threshold=0.7)

    def _save_behavior(self) -> None:
        """Save user behavior to YAML file."""
        self.behavior.last_updated = datetime.now()

        # Convert to dict for YAML
        data = self.behavior.model_dump(mode="json")

        write_yaml(self.behavior_file, data)

    def save(self) -> None:
        """
        Manually save behavior data.

        Use this when auto_save=False for batch operations.
        """
        self._save_behavior()

    def record_tool_usage(
        self, tool_name: str, result: str, context: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Record MCP tool usage.

        Args:
            tool_name: Name of the tool used
            result: "accepted", "rejected", or "ignored"
            context: Additional context about the usage
        """
        if context is None:
            context = {}

        usage = ToolUsage(
            tool_name=tool_name,
            timestamp=datetime.now(),
            parameters={},
            result=result,
            context=context,
        )

        self.behavior.tool_usage_history.append(usage)

        # Update active hours
        hour = usage.timestamp.hour
        self.behavior.active_hours[hour] = self.behavior.active_hours.get(hour, 0) + 1

        # Keep only last 1000 entries to prevent unbounded growth
        if len(self.behavior.tool_usage_history) > 1000:
            self.behavior.tool_usage_history = self.behavior.tool_usage_history[-1000:]

        if self.auto_save:
            self._save_behavior()

    def record_suggestion_feedback(
        self, suggestion_type: "SuggestionType", accepted: bool
    ) -> None:
        """
        Record user feedback on a suggestion.

        Args:
            suggestion_type: Type of suggestion
            accepted: Whether user accepted the suggestion
        """
        type_str = suggestion_type.value

        # Get current stats
        if type_str not in self.behavior.preferred_suggestion_types:
            self.behavior.preferred_suggestion_types[type_str] = 0.5  # Neutral start

        current_rate = self.behavior.preferred_suggestion_types[type_str]

        # Update acceptance rate with exponential moving average
        # Weight recent feedback more heavily (alpha = 0.3)
        alpha = 0.3
        new_value = 1.0 if accepted else 0.0
        updated_rate = (alpha * new_value) + ((1 - alpha) * current_rate)

        self.behavior.preferred_suggestion_types[type_str] = updated_rate

        if self.auto_save:
            self._save_behavior()

    def get_preference_score(self, suggestion_type: "SuggestionType") -> float:
        """
        Get user's preference score for a suggestion type.

        Args:
            suggestion_type: Type of suggestion

        Returns:
            Preference score (0.0-1.0), default 0.5 if no history
        """
        type_str = suggestion_type.value
        return self.behavior.preferred_suggestion_types.get(type_str, 0.5)

    def is_active_time(self, tolerance_hours: int = 2) -> bool:
        """
        Check if current time matches user's typical active hours.

        Args:
            tolerance_hours: How many hours to consider "nearby" (default: 2)

        Returns:
            True if current hour is within user's active time
        """
        if not self.behavior.active_hours:
            return True  # No data, assume active

        current_hour = datetime.now().hour

        # Check current hour and nearby hours
        for offset in range(-tolerance_hours, tolerance_hours + 1):
            check_hour = (current_hour + offset) % 24
            if check_hour in self.behavior.active_hours:
                return True

        return False

    def adjust_confidence(
        self, base_confidence: float, suggestion_type: "SuggestionType"
    ) -> float:
        """
        Adjust suggestion confidence based on user preferences.

        Args:
            base_confidence: Original confidence score (0.0-1.0)
            suggestion_type: Type of suggestion

        Returns:
            Adjusted confidence score (0.0-1.0)
        """
        preference_score = self.get_preference_score(suggestion_type)

        # Blend base confidence with preference (70% base, 30% preference)
        adjusted = (0.7 * base_confidence) + (0.3 * preference_score)

        # Clamp to [0.0, 1.0]
        return max(0.0, min(1.0, adjusted))

    def get_usage_stats(self, days: int = 30) -> Dict[str, Any]:
        """
        Get usage statistics for the last N days.

        Args:
            days: Number of days to analyze (default: 30)

        Returns:
            Usage statistics dictionary
        """
        cutoff = datetime.now() - timedelta(days=days)

        recent_usage = [
            u for u in self.behavior.tool_usage_history if u.timestamp >= cutoff
        ]

        if not recent_usage:
            return {
                "total_tool_calls": 0,
                "accepted_count": 0,
                "rejected_count": 0,
                "ignored_count": 0,
                "acceptance_rate": 0.0,
                "most_used_tools": [],
                "peak_hours": [],
            }

        # Count results
        accepted = sum(1 for u in recent_usage if u.result == "accepted")
        rejected = sum(1 for u in recent_usage if u.result == "rejected")
        ignored = sum(1 for u in recent_usage if u.result == "ignored")

        # Calculate acceptance rate
        total_feedback = accepted + rejected
        acceptance_rate = (accepted / total_feedback) if total_feedback > 0 else 0.0

        # Most used tools
        tool_counts: Dict[str, int] = {}
        for usage in recent_usage:
            tool_counts[usage.tool_name] = tool_counts.get(usage.tool_name, 0) + 1

        most_used = sorted(tool_counts.items(), key=lambda x: x[1], reverse=True)[:5]

        # Peak hours
        hour_counts = sorted(
            self.behavior.active_hours.items(), key=lambda x: x[1], reverse=True
        )[:3]

        return {
            "total_tool_calls": len(recent_usage),
            "accepted_count": accepted,
            "rejected_count": rejected,
            "ignored_count": ignored,
            "acceptance_rate": acceptance_rate,
            "most_used_tools": [
                {"tool": tool, "count": count} for tool, count in most_used
            ],
            "peak_hours": [{"hour": hour, "count": count} for hour, count in hour_counts],
        }

    def update_confidence_threshold(self, threshold: float) -> None:
        """
        Update user's preferred confidence threshold.

        Args:
            threshold: New threshold (0.0-1.0)
        """
        if not 0.0 <= threshold <= 1.0:
            raise ValueError("Threshold must be between 0.0 and 1.0")

        self.behavior.confidence_threshold = threshold

        if self.auto_save:
            self._save_behavior()

    def get_confidence_threshold(self) -> float:
        """
        Get user's preferred confidence threshold.

        Returns:
            Confidence threshold (0.0-1.0)
        """
        return self.behavior.confidence_threshold
