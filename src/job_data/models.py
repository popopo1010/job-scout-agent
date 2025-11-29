"""求人データ整備のデータモデル"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import List, Optional, Set, Tuple


class SalaryType(str, Enum):
    """給与種別"""

    YEARLY = "yearly"
    MONTHLY = "monthly"
    DAILY = "daily"


@dataclass
class SalaryInfo:
    """給与情報"""

    salary_type: SalaryType
    daily_min: Optional[int] = None
    daily_max: Optional[int] = None
    monthly_min: Optional[float] = None  # 万円
    monthly_max: Optional[float] = None  # 万円
    yearly_min: Optional[float] = None  # 万円
    yearly_max: Optional[float] = None  # 万円

    def get_yearly_range(self) -> Tuple[Optional[float], Optional[float]]:
        """年収レンジを取得（日給・月給は換算）"""
        if self.yearly_min is not None or self.yearly_max is not None:
            return (self.yearly_min, self.yearly_max)

        if self.monthly_min is not None or self.monthly_max is not None:
            min_val = self.monthly_min * 12 if self.monthly_min else None
            max_val = self.monthly_max * 12 if self.monthly_max else None
            return (min_val, max_val)

        if self.daily_min is not None or self.daily_max is not None:
            # 日給 × 240日（年間稼働日数）/ 10000（万円換算）
            min_val = self.daily_min * 240 / 10000 if self.daily_min else None
            max_val = self.daily_max * 240 / 10000 if self.daily_max else None
            return (min_val, max_val)

        return (None, None)


@dataclass
class ScrapedJob:
    """スクレイピングした求人"""

    scraped_id: str
    source: str
    source_id: str
    company_name: str
    prefecture: str
    city: str
    title: str
    qualification: str
    salary: SalaryInfo
    url: str
    scraped_at: str
    phone_number: Optional[str] = None  # 人事向け電話番号

    @property
    def yearly_salary_range(self) -> Tuple[Optional[float], Optional[float]]:
        """年収レンジを取得"""
        return self.salary.get_yearly_range()


@dataclass
class OwnedJob:
    """自社保有求人"""

    job_id: str
    company_id: str
    company_name: str
    prefecture: str
    title: str
    qualification: str
    salary: SalaryInfo
    is_active: bool = True

    @property
    def yearly_salary_range(self) -> Tuple[Optional[float], Optional[float]]:
        """年収レンジを取得"""
        return self.salary.get_yearly_range()


@dataclass
class Company:
    """保有法人"""

    company_id: str
    company_name: str
    covered_prefectures: List[str] = field(default_factory=list)
    has_relationship: bool = True
    notes: str = ""


@dataclass
class NewCompanyResult:
    """新規法人検出結果"""

    company_name: str
    jobs: List[ScrapedJob] = field(default_factory=list)
    prefectures: Set[str] = field(default_factory=set)

    @property
    def job_count(self) -> int:
        return len(self.jobs)


@dataclass
class NewAreaResult:
    """既存法人・新規エリア検出結果"""

    company_name: str
    existing_prefectures: List[str] = field(default_factory=list)
    new_prefectures: Set[str] = field(default_factory=set)
    jobs: List[ScrapedJob] = field(default_factory=list)


@dataclass
class MissingJobResult:
    """不足求人検出結果"""

    company_name: str
    prefecture: str
    scraped_job: ScrapedJob
    owned_job: Optional[OwnedJob] = None
    salary_diff: Optional[float] = None  # 年収差（万円）
