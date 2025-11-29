#!/usr/bin/env python3
"""
事業戦略の定期チェックスクリプト

市場データ、競合情報、法規制情報などをチェックし、
事業戦略の更新が必要かを判定します。
"""

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional

# プロジェクトルートをパスに追加
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from dataclasses import dataclass, asdict
from enum import Enum


class UpdatePriority(Enum):
    """更新優先度"""
    LOW = "低"
    MEDIUM = "中"
    HIGH = "高"
    CRITICAL = "緊急"


@dataclass
class StrategyCheckItem:
    """戦略チェック項目"""
    category: str  # カテゴリ（市場データ、競合、法規制など）
    item: str  # 項目名
    last_checked: Optional[datetime]  # 最終チェック日
    last_updated: Optional[datetime]  # 最終更新日
    status: str  # 状態（OK, NEEDS_UPDATE, URGENT）
    priority: UpdatePriority  # 優先度
    notes: str = ""  # メモ
    resource_url: str = ""  # リソースURL
    auto_checkable: bool = False  # 自動チェック可能か


class StrategyChecker:
    """事業戦略チェッカー"""

    def __init__(self, data_dir: Path = None):
        if data_dir is None:
            data_dir = project_root / "data" / "monitoring"
        self.data_dir = data_dir
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.check_data_file = self.data_dir / "strategy_checks.json"

    def load_check_data(self) -> Dict:
        """チェックデータを読み込む"""
        if self.check_data_file.exists():
            with open(self.check_data_file, "r", encoding="utf-8") as f:
                return json.load(f)
        return {}

    def save_check_data(self, data: Dict):
        """チェックデータを保存"""
        with open(self.check_data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2, default=str)

    def get_default_check_items(self) -> List[StrategyCheckItem]:
        """デフォルトのチェック項目を取得"""
        now = datetime.now()
        return [
            # 月次チェック項目
            StrategyCheckItem(
                category="KPI",
                item="KPI実績の更新",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.HIGH,
                notes="毎月1回、KPI実績を更新",
                auto_checkable=False
            ),
            StrategyCheckItem(
                category="市場データ",
                item="有効求人倍率の確認",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.MEDIUM,
                notes="厚生労働省の統計データを確認",
                resource_url="https://www.mhlw.go.jp/stf/houdou/",
                auto_checkable=True
            ),
            StrategyCheckItem(
                category="市場データ",
                item="電気工事士求人数の推移",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.MEDIUM,
                notes="主要求人サイトの求人数を確認",
                auto_checkable=True
            ),
            # 四半期チェック項目
            StrategyCheckItem(
                category="経営計画",
                item="経営計画の見直し",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.HIGH,
                notes="四半期ごとに見直し",
                auto_checkable=False
            ),
            StrategyCheckItem(
                category="ロードマップ",
                item="マイルストーンの達成状況",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.HIGH,
                notes="四半期ごとに確認",
                auto_checkable=False
            ),
            StrategyCheckItem(
                category="競合",
                item="競合動向の確認",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.MEDIUM,
                notes="競合サイトの新機能・サービスを確認",
                auto_checkable=True
            ),
            # 年次チェック項目
            StrategyCheckItem(
                category="マーケット分析",
                item="マーケットサイズ分析の更新",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.MEDIUM,
                notes="年次で市場サイズを再計算",
                auto_checkable=False
            ),
            StrategyCheckItem(
                category="PEST分析",
                item="外部環境分析の見直し",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.MEDIUM,
                notes="年次でPEST分析を見直し",
                auto_checkable=False
            ),
            StrategyCheckItem(
                category="SWOT分析",
                item="SWOT分析の見直し",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.MEDIUM,
                notes="年次でSWOT分析を見直し",
                auto_checkable=False
            ),
            # 随時チェック項目
            StrategyCheckItem(
                category="法規制",
                item="法規制の変更確認",
                last_checked=None,
                last_updated=None,
                status="NEEDS_UPDATE",
                priority=UpdatePriority.HIGH,
                notes="電気工事士法、人材紹介事業法などの変更を確認",
                resource_url="https://www.mhlw.go.jp/",
                auto_checkable=True
            ),
        ]

    def check_strategy_updates(self) -> List[StrategyCheckItem]:
        """事業戦略の更新が必要かをチェック"""
        data = self.load_check_data()
        items = self.get_default_check_items()

        # 保存データから最終チェック日を読み込む
        for item in items:
            key = f"{item.category}:{item.item}"
            if key in data:
                item_data = data[key]
                if item_data.get("last_checked"):
                    item.last_checked = datetime.fromisoformat(
                        item_data["last_checked"]
                    )
                if item_data.get("last_updated"):
                    item.last_updated = datetime.fromisoformat(
                        item_data["last_updated"]
                    )
                item.status = item_data.get("status", "NEEDS_UPDATE")
                item.notes = item_data.get("notes", item.notes)

        # 更新が必要かを判定
        now = datetime.now()
        for item in items:
            if item.last_checked is None:
                item.status = "NEEDS_UPDATE"
            elif item.category == "KPI":
                # KPIは月次チェック
                if (now - item.last_checked).days > 30:
                    item.status = "NEEDS_UPDATE"
            elif item.category in ["経営計画", "ロードマップ", "競合"]:
                # 四半期チェック
                if (now - item.last_checked).days > 90:
                    item.status = "NEEDS_UPDATE"
            elif item.category in ["マーケット分析", "PEST分析", "SWOT分析"]:
                # 年次チェック
                if (now - item.last_checked).days > 365:
                    item.status = "NEEDS_UPDATE"
            elif item.category == "法規制":
                # 法規制は月次チェック
                if (now - item.last_checked).days > 30:
                    item.status = "NEEDS_UPDATE"

        return items

    def generate_report(self, items: List[StrategyCheckItem]) -> str:
        """チェック結果レポートを生成"""
        report = []
        report.append("=" * 60)
        report.append("事業戦略定期チェックレポート")
        report.append("=" * 60)
        report.append(f"生成日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append("")

        # カテゴリ別にグループ化
        by_category = {}
        for item in items:
            if item.category not in by_category:
                by_category[item.category] = []
            by_category[item.category].append(item)

        # 優先度順にソート
        priority_order = {
            UpdatePriority.CRITICAL: 0,
            UpdatePriority.HIGH: 1,
            UpdatePriority.MEDIUM: 2,
            UpdatePriority.LOW: 3,
        }

        for category in sorted(by_category.keys()):
            report.append(f"## {category}")
            report.append("")
            category_items = sorted(
                by_category[category],
                key=lambda x: priority_order[x.priority]
            )
            for item in category_items:
                status_icon = {
                    "OK": "✅",
                    "NEEDS_UPDATE": "⚠️",
                    "URGENT": "🚨"
                }.get(item.status, "❓")
                report.append(
                    f"  {status_icon} [{item.priority.value}] {item.item}"
                )
                if item.last_checked:
                    report.append(
                        f"      最終チェック: {item.last_checked.strftime('%Y-%m-%d')}"
                    )
                if item.resource_url:
                    report.append(f"      リソース: {item.resource_url}")
                if item.notes:
                    report.append(f"      メモ: {item.notes}")
                report.append("")

        # サマリー
        needs_update = [item for item in items if item.status == "NEEDS_UPDATE"]
        urgent = [item for item in items if item.status == "URGENT"]
        report.append("=" * 60)
        report.append("サマリー")
        report.append("=" * 60)
        report.append(f"更新が必要: {len(needs_update)}件")
        report.append(f"緊急: {len(urgent)}件")
        report.append(f"総件数: {len(items)}件")

        return "\n".join(report)

    def run(self):
        """チェックを実行"""
        print("事業戦略の定期チェックを実行中...")
        items = self.check_strategy_updates()
        report = self.generate_report(items)
        print("\n" + report)

        # レポートをファイルに保存
        report_file = self.data_dir / f"strategy_check_report_{datetime.now().strftime('%Y%m%d')}.txt"
        with open(report_file, "w", encoding="utf-8") as f:
            f.write(report)
        print(f"\nレポートを保存しました: {report_file}")

        return items


def main():
    """メイン関数"""
    checker = StrategyChecker()
    items = checker.run()

    # 更新が必要な項目がある場合は終了コード1を返す
    needs_update = [item for item in items if item.status in ["NEEDS_UPDATE", "URGENT"]]
    if needs_update:
        print(f"\n⚠️  {len(needs_update)}件の更新が必要な項目があります。")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

