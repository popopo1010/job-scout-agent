"""音声ファイル名の自動解析・変換モジュール"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Optional, Tuple


class AudioFilenameParser:
    """音声ファイル名を解析して、システム形式に変換するクラス"""

    # 日付パターン（様々な形式に対応）
    DATE_PATTERNS = [
        r"(\d{4})(\d{2})(\d{2})",  # YYYYMMDD
        r"(\d{4})-(\d{2})-(\d{2})",  # YYYY-MM-DD
        r"(\d{4})/(\d{2})/(\d{2})",  # YYYY/MM/DD
        r"(\d{4})\.(\d{2})\.(\d{2})",  # YYYY.MM.DD
    ]

    # 既知のシステムファイル名パターン（そのまま使用）
    SYSTEM_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})_([A-Za-z0-9]+)_(.+)\.(\w+)")

    @classmethod
    def parse_date_from_filename(cls, filename: str) -> Optional[str]:
        """ファイル名から日付を抽出（YYYY-MM-DD形式）
        
        Args:
            filename: ファイル名
            
        Returns:
            日付文字列（YYYY-MM-DD）または None
        """
        # 既存のシステム形式の場合はそのまま返す
        match = cls.SYSTEM_PATTERN.match(filename)
        if match:
            return match.group(1)
        
        # 様々な日付パターンを試す
        for pattern in cls.DATE_PATTERNS:
            matches = re.findall(pattern, filename)
            if matches:
                # 最初に見つかった日付を使用
                year, month, day = matches[0]
                
                # 妥当性チェック
                try:
                    datetime(int(year), int(month), int(day))
                    return f"{year}-{month}-{day}"
                except ValueError:
                    continue
        
        # タイムスタンプ形式 (YYYYMMDDHHMMSS) から日付を抽出
        timestamp_pattern = r"(\d{4})(\d{2})(\d{2})(\d{2})(\d{2})(\d{2})"
        match = re.search(timestamp_pattern, filename)
        if match:
            year, month, day, _, _, _ = match.groups()
            try:
                datetime(int(year), int(month), int(day))
                return f"{year}-{month}-{day}"
            except ValueError:
                pass
        
        return None

    @classmethod
    def extract_guid_or_id(cls, filename: str) -> Optional[str]:
        """ファイル名からGUIDやIDを抽出
        
        Args:
            filename: ファイル名
            
        Returns:
            GUID/ID文字列または None
        """
        # GUID形式を検索
        guid_pattern = r"([a-f0-9]{8}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{4}-[a-f0-9]{12})"
        match = re.search(guid_pattern, filename, re.IGNORECASE)
        if match:
            return match.group(1)[:8]  # GUIDの最初の8文字を使用
        
        # 他のIDパターンを試す
        id_patterns = [
            r"([a-f0-9]{8,})",  # 16進数のID
            r"([0-9]{6,})",  # 数字のID
        ]
        
        for pattern in id_patterns:
            match = re.search(pattern, filename)
            if match:
                return match.group(1)[:8]  # 最初の8文字を使用
        
        return None

    @classmethod
    def normalize_filename(
        cls,
        filename: str,
        ca_id: Optional[str] = None,
        meeting_id: Optional[str] = None,
        date: Optional[str] = None,
    ) -> Tuple[str, str, str, str]:
        """ファイル名を正規化してシステム形式に変換
        
        Args:
            filename: 元のファイル名
            ca_id: CA ID（指定された場合）
            meeting_id: 会議ID（指定された場合）
            date: 日付（YYYY-MM-DD形式、指定された場合）
            
        Returns:
            (normalized_filename, date, ca_id, meeting_id)
        """
        # 拡張子を取得
        file_path = Path(filename)
        extension = file_path.suffix.lower()
        
        # 既にシステム形式の場合
        match = cls.SYSTEM_PATTERN.match(file_path.name)
        if match:
            return file_path.name, match.group(1), match.group(2), match.group(3)
        
        # 日付を抽出
        extracted_date = date or cls.parse_date_from_filename(filename)
        
        if not extracted_date:
            # 日付が見つからない場合は今日の日付を使用
            extracted_date = datetime.now().strftime("%Y-%m-%d")
        
        # CA IDを決定
        if not ca_id:
            # ファイル名から抽出を試みる
            # 一般的なパターン: CA001, FUKUYAMA, etc.
            ca_patterns = [
                r"(CA\d+)",
                r"([A-Z]{2,})",
                r"(FUKUYAMA|CA001|CA002|CA003)",
            ]
            
            for pattern in ca_patterns:
                match = re.search(pattern, filename, re.IGNORECASE)
                if match:
                    ca_id = match.group(1).upper()
                    break
            
            # 見つからない場合はデフォルト値
            if not ca_id:
                ca_id = "UNKNOWN"
        
        # 会議IDを決定
        if not meeting_id:
            # GUIDやIDから抽出
            guid_or_id = cls.extract_guid_or_id(filename)
            if guid_or_id:
                meeting_id = f"meeting-{guid_or_id}"
            else:
                # ファイル名のベース名を使用（安全な文字のみ）
                base_name = file_path.stem
                # 英数字とハイフンのみを許可
                safe_name = re.sub(r'[^a-zA-Z0-9-]', '-', base_name)
                # 長すぎる場合は短縮
                if len(safe_name) > 30:
                    safe_name = safe_name[:30]
                meeting_id = safe_name or "meeting-001"
        
        # 正規化されたファイル名を生成
        normalized = f"{extracted_date}_{ca_id}_{meeting_id}{extension}"
        
        return normalized, extracted_date, ca_id, meeting_id

    @classmethod
    def smart_rename(
        cls,
        source_path: Path,
        ca_id: Optional[str] = None,
        meeting_id: Optional[str] = None,
        date: Optional[str] = None,
        target_dir: Optional[Path] = None,
    ) -> Tuple[Path, str, str, str]:
        """ファイルをスマートにリネームして移動
        
        Args:
            source_path: 元のファイルパス
            ca_id: CA ID（指定された場合）
            meeting_id: 会議ID（指定された場合）
            date: 日付（YYYY-MM-DD形式、指定された場合）
            target_dir: 移動先ディレクトリ（指定された場合）
            
        Returns:
            (new_path, date, ca_id, meeting_id)
        """
        # ファイル名を正規化
        normalized_name, extracted_date, extracted_ca_id, extracted_meeting_id = cls.normalize_filename(
            source_path.name,
            ca_id=ca_id,
            meeting_id=meeting_id,
            date=date,
        )
        
        # 移動先を決定
        if target_dir:
            target_dir.mkdir(parents=True, exist_ok=True)
            new_path = target_dir / normalized_name
        else:
            new_path = source_path.parent / normalized_name
        
        return new_path, extracted_date, extracted_ca_id, extracted_meeting_id

