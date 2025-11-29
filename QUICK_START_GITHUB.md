# 🚀 GitHub連携クイックスタート

Cursorで編集したデータをGitHubにプッシュする手順です。

## ✅ 現在の状態

- ✅ 初回コミットが完了しました（78ファイル、10,004行）
- ⏳ GitHubリポジトリの作成が必要です

## 📝 手順

### ステップ1: GitHubリポジトリを作成

1. **GitHubにアクセス**
   - https://github.com を開く
   - ログイン（アカウントがない場合は作成）

2. **新しいリポジトリを作成**
   - 右上の「+」→「New repository」をクリック
   - **Repository name**: `job-scout-agent`（または任意の名前）
   - **Description**: 「人材紹介事業 AIエージェントシステム」（任意）
   - **Public** または **Private** を選択
   - ⚠️ **「Initialize this repository with a README」はチェックしない**
   - 「Create repository」をクリック

3. **リポジトリURLをコピー**
   - 作成後、表示されるURLをコピー
   - 例: `https://github.com/yourusername/job-scout-agent.git`

### ステップ2: リモートリポジトリを設定

ターミナルで以下のコマンドを実行してください：

```bash
cd /Users/ikeobook15/Downloads/job-scout-agent

# リモートリポジトリを追加（yourusernameを実際のユーザー名に置き換える）
git remote add origin https://github.com/yourusername/job-scout-agent.git

# 確認
git remote -v
```

### ステップ3: 初回プッシュ

```bash
# メインブランチをプッシュ
git push -u origin main
```

**認証が求められた場合:**
- ユーザー名: GitHubのユーザー名
- パスワード: **Personal Access Token (PAT)** を使用
  - GitHub → Settings → Developer settings → Personal access tokens → Tokens (classic)
  - 「Generate new token」→ スコープ `repo` にチェック → 生成
  - トークンをコピーしてパスワードの代わりに入力

### ステップ4: 確認

GitHubのリポジトリページを開いて、ファイルがアップロードされていることを確認してください。

---

## 🔄 今後の使い方

### Cursorから直接プッシュ

1. **ソース管理パネルを開く**（左側のGitアイコン）
2. **変更をステージング**（ファイルの横の「+」ボタン）
3. **コミットメッセージを入力**
4. **「✓ Commit」をクリック**
5. **「↑ Push」をクリック**

### コマンドラインからプッシュ

```bash
# 変更を確認
git status

# 変更をステージング
git add .

# コミット
git commit -m "変更内容の説明"

# プッシュ
git push
```

### 自動同期スクリプトを使う

```bash
# 自動的にコミット・プッシュ
./scripts/sync_obsidian.sh
```

---

## ⚙️ Git設定（推奨）

コミットに名前とメールアドレスを設定する場合：

```bash
# ユーザー名を設定
git config --global user.name "Your Name"

# メールアドレスを設定
git config --global user.email "your.email@example.com"
```

---

## 📚 詳細情報

詳細な手順やトラブルシューティングは [GITHUB_SETUP.md](./GITHUB_SETUP.md) を参照してください。

---

## 🎯 次のステップ

1. ✅ GitHubリポジトリを作成
2. ✅ リモートリポジトリを設定
3. ✅ 初回プッシュを実行
4. ✅ 自動同期を設定（任意）

**準備ができたら、上記のコマンドを実行してください！**

