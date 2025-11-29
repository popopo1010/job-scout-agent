#!/bin/bash
# Obsidian自動同期のセットアップスクリプト（macOS用）

set -e

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}🚀 Obsidian自動同期のセットアップを開始します...${NC}\n"

# プロジェクトのルートディレクトリ
PROJECT_DIR="$(cd "$(dirname "$0")/.." && pwd)"
SCRIPT_PATH="$PROJECT_DIR/scripts/sync_obsidian.sh"

# LaunchAgentディレクトリ
LAUNCH_AGENTS_DIR="$HOME/Library/LaunchAgents"
PLIST_FILE="$LAUNCH_AGENTS_DIR/com.jobscout.obsidian-sync.plist"

# LaunchAgentディレクトリを作成
mkdir -p "$LAUNCH_AGENTS_DIR"

echo -e "${GREEN}📝 LaunchAgent設定ファイルを作成中...${NC}"

# plistファイルを作成
cat > "$PLIST_FILE" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.jobscout.obsidian-sync</string>
    <key>ProgramArguments</key>
    <array>
        <string>/bin/bash</string>
        <string>$SCRIPT_PATH</string>
    </array>
    <key>StartInterval</key>
    <integer>3600</integer>
    <key>RunAtLoad</key>
    <false/>
    <key>StandardOutPath</key>
    <string>/tmp/obsidian-sync.log</string>
    <key>StandardErrorPath</key>
    <string>/tmp/obsidian-sync-error.log</string>
    <key>WorkingDirectory</key>
    <string>$PROJECT_DIR</string>
</dict>
</plist>
EOF

echo -e "${GREEN}✅ 設定ファイルを作成しました: $PLIST_FILE${NC}"

# LaunchAgentを読み込む
echo -e "${BLUE}🔄 LaunchAgentを読み込み中...${NC}"

# 既に読み込まれている場合はアンロード
if launchctl list | grep -q "com.jobscout.obsidian-sync"; then
    echo -e "${YELLOW}⚠️  既存のLaunchAgentをアンロードします...${NC}"
    launchctl unload "$PLIST_FILE" 2>/dev/null || true
fi

# 新しいLaunchAgentを読み込む
launchctl load "$PLIST_FILE"

echo -e "${GREEN}✅ LaunchAgentを読み込みました${NC}"

# 確認
echo -e "\n${BLUE}📊 設定確認:${NC}"
if launchctl list | grep -q "com.jobscout.obsidian-sync"; then
    echo -e "${GREEN}✅ 自動同期が有効になりました！${NC}"
    echo -e "${BLUE}ℹ️  1時間ごとに自動同期されます${NC}"
    echo -e "${BLUE}ℹ️  ログ: /tmp/obsidian-sync.log${NC}"
else
    echo -e "${RED}❌ 自動同期の設定に失敗しました${NC}"
    exit 1
fi

echo -e "\n${GREEN}🎉 セットアップ完了！${NC}"
echo -e "\n${YELLOW}💡 手動で同期する場合:${NC}"
echo -e "   $SCRIPT_PATH"
echo -e "\n${YELLOW}💡 自動同期を停止する場合:${NC}"
echo -e "   launchctl unload $PLIST_FILE"
echo -e "\n${YELLOW}💡 自動同期を再開する場合:${NC}"
echo -e "   launchctl load $PLIST_FILE"

