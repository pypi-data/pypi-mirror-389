# Clauxton Strategic Positioning

**Last Updated**: 2025-11-03
**Version**: Post-v0.14.0 Strategic Refinement

## Executive Summary

Clauxton は、**Project Memory System for AI Development** という新しいカテゴリーを創造するプロダクトです。Claude Code のユーザーが長期プロジェクトや複数プロジェクトで過去の決定やコンテキストを忘れてしまう問題に対し、設計判断・コード構造・変更履歴を統合された記憶として保存し、いつでも検索・参照可能にします。

**キャッチコピー**: "Obsidian for Code Projects, Built for Claude"

---

## 戦略的方向性の転換

### これまでの課題
- 36個のMCPツール、多数の機能を持つが「何が得意か不明確」
- Multi-Agent、TUI、Web Dashboard など散在した機能ロードマップ
- 競合との差別化が不明瞭
- 市場ポジショニングが曖昧

### 新しいアプローチ: "本質に沿ってブラッシュアップ"
削減ではなく、**統合と深化**による本質の研ぎ澄まし:

1. **Unified Memory Model**: KB、Task、Repository Map、Code を統合
2. **Smart Memory**: コミット/コードから自動抽出
3. **Memory Intelligence**: 質問応答、関連付け、予測
4. **Developer-Specific**: コード理解に特化

### 具体的な削減と統合（段階的）

#### 段階的削減のタイムライン

| Phase | MCP Tools | CLI Cmds | Languages | Tests | LOC |
|-------|-----------|----------|-----------|-------|-----|
| v0.14.0 | 36 | 40+ | 12 | 1,953 | 15,000 |
| **v0.15.0** | **36*** | **40+*** | **12*** | **2,081** | **17,000** |
| v0.16.0 | 25 | 20 | 3 | 1,201 | 10,000 |

*v0.15.0: Deprecated but still working (Backward compatibility)

#### v0.15.0 (2026-01-24): Deprecation（削除なし）

**重要**: 何も削除しない。全機能が動作する。

**実装**:
```
✅ Memory System 実装 (7 new MCP tools)
✅ Backward compatibility layer
⚠️ Deprecation warnings
✅ KB/Task API は動作（内部で Memory API 使用）
✅ Daily commands は動作（警告表示）
✅ 12言語は動作（3言語以外は警告）
```

**Example**:
```bash
$ clauxton kb add --title "API Design"
⚠️  WARNING: 'kb add' is deprecated. Use 'memory add --type knowledge'
Entry added: KB-20260124-001 (migrated to MEM-20260124-001)
```

#### v0.16.0 (2026-03-20): 実際の削除

**削除対象**:
- ❌ Backward compatibility layer
- ❌ KB/Task MCP tools (11 tools)
- ❌ Daily workflow commands (8 commands)
- ❌ Legacy languages (9 parsers)
- ❌ Real-time monitoring

**削減効果**:
```
MCP Tools:      36 → 25   (-30%)
CLI Commands:   40 → 20   (-50%)
Languages:      12 → 3    (-75%)
Tests:       1,953 → 1,201 (-38%)
LOC:        15,000 → 10,000 (-33%)
CI Time:     3m30s → 2m30s (-30%)
```

**保持・強化（本質）**:
- ✅ Memory System（永続的記憶）
- ✅ Conflict Detection（依存関係可視化）
- ✅ Team Features（知識標準化）
- ✅ TUI（UX価値高い）

**削除（非本質）**:
- ❌ Daily workflow commands（Claude Code で代替）
- ❌ 9言語サポート（使用率 < 3%）
- ❌ Real-time monitoring（On-demand で十分）
- ❌ 重複 MCP tools（Memory API に統合）

#### 動作保証

1. ✅ **Migration script**: `clauxton migrate --from v0.14.0`
2. ✅ **Backward compat**: v0.15.0 で全API動作
3. ✅ **Testing**: >85% coverage (1,201 tests in v0.16.0)
4. ✅ **Documentation**: Migration Guide 完備
5. ✅ **User support**: 2ヶ月の deprecation 期間

詳細: `docs/DEPRECATION_PLAN.md`, `docs/v0.15.0_MIGRATION_VALIDATION.md`

---

## 市場ポジショニング

### 新カテゴリー創造
**カテゴリー名**: Project Memory System for AI Development

**定義**: AI開発ツール（Claude Code等）と統合し、プロジェクトの知識・決定・コンテキストを永続的に記憶・活用するシステム

### 競合ポジショニングマップ

```
AI Integration (深い統合)
        ↑
    100 |
        |                        ● Clauxton
     90 |                        (90, 85)
        |
     80 |
        |
     70 |
        |              ● Cursor Projects
     60 |              (60, 40)
        |
     50 |    ● Notion AI                ● Linear
        |    (50, 70)                   (55, 50)
     40 |
        |
     30 |                        ● GitHub Issues
        |                        (40, 30)
     20 |
        |
     10 |    ● Obsidian
        |    (20, 80)
      0 |_____________________________________________→
        0   10  20  30  40  50  60  70  80  90  100
                    Knowledge Management (強い管理)
```

### 差別化ポイント

| 軸 | Clauxton | Notion | Linear | Obsidian | Cursor | GitHub |
|---|---------|--------|--------|----------|--------|--------|
| **Claude Code統合** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐ | ⭐ | ⭐⭐⭐ | ⭐⭐ |
| **コミットから自動抽出** | ⭐⭐⭐⭐⭐ | - | - | - | ⭐⭐⭐ | ⭐⭐ |
| **記憶の関連付け** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐ | ⭐ |
| **質問応答機能** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐ | - | ⭐⭐⭐ | - |
| **コード理解** | ⭐⭐⭐⭐⭐ | ⭐ | ⭐⭐ | ⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ |
| **チーム共有** | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ |

---

## コア価値提案

### 1. プロジェクトの永続的な記憶 (4/5 価値)

**問題**:
- Claudeは会話履歴を200K tokensしか保持できない
- 長期プロジェクトで3ヶ月前の設計判断を忘れる
- 複数プロジェクト間でコンテキストが混在

**解決策**:
- すべての設計判断・アーキテクチャ決定を永続保存
- セマンティック検索で即座に参照可能
- Claude Code MCP統合により透過的にアクセス

**競合との違い**:
- Notion: 手動管理、Claude統合なし
- GitHub Issues: タスク管理特化、知識管理弱い
- Obsidian: Claude統合なし、コード理解なし

### 2. タスク依存関係の可視化 (3/5 価値)

**問題**:
- 複雑なリファクタリングで作業順序が不明
- タスクの依存関係を手動管理が煩雑
- マージコンフリクトの予測が困難

**解決策**:
- DAG (Directed Acyclic Graph) による自動依存関係検出
- ファイルレベルのコンフリクト予測
- 安全な実行順序の推奨

**競合との違い**:
- Linear: 依存関係管理あり、但しコンフリクト予測なし
- GitHub Projects: 基本的な依存関係のみ
- Cursor: 依存関係管理なし

### 3. チーム知識の標準化 (3/5 価値)

**問題**:
- 新メンバーがプロジェクトコンテキストを学習するのに時間がかかる
- コーディング規約・設計パターンが散在
- チーム内で知識の非対称性が発生

**解決策**:
- 統一されたKnowledge Base
- カテゴリー別整理（architecture, patterns, constraints）
- Markdown exportによるドキュメント生成

**競合との違い**:
- Notion: 汎用的すぎる、コード特化なし
- Confluence: 重い、AI統合なし
- GitHub Wiki: 検索弱い、構造化されていない

---

## ターゲット市場

### セグメント1: 複数プロジェクトを持つ個人開発者
- **市場規模**: 50,000 - 100,000 ユーザー
- **ARPU**: $15-29/年
- **特徴**:
  - 3-5個のプロジェクトを同時進行
  - フリーランスまたはサイドプロジェクト
  - Claude Proユーザー（$20/月）
- **ペインポイント**:
  - プロジェクト切り替え時のコンテキスト喪失
  - 過去の設計判断を思い出せない
  - 同じ問題を何度も調査

### セグメント2: 長期プロジェクトの開発者
- **市場規模**: 20,000 - 50,000 ユーザー
- **ARPU**: $29-49/年
- **特徴**:
  - 1-2年以上継続するプロジェクト
  - レガシーコード管理
  - アーキテクチャ進化の追跡が重要
- **ペインポイント**:
  - 6ヶ月前の設計判断理由が不明
  - リファクタリング時の影響範囲が不明確
  - チーム内での知識伝達

### セグメント3: 小規模チーム（2-5人）
- **市場規模**: 10,000 - 30,000 チーム
- **ARPU**: $99-199/年/チーム
- **特徴**:
  - スタートアップまたは小規模プロダクトチーム
  - 全員がClaude Code使用
  - ドキュメント整備リソース不足
- **ペインポイント**:
  - 知識の属人化
  - オンボーディング時間（2-4週間）
  - コーディング規約の不統一

### 市場規模の現実的試算

**TAM (Total Addressable Market)**:
- Claude Pro ユーザー: 500,000人 (推定)
- ARPU: $29/年
- TAM = 500,000 × $29 = $14.5M
- + チーム市場 (100,000チーム × $149/年) = $14.9M
- + Enterprise (1,000社 × $999/年) = $1M
- **合計 TAM**: **$30.4M - $43.5M**

**SAM (Serviceable Addressable Market)**:
- Claude Code で長期/複数プロジェクトを扱うユーザー: 10% = 50,000人
- チーム採用率: 10% = 10,000チーム
- SAM = (50,000 × $29) + (10,000 × $149) = **$2.9M**

**SOM (Serviceable Obtainable Market) - 5年目標**:
- 個人ユーザー: 10,000人 (20% シェア)
- チーム: 2,000チーム (20% シェア)
- SOM = (10,000 × $29) + (2,000 × $149) = **$588K ARR**

**結論**:
- 🟢 副業/OSSプロジェクトとして適切
- 🔴 フルタイムビジネスとしては小さい
- 🟡 ニッチ市場でのリーダーシップは可能

---

## リスク評価

### リスク1: Claude Code のネイティブ機能追加 (確率: 50%)

**シナリオ**:
- Anthropic が Claude Code に Project Memory 機能を追加
- MCP経由ではなく、ネイティブ実装

**影響**:
- 個人ユーザーセグメントの80%が流出
- チームセグメントは残存（カスタマイズ性で差別化）

**対策**:
- Anthropic との協業（公式プラグインとして採用を目指す）
- チーム機能・カスタマイズ性の強化
- エンタープライズ向けセルフホスト対応

### リスク2: Notion の Claude 統合強化 (確率: 30%)

**シナリオ**:
- Notion が Claude API を深く統合
- Knowledge Base として Notion が選ばれる

**影響**:
- 知識管理セグメントの競合激化
- 汎用性 vs 専門性の戦い

**対策**:
- コード特化の価値を強調
- 自動抽出・依存関係検出など開発者特化機能
- Notion との連携（競合ではなく補完）

### リスク3: 市場規模の限界 (確率: 80%)

**現実**:
- 5年で $580K ARR が天井
- フルタイムビジネスとしては小さい

**対策**:
- OSS として継続（収益化は副次的）
- 企業スポンサーシップモデル
- 関連ツールへのピボット（Web Dashboard → Team Notion for Code）

---

## ポジショニング・ステートメント

**For** 長期プロジェクトまたは複数プロジェクトに取り組み、過去の決定やコンテキストを忘れてしまう Claude Code ユーザー

**Who** プロジェクトの設計判断、コード構造、変更履歴を統合された記憶として保存し、いつでも検索・参照可能にしたい

**Clauxton is a** Project Memory System

**That** Claude Code とネイティブ統合し、コミット/コードから自動的に記憶を抽出し、質問応答により知識を活用可能にする

**Unlike** Notion（汎用的）や Linear（タスク特化）

**Clauxton** はコード理解に特化し、Claude Code ネイティブ統合、自動抽出、質問応答機能により開発者の記憶を拡張する

---

## 今後の方向性

### 優先事項
1. ✅ **本質の研ぎ澄まし**: Unified Memory Model への統合
2. ✅ **自動化の強化**: コミット/コードからの知識抽出
3. ✅ **知識活用**: 質問応答、関連付け、予測
4. 🟡 **チーム機能**: 知識共有、オンボーディング支援
5. 🔴 **Enterprise**: セルフホスト、SSO、監査ログ (低優先度)

### 削減/廃止候補
- ❌ Multi-Agent Workflow Templates (価値不明確)
- 🟡 Web Dashboard (v0.15.0 → 低優先度)
- 🟡 Advanced AI Features (v0.16.0 → 低優先度)
- ✅ TUI は維持（v0.14.0 で実装済み、UX価値あり）
- ✅ Daily Workflow commands は維持（実用性高い）

### 8週間実装計画

**Week 1-2: Core Integration (統合の基盤)**
- Unified Memory Entry モデル
- KB + Task + Repository Map 統合
- 後方互換性の確保

**Week 3-4: Smart Memory (賢い記憶)**
- コミットからの自動抽出
- コード変更パターン検出
- 記憶の自動関連付け

**Week 5-6: Memory Intelligence (記憶の知能化)**
- 記憶の自動要約
- 質問応答システム
- 次のタスク予測

**Week 7-8: UX Polish (体験の洗練)**
- スマートデフォルト設定
- ガイド付きワークフロー
- 記憶可視化（TUI強化）

---

## 成功指標 (KPI)

### フェーズ1: 基礎確立 (3ヶ月)
- ⭐ GitHub Stars: 200+ → 500+
- 📥 PyPI downloads: 5K/月 → 15K/月
- 💬 MCP tool usage: 平均 10回/日/ユーザー
- ❤️ User retention (30日): 30% → 50%

### フェーズ2: 成長期 (6ヶ月)
- 👤 Active users: 1,000人 → 5,000人
- 💰 Paying users (Pro): 100人 ($29/年)
- 👥 Team adoption: 20チーム ($149/年)
- 🎯 Feature adoption: 70% が Unified Memory 使用

### フェーズ3: 拡大期 (12ヶ月)
- 👤 Active users: 10,000人
- 💰 Individual Pro: 500人 → $14.5K ARR
- 👥 Teams: 100チーム → $14.9K ARR
- 🏢 Enterprise pilots: 3社
- **合計 ARR**: **$29.4K**

### 長期目標 (24-36ヶ月)
- 💰 Individual Pro: 2,000人 → $58K ARR
- 👥 Teams: 500チーム → $74.5K ARR
- 🏢 Enterprise: 10社 × $4,999/年 → $49.9K ARR
- **合計 ARR**: **$182.4K**

### 5年ビジョン (60ヶ月)
- 💰 Individual Pro: 10,000人 → $290K ARR
- 👥 Teams: 2,000チーム → $298K ARR
- 🏢 Enterprise: 50社 → $249.5K ARR
- **合計 ARR**: **$837.5K** (修正: $580K - $840K レンジ)

---

## 結論

Clauxton は **"Obsidian for Code Projects, Built for Claude"** として、新しい市場カテゴリー「Project Memory System for AI Development」を創造します。

削減ではなく**統合と深化**により、Claude Code ユーザーの記憶を拡張し、長期プロジェクト・複数プロジェクトでの開発生産性を向上させます。

市場規模は $580K-840K ARR と限定的ですが、ニッチ市場でのリーダーシップとOSSコミュニティの構築により、持続可能なプロジェクトとして成長可能です。
