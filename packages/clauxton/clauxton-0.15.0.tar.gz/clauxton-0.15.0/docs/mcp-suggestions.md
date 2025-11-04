# MCP Proactive Suggestions

**KB Update Suggestions and Anomaly Detection**

[← Back to Index](mcp-index.md) | [Context Intelligence](mcp-context-intelligence.md)

## Proactive Suggestion Tools (v0.13.0 Week 2) 🔥 NEW

### suggest_kb_updates

**Analyze recent file changes to suggest Knowledge Base documentation opportunities.**

Intelligently analyzes recent development activity and suggests KB entries for:
- Module-wide changes (architecture decisions)
- New features (feature documentation)
- Configuration changes (setup documentation)
- Documentation gaps (missing docs)

**Parameters**:
- `threshold` (float, optional): Minimum confidence threshold (default: 0.7, range: 0.0-1.0)
- `minutes` (int, optional): Time window to analyze in minutes (default: 10)
- `max_suggestions` (int, optional): Maximum number of suggestions to return (default: 5)

**Returns**: Dictionary with:
- `status`: "success", "no_suggestions", "no_changes", or "error"
- `suggestion_count`: Number of suggestions returned
- `time_window_minutes`: Time window analyzed
- `threshold`: Confidence threshold used
- `suggestions`: List of KB/documentation suggestions with:
  - `type`: "kb_entry" or "documentation"
  - `title`: Suggestion title
  - `description`: Detailed description
  - `confidence`: Confidence score (0.0-1.0)
  - `priority`: "low", "medium", "high", or "critical"
  - `affected_files`: List of relevant files
  - `reasoning`: Explanation of why this suggestion was made
  - `metadata`: Additional context
  - `created_at`: Timestamp

**Example**:
```python
# After refactoring authentication module
suggest_kb_updates(threshold=0.7, minutes=30, max_suggestions=5)

# Returns:
{
  "status": "success",
  "suggestion_count": 2,
  "suggestions": [
    {
      "type": "kb_entry",
      "title": "Document changes in src/auth",
      "description": "3 files modified in authentication module",
      "confidence": 0.85,
      "priority": "medium",
      "affected_files": ["src/auth/login.py", "src/auth/token.py"],
      "reasoning": "Multiple files in same module indicate architectural change"
    }
  ]
}
```

**Use Cases**:
- **Auto-Documentation**: "What should I document after this refactoring?"
- **Knowledge Capture**: "Any KB entries I should create based on recent work?"
- **Team Communication**: "What context should I share with the team?"

**Performance**: <200ms for 10 files, <500ms for 100 files

---

### detect_anomalies

**Detect unusual development activity patterns with severity levels.**

Analyzes recent file changes to identify anomalies that may require attention:
1. **Rapid changes** (many files in short time)
2. **Mass deletions** (5+ files deleted)
3. **Weekend activity** (work on Saturday/Sunday)
4. **Late-night activity** (work 10 PM - 6 AM)

**Parameters**:
- `minutes` (int, optional): Time window to analyze in minutes (default: 60)
- `severity_threshold` (string, optional): Minimum severity level to return
  Values: "low" (all), "medium" (medium+), "high" (high+), "critical" (critical only)

**Returns**: Dictionary with:
- `status`: "success", "no_anomalies", "no_changes", or "error"
- `anomaly_count`: Number of anomalies detected
- `time_window_minutes`: Time window analyzed
- `severity_threshold`: Severity threshold used
- `anomalies`: List of detected anomalies (sorted by severity: critical → high → medium → low) with:
  - `type`: "anomaly"
  - `title`: Anomaly description
  - `description`: Detailed explanation
  - `confidence`: Confidence score (0.0-1.0)
  - `priority`: Task priority level
  - `severity`: "low", "medium", "high", or "critical"
  - `affected_files`: List of relevant files
  - `reasoning`: Explanation
  - `metadata`: Additional data (e.g., change_count, deletion_count, ratios)
  - `created_at`: Timestamp

**Severity Levels**:
- **critical**: 20+ rapid changes (immediate attention required)
- **high**: 10+ rapid changes, mass deletions (review soon)
- **medium**: 5+ rapid changes, weekend work (worth noting)
- **low**: Late-night activity, minor patterns (informational)

**Example**:
```python
# Check for anomalies in last hour
detect_anomalies(minutes=60, severity_threshold="medium")

# Returns:
{
  "status": "success",
  "anomaly_count": 2,
  "anomalies": [
    {
      "type": "anomaly",
      "title": "Rapid changes: 15 changes in 10 minutes",
      "description": "15 files changed very quickly. This may indicate automated refactoring or mass find-replace.",
      "confidence": 0.82,
      "priority": "high",
      "severity": "high",
      "metadata": {"change_count": 15, "time_span_minutes": 10}
    },
    {
      "type": "anomaly",
      "title": "Mass deletion: 8 files deleted",
      "description": "8 files have been deleted. Ensure this is intentional and update documentation if needed.",
      "confidence": 0.77,
      "priority": "high",
      "severity": "medium"
    }
  ]
}
```

**Use Cases**:
- **Quality Assurance**: "Any unusual patterns in my recent work?"
- **Work-Life Balance**: "Am I working too much late at night?"
- **Risk Detection**: "Any potentially risky changes I should review?"
- **Team Health**: "How are team work patterns looking?"

**Performance**: <150ms for 20 files, <300ms for 100 files

---


---

## Integration Workflow

### Typical Usage Pattern

```python
# 1. After working for a while (10-30 minutes)
suggestions = suggest_kb_updates(threshold=0.7, minutes=30, max_suggestions=5)

if suggestions['status'] == 'success':
    for sug in suggestions['suggestions']:
        print(f"[{sug['priority']}] {sug['title']}")
        print(f"  Confidence: {sug['confidence']:.0%}")
        print(f"  Files: {', '.join(sug['affected_files'][:3])}")
        print(f"  Reason: {sug['reasoning']}\n")

# 2. Check for anomalies
anomalies = detect_anomalies(minutes=60, severity_threshold="medium")

if anomalies['status'] == 'success' and anomalies['anomaly_count'] > 0:
    for anom in anomalies['anomalies']:
        severity_indicator = "🔴" if anom['severity'] == 'critical' else "🟠" if anom['severity'] == 'high' else "🟡"
        print(f"{severity_indicator} [{anom['severity'].upper()}] {anom['title']}")
        print(f"  {anom['description']}\n")
```

### Proactive Automation

Claude Code can automatically:
1. **Call suggest_kb_updates** every 30-60 minutes during active work
2. **Call detect_anomalies** after significant file changes (10+ files)
3. **Present suggestions** proactively when confidence > 0.8
4. **Alert on anomalies** when severity is high or critical

---

## Best Practices

### KB Update Suggestions

**When to call**:
- After completing a feature (30-60 minutes of work)
- After refactoring a module
- Before creating a pull request
- At end of work session

**Threshold guidance**:
- `threshold=0.9`: Only very high-confidence suggestions (fewer results)
- `threshold=0.7`: Balanced (default, recommended)
- `threshold=0.5`: More suggestions, some may be false positives

### Anomaly Detection

**When to call**:
- After bulk operations (mass edits, renames, deletions)
- Before committing major changes
- Daily summary of work patterns
- Team health monitoring

**Severity threshold guidance**:
- `"critical"`: Only urgent issues requiring immediate attention
- `"high"`: Important patterns to review soon
- `"medium"`: Noteworthy patterns (default, recommended)
- `"low"`: All patterns including informational

---

## Response Handling

### No Suggestions/Anomalies

```python
result = suggest_kb_updates(minutes=10)
if result['status'] == 'no_suggestions':
    # Not enough activity or patterns below threshold
    pass
elif result['status'] == 'no_changes':
    # No file changes in time window
    pass
```

### Error Handling

```python
try:
    suggestions = suggest_kb_updates(threshold=0.7, minutes=30)
    if suggestions['status'] == 'error':
        print(f"Error: {suggestions.get('error', 'Unknown error')}")
except Exception as e:
    print(f"Exception calling suggest_kb_updates: {e}")
```

---

## Performance Characteristics

- **suggest_kb_updates**: <200ms for 10 files, <500ms for 100 files
- **detect_anomalies**: <150ms for 20 files, <300ms for 100 files
- Memory footprint: ~3MB for tracking 100 files
- CPU: <5% during analysis

---

[← Back to Index](mcp-index.md) | [Overview](mcp-overview.md)
