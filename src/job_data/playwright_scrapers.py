"""Playwrightを使ったWebスクレイパー実装

IndeedとRikunabi Nextから実際に求人情報をスクレイピングする。
ブラウザ自動化によりボット検出を回避。
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any

from playwright.sync_api import sync_playwright, Page, Browser, BrowserContext
from bs4 import BeautifulSoup

from .models import ScrapedJob, SalaryInfo, SalaryType


@dataclass
class PlaywrightScrapingOptions:
    """Playwrightスクレイピングオプション"""

    max_pages: int = 500  # 最大ページ数（全件取得を目指す）
    delay: float = 2.0  # リクエスト間の遅延（秒）
    timeout: float = 30000.0  # タイムアウト（ミリ秒）
    headless: bool = True  # ヘッドレスモード
    wait_for_selector: str = ""  # 待機するセレクタ


class PlaywrightIndeedScraper:
    """Playwrightを使ったIndeedスクレイパー"""

    BASE_URL = "https://jp.indeed.com"

    def __init__(self, options: Optional[PlaywrightScrapingOptions] = None) -> None:
        self.options = options or PlaywrightScrapingOptions()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    def __enter__(self):
        """コンテキストマネージャーとして使用"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=self.options.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        )
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """クリーンアップ"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def search_jobs(
        self,
        keyword: str = "電気工事士",
        location: str = "",
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """求人を検索してスクレイピング

        Args:
            keyword: 検索キーワード
            location: 場所（都道府県など）
            max_results: 最大取得件数

        Returns:
            求人データのリスト
        """
        if not self.context:
            raise RuntimeError("コンテキストが初期化されていません。with文で使用してください。")

        jobs = []
        page = self.context.new_page()

        try:
            # 検索URLを構築
            from urllib.parse import quote
            params = {
                "q": keyword,
                "l": location,
            }
            url = f"{self.BASE_URL}/jobs?" + "&".join(f"{k}={quote(str(v))}" for k, v in params.items() if v)

            print(f"Indeed: {url} を取得中...")

            # ページにアクセス
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=int(self.options.timeout * 2))
            except Exception as e:
                print(f"  ページ読み込みエラー: {e}")
                try:
                    page.reload(wait_until="domcontentloaded", timeout=int(self.options.timeout * 2))
                except:
                    pass
            time.sleep(8)  # ページの読み込みを待つ
            
            # Cloudflareの検証ページか確認
            page_content = page.content()
            if "Just a moment" in page_content or "Cloudflare" in page_content:
                print("  Cloudflare検証を待機中...（最大30秒）")
                for i in range(6):  # 最大30秒待つ
                    time.sleep(5)
                    page.reload(wait_until="domcontentloaded", timeout=int(self.options.timeout))
                    page_content = page.content()
                    if "Just a moment" not in page_content and "Cloudflare" not in page_content:
                        print("  Cloudflare検証が完了しました")
                        break
                else:
                    print("  Cloudflare検証がタイムアウトしました。続行します...")

            page_num = 0
            consecutive_empty = 0  # 連続して求人が見つからない回数
            seen_job_ids = set()  # 重複チェック用

            while len(jobs) < max_results and page_num < self.options.max_pages:
                page_num += 1
                print(f"\n  ページ {page_num} を処理中...")

                # ページのHTMLを取得してBeautifulSoupでパース
                html = page.content()
                soup = BeautifulSoup(html, "lxml")

                # 求人カードを取得（複数のセレクタを試す）
                job_cards = soup.find_all("a", {"data-jk": True})
                if not job_cards:
                    job_cards = soup.find_all("div", class_="job_seen_beacon")
                if not job_cards:
                    job_cards = soup.find_all("h2", class_="jobTitle")

                if not job_cards:
                    # デバッグ: ページの内容を確認
                    page_text = soup.get_text()[:500] if soup else ""
                    print(f"  求人が見つかりませんでした。")
                    print(f"  ページテキスト（最初の500文字）: {page_text}")
                    
                    # ページタイトルを確認
                    title = soup.title.string if soup.title else "N/A"
                    print(f"  ページタイトル: {title}")
                    
                    # リンクを確認
                    all_links = soup.find_all("a", href=True)
                    print(f"  ページ内のリンク数: {len(all_links)}")
                    
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        print("  連続して求人が見つかりませんでした。終了します。")
                        break
                    continue

                consecutive_empty = 0
                print(f"  求人カード数: {len(job_cards)}")

                page_jobs_count = 0
                for i, card in enumerate(job_cards):
                    if len(jobs) >= max_results:
                        break

                    job_data = self._parse_job_card_bs4(soup, card, keyword)
                    if job_data:
                        # 重複チェック
                        job_id = job_data.get("source_id") or job_data.get("scraped_id")
                        if job_id and job_id in seen_job_ids:
                            continue
                        seen_job_ids.add(job_id)
                        
                        jobs.append(job_data)
                        page_jobs_count += 1
                        if len(jobs) <= 10 or page_jobs_count <= 3:  # 最初の10件または各ページの最初の3件を表示
                            print(f"  ✓ [{len(jobs)}] {job_data.get('company_name', 'N/A')[:30]} - {job_data.get('title', 'N/A')[:40]}")

                print(f"  ページ {page_num}: {page_jobs_count}件取得 (累計: {len(jobs)}件)")

                if len(jobs) >= max_results:
                    break

                # 次のページに移動
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

                # 次のページボタンを探す（複数のセレクタを試す）
                next_button = None
                next_selectors = [
                    "a[aria-label*='次']",
                    "a[aria-label*='Next']",
                    "a[data-testid='pagination-page-next']",
                    "a[aria-label*='次の']",
                    "nav[aria-label='ページネーション'] a:last-child",
                ]

                for selector in next_selectors:
                    next_button = page.query_selector(selector)
                    if next_button:
                        # ボタンが有効か確認
                        is_disabled = next_button.get_attribute("aria-disabled") == "true"
                        if not is_disabled:
                            break
                        next_button = None

                # 次のページに移動（URLを直接変更する方法を優先）
                start = page_num * 10
                next_url = f"{url}&start={start}"
                
                # URLにstartパラメータが既にある場合は置き換え
                if "&start=" in next_url or "?start=" in next_url:
                    import re
                    next_url = re.sub(r"[&?]start=\d+", f"&start={start}", next_url)
                elif "?" in next_url:
                    next_url = f"{next_url}&start={start}"
                else:
                    next_url = f"{next_url}?start={start}"
                
                print(f"  次のページURLに直接移動: start={start}")
                try:
                    page.goto(next_url, wait_until="domcontentloaded", timeout=int(self.options.timeout))
                    time.sleep(3)
                    
                    # Cloudflareの検証ページか確認
                    current_html = page.content()
                    if "Just a moment" in current_html or "Cloudflare" in current_html:
                        print("  Cloudflare検証を待機中...")
                        for wait_sec in range(60):  # 最大60秒待つ
                            time.sleep(1)
                            current_html = page.content()
                            if "Just a moment" not in current_html and "Cloudflare" not in current_html:
                                print("  Cloudflare検証が完了しました")
                                break
                        else:
                            print("  Cloudflare検証がタイムアウトしました。ページを再読み込みします...")
                            page.reload(wait_until="domcontentloaded", timeout=int(self.options.timeout))
                            time.sleep(5)
                    
                    # ページが完全に読み込まれるまで待つ
                    try:
                        page.wait_for_load_state("networkidle", timeout=30000)
                    except:
                        pass
                    time.sleep(3)
                    
                    # 求人が見つかるか確認（複数回試行）
                    test_cards = []
                    for retry in range(10):  # 10回までリトライ
                        time.sleep(2)
                        current_html = page.content()
                        current_soup = BeautifulSoup(current_html, "lxml")
                        test_cards = current_soup.find_all("a", {"data-jk": True})
                        if test_cards:
                            print(f"  次のページで {len(test_cards)}件の求人カードを発見")
                            break
                        if retry < 9:
                            print(f"    求人検索リトライ {retry + 1}/10...")
                            # ページをスクロールしてコンテンツを読み込む
                            page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                            time.sleep(1)
                    
                    if not test_cards:
                        print("  次のページに求人がありませんでした。終了します。")
                        break
                    
                    # 同じページか確認（取得した求人数で判断）
                    if len(test_cards) == 0:
                        print("  求人が見つかりませんでした。終了します。")
                        break
                        
                except Exception as e:
                    print(f"  URL移動エラー: {e}")
                    # ボタンクリックを試す
                    if next_button:
                        try:
                            next_button.click()
                            time.sleep(self.options.delay + 2)
                        except Exception as e2:
                            print(f"  ボタンクリックエラー: {e2}")
                            break
                    else:
                        # 「もっと見る」ボタンを探す
                        more_button = page.query_selector("button[data-testid*='more'], a[data-testid*='more']")
                        if more_button:
                            more_button.click()
                            time.sleep(3)
                        else:
                            print("  次のページに移動できませんでした。終了します。")
                            break

        except Exception as e:
            print(f"エラー: {e}")
        finally:
            page.close()

        print(f"\nIndeed: 合計 {len(jobs)}件の求人を取得しました")
        return jobs

    def _parse_job_card(self, page: Page, card: Any, keyword: str) -> Optional[Dict[str, Any]]:
        """求人カードをパース"""
        try:
            # タイトル（複数のセレクタを試す）
            title = ""
            title_selectors = [
                "h2.jobTitle a",
                "h2.jobTitle",
                "a[data-jk]",
                "h2",
                "h3",
                "a[class*='title']",
            ]
            for selector in title_selectors:
                title_elem = card.query_selector(selector)
                if title_elem:
                    title = title_elem.inner_text().strip()
                    if title:
                        break

            # URL（複数のセレクタを試す）
            url = ""
            job_id = ""
            link_selectors = [
                "a[data-jk]",
                "h2.jobTitle a",
                "a[href*='viewjob']",
                "a",
            ]
            for selector in link_selectors:
                link_elem = card.query_selector(selector)
                if link_elem:
                    href = link_elem.get_attribute("href") or ""
                    job_id = link_elem.get_attribute("data-jk") or ""
                    if href:
                        if href.startswith("/"):
                            url = f"{self.BASE_URL}{href}"
                        else:
                            url = href
                        break

            # 会社名（親要素からも探す）
            company_name = ""
            company_selectors = [
                "span.companyName",
                "a.companyName",
                "div[class*='company']",
                "span[class*='company']",
            ]
            for selector in company_selectors:
                company_elem = card.query_selector(selector)
                if company_elem:
                    company_name = company_elem.inner_text().strip()
                    if company_name:
                        break
            
            # 親要素から探す
            if not company_name:
                parent = card.evaluate_handle("el => el.parentElement")
                if parent:
                    try:
                        parent_elem = parent.as_element()
                        company_elem = parent_elem.query_selector("span.companyName, a.companyName")
                        if company_elem:
                            company_name = company_elem.inner_text().strip()
                    except:
                        pass
            
            # ページ全体から探す（data-jkから）
            if not company_name and job_id:
                try:
                    # 同じdata-jkを持つ要素の親から会社名を探す
                    company_elem = page.query_selector(f"a[data-jk='{job_id}']")
                    if company_elem:
                        # 親要素を取得
                        parent_html = company_elem.evaluate("el => el.closest('div[class*=\"job\"]')?.innerHTML || ''")
                        if parent_html:
                            from bs4 import BeautifulSoup
                            soup = BeautifulSoup(parent_html, "html.parser")
                            company_elem_bs = soup.select_one("span.companyName, a.companyName")
                            if company_elem_bs:
                                company_name = company_elem_bs.get_text(strip=True)
                except:
                    pass

            # 場所（複数のセレクタを試す）
            location = ""
            location_selectors = [
                "div.companyLocation",
                "div[class*='location']",
                "span[class*='location']",
            ]
            for selector in location_selectors:
                location_elem = card.query_selector(selector)
                if location_elem:
                    location = location_elem.inner_text().strip()
                    if location:
                        break

            # 給与（複数のセレクタを試す）
            salary_text = ""
            salary_selectors = [
                "div.salary-snippet",
                "span.salaryText",
                "div[class*='salary']",
                "span[class*='salary']",
            ]
            for selector in salary_selectors:
                salary_elem = card.query_selector(selector)
                if salary_elem:
                    salary_text = salary_elem.inner_text().strip()
                    if salary_text:
                        break

            # 給与をパース
            salary_info = self._parse_salary(salary_text)

            # 都道府県と市区町村を抽出
            prefecture, city = self._parse_location(location)

            if not title or not company_name:
                return None

            return {
                "scraped_id": f"ID{job_id[:6]}" if job_id else "",
                "source_id": job_id or "",
                "company_name": company_name,
                "prefecture": prefecture,
                "city": city or location,
                "title": title,
                "qualification": keyword,
                "salary_type": salary_info["type"],
                "daily_min": salary_info.get("daily_min"),
                "daily_max": salary_info.get("daily_max"),
                "monthly_min": salary_info.get("monthly_min"),
                "monthly_max": salary_info.get("monthly_max"),
                "yearly_min": salary_info.get("yearly_min"),
                "yearly_max": salary_info.get("yearly_max"),
                "url": url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            print(f"パースエラー: {e}")
            return None

    def _parse_salary(self, salary_text: str) -> Dict[str, Any]:
        """給与テキストをパース"""
        if not salary_text:
            return {"type": "monthly"}

        # 年収
        yearly_match = re.search(r"年収[：:]\s*(\d+)[〜~-]?(\d+)?万円?", salary_text)
        if yearly_match:
            min_val = float(yearly_match.group(1))
            max_val = float(yearly_match.group(2)) if yearly_match.group(2) else min_val
            return {
                "type": "yearly",
                "yearly_min": min_val,
                "yearly_max": max_val,
            }

        # 月給
        monthly_match = re.search(r"月給[：:]\s*(\d+)[〜~-]?(\d+)?万円?", salary_text)
        if monthly_match:
            min_val = float(monthly_match.group(1))
            max_val = float(monthly_match.group(2)) if monthly_match.group(2) else min_val
            return {
                "type": "monthly",
                "monthly_min": min_val,
                "monthly_max": max_val,
            }

        # 日給
        daily_match = re.search(r"日給[：:]\s*(\d+)[〜~-]?(\d+)?円?", salary_text)
        if daily_match:
            min_val = int(daily_match.group(1))
            max_val = int(daily_match.group(2)) if daily_match.group(2) else min_val
            return {
                "type": "daily",
                "daily_min": min_val,
                "daily_max": max_val,
            }

        return {"type": "monthly"}

    def _parse_location(self, location: str) -> tuple[str, str]:
        """場所を都道府県と市区町村に分割"""
        if not location:
            return ("", "")

        prefectures = [
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
        ]

        prefecture = ""
        city = location

        for pref in prefectures:
            if pref in location:
                prefecture = pref
                city = location.replace(pref, "").strip()
                break

        return (prefecture, city)

    def _parse_job_card_bs4(self, soup: BeautifulSoup, card: Any, keyword: str) -> Optional[Dict[str, Any]]:
        """BeautifulSoupで求人カードをパース"""
        try:
            # タイトル
            title = ""
            if card.name == "a" and card.get("data-jk"):
                title = card.get_text(strip=True)
            else:
                title_elem = card.find("h2") or card.find("h3") or card.find("a")
                if title_elem:
                    title = title_elem.get_text(strip=True)

            if not title:
                return None

            # URLとjob_id
            url = ""
            job_id = ""
            if card.name == "a":
                href = card.get("href", "")
                job_id = card.get("data-jk", "")
                if href:
                    if href.startswith("/"):
                        url = f"{self.BASE_URL}{href}"
                    else:
                        url = href
            else:
                link_elem = card.find("a", {"data-jk": True}) or card.find("a", href=re.compile(r"viewjob"))
                if link_elem:
                    href = link_elem.get("href", "")
                    job_id = link_elem.get("data-jk", "")
                    if href:
                        if href.startswith("/"):
                            url = f"{self.BASE_URL}{href}"
                        else:
                            url = href

            # 会社名（親要素から探す）
            company_name = ""
            # まずカード内を探す
            company_elem = card.find("span", class_="companyName") or card.find("a", class_="companyName")
            if company_elem:
                company_name = company_elem.get_text(strip=True)
            
            # 親要素を階層的に探す（最大5階層まで）
            if not company_name:
                current = card.parent
                for depth in range(5):
                    if not current:
                        break
                    company_elem = current.find("span", class_="companyName") or current.find("a", class_="companyName")
                    if company_elem:
                        company_name = company_elem.get_text(strip=True)
                        break
                    current = current.parent
            
            # まだ見つからない場合は、data-jkを使ってページ全体から探す
            if not company_name and job_id:
                try:
                    # 同じdata-jkを持つ要素を探す
                    job_elem = soup.find("a", {"data-jk": job_id})
                    if job_elem:
                        # 親要素を階層的に探す（最大15階層）
                        current = job_elem.parent
                        for depth in range(15):
                            if not current:
                                break
                            # 会社名を探す（複数のセレクタを試す）
                            company_elem = (
                                current.find("span", class_="companyName") or
                                current.find("a", class_="companyName") or
                                current.find("span", class_=re.compile(r"company")) or
                                current.find("div", class_=re.compile(r"company"))
                            )
                            if company_elem:
                                company_name = company_elem.get_text(strip=True)
                                if company_name:
                                    break
                            
                            # 兄弟要素も探す
                            if current.next_sibling:
                                sibling = current.next_sibling
                                if hasattr(sibling, 'find'):
                                    company_elem = (
                                        sibling.find("span", class_="companyName") or
                                        sibling.find("a", class_="companyName")
                                    )
                                    if company_elem:
                                        company_name = company_elem.get_text(strip=True)
                                        if company_name:
                                            break
                            
                            current = current.parent
                except Exception as e:
                    print(f"    会社名検索エラー: {e}")

            # 場所
            location = ""
            location_elem = card.find("div", class_="companyLocation")
            if location_elem:
                location = location_elem.get_text(strip=True)
            else:
                parent = card.parent
                if parent:
                    location_elem = parent.find("div", class_="companyLocation")
                    if location_elem:
                        location = location_elem.get_text(strip=True)

            # 給与
            salary_text = ""
            salary_elem = card.find("div", class_="salary-snippet") or card.find("span", class_="salaryText")
            if salary_elem:
                salary_text = salary_elem.get_text(strip=True)

            if not company_name:
                return None
            
            # 会社名から都道府県・市区町村を除去（誤って含まれている場合）
            # 会社名の後に都道府県名が続いている場合は除去
            prefectures_list = [
                "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
                "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
                "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
                "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
                "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
                "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
                "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
            ]
            
            # 会社名の最後に都道府県名がある場合は除去
            for pref in prefectures_list:
                if company_name.endswith(pref):
                    company_name = company_name[:-len(pref)].strip()
                    break
                # 都道府県名の後に市区町村名が続いている場合
                if pref in company_name:
                    idx = company_name.find(pref)
                    # 都道府県名以降を除去（ただし、会社名の一部として都道府県名が含まれている場合は除く）
                    if idx > 10:  # 会社名の後半にある場合のみ
                        company_name = company_name[:idx].strip()
                        break

            # 給与をパース
            salary_info = self._parse_salary(salary_text)

            # 都道府県と市区町村を抽出
            prefecture, city = self._parse_location(location)

            return {
                "scraped_id": f"ID{job_id[:6]}" if job_id else "",
                "source_id": job_id or "",
                "company_name": company_name,
                "prefecture": prefecture,
                "city": city or location,
                "title": title,
                "qualification": keyword,
                "salary_type": salary_info["type"],
                "daily_min": salary_info.get("daily_min"),
                "daily_max": salary_info.get("daily_max"),
                "monthly_min": salary_info.get("monthly_min"),
                "monthly_max": salary_info.get("monthly_max"),
                "yearly_min": salary_info.get("yearly_min"),
                "yearly_max": salary_info.get("yearly_max"),
                "url": url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            print(f"パースエラー: {e}")
            return None


class PlaywrightRikunabiNextScraper:
    """Playwrightを使ったRikunabi Nextスクレイパー"""

    BASE_URL = "https://next.rikunabi.com"

    def __init__(self, options: Optional[PlaywrightScrapingOptions] = None) -> None:
        self.options = options or PlaywrightScrapingOptions()
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None

    def __enter__(self):
        """コンテキストマネージャーとして使用"""
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(
            headless=False,  # ヘッドレスモードを無効にしてボット検出を回避
            args=[
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--no-sandbox",
            ],
        )
        self.context = self.browser.new_context(
            viewport={"width": 1920, "height": 1080},
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            locale="ja-JP",
            timezone_id="Asia/Tokyo",
        )
        # ボット検出を回避するためのJavaScriptを追加
        self.context.add_init_script("""
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined
            });
            window.navigator.chrome = {
                runtime: {}
            };
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5]
            });
        """)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """クリーンアップ"""
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()

    def search_jobs(
        self,
        keyword: str = "電気工事士",
        area: str = "",
        max_results: int = 1000,
    ) -> List[Dict[str, Any]]:
        """求人を検索してスクレイピング"""
        if not self.context:
            raise RuntimeError("コンテキストが初期化されていません。with文で使用してください。")

        jobs = []
        seen_job_ids = set()  # 重複チェック用
        page = self.context.new_page()

        try:
            # 検索URLを構築
            from urllib.parse import quote
            if area:
                url = f"{self.BASE_URL}/job_search/area-{self._area_to_code(area)}/kw/{quote(keyword)}/"
            else:
                url = f"{self.BASE_URL}/job_search/kw/{quote(keyword)}/"

            print(f"Rikunabi Next: {url} を取得中...")

            # ページにアクセス
            try:
                page.goto(url, wait_until="domcontentloaded", timeout=int(self.options.timeout))
            except Exception as e:
                print(f"  ページ読み込みエラー: {e}")
                try:
                    page.reload(wait_until="domcontentloaded", timeout=int(self.options.timeout))
                except:
                    pass
            time.sleep(3)

            page_num = 1
            consecutive_empty = 0

            while len(jobs) < max_results and page_num <= self.options.max_pages:
                print(f"\n  ページ {page_num} を処理中...")

                # ページのHTMLを取得してBeautifulSoupでパース
                html = page.content()
                soup = BeautifulSoup(html, "lxml")

                # 求人カードを取得（複数のセレクタを試す）
                # Rikunabi Nextの実際のHTML構造に合わせてセレクタを調整
                job_cards = []
                
                # 方法1: 求人カードを直接探す
                job_cards = soup.find_all("div", class_=re.compile(r"rnn-jobCard|jobCard"))
                if not job_cards:
                    job_cards = soup.find_all("article", class_=re.compile(r"rnn-jobCard|jobCard"))
                if not job_cards:
                    job_cards = soup.find_all("li", class_=re.compile(r"rnn-jobCard|jobCard"))
                
                # 方法2: ページ内のテキストから求人数を確認
                page_text = soup.get_text()
                if "件" in page_text:
                    match = re.search(r"(\d+)件", page_text)
                    if match:
                        total_count = int(match.group(1))
                        print(f"  ページに表示されている求人数: {total_count}件")
                
                # 方法3: Playwrightで直接要素を取得（JavaScriptで読み込まれた後）
                if not job_cards:
                    try:
                        # Playwrightのセレクタで直接取得
                        playwright_cards = page.query_selector_all("div[class*='jobCard'], article[class*='jobCard'], li[class*='jobCard']")
                        if playwright_cards:
                            print(f"  Playwrightで {len(playwright_cards)}件の求人カードを発見")
                            # Playwrightの要素からHTMLを取得してBeautifulSoupでパース
                            for pw_card in playwright_cards[:20]:  # 最初の20件だけ
                                card_html = pw_card.inner_html()
                                card_soup = BeautifulSoup(card_html, "lxml")
                                job_cards.append(card_soup)
                    except Exception as e:
                        print(f"  Playwright取得エラー: {e}")
                
                # 方法4: /job/で始まるリンクを探す
                if not job_cards:
                    job_links = soup.find_all("a", href=re.compile(r"/job/"))
                    print(f"  /job/で始まるリンク数: {len(job_links)}")
                    
                    if job_links:
                        # 最初の3つのリンクのhrefを表示
                        for i, link in enumerate(job_links[:3]):
                            print(f"    リンク[{i+1}]: {link.get('href', 'N/A')}")
                        print(f"  求人リンク数: {len(job_links)}")
                        # リンクの親要素をカードとして扱う（より上位の親を探す）
                        temp_cards = []
                        seen_links = set()
                        for link in job_links:
                            href = link.get("href", "")
                            if href in seen_links:
                                continue
                            seen_links.add(href)
                            
                            # 親要素を階層的に探す（最大15階層）
                            parent = link.parent
                            depth = 0
                            best_parent = None
                            while parent and depth < 15:
                                if parent.name in ["div", "article", "li", "section"]:
                                    parent_text = parent.get_text(strip=True)
                                    # 求人カードらしい要素を探す（タイトル、会社名、給与を含む）
                                    if (
                                        len(parent_text) > 50 and
                                        len(parent_text) < 2000 and  # 長すぎるものは除外
                                        ("年俸" in parent_text or "月給" in parent_text or "万円" in parent_text) and
                                        ("すべての条件" not in parent_text) and
                                        ("関連度順" not in parent_text) and
                                        ("新着順" not in parent_text) and
                                        ("気になる年収" not in parent_text)
                                    ):
                                        best_parent = parent
                                parent = parent.parent
                                depth += 1
                            
                            if best_parent and best_parent not in temp_cards:
                                temp_cards.append(best_parent)
                        
                        if temp_cards:
                            job_cards = temp_cards
                            print(f"  求人カード数: {len(job_cards)}")
                
                if not job_cards:
                    job_cards = []

                if not job_cards:
                    # デバッグ: ページの内容を確認
                    page_text = soup.get_text()[:500] if soup else ""
                    print(f"  求人が見つかりませんでした。")
                    print(f"  ページテキスト（最初の500文字）: {page_text}")
                    
                    # ページタイトルを確認
                    title = soup.title.string if soup.title else "N/A"
                    print(f"  ページタイトル: {title}")
                    
                    # リンクを確認
                    all_links = soup.find_all("a", href=True)
                    print(f"  ページ内のリンク数: {len(all_links)}")
                    
                    consecutive_empty += 1
                    if consecutive_empty >= 2:
                        print("  連続して求人が見つかりませんでした。終了します。")
                        break
                    continue

                consecutive_empty = 0
                print(f"  求人カード数: {len(job_cards)}")

                page_jobs_count = 0
                for i, card in enumerate(job_cards):
                    if len(jobs) >= max_results:
                        break

                    job_data = self._parse_job_card_bs4_rikunabi(soup, card, keyword)
                    if job_data:
                        # 重複チェック
                        job_id = job_data.get("source_id") or job_data.get("scraped_id")
                        if job_id and job_id in seen_job_ids:
                            continue
                        seen_job_ids.add(job_id)
                        
                        jobs.append(job_data)
                        page_jobs_count += 1
                        if len(jobs) <= 10 or page_jobs_count <= 3:
                            print(f"  ✓ [{len(jobs)}] {job_data.get('company_name', 'N/A')[:30]} - {job_data.get('title', 'N/A')[:40]}")
                    elif i < 3:  # 最初の3件でパース失敗した場合、デバッグ出力
                        card_text = card.get_text(strip=True)[:200] if hasattr(card, 'get_text') else str(card)[:200]
                        card_html = str(card)[:500] if hasattr(card, '__str__') else ""
                        print(f"  ✗ パース失敗 [{i+1}]: テキスト={card_text[:100]}")
                        print(f"     HTML={card_html[:300]}")

                print(f"  ページ {page_num}: {page_jobs_count}件取得 (累計: {len(jobs)}件)")

                if len(jobs) >= max_results:
                    break

                # 次のページに移動
                page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                time.sleep(1)

                # 次のページボタンを探す
                next_button = page.query_selector("a.rnn-pager__next, a[class*='next'], a[aria-label*='次']")
                if not next_button:
                    # URLを直接変更
                    next_url = f"{url}page-{page_num + 1}/"
                    try:
                        page.goto(next_url, wait_until="domcontentloaded", timeout=int(self.options.timeout))
                        time.sleep(2)
                        current_html = page.content()
                        if current_html == html:
                            print("  同じページが表示されました。終了します。")
                            break
                        page_num += 1
                        continue
                    except:
                        print("  次のページに移動できませんでした。終了します。")
                        break

                next_button.click()
                time.sleep(self.options.delay)
                page_num += 1

        except Exception as e:
            print(f"エラー: {e}")
            import traceback
            traceback.print_exc()
        finally:
            page.close()

        print(f"\nRikunabi Next: 合計 {len(jobs)}件の求人を取得しました")
        return jobs

    def _parse_job_card(self, page: Page, card: Any, keyword: str) -> Optional[Dict[str, Any]]:
        """求人カードをパース"""
        try:
            # タイトル
            title_elem = card.query_selector("h3, h2, a[class*='title']")
            title = title_elem.inner_text().strip() if title_elem else ""

            # URL
            link_elem = card.query_selector("a[href*='/job/']")
            if link_elem:
                href = link_elem.get_attribute("href") or ""
                if href.startswith("/"):
                    url = f"{self.BASE_URL}{href}"
                else:
                    url = href
                job_id = href.split("/")[-1] if "/" in href else ""
            else:
                url = ""
                job_id = ""

            # 会社名
            company_elem = card.query_selector("div[class*='company'], a[class*='company']")
            company_name = company_elem.inner_text().strip() if company_elem else ""

            # 場所
            location_elem = card.query_selector("div[class*='location'], span[class*='location']")
            location = location_elem.inner_text().strip() if location_elem else ""

            # 給与
            salary_elem = card.query_selector("div[class*='salary'], span[class*='salary']")
            salary_text = salary_elem.inner_text().strip() if salary_elem else ""

            # 給与をパース
            salary_info = self._parse_salary(salary_text)

            # 都道府県と市区町村を抽出
            prefecture, city = self._parse_location(location)

            if not title or not company_name:
                return None

            return {
                "scraped_id": f"RN{job_id[:6]}" if job_id else "",
                "source_id": job_id or "",
                "company_name": company_name,
                "prefecture": prefecture,
                "city": city or location,
                "title": title,
                "qualification": keyword,
                "salary_type": salary_info["type"],
                "daily_min": salary_info.get("daily_min"),
                "daily_max": salary_info.get("daily_max"),
                "monthly_min": salary_info.get("monthly_min"),
                "monthly_max": salary_info.get("monthly_max"),
                "yearly_min": salary_info.get("yearly_min"),
                "yearly_max": salary_info.get("yearly_max"),
                "url": url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            print(f"パースエラー: {e}")
            return None

    def _parse_salary(self, salary_text: str) -> Dict[str, Any]:
        """給与テキストをパース"""
        if not salary_text:
            return {"type": "monthly"}

        # 年収
        yearly_match = re.search(r"年収[：:]\s*(\d+)[〜~-]?(\d+)?万円?", salary_text)
        if yearly_match:
            min_val = float(yearly_match.group(1))
            max_val = float(yearly_match.group(2)) if yearly_match.group(2) else min_val
            return {
                "type": "yearly",
                "yearly_min": min_val,
                "yearly_max": max_val,
            }

        # 月給
        monthly_match = re.search(r"月給[：:]\s*(\d+)[〜~-]?(\d+)?万円?", salary_text)
        if monthly_match:
            min_val = float(monthly_match.group(1))
            max_val = float(monthly_match.group(2)) if monthly_match.group(2) else min_val
            return {
                "type": "monthly",
                "monthly_min": min_val,
                "monthly_max": max_val,
            }

        # 日給
        daily_match = re.search(r"日給[：:]\s*(\d+)[〜~-]?(\d+)?円?", salary_text)
        if daily_match:
            min_val = int(daily_match.group(1))
            max_val = int(daily_match.group(2)) if daily_match.group(2) else min_val
            return {
                "type": "daily",
                "daily_min": min_val,
                "daily_max": max_val,
            }

        return {"type": "monthly"}

    def _parse_location(self, location: str) -> tuple[str, str]:
        """場所を都道府県と市区町村に分割"""
        if not location:
            return ("", "")

        prefectures = [
            "北海道", "青森県", "岩手県", "宮城県", "秋田県", "山形県", "福島県",
            "茨城県", "栃木県", "群馬県", "埼玉県", "千葉県", "東京都", "神奈川県",
            "新潟県", "富山県", "石川県", "福井県", "山梨県", "長野県", "岐阜県",
            "静岡県", "愛知県", "三重県", "滋賀県", "京都府", "大阪府", "兵庫県",
            "奈良県", "和歌山県", "鳥取県", "島根県", "岡山県", "広島県", "山口県",
            "徳島県", "香川県", "愛媛県", "高知県", "福岡県", "佐賀県", "長崎県",
            "熊本県", "大分県", "宮崎県", "鹿児島県", "沖縄県",
        ]

        prefecture = ""
        city = location

        for pref in prefectures:
            if pref in location:
                prefecture = pref
                city = location.replace(pref, "").strip()
                break

        return (prefecture, city)

    def _area_to_code(self, area: str) -> str:
        """エリア名をコードに変換"""
        area_map = {
            "東京都": "tokyo",
            "神奈川県": "kanagawa",
            "大阪府": "osaka",
            "京都府": "kyoto",
            "愛知県": "aichi",
            "福岡県": "fukuoka",
            "北海道": "hokkaido",
        }
        return area_map.get(area, area.lower().replace("県", "").replace("府", "").replace("都", ""))

    def _parse_job_card_bs4_rikunabi(self, soup: BeautifulSoup, card: Any, keyword: str) -> Optional[Dict[str, Any]]:
        """BeautifulSoupでRikunabi Nextの求人カードをパース"""
        try:
            # カードがリンクの場合は親要素を取得
            if card.name == "a":
                card = card.parent if card.parent else card

            # タイトル（複数の方法で探す）
            title = ""
            # まずリンクから探す
            link_elem = card.find("a", href=re.compile(r"/job/"))
            if link_elem:
                title = link_elem.get_text(strip=True)
                if not title:
                    # リンク内の子要素から探す
                    title_elem = link_elem.find("h3") or link_elem.find("h2") or link_elem.find("span")
                    if title_elem:
                        title = title_elem.get_text(strip=True)
            
            if not title:
                # カード全体からタイトルを探す
                title_elem = card.find("h3") or card.find("h2") or card.find("a", class_=re.compile(r"title"))
                if title_elem:
                    title = title_elem.get_text(strip=True)
            
            # タイトルが長すぎる場合は最初の部分だけ
            if len(title) > 100:
                title = title[:100]

            if not title or len(title) < 3:
                return None

            # URLとjob_id
            url = ""
            job_id = ""
            if link_elem:
                href = link_elem.get("href", "")
                if href:
                    if href.startswith("/"):
                        url = f"{self.BASE_URL}{href}"
                    else:
                        url = href
                    # job_idを抽出
                    job_match = re.search(r"/job/([^/]+)", href)
                    if job_match:
                        job_id = job_match.group(1)
                    else:
                        job_id = href.split("/")[-1] if "/" in href else ""

            # 会社名（複数の方法で探す）
            company_name = ""
            # カード内を探す
            company_elem = (
                card.find("div", class_=re.compile(r"company")) or
                card.find("a", class_=re.compile(r"company")) or
                card.find("span", class_=re.compile(r"company"))
            )
            if company_elem:
                company_name = company_elem.get_text(strip=True)
            
            # 親要素から探す
            if not company_name:
                current = card.parent
                for depth in range(10):
                    if not current:
                        break
                    company_elem = (
                        current.find("div", class_=re.compile(r"company")) or
                        current.find("a", class_=re.compile(r"company")) or
                        current.find("span", class_=re.compile(r"company"))
                    )
                    if company_elem:
                        company_name = company_elem.get_text(strip=True)
                        if company_name and len(company_name) > 2:
                            break
                    current = current.parent

            # 場所（複数の方法で探す）
            location = ""
            location_elem = (
                card.find("div", class_=re.compile(r"location")) or
                card.find("span", class_=re.compile(r"location")) or
                card.find(string=re.compile(r"〒|東京都|大阪府|京都府|.*県"))
            )
            if location_elem:
                if hasattr(location_elem, 'get_text'):
                    location = location_elem.get_text(strip=True)
                else:
                    location = str(location_elem).strip()

            # 給与（複数の方法で探す）
            salary_text = ""
            salary_elem = (
                card.find("div", class_=re.compile(r"salary")) or
                card.find("span", class_=re.compile(r"salary")) or
                card.find(string=re.compile(r"年俸|月給|万円"))
            )
            if salary_elem:
                if hasattr(salary_elem, 'get_text'):
                    salary_text = salary_elem.get_text(strip=True)
                else:
                    salary_text = str(salary_elem).strip()

            if not company_name or len(company_name) < 2:
                return None

            # 給与をパース
            salary_info = self._parse_salary(salary_text)

            # 都道府県と市区町村を抽出
            prefecture, city = self._parse_location(location)

            return {
                "scraped_id": f"RN{job_id[:6]}" if job_id else "",
                "source_id": job_id or "",
                "company_name": company_name[:100],  # 長すぎる場合は切り詰め
                "prefecture": prefecture,
                "city": city or location[:50] if location else "",
                "title": title[:100],
                "qualification": keyword,
                "salary_type": salary_info["type"],
                "daily_min": salary_info.get("daily_min"),
                "daily_max": salary_info.get("daily_max"),
                "monthly_min": salary_info.get("monthly_min"),
                "monthly_max": salary_info.get("monthly_max"),
                "yearly_min": salary_info.get("yearly_min"),
                "yearly_max": salary_info.get("yearly_max"),
                "url": url,
                "scraped_at": datetime.now().strftime("%Y-%m-%d"),
            }

        except Exception as e:
            print(f"パースエラー: {e}")
            import traceback
            traceback.print_exc()
            return None

