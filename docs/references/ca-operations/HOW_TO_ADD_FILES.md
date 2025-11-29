# ca-operations/ ディレクトリにファイルを追加する方法

このディレクトリにPDFファイルやその他の参考資料を配置する手順です。

## 方法1: Finder（macOS）またはエクスプローラー（Windows）で直接コピー

1. Finderを開く（macOS）またはエクスプローラーを開く（Windows）
2. このディレクトリに移動：
   ```
   /Users/ikeobook15/Downloads/job-scout-agent/docs/references/ca-operations/
   ```
3. 追加したいPDFファイルをこのディレクトリにドラッグ&ドロップまたはコピー&ペースト

## 方法2: コマンドラインでコピー

```bash
# プロジェクトのルートディレクトリに移動
cd /Users/ikeobook15/Downloads/job-scout-agent

# 単一のPDFファイルをコピー
cp /path/to/your/file.pdf docs/references/ca-operations/

# または、ファイルを移動
mv /path/to/your/file.pdf docs/references/ca-operations/

# 複数のPDFファイルを一度にコピー
cp /path/to/*.pdf docs/references/ca-operations/

# 特定のファイル名でコピー（名前を変更しながら）
cp /path/to/original.pdf docs/references/ca-operations/new-name.pdf
```

## 方法3: ターミナルで開く

```bash
# このディレクトリをFinderで開く（macOS）
open docs/references/ca-operations/

# または、エクスプローラーで開く（Windows - Git Bash等）
explorer docs/references/ca-operations/
```

## ファイルを追加した後の手順

### 1. ファイルが正しく配置されたか確認

```bash
ls -la docs/references/ca-operations/
```

### 2. Gitに追加（必要に応じて）

```bash
# プロジェクトのルートディレクトリで実行
cd /Users/ikeobook15/Downloads/job-scout-agent

# 追加したPDFファイルをGitに追加
git add docs/references/ca-operations/your-file.pdf

# または、ディレクトリ内のすべてのファイルを追加
git add docs/references/ca-operations/

# 追加されたファイルを確認
git status
```

### 3. コミット

```bash
git commit -m "Add PDF reference: ファイル名.pdf"
```

### 4. プッシュ（リモートリポジトリに共有）

```bash
git push
```

## 注意事項

- PDFファイルのサイズが大きい（10MB以上）場合は、Git LFSを使用することを検討してください
- 機密情報が含まれるPDFファイルは、`.gitignore`に追加してGit管理から除外してください
- ファイル名にスペースや特殊文字が含まれる場合は、アンダースコア（_）やハイフン（-）を使用することを推奨します

## CAマニュアルから参照する

ファイルを追加したら、`docs/ca-manual.md`の「参考資料」セクションにリンクを追加してください：

```markdown
- [ファイル名.pdf](../references/ca-operations/ファイル名.pdf)
```

