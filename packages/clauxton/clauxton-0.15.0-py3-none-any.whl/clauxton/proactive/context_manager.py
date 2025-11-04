"""
Project context awareness for intelligent, context-aware suggestions.

This module provides rich contextual information about the current project state,
including git branch, active files, recent commits, and time-based context.
"""

import logging
import re
import subprocess
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger(__name__)

# Week 3: Context Intelligence Constants
BREAK_THRESHOLD_MINUTES = 15  # Minimum gap to be considered a break
HIGH_FOCUS_THRESHOLD = 5  # File switches per hour for high focus
MEDIUM_FOCUS_THRESHOLD = 15  # File switches per hour for medium focus
SESSION_LOOKBACK_HOURS = 2  # How far back to look for session start


class ProjectContext(BaseModel):
    """Rich project context for intelligent suggestions."""

    model_config = ConfigDict(
        json_encoders={datetime: lambda v: v.isoformat()}
    )

    current_branch: Optional[str] = Field(
        None, description="Current git branch name"
    )
    active_files: List[str] = Field(
        default_factory=list, description="Recently modified files"
    )
    recent_commits: List[Dict[str, str]] = Field(
        default_factory=list, description="Recent commit information"
    )
    current_task: Optional[str] = Field(
        None, description="Current task ID from task manager"
    )
    time_context: str = Field(
        "unknown", description="Time context: morning, afternoon, evening, night"
    )
    work_session_start: Optional[datetime] = Field(
        None, description="When current work session started"
    )
    last_activity: Optional[datetime] = Field(
        None, description="Last detected activity"
    )
    is_feature_branch: bool = Field(
        False, description="Whether current branch is a feature branch"
    )
    is_git_repo: bool = Field(True, description="Whether project is a git repository")

    # Week 3: Session analysis
    session_duration_minutes: Optional[int] = Field(
        None, description="Current session duration in minutes"
    )
    focus_score: Optional[float] = Field(
        None, description="Focus score (0.0-1.0), based on file switch frequency"
    )
    breaks_detected: int = Field(
        0, description="Number of breaks detected in current session"
    )

    # Week 3: Prediction
    predicted_next_action: Optional[Dict[str, Any]] = Field(
        None, description="Predicted next action based on patterns"
    )
    prediction_error: Optional[str] = Field(
        None, description="Error message if prediction failed"
    )

    # Week 3: Enhanced git stats
    uncommitted_changes: int = Field(
        0, description="Number of uncommitted changes"
    )
    diff_stats: Optional[Dict[str, int]] = Field(
        None, description="Git diff statistics (additions, deletions, files_changed)"
    )


class ContextManager:
    """Manage and provide project context."""

    def __init__(self, project_root: Path):
        """
        Initialize context manager.

        Args:
            project_root: Root directory of the project
        """
        self.project_root = Path(project_root)
        self._cache: Dict[str, Any] = {}
        self._cache_timeout = timedelta(seconds=30)  # Cache for 30 seconds

    def get_current_context(self, include_prediction: bool = True) -> ProjectContext:
        """
        Get comprehensive project context.

        Args:
            include_prediction: Whether to include next action prediction (default: True)
                               Set to False to avoid circular dependency

        Returns:
            ProjectContext with all available information
        """
        # Check cache
        cache_key = f"current_context_{include_prediction}"
        if cache_key in self._cache:
            cached_data = self._cache[cache_key]
            cached_context: ProjectContext = cached_data[0]
            cached_time: datetime = cached_data[1]
            age = datetime.now() - cached_time
            if age < self._cache_timeout:
                logger.debug(
                    f"Cache hit for {cache_key} (age: {age.total_seconds():.1f}s, "
                    f"timeout: {self._cache_timeout.total_seconds()}s)"
                )
                return cached_context
            else:
                logger.debug(
                    f"Cache expired for {cache_key} (age: {age.total_seconds():.1f}s)"
                )
        else:
            logger.debug(f"Cache miss for {cache_key}")

        # Week 3: Calculate new fields
        session_duration = self._calculate_session_duration()
        focus_score = self._calculate_focus_score()
        breaks = self._detect_breaks()
        uncommitted = self._count_uncommitted_changes()
        diff_stats = self._get_git_diff_stats()

        # Build fresh context (without prediction first to avoid circular dependency)
        context = ProjectContext(
            # Original fields
            current_branch=self._get_current_branch(),
            active_files=self.detect_active_files(minutes=30),
            recent_commits=self._get_recent_commits(limit=5),
            current_task=self._infer_current_task(),
            time_context=self.get_time_context(),
            work_session_start=self._estimate_session_start(),
            last_activity=datetime.now(),
            is_feature_branch=self._is_feature_branch(),
            is_git_repo=self._is_git_repository(),
            # Week 3: New fields
            session_duration_minutes=session_duration,
            focus_score=round(focus_score, 2) if focus_score else None,
            breaks_detected=len(breaks),
            uncommitted_changes=uncommitted,
            diff_stats=diff_stats,
            predicted_next_action=None,  # Will be populated below if needed
            prediction_error=None,
        )

        # Cache the basic context temporarily for prediction
        self._cache[cache_key] = (context, datetime.now())

        # Add prediction if requested (uses the cached context above)
        if include_prediction:
            try:
                prediction = self._predict_next_action_internal(context)
                context = ProjectContext(
                    **context.model_dump(exclude={"predicted_next_action", "prediction_error"}),
                    predicted_next_action=prediction,
                    prediction_error=None,
                )
                # Update cache with full context
                self._cache[cache_key] = (context, datetime.now())
            except Exception as e:
                logger.error(f"Error predicting next action: {e}")
                # Surface error to caller
                context = ProjectContext(
                    **context.model_dump(exclude={"predicted_next_action", "prediction_error"}),
                    predicted_next_action=None,
                    prediction_error=str(e),
                )
                # Update cache with error context
                self._cache[cache_key] = (context, datetime.now())

        return context

    def _predict_next_action_internal(
        self, context: ProjectContext
    ) -> Dict[str, Any]:
        """
        Internal prediction method that uses provided context.

        Args:
            context: ProjectContext to use for prediction

        Returns:
            Dictionary with prediction details
        """
        predictions: List[Dict[str, Any]] = []

        # 1. File change patterns
        active_files = context.active_files

        # Check for test files
        test_files = [f for f in active_files if "test" in f.lower()]
        impl_files = [
            f
            for f in active_files
            if f.endswith(".py") and "test" not in f.lower()
        ]

        if test_files:
            predictions.append(
                {
                    "action": "run_tests",
                    "confidence": 0.80,
                    "reasoning": f"{len(test_files)} test file(s) recently modified",
                }
            )
        elif impl_files and not test_files:
            predictions.append(
                {
                    "action": "write_tests",
                    "confidence": 0.70,
                    "reasoning": f"{len(impl_files)} implementation file(s) modified without tests",
                }
            )

        # 2. Git context - uncommitted changes
        uncommitted = context.uncommitted_changes
        if uncommitted >= 10:
            predictions.append(
                {
                    "action": "commit_changes",
                    "confidence": 0.85,
                    "reasoning": f"{uncommitted} uncommitted file(s) - good time to commit",
                }
            )
        elif uncommitted >= 5:
            predictions.append(
                {
                    "action": "review_changes",
                    "confidence": 0.70,
                    "reasoning": f"{uncommitted} uncommitted file(s) - review before committing",
                }
            )

        # 3. Feature branch with many changes
        if context.is_feature_branch and uncommitted >= 15:
            predictions.append(
                {
                    "action": "create_pr",
                    "confidence": 0.75,
                    "reasoning": f"Feature branch with {uncommitted} changes - ready for PR",
                }
            )

        # 4. Time context
        time_ctx = context.time_context
        if time_ctx == "morning" and uncommitted < 3:
            predictions.append(
                {
                    "action": "planning",
                    "confidence": 0.60,
                    "reasoning": "Morning with few changes - good for planning",
                }
            )
        elif time_ctx == "evening" and uncommitted >= 3:
            predictions.append(
                {
                    "action": "documentation",
                    "confidence": 0.65,
                    "reasoning": "Evening with changes made - good for documentation",
                }
            )
        elif time_ctx == "night":
            predictions.append(
                {
                    "action": "wrap_up",
                    "confidence": 0.70,
                    "reasoning": "Late evening - consider wrapping up work",
                }
            )

        # 5. Long session with high focus
        session_duration = context.session_duration_minutes or 0
        focus_score = context.focus_score or 0.5
        if session_duration > 90 and focus_score > 0.7:
            predictions.append(
                {
                    "action": "take_break",
                    "confidence": 0.75,
                    "reasoning": f"Long focused session ({session_duration}min) - time for a break",
                }
            )

        # Return highest confidence prediction
        if predictions:
            best = max(predictions, key=lambda p: p["confidence"])
            return {
                "action": best["action"],
                "task_id": context.current_task,
                "confidence": round(best["confidence"], 2),
                "reasoning": best["reasoning"],
            }

        # Default: continue work
        return {
            "action": "continue_work",
            "task_id": context.current_task,
            "confidence": 0.50,
            "reasoning": "No clear pattern detected - continue current work",
        }

    def detect_active_files(self, minutes: int = 30) -> List[str]:
        """
        Detect recently modified files.

        Args:
            minutes: Time window in minutes (default: 30)

        Returns:
            List of file paths relative to project root
        """
        active_files: List[str] = []

        try:
            # Use find to get recently modified files
            # Search only common source directories to avoid scanning everything
            search_dirs = [".", "src", "lib", "clauxton", "tests"]

            for search_dir in search_dirs:
                dir_path = self.project_root / search_dir
                if not dir_path.exists():
                    continue

                # Find files modified in the last N minutes
                result = subprocess.run(
                    [
                        "find",
                        str(dir_path),
                        "-type",
                        "f",
                        "-mmin",
                        f"-{minutes}",
                        "-not",
                        "-path",
                        "*/.git/*",
                        "-not",
                        "-path",
                        "*/__pycache__/*",
                        "-not",
                        "-path",
                        "*/.clauxton/*",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0:
                    files = result.stdout.strip().split("\n")
                    for file_path in files:
                        if file_path:
                            try:
                                rel_path = Path(file_path).relative_to(self.project_root)
                                active_files.append(str(rel_path))
                            except ValueError:
                                pass  # Skip files outside project root

        except subprocess.TimeoutExpired:
            logger.warning(f"Timeout detecting active files in {search_dir}")
        except FileNotFoundError:
            logger.debug("find command not available")
        except Exception as e:
            logger.error(f"Error detecting active files: {e}")

        return sorted(list(set(active_files)))  # Deduplicate and sort

    def get_branch_context(self) -> Dict[str, Any]:
        """
        Get git branch information.

        Returns:
            Dictionary with branch details
        """
        return {
            "current_branch": self._get_current_branch(),
            "is_feature_branch": self._is_feature_branch(),
            "is_main_branch": self._is_main_branch(),
            "is_git_repo": self._is_git_repository(),
        }

    def get_time_context(self) -> str:
        """
        Get time-based context.

        Returns:
            "morning", "afternoon", "evening", or "night"
        """
        hour = datetime.now().hour

        if 6 <= hour < 12:
            return "morning"
        elif 12 <= hour < 17:
            return "afternoon"
        elif 17 <= hour < 22:
            return "evening"
        else:
            return "night"

    def infer_current_task(self) -> Optional[str]:
        """
        Infer what user is working on based on context.

        Returns:
            Task ID or description, if detectable
        """
        return self._infer_current_task()

    def _get_current_branch(self) -> Optional[str]:
        """
        Get current git branch name.

        Returns:
            Branch name or None if not in git repo
        """
        if not self._is_git_repository():
            return None

        try:
            result = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=2,
            )

            if result.returncode == 0:
                return result.stdout.strip()
        except subprocess.TimeoutExpired:
            logger.warning("Timeout getting git branch")
        except FileNotFoundError:
            logger.debug("git command not available")
        except Exception as e:
            logger.error(f"Error getting git branch: {e}")

        return None

    def _is_git_repository(self) -> bool:
        """
        Check if project is a git repository.

        Returns:
            True if git repository, False otherwise
        """
        git_dir = self.project_root / ".git"
        return git_dir.exists()

    def _is_feature_branch(self) -> bool:
        """
        Check if current branch is a feature branch.

        Returns:
            True if branch name suggests feature branch
        """
        branch = self._get_current_branch()
        if not branch:
            return False

        # Common feature branch prefixes
        feature_prefixes = ["feature/", "feat/", "fix/", "bugfix/", "hotfix/"]
        return any(branch.startswith(prefix) for prefix in feature_prefixes)

    def _is_main_branch(self) -> bool:
        """
        Check if current branch is main/master branch.

        Returns:
            True if main or master branch
        """
        branch = self._get_current_branch()
        return branch in ["main", "master"] if branch else False

    def _get_recent_commits(self, limit: int = 5) -> List[Dict[str, str]]:
        """
        Get recent git commits.

        Args:
            limit: Maximum number of commits to retrieve

        Returns:
            List of commit dictionaries
        """
        if not self._is_git_repository():
            return []

        try:
            result = subprocess.run(
                [
                    "git",
                    "log",
                    f"-{limit}",
                    "--pretty=format:%H|%an|%ae|%s|%ai",
                ],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode == 0:
                commits = []
                for line in result.stdout.strip().split("\n"):
                    if line:
                        parts = line.split("|")
                        if len(parts) >= 5:
                            commits.append(
                                {
                                    "hash": parts[0][:8],  # Short hash
                                    "author_name": parts[1],
                                    "author_email": parts[2],
                                    "message": parts[3],
                                    "date": parts[4],
                                }
                            )
                return commits
        except subprocess.TimeoutExpired:
            logger.warning("Timeout getting git commits")
        except FileNotFoundError:
            logger.debug("git command not available")
        except Exception as e:
            logger.error(f"Error getting git commits: {e}")

        return []

    def _infer_current_task(self) -> Optional[str]:
        """
        Infer current task from branch name or recent commits.

        Returns:
            Task ID or None
        """
        branch = self._get_current_branch()
        if not branch:
            return None

        # Try to extract task ID from branch name
        # Common patterns: feature/TASK-123, fix/TASK-456
        task_pattern = r"TASK-\d+"
        match = re.search(task_pattern, branch)
        if match:
            return match.group(0)

        # Check recent commit messages
        commits = self._get_recent_commits(limit=3)
        for commit in commits:
            match = re.search(task_pattern, commit["message"])
            if match:
                return match.group(0)

        return None

    def _estimate_session_start(self) -> Optional[datetime]:
        """
        Estimate when current work session started.

        Looks back SESSION_LOOKBACK_HOURS hours to find the oldest
        modified file, which approximates when the work session began.

        Returns:
            Estimated session start time or None if no active files
        """
        lookback_minutes = SESSION_LOOKBACK_HOURS * 60
        active_files = self.detect_active_files(minutes=lookback_minutes)

        if not active_files:
            return None

        # Try to get oldest modification time from active files
        try:
            oldest_time = None
            for file_path in active_files:
                full_path = self.project_root / file_path
                if full_path.exists():
                    mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                    if oldest_time is None or mtime < oldest_time:
                        oldest_time = mtime

            return oldest_time
        except OSError as e:
            logger.warning(f"Error accessing file stats: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error estimating session start: {e}")
            return None

    def clear_cache(self) -> None:
        """Clear the context cache."""
        self._cache.clear()

    # Week 3: Git Statistics Methods

    def _count_uncommitted_changes(self) -> int:
        """
        Count number of files with uncommitted changes.

        Returns:
            Number of files with uncommitted changes (0 if not a git repo)
        """
        if not self._is_git_repository():
            return 0

        try:
            result = subprocess.run(
                ["git", "status", "--porcelain"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=3,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                return len([line for line in lines if line.strip()])

        except subprocess.TimeoutExpired:
            logger.warning("Timeout counting uncommitted changes")
        except FileNotFoundError:
            logger.debug("git command not available")
        except Exception as e:
            logger.error(f"Error counting uncommitted changes: {e}")

        return 0

    def _get_git_diff_stats(self) -> Optional[Dict[str, int]]:
        """
        Get git diff statistics for uncommitted changes.

        Returns:
            Dictionary with keys: additions, deletions, files_changed
            or None if not a git repo or error occurs
        """
        if not self._is_git_repository():
            return None

        try:
            # Get diff stats
            result = subprocess.run(
                ["git", "diff", "--stat"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=5,
            )

            if result.returncode == 0:
                output = result.stdout.strip()
                if not output:
                    return {"additions": 0, "deletions": 0, "files_changed": 0}

                # Parse last line: "X files changed, Y insertions(+), Z deletions(-)"
                lines = output.split("\n")
                summary = lines[-1] if lines else ""

                # Extract numbers using regex
                files_match = re.search(r"(\d+) files? changed", summary)
                additions_match = re.search(r"(\d+) insertions?", summary)
                deletions_match = re.search(r"(\d+) deletions?", summary)

                return {
                    "additions": int(additions_match.group(1)) if additions_match else 0,
                    "deletions": int(deletions_match.group(1)) if deletions_match else 0,
                    "files_changed": int(files_match.group(1)) if files_match else 0,
                }

        except subprocess.TimeoutExpired:
            logger.warning("Timeout getting git diff stats")
        except FileNotFoundError:
            logger.debug("git command not available")
        except Exception as e:
            logger.error(f"Error getting git diff stats: {e}")

        return None

    # Week 3: Session Analysis Helper Methods

    def _calculate_session_duration(self) -> int:
        """
        Calculate current session duration in minutes.

        Returns:
            Session duration in minutes (0 if no session detected)
        """
        session_start = self._estimate_session_start()
        if session_start:
            duration = (datetime.now() - session_start).total_seconds() / 60
            return int(duration)
        return 0

    def _calculate_focus_score(self) -> float:
        """
        Calculate focus score based on file switch frequency.

        Algorithm:
        - High focus (0.8-1.0): < HIGH_FOCUS_THRESHOLD switches/hour
        - Medium focus (0.5-0.8): HIGH_FOCUS_THRESHOLD to MEDIUM_FOCUS_THRESHOLD switches/hour
        - Low focus (0.0-0.5): > MEDIUM_FOCUS_THRESHOLD switches/hour

        The algorithm considers that:
        - Very few switches = deep focus on one area
        - Moderate switches = exploring related code
        - Many switches = scattered attention or exploratory work

        Returns:
            Focus score between 0.0 and 1.0
        """
        duration_minutes = self._calculate_session_duration()
        if duration_minutes == 0:
            return 0.5  # Neutral score for new sessions

        # For very short sessions (<5 min), return neutral score
        if duration_minutes < 5:
            return 0.5

        active_files = self.detect_active_files(minutes=duration_minutes)
        file_count = len(active_files)

        # Single file = maximum focus
        if file_count <= 1:
            return 1.0

        # Calculate switches per hour
        duration_hours = duration_minutes / 60.0
        switches_per_hour = file_count / duration_hours

        if switches_per_hour < HIGH_FOCUS_THRESHOLD:
            # High focus: map [0, 5) to [0.85, 1.0]
            normalized = (HIGH_FOCUS_THRESHOLD - switches_per_hour) / HIGH_FOCUS_THRESHOLD
            return min(1.0, 0.85 + normalized * 0.15)
        elif switches_per_hour < MEDIUM_FOCUS_THRESHOLD:
            # Medium focus: map [5, 15) to [0.5, 0.85]
            range_size = MEDIUM_FOCUS_THRESHOLD - HIGH_FOCUS_THRESHOLD
            normalized = (MEDIUM_FOCUS_THRESHOLD - switches_per_hour) / range_size
            return 0.5 + normalized * 0.35
        else:
            # Low focus: map [15, ∞) to [0.0, 0.5]
            # Cap at 40 switches/hr for the calculation
            capped_switches = min(switches_per_hour, 40)
            penalty = (capped_switches - MEDIUM_FOCUS_THRESHOLD) / 25.0
            return max(0.0, 0.5 - penalty * 0.5)

    def _detect_breaks(self) -> List[Dict[str, Any]]:
        """
        Detect breaks in work session (BREAK_THRESHOLD_MINUTES+ gaps in file activity).

        A break is defined as a gap of BREAK_THRESHOLD_MINUTES or more between
        file modifications. This helps identify when the user stepped away from work.

        Returns:
            List of breaks with start, end, and duration_minutes
        """
        breaks: List[Dict[str, Any]] = []

        # Get active files from last SESSION_LOOKBACK_HOURS
        lookback_minutes = SESSION_LOOKBACK_HOURS * 60
        active_files = self.detect_active_files(minutes=lookback_minutes)
        if not active_files:
            return breaks

        # Get modification times for all files
        file_times: List[datetime] = []
        for file_path in active_files:
            try:
                full_path = self.project_root / file_path
                if full_path.exists():
                    mtime = datetime.fromtimestamp(full_path.stat().st_mtime)
                    file_times.append(mtime)
            except OSError as e:
                logger.debug(f"Could not stat file {file_path}: {e}")
                continue
            except Exception as e:
                logger.warning(f"Unexpected error getting file time for {file_path}: {e}")
                continue

        if len(file_times) < 2:
            return breaks

        # Sort and deduplicate times (files modified at same second)
        file_times = sorted(set(file_times))

        # Find gaps of BREAK_THRESHOLD_MINUTES+ minutes
        break_threshold = timedelta(minutes=BREAK_THRESHOLD_MINUTES)
        for i in range(len(file_times) - 1):
            gap = file_times[i + 1] - file_times[i]
            if gap >= break_threshold:
                breaks.append(
                    {
                        "start": file_times[i],
                        "end": file_times[i + 1],
                        "duration_minutes": int(gap.total_seconds() / 60),
                    }
                )

        return breaks

    def _calculate_active_periods(
        self, breaks: List[Dict[str, Any]], session_start: Optional[datetime] = None
    ) -> List[Dict[str, Any]]:
        """
        Calculate active work periods between breaks.

        Args:
            breaks: List of breaks from _detect_breaks()
            session_start: Optional pre-calculated session start time (avoids redundant call)

        Returns:
            List of active periods with start, end, and duration_minutes
        """
        # Get session start (use cached value if provided)
        if session_start is None:
            session_start = self._estimate_session_start()

        if not session_start:
            return []

        if not breaks:
            # No breaks: entire session is one active period
            duration = (datetime.now() - session_start).total_seconds() / 60
            return [
                {
                    "start": session_start,
                    "end": datetime.now(),
                    "duration_minutes": int(duration),
                }
            ]

        active_periods: List[Dict[str, Any]] = []

        # Period before first break
        first_break = breaks[0]
        if first_break["start"] > session_start:
            duration = (first_break["start"] - session_start).total_seconds() / 60
            active_periods.append(
                {
                    "start": session_start,
                    "end": first_break["start"],
                    "duration_minutes": int(duration),
                }
            )

        # Periods between breaks
        for i in range(len(breaks) - 1):
            current_break = breaks[i]
            next_break = breaks[i + 1]
            duration = (
                next_break["start"] - current_break["end"]
            ).total_seconds() / 60
            active_periods.append(
                {
                    "start": current_break["end"],
                    "end": next_break["start"],
                    "duration_minutes": int(duration),
                }
            )

        # Period after last break
        last_break = breaks[-1]
        duration = (datetime.now() - last_break["end"]).total_seconds() / 60
        active_periods.append(
            {
                "start": last_break["end"],
                "end": datetime.now(),
                "duration_minutes": int(duration),
            }
        )

        return active_periods

    # Week 3: Main Analysis Methods

    def analyze_work_session(self) -> Dict[str, Any]:
        """
        Analyze current work session.

        Provides a comprehensive analysis of the current work session including:
        - Duration tracking
        - Focus score based on file switching behavior
        - Break detection (gaps in activity)
        - Active work periods (time between breaks)

        Returns:
            Dictionary with session analysis:
            - duration_minutes: Session duration in minutes
            - focus_score: Focus score (0.0-1.0)
            - breaks: List of breaks detected
            - file_switches: Number of unique files modified
            - active_periods: List of active work periods
        """
        # Get session start once (used by multiple methods)
        session_start = self._estimate_session_start()

        # Calculate duration
        if session_start:
            duration_minutes = int((datetime.now() - session_start).total_seconds() / 60)
        else:
            duration_minutes = 0

        # Calculate focus score
        focus_score = self._calculate_focus_score()

        # Detect breaks
        breaks = self._detect_breaks()

        # Get active files
        minutes = duration_minutes if duration_minutes > 0 else 30
        active_files = self.detect_active_files(minutes=minutes)

        # Calculate active periods (pass session_start to avoid redundant calculation)
        active_periods = self._calculate_active_periods(breaks, session_start)

        return {
            "duration_minutes": duration_minutes,
            "focus_score": round(focus_score, 2),
            "breaks": breaks,
            "file_switches": len(active_files),
            "active_periods": active_periods,
        }

    def predict_next_action(self) -> Dict[str, Any]:
        """
        Predict likely next action based on context.

        Uses rule-based prediction analyzing:
        - File change patterns (test files, implementation files)
        - Git context (uncommitted changes, branch status)
        - Time context (morning, afternoon, evening, night)

        Returns:
            Dictionary with prediction:
            - action: Predicted action name
            - task_id: Related task ID (if available)
            - confidence: Confidence score (0.0-1.0)
            - reasoning: Explanation of prediction
        """
        # Get context without prediction to avoid circular dependency
        context = self.get_current_context(include_prediction=False)
        return self._predict_next_action_internal(context)
