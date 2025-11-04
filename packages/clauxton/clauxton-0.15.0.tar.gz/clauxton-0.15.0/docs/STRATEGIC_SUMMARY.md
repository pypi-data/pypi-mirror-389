# Clauxton Strategic Summary (Post-v0.14.0)

**Date**: 2025-11-03
**Current Version**: v0.14.0 (Complete)
**Next Version**: v0.15.0 - Unified Memory Model (Planning)

---

## Executive Summary

Clauxton は v0.14.0 完成後、**戦略的転換点** を迎えました。

### 従来の課題
- 36個のMCPツール、多数の機能
- しかし「何でもできる = 何が得意か不明」
- 市場ポジショニングが曖昧
- 競合との差別化が不明瞭

### 新しい方向性
**"削減" ではなく "本質に沿ってブラッシュアップ"**

**コアコンセプト**: "Obsidian for Code Projects, Built for Claude"
**市場カテゴリー**: Project Memory System for AI Development (新カテゴリー創造)

---

## 3つのコア価値

### 1. プロジェクトの永続的な記憶 (4/5 価値)
Claude Code は 200K tokens しか保持できない。
Clauxton はすべての設計判断・アーキテクチャ決定を永続保存し、セマンティック検索で即座に参照可能にする。

**競合との違い**:
- Notion: 手動管理、Claude統合なし
- GitHub Issues: タスク管理特化、知識管理弱い
- Obsidian: Claude統合なし、コード理解なし

### 2. タスク依存関係の可視化 (3/5 価値)
DAG による自動依存関係検出とファイルレベルのコンフリクト予測。

**競合との違い**:
- Linear: 依存関係管理あり、但しコンフリクト予測なし
- GitHub Projects: 基本的な依存関係のみ

### 3. チーム知識の標準化 (3/5 価値)
統一されたKnowledge Base で新メンバーのオンボーディング時間を短縮。

**競合との違い**:
- Notion: 汎用的すぎる、コード特化なし
- Confluence: 重い、AI統合なし

---

## 次期バージョン: v0.15.0 Unified Memory Model

### 戦略: 統合と深化

**Before (Fragmented)**:
```
Knowledge Base  →  kb_add(), kb_search(), ...
Task Management →  task_add(), task_list(), ...
Repository Map  →  index_repository(), ...
Code Analysis   →  analyze_commits(), ...
```

**After (Unified)**:
```
Memory System   →  memory_add(), memory_search(), ...
                   - type: knowledge | decision | code | task | pattern
                   - Auto-extraction from commits
                   - Automatic relationships
                   - Question-answering
```

### 主要機能

1. **Unified Memory Entry**: すべてをMemory Entryとして統一
2. **Smart Memory**: コミット/コードから自動抽出
3. **Memory Intelligence**: 質問応答、関連付け、予測
4. **Backward Compatibility**: 既存API保持（段階的移行）

### 実装計画 (8週間)

| Week | Focus | Deliverables |
|------|-------|-------------|
| 1-2 | Core Integration | Memory model, storage, migration |
| 3-4 | Smart Memory | Auto-extraction, relationship detection |
| 5-6 | Memory Intelligence | Q&A, summarization, prediction |
| 7-8 | UX Polish | Guided workflows, TUI, documentation |

**目標**: 2026-01-24 リリース

### 削減計画: 段階的削除による本質への集中

**戦略**: "統合と深化" + 動作保証 + 段階的削除

#### 段階的削減のタイムライン

| Phase | Action | Status |
|-------|--------|--------|
| **v0.15.0** (2026-01-24) | Deprecation 警告追加 | **削除なし、全機能動作** |
| **v0.16.0** (2026-03-20) | 実際に削除 | Memory System のみ |

#### v0.15.0: Deprecation（削除なし）

**重要**: v0.15.0 では何も削除しない。Backward compatibility layer で既存機能を保持。

**実装内容**:
- ✅ Memory System 実装 (7 new MCP tools)
- ✅ Backward compatibility layer 実装
- ⚠️ Deprecation warnings 追加
- ✅ **KB/Task/Daily commands は全て動作**
- ✅ Tests: 2,081 (+128 from v0.14.0)

**Deprecated (but working) features**:
```
⚠️ kb_add(), kb_search() → memory_add(), memory_search()
⚠️ task_add(), task_list() → memory_add(), memory_search()
⚠️ clauxton morning/daily/weekly → Claude Code で代替推奨
⚠️ Go/Rust/Java等 9言語 → Python/JS/TS 推奨
⚠️ Real-time monitoring → On-demand 推奨
```

#### v0.16.0: 実際の削除

**削除対象**:
- ❌ Backward compatibility layer
- ❌ KB/Task MCP tools (11 tools)
- ❌ Daily workflow commands (8 commands)
- ❌ Legacy language parsers (9 languages)
- ❌ Real-time monitoring

**削減効果**:

| Metric | v0.14.0 | v0.15.0 | v0.16.0 | Change |
|--------|---------|---------|---------|--------|
| MCP tools | 36 | 36* | 25 | -30% |
| CLI commands | 40+ | 40+* | 20 | -50% |
| Languages | 12 | 12* | 3 | -75% |
| Tests | 1,953 | 2,081 | 1,201 | -38% |
| LOC | 15,000 | 17,000 | 10,000 | -33% |

*v0.15.0: Deprecated but still working

#### 本質への集中

**保持・強化 (コア価値)**:
- ✅ 永続的記憶 (Memory System)
- ✅ 依存関係可視化 (Conflict Detection)
- ✅ チーム知識標準化 (Team Features)
- ✅ TUI (UX価値高い)

**削除 (非本質)**:
- ❌ Daily workflow commands (Claude Code で代替)
- ❌ 9言語サポート (使用率 < 10%)
- ❌ Real-time monitoring (On-demand で十分)
- ❌ 重複 MCP tools (Memory API に統合)

#### 動作保証

1. ✅ **v0.15.0**: Backward compatibility layer で全機能動作
2. ✅ **Migration script**: KB/Task → Memory 自動変換
3. ✅ **Testing**: >85% coverage 維持 (2,081 → 1,201 tests)
4. ✅ **Documentation**: 完全な Migration Guide
5. ✅ **Roadmap**: v0.16.0 Team Features は Memory System で実現

詳細: `docs/DEPRECATION_PLAN.md`, `docs/v0.15.0_MIGRATION_VALIDATION.md`

---

## 市場ポジショニング

### ターゲット市場

| セグメント | 市場規模 | ARPU | 特徴 |
|-----------|---------|------|------|
| 複数プロジェクトを持つ個人開発者 | 50K-100K | $15-29/年 | 3-5個のプロジェクト同時進行 |
| 長期プロジェクトの開発者 | 20K-50K | $29-49/年 | 1-2年以上継続プロジェクト |
| 小規模チーム (2-5人) | 10K-30K | $99-199/年/チーム | スタートアップ、全員Claude使用 |

### 市場規模の現実的試算

**TAM**: $30M-43M (Claude Pro ユーザー全体)
**SAM**: $2.9M (長期/複数プロジェクトユーザー)
**SOM (5年)**: $580K-840K ARR

**結論**:
- 🟢 副業/OSSプロジェクトとして適切
- 🔴 フルタイムビジネスとしては小さい
- 🟡 ニッチ市場でのリーダーシップは可能

### 競合ポジショニング

```
AI Integration (深い統合)
        ↑
    100 |
        |                        ● Clauxton (90, 85)
     80 |
        |
     60 |              ● Cursor Projects (60, 40)
        |
     50 |    ● Notion AI (50, 70)      ● Linear (55, 50)
        |
     40 |                        ● GitHub Issues (40, 30)
        |
     20 |    ● Obsidian (20, 80)
        |
      0 |_____________________________________________→
        0   10  20  30  40  50  60  70  80  90  100
                    Knowledge Management (強い管理)
```

**差別化ポイント**:
1. ⭐⭐⭐⭐⭐ Claude Code ネイティブ統合 (MCP)
2. ⭐⭐⭐⭐⭐ コミットから自動抽出
3. ⭐⭐⭐⭐⭐ 質問応答機能
4. ⭐⭐⭐⭐⭐ コード理解に特化
5. ⭐⭐⭐⭐⭐ 記憶の自動関連付け

---

## ロードマップ (改訂版)

| Version | Focus | Target Date | Status |
|---------|-------|-------------|--------|
| v0.14.0 | Interactive TUI | 2025-10-28 | ✅ Complete |
| **v0.15.0** | **Unified Memory Model** | **2026-01-24** | **📋 Planning** |
| v0.16.0 | Team & Collaboration | 2026-03-20 | 📋 Planned |
| v0.17.0+ | Advanced Features | TBD | 🔮 User-Driven |

### フェーズ移行の理由

**v0.15.0 (Web Dashboard) → v0.15.0 (Unified Memory Model)**

**旧計画**: Web Dashboard, 可視化、チーム機能
**問題点**: 本質的価値よりもUI重視、差別化不明確

**新計画**: Unified Memory Model, 統合と深化
**理由**:
- コア価値（永続的記憶）の強化
- 自動化による UX 向上
- 競合との明確な差別化
- 市場ポジショニングの明確化

**v0.16.0 (Advanced AI) → v0.16.0 (Team & Collaboration)**

**理由**:
- Team market は具体的ニーズあり（$3K+ ARR 潜在的）
- Advanced AI は価値不明確（"Claude Code と何が違う？"）
- 段階的な市場拡大戦略

---

## 成功指標 (KPI)

### v0.15.0 リリース後 (3ヶ月)
- 🎯 Memory 統合率: 80%+ (KB/Task からの移行)
- ⚡ 自動抽出利用率: 50%+
- 💬 Q&A 機能利用率: 40%+
- ❤️ ユーザー満足度: 4.3+/5.0
- ⭐ GitHub stars: 500+
- 📥 PyPI downloads: 20K/月

### 長期 (24-36ヶ月)
- 👤 Active users: 10,000人
- 💰 Individual Pro: $58K ARR (2,000人)
- 👥 Team ARR: $74.5K (500チーム)
- 🏢 Enterprise ARR: $49.9K (10社)
- **Total ARR**: **$182K** (現実的目標)

**Note**: 当初目標 $580K-840K を $182K に修正（2-3年目標）

---

## リスク評価

### リスク1: Claude Code のネイティブ機能追加 (確率: 50%)
**影響**: 個人ユーザーの80%流出可能性
**対策**:
- Anthropic との協業（公式プラグイン化）
- チーム機能・カスタマイズ性の強化
- エンタープライズ向けセルフホスト

### リスク2: Notion の Claude 統合強化 (確率: 30%)
**影響**: 知識管理セグメントの競合激化
**対策**:
- コード特化の価値強調
- 自動抽出・依存関係検出など開発者特化機能
- Notion との連携（競合ではなく補完）

### リスク3: 市場規模の限界 (確率: 80%)
**現実**: 5年で $580K ARR が天井
**対策**:
- OSS として継続（収益化は副次的）
- 企業スポンサーシップモデル
- 関連ツールへのピボット検討

---

## ポジショニング・ステートメント

**For** 長期プロジェクトまたは複数プロジェクトに取り組み、過去の決定やコンテキストを忘れてしまう Claude Code ユーザー

**Who** プロジェクトの設計判断、コード構造、変更履歴を統合された記憶として保存し、いつでも検索・参照可能にしたい

**Clauxton is a** Project Memory System for AI Development

**That** Claude Code とネイティブ統合し、コミット/コードから自動的に記憶を抽出し、質問応答により知識を活用可能にする

**Unlike** Notion（汎用的）や Linear（タスク特化）や Obsidian（AI統合なし）

**Clauxton** はコード理解に特化し、Claude Code ネイティブ統合、自動抽出、質問応答機能により開発者の記憶を拡張する

---

## 次のアクション

### 開発者向け (実装開始)
1. ✅ 戦略文書レビュー (このドキュメント)
2. 📖 `docs/v0.15.0_IMPLEMENTATION_PLAN.md` を読む
3. 🚀 Week 1 Day 1 から実装開始 (2025-11-27)
4. 🧪 TDD approach: テストファースト開発

### ユーザー向け (現在)
1. ✅ v0.14.0 を使い続ける (安定版)
2. 📣 フィードバック提供 (GitHub Issues/Discussions)
3. 🧪 v0.15.0 Beta テスター登録 (2026-01-10頃)

### コミュニティ向け
1. 💡 GitHub Discussions で議論参加
2. 🔀 PRs welcome (特に documentation, tests)
3. ⭐ GitHub Star で応援

---

## ドキュメント構成

この戦略転換に関連する完全なドキュメントセット:

1. **`STRATEGIC_SUMMARY.md`** (このファイル) - 戦略概要
2. **`POSITIONING.md`** - 市場ポジショニング詳細分析
3. **`ROADMAP.md`** - 改訂ロードマップ (v0.15.0+)
4. **`v0.15.0_IMPLEMENTATION_PLAN.md`** - 8週間実装計画

すべて `docs/` ディレクトリに配置。

---

## まとめ: "本質に沿ってブラッシュアップ"

### Before (v0.14.0)
- 36個のMCPツール
- 多機能だが焦点不明確
- 競合との差別化曖昧
- "何でもできる = 何が得意か不明"

### After (v0.15.0+)
- Unified Memory Model (統合)
- Auto-extraction & Intelligence (深化)
- "Obsidian for Code Projects, Built for Claude" (明確な positioning)
- Project Memory System (新カテゴリー)

### キーワード
- ❌ 削減 (reduction)
- ✅ 統合と深化 (integration and deepening)
- ✅ 本質の研ぎ澄まし (sharpening the essence)
- ✅ 新カテゴリー創造 (category creation)

---

**Prepared by**: Claude Code Strategic Review
**Last updated**: 2025-11-03
**Status**: 📋 Ready for Implementation
**Next Milestone**: v0.15.0 Release (2026-01-24)
