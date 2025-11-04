"""
Git commit analyzer for Clauxton.

This module analyzes Git commit history to extract patterns, decisions, and insights.
"""

from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

try:
    from git import Commit, InvalidGitRepositoryError, Repo
except ImportError:
    Repo = None  # type: ignore
    Commit = None  # type: ignore
    InvalidGitRepositoryError = Exception  # type: ignore


class GitAnalyzerError(Exception):
    """Base exception for GitAnalyzer errors."""
    pass


class NotAGitRepositoryError(GitAnalyzerError):
    """Raised when the project is not a Git repository."""
    pass


class CommitInfo:
    """Structured commit information."""

    def __init__(
        self,
        sha: str,
        message: str,
        author: str,
        date: datetime,
        files: List[str],
        diff: str,
        stats: Dict[str, int],
    ):
        self.sha = sha
        self.message = message
        self.author = author
        self.date = date
        self.files = files
        self.diff = diff
        self.stats = stats

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "sha": self.sha,
            "message": self.message,
            "author": self.author,
            "date": self.date.isoformat(),
            "files": self.files,
            "diff": self.diff,
            "stats": self.stats,
        }


class GitAnalyzer:
    """
    Git commit analyzer.

    Analyzes Git commit history to extract patterns and insights.
    """

    def __init__(self, project_root: Path):
        """
        Initialize GitAnalyzer.

        Args:
            project_root: Path to project root directory

        Raises:
            NotAGitRepositoryError: If project is not a Git repository
            ImportError: If GitPython is not installed
        """
        if Repo is None:
            raise ImportError(
                "GitPython is required for commit analysis. "
                "Install with: pip install gitpython"
            )

        self.project_root = project_root
        try:
            self.repo = Repo(project_root)
        except InvalidGitRepositoryError:
            raise NotAGitRepositoryError(
                f"{project_root} is not a Git repository. "
                "Initialize with 'git init' first."
            )

    def get_recent_commits(
        self,
        since_days: int = 7,
        max_count: Optional[int] = None,
        branch: Optional[str] = None,
    ) -> List[CommitInfo]:
        """
        Get recent commits.

        Args:
            since_days: Number of days to look back (default: 7)
            max_count: Maximum number of commits to return
            branch: Branch name (default: current branch)

        Returns:
            List of CommitInfo objects
        """
        since_date = datetime.now() - timedelta(days=since_days)

        # Get commits
        commits_iter = self.repo.iter_commits(
            rev=branch,
            since=since_date,
            max_count=max_count,
        )

        commit_infos = []
        for commit in commits_iter:
            info = self.analyze_commit(commit.hexsha)
            commit_infos.append(info)

        return commit_infos

    def analyze_commit(self, commit_sha: str) -> CommitInfo:
        """
        Analyze a specific commit.

        Args:
            commit_sha: Commit SHA hash

        Returns:
            CommitInfo object

        Raises:
            GitAnalyzerError: If commit not found
        """
        try:
            commit = self.repo.commit(commit_sha)
        except Exception as e:
            raise GitAnalyzerError(f"Commit {commit_sha} not found: {e}")

        # Get modified files
        files = self.get_modified_files(commit_sha)

        # Get diff
        diff = self.get_commit_diff(commit_sha)

        # Get stats
        stats = self.get_commit_stats(commit_sha)

        # Handle message (str or bytes)
        message = commit.message
        if isinstance(message, bytes):
            message = message.decode("utf-8", errors="ignore")
        message = message.strip()

        # Handle author name (may be None)
        author_name = commit.author.name if commit.author.name else "Unknown"

        return CommitInfo(
            sha=commit.hexsha,
            message=message,
            author=author_name,
            date=datetime.fromtimestamp(commit.committed_date),
            files=files,
            diff=diff,
            stats=stats,
        )

    def get_commit_diff(self, commit_sha: str) -> str:
        """
        Get commit diff.

        Args:
            commit_sha: Commit SHA hash

        Returns:
            Diff as string
        """
        commit = self.repo.commit(commit_sha)

        # Get diff with parent (or empty tree for first commit)
        if commit.parents:
            parent = commit.parents[0]
            diff = commit.diff(parent, create_patch=True)
        else:
            # First commit - diff against empty tree
            diff = commit.diff(None, create_patch=True)

        # Convert to string
        diff_str = ""
        for diff_item in diff:
            if diff_item.diff:
                diff_content = diff_item.diff
                if isinstance(diff_content, bytes):
                    diff_str += diff_content.decode("utf-8", errors="ignore")
                else:
                    diff_str += diff_content

        return diff_str

    def get_modified_files(self, commit_sha: str) -> List[str]:
        """
        Get list of modified files.

        Args:
            commit_sha: Commit SHA hash

        Returns:
            List of file paths
        """
        commit = self.repo.commit(commit_sha)

        files = []
        if commit.parents:
            parent = commit.parents[0]
            diff = commit.diff(parent)
        else:
            diff = commit.diff(None)

        for diff_item in diff:
            # Handle renamed files
            if diff_item.renamed_file and diff_item.rename_to:
                files.append(diff_item.rename_to)
            elif diff_item.a_path:
                files.append(diff_item.a_path)
            elif diff_item.b_path:
                files.append(diff_item.b_path)

        return files

    def get_commit_stats(self, commit_sha: str) -> Dict[str, int]:
        """
        Get commit statistics.

        Args:
            commit_sha: Commit SHA hash

        Returns:
            Dictionary with stats: insertions, deletions, files_changed
        """
        commit = self.repo.commit(commit_sha)

        insertions = 0
        deletions = 0
        files_changed = 0

        if commit.parents:
            parent = commit.parents[0]
            diff = commit.diff(parent, create_patch=True)
        else:
            diff = commit.diff(None, create_patch=True)

        for diff_item in diff:
            files_changed += 1
            # Parse diff stats
            if hasattr(diff_item, 'diff') and diff_item.diff:
                diff_content = diff_item.diff
                if isinstance(diff_content, bytes):
                    diff_str = diff_content.decode("utf-8", errors="ignore")
                else:
                    diff_str = diff_content
                for line in diff_str.split("\n"):
                    if line.startswith("+") and not line.startswith("+++"):
                        insertions += 1
                    elif line.startswith("-") and not line.startswith("---"):
                        deletions += 1

        return {
            "insertions": insertions,
            "deletions": deletions,
            "files_changed": files_changed,
        }

    def get_commit_count(
        self,
        since_days: Optional[int] = None,
        branch: Optional[str] = None,
    ) -> int:
        """
        Get number of commits.

        Args:
            since_days: Number of days to look back
            branch: Branch name (default: current branch)

        Returns:
            Number of commits
        """
        if since_days:
            since_date = datetime.now() - timedelta(days=since_days)
            return sum(1 for _ in self.repo.iter_commits(rev=branch, since=since_date))
        else:
            return sum(1 for _ in self.repo.iter_commits(rev=branch))

    def get_active_branches(self) -> List[str]:
        """
        Get list of active branches.

        Returns:
            List of branch names
        """
        return [branch.name for branch in self.repo.branches]

    def get_current_branch(self) -> str:
        """
        Get current branch name.

        Returns:
            Branch name
        """
        return str(self.repo.active_branch.name)
