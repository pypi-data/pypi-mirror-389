# MCP Proactive Monitoring

**Real-time File Change Tracking and Pattern Detection**

[← Back to Index](mcp-index.md) | [Repository Intelligence](mcp-repository-intelligence.md)

## Proactive Monitoring Tools (v0.13.0+)

### 1. watch_project_changes

Enable or disable real-time file monitoring to track changes and detect patterns.

**Parameters**:
- `enabled` (boolean, required): True to start monitoring, False to stop

**Returns**: Dictionary with:
- `status` - "success" or "error"
- `monitoring` - Current monitoring state (true/false)
- `message` - Status message
- `config` - Monitoring configuration (when enabled):
  - `watch_patterns` - File patterns being watched
  - `ignore_patterns` - Ignored file patterns
  - `debounce_seconds` - Debounce interval

**Example**:
```python
# Enable monitoring
result = watch_project_changes(enabled=True)
# → {"status": "success", "monitoring": true, "message": "File monitoring started", ...}

# Disable monitoring
result = watch_project_changes(enabled=False)
# → {"status": "success", "monitoring": false, "message": "File monitoring stopped"}
```

**Features**:
- Real-time file change detection using `watchdog`
- Configurable file patterns (supports `.py`, `.js`, `.ts`, `.go`, etc.)
- Automatic ignore patterns (`.git/`, `node_modules/`, `__pycache__/`, etc.)
- Debouncing (500ms) to avoid duplicate events
- Background monitoring (non-blocking)

**Use Cases**:
1. **Continuous Monitoring**: Track ongoing development activity
2. **Pattern Detection**: Identify refactoring, bulk edits, new features
3. **Context Awareness**: Provide real-time suggestions based on changes
4. **Workflow Automation**: Auto-update KB entries from code changes

**Note**: Monitoring runs in background. Use `get_recent_changes()` to retrieve detected changes.

---

### 2. get_recent_changes

Get recent file changes and detected patterns from the monitoring system.

**Parameters**:
- `minutes` (integer, optional): Time window in minutes (default: 60)

**Returns**: Dictionary with:
- `status` - "success" or "error"
- `monitoring_active` - Whether monitoring is currently running
- `time_window` - Requested time window
- `changes` - List of file change events:
  - `timestamp` - When change occurred (ISO 8601)
  - `event_type` - "modified", "created", "deleted", "moved"
  - `file_path` - Affected file path
  - `metadata` - Additional event details
- `patterns` - Detected patterns with confidence scores:
  - `type` - Pattern type (bulk_edit, new_feature, refactoring, cleanup, config_change)
  - `confidence` - Confidence score (0.0-1.0)
  - `description` - Human-readable description
  - `files_involved` - List of affected files
  - `detected_at` - When pattern was detected

**Pattern Types**:
- **bulk_edit**: Same file modified multiple times rapidly
- **new_feature**: Multiple new files created in short time
- **refactoring**: Files renamed or moved together
- **cleanup**: Files deleted in bulk
- **config_change**: Configuration files modified

**Example**:
```python
# Get last hour of changes
result = get_recent_changes(minutes=60)
# → {
#   "status": "success",
#   "monitoring_active": true,
#   "changes": [
#     {"timestamp": "2025-10-26T10:30:00", "event_type": "modified", "file_path": "src/auth.py"},
#     {"timestamp": "2025-10-26T10:31:00", "event_type": "created", "file_path": "tests/test_auth.py"}
#   ],
#   "patterns": [
#     {
#       "type": "new_feature",
#       "confidence": 0.85,
#       "description": "New feature development detected",
#       "files_involved": ["src/auth.py", "tests/test_auth.py"],
#       "detected_at": "2025-10-26T10:31:30"
#     }
#   ]
# }

# Get last 10 minutes
result = get_recent_changes(minutes=10)
```

**Use Cases**:
1. **Progress Summary**: "What have I worked on in the last hour?"
2. **Pattern Recognition**: "Am I refactoring or adding features?"
3. **Context for Suggestions**: "Based on recent changes, suggest next tasks"
4. **Activity Log**: Track development patterns over time

**Note**: Returns empty lists if monitoring is not active or no changes in time window.

---

## Integration Workflow

Here's a typical workflow for using Proactive Monitoring with Claude Code:

### 1. Start Monitoring
```python
# Claude Code automatically calls this when starting a work session
result = watch_project_changes(enabled=True)
# → Monitoring starts in background
```

### 2. Development Phase
```python
# User edits multiple files...
# src/auth.py (10:30:00)
# src/auth.py (10:30:15) - quick fix
# tests/test_auth.py (10:31:00) - add tests
```

### 3. Check Recent Activity
```python
# Claude Code periodically calls this (or when user asks)
changes = get_recent_changes(minutes=30)
# → Returns:
#   - 3 file changes (2 edits to auth.py, 1 new test file)
#   - Pattern: "bulk_edit" (auth.py modified rapidly)
#   - Pattern: "new_feature" (new test file suggests feature work)
```

### 4. Proactive Suggestions
Based on detected patterns, Claude Code can:
- **Bulk Edit Pattern**: "I notice you're iterating on auth.py. Need help with the logic?"
- **New Feature Pattern**: "You're adding authentication. Should I check for related KB entries?"
- **Refactoring Pattern**: "Detected file moves. Want me to update import statements?"

### 5. End Session
```python
# Optional: Stop monitoring when done
result = watch_project_changes(enabled=False)
```

### Performance Characteristics
- **Event Processing**: <5ms per file change
- **Pattern Detection**: <10ms (runs after debounce)
- **Memory Footprint**: ~2MB for 1000 events
- **Background CPU**: <1% (idle when no changes)

### Transparent Usage in Claude Code
Claude Code can automatically:
1. **Start monitoring** when project opens
2. **Check patterns** periodically (every 5-10 minutes)
3. **Provide suggestions** based on detected patterns
4. **Stop monitoring** when project closes

You can also manually trigger these via natural language:
- "Start monitoring my files"
- "What have I changed in the last hour?"
- "Stop file monitoring"

---

## Troubleshooting

### Monitoring Issues

### Proactive Monitoring Issues

**Issue**: `watch_project_changes` returns "already running" error
- **Solution**: Call `watch_project_changes(enabled=False)` first to stop existing monitor
- **Alternative**: Check if monitoring is active with `get_recent_changes()`

**Issue**: `get_recent_changes` returns empty results
- **Solution**: Ensure monitoring is enabled with `watch_project_changes(enabled=True)`
- **Verify**: Check `monitoring_active` field in response

**Issue**: Too many events being captured
- **Solution**: Adjust `ignore_patterns` in MonitorConfig
- **Common patterns**: `*.pyc`, `*.log`, `.DS_Store`, `node_modules/`
- **Edit**: `.clauxton/monitor-config.json` (if exists)

**Issue**: Patterns not being detected
- **Verify**: Enough file changes occurred (patterns need ≥2 files or ≥3 edits)
- **Check**: Time window is sufficient (use `minutes=120` for longer history)
- **Debug**: Check event count in `changes` list

**Issue**: High CPU usage during monitoring
- **Solution**: Add more ignore patterns to reduce event volume
- **Verify**: Large directories like `node_modules/`, `.venv/` are ignored
- **Alternative**: Disable monitoring when not needed

### Repository Map Issues

**Issue**: `search_symbols` returns empty results
- **Solution**: Run `index_repository()` first to build the symbol map
- **Check**: Ensure `.clauxton/map/index.json` exists

**Issue**: Symbols not found after adding new code
- **Solution**: Re-run `index_repository()` to refresh the index
- **Tip**: Index is cached, rebuild after significant changes

**Issue**: Slow indexing performance
- **Check**: Project size (>10,000 files may take longer)
- **Solution**: Add large directories to `.gitignore` (node_modules, .venv, etc.)
- **Verify**: Run `du -sh .clauxton/map/` to check index size

**Issue**: Unicode errors during indexing
- **Solution**: Ensure files are UTF-8 encoded
- **Note**: Binary files are automatically skipped

**Issue**: `semantic` search mode not working
- **Solution**: Install scikit-learn: `pip install scikit-learn`
- **Fallback**: Automatically falls back to `exact` mode if unavailable

### General MCP Issues

**Issue**: MCP Server not connecting
- **Check**: `.claude-plugin/mcp-servers.json` configuration
- **Verify**: `clauxton-mcp --help` works
- **Solution**: Restart Claude Code after configuration changes

**Issue**: "Clauxton not initialized" error
- **Solution**: Run `clauxton init` in project root
- **Verify**: `.clauxton/` directory exists

**Issue**: Permission errors
- **Check**: `.clauxton/` directory permissions (should be 700)
- **Solution**: `chmod 700 .clauxton && chmod 600 .clauxton/*.yml`

---

---


---

[← Back to Index](mcp-index.md) | [Next: Context Intelligence →](mcp-context-intelligence.md)
