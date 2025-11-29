# デプロイ手順

## 1. 環境構成

### 1.1 環境一覧

| 環境 | 用途 | インフラ |
|------|------|----------|
| Local | 開発・テスト | ローカルマシン |
| Staging | 検証 | TBD |
| Production | 本番 | TBD |

### 1.2 最小構成要件

| 項目 | 要件 |
|------|------|
| CPU | 2コア以上 |
| メモリ | 4GB以上 |
| ストレージ | 50GB以上 |
| Python | 3.11以上 |

---

## 2. ローカル環境

### 2.1 セットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd job-scout-agent

# 仮想環境作成・有効化
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 依存関係インストール
pip install -e ".[dev]"

# 環境変数設定
cp .env.example .env
# .envファイルを編集

# データベース初期化
python scripts/init_db.py

# データディレクトリ作成
mkdir -p data/{transcripts,exports,cache}
mkdir -p logs
```

### 2.2 環境変数

```env
# .env

# ===================
# API Keys
# ===================
ANTHROPIC_API_KEY=your_anthropic_api_key
OPENAI_API_KEY=your_openai_api_key  # Whisper用（オプション）

# ===================
# Slack
# ===================
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_SIGNING_SECRET=your_signing_secret

# ===================
# Database
# ===================
DATABASE_URL=sqlite:///data/app.db
# 本番: postgresql://user:pass@host:5432/dbname

# ===================
# File Paths
# ===================
TRANSCRIPT_DIR=./data/transcripts
EXPORT_DIR=./data/exports

# ===================
# Application
# ===================
DEBUG_MODE=true
LOG_LEVEL=INFO
```

### 2.3 書き起こしファイルの配置

フィードバックシステムは、事前に書き起こされたテキストファイルを読み込みます。

```
data/
└── transcripts/
    ├── 2025-01-15_ca001_meeting123.txt
    ├── 2025-01-15_ca002_meeting456.txt
    └── ...
```

**ファイル命名規則:**
```
{日付}_{CA_ID}_{会議ID}.txt
```

**ファイル形式:**
- UTF-8エンコーディング
- プレーンテキスト
- タイムスタンプ付きが望ましい（任意）

---

## 3. 本番環境

### 3.1 サーバーセットアップ（Linux）

```bash
# システム更新
sudo apt update && sudo apt upgrade -y

# Python環境
sudo apt install python3.11 python3.11-venv python3-pip -y

# PostgreSQL（オプション）
sudo apt install postgresql postgresql-contrib -y

# アプリケーションディレクトリ作成
sudo mkdir -p /opt/job-scout-agent
sudo chown $USER:$USER /opt/job-scout-agent
```

### 3.2 アプリケーションデプロイ

```bash
cd /opt/job-scout-agent

# コードデプロイ
git clone <repository-url> .
# または git pull origin main

# 仮想環境セットアップ
python3.11 -m venv .venv
source .venv/bin/activate
pip install -e .

# 環境変数設定
cp .env.example .env
# 本番用の値を設定

# データベース初期化
python scripts/init_db.py

# ディレクトリ作成
mkdir -p data/{transcripts,exports,cache}
mkdir -p logs
```

### 3.3 Systemdサービス設定

```ini
# /etc/systemd/system/job-scout-agent.service
[Unit]
Description=Job Scout Agent
After=network.target

[Service]
Type=simple
User=jobscout
WorkingDirectory=/opt/job-scout-agent
Environment="PATH=/opt/job-scout-agent/.venv/bin"
ExecStart=/opt/job-scout-agent/.venv/bin/python -m src.agent
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

```bash
# サービス有効化
sudo systemctl daemon-reload
sudo systemctl enable job-scout-agent
sudo systemctl start job-scout-agent

# ステータス確認
sudo systemctl status job-scout-agent
```

---

## 4. データベースセットアップ

### 4.1 SQLite（開発/小規模）

```python
# scripts/init_db.py
from src.common.database import engine, Base
from src.analytics.models import *
from src.feedback.models import *
from src.job_data.models import *

def init_database():
    Base.metadata.create_all(bind=engine)
    print("Database initialized successfully")

if __name__ == "__main__":
    init_database()
```

### 4.2 PostgreSQL（本番）

```bash
# データベース作成
sudo -u postgres createuser jobscout
sudo -u postgres createdb jobscout_db -O jobscout

# パスワード設定
sudo -u postgres psql
ALTER USER jobscout WITH PASSWORD 'secure_password';
\q
```

```env
# .env
DATABASE_URL=postgresql://jobscout:secure_password@localhost:5432/jobscout_db
```

---

## 5. 定期実行設定

### 5.1 APScheduler（アプリケーション内）

```python
# src/common/scheduler.py
from apscheduler.schedulers.background import BackgroundScheduler

scheduler = BackgroundScheduler()

# フィードバック生成: 毎日9時
scheduler.add_job(
    process_new_transcripts,
    'cron',
    hour=9,
    minute=0
)

# 求人データ収集: 毎週月曜 2時
scheduler.add_job(
    collect_job_data,
    'cron',
    day_of_week='mon',
    hour=2
)

scheduler.start()
```

### 5.2 Cron（システム）

```bash
# crontab -e

# フィードバック処理: 毎日9時
0 9 * * * cd /opt/job-scout-agent && .venv/bin/python -m src.feedback.runner

# 求人データ収集: 毎週月曜 2時
0 2 * * 1 cd /opt/job-scout-agent && .venv/bin/python -m src.job_data.runner

# 経営分析レポート: 毎日6時
0 6 * * * cd /opt/job-scout-agent && .venv/bin/python -m src.analytics.runner
```

---

## 6. 監視設定

### 6.1 ログ設定

```python
# ログローテーション設定
# /etc/logrotate.d/job-scout-agent
/opt/job-scout-agent/logs/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    notifempty
}
```

### 6.2 ヘルスチェック

```python
# src/common/health.py
from datetime import datetime

def health_check() -> dict:
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "database": check_database(),
        "disk_space": check_disk_space(),
    }
```

---

## 7. バックアップ

### 7.1 データベースバックアップ

```bash
# SQLite
cp data/app.db backups/app_$(date +%Y%m%d).db

# PostgreSQL
pg_dump -U jobscout jobscout_db > backups/db_$(date +%Y%m%d).sql
```

### 7.2 自動バックアップ設定

```bash
# /etc/cron.daily/job-scout-backup
#!/bin/bash
BACKUP_DIR=/opt/job-scout-agent/backups
mkdir -p $BACKUP_DIR

# 7日以上古いバックアップを削除
find $BACKUP_DIR -name "*.db" -mtime +7 -delete
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete

# バックアップ実行
cp /opt/job-scout-agent/data/app.db $BACKUP_DIR/app_$(date +%Y%m%d).db
```

---

## 8. トラブルシューティング

### 8.1 よくある問題

| 問題 | 原因 | 解決策 |
|------|------|--------|
| APIエラー | APIキー未設定 | .envファイル確認 |
| DB接続エラー | 接続文字列不正 | DATABASE_URL確認 |
| 権限エラー | ディレクトリ権限 | chmod/chown確認 |
| メモリ不足 | 大量データ処理 | バッチサイズ調整 |

### 8.2 ログ確認

```bash
# アプリケーションログ
tail -f /opt/job-scout-agent/logs/app.log

# Systemdログ
journalctl -u job-scout-agent -f
```

---

*最終更新: 2025-01-15*
