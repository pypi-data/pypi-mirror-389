# Clauxton 新規プロジェクトセットアップ手順（日本語版）

**Claude Code で Clauxton をシームレスに使うための完全ガイド**

この手順書では、新規プロジェクトで Clauxton を導入し、Claude Code との統合を5分で完了できます。

---

## 前提条件

- **Python 3.11+** がインストール済み
- **Claude Code** がインストール済み
- **インターネット接続** (PyPI からのインストール用)

---

## 📦 手順 1: Clauxton のインストール

### 推奨インストール（セマンティック検索付き）

```bash
# セマンティック検索機能を含む完全版をインストール（推奨）
pip install clauxton[semantic]

# インストール確認
clauxton --version
# 出力例: clauxton, version 0.14.0
```

**インストールオプション**:
```bash
# 基本版（軽量、高速）
pip install clauxton

# セマンティック検索機能付き（推奨）
pip install clauxton[semantic]

# Python プロジェクト用（Python パーサー付き）
pip install clauxton[parsers-python,semantic]

# Web プロジェクト用（JS/TS/PHP パーサー付き）
pip install clauxton[parsers-web,semantic]

# フルパッケージ（全機能、12言語対応）
pip install clauxton[parsers-all,semantic]
```

---

## 🚀 手順 2: プロジェクトの初期化（2つの方法）

### 方法 A: 一括セットアップ（最速・推奨）⚡

```bash
# プロジェクトディレクトリに移動
cd /path/to/your-new-project

# すべてを一度にセットアップ
clauxton quickstart

# 出力例:
# ✓ Initialized Clauxton
#   Location: /path/to/your-new-project/.clauxton
# ✓ Indexed 50 files, found 200 symbols
# ✓ MCP configuration created successfully!
#   Location: .claude-plugin/mcp-servers.json
#
# 📋 Next Steps:
# 1. Restart Claude Code to load the MCP server
# 2. Verify connection: Claude Code should show MCP tools available
# 3. Test with: Ask Claude to search your knowledge base
```

**これで完了です！** 手順 4 へ進んでください。

---

### 方法 B: ステップバイステップ（詳細制御）📋

#### 2-1. Clauxton の初期化

```bash
cd /path/to/your-new-project

clauxton init
```

**出力例**:
```
✓ Initialized Clauxton
  Location: /path/to/your-new-project/.clauxton
  Knowledge Base: /path/to/your-new-project/.clauxton/knowledge-base.yml
  Tasks: /path/to/your-new-project/.clauxton/tasks.yml
```

**何が起こるか**:
- `.clauxton/` ディレクトリが作成される
- `knowledge-base.yml` (空の知識ベース)
- `tasks.yml` (空のタスクリスト)
- `config.yml` (設定ファイル)
- `backups/` (自動バックアップ用)

#### 2-2. コードベースのインデックス作成（Repository Map）

```bash
clauxton repo index
```

**出力例**:
```
Indexing repository...
✓ Indexed 50 files
✓ Found 200 symbols (150 functions, 30 classes, 20 variables)
✓ Languages: Python (40 files), JavaScript (10 files)
```

**何が起こるか**:
- プロジェクト内のコードファイルをスキャン
- 関数、クラス、変数などのシンボルを抽出
- `.clauxton/repository_map.json` に保存

#### 2-3. MCP サーバーの設定

```bash
clauxton mcp setup
```

**出力例**:
```
✓ MCP configuration created successfully!
  Location: .claude-plugin/mcp-servers.json

📋 Next Steps:
1. Restart Claude Code to load the MCP server
2. Verify connection: Claude Code should show MCP tools available
3. Test with: Ask Claude to search your knowledge base
```

**何が起こるか**:
- `.claude-plugin/mcp-servers.json` が自動作成される
- Claude Code が Clauxton の 36 個のツールを使えるようになる

**設定ファイルの中身（参考）**:
```json
{
  "mcpServers": {
    "clauxton": {
      "command": "python",
      "args": ["-m", "clauxton.mcp.server"],
      "cwd": "${workspaceFolder}",
      "env": {
        "PYTHONPATH": "${workspaceFolder}"
      }
    }
  }
}
```

---

## 🔧 手順 3: 初期知識の追加（オプションだが推奨）

プロジェクトの重要な決定事項や制約を記録しましょう。

### 対話形式で追加

```bash
clauxton kb add
```

**入力例**:
```
Title: Python 3.11+ を使用
Category: constraint
Content: このプロジェクトは Python 3.11 以降を必須とします。型ヒントを活用します。
Tags (comma-separated): python,version,constraint

✓ Added entry: KB-20251028-001
```

### もう少し追加してみる

```bash
# アーキテクチャの決定
clauxton kb add
# Title: FastAPI をバックエンドに採用
# Category: architecture
# Content: すべてのバックエンド API は FastAPI で実装します。非同期処理と自動ドキュメント生成が理由です。
# Tags: fastapi,backend,api

# データベースの選択
clauxton kb add
# Title: PostgreSQL を本番環境で使用
# Category: decision
# Content: 本番環境では PostgreSQL 15+ を使用します。
# Tags: database,postgresql,production

# コーディング規約
clauxton kb add
# Title: type hints を必須とする
# Category: convention
# Content: すべての関数に型ヒント（引数と戻り値）を付けることを必須とします。
# Tags: python,typing,convention
```

### 確認

```bash
clauxton kb list
```

**出力例**:
```
Knowledge Base Entries (4 total)

KB-20251028-001 [constraint]
  Title: Python 3.11+ を使用
  Tags: python, version, constraint

KB-20251028-002 [architecture]
  Title: FastAPI をバックエンドに採用
  Tags: fastapi, backend, api

KB-20251028-003 [decision]
  Title: PostgreSQL を本番環境で使用
  Tags: database, postgresql, production

KB-20251028-004 [convention]
  Title: type hints を必須とする
  Tags: python, typing, convention
```

---

## 🔄 手順 4: Claude Code の再起動

**重要**: MCP サーバーを有効にするため、Claude Code を再起動してください。

1. Claude Code を終了
2. Claude Code を再起動
3. プロジェクトディレクトリを開く

---

## ✅ 手順 5: 統合テスト

Claude Code が Clauxton を認識しているか確認しましょう。

### テスト 1: 知識ベースの検索

Claude Code で以下のように質問してみてください：

**あなた**: "このプロジェクトのバックエンドアーキテクチャは何ですか？"

**Claude Code の動作**:
1. `kb_search(query="backend architecture", category="architecture")` を実行
2. KB-20251028-002 を取得
3. 回答: 「知識ベース（KB-20251028-002）によると、このプロジェクトではすべてのバックエンド API に FastAPI を採用しています。理由は非同期処理と自動ドキュメント生成のためです。」

---

### テスト 2: 新しい決定を記録

**あなた**: "Redis をキャッシュに使うことにしました。記録してください。"

**Claude Code の動作**:
1. `kb_add(title="Redis をキャッシュに使用", category="decision", content="アプリケーションキャッシュに Redis を使用してパフォーマンスを向上させます。", tags=["redis", "cache", "performance"])` を実行
2. エントリ ID を取得（例: KB-20251028-005）
3. 回答: "了解しました。この決定を知識ベースに KB-20251028-005 として記録しました。"

**確認**:
```bash
clauxton kb get KB-20251028-005
```

---

### テスト 3: コードシンボルの検索

**あなた**: "このプロジェクトに `authenticate` という関数はありますか？"

**Claude Code の動作**:
1. `search_symbols(query="authenticate", mode="fuzzy")` を実行
2. Repository Map から該当シンボルを検索
3. 該当する関数があれば場所を回答

---

### テスト 4: タスク管理

**あなた**: "ユーザー認証機能を実装するタスクを追加してください。"

**Claude Code の動作**:
1. `task_add(name="ユーザー認証機能の実装", priority="high", status="pending", description="JWT トークンベースの認証を実装", tags=["auth", "security"])` を実行
2. タスク ID を取得（例: TASK-001）
3. 回答: "タスク TASK-001 を追加しました。"

**確認**:
```bash
clauxton task list
```

---

## 🎯 手順 6: 日常的な使い方

### 朝の作業開始時

```bash
# 今日やることを整理
clauxton morning

# 出力例:
# Good morning! Here's your daily briefing:
#
# 📊 Yesterday's Summary:
# - 3 tasks completed
# - 2 KB entries added
#
# 🎯 Today's Focus:
# TASK-001: ユーザー認証機能の実装 [high priority]
# TASK-002: API エンドポイントの作成 [medium priority]
#
# ⏰ Estimated time: 6 hours
```

### 作業中

Claude Code と会話しながら、自然に知識ベースとタスクが更新されていきます。

**典型的な会話例**:

**あなた**: "ユーザー認証に JWT トークンを使います。有効期限は 24 時間にします。"

**Claude Code**:
- 自動的に知識ベースに記録
- 実装コードを提案
- セキュリティのベストプラクティスを確認

**あなた**: "認証機能が完成しました。TASK-001 を完了にしてください。"

**Claude Code**:
- `task_update(task_id="TASK-001", status="completed")` を実行
- 次のタスクを推薦

### 作業終了時

```bash
# 今日の作業をサマリー
clauxton daily

# 出力例:
# 📊 Daily Summary (2025-10-28)
#
# ✅ Tasks Completed: 2
# - TASK-001: ユーザー認証機能の実装
# - TASK-002: API エンドポイントの作成
#
# 📝 KB Entries Added: 3
# - KB-20251028-006: JWT トークンの有効期限
# - KB-20251028-007: エラーハンドリングパターン
# - KB-20251028-008: API バージョニング戦略
#
# ⏱️  Total Work Time: 7h 30m
# 🔥 Productivity: High
```

---

## 🎨 手順 7: Interactive TUI を試す（v0.14.0+）

ターミナルベースの対話型 UI で、より直感的に操作できます。

```bash
clauxton tui
```

**TUI の機能**:
- **3パネルダッシュボード**: KB/Tasks/Repository Map を同時表示
- **Vim スタイルナビゲーション**: `j`/`k` で移動、`Enter` で選択
- **検索モーダル**: `/` でクエリ入力、オートコンプリート対応
- **AI サジェスチョン**: リアルタイムで推薦を表示
- **キーボードショートカット**:
  - `q`: 終了
  - `Tab`: パネル切り替え
  - `/`: 検索
  - `a`: 新規追加
  - `d`: 削除
  - `e`: 編集

---

## 📚 利用可能な MCP ツール（36個）

Claude Code は以下のツールを自動的に使います：

### Knowledge Base (6 tools)
- `kb_search()` - 知識ベース検索
- `kb_add()` - エントリ追加
- `kb_list()` - リスト表示
- `kb_get()` - エントリ取得
- `kb_update()` - 更新
- `kb_delete()` - 削除

### Task Management (7 tools)
- `task_add()` - タスク追加
- `task_import_yaml()` - YAML インポート
- `task_list()` - リスト表示
- `task_get()` - タスク取得
- `task_update()` - 更新
- `task_next()` - 次のタスクを推薦
- `task_delete()` - 削除

### Conflict Detection (3 tools)
- `detect_conflicts()` - コンフリクト検出
- `recommend_safe_order()` - 安全な実行順序を推薦
- `check_file_conflicts()` - ファイルの競合チェック

### Repository Intelligence (4 tools)
- `index_repository()` - リポジトリインデックス
- `search_symbols()` - シンボル検索（関数、クラスなど）
- `search_knowledge_semantic()` - セマンティック検索（KB）
- `search_files_semantic()` - セマンティック検索（ファイル）

### Context Intelligence (4 tools)
- `get_project_context()` - プロジェクトコンテキスト取得
- `generate_project_summary()` - サマリー生成
- `get_knowledge_graph()` - 知識グラフ取得
- `kb_export_docs()` - ドキュメントエクスポート

### Proactive Features (4 tools)
- `watch_project_changes()` - リアルタイム変更監視
- `get_recent_changes()` - 最近の変更取得
- `suggest_kb_updates()` - KB 更新提案
- `detect_anomalies()` - 異常検出

### Analysis & Suggestions (4 tools)
- `analyze_recent_commits()` - コミット分析
- `suggest_next_tasks()` - タスク提案
- `extract_decisions_from_commits()` - 決定の抽出
- `find_related_entries()` - 関連エントリ検索

### Utilities (4 tools)
- `undo_last_operation()` - 最後の操作を元に戻す
- `get_recent_operations()` - 操作履歴取得
- `search_tasks_semantic()` - タスクのセマンティック検索
- `search_knowledge_semantic()` - KB のセマンティック検索

---

## 🔧 トラブルシューティング

### 問題 1: Claude が知識ベースを使っていない

**確認**:
```bash
# MCP 設定を確認
clauxton mcp status

# 出力例:
# ✓ MCP configuration found
#   Location: .claude-plugin/mcp-servers.json
# ✓ Clauxton MCP server is configured
```

**解決策**:
1. `.claude-plugin/mcp-servers.json` が存在するか確認
2. Claude Code を再起動
3. MCP サーバーが動作するか手動テスト: `python -m clauxton.mcp.server`
4. `.clauxton/` ディレクトリが存在するか確認: `ls -la .clauxton/`

---

### 問題 2: "ModuleNotFoundError: No module named 'mcp'"

**解決策**:
```bash
pip install mcp
# または
pip install clauxton[semantic]  # 再インストール
```

---

### 問題 3: "Knowledge Base not initialized"

**解決策**:
```bash
clauxton init
```

---

### 問題 4: セマンティック検索が動かない

**原因**: `sentence-transformers` がインストールされていない

**解決策**:
```bash
pip install clauxton[semantic]
```

---

### 問題 5: Repository Map が言語をサポートしていない

**例**: Go プロジェクトでシンボルが抽出されない

**解決策**:
```bash
# Go パーサーをインストール
pip install clauxton[parsers-systems]

# または全言語対応
pip install clauxton[parsers-all]

# 再インデックス
clauxton repo index
```

---

## 🎯 ベストプラクティス

### 1. 知識ベースの活用

**良い例**:
- アーキテクチャの決定を記録（「なぜ FastAPI を選んだか」）
- コーディング規約を記録（「type hints を必須とする」）
- 制約を記録（「Python 3.11+ のみサポート」）

**避けるべき例**:
- 実装の詳細（「この関数は X を返す」）→ コードコメントで十分
- 一時的な情報（「明日ミーティング」）→ カレンダーへ

### 2. タスク管理

**良い例**:
- 具体的なタスク名（「JWT 認証の実装」）
- 優先度の設定（`high`, `medium`, `low`）
- 依存関係の明示（`depends_on: ["TASK-001"]`）

**避けるべき例**:
- 曖昧なタスク（「バグ修正」）→ 具体的に
- すべて高優先度 → 優先順位がつかない

### 3. Git との統合

```bash
# .clauxton/ をコミット（チーム共有）
git add .clauxton/
git commit -m "Add project knowledge and tasks"

# .gitignore に以下を追加（オプション）
# .clauxton/backups/     # バックアップは共有不要
# .clauxton/.cache/      # キャッシュは共有不要
```

### 4. 定期的なレビュー

```bash
# 週次レビュー
clauxton weekly

# トレンド分析（30日間）
clauxton trends

# 知識ベースのエクスポート（ドキュメント化）
clauxton kb export
```

---

## 📖 次のステップ

### 詳細ドキュメント

- **[MCP Tools Documentation](mcp-index.md)** - 全 36 ツールの詳細
- **[CLAUDE.md](CLAUDE.md)** - Clauxton 開発者向けガイド
- **[ROADMAP.md](ROADMAP.md)** - 今後の機能開発計画

### コミュニティ

- **GitHub Issues**: https://github.com/nakishiyaman/clauxton/issues
- **PyPI**: https://pypi.org/project/clauxton/

---

## 🎉 完了！

これで Clauxton が Claude Code とシームレスに統合されました。

**日常の流れ**:
1. **朝**: `clauxton morning` で今日のタスク確認
2. **作業中**: Claude Code と会話しながら自然に KB/タスクが更新される
3. **夕方**: `clauxton daily` で進捗確認
4. **週末**: `clauxton weekly` で振り返り

**重要なポイント**:
- Claude Code が自動的に Clauxton のツールを使用
- あなたは普段通り会話するだけ
- 知識とタスクは永続化され、チームで共有可能
- CLI でいつでもオーバーライド可能

**Happy Coding with Clauxton!** 🚀
