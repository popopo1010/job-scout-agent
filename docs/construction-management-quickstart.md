# 施工管理人材紹介システム クイックスタート

## 最小限の使用例

### ステップ1: 音声ファイルをアップロード

```bash
python scripts/upload_audio_cm.py "2025-01-15_CA001_call-001.m4a"
```

### ステップ2: ZoomやNottaで書き起こしを実施

ZoomやNottaで書き起こしファイル（.txt）をダウンロードします。

### ステップ3: 書き起こしファイルを紐付け

```bash
python scripts/link_transcript_cm.py \
  2025-01-15 \
  CA001 \
  call-001 \
  transcript.txt
```

### ステップ4: フィードバック生成

```bash
python scripts/run_audio_feedback_cm.py
```

## 1行で確認するステータス

```bash
# 書き起こし待ちのファイル数を確認
python -c "from src.feedback import AudioCMManager; am = AudioCMManager(); print(f'書き起こし待ち: {len(am.list_pending_audio())}件')"
```

## よくある使用パターン

### パターン1: Zoomの書き起こしを使う（建築施工管理技士）

```bash
# 1. 音声ファイルをアップロード
python scripts/upload_audio_cm.py zoom_recording.m4a \
  --ca-id CA001 \
  --date 2025-01-15 \
  --meeting-id zoom-call \
  --qualification "1級建築施工管理技士"

# 2. Zoomで書き起こしを実施（手動）

# 3. Zoomの書き起こしファイルを紐付け
python scripts/link_transcript_cm.py 2025-01-15 CA001 zoom-call zoom_transcript.txt

# 4. フィードバック生成
python scripts/run_audio_feedback_cm.py
```

### パターン2: Nottaの書き起こしを使う（土木施工管理技士）

```bash
# 1. 音声ファイルをアップロード
python scripts/upload_audio_cm.py notta_recording.m4a \
  --ca-id CA002 \
  --date 2025-01-15 \
  --meeting-id client-call \
  --qualification "2級土木施工管理技士"

# 2. Nottaで書き起こしを実施（手動）

# 3. Nottaの書き起こしファイルを紐付け
python scripts/link_transcript_cm.py 2025-01-15 CA002 client-call notta_transcript.txt

# 4. フィードバック生成
python scripts/run_audio_feedback_cm.py --use-ai
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

## 対象資格の指定

施工管理技士の場合は、資格情報を指定できます：

### 建築
```bash
python scripts/upload_audio_cm.py audio.m4a --qualification "1級建築施工管理技士"
python scripts/upload_audio_cm.py audio.m4a --qualification "2級建築施工管理技士"
```

### 土木
```bash
python scripts/upload_audio_cm.py audio.m4a --qualification "1級土木施工管理技士"
python scripts/upload_audio_cm.py audio.m4a --qualification "2級土木施工管理技士"
```

### 電気工事
```bash
python scripts/upload_audio_cm.py audio.m4a --qualification "1級電気工事施工管理技士"
python scripts/upload_audio_cm.py audio.m4a --qualification "2級電気工事施工管理技士"
```

### 管工事
```bash
python scripts/upload_audio_cm.py audio.m4a --qualification "1級管工事施工管理技士"
python scripts/upload_audio_cm.py audio.m4a --qualification "2級管工事施工管理技士"
```

### 造園
```bash
python scripts/upload_audio_cm.py audio.m4a --qualification "1級造園施工管理技士"
python scripts/upload_audio_cm.py audio.m4a --qualification "2級造園施工管理技士"
```

### 建設機械
```bash
python scripts/upload_audio_cm.py audio.m4a --qualification "1級建設機械施工技士"
python scripts/upload_audio_cm.py audio.m4a --qualification "2級建設機械施工技士"
```

## トラブルシューティング

### エラー: "音声ファイルが見つかりません"

→ 書き起こしファイルを紐付ける前に、音声ファイルをアップロードしてください。

### エラー: "ファイル名から情報を抽出できませんでした"

→ `--ca-id`, `--date`, `--meeting-id` オプションを使用してください。

### エラー: "既に存在します"

→ `--force` オプションを使用して上書きできます（注意して使用してください）。

---

*最終更新: 2025-01-15*

