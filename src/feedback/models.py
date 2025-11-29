"""フィードバックシステムのデータモデル"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Literal, Optional


class EvaluationLevel(str, Enum):
    """評価レベル（A/B/C/D）"""

    A = "A"  # 優秀
    B = "B"  # 良好
    C = "C"  # 要改善
    D = "D"  # 要指導

    @property
    def score(self) -> int:
        """数値スコア（A=4, B=3, C=2, D=1）"""
        return {"A": 4, "B": 3, "C": 2, "D": 1}[self.value]

    @property
    def label(self) -> str:
        """日本語ラベル"""
        return {"A": "優秀", "B": "良好", "C": "要改善", "D": "要指導"}[self.value]


class OverallRating(str, Enum):
    """総合評価"""

    EXCELLENT = "excellent"  # 優秀（3.5以上）
    GOOD = "good"  # 良好（2.5〜3.4）
    NEEDS_IMPROVEMENT = "needs_improvement"  # 要改善（1.5〜2.4）
    REQUIRES_COACHING = "requires_coaching"  # 要指導（1.5未満）

    @property
    def label(self) -> str:
        return {
            "excellent": "優秀（Excellent）",
            "good": "良好（Good）",
            "needs_improvement": "要改善（Needs Improvement）",
            "requires_coaching": "要指導（Requires Coaching）",
        }[self.value]

    @classmethod
    def from_score(cls, score: float) -> "OverallRating":
        """スコアから総合評価を判定"""
        if score >= 3.5:
            return cls.EXCELLENT
        elif score >= 2.5:
            return cls.GOOD
        elif score >= 1.5:
            return cls.NEEDS_IMPROVEMENT
        else:
            return cls.REQUIRES_COACHING


@dataclass
class Transcript:
    """書き起こしデータ"""

    file_path: str
    ca_id: str
    ca_name: Optional[str] = None
    date: str = ""
    meeting_id: str = ""
    client_name: Optional[str] = None
    content: str = ""
    duration_minutes: Optional[int] = None

    @classmethod
    def from_filename(cls, filename: str, content: str = "") -> "Transcript":
        """
        ファイル名から情報を抽出して生成

        命名規則: {日付}_{CA_ID}_{会議識別子}.txt
        例: 2025-01-15_CA001_client-call-001.txt
        """
        import re
        from pathlib import Path

        path = Path(filename)
        stem = path.stem  # 拡張子なしのファイル名

        # 命名規則パターン
        pattern = r"(\d{4}-\d{2}-\d{2})_([A-Za-z0-9]+)_(.+)"
        match = re.match(pattern, stem)

        if match:
            date, ca_id, meeting_id = match.groups()
            return cls(
                file_path=filename,
                ca_id=ca_id,
                date=date,
                meeting_id=meeting_id,
                content=content,
            )
        else:
            # パターンにマッチしない場合
            return cls(
                file_path=filename,
                ca_id="UNKNOWN",
                content=content,
            )


@dataclass
class PSSEvaluation:
    """PSS (Professional Selling Skills) 評価"""

    opening: EvaluationLevel  # オープニング
    need_identification: EvaluationLevel  # ニーズ把握
    presentation: EvaluationLevel  # 提案
    handling_objections: EvaluationLevel  # 反論対応
    closing: EvaluationLevel  # クロージング

    opening_comment: str = ""
    need_identification_comment: str = ""
    presentation_comment: str = ""
    handling_objections_comment: str = ""
    closing_comment: str = ""

    @property
    def average_score(self) -> float:
        """平均スコア"""
        scores = [
            self.opening.score,
            self.need_identification.score,
            self.presentation.score,
            self.handling_objections.score,
            self.closing.score,
        ]
        return sum(scores) / len(scores)


@dataclass
class ADSEvaluation:
    """ADS (Adaptive Dealer Selling) 評価"""

    adaptability: EvaluationLevel  # 相手への適応
    rapport_building: EvaluationLevel  # 信頼関係構築
    value_delivery: EvaluationLevel  # 価値提供

    adaptability_comment: str = ""
    rapport_building_comment: str = ""
    value_delivery_comment: str = ""

    @property
    def average_score(self) -> float:
        """平均スコア"""
        scores = [
            self.adaptability.score,
            self.rapport_building.score,
            self.value_delivery.score,
        ]
        return sum(scores) / len(scores)


@dataclass
class Feedback:
    """フィードバック"""

    transcript: Transcript
    pss: PSSEvaluation
    ads: ADSEvaluation
    good_points: list[str] = field(default_factory=list)
    improvement_points: list[str] = field(default_factory=list)
    specific_advice: str = ""
    next_goals: str = ""
    created_at: datetime = field(default_factory=datetime.now)

    @property
    def overall_score(self) -> float:
        """総合スコア"""
        # PSS 5項目 + ADS 3項目 の平均
        pss_total = (
            self.pss.opening.score
            + self.pss.need_identification.score
            + self.pss.presentation.score
            + self.pss.handling_objections.score
            + self.pss.closing.score
        )
        ads_total = (
            self.ads.adaptability.score
            + self.ads.rapport_building.score
            + self.ads.value_delivery.score
        )
        return (pss_total + ads_total) / 8

    @property
    def overall_rating(self) -> OverallRating:
        """総合評価"""
        return OverallRating.from_score(self.overall_score)

    def to_slack_message(self) -> str:
        """Slack送信用フォーマット"""
        lines = [
            f"*【通話フィードバック】*",
            f"日付: {self.transcript.date}",
            f"CA: {self.transcript.ca_name or self.transcript.ca_id}",
            "",
            f"*■ 総合評価: {self.overall_rating.label}* (スコア: {self.overall_score:.1f}/4.0)",
            "",
            "*■ 良かった点:*",
        ]
        for i, point in enumerate(self.good_points, 1):
            lines.append(f"{i}. {point}")

        lines.append("")
        lines.append("*■ 改善点:*")
        for i, point in enumerate(self.improvement_points, 1):
            lines.append(f"{i}. {point}")

        lines.extend(
            [
                "",
                "*■ 各項目評価:*",
                f"• オープニング: {self.pss.opening.value} ({self.pss.opening.label})",
                f"• ニーズ把握: {self.pss.need_identification.value} ({self.pss.need_identification.label})",
                f"• 提案: {self.pss.presentation.value} ({self.pss.presentation.label})",
                f"• 反論対応: {self.pss.handling_objections.value} ({self.pss.handling_objections.label})",
                f"• クロージング: {self.pss.closing.value} ({self.pss.closing.label})",
                "",
                f"*■ 具体的な改善アドバイス:*",
                self.specific_advice,
                "",
                f"*■ 次回に向けた目標:*",
                self.next_goals,
            ]
        )
        return "\n".join(lines)

    def to_text_report(self) -> str:
        """テキストレポート形式"""
        lines = [
            "=" * 60,
            "通話フィードバックレポート",
            "=" * 60,
            "",
            f"日付: {self.transcript.date}",
            f"CA: {self.transcript.ca_name or self.transcript.ca_id}",
            f"会議ID: {self.transcript.meeting_id}",
            "",
            "-" * 60,
            f"■ 総合評価: {self.overall_rating.label}",
            f"  スコア: {self.overall_score:.2f} / 4.00",
            "-" * 60,
            "",
            "■ 良かった点:",
        ]
        for i, point in enumerate(self.good_points, 1):
            lines.append(f"  {i}. {point}")

        lines.append("")
        lines.append("■ 改善点:")
        for i, point in enumerate(self.improvement_points, 1):
            lines.append(f"  {i}. {point}")

        lines.extend(
            [
                "",
                "-" * 60,
                "■ PSS (Professional Selling Skills) 評価",
                "-" * 60,
                f"  オープニング: {self.pss.opening.value} - {self.pss.opening_comment}",
                f"  ニーズ把握: {self.pss.need_identification.value} - {self.pss.need_identification_comment}",
                f"  提案: {self.pss.presentation.value} - {self.pss.presentation_comment}",
                f"  反論対応: {self.pss.handling_objections.value} - {self.pss.handling_objections_comment}",
                f"  クロージング: {self.pss.closing.value} - {self.pss.closing_comment}",
                "",
                "-" * 60,
                "■ ADS (Adaptive Dealer Selling) 評価",
                "-" * 60,
                f"  相手への適応: {self.ads.adaptability.value} - {self.ads.adaptability_comment}",
                f"  信頼関係構築: {self.ads.rapport_building.value} - {self.ads.rapport_building_comment}",
                f"  価値提供: {self.ads.value_delivery.value} - {self.ads.value_delivery_comment}",
                "",
                "-" * 60,
                "■ 具体的な改善アドバイス",
                "-" * 60,
                self.specific_advice,
                "",
                "-" * 60,
                "■ 次回に向けた目標",
                "-" * 60,
                self.next_goals,
                "",
                "=" * 60,
            ]
        )
        return "\n".join(lines)
