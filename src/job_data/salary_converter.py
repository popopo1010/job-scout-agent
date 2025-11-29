"""給与換算ロジック"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from .models import SalaryInfo, SalaryType


class SalaryConverter:
    """給与の換算処理"""

    # 年間稼働日数（日給→年収換算用）
    WORKING_DAYS_PER_YEAR = 240

    @classmethod
    def daily_to_yearly(cls, daily_wage: int) -> float:
        """
        日給を年収に換算（万円）

        Args:
            daily_wage: 日給（円）

        Returns:
            年収（万円）
        """
        return daily_wage * cls.WORKING_DAYS_PER_YEAR / 10000

    @staticmethod
    def monthly_to_yearly(monthly_wage: float) -> float:
        """
        月給を年収に換算（万円）

        Args:
            monthly_wage: 月給（万円）

        Returns:
            年収（万円）
        """
        return monthly_wage * 12

    @classmethod
    def to_yearly_range(cls, salary: SalaryInfo) -> Tuple[Optional[float], Optional[float]]:
        """
        SalaryInfoを年収レンジに変換

        Args:
            salary: 給与情報

        Returns:
            (最低年収, 最高年収) タプル（万円）
        """
        return salary.get_yearly_range()

    @classmethod
    def compare_salaries(
        cls,
        salary1: SalaryInfo,
        salary2: SalaryInfo,
    ) -> Dict[str, Optional[float]]:
        """
        2つの給与を比較（年収ベース）

        Args:
            salary1: 給与1
            salary2: 給与2

        Returns:
            比較結果のdict
        """
        range1 = salary1.get_yearly_range()
        range2 = salary2.get_yearly_range()

        result: Dict[str, Optional[float]] = {
            "salary1_min": range1[0],
            "salary1_max": range1[1],
            "salary2_min": range2[0],
            "salary2_max": range2[1],
            "min_diff": None,
            "max_diff": None,
        }

        if range1[0] is not None and range2[0] is not None:
            result["min_diff"] = range1[0] - range2[0]

        if range1[1] is not None and range2[1] is not None:
            result["max_diff"] = range1[1] - range2[1]

        return result

    @staticmethod
    def format_salary_range(
        min_val: Optional[float], max_val: Optional[float], unit: str = "万円"
    ) -> str:
        """給与レンジを文字列にフォーマット"""
        if min_val is None and max_val is None:
            return "不明"
        if min_val is None:
            return f"〜{max_val:.0f}{unit}"
        if max_val is None:
            return f"{min_val:.0f}{unit}〜"
        if min_val == max_val:
            return f"{min_val:.0f}{unit}"
        return f"{min_val:.0f}〜{max_val:.0f}{unit}"
