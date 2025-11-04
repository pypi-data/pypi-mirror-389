# Troubleshooting Guide

**Common issues and solutions for Context Intelligence**

---

## Quick Diagnosis

Use this flowchart to identify your issue:

```
Issue Type?
├─ Session Analysis → Section 1
├─ Action Prediction → Section 2
├─ Project Context → Section 3
├─ Performance → Section 4
└─ Configuration → Section 5
```

---

## 1. Session Analysis Issues

### Issue: "No session detected" (status: no_session)

**Symptoms**:
```python
result = analyze_work_session()
# → {"status": "no_session", "message": "No active files detected"}
```

**Causes**:
- No files modified in the last 30 minutes
- All files were deleted (not modified)
- Working in a different directory

**Solutions**:

✅ **Start working on files**:
```bash
# Edit any file
echo "# Working" >> README.md
```

✅ **Check working directory**:
```bash
# Verify you're in project root
pwd
# → Should be /path/to/your/project

# If wrong directory
cd /path/to/your/project
```

✅ **Verify files exist**:
```bash
ls -la  # Check files are present
git status  # Check git sees changes
```

---

### Issue: Focus score seems wrong

**Symptoms**:
- Focus score is 0.3 but you felt focused
- Focus score doesn't change even when switching many files

**Causes**:
- Focus is calculated over entire session (not just recent work)
- Early file switches lower the score
- Formula: `1 - (file_switches / (duration_minutes / 10))`

**Solutions**:

✅ **Understand the calculation**:
```python
# Example 1: High focus
# Duration: 60 minutes, File switches: 3
# Focus = 1 - (3 / 6) = 0.50 (medium)

# Example 2: Low focus
# Duration: 60 minutes, File switches: 15
# Focus = 1 - (15 / 6) = -1.5 → 0.00 (clamped to 0)
```

✅ **Reset session**:
```bash
# Take a 15+ minute break
# → New session starts after break
# → Focus score resets
```

✅ **Accept early fluctuations**:
- Focus score stabilizes after 30-60 minutes
- Early in session, small changes have large impact

---

### Issue: Breaks not detected

**Symptoms**:
- Took a 20-minute lunch break
- `breaks` list is empty

**Causes**:
- Break was < 15 minutes (default threshold)
- File system timestamps not updated correctly
- System clock issues

**Solutions**:

✅ **Check break threshold**:
```yaml
# .clauxton/config.yml
proactive:
  break_threshold_minutes: 15  # Default
  # Set to 10 for shorter breaks
```

✅ **Verify timestamps**:
```bash
# Check file modification times
stat -c '%y %n' $(find . -type f -mmin -120)
# Should show files modified 2 hours ago
```

✅ **Manual break tracking**:
- Take breaks >= 15 minutes for detection
- Or lower threshold in config

---

## 2. Action Prediction Issues

### Issue: Always returns "no_clear_action"

**Symptoms**:
```python
result = predict_next_action()
# → {"action": "no_clear_action", "confidence": 0.35}
```

**Causes**:
- Not enough context (too early in session)
- Ambiguous state (multiple competing signals)
- All heuristics have low confidence

**Solutions**:

✅ **Continue working**:
```bash
# Do more work (edit files, commit, etc.)
# After 15-30 minutes, try again
result = predict_next_action()
```

✅ **Create clearer context**:
```bash
# If many uncommitted changes
git add .  # Stage changes

# If no tests modified
# → Edit test files to signal testing intent
```

✅ **Ask specific questions**:
```bash
# Instead of generic "What next?"
# Ask specific questions:
"Should I run tests now?"
"Am I ready to commit?"
"Should I create a PR?"
```

---

### Issue: Wrong prediction (low accuracy)

**Symptoms**:
- Predicts `run_tests` but tests already passed
- Predicts `commit_changes` but code isn't ready

**Causes**:
- Algorithm doesn't know external state (tests already run, bugs exist)
- Heuristics conflict
- Context incomplete

**Solutions**:

✅ **Provide feedback**:
```bash
# Tell Claude Code the prediction was wrong
"I already ran tests, they passed"
# Claude adjusts and suggests next step
```

✅ **Use predictions as suggestions, not commands**:
- High confidence (>0.8): Strong suggestion
- Medium confidence (0.5-0.8): Consider it
- Low confidence (<0.5): Ignore

✅ **Check reasoning**:
```python
prediction = predict_next_action()
print(prediction['reasoning'])
# → Understand why it made that prediction
# → Decide if reasoning is valid for your situation
```

---

## 3. Project Context Issues

### Issue: Context is stale/outdated

**Symptoms**:
- Context shows old branch
- Uncommitted changes count is wrong
- Recent commits don't appear

**Causes**:
- Context is cached (30-second cache)
- Working directory changed
- Git state changed outside of session

**Solutions**:

✅ **Wait for cache expiry**:
```python
# Cache expires after 30 seconds
# Wait 30 seconds, then call again
import time
time.sleep(30)
context = get_current_context()
```

✅ **Trigger cache invalidation**:
```bash
# Modify any file (forces new context)
touch dummy.txt
rm dummy.txt
```

✅ **Verify working directory**:
```bash
pwd  # Check you're in project root
git status  # Verify git sees correct state
```

---

### Issue: Missing prediction in context

**Symptoms**:
```python
context = get_current_context()
# → predicted_next_action is None
```

**Causes**:
- `include_prediction=False` was used
- Prediction calculation failed (error)
- No context for prediction

**Solutions**:

✅ **Enable prediction**:
```python
# Explicitly enable prediction
context = get_current_context(include_prediction=True)
```

✅ **Check for errors**:
```python
context = get_current_context()
if context.get('prediction_error'):
    print(f"Prediction failed: {context['prediction_error']}")
```

---

## 4. Performance Issues

### Issue: MCP tools are slow (>1 second)

**Symptoms**:
- `analyze_work_session()` takes 2+ seconds
- `get_current_context()` takes 1+ second

**Causes**:
- Large project (1000+ files)
- Git operations slow (large repo history)
- No caching (cache disabled or expired)

**Solutions**:

✅ **Use caching**:
```python
# First call: Slow (~500ms)
context = get_current_context()

# Subsequent calls (within 30s): Fast (<10ms)
context = get_current_context()  # Cached
```

✅ **Skip prediction for speed**:
```python
# Fast context (no prediction)
context = get_current_context(include_prediction=False)
# → ~50% faster
```

✅ **Check git performance**:
```bash
# Test git operations
time git status  # Should be <100ms
time git log -5  # Should be <50ms
time git diff --shortstat  # Should be <100ms

# If slow, check repo size
git count-objects -vH
# → If > 1GB, consider shallow clone
```

---

### Issue: High memory usage

**Symptoms**:
- Python process uses >500MB RAM
- System slows down during analysis

**Causes**:
- Large file content being loaded
- Event queue unbounded
- Memory leak

**Solutions**:

✅ **Check event queue size**:
```yaml
# .clauxton/config.yml
proactive:
  max_events: 1000  # Limit event history
```

✅ **Monitor memory**:
```bash
# Check Python memory usage
ps aux | grep python
# → Should be <100MB for normal projects
```

✅ **Restart if needed**:
```bash
# Stop monitoring (if enabled)
# Memory will be released
```

---

## 5. Configuration Issues

### Issue: Config changes not taking effect

**Symptoms**:
- Changed `break_threshold_minutes` to 10
- Still only detects breaks >= 15 minutes

**Causes**:
- Config file syntax error
- Config file in wrong location
- Cache using old config

**Solutions**:

✅ **Verify config location**:
```bash
# Config should be here
ls -la .clauxton/config.yml
# → Should exist

# Check syntax
python -c "import yaml; yaml.safe_load(open('.clauxton/config.yml'))"
# → Should not error
```

✅ **Restart to reload config**:
```bash
# Config is loaded at startup
# Restart Python process or Claude Code
```

✅ **Check config format**:
```yaml
# Correct format
proactive:
  break_threshold_minutes: 10

# Wrong format (will not work)
break_threshold_minutes: 10  # Missing 'proactive:' key
```

---

### Issue: Config file not found

**Symptoms**:
- Error: "Config file not found"
- Using default settings even though config exists

**Causes**:
- Config in wrong directory
- Config file name wrong
- Permissions issue

**Solutions**:

✅ **Create config**:
```bash
# Initialize if missing
clauxton init

# Manually create
mkdir -p .clauxton
cat > .clauxton/config.yml << 'EOF'
proactive:
  enabled: true
  session_timeout_minutes: 30
  focus_threshold: 0.7
  break_threshold_minutes: 15
EOF
```

✅ **Check permissions**:
```bash
# Config must be readable
chmod 644 .clauxton/config.yml
```

---

## 6. Integration Issues (Claude Code)

### Issue: Claude Code not using Context Intelligence

**Symptoms**:
- Ask "Analyze my session"
- Claude responds generically without MCP tool data

**Causes**:
- MCP server not configured
- MCP tools not accessible
- Claude Code not recognizing intent

**Solutions**:

✅ **Verify MCP setup**:
```bash
# Check MCP config exists
ls -la .claude-plugin/mcp-servers.json

# Verify entry for Clauxton
cat .claude-plugin/mcp-servers.json | grep clauxton
```

✅ **Test MCP tools manually**:
```bash
# Test tool directly
python -m clauxton.mcp.server
# → Should start server (Ctrl+C to exit)
```

✅ **Be more specific**:
```bash
# Instead of
"Analyze session"

# Try
"Use analyze_work_session MCP tool"
"Call get_current_context()"
```

---

## 7. Common Error Messages

### Error: "ImportError: No module named 'clauxton.proactive'"

**Cause**: Clauxton not installed or wrong version

**Solution**:
```bash
pip install --upgrade clauxton
# → Install v0.13.0+
```

---

### Error: "ValidationError: focus_score must be between 0 and 1"

**Cause**: Internal calculation error (bug)

**Solution**:
```bash
# Report the issue with details:
# 1. Session duration
# 2. File switch count
# 3. Full error traceback

# Workaround: Restart session
# (take 15+ minute break)
```

---

### Error: "RuntimeError: Git repository not found"

**Cause**: Not in a git repository or .git directory missing

**Solution**:
```bash
# Initialize git if needed
git init

# Or navigate to git repo
cd /path/to/your/repo
```

---

## 8. Debug Mode

### Enable Debug Logging

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Now all Context Intelligence operations log details
```

### Check Log Output

```bash
# Logs show:
# - Cache hits/misses
# - Performance metrics
# - Calculation details
# - Error stack traces
```

---

## Getting Help

If issues persist:

1. **Check documentation**:
   - [Context Intelligence Guide](CONTEXT_INTELLIGENCE_GUIDE.md)
   - [MCP Documentation](../mcp-context-intelligence.md)

2. **Search existing issues**:
   - https://github.com/nakishiyaman/clauxton/issues

3. **Create new issue**:
   - Include: Clauxton version, OS, error message, steps to reproduce
   - Run: `clauxton --version` and `python --version`

4. **Community support**:
   - GitHub Discussions: Ask questions, share workflows

---

## Summary of Solutions

| Issue | Quick Fix |
|-------|-----------|
| No session detected | Edit a file, verify working directory |
| Wrong focus score | Wait for session to mature (30+ min) |
| No clear action | Continue working, provide more context |
| Stale context | Wait 30s for cache expiry |
| Slow performance | Use caching, skip prediction |
| Config not working | Check syntax, restart process |
| MCP not working | Verify setup, be specific in queries |

---

**Still stuck?** Open an issue on GitHub with details!
