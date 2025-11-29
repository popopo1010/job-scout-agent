"""Webスクレイパー実装

IndeedとRikunabi Nextから実際に求人情報をスクレイピングする。
"""

from __future__ import annotations

import re
import time
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Dict, Any
from urllib.parse import quote, urljoin, urlparse, parse_qs

import httpx
from bs4 import BeautifulSoup

from .models import ScrapedJob, SalaryInfo, SalaryType


@dataclass
class ScrapingOptions:
    """スクレイピングオプション"""

    max_pages: int = 10  # 最大ページ数
    delay: float = 1.0  # リクエスト間の遅延（秒）
    timeout: float = 30.0  # タイムアウト（秒）
    user_agent: str = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"


class IndeedScraper:
    """Indeedスクレイパー"""

    BASE_URL = "https://jp.indeed.com"

    def __init__(self, options: Optional[ScrapingOptions] = None) -> None:
        self.options = options or ScrapingOptions()
        self.client = httpx.Client(
            timeout=self.options.timeout,
            headers={
                "User-Agent": self.options.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
            follow_redirects=True,
        )

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
        jobs = []
        start = 0

        while len(jobs) < max_results:
            # 検索URLを構築
            params = {
                "q": keyword,
                "l": location,
                "start": start,
            }
            url = f"{self.BASE_URL}/jobs?" + "&".join(f"{k}={quote(str(v))}" for k, v in params.items())

            print(f"Indeed: {url} を取得中...")

            try:
                response = self.client.get(url)
                
                # 403エラーの場合は詳細を表示
                if response.status_code == 403:
                    print(f"⚠️  Indeed: アクセス拒否 (403) - ボット検出の可能性があります")
                    print(f"   レスポンスサイズ: {len(response.text)} bytes")
                    # HTMLの一部を表示してデバッグ
                    if len(response.text) > 0:
                        print(f"   レスポンスの先頭500文字: {response.text[:500]}")
                    break
                
                response.raise_for_status()
                
                # レスポンスのエンコーディングを確認
                if not response.text or len(response.text) < 100:
                    print(f"⚠️  レスポンスが空または短すぎます (サイズ: {len(response.content)} bytes)")
                    # バイナリデータの場合はテキストに変換を試みる
                    try:
                        text = response.content.decode('utf-8', errors='ignore')
                        if len(text) > 100:
                            response._content = text.encode('utf-8')
                    except:
                        pass
                
                soup = BeautifulSoup(response.text, "lxml")

                # 求人カードを取得（複数のセレクタを試す）
                job_cards = soup.find_all("div", class_="job_seen_beacon")
                if not job_cards:
                    job_cards = soup.find_all("a", {"data-jk": True})
                if not job_cards:
                    job_cards = soup.find_all("div", {"data-jk": True})
                if not job_cards:
                    job_cards = soup.find_all("h2", class_="jobTitle")
                if not job_cards:
                    # デバッグ: HTMLの構造を確認
                    print(f"⚠️  求人カードが見つかりませんでした")
                    print(f"   HTMLの一部を確認: {soup.get_text()[:200]}")
                    break

                for card in job_cards:
                    if len(jobs) >= max_results:
                        break

                    job_data = self._parse_job_card(card, keyword)
                    if job_data:
                        jobs.append(job_data)

                # 次のページがあるか確認
                next_button = soup.find("a", {"aria-label": re.compile(r"次|Next")})
                if not next_button:
                    break

                start += 10
                time.sleep(self.options.delay)

            except Exception as e:
                print(f"エラー: {e}")
                break

        print(f"Indeed: {len(jobs)}件の求人を取得しました")
        return jobs

    def _parse_job_card(self, card: Any, keyword: str) -> Optional[Dict[str, Any]]:
        """求人カードをパース"""

        try:
            # タイトル
            title_elem = card.find("h2", class_="jobTitle") or card.find("a", class_="jcs-JobTitle")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            if not title:
                return None

            # URL
            link_elem = card.find("a", {"data-jk": True}) or card.find("a", class_="jcs-JobTitle")
            if link_elem:
                job_id = link_elem.get("data-jk", "")
                url = f"{self.BASE_URL}/viewjob?jk={job_id}" if job_id else ""
            else:
                url = ""

            # 会社名
            company_elem = card.find("span", class_="companyName") or card.find("a", class_="companyName")
            company_name = company_elem.get_text(strip=True) if company_elem else ""

            # 場所
            location_elem = card.find("div", class_="companyLocation")
            location = location_elem.get_text(strip=True) if location_elem else ""

            # 給与
            salary_elem = card.find("div", class_="salary-snippet") or card.find("span", class_="salaryText")
            salary_text = salary_elem.get_text(strip=True) if salary_elem else ""

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

        # 数値のみ（万円単位と仮定）
        num_match = re.search(r"(\d+)[〜~-]?(\d+)?万円?", salary_text)
        if num_match:
            min_val = float(num_match.group(1))
            max_val = float(num_match.group(2)) if num_match.group(2) else min_val
            return {
                "type": "monthly",
                "monthly_min": min_val,
                "monthly_max": max_val,
            }

        return {"type": "monthly"}

    def _parse_location(self, location: str) -> tuple[str, str]:
        """場所を都道府県と市区町村に分割"""
        if not location:
            return ("", "")

        # 都道府県を抽出
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

    def close(self) -> None:
        """クライアントを閉じる"""
        self.client.close()


class RikunabiNextScraper:
    """Rikunabi Nextスクレイパー"""

    BASE_URL = "https://next.rikunabi.com"

    def __init__(self, options: Optional[ScrapingOptions] = None) -> None:
        self.options = options or ScrapingOptions()
        self.client = httpx.Client(
            timeout=self.options.timeout,
            headers={
                "User-Agent": self.options.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
                "Connection": "keep-alive",
                "Upgrade-Insecure-Requests": "1",
            },
            follow_redirects=True,
        )

    def search_jobs(
        self,
        keyword: str = "電気工事士",
        area: str = "",
        max_results: int = 100,
    ) -> List[Dict[str, Any]]:
        """求人を検索してスクレイピング

        Args:
            keyword: 検索キーワード
            area: エリア（都道府県など）
            max_results: 最大取得件数

        Returns:
            求人データのリスト
        """
        jobs = []
        page = 1

        while len(jobs) < max_results:
            # 検索URLを構築
            if area:
                url = f"{self.BASE_URL}/job_search/area-{self._area_to_code(area)}/kw/{quote(keyword)}/page-{page}/"
            else:
                url = f"{self.BASE_URL}/job_search/kw/{quote(keyword)}/page-{page}/"

            print(f"Rikunabi Next: {url} を取得中...")

            try:
                response = self.client.get(url)
                
                if response.status_code == 403:
                    print(f"⚠️  Rikunabi Next: アクセス拒否 (403)")
                    break
                
                response.raise_for_status()
                
                # レスポンスのエンコーディングを確認
                if not response.text or len(response.text) < 100:
                    print(f"⚠️  レスポンスが空または短すぎます (サイズ: {len(response.content)} bytes)")
                    # バイナリデータの場合はテキストに変換を試みる
                    try:
                        text = response.content.decode('utf-8', errors='ignore')
                        if len(text) > 100:
                            response._content = text.encode('utf-8')
                    except:
                        pass
                
                soup = BeautifulSoup(response.text, "lxml")

                # 求人カードを取得（複数のセレクタを試す）
                job_cards = soup.find_all("div", class_="rnn-jobCard")
                if not job_cards:
                    job_cards = soup.find_all("article", class_="rnn-jobCard")
                if not job_cards:
                    job_cards = soup.find_all("div", {"data-job-id": True})
                if not job_cards:
                    job_cards = soup.find_all("li", class_="rnn-jobCard")
                if not job_cards:
                    # デバッグ: HTMLの構造を確認
                    print(f"⚠️  求人カードが見つかりませんでした")
                    print(f"   ページタイトル: {soup.title.string if soup.title else 'N/A'}")
                    # リンクを確認
                    links = soup.find_all("a", href=re.compile(r"/job/"))
                    print(f"   求人リンク数: {len(links)}")
                    if links:
                        print(f"   最初のリンク: {links[0].get('href', 'N/A')}")
                    break

                for card in job_cards:
                    if len(jobs) >= max_results:
                        break

                    job_data = self._parse_job_card(card, keyword)
                    if job_data:
                        jobs.append(job_data)

                # 次のページがあるか確認
                next_button = soup.find("a", class_="rnn-pager__next") or soup.find("a", string=re.compile(r"次|Next"))
                if not next_button or page >= self.options.max_pages:
                    break

                page += 1
                time.sleep(self.options.delay)

            except Exception as e:
                print(f"エラー: {e}")
                break

        print(f"Rikunabi Next: {len(jobs)}件の求人を取得しました")
        return jobs

    def _parse_job_card(self, card: Any, keyword: str) -> Optional[Dict[str, Any]]:
        """求人カードをパース"""

        try:
            # タイトル
            title_elem = card.find("h3", class_="rnn-jobCard__title") or card.find("a", class_="rnn-jobCard__titleLink")
            if not title_elem:
                return None

            title = title_elem.get_text(strip=True)
            if not title:
                return None

            # URL
            link_elem = card.find("a", class_="rnn-jobCard__titleLink") or card.find("a", href=re.compile(r"/job/"))
            if link_elem:
                url = urljoin(self.BASE_URL, link_elem.get("href", ""))
                job_id = url.split("/")[-1] if "/" in url else ""
            else:
                url = ""
                job_id = ""

            # 会社名
            company_elem = card.find("div", class_="rnn-jobCard__companyName") or card.find("a", class_="rnn-jobCard__companyName")
            company_name = company_elem.get_text(strip=True) if company_elem else ""

            # 場所
            location_elem = card.find("div", class_="rnn-jobCard__location") or card.find("span", class_="rnn-jobCard__location")
            location = location_elem.get_text(strip=True) if location_elem else ""

            # 給与
            salary_elem = card.find("div", class_="rnn-jobCard__salary") or card.find("span", class_="rnn-jobCard__salary")
            salary_text = salary_elem.get_text(strip=True) if salary_elem else ""

            # 給与をパース
            salary_info = self._parse_salary(salary_text)

            # 都道府県と市区町村を抽出
            prefecture, city = self._parse_location(location)

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

        # 数値のみ（万円単位と仮定）
        num_match = re.search(r"(\d+)[〜~-]?(\d+)?万円?", salary_text)
        if num_match:
            min_val = float(num_match.group(1))
            max_val = float(num_match.group(2)) if num_match.group(2) else min_val
            return {
                "type": "monthly",
                "monthly_min": min_val,
                "monthly_max": max_val,
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

    def close(self) -> None:
        """クライアントを閉じる"""
        self.client.close()

