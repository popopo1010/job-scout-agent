#!/usr/bin/env python3
"""
IndeedとRikunabi Nextから電気工事士の求人をすべてスクレイピングし、
電話番号をリサーチしてデータを蓄積するスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from typing import List, Dict, Any, Optional

from src.job_data.playwright_scrapers import (
    PlaywrightIndeedScraper,
    PlaywrightRikunabiNextScraper,
    PlaywrightScrapingOptions,
)
from src.job_data.phone_researcher import PhoneResearcher
from src.job_data.scraping_engine import ScrapingEngine
from src.job_data.models import ScrapedJob


def progress_callback(company_name: str, phone_number: Optional[str], status: str, completed: int, total: int) -> None:
    """進捗コールバック"""
    print(f"[{completed}/{total}] {company_name}: {phone_number or '見つからず'} ({status})")


def main() -> None:
    """メイン処理"""
    print("=" * 70)
    print("電気工事士求人スクレイピング & 電話番号リサーチ")
    print("=" * 70)
    print()

    # 設定
    keyword = "電気工事士"
    max_results = 5000  # 最大取得件数（各ソース）- 全件取得を目指す
    output_dir = project_root / "data" / "exports" / "scraped"
    output_dir.mkdir(parents=True, exist_ok=True)

    all_jobs_data: List[Dict[str, Any]] = []
    all_source_urls: List[str] = []

    # スクレイピングオプション
    scraping_options = PlaywrightScrapingOptions(
        max_pages=50,  # 最大50ページ
        delay=2.0,  # 2秒間隔
        timeout=30000.0,  # 30秒
        headless=True,  # ヘッドレスモード
    )

    # 1. Indeedからスクレイピング（Playwright使用）
    print("■ Indeedからスクレイピング中（Playwright）...")
    print()
    try:
        with PlaywrightIndeedScraper(options=scraping_options) as indeed_scraper:
            indeed_jobs = indeed_scraper.search_jobs(
                keyword=keyword,
                location="",  # 全国
                max_results=max_results,
            )
            all_jobs_data.extend(indeed_jobs)
            all_source_urls.append("https://jp.indeed.com/")
            print(f"Indeed: {len(indeed_jobs)}件の求人を取得しました")
            print()
    except Exception as e:
        print(f"Indeedスクレイピングエラー: {e}")
        import traceback
        traceback.print_exc()

    # 2. Rikunabi Nextからスクレイピング（Playwright使用）
    print("■ Rikunabi Nextからスクレイピング中（Playwright）...")
    print()
    try:
        with PlaywrightRikunabiNextScraper(options=scraping_options) as rikunabi_scraper:
            rikunabi_jobs = rikunabi_scraper.search_jobs(
                keyword=keyword,
                area="",  # 全国
                max_results=max_results,
            )
            all_jobs_data.extend(rikunabi_jobs)
            all_source_urls.append("https://next.rikunabi.com/")
            print(f"Rikunabi Next: {len(rikunabi_jobs)}件の求人を取得しました")
            print()
    except Exception as e:
        print(f"Rikunabi Nextスクレイピングエラー: {e}")
        import traceback
        traceback.print_exc()

    print(f"合計: {len(all_jobs_data)}件の求人を取得しました")
    print()

    if not all_jobs_data:
        print("スクレイピングした求人がありません。")
        return

    # 3. 電話番号リサーチ（並列処理）
    print("=" * 70)
    print("■ 電話番号リサーチ中（並列処理）...")
    print("=" * 70)
    print()

    # 会社名のリストを取得（重複除去）
    company_names = list(set(job.get("company_name", "") for job in all_jobs_data if job.get("company_name")))

    print(f"対象会社数: {len(company_names)}社")
    print()

    phone_researcher = PhoneResearcher(max_workers=10, timeout=30.0, delay=0.5)
    phone_numbers = phone_researcher.research_phones(company_names, progress_callback=progress_callback)

    print()
    print(f"電話番号取得: {sum(1 for v in phone_numbers.values() if v)}/{len(company_names)}社")
    print()

    # 4. 電話番号を求人データに追加
    print("■ 電話番号を求人データに追加中...")
    for job_data in all_jobs_data:
        company_name = job_data.get("company_name", "")
        if company_name in phone_numbers:
            job_data["phone_number"] = phone_numbers[company_name]

    # 5. データを正規化して保存
    print("=" * 70)
    print("■ データを正規化して保存中...")
    print("=" * 70)
    print()

    # スクレイピングエンジンを初期化
    engine = ScrapingEngine(output_dir=output_dir)

    # データを処理
    results = []
    for i, job_data in enumerate(all_jobs_data, 1):
        # scraped_idが未設定の場合は自動生成
        if not job_data.get("scraped_id"):
            source = job_data.get("source", "UNKNOWN")
            prefix = source[:2].upper() if len(source) >= 2 else "UN"
            job_data["scraped_id"] = f"{prefix}{i:04d}"

        # ソースを設定
        if "indeed" in job_data.get("url", "").lower():
            job_data["source"] = "indeed"
        elif "rikunabi" in job_data.get("url", "").lower():
            job_data["source"] = "rikunabi_next"
        else:
            job_data["source"] = job_data.get("source", "unknown")

    # ワークフローを実行
    workflow_result = engine.run_workflow(
        jobs_data=all_jobs_data,
        source="combined",
        source_urls=all_source_urls,
        search_keyword=keyword,
        search_area="全国",
        high_salary_threshold=500,
        save_csv=True,
        save_report=True,
    )

    # 6. 結果を表示
    print("=" * 70)
    print("スクレイピング完了")
    print("=" * 70)
    print()
    print(f"取得件数: {workflow_result.scraping_result.total_count}件")
    print(f"新規法人: {len(workflow_result.new_companies)}社")
    print(f"既存法人・新規エリア: {len(workflow_result.new_areas)}社")
    print()

    if workflow_result.csv_path:
        print(f"CSV保存先: {workflow_result.csv_path}")
    if workflow_result.report_path:
        print(f"レポート保存先: {workflow_result.report_path}")
    print()

    # 電話番号付き求人の統計
    jobs_with_phone = sum(1 for job_data in all_jobs_data if job_data.get("phone_number"))
    print(f"電話番号取得済み: {jobs_with_phone}/{len(all_jobs_data)}件 ({jobs_with_phone/len(all_jobs_data)*100:.1f}%)")
    print()

    # 分析レポートを表示
    analysis_report = engine.generate_analysis_report(workflow_result)
    print(analysis_report)

    print()
    print("=" * 70)
    print("完了")
    print("=" * 70)


if __name__ == "__main__":
    main()

