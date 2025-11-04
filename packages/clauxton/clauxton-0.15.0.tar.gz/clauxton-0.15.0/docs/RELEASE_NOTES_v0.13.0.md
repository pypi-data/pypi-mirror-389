# Release Notes - v0.13.0

**Release Date**: 2025-10-27
**Status**: Stable
**Codename**: "Context Intelligence & Proactive Monitoring"

---

## 🎉 Overview

v0.13.0 introduces **Context Intelligence** - AI-powered understanding of your development workflow with real-time session analysis, next action prediction, and enhanced project awareness. This release focuses on making Clauxton **proactive** and **context-aware**, helping you stay focused and productive.

### Key Highlights

- 🧠 **Work Session Analysis**: Automatic tracking of session duration, focus score, breaks, and file switching
- 🤖 **AI Action Prediction**: Intelligent next action recommendations with 9 supported actions and confidence scoring
- 📊 **Enhanced Context**: Rich project awareness with Git info, time context, and session data
- 👁️ **Proactive Monitoring**: Real-time file watching with pattern detection (bulk edits, new features, refactoring)
- ⚡ **Fast**: <50ms session analysis, <100ms action prediction (with 30-second caching)
- 📚 **Comprehensive Docs**: 4 user guides (~1500 lines) with examples and best practices

### What's New

```
v0.13.0 = v0.12.0 + Context Intelligence + Proactive Monitoring
        = 32 MCP tools + 5 new tools
        = 36 MCP tools total
        = 1,637 tests + 316 new tests
        = 1,953+ tests total
        = 86% → 90% coverage
```

---

## ✨ New Features

### 1. Work Session Analysis

#### What is it?

Automatic tracking and analysis of your development sessions with focus scoring and break detection.

#### Features

- **Session Duration Tracking**:
  - Automatic start from first file change
  - 30-minute session timeout (configurable)
  - Active period tracking between breaks

- **Focus Score Calculation** (0.0-1.0):
  - High focus (0.8+): Concentrated work with few file switches
  - Medium focus (0.5-0.8): Moderate context switching
  - Low focus (<0.5): Scattered work across many files
  - Formula: `max(0, 1 - (file_switches / (duration_minutes / 10)))`

- **Break Detection**:
  - Automatically detect breaks ≥15 minutes (configurable)
  - Track break duration and frequency
  - Identify continuous work periods

- **File Switching Analysis**:
  - Count and track file switches
  - Impact on focus score
  - Help identify context switching issues

#### MCP Tool

**`analyze_work_session()`** - Returns session metrics

```python
# Via Claude Code (automatic)
User: "How's my work session going?"
→ Claude Code calls analyze_work_session()
→ "Your session: 87 minutes with high focus (0.82).
   You've modified 12 files without taking a break.
   Consider taking a short break after 90 minutes."

# Via MCP
result = analyze_work_session()
# → {
#   "status": "success",
#   "duration_minutes": 87,
#   "focus_score": 0.82,
#   "breaks": [],
#   "file_switches": 12,
#   "active_periods": [
#     {"start": "10:30", "end": "11:57", "duration_minutes": 87}
#   ]
# }
```

#### Performance

- Session analysis: <50ms average
- With caching: <10ms for repeated calls (30-second cache)
- Zero overhead when not in use

#### Use Cases

- 📈 "Analyze my work session" → Get productivity insights
- ⏸️  "Should I take a break?" → Check session duration and breaks
- 🎯 "How's my focus today?" → See focus score and file switching

**See**: [Context Intelligence Guide](guides/CONTEXT_INTELLIGENCE_GUIDE.md)

---

### 2. AI Action Prediction

#### What is it?

Intelligent next action prediction based on context analysis (git status, file changes, session duration, time of day).

#### Features

- **9 Supported Actions**:
  - `run_tests` - Tests need to be run
  - `write_tests` - Tests need to be written
  - `commit_changes` - Ready to commit
  - `create_pr` - Ready for pull request
  - `take_break` - Break recommended
  - `morning_planning` - Plan your day
  - `resume_work` - Resume after break
  - `review_code` - Code review suggested
  - `no_clear_action` - No strong recommendation

- **Confidence Scoring** (0.0-1.0):
  - High (0.8+): Strong recommendation, follow it
  - Medium (0.5-0.8): Consider as suggestion
  - Low (<0.5): Informational only

- **Context-Aware Analysis**:
  - Git status (uncommitted changes, branch state)
  - File modifications (count, types, patterns)
  - Session duration and breaks
  - Time of day (morning/afternoon/evening/night)

- **Human-Readable Reasoning**:
  - Clear explanation for each prediction
  - Understanding of why the action was suggested

#### MCP Tool

**`predict_next_action()`** - Returns action recommendation

```python
# Via Claude Code (automatic)
User: "What should I do before committing?"
→ Claude Code calls predict_next_action()
→ "Recommendation: run_tests (85% confidence).
   Reasoning: 15 files changed without recent test runs."

# Via MCP
prediction = predict_next_action()
# → {
#   "action": "run_tests",
#   "confidence": 0.87,
#   "reasoning": "15 files changed without recent test runs. "
#                "Run tests before committing."
# }
```

#### Example Predictions

```
Action: run_tests (confidence: 0.87)
Reasoning: 15 files changed without recent test runs. Run tests before committing.

Action: take_break (confidence: 0.85)
Reasoning: Session duration 120 minutes with 0 breaks. Take a 10-minute break.

Action: commit_changes (confidence: 0.75)
Reasoning: 8 files modified, tests passing. Ready to commit.

Action: morning_planning (confidence: 0.90)
Reasoning: Morning time (10:30), no recent activity. Review open tasks and plan your day.
```

#### Performance

- Action prediction: <100ms with all heuristics
- With caching: <10ms for repeated calls (30-second cache)
- Heuristic evaluation: <20ms per action

#### Use Cases

- 🎯 "Am I ready to commit?" → Check if tests need to run first
- 🔄 "What's next?" → Get AI-recommended next action
- 📋 "What should I work on today?" → Morning planning with context

**See**: [Workflow Examples](guides/WORKFLOW_EXAMPLES.md)

---

### 3. Enhanced Project Context

#### What is it?

Rich project awareness combining Git information, active files, time context, and work session data.

#### Features

- **Git Information**:
  - Current branch
  - Recent commits (last 5)
  - Uncommitted changes count
  - Diff statistics (lines added/deleted, files changed)

- **Active Files**:
  - Recently modified files (last 30 minutes)
  - Modification timestamps
  - File paths relative to project root

- **Time Context**:
  - Morning (6-12)
  - Afternoon (12-18)
  - Evening (18-22)
  - Night (22-6)

- **Work Session Data**:
  - Duration, focus score, breaks
  - File switches, active periods

- **Predicted Action** (optional):
  - Next recommended action
  - Confidence and reasoning
  - Can be disabled for speed

- **30-Second Caching**:
  - <100ms fresh call (with prediction)
  - <50ms fresh call (without prediction)
  - <10ms cached call

#### MCP Tool

**`get_current_context(include_prediction=True)`** - Returns project context

```python
# Via Claude Code (automatic)
User: "Give me full project context"
→ Claude Code calls get_current_context(include_prediction=True)
→ "Working on: feature/api-refactor (3 commits ahead)
   Session: 87 minutes, focus 0.82 (high)
   Uncommitted: 8 files
   Suggestion: run_tests (85% confidence)"

# Via MCP
context = get_current_context(include_prediction=True)
# → {
#   "current_branch": "feature/api-refactor",
#   "recent_commits": [...],
#   "uncommitted_changes": 8,
#   "diff_stats": {"lines_added": 245, "lines_deleted": 87, "files_changed": 8},
#   "active_files": [
#     {"path": "src/api/users.py", "modified_at": "11:45"},
#     {"path": "src/api/auth.py", "modified_at": "11:42"}
#   ],
#   "time_context": "afternoon",
#   "session_duration_minutes": 87,
#   "focus_score": 0.82,
#   "predicted_next_action": {
#     "action": "run_tests",
#     "confidence": 0.87,
#     "reasoning": "15 files changed without recent test runs."
#   }
# }
```

#### Performance

- Context retrieval: <100ms (with prediction)
- Context retrieval: <50ms (without prediction)
- Cached calls: <10ms (30-second cache)
- Git operations: <50ms average

#### Use Cases

- 🌅 "What should I work on today?" → Morning planning with yesterday's context
- 🔄 "Where did I leave off?" → Project context with recent activity
- 📊 "Show me project status" → Git info, session data, prediction

**See**: [Best Practices](guides/BEST_PRACTICES.md)

---

### 4. Proactive Monitoring (Week 1)

#### What is it?

Real-time file watching with pattern detection for bulk edits, new features, refactoring, and more.

#### Features

- **Real-time File Monitoring**:
  - watchdog integration
  - Background file change detection
  - Debounced events (500ms)
  - Configurable patterns (watch specific file types)

- **5 Pattern Detection Algorithms**:
  - Bulk Edit Detection (same file modified 3+ times)
  - New Feature Detection (multiple new files)
  - Refactoring Detection (files renamed/moved together)
  - Cleanup Detection (files deleted in bulk)
  - Config Change Detection (configuration file modifications)

- **Confidence Scoring** (0.0-1.0)
- **Time Windows**: Flexible query by minutes (default: 60)
- **Performance**: <5ms event processing, <1% CPU when idle

#### MCP Tools

**`watch_project_changes(enabled)`** - Start/stop monitoring

```python
# Enable monitoring
watch_project_changes(enabled=True)

# Disable monitoring
watch_project_changes(enabled=False)
```

**`get_recent_changes(minutes=60)`** - Get changes and patterns

```python
# Get last hour of changes
changes = get_recent_changes(minutes=60)
# → {
#   "total_events": 25,
#   "event_types": {"modified": 18, "created": 5, "deleted": 2},
#   "files_affected": 12,
#   "detected_patterns": [
#     {
#       "type": "bulk_edit",
#       "confidence": 0.9,
#       "description": "File 'api.py' modified 5 times in 10 minutes",
#       "files": ["src/api.py"]
#     }
#   ]
# }
```

#### Use Cases

- 🔍 "What have I changed in the last hour?" → Get recent changes
- 🎯 "Show me detected patterns" → See bulk edits, refactoring
- 📈 "Based on my changes, suggest next tasks" → Pattern-based suggestions

**See**: [Proactive Monitoring Guide](PROACTIVE_MONITORING_GUIDE.md)

---

## 📊 Quality & Testing

### Test Coverage

- **316 new proactive tests** (1,953+ total, +19% increase)
  - Week 1: 56 tests (config, event_processor, file_monitor MCP)
  - Week 2: 132 tests (behavior_tracker, suggestion_engine, context_manager)
  - Week 3: 128 tests (context intelligence MCP tools, integration scenarios)

### Test Breakdown

- `test_context_manager.py`: 42 tests (session analysis, context retrieval) - **95% coverage**
- `test_suggestion_engine.py`: 26 tests (action prediction, all 9 actions) - **96% coverage**
- `test_behavior_tracker.py`: 33 tests (pattern learning, trend analysis) - **92% coverage**
- `test_mcp_context.py`: 18 tests (3 new MCP tools, error handling) - **100% coverage**
- `test_integration_day5.py`: 23 tests (end-to-end workflows) - **N/A**

### Coverage Metrics

- **Proactive modules**: 89-100% coverage
  - context_manager: 95%
  - suggestion_engine: 96%
  - behavior_tracker: 92%
  - event_processor: 97%
  - file_monitor: 100%
  - config: 100%
- **MCP server**: 93% coverage (36 tools, all tested individually)
- **Overall project**: 90% coverage (up from 86%)

### Test Quality

- All performance benchmarks passing
- Security tests: 19 tests, no vulnerabilities
- Error handling: 33 comprehensive tests
- Scenario coverage: 23 real-world integration tests

### Code Quality

- **Type Safety**: 100% (mypy strict mode, 0 errors)
- **Linting**: 100% (ruff, 0 errors)
- **Security**: Bandit scan passed (0 issues)

---

## 🚀 Performance

### Benchmarks

| Operation | Time (p95) | Notes |
|-----------|-----------|-------|
| Session analysis | <50ms | With 30-second cache |
| Action prediction | <100ms | All 9 heuristics |
| Context retrieval (with prediction) | <100ms | Full context |
| Context retrieval (without prediction) | <50ms | Faster variant |
| Cached context calls | <10ms | 30-second cache |
| File monitoring | <5ms | Per event batch |
| Pattern detection | <20ms | Per event batch |

### Optimizations

- **30-second context cache**: Drastically speeds up repeated calls
- **Optional prediction**: Skip prediction for faster context retrieval
- **Incremental updates**: No full rebuild needed
- **Debounced events**: Reduces duplicate processing (500ms debounce)

---

## 📚 Documentation

### New User Guides (~1500 lines total)

1. **[Context Intelligence Guide](guides/CONTEXT_INTELLIGENCE_GUIDE.md)** (400+ lines)
   - Core concepts (session analysis, action prediction, project context)
   - Usage examples (morning workflow, development session, pre-commit, evening wrap-up)
   - Integration with Claude Code
   - Advanced topics (caching, custom patterns, multi-project setup)
   - Troubleshooting

2. **[Workflow Examples](guides/WORKFLOW_EXAMPLES.md)** (350+ lines)
   - 6 real-world scenarios:
     - Morning start (understanding where you left off)
     - Feature development (90-minute focused session)
     - Bug fixing (quick fix without losing context)
     - Code review (efficient PR review)
     - End of day (wrapping up and planning)
     - Team collaboration (handoff documentation)
   - Tips for effective workflows
   - Keyboard shortcuts and Git hook integration

3. **[Best Practices](guides/BEST_PRACTICES.md)** (400+ lines)
   - General principles (let Context Intelligence work for you)
   - Session management (optimize focus score, break management)
   - Action prediction (when to follow, when to override)
   - Performance optimization (context caching, reduce tool calls)
   - Git integration (smart commits, branch management)
   - Team practices (pair programming, code reviews, documentation)
   - Configuration tuning (adjust thresholds, per-project settings)
   - Common patterns and anti-patterns
   - Metrics to track (personal KPIs, weekly review)

4. **[Troubleshooting Guide](guides/TROUBLESHOOTING.md)** (350+ lines)
   - Quick diagnosis flowchart
   - 8 sections covering:
     - Session analysis issues (no session detected, wrong focus score, breaks not detected)
     - Action prediction issues (always "no_clear_action", wrong predictions)
     - Project context issues (stale context, missing prediction)
     - Performance issues (slow tools, high memory usage)
     - Configuration issues (config not taking effect, config file not found)
     - Integration issues (Claude Code not using tools)
     - Common error messages
     - Debug mode

### Updated Documentation

- **README.md**: Updated with Context Intelligence features, 36 MCP tools, 1,953+ test statistics
- **CHANGELOG.md**: Comprehensive v0.13.0 entry with all changes
- **[Quality Report v0.13.0](QUALITY_REPORT_v0.13.0.md)**: Detailed quality assessment

---

## 🔄 Migration Guide

### Upgrading from v0.12.0

```bash
# Upgrade Clauxton
pip install --upgrade clauxton

# Verify version
clauxton --version  # Should show: clauxton, version 0.13.0
```

### No Breaking Changes

All existing functionality remains unchanged. New features are opt-in via MCP tool calls.

### New MCP Tools (5 total)

**Context Intelligence (3 tools)**:
- `analyze_work_session()` - Session analysis
- `predict_next_action()` - Action prediction
- `get_current_context(include_prediction)` - Enhanced context

**Proactive Monitoring (2 tools)**:
- `watch_project_changes(enabled)` - File monitoring
- `get_recent_changes(minutes)` - Recent changes

### Optional Configuration

Add to `.clauxton/config.yml` for customization:

```yaml
proactive:
  enabled: true
  session_timeout_minutes: 30  # Session ends after inactivity
  focus_threshold: 0.7          # High focus threshold
  break_threshold_minutes: 15   # Break detection threshold
```

### Natural Language Usage

```
# Claude Code automatically uses new tools
"How's my work session going?"       → analyze_work_session()
"What should I do before committing?" → predict_next_action()
"Give me full project context"       → get_current_context(True)
"What have I changed recently?"      → get_recent_changes(60)
```

---

## 🎯 Use Cases

### Morning Planning

```
You: "Good morning! Where did I leave off?"
Claude Code: → Calls get_current_context()
"You're on feature/auth-refactor branch with 3 uncommitted files.
Last activity: Yesterday 6:45 PM.
Suggestion: Review uncommitted changes before starting new work."
```

### Pre-Commit Check

```
You: "What should I do before committing?"
Claude Code: → Calls predict_next_action()
"Recommendation: run_tests (85% confidence).
Reasoning: 12 files changed without recent test runs."
```

### Session Analysis

```
You: "Analyze my work session"
Claude Code: → Calls analyze_work_session()
"Your session: 87 minutes with high focus (0.82).
You've modified 12 files without taking a break.
Consider taking a short break after 90 minutes."
```

### Daily Wrap-up

```
You: "Summarize my work today"
Claude Code: → Calls get_current_context() + analyze_work_session()
"Today's session: 6 hours 12 minutes, focus 0.74 (medium-high).
Modified 18 files across 3 major areas.
Uncommitted: 2 files (config/stripe.py, docs/payments.md).
Suggestion: Commit before leaving (88% confidence)."
```

---

## 🔗 Links

- **PyPI**: [https://pypi.org/project/clauxton/](https://pypi.org/project/clauxton/)
- **GitHub**: [https://github.com/nakishiyaman/clauxton](https://github.com/nakishiyaman/clauxton)
- **Documentation**: [docs/](https://github.com/nakishiyaman/clauxton/tree/main/docs)
- **Issues**: [GitHub Issues](https://github.com/nakishiyaman/clauxton/issues)

---

## 🙏 Acknowledgments

Thanks to all contributors and users who provided feedback during the v0.13.0 development cycle!

---

**Happy coding with Context Intelligence!** 🚀
