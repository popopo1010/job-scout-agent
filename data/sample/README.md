# サンプルデータ

このディレクトリには、各システムの動作確認用サンプルデータが含まれています。

## ディレクトリ構成

```
data/sample/
├── analytics/           # 経営分析基盤用
│   ├── leads.csv                    # リードデータ（セグメント情報付き）
│   ├── conversion_history.csv       # 展開実績データ
│   ├── ca_master.csv                # CAマスタ（期待値サマリ付き）
│   ├── segment_conversion_rates.csv # セグメント別期待展開率マスタ
│   └── ca_segment_holdings.csv      # CA別セグメント保有状況
├── feedback/            # フィードバックシステム用
│   ├── transcripts/     # 書き起こしファイル
│   │   ├── 2025-01-15_CA001_client-call-001.txt
│   │   └── 2025-01-16_CA002_client-call-002.txt
│   └── pss_ads_criteria.md  # PSS/ADS評価基準
└── job_data/            # 求人データ整備用
    ├── existing_companies.csv  # 既存保有法人リスト
    ├── owned_jobs.csv         # 自社保有求人
    └── scraped_jobs.csv       # スクレイピング結果（模擬）
```

---

## 1. 経営分析基盤用データ

### leads.csv - リードデータ
現在保有しているリード（見込み求職者）の情報。セグメントは自動ラベリング。

| カラム | 型 | 説明 |
|--------|-----|------|
| lead_id | string | リードID |
| name | string | 氏名 |
| age | int | 年齢 |
| prefecture | string | 都道府県 |
| qualification | string | 保有資格（第一種/第二種電気工事士 or なし） |
| has_qualification | bool | 電気工事士資格の有無 |
| assigned_ca_id | string | 担当CA ID |
| status | string | ステータス（active/converted/lost） |
| segment_id | string | 自動計算されたセグメントID（A/B/C/D） |
| conversion_rate | float | 期待展開率（0.0〜1.0） |
| created_at | date | 登録日 |

### conversion_history.csv - 展開実績データ
過去のリード展開（成約/失注）の実績データ

| カラム | 型 | 説明 |
|--------|-----|------|
| record_id | string | レコードID |
| lead_id | string | リードID |
| prefecture | string | 都道府県 |
| age_group | string | 年齢層（20代/30代/40代） |
| qualification | string | 資格 |
| ca_id | string | 担当CA ID |
| result | string | 結果（success/failed） |
| converted_at | date | 展開日 |

### segment_conversion_rates.csv - セグメント定義マスタ
4つのセグメント定義と期待展開率

| カラム | 型 | 説明 |
|--------|-----|------|
| segment_id | string | セグメントID（A/B/C/D） |
| segment_name | string | セグメント名 |
| has_qualification | bool | 電気工事士資格の有無 |
| age_condition | string | 年齢条件 |
| description | string | セグメントの説明 |
| sample_size | int | サンプル数（過去実績件数） |
| success_count | int | 成功件数 |
| conversion_rate | float | 展開率（0.0〜1.0） |
| priority | int | 優先度（1が最優先） |

**セグメント定義:**
| ID | 名称 | 資格 | 年齢 | 期待展開率 | 説明 |
|----|------|------|------|-----------|------|
| A | 資格あり若手 | あり | 40歳以下 | 75% | 即戦力として期待できる若手層 |
| B | 資格ありベテラン | あり | 40歳超 | 60% | 経験豊富な即戦力 |
| C | 資格なし若手 | なし | 40歳以下 | 40% | 育成対象として可能性あり |
| D | 資格なしシニア | なし | 40歳超 | 20% | 展開難易度が高い |

### ca_segment_holdings.csv - CA別セグメント保有状況
各CAが保有するリードのセグメント別内訳

| カラム | 型 | 説明 |
|--------|-----|------|
| ca_id | string | CA ID |
| segment_id | string | セグメントID（A/B/C/D） |
| segment_name | string | セグメント名 |
| lead_count | int | 保有リード数 |
| conversion_rate | float | 期待展開率 |
| expected_conversions | float | 期待展開数（lead_count × conversion_rate） |

### ca_master.csv - CAマスタ
キャリアアドバイザーの基本情報とセグメント別保有状況サマリ

| カラム | 型 | 説明 |
|--------|-----|------|
| ca_id | string | CA ID |
| name | string | 氏名 |
| team | string | 所属チーム |
| slack_user_id | string | Slack ユーザーID |
| target_leads | int | 目標保有件数 |
| current_leads | int | 現在保有件数 |
| segment_a_count | int | セグメントA保有数 |
| segment_b_count | int | セグメントB保有数 |
| segment_c_count | int | セグメントC保有数 |
| segment_d_count | int | セグメントD保有数 |
| target_expected_conversions | float | 目標期待展開数 |
| current_expected_conversions | float | 現在の期待展開数合計 |
| achievement_rate | float | 達成率（current / target） |
| avg_conversion_rate | float | 平均期待展開率 |
| status | string | 状態（on_track/below_target/at_risk）|

**ステータス判定基準:**
| status | 条件 | 説明 |
|--------|------|------|
| on_track | achievement_rate >= 0.7 | 順調 |
| below_target | 0.5 <= achievement_rate < 0.7 | 目標未達 |
| at_risk | achievement_rate < 0.5 | 要注意 |

### セグメント自動ラベリングロジック

リードのセグメントは以下のロジックで自動計算されます：

```python
def assign_segment(has_qualification: bool, age: int) -> str:
    """
    リードのセグメントを自動判定

    Args:
        has_qualification: 電気工事士資格の有無
        age: 年齢

    Returns:
        segment_id: A, B, C, D のいずれか
    """
    if has_qualification:
        if age <= 40:
            return "A"  # 資格あり若手
        else:
            return "B"  # 資格ありベテラン
    else:
        if age <= 40:
            return "C"  # 資格なし若手
        else:
            return "D"  # 資格なしシニア

def get_conversion_rate(segment_id: str) -> float:
    """セグメントIDから期待展開率を取得"""
    rates = {"A": 0.75, "B": 0.60, "C": 0.40, "D": 0.20}
    return rates[segment_id]
```

**判定フロー図:**
```
                    ┌─────────────────┐
                    │  リード登録     │
                    └────────┬────────┘
                             │
                    ┌────────▼────────┐
                    │ 電気工事士資格   │
                    │ を保有している？ │
                    └────────┬────────┘
                             │
              ┌──────────────┴──────────────┐
              │ Yes                         │ No
     ┌────────▼────────┐           ┌────────▼────────┐
     │ 年齢 <= 40歳？  │           │ 年齢 <= 40歳？  │
     └────────┬────────┘           └────────┬────────┘
              │                             │
    ┌─────────┴─────────┐         ┌─────────┴─────────┐
    │ Yes      │ No     │         │ Yes      │ No     │
┌───▼───┐  ┌───▼───┐  ┌───▼───┐  ┌───▼───┐
│ A:75% │  │ B:60% │  │ C:40% │  │ D:20% │
└───────┘  └───────┘  └───────┘  └───────┘
```

---

## 2. フィードバックシステム用データ

### transcripts/ - 書き起こしファイル

**ファイル命名規則:**
```
{YYYY-MM-DD}_{CA_ID}_{会議識別子}.txt
```

**サンプルファイル:**
- `2025-01-15_CA001_client-call-001.txt` - 良い例（丁寧なヒアリング、適切な提案）
- `2025-01-16_CA002_client-call-002.txt` - 改善が必要な例（雑な対応、ニーズ把握不足）

### pss_ads_criteria.md - 評価基準
PSS/ADSに基づくフィードバック評価基準

---

## 3. 求人データ整備用データ

### existing_companies.csv - 既存保有法人リスト
すでに取引関係のある法人

| カラム | 型 | 説明 |
|--------|-----|------|
| company_id | string | 法人ID |
| company_name | string | 法人名 |
| covered_prefectures | string | 保有エリア（カンマ区切り） |
| has_relationship | bool | 取引関係有無 |
| notes | string | 備考 |

### owned_jobs.csv - 自社保有求人
自社で保有している求人情報

| カラム | 型 | 説明 |
|--------|-----|------|
| job_id | string | 求人ID |
| company_id | string | 法人ID |
| company_name | string | 法人名 |
| prefecture | string | 都道府県 |
| title | string | 求人タイトル |
| qualification | string | 必要資格 |
| salary_type | string | 元の給与形態（yearly/monthly/daily） |
| daily_min | int | 日給下限（円）※日給の場合のみ |
| daily_max | int | 日給上限（円）※日給の場合のみ |
| monthly_min | int | 月給下限（万円）※月給・日給の場合 |
| monthly_max | int | 月給上限（万円）※月給・日給の場合 |
| yearly_min | int | 年収下限（万円）※全形態で算出 |
| yearly_max | int | 年収上限（万円）※全形態で算出 |
| is_active | bool | 有効フラグ |

### scraped_jobs.csv - スクレイピング結果（模擬）
求人サイトからスクレイピングした結果を模擬

| カラム | 型 | 説明 |
|--------|-----|------|
| scraped_id | string | スクレイピングID |
| source | string | 取得元サイト |
| source_id | string | 元サイトでのID |
| company_name | string | 法人名 |
| prefecture | string | 都道府県 |
| city | string | 市区町村 |
| title | string | 求人タイトル |
| qualification | string | 必要資格 |
| salary_type | string | 元の給与形態（yearly/monthly/daily） |
| daily_min | int | 日給下限（円）※日給の場合のみ |
| daily_max | int | 日給上限（円）※日給の場合のみ |
| monthly_min | int | 月給下限（万円）※月給・日給の場合 |
| monthly_max | int | 月給上限（万円）※月給・日給の場合 |
| yearly_min | int | 年収下限（万円）※全形態で算出 |
| yearly_max | int | 年収上限（万円）※全形態で算出 |
| url | string | 求人URL |
| scraped_at | date | スクレイピング日時 |

### 給与形態と換算ロジック

求人データは3種類の給与形態で記載され、すべて年収に換算されます。
日給の場合は月給も併せて算出します。

| salary_type | 元データ | 月給換算 | 年収換算 |
|-------------|---------|---------|---------|
| yearly | yearly_min/max のみ | - | そのまま |
| monthly | monthly_min/max | そのまま | × 12 |
| daily | daily_min/max | × 20（月間稼働20日） | × 240（年間稼働240日） |

**換算例:**

| 元の給与形態 | 元データ | → 月給（万円） | → 年収（万円） |
|-------------|---------|---------------|---------------|
| yearly | 400〜550万円 | - | 400〜550 |
| monthly | 30〜40万円 | 30〜40 | 360〜480 |
| daily | 14,000〜18,000円 | 28〜36 | 336〜432 |

**比較時の注意点:**
- 年収（yearly_min/max）は全ての求人で算出済みのため、比較に使用
- 月給・日給は元の給与形態がその形態の場合のみ値が入る
- 空欄の場合は該当する給与形態ではないことを示す

---

## 期待される出力（求人データ整備）

### 新規法人リスト
`scraped_jobs.csv`から`existing_companies.csv`に存在しない法人を抽出

**期待結果:**
- 新日本電気株式会社（東京都、神奈川県）
- 日本電設サービス株式会社（大阪府）
- 南九州電設株式会社（宮崎県）
- 四国電気工業株式会社（香川県、愛媛県）
- 北陸電設株式会社（石川県、富山県）
- 山陰電気サービス株式会社（島根県）

### 既存法人・新規エリアリスト
`existing_companies.csv`の法人が新しいエリアで求人を出しているケース

**期待結果:**
| 法人名 | 既存エリア | 新規エリア |
|--------|-----------|-----------|
| 東京電気工事株式会社 | 東京都,神奈川県,埼玉県 | 千葉県 |
| 関西電設株式会社 | 大阪府,兵庫県,京都府 | 奈良県 |
| 中部エンジニアリング株式会社 | 愛知県,静岡県 | 三重県 |
| 九州電工株式会社 | 福岡県,熊本県 | 鹿児島県 |
| 東北電気工業株式会社 | 宮城県,岩手県 | 秋田県 |

---

## 使用方法

```python
import pandas as pd

# 経営分析基盤
leads = pd.read_csv('data/sample/analytics/leads.csv')
history = pd.read_csv('data/sample/analytics/conversion_history.csv')
ca_master = pd.read_csv('data/sample/analytics/ca_master.csv')

# 求人データ整備
existing = pd.read_csv('data/sample/job_data/existing_companies.csv')
owned = pd.read_csv('data/sample/job_data/owned_jobs.csv')
scraped = pd.read_csv('data/sample/job_data/scraped_jobs.csv')
```

---

*最終更新: 2025-11-29*
