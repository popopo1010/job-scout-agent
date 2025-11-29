#!/usr/bin/env python3
"""
書き起こしファイル紐付けスクリプト

音声ファイルと書き起こしファイルを紐付けます。
紐付け後、自動的に既存のフィードバックシステムで処理されます。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feedback.audio_manager import AudioManager


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="音声ファイルと書き起こしファイルを紐付け")
    parser.add_argument("date", type=str, help="日付 YYYY-MM-DD")
    parser.add_argument("ca_id", type=str, help="CA ID")
    parser.add_argument("meeting_id", type=str, help="会議識別子")
    parser.add_argument("transcript_file", type=Path, help="書き起こしファイルのパス")
    parser.add_argument(
        "--audio-dir",
        type=Path,
        default=None,
        help="音声ファイルディレクトリ（デフォルト: data/audio）",
    )

    args = parser.parse_args()

    # AudioManagerを初期化
    audio_manager = AudioManager(audio_dir=args.audio_dir)

    print("=" * 70)
    print("書き起こしファイル紐付け")
    print("=" * 70)
    print()

    # 音声ファイルを検索
    audio_file = audio_manager.find_audio_file(args.date, args.ca_id, args.meeting_id)

    if not audio_file:
        print(f"❌ エラー: 音声ファイルが見つかりません")
        print(f"   検索条件: {args.date} / {args.ca_id} / {args.meeting_id}")
        print()
        print("💡 ヒント: 音声ファイルを先にアップロードしてください")
        print("   python scripts/upload_audio.py <音声ファイル>")
        sys.exit(1)

    print(f"✅ 音声ファイルを発見:")
    print(f"   {audio_file.file_path}")
    print(f"   ステータス: {audio_file.status.value}")
    print()

    # 書き起こしファイルの確認
    if not args.transcript_file.exists():
        print(f"❌ エラー: 書き起こしファイルが見つかりません: {args.transcript_file}")
        sys.exit(1)

    print(f"📝 書き起こしファイル:")
    print(f"   {args.transcript_file}")
    print()

    try:
        # 書き起こしファイルを紐付け
        audio_manager.link_transcript(audio_file, args.transcript_file)

        print("✅ 書き起こしファイルを紐付けました")
        print(f"   書き起こしファイル保存先: {audio_file.transcript_path}")
        print(f"   新しいステータス: {audio_file.status.value}")
        print()
        print("📋 次のステップ:")
        print("   以下のコマンドでフィードバックを生成:")
        print("   python scripts/run_audio_feedback.py")

    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

