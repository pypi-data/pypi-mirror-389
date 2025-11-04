"""
Suggestion Service.

Generates AI suggestions by analyzing project state and history.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from clauxton.tui.models.suggestion import Suggestion, SuggestionType

logger = logging.getLogger(__name__)


class SuggestionService:
    """
    Service for generating AI suggestions.

    Integrates with various analysis modules to generate
    contextual suggestions for tasks, KB entries, and code reviews.
    """

    def __init__(self, project_root: Path) -> None:
        """
        Initialize suggestion service.

        Args:
            project_root: Project root directory
        """
        self.project_root = project_root
        self._cache: List[Suggestion] = []
        self._cache_timestamp: Optional[datetime] = None
        self._cache_ttl = 300  # 5 minutes

    def get_suggestions(
        self,
        limit: int = 10,
        min_confidence: float = 0.5,
        suggestion_types: Optional[List[SuggestionType]] = None,
    ) -> List[Suggestion]:
        """
        Get AI suggestions.

        Args:
            limit: Maximum number of suggestions
            min_confidence: Minimum confidence threshold
            suggestion_types: Filter by suggestion types

        Returns:
            List of suggestions
        """
        # Check cache
        if self._is_cache_valid():
            suggestions = self._cache
        else:
            suggestions = self._generate_suggestions()
            self._cache = suggestions
            self._cache_timestamp = datetime.now()

        # Filter by confidence
        suggestions = [s for s in suggestions if s.confidence >= min_confidence]

        # Filter by type
        if suggestion_types:
            suggestions = [s for s in suggestions if s.type in suggestion_types]

        # Sort by confidence (descending)
        suggestions.sort(key=lambda s: s.confidence, reverse=True)

        return suggestions[:limit]

    def _is_cache_valid(self) -> bool:
        """Check if cache is still valid."""
        if not self._cache or not self._cache_timestamp:
            return False

        age = (datetime.now() - self._cache_timestamp).total_seconds()
        return age < self._cache_ttl

    def _generate_suggestions(self) -> List[Suggestion]:
        """Generate fresh suggestions."""
        suggestions: List[Suggestion] = []

        # Task suggestions
        task_suggestions = self._generate_task_suggestions()
        suggestions.extend(task_suggestions)

        # KB suggestions
        kb_suggestions = self._generate_kb_suggestions()
        suggestions.extend(kb_suggestions)

        # Code review suggestions
        review_suggestions = self._generate_review_suggestions()
        suggestions.extend(review_suggestions)

        logger.info(f"Generated {len(suggestions)} suggestions")
        return suggestions

    def _generate_task_suggestions(self) -> List[Suggestion]:
        """Generate task suggestions."""
        suggestions = []

        try:
            # Try to use TaskSuggester if available
            from clauxton.analysis.task_suggester import TaskSuggester

            suggester = TaskSuggester(self.project_root)
            # TODO: Fix API signature - suggest_tasks doesn't accept limit parameter
            # task_suggestions = suggester.suggest_tasks(limit=5)
            task_suggestions = suggester.suggest_tasks()  # type: ignore[call-arg]

            for idx, task_sugg in enumerate(list(task_suggestions)[:5]):
                # TaskSuggestion object needs different access pattern
                suggestions.append(
                    Suggestion(
                        id=f"TASK-SUGG-{idx+1}",
                        type=SuggestionType.TASK,
                        title=getattr(task_sugg, "task_name", "Untitled task"),
                        description=getattr(task_sugg, "reasoning", ""),
                        confidence=getattr(task_sugg, "confidence", 0.7),
                        metadata={
                            "task_name": getattr(task_sugg, "task_name", ""),
                            "reasoning": getattr(task_sugg, "reasoning", ""),
                        },
                    )
                )
        except Exception as e:
            logger.debug(f"TaskSuggester not available: {e}")

        return suggestions

    def _generate_kb_suggestions(self) -> List[Suggestion]:
        """Generate KB entry suggestions."""
        suggestions: List[Suggestion] = []

        try:
            # Try to use DecisionExtractor if available
            # from clauxton.analysis.decision_extractor import DecisionExtractor
            # extractor = DecisionExtractor(self.project_root)
            # TODO: Fix API - method name might be different
            # decisions = extractor.extract_from_recent_commits(limit=5)
            # For now, use placeholder
            logger.debug("DecisionExtractor integration not yet complete")
        except (AttributeError, ImportError) as e:
            logger.debug(f"DecisionExtractor not available: {e}")
        except Exception as e:
            logger.debug(f"DecisionExtractor error: {e}")

        return suggestions

    def _generate_review_suggestions(self) -> List[Suggestion]:
        """Generate code review suggestions."""
        suggestions: List[Suggestion] = []

        try:
            # Try to use PatternExtractor if available
            # from clauxton.analysis.pattern_extractor import PatternExtractor
            # TODO: Fix API - PatternExtractor constructor signature
            # extractor = PatternExtractor(self.project_root)
            # patterns = extractor.extract_patterns()  # Method name might be detect_patterns
            # For now, use placeholder
            logger.debug("PatternExtractor integration not yet complete")
        except (AttributeError, ImportError, TypeError) as e:
            logger.debug(f"PatternExtractor not available: {e}")
        except Exception as e:
            logger.debug(f"PatternExtractor error: {e}")

        return suggestions

    def invalidate_cache(self) -> None:
        """Invalidate suggestion cache."""
        self._cache = []
        self._cache_timestamp = None
        logger.debug("Suggestion cache invalidated")
