# クイックスタートガイド

このドキュメントは、本プロジェクトの実装を開始するための最重要ガイドです。

## プロジェクト概要

**人材紹介事業 AIエージェントシステム** - 3つのサブシステムで構成

| システム | 目的 | 主要技術 |
|---------|------|----------|
| 経営分析基盤 | リード期待展開率の多次元分析 | Python, Claude AI |
| フィードバックシステム | 営業通話の書き起こし分析・FB生成 | Claude AI, Slack |
| 求人データ整備 | 新規法人発見・既存法人新規エリア検出 | Web Scraping, Claude AI |

## 環境構築

### 1. リポジトリのクローン

```bash
git clone <repository-url>
cd job-scout-agent
```

### 2. Python環境のセットアップ

```bash
# Python 3.11+ が必要
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -e ".[dev]"
```

### 3. 環境変数の設定

```bash
cp .env.example .env
```

`.env` ファイルを編集して以下のAPIキーを設定：

```env
# 必須
ANTHROPIC_API_KEY=your_anthropic_api_key

# フィードバックシステム用
SLACK_BOT_TOKEN=your_slack_bot_token

# ファイルパス
TRANSCRIPT_DIR=./data/transcripts

# 求人データ整備用（必要に応じて）
# 各求人サイトのAPI認証情報
```

### 4. 動作確認

```bash
# テスト実行
pytest

# リンターチェック
ruff check .

# 型チェック
mypy src/
```

## プロジェクト構成

```
job-scout-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py              # メインエージェント
│   ├── analytics/            # 経営分析基盤
│   ├── feedback/             # フィードバックシステム
│   └── job_data/             # 求人データ整備
├── spec/                     # 仕様書（このディレクトリ）
│   ├── 00-specification.md  # 使用定義書（仕様定義書）- Mission含む
│   ├── 00-quickstart.md      # ← 今ここ
│   ├── 01-requirements.md    # 要件定義
│   ├── 02-use-cases.md       # ユースケース
│   ├── 03-architecture.md    # アーキテクチャ
│   ├── 04-tasks.md           # タスクバックログ
│   ├── 05-implementation-guide.md
│   ├── 06-deployment.md
│   ├── 07-operations.md
│   ├── 08-repository-structure.md  # リポジトリ構造
│   └── notes/                # 詳細設計メモ
├── tests/
├── config/
└── pyproject.toml
```

## 実装の進め方

### Phase 1: 基盤構築（現在）
1. プロジェクト構造のセットアップ
2. 共通モジュールの実装（DB接続、ログ、設定管理）
3. 各システムのスケルトン作成

### Phase 2: 経営分析基盤
1. データモデル定義
2. セグメント分析ロジック実装
3. レポート生成機能

### Phase 3: フィードバックシステム
1. 書き起こしファイル読込機能
2. Claude AIによる分析・FB生成
3. Slack通知

### Phase 4: 求人データ整備
1. スクレイピング基盤
2. データ正規化
3. 新規法人検出・既存法人新規エリア検出
4. 自社求人比較・不足求人検出
5. 定期チェック・通知

## 次のステップ

1. **Mission確認**: [00-specification.md](./00-specification.md) でプロジェクトの使命と全体像を確認
2. **要件確認**: [01-requirements.md](./01-requirements.md) で詳細要件を確認
3. **ユースケース理解**: [02-use-cases.md](./02-use-cases.md) で具体的な利用シナリオを把握
4. **タスク確認**: [04-tasks.md](./04-tasks.md) で現在のタスクを確認し、着手

## 重要な決定事項

| 項目 | 決定内容 | 備考 |
|------|---------|------|
| データベース | TBD | PostgreSQL or SQLite |
| ジョブスケジューラ | TBD | Celery or APScheduler |
| ダッシュボード | TBD | Streamlit or Metabase |

## 関連ドキュメント

- [使用定義書（仕様定義書）](./00-specification.md) - Missionを含むプロジェクト全体の仕様
- [要件定義](./01-requirements.md)
- [ユースケース](./02-use-cases.md)
- [アーキテクチャ](./03-architecture.md)
- [タスクバックログ](./04-tasks.md)
- [実装ガイド](./05-implementation-guide.md)
- [リポジトリ構造](./08-repository-structure.md)

---

*最終更新: 2025-11-29*
