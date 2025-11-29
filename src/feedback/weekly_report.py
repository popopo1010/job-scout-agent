"""週次フィードバックレポート生成モジュール"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from .feedback_history import FeedbackHistoryManager
from .models import Feedback
from .ca_mapping import CAMappingManager


@dataclass
class WeeklyFeedbackSummary:
    """週次フィードバックサマリー"""

    ca_id: str
    ca_name: Optional[str]
    week_start: str  # YYYY-MM-DD
    week_end: str  # YYYY-MM-DD
    feedback_count: int
    average_score: float
    scores: List[float]
    rating_distribution: Dict[str, int]  # {"優秀": 0, "良好": 2, ...}
    improvement_points_frequency: Dict[str, int]  # 改善点の頻度
    repeated_improvements: List[dict]  # 繰り返し改善点
    top_improvement_points: List[tuple]  # (改善点, 回数)
    pss_averages: Dict[str, float]  # 各PSS項目の平均
    ads_averages: Dict[str, float]  # 各ADS項目の平均
    good_points_summary: Dict[str, int]  # 良かった点の頻度


class WeeklyReportGenerator:
    """週次レポート生成クラス"""

    def __init__(
        self,
        history_file: Optional[Path] = None,
        mapping_file: Optional[Path] = None,
    ):
        """
        Args:
            history_file: フィードバック履歴ファイルのパス
            mapping_file: CA-Slack IDマッピングファイルのパス
        """
        from pathlib import Path
        
        self.history_manager = FeedbackHistoryManager(history_file=history_file)
        self.ca_mapping = CAMappingManager(csv_file=mapping_file)

    def generate_weekly_summary(
        self,
        ca_id: str,
        week_start: Optional[str] = None,
        week_end: Optional[str] = None,
    ) -> Optional[WeeklyFeedbackSummary]:
        """週次サマリーを生成
        
        Args:
            ca_id: CA ID
            week_start: 週の開始日（YYYY-MM-DD）。Noneの場合は前週の月曜日
            week_end: 週の終了日（YYYY-MM-DD）。Noneの場合は前週の日曜日
            
        Returns:
            週次サマリー、データがない場合はNone
        """
        # 期間を決定（デフォルトは前週）
        if week_start is None or week_end is None:
            today = datetime.now()
            # 前週の月曜日を計算
            days_since_monday = (today.weekday() + 1) % 7  # 0=月曜日
            last_monday = today - timedelta(days=days_since_monday + 7)
            week_start = last_monday.strftime("%Y-%m-%d")
            week_end = (last_monday + timedelta(days=6)).strftime("%Y-%m-%d")
        
        # 期間内のフィードバック履歴を取得
        start_date = datetime.strptime(week_start, "%Y-%m-%d").date()
        end_date = datetime.strptime(week_end, "%Y-%m-%d").date()
        
        past_feedbacks = self.history_manager.get_past_feedbacks(ca_id, days=90)
        
        # 期間内のフィードバックをフィルタリング
        week_feedbacks = []
        for entry in past_feedbacks:
            try:
                entry_date = datetime.strptime(entry.date, "%Y-%m-%d").date() if "T" not in entry.date else datetime.fromisoformat(entry.date).date()
                if start_date <= entry_date <= end_date:
                    week_feedbacks.append(entry)
            except Exception:
                continue
        
        if not week_feedbacks:
            return None
        
        # サマリーを計算
        scores = []
        rating_counts = defaultdict(int)
        improvement_points_all = []
        good_points_all = []
        pss_scores = defaultdict(list)
        ads_scores = defaultdict(list)
        
        for entry in week_feedbacks:
            scores.append(entry.overall_score)
            improvement_points_all.extend(entry.improvement_points)
        
        # 改善点の頻度を計算
        improvement_frequency = defaultdict(int)
        for point in improvement_points_all:
            # マーカーを除去
            clean_point = point
            for marker in ["【重要】", "【必須】", "【緊急】"]:
                clean_point = clean_point.replace(marker, "").strip()
            improvement_frequency[clean_point] += 1
        
        # トップ改善点を取得
        top_improvements = sorted(
            improvement_frequency.items(),
            key=lambda x: x[1],
            reverse=True
        )[:3]
        
        # 平均スコアから評価分布を推定（実際のフィードバックから取得できないため）
        # ここでは簡易的に計算
        average_score = sum(scores) / len(scores) if scores else 0.0
        
        # CA名を取得
        ca_name = self.ca_mapping.get_ca_name(ca_id) or ca_id
        
        return WeeklyFeedbackSummary(
            ca_id=ca_id,
            ca_name=ca_name,
            week_start=week_start,
            week_end=week_end,
            feedback_count=len(week_feedbacks),
            average_score=average_score,
            scores=scores,
            rating_distribution={},  # 実際のデータから計算する必要がある
            improvement_points_frequency=dict(improvement_frequency),
            repeated_improvements=[],  # 後で計算
            top_improvement_points=top_improvements,
            pss_averages={},
            ads_averages={},
            good_points_summary={},
        )

    def generate_weekly_report_message(
        self,
        summary: WeeklyFeedbackSummary,
        previous_week_summary: Optional[WeeklyFeedbackSummary] = None,
    ) -> str:
        """週次レポートメッセージを生成（Slack用）"""
        mention = self.ca_mapping.get_slack_mention(summary.ca_id)
        if mention:
            mention_text = f"{mention} {summary.ca_name}さんの週次フィードバックレポート\n"
        else:
            mention_text = f"{summary.ca_name or summary.ca_id}さんの週次フィードバックレポート\n"
        
        lines = [
            mention_text,
            "*【週次フィードバックレポート】*",
            f"期間: {summary.week_start} 〜 {summary.week_end}",
            "",
            f"*■ 今週のフィードバック件数: {summary.feedback_count}件*",
        ]
        
        # 平均スコア（前週比較）
        if previous_week_summary:
            score_diff = summary.average_score - previous_week_summary.average_score
            arrow = "⬆️" if score_diff > 0 else "⬇️" if score_diff < 0 else "➡️"
            lines.append(
                f"*■ 平均スコア: {summary.average_score:.1f} / 4.0* "
                f"（前週: {previous_week_summary.average_score:.1f} → "
                f"{score_diff:+.1f} {arrow}）"
            )
        else:
            lines.append(f"*■ 平均スコア: {summary.average_score:.1f} / 4.0*")
        
        lines.append("")
        
        # トップ改善点
        if summary.top_improvement_points:
            lines.append("*■ 今週最も多く指摘された改善点*")
            for i, (point, count) in enumerate(summary.top_improvement_points, 1):
                lines.append(f"{i}. {point}（{count}回）")
                # 繰り返し改善点かチェック
                for repeated in summary.repeated_improvements:
                    if point in repeated.get("improvement_point", ""):
                        lines.append(f"   → 過去も{repeated['count']}回指摘されています。根本的な改善が必要です。")
            
            lines.append("")
        
        # 成長傾向
        if previous_week_summary:
            score_diff = summary.average_score - previous_week_summary.average_score
            if score_diff > 0:
                lines.append(f"*■ 成長傾向*")
                lines.append(f"前週と比較して、平均スコアが{score_diff:.1f}ポイント向上しています。")
                lines.append("この調子で継続してください。")
            elif score_diff < 0:
                lines.append(f"*■ 成長傾向*")
                lines.append(f"前週と比較して、平均スコアが{abs(score_diff):.1f}ポイント低下しています。")
                lines.append("改善が必要です。次週は必ず向上させてください。")
            lines.append("")
        
        # 次週の目標
        if summary.top_improvement_points:
            top_point, top_count = summary.top_improvement_points[0]
            lines.append(f"*■ 次週に向けた改善目標*")
            lines.append(f"最も多く指摘された「{top_point}」を必ず改善してください。")
            lines.append(f"期待展開率8%を実現するため、この改善は必須です。")
            lines.append("同じ指摘を繰り返さないよう、徹底してください。")
            lines.append("")
        
        lines.extend([
            "─────────────────────────────────────",
            "",
            "あなたの成長を心から期待しています。",
        ])
        
        return "\n".join(lines)

    def generate_overall_summary(
        self,
        summaries: List[WeeklyFeedbackSummary],
        week_start: str,
        week_end: str,
    ) -> str:
        """全体サマリーレポートを生成"""
        total_count = sum(s.feedback_count for s in summaries)
        avg_score = sum(s.average_score for s in summaries) / len(summaries) if summaries else 0.0
        
        # 最も多い改善点を集計
        all_improvements = defaultdict(int)
        for summary in summaries:
            for point, count in summary.improvement_points_frequency.items():
                all_improvements[point] += count
        
        top_improvement = max(all_improvements.items(), key=lambda x: x[1]) if all_improvements else None
        
        lines = [
            "*【週次フィードバックレポート - 全体サマリー】*",
            f"期間: {week_start} 〜 {week_end}",
            "",
            "*■ 全体サマリー*",
            f"- フィードバック生成件数: {total_count}件",
            f"- 平均スコア: {avg_score:.1f} / 4.0",
        ]
        
        if top_improvement:
            lines.append(f"- 最も多く指摘された改善点: {top_improvement[0]}（{top_improvement[1]}件）")
        
        lines.extend([
            "",
            "各CAの詳細は、以下をご確認ください。",
            "",
            "─────────────────────────────────────",
        ])
        
        return "\n".join(lines)

