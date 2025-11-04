"""
Suggestion Data Model.

Defines the structure for AI-generated suggestions.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, Optional

from pydantic import BaseModel, ConfigDict, Field


class SuggestionType(str, Enum):
    """Type of AI suggestion."""

    TASK = "task"  # Task creation suggestion
    KB = "kb"  # KB entry suggestion
    REVIEW = "review"  # Code review insight
    REFACTOR = "refactor"  # Refactoring suggestion
    PATTERN = "pattern"  # Pattern detection
    OTHER = "other"  # Other suggestions


class Suggestion(BaseModel):
    """
    AI-generated suggestion model.

    Represents a single suggestion from the AI system with
    confidence score and associated metadata.
    """

    id: str = Field(..., description="Unique suggestion ID")
    type: SuggestionType = Field(..., description="Type of suggestion")
    title: str = Field(..., min_length=1, max_length=200, description="Suggestion title")
    description: str = Field(
        ..., min_length=1, max_length=2000, description="Detailed description"
    )
    confidence: float = Field(
        ..., ge=0.0, le=1.0, description="Confidence score (0.0-1.0)"
    )
    metadata: Dict[str, Any] = Field(
        default_factory=dict, description="Additional metadata"
    )
    created_at: datetime = Field(default_factory=datetime.now, description="Creation time")
    accepted: Optional[bool] = Field(
        default=None, description="Whether suggestion was accepted"
    )

    @property
    def confidence_level(self) -> str:
        """
        Get human-readable confidence level.

        Returns:
            Confidence level: "high", "medium", or "low"
        """
        if self.confidence >= 0.75:
            return "high"
        elif self.confidence >= 0.5:
            return "medium"
        else:
            return "low"

    @property
    def emoji(self) -> str:
        """
        Get emoji for suggestion type.

        Returns:
            Emoji representing the suggestion type
        """
        emoji_map = {
            SuggestionType.TASK: "📋",
            SuggestionType.KB: "📚",
            SuggestionType.REVIEW: "🔍",
            SuggestionType.REFACTOR: "♻️",
            SuggestionType.PATTERN: "🎨",
            SuggestionType.OTHER: "💡",
        }
        return emoji_map.get(self.type, "💡")

    def accept(self) -> None:
        """Mark suggestion as accepted."""
        self.accepted = True

    def reject(self) -> None:
        """Mark suggestion as rejected."""
        self.accepted = False

    model_config = ConfigDict(use_enum_values=True)
