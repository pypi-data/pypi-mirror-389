# Phase 3 Integration Test Plan

**Version**: v0.15.0 Unified Memory Model
**Phase**: Phase 3 - Memory Intelligence
**Date**: 2025-11-03
**Status**: 🔄 In Progress

---

## 目的

Phase 3 (Memory Intelligence) の実装が Phase 1-2 と正しく統合されていることを確認し、エンドツーエンドのワークフローが期待通りに動作することを検証する。

---

## 統合テストのスコープ

### 1. Phase 2 ↔ Phase 3 統合テスト

#### 1.1 Memory Extraction → Question Answering
**シナリオ**: Git コミットから抽出したメモリに対して質問する

```bash
# Step 1: Extract memories from commits (Phase 2)
clauxton memory extract --limit 10 --auto-add

# Step 2: Ask questions about extracted memories (Phase 3)
clauxton memory ask "What decisions were made recently?"
```

**期待される結果**:
- [x] 抽出されたメモリが正しく保存される
- [ ] 質問に対して関連するメモリが返される
- [ ] 信頼度スコアが適切に計算される
- [ ] ソースコミットが追跡可能

**テストコマンド**:
```bash
pytest tests/integration/test_phase2_phase3_integration.py::test_extract_and_ask -v
```

#### 1.2 Memory Linking → Graph Visualization
**シナリオ**: リンクされたメモリの関係をグラフで可視化

```bash
# Step 1: Link related memories (Phase 2)
clauxton memory link --auto --threshold 0.7

# Step 2: Generate graph (Phase 3)
clauxton memory graph --format mermaid --output memory_graph.md
```

**期待される結果**:
- [ ] 関連メモリが正しくリンクされる
- [ ] グラフにリンクがエッジとして表示される
- [ ] ノードサイズが関係数を反映
- [ ] すべてのメモリタイプが正しく色分けされる

**テストコマンド**:
```bash
pytest tests/integration/test_phase2_phase3_integration.py::test_link_and_visualize -v
```

#### 1.3 Memory Extraction → Summarization
**シナリオ**: 抽出したメモリからプロジェクトサマリを生成

```bash
# Step 1: Extract memories from commits (Phase 2)
clauxton memory extract --limit 50 --auto-add

# Step 2: Generate summary (Phase 3)
clauxton memory summarize
```

**期待される結果**:
- [ ] アーキテクチャ決定が正しく抽出される
- [ ] 技術スタックが検出される
- [ ] 最近の変更がタイムスタンプ順に表示される
- [ ] 統計情報が正確

**テストコマンド**:
```bash
pytest tests/integration/test_phase2_phase3_integration.py::test_extract_and_summarize -v
```

---

### 2. エンドツーエンドワークフローテスト

#### 2.1 完全なメモリライフサイクル
**シナリオ**: メモリの作成 → リンク → 質問 → 可視化 → サマリ

```bash
# 1. Manual memory creation (Phase 1)
clauxton memory add --title "Switch to PostgreSQL" \
                    --type decision \
                    --category database \
                    --content "Migrate from MySQL for better JSONB support"

# 2. Extract from commits (Phase 2)
clauxton memory extract --limit 10 --auto-add

# 3. Auto-link memories (Phase 2)
clauxton memory link --auto

# 4. Ask questions (Phase 3)
echo "Q: Why did we switch to PostgreSQL?"
clauxton memory ask "Why PostgreSQL?"

# 5. Get task suggestions (Phase 3)
clauxton memory suggest-tasks --limit 5

# 6. Visualize (Phase 3)
clauxton memory graph --format mermaid

# 7. Generate summary (Phase 3)
clauxton memory summarize
```

**期待される結果**:
- [ ] すべてのコマンドがエラーなく実行される
- [ ] メモリが正しくリンクされる
- [ ] 質問に適切な回答が返される
- [ ] タスク提案が関連性が高い
- [ ] グラフが正しく生成される
- [ ] サマリが包括的

**テストコマンド**:
```bash
pytest tests/integration/test_e2e_workflow.py::test_full_memory_lifecycle -v
```

#### 2.2 MCP ツール統合ワークフロー
**シナリオ**: Claude Code から MCP ツールを使用した統合フロー

**期待される結果**:
- [ ] すべての MCP ツールが正常に動作
- [ ] Phase 2 と Phase 3 の MCP ツールが連携
- [ ] エラーハンドリングが適切
- [ ] レスポンス形式が一貫している

**テストコマンド**:
```bash
pytest tests/integration/test_mcp_integration.py -v
```

---

### 3. パフォーマンス統合テスト

#### 3.1 大規模プロジェクトでのパフォーマンス
**シナリオ**: 1,000+ メモリを含むプロジェクトでの動作

**テスト条件**:
- メモリ数: 1,000
- メモリタイプ: すべて (knowledge, decision, code, task, pattern)
- 関係数: 平均 3-5 per メモリ

**パフォーマンス目標**:
| 操作 | 目標 | 実測 | ステータス |
|------|------|------|-----------|
| Memory extraction (100 commits) | <30s | - | ⏳ |
| Memory linking (1,000 memories) | <60s | - | ⏳ |
| Question answering | <500ms | - | ⏳ |
| Summarization | <2s | - | ⏳ |
| Graph generation (100 nodes) | <2s | - | ⏳ |

**テストコマンド**:
```bash
pytest tests/integration/test_performance.py::test_large_project_performance -v
```

#### 3.2 並行操作のパフォーマンス
**シナリオ**: 複数の Phase 3 操作を並行実行

```python
# Pseudo-code for concurrent test
import concurrent.futures

with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
    future_qa = executor.submit(answer_question, "What is our API design?")
    future_summary = executor.submit(generate_summary)
    future_graph = executor.submit(generate_graph)

    results = [f.result() for f in [future_qa, future_summary, future_graph]]
```

**期待される結果**:
- [ ] 並行実行でデッドロックが発生しない
- [ ] 各操作が期待時間内に完了
- [ ] データ整合性が保たれる

**テストコマンド**:
```bash
pytest tests/integration/test_concurrent_operations.py -v
```

---

### 4. エッジケース統合テスト

#### 4.1 空のプロジェクト
**シナリオ**: メモリがゼロの状態での Phase 3 操作

```bash
# Empty project
clauxton memory ask "What is our tech stack?"
clauxton memory summarize
clauxton memory graph
clauxton memory suggest-tasks
```

**期待される結果**:
- [ ] エラーが発生しない
- [ ] 適切な "No data" メッセージが表示される
- [ ] 空のグラフが生成される

#### 4.2 非常に大きなメモリ
**シナリオ**: 10,000文字のメモリコンテンツ

**期待される結果**:
- [ ] 質問応答が正常に動作
- [ ] サマリ生成で切り詰めが適切に行われる
- [ ] グラフノードラベルが適切にトリミングされる

#### 4.3 特殊文字を含むメモリ
**シナリオ**: Unicode、絵文字、改行、コードブロックを含むメモリ

**期待される結果**:
- [ ] すべての操作が正常に動作
- [ ] エクスポート形式 (DOT, Mermaid, JSON) が有効

**テストコマンド**:
```bash
pytest tests/integration/test_edge_cases.py -v
```

---

### 5. 互換性テスト

#### 5.1 Phase 1 (Legacy) との互換性
**シナリオ**: 古い KB/Task 形式からの移行後の Phase 3 操作

**テストコマンド**:
```bash
pytest tests/integration/test_legacy_compatibility.py -v
```

#### 5.2 外部ツールとの統合
**シナリオ**: 生成された出力を外部ツールで使用

- **DOT → Graphviz**: `dot -Tpng graph.dot -o graph.png`
- **Mermaid → GitHub**: Markdown レンダリング
- **JSON → D3.js**: Web 可視化

**テストコマンド**:
```bash
pytest tests/integration/test_external_tools.py -v
```

---

## 統合テスト実行計画

### フェーズ 1: 基本統合テスト (30分)
```bash
# Phase 2 ↔ Phase 3 integration
pytest tests/integration/test_phase2_phase3_integration.py -v

# End-to-end workflows
pytest tests/integration/test_e2e_workflow.py -v
```

### フェーズ 2: パフォーマンステスト (1時間)
```bash
# Large project performance
pytest tests/integration/test_performance.py -v --benchmark

# Concurrent operations
pytest tests/integration/test_concurrent_operations.py -v
```

### フェーズ 3: エッジケース & 互換性 (30分)
```bash
# Edge cases
pytest tests/integration/test_edge_cases.py -v

# Legacy compatibility
pytest tests/integration/test_legacy_compatibility.py -v

# External tools
pytest tests/integration/test_external_tools.py -v
```

### フェーズ 4: MCP 統合テスト (30分)
```bash
# MCP tools integration
pytest tests/integration/test_mcp_integration.py -v
```

**合計予想時間**: 2.5時間

---

## 成功基準

### 必須 (Must Have)
- [ ] すべての Phase 2 ↔ Phase 3 統合テストが通過
- [ ] エンドツーエンドワークフローが完全に動作
- [ ] パフォーマンス目標を達成
- [ ] MCP ツールがすべて正常に動作

### 推奨 (Should Have)
- [ ] エッジケーステストが 90% 以上通過
- [ ] 並行操作で問題なし
- [ ] 外部ツールとの統合が確認できる

### オプション (Nice to Have)
- [ ] パフォーマンスが目標の 2倍速い
- [ ] カバレッジが 95% 以上
- [ ] すべてのエッジケースでグレースフルな動作

---

## リスクと対応策

| リスク | 影響度 | 対応策 |
|-------|--------|--------|
| Phase 2 との非互換性 | 高 | API の再設計、アダプタパターンの使用 |
| パフォーマンス目標未達 | 中 | キャッシング、インデックス最適化 |
| MCP ツールのエラー | 中 | エラーハンドリング改善、フォールバック実装 |
| 大規模データでのメモリ不足 | 低 | ストリーミング処理、ページネーション |

---

## 次のアクション

1. **今すぐ**: 基本統合テストの実装を開始
2. **今日中**: Phase 1 の統合テスト実行
3. **明日**: Phase 2-4 の統合テスト実行
4. **週末まで**: すべての統合テストを完了

---

**最終更新**: 2025-11-03
**次回レビュー**: 統合テスト完了後
