"""フィードバック履歴管理モジュール"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from .models import Feedback


@dataclass
class FeedbackHistoryEntry:
    """フィードバック履歴エントリ"""

    ca_id: str
    date: str
    meeting_id: str
    improvement_points: List[str]
    good_points: List[str]
    overall_score: float
    overall_rating: str  # "excellent", "good", "needs_improvement", "requires_coaching"
    pss_scores: Dict[str, int]  # {"opening": 3, "need_identification": 2, ...}
    ads_scores: Dict[str, int]  # {"adaptability": 3, "rapport_building": 2, ...}
    feedback_id: str  # ユニークID
    created_at: str

    @classmethod
    def from_feedback(cls, feedback: Feedback, feedback_id: Optional[str] = None) -> "FeedbackHistoryEntry":
        """Feedbackオブジェクトから生成"""
        if feedback_id is None:
            feedback_id = f"{feedback.transcript.date}_{feedback.transcript.ca_id}_{feedback.transcript.meeting_id}"
        
        return cls(
            ca_id=feedback.transcript.ca_id,
            date=feedback.transcript.date,
            meeting_id=feedback.transcript.meeting_id,
            improvement_points=feedback.improvement_points,
            good_points=feedback.good_points,
            overall_score=feedback.overall_score,
            overall_rating=feedback.overall_rating.value,
            pss_scores={
                "opening": feedback.pss.opening.score,
                "need_identification": feedback.pss.need_identification.score,
                "presentation": feedback.pss.presentation.score,
                "handling_objections": feedback.pss.handling_objections.score,
                "closing": feedback.pss.closing.score,
            },
            ads_scores={
                "adaptability": feedback.ads.adaptability.score,
                "rapport_building": feedback.ads.rapport_building.score,
                "value_delivery": feedback.ads.value_delivery.score,
            },
            feedback_id=feedback_id,
            created_at=feedback.created_at.isoformat(),
        )


class FeedbackHistoryManager:
    """フィードバック履歴管理クラス"""

    def __init__(self, history_file: Optional[Path] = None):
        """
        Args:
            history_file: 履歴ファイルのパス（デフォルト: data/feedback/history.json）
        """
        self.history_file = history_file or Path("data/feedback/history.json")
        self.history_file.parent.mkdir(parents=True, exist_ok=True)
        self._history: List[FeedbackHistoryEntry] = []
        self._load_history()

    def _load_history(self) -> None:
        """履歴を読み込む"""
        if self.history_file.exists():
            try:
                data = json.loads(self.history_file.read_text(encoding="utf-8"))
                entries = []
                for entry_data in data.get("feedbacks", []):
                    # 後方互換性: 古い形式のデータに対応
                    if "good_points" not in entry_data:
                        entry_data["good_points"] = []
                    if "overall_rating" not in entry_data:
                        # スコアから評価を推定
                        score = entry_data.get("overall_score", 0.0)
                        if score >= 3.5:
                            entry_data["overall_rating"] = "excellent"
                        elif score >= 2.5:
                            entry_data["overall_rating"] = "good"
                        elif score >= 1.5:
                            entry_data["overall_rating"] = "needs_improvement"
                        else:
                            entry_data["overall_rating"] = "requires_coaching"
                    if "pss_scores" not in entry_data:
                        entry_data["pss_scores"] = {}
                    if "ads_scores" not in entry_data:
                        entry_data["ads_scores"] = {}
                    
                    entries.append(FeedbackHistoryEntry(**entry_data))
                self._history = entries
            except Exception as e:
                print(f"Warning: Failed to load feedback history: {e}")
                self._history = []

    def _save_history(self) -> None:
        """履歴を保存"""
        try:
            data = {
                "feedbacks": [asdict(entry) for entry in self._history],
                "last_updated": datetime.now().isoformat(),
            }
            self.history_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception as e:
            print(f"Warning: Failed to save feedback history: {e}")

    def add_feedback(self, feedback: Feedback) -> None:
        """フィードバックを履歴に追加"""
        entry = FeedbackHistoryEntry.from_feedback(feedback)
        self._history.append(entry)
        self._save_history()

    def get_past_feedbacks(
        self,
        ca_id: str,
        exclude_feedback_id: Optional[str] = None,
        days: int = 90,
    ) -> List[FeedbackHistoryEntry]:
        """過去のフィードバックを取得
        
        Args:
            ca_id: CA ID
            exclude_feedback_id: 除外するフィードバックID（現在のフィードバック）
            days: 過去何日分を取得するか（デフォルト: 90日）
            
        Returns:
            過去のフィードバック履歴エントリのリスト
        """
        from datetime import timedelta
        
        cutoff_date = (datetime.now() - timedelta(days=days)).date()
        
        past_feedbacks = []
        for entry in self._history:
            if entry.ca_id != ca_id:
                continue
            
            if exclude_feedback_id and entry.feedback_id == exclude_feedback_id:
                continue
            
            try:
                entry_date = datetime.fromisoformat(entry.date).date() if "T" not in entry.date else datetime.fromisoformat(entry.date).date()
                if entry_date >= cutoff_date:
                    past_feedbacks.append(entry)
            except Exception:
                # 日付パースに失敗した場合はスキップ
                continue
        
        # 日付順にソート（新しい順）
        past_feedbacks.sort(key=lambda x: x.date, reverse=True)
        return past_feedbacks

    def find_repeated_improvements(
        self,
        current_improvement_points: List[str],
        ca_id: str,
        exclude_feedback_id: Optional[str] = None,
        days: int = 90,
    ) -> List[dict]:
        """繰り返されている改善点を検出
        
        Args:
            current_improvement_points: 現在のフィードバックの改善点
            ca_id: CA ID
            exclude_feedback_id: 除外するフィードバックID
            days: 検索期間（日数）
            
        Returns:
            繰り返されている改善点のリスト。各要素は以下の形式:
            {
                "improvement_point": "改善点のテキスト",
                "count": 繰り返し回数,
                "last_feedback_date": "最後に指摘された日付",
                "past_feedback_ids": ["過去のフィードバックID", ...]
            }
        """
        past_feedbacks = self.get_past_feedbacks(ca_id, exclude_feedback_id, days)
        
        # 改善点をキーワードでグループ化
        improvement_keywords = {}
        for improvement in current_improvement_points:
            # 改善点から主要なキーワードを抽出（「【重要】」「【必須】」などのマークを除去）
            clean_improvement = improvement
            for marker in ["【重要】", "【必須】", "【緊急】"]:
                clean_improvement = clean_improvement.replace(marker, "").strip()
            
            # 改善点の先頭部分をキーワードとして使用（最初の30文字程度）
            keyword = clean_improvement[:30] if len(clean_improvement) > 30 else clean_improvement
            
            improvement_keywords[improvement] = keyword
        
        repeated = []
        for current_improvement, keyword in improvement_keywords.items():
            matching_count = 0
            last_date = None
            past_feedback_ids = []
            
            for past_feedback in past_feedbacks:
                for past_improvement in past_feedback.improvement_points:
                    # 類似性チェック（キーワードマッチング）
                    clean_past = past_improvement
                    for marker in ["【重要】", "【必須】", "【緊急】"]:
                        clean_past = clean_past.replace(marker, "").strip()
                    
                    past_keyword = clean_past[:30] if len(clean_past) > 30 else clean_past
                    
                    # キーワードが類似しているかチェック（部分一致）
                    if keyword in past_keyword or past_keyword in keyword:
                        matching_count += 1
                        if last_date is None or past_feedback.date > last_date:
                            last_date = past_feedback.date
                        past_feedback_ids.append(past_feedback.feedback_id)
                        break
            
            if matching_count > 0:
                repeated.append({
                    "improvement_point": current_improvement,
                    "count": matching_count,
                    "last_feedback_date": last_date,
                    "past_feedback_ids": past_feedback_ids,
                })
        
        return repeated

