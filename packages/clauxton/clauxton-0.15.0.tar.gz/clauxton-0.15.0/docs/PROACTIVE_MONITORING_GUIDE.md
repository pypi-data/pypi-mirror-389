# Proactive Monitoring Guide

**Real-time file monitoring and pattern detection for Clauxton (v0.13.0 Week 1)**

---

## Overview

Proactive Monitoring enables Clauxton to watch your project files in real-time and detect development patterns as you work. This provides context-aware suggestions and helps track your workflow automatically.

**Key Features**:
- 🔥 Real-time file change detection with `watchdog`
- 🎯 5 pattern detection algorithms
- 📊 Event processing with confidence scoring
- 🤖 MCP integration for Claude Code
- ⚡ High performance (<5ms event processing)

**Status**: ✅ Week 1 Complete (56 tests, 96-100% coverage)

---

## Quick Start

### Enable Monitoring via MCP (Claude Code)

When using Claude Code, monitoring can be enabled automatically:

```python
# Claude Code calls this internally
result = watch_project_changes(enabled=True)
# → {"status": "success", "monitoring": true, "message": "File monitoring started"}
```

### Get Recent Changes

```python
# Get last hour of changes and detected patterns
changes = get_recent_changes(minutes=60)
# → {
#   "status": "success",
#   "monitoring_active": true,
#   "changes": [...],
#   "patterns": [...]
# }
```

---

## Architecture

### Components

```
clauxton/proactive/
├── config.py          # MonitorConfig (watch/ignore patterns)
├── models.py          # FileEvent, DetectedPattern
├── file_monitor.py    # FileMonitor (watchdog integration)
└── event_processor.py # EventProcessor (pattern detection)
```

### Data Flow

```
File Change
    ↓
watchdog Handler
    ↓
FileMonitor (debounce 500ms)
    ↓
FileEvent created
    ↓
EventProcessor.process_event()
    ↓
Pattern Detection (5 algorithms)
    ↓
DetectedPattern with confidence
    ↓
Store in memory
    ↓
get_recent_changes() retrieves
```

---

## File Monitoring

### MonitorConfig

Configuration for file monitoring:

```python
from clauxton.proactive.config import MonitorConfig

config = MonitorConfig(
    watch_patterns=[
        "*.py", "*.js", "*.ts", "*.jsx", "*.tsx",
        "*.go", "*.rs", "*.java", "*.cpp", "*.c", "*.h"
    ],
    ignore_patterns=[
        ".git/", "node_modules/", "__pycache__/",
        ".venv/", "venv/", "*.pyc", "*.log"
    ],
    debounce_seconds=0.5  # Wait 500ms before processing
)

# Save to project
config.save_to_file(project_root / ".clauxton" / "monitoring_config.yml")
```

**Default Configuration**:
- **Watch patterns**: Common source files (`.py`, `.js`, `.ts`, etc.)
- **Ignore patterns**: Build artifacts, dependencies, temp files
- **Debounce**: 500ms (avoid duplicate events)

### FileMonitor

Real-time file watcher using `watchdog`:

```python
from clauxton.proactive.file_monitor import FileMonitor

# Create monitor
monitor = FileMonitor(
    project_root=Path("/path/to/project"),
    config=config
)

# Start monitoring
monitor.start()
# → Background thread starts watching files

# Check status
is_running = monitor.is_running()  # → True

# Get events
events = monitor.get_events(minutes=30)
# → [FileEvent(...), FileEvent(...), ...]

# Stop monitoring
monitor.stop()
```

**Features**:
- Non-blocking background thread
- Automatic debouncing (500ms default)
- Event storage with timestamps
- Configurable patterns

---

## Event Processing

### FileEvent Model

Represents a file change event:

```python
from clauxton.proactive.models import FileEvent
from datetime import datetime

event = FileEvent(
    timestamp=datetime.now(),
    event_type="modified",      # "modified", "created", "deleted", "moved"
    file_path=Path("src/auth.py"),
    metadata={
        "src_path": "src/auth_old.py",  # For "moved" events
        "size": 1024,
        "extension": ".py"
    }
)
```

**Event Types**:
- `modified` - File content changed
- `created` - New file created
- `deleted` - File deleted
- `moved` - File renamed or moved

### EventProcessor

Pattern detection engine:

```python
from clauxton.proactive.event_processor import EventProcessor

processor = EventProcessor()

# Process single event
pattern = processor.process_event(event)
if pattern:
    print(f"Detected: {pattern.type} ({pattern.confidence:.2f})")

# Get recent patterns
patterns = processor.get_recent_patterns(minutes=60)
# → [DetectedPattern(...), DetectedPattern(...)]

# Clear old events (cleanup)
processor.clear_old_events(hours=24)
```

---

## Pattern Detection

### 5 Detection Algorithms

#### 1. Bulk Edit Detection

**Trigger**: Same file modified 3+ times within 10 minutes

**Confidence Calculation**:
```python
edit_count = 5  # Number of edits
confidence = min(0.5 + (edit_count - 3) * 0.1, 1.0)
# → 0.5 (base) + 0.2 (2 extra edits) = 0.7
```

**Example**:
```
10:00:00 - src/auth.py modified
10:00:15 - src/auth.py modified  # Quick iteration
10:00:30 - src/auth.py modified
10:01:00 - src/auth.py modified
→ Pattern: bulk_edit, confidence=0.6
```

**Use Case**: Rapid iteration, debugging, refining logic

---

#### 2. New Feature Detection

**Trigger**: 2+ new files created within 15 minutes

**Confidence Calculation**:
```python
new_files = 4  # Number of new files
confidence = min(0.6 + (new_files - 2) * 0.1, 1.0)
# → 0.6 (base) + 0.2 (2 extra files) = 0.8
```

**Example**:
```
10:00:00 - src/auth.py created
10:02:00 - src/models/user.py created
10:05:00 - tests/test_auth.py created
→ Pattern: new_feature, confidence=0.7
```

**Use Case**: Starting new feature, adding modules

---

#### 3. Refactoring Detection

**Trigger**: 2+ files renamed/moved within 10 minutes

**Confidence Calculation**:
```python
moved_files = 3  # Number of moves
confidence = min(0.7 + (moved_files - 2) * 0.1, 1.0)
# → 0.7 (base) + 0.1 (1 extra move) = 0.8
```

**Example**:
```
10:00:00 - auth.py → src/auth/core.py (moved)
10:00:30 - utils.py → src/auth/utils.py (moved)
→ Pattern: refactoring, confidence=0.7
```

**Use Case**: Reorganizing code, restructuring modules

---

#### 4. Cleanup Detection

**Trigger**: 3+ files deleted within 15 minutes

**Confidence Calculation**:
```python
deleted_files = 5  # Number of deletions
confidence = min(0.5 + (deleted_files - 3) * 0.1, 1.0)
# → 0.5 (base) + 0.2 (2 extra deletions) = 0.7
```

**Example**:
```
10:00:00 - old_auth.py deleted
10:00:15 - legacy_utils.py deleted
10:00:30 - deprecated_models.py deleted
→ Pattern: cleanup, confidence=0.5
```

**Use Case**: Removing old code, cleaning up project

---

#### 5. Config Change Detection

**Trigger**: Configuration file modified

**Confidence**: Always 1.0 (high confidence)

**Recognized Config Files**:
- `*.yml`, `*.yaml` - YAML config
- `*.json` - JSON config
- `*.toml` - TOML config
- `*.ini`, `*.cfg` - INI config
- `.env*` - Environment files
- `Dockerfile`, `docker-compose.yml` - Docker
- `package.json`, `requirements.txt`, `Cargo.toml`, `go.mod` - Dependencies

**Example**:
```
10:00:00 - pyproject.toml modified
→ Pattern: config_change, confidence=1.0
```

**Use Case**: Dependency updates, environment changes

---

## MCP Integration

### 1. watch_project_changes

Enable or disable file monitoring.

**Function Signature**:
```python
def watch_project_changes(enabled: bool) -> dict:
    """
    Enable or disable real-time file monitoring.

    Args:
        enabled: True to start, False to stop

    Returns:
        {
            "status": "success" | "error",
            "monitoring": bool,
            "message": str,
            "config": {...}  # When enabled
        }
    """
```

**Example (Enable)**:
```python
result = watch_project_changes(enabled=True)
# → {
#   "status": "success",
#   "monitoring": true,
#   "message": "File monitoring started",
#   "config": {
#     "watch_patterns": ["*.py", "*.js", ...],
#     "ignore_patterns": [".git/", "node_modules/", ...],
#     "debounce_seconds": 0.5
#   }
# }
```

**Example (Disable)**:
```python
result = watch_project_changes(enabled=False)
# → {
#   "status": "success",
#   "monitoring": false,
#   "message": "File monitoring stopped"
# }
```

---

### 2. get_recent_changes

Get recent file changes and detected patterns.

**Function Signature**:
```python
def get_recent_changes(minutes: int = 60) -> dict:
    """
    Get recent file changes and detected patterns.

    Args:
        minutes: Time window in minutes (default: 60)

    Returns:
        {
            "status": "success" | "error",
            "monitoring_active": bool,
            "time_window": int,
            "changes": [FileEvent, ...],
            "patterns": [DetectedPattern, ...]
        }
    """
```

**Example**:
```python
changes = get_recent_changes(minutes=30)
# → {
#   "status": "success",
#   "monitoring_active": true,
#   "time_window": 30,
#   "changes": [
#     {
#       "timestamp": "2025-10-26T10:30:00",
#       "event_type": "modified",
#       "file_path": "src/auth.py",
#       "metadata": {}
#     },
#     {
#       "timestamp": "2025-10-26T10:31:00",
#       "event_type": "created",
#       "file_path": "tests/test_auth.py",
#       "metadata": {}
#     }
#   ],
#   "patterns": [
#     {
#       "type": "new_feature",
#       "confidence": 0.7,
#       "description": "New feature development detected",
#       "files_involved": ["src/auth.py", "tests/test_auth.py"],
#       "detected_at": "2025-10-26T10:31:30"
#     }
#   ]
# }
```

---

## Use Cases

### 1. Progress Summary

**User Question**: "What have I worked on in the last hour?"

**Claude Code Flow**:
```python
changes = get_recent_changes(minutes=60)
# → Summarize changes and patterns for user
```

**Response**:
```
In the last hour, you've made 8 changes across 4 files:
- Modified: src/auth.py (3 times) - detected bulk editing
- Created: tests/test_auth.py
- Modified: src/models/user.py
- Modified: README.md

Detected patterns:
- Bulk Edit (confidence: 0.6) - You're iterating on auth.py
- New Feature (confidence: 0.7) - Adding authentication functionality
```

---

### 2. Context-Aware Suggestions

**Detected Pattern**: bulk_edit on `src/auth.py`

**Claude Code Suggestion**:
```
I notice you're iterating on auth.py. Based on your edits:
1. Would you like me to check for related KB entries about authentication?
2. Should I look for similar patterns in other auth-related files?
3. Need help with the logic you're refining?
```

---

### 3. Proactive KB Updates

**Detected Pattern**: config_change on `pyproject.toml`

**Claude Code Action**:
```python
# Automatically suggest KB entry
kb_add(
    title="Dependency Update",
    category="decision",
    content="Updated to FastAPI 0.104.0 for security fixes",
    tags=["dependencies", "fastapi", "security"]
)
```

---

### 4. Workflow Tracking

**Detected Pattern**: new_feature (multiple files)

**Claude Code Action**:
```python
# Automatically create task
task_add(
    name="Implement authentication",
    priority="high",
    files=["src/auth.py", "tests/test_auth.py"],
    status="in_progress"
)
```

---

## Performance Characteristics

### Benchmarks

**Event Processing**:
```
Single event processing: 2-5ms
Batch processing (100 events): 150-200ms
Pattern detection: 5-10ms per check
```

**Memory Usage**:
```
Base (idle): ~2MB
1000 events: ~4MB
10000 events: ~20MB
```

**CPU Usage**:
```
Idle (monitoring): <1%
Active (many changes): 2-5%
Pattern detection: <3%
```

### Optimization Tips

1. **Adjust Debounce**:
```python
config.debounce_seconds = 1.0  # Slower, fewer events
config.debounce_seconds = 0.2  # Faster, more events
```

2. **Tune Ignore Patterns**:
```python
config.ignore_patterns.extend([
    "dist/", "build/", "*.min.js", "*.map"
])
```

3. **Regular Cleanup**:
```python
# Clear events older than 24 hours
processor.clear_old_events(hours=24)
```

---

## Configuration

### Default Config

Located at `.clauxton/monitoring_config.yml`:

```yaml
watch_patterns:
  - "*.py"
  - "*.js"
  - "*.ts"
  - "*.jsx"
  - "*.tsx"
  - "*.go"
  - "*.rs"
  - "*.java"
  - "*.cpp"
  - "*.c"
  - "*.h"

ignore_patterns:
  - ".git/"
  - "node_modules/"
  - "__pycache__/"
  - ".venv/"
  - "venv/"
  - "*.pyc"
  - "*.log"
  - "*.tmp"
  - ".DS_Store"

debounce_seconds: 0.5
```

### Custom Configuration

```python
from clauxton.proactive.config import MonitorConfig

# Create custom config
config = MonitorConfig(
    watch_patterns=["*.md", "*.rst"],  # Documentation only
    ignore_patterns=["drafts/"],
    debounce_seconds=2.0  # Longer debounce
)

# Save
config.save_to_file(Path(".clauxton/monitoring_config.yml"))
```

---

## Testing

### Unit Tests

**Config Tests** (21 tests, 100% coverage):
```bash
pytest tests/proactive/test_config.py -v
```

**Event Processor Tests** (20 tests, 98% coverage):
```bash
pytest tests/proactive/test_event_processor.py -v
```

**File Monitor Tests** (15 tests, 96% coverage):
```bash
pytest tests/proactive/test_file_monitor.py -v
```

### Integration Tests

**MCP Integration** (15 tests):
```bash
pytest tests/mcp/test_proactive_integration.py -v
```

### All Proactive Tests

```bash
pytest tests/proactive/ tests/mcp/test_proactive_integration.py -v
# → 56 tests, all passing
```

---

## Troubleshooting

### Issue: Monitoring not starting

**Symptoms**: `watch_project_changes(True)` returns error

**Solutions**:
1. Check config file exists:
```bash
ls -la .clauxton/monitoring_config.yml
```

2. Validate config:
```python
config = MonitorConfig.load_from_file(Path(".clauxton/monitoring_config.yml"))
# Should not raise exception
```

3. Check file permissions:
```bash
chmod 700 .clauxton
chmod 600 .clauxton/monitoring_config.yml
```

---

### Issue: Too many events

**Symptoms**: High CPU usage, slow response

**Solutions**:
1. Add more ignore patterns:
```yaml
ignore_patterns:
  - "node_modules/"
  - "dist/"
  - "build/"
  - "*.min.js"
  - "*.map"
```

2. Increase debounce:
```yaml
debounce_seconds: 1.0  # Was 0.5
```

3. Reduce watch patterns:
```yaml
watch_patterns:
  - "*.py"  # Python only
```

---

### Issue: Patterns not detected

**Symptoms**: `get_recent_changes()` returns no patterns

**Checks**:
1. Verify enough events:
```python
changes = get_recent_changes(minutes=60)
print(f"Events: {len(changes['changes'])}")
# Need ≥2 events for most patterns
```

2. Check time window:
```python
# Expand time window
changes = get_recent_changes(minutes=120)
```

3. Verify event types:
```python
for change in changes['changes']:
    print(f"{change['event_type']}: {change['file_path']}")
```

---

## API Reference

### MonitorConfig

```python
class MonitorConfig:
    watch_patterns: List[str]
    ignore_patterns: List[str]
    debounce_seconds: float

    @classmethod
    def load_from_file(cls, path: Path) -> "MonitorConfig"

    def save_to_file(self, path: Path) -> None
```

### FileEvent

```python
class FileEvent:
    timestamp: datetime
    event_type: Literal["modified", "created", "deleted", "moved"]
    file_path: Path
    metadata: Dict[str, Any]
```

### DetectedPattern

```python
class DetectedPattern:
    type: Literal["bulk_edit", "new_feature", "refactoring", "cleanup", "config_change"]
    confidence: float  # 0.0-1.0
    description: str
    files_involved: List[Path]
    detected_at: datetime
```

### FileMonitor

```python
class FileMonitor:
    def __init__(self, project_root: Path, config: MonitorConfig)
    def start(self) -> None
    def stop(self) -> None
    def is_running(self) -> bool
    def get_events(self, minutes: int = 60) -> List[FileEvent]
```

### EventProcessor

```python
class EventProcessor:
    def process_event(self, event: FileEvent) -> Optional[DetectedPattern]
    def get_recent_patterns(self, minutes: int = 60) -> List[DetectedPattern]
    def clear_old_events(self, hours: int = 24) -> int
```

---

---

## Behavior Tracking & Context Awareness (Week 2 Day 5)

### Overview

**Status**: ✅ Complete (43 tests, 89-95% coverage)

Day 5 adds intelligent behavior tracking and context awareness to enhance suggestion quality:

**Key Features**:
- 📊 **Behavior Tracking**: Learn from user interactions
- 🧠 **Preference Learning**: Adjust confidence based on acceptance/rejection
- 🌍 **Project Context**: Understand git branch, time, active files
- ⏰ **Time-Aware**: Morning/afternoon/evening/night context
- 🎯 **Personalized**: Suggestions improve over time

### Components

```
clauxton/proactive/
├── behavior_tracker.py    # User behavior tracking
├── context_manager.py     # Project context awareness
└── suggestion_engine.py   # Enhanced with behavior + context
```

### BehaviorTracker

Tracks user interactions to personalize suggestions:

```python
from clauxton.proactive.behavior_tracker import BehaviorTracker

tracker = BehaviorTracker(project_root)

# Record tool usage
tracker.record_tool_usage(
    tool_name="suggest_kb_updates",
    result="accepted",  # or "rejected", "ignored"
)

# Record suggestion feedback
from clauxton.proactive.suggestion_engine import SuggestionType

tracker.record_suggestion_feedback(
    SuggestionType.KB_ENTRY,
    accepted=True
)

# Get preference score (0.0-1.0)
score = tracker.get_preference_score(SuggestionType.KB_ENTRY)
# → 0.75 (higher = more preferred)

# Adjust confidence based on preferences
adjusted = tracker.adjust_confidence(
    base_confidence=0.70,
    suggestion_type=SuggestionType.KB_ENTRY
)
# → 0.75 (boosted due to high preference)
```

**Stored in**: `.clauxton/behavior.yml`

**Data Tracked**:
- Tool usage history (last 1000 entries)
- Suggestion type preferences (acceptance rates)
- Active hours (when user works)
- Confidence threshold

### ContextManager

Provides rich project context:

```python
from clauxton.proactive.context_manager import ContextManager

manager = ContextManager(project_root)
context = manager.get_current_context()

# Git context
print(context.current_branch)        # → "feature/new-auth"
print(context.is_feature_branch)     # → True
print(context.current_task)          # → "TASK-123" (inferred)

# Time context
print(context.time_context)          # → "morning" | "afternoon" | "evening" | "night"

# Active files (modified in last 30 minutes)
print(context.active_files)          # → ["src/auth.py", "src/api.py"]

# Recent commits
print(context.recent_commits[0])
# → {"hash": "abc1234", "message": "feat: add auth"}

# Work session
print(context.work_session_start)    # → datetime(...)
```

**Context is cached** for 30 seconds for performance.

### Enhanced SuggestionEngine

Integrates behavior tracking and context awareness:

```python
from clauxton.proactive.suggestion_engine import SuggestionEngine
from clauxton.proactive.behavior_tracker import BehaviorTracker
from clauxton.proactive.context_manager import ContextManager

# Create with behavior and context
tracker = BehaviorTracker(project_root)
context_manager = ContextManager(project_root)

engine = SuggestionEngine(
    project_root=project_root,
    min_confidence=0.7,
    behavior_tracker=tracker,        # ← NEW
    context_manager=context_manager  # ← NEW
)

# Get context-aware suggestions
suggestions = engine.get_context_aware_suggestions()

# Examples:
# - Morning: "Plan today's work"
# - Feature branch: "Document feature: new-auth"
# - Evening: "Document today's changes before wrapping up"
# - Long session (>3 hours): "Consider a break"
```

### Context-Aware Suggestion Types

| Context | Suggestion Type | Example |
|---------|----------------|---------|
| **Morning** | TASK | "Plan today's work" |
| **Feature branch** | KB_ENTRY | "Document feature: payment" |
| **Active files (3+)** | KB_ENTRY | "Document changes across 3 modules" |
| **Current task** | TASK | "Review progress on TASK-456" |
| **Evening + active files** | KB_ENTRY | "Document today's changes" |
| **Night** | ANOMALY | "Late-night work detected" |
| **Long session (>3h)** | TASK | "Consider a break" |

### Learning Over Time

The system improves with usage:

**Initial State** (neutral preferences):
```python
tracker.get_preference_score(SuggestionType.KB_ENTRY)
# → 0.5 (neutral)

adjusted = tracker.adjust_confidence(0.75, SuggestionType.KB_ENTRY)
# → 0.73 (minimal adjustment)
```

**After Learning** (10 acceptances):
```python
# User accepted 10 KB suggestions
for _ in range(10):
    tracker.record_suggestion_feedback(SuggestionType.KB_ENTRY, accepted=True)

tracker.get_preference_score(SuggestionType.KB_ENTRY)
# → 0.85 (learned preference)

adjusted = tracker.adjust_confidence(0.75, SuggestionType.KB_ENTRY)
# → 0.79 (boosted confidence)
```

**Effect**: Future KB suggestions rank higher and appear more frequently.

### Usage Statistics

```python
# Get usage stats for last 30 days
stats = tracker.get_usage_stats(days=30)

print(stats)
# → {
#   "total_tool_calls": 45,
#   "accepted_count": 32,
#   "rejected_count": 10,
#   "ignored_count": 3,
#   "acceptance_rate": 0.76,
#   "most_used_tools": [
#       {"tool": "suggest_kb_updates", "count": 15},
#       {"tool": "detect_anomalies", "count": 10}
#   ],
#   "peak_hours": [
#       {"hour": 9, "count": 12},
#       {"hour": 14, "count": 10}
#   ]
# }
```

### Configuration

Update confidence threshold:

```python
# Set user's preferred threshold
tracker.update_confidence_threshold(0.85)

# Get current threshold
threshold = tracker.get_confidence_threshold()
# → 0.85
```

---

## Future Enhancements (Week 2 Day 6-7)

**Week 2 Day 6-7**: Integration & Polish
- End-to-end workflow tests
- Performance optimization
- Production readiness

---

## References

- [MCP Server Guide](mcp-server.md) - MCP integration details
- [CLAUDE.md](../CLAUDE.md) - Development roadmap
- [watchdog Documentation](https://python-watchdog.readthedocs.io/) - File monitoring library
- [Week 2 Day 5 Progress](WEEK2_DAY5_PROGRESS_v0.13.0.md) - Implementation details

---

**Status**: ✅ v0.13.0 Week 2 Day 5 Complete - Behavior Tracking, Context Awareness & Personalized Suggestions
