# GitHub連携セットアップガイド

Cursorで編集したデータをGitHubと連携する手順です。

## 🚀 クイックスタート

### ステップ1: GitHubリポジトリを作成

1. **GitHubにログイン**
   - https://github.com にアクセス
   - ログイン（アカウントがない場合は作成）

2. **新しいリポジトリを作成**
   - 右上の「+」→「New repository」をクリック
   - リポジトリ名を入力（例: `job-scout-agent`）
   - 説明を入力（任意）
   - **Public** または **Private** を選択
   - ⚠️ **「Initialize this repository with a README」はチェックしない**
   - 「Create repository」をクリック

3. **リポジトリURLをコピー**
   - 作成後、表示されるURLをコピー
   - 例: `https://github.com/yourusername/job-scout-agent.git`
   - または: `git@github.com:yourusername/job-scout-agent.git` (SSH)

### ステップ2: リモートリポジトリを設定

```bash
cd /Users/ikeobook15/Downloads/job-scout-agent

# HTTPSを使う場合（推奨・簡単）
git remote add origin https://github.com/yourusername/job-scout-agent.git

# またはSSHを使う場合（既にSSH鍵を設定している場合）
# git remote add origin git@github.com:yourusername/job-scout-agent.git
```

**⚠️ 注意**: `yourusername` と `job-scout-agent` を実際の値に置き換えてください。

### ステップ3: 初回プッシュ

```bash
# メインブランチをプッシュ
git push -u origin main
```

### ステップ4: 確認

GitHubのリポジトリページを開いて、ファイルがアップロードされていることを確認してください。

---

## 🔄 今後の使い方

### 変更をGitHubにプッシュする

```bash
# 1. 変更を確認
git status

# 2. 変更をステージング
git add .

# または特定のファイルだけ
git add path/to/file.py

# 3. コミット
git commit -m "変更内容の説明"

# 4. プッシュ
git push
```

### 自動同期スクリプトを使う

```bash
# 自動的にコミット・プッシュ
./scripts/sync_obsidian.sh
```

### Cursorから直接プッシュ

CursorにはGit統合機能があります：

1. **ソース管理パネルを開く**（左側のアイコン）
2. **変更をステージング**（「+」ボタン）
3. **コミットメッセージを入力**
4. **「✓ Commit」をクリック**
5. **「↑ Push」をクリック**

---

## 🔐 認証設定

### HTTPSを使う場合

初回プッシュ時に認証情報を求められます：

1. **Personal Access Token (PAT) を使う（推奨）**
   - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
   - 「Generate new token」をクリック
   - スコープ: `repo` にチェック
   - トークンをコピー
   - パスワードの代わりにトークンを入力

2. **Git Credential Managerを使う**
   ```bash
   # macOSの場合
   git config --global credential.helper osxkeychain
   ```

### SSHを使う場合

1. **SSH鍵を生成**（まだの場合）
   ```bash
   ssh-keygen -t ed25519 -C "your_email@example.com"
   ```

2. **公開鍵をGitHubに追加**
   - `~/.ssh/id_ed25519.pub` の内容をコピー
   - GitHub → Settings → SSH and GPG keys → New SSH key
   - 鍵を貼り付けて保存

3. **リモートURLをSSHに変更**
   ```bash
   git remote set-url origin git@github.com:yourusername/job-scout-agent.git
   ```

---

## 📋 よくある操作

### リモートリポジトリの確認

```bash
git remote -v
```

### リモートURLの変更

```bash
git remote set-url origin https://github.com/newusername/new-repo.git
```

### 最新の変更を取得

```bash
git pull origin main
```

### ブランチの作成と切り替え

```bash
# 新しいブランチを作成
git checkout -b feature/new-feature

# ブランチを切り替え
git checkout main
```

### 変更履歴の確認

```bash
git log --oneline
```

---

## 🛠️ トラブルシューティング

### エラー: "remote origin already exists"

既にリモートが設定されている場合：

```bash
# 既存のリモートを確認
git remote -v

# リモートを削除して再設定
git remote remove origin
git remote add origin https://github.com/yourusername/job-scout-agent.git
```

### エラー: "failed to push some refs"

リモートに既にコミットがある場合：

```bash
# リモートの変更を取得
git pull origin main --allow-unrelated-histories

# 競合を解決してから
git push origin main
```

### 認証エラー

```bash
# 認証情報をクリア
git credential-osxkeychain erase
host=github.com
protocol=https

# 次回プッシュ時に再認証
```

---

## 🔄 自動同期の設定

macOSで自動同期を設定する場合：

```bash
# 自動同期をセットアップ（1時間ごと）
./scripts/setup_auto_sync.sh
```

詳細は [OBSIDIAN_SYNC.md](./OBSIDIAN_SYNC.md) を参照してください。

---

## 📚 関連ドキュメント

- [Obsidian連携ガイド](./OBSIDIAN_INTEGRATION.md)
- [Obsidian自動同期](./OBSIDIAN_SYNC.md)
- [プロジェクト構造](./PROJECT_STRUCTURE.md)

---

## ✅ チェックリスト

- [ ] GitHubリポジトリを作成
- [ ] リモートリポジトリを設定
- [ ] 初回プッシュを実行
- [ ] 認証設定を完了
- [ ] 自動同期を設定（任意）

---

**次のステップ**: GitHubリポジトリを作成したら、上記のコマンドを実行して連携を完了してください。

