# TODO: v0.13.0 Deferred Tasks

**Created**: 2025年10月27日
**Status**: Week 3 Day 2 完了後に延期されたタスク
**Target**: v0.13.1 または v0.14.0 で対応

---

## 📋 概要

Week 3 Day 2 のコードレビューで特定された25個の課題のうち、Phase 1（高優先度6個）は完了。
残りの Phase 2（中優先度15個）と Phase 3（低優先度4個）を記録。

**Phase 1 完了状況**: ✅ 6/6 完了（100%）
**Phase 2 未対応**: ⏳ 0/15 完了（0%）
**Phase 3 未対応**: ⏳ 0/4 完了（0%）

---

## 🔥 Phase 2: 中優先度タスク（15 issues）

**優先度**: Medium
**推定工数**: 4-6時間
**対応時期**: v0.13.1 または v0.14.0
**詳細ドキュメント**: `docs/WEEK3_DAY2_HANDOFF_NEXT.md#phase-2`

### 2.1 ドキュメント改善

- [ ] **Task**: `predict_next_action()` の failure mode ドキュメント追加
  - **File**: `clauxton/mcp/server.py:3228-3307`
  - **What**: Error Modes セクション追加（import_error, validation_error, runtime_error）
  - **Examples**: Success/Error case の例を追加
  - **Effort**: 30分

- [ ] **Task**: `analyze_work_session()` の failure mode ドキュメント追加
  - **File**: `clauxton/mcp/server.py:3141-3225`
  - **What**: Error Modes セクション追加
  - **Effort**: 30分

- [ ] **Task**: `get_current_context()` の `prediction_error` フィールド説明追加
  - **File**: `clauxton/mcp/server.py:3310-3408`
  - **What**: prediction_error フィールドの説明とエラーハンドリング例
  - **Effort**: 20分

- [ ] **Task**: Pydantic モデルの詳細 docstring 追加
  - **File**: `clauxton/core/models.py:390-488`
  - **What**: MCPErrorResponse, WorkSessionAnalysis, NextActionPrediction, CurrentContextResponse の詳細説明
  - **Effort**: 1時間

**小計**: 2時間20分

### 2.2 テスト assertion 強化

- [ ] **Task**: `test_analyze_work_session_*` テストの range validation 追加
  - **File**: `tests/proactive/test_mcp_context.py:76-213`
  - **Tests**: 6テスト全て
  - **What**: focus_score (0.0-1.0), duration (>=0), breaks 構造の詳細検証
  - **Example**:
    ```python
    assert 0.0 <= result["focus_score"] <= 1.0
    for brk in result["breaks"]:
        assert "start" in brk and "end" in brk
        assert brk["duration_minutes"] >= 0
    ```
  - **Effort**: 1時間

- [ ] **Task**: `test_predict_next_action_*` テストの range validation 追加
  - **File**: `tests/proactive/test_mcp_context.py:215-394`
  - **Tests**: 6テスト全て
  - **What**: confidence (0.0-1.0), action の妥当性検証
  - **Effort**: 1時間

- [ ] **Task**: `test_get_current_context_*` テストの range validation 追加
  - **File**: `tests/proactive/test_mcp_context.py:396-490`
  - **Tests**: 3テスト全て
  - **What**: 全フィールドの型・範囲検証
  - **Effort**: 45分

**小計**: 2時間45分

### 2.3 包括的エラーテスト追加

- [ ] **Task**: `TestAnalyzeWorkSessionErrors` クラス作成
  - **File**: `tests/proactive/test_mcp_context.py`（新規追加）
  - **Tests**: 4-5テスト
    - `test_import_error_handling`: ImportError シナリオ
    - `test_validation_error_handling`: ValueError シナリオ（focus_score > 1.0 等）
    - `test_type_error_handling`: TypeError シナリオ（duration が str 等）
    - `test_key_error_handling`: KeyError シナリオ（必須キー欠落）
  - **Effort**: 1時間30分

- [ ] **Task**: `TestPredictNextActionErrors` クラス作成
  - **File**: `tests/proactive/test_mcp_context.py`（新規追加）
  - **Tests**: 4-5テスト
    - 同様のエラーシナリオ
  - **Effort**: 1時間30分

- [ ] **Task**: `TestGetCurrentContextErrors` クラス作成
  - **File**: `tests/proactive/test_mcp_context.py`（新規追加）
  - **Tests**: 4-5テスト
    - 同様のエラーシナリオ + invalid parameter テスト
  - **Effort**: 1時間30分

- [ ] **Task**: `TestEdgeCases` クラス作成
  - **File**: `tests/proactive/test_mcp_context.py`（新規追加）
  - **Tests**: 4-5テスト
    - `test_empty_values`: None/空値ハンドリング
    - `test_unexpected_structure`: 予期しない構造
    - `test_concurrent_calls`: 並行呼び出しのスレッドセーフティ
    - `test_cache_expiration`: キャッシュ期限切れ
  - **Effort**: 2時間

**小計**: 6時間30分（Phase 2 で最大の工数）

### 2.4 コードの重複削減

- [ ] **Task**: Validation helper 関数の作成
  - **File**: `clauxton/mcp/server.py`（新規追加: lines ~160-200）
  - **Functions**:
    - `_validate_field_type()`
    - `_validate_field_range()`
  - **Effort**: 1時間

- [ ] **Task**: `_validate_session_analysis()` のリファクタリング
  - **File**: `clauxton/mcp/server.py:108-134`
  - **What**: 新しい helper 関数を使用
  - **Effort**: 30分

- [ ] **Task**: `_validate_prediction()` のリファクタリング
  - **File**: `clauxton/mcp/server.py:137-152`
  - **What**: 新しい helper 関数を使用
  - **Effort**: 30分

**小計**: 2時間

### 2.5 パフォーマンス最適化

- [ ] **Task**: Pydantic validation のみに一本化（重複削除）
  - **File**: `clauxton/mcp/server.py:3141-3408`
  - **What**: Manual validation (`_validate_*`) を削除し、Pydantic に一任
  - **Impact**: 10-20% パフォーマンス向上
  - **Effort**: 1時間30分

- [ ] **Task**: パフォーマンステスト追加
  - **File**: `tests/proactive/test_performance.py`（既存）
  - **Tests**: MCP tool response time benchmarks
  - **Effort**: 1時間

**小計**: 2時間30分

---

### Phase 2 合計工数: 16時間5分

**Note**: 当初の推定（4-6時間）より多い理由:
- テスト追加が予想より大規模（15-20テスト）
- エラーテストの網羅性を高める必要がある

**推奨アプローチ**:
1. **Quick Win**: 2.1 + 2.2 のみ実施（5時間）→ v0.13.1
2. **Full Phase 2**: 全て実施（16時間）→ v0.14.0

---

## 🔹 Phase 3: 低優先度タスク（4 issues）

**優先度**: Low
**推定工数**: 2-3時間
**対応時期**: v0.14.0 または v0.15.0
**詳細ドキュメント**: `docs/WEEK3_DAY2_HANDOFF_NEXT.md#phase-3`

### 3.1 Docstring 標準化

- [ ] **Task**: 全 MCP tools の docstring を Google style に統一
  - **Files**: `clauxton/mcp/server.py`（32 tools）
  - **What**: 統一されたフォーマット、Cross-reference 追加
  - **Effort**: 2時間

- [ ] **Task**: 例をドキュメントに移動
  - **Files**: `docs/mcp/examples.md`（新規作成）
  - **What**: Docstring から例を抽出し、専用ドキュメント作成
  - **Effort**: 1時間

**小計**: 3時間

### 3.2 テストデータ品質向上

- [ ] **Task**: `create_modified_files()` の改善
  - **File**: `tests/proactive/test_mcp_context.py:55-74`
  - **What**:
    - 多様なファイルタイプ（.py, .md, .json, .yaml, .ts）
    - Realistic content（実際のコード/ドキュメント）
    - 非均一な時間分布（exponential decay）
  - **Effort**: 1時間

- [ ] **Task**: Unicode/特殊文字のテストデータ追加
  - **File**: `tests/proactive/test_mcp_context.py`（新規テスト）
  - **Tests**: 2-3テスト
  - **Effort**: 30分

**小計**: 1時間30分

### 3.3 ロギング強化

- [ ] **Task**: MCP tools にパフォーマンスログ追加
  - **Files**: `clauxton/mcp/server.py:3141-3408`
  - **What**:
    - ツール開始/終了ログ（duration 付き）
    - 主要ステップのデバッグログ
    - キャッシュヒット/ミスのログ
  - **Effort**: 1時間30分

- [ ] **Task**: Structured logging の導入
  - **Files**: `clauxton/utils/logger.py`（既存）
  - **What**: JSON 形式のログ、context 付きログ
  - **Effort**: 1時間

**小計**: 2時間30分

### 3.4 ドキュメント整理

- [ ] **Task**: `docs/mcp-server.md` のセクション分割
  - **New Files**:
    - `docs/mcp/context-intelligence.md` (Week 3 ツール)
    - `docs/mcp/semantic-search.md` (Week 2 ツール)
    - `docs/mcp/core-tools.md` (基本ツール)
  - **Effort**: 2時間

- [ ] **Task**: Cross-reference の追加
  - **Files**: All `docs/mcp/*.md`
  - **What**: See Also セクション、リンク追加
  - **Effort**: 1時間

**小計**: 3時間

---

### Phase 3 合計工数: 10時間

**Note**: 当初の推定（2-3時間）より多い理由:
- Docstring 統一が全32ツールで大規模
- ドキュメント分割が予想より複雑

**推奨アプローチ**:
- Phase 3 は v0.15.0 以降へ延期
- または、3.1 と 3.4 のみ実施（v0.14.0）

---

## 🎯 対応優先順位

### High Priority (v0.13.1 で対応推奨)
1. **2.2 テスト assertion 強化** (2時間45分)
   - テスト品質の即効性のある改善
2. **2.1 ドキュメント改善** (2時間20分)
   - ユーザー体験の向上

**合計**: 5時間5分（1日で完了可能）

### Medium Priority (v0.14.0 で対応)
3. **2.3 包括的エラーテスト追加** (6時間30分)
   - エラーハンドリングの信頼性向上
4. **2.4 コードの重複削減** (2時間)
   - メンテナンス性向上
5. **2.5 パフォーマンス最適化** (2時間30分)
   - レスポンス速度改善

**合計**: 11時間（Phase 2 残り）

### Low Priority (v0.15.0 で対応)
6. **3.1 Docstring 標準化** (3時間)
7. **3.4 ドキュメント整理** (3時間)

**合計**: 6時間（Phase 3 重要項目）

### Very Low Priority (将来対応)
- 3.2 テストデータ品質向上
- 3.3 ロギング強化

---

## 📝 対応開始時のチェックリスト

### v0.13.1 で Phase 2（一部）対応する場合

1. **準備**:
   ```bash
   git checkout -b feature/code-improvements-v0.13.1
   ```

2. **優先実施**（推奨順）:
   - [ ] 2.2 テスト assertion 強化（2時間45分）
   - [ ] 2.1 ドキュメント改善（2時間20分）
   - [ ] 2.4 コードの重複削減（2時間）- Optional

3. **テスト**:
   ```bash
   pytest tests/proactive/test_mcp_context.py -v
   pytest --cov=clauxton --cov-report=term
   ```

4. **品質チェック**:
   ```bash
   ruff check clauxton/ tests/
   mypy clauxton/
   ```

5. **コミット**:
   ```bash
   git add .
   git commit -m "refactor(mcp): Phase 2 improvements - test assertions and documentation"
   ```

### v0.14.0 で Phase 2（完全）対応する場合

1. **Phase 2 全タスクを実施**（16時間）
2. **テストカバレッジ目標**: 88-89%（+15-20テスト）
3. **パフォーマンス目標**: 10-20% 向上

### Phase 3 対応する場合

- v0.15.0 のマイルストーンで計画

---

## 🔗 関連ドキュメント

**このTODO作成の元ドキュメント**:
- `docs/WEEK3_DAY2_HANDOFF_NEXT.md`: 新セッション用ハンドオフ
- `docs/WEEK3_DAY2_CODE_IMPROVEMENTS.md`: Phase 1 完了詳細

**コードレビュー元**:
- Week 3 Day 2 Code Review（口頭での25個の課題特定）

**実装ファイル**:
- `clauxton/core/models.py`: Pydantic モデル
- `clauxton/mcp/server.py`: MCP ツール実装
- `tests/proactive/test_mcp_context.py`: テスト

---

## ✅ 完了時の更新

各タスク完了時に:
1. チェックボックスにチェック
2. Commit hash を記録
3. 所要時間を記録（推定との比較）

**Example**:
```markdown
- [x] **Task**: テスト assertion 強化
  - **Commit**: `abc1234`
  - **Effort**: 3時間（推定: 2時間45分、+15分）
  - **Notes**: Unicode テストも追加したため時間超過
```

---

**Last Updated**: 2025年10月27日
**Status**: 未着手
**Next Review**: v0.13.1 計画時 または v0.14.0 計画時
