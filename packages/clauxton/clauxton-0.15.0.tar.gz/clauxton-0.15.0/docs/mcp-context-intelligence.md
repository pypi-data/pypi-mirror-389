# MCP Context Intelligence

**Work Session Analysis and Next Action Prediction**

[← Back to Index](mcp-index.md) | [Proactive Monitoring](mcp-proactive-monitoring.md)

## Context Intelligence Tools (v0.13.0 Week 3 Day 2) 🚀 NEW

### analyze_work_session

**Analyze current work session for productivity insights.**

Provides comprehensive analysis of the current work session including:
- Duration tracking (how long you've been working)
- Focus score based on file switching behavior (0.0-1.0)
- Break detection (gaps in activity)
- Active work periods (time between breaks)
- File switch count (unique files modified)

**Parameters**: None

**Returns**: Dictionary with:
- `status`: "success", "no_session", or "error"
- `duration_minutes`: Session duration in minutes
- `focus_score`: Focus score (0.0-1.0), higher = more focused
  - 0.8+ = high focus (few file switches)
  - 0.5-0.8 = medium focus
  - <0.5 = low focus (many file switches)
- `breaks`: List of detected breaks with:
  - `start`: Break start timestamp (ISO format)
  - `duration_minutes`: Break duration
- `file_switches`: Number of unique files modified
- `active_periods`: List of active work periods with:
  - `start`: Period start timestamp (ISO format)
  - `end`: Period end timestamp (ISO format)

**Example**:
```python
result = analyze_work_session()

if result["status"] == "success":
    print(f"Session duration: {result['duration_minutes']} minutes")
    print(f"Focus score: {result['focus_score']}")
    print(f"Breaks detected: {len(result['breaks'])}")
    print(f"Files modified: {result['file_switches']}")
```

**Use Cases**:
1. **Productivity Tracking**: Understand work patterns and session quality
2. **Break Reminders**: Detect long sessions without breaks
3. **Focus Analysis**: Identify high/low focus periods for optimization
4. **Session Planning**: Optimize work sessions based on historical data

---

### predict_next_action

**Predict likely next action based on project context.**

Uses rule-based prediction analyzing:
- File change patterns (test files, implementation files)
- Git context (uncommitted changes, branch status)
- Time context (morning, afternoon, evening, night)
- Work session patterns (focus, breaks, duration)

**Parameters**: None

**Returns**: Dictionary with:
- `status`: "success" or "error"
- `action`: Predicted action name (see below)
- `task_id`: Related task ID (if available)
- `confidence`: Confidence score (0.0-1.0)
  - 0.8+ = high confidence
  - 0.5-0.8 = medium confidence
  - <0.5 = low confidence
- `reasoning`: Explanation of why this action was predicted

**Possible Actions**:
- `run_tests`: Many files changed without recent test runs
- `write_tests`: Implementation files changed, no test files
- `commit_changes`: Changes ready, feature complete
- `create_pr`: Branch ahead of main, commits ready
- `take_break`: Long session without breaks detected
- `morning_planning`: Morning time, no activity yet
- `resume_work`: Coming back from break
- `review_code`: Many changes, might need review
- `no_clear_action`: No strong pattern detected

**Example**:
```python
result = predict_next_action()

if result["status"] == "success":
    print(f"Recommended action: {result['action']}")
    print(f"Confidence: {result['confidence']:.2f}")
    print(f"Reasoning: {result['reasoning']}")

    if result['task_id']:
        print(f"Related task: {result['task_id']}")
```

**Use Cases**:
1. **Smart Suggestions**: Proactively suggest next steps in workflow
2. **Workflow Optimization**: Guide through development workflow automatically
3. **Context Switching**: Help resume work after breaks or interruptions
4. **Quality Assurance**: Remind to run tests or review code at appropriate times

---

### get_current_context

**Get comprehensive current project context.**

Provides real-time project context including:
- Git branch and status
- Active files (recently modified)
- Recent commits
- Current task (if available)
- Time context (morning/afternoon/evening/night)
- Work session analysis (duration, focus, breaks)
- Predicted next action
- Uncommitted changes and diff stats

**Parameters**:
- `include_prediction` (boolean, optional): Include next action prediction (default: True)
  - Set to False for faster response without prediction

**Returns**: Dictionary with:
- `status`: "success" or "error"
- `current_branch`: Git branch name
- `active_files`: List of recently modified files
- `recent_commits`: Recent commit information
- `current_task`: Current task ID (if available)
- `time_context`: "morning", "afternoon", "evening", or "night"
- `work_session_start`: Session start timestamp (ISO format)
- `last_activity`: Last detected activity timestamp (ISO format)
- `is_feature_branch`: Whether current branch is a feature branch
- `is_git_repo`: Whether project is a git repository
- `session_duration_minutes`: Current session duration
- `focus_score`: Focus score (0.0-1.0)
- `breaks_detected`: Number of breaks in session
- `predicted_next_action`: Predicted next action (if `include_prediction=True`):
  - `action`: Action name
  - `confidence`: Confidence score
  - `reasoning`: Explanation
- `uncommitted_changes`: Number of uncommitted changes
- `diff_stats`: Git diff statistics:
  - `additions`: Lines added
  - `deletions`: Lines deleted
  - `files_changed`: Number of files changed

**Example**:
```python
# Get full context with prediction
context = get_current_context()

print(f"Branch: {context['current_branch']}")
print(f"Session: {context['session_duration_minutes']} min")
print(f"Focus: {context['focus_score']}")
print(f"Changes: {context['uncommitted_changes']} uncommitted")

if context['predicted_next_action']:
    action = context['predicted_next_action']
    print(f"Next: {action['action']} ({action['confidence']:.2f})")

# Get context without prediction (faster)
context = get_current_context(include_prediction=False)
```

**Use Cases**:
1. **Context Awareness**: Understand current project state at a glance
2. **Smart Suggestions**: Provide context-aware recommendations
3. **Session Tracking**: Monitor work session progress
4. **Status Updates**: Quick overview of current work

**Performance**:
- Fast response (<100ms typical)
- Cached for 30 seconds for performance
- Prediction adds ~20ms if enabled

---


---

## Use Cases

### Morning Workflow



### Session Analysis



### Smart Workflow Suggestions



---

## Performance

- **analyze_work_session**: <50ms typical
- **predict_next_action**: <100ms typical
- **get_current_context**: <100ms typical (cached for 30s)
- Memory footprint: ~5MB for session tracking

---

## Integration Notes

Claude Code can automatically:
1. **Call analyze_work_session** periodically (every 15-30 minutes)
2. **Call predict_next_action** when user asks "what should I do next?"
3. **Call get_current_context** at session start to understand project state
4. **Use predictions proactively** to suggest next steps

You can also manually trigger:
- "Analyze my work session"
- "What should I do next?"
- "Show me current project context"

---

[← Back to Index](mcp-index.md) | [Next: Proactive Suggestions →](mcp-suggestions.md)
