#!/usr/bin/env python3
"""スクレイピングデモスクリプト

スクレイピングエンジンの動作を確認するためのデモ。
事前に収集されたサンプルデータを使用して、
スクレイピング→比較分析→レポート生成のワークフローを実行する。
"""

from pathlib import Path
import sys

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.job_data import ScrapingEngine, ScrapingWorkflowResult


def main() -> None:
    """デモを実行"""
    print("=" * 70)
    print("求人スクレイピングデモ")
    print("=" * 70)
    print()

    # サンプルデータ（実際のスクレイピングで収集した形式）
    sample_jobs = [
        {
            "scraped_id": "RN001",
            "company_name": "有限会社片桐電気工事",
            "prefecture": "東京都",
            "city": "新宿区",
            "title": "電気工事士",
            "qualification": "第二種電気工事士",
            "salary_type": "yearly",
            "yearly_min": 360,
            "yearly_max": 450,
            "url": "https://next.rikunabi.com/job_search/area-tokyo/kw/第二種電気工事士/",
        },
        {
            "scraped_id": "RN002",
            "company_name": "三井物産フォーサイト株式会社",
            "prefecture": "東京都",
            "city": "千代田区大手町",
            "title": "電気設備管理",
            "qualification": "第二種電気工事士",
            "salary_type": "monthly",
            "monthly_min": 30,
            "monthly_max": 37.5,
            "url": "https://next.rikunabi.com/job_search/area-tokyo/kw/第二種電気工事士/",
        },
        {
            "scraped_id": "RN003",
            "company_name": "日本通信機工業株式会社",
            "prefecture": "東京都",
            "city": "千代田区神田佐久間町",
            "title": "電気通信工事士",
            "qualification": "第二種電気工事士",
            "salary_type": "monthly",
            "monthly_min": 33,
            "monthly_max": 48,
            "url": "https://next.rikunabi.com/job_search/area-tokyo/kw/第二種電気工事士/",
        },
        {
            "scraped_id": "RN004",
            "company_name": "株式会社Ｙ２エナジーグループ",
            "prefecture": "東京都",
            "city": "渋谷区幡ヶ谷",
            "title": "電気工事士",
            "qualification": "第二種電気工事士",
            "salary_type": "monthly",
            "monthly_min": 25,
            "monthly_max": 100,
            "url": "https://next.rikunabi.com/job_search/area-tokyo/kw/第二種電気工事士/",
        },
        {
            "scraped_id": "RN005",
            "company_name": "株式会社野村総合研究所",
            "prefecture": "東京都",
            "city": "千代田区大手町",
            "title": "電気設備管理",
            "qualification": "第二種電気工事士",
            "salary_type": "monthly",
            "monthly_min": 40.5,
            "monthly_max": 89,
            "url": "https://next.rikunabi.com/job_search/sal-over700/kw/第二種電気工事士/",
        },
    ]

    source_urls = [
        "https://next.rikunabi.com/job_search/area-tokyo/kw/第二種電気工事士/",
        "https://next.rikunabi.com/job_search/kw/第一種電気工事士/",
        "https://next.rikunabi.com/job_search/sal-over700/kw/第二種電気工事士/",
    ]

    # スクレイピングエンジンを初期化
    output_dir = project_root / "data" / "exports" / "scraped"
    engine = ScrapingEngine(output_dir=output_dir)

    print("利用可能なソース:", engine.list_available_sources())
    print()

    # ワークフローを実行
    print("■ ワークフロー実行中...")
    print()

    result = engine.run_workflow(
        jobs_data=sample_jobs,
        source="rikunabi_next",
        source_urls=source_urls,
        search_keyword="電気工事士",
        search_area="東京都",
        high_salary_threshold=500,
        save_csv=False,  # デモでは保存しない
        save_report=False,
    )

    # 分析レポートを表示
    report = engine.generate_analysis_report(result)
    print(report)

    # サマリー
    print()
    print("■ 実行結果サマリー")
    print("-" * 70)
    print(f"取得求人数: {result.scraping_result.total_count}件")
    print(f"新規法人数: {len(result.new_companies)}社")
    print(f"新規エリア検出: {len(result.new_areas)}社")
    print(f"高年収求人数: {len(result.high_salary_jobs)}件")
    print()

    if result.new_companies:
        print("新規法人リスト:")
        for company in result.new_companies:
            print(f"  - {company}")
        print()

    if result.high_salary_jobs:
        print("高年収求人（500万円以上）:")
        for job in result.high_salary_jobs:
            yr = job.yearly_salary_range
            print(f"  - {job.company_name}: {yr[0]}〜{yr[1]}万円")
        print()

    print("=" * 70)
    print("デモ完了")
    print("=" * 70)


if __name__ == "__main__":
    main()
