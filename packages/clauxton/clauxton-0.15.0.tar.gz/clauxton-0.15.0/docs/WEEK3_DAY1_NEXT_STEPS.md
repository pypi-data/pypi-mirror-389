# Week 3 Day 1: Next Steps - Implementation Guide

**Date**: October 27, 2025
**Status**: Ready to Start
**Estimated Time**: 4-6 hours

---

## ✅ Already Completed

1. **Week 2 Improvements Committed** ✅
   - Pydantic V2 migration
   - Performance optimization (auto_save)
   - Enhanced error handling
   - Test fixes
   - Commit: `bcf2df8`

2. **Week 3 Planning** ✅
   - Created `WEEK3_PLAN_v0.13.0.md` (comprehensive 7-day plan)
   - ProjectContext model extended with 6 new fields

3. **ProjectContext Model Extended** ✅ (NOT YET COMMITTED)
   - Added `session_duration_minutes`
   - Added `focus_score`
   - Added `breaks_detected`
   - Added `predicted_next_action`
   - Added `uncommitted_changes`
   - Added `diff_stats`

---

## 🎯 Day 1 Remaining Tasks

### Task 1: Implement analyze_work_session() (2 hours)

**File**: `clauxton/proactive/context_manager.py`

**Implementation**:

```python
def analyze_work_session(self) -> Dict[str, Any]:
    """
    Analyze current work session.

    Returns:
        {
            "duration_minutes": int,
            "focus_score": float,  # 0.0-1.0
            "breaks": List[Dict],
            "file_switches": int,
            "active_periods": List[Dict]
        }
    """
    context = self.get_current_context()

    # Calculate duration
    if context.work_session_start:
        duration = (datetime.now() - context.work_session_start).total_seconds() / 60
    else:
        duration = 0

    # Calculate focus score
    # Algorithm:
    # - High focus (0.8-1.0): <5 file switches per hour
    # - Medium focus (0.5-0.8): 5-15 switches per hour
    # - Low focus (0.0-0.5): >15 switches per hour

    active_files = context.active_files
    if duration > 0:
        switches_per_hour = len(active_files) / (duration / 60)
        if switches_per_hour < 5:
            focus_score = 0.9
        elif switches_per_hour < 15:
            focus_score = 0.6
        else:
            focus_score = 0.3
    else:
        focus_score = 0.5  # Neutral

    # Detect breaks (15+ min gaps in file activity)
    breaks = self._detect_breaks()

    return {
        "duration_minutes": int(duration),
        "focus_score": focus_score,
        "breaks": breaks,
        "file_switches": len(active_files),
        "active_periods": self._calculate_active_periods(breaks),
    }
```

**Helper Methods**:

```python
def _detect_breaks(self) -> List[Dict[str, Any]]:
    """Detect breaks in work session (15+ min gaps)."""
    # Check file modification times
    # Find gaps >15 minutes
    # Return list of breaks with start/end times
    pass

def _calculate_active_periods(self, breaks: List[Dict]) -> List[Dict]:
    """Calculate active work periods between breaks."""
    # Split session into active periods
    # Return list of periods with duration
    pass
```

---

### Task 2: Implement predict_next_action() (1.5 hours)

**File**: `clauxton/proactive/context_manager.py`

**Implementation**:

```python
def predict_next_action(self) -> Dict[str, Any]:
    """
    Predict likely next action based on context.

    Returns:
        {
            "action": str,
            "task_id": Optional[str],
            "confidence": float,
            "reasoning": str
        }
    """
    context = self.get_current_context()

    # Rule-based prediction
    predictions = []

    # 1. File change patterns
    active_files = context.active_files
    if any("test" in f for f in active_files):
        predictions.append({
            "action": "run_tests",
            "confidence": 0.8,
            "reasoning": "Test files recently modified"
        })
    elif any(f.endswith(".py") and "test" not in f for f in active_files):
        predictions.append({
            "action": "write_tests",
            "confidence": 0.7,
            "reasoning": "Implementation files modified without tests"
        })

    # 2. Git context
    if context.uncommitted_changes > 10:
        predictions.append({
            "action": "commit_changes",
            "confidence": 0.85,
            "reasoning": f"{context.uncommitted_changes} uncommitted files"
        })

    if context.is_feature_branch and context.uncommitted_changes > 20:
        predictions.append({
            "action": "create_pr",
            "confidence": 0.75,
            "reasoning": "Feature branch with many changes"
        })

    # 3. Time context
    time_ctx = context.time_context
    if time_ctx == "morning":
        predictions.append({
            "action": "planning",
            "confidence": 0.6,
            "reasoning": "Morning time, typical for planning"
        })
    elif time_ctx == "evening":
        predictions.append({
            "action": "documentation",
            "confidence": 0.65,
            "reasoning": "Evening time, good for documentation"
        })

    # Return highest confidence prediction
    if predictions:
        best = max(predictions, key=lambda p: p["confidence"])
        return {
            "action": best["action"],
            "task_id": context.current_task,
            "confidence": best["confidence"],
            "reasoning": best["reasoning"]
        }

    return {
        "action": "continue_work",
        "task_id": context.current_task,
        "confidence": 0.5,
        "reasoning": "No clear pattern detected"
    }
```

---

### Task 3: Implement Git Diff Stats (1 hour)

**File**: `clauxton/proactive/context_manager.py`

**Implementation**:

```python
def _get_git_diff_stats(self) -> Optional[Dict[str, int]]:
    """
    Get git diff statistics for uncommitted changes.

    Returns:
        {"additions": int, "deletions": int, "files_changed": int}
        or None if not a git repo
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

            # Extract numbers
            import re
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

def _count_uncommitted_changes(self) -> int:
    """Count number of files with uncommitted changes."""
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

    except Exception as e:
        logger.error(f"Error counting uncommitted changes: {e}")

    return 0
```

---

### Task 4: Update get_current_context() (30 min)

**File**: `clauxton/proactive/context_manager.py`

**Update the method to populate new fields**:

```python
def get_current_context(self) -> ProjectContext:
    """Get comprehensive project context."""
    # ... existing cache check ...

    # Build fresh context
    context = ProjectContext(
        # Existing fields
        current_branch=self._get_current_branch(),
        active_files=self.detect_active_files(minutes=30),
        recent_commits=self._get_recent_commits(limit=5),
        current_task=self._infer_current_task(),
        time_context=self.get_time_context(),
        work_session_start=self._estimate_session_start(),
        last_activity=datetime.now(),
        is_feature_branch=self._is_feature_branch(),
        is_git_repo=self._is_git_repository(),

        # NEW: Week 3 fields
        session_duration_minutes=self._calculate_session_duration(),
        focus_score=self._calculate_focus_score(),
        breaks_detected=len(self._detect_breaks()),
        predicted_next_action=self.predict_next_action(),
        uncommitted_changes=self._count_uncommitted_changes(),
        diff_stats=self._get_git_diff_stats(),
    )

    # Cache the result
    self._cache[cache_key] = (context, datetime.now())

    return context
```

---

### Task 5: Write Tests (22+ tests) (2 hours)

**File**: `tests/proactive/test_context_week3.py` (NEW)

**Test Structure**:

```python
import pytest
from datetime import datetime, timedelta
from pathlib import Path
from clauxton.proactive.context_manager import ContextManager, ProjectContext

class TestSessionAnalysis:
    """Test work session analysis features."""

    def test_session_duration_calculation(self, tmp_path: Path):
        """Test session duration is calculated correctly."""
        manager = ContextManager(tmp_path)
        # Mock session start 45 minutes ago
        # Call analyze_work_session()
        # Assert duration is approximately 45

    def test_focus_score_high(self, tmp_path: Path):
        """Test high focus score with few file switches."""
        # 1 hour session, 3 file switches
        # Expected: focus_score > 0.8

    def test_focus_score_low(self, tmp_path: Path):
        """Test low focus score with many file switches."""
        # 1 hour session, 20 file switches
        # Expected: focus_score < 0.5

    def test_break_detection(self, tmp_path: Path):
        """Test break detection (15+ min gaps)."""
        # Simulate file activity with 20-min gap
        # Expected: 1 break detected

    # ... 4 more session tests

class TestActionPrediction:
    """Test next action prediction."""

    def test_predict_run_tests(self, tmp_path: Path):
        """Predict run_tests when test files edited."""
        # Recent activity: test_foo.py modified
        # Expected: action="run_tests", confidence>0.7

    def test_predict_commit(self, tmp_path: Path):
        """Predict commit when many uncommitted changes."""
        # 15 uncommitted files
        # Expected: action="commit_changes", confidence>0.8

    # ... 6 more prediction tests

class TestGitStats:
    """Test git diff statistics."""

    def test_get_diff_stats_with_changes(self, tmp_path: Path):
        """Test diff stats with uncommitted changes."""
        # Create git repo, modify files
        # Expected: additions>0, files_changed>0

    def test_get_diff_stats_clean_repo(self, tmp_path: Path):
        """Test diff stats with no changes."""
        # Clean repo
        # Expected: all 0

    # ... 4 more git stats tests
```

---

## 📋 Implementation Checklist

When you start Day 1 implementation, follow this checklist:

### Step 1: Setup (5 min)
- [ ] Commit current progress (ProjectContext model extension)
- [ ] Create new branch if needed
- [ ] Review this guide

### Step 2: Implement Methods (4 hours)
- [ ] `analyze_work_session()` + helpers (2h)
- [ ] `predict_next_action()` (1.5h)
- [ ] `_get_git_diff_stats()` + `_count_uncommitted_changes()` (1h)
- [ ] Update `get_current_context()` (30min)

### Step 3: Write Tests (2 hours)
- [ ] Create `tests/proactive/test_context_week3.py`
- [ ] Session analysis tests (8 tests)
- [ ] Action prediction tests (8 tests)
- [ ] Git stats tests (6 tests)
- [ ] Run all tests: `pytest tests/proactive/test_context_week3.py -v`

### Step 4: Validation (30 min)
- [ ] Run all proactive tests: `pytest tests/proactive/ -v`
- [ ] Check coverage: `pytest --cov=clauxton/proactive`
- [ ] Lint check: `ruff check clauxton/proactive/`
- [ ] Type check: `mypy clauxton/proactive/`

### Step 5: Commit (10 min)
- [ ] Add files: `git add clauxton/proactive/context_manager.py tests/proactive/test_context_week3.py`
- [ ] Commit with message: `feat(proactive): Week 3 Day 1 - Context Intelligence`
- [ ] Verify: `git log --oneline -1`

**Total Estimated Time**: 6-7 hours

---

## 🎯 Success Criteria

**Code**:
- ✅ ProjectContext has 6 new fields
- ✅ `analyze_work_session()` implemented with focus scoring
- ✅ `predict_next_action()` implemented with rule-based logic
- ✅ Git diff stats methods working
- ✅ `get_current_context()` populates all new fields

**Tests**:
- ✅ 22+ tests written
- ✅ 100% pass rate
- ✅ Coverage >85% for new code

**Quality**:
- ✅ 0 lint errors (ruff)
- ✅ 0 type errors (mypy)
- ✅ All existing tests still passing

---

## 💡 Tips for Implementation

1. **Start Simple**: Implement basic versions first, refine later
2. **Test as You Go**: Write tests after each method (faster debugging)
3. **Use Mocking**: Mock git commands in tests for consistency
4. **Cache Results**: Remember to cache expensive operations
5. **Error Handling**: Add try/except for all subprocess calls
6. **Logging**: Add logger.debug/warning for visibility

---

## 🚀 After Day 1

Once Day 1 is complete, you'll move to **Day 2-3**:
- Refine session analysis algorithms
- Add MCP tools for new context features
- Integration testing

See `WEEK3_PLAN_v0.13.0.md` for full Week 3 schedule.

---

**Ready to start? Follow the checklist above!** 🎯
