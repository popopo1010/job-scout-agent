#!/bin/bash
# Obsidianノートの自動同期スクリプト
# Gitを使って自動的にコミット・プッシュします

set -e

# プロジェクトのルートディレクトリに移動
cd "$(dirname "$0")/.."

# 色の定義
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}🔄 Obsidianノートの同期を開始します...${NC}"

# Gitの状態を確認
if ! git rev-parse --git-dir > /dev/null 2>&1; then
    echo -e "${RED}❌ エラー: Gitリポジトリではありません${NC}"
    exit 1
fi

# 変更があるか確認
if git diff --quiet && git diff --cached --quiet; then
    echo -e "${YELLOW}ℹ️  変更がありません${NC}"
    exit 0
fi

# 変更されたファイルを表示
echo -e "${GREEN}📝 変更されたファイル:${NC}"
git status --short

# すべての変更をステージング
git add -A

# コミットメッセージを生成
TIMESTAMP=$(date '+%Y-%m-%d %H:%M:%S')
COMMIT_MSG="Auto-sync Obsidian notes: $TIMESTAMP"

# コミット
if git commit -m "$COMMIT_MSG"; then
    echo -e "${GREEN}✅ コミット完了: $COMMIT_MSG${NC}"
else
    echo -e "${YELLOW}⚠️  コミットに失敗しました（変更がない可能性があります）${NC}"
    exit 0
fi

# プッシュ
if git push; then
    echo -e "${GREEN}✅ プッシュ完了${NC}"
    echo -e "${GREEN}🎉 同期が完了しました！${NC}"
else
    echo -e "${RED}❌ プッシュに失敗しました${NC}"
    echo -e "${YELLOW}💡 手動でプッシュしてください: git push${NC}"
    exit 1
fi

