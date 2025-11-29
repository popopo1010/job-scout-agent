#!/usr/bin/env python3
"""スクレイピング統合デモスクリプト

実際に収集したスクレイピングデータを既存の法人データと照合し、
新規法人・新規エリアの検出を行う統合デモ。
"""

from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.job_data import ScrapingEngine, JobScraper


def main() -> None:
    """統合デモを実行"""
    print("=" * 70)
    print("求人スクレイピング統合デモ")
    print("=" * 70)
    print()

    # パス設定
    output_dir = project_root / "data" / "exports" / "scraped"
    companies_file = project_root / "data" / "sample" / "job_data" / "existing_companies.csv"
    scraped_csv = output_dir / "rikunabi_next_電気工事士_2025-11-29.csv"

    # 既存法人データが存在するか確認
    if not companies_file.exists():
        print(f"警告: 既存法人データが見つかりません: {companies_file}")
        print("サンプルデータを使用して実行します。")
        companies_file = None

    # スクレイピングエンジンを初期化（既存法人データをロード）
    engine = ScrapingEngine(
        output_dir=output_dir,
        companies_file=companies_file,
    )

    print(f"既存法人数: {len(engine.comparator.companies)}社")
    if engine.comparator.companies:
        print("既存法人リスト:")
        for name in list(engine.comparator.companies.keys())[:5]:
            company = engine.comparator.companies[name]
            print(f"  - {name} ({', '.join(company.covered_prefectures)})")
        if len(engine.comparator.companies) > 5:
            print(f"  ... 他 {len(engine.comparator.companies) - 5}社")
    print()

    # 収集済みCSVからデータをロード
    if scraped_csv.exists():
        print(f"収集済みデータをロード: {scraped_csv}")
        scraper = JobScraper(output_dir=output_dir)
        scraping_result = scraper.load_from_csv(scraped_csv)

        # ソースURLを設定（CSVには保存されないため手動で追加）
        scraping_result.source_urls = [
            "https://next.rikunabi.com/job_search/area-tokyo/kw/第二種電気工事士/",
            "https://next.rikunabi.com/job_search/kw/第一種電気工事士/",
            "https://next.rikunabi.com/job_search/kw/第2種電気工事士/",
            "https://next.rikunabi.com/job_search/sal-over700/kw/第二種電気工事士/",
        ]
        scraping_result.search_keyword = "電気工事士"
        scraping_result.search_area = "東京都"
        scraping_result.source = "リクナビNEXT"

        print(f"ロード完了: {scraping_result.total_count}件")
        print()
    else:
        print(f"収集済みデータが見つかりません: {scraped_csv}")
        print("デモデータを使用します。")

        # デモデータを使用
        demo_jobs = [
            {
                "company_name": "東京電気工事株式会社",  # 既存法人
                "prefecture": "東京都",
                "city": "中央区",
                "title": "電気工事士",
                "qualification": "第二種電気工事士",
                "salary_type": "monthly",
                "monthly_min": 35,
                "monthly_max": 50,
            },
            {
                "company_name": "東京電気工事株式会社",  # 既存法人・新規エリア
                "prefecture": "千葉県",
                "city": "千葉市",
                "title": "電気工事士",
                "qualification": "第二種電気工事士",
                "salary_type": "monthly",
                "monthly_min": 32,
                "monthly_max": 45,
            },
            {
                "company_name": "新規電設株式会社",  # 新規法人
                "prefecture": "東京都",
                "city": "新宿区",
                "title": "電気工事士",
                "qualification": "第一種電気工事士",
                "salary_type": "yearly",
                "yearly_min": 500,
                "yearly_max": 800,
            },
        ]

        scraping_result = engine.process_scraped_data(
            jobs_data=demo_jobs,
            source="demo",
            source_urls=["デモデータ"],
            search_keyword="電気工事士",
            search_area="東京都",
        )
        print(f"デモデータ生成完了: {scraping_result.total_count}件")
        print()

    # 分析実行
    print("■ 分析実行中...")
    print("-" * 70)

    workflow_result = engine.analyze_result(
        result=scraping_result,
        high_salary_threshold=500,
    )

    # 分析レポートを表示
    report = engine.generate_analysis_report(workflow_result)
    print(report)

    # 詳細サマリー
    print()
    print("■ 詳細サマリー")
    print("=" * 70)

    # 資格別集計
    qual_counts = {}
    for job in scraping_result.jobs:
        qual = job.qualification or "不明"
        qual_counts[qual] = qual_counts.get(qual, 0) + 1

    print()
    print("資格別求人数:")
    for qual, count in sorted(qual_counts.items(), key=lambda x: -x[1]):
        print(f"  {qual}: {count}件")

    # 年収帯別集計
    salary_bands = {
        "300万円未満": 0,
        "300〜400万円": 0,
        "400〜500万円": 0,
        "500〜600万円": 0,
        "600万円以上": 0,
    }

    for job in scraping_result.jobs:
        yr = job.yearly_salary_range
        if yr[0]:
            if yr[0] < 300:
                salary_bands["300万円未満"] += 1
            elif yr[0] < 400:
                salary_bands["300〜400万円"] += 1
            elif yr[0] < 500:
                salary_bands["400〜500万円"] += 1
            elif yr[0] < 600:
                salary_bands["500〜600万円"] += 1
            else:
                salary_bands["600万円以上"] += 1

    print()
    print("年収帯別分布:")
    for band, count in salary_bands.items():
        print(f"  {band}: {count}件")

    print()
    print("=" * 70)
    print("統合デモ完了")
    print("=" * 70)


if __name__ == "__main__":
    main()
