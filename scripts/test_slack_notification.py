#!/usr/bin/env python3
"""
Slack通知のテストスクリプト

環境変数の設定を確認し、テストメッセージを送信します。
"""

import sys
import os
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.common.slack_notifier import SlackNotifier


def main():
    """テストメッセージを送信"""
    print("=" * 70)
    print("Slack通知テスト")
    print("=" * 70)
    print()

    # 環境変数の確認
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    bot_token = os.getenv("SLACK_BOT_TOKEN")
    default_channel = os.getenv("SLACK_DEFAULT_CHANNEL", "#dk_ca_ops")

    print("📋 環境変数の設定状況:")
    if webhook_url:
        # URLの一部だけ表示（セキュリティのため）
        masked_url = webhook_url[:50] + "..." if len(webhook_url) > 50 else webhook_url
        print(f"   ✅ SLACK_WEBHOOK_URL: {masked_url}")
    else:
        print("   ❌ SLACK_WEBHOOK_URL: 未設定")

    if bot_token:
        masked_token = bot_token[:20] + "..." if len(bot_token) > 20 else bot_token
        print(f"   ✅ SLACK_BOT_TOKEN: {masked_token}")
    else:
        print("   ❌ SLACK_BOT_TOKEN: 未設定")

    print(f"   channel: {default_channel}")
    print()

    # SlackNotifierを初期化
    notifier = SlackNotifier(default_channel=default_channel)

    # テストメッセージを送信
    test_message = """*【テスト通知】*

音声フィードバックシステムのSlack通知テストです。

✅ 設定が正しく動作している場合、このメッセージが `#dk_ca_ops` チャンネルに表示されます。

フィードバック生成時には、このようにフィードバック内容が自動的に送信されます。
"""

    print("▶ テストメッセージを送信中...")
    success = notifier.send_message(test_message, channel=default_channel)

    print()
    if success:
        print("✅ テストメッセージの送信に成功しました！")
        print(f"   Slackの {default_channel} チャンネルを確認してください。")
    else:
        print("❌ テストメッセージの送信に失敗しました。")
        print()
        print("💡 確認事項:")
        print("   1. SLACK_WEBHOOK_URL または SLACK_BOT_TOKEN が正しく設定されているか")
        print("   2. 環境変数が現在のシェルに読み込まれているか（exportコマンドを実行したか）")
        print("   3. .envファイルを使用している場合、python-dotenvがインストールされているか")
        print()
        print("設定方法:")
        print("   export SLACK_WEBHOOK_URL='https://hooks.slack.com/services/YOUR/WEBHOOK/URL'")
        print("   または")
        print("   export SLACK_BOT_TOKEN='xoxb-your-slack-bot-token'")


if __name__ == "__main__":
    main()

