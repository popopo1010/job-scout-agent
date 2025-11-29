#!/bin/bash
# 事業戦略チェックの自動実行設定スクリプト（macOS用）

set -e

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 事業戦略チェックの自動実行設定を開始します...${NC}\n"

# プロジェクトのルートディレクトリ
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/check_strategy_updates.py"

# LaunchAgentディレクトリ
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/com.jobscout.strategy-check.plist"

# LaunchAgentディレクトリを作成
mkdir -p "$LAUNCH_AGENTS_DIR"

echo -e "${GREEN}📝 LaunchAgent設定ファイルを作成中...${NC}"

# Pythonのパスを取得
PYTHON_PATH=$(which python3)
if [ -z "$PYTHON_PATH" ]; then
    echo -e "${RED}❌ python3が見つかりません${NC}"
    exit 1
fi

# plistファイルを作成
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobscout.strategy-check</string>
    <key>ProgramArguments</key>
    <array>
        <string>$PYTHON_PATH</string>
        <string>$SCRIPT_PATH</string>
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
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>$PROJECT_DIR/logs/strategy-check.log</string>
    <key>StandardErrorPath</key>
    <string>$PROJECT_DIR/logs/strategy-check-error.log</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
</dict>
</plist>
EOF

echo -e "${GREEN}✅ 設定ファイルを作成しました: $PLIST_FILE${NC}"

# ログディレクトリを作成
mkdir -p "$PROJECT_DIR/logs"

# LaunchAgentを読み込む
echo -e "${BLUE}🔄 LaunchAgentを読み込み中...${NC}"

# 既に読み込まれている場合はアンロード
if launchctl list | grep -q "com.jobscout.strategy-check"; then
    echo -e "${YELLOW}⚠️  既存のLaunchAgentをアンロードします...${NC}"
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# 新しいLaunchAgentを読み込む
launchctl load "$PLIST_FILE"

if [ $? -eq 0 ]; then
    echo -e "${GREEN}✅ 自動実行が有効になりました！${NC}"
    echo -e "${BLUE}ℹ️  毎週月曜日の9時に事業戦略チェックが実行されます${NC}"
else
    echo -e "${RED}❌ 自動実行の設定に失敗しました${NC}"
    exit 1
fi

echo ""
echo -e "${YELLOW}💡 自動実行を停止する場合:${NC}"
echo -e "   launchctl unload $PLIST_FILE"
echo ""
echo -e "${YELLOW}💡 自動実行を再開する場合:${NC}"
echo -e "   launchctl load $PLIST_FILE"
echo ""
echo -e "${YELLOW}💡 手動で実行する場合:${NC}"
echo -e "   python $SCRIPT_PATH"

