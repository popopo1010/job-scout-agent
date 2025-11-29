#!/usr/bin/env python3
"""
週次フィードバックレポート生成・配信スクリプト

過去1週間のフィードバックを集計し、CAごとに個別レポートを生成してSlackに配信します。
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feedback.weekly_report import WeeklyReportGenerator
from src.common.slack_notifier import SlackNotifier


def get_last_week_dates() -> tuple[str, str]:
    """前週の月曜日と日曜日を取得"""
    today = datetime.now()
    # 前週の月曜日を計算
    days_since_monday = (today.weekday() + 1) % 7  # 0=月曜日
    if days_since_monday == 0:
        days_since_monday = 7
    last_monday = today - timedelta(days=days_since_monday + 7)
    last_sunday = last_monday + timedelta(days=6)
    
    return last_monday.strftime("%Y-%m-%d"), last_sunday.strftime("%Y-%m-%d")


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="週次フィードバックレポート生成・配信")
    parser.add_argument(
        "--week-start",
        type=str,
        default=None,
        help="週の開始日（YYYY-MM-DD）。指定しない場合は前週の月曜日",
    )
    parser.add_argument(
        "--week-end",
        type=str,
        default=None,
        help="週の終了日（YYYY-MM-DD）。指定しない場合は前週の日曜日",
    )
    parser.add_argument(
        "--slack-channel",
        type=str,
        default=None,
        help="Slack通知先チャンネル（デフォルト: #dk_ca_ops）",
    )
    parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Slack通知を無効化",
    )
    parser.add_argument(
        "--ca-id",
        type=str,
        default=None,
        help="特定のCAのみレポート生成（指定しない場合は全CA）",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("週次フィードバックレポート生成・配信")
    print("=" * 70)
    print()

    # 期間を決定
    if args.week_start and args.week_end:
        week_start = args.week_start
        week_end = args.week_end
    else:
        week_start, week_end = get_last_week_dates()
    
    print(f"📅 対象期間: {week_start} 〜 {week_end}")
    print()

    # レポート生成器を初期化
    generator = WeeklyReportGenerator()

    # CAマッピングを取得
    ca_mappings = generator.ca_mapping.get_all_mappings()
    
    if not ca_mappings:
        print("⚠️  CA-Slack IDマッピングが見つかりません。")
        print("   config/ca_slack_mapping.yaml または data/sample/analytics/ca_master.csv を確認してください。")
        return
    
    # 対象CAを決定
    target_ca_ids = [args.ca_id] if args.ca_id else list(ca_mappings.keys())

    # 各CAの週次サマリーを生成
    summaries = []
    for ca_id in target_ca_ids:
        summary = generator.generate_weekly_summary(
            ca_id=ca_id,
            week_start=week_start,
            week_end=week_end,
        )
        if summary:
            summaries.append(summary)
            print(f"✅ {summary.ca_name or ca_id}: {summary.feedback_count}件のフィードバック")

    if not summaries:
        print("⚠️  対象期間にフィードバックデータがありません。")
        return

    print()
    print(f"📊 合計: {len(summaries)}名のCA、{sum(summary.feedback_count for summary in summaries)}件のフィードバック")
    print()

    # Slack通知を準備
    if not args.no_slack:
        slack_channel = args.slack_channel or "#dk_ca_ops"
        notifier = SlackNotifier(default_channel=slack_channel)

        print(f"▶ Slack通知を送信中... ({slack_channel})")
        print()

        # 全体サマリーを送信
        overall_summary = generator.generate_overall_summary(
            summaries=summaries,
            week_start=week_start,
            week_end=week_end,
        )
        notifier.send_message(overall_summary, channel=slack_channel)
        print("✅ 全体サマリーを送信しました")
        print()

        # 各CAの個別レポートを送信
        for summary in summaries:
            # 前週のサマリーも取得（比較用）
            prev_week_start = (datetime.strptime(week_start, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
            prev_week_end = (datetime.strptime(week_end, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
            
            previous_summary = generator.generate_weekly_summary(
                ca_id=summary.ca_id,
                week_start=prev_week_start,
                week_end=prev_week_end,
            )

            # レポートメッセージを生成
            report_message = generator.generate_weekly_report_message(
                summary=summary,
                previous_week_summary=previous_summary,
            )

            # Slackに送信（メンション付き）
            success = notifier.send_message(report_message, channel=slack_channel)
            
            if success:
                print(f"✅ {summary.ca_name or summary.ca_id}のレポートを送信しました")
            else:
                print(f"❌ {summary.ca_name or summary.ca_id}のレポート送信に失敗しました")

        print()
        print("=" * 70)
        print("週次レポート配信完了")
        print("=" * 70)
    else:
        # Slack通知なしの場合、レポートを表示
        print("=" * 70)
        print("週次レポート（プレビュー）")
        print("=" * 70)
        print()

        overall_summary = generator.generate_overall_summary(
            summaries=summaries,
            week_start=week_start,
            week_end=week_end,
        )
        print(overall_summary)
        print()

        for summary in summaries:
            prev_week_start = (datetime.strptime(week_start, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
            prev_week_end = (datetime.strptime(week_end, "%Y-%m-%d") - timedelta(days=7)).strftime("%Y-%m-%d")
            
            previous_summary = generator.generate_weekly_summary(
                ca_id=summary.ca_id,
                week_start=prev_week_start,
                week_end=prev_week_end,
            )

            report_message = generator.generate_weekly_report_message(
                summary=summary,
                previous_week_summary=previous_summary,
            )
            print(report_message)
            print()


if __name__ == "__main__":
    main()

