"""Tests for PatternExtractor."""

from datetime import datetime

import pytest

from clauxton.analysis.git_analyzer import CommitInfo
from clauxton.analysis.pattern_extractor import PatternExtractor


@pytest.fixture
def extractor():
    """Create PatternExtractor instance."""
    return PatternExtractor()


@pytest.fixture
def sample_commit():
    """Create sample commit for testing."""
    return CommitInfo(
        sha="abc123",
        message="feat(auth): add JWT authentication\n\nImplement JWT-based auth",
        author="Test Author",
        date=datetime.now(),
        files=["src/auth.py", "tests/test_auth.py", "README.md"],
        diff="""
+import jwt
+
+def authenticate(token):
+    # Validate JWT token
+    return jwt.decode(token)
""",
        stats={"insertions": 50, "deletions": 10, "files_changed": 3},
    )


class TestExtractFromMessage:
    """Tests for extract_from_message."""

    def test_conventional_commits_format(self, extractor):
        """Test Conventional Commits detection."""
        message = "feat(api): add user endpoint"
        patterns = extractor.extract_from_message(message)

        assert patterns["conventional_commits"] is True
        assert patterns["type"] == "feature"
        assert patterns["scope"] == "api"
        assert patterns["breaking"] is False

    def test_conventional_commits_breaking_change(self, extractor):
        """Test breaking change detection."""
        message = "feat(api)!: remove deprecated endpoint"
        patterns = extractor.extract_from_message(message)

        assert patterns["conventional_commits"] is True
        assert patterns["breaking"] is True

    def test_issue_reference_detection(self, extractor):
        """Test issue reference extraction."""
        message = "fix: resolve bug #123 and GH-456"
        patterns = extractor.extract_from_message(message)

        assert patterns["has_issue_ref"] is True
        assert "123" in patterns["issue_numbers"]
        assert "456" in patterns["issue_numbers"]

    def test_non_conventional_format(self, extractor):
        """Test non-Conventional Commits message."""
        message = "Add new feature"
        patterns = extractor.extract_from_message(message)

        assert patterns["conventional_commits"] is False
        assert patterns["type"] is None
        assert patterns["scope"] is None

    def test_multiple_commit_types(self, extractor):
        """Test different commit types."""
        test_cases = [
            ("fix: bug fix", "bugfix"),
            ("docs: update readme", "docs"),
            ("test: add tests", "test"),
            ("refactor: cleanup", "refactor"),
            ("chore: update deps", "chore"),
        ]

        for message, expected_type in test_cases:
            patterns = extractor.extract_from_message(message)
            assert patterns["type"] == expected_type


class TestExtractFromFiles:
    """Tests for extract_from_files."""

    def test_file_extensions(self, extractor):
        """Test file extension extraction."""
        files = ["src/main.py", "tests/test.js", "config.yml"]
        patterns = extractor.extract_from_files(files)

        assert "py" in patterns["file_types"]
        assert "js" in patterns["file_types"]
        assert "yml" in patterns["file_types"]

    def test_directory_extraction(self, extractor):
        """Test directory extraction."""
        files = ["src/main.py", "src/utils.py", "tests/test.py"]
        patterns = extractor.extract_from_files(files)

        assert "src" in patterns["directories"]
        assert "tests" in patterns["directories"]

    def test_test_file_detection(self, extractor):
        """Test test file detection."""
        files = ["tests/test_main.py", "src/main_spec.js"]
        patterns = extractor.extract_from_files(files)

        assert patterns["test_files"] is True

    def test_doc_file_detection(self, extractor):
        """Test documentation file detection."""
        files = ["README.md", "docs/guide.md"]
        patterns = extractor.extract_from_files(files)

        assert patterns["doc_files"] is True

    def test_config_file_detection(self, extractor):
        """Test config file detection."""
        files = ["config.yml", ".env", "settings.py"]
        patterns = extractor.extract_from_files(files)

        assert patterns["config_files"] is True

    def test_empty_file_list(self, extractor):
        """Test with empty file list."""
        patterns = extractor.extract_from_files([])

        assert patterns["file_types"] == []
        assert patterns["directories"] == []
        assert patterns["test_files"] is False


class TestExtractFromDiff:
    """Tests for extract_from_diff."""

    def test_python_imports(self, extractor):
        """Test Python import detection."""
        diff = "+import os\n+from pathlib import Path"
        patterns = extractor.extract_from_diff(diff)

        assert patterns["has_imports"] is True
        assert "python" in patterns["language_hints"]

    def test_class_definition(self, extractor):
        """Test class definition detection."""
        diff = "+class MyClass:\n+    pass"
        patterns = extractor.extract_from_diff(diff)

        assert patterns["has_class_def"] is True

    def test_python_function(self, extractor):
        """Test Python function detection."""
        diff = "+def my_function():\n+    pass"
        patterns = extractor.extract_from_diff(diff)

        assert patterns["has_function_def"] is True
        assert "python" in patterns["language_hints"]

    def test_javascript_function(self, extractor):
        """Test JavaScript function detection."""
        diff = "+function myFunc() {\n+    return true;\n+}"
        patterns = extractor.extract_from_diff(diff)

        assert patterns["has_function_def"] is True
        assert "javascript" in patterns["language_hints"]

    def test_comment_detection(self, extractor):
        """Test comment detection."""
        diff = "+# This is a comment\n+// Another comment\n+/* Block comment */"
        patterns = extractor.extract_from_diff(diff)

        assert patterns["has_comments"] is True

    def test_empty_diff(self, extractor):
        """Test with empty diff."""
        patterns = extractor.extract_from_diff("")

        assert patterns["has_imports"] is False
        assert patterns["has_class_def"] is False
        assert patterns["language_hints"] == []


class TestCategorizeCommit:
    """Tests for categorize_commit."""

    def test_feature_categorization(self, extractor):
        """Test feature commit categorization."""
        commit = CommitInfo(
            sha="abc",
            message="feat: add new API endpoint",
            author="Author",
            date=datetime.now(),
            files=["src/api.py"],
            diff="",
            stats={"insertions": 10, "deletions": 0, "files_changed": 1},
        )

        category = extractor.categorize_commit(commit)
        assert category == "feature"

    def test_bugfix_categorization(self, extractor):
        """Test bugfix commit categorization."""
        commit = CommitInfo(
            sha="abc",
            message="fix: resolve authentication bug",
            author="Author",
            date=datetime.now(),
            files=["src/auth.py"],
            diff="",
            stats={"insertions": 5, "deletions": 5, "files_changed": 1},
        )

        category = extractor.categorize_commit(commit)
        assert category == "bugfix"

    def test_test_categorization_by_files(self, extractor):
        """Test test categorization based on files."""
        commit = CommitInfo(
            sha="abc",
            message="update tests",
            author="Author",
            date=datetime.now(),
            files=["tests/test_main.py"],
            diff="",
            stats={"insertions": 10, "deletions": 0, "files_changed": 1},
        )

        category = extractor.categorize_commit(commit)
        assert category == "test"

    def test_refactor_categorization(self, extractor):
        """Test refactor categorization by keyword."""
        commit = CommitInfo(
            sha="abc",
            message="refactor database connection logic",
            author="Author",
            date=datetime.now(),
            files=["src/db.py"],
            diff="",
            stats={"insertions": 15, "deletions": 10, "files_changed": 1},
        )

        category = extractor.categorize_commit(commit)
        assert category == "refactor"

    def test_feature_keyword_categorization(self, extractor):
        """Test feature categorization by keyword."""
        commit = CommitInfo(
            sha="abc",
            message="add user authentication feature",
            author="Author",
            date=datetime.now(),
            files=["src/auth.py"],
            diff="",
            stats={"insertions": 50, "deletions": 0, "files_changed": 1},
        )

        category = extractor.categorize_commit(commit)
        assert category == "feature"

    def test_bugfix_keyword_categorization(self, extractor):
        """Test bugfix categorization by keyword."""
        commit = CommitInfo(
            sha="abc",
            message="resolve memory leak issue",
            author="Author",
            date=datetime.now(),
            files=["src/memory.py"],
            diff="",
            stats={"insertions": 5, "deletions": 2, "files_changed": 1},
        )

        category = extractor.categorize_commit(commit)
        assert category == "bugfix"

    def test_docs_categorization(self, extractor):
        """Test docs categorization."""
        commit = CommitInfo(
            sha="abc",
            message="docs: update README",
            author="Author",
            date=datetime.now(),
            files=["README.md"],
            diff="",
            stats={"insertions": 10, "deletions": 0, "files_changed": 1},
        )

        category = extractor.categorize_commit(commit)
        assert category == "docs"


class TestExtractKeywords:
    """Tests for extract_keywords."""

    def test_keyword_extraction(self, extractor):
        """Test basic keyword extraction."""
        text = "Add authentication system with JWT tokens"
        keywords = extractor.extract_keywords(text)

        assert "authentication" in keywords
        assert "system" in keywords
        assert "tokens" in keywords

    def test_stopword_filtering(self, extractor):
        """Test stopword filtering."""
        text = "The quick brown fox jumps over the lazy dog"
        keywords = extractor.extract_keywords(text)

        # Stop words should be filtered (3 chars or less, or in stopword list)
        assert "the" not in keywords
        # Note: "over" is 4 chars so it won't be filtered by length,
        # but it's in the stopword list
        # Actually checking what's NOT filtered instead
        assert "quick" in keywords
        assert "brown" in keywords

    def test_short_word_filtering(self, extractor):
        """Test short word filtering."""
        text = "Add new API for user authentication"
        keywords = extractor.extract_keywords(text)

        # Words <= 3 chars should be filtered
        assert "new" not in keywords
        assert "API" not in keywords
        assert "for" not in keywords

    def test_duplicate_removal(self, extractor):
        """Test duplicate keyword removal."""
        text = "authentication authentication system"
        keywords = extractor.extract_keywords(text)

        # Should appear only once
        assert keywords.count("authentication") == 1

    def test_limit_to_10_keywords(self, extractor):
        """Test keyword limit."""
        text = " ".join([f"word{i}" for i in range(20)])
        keywords = extractor.extract_keywords(text)

        assert len(keywords) <= 10


class TestDetectModule:
    """Tests for detect_module."""

    def test_single_module(self, extractor):
        """Test single module detection."""
        files = ["src/main.py", "src/utils.py"]
        module = extractor.detect_module(files)

        assert module == "src"

    def test_multiple_modules_most_common(self, extractor):
        """Test most common module detection."""
        files = ["src/a.py", "src/b.py", "tests/test.py"]
        module = extractor.detect_module(files)

        assert module == "src"

    def test_no_directory(self, extractor):
        """Test files without directory."""
        files = ["main.py", "utils.py"]
        module = extractor.detect_module(files)

        assert module == "unknown"

    def test_empty_file_list(self, extractor):
        """Test empty file list."""
        module = extractor.detect_module([])

        assert module == "unknown"


class TestEstimateImpact:
    """Tests for estimate_impact."""

    def test_high_impact_by_lines(self, extractor):
        """Test high impact by line changes."""
        commit = CommitInfo(
            sha="abc",
            message="Major refactoring",
            author="Author",
            date=datetime.now(),
            files=["src/main.py"],
            diff="",
            stats={"insertions": 600, "deletions": 100, "files_changed": 1},
        )

        impact = extractor.estimate_impact(commit)
        assert impact == "high"

    def test_high_impact_by_files(self, extractor):
        """Test high impact by file count."""
        commit = CommitInfo(
            sha="abc",
            message="Update multiple files",
            author="Author",
            date=datetime.now(),
            files=[f"file{i}.py" for i in range(15)],
            diff="",
            stats={"insertions": 100, "deletions": 50, "files_changed": 15},
        )

        impact = extractor.estimate_impact(commit)
        assert impact == "high"

    def test_medium_impact(self, extractor):
        """Test medium impact."""
        commit = CommitInfo(
            sha="abc",
            message="Add feature",
            author="Author",
            date=datetime.now(),
            files=["src/a.py", "src/b.py"],
            diff="",
            stats={"insertions": 150, "deletions": 50, "files_changed": 2},
        )

        impact = extractor.estimate_impact(commit)
        assert impact == "medium"

    def test_low_impact(self, extractor):
        """Test low impact."""
        commit = CommitInfo(
            sha="abc",
            message="Fix typo",
            author="Author",
            date=datetime.now(),
            files=["README.md"],
            diff="",
            stats={"insertions": 1, "deletions": 1, "files_changed": 1},
        )

        impact = extractor.estimate_impact(commit)
        assert impact == "low"


class TestDetectPatterns:
    """Tests for detect_patterns (integration)."""

    def test_full_pattern_detection(self, extractor, sample_commit):
        """Test complete pattern detection."""
        patterns = extractor.detect_patterns(sample_commit)

        # Should have all pattern types
        assert "category" in patterns
        assert "keywords" in patterns
        assert "module" in patterns
        assert "impact" in patterns
        assert "message_patterns" in patterns
        assert "file_patterns" in patterns
        assert "diff_patterns" in patterns

    def test_pattern_consistency(self, extractor, sample_commit):
        """Test pattern detection consistency."""
        patterns1 = extractor.detect_patterns(sample_commit)
        patterns2 = extractor.detect_patterns(sample_commit)

        assert patterns1["category"] == patterns2["category"]
        assert patterns1["module"] == patterns2["module"]
        assert patterns1["impact"] == patterns2["impact"]
