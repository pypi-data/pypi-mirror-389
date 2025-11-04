# Best Practices for Context Intelligence

**Optimize your workflow with these proven practices**

---

## General Principles

### 1. Let Context Intelligence Work for You

✅ **DO**:
- Ask natural language questions ("What should I do next?")
- Trust the predictions when confidence is high (>0.8)
- Use session analysis to improve focus
- Take breaks when suggested

❌ **DON'T**:
- Manually track session time (Context Intelligence does this)
- Ignore low focus scores (investigate the cause)
- Override high-confidence predictions without reason

### 2. Establish Routine Workflows

Create consistent patterns:

**Morning**:
```bash
# 1. Check context
"Where did I leave off?"

# 2. Review plan
"What should I work on today?"
```

**During Work**:
```bash
# Every 60-90 minutes
"Analyze my session"

# Before commits
"Should I run tests first?"
```

**Evening**:
```bash
# Wrap up
"Summarize my work today"
"Should I commit before leaving?"
```

---

## Session Management

### Optimize Focus Score

**High Focus (0.8+)**:
- Stay in one module/feature
- Minimize context switching
- Use focused time blocks (Pomodoro: 25min work + 5min break)

**Maintain Focus**:
- Close unnecessary files/tabs
- Batch similar tasks (all testing together, all documentation together)
- Use git stash for interruptions

**Example**:
```bash
# Bad: Low focus (0.4)
# Edit auth.py → Edit payments.py → Edit tests → Edit docs → Edit config
# (5 different areas in 30 minutes)

# Good: High focus (0.85)
# Edit auth.py → Edit auth_tests.py → Fix auth bugs → Update auth docs
# (1 area, related files)
```

### Break Management

**When to Take Breaks**:
- After 90 minutes continuous work
- When focus score drops below 0.5
- When predicted action is `take_break` (confidence >0.7)

**Break Duration**:
- Short breaks: 5-10 minutes (every 60-90min)
- Long breaks: 15-30 minutes (lunch, mid-afternoon)

**During Breaks**:
- Step away from computer
- Don't check work emails/Slack
- Context Intelligence will detect when you return

---

## Action Prediction

### When to Follow Predictions

**High Confidence (0.8+)**: Almost always follow
```bash
Prediction: run_tests (confidence: 0.87)
→ Action: Run tests immediately
```

**Medium Confidence (0.5-0.8)**: Use as suggestion
```bash
Prediction: commit_changes (confidence: 0.65)
→ Action: Review changes first, then commit if ready
```

**Low Confidence (<0.5)**: Ignore or investigate
```bash
Prediction: no_clear_action (confidence: 0.35)
→ Action: Continue current work, check again later
```

### Override Predictions Wisely

Valid reasons to override:
- You know something the algorithm doesn't (e.g., tests already run)
- External factors (meeting scheduled, urgent bug report)
- Different workflow preference

**Example**:
```bash
# Prediction: create_pr (confidence: 0.82)
# But: You want to add more documentation first
# → Override: "I'll add docs first, then create PR"
```

---

## Performance Optimization

### Context Caching

**Leverage 30-second cache**:
```python
# Efficient: Multiple calls within 30s use cache
context = get_current_context()  # Fresh (100ms)
context = get_current_context()  # Cached (5ms)
context = get_current_context()  # Cached (5ms)

# After 30 seconds
context = get_current_context()  # Fresh again (100ms)
```

**Skip prediction when not needed**:
```python
# Fast context (no prediction)
context = get_current_context(include_prediction=False)  # 50ms

# Full context (with prediction)
context = get_current_context(include_prediction=True)  # 100ms
```

### Reduce Tool Calls

**Instead of**:
```bash
"What's my session duration?"  # → analyze_work_session()
"What's my focus score?"       # → analyze_work_session() again
"How many breaks?"              # → analyze_work_session() again
```

**Do**:
```bash
"Analyze my work session"  # → analyze_work_session() once
# Returns: duration, focus score, breaks, all in one call
```

---

## Git Integration

### Smart Commits

**Before committing**:
```bash
# 1. Check prediction
"Should I commit now?"

# If prediction is 'run_tests':
pytest
# If tests pass, commit

# If prediction is 'review_code':
git diff --cached
# Review, then commit
```

**Commit message templates**:
```bash
# Let Claude Code draft commit messages
"Draft a commit message for these changes"

# Claude analyzes git diff and suggests:
# "feat: add email notification system
#
# - Implement SMTP integration
# - Add customizable templates
# - Add 15 tests with 100% coverage"
```

### Branch Management

**Feature branches**:
```bash
# Context Intelligence tracks per-branch
git checkout -b feature/new-feature
# → New session tracking starts
# → Independent focus scores
# → Separate predictions
```

**Branch switching**:
```bash
# Before switching
git stash save "WIP: feature work"

# Switch
git checkout another-branch

# Context Intelligence detects the switch
# Session resets for new branch context
```

---

## Team Practices

### Collaborative Development

**Pair Programming**:
- One person codes, other monitors Context Intelligence
- Check focus score every 30 minutes
- Take breaks together

**Code Reviews**:
```bash
# Before review
git checkout pr/feature-branch
"Give me context on this branch"
# → Get commit history, change summary, key areas

# After review
"Based on this PR, what's missing?"
# → Check for tests, docs, edge cases
```

### Documentation

**Auto-document sessions**:
```bash
# End of day
"Create a summary of today's work for the team"

# Claude uses Context Intelligence data:
# - Session duration
# - Files modified
# - Commits made
# - Areas worked on
```

---

## Configuration Tuning

### Adjust Thresholds

```yaml
# .clauxton/config.yml

proactive:
  # Session management
  session_timeout_minutes: 30  # Default: 30
  # ↑ Increase if you work in long, focused blocks
  # ↓ Decrease if you have frequent interruptions

  # Focus scoring
  focus_threshold: 0.7  # Default: 0.7
  # ↑ Increase for stricter focus requirements
  # ↓ Decrease if you naturally switch files frequently

  # Break detection
  break_threshold_minutes: 15  # Default: 15
  # ↑ Increase to detect longer breaks only
  # ↓ Decrease to catch short coffee breaks
```

### Per-Project Configuration

Different projects may need different settings:

```bash
# High-focus project (deep concentration work)
# .clauxton/config.yml
proactive:
  focus_threshold: 0.8
  break_threshold_minutes: 20

# Multi-tasking project (many small files)
# .clauxton/config.yml
proactive:
  focus_threshold: 0.6
  session_timeout_minutes: 20
```

---

## Common Patterns

### Morning Planning

```bash
# 1. Context
"Where did I leave off?"

# 2. Review uncommitted work
git status
git diff

# 3. Plan
"What are the priorities today?"

# 4. Start work
# (Context Intelligence begins tracking)
```

### Feature Development

```bash
# 1. Create branch
git checkout -b feature/name

# 2. Implement (60-90 minute blocks)
# ... code ...

# 3. Check progress
"Analyze my session"

# 4. Pre-commit
"What should I do before committing?"

# 5. Commit
git add . && git commit

# 6. Repeat
```

### Bug Fixing

```bash
# 1. Stash current work
git stash

# 2. Create bugfix branch
git checkout -b bugfix/issue

# 3. Fix quickly (< 30 minutes)
# ... fix ...

# 4. Commit
git commit -m "fix: ..."

# 5. Return
git checkout previous-branch
git stash pop

# 6. Resume
"Where was I?"
```

---

## Anti-Patterns to Avoid

### ❌ Ignoring Focus Scores

**Bad**:
```bash
# Focus: 0.35 (low)
# "I'll keep working anyway"
# → Result: Lower productivity, more bugs
```

**Good**:
```bash
# Focus: 0.35 (low)
"Why is my focus low?"
# → Identify cause (distractions, unclear requirements)
# → Take short break
# → Refocus on one task
```

### ❌ Overriding High-Confidence Predictions

**Bad**:
```bash
# Prediction: run_tests (confidence: 0.92)
# "I'll skip tests and commit anyway"
# → Result: Bugs in production
```

**Good**:
```bash
# Prediction: run_tests (confidence: 0.92)
# Run tests first
pytest
# Then commit
```

### ❌ Not Taking Breaks

**Bad**:
```bash
# Session: 180 minutes, no breaks
# Focus: 0.42 (low and declining)
# "I'll power through"
# → Result: Exhaustion, mistakes
```

**Good**:
```bash
# Session: 90 minutes
# Prediction: take_break (confidence: 0.85)
# Take 10-minute break
# → Result: Refreshed, better focus
```

---

## Metrics to Track

### Personal KPIs

Track over time to improve:

1. **Average focus score** (goal: >0.7)
2. **Session duration** (goal: 60-90 min blocks)
3. **Break frequency** (goal: every 90 min)
4. **Prediction accuracy** (are high-confidence predictions usually correct?)

### Weekly Review

```bash
# End of week
"Summarize my productivity this week"

# Analyze:
# - Total focus time
# - Average focus score
# - Break patterns
# - Most productive times of day
```

---

## Summary

**Key Takeaways**:

1. ✅ Trust high-confidence predictions (>0.8)
2. ✅ Maintain high focus (>0.7) by minimizing context switches
3. ✅ Take regular breaks (every 60-90 minutes)
4. ✅ Use Context Intelligence for routine checks (morning, pre-commit, evening)
5. ✅ Configure thresholds for your workflow
6. ✅ Track metrics to improve over time

**Remember**: Context Intelligence is a tool to enhance your workflow, not dictate it. Use it as guidance and adapt to your needs.

---

**See Also**:
- [Context Intelligence Guide](CONTEXT_INTELLIGENCE_GUIDE.md)
- [Workflow Examples](WORKFLOW_EXAMPLES.md)
- [Troubleshooting](TROUBLESHOOTING.md)
