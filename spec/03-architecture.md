# アーキテクチャ設計

## 1. システム全体構成

```
┌─────────────────────────────────────────────────────────────────────────┐
│                         外部サービス                                     │
├───────────────────────┬─────────────┬─────────────┬─────────────────────┤
│      Slack API        │ Claude API  │   求人サイト │   ファイルシステム   │
└───────────┬───────────┴──────┬──────┴───────┬─────┴──────────┬──────────┘
            │                  │              │                │
            ▼                  ▼              ▼                ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                        Integration Layer                                │
│  ┌─────────────┐ ┌─────────────────┐ ┌─────────────────────────────────┐│
│  │ SlackClient │ │ TranscriptReader│ │       ScrapingEngine            ││
│  └─────────────┘ └─────────────────┘ └─────────────────────────────────┘│
└─────────────────────────────────┬───────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         Core Services                                   │
├─────────────────────┬─────────────────────┬─────────────────────────────┤
│   経営分析基盤       │  フィードバック      │      求人データ整備          │
│   (Analytics)       │    システム          │      (JobData)              │
│                     │   (Feedback)         │                             │
│ ┌─────────────────┐ │ ┌─────────────────┐ │ ┌─────────────────────────┐ │
│ │SegmentAnalyzer  │ │ │TranscriptionSvc │ │ │ JobCollector            │ │
│ │ExpectationCalc  │ │ │FeedbackGenerator│ │ │ DataNormalizer          │ │
│ │LeadDistributor  │ │ │NotificationSvc  │ │ │ DiffExtractor           │ │
│ │ReportGenerator  │ │ │HistoryManager   │ │ │ ReportGenerator         │ │
│ └─────────────────┘ │ └─────────────────┘ │ └─────────────────────────┘ │
└─────────────────────┴─────────────────────┴─────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                         共通基盤 (Common)                               │
│  ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────┐ ┌──────────────┐  │
│  │ Database │ │ Scheduler│ │  Logger  │ │  Config  │ │  AIAgent     │  │
│  └──────────┘ └──────────┘ └──────────┘ └──────────┘ └──────────────┘  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 2. ディレクトリ構成

```
job-scout-agent/
├── src/
│   ├── __init__.py
│   ├── agent.py                    # メインエージェント
│   │
│   ├── common/                     # 共通基盤
│   │   ├── __init__.py
│   │   ├── config.py               # 設定管理
│   │   ├── database.py             # DB接続・モデル
│   │   ├── logger.py               # ログ設定
│   │   ├── scheduler.py            # ジョブスケジューラ
│   │   └── ai_client.py            # Claude APIクライアント
│   │
│   ├── integrations/               # 外部連携
│   │   ├── __init__.py
│   │   ├── transcript_reader.py    # 書き起こしファイル読込
│   │   ├── slack.py                # Slack API
│   │   └── scraper/                # Webスクレイピング
│   │       ├── __init__.py
│   │       ├── base.py             # 基底クラス
│   │       ├── indeed.py
│   │       ├── hellowork.py
│   │       └── ...
│   │
│   ├── analytics/                  # 経営分析基盤
│   │   ├── __init__.py
│   │   ├── models.py               # データモデル
│   │   ├── segment_analyzer.py     # セグメント分析
│   │   ├── expectation_calc.py     # 期待展開率計算
│   │   ├── lead_distributor.py     # リード振り分け
│   │   └── report.py               # レポート生成
│   │
│   ├── feedback/                   # フィードバックシステム
│   │   ├── __init__.py
│   │   ├── models.py               # データモデル
│   │   ├── processor.py            # ファイル処理
│   │   ├── analyzer.py             # 通話分析
│   │   ├── generator.py            # FB生成
│   │   └── notification.py         # 通知
│   │
│   └── job_data/                   # 求人データ整備
│       ├── __init__.py
│       ├── models.py               # データモデル
│       ├── collector.py            # データ収集
│       ├── normalizer.py           # データ正規化
│       ├── company_matcher.py      # 法人マッチング（新規/既存判定）
│       ├── area_detector.py        # 新規エリア検出
│       ├── job_comparator.py       # 自社求人との比較
│       └── report.py               # レポート生成
│
├── spec/                           # 仕様書
├── tests/                          # テスト
├── config/                         # 設定ファイル
├── scripts/                        # ユーティリティスクリプト
└── data/                           # データファイル（.gitignore）
    ├── recordings/                 # 録音ファイル
    ├── exports/                    # エクスポートファイル
    └── cache/                      # キャッシュ
```

---

## 3. データモデル

### 3.1 経営分析基盤

```python
# src/analytics/models.py

class SegmentDefinition:
    """セグメント定義（4分類）"""
    segment_id: str          # A, B, C, D
    segment_name: str        # 資格あり若手, 資格ありベテラン, etc.
    has_qualification: bool  # 電気工事士資格の有無
    age_condition: str       # "40歳以下" or "40歳超"
    conversion_rate: float   # 期待展開率
    priority: int            # 優先度（1-4）

# セグメント定義マスタ
SEGMENTS = {
    "A": SegmentDefinition("A", "資格あり若手", True, "40歳以下", 0.75, 1),
    "B": SegmentDefinition("B", "資格ありベテラン", True, "40歳超", 0.60, 2),
    "C": SegmentDefinition("C", "資格なし若手", False, "40歳以下", 0.40, 3),
    "D": SegmentDefinition("D", "資格なしシニア", False, "40歳超", 0.20, 4),
}

class Lead:
    """リード情報"""
    id: str
    name: str
    age: int
    prefecture: str
    qualification: str       # 第一種/第二種電気工事士 or なし
    has_qualification: bool  # 電気工事士資格の有無
    segment_id: str          # 自動計算: A/B/C/D
    conversion_rate: float   # セグメントに基づく期待展開率
    assigned_ca_id: str
    status: str              # active/converted/lost
    created_at: datetime

def assign_segment(has_qualification: bool, age: int) -> tuple[str, float]:
    """セグメント自動判定"""
    if has_qualification:
        return ("A", 0.75) if age <= 40 else ("B", 0.60)
    else:
        return ("C", 0.40) if age <= 40 else ("D", 0.20)

class CAPerformance:
    """CAパフォーマンス"""
    ca_id: str
    name: str
    team: str
    target_leads: int
    current_leads: int
    segment_a_count: int     # セグメント別保有数
    segment_b_count: int
    segment_c_count: int
    segment_d_count: int
    target_expected_conversions: float
    current_expected_conversions: float
    achievement_rate: float  # current / target
    avg_conversion_rate: float
    status: str              # on_track / below_target / at_risk
```

### 3.2 フィードバックシステム

```python
# src/feedback/models.py

class TranscriptFile:
    """書き起こしファイル"""
    id: str
    file_name: str           # 元ファイル名
    file_path: str           # ファイルパス
    ca_id: str               # ファイル名から抽出
    meeting_id: str          # ファイル名から抽出
    meeting_date: date       # ファイル名から抽出
    content: str             # テキスト内容
    status: str              # pending/processed/failed
    processed_at: datetime | None

class Feedback:
    """フィードバック"""
    id: str
    transcript_id: str
    ca_id: str
    summary: str
    strengths: list[str]
    improvements: list[str]
    pss_score: dict
    ads_score: dict
    generated_at: datetime
    notified_at: datetime | None
```

### 3.3 求人データ整備

```python
# src/job_data/models.py

class JobPosting:
    """収集した求人情報"""
    id: str
    source: str           # 取得元サイト
    source_id: str        # 元サイトでのID
    company_name: str
    prefecture: str       # 都道府県
    city: str
    qualification: str    # 必要資格
    title: str
    # 給与情報（形態別）
    salary_type: str      # yearly / monthly / daily
    daily_min: int | None   # 日給下限（円）
    daily_max: int | None   # 日給上限（円）
    monthly_min: int | None # 月給下限（万円）
    monthly_max: int | None # 月給上限（万円）
    yearly_min: int         # 年収下限（万円）※全形態で算出
    yearly_max: int         # 年収上限（万円）※全形態で算出
    url: str
    collected_at: datetime
    is_active: bool

class ExistingCompany:
    """既存保有法人"""
    id: str
    name: str
    covered_prefectures: list[str]  # 保有エリア（都道府県リスト）
    has_relationship: bool

class OwnedJobPosting:
    """自社保有求人"""
    id: str
    company_id: str       # 既存法人への参照
    company_name: str
    prefecture: str
    title: str
    qualification: str    # 必要資格
    # 給与情報（形態別）
    salary_type: str      # yearly / monthly / daily
    daily_min: int | None
    daily_max: int | None
    monthly_min: int | None
    monthly_max: int | None
    yearly_min: int
    yearly_max: int
    is_active: bool

class NewCompanyReport:
    """新規法人レポート"""
    generated_at: datetime
    new_companies: list[JobPosting]  # 新規法人の求人リスト
    total_count: int
    by_prefecture: dict[str, int]

class NewAreaReport:
    """既存法人・新規エリアレポート"""
    generated_at: datetime
    company_name: str
    existing_areas: list[str]        # 既存の保有エリア
    new_areas: list[str]             # 新たに発見されたエリア
    new_postings: list[JobPosting]   # 新エリアの求人

class MissingJobReport:
    """不足求人レポート"""
    generated_at: datetime
    missing_jobs: list[JobPosting]   # 自社で保有していない求人
    by_company: dict[str, list[JobPosting]]
    by_prefecture: dict[str, int]

class CoverageReport:
    """都道府県別カバー率レポート"""
    generated_at: datetime
    coverage_by_prefecture: dict[str, CoverageStats]

class CoverageStats:
    """都道府県別カバー統計"""
    prefecture: str
    market_total: int        # 市場全体の求人数
    owned_count: int         # 自社保有数
    coverage_rate: float     # カバー率 (owned / market)
    new_company_count: int   # 新規法人数
    new_area_count: int      # 既存法人の新規エリア数
```

---

## 4. コンポーネント詳細

### 4.1 共通基盤

#### Config（設定管理）
```python
# 環境変数から設定を読み込み
# .env, config/*.yaml をサポート
```

#### Database
```python
# SQLAlchemy ベースのORM
# PostgreSQL または SQLite をサポート
```

#### Scheduler
```python
# APScheduler または Celery
# cron形式でのジョブスケジューリング
```

#### AIClient
```python
# Anthropic Claude APIのラッパー
# プロンプト管理、レート制限対応
```

### 4.2 外部連携

#### TranscriptReader
- 指定ディレクトリからの書き起こしファイル読み込み
- ファイル名パース（日付、CA_ID、会議ID抽出）
- 処理済みファイルの移動管理

#### SlackClient
- Bot Token認証
- メッセージ送信
- ユーザーID検索

#### ScrapingEngine
- 各求人サイト用のスクレイパー
- レート制限対応
- プロキシ対応（必要に応じて）

---

## 5. データフロー

### 5.1 フィードバックシステム

```
[Zoom書き起こし] ──手動配置──▶ [data/transcripts/pending/]
                                        │
                                        ▼
                              [TranscriptReader]
                                        │
                                        ▼
                              [Claude AI分析]
                                        │
                                        ▼
                         [Feedback DB] ──通知──▶ [Slack]
                                        │
                                        ▼
                         [data/transcripts/processed/]
```

### 5.2 求人データ整備

```
[求人サイト群] ──スクレイピング──▶ [Raw Data]
                                      │
                                      ▼
                              [正規化処理]
                              (会社名、エリア、求人内容)
                                      │
                                      ▼
                              [JobPosting DB]
                                      │
                    ┌─────────────────┼─────────────────┐
                    ▼                 ▼                 ▼
           [法人マッチング]     [エリア比較]       [求人比較]
                    │                 │                 │
                    ▼                 ▼                 ▼
           ┌───────┴───────┐   ┌─────┴─────┐     ┌─────┴─────┐
           ▼               ▼   ▼           ▼     ▼           ▼
       [新規法人]    [既存法人] [既存エリア] [新エリア] [保有済] [不足求人]
           │               └───────┬───────┘     │           │
           ▼                       ▼             ▼           ▼
    [新規法人リスト]    [既存法人・新規エリアリスト]   [不足求人レポート]
           │                       │                         │
           └───────────────────────┼─────────────────────────┘
                                   ▼
                         [定期レポート/Slack通知]
```

**比較フロー詳細:**

1. **法人マッチング**: 収集した求人の法人名を既存保有法人リストと照合
   - マッチしない → 新規法人リストへ
   - マッチする → 既存法人として次の処理へ

2. **エリア比較**: 既存法人について、収集エリアと自社保有エリアを比較
   - 新しいエリア → 既存法人・新規エリアリストへ
   - 既存エリア → 求人比較へ

3. **求人比較**: 自社保有求人と収集求人を比較
   - 保有していない → 不足求人レポートへ

---

## 6. 技術選定

| 項目 | 選定 | 理由 |
|------|------|------|
| 言語 | Python 3.11+ | AIライブラリのエコシステム |
| AI | Claude API | 高品質な日本語対応 |
| DB | SQLite（開発）/ PostgreSQL（本番） | シンプルさとスケーラビリティ |
| ORM | SQLAlchemy | 柔軟性と成熟度 |
| スケジューラ | APScheduler | 軽量、単一プロセスで動作 |
| Web Scraping | httpx + BeautifulSoup | 非同期対応、シンプル |

---

## 7. セキュリティ考慮事項

### 7.1 認証情報管理
- 全てのAPIキーは環境変数で管理
- `.env`ファイルは`.gitignore`に含める
- 本番環境ではSecret Managerを使用

### 7.2 データ保護
- 個人情報を含む録音/文字起こしデータは暗号化
- データ保持期間の設定
- アクセスログの記録

### 7.3 外部サービス連携
- OAuth2対応サービスはrefresh tokenを安全に管理
- API呼び出しのレート制限を遵守
- エラー時のリトライ戦略

---

*最終更新: 2025-11-29*
