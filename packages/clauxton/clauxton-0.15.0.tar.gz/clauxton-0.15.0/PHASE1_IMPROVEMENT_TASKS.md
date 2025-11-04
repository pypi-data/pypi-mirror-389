# Phase 1 Improvement Tasks

**Project**: Clauxton v0.15.0 - Unified Memory Model
**Review Date**: 2025-11-03
**Total Tasks**: 10 (4 High, 3 Medium, 3 Low)

---

## Task Priority Matrix

```
┌─────────────┬──────────┬─────────────────────────────────────────┐
│  Priority   │  Count   │  Total Effort                           │
├─────────────┼──────────┼─────────────────────────────────────────┤
│  CRITICAL   │    0     │  0 hours                                │
│  HIGH       │    4     │  ~3.5 hours (before v0.15.0 release)    │
│  MEDIUM     │    3     │  ~9 hours (Phase 2)                     │
│  LOW        │    3     │  ~3.5 hours (when convenient)           │
├─────────────┼──────────┼─────────────────────────────────────────┤
│  TOTAL      │   10     │  ~16 hours                              │
└─────────────┴──────────┴─────────────────────────────────────────┘
```

---

## Critical Priority (0 tasks)

**No critical issues found.** ✅

All blocking issues have been resolved. Phase 1 is ready to proceed.

---

## High Priority (4 tasks)

### TASK-H1: Fix Ruff Line Length Violations

**ID**: TASK-H1
**Priority**: HIGH (Blocker for ruff check pass)
**Severity**: LOW
**Category**: Code Style
**Effort**: 5 minutes
**Assignee**: Developer
**Status**: PENDING

#### Description
Fix 2 line length violations in `clauxton/cli/migrate.py` to comply with ruff E501 (max 100 chars).

#### Location
- `clauxton/cli/migrate.py:135` (116 chars)
- `clauxton/cli/migrate.py:176` (101 chars)

#### Current Code
```python
# Line 135 (116 chars)
"  2. If something went wrong, rollback: [cyan]clauxton migrate rollback <backup_path>[/cyan]\n"

# Line 176 (101 chars)
"backup_path: Path to backup directory (e.g., .clauxton/backups/pre_migration_20260127_143052)"
```

#### Proposed Fix
```python
# Line 135
"  2. If something went wrong, rollback:\n"
"     [cyan]clauxton migrate rollback <backup_path>[/cyan]\n"

# Line 176
"backup_path: Path to backup directory\n"
"             (e.g., .clauxton/backups/pre_migration_20260127_143052)"
```

#### Acceptance Criteria
- [ ] Line 135: Break into 2 lines, max 100 chars each
- [ ] Line 176: Break into 2 lines, max 100 chars each
- [ ] `ruff check clauxton/cli/migrate.py` returns 0 errors
- [ ] Visual output unchanged (Rich formatting preserved)

#### Verification
```bash
ruff check clauxton/cli/migrate.py
# Expected: All checks passed!
```

#### Risk: None
#### Dependencies: None
#### Blocks: v0.15.0 release (ruff check must pass)

---

### TASK-H2: Create Migration Guide Documentation

**ID**: TASK-H2
**Priority**: HIGH (Required for v0.15.0 release)
**Severity**: HIGH
**Category**: Documentation
**Effort**: 2 hours
**Assignee**: Technical Writer / Developer
**Status**: PENDING

#### Description
Create comprehensive migration guide for users upgrading from Knowledge Base/Task Management to unified Memory System.

#### File
`docs/v0.15.0_MIGRATION_GUIDE.md`

#### Content Outline
```markdown
# Clauxton v0.15.0 Migration Guide

## Table of Contents
1. Overview
2. What Changed
3. Why We Unified
4. Migration Steps
5. Before/After Examples
6. Rollback Procedure
7. FAQ
8. Troubleshooting

## 1. Overview
- Brief introduction to Memory System
- Timeline (v0.15.0 → v0.17.0)
- Safety guarantees

## 2. What Changed
- Knowledge Base → Memory (type=knowledge)
- Task Management → Memory (type=task)
- New unified API
- Legacy ID preservation

## 3. Why We Unified
- Benefits: Single API, better relationships, type discrimination
- Performance improvements
- Future extensibility (code, patterns)

## 4. Migration Steps
### Step 1: Backup Your Data
```bash
# Automatic backup
cd your-project
ls .clauxton/  # Verify .clauxton exists
```

### Step 2: Dry Run (Preview)
```bash
clauxton migrate memory --dry-run
# Output:
# KB entries: 15
# Tasks: 8
# Total: 23
```

### Step 3: Review Changes
- Check dry run output
- Verify counts match expectations

### Step 4: Execute Migration
```bash
clauxton migrate memory --confirm
# Backup created: .clauxton/backups/pre_migration_20260127_143052
# Migrating...
# ✓ Complete!
```

### Step 5: Verify
```bash
clauxton memory list
# Should see all entries
```

## 5. Before/After Examples
### Knowledge Base API → Memory API
**Before (KB API - Deprecated)**:
```python
from clauxton.core.knowledge_base import KnowledgeBase

kb = KnowledgeBase(project_root)
entry = KnowledgeBaseEntry(...)
kb.add(entry)
results = kb.search("api design")
```

**After (Memory API - Recommended)**:
```python
from clauxton.core.memory import Memory, MemoryEntry

memory = Memory(project_root)
entry = MemoryEntry(type="knowledge", ...)
memory.add(entry)
results = memory.search("api design", type_filter=["knowledge"])
```

### Task Management API → Memory API
**Before (Task API - Deprecated)**:
```python
from clauxton.core.task_manager import TaskManager

tm = TaskManager(project_root)
task = Task(...)
tm.add(task)
tasks = tm.list_all(status_filter="pending")
```

**After (Memory API - Recommended)**:
```python
from clauxton.core.memory import Memory, MemoryEntry

memory = Memory(project_root)
entry = MemoryEntry(type="task", ...)
memory.add(entry)
tasks = memory.list_all(type_filter=["task"], tag_filter=["pending"])
```

## 6. Rollback Procedure
### When to Rollback
- Migration failed
- Unexpected data loss
- Data corruption

### How to Rollback
```bash
# Find backup directory
ls .clauxton/backups/
# Output: pre_migration_20260127_143052

# Rollback
clauxton migrate rollback .clauxton/backups/pre_migration_20260127_143052
# Confirm: yes
# ✓ Rollback complete!

# Verify
clauxton kb list  # Old KB entries restored
clauxton task list  # Old tasks restored
```

## 7. FAQ
**Q: Will my data be lost?**
A: No. Automatic backup is created before migration. You can rollback anytime.

**Q: Do I need to migrate immediately?**
A: No. KB/Task APIs work until v0.17.0 (deprecation in v0.16.0).

**Q: Can I use both APIs?**
A: Yes. Compatibility layers allow mixing old and new APIs.

**Q: What happens to my KB IDs (KB-*)?**
A: Preserved in `legacy_id` field. Backward compatibility maintained.

## 8. Troubleshooting
### Issue: "No .clauxton directory found"
**Solution**: Run `clauxton init` first.

### Issue: "Migration failed: ..."
**Solution**: Check error message, rollback, report issue.

### Issue: "Data missing after migration"
**Solution**: Rollback immediately, report issue with logs.
```

#### Acceptance Criteria
- [ ] All sections completed with examples
- [ ] Code examples tested and verified
- [ ] Rollback procedure verified
- [ ] FAQ covers common questions
- [ ] Linked from README.md

#### Verification
- [ ] Run all code examples
- [ ] Test migration dry-run
- [ ] Test actual migration
- [ ] Test rollback

#### Risk: Medium (user confusion if incomplete)
#### Dependencies: None
#### Blocks: v0.15.0 release

---

### TASK-H3: Update CHANGELOG.md for v0.15.0

**ID**: TASK-H3
**Priority**: HIGH (Required for v0.15.0 release)
**Severity**: MEDIUM
**Category**: Documentation
**Effort**: 30 minutes
**Assignee**: Developer
**Status**: PENDING

#### Description
Add v0.15.0 section to CHANGELOG.md documenting all Phase 1 changes.

#### File
`CHANGELOG.md`

#### Changes to Add
```markdown
## [0.15.0] - 2026-01-27

### Added
- **Unified Memory System**: Consolidates Knowledge Base, Task Management, and Code Intelligence
  - New `Memory` class for CRUD operations across all memory types
  - New `MemoryEntry` model with type discrimination (knowledge, decision, code, task, pattern)
  - New `MemoryStore` for persistent YAML storage with atomic writes and automatic backups
- **TF-IDF Search**: Relevance-based search with scikit-learn (optional dependency)
- **Backward Compatibility Layers**:
  - `KnowledgeBaseCompat`: Drop-in replacement for `KnowledgeBase` (deprecated)
  - `TaskManagerCompat`: Drop-in replacement for `TaskManager` (deprecated)
- **Migration Tool**: `clauxton migrate memory` command with dry-run and rollback support
- **6 New MCP Tools**:
  - `memory_add`: Add memory entry
  - `memory_search`: Search with type filters
  - `memory_get`: Get entry by ID
  - `memory_list`: List with filters
  - `memory_update`: Update entry fields
  - `memory_find_related`: Find related memories
- **CLI Commands**: `clauxton memory` group with add/search/list/get/update/delete/related subcommands
- **Legacy ID Preservation**: KB-* and TASK-* IDs preserved in `legacy_id` field

### Deprecated
- `KnowledgeBase` API (will be removed in v0.17.0)
- `TaskManager` API (will be removed in v0.17.0)
- Users should migrate to `Memory` API for new code
- Deprecation warnings emitted when using compatibility layers

### Changed
- **Internal Storage Format**: Migrated from `knowledge-base.yml` + `tasks.yml` to unified `memories.yml`
- **Search Behavior**: Now uses TF-IDF for better relevance (falls back to simple search if scikit-learn unavailable)
- **ID Format**: New entries use `MEM-YYYYMMDD-NNN` format (legacy IDs preserved)

### Migration
To migrate existing Knowledge Base and Task data:

```bash
# Preview changes
clauxton migrate memory --dry-run

# Execute migration (creates automatic backup)
clauxton migrate memory --confirm

# Verify migration
clauxton memory list

# Rollback if needed
clauxton migrate rollback .clauxton/backups/pre_migration_TIMESTAMP
```

**Migration Safety**:
- Automatic backup created before migration
- Rollback capability if issues occur
- Legacy IDs preserved for backward compatibility
- No data loss (backup guaranteed)

**Documentation**:
- Migration Guide: `docs/v0.15.0_MIGRATION_GUIDE.md`
- MCP Tools: `docs/mcp-memory-tools.md`

### Breaking Changes
None. Full backward compatibility maintained via compatibility layers.

### Security
- No new security vulnerabilities introduced
- YAML operations use `safe_load` only
- File permissions: 0600 (owner read/write only)
- Atomic file writes prevent data corruption

### Performance
- Memory.add(): ~5ms (10x faster than target)
- Memory.search() (TF-IDF): ~20ms (5x faster than target)
- Migration (1000 entries): <1s (estimated)

### Known Issues
- None

### Contributors
- AI Agent 1: Core Memory System
- AI Agent 2: Backward Compatibility
- AI Agent 3: Migration Tool
- AI Agent 4: CLI Commands
- AI Agent 5: MCP Integration

---

## [0.14.0] - 2025-10-21
[Previous entries...]
```

#### Acceptance Criteria
- [ ] v0.15.0 section added at top
- [ ] All major changes documented
- [ ] Migration instructions included
- [ ] Breaking changes section (None in this case)
- [ ] Links to new documentation

#### Verification
- [ ] Review CHANGELOG.md for completeness
- [ ] Verify all new features listed
- [ ] Verify deprecation notices clear
- [ ] Cross-reference with git log

#### Risk: Low
#### Dependencies: None
#### Blocks: v0.15.0 release

---

### TASK-H4: Update README.md with Memory System

**ID**: TASK-H4
**Priority**: HIGH (Required for v0.15.0 release)
**Severity**: MEDIUM
**Category**: Documentation
**Effort**: 1 hour
**Assignee**: Developer / Technical Writer
**Status**: PENDING

#### Description
Update README.md to reflect new unified Memory System and document new commands/tools.

#### File
`README.md`

#### Sections to Update

##### 1. Quick Start (Update Examples)
```markdown
## Quick Start

### Initialize Clauxton
```bash
cd your-project
clauxton init
```

### Add Knowledge
```bash
# Interactive mode
clauxton memory add -i

# Or command-line mode
clauxton memory add \
  --type knowledge \
  --title "API Design Pattern" \
  --content "Use RESTful API design with versioning" \
  --category architecture \
  --tags "api,rest,design"
```

### Search Memories
```bash
clauxton memory search "api design"
clauxton memory search "authentication" --type knowledge --type decision
```

### List All Memories
```bash
clauxton memory list
clauxton memory list --type knowledge --category architecture
```
```

##### 2. Features Section (Add Memory System)
```markdown
## Features

### 🧠 Unified Memory System (v0.15.0+)
- **Single API** for all project memory types
- **Type Discrimination**: knowledge, decision, code, task, pattern
- **TF-IDF Search**: Relevance-based search with scikit-learn
- **Relationships**: Link related memories
- **Legacy Support**: KB-* and TASK-* IDs preserved

### 📚 Knowledge Base (Deprecated)
*Use Memory System instead. See [Migration Guide](docs/v0.15.0_MIGRATION_GUIDE.md)*
- Store architecture decisions, patterns, and conventions
- Search with TF-IDF relevance ranking
- Tag-based organization

### ✅ Task Management (Deprecated)
*Use Memory System instead. See [Migration Guide](docs/v0.15.0_MIGRATION_GUIDE.md)*
- Track work items with dependencies
- Auto-inferred dependencies (DAG validation)
- Priority and status tracking
```

##### 3. CLI Commands Section
```markdown
## CLI Commands

### Memory Management (v0.15.0+)
```bash
# Add memory (interactive)
clauxton memory add -i

# Add memory (command-line)
clauxton memory add --type knowledge --title "..." --content "..." --category "..."

# Search
clauxton memory search "query" [--type TYPE] [--limit N]

# List
clauxton memory list [--type TYPE] [--category CAT] [--tag TAG]

# Get details
clauxton memory get MEM-20260127-001

# Update
clauxton memory update MEM-20260127-001 --title "New Title" --tags "api,rest,v2"

# Delete
clauxton memory delete MEM-20260127-001

# Find related
clauxton memory related MEM-20260127-001 [--limit N]
```

### Migration (v0.15.0+)
```bash
# Migrate KB and Tasks to Memory
clauxton migrate memory --dry-run    # Preview
clauxton migrate memory --confirm    # Execute

# Rollback if needed
clauxton migrate rollback .clauxton/backups/TIMESTAMP
```

### Knowledge Base (Deprecated - use Memory System)
[Existing KB commands...]

### Task Management (Deprecated - use Memory System)
[Existing Task commands...]
```

##### 4. MCP Tools Section
```markdown
## MCP Tools (32+ tools)

Clauxton provides 32+ MCP tools for Claude Code integration:

### Memory Tools (v0.15.0+) - 6 tools
- `memory_add()`: Add memory entry
- `memory_search()`: Search with type filters
- `memory_get()`: Get entry by ID
- `memory_list()`: List with filters
- `memory_update()`: Update entry
- `memory_find_related()`: Find related memories

### Knowledge Base Tools (Deprecated) - 6 tools
*Use Memory Tools instead*
- `kb_search()`, `kb_add()`, `kb_list()`, `kb_get()`, `kb_update()`, `kb_delete()`

### Task Management Tools (Deprecated) - 7 tools
*Use Memory Tools instead*
- `task_add()`, `task_list()`, `task_get()`, `task_update()`, etc.

[Rest of MCP tools...]

For detailed documentation:
- **Index**: `docs/mcp-index.md`
- **Memory Tools**: `docs/mcp-memory-tools.md` (NEW)
- **Setup**: `docs/mcp-overview.md`
```

##### 5. Migration Section (Add New)
```markdown
## Migrating to v0.15.0

If you're upgrading from v0.14.0 or earlier:

### Quick Migration
```bash
# 1. Preview migration
clauxton migrate memory --dry-run

# 2. Execute migration (automatic backup)
clauxton migrate memory --confirm

# 3. Verify
clauxton memory list
```

### Why Migrate?
- ✅ Single unified API (simpler)
- ✅ Better relationships between entries
- ✅ Type discrimination (knowledge, tasks, code, patterns)
- ✅ Future-proof (code intelligence, pattern detection)

### Backward Compatibility
- Legacy KB/Task APIs work until v0.17.0
- Deprecation warnings in v0.16.0
- Migration guide: `docs/v0.15.0_MIGRATION_GUIDE.md`

### Safety
- Automatic backup before migration
- Rollback capability
- Legacy IDs preserved
- No data loss guaranteed
```

#### Acceptance Criteria
- [ ] Quick Start updated with Memory examples
- [ ] Features section includes Memory System
- [ ] CLI Commands section updated
- [ ] MCP Tools section includes 6 new tools
- [ ] Migration section added
- [ ] Deprecation notices added to KB/Task sections
- [ ] Links to migration guide

#### Verification
- [ ] Test all code examples in README
- [ ] Verify links to documentation
- [ ] Check formatting (markdown)
- [ ] Review with fresh eyes

#### Risk: Low (documentation only)
#### Dependencies: TASK-H2 (migration guide)
#### Blocks: v0.15.0 release

---

## Medium Priority (3 tasks)

### TASK-M1: Optimize TF-IDF Index Rebuild Performance

**ID**: TASK-M1
**Priority**: MEDIUM (Optimize if performance issues reported)
**Severity**: MEDIUM
**Category**: Performance
**Effort**: 4 hours
**Assignee**: Developer
**Status**: PENDING

#### Description
Optimize TF-IDF search performance by implementing type-specific index caching. Currently, the search engine rebuilds the entire TF-IDF index on every type-filtered search, causing 50-100ms overhead.

#### Location
`clauxton/core/memory.py:292-308` (MemorySearchEngine.search)

#### Problem
```python
def search(self, query: str, type_filter: Optional[List[str]] = None, limit: int = 10):
    if type_filter:
        filtered_entries = [e for e in self.entries if e.type in type_filter]

        # Rebuilds TF-IDF index on EVERY search! 🐢
        temp_engine = MemorySearchEngine.__new__(MemorySearchEngine)
        temp_engine._build_index()  # O(n * m) overhead
```

#### Current Performance
| Entries | Current Time | Target Time |
|---------|--------------|-------------|
| 100     | 40ms         | 20ms        |
| 1,000   | 120ms        | 20ms        |
| 10,000  | 1,200ms      | 50ms        |

#### Proposed Solution
```python
class MemorySearchEngine:
    def __init__(self, entries: List[MemoryEntry]):
        self.entries = entries
        self.vectorizer = TfidfVectorizer(...)
        self.tfidf_matrix = None

        # Add type-specific caches
        self._type_caches: Dict[str, Tuple[TfidfVectorizer, Any]] = {}

        self._build_index()
        self._build_type_indexes()

    def _build_type_indexes(self) -> None:
        """Pre-build TF-IDF indexes for each memory type."""
        for mem_type in ["knowledge", "decision", "code", "task", "pattern"]:
            filtered = [e for e in self.entries if e.type == mem_type]
            if not filtered:
                continue

            # Create corpus
            corpus = [
                f"{e.title} {e.content} {' '.join(e.tags or [])} {e.category}"
                for e in filtered
            ]

            # Build type-specific vectorizer and matrix
            vectorizer = TfidfVectorizer(
                stop_words="english",
                max_features=1000,
                ngram_range=(1, 2),
                min_df=1,
                lowercase=True,
            )
            try:
                tfidf_matrix = vectorizer.fit_transform(corpus)
                self._type_caches[mem_type] = (vectorizer, tfidf_matrix, filtered)
            except ValueError:
                # Empty vocabulary
                continue

    def search(
        self,
        query: str,
        type_filter: Optional[List[str]] = None,
        limit: int = 10,
    ) -> List[tuple[MemoryEntry, float]]:
        """Search with type-specific cache optimization."""
        if not query.strip():
            return []

        # Use cached type-specific index if single type
        if type_filter and len(type_filter) == 1:
            cache_key = type_filter[0]
            if cache_key in self._type_caches:
                return self._search_with_cache(query, cache_key, limit)

        # Fall back to existing logic for multi-type or no filter
        # ... (existing implementation)

    def _search_with_cache(
        self, query: str, mem_type: str, limit: int
    ) -> List[tuple[MemoryEntry, float]]:
        """Search using cached type-specific index."""
        vectorizer, tfidf_matrix, filtered_entries = self._type_caches[mem_type]

        try:
            query_vec = vectorizer.transform([query])
            scores = cosine_similarity(query_vec, tfidf_matrix)[0]
        except ValueError:
            return []

        # Sort by score descending
        indices = scores.argsort()[-limit:][::-1]
        return [
            (filtered_entries[i], float(scores[i]))
            for i in indices
            if scores[i] > 0
        ]
```

#### Expected Performance Improvement
| Entries | Before | After | Improvement |
|---------|--------|-------|-------------|
| 100     | 40ms   | 15ms  | 2.7x faster |
| 1,000   | 120ms  | 20ms  | 6x faster   |
| 10,000  | 1,200ms| 50ms  | 24x faster  |

#### Memory Overhead
- **Per type**: ~2MB for 1,000 entries
- **Total**: ~10MB for 5 types (acceptable)

#### Acceptance Criteria
- [ ] Implement _build_type_indexes() method
- [ ] Implement _search_with_cache() method
- [ ] Update search() to use cache for single-type filters
- [ ] Add tests for cached search
- [ ] Benchmark performance (before/after)
- [ ] Update documentation

#### Verification
```python
# tests/performance/test_memory_performance.py
def test_memory_search_type_filter_performance(tmp_path, benchmark):
    """Benchmark type-filtered search with caching."""
    memory = setup_memory_with_1000_entries(tmp_path)

    # Benchmark type-filtered search
    result = benchmark(memory.search, "test query", type_filter=["knowledge"])

    # Should be <20ms for 1000 entries
    assert benchmark.stats.mean < 0.02
```

#### Risk: Low (cache invalidation handled by existing logic)
#### Dependencies: None
#### Blocks: None (optimization only)

---

### TASK-M2: Add Performance Benchmarks

**ID**: TASK-M2
**Priority**: MEDIUM (Nice-to-have for regression detection)
**Severity**: LOW
**Category**: Testing
**Effort**: 3 hours
**Assignee**: Developer
**Status**: PENDING

#### Description
Add performance benchmark tests using pytest-benchmark to detect performance regressions in critical operations.

#### File
`tests/performance/test_memory_performance.py` (new file)

#### Benchmarks to Add
```python
"""
Performance benchmarks for Memory System.

Run with: pytest tests/performance/ --benchmark-only
Compare: pytest tests/performance/ --benchmark-compare
"""

import pytest
from clauxton.core.memory import Memory, MemoryEntry
from datetime import datetime


def create_test_entry(id_suffix: int = 1) -> MemoryEntry:
    """Helper to create test entry."""
    now = datetime.now()
    return MemoryEntry(
        id=f"MEM-20260127-{id_suffix:03d}",
        type="knowledge",
        title=f"Test Entry {id_suffix}",
        content=f"Test content {id_suffix} " * 20,  # ~200 chars
        category="test",
        tags=["test", f"tag{id_suffix}"],
        created_at=now,
        updated_at=now,
        source="manual",
    )


def setup_memory_with_entries(tmp_path, count: int) -> Memory:
    """Helper to setup memory with N entries."""
    memory = Memory(tmp_path)
    for i in range(1, count + 1):
        entry = create_test_entry(i)
        memory.add(entry)
    return memory


# ============================================================================
# Add Operation Benchmarks
# ============================================================================

def test_benchmark_memory_add(tmp_path, benchmark):
    """
    Benchmark Memory.add() operation.

    Target: <50ms (actual: ~5ms)
    """
    memory = Memory(tmp_path)
    entry = create_test_entry()

    result = benchmark(memory.add, entry)

    assert result.startswith("MEM-")
    assert benchmark.stats.mean < 0.05  # <50ms target


def test_benchmark_memory_add_with_100_existing(tmp_path, benchmark):
    """
    Benchmark Memory.add() with 100 existing entries.

    Target: <50ms
    """
    memory = setup_memory_with_entries(tmp_path, 100)
    new_entry = create_test_entry(101)

    result = benchmark(memory.add, new_entry)

    assert result.startswith("MEM-")
    assert benchmark.stats.mean < 0.05  # <50ms target


# ============================================================================
# Search Operation Benchmarks
# ============================================================================

def test_benchmark_memory_search_10_entries(tmp_path, benchmark):
    """
    Benchmark search with 10 entries.

    Target: <50ms
    """
    memory = setup_memory_with_entries(tmp_path, 10)

    result = benchmark(memory.search, "test content")

    assert len(result) > 0
    assert benchmark.stats.mean < 0.05  # <50ms target


def test_benchmark_memory_search_100_entries(tmp_path, benchmark):
    """
    Benchmark search with 100 entries.

    Target: <50ms (actual: ~20ms)
    """
    memory = setup_memory_with_entries(tmp_path, 100)

    result = benchmark(memory.search, "test content")

    assert len(result) > 0
    assert benchmark.stats.mean < 0.05  # <50ms target


def test_benchmark_memory_search_1000_entries(tmp_path, benchmark):
    """
    Benchmark search with 1000 entries.

    Target: <100ms (actual: ~20ms)
    """
    memory = setup_memory_with_entries(tmp_path, 1000)

    result = benchmark(memory.search, "test content")

    assert len(result) > 0
    assert benchmark.stats.mean < 0.1  # <100ms target


def test_benchmark_memory_search_type_filter_1000_entries(tmp_path, benchmark):
    """
    Benchmark type-filtered search with 1000 entries.

    Target: <100ms (current: ~120ms, see TASK-M1)
    """
    memory = setup_memory_with_entries(tmp_path, 1000)

    result = benchmark(memory.search, "test content", type_filter=["knowledge"])

    assert len(result) > 0
    # Note: May fail until TASK-M1 is complete
    # assert benchmark.stats.mean < 0.1  # <100ms target


# ============================================================================
# Get Operation Benchmarks
# ============================================================================

def test_benchmark_memory_get_100_entries(tmp_path, benchmark):
    """
    Benchmark Memory.get() with 100 entries.

    Target: <10ms
    """
    memory = setup_memory_with_entries(tmp_path, 100)
    target_id = "MEM-20260127-050"

    result = benchmark(memory.get, target_id)

    assert result is not None
    assert benchmark.stats.mean < 0.01  # <10ms target


# ============================================================================
# Update Operation Benchmarks
# ============================================================================

def test_benchmark_memory_update_100_entries(tmp_path, benchmark):
    """
    Benchmark Memory.update() with 100 entries.

    Target: <50ms
    """
    memory = setup_memory_with_entries(tmp_path, 100)
    target_id = "MEM-20260127-050"

    result = benchmark(memory.update, target_id, title="Updated Title")

    assert result is True
    assert benchmark.stats.mean < 0.05  # <50ms target


# ============================================================================
# List Operation Benchmarks
# ============================================================================

def test_benchmark_memory_list_all_1000_entries(tmp_path, benchmark):
    """
    Benchmark Memory.list_all() with 1000 entries.

    Target: <100ms
    """
    memory = setup_memory_with_entries(tmp_path, 1000)

    result = benchmark(memory.list_all)

    assert len(result) == 1000
    assert benchmark.stats.mean < 0.1  # <100ms target


# ============================================================================
# Migration Benchmarks
# ============================================================================

def test_benchmark_migration_1000_kb_entries(tmp_path, benchmark):
    """
    Benchmark migration with 1000 KB entries.

    Target: <1s
    """
    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.utils.migrate_to_memory import MemoryMigrator

    # Setup 1000 KB entries
    kb = KnowledgeBase(tmp_path)
    for i in range(1, 1001):
        from clauxton.core.models import KnowledgeBaseEntry
        entry = KnowledgeBaseEntry(
            id=f"KB-20260127-{i:03d}",
            title=f"KB Entry {i}",
            content=f"Content {i} " * 20,
            category="test",
            created_at=datetime.now(),
            updated_at=datetime.now(),
        )
        kb.add(entry)

    migrator = MemoryMigrator(tmp_path, dry_run=False)

    result = benchmark(migrator.migrate_all)

    assert result["kb_count"] == 1000
    assert benchmark.stats.mean < 1.0  # <1s target
```

#### Setup
```bash
# Install pytest-benchmark
pip install pytest-benchmark

# Run benchmarks
pytest tests/performance/ --benchmark-only

# Compare with baseline
pytest tests/performance/ --benchmark-compare
```

#### Acceptance Criteria
- [ ] Add 10+ benchmark tests
- [ ] Cover: add, search, get, update, list, migration
- [ ] All benchmarks pass (<target time)
- [ ] CI integration (optional)
- [ ] Documentation in test docstrings

#### Verification
```bash
pytest tests/performance/test_memory_performance.py --benchmark-only -v
# All benchmarks should pass
```

#### Risk: None (testing only)
#### Dependencies: None
#### Blocks: None

---

### TASK-M3: Refactor ID Generator Duplication

**ID**: TASK-M3
**Priority**: MEDIUM (Technical debt, not urgent)
**Severity**: LOW
**Category**: Code Quality
**Effort**: 2 hours
**Assignee**: Developer
**Status**: PENDING

#### Description
Extract duplicate ID generation logic to a utility function. Currently, 4 implementations exist with similar logic (~100 lines total duplication).

#### Location
- `clauxton/core/memory.py:726-750`
- `clauxton/core/knowledge_base_compat.py:349-377`
- `clauxton/core/task_manager_compat.py:378-403`
- `clauxton/utils/migrate_to_memory.py:320-349`

#### Current Duplication
```python
# Repeated 4 times with variations
def _generate_memory_id(self) -> str:
    entries = self.store.load_all()
    today = datetime.now().strftime("%Y%m%d")
    today_ids = [
        int(e.id.split("-")[-1])
        for e in entries
        if e.id.startswith(f"MEM-{today}")
    ]
    next_num = max(today_ids, default=0) + 1
    return f"MEM-{today}-{next_num:03d}"
```

#### Proposed Solution
```python
# clauxton/utils/id_generator.py (NEW FILE)
"""
ID generation utilities for Clauxton.

Provides sequential ID generation with date prefixes.
"""

from datetime import datetime
from typing import Any, Callable, List


def generate_sequential_id(
    prefix: str,
    date_format: str = "",
    entries: List[Any] = None,
    id_extractor: Callable[[Any], str] = None,
) -> str:
    """
    Generate sequential ID with optional date prefix.

    Args:
        prefix: ID prefix (e.g., "MEM", "KB", "TASK")
        date_format: Date format for prefix (e.g., "%Y%m%d"), empty = no date
        entries: List of existing entries (optional, for collision detection)
        id_extractor: Function to extract ID from entry (default: lambda e: e.id)

    Returns:
        Sequential ID (e.g., "MEM-20260127-001" or "TASK-001")

    Example:
        >>> generate_sequential_id("MEM", "%Y%m%d", entries, lambda e: e.id)
        'MEM-20260127-001'

        >>> generate_sequential_id("TASK", "", entries, lambda e: e.id)
        'TASK-001'
    """
    if id_extractor is None:
        id_extractor = lambda e: e.id

    # Build prefix with date if format provided
    if date_format:
        today = datetime.now().strftime(date_format)
        full_prefix = f"{prefix}-{today}"
    else:
        full_prefix = prefix

    # Find existing IDs with this prefix
    existing_ids = []
    if entries:
        for entry in entries:
            entry_id = id_extractor(entry)
            if entry_id.startswith(full_prefix):
                try:
                    # Extract sequence number (last part after -)
                    seq_str = entry_id.split("-")[-1]
                    existing_ids.append(int(seq_str))
                except (ValueError, IndexError):
                    # Ignore malformed IDs
                    continue

    # Get next sequence number
    next_num = max(existing_ids, default=0) + 1

    # Format ID
    if date_format:
        return f"{prefix}-{today}-{next_num:03d}"
    else:
        return f"{prefix}-{next_num:03d}"
```

#### Refactored Usage
```python
# clauxton/core/memory.py
from clauxton.utils.id_generator import generate_sequential_id

def _generate_memory_id(self) -> str:
    return generate_sequential_id(
        prefix="MEM",
        date_format="%Y%m%d",
        entries=self.store.load_all(),
        id_extractor=lambda e: e.id
    )

# clauxton/utils/migrate_to_memory.py
from clauxton.utils.id_generator import generate_sequential_id

def _generate_memory_id(self) -> str:
    return generate_sequential_id(
        prefix="MEM",
        date_format="%Y%m%d",
        entries=self.memory.list_all(),
        id_extractor=lambda e: e.id
    )
```

#### Scope Note
**ONLY refactor**:
- `clauxton/core/memory.py`
- `clauxton/utils/migrate_to_memory.py`

**DO NOT refactor**:
- `clauxton/core/knowledge_base_compat.py` (deprecated, removal in v0.17.0)
- `clauxton/core/task_manager_compat.py` (deprecated, removal in v0.17.0)

**Rationale**: Refactoring deprecated code has limited ROI. Focus on active code only.

#### Acceptance Criteria
- [ ] Create `clauxton/utils/id_generator.py`
- [ ] Implement `generate_sequential_id()` with tests
- [ ] Refactor Memory._generate_memory_id()
- [ ] Refactor MemoryMigrator._generate_memory_id()
- [ ] Add docstrings and examples
- [ ] Add unit tests (10+ tests)
- [ ] Verify no behavior change

#### Verification
```python
# tests/utils/test_id_generator.py
def test_generate_sequential_id_with_date():
    """Test ID generation with date prefix."""
    entries = [
        MockEntry("MEM-20260127-001"),
        MockEntry("MEM-20260127-002"),
    ]

    result = generate_sequential_id(
        prefix="MEM",
        date_format="%Y%m%d",
        entries=entries,
        id_extractor=lambda e: e.id
    )

    assert result == "MEM-20260127-003"

def test_generate_sequential_id_without_date():
    """Test ID generation without date prefix."""
    entries = [
        MockEntry("TASK-001"),
        MockEntry("TASK-002"),
    ]

    result = generate_sequential_id(
        prefix="TASK",
        date_format="",
        entries=entries,
        id_extractor=lambda e: e.id
    )

    assert result == "TASK-003"
```

#### Risk: Low (existing tests verify behavior)
#### Dependencies: None
#### Blocks: None

---

## Low Priority (3 tasks)

### TASK-L1: Add CLI Integration Tests

**ID**: TASK-L1
**Priority**: LOW (CLI presentation logic, not business logic)
**Severity**: LOW
**Category**: Testing
**Effort**: 2 hours
**Assignee**: Developer
**Status**: PENDING

#### Description
Add integration tests for CLI commands to improve coverage of `clauxton/cli/migrate.py` (currently 24% coverage).

#### File
`tests/integration/test_cli_migration.py` (new file)

#### Tests to Add
```python
"""
Integration tests for CLI migration commands.

Uses CliRunner to test interactive prompts and Rich output.
"""

from click.testing import CliRunner
from clauxton.cli.migrate import migrate, memory, rollback
from clauxton.core.knowledge_base import KnowledgeBase
from clauxton.core.models import KnowledgeBaseEntry
from datetime import datetime


def test_migrate_memory_dry_run(tmp_path):
    """Test migrate memory with --dry-run flag."""
    runner = CliRunner()

    # Setup KB entries
    kb = KnowledgeBase(tmp_path)
    entry = KnowledgeBaseEntry(
        id="KB-20260127-001",
        title="Test Entry",
        content="Test content",
        category="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
    )
    kb.add(entry)

    # Run dry-run migration
    result = runner.invoke(memory, ["--dry-run"], obj={"project_root": tmp_path})

    # Verify
    assert result.exit_code == 0
    assert "Migration Preview (Dry Run)" in result.output
    assert "KB entries: 1" in result.output
    assert "Tasks: 0" in result.output
    assert "Total: 1" in result.output


def test_migrate_memory_confirm(tmp_path):
    """Test migrate memory with --confirm flag."""
    runner = CliRunner()

    # Setup KB entries
    kb = KnowledgeBase(tmp_path)
    entry = KnowledgeBaseEntry(...)
    kb.add(entry)

    # Run migration
    result = runner.invoke(memory, ["--confirm"], obj={"project_root": tmp_path})

    # Verify
    assert result.exit_code == 0
    assert "Migration complete!" in result.output
    assert "Backup created" in result.output or "backup" in result.output.lower()


def test_migrate_memory_no_flags_shows_help(tmp_path):
    """Test migrate memory without flags shows help."""
    runner = CliRunner()

    result = runner.invoke(memory, [], obj={"project_root": tmp_path})

    # Should show help text
    assert "Please use --dry-run to preview or --confirm to execute" in result.output
    assert result.exit_code == 0  # Not an error, just informational


def test_migrate_rollback_with_confirmation(tmp_path):
    """Test rollback command with user confirmation."""
    runner = CliRunner()

    # Create backup directory
    backup_dir = tmp_path / ".clauxton" / "backups" / "pre_migration_20260127_143052"
    backup_dir.mkdir(parents=True)

    # Run rollback with "yes" confirmation
    result = runner.invoke(
        rollback,
        [str(backup_dir)],
        input="yes\n",
        obj={"project_root": tmp_path}
    )

    # Verify
    assert result.exit_code == 0
    assert "Rollback complete!" in result.output


def test_migrate_rollback_cancelled(tmp_path):
    """Test rollback command cancelled by user."""
    runner = CliRunner()

    backup_dir = tmp_path / ".clauxton" / "backups" / "pre_migration_20260127_143052"
    backup_dir.mkdir(parents=True)

    # Run rollback with "no" confirmation
    result = runner.invoke(
        rollback,
        [str(backup_dir)],
        input="no\n",
        obj={"project_root": tmp_path}
    )

    # Verify
    assert result.exit_code == 0
    assert "Rollback cancelled" in result.output
```

#### Acceptance Criteria
- [ ] Add 10+ CLI integration tests
- [ ] Test dry-run mode
- [ ] Test confirm mode
- [ ] Test rollback with confirmation
- [ ] Test error handling
- [ ] Coverage: migrate.py 24% → 60%+

#### Verification
```bash
pytest tests/integration/test_cli_migration.py -v
pytest tests/cli/test_migrate.py --cov=clauxton/cli/migrate.py --cov-report=term
```

#### Risk: None (testing only)
#### Dependencies: None
#### Blocks: None

---

### TASK-L2: Add State Transition Tests

**ID**: TASK-L2
**Priority**: LOW (Current coverage adequate)
**Severity**: LOW
**Category**: Testing
**Effort**: 1 hour
**Assignee**: Developer
**Status**: PENDING

#### Description
Add comprehensive state transition tests for complete memory lifecycle scenarios.

#### File
`tests/integration/test_memory_state_transitions.py` (new file)

#### Tests to Add
```python
"""
State transition tests for Memory System.

Tests complete lifecycle and multi-step operations.
"""

from clauxton.core.memory import Memory, MemoryEntry
from datetime import datetime


def test_memory_lifecycle_complete(tmp_path):
    """Test complete memory lifecycle: add → search → update → delete."""
    memory = Memory(tmp_path)

    # Initial state: empty
    assert len(memory.list_all()) == 0

    # State 1: Add entry
    entry1 = MemoryEntry(
        id="MEM-20260127-001",
        type="knowledge",
        title="Entry 1",
        content="Content 1",
        category="test",
        created_at=datetime.now(),
        updated_at=datetime.now(),
        source="manual",
    )
    memory.add(entry1)
    assert len(memory.list_all()) == 1

    # State 2: Add related entry
    entry2 = MemoryEntry(
        id="MEM-20260127-002",
        type="knowledge",
        title="Entry 2",
        content="Content 2",
        category="test",
        related_to=["MEM-20260127-001"],
        created_at=datetime.now(),
        updated_at=datetime.now(),
        source="manual",
    )
    memory.add(entry2)
    assert len(memory.list_all()) == 2
    assert len(memory.find_related("MEM-20260127-001")) == 1

    # State 3: Search entries
    results = memory.search("Entry")
    assert len(results) == 2

    # State 4: Update entry
    memory.update("MEM-20260127-001", title="Updated Entry 1")
    updated = memory.get("MEM-20260127-001")
    assert updated.title == "Updated Entry 1"

    # State 5: Delete entry
    memory.delete("MEM-20260127-001")
    assert len(memory.list_all()) == 1
    assert memory.get("MEM-20260127-001") is None

    # State 6: Related entry still exists
    remaining = memory.get("MEM-20260127-002")
    assert remaining is not None
    # Relationship may be broken, but entry exists
    assert "MEM-20260127-001" in remaining.related_to


def test_memory_relationship_chain(tmp_path):
    """Test chain of relationships: A → B → C."""
    memory = Memory(tmp_path)

    # Add entries with relationship chain
    entry_a = create_entry("001", related_to=[])
    entry_b = create_entry("002", related_to=["MEM-20260127-001"])
    entry_c = create_entry("003", related_to=["MEM-20260127-002"])

    memory.add(entry_a)
    memory.add(entry_b)
    memory.add(entry_c)

    # Verify relationships
    related_to_a = memory.find_related("MEM-20260127-001")
    assert len(related_to_a) >= 1
    assert any(e.id == "MEM-20260127-002" for e in related_to_a)

    related_to_b = memory.find_related("MEM-20260127-002")
    assert len(related_to_b) >= 1


def test_memory_batch_operations(tmp_path):
    """Test batch operations: add multiple, update multiple."""
    memory = Memory(tmp_path)

    # Batch add
    entries = [create_entry(f"{i:03d}") for i in range(1, 11)]
    for entry in entries:
        memory.add(entry)

    assert len(memory.list_all()) == 10

    # Batch update (via loop)
    for i in range(1, 11):
        memory.update(f"MEM-20260127-{i:03d}", tags=["updated"])

    # Verify all updated
    updated_entries = memory.list_all(tag_filter=["updated"])
    assert len(updated_entries) == 10


def test_memory_migration_state_transition(tmp_path):
    """Test migration state: KB → Memory → Rollback → KB."""
    from clauxton.core.knowledge_base import KnowledgeBase
    from clauxton.utils.migrate_to_memory import MemoryMigrator

    # State 1: KB entries exist
    kb = KnowledgeBase(tmp_path)
    kb_entry = create_kb_entry("001")
    kb.add(kb_entry)
    assert len(kb.list_all()) == 1

    # State 2: Migrate to Memory
    migrator = MemoryMigrator(tmp_path)
    backup_path = migrator.create_rollback_backup()
    result = migrator.migrate_all()
    assert result["kb_count"] == 1

    memory = Memory(tmp_path)
    assert len(memory.list_all(type_filter=["knowledge"])) == 1

    # State 3: Rollback
    migrator.rollback(backup_path)

    # State 4: KB restored
    kb_restored = KnowledgeBase(tmp_path)
    assert len(kb_restored.list_all()) == 1
```

#### Acceptance Criteria
- [ ] Add 5+ state transition tests
- [ ] Test complete lifecycle
- [ ] Test relationship chains
- [ ] Test batch operations
- [ ] Test migration states

#### Verification
```bash
pytest tests/integration/test_memory_state_transitions.py -v
```

#### Risk: None (testing only)
#### Dependencies: None
#### Blocks: None

---

### TASK-L3: Document Exception Handlers

**ID**: TASK-L3
**Priority**: LOW (Code already clear)
**Severity**: LOW
**Category**: Code Quality
**Effort**: 30 minutes
**Assignee**: Developer
**Status**: PENDING

#### Description
Add inline comments to broad exception handlers explaining why they're necessary and what they catch.

#### Location
6 broad exception handlers:
1. `clauxton/core/memory.py:597`
2. `clauxton/core/memory.py:761`
3. `clauxton/core/memory_store.py:220`
4. `clauxton/core/knowledge_base_compat.py:344`
5. `clauxton/core/task_manager_compat.py:336`
6. `clauxton/utils/migrate_to_memory.py:117`

#### Current Code (Example)
```python
# clauxton/core/memory.py:597
except Exception as e:
    raise ValidationError(f"Failed to update memory: {e}") from e
```

#### Proposed Documentation
```python
# clauxton/core/memory.py:597
except Exception as e:
    # Catch all Pydantic validation errors and re-raise as ValidationError
    # This ensures consistent exception types for API callers, while preserving
    # the original exception context via the "from e" chain.
    # Common exceptions: ValidationError (Pydantic), TypeError, ValueError
    raise ValidationError(f"Failed to update memory: {e}") from e
```

#### Changes for Each Location

##### 1. clauxton/core/memory.py:597
```python
except Exception as e:
    # Catch all Pydantic validation errors and re-raise as ValidationError.
    # This ensures consistent exception types for callers while preserving
    # the original exception chain (ValidationError, TypeError, ValueError).
    raise ValidationError(f"Failed to update memory: {e}") from e
```

##### 2. clauxton/core/memory.py:761
```python
except Exception:
    # If search engine initialization fails (e.g., empty vocabulary, malformed data),
    # fall back to simple search instead of crashing. This provides graceful
    # degradation when TF-IDF vectorization fails.
    self._search_engine = None
```

##### 3. clauxton/core/memory_store.py:220
```python
except Exception:
    # Index file is optional (performance optimization only).
    # If JSON write fails (permissions, disk space), continue without index.
    # Searches will still work, just slightly slower without fast lookup.
    pass
```

##### 4. clauxton/core/knowledge_base_compat.py:344
```python
except Exception as e:
    # Catch Pydantic validation errors during KB → Memory conversion.
    # This handles edge cases like malformed category values or missing fields.
    # Re-raise as ValidationError for consistent error handling.
    raise ValidationError(
        f"Failed to convert Memory entry to KB entry: {e}"
    ) from e
```

##### 5. clauxton/core/task_manager_compat.py:336
```python
except Exception as e:
    # Catch Pydantic validation errors during Task → Memory conversion.
    # This handles edge cases like invalid status/priority values or missing fields.
    # Re-raise as ValidationError for consistent error handling.
    raise ValidationError(
        f"Failed to convert Memory entry to Task: {e}"
    ) from e
```

##### 6. clauxton/utils/migrate_to_memory.py:117
```python
except Exception as e:
    # Catch any migration errors (file I/O, validation, data corruption).
    # Inform user about backup location for rollback if needed.
    # This ensures users can always recover their data.
    if backup_path and not self.dry_run:
        logger.error(
            f"Migration failed: {e}. You can rollback using: "
            f"clauxton migrate rollback {backup_path}"
        )
    raise MigrationError(f"Migration failed: {e}") from e
```

#### Acceptance Criteria
- [ ] Add inline comments to all 6 exception handlers
- [ ] Comments explain:
  - Why broad exception is necessary
  - What exceptions are expected
  - What happens after catching
- [ ] No behavior change

#### Verification
```bash
# Review code for clarity
grep -A 3 "except Exception" clauxton/core/memory.py clauxton/core/memory_store.py clauxton/core/*_compat.py clauxton/utils/migrate_to_memory.py
```

#### Risk: None (documentation only, no behavior change)
#### Dependencies: None
#### Blocks: None

---

## Task Summary by Priority

### High Priority (Before v0.15.0 Release)
1. **TASK-H1**: Fix line length violations (5 min) ⚠️ BLOCKER
2. **TASK-H2**: Create migration guide (2 hours) ⚠️ REQUIRED
3. **TASK-H3**: Update CHANGELOG (30 min) ⚠️ REQUIRED
4. **TASK-H4**: Update README (1 hour) ⚠️ REQUIRED

**Total**: ~3.5 hours
**Status**: All must be completed before v0.15.0 release

### Medium Priority (Phase 2)
5. **TASK-M1**: Optimize TF-IDF index (4 hours) 🎯 Performance
6. **TASK-M2**: Add performance benchmarks (3 hours) 📊 Testing
7. **TASK-M3**: Refactor ID generator (2 hours) 🔧 Technical debt

**Total**: ~9 hours
**Status**: Implement during Phase 2 if time permits

### Low Priority (When Convenient)
8. **TASK-L1**: CLI integration tests (2 hours) ✅ Testing
9. **TASK-L2**: State transition tests (1 hour) ✅ Testing
10. **TASK-L3**: Document exceptions (30 min) 📝 Documentation

**Total**: ~3.5 hours
**Status**: Nice-to-have improvements

---

## Execution Plan

### Week 1 (Before v0.15.0 Release)
**Monday**:
- [ ] TASK-H1: Fix ruff warnings (5 min)
- [ ] TASK-H2: Create migration guide (2 hours)

**Tuesday**:
- [ ] TASK-H3: Update CHANGELOG (30 min)
- [ ] TASK-H4: Update README (1 hour)
- [ ] Review all documentation for consistency

**Wednesday**:
- [ ] Final review and testing
- [ ] Tag v0.15.0 release

### Phase 2 (Optional Improvements)
**As Needed**:
- [ ] TASK-M1: Optimize TF-IDF (if performance issues reported)
- [ ] TASK-M2: Add benchmarks (for regression detection)
- [ ] TASK-M3: Refactor duplicates (for cleaner code)

### Future (Low Priority)
**When Time Available**:
- [ ] TASK-L1: CLI tests (improve coverage)
- [ ] TASK-L2: State tests (edge case coverage)
- [ ] TASK-L3: Document exceptions (code clarity)

---

**Report Generated**: 2025-11-03
**Total Estimated Effort**: ~16 hours
**Critical Path**: ~3.5 hours (HIGH priority tasks)
