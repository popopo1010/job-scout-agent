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
    repeated_improvements: list[dict] = field(default_factory=list)  # 繰り返されている改善点

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

    def _get_overall_evaluation_message(self) -> str:
        """総合評価メッセージを生成（スコア別）"""
        score = self.overall_score
        rating = self.overall_rating
        
        if score >= 3.5:
            return f"""*■ 総合評価: 優秀（Excellent）* (スコア: {score:.1f}/4.0)

素晴らしい通話でした。期待展開率8%を実現できるレベルの対応ができています。
この調子で継続すれば、更なる成長が見込めます。ただし、さらに上を目指すため、細かい改善点もありますので、以下を参考にしてください。"""
        
        elif score >= 2.5:
            return f"""*■ 総合評価: 良好（Good）* (スコア: {score:.1f}/4.0)

基本的な営業スキルは身についていますが、期待展開率8%を実現するには、
まだ改善の余地があります。今回の分析結果を真摯に受け止め、次回の通話で必ず改善してください。
成長への道のりは厳しいものですが、あなたなら必ず乗り越えられます。"""
        
        elif score >= 1.5:
            return f"""*■ 総合評価: 要改善（Needs Improvement）* (スコア: {score:.1f}/4.0)

今回は期待する水準には届きませんでした。期待展開率8%を実現するためには、
根本的な見直しが必要です。ただし、課題が明確になったことは成長のチャンスです。
今回指摘する改善点を徹底的に意識し、次回は必ず改善を見せてください。"""
        
        else:
            return f"""*■ 総合評価: 要指導（Requires Coaching）* (スコア: {score:.1f}/4.0)

今回の通話は、営業の基本ができていませんでした。期待展開率8%の実現は、
まず基本を徹底的に身につけることから始まります。厳しい評価ですが、これが現実です。
しかし、この現実を受け止め、一つずつ改善していけば、必ず成長できます。
次回までに、以下を徹底的に見直し、準備して臨んでください。"""

    def to_slack_message(self) -> str:
        """Slack送信用フォーマット（営業マネージャー視点）"""
        ca_name = self.transcript.ca_name or self.transcript.ca_id
        
        lines = [
            f"*【通話フィードバック】*",
            f"日付: {self.transcript.date}",
            f"CA: {ca_name}",
            "",
            f"あなたの成長を期待しながら、今回の通話を分析しました。",
            f"期待展開率8%の実現に向けて、厳しくも建設的なフィードバックをお伝えします。",
            "",
            "─────────────────────────────────────",
            "",
            self._get_overall_evaluation_message(),
            "",
            "─────────────────────────────────────",
            "",
            "*■ 今回の通話で評価できる点:*",
        ]
        
        for i, point in enumerate(self.good_points, 1):
            lines.append(f"{i}. {point}")
            if i == 1 and self.overall_score >= 2.5:
                lines.append("   この基本動作を継続することで、信頼関係構築の土台ができています。")
            elif i == len(self.good_points) and self.overall_score >= 2.5:
                lines.append("   さらに上を目指すため、改善点もしっかりと意識してください。")

        lines.append("")
        lines.append("*■ 今回の通話で必ず改善すべき点:*")
        
        importance_markers = ["【重要】", "【必須】", "【緊急】"]
        for i, point in enumerate(self.improvement_points, 1):
            marker = importance_markers[min(i - 1, len(importance_markers) - 1)]
            lines.append(f"{marker} {point}")
            
            # 繰り返されている改善点かチェック
            for repeated in self.repeated_improvements:
                if repeated["improvement_point"] == point:
                    count = repeated["count"]
                    last_date = repeated["last_feedback_date"]
                    lines.append("")
                    lines.append(f"   ⚠️ *【重要】この改善点は過去{count}回指摘されています。*")
                    lines.append(f"   最後に指摘したのは {last_date} でした。")
                    lines.append("   同じことを繰り返さないためには、なぜこの問題が起こり続けているのか、")
                    lines.append("   根本的な原因を考える必要があります。")
                    lines.append("")
                    lines.append("   考えられる原因：")
                    lines.append("   • 改善方法が具体的でなかった？")
                    lines.append("   • 改善の優先順位が低かった？")
                    lines.append("   • 習慣化するまで時間がかかっている？")
                    lines.append("")
                    lines.append("   次回までに、この問題を解決するための具体的な行動計画を立て、")
                    lines.append("   実行してください。同じ指摘を繰り返すことは、成長を妨げます。")
                    lines.append("")
                    break
        
        if self.improvement_points:
            lines.append("期待展開率8%を実現するためには、これらは必須です。次回は絶対に改善してください。")

        lines.extend(
            [
                "",
                "─────────────────────────────────────",
                "",
                "*■ 各項目詳細評価:*",
                "",
                f"• *オープニング: {self.pss.opening.value}* ({self.pss.opening.label})",
                f"  → {self.pss.opening_comment}",
                "",
                f"• *ニーズ把握: {self.pss.need_identification.value}* ({self.pss.need_identification.label})",
                f"  → {self.pss.need_identification_comment}",
                "",
                f"• *提案: {self.pss.presentation.value}* ({self.pss.presentation.label})",
                f"  → {self.pss.presentation_comment}",
                "",
                f"• *反論対応: {self.pss.handling_objections.value}* ({self.pss.handling_objections.label})",
                f"  → {self.pss.handling_objections_comment}",
                "",
                f"• *クロージング: {self.pss.closing.value}* ({self.pss.closing.label})",
                f"  → {self.pss.closing_comment}",
                "",
                "─────────────────────────────────────",
                "",
                f"*■ 具体的な改善アクション（次回通話までに必ず実行すること）:*",
                "",
                self.specific_advice,
                "",
                "これらを徹底することで、期待展開率8%に近づけます。厳しく聞こえるかもしれませんが、",
                "これがKeyensのスタンダードです。あなたの成長を心から期待しています。",
                "",
                "─────────────────────────────────────",
                "",
                f"*■ 次回通話での{'必須改善目標' if self.overall_score < 3.5 else 'チャレンジ目標'}:*",
                "",
                self.next_goals,
                "",
                "─────────────────────────────────────",
                "",
                "今回のフィードバックはいかがでしたか？",
                "厳しく感じる部分もあるかもしれませんが、それはあなたの成長を期待しているからです。",
                "",
                "期待展開率8%を実現するためには、このレベルの営業スキルが求められます。",
                "厳しい道のりですが、一つずつ改善を積み重ねれば、必ず目標に到達できます。",
                "",
                f"次回の通話で、必ず改善を見せてください。あなたの成長を心から期待しています。",
                "質問があれば、いつでも声をかけてください。一緒に成長していきましょう。",
                "",
                "─────────────────────────────────────",
            ]
        )
        return "\n".join(lines)

    def to_text_report(self) -> str:
        """テキストレポート形式（営業マネージャー視点）"""
        ca_name = self.transcript.ca_name or self.transcript.ca_id
        overall_msg = self._get_overall_evaluation_message().replace("*", "")
        
        lines = [
            "=" * 60,
            "通話フィードバックレポート",
            "=" * 60,
            "",
            f"日付: {self.transcript.date}",
            f"CA: {ca_name}",
            f"会議ID: {self.transcript.meeting_id}",
            "",
            "あなたの成長を期待しながら、今回の通話を分析しました。",
            "期待展開率8%の実現に向けて、厳しくも建設的なフィードバックをお伝えします。",
            "",
            "-" * 60,
            overall_msg,
            "-" * 60,
            "",
            "■ 今回の通話で評価できる点:",
        ]
        for i, point in enumerate(self.good_points, 1):
            lines.append(f"  {i}. {point}")

        lines.append("")
        lines.append("■ 今回の通話で必ず改善すべき点:")
        importance_markers = ["【重要】", "【必須】", "【緊急】"]
        for i, point in enumerate(self.improvement_points, 1):
            marker = importance_markers[min(i - 1, len(importance_markers) - 1)]
            lines.append(f"  {marker} {point}")
            
            # 繰り返されている改善点かチェック
            for repeated in self.repeated_improvements:
                if repeated["improvement_point"] == point:
                    count = repeated["count"]
                    last_date = repeated["last_feedback_date"]
                    lines.append("")
                    lines.append(f"  ⚠️ 【重要】この改善点は過去{count}回指摘されています。")
                    lines.append(f"  最後に指摘したのは {last_date} でした。")
                    lines.append("  同じことを繰り返さないためには、なぜこの問題が起こり続けているのか、")
                    lines.append("  根本的な原因を考える必要があります。")
                    lines.append("")
                    lines.append("  考えられる原因：")
                    lines.append("  • 改善方法が具体的でなかった？")
                    lines.append("  • 改善の優先順位が低かった？")
                    lines.append("  • 習慣化するまで時間がかかっている？")
                    lines.append("")
                    lines.append("  次回までに、この問題を解決するための具体的な行動計画を立て、")
                    lines.append("  実行してください。同じ指摘を繰り返すことは、成長を妨げます。")
                    lines.append("")
                    break
        
        if self.improvement_points and not any(
            any(repeated["improvement_point"] == point for repeated in self.repeated_improvements)
            for point in self.improvement_points
        ):
            lines.append("期待展開率8%を実現するためには、これらは必須です。次回は絶対に改善してください。")

        lines.extend(
            [
                "",
                "-" * 60,
                "■ PSS (Professional Selling Skills) 詳細評価",
                "-" * 60,
                f"  オープニング: {self.pss.opening.value} ({self.pss.opening.label})",
                f"    → {self.pss.opening_comment}",
                "",
                f"  ニーズ把握: {self.pss.need_identification.value} ({self.pss.need_identification.label})",
                f"    → {self.pss.need_identification_comment}",
                "",
                f"  提案: {self.pss.presentation.value} ({self.pss.presentation.label})",
                f"    → {self.pss.presentation_comment}",
                "",
                f"  反論対応: {self.pss.handling_objections.value} ({self.pss.handling_objections.label})",
                f"    → {self.pss.handling_objections_comment}",
                "",
                f"  クロージング: {self.pss.closing.value} ({self.pss.closing.label})",
                f"    → {self.pss.closing_comment}",
                "",
                "-" * 60,
                "■ ADS (Adaptive Dealer Selling) 詳細評価",
                "-" * 60,
                f"  相手への適応: {self.ads.adaptability.value} ({self.ads.adaptability.label})",
                f"    → {self.ads.adaptability_comment}",
                "",
                f"  信頼関係構築: {self.ads.rapport_building.value} ({self.ads.rapport_building.label})",
                f"    → {self.ads.rapport_building_comment}",
                "",
                f"  価値提供: {self.ads.value_delivery.value} ({self.ads.value_delivery.label})",
                f"    → {self.ads.value_delivery_comment}",
                "",
                "-" * 60,
                "■ 具体的な改善アクション（次回通話までに必ず実行すること）",
                "-" * 60,
                self.specific_advice,
                "",
                "これらを徹底することで、期待展開率8%に近づけます。",
                "厳しく聞こえるかもしれませんが、これがKeyensのスタンダードです。",
                "",
                "-" * 60,
                f"■ 次回通話での{'必須改善目標' if self.overall_score < 3.5 else 'チャレンジ目標'}",
                "-" * 60,
                self.next_goals,
                "",
                "-" * 60,
                "今回のフィードバックはいかがでしたか？",
                "厳しく感じる部分もあるかもしれませんが、それはあなたの成長を期待しているからです。",
                "",
                "期待展開率8%を実現するためには、このレベルの営業スキルが求められます。",
                "厳しい道のりですが、一つずつ改善を積み重ねれば、必ず目標に到達できます。",
                "",
                f"次回の通話で、必ず改善を見せてください。あなたの成長を心から期待しています。",
                "質問があれば、いつでも声をかけてください。一緒に成長していきましょう。",
                "",
                "=" * 60,
            ]
        )
        return "\n".join(lines)
