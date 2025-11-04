# Context Intelligence User Guide

**Version**: v0.13.0
**Feature**: Context Intelligence & Proactive Monitoring

Welcome to the Context Intelligence User Guide! This document explains how to use Clauxton's intelligent work session analysis, next action prediction, and project context awareness features.

---

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Core Concepts](#core-concepts)
4. [Usage Examples](#usage-examples)
5. [Integration with Claude Code](#integration-with-claude-code)
6. [Advanced Topics](#advanced-topics)
7. [Troubleshooting](#troubleshooting)

---

## Introduction

### What is Context Intelligence?

Context Intelligence is Clauxton's AI-powered feature that:
- **Tracks your work sessions** - Duration, focus score, breaks
- **Predicts next actions** - What you're likely to do next based on patterns
- **Provides project context** - Git status, active files, recent commits, and more

All automatically, without manual input.

### Key Features

**Work Session Analysis** (`analyze_work_session`)
- Session duration tracking (minutes since first file change)
- Focus score calculation (0.0-1.0 based on file switching)
- Break detection (15+ minute gaps in activity)
- File switch frequency

**Action Prediction** (`predict_next_action`)
- 9 supported actions (run_tests, commit_changes, create_pr, etc.)
- Confidence scores (0.0-1.0)
- Context-aware reasoning

**Enhanced Project Context** (`get_current_context`)
- Git information (branch, commits, uncommitted changes, diff stats)
- Active files (recently modified)
- Time context (morning/afternoon/evening/night)
- Work session info + prediction (optional)

### Benefits

- **Productivity insights**: Understand your work patterns
- **Smart suggestions**: Get context-aware recommendations
- **Automated workflows**: Let Claude Code suggest next steps automatically
- **Better focus**: Track focus scores and take breaks at the right time

---

## Getting Started

### Installation

Context Intelligence is built into Clauxton v0.13.0+. No additional installation required.

```bash
# Install/upgrade Clauxton
pip install --upgrade clauxton

# Verify version
clauxton --version  # Should be ≥ 0.13.0
```

### Configuration

Context Intelligence works out-of-the-box with default settings. For advanced users:

```yaml
# .clauxton/config.yml (optional)
proactive:
  enabled: true
  session_timeout_minutes: 30  # Consider session ended after 30min inactivity
  focus_threshold: 0.7  # High focus = few file switches
  break_threshold_minutes: 15  # Detect breaks ≥ 15min
```

### First Steps

1. **Initialize Clauxton** in your project (if not already done):
   ```bash
   clauxton init
   ```

2. **Start working** on your project - modify files, commit changes, etc.

3. **Ask Claude Code** for session analysis:
   - "How's my work session going?"
   - "What should I do next?"
   - "Give me project context"

Claude Code will automatically use the Context Intelligence MCP tools.

---

## Core Concepts

### Work Session Analysis

**Session Start**: Estimated from the earliest modified file (within 30 minutes)

**Session Duration**: Minutes since session start

**Focus Score** (0.0-1.0):
- **High focus (0.8+)**: Few file switches, concentrated work
- **Medium focus (0.5-0.8)**: Moderate file switching
- **Low focus (<0.5)**: Many file switches, scattered work

**Formula**: `focus_score = max(0, 1 - (file_switches / (duration_minutes / 10)))`

**Break Detection**:
- Gaps ≥ 15 minutes between file modifications
- Each break includes start time and duration

**Active Periods**:
- Continuous work periods (between breaks)
- Each period has start and end time

### Action Prediction

**Prediction Algorithm**:
1. Analyze context (git status, file changes, time, session)
2. Apply rule-based heuristics
3. Calculate confidence score
4. Return action + reasoning

**Supported Actions**:

| Action | Description | Confidence Factors |
|--------|-------------|-------------------|
| `run_tests` | Many files changed, no recent test runs | File count, test file presence |
| `write_tests` | Implementation changed, no test files | Impl files vs test files ratio |
| `commit_changes` | Uncommitted changes, feature complete | File count, session duration |
| `create_pr` | Branch ahead of main, commits ready | Commits ahead, branch name |
| `take_break` | Long session without breaks | Session duration, break count |
| `morning_planning` | Morning time, no activity | Time of day, session age |
| `resume_work` | Coming back from break | Break duration |
| `review_code` | Many changes, might need review | Change size |
| `no_clear_action` | No strong pattern detected | Low confidence all around |

**Confidence Scores**:
- **0.8+**: High confidence
- **0.5-0.8**: Medium confidence
- **<0.5**: Low confidence

### Project Context

**Context Components**:
- **Git info**: Branch, recent commits, uncommitted changes
- **Active files**: Recently modified files (last 30 minutes)
- **Time context**: Morning (6-12), Afternoon (12-18), Evening (18-22), Night (22-6)
- **Work session**: Duration, focus score, breaks (from session analysis)
- **Predicted action**: Next likely action with reasoning (optional)
- **Diff stats**: Lines added/deleted, files changed

**Caching**:
- Context is cached for 30 seconds for performance
- Repeated calls within 30 seconds return cached data
- Cache includes/excludes prediction based on `include_prediction` parameter

**Customization**:
- Set `include_prediction=False` for faster context (skips prediction calculation)

---

## Usage Examples

### Morning Workflow

**Scenario**: Starting your workday

```python
# Claude Code internally calls these MCP tools

# 1. Get project context to understand where you left off
context = get_current_context()
print(f"Working on: {context['current_branch']}")
print(f"Last activity: {context['last_activity']}")

# 2. Check predicted action
action = context['predicted_next_action']
if action and action['action'] == 'morning_planning':
    print(f"Suggestion: {action['action']} ({action['confidence']:.0%} confidence)")
    print(f"Reason: {action['reasoning']}")
    # → "Suggested: morning_planning (85% confidence)"
    # → "Reason: Morning time (10:30), no recent activity. Review open tasks and plan your day."
```

**Natural Language** (Claude Code):
- "What should I work on today?"
- "Give me a summary of where I left off"

### Development Session

**Scenario**: After working for 90 minutes

```python
# Analyze your session
analysis = analyze_work_session()

if analysis['status'] == 'success':
    duration = analysis['duration_minutes']
    focus = analysis['focus_score']
    breaks = len(analysis['breaks'])

    print(f"Session: {duration} minutes")
    print(f"Focus: {focus:.2f} ({'high' if focus > 0.8 else 'medium' if focus > 0.5 else 'low'})")
    print(f"Breaks: {breaks}")

    # → "Session: 87 minutes"
    # → "Focus: 0.85 (high)"
    # → "Breaks: 0"

    if duration > 90 and breaks == 0:
        print("💡 Consider taking a break!")
```

**Natural Language** (Claude Code):
- "How's my focus today?"
- "Should I take a break?"
- "Analyze my work session"

### Pre-Commit Check

**Scenario**: Before committing changes

```python
# Get prediction
prediction = predict_next_action()

if prediction['action'] == 'run_tests':
    print(f"Recommendation: {prediction['action']}")
    print(f"Confidence: {prediction['confidence']:.0%}")
    print(f"Reasoning: {prediction['reasoning']}")
    # → "Recommendation: run_tests"
    # → "Confidence: 82%"
    # → "Reasoning: 15 files changed without recent test runs. Run tests before committing."

    # Run tests before committing
    subprocess.run(["pytest"])
elif prediction['action'] == 'commit_changes':
    print("✅ Ready to commit!")
```

**Natural Language** (Claude Code):
- "What should I do before committing?"
- "Am I ready to commit?"
- "Should I run tests first?"

### Evening Wrap-up

**Scenario**: End of workday

```python
# Get full context
context = get_current_context(include_prediction=True)

# Session summary
session_duration = context['session_duration_minutes']
focus_score = context['focus_score']
uncommitted = context['uncommitted_changes']

print(f"Today's session: {session_duration} minutes")
print(f"Focus score: {focus_score:.2f}")
print(f"Uncommitted changes: {uncommitted}")

# Check if you should commit
if context['predicted_next_action']['action'] == 'commit_changes':
    print("💡 Suggestion: Commit your work before ending the day")
```

**Natural Language** (Claude Code):
- "Summarize my work today"
- "Should I commit before leaving?"
- "Daily work summary"

---

## Integration with Claude Code

### MCP Tool Usage

Claude Code automatically uses Context Intelligence tools when you ask relevant questions:

**Automatic Triggers**:

| Your Question | MCP Tool Called | Purpose |
|---------------|-----------------|---------|
| "How's my session?" | `analyze_work_session` | Get productivity insights |
| "What's next?" | `predict_next_action` | Get action recommendation |
| "Project status?" | `get_current_context` | Get full context |
| "Should I take a break?" | `analyze_work_session` | Check session duration |
| "Am I ready to commit?" | `predict_next_action` | Check commit readiness |

### Natural Language Queries

**Examples**:
- "I've been working for a while. Analyze my session."
  → Calls `analyze_work_session()`

- "Based on my current work, what should I do next?"
  → Calls `predict_next_action()`

- "Give me full project context including what I should do next."
  → Calls `get_current_context(include_prediction=True)`

- "Quick project status without prediction."
  → Calls `get_current_context(include_prediction=False)`

### Automation Patterns

**Morning Briefing** (automatic):
```
Claude Code: "Good morning! Let me check where you left off yesterday."
  → Calls get_current_context()
  → "You're on feature/auth-refactor branch. 3 files uncommitted.
      Suggestion: Review uncommitted changes before starting new work."
```

**Pre-Commit Reminder** (automatic):
```
Claude Code: "You've modified 12 files. Should I check if tests need to run?"
  → Calls predict_next_action()
  → "Recommendation: run_tests (85% confidence). 12 files changed
      without recent test runs."
```

**Break Reminder** (automatic):
```
Claude Code: "You've been working for 120 minutes without a break."
  → Calls analyze_work_session()
  → "Focus score: 0.72 (medium). Consider taking a 10-minute break."
```

---

## Advanced Topics

### Performance Tuning

**Context Caching**:
```python
# Fast: Uses 30-second cache
context1 = get_current_context()  # Fresh call (~100ms)
context2 = get_current_context()  # Cached (<10ms)

# Skip prediction for even faster response
context_fast = get_current_context(include_prediction=False)  # ~50ms
```

**Clearing Cache**:
```python
# Context cache clears automatically after 30 seconds
# No manual clearing needed
```

### Custom Patterns

**Custom Focus Threshold**:
```yaml
# .clauxton/config.yml
proactive:
  focus_threshold: 0.6  # Lower = more lenient focus scoring
```

**Custom Break Detection**:
```yaml
proactive:
  break_threshold_minutes: 20  # Longer breaks before detection
```

### Multi-Project Setup

Context Intelligence works per-project:

```bash
# Project A
cd ~/projects/project-a
clauxton init
# Context Intelligence tracks Project A independently

# Project B
cd ~/projects/project-b
clauxton init
# Context Intelligence tracks Project B independently
```

Each project maintains its own:
- Session tracking
- Active files
- Context cache

---

## Troubleshooting

See [TROUBLESHOOTING.md](TROUBLESHOOTING.md) for detailed troubleshooting guidance.

**Quick Fixes**:

**Q**: Session analysis returns "no_session"
**A**: No files modified in the last 30 minutes. Start working on files.

**Q**: Prediction always returns "no_clear_action"
**A**: Not enough context yet. Continue working and try again after a few file changes.

**Q**: Focus score seems wrong
**A**: Focus score is calculated over the entire session. A few file switches at the start can lower the score.

**Q**: Context is stale
**A**: Wait 30 seconds for cache to expire, or modify a file to trigger cache invalidation.

---

## Support & Resources

- **Documentation**: [MCP Context Intelligence](../mcp-context-intelligence.md)
- **Workflow Examples**: [WORKFLOW_EXAMPLES.md](WORKFLOW_EXAMPLES.md)
- **Best Practices**: [BEST_PRACTICES.md](BEST_PRACTICES.md)
- **Issues**: https://github.com/nakishiyaman/clauxton/issues

---

**Happy coding with Context Intelligence!** 🚀
