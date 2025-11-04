# Clauxton Development Roadmap

This document outlines the detailed development roadmap for Clauxton from v0.12.0 onwards.

## Completed Phases

### Phase 0: Foundation (Complete - v0.7.0)
- Knowledge Base CRUD operations
- YAML storage with atomic writes
- CLI interface
- Basic search functionality

### Phase 1: Core Engine (Complete - v0.8.0)
- TF-IDF relevance search
- Task Management with DAG validation
- Auto-dependency inference
- MCP Server (12 tools)
- scikit-learn integration

### Phase 2: Conflict Detection (Complete - v0.9.0-beta)
- File overlap detection
- Risk scoring (LOW/MEDIUM/HIGH)
- Safe execution order recommendations
- 3 CLI commands: `clauxton conflict detect/order/check`
- 3 MCP tools (15 tools total)

### Phase 3: Advanced Workflows (Complete - v0.10.0)
- Bulk task operations (YAML import)
- Undo/History system (24 tests, 81% coverage)
- Human-in-the-Loop with configurable confirmation modes
- KB export to Markdown
- 7 new MCP tools (22 total)

### Phase 3.5: Repository Intelligence (Complete - v0.11.0)
- Multi-language symbol extraction (12 languages)
- Repository map with 3 search modes
- Code intelligence integration
- Tree-sitter parsers

### Phase 3.6: Daily Workflow Commands (Complete - v0.11.1)
- `morning`, `daily`, `weekly`, `trends` commands
- `focus`, `pause`, `resume`, `search` commands
- Productivity analytics
- Time tracking integration

### Phase 3.7: Test Optimization (Complete - v0.11.2)
- 97% faster test execution (52min → 1m46s)
- CI improvements for all language parsers
- 1,370 tests, 85% coverage
- Parallel test execution

### Phase 3.8: Semantic Intelligence (Complete - v0.12.0)
- Local embedding system (sentence-transformers)
- FAISS vector store
- 3 semantic search MCP tools
- Git commit analysis
- Pattern-based task suggestions
- Project context intelligence
- 10 new MCP tools (32 total)

### Phase 4: Proactive Intelligence (Complete - v0.13.0)
- Real-time file monitoring with watchdog
- Proactive MCP tools (4 new tools, 36 total)
- Context intelligence and work session analysis
- AI action prediction system
- 316 new tests, 90% coverage

### Phase 5: Interactive TUI (Complete - v0.14.0)
- Textual-based terminal interface
- AI-enhanced dashboard with suggestion panel
- Interactive task recommendations
- KB search with semantic integration
- 189 integration tests, 1,953+ tests total
- Released: 2025-10-28

**Current Status**: v0.14.0 Complete 🎉 - Strategic Refinement Phase

---

## Strategic Direction: "本質に沿ってブラッシュアップ"

After v0.14.0 completion, Clauxton shifts from feature expansion to **essence refinement** through integration and deepening.

**Core Insight**: 36 MCP tools and many features created "何でもできる = 何が得意か不明" (can do everything = unclear what it's good at)

**New Positioning**: **"Obsidian for Code Projects, Built for Claude"** - Project Memory System for AI Development

See `docs/POSITIONING.md` for comprehensive market analysis.

---

## Completed Phase 4: Proactive Intelligence (v0.13.0)

**Goal**: Real-time monitoring and proactive suggestions via Claude Code ✅

**Released**: 2025-10-27

**Priority**: 🔥🔥 High (Proactive Features)

#### Core Features Delivered

1. **Real-time File Monitoring** ✅
   - Watch file changes with `watchdog`
   - Detect new patterns in real-time
   - Update embeddings incrementally
   - Notify Claude Code of important changes

2. **Proactive MCP Tools** ✅
   - `watch_project_changes(enabled: bool)` - Enable/disable monitoring
   - `get_recent_changes(minutes: int)` - Recent activity summary
   - `suggest_kb_updates(threshold: float)` - KB entry update suggestions
   - `detect_anomalies()` - Unusual patterns in code changes

3. **Context Intelligence** ✅
   - Work session analysis (duration, breaks, focus score)
   - AI action prediction (9 actions with confidence)
   - Enhanced project context (Git, time, session data)
   - Behavior tracking and personalization

4. **Enhanced Context Awareness** ✅
   - Current branch analysis
   - Active file detection
   - Session tracking
   - Time-based context (morning/afternoon)

#### Implementation Summary

**Week 1 (Nov 18-24): File Monitoring Foundation** ✅
- [x] watchdog integration
- [x] Event processing system
- [x] Background service implementation
- [x] File change detection
- [x] Unit tests (20+ tests)

**Week 2 (Nov 25 - Dec 1): Proactive Suggestions** ✅
- [x] Context-aware suggestion engine
- [x] MCP tools for proactive features
- [x] Pattern detection
- [x] KB update suggestions
- [x] Integration tests (15+ tests)

**Week 3 (Dec 2-6): Context Intelligence & Release** ✅
- [x] Work session analysis
- [x] Action prediction system
- [x] Enhanced context management
- [x] Comprehensive documentation (4 guides)
- [x] Release preparation & deployment

#### Results
- 🎯 4 MCP tools added (36 total)
- ⚡ 316 new tests, 90% coverage
- 📚 4 comprehensive user guides
- 🚀 GitHub release successful, all CI passing

---

## Next Phase: Essence Refinement

### Phase 6: Unified Memory Model (v0.15.0) - 🔥 CURRENT FOCUS

**Goal**: Integrate and deepen core essence - Unified Memory System

**Release Target**: 2026-01-24 (8 weeks)

**Status**: 📋 Planning

**Priority**: 🔥🔥 High (Core Value Enhancement)

**Strategic Shift**: From "削減" (reduction) to "統合と深化" (integration and deepening)

#### Core Concept: Unified Memory Model

**Problem**:
- Separate systems (KB, Tasks, Repository Map, Code) create fragmentation
- Users manage multiple data types independently
- Difficult to see relationships across domains

**Solution**:
Consolidate into single **Memory Entry** concept:

```python
class MemoryEntry(BaseModel):
    id: str
    type: Literal["knowledge", "decision", "code", "task", "pattern"]
    title: str
    content: str

    # Metadata
    category: str
    tags: List[str]
    created_at: datetime
    updated_at: datetime

    # Relationships (記憶同士の関連)
    related_to: List[str]

    # Context (記憶の文脈)
    source: str  # "manual", "git-commit", "code-analysis"
    confidence: float  # 0.0-1.0
```

#### Core Features

1. **Smart Memory System**
   - Auto-extract from Git commits
   - Auto-detect code patterns
   - Auto-suggest related memories
   - Consolidate duplicate memories

2. **Memory Intelligence**
   - Question-answering over all memories
   - Automatic summarization
   - Relationship mapping
   - Next task prediction

3. **Unified Search**
   - Single search across all memory types
   - Semantic + keyword hybrid search
   - Context-aware ranking

4. **Backward Compatibility**
   - Existing KB/Task APIs preserved
   - Gradual migration path
   - Data conversion utilities

#### Implementation Plan (8 weeks)

**Week 1-2: Core Integration (統合の基盤)**
- [ ] Unified Memory Entry model
- [ ] KB + Task + Repository Map consolidation
- [ ] Migration utilities
- [ ] Backward compatibility layer
- [ ] Unit tests (50+ tests)

**Week 3-4: Smart Memory (賢い記憶)**
- [ ] Auto-extraction from commits
- [ ] Code change pattern detection
- [ ] Auto-relationship detection
- [ ] Duplicate consolidation
- [ ] Integration tests (30+ tests)

**Week 5-6: Memory Intelligence (記憶の知能化)**
- [ ] Auto-summarization system
- [ ] Question-answering over memories
- [ ] Next task prediction
- [ ] Memory graph visualization
- [ ] Intelligence tests (25+ tests)

**Week 7-8: UX Polish (体験の洗練)**
- [ ] Smart default configuration
- [ ] Guided workflows in CLI
- [ ] TUI integration (memory explorer)
- [ ] Comprehensive documentation
- [ ] User acceptance tests (15+ scenarios)

#### Success Metrics
- 🎯 Memory consolidation: 80% of KB+Task+Code unified
- ⚡ Auto-extraction accuracy: >70%
- 💬 Q&A relevance: >80% users find helpful
- 📊 Relationship discovery: Average 3-5 related memories/entry
- ❤️ User satisfaction: 4.5+/5.0

#### MCP Tool Evolution
- Current: 36 tools (fragmented)
- Target: ~25 tools (consolidated)
- Focus: Memory operations, not data type operations

**Deprecated MCP tools** (backward compatible for 2 versions):
- `kb_add()`, `kb_search()` → `memory_add()`, `memory_search()`
- `task_add()`, `task_list()` → Use `memory_*()` with type filter
- Repository tools → Integrated into memory auto-extraction

#### 削減計画: 段階的削除による本質への集中

**戦略**: 段階的削減 + Backward compatibility + 動作保証

**タイムライン**:

| Phase | Action | Tools | Commands | Tests |
|-------|--------|-------|----------|-------|
| v0.14.0 | Baseline | 36 | 40+ | 1,953 |
| **v0.15.0** | **Deprecation** | **36*** | **40+*** | **2,081** |
| v0.16.0 | Deletion | 25 | 20 | 1,201 |

*v0.15.0: Deprecated but still working

**v0.15.0 (2026-01-24): Deprecation Only**

**重要**: 何も削除しない。全機能動作。

```
✅ Memory System 実装 (新規 7 tools)
✅ Backward compatibility layer
⚠️ Deprecation warnings 追加
✅ KB/Task API 動作（警告付き）
✅ Daily commands 動作（警告付き）
✅ 12言語動作（9言語は警告付き）
```

**v0.16.0 (2026-03-20): Actual Deletion**

```
❌ Backward compatibility 削除
❌ KB/Task MCP tools 削除 (11 tools)
❌ Daily commands 削除 (8 commands)
❌ Legacy languages 削除 (9 parsers)
❌ Real-time monitoring 削除
```

**削減効果**:

```
v0.14.0 → v0.15.0 → v0.16.0
━━━━━━━━━━━━━━━━━━━━━━━━━
MCP tools:      36  →  36*  →  25   (-30%)
CLI commands:   40  →  40*  →  20   (-50%)
Languages:      12  →  12*  →   3   (-75%)
Tests:       1,953  →  2,081 → 1,201 (-38%)
LOC:        15,000  → 17,000 → 10,000 (-33%)
```

**保持（本質）**:
- ✅ Memory System（永続的記憶）
- ✅ Conflict Detection（依存関係可視化）
- ✅ Team Features（知識標準化）
- ✅ TUI（UX価値高い）

**削除（非本質）**:
- ❌ Daily workflow commands（Claude Code 代替）
- ❌ 9言語サポート（使用率 < 3%）
- ❌ Real-time monitoring（On-demand で十分）
- ❌ 重複 MCP tools（Memory API に統合）

**動作保証**:
1. ✅ Migration script 提供
2. ✅ Backward compatibility (v0.15.0)
3. ✅ >85% coverage 維持
4. ✅ Migration Guide 完備
5. ✅ 2ヶ月の deprecation 期間

詳細: `docs/DEPRECATION_PLAN.md`, `docs/v0.15.0_MIGRATION_VALIDATION.md`

---

### Phase 7: Team & Collaboration (v0.16.0) - 🟡 MEDIUM PRIORITY

**Goal**: Shared memory and team knowledge management

**Release Target**: 2026-03-20 (4 weeks)

**Priority**: 🟡 Medium (Team Features)

**Note**: Focuses on team collaboration using consolidated Memory Model from v0.15.0

#### Core Features

1. **Shared Memory Workspace**
   - Team-wide memory sharing (Git-based or Server-based)
   - Memory access control (private/team/public)
   - Collaborative memory editing
   - Conflict resolution for concurrent edits

2. **Team Knowledge Management**
   - Onboarding workflows (auto-generate memory packs for new members)
   - Team coding standards as memories
   - Shared decision history
   - Team-wide search and discovery

3. **Collaboration Features**
   - Memory commenting and discussion
   - Memory approval workflows
   - Activity feed (who added/edited what)
   - Team memory analytics

4. **Lightweight Web Interface** (Optional)
   - Memory browser (read-only)
   - Memory graph visualization
   - Team dashboard
   - Search interface

#### Technical Stack
- Storage: Git-based (default) or Server-based (optional)
- Sync: Git merge or API sync
- Web UI: Streamlit (if needed) or Textual Web Export
- Minimal infrastructure required

#### Implementation Plan (4 weeks)

**Week 1-2**: Team storage architecture
**Week 3**: Collaboration features
**Week 4**: Optional web interface + documentation

#### Success Metrics
- 👥 Team adoption: 20+ teams (realistic)
- 📚 Shared memory usage: >50% of memories shared
- ⏱️ Onboarding time reduction: -50%
- ❤️ Team satisfaction: 4.0+/5.0

---

### Phase 8: Advanced Features (v0.17.0+) - 🟢 LOW PRIORITY

**Goal**: Optional advanced capabilities (user-driven)

**Release Target**: TBD (based on user feedback)

**Priority**: 🟢 Low (Nice-to-Have)

#### Potential Features (User Feedback Driven)

1. **Multi-Project Intelligence** (If users have >5 projects)
   - Learn from all projects
   - Cross-project pattern recognition
   - Best practice recommendations
   - Template suggestions

2. **Advanced Analytics** (If teams request insights)
   - Memory usage heatmap
   - Team knowledge coverage
   - Query analytics
   - Learning progress metrics

3. **Enterprise Features** (If $10K+ ARR achieved)
   - Self-hosted deployment
   - SSO integration
   - Audit logs
   - Advanced access control

4. **Ecosystem Integration** (If community grows)
   - VS Code extension
   - GitHub App integration
   - Slack notifications
   - API for custom integrations

#### Implementation Approach
- **NOT planned as fixed roadmap**
- Build based on user requests and adoption data
- Prioritize features with proven demand
- Community contributions encouraged

---

## Technical Decisions

### Why sentence-transformers?
- ✅ Local-first (privacy)
- ✅ Fast inference (<100ms)
- ✅ No API costs
- ✅ Offline capability

### Why FAISS?
- ✅ Lightweight (no server required)
- ✅ Fast similarity search (<10ms for 10K vectors)
- ✅ Persistent storage
- ✅ Industry standard

### Why watchdog?
- ✅ Cross-platform file monitoring
- ✅ Efficient event-based architecture
- ✅ Well-maintained library
- ✅ Low overhead

### Why Textual for TUI?
- ✅ Modern, async-first design
- ✅ Rich widgets and layouts
- ✅ Great documentation
- ✅ Active development

---

## Design Philosophy

### Core Principles

1. **AI as Copilot, Not Autopilot**
   - AI suggests, user approves
   - Transparency in reasoning
   - Easy override/rejection

2. **Progressive Disclosure**
   - Simple commands by default
   - Advanced options available
   - Learning curve minimized

3. **Privacy-First**
   - Embeddings local by default
   - No external API calls for core features
   - User data never leaves project

4. **Performance Conscious**
   - Aggressive caching
   - Async operations
   - Background processing
   - <3s response time target

5. **MCP-First Integration**
   - Claude Code as primary interface
   - Natural conversation UX
   - Transparent automation
   - CLI for power users

---

## Success Metrics & KPIs

### Short-term (v0.13.0 - 3 months):
- 🎯 Proactive suggestion acceptance: >70%
- ⚡ Real-time update latency: <500ms
- 📚 KB coverage improvement: +40%
- 🚀 Development velocity: +50%

### Medium-term (v0.14.0-v0.15.0 - 6 months):
- 🤖 50% of tasks created by AI suggestions
- 🔍 70% of KB entries AI-assisted
- 💬 Daily AI query usage: 5+ per user
- ⭐ GitHub stars: 500+
- 📥 PyPI downloads: 50K+/month

### Long-term (v0.16.0+ - 12 months):
- 👥 Team adoption: 100+ teams
- 🌐 Enterprise deployments: 10+
- 📊 Community contributions: 50+ PRs
- 💡 Plugin ecosystem: 20+ extensions

---

## Release Schedule (Revised)

| Version | Focus | Target Date | Status |
|---------|-------|-------------|--------|
| v0.12.0 | Semantic Intelligence | 2025-11-15 | ✅ Complete |
| v0.13.0 | Proactive Intelligence | 2025-10-27 | ✅ Complete |
| v0.14.0 | Interactive TUI | 2025-10-28 | ✅ Complete |
| **v0.15.0** | **Unified Memory Model** | **2026-01-24** | **📋 Planning (Current)** |
| v0.16.0 | Team & Collaboration | 2026-03-20 | 📋 Planned |
| v0.17.0+ | Advanced Features | TBD | 🔮 User-Driven |

**Strategic Milestone**: v0.15.0 marks the shift from feature expansion to essence refinement through the Unified Memory Model.

---

## Success Metrics & KPIs (Revised)

### Phase 6 (v0.15.0 - Unified Memory Model):
- 🎯 Memory consolidation: 80% of KB+Task+Code unified
- ⚡ Auto-extraction accuracy: >70%
- 💬 Q&A relevance: >80% users find helpful
- 📊 Average related memories per entry: 3-5
- ⭐ GitHub stars: 500+
- 📥 PyPI downloads: 20K+/month

### Phase 7 (v0.16.0 - Team Features):
- 👥 Team adoption: 20+ teams
- 📚 Shared memory usage: >50%
- ⏱️ Onboarding time reduction: -50%
- 💰 Team ARR: $3K+ (20 teams × $149/year)

### Long-term (24-36 months):
- 👤 Active users: 10,000+
- 💰 Individual Pro: $58K ARR (2,000 users)
- 👥 Team ARR: $74.5K (500 teams)
- 🏢 Enterprise ARR: $49.9K (10 companies)
- **Total ARR Target**: **$182K** (realistic)

**Note**: Original target was $580K-840K ARR in 5 years. Revised to $182K in 2-3 years as more achievable milestone.

---

## Feedback & Contributions

We welcome feedback and contributions! Please:

- 🐛 Report bugs: https://github.com/nakishiyaman/clauxton/issues
- 💡 Suggest features: https://github.com/nakishiyaman/clauxton/discussions
- 🔀 Submit PRs: https://github.com/nakishiyaman/clauxton/pulls
- 📖 Positioning & Strategy: See `docs/POSITIONING.md`

---

**Last updated**: 2025-11-03 (v0.14.0 Complete, Strategic Refinement Phase, v0.15.0 Planning)
