"""書き起こしファイル読み込み"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Iterator, List, Optional

from .models import Transcript


class TranscriptLoader:
    """書き起こしファイルのローダー"""

    # 対応する書き起こしファイルの命名規則
    FILENAME_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})_([A-Za-z0-9]+)_(.+)\.txt")

    def __init__(
        self,
        pending_dir: Optional[Path] = None,
        processed_dir: Optional[Path] = None,
    ) -> None:
        """
        Args:
            pending_dir: 処理待ちファイルのディレクトリ
            processed_dir: 処理済みファイルの移動先ディレクトリ
        """
        self.pending_dir = pending_dir or Path("data/transcripts/pending")
        self.processed_dir = processed_dir or Path("data/transcripts/processed")

    def find_pending_files(self) -> List[Path]:
        """処理待ちファイルを検索"""
        if not self.pending_dir.exists():
            return []

        files = []
        for path in self.pending_dir.glob("*.txt"):
            if self.FILENAME_PATTERN.match(path.name):
                files.append(path)
            else:
                # 命名規則に従っていないファイルも読み込み対象とする（警告付き）
                files.append(path)

        # 日付順にソート
        files.sort()
        return files

    def load_transcript(self, file_path: Path) -> Transcript:
        """単一ファイルを読み込んでTranscriptオブジェクトを生成"""
        content = file_path.read_text(encoding="utf-8")
        transcript = Transcript.from_filename(str(file_path), content)

        # コンテンツから追加情報を抽出
        self._extract_metadata(transcript, content)

        return transcript

    def load_all_pending(self) -> List[Transcript]:
        """全ての処理待ちファイルを読み込み"""
        transcripts = []
        for file_path in self.find_pending_files():
            transcript = self.load_transcript(file_path)
            transcripts.append(transcript)
        return transcripts

    def iter_pending(self) -> Iterator[Transcript]:
        """処理待ちファイルをイテレート"""
        for file_path in self.find_pending_files():
            yield self.load_transcript(file_path)

    def mark_as_processed(self, transcript: Transcript) -> Path:
        """ファイルを処理済みとしてマーク（移動）"""
        source = Path(transcript.file_path)
        if not source.exists():
            raise FileNotFoundError(f"File not found: {source}")

        # 処理済みディレクトリを作成
        self.processed_dir.mkdir(parents=True, exist_ok=True)

        # 移動
        dest = self.processed_dir / source.name
        source.rename(dest)

        return dest

    def _extract_metadata(self, transcript: Transcript, content: str) -> None:
        """コンテンツからメタデータを抽出"""
        lines = content.split("\n")

        for line in lines[:20]:  # 最初の20行を確認
            # CA名を抽出: "CA: 山田一郎 (CA001)"
            ca_match = re.search(r"CA:\s*(.+?)\s*\(([A-Za-z0-9]+)\)", line)
            if ca_match:
                transcript.ca_name = ca_match.group(1).strip()
                # CA IDも上書き（ファイル名より信頼性が高い場合）
                if transcript.ca_id == "UNKNOWN":
                    transcript.ca_id = ca_match.group(2)

            # クライアント名を抽出: "求職者: 田中太郎 様"
            client_match = re.search(r"求職者:\s*(.+?)[\s様]*$", line)
            if client_match:
                transcript.client_name = client_match.group(1).strip()

            # 日時を抽出: "日時: 2025年1月15日 14:00-14:35"
            date_match = re.search(r"日時:\s*(\d{4})年(\d{1,2})月(\d{1,2})日", line)
            if date_match:
                year, month, day = date_match.groups()
                transcript.date = f"{year}-{int(month):02d}-{int(day):02d}"

            # 通話時間を抽出: "14:00-14:35"
            time_match = re.search(r"(\d{1,2}):(\d{2})-(\d{1,2}):(\d{2})", line)
            if time_match:
                start_h, start_m, end_h, end_m = map(int, time_match.groups())
                start_minutes = start_h * 60 + start_m
                end_minutes = end_h * 60 + end_m
                transcript.duration_minutes = end_minutes - start_minutes

    def validate_filename(self, filename: str) -> bool:
        """ファイル名が命名規則に従っているか確認"""
        return bool(self.FILENAME_PATTERN.match(Path(filename).name))

    def get_expected_filename_format(self) -> str:
        """期待されるファイル名形式を返す"""
        return "{日付}_{CA_ID}_{会議識別子}.txt\n例: 2025-01-15_CA001_client-call-001.txt"
