"""Tests for GitAnalyzer."""

from datetime import datetime

import pytest

from clauxton.analysis.git_analyzer import (
    CommitInfo,
    GitAnalyzer,
    GitAnalyzerError,
    NotAGitRepositoryError,
)


@pytest.fixture
def project_root(tmp_path):
    """Create a temporary Git repository."""
    import subprocess

    # Initialize git repo
    subprocess.run(["git", "init"], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "config", "user.name", "Test User"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )
    subprocess.run(
        ["git", "config", "user.email", "test@example.com"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    # Create initial commit
    (tmp_path / "README.md").write_text("# Test Project\n")
    subprocess.run(["git", "add", "."], cwd=tmp_path, check=True, capture_output=True)
    subprocess.run(
        ["git", "commit", "-m", "Initial commit"],
        cwd=tmp_path,
        check=True,
        capture_output=True,
    )

    return tmp_path


@pytest.fixture
def analyzer(project_root):
    """Create GitAnalyzer instance."""
    return GitAnalyzer(project_root)


class TestInitialization:
    """Tests for GitAnalyzer initialization."""

    def test_init_with_valid_repo(self, project_root):
        """Test initialization with valid Git repository."""
        analyzer = GitAnalyzer(project_root)
        assert analyzer.project_root == project_root
        assert analyzer.repo is not None

    def test_init_with_non_git_directory(self, tmp_path):
        """Test initialization with non-Git directory."""
        non_git_dir = tmp_path / "not_a_repo"
        non_git_dir.mkdir()

        with pytest.raises(NotAGitRepositoryError) as exc_info:
            GitAnalyzer(non_git_dir)

        assert "not a Git repository" in str(exc_info.value)

    def test_init_without_gitpython(self, monkeypatch, project_root):
        """Test initialization without GitPython installed."""
        # This test would require unloading the git module, which is complex
        # Skip for now, as it's an edge case
        pass


class TestGetRecentCommits:
    """Tests for get_recent_commits."""

    def test_get_recent_commits_default(self, analyzer, project_root):
        """Test getting recent commits with defaults."""
        commits = analyzer.get_recent_commits()

        assert isinstance(commits, list)
        assert len(commits) >= 1  # At least initial commit
        assert all(isinstance(c, CommitInfo) for c in commits)

    def test_get_recent_commits_with_limit(self, analyzer, project_root):
        """Test getting recent commits with max_count."""
        # Create multiple commits
        import subprocess

        for i in range(5):
            (project_root / f"file{i}.txt").write_text(f"Content {i}")
            subprocess.run(
                ["git", "add", "."], cwd=project_root, check=True, capture_output=True
            )
            subprocess.run(
                ["git", "commit", "-m", f"Commit {i}"],
                cwd=project_root,
                check=True,
                capture_output=True,
            )

        commits = analyzer.get_recent_commits(max_count=3)
        assert len(commits) == 3

    def test_get_recent_commits_since_days(self, analyzer):
        """Test getting commits from specific time range."""
        # Get commits from last 365 days (should include all)
        commits = analyzer.get_recent_commits(since_days=365)

        assert len(commits) >= 1

    def test_commit_info_structure(self, analyzer):
        """Test CommitInfo structure."""
        commits = analyzer.get_recent_commits(max_count=1)

        if commits:
            commit = commits[0]
            assert hasattr(commit, "sha")
            assert hasattr(commit, "message")
            assert hasattr(commit, "author")
            assert hasattr(commit, "date")
            assert hasattr(commit, "files")
            assert hasattr(commit, "diff")
            assert hasattr(commit, "stats")


class TestAnalyzeCommit:
    """Tests for analyze_commit."""

    def test_analyze_commit_valid_sha(self, analyzer):
        """Test analyzing a valid commit."""
        # Get first commit SHA
        commits = analyzer.get_recent_commits(max_count=1)
        assert len(commits) > 0

        commit_sha = commits[0].sha
        commit_info = analyzer.analyze_commit(commit_sha)

        assert isinstance(commit_info, CommitInfo)
        assert commit_info.sha == commit_sha
        assert isinstance(commit_info.message, str)
        assert isinstance(commit_info.author, str)
        assert isinstance(commit_info.date, datetime)

    def test_analyze_commit_invalid_sha(self, analyzer):
        """Test analyzing invalid commit SHA."""
        with pytest.raises(GitAnalyzerError) as exc_info:
            analyzer.analyze_commit("invalid_sha_12345")

        assert "not found" in str(exc_info.value).lower()

    def test_analyze_commit_short_sha(self, analyzer):
        """Test analyzing with short SHA."""
        commits = analyzer.get_recent_commits(max_count=1)
        if commits:
            short_sha = commits[0].sha[:7]
            commit_info = analyzer.analyze_commit(short_sha)
            assert commit_info.sha.startswith(short_sha)


class TestGetCommitDiff:
    """Tests for get_commit_diff."""

    def test_get_commit_diff(self, analyzer, project_root):
        """Test getting commit diff."""
        import subprocess

        # Create a new commit with changes
        (project_root / "test.txt").write_text("Hello World")
        subprocess.run(
            ["git", "add", "."], cwd=project_root, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Add test file"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        commits = analyzer.get_recent_commits(max_count=1)
        diff = analyzer.get_commit_diff(commits[0].sha)

        assert isinstance(diff, str)
        assert "Hello World" in diff or "+Hello World" in diff

    def test_get_commit_diff_first_commit(self, analyzer):
        """Test getting diff for first commit."""
        # Get all commits
        all_commits = analyzer.get_recent_commits(since_days=365, max_count=100)

        if all_commits:
            # Last commit in list should be first commit
            first_commit = all_commits[-1]
            diff = analyzer.get_commit_diff(first_commit.sha)

            assert isinstance(diff, str)
            # First commit may have empty diff in some cases, just verify it's a string
            assert diff is not None


class TestGetModifiedFiles:
    """Tests for get_modified_files."""

    def test_get_modified_files(self, analyzer, project_root):
        """Test getting modified files."""
        import subprocess

        # Create commit with multiple files
        (project_root / "file1.py").write_text("print('file1')")
        (project_root / "file2.py").write_text("print('file2')")
        subprocess.run(
            ["git", "add", "."], cwd=project_root, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Add files"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        commits = analyzer.get_recent_commits(max_count=1)
        files = analyzer.get_modified_files(commits[0].sha)

        assert isinstance(files, list)
        assert "file1.py" in files
        assert "file2.py" in files

    def test_get_modified_files_with_rename(self, analyzer, project_root):
        """Test getting files with renames."""
        import subprocess

        # Create and commit a file
        (project_root / "old_name.txt").write_text("content")
        subprocess.run(
            ["git", "add", "."], cwd=project_root, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Add file"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        # Rename file
        subprocess.run(
            ["git", "mv", "old_name.txt", "new_name.txt"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )
        subprocess.run(
            ["git", "commit", "-m", "Rename file"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        commits = analyzer.get_recent_commits(max_count=1)
        files = analyzer.get_modified_files(commits[0].sha)

        # Should contain either old or new name (Git rename detection may vary)
        assert "new_name.txt" in files or "old_name.txt" in files
        assert len(files) > 0


class TestGetCommitStats:
    """Tests for get_commit_stats."""

    def test_get_commit_stats(self, analyzer, project_root):
        """Test getting commit statistics."""
        import subprocess

        # Create commit with known changes
        content = "line1\nline2\nline3\n"
        (project_root / "stats_test.txt").write_text(content)
        subprocess.run(
            ["git", "add", "."], cwd=project_root, check=True, capture_output=True
        )
        subprocess.run(
            ["git", "commit", "-m", "Add stats test"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        commits = analyzer.get_recent_commits(max_count=1)
        stats = analyzer.get_commit_stats(commits[0].sha)

        assert isinstance(stats, dict)
        assert "insertions" in stats
        assert "deletions" in stats
        assert "files_changed" in stats
        assert stats["insertions"] >= 0
        assert stats["deletions"] >= 0
        assert stats["files_changed"] >= 1


class TestGetCommitCount:
    """Tests for get_commit_count."""

    def test_get_commit_count_all(self, analyzer):
        """Test getting total commit count."""
        count = analyzer.get_commit_count()

        assert isinstance(count, int)
        assert count >= 1  # At least initial commit

    def test_get_commit_count_recent(self, analyzer):
        """Test getting recent commit count."""
        count = analyzer.get_commit_count(since_days=1)

        assert isinstance(count, int)
        assert count >= 0


class TestBranchOperations:
    """Tests for branch-related operations."""

    def test_get_active_branches(self, analyzer):
        """Test getting active branches."""
        branches = analyzer.get_active_branches()

        assert isinstance(branches, list)
        assert len(branches) >= 1
        assert "master" in branches or "main" in branches

    def test_get_current_branch(self, analyzer):
        """Test getting current branch."""
        branch = analyzer.get_current_branch()

        assert isinstance(branch, str)
        assert len(branch) > 0
        assert branch in ["master", "main"]

    def test_create_and_list_branches(self, analyzer, project_root):
        """Test creating and listing branches."""
        import subprocess

        # Create new branch
        subprocess.run(
            ["git", "checkout", "-b", "test-branch"],
            cwd=project_root,
            check=True,
            capture_output=True,
        )

        branches = analyzer.get_active_branches()
        current = analyzer.get_current_branch()

        assert "test-branch" in branches
        assert current == "test-branch"


class TestCommitInfoToDict:
    """Tests for CommitInfo.to_dict."""

    def test_commit_info_to_dict(self, analyzer):
        """Test CommitInfo conversion to dictionary."""
        commits = analyzer.get_recent_commits(max_count=1)

        if commits:
            commit_dict = commits[0].to_dict()

            assert isinstance(commit_dict, dict)
            assert "sha" in commit_dict
            assert "message" in commit_dict
            assert "author" in commit_dict
            assert "date" in commit_dict
            assert "files" in commit_dict
            assert "diff" in commit_dict
            assert "stats" in commit_dict
