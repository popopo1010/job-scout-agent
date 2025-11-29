"""セグメント自動分類ロジック"""

from __future__ import annotations

from typing import List

from .models import Lead, SegmentType, SEGMENT_CONVERSION_RATES


class SegmentClassifier:
    """リードのセグメント自動分類"""

    @staticmethod
    def assign_segment(has_qualification: bool, age: int) -> SegmentType:
        """
        資格有無×年齢からセグメントを自動判定

        Args:
            has_qualification: 電気工事士資格の有無
            age: 年齢

        Returns:
            SegmentType: 判定されたセグメント
        """
        if has_qualification:
            return SegmentType.A if age <= 40 else SegmentType.B
        else:
            return SegmentType.C if age <= 40 else SegmentType.D

    @staticmethod
    def get_conversion_rate(segment: SegmentType) -> float:
        """セグメントの期待展開率を取得"""
        return SEGMENT_CONVERSION_RATES.get(segment, 0.0)

    @classmethod
    def classify_lead(cls, lead: Lead) -> Lead:
        """
        リードにセグメントと期待展開率を設定

        Args:
            lead: 分類対象のリード

        Returns:
            Lead: セグメント情報が設定されたリード
        """
        lead.segment_id = cls.assign_segment(lead.has_qualification, lead.age)
        lead.conversion_rate = cls.get_conversion_rate(lead.segment_id)
        return lead

    @classmethod
    def classify_leads(cls, leads: List[Lead]) -> List[Lead]:
        """複数リードを一括分類"""
        return [cls.classify_lead(lead) for lead in leads]

    @staticmethod
    def get_segment_description(segment: SegmentType) -> str:
        """セグメントの説明を取得"""
        descriptions = {
            SegmentType.A: "資格あり若手（電気工事士資格あり & 40歳以下）- 期待展開率: 75%",
            SegmentType.B: "資格ありベテラン（電気工事士資格あり & 40歳超）- 期待展開率: 60%",
            SegmentType.C: "資格なし若手（電気工事士資格なし & 40歳以下）- 期待展開率: 40%",
            SegmentType.D: "資格なしシニア（電気工事士資格なし & 40歳超）- 期待展開率: 20%",
        }
        return descriptions.get(segment, "不明なセグメント")
