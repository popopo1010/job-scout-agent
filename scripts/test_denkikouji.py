#!/usr/bin/env python3
"""
電気工事.comのスクレイパーの動作確認用テストスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.job_data.playwright_scrapers import (
    PlaywrightDenkikoujiComScraper,
    PlaywrightScrapingOptions,
)


def main():
    """テスト実行"""
    print("=" * 70)
    print("電気工事.com スクレイパー動作確認")
    print("=" * 70)
    print()

    # スクレイピングオプション（テスト用に少なめに設定）
    scraping_options = PlaywrightScrapingOptions(
        max_pages=5,  # 最大5ページ
        delay=3.0,
        timeout=60000.0,
        headless=False,  # ブラウザを表示して確認
    )

    keyword = "電気工事士"
    max_results = 50  # テスト用に50件まで

    try:
        with PlaywrightDenkikoujiComScraper(options=scraping_options) as scraper:
            jobs = scraper.search_jobs(
                keyword=keyword,
                area="",
                max_results=max_results,
            )
            
            print()
            print("=" * 70)
            print(f"取得結果: {len(jobs)}件")
            print("=" * 70)
            
            if jobs:
                print("\n取得した求人のサンプル（最初の5件）:")
                for i, job in enumerate(jobs[:5], 1):
                    print(f"\n[{i}]")
                    print(f"  会社名: {job.get('company_name', 'N/A')}")
                    print(f"  タイトル: {job.get('title', 'N/A')}")
                    print(f"  場所: {job.get('prefecture', '')} {job.get('city', '')}")
                    print(f"  URL: {job.get('url', 'N/A')}")
            else:
                print("\n求人が取得できませんでした。")
                print("URLやセレクタを確認してください。")
                
    except Exception as e:
        print(f"\nエラー: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

