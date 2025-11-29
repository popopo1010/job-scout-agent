# Obsidian自動同期ガイド

このプロジェクトのObsidianノートを自動同期する方法を説明します。

## 🔄 同期方法の選択肢

### 1. **Obsidian Sync（公式・推奨）** ⭐
- **料金**: 月額 $8（年払いで割引あり）
- **特徴**: 
  - 公式の同期サービス
  - エンドツーエンド暗号化
  - 複数デバイス間で自動同期
  - 設定が簡単
  - バージョン履歴あり

### 2. **Git/GitHub（無料・推奨）** ⭐
- **料金**: 無料
- **特徴**:
  - バージョン管理が可能
  - 変更履歴を追跡
  - チームで共有可能
  - 自動化スクリプト付き

### 3. **クラウドストレージ（無料）**
- **iCloud Drive**（Mac/iOS）
- **Dropbox**
- **Google Drive**
- **OneDrive**

### 4. **Remotely Saveプラグイン（無料）**
- 各種クラウドストレージに対応
- S3、WebDAVなどにも対応

---

## 🚀 方法1: Obsidian Sync（公式）

### セットアップ手順

1. **Obsidian Syncを有効化**
   - Obsidianを開く
   - 設定（`Cmd+,`）→「Sync」を開く
   - 「Enable Sync」をクリック
   - アカウントを作成またはログイン

2. **このボルトを同期対象に追加**
   - 「Vaults」タブで「Add vault」をクリック
   - このプロジェクトフォルダを選択
   - 自動的に同期が開始されます

3. **設定**
   - 「Sync settings」で同期するファイルタイプを選択
   - デフォルトで`.md`ファイルと`.obsidian`設定が同期されます

### メリット
- ✅ 設定が簡単
- ✅ 自動バックアップ
- ✅ バージョン履歴
- ✅ 複数デバイス間で即座に同期

### デメリット
- ❌ 有料（月額 $8）

---

## 🔧 方法2: Git/GitHub（推奨・無料）

### セットアップ手順

#### ステップ1: GitHubリポジトリを作成

```bash
# GitHubで新しいリポジトリを作成
# 例: https://github.com/yourusername/job-scout-agent
```

#### ステップ2: リモートリポジトリを設定

```bash
cd /Users/ikeobook15/Downloads/job-scout-agent

# リモートリポジトリを追加（まだの場合）
git remote add origin https://github.com/yourusername/job-scout-agent.git

# または既存のリモートを確認
git remote -v
```

#### ステップ3: 自動同期スクリプトを使用

プロジェクトには自動同期スクリプトが含まれています：

```bash
# 手動で同期
./scripts/sync_obsidian.sh
```

#### ステップ4: 自動実行の設定（macOS）

**方法A: LaunchAgentを使う（推奨）**

```bash
# LaunchAgentディレクトリを作成
mkdir -p ~/Library/LaunchAgents

# 自動同期用のplistファイルを作成
cat > ~/Library/LaunchAgents/com.jobscout.obsidian-sync.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobscout.obsidian-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>/Users/ikeobook15/Downloads/job-scout-agent/scripts/sync_obsidian.sh</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/obsidian-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/obsidian-sync-error.log</string>
</dict>
</plist>
EOF

# LaunchAgentを読み込む
launchctl load ~/Library/LaunchAgents/com.jobscout.obsidian-sync.plist

# 確認
launchctl list | grep obsidian-sync
```

**方法B: cronを使う**

```bash
# crontabを編集
crontab -e

# 1時間ごとに自動同期（以下を追加）
0 * * * * /Users/ikeobook15/Downloads/job-scout-agent/scripts/sync_obsidian.sh >> /tmp/obsidian-sync.log 2>&1
```

**方法C: Obsidianのプラグイン「Git」を使う**

1. Obsidianで「Settings」→「Community plugins」を開く
2. 「Git」プラグインをインストール
3. 設定で自動コミット・プッシュを有効化
4. 自動コミット間隔を設定（例: 5分）

### メリット
- ✅ 無料
- ✅ バージョン管理
- ✅ 変更履歴の追跡
- ✅ チームで共有可能
- ✅ プルリクエストでレビュー可能

### デメリット
- ❌ 設定がやや複雑
- ❌ 手動でプッシュが必要（自動化しない場合）

---

## ☁️ 方法3: クラウドストレージ（iCloud Drive）

### セットアップ手順

1. **プロジェクトフォルダをiCloud Driveに移動**

```bash
# iCloud Driveに移動
mv /Users/ikeobook15/Downloads/job-scout-agent ~/Library/Mobile\ Documents/com~apple~CloudDocs/job-scout-agent
```

2. **Obsidianで新しい場所を開く**
   - Obsidianを開く
   - 「Open folder as vault」
   - 新しい場所を選択

3. **自動同期**
   - iCloud Driveは自動的に同期されます
   - 変更は自動的にクラウドにアップロードされます

### メリット
- ✅ 無料（iCloudの容量内）
- ✅ 設定が簡単
- ✅ macOS/iOS間で自動同期

### デメリット
- ❌ バージョン管理機能なし
- ❌ 競合解決が手動
- ❌ 変更履歴の追跡が限定的

---

## 🔌 方法4: Remotely Saveプラグイン

### セットアップ手順

1. **プラグインをインストール**
   - Obsidianで「Settings」→「Community plugins」
   - 「Remotely Save」を検索してインストール

2. **設定**
   - 「Settings」→「Remotely Save」
   - 使用するサービスを選択（Dropbox、S3、WebDAVなど）
   - 認証情報を入力

3. **自動同期**
   - 設定で自動同期間隔を指定
   - ファイル保存時に自動同期も可能

### 対応サービス
- Dropbox
- S3
- WebDAV
- OneDrive
- Google Drive

---

## 📊 方法の比較

| 方法 | 料金 | 設定の簡単さ | バージョン管理 | 自動同期 | 推奨度 |
|------|------|------------|--------------|---------|--------|
| Obsidian Sync | $8/月 | ⭐⭐⭐⭐⭐ | ✅ | ✅ | ⭐⭐⭐⭐⭐ |
| Git/GitHub | 無料 | ⭐⭐⭐ | ✅ | ✅* | ⭐⭐⭐⭐ |
| iCloud Drive | 無料* | ⭐⭐⭐⭐ | ❌ | ✅ | ⭐⭐⭐ |
| Remotely Save | 無料 | ⭐⭐⭐ | ❌ | ✅ | ⭐⭐⭐ |

*Gitは自動化スクリプトで自動同期可能
*iCloudの容量内で無料

---

## 🎯 推奨設定

### 個人利用の場合
1. **Obsidian Sync**（予算がある場合）
2. **Git/GitHub + 自動化スクリプト**（無料で使いたい場合）

### チーム利用の場合
1. **Git/GitHub**（変更履歴とレビューが必要）
2. **Obsidian Sync**（簡単に共有したい場合）

---

## 🔍 トラブルシューティング

### Git同期でエラーが出る場合

```bash
# リモートリポジトリの状態を確認
git remote -v

# 最新の状態を取得
git pull origin main

# 競合がある場合
git status
# 競合を解決してから
git add .
git commit -m "Resolve conflicts"
git push
```

### 自動同期が動作しない場合

```bash
# ログを確認
tail -f /tmp/obsidian-sync.log

# スクリプトを手動実行してエラーを確認
./scripts/sync_obsidian.sh
```

### Obsidian Syncが遅い場合

- ネットワーク接続を確認
- 大きなファイルがないか確認
- Obsidian Syncの設定で同期対象ファイルを制限

---

## 📝 注意事項

1. **`.obsidian/workspace.json`は同期しない**
   - 個人のワークスペース設定のため
   - 既に`.gitignore`に含まれています

2. **機密情報を含むファイル**
   - `.env`ファイルは同期しない
   - APIキーなどの機密情報は除外

3. **大きなファイル**
   - 画像や動画は別途管理を検討
   - Git LFSを使うか、外部ストレージを検討

---

## 🚀 クイックスタート

### Git/GitHubを使う場合（推奨）

```bash
# 1. GitHubリポジトリを作成
# 2. リモートを設定
git remote add origin https://github.com/yourusername/job-scout-agent.git

# 3. 初回プッシュ
git add .
git commit -m "Initial commit"
git push -u origin main

# 4. 自動同期を設定（macOS）
# LaunchAgentまたはcronを使用（上記参照）
```

### Obsidian Syncを使う場合

1. Obsidianを開く
2. 設定 → Sync → Enable Sync
3. アカウント作成/ログイン
4. このボルトを追加
5. 完了！

---

## 📚 関連ドキュメント

- [Obsidian連携ガイド](./OBSIDIAN_INTEGRATION.md)
- [プロジェクト構造](./PROJECT_STRUCTURE.md)
- [README](./README.md)
