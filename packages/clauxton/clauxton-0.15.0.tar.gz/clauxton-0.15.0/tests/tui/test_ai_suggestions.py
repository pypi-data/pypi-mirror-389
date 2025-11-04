"""Tests for AI Suggestions (widgets/ai_suggestions.py and models/suggestion.py)."""

from datetime import datetime
from pathlib import Path

from clauxton.tui.models.suggestion import Suggestion, SuggestionType
from clauxton.tui.services.suggestion_service import SuggestionService
from clauxton.tui.widgets.ai_suggestions import AISuggestionPanel, SuggestionCard


class TestSuggestionModel:
    """Test suite for Suggestion model."""

    def test_suggestion_creation(self) -> None:
        """Test creating a suggestion."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test Suggestion",
            description="This is a test suggestion",
            confidence=0.85,
        )

        assert suggestion.id == "TEST-001"
        assert suggestion.type == SuggestionType.TASK
        assert suggestion.title == "Test Suggestion"
        assert suggestion.confidence == 0.85

    def test_suggestion_confidence_level_high(self) -> None:
        """Test confidence level calculation - high."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.85,
        )

        assert suggestion.confidence_level == "high"

    def test_suggestion_confidence_level_medium(self) -> None:
        """Test confidence level calculation - medium."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.65,
        )

        assert suggestion.confidence_level == "medium"

    def test_suggestion_confidence_level_low(self) -> None:
        """Test confidence level calculation - low."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.3,
        )

        assert suggestion.confidence_level == "low"

    def test_suggestion_emoji_task(self) -> None:
        """Test emoji for task suggestion."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.8,
        )

        assert suggestion.emoji == "📋"

    def test_suggestion_emoji_kb(self) -> None:
        """Test emoji for KB suggestion."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.KB,
            title="Test",
            description="Test",
            confidence=0.8,
        )

        assert suggestion.emoji == "📚"

    def test_suggestion_emoji_review(self) -> None:
        """Test emoji for review suggestion."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.REVIEW,
            title="Test",
            description="Test",
            confidence=0.8,
        )

        assert suggestion.emoji == "🔍"

    def test_suggestion_accept(self) -> None:
        """Test accepting a suggestion."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.8,
        )

        suggestion.accept()
        assert suggestion.accepted is True

    def test_suggestion_reject(self) -> None:
        """Test rejecting a suggestion."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.8,
        )

        suggestion.reject()
        assert suggestion.accepted is False

    def test_suggestion_with_metadata(self) -> None:
        """Test suggestion with metadata."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.8,
            metadata={"files": ["test.py"], "priority": "high"},
        )

        assert suggestion.metadata["files"] == ["test.py"]
        assert suggestion.metadata["priority"] == "high"

    def test_suggestion_default_created_at(self) -> None:
        """Test suggestion has default created_at."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.8,
        )

        assert isinstance(suggestion.created_at, datetime)


class TestSuggestionCard:
    """Test suite for SuggestionCard widget."""

    def test_card_initialization(self) -> None:
        """Test card initializes correctly."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.8,
        )

        card = SuggestionCard(suggestion)

        assert card.suggestion == suggestion

    def test_card_has_compose_method(self) -> None:
        """Test card has compose method."""
        suggestion = Suggestion(
            id="TEST-001",
            type=SuggestionType.TASK,
            title="Test",
            description="Test",
            confidence=0.8,
        )

        card = SuggestionCard(suggestion)

        assert hasattr(card, "compose")
        assert callable(card.compose)


class TestAISuggestionPanel:
    """Test suite for AISuggestionPanel widget."""

    def test_panel_initialization(self, tmp_path: Path) -> None:
        """Test panel initializes correctly."""
        (tmp_path / ".clauxton").mkdir()

        panel = AISuggestionPanel(project_root=tmp_path)

        assert panel.project_root == tmp_path
        assert panel.refresh_interval == 30
        assert isinstance(panel.suggestions, list)

    def test_panel_custom_refresh_interval(self, tmp_path: Path) -> None:
        """Test panel with custom refresh interval."""
        (tmp_path / ".clauxton").mkdir()

        panel = AISuggestionPanel(project_root=tmp_path, refresh_interval=60)

        assert panel.refresh_interval == 60

    def test_panel_has_refresh_method(self, tmp_path: Path) -> None:
        """Test panel has refresh method."""
        (tmp_path / ".clauxton").mkdir()

        panel = AISuggestionPanel(project_root=tmp_path)

        assert hasattr(panel, "refresh_suggestions")
        assert callable(panel.refresh_suggestions)

    def test_panel_has_compose_method(self, tmp_path: Path) -> None:
        """Test panel has compose method."""
        (tmp_path / ".clauxton").mkdir()

        panel = AISuggestionPanel(project_root=tmp_path)

        assert hasattr(panel, "compose")
        assert callable(panel.compose)


class TestSuggestionService:
    """Test suite for SuggestionService."""

    def test_service_initialization(self, tmp_path: Path) -> None:
        """Test service initializes correctly."""
        (tmp_path / ".clauxton").mkdir()

        service = SuggestionService(project_root=tmp_path)

        assert service.project_root == tmp_path
        assert isinstance(service._cache, list)

    def test_service_get_suggestions(self, tmp_path: Path) -> None:
        """Test getting suggestions."""
        (tmp_path / ".clauxton").mkdir()

        service = SuggestionService(project_root=tmp_path)
        suggestions = service.get_suggestions(limit=5)

        assert isinstance(suggestions, list)
        assert len(suggestions) <= 5

    def test_service_filter_by_confidence(self, tmp_path: Path) -> None:
        """Test filtering by confidence."""
        (tmp_path / ".clauxton").mkdir()

        service = SuggestionService(project_root=tmp_path)
        suggestions = service.get_suggestions(min_confidence=0.8)

        # All suggestions should have confidence >= 0.8
        assert all(s.confidence >= 0.8 for s in suggestions)

    def test_service_filter_by_type(self, tmp_path: Path) -> None:
        """Test filtering by type."""
        (tmp_path / ".clauxton").mkdir()

        service = SuggestionService(project_root=tmp_path)
        suggestions = service.get_suggestions(
            suggestion_types=[SuggestionType.TASK, SuggestionType.KB]
        )

        # All suggestions should be TASK or KB
        assert all(
            s.type in [SuggestionType.TASK, SuggestionType.KB] for s in suggestions
        )

    def test_service_cache_invalidation(self, tmp_path: Path) -> None:
        """Test cache invalidation."""
        (tmp_path / ".clauxton").mkdir()

        service = SuggestionService(project_root=tmp_path)

        # Manually populate cache for testing
        from datetime import datetime

        from clauxton.tui.models.suggestion import Suggestion, SuggestionType

        service._cache = [
            Suggestion(
                id="TEST-001",
                type=SuggestionType.TASK,
                title="Test",
                description="Test",
                confidence=0.8,
            )
        ]
        service._cache_timestamp = datetime.now()

        assert len(service._cache) > 0
        assert service._cache_timestamp is not None

        service.invalidate_cache()

        assert len(service._cache) == 0
        assert service._cache_timestamp is None
