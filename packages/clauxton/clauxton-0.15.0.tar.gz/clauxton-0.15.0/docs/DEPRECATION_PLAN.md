# Deprecation Plan: 本質的でない機能の削除

**Version**: v0.15.0 - v0.17.0
**Strategy**: "統合と深化" に伴う非本質機能の段階的削除
**Validation**: `docs/v0.15.0_MIGRATION_VALIDATION.md` 参照
**Last Updated**: 2025-11-03

---

## 削除の原則

### 削除基準
1. **コア価値に寄与しない** - 永続的記憶、依存関係可視化、チーム知識標準化に貢献しない
2. **使用率が低い** - ユーザーの10%未満しか使用していない
3. **保守コストが高い** - テスト/ドキュメント維持コストが価値を上回る
4. **Claude Codeで代替可能** - Claude Codeが直接実行できる機能

### 削除しないもの
- コア価値に直結する機能
- 高使用率の機能（20%以上）
- 競合優位性を生む機能
- 削除コストが高い機能（アーキテクチャ変更必要）

### 段階的削除の方針
- **v0.15.0**: Deprecation warnings 追加、**削除はしない**
- **v0.16.0**: 実際に削除（2ヶ月の猶予期間後）
- **v0.17.0+**: 使用率に応じた追加削減検討

---

## v0.15.0 での Deprecation (2026-01-24)

**重要**: v0.15.0 では**削除しない**。Deprecation warnings のみ追加。

### 目標
- ✅ Memory System 実装完了
- ✅ Backward compatibility layer 実装
- ✅ Deprecation warnings 追加
- ⚠️ **機能は全て動作する**（削除は v0.16.0）

### 1. MCP Tools の統合: 36 tools (v0.15.0) → 25 tools (v0.16.0)

#### v0.15.0: 新規追加 (7 tools) + Deprecated (11 tools still working)

**Unified Memory Tools (新規)**
```python
✅ memory_add(entry: Dict) -> str              # NEW
✅ memory_search(query: str, type_filter: List[str], limit: int) -> str  # NEW
✅ memory_get(id: str) -> str                   # NEW
✅ memory_update(id: str, **kwargs) -> str      # NEW
✅ memory_delete(id: str) -> str                # NEW
✅ memory_find_related(id: str, limit: int) -> str  # NEW
✅ memory_import_yaml(yaml_path: str) -> str    # NEW
```

**Deprecated (but still working in v0.15.0)**

**Knowledge Base Tools (6 tools - DEPRECATED)**
```python
⚠️ kb_add()           # Deprecated → memory_add(type="knowledge")
⚠️ kb_search()        # Deprecated → memory_search(type_filter=["knowledge"])
⚠️ kb_list()          # Deprecated → memory_search(type_filter=["knowledge"])
⚠️ kb_get()           # Deprecated → memory_get()
⚠️ kb_update()        # Deprecated → memory_update()
⚠️ kb_delete()        # Deprecated → memory_delete()
```

**Task Management Tools (7 tools - DEPRECATED)**
```python
⚠️ task_add()         # Deprecated → memory_add(type="task")
⚠️ task_list()        # Deprecated → memory_search(type_filter=["task"])
⚠️ task_get()         # Deprecated → memory_get()
⚠️ task_update()      # Deprecated → memory_update()
⚠️ task_import_yaml() # Deprecated → memory_import_yaml()
⚠️ task_next()        # Deprecated → suggest_next_tasks()
⚠️ task_delete()      # Deprecated → memory_delete()
```

**Repository Intelligence Tools (2 tools - DEPRECATED)**
```python
⚠️ index_repository()     # Deprecated → Auto background processing
⚠️ search_symbols()       # Deprecated → memory_search(type_filter=["code"])
```

**Conflict Detection Tools (3 → 2 in v0.16.0)**
```python
✅ detect_conflicts()          # KEPT (core value)
✅ recommend_safe_order()      # KEPT (core value)
⚠️ check_file_conflicts()      # Deprecated → detect_conflicts() (integrated)
```

#### Backward Compatibility Layer

```python
# clauxton/mcp/server.py (v0.15.0)

@server.call_tool()
async def kb_add(title: str, category: str, content: str, tags: List[str] = []) -> str:
    """[DEPRECATED] Add KB entry - use memory_add() instead

    This tool is deprecated and will be removed in v0.16.0.
    Use memory_add(type='knowledge') instead.
    """
    warnings.warn(
        "kb_add() is deprecated and will be removed in v0.16.0. "
        "Use memory_add(type='knowledge') instead.",
        DeprecationWarning
    )

    # 内部で memory_add() を呼び出す
    return await memory_add({
        "type": "knowledge",
        "title": title,
        "category": category,
        "content": content,
        "tags": tags,
        "source": "manual"
    })

# task_add(), kb_search() など全ての deprecated tools も同様の実装
```

#### v0.15.0 での MCP Tool Count
- **New memory tools**: 7
- **Deprecated (still working)**: 11
- **Kept (no change)**: 18 (semantic, proactive, conflict, utilities)
- **Total in v0.15.0**: **36 tools** (変わらず)

#### v0.16.0 での削除後
- **Memory tools**: 7
- **Kept tools**: 18
- **Total in v0.16.0**: **25 tools** (-30%)

---

### 2. CLI Commands: 40+ commands (v0.15.0) → 20 commands (v0.16.0)

#### v0.15.0: Deprecated (but still working)

**Daily Workflow Commands (8 commands - DEPRECATED)**
```bash
⚠️ clauxton morning      # Deprecated → Claude Code: "Show me today's tasks"
⚠️ clauxton daily        # Deprecated → Claude Code: "What did I do today?"
⚠️ clauxton weekly       # Deprecated → Claude Code: "Weekly summary"
⚠️ clauxton trends       # Deprecated → Claude Code: "Show productivity trends"
⚠️ clauxton focus        # Deprecated → clauxton memory update (type="task")
⚠️ clauxton pause        # Deprecated → 低使用率
⚠️ clauxton continue     # Deprecated → 低使用率
⚠️ clauxton resume       # Deprecated → Claude Code: "What should I resume?"
```

**Deprecation Warning Example**:
```bash
$ clauxton morning
⚠️  WARNING: 'clauxton morning' is deprecated and will be removed in v0.16.0
    Use Claude Code instead: "Show me today's tasks and suggest priorities"
    Or use: clauxton memory search --type task --filter status=pending

[... existing output continues ...]
```

**Core Commands (KEPT)**
```bash
✅ clauxton init
✅ clauxton memory add/search/list/get/update/delete  # NEW in v0.15.0
✅ clauxton memory extract      # NEW: コミットから抽出
✅ clauxton memory link         # NEW: 自動リンク
✅ clauxton memory graph        # NEW: 関係グラフ
✅ clauxton conflict detect/order
✅ clauxton undo
✅ clauxton search              # 統合検索 (保持、高使用率)
✅ clauxton tui                 # 保持 (UX価値高い)
```

#### v0.16.0: Daily commands 削除
```bash
# v0.16.0 では以下は削除される
$ clauxton morning
Error: Unknown command 'morning'. Did you mean 'memory'?
Use 'clauxton --help' for available commands.
```

---

### 3. Repository Map 言語サポート: 12 languages (v0.15.0) → 3 languages (v0.16.0)

#### v0.15.0: Focus languages + Legacy languages (deprecated)

**Focus Languages (HIGH PRIORITY)**
```python
SUPPORTED_LANGUAGES = {
    "python": {"priority": "high", "parser": "tree-sitter-python"},
    "javascript": {"priority": "high", "parser": "tree-sitter-javascript"},
    "typescript": {"priority": "high", "parser": "tree-sitter-typescript"},
}
```

**Legacy Languages (DEPRECATED, 使用率 < 3%)**
```python
LEGACY_LANGUAGES = {
    "ruby": {"priority": "deprecated", "parser": "tree-sitter-ruby"},
    "go": {"priority": "deprecated", "parser": "tree-sitter-go"},
    "rust": {"priority": "deprecated", "parser": "tree-sitter-rust"},
    "java": {"priority": "deprecated", "parser": "tree-sitter-java"},
    "cpp": {"priority": "deprecated", "parser": "tree-sitter-cpp"},
    "csharp": {"priority": "deprecated", "parser": "tree-sitter-c-sharp"},
    "php": {"priority": "deprecated", "parser": "tree-sitter-php"},
    "swift": {"priority": "deprecated", "parser": "tree-sitter-swift"},
    "kotlin": {"priority": "deprecated", "parser": "tree-sitter-kotlin"},
}
```

**Deprecation Warning**:
```bash
$ clauxton repo index
⚠️  Detected Go files (12 files)
    WARNING: Go language support is deprecated and will be removed in v0.16.0
    Focus languages: Python, JavaScript, TypeScript
    Go parser will be removed in v0.16.0

Indexing repository...
  Python: 45 files, 120 symbols
  Go: 12 files, 35 symbols (DEPRECATED)
```

**v0.15.0 では全言語動作**: 警告は出すが、Go/Rust 等も動作する

**v0.16.0 で削除**:
- Tests: -500 tests (9言語分)
- Dependencies: -9 tree-sitter parsers
- Maintenance cost: -40%

---

### 4. Proactive Monitoring: Simplification

#### v0.15.0: Deprecated (but still working)

**Real-time Monitoring (DEPRECATED)**
```python
@deprecated("Real-time monitoring will be removed in v0.16.0. Use on-demand extraction.")
def watch_project_changes(enabled: bool):
    """[DEPRECATED] Enable/disable file watching

    This feature is deprecated and will be removed in v0.16.0.
    Use 'clauxton memory extract --since 7d' instead.
    """
    warnings.warn(
        "Real-time monitoring is deprecated. "
        "Use on-demand extraction: 'clauxton memory extract --since 7d'",
        DeprecationWarning
    )
    # 機能は動作する
    start_file_watcher() if enabled else stop_file_watcher()
```

**MCP Tools (4 → 1)**
```python
⚠️ watch_project_changes()    # Deprecated → On-demand extraction
⚠️ get_recent_changes()       # Deprecated → memory_search(since=...)
⚠️ detect_anomalies()         # Deprecated → 価値不明確
✅ suggest_memory_updates()   # KEPT (renamed from suggest_kb_updates)
```

**v0.15.0**: 全て動作する（警告付き）
**v0.16.0**: watchdog削除、on-demandのみ

**理由**:
- セッション開始時に `clauxton memory extract --since 7d` で十分
- バックグラウンドサービスのリソースコスト > 価値

---

## v0.16.0 での削除 (2026-03-20)

**重要**: v0.15.0 で 2ヶ月間 deprecation 期間を経た後に削除

### 目標
- ❌ Backward compatibility layer 削除
- ❌ Deprecated MCP tools 削除 (11 tools)
- ❌ Daily workflow commands 削除 (8 commands)
- ❌ Legacy language parsers 削除 (9 languages)
- ❌ Real-time monitoring 削除
- ✅ Memory System のみ稼働

### 1. Code Deletion

**Deleted Files**:
```
clauxton/core/knowledge_base_compat.py         # Backward compat layer
clauxton/core/task_manager_compat.py           # Backward compat layer
clauxton/cli/daily.py                          # Daily workflow commands
clauxton/intelligence/parsers/go.py            # Legacy language parsers
clauxton/intelligence/parsers/rust.py
clauxton/intelligence/parsers/java.py
clauxton/intelligence/parsers/cpp.py
clauxton/intelligence/parsers/csharp.py
clauxton/intelligence/parsers/php.py
clauxton/intelligence/parsers/ruby.py
clauxton/intelligence/parsers/swift.py
clauxton/intelligence/parsers/kotlin.py
clauxton/proactive/file_monitor.py            # Real-time monitoring
```

**Modified Files**:
```python
# clauxton/mcp/server.py
# kb_add(), kb_search(), task_add(), task_list() など 11 tools 削除
# memory_add(), memory_search() など Memory tools のみ残す

# clauxton/cli/main.py
# morning, daily, weekly, trends, focus, pause, continue, resume 削除
# memory, conflict, undo, tui, search のみ残す
```

**Estimated LOC Reduction**: ~5,000 LOC

---

### 2. Test Deletion and Conversion

#### Deleted Tests (1,030 tests)
```
tests/core/test_knowledge_base.py              # -200 tests
tests/core/test_task_manager.py                # -180 tests
tests/cli/test_daily.py                        # -50 tests
tests/intelligence/parsers/test_*.py (9 langs) # -500 tests
tests/proactive/test_file_monitor.py           # -100 tests
```

#### Converted Tests (重要なケースを Memory tests に統合)
```python
# tests/core/test_memory.py に追加
# 例: KB category search → Memory type filter + category filter

def test_memory_search_by_type_and_category():
    """Converted from test_kb_search_by_category"""
    memory = Memory()
    results = memory.search(
        "authentication",
        type_filter=["knowledge"],
        category_filter="api"
    )
    assert len(results) > 0
    assert all(r.type == "knowledge" for r in results)
    assert all(r.category == "api" for r in results)
```

#### Test Count After v0.16.0
```
Before (v0.15.0):  2,081 tests
Deleted:           -1,030 tests
Converted/Added:   +150 tests (重要ケース)
After (v0.16.0):   1,201 tests
```

**Coverage Requirement**: Must maintain >85%

---

### 3. Documentation Deletion and Replacement

#### Deleted Docs
```
docs/quick-start.md (KB-centric)               # Replaced by docs/MEMORY_QUICK_START.md
docs/task-management-guide.md                  # Replaced by docs/MEMORY_SYSTEM.md
docs/DAILY_WORKFLOW_GUIDE.md                   # Removed (feature deleted)
docs/REPOSITORY_MAP_GUIDE.md (9言語記載)       # Replaced by docs/MEMORY_CODE_INTELLIGENCE.md
docs/PROACTIVE_MONITORING_GUIDE.md             # Removed (feature simplified)
```

#### New/Replaced Docs (v0.15.0 で作成済み)
```
docs/MEMORY_SYSTEM.md                          # Comprehensive Memory System guide
docs/MEMORY_QUICK_START.md                     # Quick start with Memory API
docs/MIGRATION_GUIDE_v0.15_to_v0.16.md         # Migration guide from v0.15.0
docs/MEMORY_CODE_INTELLIGENCE.md               # Code extraction from commits
```

#### Updated Docs
```
README.md                                      # Memory-centric
docs/mcp-index.md                              # Memory tools only
docs/architecture.md                           # Memory System architecture
docs/MCP_INTEGRATION_GUIDE.md                  # Updated for Memory tools
```

---

### 4. TUI の機能調整

**Deprecated Tabs (機能削除に伴い)**:
```
❌ Daily workflow tab     # Daily commands 削除に伴い
```

**Kept Tabs (Memory System 対応)**:
```
✅ Memory Explorer tab    # KB Browser → Memory Explorer に改名
✅ AI Suggestions tab     # Memory-based suggestions
✅ Help tab               # Updated for Memory commands
```

**TUI は削減せず維持** (UX価値高い)

---

## v0.17.0+ での削除検討 (TBD)

### 削除候補（使用率次第）

#### 1. TUI 全体の削除検討
**条件**: TUI 使用率 < 10%
**理由**: 保守コスト高、CLI で十分
**代替**: `memory graph` コマンドで可視化

#### 2. Conflict Detection の削除検討
**条件**: Git の conflict detection 機能が向上した場合
**理由**: Git native 機能で代替可能
**但し**: 現時点では保持（競合優位性）

#### 3. Undo System の簡素化
**条件**: 使用率 < 20%
**理由**: Git でロールバック可能
**代替**: Git reset/revert 推奨

---

## 削減効果の総計

### コードベース削減

| Metric | v0.14.0 | v0.15.0 | v0.16.0 | Change |
|--------|---------|---------|---------|--------|
| **MCP Tools** | 36 | 36* | 25 | -30% |
| **CLI Commands** | 40+ | 40+* | 20 | -50% |
| **Languages** | 12 | 12* | 3 | -75% |
| **Tests** | 1,953 | 2,081 | 1,201 | -38% from v0.14.0 |
| **LOC** | ~15,000 | ~17,000 | ~10,000 | -33% |
| **Dependencies** | 25 | 25 | 16 | -36% |

*v0.15.0: Deprecated but still working

### 保守コスト削減
- **Test execution**: 1m46s → 1m15s (-30%)
- **CI time**: 3m30s → 2m30s (-30%)
- **Documentation**: -40% maintenance cost
- **Dependencies**: 25 → 16 parsers/libs (-36%)
- **Code complexity**: -33% LOC

### ユーザー体験向上
- ✅ MCP tool リストが短く明確に (36 → 25)
- ✅ CLI コマンドが直感的に (Memory-centric)
- ✅ 学習コストが低減 (統一された Memory API)
- ✅ パフォーマンス向上 (テスト時間 -30%)
- ✅ Focus on core value (永続的記憶)

---

## 動作保証チェックリスト

### v0.15.0 リリース前

#### Core Functionality
- [ ] Memory System 完全実装
  - [ ] CRUD operations
  - [ ] Type filtering (knowledge/task/code/decision/pattern)
  - [ ] Relationship management
  - [ ] Search (TF-IDF + semantic)
- [ ] Backward compatibility layer 実装
  - [ ] KB API → Memory API 変換
  - [ ] Task API → Memory API 変換
  - [ ] Deprecation warnings 表示
- [ ] Migration script 実装
  - [ ] KB → Memory migration
  - [ ] Task → Memory migration
  - [ ] Data integrity check
  - [ ] Rollback capability

#### Testing (2,081 tests)
- [ ] All existing tests pass (with deprecation warnings ignored)
- [ ] New Memory tests pass (178 tests)
- [ ] Backward compatibility tests pass (40 tests)
- [ ] Integration tests pass
- [ ] Coverage >85%

#### Documentation
- [ ] `docs/MEMORY_SYSTEM.md` complete
- [ ] `docs/MIGRATION_GUIDE_v0.15.0.md` complete
- [ ] `README.md` updated
- [ ] `docs/mcp-index.md` updated
- [ ] Deprecation warnings documented

#### User Communication
- [ ] CHANGELOG.md updated
- [ ] GitHub release notes prepared
- [ ] Deprecation announcement drafted
- [ ] Migration guide publicized

### v0.16.0 リリース前

#### Deletion Validation
- [ ] All deprecated code identified
- [ ] Important test cases converted to Memory tests
- [ ] Documentation updated/replaced
- [ ] Migration from v0.15.0 tested

#### Core Functionality (Post-Deletion)
- [ ] Memory System works without backward compat
- [ ] MCP tools (25) all work
- [ ] CLI commands (20) all work
- [ ] TUI works with Memory Explorer
- [ ] Conflict detection works
- [ ] Search works

#### Testing (1,201 tests)
- [ ] All tests pass
- [ ] Coverage >85%
- [ ] No broken tests
- [ ] Performance benchmarks met

#### User Migration
- [ ] 5+ beta testers complete migration
- [ ] No data loss reported
- [ ] Migration script works on real projects
- [ ] User feedback incorporated

#### Documentation
- [ ] All deprecated docs removed/replaced
- [ ] Migration guide complete
- [ ] Quick start guide updated
- [ ] MCP documentation accurate

---

## ロードマップとの整合性

### v0.15.0: Unified Memory Model
- ✅ Memory System 実装
- ✅ KB/Task を Memory として統合
- ✅ Backward compatibility 保持
- ✅ **既存機能は全て動作**
- ✅ v0.16.0 Team & Collaboration の基盤完成

### v0.16.0: Team & Collaboration
- ✅ Memory System を基盤に使用
- ✅ Shared memory workspace
- ✅ Team knowledge management
- ✅ **Memory System のみで実現可能**
- ✅ KB/Task API 不要（削除可能）

### v0.17.0+: Advanced Features
- ✅ Memory System のみに依存
- ✅ Multi-project intelligence
- ✅ Advanced analytics
- ✅ **統一されたデータモデル**

**結論**: 削除してもロードマップは実現可能。Memory System が全ての基盤。

---

## 削除スケジュール

| Version | 削除内容 | Impact | 代替手段 |
|---------|---------|--------|---------|
| v0.15.0 | MCP tools 統合 (36→25) | Medium | Unified memory_*() tools |
| v0.15.0 | Daily workflow commands | Low | Claude Code direct |
| v0.15.0 | Repository languages (12→3) | Low | Community plugins |
| v0.15.0 | Proactive monitoring 簡素化 | Low | On-demand extraction |
| v0.16.0 | Backward compatibility 削除 | High | Migration guide |
| v0.16.0 | TUI tabs 削減 | Low | Memory Explorer |
| v0.17.0 | TUI 全体削除検討 | Medium | CLI + memory graph |
| v0.17.0 | Conflict detection 削除検討 | High | Git native |

---

## 削除の通知戦略

### v0.15.0 リリース時
1. **CHANGELOG.md** に削除リスト明記
2. **Migration Guide** 提供
3. **Deprecation warnings** 実装
4. **GitHub Discussions** でアナウンス
5. **README.md** 更新

### Deprecation Warning 例
```python
# v0.15.0 で deprecated な API 呼び出し時
@deprecated("kb_add() is deprecated. Use memory_add(type='knowledge') instead.")
def kb_add(entry: KnowledgeBaseEntry) -> str:
    warnings.warn(
        "kb_add() will be removed in v0.16.0. "
        "Use memory_add(type='knowledge') instead.",
        DeprecationWarning,
        stacklevel=2
    )
    return compat_kb_add(entry)
```

### CLI Deprecation Warning
```bash
$ clauxton morning
⚠️  Warning: 'clauxton morning' is deprecated and will be removed in v0.16.0
    Use Claude Code instead: "Show me today's tasks"
    Or use: clauxton memory search --type task --filter status=pending

[... output ...]
```

---

## ロールバック計画

### 削除が問題を起こした場合

**条件**:
- 20%以上のユーザーから削除反対の声
- 重要な使用ケースが判明
- 代替手段が不十分

**対応**:
1. v0.15.1 パッチリリースで機能復活
2. 削除計画の再検討
3. コミュニティとの議論

**Example**: Daily workflow commands
- 使用率が実は30%だった場合 → v0.15.1 で復活
- ただし、Memory system との統合形式で再実装

---

## まとめ

### 段階的削減の戦略

#### v0.15.0 (2026-01-24)
- ✅ Memory System 実装
- ✅ Backward compatibility 実装
- ⚠️ Deprecation warnings 追加
- ✅ **全機能が動作**（削除なし）
- ✅ Tests: 2,081 (+128 from v0.14.0)

#### v0.16.0 (2026-03-20)
- ❌ Backward compatibility 削除
- ❌ Deprecated features 削除
- ✅ Memory System のみ
- ✅ Tests: 1,201 (-38% from v0.14.0, but >85% coverage)
- ✅ LOC: 10,000 (-33%)

### 削減の効果
| Metric | v0.14.0 | v0.16.0 | Reduction |
|--------|---------|---------|-----------|
| MCP tools | 36 | 25 | -30% |
| CLI commands | 40+ | 20 | -50% |
| Language parsers | 12 | 3 | -75% |
| Tests | 1,953 | 1,201 | -38% |
| LOC | 15,000 | 10,000 | -33% |
| Dependencies | 25 | 16 | -36% |

### 本質への集中
- ✅ 永続的記憶（Memory System）
- ✅ 依存関係可視化（Conflict Detection）
- ✅ チーム知識標準化（Team Features in v0.16.0）
- ✅ TUI（UX価値高い）

### 削減されるもの
- ❌ Daily workflow commands (Claude Code が代替)
- ❌ 9言語サポート（使用率 < 10%）
- ❌ Real-time monitoring（On-demand で十分）
- ❌ 重複した MCP tools（Memory API に統合）

### 動作保証
1. ✅ **v0.15.0**: 全機能動作（Deprecation warnings のみ）
2. ✅ **Migration path**: KB/Task → Memory への移行スクリプト提供
3. ✅ **Documentation**: 完全な Migration Guide 提供
4. ✅ **Testing**: >85% coverage 維持
5. ✅ **Roadmap**: v0.16.0 Team & Collaboration は Memory System で実現可能

**結論**: "削減" と "統合と深化" は両立可能。段階的移行により、削除後も正常に動作し、開発フローが回る。

---

**Last Updated**: 2025-11-03
**Status**: 📋 Planning Complete - Ready for v0.15.0 Implementation
**Validation**: See `docs/v0.15.0_MIGRATION_VALIDATION.md` for detailed validation plan
**Next Action**: Begin v0.15.0 Week 1 implementation (2025-11-27)
