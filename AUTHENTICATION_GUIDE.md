# GitHub認証ガイド

GitHubにプッシュするための認証設定方法です。

## 🔐 方法1: Personal Access Token (PAT) を使う（推奨）

### ステップ1: Personal Access Tokenを作成

1. **GitHubにログイン**
   - https://github.com にアクセス

2. **Settingsを開く**
   - 右上のプロフィール画像をクリック
   - 「Settings」をクリック

3. **Developer settingsを開く**
   - 左側のメニューで「Developer settings」をクリック
   - 「Personal access tokens」→「Tokens (classic)」をクリック

4. **新しいトークンを生成**
   - 「Generate new token」→「Generate new token (classic)」をクリック
   - **Note**: `job-scout-agent` など、わかりやすい名前を入力
   - **Expiration**: 有効期限を選択（90日、1年など）
   - **Select scopes**: 以下のスコープにチェック
     - ✅ `repo` (すべてのリポジトリへのアクセス)
   - 「Generate token」をクリック

5. **トークンをコピー**
   - ⚠️ **このトークンは一度しか表示されません！必ずコピーしてください**
   - 安全な場所に保存してください

### ステップ2: プッシュ時にトークンを使用

```bash
cd /Users/ikeobook15/Downloads/job-scout-agent

# プッシュを実行
git push -u origin main
```

認証が求められたら：
- **Username**: `popopo1010`（GitHubのユーザー名）
- **Password**: **Personal Access Token**（パスワードではなく、作成したトークンを貼り付け）

### ステップ3: 認証情報を保存（オプション）

認証情報を保存して、次回から自動的に認証されるようにする：

```bash
# macOSの場合
git config --global credential.helper osxkeychain
```

これで、次回からは自動的に認証されます。

---

## 🔐 方法2: SSH鍵を使う（推奨・セキュア）

### ステップ1: SSH鍵を生成

```bash
# SSH鍵を生成（まだの場合）
ssh-keygen -t ed25519 -C "your_email@example.com"

# 既存の鍵があるか確認
ls -la ~/.ssh/id_ed25519.pub
```

### ステップ2: 公開鍵をGitHubに追加

1. **公開鍵をコピー**
   ```bash
   cat ~/.ssh/id_ed25519.pub
   # 表示された内容をコピー
   ```

2. **GitHubに追加**
   - GitHub → Settings → SSH and GPG keys
   - 「New SSH key」をクリック
   - **Title**: `MacBook Air` など、わかりやすい名前
   - **Key**: コピーした公開鍵を貼り付け
   - 「Add SSH key」をクリック

### ステップ3: リモートURLをSSHに変更

```bash
cd /Users/ikeobook15/Downloads/job-scout-agent

# リモートURLをSSHに変更
git remote set-url origin git@github.com:popopo1010/job-scout-agent.git

# 確認
git remote -v
```

### ステップ4: 接続テスト

```bash
# SSH接続をテスト
ssh -T git@github.com

# 成功すると以下のメッセージが表示されます:
# Hi popopo1010! You've successfully authenticated, but GitHub does not provide shell access.
```

### ステップ5: プッシュ

```bash
git push -u origin main
```

SSHを使う場合、認証情報の入力は不要です。

---

## 🎯 推奨方法

- **個人利用・簡単に始めたい**: Personal Access Token (PAT)
- **セキュア・長期的に使う**: SSH鍵

---

## 🔄 認証方法の切り替え

### HTTPSからSSHに変更

```bash
git remote set-url origin git@github.com:popopo1010/job-scout-agent.git
```

### SSHからHTTPSに変更

```bash
git remote set-url origin https://github.com/popopo1010/job-scout-agent.git
```

---

## 🛠️ トラブルシューティング

### 認証エラーが続く場合

```bash
# 認証情報をクリア（macOS）
git credential-osxkeychain erase
host=github.com
protocol=https
# （空行を2回Enter）

# 再度プッシュを試す
git push -u origin main
```

### SSH接続エラー

```bash
# SSH接続をテスト
ssh -T git@github.com

# エラーの場合、SSH鍵を再生成
ssh-keygen -t ed25519 -C "your_email@example.com"
# 新しい公開鍵をGitHubに追加
```

---

## ✅ 次のステップ

認証設定が完了したら：

```bash
# プッシュを実行
git push -u origin main
```

成功すると、GitHubリポジトリにすべてのファイルがアップロードされます！

