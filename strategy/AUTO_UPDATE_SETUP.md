# 事業戦略自動更新のセットアップ

事業戦略を定期チェック・自動更新するためのセットアップ方法です。

## 🚀 クイックスタート

### 1. 手動チェック

```bash
# 事業戦略の更新状況をチェック
python scripts/check_strategy_updates.py
```

### 2. 定期実行の設定（Cron）

```bash
# crontab -e で以下を追加

# 毎週月曜日の9時に事業戦略チェックを実行
0 9 * * 1 cd /path/to/job-scout-agent && python scripts/check_strategy_updates.py >> logs/strategy_check.log 2>&1
```

### 3. 定期実行の設定（macOS LaunchAgent）

```bash
# macOSで自動実行を設定
./scripts/setup_strategy_check.sh
```

---

## 📋 チェック項目の追加・編集

`scripts/check_strategy_updates.py` の `get_default_check_items()` メソッドを編集して、チェック項目を追加・編集できます。

```python
StrategyCheckItem(
    category="新しいカテゴリ",
    item="チェック項目名",
    last_checked=None,
    last_updated=None,
    status="NEEDS_UPDATE",
    priority=UpdatePriority.HIGH,
    notes="チェック内容の説明",
    resource_url="https://example.com",
    auto_checkable=True  # 自動チェック可能か
)
```

---

## 🤖 自動化可能な項目

### 1. 市場データの自動収集

以下のような自動化スクリプトを作成できます：

```python
# scripts/collect_market_data.py
# 政府統計データの自動取得
```

**対象データ**:
- 有効求人倍率（厚生労働省）
- 雇用統計
- 賃金統計

### 2. 競合サイトの監視

```python
# scripts/monitor_competitors.py
# 競合サイトの変更検知
```

**監視項目**:
- 求人数の推移
- 新機能のリリース
- 価格・料金体系の変更

### 3. 法規制情報の監視

```python
# scripts/monitor_regulations.py
# 省庁サイトの更新チェック
```

**監視対象**:
- 厚生労働省
- 経済産業省
- 国土交通省

---

## 📊 データ保存場所

チェック結果と収集データは以下に保存されます：

```
data/
└── monitoring/
    ├── strategy_checks.json           # チェック履歴
    ├── strategy_check_report_*.txt    # レポート
    ├── market_data/                   # 市場データ
    ├── competitors/                   # 競合情報
    └── regulations/                   # 法規制情報
```

---

## 🔔 通知設定

### Slack通知

チェック結果をSlackに通知する場合：

```python
# scripts/notify_strategy_updates.py
import httpx
from scripts.check_strategy_updates import StrategyChecker

def notify_to_slack(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    httpx.post(webhook_url, json={"text": message})
```

### メール通知

メールで通知する場合：

```python
# scripts/notify_strategy_updates.py
import smtplib
from email.mime.text import MIMEText
```

---

## 📅 推奨スケジュール

| 項目 | 頻度 | 実行タイミング |
|------|------|---------------|
| **事業戦略チェック** | 週次 | 毎週月曜 9:00 |
| **市場データ収集** | 月次 | 毎月1日 10:00 |
| **競合監視** | 週次 | 毎週月曜 9:00 |
| **法規制監視** | 月次 | 毎月1日 10:00 |

---

## 🔗 関連ドキュメント

- [チェックリスト](CHECKLIST.md)
- [監視リソース](MONITORING_RESOURCES.md)
- [事業戦略一覧](README.md)

---

*最終更新: 2025年11月30日*

