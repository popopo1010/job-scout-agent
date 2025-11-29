"""経営分析基盤のデータモデル"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Literal, Optional


class SegmentType(str, Enum):
    """セグメント種別（4分類）"""

    A = "A"  # 資格あり & 40歳以下
    B = "B"  # 資格あり & 40歳超
    C = "C"  # 資格なし & 40歳以下
    D = "D"  # 資格なし & 40歳超


# セグメント別期待展開率
SEGMENT_CONVERSION_RATES: Dict[SegmentType, float] = {
    SegmentType.A: 0.75,
    SegmentType.B: 0.60,
    SegmentType.C: 0.40,
    SegmentType.D: 0.20,
}

# セグメント優先度（1が最高）
SEGMENT_PRIORITY: Dict[SegmentType, int] = {
    SegmentType.A: 1,
    SegmentType.B: 2,
    SegmentType.C: 3,
    SegmentType.D: 4,
}


@dataclass
class Segment:
    """セグメント定義"""

    segment_id: SegmentType
    name: str
    has_qualification: bool
    age_condition: str
    conversion_rate: float
    priority: int

    @classmethod
    def get_all_segments(cls) -> List[Segment]:
        """全セグメント定義を取得"""
        return [
            cls(
                segment_id=SegmentType.A,
                name="資格あり若手",
                has_qualification=True,
                age_condition="40歳以下",
                conversion_rate=0.75,
                priority=1,
            ),
            cls(
                segment_id=SegmentType.B,
                name="資格ありベテラン",
                has_qualification=True,
                age_condition="40歳超",
                conversion_rate=0.60,
                priority=2,
            ),
            cls(
                segment_id=SegmentType.C,
                name="資格なし若手",
                has_qualification=False,
                age_condition="40歳以下",
                conversion_rate=0.40,
                priority=3,
            ),
            cls(
                segment_id=SegmentType.D,
                name="資格なしシニア",
                has_qualification=False,
                age_condition="40歳超",
                conversion_rate=0.20,
                priority=4,
            ),
        ]


@dataclass
class Lead:
    """リード（見込み顧客）"""

    lead_id: str
    name: str
    age: int
    prefecture: str
    qualification: str
    has_qualification: bool
    assigned_ca_id: str
    status: str
    segment_id: Optional[SegmentType] = None
    conversion_rate: Optional[float] = None
    created_at: str = ""

    def __post_init__(self) -> None:
        """セグメントと期待展開率を自動設定"""
        if self.segment_id is None:
            self.segment_id = self._calculate_segment()
        if self.conversion_rate is None:
            self.conversion_rate = SEGMENT_CONVERSION_RATES.get(self.segment_id, 0.0)

    def _calculate_segment(self) -> SegmentType:
        """資格有無×年齢からセグメントを自動判定"""
        if self.has_qualification:
            return SegmentType.A if self.age <= 40 else SegmentType.B
        else:
            return SegmentType.C if self.age <= 40 else SegmentType.D


StatusType = Literal["on_track", "below_target", "at_risk"]


@dataclass
class CAPerformance:
    """CAパフォーマンス指標"""

    segment_a_count: int = 0
    segment_b_count: int = 0
    segment_c_count: int = 0
    segment_d_count: int = 0
    target_expected_conversions: float = 0.0
    current_expected_conversions: float = 0.0
    achievement_rate: float = 0.0
    avg_conversion_rate: float = 0.0
    status: StatusType = "on_track"

    @property
    def total_leads(self) -> int:
        """合計保有リード数"""
        return (
            self.segment_a_count
            + self.segment_b_count
            + self.segment_c_count
            + self.segment_d_count
        )


@dataclass
class CA:
    """キャリアアドバイザー"""

    ca_id: str
    name: str
    team: str
    slack_user_id: str
    target_leads: int
    current_leads: int = 0
    performance: CAPerformance = field(default_factory=CAPerformance)
    leads: List[Lead] = field(default_factory=list)

    def calculate_performance(self) -> None:
        """保有リードからパフォーマンス指標を再計算"""
        counts = {SegmentType.A: 0, SegmentType.B: 0, SegmentType.C: 0, SegmentType.D: 0}

        for lead in self.leads:
            if lead.segment_id:
                counts[lead.segment_id] += 1

        self.performance.segment_a_count = counts[SegmentType.A]
        self.performance.segment_b_count = counts[SegmentType.B]
        self.performance.segment_c_count = counts[SegmentType.C]
        self.performance.segment_d_count = counts[SegmentType.D]
        self.current_leads = self.performance.total_leads

        # 期待展開数を計算
        self.performance.current_expected_conversions = sum(
            lead.conversion_rate or 0.0 for lead in self.leads
        )

        # 目標期待展開数（目標リード数 × 平均展開率0.5を想定）
        # 実際には目標に対する期待値を設定する必要がある
        self.performance.target_expected_conversions = self.target_leads * 0.5

        # 達成率
        if self.performance.target_expected_conversions > 0:
            self.performance.achievement_rate = (
                self.performance.current_expected_conversions
                / self.performance.target_expected_conversions
            )
        else:
            self.performance.achievement_rate = 0.0

        # 平均展開率
        if self.current_leads > 0:
            self.performance.avg_conversion_rate = (
                self.performance.current_expected_conversions / self.current_leads
            )
        else:
            self.performance.avg_conversion_rate = 0.0

        # ステータス判定
        if self.performance.achievement_rate >= 0.8:
            self.performance.status = "on_track"
        elif self.performance.achievement_rate >= 0.5:
            self.performance.status = "below_target"
        else:
            self.performance.status = "at_risk"
