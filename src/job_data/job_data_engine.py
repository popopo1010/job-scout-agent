"""求人データ整備エンジン（統合クラス）"""

from pathlib import Path
from typing import Optional

from .models import ScrapedJob, OwnedJob, Company
from .job_comparator import JobComparator
from .salary_converter import SalaryConverter


class JobDataEngine:
    """求人データ整備の統合エンジン"""

    def __init__(self, data_dir: Optional[Path] = None) -> None:
        self.data_dir = data_dir or Path("data/sample/job_data")
        self.comparator = JobComparator(data_dir=self.data_dir)
        self.salary_converter = SalaryConverter()

    @property
    def scraped_jobs(self) -> list[ScrapedJob]:
        return self.comparator.scraped_jobs

    @property
    def owned_jobs(self) -> list[OwnedJob]:
        return self.comparator.owned_jobs

    @property
    def existing_companies(self) -> dict[str, Company]:
        return self.comparator.companies

    def load_all_data(self) -> None:
        """全データを読み込み"""
        self.comparator.load_scraped_jobs()
        self.comparator.load_owned_jobs()
        self.comparator.load_companies()

    def generate_new_companies_report(self) -> str:
        """新規法人検出レポート"""
        return self.comparator.generate_new_company_report()

    def generate_new_areas_report(self) -> str:
        """新規エリア検出レポート"""
        return self.comparator.generate_new_area_report()

    def generate_coverage_report(self) -> str:
        """カバー率レポート"""
        return self.comparator.generate_coverage_report()

    def generate_salary_comparison_report(self) -> str:
        """給与比較レポート"""
        lines = [
            "=" * 70,
            "給与比較レポート（自社 vs 市場）",
            "=" * 70,
            "",
        ]

        # 会社名×都道府県で比較
        comparisons = []
        for owned in self.owned_jobs:
            key = (owned.company_name, owned.prefecture)
            owned_range = owned.yearly_salary_range

            # 同じ会社・同じエリアのスクレイピング求人を検索
            matched_scraped = [
                s for s in self.scraped_jobs
                if s.company_name == owned.company_name and s.prefecture == owned.prefecture
            ]

            for scraped in matched_scraped:
                scraped_range = scraped.yearly_salary_range

                if owned_range[1] and scraped_range[1]:
                    diff = scraped_range[1] - owned_range[1]
                    comparisons.append({
                        "company": owned.company_name,
                        "prefecture": owned.prefecture,
                        "owned_min": owned_range[0],
                        "owned_max": owned_range[1],
                        "scraped_min": scraped_range[0],
                        "scraped_max": scraped_range[1],
                        "diff": diff,
                    })

        if not comparisons:
            lines.append("比較可能なデータがありません")
        else:
            # 差分が大きい順にソート
            comparisons.sort(key=lambda x: x["diff"], reverse=True)

            lines.append(f"{'法人名':<20} {'エリア':<8} {'自社年収':>12} {'市場年収':>12} {'差額':>8}")
            lines.append("-" * 65)

            for c in comparisons[:10]:  # 上位10件
                owned_str = f"{c['owned_min'] or '?'}〜{c['owned_max'] or '?'}万"
                scraped_str = f"{c['scraped_min'] or '?'}〜{c['scraped_max'] or '?'}万"
                diff_str = f"+{c['diff']:.0f}万" if c['diff'] > 0 else f"{c['diff']:.0f}万"
                lines.append(
                    f"{c['company'][:18]:<20} {c['prefecture']:<8} {owned_str:>12} {scraped_str:>12} {diff_str:>8}"
                )

        lines.append("")
        lines.append("=" * 70)
        return "\n".join(lines)

    def generate_full_report(self) -> str:
        """全レポートを生成"""
        reports = [
            self.generate_new_companies_report(),
            "",
            self.generate_new_areas_report(),
            "",
            self.generate_coverage_report(),
            "",
            self.generate_salary_comparison_report(),
        ]
        return "\n".join(reports)

    def export_all(self, output_dir: Path) -> None:
        """全データをエクスポート"""
        output_dir.mkdir(parents=True, exist_ok=True)

        # 新規法人CSV
        self.comparator.export_new_companies_csv(output_dir / "new_companies.csv")

        # 新規エリアCSV
        self.comparator.export_new_areas_csv(output_dir / "new_areas.csv")

        # フルレポート
        report_path = output_dir / "job_data_report.txt"
        report_path.write_text(self.generate_full_report(), encoding="utf-8")
