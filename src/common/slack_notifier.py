"""Slack通知ユーティリティ"""

from __future__ import annotations

import os
from typing import Optional

import httpx


class SlackNotifier:
    """Slack通知を送信するクラス"""

    def __init__(
        self,
        webhook_url: Optional[str] = None,
        bot_token: Optional[str] = None,
        default_channel: str = "#dk_ca_ops",
    ):
        """
        Args:
            webhook_url: Slack Webhook URL（優先度: 低）
            bot_token: Slack Bot Token（優先度: 高、チャンネル指定可能）
            default_channel: デフォルトチャンネル（Bot Token使用時）
        """
        self.webhook_url = webhook_url or os.getenv("SLACK_WEBHOOK_URL")
        self.bot_token = bot_token or os.getenv("SLACK_BOT_TOKEN")
        self.default_channel = default_channel or os.getenv("SLACK_DEFAULT_CHANNEL", "#dk_ca_ops")

    def send_message(
        self,
        message: str,
        channel: Optional[str] = None,
        blocks: Optional[list] = None,
    ) -> bool:
        """
        Slackにメッセージを送信

        Args:
            message: 送信するメッセージ
            channel: チャンネル名（Bot Token使用時のみ有効）
            blocks: Slack Block Kit形式のブロック（Bot Token使用時のみ有効）

        Returns:
            送信成功した場合True
        """
        # Bot Tokenが設定されている場合は、API経由で送信（チャンネル指定可能）
        if self.bot_token:
            return self._send_via_api(message, channel or self.default_channel, blocks)

        # Webhook URLが設定されている場合は、Webhook経由で送信
        if self.webhook_url:
            return self._send_via_webhook(message)

        print("⚠️  Slack通知が設定されていません（SLACK_BOT_TOKEN または SLACK_WEBHOOK_URL を設定してください）")
        return False

    def _send_via_api(
        self,
        message: str,
        channel: str,
        blocks: Optional[list] = None,
    ) -> bool:
        """Slack APIを使用してメッセージを送信"""
        try:
            url = "https://slack.com/api/chat.postMessage"
            headers = {
                "Authorization": f"Bearer {self.bot_token}",
                "Content-Type": "application/json",
            }
            payload = {
                "channel": channel,
                "text": message,
            }
            if blocks:
                payload["blocks"] = blocks

            response = httpx.post(url, headers=headers, json=payload, timeout=10.0)
            response.raise_for_status()

            result = response.json()
            if result.get("ok"):
                print(f"✅ Slack通知を送信しました: {channel}")
                return True
            else:
                error = result.get("error", "unknown error")
                print(f"❌ Slack通知の送信に失敗しました: {error}")
                return False

        except Exception as e:
            print(f"❌ Slack通知の送信でエラーが発生しました: {e}")
            return False

    def _send_via_webhook(self, message: str) -> bool:
        """Slack Webhookを使用してメッセージを送信"""
        try:
            response = httpx.post(
                self.webhook_url,
                json={"text": message},
                timeout=10.0,
            )
            response.raise_for_status()
            print("✅ Slack通知を送信しました（Webhook経由）")
            return True
        except Exception as e:
            print(f"❌ Slack通知の送信でエラーが発生しました: {e}")
            return False

