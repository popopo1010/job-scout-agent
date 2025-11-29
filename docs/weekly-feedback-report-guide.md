# 週次フィードバックレポート機能 使用ガイド

## 概要

週次でフィードバックの総括レポートを生成し、CAごとにSlackメンションをつけて自動配信する機能です。

## 機能

- **自動集計**: 過去1週間（月曜日〜日曜日）のフィードバックを自動集計
- **CAごとの個別レポート**: 各CAにメンション付きで個別レポートを配信
- **前週比較**: 前週とのスコア比較で成長傾向を表示
- **繰り返し改善点の検出**: 週内で繰り返し指摘された改善点を強調
- **全体サマリー**: チーム全体のサマリーを先に配信

## 使用方法

### 手動実行

```bash
# 前週のレポートを生成・配信
python3 scripts/generate_weekly_report.py

# 特定の期間を指定
python3 scripts/generate_weekly_report.py \
  --week-start 2025-11-24 \
  --week-end 2025-11-30

# 特定のCAのみ
python3 scripts/generate_weekly_report.py --ca-id FUKUYAMA

# Slack通知なし（プレビュー）
python3 scripts/generate_weekly_report.py --no-slack
```

### 定期実行の設定

#### Cronを使う方法（推奨）

```bash
# crontab -e

# 毎週月曜日 9:00に実行
0 9 * * 1 cd /Users/ikeobook15/Downloads/job-scout-agent && /usr/bin/python3 scripts/generate_weekly_report.py >> logs/weekly_report.log 2>&1
```

#### macOSのLaunchAgentを使う方法

```bash
# スクリプトを作成
cat > ~/Library/LaunchAgents/com.jobscout.weekly-report.plist << 'EOF'
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobscout.weekly-report</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>/Users/ikeobook15/Downloads/job-scout-agent/scripts/generate_weekly_report.py</string>
    </array>
    <key>StartCalendarInterval</key>
    <dict>
        <key>Weekday</key>
        <integer>1</integer>
        <key>Hour</key>
        <integer>9</integer>
        <key>Minute</key>
        <integer>0</integer>
    </dict>
    <key>StandardOutPath</key>
    <string>/Users/ikeobook15/Downloads/job-scout-agent/logs/weekly_report.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/ikeobook15/Downloads/job-scout-agent/logs/weekly_report_error.log</string>
</dict>
</plist>
EOF

# LaunchAgentを読み込む
launchctl load ~/Library/LaunchAgents/com.jobscout.weekly-report.plist
```

## 設定

### CA-Slack IDマッピング

CA IDとSlackユーザーIDの紐付けが必要です。

#### 方法1: CSVファイルから読み込む（推奨）

`data/sample/analytics/ca_master.csv` に `slack_user_id` カラムがあれば、自動的に読み込まれます。

```csv
ca_id,name,team,slack_user_id,...
FUKUYAMA,ふくやま,チーム名,U01234567,...
```

#### 方法2: YAMLファイルで設定

`config/ca_slack_mapping.yaml` を作成：

```yaml
ca_slack_mappings:
  - ca_id: "FUKUYAMA"
    name: "ふくやま"
    slack_user_id: "U01234567"
  - ca_id: "CA001"
    name: "山田一郎"
    slack_user_id: "U0001YAMADA"
```

### Slack設定

環境変数を設定：

```bash
export SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"
export SLACK_DEFAULT_CHANNEL="#dk_ca_ops"
```

または、`.env`ファイルに設定：

```env
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_DEFAULT_CHANNEL=#dk_ca_ops
```

**重要**: メンション機能を使用するには、`SLACK_BOT_TOKEN`が必要です（Webhook URLではメンションできません）。

## レポート内容

### 全体サマリー

- フィードバック生成件数（合計）
- 平均スコア
- 最も多く指摘された改善点

### CAごとの個別レポート

- **今週のフィードバック件数**: 週内に生成されたフィードバック数
- **平均スコア**: 前週との比較付き
- **総合評価の分布**: 優秀/良好/要改善/要指導の件数
- **今週最も多く指摘された改善点**: トップ3
- **今週の良かった点**: 評価された点
- **成長傾向**: 前週との比較
- **次週に向けた改善目標**: 最も重要な改善点

## 配信フロー

1. **全体サマリーを配信** → `#dk_ca_ops`チャンネル
2. **各CAの個別レポートを配信** → `#dk_ca_ops`チャンネル（メンション付き）

各レポートは別々のメッセージとして送信されます。

## 動作確認

```bash
# プレビュー（Slack通知なし）
python3 scripts/generate_weekly_report.py --no-slack

# 特定のCAでテスト
python3 scripts/generate_weekly_report.py --ca-id FUKUYAMA --no-slack
```

## トラブルシューティング

### CA-Slack IDマッピングが見つからない

```bash
# マッピングファイルを確認
cat data/sample/analytics/ca_master.csv | grep slack_user_id

# または、config/ca_slack_mapping.yaml を作成
```

### メンションが機能しない

- `SLACK_BOT_TOKEN`が設定されているか確認
- Botがワークスペースにインストールされているか確認
- Botがチャンネルに追加されているか確認

### フィードバック履歴が見つからない

- `data/feedback/history.json` が存在するか確認
- フィードバックが生成されているか確認（履歴はフィードバック生成時に自動保存されます）

## レポート例

### 全体サマリー

```
【週次フィードバックレポート - 全体サマリー】
期間: 2025-11-24 〜 2025-11-30

■ 全体サマリー
- フィードバック生成件数: 15件
- 平均スコア: 2.8 / 4.0
- 最も多く指摘された改善点: ニーズの深掘り不足（8件）

各CAの詳細は、以下をご確認ください。

─────────────────────────────────────
```

### CAごとの個別レポート

```
<@U01234567> ふくやまさんの週次フィードバックレポート

【週次フィードバックレポート】
期間: 2025-11-24 〜 2025-11-30

■ 今週のフィードバック件数: 3件
■ 平均スコア: 2.9 / 4.0（前週: 2.7 → +0.2 ⬆️）

■ 総合評価の分布
- 優秀: 0件
- 良好: 2件
- 要改善: 1件
- 要指導: 0件

■ 今週最も多く指摘された改善点
1. ニーズの深掘り不足（2回）
   ⚠️ 過去も2回指摘されています。根本的な改善が必要です。
2. クロージング時の期限設定が曖昧（1回）

■ 今週の良かった点
- 適切な自己紹介と時間確認ができていた（3件で評価）

■ 成長傾向
前週と比較して、平均スコアが0.2ポイント向上しています。
この調子で継続してください。

■ 次週に向けた改善目標
最も多く指摘された「ニーズの深掘り不足」を必ず改善してください。
期待展開率8%を実現するため、この改善は必須です。
同じ指摘を繰り返さないよう、徹底してください。

─────────────────────────────────────

あなたの成長を心から期待しています。
```

---

この機能により、週次でCAの成長を可視化し、継続的な改善を促すことができます。

