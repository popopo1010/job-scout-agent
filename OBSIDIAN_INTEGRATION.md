# Obsidian連携ガイド

このプロジェクトは既にObsidianで開くことができます。`.obsidian`ディレクトリが存在するため、Obsidianでこのフォルダを開けば、すべてのMarkdownファイルが自動的に認識されます。

## 📖 基本的な使い方

### 1. Obsidianでプロジェクトを開く

```bash
# Obsidianを起動して、このフォルダを開く
# File > Open folder as vault > /Users/ikeobook15/Downloads/job-scout-agent
```

または、Obsidianのコマンドパレット（`Cmd+P`）から「Open another vault」を選択して、このフォルダを指定します。

### 2. プロジェクト内のMarkdownファイル

プロジェクトには以下のMarkdownファイルが含まれています：

#### 📚 仕様書（`spec/`）
- `00-quickstart.md` - クイックスタートガイド
- `01-requirements.md` - 要件定義
- `02-use-cases.md` - ユースケース
- `03-architecture.md` - アーキテクチャ設計
- `04-tasks.md` - タスクバックログ
- `05-implementation-guide.md` - 実装ガイド
- `06-deployment.md` - デプロイ手順
- `07-operations.md` - 運用ガイド

#### 📝 その他のドキュメント
- `README.md` - プロジェクト概要
- `PROJECT_STRUCTURE.md` - プロジェクト構造の全体像
- `data/sample/README.md` - サンプルデータの説明

## 🔗 リンクの活用

Obsidianでは、Markdownファイル間のリンクが自動的に認識されます。

### 内部リンクの作成

```markdown
[[README]]  # README.mdへのリンク
[[spec/00-quickstart]]  # spec/00-quickstart.mdへのリンク
[[PROJECT_STRUCTURE]]  # PROJECT_STRUCTURE.mdへのリンク
```

### バックリンクの活用

Obsidianのバックリンクパネル（右側）で、どのファイルからリンクされているかを確認できます。

## 🎨 推奨されるObsidianプラグイン

### 既に有効なプラグイン
- ✅ **File Explorer** - ファイルナビゲーション
- ✅ **Graph View** - ファイル間の関係を可視化
- ✅ **Backlinks** - バックリンク表示
- ✅ **Search** - 全文検索
- ✅ **Templates** - テンプレート機能
- ✅ **Daily Notes** - 日次ノート

### 追加推奨プラグイン

以下のプラグインを追加すると、開発作業がより便利になります：

1. **Code Block Enhancer** - コードブロックの拡張機能
2. **Dataview** - データベース的なクエリ機能
   - タスク一覧の自動生成
   - プロジェクト進捗の可視化
3. **Tasks** - タスク管理
   - `spec/04-tasks.md`のタスクを管理
4. **Tag Wrangler** - タグ管理
5. **Calendar** - カレンダー表示
6. **Kanban** - カンバンボード
   - タスク管理に活用

## 📋 プロジェクト固有の活用方法

### 1. タスク管理

`spec/04-tasks.md`のタスクをObsidianで管理：

```markdown
- [ ] **T-001**: 共通基盤モジュール作成
  - [ ] `src/common/config.py` - 設定管理
  - [ ] `src/common/logger.py` - ログ設定
```

Tasksプラグインを使うと、これらのタスクを自動的に収集・表示できます。

### 2. グラフビューの活用

Obsidianのグラフビュー（`Cmd+G`）で、ドキュメント間の関係を可視化できます。

- 仕様書間の参照関係
- コードとドキュメントの関連
- タスクと要件の関連

### 3. 検索の活用

Obsidianの検索機能（`Cmd+Shift+F`）で、プロジェクト全体を横断検索：

- 特定の機能名で検索
- コードとドキュメントを同時に検索
- 正規表現検索も可能

### 4. テンプレートの作成

開発メモ用のテンプレートを作成：

```markdown
# {{title}}

## 日付
{{date}}

## 目的

## 実装内容

## 課題・メモ

## 関連リンク
- [[関連ドキュメント]]
```

## 🔧 Obsidian設定のカスタマイズ

### 推奨設定

`.obsidian/app.json`に以下の設定を追加することを推奨します：

```json
{
  "alwaysUpdateLinks": true,
  "newFileLocation": "folder",
  "newFileFolderPath": "spec/notes",
  "attachmentFolderPath": "data/exports",
  "useMarkdownLinks": true,
  "strictLineBreaks": false,
  "showLineNumber": true,
  "spellcheck": true,
  "spellcheckLanguages": ["ja", "en"]
}
```

### ワークスペースの保存

現在のワークスペース（開いているファイル、パネル配置）は自動的に保存されます。

## 📊 プロジェクト構造の可視化

`PROJECT_STRUCTURE.md`を開くと、プロジェクト全体の構造が一目で分かります。

Obsidianのアウトライン機能（右側パネル）で、ドキュメントの階層構造を確認できます。

## 🔍 便利なショートカット

| 機能 | ショートカット |
|------|---------------|
| コマンドパレット | `Cmd+P` |
| グラフビュー | `Cmd+G` |
| 検索 | `Cmd+Shift+F` |
| ファイル検索 | `Cmd+O` |
| バックリンク表示 | `Cmd+Shift+B` |
| アウトライン表示 | `Cmd+Shift+O` |

## 💡 活用例

### 例1: 要件定義から実装タスクへのリンク

`spec/01-requirements.md`から`spec/04-tasks.md`へのリンクを作成：

```markdown
関連タスク: [[04-tasks#フェーズ2-経営分析基盤]]
```

### 例2: コードとドキュメントの関連付け

`src/analytics/analytics_engine.py`についてのメモを作成：

```markdown
# Analytics Engine メモ

## 実装内容
[[03-architecture#経営分析基盤]]を参照

## 関連タスク
[[04-tasks#T-010-データモデル実装]]
```

### 例3: 日次開発ログ

Daily Notesプラグインを使って、開発の進捗を記録：

```markdown
# 2025-01-XX 開発ログ

## 実装した機能
- [[04-tasks#T-001]] 完了

## 課題
- パフォーマンス最適化が必要

## 次のステップ
- [[04-tasks#T-002]] に着手
```

## 🔄 自動同期について

Obsidianノートの自動同期方法については、[OBSIDIAN_SYNC.md](./OBSIDIAN_SYNC.md)を参照してください。

**クイックスタート（Git/GitHub）:**
```bash
# 自動同期をセットアップ（macOS）
./scripts/setup_auto_sync.sh

# 手動で同期
./scripts/sync_obsidian.sh
```

## 🚀 次のステップ

1. **Obsidianでこのフォルダを開く**
2. **`PROJECT_STRUCTURE.md`を開いて全体像を把握**
3. **`spec/00-quickstart.md`から始める**
4. **必要に応じてプラグインを追加**
5. **自動同期を設定**（[OBSIDIAN_SYNC.md](./OBSIDIAN_SYNC.md)参照）

## 📝 メモ

- プロジェクト内のMarkdownファイルはすべてObsidianで編集可能
- コードファイル（`.py`）はObsidianで開くこともできますが、編集は推奨しません
- `.obsidian`ディレクトリは`.gitignore`に含めることを推奨（個人設定のため）

