"""フィードバックエンジン（統合クラス）"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional

from .models import Feedback
from .transcript_loader import TranscriptLoader
from .feedback_generator import FeedbackGenerator


class FeedbackEngine:
    """フィードバックシステムの統合エンジン"""

    def __init__(
        self,
        transcripts_dir: Optional[Path] = None,
        criteria_path: Optional[Path] = None,
        use_ai: bool = False,
    ) -> None:
        """
        Args:
            transcripts_dir: 書き起こしファイルのディレクトリ
            criteria_path: PSS/ADS評価基準ファイルのパス
            use_ai: Claude AIを使用するか（デフォルト: False）
        """
        transcripts_dir = transcripts_dir or Path("data/transcripts/pending")
        self.loader = TranscriptLoader(pending_dir=transcripts_dir)
        self.generator = FeedbackGenerator(criteria_path=criteria_path, use_ai=use_ai)
        self.feedbacks: List[Feedback] = []

    def process_all_pending(self) -> List[Feedback]:
        """全ての処理待ち書き起こしを処理"""
        self.feedbacks = []

        for transcript in self.loader.iter_pending():
            feedback = self.generator.generate_feedback(transcript)
            self.feedbacks.append(feedback)

        return self.feedbacks

    def process_single_file(self, file_path: Path) -> Feedback:
        """単一ファイルを処理"""
        transcript = self.loader.load_transcript(file_path)
        feedback = self.generator.generate_feedback(transcript)
        self.feedbacks.append(feedback)
        return feedback

    def generate_summary_report(self) -> str:
        """サマリーレポートを生成"""
        if not self.feedbacks:
            return "フィードバックデータがありません"

        lines = [
            "=" * 70,
            "フィードバックサマリーレポート",
            "=" * 70,
            "",
            f"処理件数: {len(self.feedbacks)}件",
            "",
        ]

        # 総合評価の分布
        ratings = {}
        for fb in self.feedbacks:
            rating = fb.overall_rating.label
            ratings[rating] = ratings.get(rating, 0) + 1

        lines.append("■ 総合評価分布:")
        for rating, count in sorted(ratings.items()):
            lines.append(f"  {rating}: {count}件")

        # 平均スコア
        avg_score = sum(fb.overall_score for fb in self.feedbacks) / len(self.feedbacks)
        lines.append("")
        lines.append(f"■ 平均スコア: {avg_score:.2f} / 4.00")

        # 各項目の平均
        lines.extend(
            [
                "",
                "■ PSS項目別平均スコア:",
            ]
        )
        pss_items = ["opening", "need_identification", "presentation", "handling_objections", "closing"]
        pss_labels = ["オープニング", "ニーズ把握", "提案", "反論対応", "クロージング"]

        for item, label in zip(pss_items, pss_labels):
            avg = sum(getattr(fb.pss, item).score for fb in self.feedbacks) / len(self.feedbacks)
            lines.append(f"  {label}: {avg:.2f}")

        lines.extend(
            [
                "",
                "■ ADS項目別平均スコア:",
            ]
        )
        ads_items = ["adaptability", "rapport_building", "value_delivery"]
        ads_labels = ["相手への適応", "信頼関係構築", "価値提供"]

        for item, label in zip(ads_items, ads_labels):
            avg = sum(getattr(fb.ads, item).score for fb in self.feedbacks) / len(self.feedbacks)
            lines.append(f"  {label}: {avg:.2f}")

        lines.append("")
        lines.append("=" * 70)

        return "\n".join(lines)

    def export_all_feedbacks(self, output_dir: Path) -> None:
        """全フィードバックをエクスポート"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 個別レポート
        for fb in self.feedbacks:
            filename = f"feedback_{fb.transcript.date}_{fb.transcript.ca_id}.txt"
            output_path = output_dir / filename
            output_path.write_text(fb.to_text_report(), encoding="utf-8")

        # CSVエクスポート
        if self.feedbacks:
            csv_path = output_dir / "feedback_summary.csv"
            self.generator.export_feedback_csv(self.feedbacks, csv_path)
