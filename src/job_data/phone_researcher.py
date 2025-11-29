"""電話番号リサーチモジュール

会社名から人事向けの電話番号をリサーチする。
並列処理で複数の会社の電話番号を同時に取得する。
"""

from __future__ import annotations

import re
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Optional, Dict, Any, Callable
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup


class PhoneResearcher:
    """電話番号リサーチクラス"""

    def __init__(
        self,
        max_workers: int = 10,
        timeout: float = 30.0,
        delay: float = 0.5,
    ) -> None:
        """
        Args:
            max_workers: 並列実行数
            timeout: タイムアウト（秒）
            delay: リクエスト間の遅延（秒）
        """
        self.max_workers = max_workers
        self.timeout = timeout
        self.delay = delay
        self.user_agent = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"

    def research_phones(
        self,
        company_names: List[str],
        progress_callback: Optional[Callable[[str, Optional[str], str, int, int], None]] = None,
    ) -> Dict[str, Optional[str]]:
        """複数の会社の電話番号を並列でリサーチ

        Args:
            company_names: 会社名のリスト
            progress_callback: 進捗コールバック関数（company_name, phone_number, status）

        Returns:
            会社名をキー、電話番号を値とする辞書
        """
        results = {}
        total = len(company_names)

        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            # 各会社の電話番号リサーチを並列実行
            future_to_company = {
                executor.submit(self._research_phone, company_name): company_name
                for company_name in company_names
            }

            completed = 0
            for future in as_completed(future_to_company):
                company_name = future_to_company[future]
                try:
                    phone_number = future.result()
                    results[company_name] = phone_number
                    completed += 1

                    if progress_callback:
                        status = "成功" if phone_number else "見つからず"
                        progress_callback(company_name, phone_number, status, completed, total)

                except Exception as e:
                    results[company_name] = None
                    completed += 1
                    if progress_callback:
                        progress_callback(company_name, None, f"エラー: {e}", completed, total)

        return results

    def _research_phone(self, company_name: str) -> Optional[str]:
        """単一の会社の電話番号をリサーチ

        Args:
            company_name: 会社名

        Returns:
            電話番号（見つからない場合はNone）
        """
        if not company_name or company_name.strip() == "":
            return None

        # 方法1: Google検索で会社名+電話番号で検索
        phone = self._search_google(company_name)
        if phone:
            return phone

        # 方法2: 会社名+採用+電話番号で検索
        phone = self._search_google(f"{company_name} 採用 電話番号")
        if phone:
            return phone

        # 方法3: 会社名+人事+電話番号で検索
        phone = self._search_google(f"{company_name} 人事 電話番号")
        if phone:
            return phone

        return None

    def _search_google(self, query: str) -> Optional[str]:
        """Google検索で電話番号を探す

        Args:
            query: 検索クエリ

        Returns:
            電話番号（見つからない場合はNone）
        """
        try:
            # Google検索URL
            url = f"https://www.google.com/search?q={quote(query)}&num=5"

            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                "Accept-Language": "ja,en-US;q=0.9,en;q=0.8",
            }

            with httpx.Client(timeout=self.timeout, headers=headers, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")

                # 検索結果から電話番号を抽出
                text = soup.get_text()

                # 電話番号パターン（日本の電話番号）
                phone_patterns = [
                    r"0\d{1,4}-\d{1,4}-\d{4}",  # 03-1234-5678
                    r"0\d{2,3}-\d{3,4}-\d{4}",  # 03-1234-5678, 0123-45-6789
                    r"0\d{9,10}",  # 0312345678
                    r"\(0\d{1,4}\)\s*\d{1,4}-\d{4}",  # (03) 1234-5678
                ]

                for pattern in phone_patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        # 最初に見つかった電話番号を返す
                        phone = matches[0].strip()
                        # フォーマットを統一（ハイフン付き）
                        phone = self._normalize_phone(phone)
                        if self._is_valid_phone(phone):
                            return phone

                # 検索結果のリンクから電話番号を探す
                links = soup.find_all("a", href=True)
                for link in links[:10]:  # 最初の10件のリンクをチェック
                    href = link.get("href", "")
                    if href.startswith("http"):
                        phone = self._extract_phone_from_url(href)
                        if phone:
                            return phone

        except Exception as e:
            print(f"Google検索エラー ({query}): {e}")
            return None

        return None

    def _extract_phone_from_url(self, url: str) -> Optional[str]:
        """URLから電話番号を抽出

        Args:
            url: ウェブページのURL

        Returns:
            電話番号（見つからない場合はNone）
        """
        try:
            headers = {
                "User-Agent": self.user_agent,
                "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            }

            with httpx.Client(timeout=self.timeout, headers=headers, follow_redirects=True) as client:
                response = client.get(url)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")
                text = soup.get_text()

                # 電話番号パターン
                phone_patterns = [
                    r"0\d{1,4}-\d{1,4}-\d{4}",
                    r"0\d{2,3}-\d{3,4}-\d{4}",
                    r"\(0\d{1,4}\)\s*\d{1,4}-\d{4}",
                ]

                for pattern in phone_patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        phone = self._normalize_phone(matches[0].strip())
                        if self._is_valid_phone(phone):
                            return phone

        except Exception:
            pass

        return None

    def _normalize_phone(self, phone: str) -> str:
        """電話番号を正規化

        Args:
            phone: 電話番号文字列

        Returns:
            正規化された電話番号
        """
        # 括弧とスペースを削除
        phone = re.sub(r"[\(\)\s]", "", phone)

        # ハイフンで区切る
        if len(phone) == 10:
            # 03-1234-5678形式
            return f"{phone[:2]}-{phone[2:6]}-{phone[6:]}"
        elif len(phone) == 11:
            # 0123-45-6789形式
            if phone.startswith("0"):
                if phone[1:3] in ["90", "80", "70", "60", "50"]:
                    return f"{phone[:3]}-{phone[3:7]}-{phone[7:]}"
                else:
                    return f"{phone[:2]}-{phone[2:6]}-{phone[6:]}"

        # 既にハイフンがある場合はそのまま
        if "-" in phone:
            return phone

        return phone

    def _is_valid_phone(self, phone: str) -> bool:
        """電話番号が有効かチェック

        Args:
            phone: 電話番号文字列

        Returns:
            有効な場合はTrue
        """
        if not phone:
            return False

        # 0で始まる必要がある
        if not phone.startswith("0"):
            return False

        # 数字とハイフンのみ
        if not re.match(r"^0[\d-]+$", phone):
            return False

        # 長さチェック（ハイフン除く）
        digits = re.sub(r"-", "", phone)
        if len(digits) < 10 or len(digits) > 11:
            return False

        return True

    async def research_phones_async(
        self,
        company_names: List[str],
        progress_callback: Optional[Callable[[str, Optional[str], str, int, int], None]] = None,
    ) -> Dict[str, Optional[str]]:
        """非同期で複数の会社の電話番号をリサーチ

        Args:
            company_names: 会社名のリスト
            progress_callback: 進捗コールバック関数

        Returns:
            会社名をキー、電話番号を値とする辞書
        """
        results = {}
        total = len(company_names)

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            tasks = [
                self._research_phone_async(client, company_name)
                for company_name in company_names
            ]

            completed = 0
            for coro in asyncio.as_completed(tasks):
                company_name, phone_number = await coro
                results[company_name] = phone_number
                completed += 1

                if progress_callback:
                    status = "成功" if phone_number else "見つからず"
                    progress_callback(company_name, phone_number, status, completed, total)

        return results

    async def _research_phone_async(
        self,
        client: httpx.AsyncClient,
        company_name: str,
    ) -> tuple[str, Optional[str]]:
        """非同期で単一の会社の電話番号をリサーチ"""
        if not company_name or company_name.strip() == "":
            return (company_name, None)

        # Google検索
        queries = [
            company_name,
            f"{company_name} 採用 電話番号",
            f"{company_name} 人事 電話番号",
        ]

        for query in queries:
            try:
                url = f"https://www.google.com/search?q={quote(query)}&num=5"
                headers = {
                    "User-Agent": self.user_agent,
                    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
                }

                response = await client.get(url, headers=headers)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "lxml")
                text = soup.get_text()

                phone_patterns = [
                    r"0\d{1,4}-\d{1,4}-\d{4}",
                    r"0\d{2,3}-\d{3,4}-\d{4}",
                    r"\(0\d{1,4}\)\s*\d{1,4}-\d{4}",
                ]

                for pattern in phone_patterns:
                    matches = re.findall(pattern, text)
                    if matches:
                        phone = self._normalize_phone(matches[0].strip())
                        if self._is_valid_phone(phone):
                            await asyncio.sleep(self.delay)
                            return (company_name, phone)

                await asyncio.sleep(self.delay)

            except Exception:
                continue

        return (company_name, None)

