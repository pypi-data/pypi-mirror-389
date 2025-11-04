# v0.13.0 最適実施計画 - 全タスク完遂ロードマップ

**作成日**: 2025年10月27日
**目標**: Phase 2/3改善 + Week 3 Day 3-5を最適順序で全て完遂
**予想期間**: 5-6日（推定30-40時間）
**リリース目標**: 2025年12月6日

---

## 📊 現在の状態（Week 3 Day 2完了時点）

### ✅ 完了した作業
- **Week 3 Day 1**: Context Intelligence実装（74テスト、88%カバレッジ）
- **Week 3 Day 2**: 3つのMCPツール実装（15テスト、100%パス）
- **Phase 1改善**: Pydanticモデル、エラーハンドリング標準化

### 📈 メトリクス
| 項目 | 現状 | 目標 |
|------|------|------|
| テスト数 | 274 passed | 320+ |
| カバレッジ | 87% | 90%+ |
| MCP Tools | 32 tools | 35 tools |
| Ruff | 0 errors | 0 errors |
| Mypy | 0 errors (新規) | 0 errors (全体) |

### 📝 残タスク
- **Phase 2**: 15個の中優先度改善（推定6-8時間）
- **Phase 3**: 4個の低優先度改善（推定3-4時間）
- **Day 3-5**: 統合テスト、ドキュメント、リリース準備（推定18-22時間）

---

## 🎯 最適実施順序の原則

### 原則1: 統合テストを先に実施
**理由**: 実際の使用パターンで問題を発見してから改善を実施する方が効率的

### 原則2: 高影響の改善を優先
**理由**: ユーザー体験に直結する改善（ドキュメント、エラーハンドリング）を優先

### 原則3: 段階的コミット
**理由**: 各フェーズ完了時にコミットして、問題発生時にロールバック可能に

### 原則4: テストカバレッジを維持
**理由**: 改善を加えるたびにテストを追加し、90%+を維持

---

## 📅 5段階実施計画（最適順序）

### 🔹 Stage 1: 統合テスト作成（Day 3前半） - 8-10時間

**目的**: 現在の実装の実際の動作を確認し、問題点を発見

#### タスク

##### 1.1 統合テストファイル作成
- **File**: `tests/proactive/test_integration_week3.py`
- **Tests**: 20-25テスト
- **内容**:
  - End-to-end ワークフローテスト
  - MCP tool連携テスト
  - マルチコンポーネント統合テスト
  - パフォーマンスベンチマーク
  - エラーシナリオの統合テスト

**テストケース例**:
```python
class TestIntegrationWorkflows:
    """End-to-end workflow integration tests."""

    def test_morning_workflow_complete(self, tmp_path):
        """Test complete morning workflow: context → analysis → prediction."""
        # Setup project
        setup_test_project(tmp_path)

        # Morning workflow
        context = get_current_context(include_prediction=True)
        analysis = analyze_work_session()
        prediction = predict_next_action()

        # Verify workflow coherence
        assert context["time_context"] == "morning"
        assert prediction["action"] in ["planning", "task_review"]
        assert analysis["duration_minutes"] == 0  # Fresh start

    def test_development_session_workflow(self, tmp_path):
        """Test development session: files changed → tests → commit → PR."""
        # Simulate development
        create_feature_branch(tmp_path)
        modify_files(tmp_path, count=5)

        # Check predictions evolve
        pred1 = predict_next_action()
        assert pred1["action"] in ["run_tests", "write_tests"]

        # Simulate test run
        create_test_files(tmp_path)

        pred2 = predict_next_action()
        assert pred2["action"] == "commit_changes"

        # Commit and check
        commit_changes(tmp_path)

        pred3 = predict_next_action()
        assert pred3["action"] == "create_pr"

class TestMCPToolIntegration:
    """MCP tool integration tests."""

    def test_context_manager_mcp_consistency(self, tmp_path):
        """Verify ContextManager and MCP tools return consistent data."""
        # Direct ContextManager call
        mgr = ContextManager(tmp_path)
        direct_context = mgr.get_current_context()
        direct_analysis = mgr.analyze_work_session()

        # MCP tool calls
        mcp_context = server.get_current_context()
        mcp_analysis = server.analyze_work_session()

        # Verify consistency
        assert direct_context.current_branch == mcp_context["current_branch"]
        assert direct_analysis["duration_minutes"] == mcp_analysis["duration_minutes"]

    def test_prediction_accuracy_tracking(self, tmp_path):
        """Track prediction accuracy across multiple scenarios."""
        scenarios = [
            ("many_files_no_tests", "run_tests"),
            ("feature_branch_ready", "commit_changes"),
            ("branch_ahead_main", "create_pr"),
        ]

        accuracy_scores = []
        for scenario, expected_action in scenarios:
            setup_scenario(tmp_path, scenario)
            prediction = predict_next_action()
            is_correct = prediction["action"] == expected_action
            accuracy_scores.append(is_correct)

        accuracy = sum(accuracy_scores) / len(accuracy_scores)
        assert accuracy >= 0.7, f"Prediction accuracy too low: {accuracy}"

class TestPerformanceBenchmarks:
    """Performance benchmark integration tests."""

    def test_end_to_end_performance(self, tmp_path):
        """Benchmark complete workflow performance."""
        setup_large_project(tmp_path, files=100)

        start = time.perf_counter()

        # Complete workflow
        context = get_current_context(include_prediction=True)
        analysis = analyze_work_session()
        prediction = predict_next_action()

        elapsed = time.perf_counter() - start

        # Performance targets
        assert elapsed < 0.5, f"Workflow too slow: {elapsed:.3f}s"
        assert context["status"] == "success"
        assert analysis["status"] == "success"
        assert prediction["status"] == "success"
```

##### 1.2 統合テスト実行と結果分析
```bash
pytest tests/proactive/test_integration_week3.py -v --cov=clauxton --cov-report=term
```

##### 1.3 発見された問題をドキュメント化
- **File**: `docs/WEEK3_INTEGRATION_ISSUES.md`
- **内容**: 統合テストで発見された問題リスト

**成果物**:
- ✅ `tests/proactive/test_integration_week3.py` (20-25テスト)
- ✅ `docs/WEEK3_INTEGRATION_ISSUES.md`
- ✅ テスト実行レポート

**Commit**: `test(proactive): add Week 3 integration tests`

---

### 🔹 Stage 2: Phase 2.1-2.2 高優先度改善（Day 3後半） - 4-5時間

**目的**: 統合テストの結果を踏まえ、ドキュメントとテスト品質を向上

#### タスク

##### 2.1 ドキュメント改善
**File**: `clauxton/mcp/server.py`

**作業内容**:
1. 全MCPツールのdocstring拡充
2. Error modesセクション追加
3. 使用例追加（inline examples）
4. See Alsoセクション追加（cross-reference）

**テンプレート**:
```python
@mcp.tool()
def analyze_work_session() -> dict[str, Any]:
    """
    Analyze current work session for productivity insights.

    Provides detailed analysis of:
    - Session duration (minutes)
    - Focus score (0.0-1.0) based on file switching behavior
    - Break detection (15+ minute gaps)
    - Active work periods
    - File switch frequency

    Returns:
        dict: Work session analysis with structure:
            - status (str): "success", "error", or "no_session"
            - duration_minutes (int): Session duration
            - focus_score (float|None): Focus score 0.0-1.0
            - breaks (list[dict]): Detected breaks
            - file_switches (int): Unique files modified
            - active_periods (list[dict]): Active work periods
            - message (str|None): Status message
            - error (str|None): Error details

    Error Modes:
        - import_error: ContextManager module unavailable
        - validation_error: Invalid context data structure
        - runtime_error: Analysis calculation failed
        - no_session: No active files detected (not an error)

    Examples:
        >>> # Success case
        >>> result = analyze_work_session()
        >>> if result["status"] == "success":
        ...     print(f"Session: {result['duration_minutes']}min")
        ...     print(f"Focus: {result['focus_score']:.2f}")

        >>> # No session case
        >>> result = analyze_work_session()
        >>> if result["status"] == "no_session":
        ...     print("No active session detected")

    See Also:
        - get_current_context(): Get full project context
        - predict_next_action(): Predict next likely action
        - docs/mcp-server.md: Full MCP documentation

    Note:
        This tool uses a 30-second cache. Repeated calls within
        30 seconds will return cached results for performance.
    """
```

**対象ツール**:
- `analyze_work_session()`
- `predict_next_action()`
- `get_current_context()`

##### 2.2 テストassertion強化
**File**: `tests/proactive/test_mcp_context.py`

**作業内容**:
1. 全テストに範囲検証追加
2. データ構造検証強化
3. エッジケース検証追加

**改善パターン**:
```python
# Before
assert "focus_score" in result
assert isinstance(result["focus_score"], (int, float))

# After
assert "focus_score" in result
focus = result["focus_score"]
if focus is not None:
    assert isinstance(focus, (int, float)), f"Invalid type: {type(focus)}"
    assert 0.0 <= focus <= 1.0, f"focus_score out of range: {focus}"

# Before
assert "breaks" in result

# After
assert "breaks" in result
assert isinstance(result["breaks"], list), "breaks must be a list"
for i, brk in enumerate(result["breaks"]):
    assert "start" in brk, f"Break {i} missing 'start'"
    assert "end" in brk, f"Break {i} missing 'end'"
    assert "duration_minutes" in brk, f"Break {i} missing 'duration_minutes'"
    assert brk["duration_minutes"] > 0, f"Break {i} has invalid duration"
```

**対象テスト**:
- `test_analyze_work_session_*` (6テスト)
- `test_predict_next_action_*` (6テスト)
- `test_get_current_context_*` (3テスト)

**成果物**:
- ✅ MCPツールのdocstring改善（3ツール）
- ✅ テストassertion強化（15テスト）
- ✅ `docs/PHASE2_IMPROVEMENTS_PART1.md`

**Commit**: `docs(mcp): improve docstrings and test assertions`

---

### 🔹 Stage 3: Phase 2.3-2.5 コア改善（Day 4前半） - 5-6時間

**目的**: エラーハンドリング、コード品質、パフォーマンスを向上

#### タスク

##### 2.3 包括的エラーテスト追加
**File**: `tests/proactive/test_mcp_context.py`

**作業内容**:
1. エラータイプ別のテストクラス追加
2. エラーシナリオ網羅（15-20テスト）

**テストクラス**:
```python
class TestAnalyzeWorkSessionErrors:
    """Comprehensive error handling tests."""

    def test_import_error_handling(self, tmp_path, monkeypatch):
        """Test ImportError handling."""

    def test_validation_error_invalid_focus_score(self, tmp_path):
        """Test focus_score > 1.0 validation."""

    def test_validation_error_negative_duration(self, tmp_path):
        """Test negative duration validation."""

    def test_type_error_wrong_data_types(self, tmp_path):
        """Test wrong data type handling."""

    def test_key_error_missing_required_keys(self, tmp_path):
        """Test missing key handling."""

class TestPredictNextActionErrors:
    """Error tests for predict_next_action."""

    def test_import_error_context_manager_unavailable(self, tmp_path):
        """Test ContextManager import failure."""

    def test_validation_error_confidence_out_of_range(self, tmp_path):
        """Test confidence > 1.0 validation."""

    def test_runtime_error_prediction_logic_failure(self, tmp_path):
        """Test prediction calculation failure."""

class TestGetCurrentContextErrors:
    """Error tests for get_current_context."""

    def test_prediction_error_captured_in_response(self, tmp_path):
        """Test prediction_error field populated on failure."""

    def test_partial_context_on_git_failure(self, tmp_path):
        """Test context returned even if git fails."""

class TestEdgeCases:
    """Edge case tests for all MCP tools."""

    def test_empty_values_handling(self, tmp_path):
        """Test None values in all fields."""

    def test_unexpected_structure_handling(self, tmp_path):
        """Test extra keys in response."""

    def test_concurrent_calls_thread_safety(self, tmp_path):
        """Test thread safety."""

    def test_cache_expiration_mid_call(self, tmp_path):
        """Test cache expiration during call."""
```

**追加テスト数**: 15-20テスト

##### 2.4 コード重複削減
**File**: `clauxton/mcp/server.py`

**作業内容**:
1. Validation helper関数作成
2. 重複コードをヘルパーに置き換え

**Helper Functions**:
```python
def _validate_field_type(
    data: dict[str, Any],
    field: str,
    expected_types: type | tuple[type, ...],
    context: str,
) -> None:
    """Validate field type in data dict."""
    if field not in data:
        raise KeyError(f"Missing field '{field}' in {context}")

    value = data[field]
    if value is not None and not isinstance(value, expected_types):
        raise TypeError(
            f"Field '{field}' must be {expected_types}, "
            f"got {type(value)} in {context}"
        )

def _validate_field_range(
    data: dict[str, Any],
    field: str,
    min_val: float | None = None,
    max_val: float | None = None,
    context: str = "",
) -> None:
    """Validate field is within range."""
    if field not in data:
        return

    value = data[field]
    if value is None:
        return

    if min_val is not None and value < min_val:
        raise ValueError(
            f"Field '{field}' must be >= {min_val}, got {value} in {context}"
        )
    if max_val is not None and value > max_val:
        raise ValueError(
            f"Field '{field}' must be <= {max_val}, got {value} in {context}"
        )

def _validate_session_analysis(analysis: dict[str, Any]) -> None:
    """Validate session analysis structure."""
    _validate_field_type(analysis, "duration_minutes", int, "session analysis")
    _validate_field_range(analysis, "duration_minutes", min_val=0, context="session")

    _validate_field_type(analysis, "focus_score", (int, float), "session analysis")
    _validate_field_range(analysis, "focus_score", min_val=0.0, max_val=1.0, context="session")

    _validate_field_type(analysis, "breaks", list, "session analysis")
    _validate_field_type(analysis, "file_switches", int, "session analysis")
```

##### 2.5 パフォーマンス最適化
**作業内容**:
1. 重複validation削除（Pydanticに一任）
2. Optional validation追加

**Before**:
```python
def analyze_work_session() -> dict[str, Any]:
    try:
        analysis = context_mgr.analyze_work_session()

        # Manual validation
        _validate_session_analysis(analysis)

        # Pydantic validation (duplicate!)
        response = WorkSessionAnalysis(**analysis)
        return response.model_dump()
```

**After**:
```python
def analyze_work_session() -> dict[str, Any]:
    try:
        analysis = context_mgr.analyze_work_session()

        # Let Pydantic handle all validation
        response = WorkSessionAnalysis(**analysis)
        return response.model_dump()
    except ValidationError as e:
        logger.error(f"Session analysis validation failed: {e}")
        return _handle_mcp_error(e, "analyze_work_session")
```

**成果物**:
- ✅ 15-20個のエラーテスト追加
- ✅ Validation helper関数（3関数）
- ✅ パフォーマンス改善（10-20%）
- ✅ `docs/PHASE2_IMPROVEMENTS_PART2.md`

**Commit**: `refactor(mcp): improve error handling and reduce duplication`

---

### 🔹 Stage 4: Phase 3 + ドキュメント作成（Day 4後半-5前半） - 8-10時間

**目的**: 最終的な品質向上とユーザードキュメント作成

#### タスク

##### 3.1 Docstring標準化
**File**: `clauxton/mcp/server.py`

**作業内容**:
1. 全MCPツールをGoogle style統一
2. Cross-reference追加
3. 冗長な例をドキュメントに移動

##### 3.2 テストデータ品質向上
**File**: `tests/proactive/test_mcp_context.py`

**作業内容**:
1. `create_modified_files()` 改善
2. リアルなファイルコンテンツ生成
3. 多様なファイルタイプ

##### 3.3 ロギング強化
**File**: `clauxton/mcp/server.py`

**作業内容**:
1. パフォーマンスメトリクス追加
2. キャッシュヒット/ミスログ
3. デバッグログ拡充

##### 3.4 ユーザードキュメント作成
**Files**:
- `docs/guides/CONTEXT_INTELLIGENCE_GUIDE.md` - ユーザーガイド
- `docs/guides/WORKFLOW_EXAMPLES.md` - ワークフロー例
- `docs/guides/BEST_PRACTICES.md` - ベストプラクティス
- `docs/guides/TROUBLESHOOTING.md` - トラブルシューティング

**ユーザーガイド目次**:
```markdown
# Context Intelligence User Guide

## Introduction
- What is Context Intelligence?
- Key Features
- Benefits

## Getting Started
### Installation
### Configuration
### First Steps

## Core Concepts
### Work Session Analysis
- Session duration tracking
- Focus score calculation
- Break detection

### Action Prediction
- Prediction algorithm
- Confidence scores
- Supported actions

### Project Context
- Context components
- Caching behavior
- Customization

## Usage Examples
### Morning Workflow
### Development Session
### Evening Wrap-up

## Integration with Claude Code
### MCP Tool Usage
### Natural Language Queries
### Automation Patterns

## Advanced Topics
### Performance Tuning
### Custom Patterns
### Multi-Project Setup

## Troubleshooting
### Common Issues
### Debug Mode
### Support Resources
```

**成果物**:
- ✅ Phase 3改善完了（4タスク）
- ✅ ユーザードキュメント（4ファイル）
- ✅ `docs/PHASE3_IMPROVEMENTS.md`

**Commit**: `docs: add comprehensive user guides for Context Intelligence`

---

### 🔹 Stage 5: 最終調整とリリース準備（Day 5） - 6-8時間

**目的**: v0.13.0リリース準備完了

#### タスク

##### 5.1 mcp-server.mdの分割・整理
**作業内容**:
1. ドキュメント分割
   - `docs/mcp/core-tools.md` - KB, Task, Conflict tools
   - `docs/mcp/semantic-search.md` - Semantic Intelligence tools
   - `docs/mcp/context-intelligence.md` - Context Intelligence tools
   - `docs/mcp/overview.md` - MCP Server概要
2. Cross-reference追加
3. 目次とナビゲーション整備

##### 5.2 README.md更新
**File**: `README.md`

**作業内容**:
1. Context Intelligence機能追加
2. MCP Tools一覧更新（35 tools）
3. 統計情報更新（320+ tests, 90%+ coverage）
4. 使用例追加

##### 5.3 CHANGELOG.md更新
**File**: `CHANGELOG.md`

**作業内容**:
```markdown
## [0.13.0] - 2025-12-06

### Added - Context Intelligence
- **Work Session Analysis**: Track session duration, focus score, breaks
- **Action Prediction**: Context-aware next action prediction (9 actions)
- **Enhanced Project Context**: Git stats, session info, predictions
- **3 New MCP Tools**: `analyze_work_session`, `predict_next_action`, `get_current_context`

### Improved
- **Error Handling**: Standardized error responses with Pydantic models
- **Documentation**: Comprehensive user guides and workflow examples
- **Test Coverage**: 320+ tests (90%+ coverage)
- **Performance**: 10-20% improvement in MCP tool response time

### Fixed
- Prediction silent failures now properly surfaced
- Context validation edge cases handled
- Cache consistency issues resolved

### Documentation
- User Guide: Context Intelligence
- Workflow Examples
- Best Practices
- Troubleshooting Guide
```

##### 5.4 リリースノート作成
**File**: `docs/RELEASE_NOTES_v0.13.0.md`

**内容**:
- 主要機能の説明
- マイグレーションガイド
- Breaking changes（なし）
- Known issues

##### 5.5 品質チェック
```bash
# Full test suite
pytest --cov=clauxton --cov-report=html --cov-report=term

# Type checking
mypy clauxton --strict

# Linting
ruff check clauxton tests

# Performance benchmarks
pytest tests/proactive/test_context_performance.py -v

# Integration tests
pytest tests/proactive/test_integration_week3.py -v
```

##### 5.6 __version__.py更新
**File**: `clauxton/__version__.py`

```python
"""Version information for Clauxton."""

__version__ = "0.13.0"
```

**成果物**:
- ✅ ドキュメント整理完了
- ✅ README/CHANGELOG更新
- ✅ リリースノート作成
- ✅ 全品質チェック通過
- ✅ バージョン更新

**Commit**: `chore: prepare v0.13.0 release`

---

## 📊 予想成果物サマリー

### コード
- **新規ファイル**: 1個（`test_integration_week3.py`）
- **修正ファイル**: 3個（`server.py`, `test_mcp_context.py`, `__version__.py`）
- **新規テスト**: 35-45テスト
- **総テスト数**: 310-320テスト
- **カバレッジ**: 90%+

### ドキュメント
- **ユーザーガイド**: 4個
- **MCP分割ドキュメント**: 4個
- **改善レポート**: 3個
- **リリースノート**: 1個
- **総ページ数**: 2000-2500行

### 品質
- **Ruff**: 0 errors
- **Mypy**: 0 errors
- **Performance**: 10-20% improvement
- **Test Pass Rate**: 100%

---

## 🎯 マイルストーン

| Stage | 完了条件 | 推定時間 | 累計時間 |
|-------|---------|---------|---------|
| **Stage 1** | 統合テスト20+作成、実行成功 | 8-10h | 8-10h |
| **Stage 2** | ドキュメント改善、assertion強化 | 4-5h | 12-15h |
| **Stage 3** | エラーテスト15+追加、重複削減 | 5-6h | 17-21h |
| **Stage 4** | Phase 3完了、ユーザーガイド4個 | 8-10h | 25-31h |
| **Stage 5** | リリース準備完了、全チェック通過 | 6-8h | 31-39h |

**Total**: 31-39時間（5-6日）

---

## ✅ チェックリスト

### Stage 1: 統合テスト
- [ ] `test_integration_week3.py` 作成（20-25テスト）
- [ ] 全テスト実行成功
- [ ] 問題点ドキュメント化
- [ ] Commit: `test(proactive): add Week 3 integration tests`

### Stage 2: Phase 2.1-2.2
- [ ] MCPツールdocstring改善（3ツール）
- [ ] テストassertion強化（15テスト）
- [ ] ドキュメント作成
- [ ] Commit: `docs(mcp): improve docstrings and test assertions`

### Stage 3: Phase 2.3-2.5
- [ ] エラーテスト追加（15-20テスト）
- [ ] Validation helper作成
- [ ] パフォーマンス最適化
- [ ] Commit: `refactor(mcp): improve error handling and reduce duplication`

### Stage 4: Phase 3 + ドキュメント
- [ ] Docstring標準化
- [ ] テストデータ改善
- [ ] ロギング強化
- [ ] ドキュメント分割
- [ ] ユーザーガイド4個作成
- [ ] Commit: `docs: add comprehensive user guides for Context Intelligence`

### Stage 5: リリース準備
- [ ] README/CHANGELOG更新
- [ ] リリースノート作成
- [ ] 全品質チェック通過
- [ ] バージョン更新
- [ ] Commit: `chore: prepare v0.13.0 release`
- [ ] Git tag: `v0.13.0`

---

## 🚦 リスクと対策

### リスク1: 統合テストで重大な問題発見
**対策**: Stage 1で早期発見し、Stage 2-3で修正

### リスク2: 時間超過
**対策**: Stage 4のPhase 3を省略可能（v0.13.1へ延期）

### リスク3: テストカバレッジ90%未達
**対策**: Stage 3でエラーテストを重点的に追加

---

## 📞 次セッションでの開始方法

```bash
# 1. このドキュメントを確認
cat docs/WEEK3_OPTIMAL_PLAN_v0.13.0.md

# 2. 現在の状態を確認
git status
git log --oneline -5

# 3. テスト実行
source .venv/bin/activate
pytest tests/proactive/ -v

# 4. Stage 1開始
# tests/proactive/test_integration_week3.py を作成
```

---

**Last Updated**: 2025年10月27日
**Status**: 計画作成完了、Stage 1開始準備完了
**Next Action**: Stage 1の統合テスト作成を開始
