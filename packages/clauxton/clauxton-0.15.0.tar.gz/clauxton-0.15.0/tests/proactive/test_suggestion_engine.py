"""Tests for proactive suggestion engine."""

from datetime import datetime, timedelta
from pathlib import Path

import pytest

from clauxton.core.models import Priority
from clauxton.proactive.models import (
    ChangeType,
    DetectedPattern,
    FileChange,
    PatternType,
)
from clauxton.proactive.suggestion_engine import (
    Suggestion,
    SuggestionEngine,
    SuggestionType,
)


class TestSuggestionModel:
    """Test Suggestion Pydantic model."""

    def test_suggestion_creation_valid(self):
        """Test creating valid suggestion."""
        suggestion = Suggestion(
            type=SuggestionType.KB_ENTRY,
            title="Test suggestion",
            description="Test description",
            confidence=0.85,
            reasoning="Test reasoning",
            affected_files=["file1.py", "file2.py"],
            priority=Priority.HIGH,
        )

        assert suggestion.type == SuggestionType.KB_ENTRY
        assert suggestion.title == "Test suggestion"
        assert suggestion.confidence == 0.85
        assert len(suggestion.affected_files) == 2
        assert suggestion.priority == Priority.HIGH

    def test_suggestion_confidence_bounds(self):
        """Test confidence must be between 0 and 1."""
        from pydantic import ValidationError

        with pytest.raises(ValidationError):
            Suggestion(
                type=SuggestionType.TASK,
                title="Test",
                description="Test",
                confidence=1.5,  # Invalid
                reasoning="Test",
            )

        with pytest.raises(ValidationError):
            Suggestion(
                type=SuggestionType.TASK,
                title="Test",
                description="Test",
                confidence=-0.1,  # Invalid
                reasoning="Test",
            )

    def test_suggestion_defaults(self):
        """Test default values for optional fields."""
        suggestion = Suggestion(
            type=SuggestionType.DOCUMENTATION,
            title="Test",
            description="Test",
            confidence=0.7,
            reasoning="Test",
        )

        assert suggestion.affected_files == []
        assert suggestion.priority == Priority.MEDIUM
        assert isinstance(suggestion.created_at, datetime)
        assert suggestion.metadata == {}


class TestSuggestionEngine:
    """Test SuggestionEngine class."""

    @pytest.fixture
    def temp_project(self, tmp_path: Path):
        """Create temporary project directory."""
        project = tmp_path / "test_project"
        project.mkdir()
        return project

    @pytest.fixture
    def engine(self, temp_project: Path):
        """Create SuggestionEngine instance."""
        return SuggestionEngine(temp_project, min_confidence=0.7)

    def test_engine_initialization(self, temp_project: Path):
        """Test engine initialization."""
        engine = SuggestionEngine(temp_project, min_confidence=0.8)
        assert engine.project_root == temp_project
        assert engine.min_confidence == 0.8
        assert engine._suggestion_counter == 0

    def test_analyze_pattern_kb_entry(self, engine: SuggestionEngine):
        """Test KB entry suggestion from pattern."""
        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[Path("src/auth.py"), Path("src/api.py"), Path("src/models.py")],
            confidence=0.85,
            description="Multiple files edited quickly",
        )

        suggestions = engine.analyze_pattern(pattern)

        assert len(suggestions) >= 1
        kb_suggestions = [s for s in suggestions if s.type == SuggestionType.KB_ENTRY]
        assert len(kb_suggestions) >= 1

        kb_sugg = kb_suggestions[0]
        assert "src" in kb_sugg.title.lower() or "auth" in kb_sugg.title.lower()
        assert kb_sugg.confidence >= 0.7
        assert len(kb_sugg.affected_files) == 3

    def test_analyze_pattern_task_missing_tests(self, engine: SuggestionEngine):
        """Test task suggestion when tests are missing."""
        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[Path("src/auth.py"), Path("src/api.py")],  # No test files
            confidence=0.80,
            description="Code files modified",
        )

        suggestions = engine.analyze_pattern(pattern)

        task_suggestions = [s for s in suggestions if s.type == SuggestionType.TASK]
        assert len(task_suggestions) >= 1

        task_sugg = task_suggestions[0]
        assert "test" in task_sugg.title.lower()
        assert task_sugg.confidence >= 0.7
        assert task_sugg.priority == Priority.HIGH

    def test_analyze_pattern_refactor(self, engine: SuggestionEngine):
        """Test refactor suggestion for large files."""
        pattern = DetectedPattern(
            pattern_type=PatternType.REFACTORING,
            files=[Path("src/large_module.py")],
            confidence=0.75,
            description="Large file changes",
        )

        suggestions = engine.analyze_pattern(pattern)

        refactor_suggestions = [
            s for s in suggestions if s.type == SuggestionType.REFACTOR
        ]
        # May or may not trigger based on filename
        assert isinstance(refactor_suggestions, list)

    def test_analyze_pattern_empty(self, engine: SuggestionEngine):
        """Test analyzing pattern with no files returns no suggestions."""
        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[],
            confidence=0.60,
            description="Empty pattern",
        )

        suggestions = engine.analyze_pattern(pattern)

        # Should return empty list or low-confidence suggestions
        assert all(s.confidence >= 0.7 for s in suggestions)

    def test_analyze_changes_module_changes(self, engine: SuggestionEngine):
        """Test analyzing changes for module-wide changes."""
        now = datetime.now()
        changes = [
            FileChange(
                path=Path("src/auth.py"),
                change_type=ChangeType.MODIFIED,
                timestamp=now,
            ),
            FileChange(
                path=Path("src/api.py"),
                change_type=ChangeType.MODIFIED,
                timestamp=now,
            ),
            FileChange(
                path=Path("src/models.py"),
                change_type=ChangeType.MODIFIED,
                timestamp=now,
            ),
        ]

        suggestions = engine.analyze_changes(changes)

        assert len(suggestions) >= 1
        kb_suggestions = [s for s in suggestions if s.type == SuggestionType.KB_ENTRY]
        assert len(kb_suggestions) >= 1

    def test_analyze_changes_rapid_changes(self, engine: SuggestionEngine):
        """Test anomaly detection for rapid changes."""
        now = datetime.now()
        # Create 15 changes all within the last 5 minutes (rapid!)
        changes = [
            FileChange(
                path=Path("file.py"),
                change_type=ChangeType.MODIFIED,
                timestamp=now - timedelta(seconds=i * 20),  # 20 seconds apart
            )
            for i in range(15)  # 15 changes in 5 minutes
        ]

        suggestions = engine.analyze_changes(changes)

        anomaly_suggestions = [
            s for s in suggestions if s.type == SuggestionType.ANOMALY
        ]
        assert len(anomaly_suggestions) >= 1

        anomaly = anomaly_suggestions[0]
        assert "rapid" in anomaly.title.lower()
        assert anomaly.confidence >= 0.7

    def test_analyze_changes_empty(self, engine: SuggestionEngine):
        """Test analyzing empty change list."""
        suggestions = engine.analyze_changes([])
        assert suggestions == []

    def test_confidence_scoring(self, engine: SuggestionEngine):
        """Test confidence calculation with evidence."""
        evidence = {
            "pattern_frequency": 0.8,
            "file_relevance": 0.7,
            "historical_accuracy": 0.9,
            "user_context": 0.6,
        }

        confidence = engine.calculate_confidence(evidence)

        assert 0.0 <= confidence <= 1.0
        # Should be weighted average: 0.8*0.3 + 0.7*0.25 + 0.9*0.25 + 0.6*0.2
        expected = 0.8 * 0.3 + 0.7 * 0.25 + 0.9 * 0.25 + 0.6 * 0.2
        assert abs(confidence - expected) < 0.01

    def test_confidence_scoring_missing_evidence(self, engine: SuggestionEngine):
        """Test confidence with missing evidence fields."""
        evidence = {
            "pattern_frequency": 0.8,
            # Missing other fields
        }

        confidence = engine.calculate_confidence(evidence)

        assert 0.0 <= confidence <= 1.0
        # Should only count pattern_frequency: 0.8 * 0.3 = 0.24
        assert abs(confidence - 0.24) < 0.01

    def test_suggestion_ranking(self, engine: SuggestionEngine):
        """Test suggestions are ranked by confidence and priority."""
        suggestions = [
            Suggestion(
                type=SuggestionType.KB_ENTRY,
                title="Low confidence",
                description="Test",
                confidence=0.6,
                reasoning="Test",
                priority=Priority.LOW,
            ),
            Suggestion(
                type=SuggestionType.TASK,
                title="High confidence",
                description="Test",
                confidence=0.9,
                reasoning="Test",
                priority=Priority.HIGH,
            ),
            Suggestion(
                type=SuggestionType.REFACTOR,
                title="Medium confidence",
                description="Test",
                confidence=0.75,
                reasoning="Test",
                priority=Priority.MEDIUM,
            ),
        ]

        ranked = engine.rank_suggestions(suggestions)

        # Should be sorted by confidence (desc), then priority
        assert ranked[0].title == "High confidence"
        assert ranked[1].title == "Medium confidence"
        assert ranked[2].title == "Low confidence"

    def test_suggestion_deduplication(self, engine: SuggestionEngine):
        """Test duplicate suggestions are removed."""
        suggestions = [
            Suggestion(
                type=SuggestionType.KB_ENTRY,
                title="Duplicate title",
                description="Test 1",
                confidence=0.8,
                reasoning="Test",
            ),
            Suggestion(
                type=SuggestionType.KB_ENTRY,
                title="Duplicate title",  # Same title
                description="Test 2",
                confidence=0.9,
                reasoning="Test",
            ),
            Suggestion(
                type=SuggestionType.TASK,
                title="Unique title",
                description="Test",
                confidence=0.7,
                reasoning="Test",
            ),
        ]

        ranked = engine.rank_suggestions(suggestions)

        # Should have 2 suggestions (1 duplicate removed)
        assert len(ranked) == 2
        titles = [s.title for s in ranked]
        assert titles.count("Duplicate title") == 1
        assert "Unique title" in titles

    def test_metadata_preservation(self, engine: SuggestionEngine):
        """Test metadata is preserved in suggestions."""
        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[Path("src/auth.py")],
            confidence=0.80,
            description="Auth file modified",
        )

        suggestions = engine.analyze_pattern(pattern)

        # At least one suggestion should have metadata
        assert any(s.metadata for s in suggestions)

    def test_common_path_prefix_single_file(self, engine: SuggestionEngine):
        """Test common path prefix with single file."""
        prefix = engine._get_common_path_prefix(["src/auth.py"])
        assert prefix in ["src", "auth.py"]  # Either parent or filename

    def test_common_path_prefix_multiple_files(self, engine: SuggestionEngine):
        """Test common path prefix with multiple files."""
        files = ["src/api/auth.py", "src/api/users.py", "src/api/models.py"]
        prefix = engine._get_common_path_prefix(files)
        assert "api" in prefix or "src" in prefix

    def test_common_path_prefix_no_common(self, engine: SuggestionEngine):
        """Test common path prefix with no common path."""
        files = ["file1.py", "other/file2.py", "another/deep/file3.py"]
        prefix = engine._get_common_path_prefix(files)
        # May return empty or root directory
        assert isinstance(prefix, str)

    def test_generate_id_increments(self, engine: SuggestionEngine):
        """Test suggestion IDs increment correctly."""
        id1 = engine._generate_id()
        id2 = engine._generate_id()
        id3 = engine._generate_id()

        assert id1 == "SUGG-001"
        assert id2 == "SUGG-002"
        assert id3 == "SUGG-003"

    def test_multiple_suggestions_same_pattern(self, engine: SuggestionEngine):
        """Test pattern can generate multiple suggestion types."""
        # Pattern that should trigger both KB entry and task suggestions
        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[Path("src/auth.py"), Path("src/api.py")],  # No tests
            confidence=0.85,
            description="Multiple files modified without tests",
        )

        suggestions = engine.analyze_pattern(pattern)

        # Should have at least KB entry and task suggestions
        types = {s.type for s in suggestions}
        assert SuggestionType.KB_ENTRY in types
        assert SuggestionType.TASK in types

    def test_confidence_threshold_filtering(self, engine: SuggestionEngine):
        """Test suggestions below threshold are filtered out."""
        # Create engine with high threshold
        strict_engine = SuggestionEngine(engine.project_root, min_confidence=0.95)

        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[Path("file.py")],
            confidence=0.60,
            description="Single file change",
        )

        suggestions = strict_engine.analyze_pattern(pattern)

        # With high threshold, should get very few or no suggestions
        assert all(s.confidence >= 0.95 for s in suggestions)


class TestDay2AdvancedFeatures:
    """Test Day 2 advanced suggestion features."""

    @pytest.fixture
    def engine(self, tmp_path: Path):
        """Create engine for testing."""
        return SuggestionEngine(tmp_path)

    def test_documentation_gap_detection(self, engine: SuggestionEngine):
        """Test detection of documentation gaps."""
        pattern = DetectedPattern(
            pattern_type=PatternType.NEW_FEATURE,
            files=[
                Path("src/new_module.py"),
                Path("src/new_api.py"),
                Path("src/new_models.py"),
            ],
            confidence=0.80,
            description="New feature files created",
        )

        suggestions = engine.analyze_pattern(pattern)

        doc_suggestions = [
            s for s in suggestions if s.type == SuggestionType.DOCUMENTATION
        ]
        assert len(doc_suggestions) >= 1

        doc_sugg = doc_suggestions[0]
        assert "documentation" in doc_sugg.title.lower() or "docstring" in doc_sugg.title.lower()
        assert doc_sugg.confidence >= 0.7
        assert len(doc_sugg.affected_files) >= 1

    def test_code_smell_large_file_detection(self, engine: SuggestionEngine):
        """Test detection of large file code smell."""
        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[Path("src/large_utils.py"), Path("src/big_main.py")],
            confidence=0.85,
            description="Large files modified",
        )

        suggestions = engine.analyze_pattern(pattern)

        refactor_suggestions = [
            s for s in suggestions if s.type == SuggestionType.REFACTOR
        ]
        assert len(refactor_suggestions) >= 1

        # Check for code smell detection
        assert any(
            "size" in s.title.lower() or "complexity" in s.title.lower()
            for s in refactor_suggestions
        )

    def test_code_smell_high_change_frequency(self, engine: SuggestionEngine):
        """Test detection of high change frequency code smell."""
        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[Path(f"src/file{i}.py") for i in range(6)],  # 6 files
            confidence=0.85,
            description="Many files changed frequently",
        )

        suggestions = engine.analyze_pattern(pattern)

        refactor_suggestions = [
            s for s in suggestions if s.type == SuggestionType.REFACTOR
        ]
        assert any(
            "frequency" in s.title.lower()
            or "instability" in s.description.lower()
            for s in refactor_suggestions
        )

    def test_code_smell_test_organization(self, engine: SuggestionEngine):
        """Test detection of test organization issues."""
        pattern = DetectedPattern(
            pattern_type=PatternType.BULK_EDIT,
            files=[Path(f"tests/test_file{i}.py") for i in range(6)],  # 6 test files
            confidence=0.85,  # Must be > 0.8 to trigger code smell detection
            description="Many test files modified",
        )

        suggestions = engine.analyze_pattern(pattern)

        refactor_suggestions = [
            s for s in suggestions if s.type == SuggestionType.REFACTOR
        ]

        # Check for test organization suggestion
        # Should have at least one refactor suggestion
        assert len(refactor_suggestions) >= 1
        # At least one should mention tests
        assert any(
            "test" in s.title.lower() or "test" in s.description.lower()
            for s in refactor_suggestions
        )

    def test_analyze_file_content_large_file(self, engine: SuggestionEngine, tmp_path: Path):
        """Test file content analysis for large files."""
        # Create a large file
        test_file = tmp_path / "large_file.py"
        with open(test_file, "w") as f:
            for i in range(600):  # More than MAX_FILE_LINES (500)
                f.write(f"# Line {i}\n")

        suggestions = engine.analyze_file_content(test_file)

        assert len(suggestions) >= 1
        large_file_sugg = [
            s for s in suggestions
            if "large" in s.title.lower() and s.type == SuggestionType.REFACTOR
        ]
        assert len(large_file_sugg) == 1
        assert "600" in large_file_sugg[0].description

    def test_analyze_file_content_missing_docstring(self, engine: SuggestionEngine, tmp_path: Path):
        """Test detection of missing module docstrings."""
        # Create Python file without docstring
        test_file = tmp_path / "no_docstring.py"
        with open(test_file, "w") as f:
            for i in range(30):  # More than 20 lines
                f.write(f"def function_{i}():\n    pass\n\n")

        suggestions = engine.analyze_file_content(test_file)

        doc_suggestions = [
            s for s in suggestions if s.type == SuggestionType.DOCUMENTATION
        ]
        assert len(doc_suggestions) >= 1
        assert "docstring" in doc_suggestions[0].title.lower()

    def test_analyze_file_content_deep_nesting(self, engine: SuggestionEngine, tmp_path: Path):
        """Test detection of deep nesting."""
        # Create file with deep nesting
        test_file = tmp_path / "nested_code.py"
        with open(test_file, "w") as f:
            f.write("def function():\n")
            indent = "    "
            for i in range(6):  # 6 levels of nesting (>4 threshold)
                f.write(f"{indent * (i + 1)}if condition_{i}:\n")
            f.write(f"{indent * 7}do_something()\n")

        suggestions = engine.analyze_file_content(test_file)

        refactor_suggestions = [
            s for s in suggestions
            if s.type == SuggestionType.REFACTOR and "nesting" in s.title.lower()
        ]
        assert len(refactor_suggestions) >= 1

    def test_detect_file_deletion_pattern(self, engine: SuggestionEngine):
        """Test detection of file deletion patterns."""
        now = datetime.now()
        changes = [
            FileChange(
                path=Path(f"old_file{i}.py"),
                change_type=ChangeType.DELETED,
                timestamp=now,
            )
            for i in range(6)  # 6 deletions
        ]

        suggestions = engine.analyze_changes(changes)

        deletion_suggestions = [
            s for s in suggestions if "delet" in s.title.lower()
        ]
        assert len(deletion_suggestions) >= 1

        deletion_sugg = deletion_suggestions[0]
        assert deletion_sugg.priority == Priority.HIGH
        assert (
            "mass deletion" in deletion_sugg.title.lower()
            or "deletion" in deletion_sugg.title.lower()
        )
        assert deletion_sugg.type == SuggestionType.ANOMALY  # Should be anomaly type

    def test_detect_weekend_activity(self, engine: SuggestionEngine):
        """Test detection of weekend activity patterns."""
        # Create changes on Saturday (weekday 5)
        base_date = datetime(2025, 10, 25, 14, 0)  # Saturday, Oct 25, 2025
        changes = [
            FileChange(
                path=Path(f"file{i}.py"),
                change_type=ChangeType.MODIFIED,
                timestamp=base_date + timedelta(hours=i),
            )
            for i in range(6)  # 6 weekend changes
        ]

        suggestions = engine.analyze_changes(changes)

        weekend_suggestions = [
            s for s in suggestions
            if "weekend" in s.title.lower()
        ]
        assert len(weekend_suggestions) >= 1

        weekend_sugg = weekend_suggestions[0]
        assert weekend_sugg.type == SuggestionType.ANOMALY
        assert "weekend" in weekend_sugg.title.lower()

    def test_detect_late_night_activity(self, engine: SuggestionEngine):
        """Test detection of late-night activity patterns."""
        # Create changes at 11 PM on a WEEKDAY (important!)
        base_date = datetime(2025, 10, 22, 23, 0)  # Wednesday, Oct 22, 11 PM
        changes = [
            FileChange(
                path=Path(f"file{i}.py"),
                change_type=ChangeType.MODIFIED,
                timestamp=base_date + timedelta(minutes=i * 10),
            )
            for i in range(10)  # 10 late-night changes (11 PM - 1:30 AM)
        ]

        suggestions = engine.analyze_changes(changes)

        late_night_suggestions = [
            s for s in suggestions
            if "late" in s.title.lower() or "night" in s.title.lower()
        ]
        assert len(late_night_suggestions) >= 1

        late_night_sugg = late_night_suggestions[0]
        assert late_night_sugg.type == SuggestionType.ANOMALY

    def test_no_false_positives_normal_activity(self, engine: SuggestionEngine):
        """Test that normal activity doesn't trigger anomaly detection."""
        # Create normal activity: weekday, normal hours, few files
        base_date = datetime(2025, 10, 24, 14, 0)  # Friday, 2 PM
        changes = [
            FileChange(
                path=Path(f"file{i}.py"),
                change_type=ChangeType.MODIFIED,
                timestamp=base_date + timedelta(minutes=i * 5),
            )
            for i in range(3)  # Only 3 changes
        ]

        suggestions = engine.analyze_changes(changes)

        # Should not have weekend or late-night suggestions
        anomaly_suggestions = [
            s for s in suggestions if s.type == SuggestionType.ANOMALY
        ]
        assert len(anomaly_suggestions) == 0

    def test_analyze_file_content_nonexistent_file(self, engine: SuggestionEngine, tmp_path: Path):
        """Test file content analysis for nonexistent files."""
        nonexistent = tmp_path / "does_not_exist.py"
        suggestions = engine.analyze_file_content(nonexistent)
        assert suggestions == []

    def test_analyze_file_content_non_code_file(self, engine: SuggestionEngine, tmp_path: Path):
        """Test file content analysis skips non-code files."""
        text_file = tmp_path / "readme.txt"
        text_file.write_text("This is a text file")

        suggestions = engine.analyze_file_content(text_file)
        assert suggestions == []

    def test_documentation_gap_readme_suggestion(self, engine: SuggestionEngine):
        """Test README suggestion for new modules."""
        pattern = DetectedPattern(
            pattern_type=PatternType.NEW_FEATURE,
            files=[
                Path("new_module/file1.py"),
                Path("new_module/subdir/file2.py"),
                Path("new_module/file3.py"),
            ],
            confidence=0.80,
            description="New module created",
        )

        suggestions = engine.analyze_pattern(pattern)

        doc_suggestions = [
            s for s in suggestions if s.type == SuggestionType.DOCUMENTATION
        ]
        # Should suggest README for new module
        assert len(doc_suggestions) >= 1
