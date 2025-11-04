"""
Tests for memory extraction from Git commits.

This module tests the MemoryExtractor class, which automatically extracts
architectural decisions and code patterns from Git commit history.
"""

import re
import time
from pathlib import Path

import pytest

from clauxton.semantic.memory_extractor import MemoryExtractor

# Import Git-related classes
try:
    from git import Repo

    GITPYTHON_AVAILABLE = True
except ImportError:
    GITPYTHON_AVAILABLE = False


@pytest.fixture
def git_repo(tmp_path: Path) -> Path:
    """Create a temporary Git repository for testing."""
    if not GITPYTHON_AVAILABLE:
        pytest.skip("GitPython not available")

    # Initialize Git repo
    repo = Repo.init(tmp_path)

    # Configure Git user
    with repo.config_writer() as config:
        config.set_value("user", "name", "Test User")
        config.set_value("user", "email", "test@example.com")

    # Create initial commit
    readme = tmp_path / "README.md"
    readme.write_text("# Test Project\n")
    repo.index.add([str(readme)])
    repo.index.commit("Initial commit")

    return tmp_path


@pytest.fixture
def extractor(git_repo: Path) -> MemoryExtractor:
    """Create MemoryExtractor instance for testing."""
    return MemoryExtractor(git_repo)


# ============================================================================
# Test: Decision Extraction from Feat Commits
# ============================================================================


def test_extract_decision_from_feat_commit(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting decision from 'feat:' commit."""
    # Create commit with feat pattern
    repo = Repo(git_repo)
    test_file = git_repo / "api" / "users.py"
    test_file.parent.mkdir(exist_ok=True)
    test_file.write_text("def get_user(): pass\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("feat: Add user authentication with JWT")

    # Extract memories
    memories = extractor.extract_from_commit(commit.hexsha)

    # Assertions
    assert len(memories) >= 1
    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert "authentication" in decision.title.lower() or "jwt" in decision.title.lower()
    assert decision.category in ["api", "security", "general"]
    assert decision.confidence >= 0.7
    assert decision.source == "git-commit"
    assert decision.source_ref == commit.hexsha
    assert "authentication" in decision.tags or "jwt" in decision.tags


def test_extract_decision_from_feat_with_body(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting decision from feat commit with body."""
    repo = Repo(git_repo)
    test_file = git_repo / "auth.py"
    test_file.write_text("def authenticate(): pass\n")
    repo.index.add([str(test_file)])
    commit_message = """feat: Add OAuth2 authentication

We are switching to OAuth2 for better security and user experience.
This includes support for Google and GitHub providers."""
    commit = repo.index.commit(commit_message)

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert "oauth" in decision.tags or "authentication" in decision.tags or "auth" in decision.tags
    assert "Details:" in decision.content or "OAuth2" in decision.content


# ============================================================================
# Test: Decision Extraction from Migration Commits
# ============================================================================


def test_extract_decision_from_migration_commit(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting decision from migration commit."""
    repo = Repo(git_repo)
    test_file = git_repo / "config.py"
    test_file.write_text("DATABASE = 'postgresql'\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("Migrate to PostgreSQL from MySQL")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert "postgresql" in decision.title.lower() or "mysql" in decision.title.lower()
    assert decision.confidence >= 0.85  # Migration should have high confidence
    assert decision.category in ["database", "architecture", "general"]


def test_extract_decision_from_switch_commit(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting decision from 'switch to' commit."""
    repo = Repo(git_repo)
    test_file = git_repo / "cache.py"
    test_file.write_text("CACHE = 'redis'\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("Switch to Redis for caching")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert "redis" in decision.title.lower()
    assert decision.confidence >= 0.85
    assert "redis" in decision.tags or "cache" in decision.tags


# ============================================================================
# Test: Decision Extraction from Refactor Commits
# ============================================================================


def test_extract_decision_from_refactor_commit(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting decision from refactor commit."""
    repo = Repo(git_repo)
    test_file = git_repo / "api.py"
    test_file.write_text("class API: pass\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("refactor: Restructure API module for better maintainability")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert "api" in decision.title.lower() or "restructure" in decision.title.lower()
    assert decision.confidence >= 0.6
    assert decision.category in ["api", "architecture", "general"]


# ============================================================================
# Test: Pattern Detection
# ============================================================================


def test_detect_api_pattern(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test detecting API pattern from multiple API files."""
    repo = Repo(git_repo)

    # Create multiple API files
    api_dir = git_repo / "api"
    api_dir.mkdir(exist_ok=True)
    for i in range(3):
        api_file = api_dir / f"endpoint_{i}.py"
        api_file.write_text(f"def handler_{i}(): pass\n")
        repo.index.add([str(api_file)])

    commit = repo.index.commit("Add new API endpoints")

    memories = extractor.extract_from_commit(commit.hexsha)

    pattern = next((m for m in memories if m.type == "pattern" and m.category == "api"), None)
    assert pattern is not None
    assert pattern.confidence >= 0.7
    assert "api" in pattern.tags
    assert pattern.source == "git-commit"


def test_detect_ui_pattern(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test detecting UI pattern from multiple UI files."""
    repo = Repo(git_repo)

    # Create multiple UI files
    ui_dir = git_repo / "components"
    ui_dir.mkdir(exist_ok=True)
    for i in range(4):
        ui_file = ui_dir / f"Component{i}.tsx"
        ui_file.write_text(f"export const Component{i} = () => <div></div>;\n")
        repo.index.add([str(ui_file)])

    commit = repo.index.commit("Update UI components")

    memories = extractor.extract_from_commit(commit.hexsha)

    pattern = next((m for m in memories if m.type == "pattern" and m.category == "ui"), None)
    assert pattern is not None
    assert pattern.confidence >= 0.6
    assert "ui" in pattern.tags


def test_detect_database_pattern(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test detecting database pattern from migration file."""
    repo = Repo(git_repo)

    # Create migration file
    migration_file = git_repo / "migrations" / "001_initial.sql"
    migration_file.parent.mkdir(exist_ok=True)
    migration_file.write_text("CREATE TABLE users (id INT PRIMARY KEY);\n")
    repo.index.add([str(migration_file)])

    commit = repo.index.commit("Add initial database migration")

    memories = extractor.extract_from_commit(commit.hexsha)

    pattern = next((m for m in memories if m.type == "pattern" and m.category == "database"), None)
    assert pattern is not None
    assert pattern.confidence >= 0.85  # Database patterns should have high confidence
    assert "database" in pattern.tags


def test_detect_test_pattern(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test detecting test pattern from multiple test files."""
    repo = Repo(git_repo)

    # Create test files
    test_dir = git_repo / "tests"
    test_dir.mkdir(exist_ok=True)
    for i in range(3):
        test_file = test_dir / f"test_feature_{i}.py"
        test_file.write_text(f"def test_feature_{i}(): pass\n")
        repo.index.add([str(test_file)])

    commit = repo.index.commit("Add tests for new features")

    memories = extractor.extract_from_commit(commit.hexsha)

    pattern = next((m for m in memories if m.type == "pattern" and m.category == "test"), None)
    assert pattern is not None
    assert pattern.confidence >= 0.5
    assert "test" in pattern.tags


# ============================================================================
# Test: Extract from Recent Commits
# ============================================================================


def test_extract_from_recent_commits(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting from recent commits."""
    repo = Repo(git_repo)

    # Create multiple commits
    for i in range(5):
        test_file = git_repo / f"file_{i}.py"
        test_file.write_text(f"# File {i}\n")
        repo.index.add([str(test_file)])
        repo.index.commit(f"feat: Add feature {i}")

    # Extract from last 7 days
    memories = extractor.extract_from_recent_commits(since_days=7)

    # Should extract decisions from all commits
    assert len(memories) >= 5
    decisions = [m for m in memories if m.type == "decision"]
    assert len(decisions) >= 5


def test_extract_from_recent_commits_with_auto_add(
    git_repo: Path, extractor: MemoryExtractor
) -> None:
    """Test extracting from recent commits with auto-add."""
    repo = Repo(git_repo)

    # Create commit
    test_file = git_repo / "auth.py"
    test_file.write_text("def authenticate(): pass\n")
    repo.index.add([str(test_file)])
    repo.index.commit("feat: Add authentication")

    # Extract with auto-add
    memories = extractor.extract_from_recent_commits(since_days=7, auto_add=True)

    # Verify memories were added to storage
    assert len(memories) >= 1
    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None

    # Verify in storage
    stored = extractor.memory.get(decision.id)
    assert stored is not None
    assert stored.id == decision.id


# ============================================================================
# Test: Edge Cases
# ============================================================================


def test_extract_from_initial_commit(git_repo: Path) -> None:
    """Test extracting from initial commit (no parent)."""
    # The fixture already creates an initial commit
    extractor = MemoryExtractor(git_repo)
    repo = Repo(git_repo)

    # Get initial commit
    commits = list(repo.iter_commits())
    initial_commit = commits[-1]  # First commit is last in list

    # Extract memories (should not crash)
    memories = extractor.extract_from_commit(initial_commit.hexsha)

    # May or may not extract memories, but should not crash
    assert isinstance(memories, list)


def test_extract_from_merge_commit(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting from merge commit (multiple parents)."""
    repo = Repo(git_repo)

    # Create a branch
    main_branch = repo.active_branch
    feature_branch = repo.create_head("feature")
    feature_branch.checkout()

    # Add commit in feature branch
    test_file = git_repo / "feature.py"
    test_file.write_text("def feature(): pass\n")
    repo.index.add([str(test_file)])
    repo.index.commit("feat: Add feature")

    # Switch back to main
    main_branch.checkout()

    # Create merge commit
    repo.git.merge("feature", "--no-ff", "-m", "Merge feature branch")

    # Get merge commit
    merge_commit = repo.head.commit

    # Extract memories (should handle merge commit)
    memories = extractor.extract_from_commit(merge_commit.hexsha)

    # Should extract decision from merge message
    assert isinstance(memories, list)


def test_extract_from_empty_commit_message(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting from commit with minimal message."""
    repo = Repo(git_repo)
    test_file = git_repo / "test.py"
    test_file.write_text("# Test\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("Update")

    memories = extractor.extract_from_commit(commit.hexsha)

    # Should not extract decision from generic message
    decisions = [m for m in memories if m.type == "decision"]
    assert len(decisions) == 0


def test_extract_from_very_long_commit_message(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting from commit with very long message."""
    repo = Repo(git_repo)
    test_file = git_repo / "test.py"
    test_file.write_text("# Test\n")
    repo.index.add([str(test_file)])

    # Create very long commit message
    long_message = "feat: " + "A" * 500 + "\n\nThis is a very long body. " * 100
    commit = repo.index.commit(long_message)

    memories = extractor.extract_from_commit(commit.hexsha)

    # Should extract decision and truncate title to 200 chars
    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert len(decision.title) <= 200


def test_extract_from_special_characters_in_message(
    git_repo: Path, extractor: MemoryExtractor
) -> None:
    """Test extracting from commit with special characters."""
    repo = Repo(git_repo)
    test_file = git_repo / "test.py"
    test_file.write_text("# Test\n")
    repo.index.add([str(test_file)])

    # Commit with special characters
    commit = repo.index.commit("feat: Add authentication with 🔒 JWT & OAuth2")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    # Should handle Unicode characters gracefully
    assert len(decision.title) > 0


def test_extract_from_commit_with_no_files(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test extracting from commit with no file changes (edge case)."""
    repo = Repo(git_repo)

    # Create empty commit (allowed with --allow-empty)
    repo.git.commit("--allow-empty", "-m", "feat: Add feature (documentation only)")

    # Get the empty commit
    commit = repo.head.commit

    memories = extractor.extract_from_commit(commit.hexsha)

    # Should still extract decision from message
    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None


# ============================================================================
# Test: Tag Extraction
# ============================================================================


def test_extract_tags_from_commit_message(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test tag extraction from commit message."""
    repo = Repo(git_repo)
    test_file = git_repo / "test.py"
    test_file.write_text("# Test\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("feat: Add REST API with Redis cache and PostgreSQL database")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    # Should extract multiple relevant tags
    assert any(tag in decision.tags for tag in ["api", "rest"])
    assert any(tag in decision.tags for tag in ["redis", "cache"])
    assert any(tag in decision.tags for tag in ["postgresql", "postgres", "database"])


# ============================================================================
# Test: Category Determination
# ============================================================================


def test_determine_category_from_message(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test category determination from commit message."""
    repo = Repo(git_repo)
    test_file = git_repo / "test.py"
    test_file.write_text("# Test\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("feat: Add database migration for users table")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert decision.category == "database"


def test_determine_category_from_files(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test category determination from modified files."""
    repo = Repo(git_repo)

    # Create API file
    api_file = git_repo / "api" / "users.py"
    api_file.parent.mkdir(exist_ok=True)
    api_file.write_text("def get_users(): pass\n")
    repo.index.add([str(api_file)])
    commit = repo.index.commit("feat: Add new feature")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    # Should infer 'api' category from file path
    assert decision.category in ["api", "general"]


# ============================================================================
# Test: Performance
# ============================================================================


def test_extraction_performance(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test that extraction is fast (<100ms per commit)."""
    repo = Repo(git_repo)

    # Create a commit with multiple files
    for i in range(10):
        test_file = git_repo / f"file_{i}.py"
        test_file.write_text(f"# File {i}\n" * 100)
        repo.index.add([str(test_file)])
    commit = repo.index.commit("feat: Add multiple features")

    # Measure extraction time
    start = time.time()
    memories = extractor.extract_from_commit(commit.hexsha)
    elapsed = (time.time() - start) * 1000  # Convert to ms

    # Should complete in <100ms
    assert elapsed < 100
    assert len(memories) >= 1


# ============================================================================
# Test: Confidence Scoring
# ============================================================================


def test_confidence_scoring_migration(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test confidence scoring for migration commits (high confidence)."""
    repo = Repo(git_repo)
    test_file = git_repo / "config.py"
    test_file.write_text("DB = 'postgres'\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("Migrate to PostgreSQL")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert decision.confidence >= 0.85  # Migration should have high confidence


def test_confidence_scoring_feature(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test confidence scoring for feature commits (medium confidence)."""
    repo = Repo(git_repo)
    test_file = git_repo / "feature.py"
    test_file.write_text("def feature(): pass\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("feat: Add new feature")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert 0.7 <= decision.confidence <= 0.9


def test_confidence_scoring_refactor(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test confidence scoring for refactor commits (medium confidence)."""
    repo = Repo(git_repo)
    test_file = git_repo / "code.py"
    test_file.write_text("# Refactored\n")
    repo.index.add([str(test_file)])
    commit = repo.index.commit("refactor: Improve code structure")

    memories = extractor.extract_from_commit(commit.hexsha)

    decision = next((m for m in memories if m.type == "decision"), None)
    assert decision is not None
    assert 0.6 <= decision.confidence <= 0.8


# ============================================================================
# Test: Memory ID Generation
# ============================================================================


def test_memory_id_generation(git_repo: Path, extractor: MemoryExtractor) -> None:
    """Test that memory IDs are unique and follow format."""
    repo = Repo(git_repo)

    # Create multiple commits with auto_add to ensure IDs are tracked
    ids = set()
    for i in range(5):
        test_file = git_repo / f"file_{i}.py"
        test_file.write_text(f"# File {i}\n")
        repo.index.add([str(test_file)])
        commit = repo.index.commit(f"feat: Add feature {i}")

        memories = extractor.extract_from_commit(commit.hexsha, auto_add=True)
        for memory in memories:
            # Check ID format: MEM-YYYYMMDD-NNN
            assert re.match(r"^MEM-\d{8}-\d{3}$", memory.id)
            # Check uniqueness
            assert memory.id not in ids
            ids.add(memory.id)
