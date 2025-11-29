# 音声ファイル自動処理機能 実装提案

## 現状

現在は以下の手順で手動実行が必要です：
1. `scripts/upload_audio.py` で音声ファイルをアップロード
2. Zoom/Nottaで書き起こしを実施
3. `scripts/link_transcript.py` で書き起こしファイルを紐付け
4. `scripts/run_audio_feedback.py` でフィードバック生成

## 提案

### 方法1: フォルダ監視による自動処理（推奨）

`data/audio/pending/` フォルダに音声ファイルを置くだけで、自動的に処理を開始します。

**機能:**
1. **音声ファイル自動検出**: `data/audio/pending/` に新しいファイルが追加されたら自動登録
2. **書き起こしファイル自動検出**: `data/audio/transcripts/pending/` に書き起こしファイルが追加されたら自動紐付け
3. **自動フィードバック生成**: 紐付け完了したファイルは自動的にフィードバック生成

**実装方法:**
- `watchdog` ライブラリでフォルダを監視
- 新しいファイルを検出したら自動的に処理

### 方法2: 定期実行スクリプト（シンプル）

定期的に（例：5分ごと）フォルダをチェックして、新しいファイルを処理します。

**機能:**
- 定期的に `data/audio/pending/` をスキャン
- 未登録の音声ファイルを自動登録
- 書き起こしファイルも自動検出・紐付け
- フィードバック生成も自動実行

**実装方法:**
- Cron やスケジューラーで定期実行
- シンプルで確実

## 推奨実装

**方法1（フォルダ監視）+ 方法2（定期実行）のハイブリッド**

1. **定期実行スクリプト**: 5分ごとにチェック（確実性重視）
2. **フォルダ監視サービス**: リアルタイム処理（オプション）

## 実装内容

1. **自動音声ファイル登録スクリプト** (`scripts/auto_import_audio.py`)
   - `data/audio/pending/` をスキャン
   - 未登録のファイルを自動登録
   - ファイル名から情報を自動抽出

2. **自動書き起こし紐付けスクリプト** (`scripts/auto_link_transcripts.py`)
   - `data/audio/transcripts/pending/` をスキャン
   - 対応する音声ファイルを検索して自動紐付け

3. **統合自動処理スクリプト** (`scripts/auto_process_audio.py`)
   - 上記2つを実行
   - フィードバック生成も自動実行
   - 定期実行用

4. **フォルダ監視サービス** (`scripts/watch_audio_folder.py`) - オプション
   - `watchdog` を使用
   - リアルタイムで新しいファイルを検出

## 使用方法

### 自動処理を有効にする

```bash
# 定期実行を設定（5分ごと）
*/5 * * * * cd /Users/ikeobook15/Downloads/job-scout-agent && python3 scripts/auto_process_audio.py
```

### 手動で実行

```bash
# 一度だけ実行（テスト用）
python3 scripts/auto_process_audio.py
```

## ワークフロー

```
1. 音声ファイルを data/audio/pending/ にコピー
   ↓
2. 自動検出・登録（定期実行またはリアルタイム）
   ↓
3. Zoom/Nottaで書き起こしを実施
   ↓
4. 書き起こしファイルを data/audio/transcripts/pending/ に配置
   ↓
5. 自動紐付け・フィードバック生成
   ↓
6. Slack通知
```

承認いただけましたら、実装に進みます。

