# 週1回自動チェックの設定状況

## ✅ 現在の設定

### 実行スケジュール

- **頻度**: 毎週1回
- **曜日**: 月曜日
- **時刻**: 9:00
- **スクリプト**: `scripts/check_strategy_updates.py`

### 設定ファイルの場所

```
~/Library/LaunchAgents/com.jobscout.strategy-check.plist
```

### ログファイル

- **標準出力**: `logs/strategy-check.log`
- **エラー出力**: `logs/strategy-check-error.log`
- **チェック履歴**: `data/monitoring/strategy_checks.json`
- **レポート**: `data/monitoring/strategy_check_report_YYYYMMDD.txt`

---

## 🔍 設定の確認方法

### 1. 自動実行の状態確認

```bash
# LaunchAgentの状態を確認
launchctl list | grep strategy-check
```

**出力例**:
```
-	0	com.jobscout.strategy-check
```
`-` は正常、数字はエラーコード

### 2. 設定ファイルの内容確認

```bash
cat ~/Library/LaunchAgents/com.jobscout.strategy-check.plist
```

### 3. ログの確認

```bash
# 最新のログを確認
tail -f logs/strategy-check.log

# エラーログを確認
tail -f logs/strategy-check-error.log

# 最新のレポートを確認
ls -lt data/monitoring/strategy_check_report_*.txt | head -1 | xargs cat
```

---

## 🛠️ 設定の変更

### 実行頻度の変更

設定ファイルを編集して変更できます：

```bash
# 設定ファイルを編集
open ~/Library/LaunchAgents/com.jobscout.strategy-check.plist
```

**変更例**:

1. **毎週火曜日 10:00**に変更:
   ```xml
   <key>Weekday</key>
   <integer>2</integer>  <!-- 1=月, 2=火, ..., 7=日 -->
   <key>Hour</key>
   <integer>10</integer>
   ```

2. **毎日 9:00**に変更:
   ```xml
   <!-- StartCalendarIntervalを削除してStartIntervalに変更 -->
   <key>StartInterval</key>
   <integer>86400</integer>  <!-- 秒単位（86400秒=24時間） -->
   ```

3. **毎週月・水・金 9:00**に変更:
   - 3つのLaunchAgent設定ファイルを作成

### 設定変更後の再読み込み

```bash
# 既存の設定をアンロード
launchctl unload ~/Library/LaunchAgents/com.jobscout.strategy-check.plist

# 変更後の設定を読み込み
launchctl load ~/Library/LaunchAgents/com.jobscout.strategy-check.plist
```

---

## 📧 通知設定（オプション）

チェック結果をSlackやメールで通知する場合は、スクリプトを拡張できます。

### Slack通知の追加

```python
# scripts/check_strategy_updates.py に追加
import os
import httpx

def notify_to_slack(message: str):
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if webhook_url:
        httpx.post(webhook_url, json={"text": message})
```

---

## ✅ 動作確認

### 手動で実行してテスト

```bash
# 手動でスクリプトを実行
python scripts/check_strategy_updates.py
```

### 次回実行日の確認

LaunchAgentは毎週月曜日9時に自動実行されます。

---

## 🔄 自動実行の停止・再開

### 停止

```bash
launchctl unload ~/Library/LaunchAgents/com.jobscout.strategy-check.plist
```

### 再開

```bash
launchctl load ~/Library/LaunchAgents/com.jobscout.strategy-check.plist
```

### 完全削除

```bash
launchctl unload ~/Library/LaunchAgents/com.jobscout.strategy-check.plist
rm ~/Library/LaunchAgents/com.jobscout.strategy-check.plist
```

---

## 📊 チェック結果の活用

### レポートの確認

```bash
# 最新のレポートを表示
ls -t data/monitoring/strategy_check_report_*.txt | head -1 | xargs cat
```

### チェック履歴の確認

```bash
# チェック履歴（JSON形式）を確認
cat data/monitoring/strategy_checks.json
```

---

## 🔗 関連ドキュメント

- [チェックリスト](CHECKLIST.md)
- [監視リソース](MONITORING_RESOURCES.md)
- [自動更新セットアップ](AUTO_UPDATE_SETUP.md)

---

*最終更新: 2025年11月30日*

