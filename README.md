# 人材紹介事業 AIエージェントシステム

人材紹介事業の業務効率化・意思決定支援を行うAIエージェントシステムです。

## 概要

本プロジェクトは、人材紹介事業における以下の3つの課題を解決するシステムを構築します：

1. **経営分析基盤** - リードの期待展開率算出と適正保有件数の可視化
2. **フィードバックシステム** - 営業通話の書き起こしファイルからフィードバック生成
3. **求人データ整備** - 電気工事士求人の網羅的収集と整理

## クイックスタート

詳細は [spec/00-quickstart.md](spec/00-quickstart.md) を参照してください。

```bash
# リポジトリのクローン
git clone <repository-url>
cd job-scout-agent

# 仮想環境の作成
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係のインストール
pip install -e ".[dev]"

# 環境変数の設定
cp .env.example .env
# .envファイルを編集してAPIキーを設定
```

## システム構成

### 1. 経営分析基盤

現状の課題：エリア・年齢・資格ごとの単独セグメントでしか期待展開率を算出できていない

**セグメント定義（4分類）：**
| ID | 名称 | 条件 | 期待展開率 |
|----|------|------|-----------|
| A | 資格あり若手 | 電気工事士資格あり & 40歳以下 | 75% |
| B | 資格ありベテラン | 電気工事士資格あり & 40歳超 | 60% |
| C | 資格なし若手 | 電気工事士資格なし & 40歳以下 | 40% |
| D | 資格なしシニア | 電気工事士資格なし & 40歳超 | 20% |

**実現する機能：**
- リードの自動セグメント分類（資格有無×年齢による4分類）
- セグメント別期待展開率の算出
- 一人あたりの適正保有件数の算出
- 日々のリード振り分け支援
- 適正期待展開率に対するパフォーマンス可視化

### 2. フィードバックシステム

**実現する機能：**
- 書き起こしファイル（Zoom等で書き起こし済みテキスト）の読み込み
- CA向け営業マニュアル・PSS/ADSスキル資料に基づくAI分析
- フィードバック生成とSlackへの自動送信

**書き起こしファイルの配置:**
```
data/transcripts/pending/
├── 2025-01-15_ca001_meeting123.txt
└── 2025-01-15_ca002_meeting456.txt
```

### 3. 求人データ整備

**課題1:** まだ保有していない法人が電気工事士求人を出している（新規法人の見落とし）
**課題2:** 既存法人が自社で把握していないエリアで新たに求人を出している（新規エリアの見落とし）

**実現する機能：**
- **新規法人発見**: 保有していない法人の電気工事士求人をキャッチ
- **既存法人の新規エリア検出**: 既存法人が新エリアで出している求人を検出
- **自社求人との比較**: 収集求人と自社保有求人を比較し、不足分を特定
- **定期自動チェック**: 上記を自動で定期実行し、発見時に通知

## プロジェクト構成

```
job-scout-agent/
├── src/                      # ソースコード
│   ├── __init__.py
│   ├── agent.py              # コアエージェント実装
│   ├── common/               # 共通基盤
│   ├── integrations/         # 外部連携
│   ├── analytics/            # 経営分析基盤
│   ├── feedback/             # フィードバックシステム
│   └── job_data/             # 求人データ整備
├── spec/                     # 仕様書
│   ├── 00-quickstart.md      # クイックスタート
│   ├── 01-requirements.md    # 要件定義
│   ├── 02-use-cases.md       # ユースケース
│   ├── 03-architecture.md    # アーキテクチャ
│   ├── 04-tasks.md           # タスクバックログ
│   ├── 05-implementation-guide.md
│   ├── 06-deployment.md
│   ├── 07-operations.md
│   └── notes/                # 詳細設計メモ
├── tests/                    # テストファイル
├── config/                   # 設定ファイル
├── data/                     # データファイル
│   ├── sample/               # サンプルデータ
│   │   ├── analytics/        # 経営分析基盤用サンプル
│   │   └── job_data/         # 求人データ整備用サンプル
│   ├── transcripts/          # 書き起こしファイル
│   ├── exports/              # エクスポート
│   └── cache/
└── pyproject.toml
```

## サンプルデータ

`data/sample/` にサンプルデータが含まれています。詳細は [data/sample/README.md](data/sample/README.md) を参照してください。

**主要なサンプルファイル：**
- `analytics/leads.csv` - リードデータ（自動セグメント分類対応）
- `analytics/ca_master.csv` - CAマスター（セグメント別保有状況・達成率）
- `analytics/segment_conversion_rates.csv` - 4セグメント定義
- `job_data/scraped_jobs.csv` - スクレイピング求人（日給・月給・年収対応）
- `job_data/owned_jobs.csv` - 自社保有求人

## 開発

```bash
# テスト実行
pytest

# リンター実行
ruff check .

# 型チェック
mypy src/
```

## ドキュメント

| ドキュメント | 説明 |
|-------------|------|
| [クイックスタート](spec/00-quickstart.md) | 実装開始のためのガイド |
| [要件定義](spec/01-requirements.md) | 詳細な要件と仕様 |
| [ユースケース](spec/02-use-cases.md) | 利用シナリオ |
| [アーキテクチャ](spec/03-architecture.md) | システム設計 |
| [タスク一覧](spec/04-tasks.md) | 実装タスク |
| [実装ガイド](spec/05-implementation-guide.md) | コーディング規約等 |
| [デプロイ手順](spec/06-deployment.md) | 環境構築・デプロイ |
| [運用ガイド](spec/07-operations.md) | 日常運用手順 |

## ライセンス

MIT License
