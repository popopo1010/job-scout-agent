"""フィードバック生成ロジック"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from typing import Any, List, Optional

try:
    import anthropic
    HAS_ANTHROPIC = True
except ImportError:
    HAS_ANTHROPIC = False

from .models import (
    Transcript,
    PSSEvaluation,
    ADSEvaluation,
    Feedback,
    EvaluationLevel,
)


class FeedbackGenerator:
    """フィードバック生成エンジン

    本番環境ではClaude APIを使用してAI分析を行うが、
    サンプル実行時はルールベースの簡易分析を提供する。
    """

    # PSS評価のキーワードパターン
    PSS_PATTERNS = {
        "opening": {
            "positive": ["ありがとうございます", "お時間", "よろしいでしょうか", "自己紹介"],
            "negative": ["いきなり", "急に"],
        },
        "need_identification": {
            "positive": ["教えていただけ", "きっかけ", "ご希望", "具体的に", "どのくらい"],
            "negative": ["一方的", "聞かない"],
        },
        "presentation": {
            "positive": ["ご紹介", "年収", "残業", "仕事内容", "具体的"],
            "negative": ["詳細不明", "曖昧"],
        },
        "handling_objections": {
            "positive": ["なるほど", "お気持ち", "わかります", "承知"],
            "negative": ["否定", "反論"],
        },
        "closing": {
            "positive": ["次", "いつまで", "金曜日", "準備", "お送り"],
            "negative": ["曖昧", "不明確"],
        },
    }

    # ADS評価のキーワードパターン
    ADS_PATTERNS = {
        "adaptability": {
            "positive": ["承知しました", "なるほど", "ですね"],
            "negative": ["専門用語", "わかりにくい"],
        },
        "rapport_building": {
            "positive": ["お気持ち", "わかります", "確かに", "十分"],
            "negative": ["冷たい", "機械的"],
        },
        "value_delivery": {
            "positive": ["メリット", "スキルアップ", "年収", "残業", "環境"],
            "negative": ["抽象的", "具体性なし"],
        },
    }

    def __init__(
        self,
        criteria_path: Optional[Path] = None,
        use_ai: bool = False,
    ) -> None:
        """
        Args:
            criteria_path: PSS/ADS評価基準ファイルのパス
            use_ai: Claude AIを使用するかどうか（デフォルト: False）
        """
        self.criteria_path = criteria_path
        self.use_ai = use_ai
        self.criteria_content: str | None = None

        if criteria_path and criteria_path.exists():
            self.criteria_content = criteria_path.read_text(encoding="utf-8")

    def generate_feedback(self, transcript: Transcript) -> Feedback:
        """書き起こしからフィードバックを生成"""
        if self.use_ai:
            return self._generate_with_ai(transcript)
        else:
            return self._generate_rule_based(transcript)

    def _generate_rule_based(self, transcript: Transcript) -> Feedback:
        """ルールベースのフィードバック生成（サンプル/テスト用）"""
        content = transcript.content.lower()

        # PSS評価
        pss = self._evaluate_pss(content)

        # ADS評価
        ads = self._evaluate_ads(content)

        # 良かった点を抽出
        good_points = self._extract_good_points(content, pss, ads)

        # 改善点を抽出
        improvement_points = self._extract_improvement_points(content, pss, ads)

        # 具体的アドバイスを生成
        specific_advice = self._generate_advice(pss, ads)

        # 次回目標を生成
        next_goals = self._generate_goals(pss, ads)

        return Feedback(
            transcript=transcript,
            pss=pss,
            ads=ads,
            good_points=good_points,
            improvement_points=improvement_points,
            specific_advice=specific_advice,
            next_goals=next_goals,
        )

    def _evaluate_pss(self, content: str) -> PSSEvaluation:
        """PSSの各項目を評価"""
        evaluations = {}
        comments = {}

        for item, patterns in self.PSS_PATTERNS.items():
            positive_count = sum(1 for p in patterns["positive"] if p in content)
            negative_count = sum(1 for p in patterns["negative"] if p in content)

            # スコア計算
            score = positive_count - negative_count * 2

            if score >= 3:
                level = EvaluationLevel.A
                comment = "すべての要素を満たしている"
            elif score >= 1:
                level = EvaluationLevel.B
                comment = "基本的な要素を満たしている"
            elif score >= 0:
                level = EvaluationLevel.C
                comment = "一部の要素が不足"
            else:
                level = EvaluationLevel.D
                comment = "改善が必要"

            evaluations[item] = level
            comments[item + "_comment"] = comment

        return PSSEvaluation(
            opening=evaluations["opening"],
            need_identification=evaluations["need_identification"],
            presentation=evaluations["presentation"],
            handling_objections=evaluations["handling_objections"],
            closing=evaluations["closing"],
            opening_comment=comments["opening_comment"],
            need_identification_comment=comments["need_identification_comment"],
            presentation_comment=comments["presentation_comment"],
            handling_objections_comment=comments["handling_objections_comment"],
            closing_comment=comments["closing_comment"],
        )

    def _evaluate_ads(self, content: str) -> ADSEvaluation:
        """ADSの各項目を評価"""
        evaluations = {}
        comments = {}

        for item, patterns in self.ADS_PATTERNS.items():
            positive_count = sum(1 for p in patterns["positive"] if p in content)
            negative_count = sum(1 for p in patterns["negative"] if p in content)

            score = positive_count - negative_count * 2

            if score >= 2:
                level = EvaluationLevel.A
                comment = "優れた対応"
            elif score >= 1:
                level = EvaluationLevel.B
                comment = "良好な対応"
            elif score >= 0:
                level = EvaluationLevel.C
                comment = "標準的な対応"
            else:
                level = EvaluationLevel.D
                comment = "改善が必要"

            evaluations[item] = level
            comments[item + "_comment"] = comment

        return ADSEvaluation(
            adaptability=evaluations["adaptability"],
            rapport_building=evaluations["rapport_building"],
            value_delivery=evaluations["value_delivery"],
            adaptability_comment=comments["adaptability_comment"],
            rapport_building_comment=comments["rapport_building_comment"],
            value_delivery_comment=comments["value_delivery_comment"],
        )

    def _extract_good_points(
        self, content: str, pss: PSSEvaluation, ads: ADSEvaluation
    ) -> List[str]:
        """良かった点を抽出"""
        good_points = []

        if pss.opening in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("適切な自己紹介と時間確認ができている")

        if pss.need_identification in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("オープンクエスチョンでニーズを引き出している")

        if pss.presentation in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("具体的な求人情報を提示できている")

        if pss.closing in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("明確なネクストステップを設定している")

        if ads.rapport_building in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("求職者への共感を示している")

        if ads.value_delivery in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("求人のメリットを具体的に伝えている")

        return good_points[:3]  # 最大3つ

    def _extract_improvement_points(
        self, content: str, pss: PSSEvaluation, ads: ADSEvaluation
    ) -> List[str]:
        """改善点を抽出"""
        improvements = []

        if pss.need_identification in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("より深いニーズの深掘りを行う")

        if pss.handling_objections in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("反論や懸念への対応力を強化する")

        if pss.closing in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("クロージング時の期限設定を明確にする")

        if ads.adaptability in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("相手のペースに合わせたコミュニケーションを心がける")

        if ads.value_delivery in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("具体的な数字やメリットをより明確に伝える")

        return improvements[:3]  # 最大3つ

    def _generate_advice(self, pss: PSSEvaluation, ads: ADSEvaluation) -> str:
        """具体的アドバイスを生成"""
        advice_parts = []

        # 最も低いスコアの項目にフォーカス
        all_scores = [
            ("オープニング", pss.opening),
            ("ニーズ把握", pss.need_identification),
            ("提案", pss.presentation),
            ("反論対応", pss.handling_objections),
            ("クロージング", pss.closing),
        ]

        lowest = min(all_scores, key=lambda x: x[1].score)

        if lowest[1] in (EvaluationLevel.C, EvaluationLevel.D):
            if lowest[0] == "オープニング":
                advice_parts.append(
                    "オープニングでは、自己紹介・目的・時間確認の3点を必ず含めましょう。"
                )
            elif lowest[0] == "ニーズ把握":
                advice_parts.append(
                    "「なぜ？」「具体的には？」などの深掘り質問を意識的に使いましょう。"
                )
            elif lowest[0] == "提案":
                advice_parts.append(
                    "年収・残業・仕事内容など、求職者のニーズに直結する情報を具体的に伝えましょう。"
                )
            elif lowest[0] == "反論対応":
                advice_parts.append(
                    "反論は否定せず「おっしゃる通りです」と一度受け止めてから回答しましょう。"
                )
            elif lowest[0] == "クロージング":
                advice_parts.append(
                    "次のアクションと期限を明確に設定し、相手の合意を得ましょう。"
                )

        if not advice_parts:
            advice_parts.append("全体的にバランスの取れた通話でした。さらなる向上のため、潜在ニーズの深掘りを意識しましょう。")

        return " ".join(advice_parts)

    def _generate_goals(self, pss: PSSEvaluation, ads: ADSEvaluation) -> str:
        """次回目標を生成"""
        goals = []

        # 改善が必要な項目を1つ目標に
        if pss.need_identification.score < 4:
            goals.append("ニーズ把握で深掘り質問を2回以上行う")
        if pss.closing.score < 4:
            goals.append("クロージング時に具体的な期限を設定する")
        if ads.rapport_building.score < 4:
            goals.append("共感フレーズを会話中に3回以上使用する")

        if not goals:
            goals.append("現状の質を維持しながら、より複雑なケースにも対応できるよう準備する")

        return goals[0]

    def _generate_with_ai(self, transcript: Transcript) -> Feedback:
        """Claude AIを使用したフィードバック生成"""
        if not HAS_ANTHROPIC:
            raise ImportError(
                "anthropic package is required for AI-based feedback. "
                "Install with: pip install anthropic"
            )

        client = anthropic.Anthropic()

        # 評価基準を含めたプロンプトを構築
        criteria_text = self.criteria_content or self._get_default_criteria()

        prompt = f"""以下の営業通話の書き起こしを分析し、PSS/ADSの観点でフィードバックを生成してください。

## 評価基準
{criteria_text}

## 書き起こし内容
{transcript.content}

## 出力形式
以下のJSON形式で出力してください。評価レベルは A/B/C/D のいずれかで指定してください。

```json
{{
  "pss": {{
    "opening": {{"level": "A/B/C/D", "comment": "評価コメント"}},
    "need_identification": {{"level": "A/B/C/D", "comment": "評価コメント"}},
    "presentation": {{"level": "A/B/C/D", "comment": "評価コメント"}},
    "handling_objections": {{"level": "A/B/C/D", "comment": "評価コメント"}},
    "closing": {{"level": "A/B/C/D", "comment": "評価コメント"}}
  }},
  "ads": {{
    "adaptability": {{"level": "A/B/C/D", "comment": "評価コメント"}},
    "rapport_building": {{"level": "A/B/C/D", "comment": "評価コメント"}},
    "value_delivery": {{"level": "A/B/C/D", "comment": "評価コメント"}}
  }},
  "good_points": ["良かった点1", "良かった点2", "良かった点3"],
  "improvement_points": ["改善点1", "改善点2", "改善点3"],
  "specific_advice": "具体的な改善アドバイス",
  "next_goals": "次回に向けた目標"
}}
```

JSONのみを出力し、それ以外のテキストは含めないでください。
"""

        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=2000,
            messages=[
                {"role": "user", "content": prompt}
            ],
        )

        # レスポンスをパース
        response_text = message.content[0].text

        # JSONを抽出（```json ... ``` で囲まれている場合を考慮）
        if "```json" in response_text:
            json_start = response_text.find("```json") + 7
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()
        elif "```" in response_text:
            json_start = response_text.find("```") + 3
            json_end = response_text.find("```", json_start)
            response_text = response_text[json_start:json_end].strip()

        result = json.loads(response_text)

        # Feedbackオブジェクトを構築
        pss = PSSEvaluation(
            opening=EvaluationLevel(result["pss"]["opening"]["level"]),
            need_identification=EvaluationLevel(result["pss"]["need_identification"]["level"]),
            presentation=EvaluationLevel(result["pss"]["presentation"]["level"]),
            handling_objections=EvaluationLevel(result["pss"]["handling_objections"]["level"]),
            closing=EvaluationLevel(result["pss"]["closing"]["level"]),
            opening_comment=result["pss"]["opening"]["comment"],
            need_identification_comment=result["pss"]["need_identification"]["comment"],
            presentation_comment=result["pss"]["presentation"]["comment"],
            handling_objections_comment=result["pss"]["handling_objections"]["comment"],
            closing_comment=result["pss"]["closing"]["comment"],
        )

        ads = ADSEvaluation(
            adaptability=EvaluationLevel(result["ads"]["adaptability"]["level"]),
            rapport_building=EvaluationLevel(result["ads"]["rapport_building"]["level"]),
            value_delivery=EvaluationLevel(result["ads"]["value_delivery"]["level"]),
            adaptability_comment=result["ads"]["adaptability"]["comment"],
            rapport_building_comment=result["ads"]["rapport_building"]["comment"],
            value_delivery_comment=result["ads"]["value_delivery"]["comment"],
        )

        return Feedback(
            transcript=transcript,
            pss=pss,
            ads=ads,
            good_points=result["good_points"],
            improvement_points=result["improvement_points"],
            specific_advice=result["specific_advice"],
            next_goals=result["next_goals"],
        )

    def _get_default_criteria(self) -> str:
        """デフォルトの評価基準"""
        return """
## PSS (Professional Selling Skills) 評価項目

### オープニング（Opening）
- 自己紹介が明確か
- 通話の目的を伝えているか
- 相手の時間を確認しているか
評価: A=すべて満たす, B=基本的な要素を満たす, C=一部欠ける, D=不十分

### ニーズの把握（Need Identification）
- オープンクエスチョンを使っているか
- 相手の話を傾聴しているか
- 深掘り質問ができているか
評価: A=深いニーズまで引き出す, B=基本的なニーズを把握, C=表面的, D=不十分

### 提案（Presentation）
- ニーズに合った提案ができているか
- 具体的な情報を提供しているか
- メリットを明確に伝えているか
評価: A=完全にマッチ, B=適切だがやや不足, C=部分的にマッチ, D=一方的

### 反論対応（Handling Objections）
- 反論を否定せず受け止めているか
- 適切な回答・代替案を提示しているか
評価: A=機会に変えている, B=適切に対応, C=懸念が解消されていない, D=不適切

### クロージング（Closing）
- 次のアクションを明確にしているか
- 期限を設定しているか
- 相手の合意を得ているか
評価: A=明確なネクストステップと合意, B=やや曖昧, C=弱い, D=不明確

## ADS (Adaptive Dealer Selling) 評価項目

### 相手への適応（Adaptability）
- 相手のペースに合わせているか
- 専門用語の使い方が適切か

### 信頼関係構築（Rapport Building）
- 共感を示しているか
- 相手の立場を理解しているか

### 価値提供（Value Delivery）
- 相手にとってのメリットを明確にしているか
- 具体的な数字やデータを提示しているか
"""

    def export_feedback_csv(self, feedbacks: List[Feedback], output_path: Path) -> None:
        """フィードバック一覧をCSVにエクスポート"""
        rows = []
        for fb in feedbacks:
            rows.append(
                {
                    "date": fb.transcript.date,
                    "ca_id": fb.transcript.ca_id,
                    "ca_name": fb.transcript.ca_name or "",
                    "meeting_id": fb.transcript.meeting_id,
                    "overall_score": round(fb.overall_score, 2),
                    "overall_rating": fb.overall_rating.value,
                    "pss_opening": fb.pss.opening.value,
                    "pss_need_identification": fb.pss.need_identification.value,
                    "pss_presentation": fb.pss.presentation.value,
                    "pss_handling_objections": fb.pss.handling_objections.value,
                    "pss_closing": fb.pss.closing.value,
                    "ads_adaptability": fb.ads.adaptability.value,
                    "ads_rapport_building": fb.ads.rapport_building.value,
                    "ads_value_delivery": fb.ads.value_delivery.value,
                    "good_points": "; ".join(fb.good_points),
                    "improvement_points": "; ".join(fb.improvement_points),
                }
            )

        with open(output_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=rows[0].keys())
            writer.writeheader()
            writer.writerows(rows)
