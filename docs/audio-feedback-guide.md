# 音声データフィードバックシステム 使用ガイド

## 概要

音声ファイルを格納し、ZoomやNottaで作成した書き起こしファイルと紐付けて、自動的にフィードバックを生成するシステムです。

**APIを使わずに実装**されており、既存のZoom書き起こし機能やNottaの書き起こし結果をそのまま活用できます。

## システム構成

```
音声ファイル → アップロード → 書き起こしファイルと紐付け → フィードバック生成 → Slack通知
```

1. **音声ファイルのアップロード**: 音声ファイルをシステムに登録
2. **書き起こしの実施**: ZoomやNottaで手動で書き起こしを行う
3. **紐付け**: 書き起こしファイルを音声ファイルと紐付け
4. **自動フィードバック生成**: 既存システムでフィードバックを生成
5. **Slack通知**: 生成されたフィードバックを自動的にSlackに送信（`#dk_ca_ops`チャンネル）

## ディレクトリ構造

```
data/
└── audio/
    ├── pending/              # 未処理の音声ファイル
    ├── processed/            # 処理完了した音声ファイル
    ├── failed/               # 処理失敗した音声ファイル
    ├── transcripts/          # 書き起こしファイル（システム管理用）
    └── audio_metadata.json   # 音声ファイルのメタデータ
```

## 使い方

### 🚀 簡単な方法: 自動処理（推奨）

**音声ファイルをフォルダに置くだけ！** 自動的にインポート・分析が始まります。

#### ステップ1: 音声ファイルを配置

ファイル名を以下の形式にして、`data/audio/pending/` フォルダに配置：

```
{YYYY-MM-DD}_{CA_ID}_{会議識別子}.{拡張子}
```

例:
- `2025-01-15_CA001_client-call-001.m4a`
- `2025-11-28_FUKUYAMA_test-slack-001.m4a`

#### ステップ2: 自動処理を実行（定期実行も可能）

```bash
# 一度だけ実行
python3 scripts/auto_process_audio.py

# AIを使用する場合
python3 scripts/auto_process_audio.py --use-ai
```

**自動処理の内容:**
1. ✅ `data/audio/pending/` 内の新しい音声ファイルを自動登録
2. ✅ `data/audio/transcripts/pending/` 内の書き起こしファイルを自動検出・紐付け
3. ✅ 紐付け完了したファイルを自動的にフィードバック生成
4. ✅ Slack通知も自動送信

#### ステップ3: 書き起こしファイルを配置

ZoomやNottaで書き起こしを実施後、書き起こしファイル（.txt）を以下のフォルダに配置：

```
data/audio/transcripts/pending/
```

ファイル名は音声ファイルと同じ形式にしてください：
```
{YYYY-MM-DD}_{CA_ID}_{会議識別子}.txt
```

#### 定期実行の設定（オプション）

5分ごとに自動チェックする場合：

```bash
# crontab -e
*/5 * * * * cd /Users/ikeobook15/Downloads/job-scout-agent && /usr/bin/python3 scripts/auto_process_audio.py >> logs/auto_process.log 2>&1
```

これで、フォルダにファイルを置くだけで、すべて自動処理されます！

---

### 📋 従来の手動方法

#### 方法A: ファイル名から自動抽出

```bash
python scripts/upload_audio.py "2025-01-15_CA001_client-call-001.m4a"
```

#### 方法B: 手動で情報を指定

```bash
python scripts/upload_audio.py audio.m4a \
  --ca-id CA001 \
  --date 2025-01-15 \
  --meeting-id client-call-001
```

#### 書き起こしファイルと紐付け

```bash
python scripts/link_transcript.py \
  2025-01-15 \
  CA001 \
  client-call-001 \
  transcript.txt
```

#### フィードバック生成とSlack通知

```bash
python scripts/run_audio_feedback.py
```

**Slack通知について:**
- フィードバック生成後、自動的にSlackに通知が送信されます
- デフォルトチャンネル: `#dk_ca_ops`
- 別のチャンネルに送信したい場合: `--slack-channel "#チャンネル名"` を指定
- Slack通知を無効化したい場合: `--no-slack` オプションを指定

**例:**
```bash
# 別チャンネルに送信
python scripts/run_audio_feedback.py --slack-channel "#general"

# Slack通知なしで実行
python scripts/run_audio_feedback.py --no-slack
```

## 対応形式

### 音声ファイル形式
- `.m4a` (iOS録音、Zoom録音) - 推奨
- `.mp3` (一般的な音声形式)
- `.wav` (高品質音声)
- `.webm` (ブラウザ録音)
- `.mp4` (動画形式の音声)

### 書き起こしファイル形式
- `.txt` (UTF-8エンコーディング)
- 既存システムと同じ形式

## ファイル命名規則

### 音声ファイル

**推奨形式:**
```
{YYYY-MM-DD}_{CA_ID}_{会議識別子}.{拡張子}
```

**例:**
- `2025-01-15_CA001_client-call-001.m4a`
- `2025-01-15_CA002_weekly-mtg.mp3`

### 書き起こしファイル

書き起こしファイルは自動的に同じ名前で保存されます（拡張子のみ`.txt`に変更）。

## ステータス管理

音声ファイルは以下のステータスを持ちます：

- `pending`: 書き起こし待ち（アップロード直後）
- `transcript_ready`: 書き起こしファイル準備済み（紐付け後）
- `processed`: フィードバック生成完了
- `failed`: 処理失敗

## トラブルシューティング

### ファイルが見つからない

```bash
# 音声ファイルの一覧を確認
ls -la data/audio/pending/
```

### 書き起こしファイルを再紐付けしたい

既存の紐付けを上書きする場合は、再度 `link_transcript.py` を実行してください。

### メタデータを確認したい

```bash
cat data/audio/audio_metadata.json
```

## 既存システムとの互換性

このシステムは既存のフィードバックシステムと完全に互換性があります：

- 書き起こしファイルは `data/transcripts/pending/` にも自動的に配置されます
- 既存の `scripts/run_feedback.py` も引き続き使用可能です
- フィードバック形式は既存システムと同じです

## Slack通知の設定

### 環境変数の設定

Slack通知を有効にするには、以下の環境変数を設定してください：

```bash
# 方法1: Slack Bot Tokenを使用（推奨、チャンネル指定可能）
export SLACK_BOT_TOKEN="xoxb-your-slack-bot-token"
export SLACK_DEFAULT_CHANNEL="#dk_ca_ops"  # オプション、デフォルト値が使用される

# 方法2: Slack Webhook URLを使用（シンプル、チャンネル指定不可）
export SLACK_WEBHOOK_URL="https://hooks.slack.com/services/YOUR/WEBHOOK/URL"
```

`.env`ファイルに設定することもできます：

```env
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token
SLACK_DEFAULT_CHANNEL=#dk_ca_ops
# または
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

### Slack Bot Tokenの取得方法

1. [Slack API](https://api.slack.com/apps)にアクセス
2. 新しいアプリを作成
3. 「OAuth & Permissions」で以下のスコープを追加:
   - `chat:write`
   - `chat:write.public`
4. Bot Token（`xoxb-`で始まる）をコピー
5. Botをワークスペースにインストール
6. 送信先チャンネルにBotを追加（`#dk_ca_ops`など）

### 通知内容

フィードバック通知には以下の情報が含まれます：
- 日付・CA情報
- 総合評価とスコア
- 良かった点
- 改善点
- 各項目評価（PSS/ADS）
- 具体的な改善アドバイス
- 次回に向けた目標

## 今後の拡張

- Notta APIとの自動連携（将来実装予定）
- Zoom自動書き起こし取得（将来実装予定）
- Web UIでのアップロード・管理（将来実装予定）

