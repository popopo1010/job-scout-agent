# 参考資料

このディレクトリには、CAマニュアルで参照するPDFファイルやその他の参考資料を保存します。

## ディレクトリ構成

```
docs/references/
├── README.md                    # このファイル
├── ca-operations/               # CA運用作成資料
│   └── （PDFファイル等）
├── training-materials/          # トレーニング資料
│   └── （PDFファイル等）
└── external-resources/          # 外部リソース
    └── （PDFファイル等）
```

## PDFファイルの追加方法

### 1. ファイルを配置する

PDFファイルをこのディレクトリ（または適切なサブディレクトリ）に配置してください。

```bash
# 例：PDFファイルをコピー
cp /path/to/your/file.pdf docs/references/ca-operations/
```

### 2. CAマニュアルから参照する

`docs/ca-manual.md` の「参考資料」セクションに、以下のようにリンクを追加してください：

```markdown
- [【KJA】基本的なマッチングの流れとポイントv1.1.pdf](./references/ca-operations/KJA-基本的なマッチングの流れとポイントv1.1.pdf)
```

### 3. Git管理について

PDFファイルは通常サイズが大きくなるため、以下のいずれかの方法を検討してください：

#### オプションA: Gitで管理する（小さいファイルの場合）

PDFファイルをそのままGitリポジトリにコミットします。
小さいファイル（数MB以下）の場合に推奨されます。

#### オプションB: Git LFSを使用する（大きいファイルの場合）

```bash
# Git LFSを初期化
git lfs install

# PDFファイルをLFSで追跡
git lfs track "*.pdf"
git add .gitattributes
git add docs/references/
git commit -m "Add PDF reference files with LFS"
```

#### オプションC: 外部ストレージを使用する

大きなファイルや機密情報が含まれる場合は、以下のような外部ストレージを使用し、READMEにダウンロード手順を記載してください：

- Google Drive
- Dropbox
- S3（AWS）
- 社内ファイルサーバー

## 現在の参考資料

### CA運作用資料

- （PDFファイルを追加したらここにリストしてください）

### トレーニング資料

- （PDFファイルを追加したらここにリストしてください）

### 外部リソース

- （PDFファイルを追加したらここにリストしてください）

## 注意事項

- PDFファイルに機密情報が含まれる場合は、`.gitignore`に追加してGit管理から除外してください
- ファイル名に日本語を使用する場合は、URLエンコードが必要になる場合があります
- 定期的にリンクが有効か確認し、更新してください

