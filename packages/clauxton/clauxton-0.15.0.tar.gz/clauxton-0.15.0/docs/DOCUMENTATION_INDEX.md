# Clauxton Documentation Index

**Last Updated**: 2025-11-03
**Current Version**: v0.14.0 (Complete)
**Next Version**: v0.15.0 - Unified Memory Model (Planning)

---

## 📋 戦略文書 (Post-v0.14.0 Strategic Direction)

### 必読文書（優先順位順）

1. **[Strategic Summary](STRATEGIC_SUMMARY.md)** 🎯
   - Post-v0.14.0 戦略概要
   - 3つのコア価値
   - v0.15.0 Unified Memory Model 概要
   - 段階的削減計画（v0.15.0 → v0.16.0）
   - 市場ポジショニング概要
   - **読者**: 全員（開発者・ユーザー・ステークホルダー）
   - **推定読了時間**: 15分

2. **[Market Positioning](POSITIONING.md)** 📊
   - 市場分析（TAM/SAM/SOM）
   - 競合ポジショニングマップ
   - ターゲット市場セグメント
   - リスク評価
   - 段階的削減計画の詳細
   - **読者**: ステークホルダー、マーケター
   - **推定読了時間**: 30分

3. **[Development Roadmap](ROADMAP.md)** 🗺️
   - v0.15.0 Unified Memory Model 詳細
   - v0.16.0 Team & Collaboration 計画
   - v0.17.0+ Advanced Features 構想
   - 段階的削減のタイムライン
   - リリーススケジュール
   - **読者**: 開発者、プロジェクトマネージャー
   - **推定読了時間**: 45分

4. **[Deprecation Plan](DEPRECATION_PLAN.md)** 📉
   - 削除基準と原則
   - v0.15.0: Deprecation（削除なし）
   - v0.16.0: 実際の削除
   - テスト/ドキュメント修正計画
   - 動作保証チェックリスト
   - ロードマップとの整合性確認
   - **読者**: 開発者、ユーザー（移行準備）
   - **推定読了時間**: 60分

5. **[v0.15.0 Implementation Plan](v0.15.0_IMPLEMENTATION_PLAN.md)** 📝
   - 8週間詳細実装計画
   - Week 1-2: Core Integration
   - Week 3-4: Smart Memory
   - Week 5-6: Memory Intelligence
   - Week 7-8: UX Polish
   - コード例、テスト計画
   - **読者**: 開発者（実装担当）
   - **推定読了時間**: 90分

6. **[v0.15.0 Migration Validation](v0.15.0_MIGRATION_VALIDATION.md)** ✅
   - 動作保証の詳細
   - Backward compatibility 実装計画
   - テスト完全性の確保
   - ドキュメント修正計画
   - 開発フローの確認
   - リスク管理
   - **読者**: 開発者、QAエンジニア
   - **推定読了時間**: 60分

7. **[v0.15.0 SubAgent Plan](v0.15.0_SUBAGENT_PLAN.md)** 🤖
   - SubAgentを使った並列開発計画
   - 8週間 → 4-5週間への短縮戦略
   - 15 SubAgents の実行計画
   - Agent依存関係と実行順序
   - 3層品質保証戦略
   - **読者**: 開発者（実装リーダー）
   - **推定読了時間**: 75分

8. **[Quality Review Prompts](QUALITY_REVIEW_PROMPTS.md)** 📋
   - Phase完了後の品質レビュープロンプト集
   - 包括的品質レビュー（7カテゴリ）
   - 特定カテゴリの詳細レビュー
   - 改善タスク実行用プロンプト
   - 具体的な成果物定義
   - **読者**: 開発者（品質担当）、SubAgent実行者
   - **推定読了時間**: 45分

---

## 🔑 重要な戦略決定

### 1. "削減" ではなく "統合と深化"
- ❌ 単純な機能削減ではない
- ✅ Unified Memory Model による統合
- ✅ 自動化・知能化による深化
- ✅ 本質的価値への集中

### 2. 段階的削減による動作保証
- **v0.15.0** (2026-01-24): Deprecation のみ、**削除なし**
  - Backward compatibility layer 実装
  - 全機能が動作（警告付き）
  - Tests: 2,081 (+128)
- **v0.16.0** (2026-03-20): 実際の削除
  - Deprecated features 削除
  - Memory System のみ
  - Tests: 1,201 (-38% but >85% coverage)

### 3. 本質的価値への集中
**保持・強化**:
- ✅ 永続的記憶 (Memory System)
- ✅ 依存関係可視化 (Conflict Detection)
- ✅ チーム知識標準化 (Team Features)
- ✅ TUI (UX価値高い)

**削除**:
- ❌ Daily workflow commands (Claude Code 代替)
- ❌ 9言語サポート (使用率 < 3%)
- ❌ Real-time monitoring (On-demand で十分)
- ❌ 重複 MCP tools (Memory API に統合)

### 4. 市場ポジショニング
- **カテゴリー**: Project Memory System for AI Development (新カテゴリー創造)
- **キャッチコピー**: "Obsidian for Code Projects, Built for Claude"
- **TAM**: $43M, **SAM**: $2.9M, **SOM (5年)**: $580K-840K ARR
- **結論**: 副業/OSSプロジェクトとして適切、ニッチ市場リーダーシップ可能

---

## 📊 削減効果サマリー

| Metric | v0.14.0 | v0.15.0 | v0.16.0 | Change |
|--------|---------|---------|---------|--------|
| **MCP Tools** | 36 | 36* | 25 | -30% |
| **CLI Commands** | 40+ | 40+* | 20 | -50% |
| **Languages** | 12 | 12* | 3 | -75% |
| **Tests** | 1,953 | 2,081 | 1,201 | -38% |
| **LOC** | 15,000 | 17,000 | 10,000 | -33% |
| **Dependencies** | 25 | 25 | 16 | -36% |
| **CI Time** | 3m30s | 3m30s | 2m30s | -30% |

*v0.15.0: Deprecated but still working

---

## 🎯 ユーザー向けガイド

### v0.14.0 ユーザー（現在）
- ✅ 安定版を使い続ける
- 📣 v0.15.0 Beta テスター募集（2026-01-10頃）
- 📖 `docs/DEPRECATION_PLAN.md` を読んで移行準備

### v0.15.0 ユーザー（2026-01-24〜）
- ⚠️ Deprecation warnings を確認
- 📖 `docs/MIGRATION_GUIDE_v0.15.0.md` を読む
- 🔄 新しい Memory API を試す
- ✅ 既存コードは動作（警告付き）

### v0.16.0 ユーザー（2026-03-20〜）
- ✅ Memory System のみ使用
- ❌ KB/Task API は削除済み
- 📖 `docs/MEMORY_SYSTEM.md` 参照

---

## 👨‍💻 開発者向けガイド

### v0.15.0 実装開始（2025-11-27〜）
1. 📖 `docs/v0.15.0_IMPLEMENTATION_PLAN.md` を読む
2. 📖 `docs/v0.15.0_MIGRATION_VALIDATION.md` を読む
3. 🚀 Week 1 Day 1 から実装開始
4. 🧪 TDD approach: テストファースト開発

### 実装優先順位
- **Week 1-2**: Core Integration（最優先）
  - Memory Entry model
  - Backward compatibility layer
  - Migration script
- **Week 3-4**: Smart Memory
  - Auto-extraction from commits
  - Relationship detection
- **Week 5-6**: Memory Intelligence
  - Q&A system
  - Summarization
- **Week 7-8**: UX Polish
  - Guided workflows
  - TUI integration
  - Documentation

---

## 🔗 関連ドキュメント

### ユーザーガイド
- [Quick Start Guide](quick-start.md)
- [Developer Workflow Guide](DEVELOPER_WORKFLOW_GUIDE.md)
- [MCP Integration Guide](MCP_INTEGRATION_GUIDE.md)
- [TUI User Guide](TUI_USER_GUIDE.md)

### 技術文書
- [Architecture Overview](architecture.md)
- [Development Guide](development.md)
- [MCP Server Documentation](mcp-index.md)

### 将来作成予定
- `docs/MEMORY_SYSTEM.md` (v0.15.0)
- `docs/MIGRATION_GUIDE_v0.15.0.md` (v0.15.0)
- `docs/MEMORY_QUICK_START.md` (v0.15.0)
- `docs/MIGRATION_GUIDE_v0.15_to_v0.16.md` (v0.16.0)

---

## ✅ ドキュメント整合性確認

### 確認済み一貫性
- ✅ STRATEGIC_SUMMARY.md - 段階的削減反映
- ✅ POSITIONING.md - 段階的削減反映
- ✅ ROADMAP.md - 段階的削減反映
- ✅ DEPRECATION_PLAN.md - 動作保証追加
- ✅ v0.15.0_MIGRATION_VALIDATION.md - 詳細検証計画
- ✅ v0.15.0_IMPLEMENTATION_PLAN.md - 8週間実装計画
- ✅ v0.15.0_SUBAGENT_PLAN.md - 並列開発 + 品質保証戦略
- ✅ QUALITY_REVIEW_PROMPTS.md - 改善されたレビュープロンプト
- ✅ README.md - Strategic Documentation セクション追加

### キーメッセージの一貫性
すべてのドキュメントで以下が一貫:
1. ✅ v0.15.0 では削除しない（Deprecation のみ）
2. ✅ v0.16.0 で実際に削除
3. ✅ Backward compatibility で動作保証
4. ✅ >85% coverage 維持
5. ✅ Unified Memory Model がロードマップの基盤

---

## 📝 まとめ

### 戦略的方向性
- **"Obsidian for Code Projects, Built for Claude"**
- **Project Memory System for AI Development** (新カテゴリー)
- **"削減" ではなく "統合と深化"**

### 次のアクション
- **開発者**: v0.15.0 Week 1 実装開始（2025-11-27）
- **ユーザー**: v0.14.0 使用継続、v0.15.0 Beta 準備
- **ステークホルダー**: 市場ポジショニング確認、リスク評価

### 成功指標
- **v0.15.0**: 80% migration rate, 4.3+/5.0 satisfaction
- **v0.16.0**: 25 MCP tools, 1,201 tests, >85% coverage
- **Long-term**: $182K ARR (24-36ヶ月), ニッチ市場リーダーシップ

---

**Status**: 📋 Strategic Planning Complete
**Next Milestone**: v0.15.0 Implementation Start (2025-11-27)
**Last Updated**: 2025-11-03
