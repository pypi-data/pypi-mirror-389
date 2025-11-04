# Week 2 Implementation Plan - v0.13.0 Proactive Intelligence

**Sprint**: October 26 - November 1, 2025
**Status**: 🚀 Ready to Start
**Phase**: Proactive Suggestions & Context Awareness

---

## 📋 Overview

Building on Week 1's file monitoring foundation, Week 2 focuses on **intelligent suggestions** and **context-aware recommendations**. The system will analyze patterns, track user behavior, and proactively suggest actions through MCP tools.

### Week 1 Recap (✅ Complete)
- File monitoring with watchdog (11 tests)
- Event processing with pattern detection (15 tests)
- MCP tools: `monitor_start/stop/status/events` (4 tools)
- Phase 1 tests: Performance, Security, Error Handling (37 tests)
- **Total**: 93 tests, 85% quality score (B+)

### Week 2 Goals
- **Proactive suggestion engine** with pattern-based recommendations
- **4 new MCP tools** for proactive features
- **User behavior tracking** with usage analytics
- **Enhanced context awareness** (git branch, active files, time-based)
- **Comprehensive tests** (target: 40+ new tests)

---

## 🎯 Core Features

### 1. Proactive Suggestion Engine (Days 1-3)

**File**: `clauxton/proactive/suggestion_engine.py`

**Capabilities**:
- Analyze event patterns and suggest KB entries
- Recommend tasks based on file change patterns
- Detect code smells and suggest refactoring
- Identify documentation gaps
- Confidence scoring for suggestions

**Key Classes**:

```python
class SuggestionType(str, Enum):
    KB_ENTRY = "kb_entry"           # Suggest KB documentation
    TASK = "task"                    # Suggest new task
    REFACTOR = "refactor"            # Suggest refactoring
    DOCUMENTATION = "documentation"  # Suggest docs update
    CONFLICT = "conflict"            # Warn about conflicts

class Suggestion(BaseModel):
    type: SuggestionType
    title: str
    description: str
    confidence: float  # 0.0-1.0
    reasoning: str
    affected_files: List[str]
    priority: Priority
    created_at: datetime
    metadata: Dict[str, Any] = {}

class SuggestionEngine:
    def __init__(self, project_root: Path, config: ProactiveConfig):
        """Initialize suggestion engine."""

    def analyze_pattern(self, pattern: EventPattern) -> List[Suggestion]:
        """Generate suggestions from detected pattern."""

    def suggest_kb_entry(self, events: List[FileEvent]) -> Optional[Suggestion]:
        """Suggest KB entry based on recent changes."""

    def suggest_task(self, events: List[FileEvent]) -> Optional[Suggestion]:
        """Suggest task based on activity patterns."""

    def detect_anomaly(self, events: List[FileEvent]) -> Optional[Suggestion]:
        """Detect unusual patterns that need attention."""

    def rank_suggestions(self, suggestions: List[Suggestion]) -> List[Suggestion]:
        """Rank suggestions by confidence and priority."""
```

**Suggestion Logic**:

1. **KB Entry Suggestions**:
   - Multiple files in same module changed → "Document this module"
   - New design pattern introduced → "Add architecture decision"
   - Configuration changes → "Update configuration docs"

2. **Task Suggestions**:
   - TODO comments added → "Create task from TODO"
   - Test failures detected → "Fix failing tests"
   - Incomplete feature (files modified but not tests) → "Add tests"

3. **Refactoring Suggestions**:
   - Large file changes (>300 lines) → "Consider splitting"
   - High cyclomatic complexity → "Refactor complex function"
   - Code duplication detected → "Extract common code"

4. **Anomaly Detection**:
   - Unusual file access patterns → "Security review needed"
   - Rapid repeated changes → "Potential merge conflict"
   - Orphaned files → "Remove unused files"

**Confidence Scoring**:
```python
def calculate_confidence(self, evidence: Dict[str, Any]) -> float:
    """
    Score based on:
    - Pattern frequency (30%)
    - File relevance (25%)
    - Historical accuracy (25%)
    - User context (20%)
    """
    score = 0.0
    score += evidence["pattern_frequency"] * 0.3
    score += evidence["file_relevance"] * 0.25
    score += evidence["historical_accuracy"] * 0.25
    score += evidence["user_context"] * 0.2
    return min(1.0, max(0.0, score))
```

---

### 2. Proactive MCP Tools (Days 3-4)

**File**: `clauxton/mcp/server.py` (extend existing)

#### 2.1 `watch_project_changes` Tool

```python
@server.call_tool()
async def watch_project_changes(enabled: bool) -> dict:
    """
    Enable/disable proactive change monitoring.

    Args:
        enabled: True to start monitoring, False to stop

    Returns:
        {
            "status": "monitoring" | "stopped",
            "watching_paths": [...],
            "suggestion_count": 0
        }
    """
```

**Use Case**:
```
User in Claude Code:
> "Watch my project and suggest improvements"

Claude Code calls:
watch_project_changes(enabled=True)
→ Monitoring starts in background
→ Suggestions appear as changes are detected
```

#### 2.2 `get_recent_changes` Tool

```python
@server.call_tool()
async def get_recent_changes(minutes: int = 30) -> dict:
    """
    Get summary of recent file changes and suggestions.

    Args:
        minutes: Time window to analyze (default: 30)

    Returns:
        {
            "time_window": "30 minutes",
            "changes": [
                {
                    "file": "src/auth.py",
                    "type": "modified",
                    "lines_changed": 45,
                    "timestamp": "2025-10-26T10:30:00"
                }
            ],
            "suggestions": [
                {
                    "type": "kb_entry",
                    "title": "Document authentication flow",
                    "confidence": 0.85
                }
            ],
            "patterns_detected": ["rapid_editing", "new_module"]
        }
    """
```

**Use Case**:
```
User in Claude Code:
> "What have I been working on?"

Claude Code calls:
get_recent_changes(minutes=60)
→ Shows recent activity + suggestions
```

#### 2.3 `suggest_kb_updates` Tool

```python
@server.call_tool()
async def suggest_kb_updates(threshold: float = 0.7) -> dict:
    """
    Get KB entry suggestions based on recent activity.

    Args:
        threshold: Minimum confidence score (0.0-1.0)

    Returns:
        {
            "suggestions": [
                {
                    "title": "API Authentication Pattern",
                    "category": "architecture",
                    "confidence": 0.85,
                    "reasoning": "3 auth-related files modified",
                    "affected_files": ["src/auth.py", "src/api.py"],
                    "suggested_content": "..."
                }
            ],
            "count": 3,
            "threshold_used": 0.7
        }
    """
```

**Use Case**:
```
User in Claude Code:
> "Do I need to update documentation?"

Claude Code calls:
suggest_kb_updates(threshold=0.8)
→ Shows high-confidence KB suggestions
```

#### 2.4 `detect_anomalies` Tool

```python
@server.call_tool()
async def detect_anomalies() -> dict:
    """
    Detect unusual patterns in recent activity.

    Returns:
        {
            "anomalies": [
                {
                    "type": "rapid_changes",
                    "description": "auth.py modified 15 times in 10 minutes",
                    "severity": "medium",
                    "recommendation": "Consider debugging or reverting"
                }
            ],
            "security_concerns": [...],
            "performance_issues": [...]
        }
    """
```

**Use Case**:
```
Claude Code (proactively):
*detects unusual activity*
detect_anomalies()
→ "I noticed unusual rapid changes. Debugging?"
```

---

### 3. User Behavior Tracking (Day 4-5)

**File**: `clauxton/proactive/behavior_tracker.py`

**Capabilities**:
- Track MCP tool usage patterns
- Learn user preferences
- Personalize suggestion ranking
- Improve confidence scoring over time

**Key Classes**:

```python
class ToolUsage(BaseModel):
    tool_name: str
    timestamp: datetime
    parameters: Dict[str, Any]
    result: str  # "accepted" | "rejected" | "ignored"
    context: Dict[str, Any]

class UserBehavior(BaseModel):
    tool_usage_history: List[ToolUsage] = []
    preferred_suggestion_types: Dict[SuggestionType, float] = {}
    active_hours: Dict[int, int] = {}  # hour -> count
    preferred_file_patterns: List[str] = []
    confidence_threshold: float = 0.7
    last_updated: datetime

class BehaviorTracker:
    def __init__(self, project_root: Path):
        """Initialize behavior tracker."""

    def record_tool_usage(self, tool_name: str, result: str, context: Dict):
        """Record MCP tool usage."""

    def record_suggestion_feedback(self, suggestion_id: str, accepted: bool):
        """Record user feedback on suggestion."""

    def get_preference_score(self, suggestion_type: SuggestionType) -> float:
        """Get user's preference score for suggestion type."""

    def is_active_time(self) -> bool:
        """Check if current time matches user's active hours."""

    def adjust_confidence(self, base_confidence: float, suggestion_type: SuggestionType) -> float:
        """Adjust confidence based on user behavior."""
```

**Storage**:
```yaml
# .clauxton/behavior.yml
tool_usage_history:
  - tool_name: "suggest_kb_updates"
    timestamp: "2025-10-26T10:00:00"
    result: "accepted"
    context:
      suggestion_count: 3

preferred_suggestion_types:
  kb_entry: 0.85      # High acceptance rate
  task: 0.70          # Medium acceptance
  refactor: 0.40      # Low acceptance

active_hours:
  9: 15   # 9am: 15 operations
  10: 22  # 10am: 22 operations
  14: 18  # 2pm: 18 operations

confidence_threshold: 0.75
```

---

### 4. Enhanced Context Awareness (Day 5-6)

**File**: `clauxton/proactive/context_manager.py`

**Capabilities**:
- Track current git branch
- Detect active files (recently edited)
- Analyze conversation history (if available)
- Provide time-based context

**Key Classes**:

```python
class ProjectContext(BaseModel):
    current_branch: Optional[str] = None
    active_files: List[str] = []
    recent_commits: List[Dict[str, str]] = []
    current_task: Optional[str] = None  # From task manager
    time_context: str  # "morning" | "afternoon" | "evening"
    work_session_start: Optional[datetime] = None
    last_activity: Optional[datetime] = None

class ContextManager:
    def __init__(self, project_root: Path):
        """Initialize context manager."""

    def get_current_context(self) -> ProjectContext:
        """Get comprehensive project context."""

    def detect_active_files(self, minutes: int = 30) -> List[str]:
        """Detect recently modified files."""

    def get_branch_context(self) -> Dict[str, Any]:
        """Get git branch information."""

    def get_time_context(self) -> str:
        """Get time-based context (morning/afternoon/evening)."""

    def infer_current_task(self) -> Optional[str]:
        """Infer what user is working on."""
```

**Context Usage**:
```python
# In suggestion engine
context = self.context_manager.get_current_context()

if context.time_context == "morning":
    # Suggest planning tasks
    suggestions.append(Suggestion(
        type=SuggestionType.TASK,
        title="Review today's tasks",
        confidence=0.8
    ))

if context.current_branch and "feature/" in context.current_branch:
    # Suggest KB documentation for feature
    suggestions.append(Suggestion(
        type=SuggestionType.KB_ENTRY,
        title=f"Document feature: {context.current_branch}",
        confidence=0.75
    ))
```

---

## 🗂️ File Structure

```
clauxton/proactive/
├── __init__.py
├── config.py                   # ✅ Week 1
├── file_monitor.py             # ✅ Week 1
├── event_processor.py          # ✅ Week 1
├── suggestion_engine.py        # 🆕 Week 2 (Day 1-3)
├── behavior_tracker.py         # 🆕 Week 2 (Day 4-5)
└── context_manager.py          # 🆕 Week 2 (Day 5-6)

clauxton/mcp/
└── server.py                   # Extend with 4 new tools

tests/proactive/
├── test_file_monitor.py        # ✅ Week 1
├── test_event_processor.py     # ✅ Week 1
├── test_performance.py         # ✅ Phase 1
├── test_security.py            # ✅ Phase 1
├── test_error_handling.py      # ✅ Phase 1
├── test_suggestion_engine.py   # 🆕 Week 2
├── test_behavior_tracker.py    # 🆕 Week 2
└── test_context_manager.py     # 🆕 Week 2

tests/mcp/
└── test_proactive_tools.py     # 🆕 Week 2 (MCP tool tests)

.clauxton/
├── monitoring.yml              # ✅ Week 1
├── events.yml                  # ✅ Week 1
├── behavior.yml                # 🆕 Week 2
└── suggestions.yml             # 🆕 Week 2
```

---

## 📅 Daily Schedule

### Day 1 (Oct 26): Suggestion Engine Foundation

**Tasks**:
- [x] Create `suggestion_engine.py` with base classes
- [ ] Implement `Suggestion` and `SuggestionType` models
- [ ] Implement `analyze_pattern()` method
- [ ] Add basic KB entry suggestion logic
- [ ] Write 10+ unit tests

**Deliverables**:
- `SuggestionEngine` class functional
- Basic pattern → suggestion conversion
- Tests passing

**Time**: 6-8 hours

---

### Day 2 (Oct 27): Advanced Suggestion Logic

**Tasks**:
- [ ] Implement task suggestion logic
- [ ] Add refactoring suggestions
- [ ] Implement anomaly detection
- [ ] Add confidence scoring algorithm
- [ ] Write 12+ unit tests

**Deliverables**:
- All suggestion types working
- Confidence scoring accurate
- Comprehensive tests

**Time**: 6-8 hours

---

### Day 3 (Oct 28): MCP Tools Part 1

**Tasks**:
- [ ] Implement `watch_project_changes()` MCP tool
- [ ] Implement `get_recent_changes()` MCP tool
- [ ] Add tool parameter validation
- [ ] Write 8+ integration tests

**Deliverables**:
- 2/4 MCP tools complete
- Tools callable from Claude Code
- Tests passing

**Time**: 5-7 hours

---

### Day 4 (Oct 29): MCP Tools Part 2 + Behavior Tracking

**Tasks**:
- [ ] Implement `suggest_kb_updates()` MCP tool
- [ ] Implement `detect_anomalies()` MCP tool
- [ ] Create `behavior_tracker.py`
- [ ] Implement tool usage recording
- [ ] Write 10+ tests

**Deliverables**:
- All 4 MCP tools complete
- Behavior tracking functional
- Tests passing

**Time**: 6-8 hours

---

### Day 5 (Oct 30): Context Awareness + Learning

**Tasks**:
- [ ] Create `context_manager.py`
- [ ] Implement git branch detection
- [ ] Implement active file detection
- [ ] Add time-based context
- [ ] Implement preference learning
- [ ] Write 10+ tests

**Deliverables**:
- Context manager functional
- Learning from user behavior
- Tests passing

**Time**: 6-8 hours

---

### Day 6 (Oct 31): Integration + Polish

**Tasks**:
- [ ] Integrate all components
- [ ] End-to-end testing (5+ scenarios)
- [ ] Performance optimization
- [ ] Documentation updates
- [ ] Bug fixes

**Deliverables**:
- Fully integrated system
- All tests passing (target: 130+ total)
- Documentation complete

**Time**: 6-8 hours

---

### Day 7 (Nov 1): Testing + Documentation

**Tasks**:
- [ ] Write Phase 2 tests (error handling, edge cases)
- [ ] Update CLAUDE.md with Week 2 features
- [ ] Create user guide for proactive features
- [ ] Prepare Week 3 plan
- [ ] Code review and cleanup

**Deliverables**:
- Quality score: A- (90+)
- Total tests: 135+
- Documentation complete
- Ready for Week 3

**Time**: 5-7 hours

---

## 🎯 Success Metrics

### Code Quality
- **Total tests**: 135+ (currently 93)
- **New tests**: 40+ for Week 2
- **Test coverage**: >85% for proactive module
- **Quality score**: A- (90+) from B+ (85)

### Functional Metrics
- **Suggestion accuracy**: >75%
- **Confidence scoring**: MAE <0.15
- **MCP tool response time**: <200ms
- **Context detection**: >90% accuracy

### User Experience
- **False positive rate**: <15%
- **Accepted suggestions**: >60%
- **Tool usage**: 4 MCP tools used regularly
- **Learning improvement**: +20% accuracy over time

---

## 🧪 Testing Strategy

### Unit Tests (25+)

**suggestion_engine.py** (12 tests):
- `test_analyze_pattern_kb_entry()`
- `test_analyze_pattern_task()`
- `test_analyze_pattern_refactor()`
- `test_detect_anomaly_rapid_changes()`
- `test_confidence_scoring()`
- `test_suggestion_ranking()`
- `test_empty_pattern_handling()`
- `test_multiple_suggestions_same_pattern()`
- `test_confidence_threshold_filtering()`
- `test_suggestion_deduplication()`
- `test_metadata_preservation()`
- `test_priority_calculation()`

**behavior_tracker.py** (8 tests):
- `test_record_tool_usage()`
- `test_record_suggestion_feedback()`
- `test_preference_score_calculation()`
- `test_active_hours_detection()`
- `test_confidence_adjustment()`
- `test_behavior_persistence()`
- `test_empty_history_handling()`
- `test_preference_updates_over_time()`

**context_manager.py** (8 tests):
- `test_get_current_context()`
- `test_detect_active_files()`
- `test_git_branch_detection()`
- `test_time_context_morning()`
- `test_time_context_afternoon()`
- `test_infer_current_task()`
- `test_no_git_repo_fallback()`
- `test_context_caching()`

### Integration Tests (10+)

**test_proactive_tools.py** (10 tests):
- `test_watch_project_changes_enable()`
- `test_watch_project_changes_disable()`
- `test_get_recent_changes_30min()`
- `test_get_recent_changes_empty()`
- `test_suggest_kb_updates_high_threshold()`
- `test_suggest_kb_updates_low_threshold()`
- `test_detect_anomalies_none()`
- `test_detect_anomalies_rapid_changes()`
- `test_tool_error_handling()`
- `test_tool_parameter_validation()`

### End-to-End Tests (5+)

**test_proactive_e2e.py** (5 tests):
- `test_full_workflow_file_change_to_suggestion()`
- `test_learning_improves_suggestions()`
- `test_context_affects_suggestions()`
- `test_anomaly_detection_triggers_alert()`
- `test_mcp_tool_integration_with_claude_code()`

---

## 📚 Documentation Updates

### Files to Update:
1. **CLAUDE.md** - Add Week 2 features to roadmap
2. **docs/PROACTIVE_MONITORING_GUIDE.md** - Add suggestion engine section
3. **docs/mcp-server.md** - Document 4 new MCP tools
4. **README.md** - Update feature list

### New Documentation:
1. **docs/PROACTIVE_SUGGESTIONS_GUIDE.md**
   - How suggestions work
   - Customizing confidence thresholds
   - Learning from behavior
   - Best practices

2. **docs/WEEK2_RESULTS_v0.13.0.md**
   - Implementation summary
   - Test results
   - Performance benchmarks
   - Lessons learned

---

## 🚧 Risks & Mitigations

### Risk 1: False Positive Suggestions
**Impact**: Medium - Users get annoyed by bad suggestions
**Mitigation**:
- Conservative confidence thresholds (≥0.7)
- User feedback learning
- Whitelist/blacklist patterns

### Risk 2: Performance Impact
**Impact**: Medium - Real-time analysis slows down
**Mitigation**:
- Async processing
- Batch suggestions every 5 minutes
- Cache analyzed patterns

### Risk 3: Privacy Concerns
**Impact**: Low - User behavior tracking
**Mitigation**:
- All data stays local (.clauxton/)
- Clear documentation
- Opt-out capability

### Risk 4: Context Detection Errors
**Impact**: Low-Medium - Wrong context → bad suggestions
**Mitigation**:
- Multiple context sources
- Fallback to generic suggestions
- User can override context

---

## 🔧 Technical Decisions

### 1. Confidence Scoring Algorithm
**Decision**: Weighted evidence scoring (4 factors)
**Rationale**:
- Pattern frequency: Most reliable indicator
- File relevance: Context matters
- Historical accuracy: Learn from past
- User context: Personalize

### 2. Suggestion Storage
**Decision**: YAML files (.clauxton/suggestions.yml)
**Rationale**:
- Consistent with existing architecture
- Human-readable
- Git-friendly
- Easy to inspect/debug

### 3. Learning Approach
**Decision**: Simple frequency-based learning
**Rationale**:
- No ML dependencies needed
- Fast and interpretable
- Good enough for MVP
- Can upgrade to ML later

### 4. MCP Tool Design
**Decision**: 4 focused tools (not 1 monolithic tool)
**Rationale**:
- Single Responsibility Principle
- Easier to test
- Better error handling
- Claude Code can compose as needed

---

## 🎯 Definition of Done

### Feature Complete
- [ ] All 4 MCP tools implemented and tested
- [ ] Suggestion engine generates all types
- [ ] Behavior tracking records and learns
- [ ] Context manager provides rich context
- [ ] All components integrated

### Quality Standards
- [ ] 135+ tests passing (40+ new tests)
- [ ] Test coverage >85% for new code
- [ ] Quality score A- (90+)
- [ ] No critical bugs
- [ ] Performance benchmarks met

### Documentation
- [ ] All MCP tools documented
- [ ] User guide written
- [ ] CLAUDE.md updated
- [ ] Week 2 results documented
- [ ] Week 3 plan drafted

### Code Review
- [ ] Type hints on all functions
- [ ] Docstrings (Google style)
- [ ] Error handling comprehensive
- [ ] Code follows project style
- [ ] No security vulnerabilities

---

## 📈 Progress Tracking

| Day | Tasks | Tests | Status |
|-----|-------|-------|--------|
| Day 1 | Suggestion engine foundation | 10+ | 🔵 Planned |
| Day 2 | Advanced suggestion logic | 12+ | 🔵 Planned |
| Day 3 | MCP tools part 1 | 8+ | 🔵 Planned |
| Day 4 | MCP tools part 2 + behavior | 10+ | 🔵 Planned |
| Day 5 | Context awareness + learning | 10+ | 🔵 Planned |
| Day 6 | Integration + polish | 5+ | 🔵 Planned |
| Day 7 | Testing + documentation | 0 | 🔵 Planned |
| **Total** | **Week 2 Complete** | **40+** | **Target: Nov 1** |

**Legend**:
- 🔵 Planned
- 🟡 In Progress
- 🟢 Complete
- 🔴 Blocked

---

## 🚀 Next Steps (After Week 2)

### Week 3: MCP Tool Integration & Polish
- Advanced context awareness
- Multi-project intelligence
- Performance optimization
- Production readiness

### Phase 2 Tests
- More edge cases
- Performance benchmarks
- Security audits
- User acceptance testing

---

## 📞 Questions & Clarifications

**Q: How do we handle suggestion spam?**
A: Batch suggestions every 5 minutes, max 3 per batch, confidence ≥0.7

**Q: Should suggestions persist across sessions?**
A: Yes, store in .clauxton/suggestions.yml with timestamps

**Q: How to handle user rejecting suggestions?**
A: Record in behavior tracker, adjust confidence for that type

**Q: What if git is not available?**
A: Graceful fallback, context_manager returns empty branch info

---

## 🎉 Expected Outcomes

After Week 2 completion:

1. **Users get proactive help** - Claude Code suggests relevant actions
2. **System learns preferences** - Gets better with usage
3. **Context-aware suggestions** - Smart timing and relevance
4. **26 total MCP tools** - 22 (v0.11.2) + 4 (Week 2) = 26
5. **135+ tests** - Comprehensive coverage
6. **Quality score A-** - Production-ready code

**User Experience**:
```
Morning (9am):
Claude Code: "Good morning! Based on your recent work on auth.py,
              I suggest documenting the authentication flow in KB.
              Would you like me to draft an entry?"

After 15 file changes:
Claude Code: "I noticed rapid changes to database models.
              Consider creating a task for database migration.
              Should I add this to your task list?"

Evening (5pm):
Claude Code: "You've made great progress today! 3 files in the
              API module were modified. I recommend updating the
              API documentation before wrapping up."
```

---

**Ready to implement Week 2! 🚀**

Let's build intelligent, proactive assistance that makes Clauxton truly helpful.
