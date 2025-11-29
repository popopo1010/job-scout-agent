"""求人スクレイピングモジュール

Web検索を使用して求人情報を収集する。
実際のスクレイピングはLLM（Claude）が実行し、結果を構造化データとして返す。
"""

from __future__ import annotations

import csv
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import List, Optional, Dict, Any

from .models import ScrapedJob, SalaryInfo, SalaryType


@dataclass
class ScrapingResult:
    """スクレイピング結果"""

    jobs: List[ScrapedJob] = field(default_factory=list)
    source: str = ""
    source_urls: List[str] = field(default_factory=list)
    search_keyword: str = ""
    search_area: str = ""
    scraped_at: str = ""
    total_count: int = 0

    def __post_init__(self) -> None:
        if not self.scraped_at:
            self.scraped_at = datetime.now().strftime("%Y-%m-%d")
        self.total_count = len(self.jobs)


@dataclass
class ScrapingConfig:
    """スクレイピング設定"""

    source: str  # rikunabi_next, indeed, hellowork など
    base_url: str
    search_keywords: List[str] = field(default_factory=lambda: ["電気工事士"])
    search_areas: List[str] = field(default_factory=lambda: ["東京都"])
    max_pages: int = 3


class JobScraper:
    """求人スクレイパー

    LLMが収集した求人データを構造化して保存する。
    実際のWeb検索・データ収集はLLMが実行する。
    """

    # 対応ソースの設定
    SOURCES: Dict[str, ScrapingConfig] = {
        "rikunabi_next": ScrapingConfig(
            source="rikunabi_next",
            base_url="https://next.rikunabi.com/",
            search_keywords=["電気工事士", "第一種電気工事士", "第二種電気工事士"],
            search_areas=["東京都", "神奈川県", "大阪府"],
        ),
        "indeed": ScrapingConfig(
            source="indeed",
            base_url="https://jp.indeed.com/",
            search_keywords=["電気工事士"],
            search_areas=["東京都"],
        ),
        "hellowork": ScrapingConfig(
            source="hellowork",
            base_url="https://www.hellowork.mhlw.go.jp/",
            search_keywords=["電気工事士"],
            search_areas=["東京都"],
        ),
    }

    def __init__(self, output_dir: Optional[Path] = None) -> None:
        self.output_dir = output_dir or Path("data/exports/scraped")
        self.results: List[ScrapingResult] = []

    def _parse_float(self, value: Any) -> Optional[float]:
        """値をfloatに変換（空文字列やNoneはNoneを返す）"""
        if value is None or value == "":
            return None
        try:
            return float(value)
        except (ValueError, TypeError):
            return None

    def _parse_int(self, value: Any) -> Optional[int]:
        """値をintに変換（空文字列やNoneはNoneを返す）"""
        if value is None or value == "":
            return None
        try:
            return int(float(value))
        except (ValueError, TypeError):
            return None

    def create_job_from_dict(self, data: Dict[str, Any], source: str) -> ScrapedJob:
        """辞書データからScrapedJobを生成"""
        # 給与情報の解析
        salary_type_str = str(data.get("salary_type", "monthly")).lower()
        if salary_type_str == "yearly":
            salary_type = SalaryType.YEARLY
        elif salary_type_str == "daily":
            salary_type = SalaryType.DAILY
        else:
            salary_type = SalaryType.MONTHLY

        salary = SalaryInfo(
            salary_type=salary_type,
            daily_min=self._parse_int(data.get("daily_min")),
            daily_max=self._parse_int(data.get("daily_max")),
            monthly_min=self._parse_float(data.get("monthly_min")),
            monthly_max=self._parse_float(data.get("monthly_max")),
            yearly_min=self._parse_float(data.get("yearly_min")),
            yearly_max=self._parse_float(data.get("yearly_max")),
        )

        return ScrapedJob(
            scraped_id=data.get("scraped_id", ""),
            source=source,
            source_id=data.get("source_id", ""),
            company_name=data.get("company_name", ""),
            prefecture=data.get("prefecture", ""),
            city=data.get("city", ""),
            title=data.get("title", ""),
            qualification=data.get("qualification", ""),
            salary=salary,
            url=data.get("url", ""),
            scraped_at=data.get("scraped_at", datetime.now().strftime("%Y-%m-%d")),
        )

    def add_result(self, result: ScrapingResult) -> None:
        """スクレイピング結果を追加"""
        self.results.append(result)

    def save_to_csv(self, result: ScrapingResult, filename: Optional[str] = None) -> Path:
        """結果をCSVに保存"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not filename:
            filename = f"{result.source}_{result.search_keyword}_{result.scraped_at}.csv"

        filepath = self.output_dir / filename

        rows = []
        for job in result.jobs:
            yearly_range = job.yearly_salary_range
            rows.append({
                "scraped_id": job.scraped_id,
                "source": job.source,
                "company_name": job.company_name,
                "prefecture": job.prefecture,
                "city": job.city,
                "title": job.title,
                "qualification": job.qualification,
                "salary_type": job.salary.salary_type.value,
                "monthly_min": job.salary.monthly_min,
                "monthly_max": job.salary.monthly_max,
                "yearly_min": yearly_range[0],
                "yearly_max": yearly_range[1],
                "url": job.url,
                "scraped_at": job.scraped_at,
            })

        if rows:
            with open(filepath, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

        return filepath

    def generate_report(self, result: ScrapingResult) -> str:
        """スクレイピング結果のレポートを生成"""
        lines = [
            "=" * 70,
            "求人スクレイピングレポート",
            "=" * 70,
            f"実行日時: {result.scraped_at}",
            f"データソース: {result.source}",
            f"検索キーワード: {result.search_keyword}",
            f"対象エリア: {result.search_area}",
            "=" * 70,
            "",
            "■ 収集サマリー",
            "-" * 70,
            f"取得件数: {result.total_count}件",
            "",
            "データソースURL:",
        ]

        for url in result.source_urls:
            lines.append(f"  - {url}")

        # 資格別内訳
        qual_counts: Dict[str, int] = {}
        for job in result.jobs:
            qual = job.qualification or "不明"
            qual_counts[qual] = qual_counts.get(qual, 0) + 1

        lines.extend([
            "",
            "■ 資格別内訳",
            "-" * 70,
        ])
        for qual, count in sorted(qual_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {qual}: {count}件")

        # エリア別内訳
        area_counts: Dict[str, int] = {}
        for job in result.jobs:
            area = job.city or job.prefecture or "不明"
            area_counts[area] = area_counts.get(area, 0) + 1

        lines.extend([
            "",
            "■ エリア別内訳",
            "-" * 70,
        ])
        for area, count in sorted(area_counts.items(), key=lambda x: -x[1]):
            lines.append(f"  {area}: {count}件")

        # 給与分析
        yearly_mins = []
        yearly_maxs = []
        for job in result.jobs:
            yr = job.yearly_salary_range
            if yr[0]:
                yearly_mins.append(yr[0])
            if yr[1]:
                yearly_maxs.append(yr[1])

        lines.extend([
            "",
            "■ 給与レンジ分析（年収換算・万円）",
            "-" * 70,
        ])

        if yearly_mins:
            lines.append(f"最低年収: {min(yearly_mins):.0f}万円")
        if yearly_maxs:
            lines.append(f"最高年収: {max(yearly_maxs):.0f}万円")
        if yearly_mins:
            lines.append(f"平均年収（下限）: {sum(yearly_mins) / len(yearly_mins):.0f}万円")
        if yearly_maxs:
            lines.append(f"平均年収（上限）: {sum(yearly_maxs) / len(yearly_maxs):.0f}万円")

        # 求人一覧
        lines.extend([
            "",
            "■ 収集求人一覧",
            "-" * 70,
            f"{'No.':<4} {'会社名':<30} {'エリア':<15} {'年収（万円）'}",
            "-" * 70,
        ])

        for i, job in enumerate(result.jobs, 1):
            yr = job.yearly_salary_range
            salary_str = f"{yr[0] or '?'}〜{yr[1] or '?'}"
            lines.append(f"{i:02d}. {job.company_name[:28]:<30} {job.city or job.prefecture:<15} {salary_str}")

        lines.extend([
            "",
            "=" * 70,
            f"レポート生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 70,
        ])

        return "\n".join(lines)

    def save_report(self, result: ScrapingResult, filename: Optional[str] = None) -> Path:
        """レポートをファイルに保存"""
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if not filename:
            filename = f"scraping_report_{result.scraped_at}.txt"

        filepath = self.output_dir / filename
        report = self.generate_report(result)
        filepath.write_text(report, encoding="utf-8")

        return filepath

    def load_from_csv(self, filepath: Path) -> ScrapingResult:
        """CSVからスクレイピング結果を読み込み"""
        jobs = []

        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                job = self.create_job_from_dict(row, row.get("source", "unknown"))
                jobs.append(job)

        # ファイル名からメタデータを推測
        stem = filepath.stem
        parts = stem.split("_")
        source = parts[0] if parts else "unknown"

        return ScrapingResult(
            jobs=jobs,
            source=source,
            source_urls=[],
            search_keyword="電気工事士",
            search_area="東京都",
        )
