"""経営分析エンジン"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import CA, Lead, CAPerformance, SegmentType, Segment, SEGMENT_CONVERSION_RATES
from .segment_classifier import SegmentClassifier


class AnalyticsEngine:
    """経営分析基盤のコアエンジン"""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or Path("data/sample/analytics")
        self.leads: List[Lead] = []
        self.cas: Dict[str, CA] = {}
        self.classifier = SegmentClassifier()

    def load_leads_from_csv(self, filepath: Optional[Path] = None) -> List[Lead]:
        """CSVからリードデータを読み込み"""
        filepath = filepath or self.data_dir / "leads.csv"

        leads = []
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                has_qual = row.get("has_qualification", "").lower() == "true"
                lead = Lead(
                    lead_id=row["lead_id"],
                    name=row["name"],
                    age=int(row["age"]),
                    prefecture=row["prefecture"],
                    qualification=row["qualification"],
                    has_qualification=has_qual,
                    assigned_ca_id=row["assigned_ca_id"],
                    status=row["status"],
                    created_at=row.get("created_at", ""),
                )
                # セグメント自動分類
                self.classifier.classify_lead(lead)
                leads.append(lead)

        self.leads = leads
        return leads

    def load_cas_from_csv(self, filepath: Optional[Path] = None) -> Dict[str, CA]:
        """CSVからCAマスターを読み込み"""
        filepath = filepath or self.data_dir / "ca_master.csv"

        cas = {}
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                ca = CA(
                    ca_id=row["ca_id"],
                    name=row["name"],
                    team=row["team"],
                    slack_user_id=row["slack_user_id"],
                    target_leads=int(row["target_leads"]),
                )
                cas[ca.ca_id] = ca

        self.cas = cas
        return cas

    def assign_leads_to_cas(self) -> None:
        """リードをCAに割り当て"""
        for lead in self.leads:
            if lead.assigned_ca_id in self.cas:
                self.cas[lead.assigned_ca_id].leads.append(lead)

        # 各CAのパフォーマンスを再計算
        for ca in self.cas.values():
            ca.calculate_performance()

    def get_segment_summary(self) -> Dict[SegmentType, Dict[str, Any]]:
        """セグメント別サマリーを取得"""
        summary: Dict[SegmentType, Dict[str, Any]] = {
            seg: {"count": 0, "expected_conversions": 0.0, "conversion_rate": rate}
            for seg, rate in SEGMENT_CONVERSION_RATES.items()
        }

        for lead in self.leads:
            if lead.segment_id:
                summary[lead.segment_id]["count"] += 1
                summary[lead.segment_id]["expected_conversions"] += lead.conversion_rate or 0.0

        return summary

    def get_ca_summary(self) -> List[Dict[str, Any]]:
        """CA別サマリーを取得"""
        summaries = []
        for ca in self.cas.values():
            summaries.append(
                {
                    "ca_id": ca.ca_id,
                    "name": ca.name,
                    "team": ca.team,
                    "target_leads": ca.target_leads,
                    "current_leads": ca.current_leads,
                    "segment_a_count": ca.performance.segment_a_count,
                    "segment_b_count": ca.performance.segment_b_count,
                    "segment_c_count": ca.performance.segment_c_count,
                    "segment_d_count": ca.performance.segment_d_count,
                    "target_expected_conversions": round(
                        ca.performance.target_expected_conversions, 2
                    ),
                    "current_expected_conversions": round(
                        ca.performance.current_expected_conversions, 2
                    ),
                    "achievement_rate": round(ca.performance.achievement_rate, 2),
                    "avg_conversion_rate": round(ca.performance.avg_conversion_rate, 2),
                    "status": ca.performance.status,
                }
            )
        return summaries

    def get_lead_allocation_suggestion(self, new_lead: Lead) -> List[Dict[str, Any]]:
        """新規リードの振り分け提案を取得"""
        # セグメント分類
        self.classifier.classify_lead(new_lead)

        suggestions = []
        for ca in self.cas.values():
            # 空き枠
            vacancy = ca.target_leads - ca.current_leads

            # スコア計算（空き枠が多く、達成率が低いCAを優先）
            score = vacancy * (1 - ca.performance.achievement_rate)

            suggestions.append(
                {
                    "ca_id": ca.ca_id,
                    "name": ca.name,
                    "team": ca.team,
                    "current_leads": ca.current_leads,
                    "target_leads": ca.target_leads,
                    "vacancy": vacancy,
                    "achievement_rate": round(ca.performance.achievement_rate, 2),
                    "score": round(score, 2),
                }
            )

        # スコア順にソート
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        return suggestions

    def generate_segment_report(self) -> str:
        """セグメント別レポートを生成"""
        summary = self.get_segment_summary()

        lines = [
            "=" * 60,
            "セグメント別期待展開率レポート",
            "=" * 60,
            "",
        ]

        total_leads = 0
        total_expected = 0.0

        for segment in SegmentType:
            data = summary[segment]
            count = data["count"]
            expected = data["expected_conversions"]
            rate = data["conversion_rate"]
            total_leads += count
            total_expected += expected

            segment_info = Segment.get_all_segments()
            seg_def = next((s for s in segment_info if s.segment_id == segment), None)
            name = seg_def.name if seg_def else segment.value

            lines.append(f"【セグメント {segment.value}: {name}】")
            lines.append(f"  条件: {'資格あり' if seg_def and seg_def.has_qualification else '資格なし'} & {seg_def.age_condition if seg_def else ''}")
            lines.append(f"  期待展開率: {rate:.0%}")
            lines.append(f"  保有リード数: {count}件")
            lines.append(f"  期待展開数: {expected:.2f}件")
            lines.append("")

        lines.append("-" * 60)
        lines.append(f"合計リード数: {total_leads}件")
        lines.append(f"合計期待展開数: {total_expected:.2f}件")
        if total_leads > 0:
            lines.append(f"平均期待展開率: {total_expected / total_leads:.1%}")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_ca_report(self) -> str:
        """CA別パフォーマンスレポートを生成"""
        lines = [
            "=" * 80,
            "CA別パフォーマンスレポート",
            "=" * 80,
            "",
        ]

        for ca in self.cas.values():
            perf = ca.performance
            status_label = {
                "on_track": "順調",
                "below_target": "要注意",
                "at_risk": "要対応",
            }.get(perf.status, perf.status)

            lines.append(f"【{ca.name}】({ca.ca_id}) - {ca.team}")
            lines.append(f"  ステータス: {status_label}")
            lines.append(
                f"  保有リード: {ca.current_leads}/{ca.target_leads}件 "
                f"(空き: {ca.target_leads - ca.current_leads}件)"
            )
            lines.append(
                f"  セグメント内訳: A={perf.segment_a_count}, B={perf.segment_b_count}, "
                f"C={perf.segment_c_count}, D={perf.segment_d_count}"
            )
            lines.append(
                f"  期待展開数: {perf.current_expected_conversions:.2f}/"
                f"{perf.target_expected_conversions:.2f}件"
            )
            lines.append(f"  達成率: {perf.achievement_rate:.1%}")
            lines.append(f"  平均展開率: {perf.avg_conversion_rate:.1%}")
            lines.append("")

        lines.append("=" * 80)
        return "\n".join(lines)

    def export_ca_summary_csv(self, output_path: Path) -> None:
        """CA別サマリーをCSVにエクスポート"""
        summaries = self.get_ca_summary()
        if not summaries:
            return

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=summaries[0].keys())
            writer.writeheader()
            writer.writerows(summaries)

    def export_leads_csv(self, output_path: Path) -> None:
        """リード一覧（セグメント付き）をCSVにエクスポート"""
        if not self.leads:
            return

        rows = []
        for lead in self.leads:
            rows.append(
                {
                    "lead_id": lead.lead_id,
                    "name": lead.name,
                    "age": lead.age,
                    "prefecture": lead.prefecture,
                    "qualification": lead.qualification,
                    "has_qualification": lead.has_qualification,
                    "assigned_ca_id": lead.assigned_ca_id,
                    "status": lead.status,
                    "segment_id": lead.segment_id.value if lead.segment_id else "",
                    "conversion_rate": lead.conversion_rate,
                    "created_at": lead.created_at,
                }
            )

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
