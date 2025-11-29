#!/usr/bin/env python3
"""サンプルデータを使ったデモスクリプト"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root / "src"))

from analytics import AnalyticsEngine
from job_data import JobComparator


def demo_analytics() -> None:
    """経営分析基盤のデモ"""
    print("\n" + "=" * 80)
    print("経営分析基盤 デモ")
    print("=" * 80 + "\n")

    data_dir = project_root / "data" / "sample" / "analytics"
    engine = AnalyticsEngine(data_dir)

    # データ読み込み
    print("データ読み込み中...")
    leads = engine.load_leads_from_csv()
    cas = engine.load_cas_from_csv()
    engine.assign_leads_to_cas()

    print(f"  リード数: {len(leads)}件")
    print(f"  CA数: {len(cas)}名\n")

    # セグメント別レポート
    print(engine.generate_segment_report())
    print()

    # CA別レポート
    print(engine.generate_ca_report())


def demo_job_data() -> None:
    """求人データ整備のデモ"""
    print("\n" + "=" * 80)
    print("求人データ整備 デモ")
    print("=" * 80 + "\n")

    data_dir = project_root / "data" / "sample" / "job_data"
    comparator = JobComparator(data_dir)

    # データ読み込み
    print("データ読み込み中...")
    scraped = comparator.load_scraped_jobs()
    owned = comparator.load_owned_jobs()
    companies = comparator.load_companies()

    print(f"  スクレイピング求人数: {len(scraped)}件")
    print(f"  自社保有求人数: {len(owned)}件")
    print(f"  保有法人数: {len(companies)}社\n")

    # 全レポート出力
    print(comparator.generate_full_report())


def main() -> None:
    """メイン処理"""
    print("\n" + "#" * 80)
    print("#  人材紹介事業AIエージェントシステム - サンプルデータデモ")
    print("#" * 80)

    demo_analytics()
    demo_job_data()

    print("\n" + "#" * 80)
    print("#  デモ完了")
    print("#" * 80 + "\n")


if __name__ == "__main__":
    main()
