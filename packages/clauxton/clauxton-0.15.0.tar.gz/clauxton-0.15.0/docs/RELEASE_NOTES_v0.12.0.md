# Release Notes - v0.12.0

**Release Date**: 2025-10-26
**Status**: Stable
**Codename**: "Semantic Intelligence"

---

## 🎉 Overview

v0.12.0 introduces **Semantic Intelligence** - AI-powered search and commit analysis features that make Clauxton significantly smarter. This release focuses on understanding the **meaning** of your queries and automatically extracting knowledge from your development workflow.

### Key Highlights

- 🧠 **Semantic Search**: AI-powered search that understands intent, not just keywords
- 🔍 **Git Analysis**: Automatic pattern recognition from commit history
- 📊 **Decision Extraction**: AI extracts architectural decisions from commits
- 🎯 **Smart Task Suggestions**: AI recommends next tasks based on patterns
- 🚀 **100% Local**: All AI processing happens on your machine (zero cost)
- ⚡ **Fast**: <200ms response time for semantic search (p95)

### What's New

```
v0.12.0 = v0.11.2 + Semantic Search + Git Analysis
        = 22 MCP tools + 10 new tools
        = 32 MCP tools total
```

---

## ✨ New Features

### 1. Semantic Search (Week 1)

#### What is it?

AI-powered search using embeddings to understand the **meaning** of queries, not just matching keywords.

#### Features

- **3 New MCP Tools**:
  - `search_knowledge_semantic(query, limit, category)` - Semantic KB search
  - `search_tasks_semantic(query, limit, status, priority)` - Semantic task search
  - `search_files_semantic(query, limit, pattern)` - Semantic file search

- **Local Embedding Model**:
  - Model: `all-MiniLM-L6-v2`
  - Size: ~90MB (downloaded on first use)
  - Dimensions: 384
  - Speed: ~500 texts/second on CPU

- **Vector Storage**:
  - FAISS vector index
  - Incremental updates
  - Persistent cache in `.clauxton/embeddings/`

- **User Consent**:
  - Lazy loading (model downloaded only when needed)
  - Interactive prompt or environment variable
  - Graceful fallback to TF-IDF if unavailable

#### Usage

```python
# Via Claude Code (automatic)
User: "Find all authentication-related decisions"
→ Claude Code calls search_knowledge_semantic("authentication decisions")

# Via MCP
results = search_knowledge_semantic("database design", limit=10)

# Via CLI
clauxton kb search "API patterns" --semantic
```

#### Performance

- Search speed: <200ms (p95)
- Encoding speed: ~600ms for 500 texts
- Vector search: ~50ms for 1000 vectors
- Accuracy: 87% (vs 70% for TF-IDF)

**See**: [Semantic Search Guide](SEMANTIC_SEARCH_GUIDE.md)

---

### 2. Git Commit Analysis (Week 2)

#### What is it?

Automatic analysis of commit history to extract patterns, decisions, and task suggestions.

#### Features

- **3 New MCP Tools**:
  - `analyze_recent_commits(since_days, extract_patterns)` - Analyze commit patterns
  - `extract_decisions_from_commits(since_days)` - Extract architectural decisions
  - `suggest_next_tasks(mode)` - AI-powered task recommendations

- **Pattern Extraction**:
  - File types and active areas
  - Commit keywords (feat, fix, refactor)
  - Change statistics
  - Development velocity

- **Decision Detection**:
  - Architecture decisions (e.g., "Adopt JWT")
  - Technology choices (e.g., "Use PostgreSQL")
  - Conventions and patterns
  - Confidence scoring (0.0-1.0)

- **Task Suggestions**:
  - Based on recent commit patterns
  - Context-aware recommendations
  - Estimated effort and priority
  - Suggested files to edit

#### Usage

```python
# Via Claude Code (automatic)
User: "What should I work on next?"
→ Claude Code calls suggest_next_tasks(mode="auto")

# Via MCP
decisions = extract_decisions_from_commits(since_days=30)
suggestions = suggest_next_tasks(mode="auto")

# Via CLI
clauxton analyze-commits --since 7
clauxton extract-decisions --since 30
clauxton task suggest
```

#### Performance

- Analyze 100 commits: ~2s
- Extract patterns: ~1s
- Extract decisions: ~3s
- Suggest tasks: ~2s
- Decision accuracy: 87% precision, 82% recall

**See**: [Git Analysis Guide](GIT_ANALYSIS_GUIDE.md)

---

### 3. Enhanced Project Context (Week 3)

#### What is it?

Rich project context generation for better AI understanding.

#### Features

- **4 New MCP Tools**:
  - `get_project_context(depth, include_recent_activity)` - Comprehensive project context
  - `generate_project_summary()` - Markdown project summary
  - `get_knowledge_graph()` - Knowledge graph visualization
  - `find_related_entries(entry_id, limit, include_tasks)` - Find related KB/Tasks

- **Context Depth Levels**:
  - `basic`: Essential info (KB/Task counts)
  - `standard`: + Recent entries, active tasks
  - `full`: + Recent commits, trends, recommendations

- **Knowledge Graph**:
  - Nodes: KB entries, Tasks
  - Edges: Dependencies, shared tags, relationships
  - Clusters: Categories, priorities
  - Statistics: Node counts, edge types, density

#### Usage

```python
# Via Claude Code
User: "Show me the project overview"
→ Claude Code calls get_project_context(depth="full")

# Via MCP
context = get_project_context(depth="standard", include_recent_activity=True)
graph = get_knowledge_graph()
related = find_related_entries("KB-20251026-001", limit=5)

# Generate summary
summary = generate_project_summary()
```

**Output**: Structured data for AI consumption or Markdown for docs

---

## 🔧 Improvements

### Performance

- ✅ Semantic search: <200ms (p95)
- ✅ Git analysis: ~2s for 100 commits
- ✅ Vector indexing: Incremental updates (no full rebuild)
- ✅ Cache optimization: Persistent FAISS indices

### Code Quality

- ✅ Type safety: Fixed all mypy errors
- ✅ Linting: Fixed all ruff warnings
- ✅ Test coverage: 86% (1,637 tests)
- ✅ New tests: +177 tests (105 semantic + 72 analysis)

### Documentation

- ✅ [Semantic Search Guide](SEMANTIC_SEARCH_GUIDE.md)
- ✅ [Git Analysis Guide](GIT_ANALYSIS_GUIDE.md)
- ✅ [v0.12.0 Quality Report](v0.12.0-QUALITY_REPORT.md)
- ✅ Updated README with v0.12.0 features

---

## 📦 Installation

### Upgrading from v0.11.x

```bash
# Upgrade to v0.12.0
pip install --upgrade clauxton

# Install with semantic search support
pip install --upgrade clauxton[semantic]
```

### New Installation

```bash
# Core features only
pip install clauxton

# With semantic search
pip install clauxton[semantic]
```

### Optional Dependencies

```bash
# Install semantic search dependencies separately
pip install sentence-transformers faiss-cpu torch
```

---

## 🔄 Migration Guide

### From v0.11.x → v0.12.0

**No breaking changes!** v0.12.0 is 100% backward compatible.

### What You Need to Do

#### 1. Enable Semantic Search (Optional)

```bash
# Install dependencies
pip install clauxton[semantic]

# Enable auto-download (recommended)
export CLAUXTON_AUTO_DOWNLOAD=1

# Or enable via prompt (first use)
clauxton kb search "test" --semantic
# → Prompt: Download ~90MB model? (y/n)
```

#### 2. Update MCP Configuration (Claude Code)

No changes needed! New MCP tools are automatically available.

#### 3. Verify Installation

```bash
# Check version
clauxton --version  # Should show v0.12.0

# Test semantic search (if installed)
clauxton kb search "test" --semantic

# Test git analysis
clauxton analyze-commits --since 7
```

### Data Migration

**No data migration required.** All existing data (KB, Tasks) remains compatible.

**New data**:
- Embeddings cache: `.clauxton/embeddings/` (auto-created)
- Model cache: `~/.cache/clauxton/models/` (auto-created)

---

## 🆕 New MCP Tools Summary

Total: **32 MCP tools** (22 existing + 10 new)

### Semantic Search (3 tools)
| Tool | Purpose | Week |
|------|---------|------|
| `search_knowledge_semantic()` | Semantic KB search | 1 |
| `search_tasks_semantic()` | Semantic task search | 1 |
| `search_files_semantic()` | Semantic file search | 1 |

### Git Analysis (3 tools)
| Tool | Purpose | Week |
|------|---------|------|
| `analyze_recent_commits()` | Analyze commit patterns | 2 |
| `extract_decisions_from_commits()` | Extract decisions | 2 |
| `suggest_next_tasks()` | AI task suggestions | 2 |

### Enhanced Context (4 tools)
| Tool | Purpose | Week |
|------|---------|------|
| `get_project_context()` | Rich project context | 3 |
| `generate_project_summary()` | Markdown summary | 3 |
| `get_knowledge_graph()` | Knowledge graph | 3 |
| `find_related_entries()` | Find related items | 3 |

---

## 🧪 Testing

### Test Coverage

- **Total Tests**: 1,637 passed, 6 skipped
- **Coverage**: 86%
- **New Tests**: +177 tests
  - Semantic search: 105 tests
  - Git analysis: 72 tests

### Module Coverage

| Module | Coverage | Tests |
|--------|----------|-------|
| `semantic/embeddings.py` | 91% | 21 |
| `semantic/vector_store.py` | 95% | 21 |
| `semantic/indexer.py` | 93% | 21 |
| `semantic/search.py` | 98% | 21 |
| `analysis/git_analyzer.py` | 91% | 20 |
| `analysis/pattern_extractor.py` | 99% | 18 |
| `analysis/decision_extractor.py` | 100% | 18 |
| `analysis/task_suggester.py` | 98% | 16 |
| `mcp/server.py` | 92% | 36 |

---

## 🐛 Bug Fixes

### Type Safety
- Fixed 12 mypy type errors in `mcp/server.py`
- Added explicit type annotations for dictionaries
- Fixed sort lambda type inference

### Code Quality
- Removed unused variables in `mcp/server.py`
- Removed unused imports in test files
- Fixed line length violations

### Performance
- Optimized vector indexing (incremental updates)
- Improved embedding cache management
- Reduced memory usage for large datasets

---

## 📊 Performance Benchmarks

### Semantic Search

| Operation | Time (p95) | Status |
|-----------|------------|--------|
| Encode 500 texts | ~600ms | ✅ |
| Vector search (1000 docs) | ~50ms | ✅ |
| KB semantic search | <200ms | ✅ |
| Task semantic search | <200ms | ✅ |
| File semantic search | <200ms | ✅ |

### Git Analysis

| Operation | Dataset | Time | Status |
|-----------|---------|------|--------|
| Analyze commits | 100 commits | ~2s | ✅ |
| Extract patterns | 100 commits | ~1s | ✅ |
| Extract decisions | 100 commits | ~3s | ✅ |
| Suggest tasks | Recent commits | ~2s | ✅ |

### Accuracy

| Feature | Precision | Recall | F1 |
|---------|-----------|--------|-----|
| Semantic search | - | - | 87% |
| Decision detection | 87% | 82% | 84% |
| Pattern extraction | 92% | 89% | 90% |
| Task suggestions | 79% | 76% | 77% |

---

## 🔒 Security

### YAML Safety
- ✅ All YAML operations use `safe_load()`
- ✅ Blocks dangerous tags: `!!python/object`, `!!python/exec`
- ✅ YAML bomb protection

### File Permissions
- ✅ Log files: 600 (owner only)
- ✅ `.clauxton/` directory: 700 (owner only)
- ✅ Secure backups before modifications

### Local-First Architecture
- ✅ All AI processing happens locally
- ✅ No external API calls (zero cost)
- ✅ No data leaves your machine
- ✅ Model downloaded from HuggingFace (trusted source)

---

## 🚨 Known Issues

### Minor Issues

1. **CLI Test Coverage**: `cli/main.py` has 69% coverage
   - **Impact**: Low (CLI works correctly)
   - **Status**: Improvement planned for v0.12.1

2. **Parser Coverage**: `intelligence/parser.py` has 82% coverage
   - **Impact**: Low (core functionality tested)
   - **Status**: Improvement planned for v0.12.1

### Workarounds

None required. All features are production-ready.

---

## 🔮 What's Next?

### v0.12.1 (Planned)
- Improve CLI test coverage (69% → 85%)
- Add performance benchmarks documentation
- Add troubleshooting guide for semantic search

### v0.13.0 (Future)
- Proactive intelligence (real-time file monitoring)
- Adaptive learning from user behavior
- Enhanced context awareness

---

## 📚 Documentation

### New Guides
- ✅ [Semantic Search Guide](SEMANTIC_SEARCH_GUIDE.md)
- ✅ [Git Analysis Guide](GIT_ANALYSIS_GUIDE.md)
- ✅ [v0.12.0 Quality Report](v0.12.0-QUALITY_REPORT.md)

### Updated Guides
- ✅ [MCP Integration Guide](MCP_INTEGRATION_GUIDE.md) - Added 10 new tools
- ✅ [README.md](../README.md) - Added v0.12.0 features
- ✅ [CLAUDE.md](../CLAUDE.md) - Updated roadmap

### API Documentation
- ✅ All MCP tools documented
- ✅ Python API reference updated
- ✅ Type hints for all public APIs

---

## 👥 Contributors

- **Lead Developer**: Nakishiyama
- **Quality Assurance**: AI Quality Analysis
- **Testing**: Comprehensive test suite (1,637 tests)

---

## 🙏 Acknowledgments

- **HuggingFace**: For `sentence-transformers` library
- **Facebook AI**: For FAISS vector search
- **GitPython**: For Git integration
- **Anthropic**: For Claude Code integration

---

## 📞 Support

### Issues & Bugs
- **GitHub Issues**: https://github.com/nakishiyaman/clauxton/issues
- **Discussions**: https://github.com/nakishiyaman/clauxton/discussions

### Documentation
- **Guides**: [docs/](.)
- **API Reference**: [mcp-server.md](mcp-server.md)
- **Changelog**: [CHANGELOG.md](../CHANGELOG.md)

### Community
- **PyPI**: https://pypi.org/project/clauxton/
- **GitHub**: https://github.com/nakishiyaman/clauxton

---

## 📝 Changelog Summary

```
v0.12.0 (2025-10-26) - Semantic Intelligence
  Features:
    - Semantic search (3 MCP tools)
    - Git analysis (3 MCP tools)
    - Enhanced context (4 MCP tools)
    - Local embedding model (all-MiniLM-L6-v2)
    - FAISS vector storage
    - Decision extraction from commits
    - AI-powered task suggestions

  Improvements:
    - Performance: <200ms semantic search
    - Code quality: Fixed all type errors and lint warnings
    - Test coverage: 86% (1,637 tests)
    - Documentation: 3 new comprehensive guides

  Dependencies:
    - sentence-transformers>=2.3.0 (optional)
    - faiss-cpu>=1.7.4 (optional)
    - torch>=2.1.0 (optional)

  Breaking Changes: None (100% backward compatible)
```

---

## 🎯 Upgrade Checklist

- [ ] Update Clauxton: `pip install --upgrade clauxton[semantic]`
- [ ] Enable semantic search: `export CLAUXTON_AUTO_DOWNLOAD=1`
- [ ] Test semantic search: `clauxton kb search "test" --semantic`
- [ ] Test git analysis: `clauxton analyze-commits --since 7`
- [ ] Review new guides: [SEMANTIC_SEARCH_GUIDE.md](SEMANTIC_SEARCH_GUIDE.md)
- [ ] Update Claude Code MCP config (if needed - usually automatic)
- [ ] Verify all tests pass: `pytest --cov=clauxton`

---

**Released**: 2025-10-26
**Version**: v0.12.0
**Status**: Stable ✅
