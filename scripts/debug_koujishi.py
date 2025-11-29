#!/usr/bin/env python3
"""
koujishi.comのページ構造を確認するデバッグスクリプト
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time

def main():
    print("koujishi.comのページ構造を確認中...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        
        # トップページにアクセス
        print("\n1. トップページを確認...")
        page.goto("https://koujishi.com/", wait_until="domcontentloaded")
        time.sleep(5)
        
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        # 検索リンクを探す
        search_links = soup.find_all("a", href=True)
        print(f"\nリンク数: {len(search_links)}")
        print("\n検索関連のリンク:")
        for link in search_links[:20]:
            href = link.get("href", "")
            text = link.get_text(strip=True)
            if "検索" in text or "search" in href.lower() or "求人" in text or "job" in href.lower():
                print(f"  - {text[:50]}: {href}")
        
        # 検索フォームを探す
        forms = soup.find_all("form")
        print(f"\nフォーム数: {len(forms)}")
        for form in forms:
            action = form.get("action", "")
            print(f"  フォームaction: {action}")
        
        # 検索ページに直接アクセス
        print("\n2. 検索ページを確認...")
        search_urls = [
            "https://koujishi.com/search?keyword=電気工事士",
            "https://koujishi.com/job/search?keyword=電気工事士",
            "https://koujishi.com/jobs?keyword=電気工事士",
        ]
        
        for url in search_urls:
            print(f"\n  {url} を試行...")
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=30000)
                time.sleep(5)
                
                html = page.content()
                soup = BeautifulSoup(html, "lxml")
                
                # ページタイトル
                title = soup.title.string if soup.title else "N/A"
                print(f"    ページタイトル: {title}")
                
                # 求人カードを探す
                job_cards = soup.find_all("div", class_=re.compile(r"job|card|item", re.I))
                print(f"    job/card/itemを含むdiv: {len(job_cards)}")
                
                # リンクを確認
                links = soup.find_all("a", href=True)
                job_links = [l for l in links if "job" in l.get("href", "").lower() or "detail" in l.get("href", "").lower()]
                print(f"    job/detailを含むリンク: {len(job_links)}")
                if job_links:
                    print(f"    最初のリンク: {job_links[0].get('href')}")
                
                # ページテキストの一部を表示
                text = soup.get_text()[:500]
                print(f"    ページテキスト（最初の500文字）: {text}")
                
                if len(job_cards) > 0 or len(job_links) > 0:
                    print(f"    ✓ このURLで求人が見つかりました！")
                    break
                    
            except Exception as e:
                print(f"    エラー: {e}")
                continue
        
        input("\nEnterキーを押すとブラウザを閉じます...")
        browser.close()

if __name__ == "__main__":
    import re
    main()

