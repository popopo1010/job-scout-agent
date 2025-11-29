#!/usr/bin/env python3
"""
音声ファイル自動処理スクリプト

data/audio/pending/ に音声ファイルを置くだけで、自動的に処理を開始します。
- 新しい音声ファイルを自動登録
- 書き起こしファイルを自動検出・紐付け
- フィードバック生成も自動実行
"""

import sys
from pathlib import Path
import re

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feedback.audio_manager import AudioManager, AudioStatus
from src.feedback.audio_feedback_engine import AudioFeedbackEngine
from src.common.slack_notifier import SlackNotifier


def extract_info_from_filename(filename: str) -> tuple[str, str, str] | None:
    """ファイル名から日付、CA ID、会議IDを抽出
    
    Args:
        filename: ファイル名（例: "2025-01-15_CA001_client-call-001.m4a"）
        
    Returns:
        (date, ca_id, meeting_id) または None
    """
    pattern = r"(\d{4}-\d{2}-\d{2})_([A-Za-z0-9]+)_(.+)\.(\w+)"
    match = re.match(pattern, filename)
    if match:
        date, ca_id, meeting_id, ext = match.groups()
        return date, ca_id, meeting_id
    return None


def auto_import_audio_files(audio_manager: AudioManager) -> int:
    """pendingフォルダ内の未登録ファイルを自動登録
    
    Returns:
        登録したファイル数
    """
    pending_dir = audio_manager.pending_dir
    if not pending_dir.exists():
        return 0
    
    registered_count = 0
    
    # pendingフォルダ内のファイルをチェック
    for file_path in pending_dir.iterdir():
        if not file_path.is_file():
            continue
        
        # 対応形式かチェック
        if file_path.suffix.lower() not in AudioManager.SUPPORTED_FORMATS:
            continue
        
        # ファイル名から情報を抽出
        info = extract_info_from_filename(file_path.name)
        if not info:
            print(f"⚠️  ファイル名の形式が正しくありません（スキップ）: {file_path.name}")
            continue
        
        date, ca_id, meeting_id = info
        
        # 既に登録済みかチェック
        existing = audio_manager.find_audio_file(date, ca_id, meeting_id)
        if existing:
            continue
        
        try:
            # ファイルを登録
            audio_file = audio_manager.add_audio_file(
                source_path=file_path,
                ca_id=ca_id,
                date=date,
                meeting_id=meeting_id,
                force=False,
            )
            print(f"✅ 音声ファイルを登録: {file_path.name}")
            registered_count += 1
        except Exception as e:
            print(f"❌ 登録失敗: {file_path.name} - {e}")
    
    return registered_count


def auto_link_transcripts(audio_manager: AudioManager) -> int:
    """書き起こしファイルを自動検出・紐付け
    
    Returns:
        紐付けしたファイル数
    """
    transcripts_pending_dir = Path("data/audio/transcripts/pending")
    if not transcripts_pending_dir.exists():
        transcripts_pending_dir.mkdir(parents=True, exist_ok=True)
        return 0
    
    linked_count = 0
    
    # 書き起こしファイルをチェック
    for transcript_path in transcripts_pending_dir.glob("*.txt"):
        # ファイル名から情報を抽出
        info = extract_info_from_filename(transcript_path.stem + ".txt")
        if not info:
            continue
        
        date, ca_id, meeting_id = info
        
        # 対応する音声ファイルを検索
        audio_file = audio_manager.find_audio_file(date, ca_id, meeting_id)
        if not audio_file:
            continue
        
        # 既に紐付け済みかチェック
        if audio_file.status == AudioStatus.TRANSCRIPT_READY:
            continue
        
        try:
            # 書き起こしファイルを紐付け
            audio_manager.link_transcript(audio_file, transcript_path)
            print(f"✅ 書き起こしを紐付け: {transcript_path.name}")
            linked_count += 1
            
            # 紐付け後、書き起こしファイルを移動（オプション）
            # processed_dir = Path("data/audio/transcripts/processed")
            # processed_dir.mkdir(parents=True, exist_ok=True)
            # transcript_path.rename(processed_dir / transcript_path.name)
        except Exception as e:
            print(f"❌ 紐付け失敗: {transcript_path.name} - {e}")
    
    return linked_count


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="音声ファイル自動処理")
    parser.add_argument(
        "--no-feedback",
        action="store_true",
        help="フィードバック生成をスキップ",
    )
    parser.add_argument(
        "--no-slack",
        action="store_true",
        help="Slack通知を無効化",
    )
    parser.add_argument(
        "--use-ai",
        action="store_true",
        help="Claude AIを使用してフィードバック生成",
    )
    parser.add_argument(
        "--slack-channel",
        type=str,
        default=None,
        help="Slack通知先チャンネル",
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("音声ファイル自動処理")
    print("=" * 70)
    print()
    
    audio_manager = AudioManager()
    
    # ステップ1: 新しい音声ファイルを自動登録
    print("▶ ステップ1: 新しい音声ファイルを検出中...")
    registered_count = auto_import_audio_files(audio_manager)
    if registered_count > 0:
        print(f"   登録完了: {registered_count}件")
    else:
        print("   新しいファイルはありません")
    print()
    
    # ステップ2: 書き起こしファイルを自動紐付け
    print("▶ ステップ2: 書き起こしファイルを検出中...")
    linked_count = auto_link_transcripts(audio_manager)
    if linked_count > 0:
        print(f"   紐付け完了: {linked_count}件")
    else:
        print("   新しい書き起こしファイルはありません")
    print()
    
    # ステップ3: フィードバック生成
    if not args.no_feedback:
        print("▶ ステップ3: フィードバック生成中...")
        engine = AudioFeedbackEngine(use_ai=args.use_ai)
        
        ready_count = engine.get_ready_count()
        if ready_count > 0:
            print(f"   処理準備済み: {ready_count}件")
            
            feedbacks = engine.process_audio_with_transcript()
            print(f"   フィードバック生成完了: {len(feedbacks)}件")
            
            # Slack通知
            if feedbacks and not args.no_slack:
                print()
                print("▶ Slack通知を送信中...")
                slack_channel = args.slack_channel or "#dk_ca_ops"
                notifier = SlackNotifier(default_channel=slack_channel)
                
                for fb in feedbacks:
                    slack_message = fb.to_slack_message()
                    notifier.send_message(slack_message, channel=slack_channel)
                
                print(f"   Slack通知完了: {len(feedbacks)}件")
        else:
            print("   処理対象のファイルはありません")
    else:
        print("▶ ステップ3: フィードバック生成をスキップ")
    
    print()
    print("=" * 70)
    print("自動処理完了")
    print("=" * 70)


if __name__ == "__main__":
    main()

