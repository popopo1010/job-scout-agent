#!/usr/bin/env python3
"""
koujishi.comの実際の求人カードHTMLを確認するデバッグスクリプト
"""

import sys
from pathlib import Path

project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from playwright.sync_api import sync_playwright
from bs4 import BeautifulSoup
import time
import re

def main():
    print("koujishi.comの実際の求人カードHTMLを確認中...")
    
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=False)
        context = browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        page = context.new_page()
        
        url = "https://koujishi.com/search?keyword=電気工事士"
        print(f"\n{url} にアクセス...")
        page.goto(url, wait_until="domcontentloaded")
        time.sleep(5)
        
        # ページをスクロール
        page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
        time.sleep(2)
        
        html = page.content()
        soup = BeautifulSoup(html, "lxml")
        
        # すべてのdivを確認
        all_divs = soup.find_all("div")
        print(f"\n全div数: {len(all_divs)}")
        
        # 求人らしいdivを探す
        job_like_divs = []
        for div in all_divs:
            div_text = div.get_text(strip=True)
            div_class = div.get("class", [])
            div_id = div.get("id", "")
            
            # 求人らしい内容を含むdiv
            if any(keyword in div_text for keyword in ["電気", "工事", "給", "万円", "株式会社"]):
                if not any(exclude in div_text for exclude in ["閲覧履歴", "気になる", "会員登録", "ログイン"]):
                    if len(div_text) > 50 and len(div_text) < 2000:  # 適切な長さ
                        job_like_divs.append((div, div_text[:200], div_class, div_id))
        
        print(f"\n求人らしいdiv: {len(job_like_divs)}件")
        for i, (div, text, cls, div_id) in enumerate(job_like_divs[:5], 1):
            print(f"\n[{i}]")
            print(f"  クラス: {cls}")
            print(f"  ID: {div_id}")
            print(f"  テキスト（最初の200文字）: {text}")
            print(f"  HTML（最初の500文字）: {str(div)[:500]}")
        
        # リンクを確認
        links = soup.find_all("a", href=True)
        job_links = []
        for link in links:
            href = link.get("href", "")
            if re.search(r"/list/\d+|/job/\d+|/detail/\d+", href):
                if "view" not in href.lower() and "history" not in href.lower():
                    job_links.append((link, href, link.get_text(strip=True)[:100]))
        
        print(f"\n求人詳細へのリンク: {len(job_links)}件")
        for i, (link, href, text) in enumerate(job_links[:5], 1):
            print(f"\n[{i}]")
            print(f"  URL: {href}")
            print(f"  テキスト: {text}")
            # 親要素を確認
            parent = link.parent
            depth = 0
            while parent and depth < 3:
                if parent.name in ["div", "article", "li"]:
                    print(f"  親要素[{depth}]: {parent.name}, クラス: {parent.get('class', [])}")
                parent = parent.parent
                depth += 1
        
        print("\n5秒後にブラウザを閉じます...")
        time.sleep(5)
        browser.close()

if __name__ == "__main__":
    main()

