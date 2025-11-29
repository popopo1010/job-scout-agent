"""スクレイピングエンジン

スクレイパーとジョブコンパレーターを統合し、
求人スクレイピング → 比較分析 → レポート生成の一連のワークフローを管理する。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

from .models import ScrapedJob, Company, SalaryInfo, SalaryType
from .scraper import JobScraper, ScrapingResult, ScrapingConfig
from .job_comparator import JobComparator


@dataclass
class ScrapingWorkflowResult:
    """スクレイピングワークフローの実行結果"""

    scraping_result: ScrapingResult
    new_companies: List[str] = field(default_factory=list)
    new_areas: Dict[str, List[str]] = field(default_factory=dict)
    high_salary_jobs: List[ScrapedJob] = field(default_factory=list)
    csv_path: Optional[Path] = None
    report_path: Optional[Path] = None
    executed_at: str = ""

    def __post_init__(self) -> None:
        if not self.executed_at:
            self.executed_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")


class ScrapingEngine:
    """スクレイピングエンジン

    Web検索から取得した求人データを処理し、
    自社保有データと比較して新規法人・新規エリアを検出する。
    """

    def __init__(
        self,
        output_dir: Optional[Path] = None,
        companies_file: Optional[Path] = None,
    ) -> None:
        self.output_dir = output_dir or Path("data/exports/scraped")
        self.scraper = JobScraper(output_dir=self.output_dir)
        self.comparator = JobComparator()
        self.companies_file = companies_file

        # 既存法人データをロード
        if companies_file and companies_file.exists():
            self.comparator.load_companies(companies_file)

    def process_scraped_data(
        self,
        jobs_data: List[Dict[str, Any]],
        source: str,
        source_urls: List[str],
        search_keyword: str = "",
        search_area: str = "",
    ) -> ScrapingResult:
        """スクレイピングデータを処理してScrapingResultを生成

        Args:
            jobs_data: LLMが収集した求人データのリスト（辞書形式）
            source: データソース名（rikunabi_next, indeed など）
            source_urls: 取得元URLのリスト
            search_keyword: 検索キーワード
            search_area: 検索エリア

        Returns:
            ScrapingResult: 構造化されたスクレイピング結果
        """
        jobs = []
        for i, data in enumerate(jobs_data, 1):
            # scraped_idが未設定の場合は自動生成
            if not data.get("scraped_id"):
                prefix = source[:2].upper()
                data["scraped_id"] = f"{prefix}{i:03d}"

            job = self.scraper.create_job_from_dict(data, source)
            jobs.append(job)

        result = ScrapingResult(
            jobs=jobs,
            source=source,
            source_urls=source_urls,
            search_keyword=search_keyword,
            search_area=search_area,
        )

        return result

    def analyze_result(
        self,
        result: ScrapingResult,
        high_salary_threshold: float = 500,
    ) -> ScrapingWorkflowResult:
        """スクレイピング結果を分析

        Args:
            result: スクレイピング結果
            high_salary_threshold: 高年収の閾値（万円）

        Returns:
            ScrapingWorkflowResult: 分析結果
        """
        # スクレイピング求人をコンパレーターに設定
        self.comparator.scraped_jobs = result.jobs

        # 新規法人を検出
        new_company_results = self.comparator.detect_new_companies()
        new_companies = [r.company_name for r in new_company_results]

        # 新規エリアを検出
        new_area_results = self.comparator.detect_new_areas()
        new_areas = {
            r.company_name: list(r.new_prefectures)
            for r in new_area_results
        }

        # 高年収求人を抽出
        high_salary_jobs = []
        for job in result.jobs:
            yearly_range = job.yearly_salary_range
            if yearly_range[1] and yearly_range[1] >= high_salary_threshold:
                high_salary_jobs.append(job)

        return ScrapingWorkflowResult(
            scraping_result=result,
            new_companies=new_companies,
            new_areas=new_areas,
            high_salary_jobs=high_salary_jobs,
        )

    def save_results(
        self,
        workflow_result: ScrapingWorkflowResult,
        save_csv: bool = True,
        save_report: bool = True,
    ) -> ScrapingWorkflowResult:
        """結果を保存

        Args:
            workflow_result: ワークフロー結果
            save_csv: CSVを保存するか
            save_report: レポートを保存するか

        Returns:
            ScrapingWorkflowResult: パス情報が追加された結果
        """
        result = workflow_result.scraping_result

        if save_csv:
            workflow_result.csv_path = self.scraper.save_to_csv(result)

        if save_report:
            workflow_result.report_path = self.scraper.save_report(result)

        return workflow_result

    def run_workflow(
        self,
        jobs_data: List[Dict[str, Any]],
        source: str,
        source_urls: List[str],
        search_keyword: str = "",
        search_area: str = "",
        high_salary_threshold: float = 500,
        save_csv: bool = True,
        save_report: bool = True,
    ) -> ScrapingWorkflowResult:
        """スクレイピングワークフローを実行

        Args:
            jobs_data: 求人データのリスト
            source: データソース名
            source_urls: 取得元URLリスト
            search_keyword: 検索キーワード
            search_area: 検索エリア
            high_salary_threshold: 高年収の閾値（万円）
            save_csv: CSVを保存するか
            save_report: レポートを保存するか

        Returns:
            ScrapingWorkflowResult: ワークフロー実行結果
        """
        # 1. データ処理
        scraping_result = self.process_scraped_data(
            jobs_data=jobs_data,
            source=source,
            source_urls=source_urls,
            search_keyword=search_keyword,
            search_area=search_area,
        )

        # 2. 分析
        workflow_result = self.analyze_result(
            result=scraping_result,
            high_salary_threshold=high_salary_threshold,
        )

        # 3. 保存
        workflow_result = self.save_results(
            workflow_result=workflow_result,
            save_csv=save_csv,
            save_report=save_report,
        )

        return workflow_result

    def generate_analysis_report(
        self,
        workflow_result: ScrapingWorkflowResult,
    ) -> str:
        """分析レポートを生成

        Args:
            workflow_result: ワークフロー結果

        Returns:
            str: レポート文字列
        """
        result = workflow_result.scraping_result
        lines = [
            "=" * 70,
            "求人スクレイピング分析レポート",
            "=" * 70,
            f"実行日時: {workflow_result.executed_at}",
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

        # 新規法人
        lines.extend([
            "",
            "■ 自社保有法人との照合結果",
            "-" * 70,
            f"新規法人: {len(workflow_result.new_companies)}社",
        ])

        if workflow_result.new_companies:
            for i, company in enumerate(workflow_result.new_companies, 1):
                lines.append(f"  {i}. {company}")

        # 新規エリア
        lines.extend([
            "",
            f"既存法人・新規エリア: {len(workflow_result.new_areas)}社",
        ])

        for company, areas in workflow_result.new_areas.items():
            lines.append(f"  - {company}: {', '.join(areas)}")

        # 高年収求人
        lines.extend([
            "",
            f"■ 注目求人（年収{500}万円以上）",
            "-" * 70,
        ])

        if workflow_result.high_salary_jobs:
            for i, job in enumerate(workflow_result.high_salary_jobs, 1):
                yr = job.yearly_salary_range
                salary_str = f"{yr[0] or '?'}〜{yr[1] or '?'}万円"
                lines.append(f"{i}. {job.company_name}（{job.city or job.prefecture}）")
                lines.append(f"   年収: {salary_str}")
                lines.append(f"   資格: {job.qualification}")
                if job.url:
                    lines.append(f"   URL: {job.url}")
                lines.append("")
        else:
            lines.append("該当なし")

        # ファイル情報
        if workflow_result.csv_path or workflow_result.report_path:
            lines.extend([
                "",
                "■ 出力ファイル",
                "-" * 70,
            ])
            if workflow_result.csv_path:
                lines.append(f"CSV: {workflow_result.csv_path}")
            if workflow_result.report_path:
                lines.append(f"レポート: {workflow_result.report_path}")

        lines.extend([
            "",
            "=" * 70,
        ])

        return "\n".join(lines)

    def get_source_config(self, source: str) -> Optional[ScrapingConfig]:
        """ソース設定を取得"""
        return self.scraper.SOURCES.get(source)

    def list_available_sources(self) -> List[str]:
        """利用可能なソース一覧を取得"""
        return list(self.scraper.SOURCES.keys())
