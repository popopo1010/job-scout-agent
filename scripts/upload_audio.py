#!/usr/bin/env python3
"""
音声ファイルアップロードスクリプト

音声ファイルをシステムに追加します。
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feedback.audio_manager import AudioManager


def main():
    """メイン処理"""
    import argparse

    parser = argparse.ArgumentParser(description="音声ファイルをアップロード")
    parser.add_argument("audio_file", type=Path, help="アップロードする音声ファイルのパス")
    parser.add_argument("--ca-id", type=str, help="CA ID（ファイル名から自動抽出できない場合）")
    parser.add_argument("--date", type=str, help="日付 YYYY-MM-DD（ファイル名から自動抽出できない場合）")
    parser.add_argument("--meeting-id", type=str, help="会議識別子（ファイル名から自動抽出できない場合）")
    parser.add_argument("--force", action="store_true", help="既存ファイルを上書き")
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
    print("音声ファイルアップロード")
    print("=" * 70)
    print()

    # ファイル存在確認
    if not args.audio_file.exists():
        print(f"❌ エラー: ファイルが見つかりません: {args.audio_file}")
        sys.exit(1)

    # ファイル名を確認
    print(f"📁 ファイル: {args.audio_file}")
    print(f"   サイズ: {args.audio_file.stat().st_size / (1024*1024):.2f} MB")

    # ファイル名から情報を抽出できるか確認
    parsed = audio_manager.parse_filename(args.audio_file.name)
    if parsed:
        date, ca_id, meeting_id = parsed
        print(f"✅ ファイル名から情報を抽出:")
        print(f"   日付: {date}")
        print(f"   CA ID: {ca_id}")
        print(f"   会議ID: {meeting_id}")
    else:
        print("⚠️  ファイル名から情報を抽出できませんでした")
        if not args.ca_id or not args.date:
            print("❌ エラー: --ca-id と --date を指定してください")
            sys.exit(1)

    print()

    try:
        # 音声ファイルを追加
        audio_file = audio_manager.add_audio_file(
            source_path=args.audio_file,
            ca_id=args.ca_id,
            date=args.date,
            meeting_id=args.meeting_id,
            force=args.force,
        )

        print("✅ 音声ファイルを追加しました:")
        print(f"   保存先: {audio_file.file_path}")
        print(f"   ステータス: {audio_file.status.value}")
        print()
        print("📋 次のステップ:")
        print("   1. ZoomやNottaで書き起こしを実施")
        print("   2. 書き起こしファイルを用意したら、以下のコマンドで紐付け:")
        print(f"      python scripts/link_transcript.py {audio_file.date} {audio_file.ca_id} {audio_file.meeting_id} <書き起こしファイル>")

    except FileExistsError as e:
        print(f"❌ エラー: {e}")
        print("   --force オプションを使用して上書きできます")
        sys.exit(1)
    except Exception as e:
        print(f"❌ エラー: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

