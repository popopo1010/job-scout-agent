# 音声データフィードバックシステム クイックスタート

## 最小限の使用例

### ステップ1: 音声ファイルをアップロード

```bash
python scripts/upload_audio.py "2025-01-15_CA001_call-001.m4a"
```

### ステップ2: ZoomやNottaで書き起こしを実施

ZoomやNottaで書き起こしファイル（.txt）をダウンロードします。

### ステップ3: 書き起こしファイルを紐付け

```bash
python scripts/link_transcript.py \
  2025-01-15 \
  CA001 \
  call-001 \
  transcript.txt
```

### ステップ4: フィードバック生成

```bash
python scripts/run_audio_feedback.py
```

## 1行で確認するステータス

```bash
# 書き起こし待ちのファイル数を確認
python -c "from src.feedback import AudioManager; am = AudioManager(); print(f'書き起こし待ち: {len(am.list_pending_audio())}件')"
```

## よくある使用パターン

### パターン1: Zoomの書き起こしを使う

```bash
# 1. 音声ファイルをアップロード
python scripts/upload_audio.py zoom_recording.m4a --ca-id CA001 --date 2025-01-15 --meeting-id zoom-call

# 2. Zoomで書き起こしを実施（手動）

# 3. Zoomの書き起こしファイルを紐付け
python scripts/link_transcript.py 2025-01-15 CA001 zoom-call zoom_transcript.txt

# 4. フィードバック生成
python scripts/run_audio_feedback.py
```

### パターン2: Nottaの書き起こしを使う

```bash
# 1. 音声ファイルをアップロード
python scripts/upload_audio.py notta_recording.m4a --ca-id CA002 --date 2025-01-15 --meeting-id client-call

# 2. Nottaで書き起こしを実施（手動）

# 3. Nottaの書き起こしファイルを紐付け
python scripts/link_transcript.py 2025-01-15 CA002 client-call notta_transcript.txt

# 4. フィードバック生成
python scripts/run_audio_feedback.py --use-ai
```

## ファイル命名のベストプラクティス

### 良い例

```
2025-01-15_CA001_client-call-001.m4a
2025-01-15_CA002_weekly-mtg.mp3
```

### 悪い例

```
recording.m4a                    # 日付やCA IDが不明
CA001_call.m4a                   # 日付が不明
2025-01-15_call.m4a             # CA IDが不明
```

## トラブルシューティング

### エラー: "音声ファイルが見つかりません"

→ 書き起こしファイルを紐付ける前に、音声ファイルをアップロードしてください。

### エラー: "ファイル名から情報を抽出できませんでした"

→ `--ca-id`, `--date`, `--meeting-id` オプションを使用してください。

### エラー: "既に存在します"

→ `--force` オプションを使用して上書きできます（注意して使用してください）。

