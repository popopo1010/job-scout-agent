"""求人比較・検出ロジック"""

from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional

from .models import (
    Company,
    MissingJobResult,
    NewAreaResult,
    NewCompanyResult,
    OwnedJob,
    SalaryInfo,
    SalaryType,
    ScrapedJob,
)
from .salary_converter import SalaryConverter


class JobComparator:
    """求人データの比較・検出エンジン"""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or Path("data/sample/job_data")
        self.scraped_jobs: List[ScrapedJob] = []
        self.owned_jobs: List[OwnedJob] = []
        self.companies: Dict[str, Company] = {}
        self.salary_converter = SalaryConverter()

    def _parse_salary_info(self, row: Dict[str, str]) -> SalaryInfo:
        """CSVの行から給与情報をパース"""

        def parse_int(val: str) -> Optional[int]:
            if val and val.strip():
                try:
                    return int(val)
                except ValueError:
                    return None
            return None

        def parse_float(val: str) -> Optional[float]:
            if val and val.strip():
                try:
                    return float(val)
                except ValueError:
                    return None
            return None

        salary_type_str = row.get("salary_type", "yearly").lower()
        salary_type = SalaryType(salary_type_str) if salary_type_str in [
            "yearly", "monthly", "daily"
        ] else SalaryType.YEARLY

        return SalaryInfo(
            salary_type=salary_type,
            daily_min=parse_int(row.get("daily_min", "")),
            daily_max=parse_int(row.get("daily_max", "")),
            monthly_min=parse_float(row.get("monthly_min", "")),
            monthly_max=parse_float(row.get("monthly_max", "")),
            yearly_min=parse_float(row.get("yearly_min", "")),
            yearly_max=parse_float(row.get("yearly_max", "")),
        )

    def load_scraped_jobs(self, filepath: Optional[Path] = None) -> List[ScrapedJob]:
        """スクレイピング求人を読み込み"""
        filepath = filepath or self.data_dir / "scraped_jobs.csv"

        jobs = []
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                salary = self._parse_salary_info(row)
                job = ScrapedJob(
                    scraped_id=row["scraped_id"],
                    source=row["source"],
                    source_id=row["source_id"],
                    company_name=row["company_name"],
                    prefecture=row["prefecture"],
                    city=row.get("city", ""),
                    title=row["title"],
                    qualification=row["qualification"],
                    salary=salary,
                    url=row.get("url", ""),
                    scraped_at=row.get("scraped_at", ""),
                )
                jobs.append(job)

        self.scraped_jobs = jobs
        return jobs

    def load_owned_jobs(self, filepath: Optional[Path] = None) -> List[OwnedJob]:
        """自社保有求人を読み込み"""
        filepath = filepath or self.data_dir / "owned_jobs.csv"

        jobs = []
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                salary = self._parse_salary_info(row)
                job = OwnedJob(
                    job_id=row["job_id"],
                    company_id=row["company_id"],
                    company_name=row["company_name"],
                    prefecture=row["prefecture"],
                    title=row["title"],
                    qualification=row["qualification"],
                    salary=salary,
                    is_active=row.get("is_active", "true").lower() == "true",
                )
                jobs.append(job)

        self.owned_jobs = jobs
        return jobs

    def load_companies(self, filepath: Optional[Path] = None) -> Dict[str, Company]:
        """保有法人を読み込み"""
        filepath = filepath or self.data_dir / "existing_companies.csv"

        companies = {}
        with open(filepath, encoding="utf-8") as f:
            reader = csv.DictReader(f)
            for row in reader:
                prefectures = [
                    p.strip() for p in row.get("covered_prefectures", "").split(",") if p.strip()
                ]
                company = Company(
                    company_id=row["company_id"],
                    company_name=row["company_name"],
                    covered_prefectures=prefectures,
                    has_relationship=row.get("has_relationship", "true").lower() == "true",
                    notes=row.get("notes", ""),
                )
                companies[company.company_name] = company

        self.companies = companies
        return companies

    def detect_new_companies(self) -> List[NewCompanyResult]:
        """新規法人を検出"""
        existing_names = set(self.companies.keys())

        # スクレイピング求人を会社名でグループ化
        company_jobs: Dict[str, List[ScrapedJob]] = defaultdict(list)
        for job in self.scraped_jobs:
            company_jobs[job.company_name].append(job)

        results = []
        for company_name, jobs in company_jobs.items():
            if company_name not in existing_names:
                prefectures = {job.prefecture for job in jobs}
                results.append(
                    NewCompanyResult(
                        company_name=company_name,
                        jobs=jobs,
                        prefectures=prefectures,
                    )
                )

        return results

    def detect_new_areas(self) -> List[NewAreaResult]:
        """既存法人の新規エリアを検出"""
        results = []

        # 既存法人名でスクレイピング求人をフィルタ
        for company_name, company in self.companies.items():
            existing_prefectures = set(company.covered_prefectures)
            scraped_in_company = [
                job for job in self.scraped_jobs if job.company_name == company_name
            ]

            if not scraped_in_company:
                continue

            scraped_prefectures = {job.prefecture for job in scraped_in_company}
            new_prefectures = scraped_prefectures - existing_prefectures

            if new_prefectures:
                new_area_jobs = [
                    job for job in scraped_in_company if job.prefecture in new_prefectures
                ]
                results.append(
                    NewAreaResult(
                        company_name=company_name,
                        existing_prefectures=company.covered_prefectures,
                        new_prefectures=new_prefectures,
                        jobs=new_area_jobs,
                    )
                )

        return results

    def detect_missing_jobs(self) -> List[MissingJobResult]:
        """不足求人を検出（自社が持っていない求人）"""
        # 自社保有求人を(会社名, 都道府県)でインデックス化
        owned_index: Dict[tuple, List[OwnedJob]] = defaultdict(list)
        for job in self.owned_jobs:
            owned_index[(job.company_name, job.prefecture)].append(job)

        results = []
        for scraped in self.scraped_jobs:
            key = (scraped.company_name, scraped.prefecture)

            # 既存法人のみチェック
            if scraped.company_name not in self.companies:
                continue

            owned_list = owned_index.get(key, [])

            if not owned_list:
                # 同エリアに自社求人がない
                results.append(
                    MissingJobResult(
                        company_name=scraped.company_name,
                        prefecture=scraped.prefecture,
                        scraped_job=scraped,
                    )
                )
            else:
                # 給与比較
                scraped_range = scraped.yearly_salary_range
                for owned in owned_list:
                    owned_range = owned.yearly_salary_range
                    if scraped_range[1] and owned_range[1]:
                        diff = scraped_range[1] - owned_range[1]
                        if diff > 50:  # 50万円以上高い場合は不足として記録
                            results.append(
                                MissingJobResult(
                                    company_name=scraped.company_name,
                                    prefecture=scraped.prefecture,
                                    scraped_job=scraped,
                                    owned_job=owned,
                                    salary_diff=diff,
                                )
                            )

        return results

    def get_prefecture_coverage(self) -> Dict[str, Dict[str, int]]:
        """都道府県別カバー率を取得"""
        coverage: Dict[str, Dict[str, int]] = defaultdict(lambda: {"scraped": 0, "owned": 0})

        for job in self.scraped_jobs:
            coverage[job.prefecture]["scraped"] += 1

        for job in self.owned_jobs:
            if job.is_active:
                coverage[job.prefecture]["owned"] += 1

        return dict(coverage)

    def generate_new_company_report(self) -> str:
        """新規法人レポートを生成"""
        new_companies = self.detect_new_companies()

        lines = [
            "=" * 60,
            "新規法人検出レポート",
            "=" * 60,
            "",
            f"検出数: {len(new_companies)}社",
            "",
        ]

        for i, result in enumerate(new_companies, 1):
            lines.append(f"【{i}. {result.company_name}】")
            lines.append(f"  求人数: {result.job_count}件")
            lines.append(f"  エリア: {', '.join(sorted(result.prefectures))}")

            # 給与レンジ
            salary_ranges = []
            for job in result.jobs:
                yr = job.yearly_salary_range
                if yr[0] or yr[1]:
                    salary_ranges.append(
                        SalaryConverter.format_salary_range(yr[0], yr[1])
                    )
            if salary_ranges:
                lines.append(f"  年収: {', '.join(set(salary_ranges))}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def generate_new_area_report(self) -> str:
        """既存法人・新規エリアレポートを生成"""
        new_areas = self.detect_new_areas()

        lines = [
            "=" * 60,
            "既存法人・新規エリア検出レポート",
            "=" * 60,
            "",
            f"検出数: {len(new_areas)}社",
            "",
        ]

        for i, result in enumerate(new_areas, 1):
            lines.append(f"【{i}. {result.company_name}】")
            lines.append(f"  既存エリア: {', '.join(result.existing_prefectures)}")
            lines.append(f"  新規エリア: {', '.join(sorted(result.new_prefectures))}")
            lines.append(f"  新規求人数: {len(result.jobs)}件")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def generate_coverage_report(self) -> str:
        """都道府県別カバー率レポートを生成"""
        coverage = self.get_prefecture_coverage()

        lines = [
            "=" * 60,
            "都道府県別カバー率レポート",
            "=" * 60,
            "",
            f"{'都道府県':<10} {'市場求人':>8} {'自社保有':>8} {'カバー率':>8}",
            "-" * 40,
        ]

        total_scraped = 0
        total_owned = 0

        for pref in sorted(coverage.keys()):
            data = coverage[pref]
            scraped = data["scraped"]
            owned = data["owned"]
            total_scraped += scraped
            total_owned += owned

            rate = owned / scraped * 100 if scraped > 0 else 0
            lines.append(f"{pref:<10} {scraped:>8}件 {owned:>8}件 {rate:>7.1f}%")

        lines.append("-" * 40)
        total_rate = total_owned / total_scraped * 100 if total_scraped > 0 else 0
        lines.append(f"{'合計':<10} {total_scraped:>8}件 {total_owned:>8}件 {total_rate:>7.1f}%")
        lines.append("=" * 60)

        return "\n".join(lines)

    def generate_full_report(self) -> str:
        """全レポートを生成"""
        reports = [
            self.generate_new_company_report(),
            "",
            self.generate_new_area_report(),
            "",
            self.generate_coverage_report(),
        ]
        return "\n".join(reports)

    def export_new_companies_csv(self, output_path: Path) -> None:
        """新規法人リストをCSVにエクスポート"""
        new_companies = self.detect_new_companies()

        rows = []
        for result in new_companies:
            for job in result.jobs:
                yr = job.yearly_salary_range
                rows.append(
                    {
                        "company_name": result.company_name,
                        "prefecture": job.prefecture,
                        "city": job.city,
                        "title": job.title,
                        "qualification": job.qualification,
                        "yearly_min": yr[0],
                        "yearly_max": yr[1],
                        "source": job.source,
                        "url": job.url,
                    }
                )

        if rows:
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)

    def export_new_areas_csv(self, output_path: Path) -> None:
        """新規エリアリストをCSVにエクスポート"""
        new_areas = self.detect_new_areas()

        rows = []
        for result in new_areas:
            for job in result.jobs:
                yr = job.yearly_salary_range
                rows.append(
                    {
                        "company_name": result.company_name,
                        "existing_prefectures": ",".join(result.existing_prefectures),
                        "new_prefecture": job.prefecture,
                        "title": job.title,
                        "yearly_min": yr[0],
                        "yearly_max": yr[1],
                        "source": job.source,
                        "url": job.url,
                    }
                )

        if rows:
            with open(output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=rows[0].keys())
                writer.writeheader()
                writer.writerows(rows)
