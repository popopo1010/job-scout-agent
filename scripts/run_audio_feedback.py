#!/usr/bin/env python3
"""
音声ファイル統合フィードバック生成スクリプト

書き起こし準備済みの音声ファイルを処理してフィードバックを生成します。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feedback.audio_feedback_engine import AudioFeedbackEngine


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="音声ファイル統合フィードバック生成")
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=None,
        help="音声ファイルディレクトリ（デフォルト: data/audio）",
    )
    parser.add_argument(
        "--transcripts-dir",
        type=Path,
        default=None,
        help="書き起こしファイルディレクトリ（デフォルト: data/transcripts/pending）",
    )
    parser.add_argument(
        "--criteria-path",
        type=Path,
        default=Path("data/sample/feedback/pss_ads_criteria.md"),
        help="PSS/ADS評価基準ファイルのパス",
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        help="Claude AIを使用してフィードバック生成",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path("data/exports/feedback"),
        help="出力ディレクトリ",
    )

    args = parser.parse_args()

    print("=" * 70)
    print("音声ファイル統合フィードバック生成")
    print("=" * 70)
    print()

    # エンジンを初期化
    engine = AudioFeedbackEngine(
        audio_dir=args.audio_dir,
        transcripts_dir=args.transcripts_dir,
        criteria_path=args.criteria_path,
        use_ai=args.use_ai,
    )

    # 状況を確認
    pending_count = engine.get_pending_count()
    ready_count = engine.get_ready_count()

    print(f"📊 処理状況:")
    print(f"   書き起こし待ち: {pending_count}件")
    print(f"   処理準備済み: {ready_count}件")
    print()

    if ready_count == 0:
        print("⚠️  処理対象の音声ファイルがありません")
        print()
        print("💡 ヒント:")
        print("   1. 音声ファイルをアップロード: python scripts/upload_audio.py <ファイル>")
        print("   2. 書き起こしファイルを紐付け: python scripts/link_transcript.py <日付> <CA_ID> <会議ID> <書き起こしファイル>")
        return

    # 処理実行
    print("▶ フィードバック生成を実行中...")
    feedbacks = engine.process_audio_with_transcript()
    print(f"   完了: {len(feedbacks)}件処理")
    print()

    # 結果表示
    if feedbacks:
        for fb in feedbacks:
            print("=" * 70)
            print(fb.to_text_report())
            print()

    # サマリー
    print(engine.generate_summary_report())

    # エクスポート
    if feedbacks:
        args.output_dir.mkdir(parents=True, exist_ok=True)
        engine.feedback_engine.export_all_feedbacks(args.output_dir)
        print(f"\n▶ レポートを出力: {args.output_dir}")


if __name__ == "__main__":
    main()

