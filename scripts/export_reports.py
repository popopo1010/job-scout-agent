#!/usr/bin/env python3
"""レポートをファイルに出力するスクリプト"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from analytics import AnalyticsEngine
from job_data import JobComparator


def export_analytics_reports(export_dir: Path) -> None:
    """経営分析基盤のレポートを出力"""
    print("経営分析基盤レポートを出力中...")

    data_dir = project_root / "data" / "sample" / "analytics"
    engine = AnalyticsEngine(data_dir)

    # データ読み込み
    engine.load_leads_from_csv()
    engine.load_cas_from_csv()
    engine.assign_leads_to_cas()

    # セグメント別レポート（テキスト）
    segment_report = engine.generate_segment_report()
    segment_file = export_dir / "segment_report.txt"
    with open(segment_file, "w", encoding="utf-8") as f:
        f.write(segment_report)
    print(f"  -> {segment_file}")

    # CA別レポート（テキスト）
    ca_report = engine.generate_ca_report()
    ca_report_file = export_dir / "ca_performance_report.txt"
    with open(ca_report_file, "w", encoding="utf-8") as f:
        f.write(ca_report)
    print(f"  -> {ca_report_file}")

    # CA別サマリー（CSV）
    ca_csv_file = export_dir / "ca_summary.csv"
    engine.export_ca_summary_csv(ca_csv_file)
    print(f"  -> {ca_csv_file}")

    # リード一覧（CSV）
    leads_csv_file = export_dir / "leads_with_segments.csv"
    engine.export_leads_csv(leads_csv_file)
    print(f"  -> {leads_csv_file}")


def export_job_data_reports(export_dir: Path) -> None:
    """求人データ整備のレポートを出力"""
    print("\n求人データ整備レポートを出力中...")

    data_dir = project_root / "data" / "sample" / "job_data"
    comparator = JobComparator(data_dir)

    # データ読み込み
    comparator.load_scraped_jobs()
    comparator.load_owned_jobs()
    comparator.load_companies()

    # 新規法人レポート（テキスト）
    new_company_report = comparator.generate_new_company_report()
    new_company_txt = export_dir / "new_companies_report.txt"
    with open(new_company_txt, "w", encoding="utf-8") as f:
        f.write(new_company_report)
    print(f"  -> {new_company_txt}")

    # 新規法人リスト（CSV）
    new_company_csv = export_dir / "new_companies.csv"
    comparator.export_new_companies_csv(new_company_csv)
    print(f"  -> {new_company_csv}")

    # 新規エリアレポート（テキスト）
    new_area_report = comparator.generate_new_area_report()
    new_area_txt = export_dir / "new_areas_report.txt"
    with open(new_area_txt, "w", encoding="utf-8") as f:
        f.write(new_area_report)
    print(f"  -> {new_area_txt}")

    # 新規エリアリスト（CSV）
    new_area_csv = export_dir / "new_areas.csv"
    comparator.export_new_areas_csv(new_area_csv)
    print(f"  -> {new_area_csv}")

    # 都道府県別カバー率レポート（テキスト）
    coverage_report = comparator.generate_coverage_report()
    coverage_file = export_dir / "prefecture_coverage_report.txt"
    with open(coverage_file, "w", encoding="utf-8") as f:
        f.write(coverage_report)
    print(f"  -> {coverage_file}")


def main() -> None:
    """メイン処理"""
    export_dir = project_root / "data" / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 60)
    print("レポート出力開始")
    print(f"出力先: {export_dir}")
    print("=" * 60)

    export_analytics_reports(export_dir)
    export_job_data_reports(export_dir)

    print("\n" + "=" * 60)
    print("レポート出力完了")
    print("=" * 60)


if __name__ == "__main__":
    main()
