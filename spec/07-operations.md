# 運用ガイド

## 1. 日常運用

### 1.1 システム稼働状況確認

```bash
# サービス状態確認
sudo systemctl status job-scout-agent

# ログ確認（直近100行）
tail -100 /opt/job-scout-agent/logs/app.log

# ディスク使用量確認
df -h /opt/job-scout-agent
du -sh /opt/job-scout-agent/data/*
```

### 1.2 定期タスク実行状況

| タスク | 実行タイミング | 確認方法 |
|--------|---------------|----------|
| フィードバック生成 | 毎日 9:00 | logs/feedback.log |
| 求人データ収集 | 毎週月曜 2:00 | logs/job_data.log |
| 経営分析レポート | 毎日 6:00 | logs/analytics.log |

---

## 2. フィードバックシステム運用

### 2.1 書き起こしファイルの配置

**ディレクトリ構成:**
```
data/
└── transcripts/
    ├── pending/           # 処理待ちファイル
    │   ├── 2025-01-15_ca001_mtg123.txt
    │   └── 2025-01-15_ca002_mtg456.txt
    ├── processed/         # 処理済みファイル
    └── failed/            # 処理失敗ファイル
```

**ファイル配置手順:**
1. Zoomの書き起こしファイルをダウンロード
2. ファイル名を命名規則に従ってリネーム
3. `data/transcripts/pending/` に配置
4. 次回の定期実行で自動処理される

**ファイル命名規則:**
```
{YYYY-MM-DD}_{CA_ID}_{会議識別子}.txt

例:
2025-01-15_ca001_weekly-mtg.txt
2025-01-15_ca002_client-call-abc.txt
```

### 2.2 手動実行

```bash
cd /opt/job-scout-agent
source .venv/bin/activate

# 全ファイル処理
python -m src.feedback.runner

# 特定ファイルのみ処理
python -m src.feedback.runner --file data/transcripts/pending/2025-01-15_ca001_mtg123.txt

# ドライラン（通知なし）
python -m src.feedback.runner --dry-run
```

### 2.3 CA-Slack ID紐付け管理

```yaml
# config/ca_mapping.yaml
ca_mappings:
  - ca_id: ca001
    name: 山田太郎
    slack_user_id: U01234567
  - ca_id: ca002
    name: 佐藤花子
    slack_user_id: U07654321
```

### 2.4 フィードバック履歴確認

```bash
# 特定CAのフィードバック履歴
python -m src.feedback.history --ca-id ca001 --days 30

# 全体統計
python -m src.feedback.stats
```

---

## 3. 経営分析基盤運用

### 3.1 データ更新

```bash
# リードデータインポート
python -m src.analytics.import_leads --file data/imports/leads_20250115.csv

# CA情報更新
python -m src.analytics.import_ca --file data/imports/ca_master.csv

# 実績データインポート
python -m src.analytics.import_results --file data/imports/results_20250115.csv
```

### 3.2 レポート生成

```bash
# セグメント別期待展開率レポート
python -m src.analytics.report segment --output exports/segment_report.xlsx

# 適正保有件数レポート
python -m src.analytics.report optimal --output exports/optimal_leads.xlsx

# パフォーマンスレポート
python -m src.analytics.report performance --start 2025-01-01 --end 2025-01-31
```

### 3.3 ダッシュボード起動

```bash
# Streamlitダッシュボード
streamlit run src/analytics/dashboard.py --server.port 8501
```

---

## 4. 求人データ整備運用

### 4.1 マスターデータのインポート

**初回または更新時に実行:**

```bash
# 既存保有法人リストのインポート
# CSV形式: company_id, company_name, covered_prefectures（カンマ区切り）
python -m src.job_data.import_companies --file data/imports/existing_companies.csv

# 自社保有求人データのインポート
# CSV形式: job_id, company_name, prefecture, title
python -m src.job_data.import_owned_jobs --file data/imports/owned_jobs.csv
```

### 4.2 手動収集実行

```bash
# 全サイト収集
python -m src.job_data.collector

# 特定サイトのみ
python -m src.job_data.collector --source indeed
python -m src.job_data.collector --source hellowork
```

### 4.3 比較・検出実行

```bash
# 新規法人検出
python -m src.job_data.detect new_companies --output exports/new_companies.xlsx

# 既存法人・新規エリア検出
python -m src.job_data.detect new_areas --output exports/new_areas.xlsx

# 自社求人との比較（不足求人検出）
python -m src.job_data.detect missing_jobs --output exports/missing_jobs.xlsx

# 全検出を一括実行
python -m src.job_data.detect all --output-dir exports/
```

### 4.4 レポート出力

```bash
# 都道府県別カバー率レポート
python -m src.job_data.report coverage --output exports/coverage_report.xlsx

# サマリーレポート（新規法人数、新規エリア数、不足求人数）
python -m src.job_data.report summary --output exports/summary_report.xlsx
```

### 4.5 定期チェック確認

定期実行は自動で行われますが、ログで確認できます：

```bash
# 直近の実行ログ確認
tail -100 logs/job_data.log

# 前回実行からの検出件数確認
python -m src.job_data.status
```

### 4.6 通知設定

```yaml
# config/job_data_notification.yaml
notifications:
  slack_channel: "#job-data-alerts"
  notify_on:
    - new_companies      # 新規法人発見時
    - new_areas          # 既存法人の新規エリア発見時
    - threshold_reached  # カバー率が閾値を下回った時
  thresholds:
    min_coverage_rate: 0.7  # 70%以下で通知
```

---

## 5. 障害対応

### 5.1 アラート一覧

| アラート | 重要度 | 対応 |
|---------|--------|------|
| API接続エラー | 高 | APIキー/ネットワーク確認 |
| DB接続エラー | 高 | DB状態確認、再起動 |
| ディスク容量警告 | 中 | 不要ファイル削除 |
| 処理遅延 | 中 | ログ確認、原因調査 |

### 5.2 エラー発生時の手順

1. **ログ確認**
   ```bash
   tail -500 logs/app.log | grep ERROR
   ```

2. **サービス状態確認**
   ```bash
   sudo systemctl status job-scout-agent
   ```

3. **再起動**
   ```bash
   sudo systemctl restart job-scout-agent
   ```

4. **詳細調査**
   ```bash
   # 特定期間のログ抽出
   grep "2025-01-15" logs/app.log > debug.log
   ```

### 5.3 データリカバリ

```bash
# バックアップからリストア（SQLite）
cp backups/app_20250114.db data/app.db

# バックアップからリストア（PostgreSQL）
psql -U jobscout jobscout_db < backups/db_20250114.sql
```

---

## 6. メンテナンス

### 6.1 定期メンテナンス項目

| 項目 | 頻度 | 手順 |
|------|------|------|
| ログローテーション | 自動（日次） | logrotate設定済み |
| 古いデータ削除 | 月次 | cleanup.pyスクリプト |
| バックアップ確認 | 週次 | バックアップ整合性チェック |
| 依存関係更新 | 月次 | pip update |

### 6.2 クリーンアップ

```bash
# 90日以上前の処理済みファイル削除
python -m src.common.cleanup --type transcripts --days 90

# キャッシュクリア
rm -rf data/cache/*

# 古いエクスポートファイル削除
find data/exports -name "*.xlsx" -mtime +30 -delete
```

### 6.3 アップデート手順

```bash
# サービス停止
sudo systemctl stop job-scout-agent

# バックアップ
cp data/app.db backups/app_before_update.db

# コード更新
git pull origin main

# 依存関係更新
source .venv/bin/activate
pip install -e .

# DBマイグレーション（必要な場合）
python scripts/migrate.py

# サービス起動
sudo systemctl start job-scout-agent

# 動作確認
tail -f logs/app.log
```

---

## 7. 連絡先・エスカレーション

### 7.1 担当者一覧

| 役割 | 担当 | 連絡先 |
|------|------|--------|
| システム管理者 | TBD | TBD |
| 開発担当 | TBD | TBD |

### 7.2 エスカレーションフロー

1. 一次対応: ログ確認・再起動
2. 二次対応: 開発担当へ連絡
3. 三次対応: 外部ベンダー連絡（API関連）

---

*最終更新: 2025-11-29*
