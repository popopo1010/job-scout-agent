#!/usr/bin/env python3
"""
デモモード: サンプルデータを使って電話番号リサーチ機能をテスト
実際のスクレイピングが困難な場合に使用
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from datetime import datetime
from typing import List, Dict, Any, Optional

from src.job_data.phone_researcher import PhoneResearcher
from src.job_data.scraping_engine import ScrapingEngine


def progress_callback(company_name: str, phone_number: Optional[str], status: str, completed: int, total: int) -> None:
    """進捗コールバック"""
    print(f"[{completed}/{total}] {company_name}: {phone_number or '見つからず'} ({status})")


def main() -> None:
    """メイン処理"""
    print("=" * 70)
    print("電気工事士求人スクレイピング & 電話番号リサーチ（デモモード）")
    print("=" * 70)
    print()

    # サンプル求人データ（実際のスクレイピングが困難な場合の代替）
    sample_jobs_data: List[Dict[str, Any]] = [
        {
            "scraped_id": "ID001",
            "source_id": "abc123",
            "company_name": "株式会社東京電気工事",
            "prefecture": "東京都",
            "city": "千代田区",
            "title": "電気工事士",
            "qualification": "第一種電気工事士",
            "salary_type": "monthly",
            "monthly_min": 30.0,
            "monthly_max": 50.0,
            "url": "https://jp.indeed.com/viewjob?jk=abc123",
            "scraped_at": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "scraped_id": "RN001",
            "source_id": "xyz789",
            "company_name": "関西電設株式会社",
            "prefecture": "大阪府",
            "city": "大阪市",
            "title": "電気工事士",
            "qualification": "第二種電気工事士",
            "salary_type": "yearly",
            "yearly_min": 400.0,
            "yearly_max": 600.0,
            "url": "https://next.rikunabi.com/job/xyz789",
            "scraped_at": datetime.now().strftime("%Y-%m-%d"),
        },
        {
            "scraped_id": "ID002",
            "source_id": "def456",
            "company_name": "中部エンジニアリング株式会社",
            "prefecture": "愛知県",
            "city": "名古屋市",
            "title": "電気工事士",
            "qualification": "第一種電気工事士",
            "salary_type": "monthly",
            "monthly_min": 35.0,
            "monthly_max": 55.0,
            "url": "https://jp.indeed.com/viewjob?jk=def456",
            "scraped_at": datetime.now().strftime("%Y-%m-%d"),
        },
    ]

    output_dir = project_root / "data" / "exports" / "scraped"
    output_dir.mkdir(parents=True, exist_ok=True)

    print(f"サンプル求人数: {len(sample_jobs_data)}件")
    print()

    # 電話番号リサーチ（並列処理）
    print("=" * 70)
    print("■ 電話番号リサーチ中（並列処理）...")
    print("=" * 70)
    print()

    # 会社名のリストを取得（重複除去）
    company_names = list(set(job.get("company_name", "") for job in sample_jobs_data if job.get("company_name")))

    print(f"対象会社数: {len(company_names)}社")
    print()

    phone_researcher = PhoneResearcher(max_workers=10, timeout=30.0, delay=0.5)
    phone_numbers = phone_researcher.research_phones(company_names, progress_callback=progress_callback)

    print()
    print(f"電話番号取得: {sum(1 for v in phone_numbers.values() if v)}/{len(company_names)}社")
    print()

    # 電話番号を求人データに追加
    print("■ 電話番号を求人データに追加中...")
    for job_data in sample_jobs_data:
        company_name = job_data.get("company_name", "")
        if company_name in phone_numbers:
            job_data["phone_number"] = phone_numbers[company_name]

    # データを正規化して保存
    print("=" * 70)
    print("■ データを正規化して保存中...")
    print("=" * 70)
    print()

    # スクレイピングエンジンを初期化
    engine = ScrapingEngine(output_dir=output_dir)

    # ワークフローを実行
    workflow_result = engine.run_workflow(
        jobs_data=sample_jobs_data,
        source="demo",
        source_urls=["デモデータ"],
        search_keyword="電気工事士",
        search_area="全国",
        high_salary_threshold=500,
        save_csv=True,
        save_report=True,
    )

    # 結果を表示
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
    jobs_with_phone = sum(1 for job_data in sample_jobs_data if job_data.get("phone_number"))
    print(f"電話番号取得済み: {jobs_with_phone}/{len(sample_jobs_data)}件 ({jobs_with_phone/len(sample_jobs_data)*100:.1f}%)")
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

