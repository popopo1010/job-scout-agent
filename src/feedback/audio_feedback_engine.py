"""音声ファイル統合フィードバックエンジン"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from .audio_manager import AudioManager, AudioStatus
from .feedback_engine import FeedbackEngine
from .models import Feedback


class AudioFeedbackEngine:
    """音声ファイルを統合したフィードバックエンジン"""

    def __init__(
        self,
        audio_dir: Optional[Path] = None,
        transcripts_dir: Optional[Path] = None,
        criteria_path: Optional[Path] = None,
        use_ai: bool = False,
    ) -> None:
        """
        Args:
            audio_dir: 音声ファイルのディレクトリ
            transcripts_dir: 書き起こしファイルのディレクトリ
            criteria_path: PSS/ADS評価基準ファイルのパス
            use_ai: Claude AIを使用するか
        """
        self.audio_manager = AudioManager(audio_dir=audio_dir)
        self.feedback_engine = FeedbackEngine(
            transcripts_dir=transcripts_dir,
            criteria_path=criteria_path,
            use_ai=use_ai,
        )

    def process_audio_with_transcript(self) -> List[Feedback]:
        """
        書き起こし準備済みの音声ファイルを処理してフィードバックを生成

        Returns:
            生成されたフィードバックのリスト
        """
        # 書き起こし準備済みの音声ファイルを取得
        ready_audio_files = self.audio_manager.list_ready_for_processing()

        if not ready_audio_files:
            return []

        feedbacks = []

        for audio_file in ready_audio_files:
            if not audio_file.transcript_path or not audio_file.transcript_path.exists():
                continue

            try:
                # 既存のフィードバック生成フローを使用
                feedback = self.feedback_engine.process_single_file(audio_file.transcript_path)

                # 音声ファイルを処理済みとしてマーク
                self.audio_manager.mark_as_processed(audio_file)

                feedbacks.append(feedback)

            except Exception as e:
                # エラーが発生した場合は失敗としてマーク
                self.audio_manager.mark_as_failed(audio_file, error_message=str(e))
                print(f"Error processing audio file {audio_file.file_path}: {e}")

        return feedbacks

    def get_pending_count(self) -> int:
        """書き起こし待ちの音声ファイル数を取得"""
        return len(self.audio_manager.list_pending_audio())

    def get_ready_count(self) -> int:
        """書き起こし準備済みの音声ファイル数を取得"""
        return len(self.audio_manager.list_ready_for_processing())

    def generate_summary_report(self) -> str:
        """サマリーレポートを生成"""
        lines = [
            "=" * 70,
            "音声ファイルフィードバックシステム - サマリーレポート",
            "=" * 70,
            "",
            f"書き起こし待ち: {self.get_pending_count()}件",
            f"処理準備済み: {self.get_ready_count()}件",
            "",
        ]

        # フィードバックエンジンのサマリーも追加
        if self.feedback_engine.feedbacks:
            lines.append(self.feedback_engine.generate_summary_report())

        return "\n".join(lines)

