"""音声ファイル管理システム"""

from __future__ import annotations

import hashlib
import json
import shutil
from dataclasses import asdict, dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional

import re


class AudioStatus(str, Enum):
    """音声ファイルの処理ステータス"""

    PENDING = "pending"  # 書き起こし待ち
    TRANSCRIPT_READY = "transcript_ready"  # 書き起こしファイル準備済み
    PROCESSED = "processed"  # フィードバック生成完了
    FAILED = "failed"  # 処理失敗


@dataclass
class AudioFile:
    """音声ファイル情報"""

    file_path: Path
    ca_id: str
    date: str
    meeting_id: str
    status: AudioStatus = AudioStatus.PENDING
    file_size: int = 0
    duration_seconds: Optional[int] = None
    transcript_path: Optional[Path] = None
    uploaded_at: datetime = field(default_factory=datetime.now)
    processed_at: Optional[datetime] = None
    metadata: Dict[str, str] = field(default_factory=dict)

    @property
    def file_hash(self) -> str:
        """ファイルのハッシュ値を計算"""
        with open(self.file_path, "rb") as f:
            return hashlib.md5(f.read()).hexdigest()

    @property
    def file_size_mb(self) -> float:
        """ファイルサイズをMBで返す"""
        return self.file_size / (1024 * 1024)

    def to_dict(self) -> dict:
        """辞書形式に変換"""
        data = asdict(self)
        data["file_path"] = str(self.file_path)
        data["transcript_path"] = str(self.transcript_path) if self.transcript_path else None
        data["status"] = self.status.value
        data["uploaded_at"] = self.uploaded_at.isoformat()
        data["processed_at"] = self.processed_at.isoformat() if self.processed_at else None
        return data

    @classmethod
    def from_dict(cls, data: dict) -> AudioFile:
        """辞書から生成"""
        audio_file = cls(
            file_path=Path(data["file_path"]),
            ca_id=data["ca_id"],
            date=data["date"],
            meeting_id=data["meeting_id"],
            status=AudioStatus(data["status"]),
            file_size=data.get("file_size", 0),
            duration_seconds=data.get("duration_seconds"),
            transcript_path=Path(data["transcript_path"]) if data.get("transcript_path") else None,
            uploaded_at=datetime.fromisoformat(data["uploaded_at"]),
            processed_at=datetime.fromisoformat(data["processed_at"]) if data.get("processed_at") else None,
            metadata=data.get("metadata", {}),
        )
        return audio_file


class AudioManager:
    """音声ファイル管理クラス"""

    # 対応する音声ファイル形式
    SUPPORTED_FORMATS = {".m4a", ".mp3", ".wav", ".webm", ".mp4"}

    # ファイル名パターン
    FILENAME_PATTERN = re.compile(r"(\d{4}-\d{2}-\d{2})_([A-Za-z0-9]+)_(.+)\.(\w+)")

    def __init__(
        self,
        audio_dir: Optional[Path] = None,
        metadata_file: Optional[Path] = None,
    ) -> None:
        """
        Args:
            audio_dir: 音声ファイルのルートディレクトリ
            metadata_file: メタデータを保存するJSONファイルのパス
        """
        self.audio_dir = audio_dir or Path("data/audio")
        self.pending_dir = self.audio_dir / "pending"
        self.processed_dir = self.audio_dir / "processed"
        self.failed_dir = self.audio_dir / "failed"
        self.transcripts_dir = self.audio_dir / "transcripts"

        # ディレクトリを作成
        for dir_path in [self.pending_dir, self.processed_dir, self.failed_dir, self.transcripts_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # メタデータファイル
        self.metadata_file = metadata_file or self.audio_dir / "audio_metadata.json"
        self._metadata: Dict[str, AudioFile] = {}
        self._load_metadata()

    def _load_metadata(self) -> None:
        """メタデータを読み込む"""
        if self.metadata_file.exists():
            try:
                data = json.loads(self.metadata_file.read_text(encoding="utf-8"))
                self._metadata = {
                    file_hash: AudioFile.from_dict(audio_data)
                    for file_hash, audio_data in data.items()
                }
            except Exception as e:
                print(f"Warning: Failed to load metadata: {e}")

    def _save_metadata(self) -> None:
        """メタデータを保存"""
        data = {
            file_hash: audio_file.to_dict()
            for file_hash, audio_file in self._metadata.items()
        }
        self.metadata_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")

    def validate_filename(self, filename: str) -> bool:
        """ファイル名が命名規則に従っているか確認"""
        return bool(self.FILENAME_PATTERN.match(Path(filename).name))

    def parse_filename(self, filename: str) -> Optional[tuple[str, str, str]]:
        """
        ファイル名から情報を抽出

        Returns:
            (date, ca_id, meeting_id) または None
        """
        match = self.FILENAME_PATTERN.match(Path(filename).name)
        if match:
            date, ca_id, meeting_id, _ = match.groups()
            return date, ca_id, meeting_id
        return None

    def add_audio_file(
        self,
        source_path: Path,
        ca_id: Optional[str] = None,
        date: Optional[str] = None,
        meeting_id: Optional[str] = None,
        force: bool = False,
    ) -> AudioFile:
        """
        音声ファイルを追加

        Args:
            source_path: 元の音声ファイルのパス
            ca_id: CA ID（ファイル名から自動抽出される場合がある）
            date: 日付（ファイル名から自動抽出される場合がある）
            meeting_id: 会議識別子（ファイル名から自動抽出される場合がある）
            force: 既存ファイルを上書きするか

        Returns:
            AudioFileオブジェクト
        """
        if not source_path.exists():
            raise FileNotFoundError(f"Audio file not found: {source_path}")

        # ファイル形式チェック
        suffix = source_path.suffix.lower()
        if suffix not in self.SUPPORTED_FORMATS:
            raise ValueError(f"Unsupported audio format: {suffix}. Supported: {self.SUPPORTED_FORMATS}")

        # ファイル名から情報を抽出
        if not ca_id or not date or not meeting_id:
            parsed = self.parse_filename(source_path.name)
            if parsed:
                date, ca_id, meeting_id = parsed
            else:
                # ファイル名から抽出できない場合は必須
                if not ca_id:
                    raise ValueError("CA ID is required (cannot be extracted from filename)")
                if not date:
                    raise ValueError("Date is required (cannot be extracted from filename)")
                if not meeting_id:
                    meeting_id = source_path.stem

        # 正しいファイル名を生成
        target_filename = f"{date}_{ca_id}_{meeting_id}{suffix}"
        target_path = self.pending_dir / target_filename

        # 重複チェック
        if target_path.exists() and not force:
            raise FileExistsError(f"Audio file already exists: {target_path}")

        # ファイルをコピー
        shutil.copy2(source_path, target_path)

        # ファイルサイズを取得
        file_size = target_path.stat().st_size

        # AudioFileオブジェクトを作成
        audio_file = AudioFile(
            file_path=target_path,
            ca_id=ca_id,
            date=date,
            meeting_id=meeting_id,
            status=AudioStatus.PENDING,
            file_size=file_size,
        )

        # ハッシュを計算してメタデータに保存
        file_hash = audio_file.file_hash
        self._metadata[file_hash] = audio_file
        self._save_metadata()

        return audio_file

    def link_transcript(self, audio_file: AudioFile, transcript_path: Path) -> None:
        """
        書き起こしファイルを音声ファイルに紐付け

        Args:
            audio_file: 音声ファイルオブジェクト
            transcript_path: 書き起こしファイルのパス
        """
        if not transcript_path.exists():
            raise FileNotFoundError(f"Transcript file not found: {transcript_path}")

        # 書き起こしファイルを専用ディレクトリにコピー
        transcript_filename = f"{audio_file.date}_{audio_file.ca_id}_{audio_file.meeting_id}.txt"
        target_transcript_path = self.transcripts_dir / transcript_filename

        shutil.copy2(transcript_path, target_transcript_path)

        # 音声ファイルの情報を更新
        audio_file.transcript_path = target_transcript_path
        audio_file.status = AudioStatus.TRANSCRIPT_READY

        # メタデータを更新
        file_hash = audio_file.file_hash
        self._metadata[file_hash] = audio_file
        self._save_metadata()

        # 既存の書き起こしディレクトリにもシンボリックリンクまたはコピーを作成
        # 既存システムとの互換性のため
        existing_transcript_dir = Path("data/transcripts/pending")
        existing_transcript_dir.mkdir(parents=True, exist_ok=True)
        existing_transcript_path = existing_transcript_dir / transcript_filename

        # コピーまたはシンボリックリンクを作成
        if not existing_transcript_path.exists():
            shutil.copy2(target_transcript_path, existing_transcript_path)

    def list_pending_audio(self) -> List[AudioFile]:
        """書き起こし待ちの音声ファイル一覧を取得"""
        return [
            audio_file
            for audio_file in self._metadata.values()
            if audio_file.status == AudioStatus.PENDING
        ]

    def list_ready_for_processing(self) -> List[AudioFile]:
        """書き起こし準備済み（フィードバック生成可能）の音声ファイル一覧を取得"""
        return [
            audio_file
            for audio_file in self._metadata.values()
            if audio_file.status == AudioStatus.TRANSCRIPT_READY
        ]

    def get_audio_file(self, file_hash: str) -> Optional[AudioFile]:
        """ハッシュ値から音声ファイルを取得"""
        return self._metadata.get(file_hash)

    def find_audio_file(self, date: str, ca_id: str, meeting_id: str) -> Optional[AudioFile]:
        """日付、CA ID、会議IDから音声ファイルを検索"""
        for audio_file in self._metadata.values():
            if (
                audio_file.date == date
                and audio_file.ca_id == ca_id
                and audio_file.meeting_id == meeting_id
            ):
                return audio_file
        return None

    def mark_as_processed(self, audio_file: AudioFile) -> None:
        """音声ファイルを処理済みとしてマーク"""
        # 音声ファイルを移動
        if audio_file.file_path.exists():
            target_path = self.processed_dir / audio_file.file_path.name
            shutil.move(str(audio_file.file_path), str(target_path))
            audio_file.file_path = target_path

        # ステータスを更新
        audio_file.status = AudioStatus.PROCESSED
        audio_file.processed_at = datetime.now()

        # メタデータを更新
        file_hash = audio_file.file_hash
        self._metadata[file_hash] = audio_file
        self._save_metadata()

    def mark_as_failed(self, audio_file: AudioFile, error_message: str = "") -> None:
        """音声ファイルを処理失敗としてマーク"""
        # 音声ファイルを移動
        if audio_file.file_path.exists():
            target_path = self.failed_dir / audio_file.file_path.name
            shutil.move(str(audio_file.file_path), str(target_path))
            audio_file.file_path = target_path

        # ステータスを更新
        audio_file.status = AudioStatus.FAILED
        audio_file.metadata["error"] = error_message

        # メタデータを更新
        file_hash = audio_file.file_hash
        self._metadata[file_hash] = audio_file
        self._save_metadata()

