"""CA-Slack IDマッピング管理モジュール"""

from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, Optional

try:
    import yaml
    HAS_YAML = True
except ImportError:
    HAS_YAML = False


@dataclass
class CAMapping:
    """CA-Slack IDマッピング"""

    ca_id: str
    name: str
    slack_user_id: str

    def to_slack_mention(self) -> str:
        """Slackメンション形式に変換"""
        return f"<@{self.slack_user_id}>"


class CAMappingManager:
    """CA-Slack IDマッピング管理クラス"""

    def __init__(
        self,
        mapping_file: Optional[Path] = None,
        csv_file: Optional[Path] = None,
    ):
        """
        Args:
            mapping_file: YAML形式のマッピングファイル
            csv_file: CSV形式のマッピングファイル（優先度: 高）
        """
        self.mapping_file = mapping_file or Path("config/ca_slack_mapping.yaml")
        self.csv_file = csv_file or Path("data/sample/analytics/ca_master.csv")
        self._mappings: Dict[str, CAMapping] = {}
        self._load_mappings()

    def _load_mappings(self) -> None:
        """マッピングを読み込む"""
        # CSVファイルから読み込み（優先）
        if self.csv_file and self.csv_file.exists():
            self._load_from_csv()
        # YAMLファイルから読み込み
        elif self.mapping_file and self.mapping_file.exists():
            self._load_from_yaml()
        else:
            print(f"Warning: マッピングファイルが見つかりません: {self.csv_file} または {self.mapping_file}")

    def _load_from_csv(self) -> None:
        """CSVファイルから読み込み"""
        try:
            with open(self.csv_file, encoding="utf-8") as f:
                reader = csv.DictReader(f)
                for row in reader:
                    ca_id = row.get("ca_id", "").strip()
                    name = row.get("name", "").strip()
                    slack_user_id = row.get("slack_user_id", "").strip()
                    
                    if ca_id and slack_user_id:
                        self._mappings[ca_id] = CAMapping(
                            ca_id=ca_id,
                            name=name or ca_id,
                            slack_user_id=slack_user_id,
                        )
        except Exception as e:
            print(f"Warning: CSVファイルの読み込みに失敗: {e}")

    def _load_from_yaml(self) -> None:
        """YAMLファイルから読み込み"""
        if not HAS_YAML:
            print("Warning: PyYAMLがインストールされていません。YAMLファイルを読み込めません。")
            return
        
        try:
            with open(self.mapping_file, encoding="utf-8") as f:
                data = yaml.safe_load(f)
                mappings = data.get("ca_slack_mappings", [])
                
                for mapping in mappings:
                    ca_id = mapping.get("ca_id", "").strip()
                    name = mapping.get("name", "").strip()
                    slack_user_id = mapping.get("slack_user_id", "").strip()
                    
                    if ca_id and slack_user_id:
                        self._mappings[ca_id] = CAMapping(
                            ca_id=ca_id,
                            name=name or ca_id,
                            slack_user_id=slack_user_id,
                        )
        except Exception as e:
            print(f"Warning: YAMLファイルの読み込みに失敗: {e}")

    def get_slack_user_id(self, ca_id: str) -> Optional[str]:
        """CA IDからSlackユーザーIDを取得"""
        mapping = self._mappings.get(ca_id)
        return mapping.slack_user_id if mapping else None

    def get_ca_name(self, ca_id: str) -> Optional[str]:
        """CA IDからCA名を取得"""
        mapping = self._mappings.get(ca_id)
        return mapping.name if mapping else None

    def get_slack_mention(self, ca_id: str) -> Optional[str]:
        """CA IDからSlackメンション形式を取得"""
        mapping = self._mappings.get(ca_id)
        return mapping.to_slack_mention() if mapping else None

    def has_mapping(self, ca_id: str) -> bool:
        """マッピングが存在するか"""
        return ca_id in self._mappings

    def get_all_mappings(self) -> Dict[str, CAMapping]:
        """全マッピングを取得"""
        return self._mappings.copy()

