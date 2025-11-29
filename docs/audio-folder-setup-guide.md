# 音声ファイル格納フォルダ セットアップガイド

## 📍 フォルダの場所

プロジェクトのルートディレクトリに以下のフォルダがあります：

```
/Users/ikeobook15/Downloads/job-scout-agent/
└── data/
    └── audio/
        ├── pending/                    # 📂 ここに音声ファイルを入れる！
        └── transcripts/
            └── pending/                # 📂 ここに書き起こしファイルを入れる！
```

### 絶対パス（フルパス）

- **音声ファイル用**: `/Users/ikeobook15/Downloads/job-scout-agent/data/audio/pending/`
- **書き起こしファイル用**: `/Users/ikeobook15/Downloads/job-scout-agent/data/audio/transcripts/pending/`

## 📂 フォルダの確認方法

ターミナルで以下のコマンドを実行すると、フォルダの存在を確認できます：

```bash
# プロジェクトディレクトリに移動
cd /Users/ikeobook15/Downloads/job-scout-agent

# フォルダを確認
ls -la data/audio/pending/
ls -la data/audio/transcripts/pending/
```

## 🚀 ファイルの入れ方

### 方法1: Finder（macOS）でドラッグ&ドロップ（最も簡単）

1. **Finderを開く**
2. **フォルダに移動**:
   - メニューバーの「移動」→「フォルダへ移動...」
   - または `Cmd + Shift + G` を押す
   - 以下のパスを入力:
     ```
     /Users/ikeobook15/Downloads/job-scout-agent/data/audio/pending
     ```
3. **ファイルをドラッグ&ドロップ**

**動画で説明すると：**
1. Finderで音声ファイルを選択
2. `Cmd + Option + V` で移動、または `Cmd + C` でコピー
3. フォルダを開いて `Cmd + V` で貼り付け

### 方法2: ターミナルでコピー

```bash
# 音声ファイルをコピー
cp "/path/to/your/audio.m4a" /Users/ikeobook15/Downloads/job-scout-agent/data/audio/pending/2025-11-28_FUKUYAMA_test-001.m4a

# 書き起こしファイルをコピー
cp "/path/to/your/transcript.txt" /Users/ikeobook15/Downloads/job-scout-agent/data/audio/transcripts/pending/2025-11-28_FUKUYAMA_test-001.txt
```

### 方法3: ターミナルで移動

```bash
# 音声ファイルを移動
mv "/path/to/your/audio.m4a" /Users/ikeobook15/Downloads/job-scout-agent/data/audio/pending/2025-11-28_FUKUYAMA_test-001.m4a

# 書き起こしファイルを移動
mv "/path/to/your/transcript.txt" /Users/ikeobook15/Downloads/job-scout-agent/data/audio/transcripts/pending/2025-11-28_FUKUYAMA_test-001.txt
```

## 📝 ファイル名の形式（重要！）

**必ず以下の形式にしてください：**

```
{YYYY-MM-DD}_{CA_ID}_{会議識別子}.{拡張子}
```

### 例（正しいファイル名）

- ✅ `2025-11-28_FUKUYAMA_test-001.m4a`
- ✅ `2025-11-28_CA001_client-call-001.m4a`
- ✅ `2025-11-28_CA002_weekly-mtg.mp3`

### 例（間違ったファイル名）

- ❌ `通話録音.m4a` （日付やCA IDがない）
- ❌ `2025-11-28.m4a` （CA IDや会議IDがない）
- ❌ `FUKUYAMA_test.m4a` （日付がない）

## 🎯 実際の手順例

### 例1: Zoomの録音ファイルを入れる場合

1. **Zoomの録音ファイルを探す**
   - 通常は `~/Downloads/` や `~/Documents/Zoom/` にある

2. **ファイル名を変更**
   - 例: `zoom_recording.m4a` → `2025-11-28_FUKUYAMA_test-001.m4a`

3. **ファイルをコピーまたは移動**
   ```bash
   # Finderでドラッグ&ドロップ、または
   cp ~/Downloads/zoom_recording.m4a ~/Downloads/job-scout-agent/data/audio/pending/2025-11-28_FUKUYAMA_test-001.m4a
   ```

### 例2: 書き起こしファイルを入れる場合

1. **ZoomやNottaで書き起こしを実施**

2. **書き起こしファイルをダウンロード**

3. **ファイル名を音声ファイルと同じ形式に変更**
   - 音声: `2025-11-28_FUKUYAMA_test-001.m4a`
   - 書き起こし: `2025-11-28_FUKUYAMA_test-001.txt` ← 拡張子のみ`.txt`

4. **書き起こしフォルダに配置**
   ```bash
   cp ~/Downloads/transcript.txt ~/Downloads/job-scout-agent/data/audio/transcripts/pending/2025-11-28_FUKUYAMA_test-001.txt
   ```

## ⚡ クイックスタート

### 1分で始める

```bash
# プロジェクトディレクトリに移動
cd /Users/ikeobook15/Downloads/job-scout-agent

# 音声ファイルを配置（ファイル名を変更してコピー）
cp "/path/to/your/audio.m4a" data/audio/pending/2025-11-28_FUKUYAMA_test-001.m4a

# 自動処理を実行
python3 scripts/auto_process_audio.py
```

## 🔍 フォルダの確認方法

### 現在のファイルを確認

```bash
# 音声ファイルを確認
ls -lh data/audio/pending/

# 書き起こしファイルを確認
ls -lh data/audio/transcripts/pending/
```

### フォルダをFinderで開く

```bash
# 音声ファイル用フォルダを開く
open data/audio/pending/

# 書き起こしファイル用フォルダを開く
open data/audio/transcripts/pending/
```

## 💡 ヒント

### Finderのサイドバーに追加

1. Finderで `data/audio/pending/` フォルダを開く
2. サイドバーにドラッグ&ドロップ
3. 次回から簡単にアクセスできます

### エイリアス（ショートカット）を作成

```bash
# ショートカットを作成
ln -s /Users/ikeobook15/Downloads/job-scout-agent/data/audio/pending ~/Desktop/音声ファイル
ln -s /Users/ikeobook15/Downloads/job-scout-agent/data/audio/transcripts/pending ~/Desktop/書き起こしファイル
```

これで、デスクトップから直接アクセスできます！

## 📋 チェックリスト

ファイルを入れる前に：

- [ ] ファイル名が正しい形式か確認（`{日付}_{CA_ID}_{会議ID}.{拡張子}`）
- [ ] 対応形式か確認（`.m4a`, `.mp3`, `.wav`, `.webm`, `.mp4`）
- [ ] フォルダのパスが正しいか確認

ファイルを入れた後：

- [ ] `ls -la data/audio/pending/` でファイルが存在するか確認
- [ ] `python3 scripts/auto_process_audio.py` を実行

---

**まとめ**: ファイルを入れる場所は `/Users/ikeobook15/Downloads/job-scout-agent/data/audio/pending/` です！
Finderでドラッグ&ドロップするのが一番簡単です。

