# 音声ファイル自動処理機能 使用ガイド

## 🎯 概要

**音声ファイルをフォルダに置くだけで、自動的にインポート・分析が始まります！**

手動でスクリプトを実行する必要はありません。フォルダにファイルを配置するだけで、すべて自動処理されます。

## 📁 フォルダ構造

```
data/
└── audio/
    ├── pending/                    # 📂 ここに音声ファイルを配置！
    │   └── 2025-11-28_FUKUYAMA_test-001.m4a
    │
    ├── transcripts/
    │   └── pending/                # 📂 ここに書き起こしファイルを配置！
    │       └── 2025-11-28_FUKUYAMA_test-001.txt
    │
    ├── processed/                  # 処理完了した音声ファイル（自動移動）
    ├── failed/                     # 処理失敗したファイル（自動移動）
    └── audio_metadata.json         # メタデータ（自動管理）
```

## 🚀 使い方

### ステップ1: 音声ファイルを配置

ファイル名を以下の形式にして、`data/audio/pending/` フォルダに**コピーまたは移動**：

```
{YYYY-MM-DD}_{CA_ID}_{会議識別子}.{拡張子}
```

**例:**
```bash
# ファイルをコピー
cp "通話録音.m4a" data/audio/pending/2025-11-28_FUKUYAMA_test-001.m4a

# または直接移動
mv "通話録音.m4a" data/audio/pending/2025-11-28_FUKUYAMA_test-001.m4a
```

**ファイル名の例:**
- ✅ `2025-11-28_FUKUYAMA_test-001.m4a`
- ✅ `2025-11-28_CA001_client-call-001.m4a`
- ❌ `通話録音.m4a` （形式が正しくないためスキップされます）

### ステップ2: 自動処理を実行

```bash
# 一度だけ実行（手動）
python3 scripts/auto_process_audio.py

# AIを使用する場合
python3 scripts/auto_process_audio.py --use-ai
```

**自動処理の内容:**
1. ✅ `data/audio/pending/` 内の新しい音声ファイルを自動登録
2. ✅ `data/audio/transcripts/pending/` 内の書き起こしファイルを自動検出・紐付け
3. ✅ 紐付け完了したファイルを自動的にフィードバック生成
4. ✅ Slack通知も自動送信

### ステップ3: 書き起こしファイルを配置（Zoom/Nottaで書き起こし後）

ZoomやNottaで書き起こしを実施後、書き起こしファイル（.txt）を以下のフォルダに配置：

```bash
# 書き起こしファイルを配置
cp "transcript.txt" data/audio/transcripts/pending/2025-11-28_FUKUYAMA_test-001.txt
```

**重要:** ファイル名は音声ファイルと同じ形式にしてください（拡張子のみ`.txt`）。

### ステップ4: 再度自動処理を実行

```bash
python3 scripts/auto_process_audio.py
```

これで、書き起こしファイルが自動的に紐付けられ、フィードバックが生成されます！

## ⏰ 定期実行の設定（オプション）

定期的に自動チェックするように設定できます。これで、フォルダにファイルを置くだけで、すべて自動処理されます。

### Cronを使う方法（推奨）

```bash
# crontab -e
# 5分ごとに実行
*/5 * * * * cd /Users/ikeobook15/Downloads/job-scout-agent && /usr/bin/python3 scripts/auto_process_audio.py >> logs/auto_process.log 2>&1
```

これで、5分ごとに自動的にチェックし、新しいファイルがあれば自動処理されます。

### 手動でテスト

```bash
# 一度だけ実行してテスト
python3 scripts/auto_process_audio.py

# ログを確認
tail -f logs/auto_process.log
```

## 📋 完全なワークフロー例

### 例: 音声ファイルからフィードバック生成まで

```bash
# 1. 音声ファイルを配置
cp "通話録音.m4a" data/audio/pending/2025-11-28_FUKUYAMA_test-001.m4a

# 2. 自動処理を実行（音声ファイルを登録）
python3 scripts/auto_process_audio.py
# → 出力: "✅ 音声ファイルを登録: 2025-11-28_FUKUYAMA_test-001.m4a"

# 3. Zoom/Nottaで書き起こしを実施（手動）
# → transcript.txt をダウンロード

# 4. 書き起こしファイルを配置
cp "transcript.txt" data/audio/transcripts/pending/2025-11-28_FUKUYAMA_test-001.txt

# 5. 再度自動処理を実行
python3 scripts/auto_process_audio.py
# → 出力: 
#    "✅ 書き起こしを紐付け: 2025-11-28_FUKUYAMA_test-001.txt"
#    "✅ フィードバック生成完了: 1件"
#    "✅ Slack通知完了: 1件"
```

## 🔧 オプション

### AIを使用する場合

```bash
python3 scripts/auto_process_audio.py --use-ai
```

### Slack通知を無効化

```bash
python3 scripts/auto_process_audio.py --no-slack
```

### フィードバック生成をスキップ（登録・紐付けのみ）

```bash
python3 scripts/auto_process_audio.py --no-feedback
```

### 別のチャンネルに送信

```bash
python3 scripts/auto_process_audio.py --slack-channel "#general"
```

## 📊 処理状況の確認

```bash
# 書き起こし待ちのファイル数を確認
python3 -c "from src.feedback import AudioManager; am = AudioManager(); print(f'書き起こし待ち: {len(am.list_pending_audio())}件')"

# 処理準備済みのファイル数を確認
python3 -c "from src.feedback import AudioFeedbackEngine; engine = AudioFeedbackEngine(); print(f'処理準備済み: {engine.get_ready_count()}件')"
```

## ⚠️ 注意事項

1. **ファイル名の形式**: ファイル名は必ず `{日付}_{CA_ID}_{会議ID}.{拡張子}` の形式にしてください
2. **重複チェック**: 同じファイル名の場合は、既に登録済みとしてスキップされます
3. **書き起こしファイル**: 書き起こしファイルも音声ファイルと同じ命名規則にしてください（拡張子のみ`.txt`）
4. **対応形式**: `.m4a`, `.mp3`, `.wav`, `.webm`, `.mp4` に対応

## 🔍 トラブルシューティング

### ファイルが登録されない

1. ファイル名の形式が正しいか確認
2. `data/audio/pending/` フォルダにファイルが配置されているか確認
3. ログを確認: `tail -f logs/auto_process.log`

### 書き起こしが紐付けられない

1. 書き起こしファイル名が音声ファイルと同じ形式か確認（拡張子のみ`.txt`）
2. `data/audio/transcripts/pending/` フォルダにファイルが配置されているか確認
3. 日付、CA ID、会議IDが一致しているか確認

### 処理が実行されない

1. 定期実行が設定されているか確認: `crontab -l`
2. ログファイルを確認: `tail -f logs/auto_process.log`
3. 手動で実行してテスト: `python3 scripts/auto_process_audio.py`

---

これで、フォルダにファイルを置くだけで、すべて自動処理されます！🎉

