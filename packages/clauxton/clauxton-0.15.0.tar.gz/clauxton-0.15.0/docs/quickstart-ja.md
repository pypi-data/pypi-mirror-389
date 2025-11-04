# Clauxton クイックスタート（5分で完了）

**Claude Code で Clauxton を今すぐ始める**

---

## 📦 1. インストール（30秒）

```bash
# 推奨：セマンティック検索機能付き
pip install clauxton[semantic]

# 確認
clauxton --version
```

---

## 🚀 2. プロジェクトセットアップ（2分）

### 方法 A: ワンコマンド（最速）⚡

```bash
cd your-project
clauxton quickstart
```

**完了！** → 手順 4 へ

---

### 方法 B: ステップバイステップ

```bash
cd your-project

# 初期化
clauxton init

# MCP サーバー設定
clauxton mcp setup

# コードベースのインデックス（オプション）
clauxton repo index
```

---

## 📝 3. 初期知識の追加（1分）

```bash
# 対話形式で追加
clauxton kb add

# または一行で追加
clauxton kb add \
  --title "FastAPI を使用" \
  --category architecture \
  --content "バックエンドは FastAPI で実装" \
  --tags "api,backend"

# 確認
clauxton kb list
```

---

## 🔄 4. Claude Code を再起動

1. Claude Code を終了
2. Claude Code を再起動
3. プロジェクトを開く

---

## ✅ 5. 動作確認（1分）

Claude Code で質問してみてください：

**質問例**:
- "このプロジェクトのアーキテクチャは？"
- "データベースは何を使っていますか？"
- "新しい決定として、Redis をキャッシュに使うことを記録してください"

**Claude が自動的に**:
- 知識ベースを検索 (`kb_search`)
- 新しい情報を記録 (`kb_add`)
- タスクを管理 (`task_add`, `task_update`)

---

## 🎯 日常的な使い方

### 朝の作業開始

```bash
clauxton morning
```

### 作業中

**Claude Code と普通に会話するだけ**
- 「この機能を実装します」→ タスクが自動作成
- 「この設計にします」→ 知識ベースに自動記録
- 「タスク完了しました」→ ステータスが自動更新

### 作業終了

```bash
clauxton daily     # 今日のサマリー
clauxton weekly    # 週次レポート
```

---

## 🔧 トラブルシューティング

### Claude が知識ベースを使わない

```bash
clauxton mcp status    # 設定確認
clauxton status        # 全体確認
```

→ Claude Code を再起動

### モジュールが見つからない

```bash
pip install clauxton[semantic]
```

### 知識ベースが初期化されていない

```bash
clauxton init
```

---

## 📚 利用可能な機能

### Knowledge Base（知識ベース）
- 設計決定、制約、パターンを永続化
- TF-IDF + セマンティック検索

### Task Management（タスク管理）
- 自動依存関係推論
- 優先度管理
- AI による次タスク推薦

### Repository Intelligence（コード解析）
- 12言語対応シンボル抽出
- 関数/クラス/変数の高速検索

### Proactive Monitoring（プロアクティブ監視）
- リアルタイムファイル監視
- 異常検出
- KB 更新提案

### Context Intelligence（コンテキスト分析）
- 作業セッション分析
- 次のアクション予測
- プロジェクトサマリー生成

---

## 🎨 Interactive TUI（v0.14.0+）

```bash
clauxton tui
```

**操作**:
- `j`/`k`: 移動
- `Tab`: パネル切り替え
- `/`: 検索
- `a`: 追加
- `q`: 終了

---

## 📖 詳細ドキュメント

- **[完全ガイド](getting-started-ja.md)** - 詳細な手順書
- **[MCP Tools](mcp-index.md)** - 全 36 ツールのリファレンス
- **[CLAUDE.md](CLAUDE.md)** - 開発者向けガイド

---

## 🎉 これで完了！

**重要なポイント**:
1. **透過的**: Claude Code と普通に会話するだけ
2. **永続化**: すべての知識とタスクが保存される
3. **共有可能**: `.clauxton/` を Git にコミット
4. **制御可能**: CLI でいつでもオーバーライド

**Happy Coding!** 🚀
