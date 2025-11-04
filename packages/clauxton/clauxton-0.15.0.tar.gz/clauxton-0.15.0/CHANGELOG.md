# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

## [0.15.0] - 2025-11-03

### Added
- **Unified Memory Model**: Integrated Knowledge Base, Task Management, and Code Intelligence into a single memory system
  - `MemoryEntry` model with 5 types: knowledge, decision, code, task, pattern
  - Unified storage in `.clauxton/memories.yml` with atomic writes
  - Relationship support: `related_to`, `supersedes` fields for memory connections
  - Confidence scoring (0.0-1.0) for auto-extracted memories
  - Legacy ID preservation for seamless migration
- **Memory Core**: New core modules for memory management
  - `Memory` class with CRUD operations (add, get, search, update, delete, find_related)
  - `MemoryStore` with YAML-based storage, in-memory caching, and automatic backups
  - TF-IDF search with simple keyword fallback
  - Sequential Memory ID generation (MEM-YYYYMMDD-NNN format)
- **Backward Compatibility Layer**: Existing APIs continue to work
  - `KnowledgeBaseCompat` - KB API → Memory API mapping
  - `TaskManagerCompat` - Task API → Memory API mapping
  - Deprecation warnings with migration guidance (removal in v0.17.0)
  - Full bidirectional conversion (KB/Task ↔ Memory)
- **Migration Utilities**: Safe migration from KB/Tasks to Memory
  - `MemoryMigrator` class with dry-run mode
  - Automatic timestamped backups before migration
  - Rollback support for failed migrations
  - CLI commands: `clauxton migrate memory`, `clauxton migrate rollback`
- **Memory CLI Commands**: 7 new commands for memory management
  - `clauxton memory add` - Add memory with interactive mode
  - `clauxton memory search` - TF-IDF search with type/category filters
  - `clauxton memory list` - List all memories with filters
  - `clauxton memory get` - View detailed memory information
  - `clauxton memory update` - Update memory fields
  - `clauxton memory delete` - Safe deletion with confirmation
  - `clauxton memory related` - Find related memories
- **Memory MCP Tools**: 6 new MCP server tools for Claude Code integration
  - `memory_add()` - Add memory entries (all 5 types)
  - `memory_search()` - Search with TF-IDF ranking
  - `memory_get()` - Retrieve memory by ID
  - `memory_list()` - List with type/category/tag filters
  - `memory_update()` - Update memory fields
  - `memory_find_related()` - Find related memories
- **Smart Memory (Phase 2)**: Auto-extraction and relationship detection
  - `MemoryExtractor` - Extract memories from Git commit history
    - Decision extraction from commit messages (feat:, refactor:, migration patterns)
    - Code pattern detection (API, UI, database, test changes)
    - Confidence scoring (0.5-1.0) for auto-extracted memories
    - Tag and category auto-assignment
  - `MemoryLinker` - Auto-detect relationships between memories
    - Multi-signal similarity: content (40%), tags (30%), category (20%), temporal (10%)
    - TF-IDF cosine similarity with keyword fallback
    - Auto-link all memories with configurable threshold
    - Merge candidate detection for duplicates (>0.8 similarity)
  - **CLI Extract Commands**: 3 new commands for smart memory features
    - `clauxton memory extract` - Extract from commits (--since, --commit, --auto-add)
    - `clauxton memory link` - Auto-link memories (--id, --auto, --threshold)
    - `clauxton memory suggest-merge` - Find duplicate memories (--threshold, --limit)
- **Comprehensive Testing**: 257 tests with high coverage
  - Memory Core: 62 tests (82-95% coverage)
  - Backward Compatibility: 40 tests (79-83% coverage)
  - Migration: 17 tests (91% coverage)
  - CLI: 58 tests (54-82% coverage)
  - MCP: 34 tests (90%+ coverage)
  - Memory Extraction: 25 tests (94% coverage)
  - Memory Linking: 22 tests (90% coverage)

### Changed
- Knowledge Base and Task Management now use unified Memory system internally
- All existing KB/Task APIs remain functional with deprecation warnings
- MCP server updated with 6 new memory tools (32 → 38 total tools)

### Deprecated
- `KnowledgeBase` API (use `Memory` with `type="knowledge"` instead)
- `TaskManager` API (use `Memory` with `type="task"` instead)
- Legacy KB MCP tools: `kb_add()`, `kb_search()`, `kb_list()`, `kb_get()`, `kb_update()`, `kb_delete()`
- Legacy Task MCP tools: `task_add()`, `task_list()`, `task_get()`, `task_update()`, `task_next()`, `task_delete()`
- **Note**: Deprecated APIs will be removed in v0.17.0 (planned for 2026-Q2)

### Fixed
- Line length violations in migration CLI (E501)
- Type safety improvements with strict mypy compliance

### Security
- 0 vulnerabilities detected in security audit
- YAML safe loading enforced (no code execution risk)
- Input validation via Pydantic models
- Atomic file writes with automatic backups

### Performance
- Memory.search(): 5-20ms (target: <100ms) ✅ 5-10x faster
- Memory.add(): 5-10ms (target: <50ms) ✅ 5-10x faster
- MemoryExtractor.extract_from_commit(): 30-80ms (target: <100ms) ✅
- MemoryLinker.find_relationships(): ~150ms for 1K entries (target: <200ms) ✅
- MemoryLinker.auto_link_all(): ~20-25s for 1K entries
- In-memory caching for repeated operations
- JSON-based index for fast lookups

### Documentation
- Phase 1 quality review reports (5 documents, 4,508 lines)
- Comprehensive API documentation (Google-style docstrings)
- CLI help texts for all memory commands
- MCP tool descriptions with examples

## [0.14.0] - 2025-10-28

### Added
- **Interactive TUI (Terminal User Interface)**: Full-featured terminal UI for Clauxton
  - Dashboard screen with 3-panel layout (KB Browser, Content Viewer, AI Suggestions)
  - Real-time knowledge base browsing with visual indicators
  - Content viewer with syntax highlighting and rich text rendering
  - AI-powered suggestions panel with actionable recommendations
  - Query modal for search and command execution (slash commands, natural language)
  - Help modal with comprehensive keyboard shortcuts reference
  - Status bar with context information and command hints
- **Keyboard Navigation**: Vim-style navigation and shortcuts
  - Navigation: `j/k` (down/up), `h/l` (left/right), `g/G` (top/bottom)
  - Actions: `/` (search), `:` (command), `?` (help), `q` (quit)
  - Focus control: `Tab/Shift+Tab` (cycle panels), `Ctrl+h/j/k/l` (panel navigation)
  - Quick actions: `a` (add KB), `t` (add task), `r` (refresh)
- **Visual Features**:
  - Theme support (light/dark modes with customizable colors)
  - Syntax highlighting for code and markdown
  - Progress indicators and loading states
  - Visual focus indicators for accessibility
- **Intelligence Features**:
  - File indexing with symbol extraction
  - Query autocomplete with intelligent suggestions
  - Context-aware AI recommendations
  - Real-time suggestion updates
- **Comprehensive Testing**: 189 integration tests, 18 edge case tests
  - Workflow tests (22 tests): KB browser, query modal, quick actions, navigation, user journeys
  - Modal tests (24 tests): Lifecycle, mode switching, help modal, interactions, focus
  - Navigation tests (37 tests): Panel focus, Vim-style, widget navigation, boundaries
  - Edge case tests (18 tests): Data boundaries, UI boundaries, error handling, search limits
- **User Documentation**:
  - [TUI User Guide](docs/TUI_USER_GUIDE.md): Complete interface guide with examples
  - [Keyboard Shortcuts](docs/TUI_KEYBOARD_SHORTCUTS.md): All shortcuts and navigation patterns
  - [Quality Report](docs/TUI_QUALITY_REPORT.md): Test coverage and quality metrics

### Changed
- CLI now supports `clauxton tui` command to launch interactive interface
- Enhanced file monitoring for TUI real-time updates
- Improved performance with efficient rendering and caching

### Technical Details
- Built with Textual framework for rich terminal UI
- Async/await architecture for responsive interface
- Modular widget system for extensibility
- Comprehensive test coverage (85% overall, 189 integration tests)
- Full keyboard accessibility (no mouse required)

## [0.13.0] - 2025-10-27

### Added
- **Context Intelligence**: AI-powered work session analysis and next action prediction (3 new MCP tools)
  - `analyze_work_session()`: Automatic session tracking with duration, focus score (0.0-1.0), break detection, and file switching analysis
  - `predict_next_action()`: AI-powered next action prediction with 9 supported actions (run_tests, write_tests, commit_changes, create_pr, take_break, morning_planning, resume_work, review_code, no_clear_action) and confidence scoring (0.0-1.0)
  - `get_current_context()`: Enhanced project context with Git info, active files, time context (morning/afternoon/evening/night), work session data, and optional action prediction
- **Proactive Monitoring**: Real-time file watching and pattern detection (2 new MCP tools)
  - `watch_project_changes()`: Enable/disable real-time file monitoring with watchdog integration
  - `get_recent_changes()`: Get recent file changes and detected patterns (bulk edits, new features, refactoring, cleanup, config changes)
- **Session Analysis Features**:
  - Session duration tracking (30-minute session timeout, configurable)
  - Focus score calculation based on file switching patterns (high: 0.8+, medium: 0.5-0.8, low: <0.5)
  - Break detection (≥15 minutes, configurable)
  - Active period tracking (continuous work periods between breaks)
  - Formula: `focus_score = max(0, 1 - (file_switches / (duration_minutes / 10)))`
- **Action Prediction Features**:
  - Context-aware prediction engine analyzing git status, file changes, session duration, and time of day
  - Confidence scoring with clear thresholds (high: 0.8+, medium: 0.5-0.8, low: <0.5)
  - Human-readable reasoning for each prediction
  - Support for 9 common development actions
- **Enhanced Context Features**:
  - Git information (branch, recent commits, uncommitted changes, diff stats)
  - Active files with modification timestamps
  - Time context awareness (morning 6-12, afternoon 12-18, evening 18-22, night 22-6)
  - 30-second caching for performance
  - Optional prediction inclusion for speed optimization
- **User Documentation**: 4 comprehensive user guides (~1500 lines total)
  - [Context Intelligence Guide](docs/guides/CONTEXT_INTELLIGENCE_GUIDE.md): Core concepts, usage, integration (400+ lines)
  - [Workflow Examples](docs/guides/WORKFLOW_EXAMPLES.md): 6 real-world scenarios (350+ lines)
  - [Best Practices](docs/guides/BEST_PRACTICES.md): Optimization tips and patterns (400+ lines)
  - [Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md): Common issues and solutions (350+ lines)

### Changed
- **Performance**: Significantly improved with intelligent caching
  - Session analysis: <50ms (p95)
  - Action prediction: <100ms with caching
  - Context retrieval: <100ms with prediction, <50ms without
  - 30-second context cache for repeated calls (<10ms)
- **Test Coverage**: Increased from 86% to 90% with comprehensive proactive testing
- **README**: Updated with Context Intelligence features, usage examples, and new statistics
- **MCP Tools**: Expanded from 32 to 36 tools total (5 new tools across 2 categories)
- **Code Quality**: Maintained strict type safety with mypy and 0 linting errors

### Fixed
- Type annotations in context_manager.py for mypy strict mode compliance
- Integration test assertions adjusted for real-world git scenarios
- ImportError handling in tests with proper skip markers
- Line length violations in test files (ruff compliance)

### Performance
- Session analysis: <50ms average, 30-second caching
- Action prediction: <100ms with all heuristics
- Context retrieval: <100ms (with prediction), <50ms (without)
- Repeated context calls: <10ms (cached)
- File monitoring: <5ms event processing, <1% CPU when idle
- Pattern detection: ~10-20ms per event batch

### Testing
- Added 316 comprehensive proactive tests (1,953+ total tests, +19% increase)
  - Week 1: 56 tests (config, event_processor, file_monitor MCP)
  - Week 2: 132 tests (behavior_tracker, suggestion_engine, context_manager)
  - Week 3: 128 tests (context intelligence MCP tools, integration scenarios)
- Test breakdown by module:
  - `test_context_manager.py`: 42 tests (session analysis, context retrieval) - 95% coverage
  - `test_suggestion_engine.py`: 26 tests (action prediction, all 9 actions) - 96% coverage
  - `test_behavior_tracker.py`: 33 tests (pattern learning, trend analysis) - 92% coverage
  - `test_mcp_context.py`: 18 tests (3 new MCP tools, error handling) - 100% coverage
  - `test_integration_day5.py`: 23 tests (end-to-end workflows) - N/A
- Coverage metrics:
  - Proactive modules: 89-100% coverage (context_manager 95%, suggestion_engine 96%, behavior_tracker 92%, event_processor 97%, file_monitor 100%, config 100%)
  - MCP server: 93% coverage (36 tools, all tested individually)
  - Overall project: 90% coverage (up from 86%)
- Test quality:
  - All performance benchmarks passing
  - Security tests: 19 tests, no vulnerabilities
  - Error handling: 33 comprehensive tests
  - Scenario coverage: 23 real-world integration tests

### Dependencies
- No new dependencies added (all built on existing stack)
- Optional dependencies remain: watchdog>=3.0.0 (for proactive monitoring, installed in v0.13.0 Week 1)

### Documentation
- [Context Intelligence User Guide](docs/guides/CONTEXT_INTELLIGENCE_GUIDE.md) - Complete guide with 8 sections
- [Workflow Examples](docs/guides/WORKFLOW_EXAMPLES.md) - 6 real-world scenarios (morning start, feature dev, bug fixing, code review, end of day, team collaboration)
- [Best Practices](docs/guides/BEST_PRACTICES.md) - Optimization tips, patterns, anti-patterns
- [Troubleshooting Guide](docs/guides/TROUBLESHOOTING.md) - 8 sections covering all common issues
- [README.md](README.md) - Updated with Context Intelligence features, 36 MCP tools, 1,953+ test statistics
- [Quality Report v0.13.0](docs/QUALITY_REPORT_v0.13.0.md) - Comprehensive quality assessment

### Migration Notes
- **MCP Tools**: 5 new tools available (3 context intelligence + 2 proactive monitoring)
- **No Breaking Changes**: All existing functionality remains unchanged
- **Opt-in Features**: Context Intelligence features are opt-in via MCP tool calls
- **Configuration**: New optional settings in `.clauxton/config.yml`:
  ```yaml
  proactive:
    enabled: true
    session_timeout_minutes: 30  # Session ends after inactivity
    focus_threshold: 0.7          # High focus threshold
    break_threshold_minutes: 15   # Break detection threshold
  ```

## [0.12.0] - 2025-10-26

### Added
- **Semantic Search**: AI-powered search using embeddings (3 new MCP tools)
  - `search_knowledge_semantic()`: Semantic KB search with similarity scoring
  - `search_tasks_semantic()`: Semantic task search with status/priority filters
  - `search_files_semantic()`: Semantic file search with pattern matching
- **Git Analysis**: Automatic commit analysis and pattern recognition (3 new MCP tools)
  - `analyze_recent_commits()`: Analyze commit patterns, file types, and statistics
  - `extract_decisions_from_commits()`: Extract architectural decisions from commits
  - `suggest_next_tasks()`: AI-powered task recommendations based on patterns
- **Enhanced Context**: Rich project context for AI consumption (4 new MCP tools)
  - `get_project_context()`: Comprehensive project context with 3 depth levels
  - `generate_project_summary()`: Markdown-formatted project summary
  - `get_knowledge_graph()`: Knowledge graph with nodes, edges, and clusters
  - `find_related_entries()`: Find related KB entries and tasks
- **Local Embedding Model**: sentence-transformers integration
  - Model: all-MiniLM-L6-v2 (384 dimensions, ~90MB)
  - Speed: ~500 texts/second on CPU
  - User consent mechanism (lazy loading)
  - Persistent FAISS vector indices
- **Documentation**: 3 comprehensive guides
  - Semantic Search Guide: Usage, configuration, troubleshooting
  - Git Analysis Guide: Pattern recognition, decision extraction
  - Release Notes v0.12.0: Full feature documentation

### Changed
- **Performance**: Semantic search <200ms (p95), Git analysis ~2s for 100 commits
- **Type Safety**: Fixed all 12 mypy type errors in mcp/server.py
- **Code Quality**: Fixed all 5 ruff linting warnings
- **Test Coverage**: Increased to 86% with +177 new tests (1,637 total)

### Fixed
- Type annotations for dictionary variables in server.py
- Unused variables and imports in MCP tools
- Line length violations in test files
- Sort lambda type inference issues

### Performance
- Semantic search: <200ms (p95)
- Encode 500 texts: ~600ms
- Vector search (1000 docs): ~50ms
- Incremental embedding updates (no full rebuild)

### Testing
- Added 105 semantic search tests
- Added 72 git analysis tests
- Coverage: semantic (93-98%), analysis (91-100%)
- All performance benchmarks passing

### Dependencies
- Added optional dependencies: sentence-transformers>=2.3.0, faiss-cpu>=1.7.4, torch>=2.1.0
- Install with: `pip install clauxton[semantic]`

### Documentation
- [Semantic Search Guide](docs/SEMANTIC_SEARCH_GUIDE.md)
- [Git Analysis Guide](docs/GIT_ANALYSIS_GUIDE.md)
- [Release Notes v0.12.0](docs/RELEASE_NOTES_v0.12.0.md)
- [v0.12.0 Quality Report](docs/v0.12.0-QUALITY_REPORT.md)

## [0.11.2] - 2025-10-25

### Internal - Test Infrastructure Optimization

**Focus**: Test execution optimization and coverage improvement
**Status**: ✅ Complete (Production Ready)

#### Improved

**Test Performance** (97% faster execution):
- ✅ Optimized test execution time from 52 minutes to 1m46s
- ✅ Separated 19 performance tests with `@pytest.mark.performance`
- ✅ Default test run excludes performance tests (1,348 tests in ~2 minutes)
- ✅ Performance tests run weekly via CI schedule (Sundays 02:00 UTC)
- ✅ Manual workflow trigger for on-demand performance testing

**Test Coverage** (81% → 85%):
- ✅ Added 50 new CLI tests:
  - 17 tests for daily workflow commands (status, overview, stats, focus, continue)
  - 15 tests for MCP commands (setup, status, configuration)
  - 18 tests for Repository commands (index, search, status)
- ✅ Improved module coverage:
  - `cli/mcp.py`: 15% → 94% (+79%)
  - `intelligence/repository_map.py`: 69% → 94% (+25%)
  - `cli/repository.py`: 65% → 70% (+5%)

**Test Infrastructure**:
- ✅ Created `tests/cli/conftest.py` for shared pytest fixtures
- ✅ Eliminated fixture code duplication across test files
- ✅ Enhanced CI/CD with weekly performance test schedule
- ✅ Added manual CI trigger capability

**Code Quality**:
- ✅ All lint checks passing (ruff)
- ✅ All type checks passing (mypy strict mode)
- ✅ 100% test pass rate (1,367/1,367 tests)
- ✅ Production-ready quality score: 4.7/5.0 (94%)

**Documentation**:
- ✅ Updated README.md with comprehensive testing guide
- ✅ Archived test optimization reports in `docs/archive/test-optimization/`
- ✅ Updated coverage badge (85%)

#### Technical Details

**Files Created**:
- `tests/cli/conftest.py` - Shared pytest fixtures
- `tests/cli/test_mcp_commands.py` - 15 MCP CLI tests
- `tests/cli/test_repository_commands.py` - 18 Repository CLI tests
- `docs/archive/test-optimization/` - Complete project documentation (5 files)

**Files Modified**:
- `.github/workflows/ci.yml` - Weekly schedule and manual trigger
- `tests/cli/test_main.py` - Added 17 tests, moved fixtures to conftest
- `tests/integration/test_performance_regression.py` - Performance markers
- `tests/performance/test_performance.py` - Performance markers
- `README.md` - Testing guide and updated statistics

**Impact**:
- Development feedback loop: 52min → 2min (26× faster)
- CI execution time: ~8 minutes for default tests
- Coverage exceeds industry standard (85% vs typical 70-80%)
- Zero regressions, all existing tests passing

## [0.11.1] - 2025-10-25

### v0.11.1 - Usability Enhancements
**Status**: ✅ Production Ready
**Focus**: Improved daily workflow and user experience

#### Added

**Productivity Analysis** (New):
- ✅ **`clauxton morning`** - Interactive morning planning workflow
  - Shows yesterday's completed tasks
  - Suggests top 5 tasks by priority
  - Interactive task selection with automatic focus setting
  - Guides you into a productive day

- ✅ **`clauxton weekly`** - Weekly productivity summary
  - Task completion rate and velocity (tasks/week)
  - Work hours breakdown (estimated vs actual)
  - Knowledge Base growth by category
  - Priority distribution of completed tasks
  - Top 5 completed tasks with `--week` offset support
  - JSON output with `--json` flag

- ✅ **`clauxton trends`** - Productivity trends and analysis
  - Analyzes last 30 days (configurable with `--days`)
  - ASCII chart showing weekly completion trends
  - Knowledge Base focus by category
  - Priority distribution over time
  - Actionable insights based on patterns

- ✅ **`clauxton daily --json`** - JSON output for daily summary
  - Machine-readable format for integrations
  - Complete task and KB entry data

- ✅ **`clauxton stats --json`** - JSON output for project statistics
  - Machine-readable project metrics

**Enhanced Workflow Commands**:
- ✅ **`clauxton resume --yesterday`** - Enhanced resume with yesterday's work
  - Shows completed tasks from yesterday
  - Work hours summary
  - Next action suggestions with executable commands

- ✅ **`clauxton search --kb-only/--tasks-only/--files-only`** - Filtered search
  - Search specific data sources
  - Faster, more focused results

- ✅ **`clauxton task add --start`** - Add task and start immediately
  - Creates task and sets focus in one command
  - Updates status to in_progress
  - Perfect for quick task capture

- ✅ **`clauxton pause --history`** - Pause history and statistics
  - Shows interruption patterns
  - Average pause duration
  - Most common reasons
  - Recent pause history with resume status

**Daily Workflow Commands** (Existing):
- ✅ **`clauxton overview`** - Comprehensive project overview
  - Knowledge Base entries grouped by category (with icons: 🏗️ 🚫 ✅ 🔧 📋)
  - Task breakdown by status and priority
  - Shows first N entries per category (configurable with `--limit`)
  - Content previews for quick context
  - Completion percentage and next task recommendations

- ✅ **`clauxton resume`** - Project resumption context
  - Time since last activity (calculates from file modification times)
  - Last task you were working on (shows in-progress tasks)
  - Recent KB entries (last 3 with age indicators)
  - AI-suggested next steps based on current state
  - Quick command references

- ✅ **`clauxton stats`** - Project statistics and insights
  - Knowledge Base distribution by category (with bar charts)
  - Task breakdown by status and priority (visual progress bars)
  - Repository map statistics (files indexed, symbols count)
  - Completion rates and time tracking
  - Project health score (0-100%) with recommendations
  - Activity metrics and trends

**Quick Add Shortcuts** (eliminates interactive prompts):
- ✅ **`clauxton add-architecture TITLE CONTENT [--tags]`** - Quick architecture entries
- ✅ **`clauxton add-decision TITLE CONTENT [--tags]`** - Quick decision logging
- ✅ **`clauxton add-constraint TITLE CONTENT [--tags]`** - Quick constraint tracking
- ✅ **`clauxton add-pattern TITLE CONTENT [--tags]`** - Quick pattern documentation
- ✅ **`clauxton add-convention TITLE CONTENT [--tags]`** - Quick convention notes
- ✅ **`clauxton quick-task NAME [--high|--critical]`** - Quick task creation
  - Default priority: medium
  - Flags: `--high`, `--critical` for priority shortcuts
  - Examples: `clauxton quick-task "Fix bug" --high`

**Enhanced Export**:
- ✅ **`clauxton kb export --summary`** - Compact summary format
  - Single SUMMARY.md file with all entries
  - Grouped by category with icons
  - Content previews (200 chars)
  - Perfect for team onboarding and quick reference
  - Includes statistics (total entries, categories)

#### Improved

**User Experience**:
- ✅ All new commands use rich formatting (colors, emojis, progress bars)
- ✅ Consistent icon usage across commands for better visual scanning
- ✅ Smart content previews (60-200 chars depending on context)
- ✅ Time-aware displays (shows "today", "yesterday", "3 days ago")
- ✅ Actionable recommendations based on project state

**Performance**:
- ✅ Quick shortcuts avoid interactive prompts (10x faster for frequent operations)
- ✅ Overview and stats commands use efficient data grouping
- ✅ Resume command uses file system metadata for fast activity detection

#### Developer Experience

**Usability Metrics**:
- KB/Task entry creation time: **5 minutes → 10 seconds** (30x faster with quick shortcuts)
- Project context understanding: **Multiple commands → Single `overview`** (1 command vs 3+)
- Daily workflow: **Streamlined with `resume` + quick commands**
- Team onboarding: **Enhanced with `--summary` export**

**Quality**:
- ✅ All commands pass mypy strict type checking
- ✅ All commands pass ruff linting
- ✅ Consistent error handling with user-friendly messages
- ✅ Rich terminal output for better readability

#### Documentation
- ✅ Updated README with new commands and examples
- ✅ Added usage examples for all quick shortcuts
- ✅ Documented project health scoring algorithm
- ✅ Added team onboarding workflow with summary export

## [0.11.0] - 2025-10-24

### v0.11.0 - Repository Map
**Status**: ✅ Production Ready (12 Languages: Python, JavaScript, TypeScript, Go, Rust, C++, Java, C#, PHP, Ruby, Swift, Kotlin)
**Test Coverage**: 91% for intelligence (441 intelligence tests + 787 core/other tests = 1228 total)

#### Added (Week 1 - Complete)

**Repository Map - Python Support**:
- ✅ **File Indexing** (`repository_map.py`): Recursive codebase scanning
  - Respects `.gitignore` patterns with default exclusions (.git, __pycache__, .venv, etc.)
  - File categorization: source/test/config/docs/other
  - Language detection: Python, JavaScript, TypeScript, Go, Rust, Java, C/C++, and more
  - Statistics collection: by_type, by_language breakdowns
  - Performance: 1000+ files in <2 seconds
  - Storage: JSON format in `.clauxton/map/` (~10-50KB per project)

- ✅ **Symbol Extraction** (`symbol_extractor.py`): Python code analysis
  - tree-sitter parser (v0.25.2) for accurate extraction
  - ast module fallback when tree-sitter unavailable
  - Extracts: functions, classes, methods with full metadata
  - Captures: signatures, docstrings, line numbers (start/end)
  - Handles: nested functions, complex signatures, Unicode characters
  - Graceful error handling for syntax errors

- ✅ **Symbol Search** (`repository_map.py`): 3 intelligent search modes
  - **Exact mode** (default): Fast substring matching with priority scoring
    - Exact match: 100 points, starts with: 90, contains: 50, docstring: 30
    - Performance: <0.01s for 1000 symbols
  - **Fuzzy mode**: Typo-tolerant using Levenshtein distance (difflib)
    - Similarity threshold: 0.4
    - Example: "authentcate" finds "authenticate_user"
  - **Semantic mode**: TF-IDF meaning-based search
    - Requires scikit-learn (graceful fallback to exact if unavailable)
    - Searches by concept, not just text
    - Example: "user login" finds authenticate_user, verify_credentials, etc.

- ✅ **CLI Commands** (`cli/repository.py`): 3 commands with Rich UI
  - `clauxton repo index [--path PATH]` - Index repository with progress tracking
  - `clauxton repo search QUERY [--mode MODE] [--limit N]` - Search symbols
  - `clauxton repo status` - Display statistics (files, symbols, categories)
  - Rich console UI: colors, tables, progress bars
  - Formatted output with docstrings and file locations

- ✅ **MCP Tools** (`mcp/server.py`): 2 new tools (20 → 22 total)
  - `index_repository(root_path)` - Index codebase with statistics
    - Returns: files_indexed, symbols_found, duration, by_type, by_language, indexed_at
    - Error handling: nonexistent paths, indexing failures
  - `search_symbols(query, mode, limit, root_path)` - Search with 3 modes
    - Returns: count, symbols list with name/type/file/lines/docstring/signature
    - Validation: mode validation, empty results handling
    - Supports: special characters (__init__), Unicode (日本語)

#### Tests (Week 1)
- ✅ **81 intelligence tests** (92%/90% coverage):
  - 64 repository_map tests: initialization, lazy loading, data models, indexing, search, helpers, errors
  - 17 symbol_extractor tests: tree-sitter, ast fallback, edge cases
- ✅ **18 MCP tests** (comprehensive scenarios):
  - Basic: default path, custom path, statistics
  - Errors: nonexistent paths, indexing/search failures, invalid modes
  - Edge cases: empty directory, no index, limit validation, special/Unicode characters
- ✅ **Total**: 868 tests (+110), all passing
- ✅ **Quality**: mypy ✓, ruff ✓, 100% test success rate

#### Documentation (Week 1)
- ✅ **REPOSITORY_MAP_GUIDE.md** (300 lines): Complete usage guide
  - Quick start, search algorithms, use cases, performance, troubleshooting
- ✅ **mcp-server.md** (+199 lines): MCP integration documentation
  - Tool descriptions, integration workflow, performance notes, troubleshooting (12 items)
- ✅ **SESSION_15_SUMMARY.md** (553 lines): Complete Week 1 implementation record
- ✅ **README.md**: Updated with v0.11.0 features and roadmap

#### Performance (Week 1)
- Indexing: FastAPI (1,175 files) in 0.73s - **63.5% faster** than 2s target
- Search: <0.01s exact, <0.1s semantic for typical projects
- Storage: ~10-50KB JSON per project

#### Added (Week 2 - Complete)

**Multi-Language Symbol Extraction**:
- ✅ **JavaScript Support** (`symbol_extractor.py`): ES6+ features
  - tree-sitter-javascript parser
  - Extracts: classes, functions (regular + arrow), methods
  - Supports: async/await, export statements, lexical declarations
  - 23 comprehensive tests with fixtures

- ✅ **TypeScript Support** (`symbol_extractor.py`): Full type system
  - tree-sitter-typescript parser
  - Extracts: interfaces, type aliases, classes, functions, methods
  - Supports: generics, type annotations, arrow functions
  - 24 comprehensive tests with fixtures (including namespace and enum)

- ✅ **Go Support** (`symbol_extractor.py`): Complete feature set
  - tree-sitter-go parser
  - Extracts: functions, methods, structs, interfaces, type aliases
  - Supports: pointer/value receivers, generics (Go 1.18+)
  - 22 comprehensive tests with fixtures

- ✅ **Rust Support** (`symbol_extractor.py`): Full language coverage
  - tree-sitter-rust parser
  - Extracts: functions, methods, structs, enums, traits, type aliases
  - Supports: self receivers (&self, &mut self, self), impl blocks, generics
  - 29 comprehensive tests with fixtures (including trait impl, multiple impl blocks)

#### Added (Week 3 Day 5-6 - Complete)

**C++ Language Support** (Day 5):
- ✅ **C++ Support** (`symbol_extractor.py`): Complete feature set
  - tree-sitter-cpp parser
  - Extracts: functions, classes, methods, structs, namespaces
  - Supports: constructors/destructors, const/static/virtual methods, templates, operator overloading, nested namespaces
  - 28 comprehensive tests with fixtures (includes edge cases)

**Java Language Support** (Day 6):
- ✅ **Java Support** (`symbol_extractor.py`): Complete feature set
  - tree-sitter-java parser
  - Extracts: classes, interfaces, methods, enums, annotations
  - Supports: constructors, generics, static methods, abstract classes, inheritance, nested classes, multiple interfaces
  - 28 comprehensive tests with fixtures (quality reviewed)

**C# Language Support** (Day 7):
- ✅ **C# Support** (`symbol_extractor.py`): Full .NET support
  - tree-sitter-c-sharp parser
  - Extracts: classes, interfaces, methods, properties, enums, delegates, namespaces
  - Supports: constructors, async methods, static methods, generics, nested classes, qualified namespaces, abstract classes, inheritance
  - 28 extractor tests + 4 parser tests = 32 comprehensive tests (all passing)

**PHP Language Support** (Week 4 Day 8):
- ✅ **PHP Support** (`symbol_extractor.py`): Complete PHP 7.4+ support
  - tree-sitter-php parser
  - Extracts: classes, functions, methods, interfaces, traits, namespaces
  - Supports: constructors, static methods, visibility modifiers (public/private/protected), magic methods, type hints, nullable types, union types, abstract classes/methods, inheritance, trait usage, promoted constructor properties (PHP 8+), attributes (PHP 8+), enums (PHP 8.1+), match expressions (PHP 8+), final/readonly modifiers
  - 38 extractor tests + 4 parser tests = 42 comprehensive tests (all passing)
  - Coverage: 92% for symbol_extractor.py

**Ruby Language Support** (Week 4 Day 9):
- ✅ **Ruby Support** (`symbol_extractor.py`): Complete Ruby 2.7+ support
  - tree-sitter-ruby parser
  - Extracts: classes, modules, methods (instance/singleton/class), attributes (attr_reader/writer/accessor)
  - Supports: inheritance, module mixins (include/extend/prepend), nested classes/modules, private/protected methods, initialize methods, singleton methods (self.method_name, class << self), multiple method definition styles, method parameters (default/keyword arguments), empty classes
  - 29 extractor tests + 4 parser tests = 33 comprehensive tests (all passing)
  - Coverage: 91% for symbol_extractor.py, 79% for parser.py

**Swift Language Support** (Week 4 Day 10):
- ✅ **Swift Support** (`symbol_extractor.py`): Complete Swift 5.0+ support
  - py-tree-sitter-swift parser (tree-sitter-swift binding)
  - Extracts: classes, structs, enums, protocols, extensions, functions, methods, properties
  - Supports: initializers (init), static methods, computed properties, generic types, optional types (?), closures, nested types, protocol conformance, class inheritance, access modifiers (public/private/internal/fileprivate/open), method parameters (external/internal names), inheritance, empty classes/structs
  - 32 extractor tests + 4 parser tests = 36 comprehensive tests (all passing)
  - Coverage: 92% for symbol_extractor.py, 79% for parser.py

**Kotlin Language Support** (Week 5):
- ✅ **Kotlin Support** (`symbol_extractor.py`): Complete Kotlin 1.x+ support
  - tree-sitter-kotlin parser (v1.1.0, released Jan 2025)
  - Extracts: classes, data classes, sealed classes, interfaces, objects, companion objects, enums, functions, suspend functions, methods, properties
  - Supports: data classes, sealed classes, companion objects, extension functions, suspend functions (coroutines), infix functions, generic types, default parameters, enum classes, object declarations (singletons), interface declarations
  - 25 extractor tests + 4 parser tests = 29 comprehensive tests (all passing)
  - Coverage: 91% for symbol_extractor.py, 82% for parser.py

**Parser Infrastructure** (`parser.py`):
- ✅ Unified BaseParser for all languages
- ✅ Language-specific parsers: PythonParser, JavaScriptParser, TypeScriptParser, GoParser, RustParser, CppParser, JavaParser, CSharpParser, PhpParser, RubyParser, SwiftParser, KotlinParser
- ✅ Graceful fallback when tree-sitter unavailable
- ✅ 46 parser tests (4 per language except Python with 6)

#### Tests (Week 2-5)
- ✅ **441 intelligence tests** (91% coverage for symbol_extractor.py, 82% for parser.py):
  - 46 parser tests (Python, JavaScript, TypeScript, Go, Rust, C++, Java, C#, PHP, Ruby, Swift, Kotlin)
  - 13 Python symbol extraction tests
  - 23 JavaScript tests + 24 TypeScript tests
  - 22 Go tests + 29 Rust tests + 28 C++ tests + 28 Java tests + 32 C# tests + 38 PHP tests + 29 Ruby tests + 32 Swift tests + 25 Kotlin tests
  - 7 integration tests
  - 81 repository map tests
- ✅ **Quality**: All tests passing, mypy ✓, ruff ✓
- ✅ **Error Handling**: Improved logging for C++ and Java extraction failures
- ✅ **PHP 8+ Features**: Comprehensive tests for enums, match expressions, promoted properties, attributes, readonly, final
- ✅ **Ruby Features**: Comprehensive tests for module mixins, singleton methods, attr_accessor/reader/writer, nested classes/modules
- ✅ **Swift Features**: Comprehensive tests for init methods, protocols, extensions, generic types, computed properties, optional types, access modifiers, method parameters, inheritance, empty classes/structs
- ✅ **Kotlin Features**: Comprehensive tests for data classes, sealed classes, companion objects, extension functions, suspend functions, infix functions, generic types, enum classes, object declarations, interface declarations
- ✅ **Total project tests**: 1228 tests

#### Documentation (Week 2-4)
- ✅ **REPOSITORY_MAP_GUIDE.md**: Updated with all 11 supported languages
- ✅ **symbol_extractor.py**: Updated docstrings
- ✅ **WEEK2_DAY1-4_COMPLETION.md**: Complete daily implementation records
- ✅ **WEEK3_DAY5_COMPLETION.md**: C++ implementation complete report
- ✅ **WEEK3_DAY5_IMPROVEMENTS.md**: C++ quality improvement report
- ✅ **WEEK3_DAY6_QUALITY_REVIEW.md**: Java quality review report
- ✅ **WEEK3_DAY7_COMPLETION.md**: C# implementation complete report
- ✅ **WEEK4_DAY8_COMPLETION.md**: PHP implementation complete report
- ✅ **WEEK4_DAY9_COMPLETION.md**: Ruby implementation complete report
- ✅ **WEEK4_DAY10_COMPLETION.md**: Swift implementation complete report
- ✅ **README.md**: Updated roadmap (Week 4 Day 10 Complete)

#### Roadmap (Weeks 3-6)
- ✅ **Week 3 Day 5**: C++ symbol extraction (Complete)
- ✅ **Week 3 Day 6**: Java symbol extraction (Complete)
- ✅ **Week 3 Day 7**: C# symbol extraction (Complete)
- ✅ **Week 4 Day 8**: PHP symbol extraction (Complete)
- ✅ **Week 4 Day 9**: Ruby symbol extraction (Complete)
- ✅ **Week 4 Day 10**: Swift symbol extraction (Complete)
- ✅ **Week 5**: Kotlin symbol extraction (Complete)
- 📋 **Week 5-6**: CLI/MCP integration enhancements
- 📋 **Week 6**: Incremental indexing & performance optimization

#### Fixed
- **Undo Functionality Integration**: Added operation history recording to CLI commands
  - `clauxton kb add` now records operations for undo support (`clauxton/cli/main.py:195-204`)
  - `clauxton task add` now records operations for undo support (`clauxton/cli/tasks.py:97-106`)
  - Fixes issue where `clauxton undo --history` showed "No operations in history" after CLI operations
  - Enables full undo/rollback functionality for KB and Task management via CLI
  - Affected commands: `kb add`, `task add` (MCP tools already had operation recording)

#### Enhanced (UI/UX Improvements)
- **Optional Dependencies**: Tree-sitter parsers now optional for faster installation
  - Base install time: ~30 seconds (was 5-10 minutes)
  - Install only needed parsers: `pip install clauxton[parsers-python]`
  - Convenience groups: `parsers-web`, `parsers-systems`, `parsers-enterprise`, `parsers-all`
  - Updated `pyproject.toml` with 12 language-specific optional dependencies

- **Parser Missing Warnings**: User-visible warnings when language parsers unavailable
  - `clauxton repo index` now shows missing parsers with install commands
  - Example: "⚠ 5 Go files found but tree-sitter-go not installed. Install with: pip install clauxton[parsers-systems]"
  - Prevents silent file skipping during indexing

- **Quick Start Command**:
  - New `clauxton quickstart` command for one-command setup
  - Automatically runs: init → repo index → mcp setup
  - Optional flags: `--skip-mcp`, `--skip-index` for flexibility
  - Shows progress for each step (Step 1/3, Step 2/3, Step 3/3)
  - Displays final status and suggests next actions
  - Reduces new user setup time: 5 minutes → 10 seconds (30x faster)

- **Improved Onboarding**:
  - Welcome message when running `clauxton` without arguments
  - Context-aware guidance (first-time vs existing users)
  - Promotes `clauxton quickstart` as recommended setup method
  - Manual setup workflow clearly documented as alternative
  - `clauxton init` now suggests next step: `clauxton repo index`
  - Updated help messages to reflect completed phases (v0.10.0, v0.11.0)

- **Enhanced Discovery**:
  - `clauxton task import --example` shows complete YAML format example
  - `clauxton config list` now displays mode descriptions and usage examples
  - All modes explained: always (maximum safety), auto (balanced), never (maximum speed)

- **Error Message Standardization**:
  - Unified error format across all CLI commands: `⚠ [problem]. [solution]`
  - Applied to: `clauxton/cli/main.py`, `tasks.py`, `config.py`
  - Example: "⚠ .clauxton/ not found. Run 'clauxton init' first"
  - Improves clarity and consistency of error messages

- **Performance Feedback**:
  - `clauxton repo index` now shows estimated time remaining during indexing
  - Dynamic calculation based on current progress: "~2m 30s remaining"
  - Updates in real-time as files are processed
  - Helps users understand indexing duration for large codebases

- **MCP Auto-Setup**:
  - New `clauxton mcp setup` command for automatic MCP server configuration
  - Detects platform and Python environment automatically
  - Generates `.claude-plugin/mcp-servers.json` with correct settings
  - Includes `clauxton mcp status` to show current configuration
  - Simplifies MCP integration from manual JSON editing to single command

- **Project Status Dashboard**:
  - New `clauxton status` command for overall project overview
  - Displays: Repository Map (files/symbols indexed), Tasks (pending/in-progress/completed), Knowledge Base (entry count/recent), MCP Server (configuration)
  - Shows "time ago" for last updates (e.g., "2 hours ago", "3 days ago")
  - Suggests next task automatically
  - Perfect for daily standup or project health check

---

## [0.10.1] - 2025-10-22

### Fixed
- **CRITICAL**: Path vs str type incompatibility in `KnowledgeBase` and `TaskManager`
  - Now accepts both `Path` and `str` for `root_dir` parameter (clauxton/core/knowledge_base.py:59, clauxton/core/task_manager.py:45)
  - Fixes `TypeError: unsupported operand type(s) for /: 'str' and 'str'` when passing string paths
  - Affects: `KnowledgeBase()`, `TaskManager()`, `ensure_clauxton_dir()`
  - Example: `kb = KnowledgeBase('.clauxton')` now works (previously required `Path('.clauxton')`)
- Japanese text in `search-algorithm.md` example ("使い方" → "Tutorial")

### Documentation
- Added `TEST_WRITING_GUIDE.md` for contributors (comprehensive testing guide with examples)
- Replaced Japanese `technical-design.md` with English version (v2.0, updated for v0.10.0)
  - Japanese version archived at `docs/archive/planning/technical-design-ja.md`
- PyPI project page now shows updated README.md (removed Phase/beta references from v0.10.0)

### Tests
- Added 9 tests for Path/str compatibility (3 for each: `file_utils.py`, `knowledge_base.py`, `task_manager.py`)
- Test coverage maintained at 91% (767 tests total, +9 from v0.10.0)

---

## [0.10.0] - 2025-10-22

### v0.10.0 - Production Ready
**Release Date**: 2025-10-22
**Status**: 🚀 Released
**Test Coverage**: 91% (758 tests)
**Previous Version**: v0.9.0-beta

### Added

**Bulk Operations**:
- ✅ **YAML Bulk Import** (Week 1 Day 1-2): `task_import_yaml()` - Create multiple tasks in one operation
  - 20 tests, 100% backward compatible
  - Circular dependency detection, dry-run mode
- ✅ **Undo/Rollback** (Week 1 Day 3): `undo_last_operation()` - Reverse accidental operations
  - 24 tests (81% coverage), supports 7 operation types
  - History stored in `.clauxton/history/operations.yml`
  - CLI: `clauxton undo`, `clauxton undo --history`
  - MCP tools: `undo_last_operation()`, `get_recent_operations()`
- ✅ **Confirmation Prompts** (Week 1 Day 4): Threshold-based confirmation for bulk operations
  - 14 tests, prevents accidental bulk operations
  - Default threshold: 10 tasks (configurable)
  - Preview generation: task count, estimated hours, priority/status breakdown
  - Parameters: `skip_confirmation`, `confirmation_threshold`
  - Returns `status: "confirmation_required"` with preview data
  - Works with: YAML import, dry-run mode, validation errors
- ✅ **Error Recovery** (Week 1 Day 5): Transactional import with configurable error handling
  - 15 tests covering rollback/skip/abort strategies
  - `on_error="rollback"` (default): Revert all changes on any error (transactional)
  - `on_error="skip"`: Skip invalid tasks, continue with valid ones (returns `status: "partial"`)
  - `on_error="abort"`: Stop immediately on first error
  - Returns `skipped` list for skip mode
  - Integration with undo functionality
- ✅ **YAML Safety** (Week 1 Day 5): Security checks to prevent code injection
  - 10 tests covering dangerous patterns
  - Detects `!!python`, `!!exec`, `!!apply` tags
  - Detects `__import__`, `eval()`, `exec()`, `compile()` patterns
  - Blocks import before any processing (highest precedence)
  - Clear security error messages

**User Experience Improvements**:
- ✅ **Enhanced Validation** (Week 2 Day 6): Pre-Pydantic validation for better error messages
  - 32 tests (100% coverage of task_validator.py)
  - Validates: task names, duplicate IDs, duplicate names (warning), priorities, statuses, dependencies, estimated hours, file paths
  - Errors (blocking): empty name, duplicate ID, invalid priority/status, negative hours
  - Warnings (non-blocking): duplicate name, large hours (>1000), nonexistent files
  - Integration: Step 1.5 in import_yaml (after YAML parse, before Pydantic)
  - Can be bypassed: `skip_validation=True` parameter
  - Works with error recovery strategies (rollback/skip/abort)
- ✅ **Operation Logging** (Week 2 Day 7): Structured logging with daily log files
  - 47 tests (97% coverage of logger.py - 28 unit + 11 MCP + 11 CLI + 6 error handling tests)
  - Features:
    - Daily log files: `.clauxton/logs/YYYY-MM-DD.log`
    - Automatic log rotation: 30-day retention
    - JSON Lines format: Structured data for easy parsing
    - Filtering: By operation type, log level, date range
    - Secure permissions: 700 for logs directory, 600 for files
  - MCP tool: `get_recent_logs(limit, operation, level, days)`
  - CLI command: `clauxton logs [--limit N] [--operation TYPE] [--level LEVEL] [--days N] [--date YYYY-MM-DD] [--json]`
  - Log levels: debug, info, warning, error
  - Graceful handling: Skips malformed JSON lines, Unicode support
- ✅ **KB Export** (Week 2 Day 8): Generate Markdown documentation from Knowledge Base
  - 24 tests (95% coverage of KB module)
  - Category-based file generation (one .md per category)
  - ADR format for decision entries (Context, Consequences sections)
  - Standard format for other categories
  - Full Unicode support (UTF-8 encoding)
  - MCP tool: `kb_export_docs(output_dir, category)`
  - CLI command: `clauxton kb export OUTPUT_DIR [--category CATEGORY]`
  - Returns statistics: total_entries, files_created, categories
- ✅ **Progress Display + Performance Optimization** (Week 2 Day 9): Batch operations with progress reporting
  - 8 tests (98% coverage of TaskManager)
  - **`add_many(tasks, progress_callback)` method**: Single file write for all tasks
  - Progress callback support: `(current, total) -> None`
  - Comprehensive validation (duplicates, dependencies, cycles)
  - **Performance improvement**: 100 tasks in 0.2s (25x faster than 5s)
  - `import_yaml()` uses batch operation automatically
  - Backward compatible: All existing tests pass (607 total)
- ✅ **Backup Enhancement** (Week 2 Day 10): Timestamped backups with generation management
  - 22 tests (18 BackupManager + 4 yaml_utils integration)
  - **`BackupManager` class**: Centralized backup management
  - **Timestamped backups**: `filename_YYYYMMDD_HHMMSS_microseconds.yml`
  - **Generation limit**: Keep latest 10 backups per file (configurable via `max_generations`)
  - **Automatic cleanup**: Old backups deleted when limit exceeded
  - **Backup directory**: `.clauxton/backups/` (auto-created with 700 permissions)
  - **Legacy compatibility**: `.bak` files still created for backward compatibility
  - **Helper methods**: `get_latest_backup()`, `count_backups()`, `list_backups()`, `restore_backup()`
  - **Performance**: Backup creation < 100ms (tested with 100-entry files)
  - **File permissions**: Backups stored with 600 (owner read/write only)
  - Integrated into `yaml_utils.write_yaml()` - all YAML writes create backups automatically
- ✅ **Error Message Improvement** (Week 2 Day 10): Actionable error messages with suggestions
  - Enhanced all exception classes with detailed docstrings and examples
  - `ValidationError`: Include specific field and fix suggestion
  - `NotFoundError`: List available IDs and how to list them
  - `DuplicateError`: Suggest update or use different ID
  - `CycleDetectedError`: Show cycle path and how to break it
  - All error handlers use new format with context + suggestion + commands
- ✅ **Configurable Confirmation Mode** (Week 2 Day 11): Customizable Human-in-the-Loop level
  - 29 tests (12 core + 17 CLI tests, 94% coverage of confirmation_manager.py)
  - Features:
    - 3 confirmation modes: "always" (100% HITL), "auto" (75% HITL, default), "never" (25% HITL)
    - Configurable thresholds per operation type (task_import, task_delete, kb_delete, kb_import)
    - Configuration stored in `.clauxton/config.yml`
    - Automatic defaults: task_import=10, task_delete=5, kb_delete=3, kb_import=5
  - Core: `ConfirmationManager` class with `get_mode()`, `set_mode()`, `should_confirm()`, `get_threshold()`, `set_threshold()`
  - CLI commands:
    - `clauxton config set confirmation_mode [always|auto|never]`
    - `clauxton config get confirmation_mode`
    - `clauxton config set task_import_threshold N`
    - `clauxton config list` - View all configuration
  - Safety: Invalid mode auto-resets to "auto", malformed config recovery
  - Persistence: Configuration saved across sessions
  - Use cases:
    - Team development: "always" mode for maximum safety
    - Individual development: "auto" mode for balanced workflow (default)
    - Rapid prototyping: "never" mode with undo capability

**📚 Documentation** (13 comprehensive docs):
- **NEW**: `docs/SESSION_8_SUMMARY.md` - KB Export feature (Week 1 Day 4)
- **NEW**: `docs/SESSION_9_SUMMARY.md` - YAML Safety (Week 1 Day 5)
- **NEW**: `docs/SESSION_10_SUMMARY.md` - MCP Undo Tools (Week 2 Day 1)
- **NEW**: `docs/SESSION_11_SUMMARY.md` - Enhanced Validation (Week 2 Day 6)
- **NEW**: `docs/SESSION_11_GAP_ANALYSIS.md` - Gap analysis and v0.10.1 planning
- **NEW**: `docs/ERROR_HANDLING_GUIDE.md` - Complete error resolution guide
- **NEW**: `docs/MIGRATION_v0.10.0.md` - Migration guide from v0.9.0-beta
- **NEW**: `docs/configuration-guide.md` - Configuration reference
- **NEW**: `docs/troubleshooting.md` - Comprehensive troubleshooting (1,300 lines!)
- Existing: `docs/YAML_TASK_FORMAT.md` - YAML format specification
- Existing: `docs/kb-export-guide.md` - KB export guide
- Existing: `docs/logging-guide.md` - Logging system guide
- Existing: `docs/performance-guide.md` - Performance optimization guide
- Existing: `docs/backup-guide.md` - Backup management guide
- Updated: `README.md` - v0.10.0 features, 17 MCP tools, 758 tests
- Updated: `CLAUDE.md` - Integration philosophy, best practices (7,000+ lines!)
- Updated: `CHANGELOG.md` - Complete v0.10.0 changelog

**🧪 Quality** (Session 11 Complete):
- **+368 tests** (390 → **758 tests**)
- **91% overall coverage** (target: 80%, +11% over)
  - **99% MCP server coverage** (target: 60%, +39% over)
  - **84-100% CLI coverage** (target: 40%, +44% over)
  - **87-96% core modules** (KB: 95%, TaskManager: 98%, Search: 86%)
  - **80-85% utils modules** (on target)
- **17 MCP tools** (15 → 17, +2 tools: undo_last_operation, get_recent_operations)
- **CI/CD**: 3 parallel jobs (test, lint, build) ~52s total
- Integration scenarios: Happy path, error recovery, undo flow, confirmation mode, performance testing

**Expected Impact**:
- User operations: 10 commands → 0 (fully automatic)
- Task registration: 5 minutes → 10 seconds (30x faster)
- Error risk: 10-20% → <1%
- Human-in-the-Loop: 50% → 75-100% (configurable)
- Claude philosophy alignment: 70% → 95%

See `docs/design/REVISED_ROADMAP_v0.10.0.md` for complete roadmap.

---

### Phase 3 Features (v0.11.0 and beyond)
- Interactive Mode: Conversational YAML generation
- Project Templates: Pre-built patterns for common projects
- Repository Map: Automatic codebase indexing (like Aider/Devin)
- Web Dashboard: Visual KB/Task/Conflict management

---

## [0.9.0-beta] - 2025-10-20 (Week 12 Complete: Conflict Detection)

### Added - Conflict Detection (Phase 2 - Week 12)

#### Core Features
- **ConflictDetector Engine**: File-based conflict prediction system
  - Detects file overlap between tasks (O(n²) pairwise comparison)
  - Risk scoring: LOW (<40%), MEDIUM (40-70%), HIGH (>70%)
  - Only checks `in_progress` tasks to avoid false positives

- **Safe Execution Order**: Topological sort + conflict-aware scheduling
  - Respects task dependencies (DAG validation)
  - Minimizes file conflicts
  - Considers task priorities (critical > high > medium > low)

- **File Availability Checking**: Pre-edit conflict detection
  - Check which tasks are editing specific files
  - Supports multiple file checking with wildcard patterns

#### CLI Commands (3 new)
- `clauxton conflict detect <TASK_ID> [--verbose]`: Check conflicts for a task
- `clauxton conflict order <TASK_IDS...> [--details]`: Get safe execution order
- `clauxton conflict check <FILES...> [--verbose]`: Check file availability

#### MCP Tools (3 new)
- `detect_conflicts`: Detect conflicts for a task
- `recommend_safe_order`: Get optimal task order
- `check_file_conflicts`: Check file availability

#### Testing & Quality (Week 12 Day 6-8)
- **390 tests total** (+38 error resilience tests): 52 conflict-related tests including:
  - 22 CLI conflict command tests (detect, order, check)
  - 13 integration workflow tests (NEW in Day 7)
  - 9 MCP conflict tool tests (NEW in Day 7)
  - 26 core ConflictDetector tests
  - Edge cases: empty files, nonexistent files, multiple in-progress tasks
  - Risk level validation (LOW/MEDIUM/HIGH)
  - Completed task filtering
  - Priority-based ordering
  - Special characters in file paths (Unicode, spaces)
  - CLI output format regression test (NEW in Day 7)
  - Error handling and boundary conditions

- **38 Error Resilience Tests** (NEW in Day 8):
  - `tests/core/test_error_resilience.py` (24 tests): YAML errors, missing resources, corrupted data, validation errors
  - `tests/cli/test_error_handling.py` (17 tests): CLI error handling, uninitialized project, input validation

- **Code Coverage**: 94% overall, 92-94% for CLI modules (+1-3% improvement)
- **Integration Tests**: 13 end-to-end workflow scenarios
  - Pre-Start Check workflow
  - Sprint Planning with priorities
  - File Coordination lifecycle
  - MCP-CLI consistency validation
  - Error recovery scenarios
  - Performance testing with 20+ tasks
- **Performance**: <500ms for conflict detection (10 tasks), <1s for ordering (20 tasks)

#### Documentation (Week 12 Day 6-8)
- **conflict-detection.md**: Complete 35KB+ guide
  - Python API, MCP tools, CLI commands
  - Algorithm details, performance tuning
  - Comprehensive troubleshooting section (10 detailed issues, NEW in Day 7)
    - No conflicts detected (with debug steps)
    - False positives explanation
    - Risk score calculation with examples
    - Safe order logic
    - Unicode/special characters handling
    - Performance issues with benchmarks
    - MCP tool errors
    - CLI command debugging
    - Vague recommendations analysis

- **quick-start.md**: Added Conflict Detection Workflow section
  - 3 CLI command examples with real output
  - Risk level explanations (🔴 HIGH, 🟡 MEDIUM, 🔵 LOW)
  - 3 common workflows (Pre-Start Check, Sprint Planning, File Coordination)

- **README.md**: Updated with Phase 2 completion
  - ⚠️ Conflict Detection feature highlighted
  - Phase 2 status: Complete (100%)
  - Test count: 390 tests
  - MCP tools: 15 total

- **RELEASE_NOTES_v0.9.0-beta.md**: Migration Guide expanded (NEW in Day 8)
  - Comprehensive upgrade instructions (v0.8.0 → v0.9.0-beta)
  - Workflow updates (Solo/Team/Sprint Planning)
  - Troubleshooting and rollback guide
  - ~5KB of user documentation

### Technical Details
- **Architecture**: ConflictDetector as standalone module in `clauxton/core/`
- **Algorithm**: Pairwise task comparison with early termination
- **Risk Calculation**: File overlap count ÷ total unique files
- **MCP Integration**: 15 tools total (12 existing + 3 new)

### Performance Benchmarks
- Conflict detection: <500ms (10 tasks)
- Safe order recommendation: <1s (20 tasks with dependencies)
- File availability check: <100ms (10 files)

---

## [Week 11] - 2025-10-17 to 2025-10-18

### Added (Week 11: Documentation & Community Setup)

#### Documentation (Days 1-2, 5-6)
- **Tutorial**: `docs/tutorial-first-kb.md` (30-minute complete beginner guide)
- **Use Cases**: `docs/use-cases.md` (10 real-world scenarios with implementation guides)
  - 5 detailed core use cases (Solo Dev, Team, OSS, Enterprise, Student)
  - 5 additional use cases (API, DevOps, Security, Product, Microservices)
  - Before/After comparisons with ROI calculations
  - 50+ code examples
- **Enhanced Guides**:
  - `docs/quick-start.md` - Added Advanced Usage section (+260 lines)
  - `docs/task-management-guide.md` - Added Real-World Workflows section (+290 lines)
  - `docs/troubleshooting.md` - Added platform-specific issues (+609 lines)
    * Windows, macOS, Linux troubleshooting
    * Common error messages explained
    * Advanced debugging techniques
    * Extended FAQ (10 new questions)

#### Community Infrastructure (Day 4)
- **GitHub Templates**:
  - `.github/ISSUE_TEMPLATE/bug_report.yml` - Structured bug reports
  - `.github/ISSUE_TEMPLATE/feature_request.yml` - Use case-focused feature requests
  - `.github/ISSUE_TEMPLATE/question.yml` - Q&A template
  - `.github/pull_request_template.md` - 22-item PR checklist
- **Contributing Guide Enhancement**:
  - `CONTRIBUTING.md` - Added CI/CD Workflow section (+243 lines)
    * Local CI checks guide
    * Troubleshooting for CI failures
    * Coverage requirements (90% minimum, 94% current)

#### CI/CD Automation (Day 3)
- **GitHub Actions Workflow** (`.github/workflows/ci.yml`):
  - Test job (Python 3.11 & 3.12, 267 tests, ~42-44s)
  - Lint job (ruff + mypy, ~18s)
  - Build job (twine validation, ~17s)
  - Total: ~44 seconds (parallel execution)
- **Type Checking Configuration**:
  - `mypy.ini` - Strict type checking with missing import handling
- **README Badges**:
  - CI status badge
  - Codecov coverage badge

### Changed (Week 11)
- **README.md**:
  - Status: Alpha → Production Ready (v0.8.0)
  - Added PyPI installation as primary method
  - Added CI and Codecov badges
  - Updated documentation links (Tutorial, Use Cases)
- **Documentation Structure**:
  - Total docs: 22 → 23 markdown files
  - Total size: ~394 KB → ~520 KB (+32% growth)

### Fixed (Week 11)
- **Tests**:
  - `test_version_command` - Updated expected version (0.1.0 → 0.8.0)
- **CI/CD**:
  - 36 ruff linting errors (unused imports, line length, whitespace)
  - 81 mypy type errors (missing type stubs for third-party libs)
  - Deprecated `upload-artifact@v3` → `v4`

### Notes (Week 11)
- **Test Coverage**: Maintained at 94% (267 tests, all passing)
- **CI/CD**: All checks passing (~44s total runtime)
- **Documentation Quality**: A+ (all recommended docs complete)
- **Community Ready**: Professional contribution infrastructure

### Planned

#### Phase 2: Conflict Prevention (Week 12+)
- Conflict Detector (pre-merge risk analysis)
- Drift Detection
- Lifecycle Hooks
- Event Logging
- Conflict Detector Subagent

---

## [0.8.0] - 2025-10-19 (Week 9-10: TF-IDF Search)

### Added
- **TF-IDF Search Engine** (`clauxton/core/search.py`):
  - Relevance-based search using scikit-learn TfidfVectorizer
  - Cosine similarity scoring for result ranking
  - Automatic stopword filtering (English)
  - N-gram support (unigrams and bigrams)
  - Category filtering with dynamic index rebuilding
  - Graceful degradation to simple search when scikit-learn unavailable
- **Fallback Search** (`knowledge_base.py`):
  - Simple keyword matching with weighted scoring (title: 2.0, tag: 1.5, content: 1.0)
  - Automatic fallback detection when TF-IDF unavailable
  - Consistent API with TF-IDF search
- **Dependencies**:
  - `scikit-learn>=1.3.0` - TF-IDF vectorization (optional)
  - `numpy>=1.24.0` - Required by scikit-learn
- **Test Suite Expansion**:
  - 18 new tests (265 total, up from 247)
  - `_simple_search` fallback method: 0% → ~95% coverage
  - Edge cases: stopwords, Unicode, special characters, error handling
  - scikit-learn unavailable scenario testing
- **Documentation**:
  - `docs/search-algorithm.md` - Complete TF-IDF algorithm explanation (350 lines)
  - README.md - TF-IDF features, dependencies, search examples
  - `docs/quick-start.md` - Search section expansion with TF-IDF usage guide

### Changed
- **Knowledge Base Search**:
  - Search results now ranked by relevance (TF-IDF scores)
  - More relevant entries appear first
  - Empty queries return empty results (consistent behavior)
- **MCP kb_search Tool**:
  - Returns relevance-scored results
  - Backward compatible (same API signature)
- **Test Coverage**:
  - Overall coverage: 92% → 94%
  - `clauxton/core/knowledge_base.py`: 85% → 96%
  - `clauxton/core/search.py`: 83% → 86% (new file)

### Fixed
- Search index rebuild order (now rebuilds before cache invalidation)
- Empty query handling (consistent empty results across both search methods)
- Long content search compatibility with TF-IDF (realistic test data)

### Performance
- Small KB (< 50 entries): Search < 5ms, Indexing < 10ms
- Medium KB (50-200 entries): Search < 10ms, Indexing < 50ms
- Large KB (200+ entries): Search < 20ms, Indexing < 200ms

### Notes
- **Backward Compatible**: Existing search functionality works unchanged
- **Optional Dependency**: scikit-learn is optional; automatic fallback to simple search
- **Production Ready**: 94% test coverage, all edge cases tested

---

## [0.1.0] - TBD (Phase 0 Target)

### Added
- Initial project structure
- Pydantic data models:
  - `KnowledgeBaseEntry` with validation
  - `KnowledgeBaseConfig`
- Knowledge Base manager (`clauxton/core/knowledge_base.py`):
  - `add()` - Add KB entry
  - `search()` - Search with keyword/category/tag filtering
  - `get()` - Retrieve entry by ID
  - `update()` - Update entry with versioning
  - `delete()` - Soft delete
  - `list_all()` - List all entries
- YAML utilities with atomic write and backup
- File utilities with secure permissions (700/600)
- CLI commands:
  - `clauxton init` - Initialize `.clauxton/` directory
  - `clauxton kb add` - Add Knowledge Base entry (interactive)
  - `clauxton kb search <query>` - Search Knowledge Base
  - `clauxton kb list` - List all KB entries
- Basic MCP Server (`clauxton/mcp/kb_server.py`):
  - Health check endpoint
  - Tool registration infrastructure
- Unit tests:
  - `tests/core/test_models.py`
  - `tests/core/test_knowledge_base.py`
  - `tests/utils/test_yaml_utils.py`
  - `tests/cli/test_main.py`
- Integration tests:
  - End-to-end workflow (init → add → search)
- Documentation:
  - `README.md` - Project overview
  - `docs/quick-start.md` - Quick start guide
  - `docs/installation.md` - Installation instructions
  - `docs/project-plan.md` - Market analysis & strategy
  - `docs/requirements.md` - Functional & non-functional requirements
  - `docs/technical-design.md` - Architecture & implementation details
  - `docs/roadmap.md` - 16-week development roadmap
  - `docs/phase-0-plan.md` - Detailed Phase 0 plan
  - `CONTRIBUTING.md` - Contribution guidelines
  - `CODE_OF_CONDUCT.md` - Code of Conduct
- GitHub templates:
  - `.github/ISSUE_TEMPLATE/bug_report.md`
  - `.github/ISSUE_TEMPLATE/feature_request.md`
  - `.github/PULL_REQUEST_TEMPLATE.md`
- Development setup:
  - `pyproject.toml` with dependencies
  - `.gitignore` for Python projects
  - MIT License

### Changed
- N/A (initial release)

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- File permissions set to 700 (directories) and 600 (files)
- YAML schema validation on read/write
- Input sanitization via Pydantic validators

---

## [0.0.1] - 2025-10-19 (Project Inception)

### Added
- Project structure initialization
- Basic package files
- Planning documentation (Japanese versions)
- Repository setup at `/home/kishiyama-n/workspace/projects/clauxton/`

---

## Format Guide

### Types of Changes
- **Added** - New features
- **Changed** - Changes to existing functionality
- **Deprecated** - Soon-to-be removed features
- **Removed** - Removed features
- **Fixed** - Bug fixes
- **Security** - Vulnerability fixes

### Version Format
- **MAJOR** - Breaking changes (e.g., 1.0.0 → 2.0.0)
- **MINOR** - New features (e.g., 0.1.0 → 0.2.0)
- **PATCH** - Bug fixes (e.g., 0.1.0 → 0.1.1)

---

**Note**: This changelog is maintained manually. Contributors should update this file when making significant changes as part of their pull requests.

[Unreleased]: https://github.com/nakishiyaman/clauxton/compare/v0.8.0...HEAD
[0.8.0]: https://github.com/nakishiyaman/clauxton/releases/tag/v0.8.0
[0.1.0]: https://github.com/nakishiyaman/clauxton/releases/tag/v0.1.0
[0.10.0]: https://github.com/nakishiyaman/clauxton/compare/v0.9.0...v0.10.0
[0.9.0-beta]: https://github.com/nakishiyaman/clauxton/compare/v0.8.0...v0.9.0
[0.0.1]: https://github.com/nakishiyaman/clauxton/releases/tag/v0.0.1
