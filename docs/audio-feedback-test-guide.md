# 音声フィードバックシステム - Slack連携テストガイド

## テスト手順

### 1. 音声ファイルの準備

音声ファイルはどこにあっても構いません。以下のいずれかの方法でアップロードできます。

#### 音声ファイルの命名規則（推奨）

ファイル名を以下の形式にすると、自動的に情報が抽出されます：

```
{YYYY-MM-DD}_{CA_ID}_{会議識別子}.{拡張子}
```

**例:**
- `2025-01-15_CA001_client-call-001.m4a`
- `2025-12-01_CA002_weekly-mtg.mp3`

### 2. 音声ファイルのアップロード

音声ファイルがどこにあっても、以下のコマンドでアップロードできます：

```bash
# 方法A: ファイル名から自動抽出（推奨）
python3 scripts/upload_audio.py "/path/to/your/audio/2025-12-01_CA001_test-call.m4a"

# 方法B: 手動で情報を指定
python3 scripts/upload_audio.py "/path/to/your/audio/audio.m4a" \
  --ca-id CA001 \
  --date 2025-12-01 \
  --meeting-id test-call
```

**アップロード先:** 自動的に `data/audio/pending/` に保存されます

### 3. 書き起こしファイルの準備と紐付け

ZoomやNottaで書き起こしを実施した後、書き起こしファイル（.txt）を紐付けます：

```bash
python3 scripts/link_transcript.py \
  2025-12-01 \
  CA001 \
  test-call \
  /path/to/transcript.txt
```

### 4. フィードバック生成とSlack通知テスト

```bash
python3 scripts/run_audio_feedback.py
```

これで：
1. フィードバックが生成されます
2. 自動的に`#dk_ca_ops`チャンネルにSlack通知が送信されます

### 5. Slack通知の確認

`#dk_ca_ops`チャンネルを確認して、フィードバックが送信されているか確認してください。

## 簡単なテスト手順（サンプルデータ使用）

テスト用のサンプルデータを使用する場合：

1. **既存のサンプル書き起こしファイルを使用**
   ```bash
   # サンプルファイルの確認
   ls data/sample/feedback/transcripts/
   ```

2. **音声ファイルなしでテストする場合**
   
   既存の書き起こしファイルを直接処理できます：
   ```bash
   # 書き起こしファイルをpendingディレクトリに配置
   cp data/sample/feedback/transcripts/*.txt data/transcripts/pending/
   
   # フィードバック生成とSlack通知
   python3 scripts/run_audio_feedback.py
   ```

## トラブルシューティング

### 音声ファイルが見つからない

```bash
# ファイルのパスを確認
ls -la /path/to/your/audio/file.m4a

# 絶対パスを使用
python3 scripts/upload_audio.py "/Users/yourname/Downloads/audio.m4a"
```

### Slack通知が送信されない

1. **環境変数の確認**
   ```bash
   echo $SLACK_WEBHOOK_URL
   ```

2. **テスト通知を送信**
   ```bash
   python3 scripts/test_slack_notification.py
   ```

3. **Slack通知を無効化して実行**
   ```bash
   python3 scripts/run_audio_feedback.py --no-slack
   ```

### 書き起こしファイルが見つからない

```bash
# pendingディレクトリを確認
ls -la data/transcripts/pending/

# 音声ファイルのステータスを確認
cat data/audio/audio_metadata.json | grep -A 5 "test-call"
```

## 対応音声形式

- `.m4a` (iOS録音、Zoom録音) - 推奨
- `.mp3` (一般的な音声形式)
- `.wav` (高品質音声)
- `.webm` (ブラウザ録音)
- `.mp4` (動画形式の音声)

## 注意事項

- 音声ファイルサイズ: 最大500MB
- 通話時間: 最大2時間まで推奨
- 個人情報が含まれる可能性があるため、適切に管理してください

