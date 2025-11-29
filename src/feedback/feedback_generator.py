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
                comment = "すべての要素を満たしており、期待展開率8%を実現できるレベルです。"
            elif score >= 1:
                level = EvaluationLevel.B
                comment = "基本的な要素を満たしていますが、さらなる改善の余地があります。"
            elif score >= 0:
                level = EvaluationLevel.C
                comment = "一部の要素が不足しています。期待展開率8%を実現するには改善が必要です。"
            else:
                level = EvaluationLevel.D
                comment = "基本的な要素ができていません。根本的な見直しが必要です。"

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
                comment = "優れた対応ができており、信頼関係構築に成功しています。"
            elif score >= 1:
                level = EvaluationLevel.B
                comment = "良好な対応ですが、さらに工夫の余地があります。"
            elif score >= 0:
                level = EvaluationLevel.C
                comment = "標準的な対応です。期待展開率8%を実現するには改善が必要です。"
            else:
                level = EvaluationLevel.D
                comment = "対応が不十分です。信頼関係構築の基本を見直してください。"

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
        """評価できる点を抽出（営業マネージャー視点）"""
        good_points = []

        if pss.opening in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("適切な自己紹介と時間確認ができていた点は評価します。第一印象は良好でした。")

        if pss.need_identification in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("オープンクエスチョンを使ってニーズを引き出せていた点は成長の証です。ただし、より深い潜在ニーズまで引き出すことが期待展開率向上の鍵となります。")

        if pss.presentation in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("具体的な求人情報を提示できていた点は良いですが、相手の反応を見ながらより刺さる情報を選ぶセンスを磨いていけば、さらに効果的になります。")

        if pss.closing in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("明確なネクストステップを設定できていた点は評価します。この基本動作を継続することで、成約につながります。")

        if ads.rapport_building in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("求職者への共感を示せていた点は良いです。信頼関係構築の土台ができています。")

        if ads.value_delivery in (EvaluationLevel.A, EvaluationLevel.B):
            good_points.append("求人のメリットを具体的に伝えられていた点は評価します。さらに、相手のニーズに合わせてメリットを強調する工夫を加えれば、さらに効果的です。")

        return good_points[:3]  # 最大3つ

    def _extract_improvement_points(
        self, content: str, pss: PSSEvaluation, ads: ADSEvaluation
    ) -> List[str]:
        """必ず改善すべき点を抽出（営業マネージャー視点）"""
        improvements = []

        if pss.need_identification in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("【重要】ニーズの深掘りが不十分でした。表面的なニーズだけで提案を始めるのではなく、「なぜその求人を探しているのか」「本当の課題は何か」まで徹底的に引き出す必要があります。期待展開率8%を実現するには、潜在ニーズまで理解することが不可欠です。次回は、最低3回は深掘り質問を入れることを徹底してください。")

        if pss.handling_objections in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("【必須】反論や懸念への対応が弱かったです。相手の懸念を受け止めた後、具体的な解決策を提示できていない場面がありました。反論は成約のチャンスです。この点が改善されれば、確実に成果につながります。反論対応のフレームワークを再確認してください。")

        if pss.closing in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("【緊急】クロージング時の期限設定が曖昧でした。次のアクションが明確でないと、せっかく良い雰囲気で終わっても、成約につながりません。期待展開率8%を実現するためには、明確な期限設定と相手の合意取得は必須です。次回は絶対に改善してください。")

        if ads.adaptability in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("【必須】相手のペースに合わせたコミュニケーションができていませんでした。相手の理解度に応じて説明を調整することが、信頼関係構築につながります。次回は、相手の反応を見ながら会話のペースを調整してください。")

        if ads.value_delivery in (EvaluationLevel.C, EvaluationLevel.D):
            improvements.append("【重要】具体的な数字やメリットをより明確に伝える必要があります。抽象的な表現では、求職者の心に響きません。年収、残業時間、福利厚生など、具体的な数字を使ってメリットを提示してください。")

        return improvements[:3]  # 最大3つ

    def _generate_advice(self, pss: PSSEvaluation, ads: ADSEvaluation) -> str:
        """具体的な改善アクションを生成（営業マネージャー視点）"""
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
                    "1. 【オープニング】通話開始時には必ず以下を実行してください：\n"
                    "   - 自己紹介（名前・所属）\n"
                    "   - 通話の目的（何のための電話か）\n"
                    "   - 時間確認（話せる時間はあるか）\n"
                    "   これができていないと、他のすべてが台無しになります。"
                )
            elif lowest[0] == "ニーズ把握":
                advice_parts.append(
                    "1. 【ニーズ深掘り】通話中に必ず以下を実行してください：\n"
                    "   - 「なぜその求人を探していらっしゃるんですか？」（1回目）\n"
                    "   - 「具体的には、どのような課題をお感じですか？」（2回目）\n"
                    "   - 「他にも気になる点はありますか？」（3回目）\n"
                    "   これらを意識的に使うことで、潜在ニーズが見えてきます。"
                )
            elif lowest[0] == "提案":
                advice_parts.append(
                    "1. 【提案】年収・残業・仕事内容など、求職者のニーズに直結する情報を具体的に伝えましょう。\n"
                    "   抽象的な表現ではなく、「年収400万円、残業月20時間、電気工事の現場管理業務」のように具体的な数字と内容を提示してください。"
                )
            elif lowest[0] == "反論対応":
                advice_parts.append(
                    "1. 【反論対応】反論が出た際は、以下のフレームワークを必ず使ってください：\n"
                    "   - ステップ1: 「おっしゃる通りです。ご不安なお気持ち、よくわかります」（共感）\n"
                    "   - ステップ2: 「実は、多くの方から同じご質問をいただくのですが...」（一般化）\n"
                    "   - ステップ3: 「具体的には、こういうケースで...」（事例・解決策提示）\n"
                    "   - ステップ4: 「いかがでしょうか？」（確認・合意取得）"
                )
            elif lowest[0] == "クロージング":
                advice_parts.append(
                    "1. 【クロージング】通話終了前5分には必ず以下を実行：\n"
                    "   - 「では、次回までに○○を準備していただくということでよろしいですか？」\n"
                    "   - 「期限は今週金曜日17時まででお願いできますか？」\n"
                    "   - 「承諾いただけましたか？」（明確な合意取得）"
                )

        if not advice_parts:
            advice_parts.append(
                "全体的にバランスの取れた通話でした。さらなる向上のため、潜在ニーズの深掘りを意識しましょう。"
            )
        else:
            advice_parts.append(
                "\nこれらを徹底することで、期待展開率8%に近づけます。厳しく聞こえるかもしれませんが、"
                "これがKeyensのスタンダードです。あなたの成長を心から期待しています。"
            )

        return "\n".join(advice_parts)

    def _generate_goals(self, pss: PSSEvaluation, ads: ADSEvaluation) -> str:
        """次回必須改善目標を生成（営業マネージャー視点）"""
        overall_score = (sum([
            pss.opening.score, pss.need_identification.score, pss.presentation.score,
            pss.handling_objections.score, pss.closing.score,
            ads.adaptability.score, ads.rapport_building.score, ads.value_delivery.score
        ]) / 8)
        
        goals = []

        # スコアに応じて異なるレベルの目標を設定
        if overall_score < 1.5:
            # 要指導レベル：基本動作の徹底
            if pss.opening.score < 4:
                goals.append("【最優先】オープニングの3要素を必ず含める（自己紹介・目的・時間確認）。これができていないと、他のすべてが台無しになります。")
            if pss.need_identification.score < 4:
                goals.append("【必須】ニーズ把握で最低2回は深掘り質問をする（「なぜ？」「具体的には？」）。")
            if pss.closing.score < 4:
                goals.append("【必須】クロージングで期限を設定する。曖昧な終わり方では成約につながりません。")
            if goals:
                return "\n".join(goals) + "\n\nまずはこれらを完璧にできるようになりましょう。基本ができてから、次のステップに進みます。期待展開率8%を実現する道のりは厳しいですが、一歩ずつ確実に進んでください。"
        
        elif overall_score < 2.5:
            # 要改善レベル：最重要改善目標
            if pss.need_identification.score < 4:
                goals.append("深掘り質問を最低3回以上実施する。これを実行することで、ニーズ把握のスコアをB以上にできるはずです。")
            if pss.handling_objections.score < 4:
                goals.append("反論対応のフレームワークを1回以上使用する。反論が出た際に、上記のフレームワークを必ず使ってください。")
            if pss.closing.score < 4:
                goals.append("クロージング時に明確な期限を設定し、相手から合意を得る。「はい、承知しました」という明確な返答をもらうまで確認してください。")
            if goals:
                return "\n".join(goals) + "\n\nこれらができなければ、次回も同じ評価になります。厳しいですが、成長には厳しさが必要です。あなたの成長を信じて期待しています。"
        
        elif overall_score < 3.5:
            # 良好レベル：必須改善目標
            if pss.need_identification.score < 4:
                goals.append("深掘り質問を最低3回以上実施する。これを実行することで、ニーズ把握のスコアをB以上にできるはずです。")
            if pss.handling_objections.score < 4:
                goals.append("反論対応のフレームワークを1回以上使用する。反論が出た際に、上記のフレームワークを必ず使ってください。")
            if pss.closing.score < 4:
                goals.append("クロージング時に明確な期限を設定し、相手から合意を得る。期待展開率8%を実現するため、これらは必須です。")
            if goals:
                return "\n".join(goals) + "\n\n期待展開率8%を実現するため、これらは必須です。次回の通話で必ず達成してください。あなたの成長を期待しています。"
        
        else:
            # 優秀レベル：チャレンジ目標
            goals.append("潜在ニーズまで深掘りし、相手も気づいていなかった課題を引き出す")
            goals.append("反論を完全に機会に変え、成約率をさらに向上させる")
            goals.append("クロージングで期限を設定し、確実に次のステップに進む")
            return "\n".join(goals) + "\n\nあなたなら可能です。期待しています。"

        if not goals:
            goals.append("現状の質を維持しながら、より複雑なケースにも対応できるよう準備する")

        return goals[0] if goals else "現状の質を維持しながら、さらなる向上を目指してください。"

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

        prompt = f"""あなたはKeyensの営業マネージャーとして、メンバーの成長を期待しながらも厳しくも建設的なフィードバックを提供する役割を担っています。

## 重要な方針
- メンバーの成長を第一に考えるが、厳しさも忘れない
- 期待展開率8%を実現するために必要な基準を明確に示す
- 建設的で実行可能なフィードバックを提供
- 成長を信じて期待を込めた表現を使用

## 評価基準
{criteria_text}

## 書き起こし内容
{transcript.content}

## フィードバック生成の指示

### 1. 評価コメントの書き方
各項目の評価コメントは、以下のスタイルで書いてください：
- 評価が高い場合: 良い点を評価しつつ、さらなる改善の余地を示唆
- 評価が低い場合: なぜ低い評価なのか理由を明確に説明し、期待展開率8%との関連性を示す
- 常に具体的で、実行可能な改善アクションを提示

### 2. 良かった点
- 「適切な自己紹介と時間確認ができていた点は評価します。第一印象は良好でした。」
  のように、評価しつつもさらなる成長への期待を示す
- 最大3つ、具体的な行動や発言に基づいて記載

### 3. 改善点
- 「【重要】」「【必須】」「【緊急】」などの重要度マークを付ける
- なぜその改善が必要なのか（期待展開率8%との関連）を明確に
- 具体的な数値目標や行動を指定（例：「最低3回は深掘り質問を入れる」）
- 厳しいが建設的な表現を使用

### 4. 具体的な改善アドバイス
- 「具体的な改善アクション（次回通話までに必ず実行すること）」として記載
- ステップバイステップで実行可能な内容
- フレームワークや具体的なフレーズを含める

### 5. 次回に向けた目標
スコアに応じて厳しさを調整：
- 3.5以上: さらに上位10%を目指すチャレンジ目標
- 2.5-3.4: 必須改善目標（期待展開率8%達成のため必須）
- 1.5-2.4: 最重要改善目標（基本動作の徹底）
- 1.5未満: 緊急改善目標（営業の基本を見直す）

## 出力形式
以下のJSON形式で出力してください。評価レベルは A/B/C/D のいずれかで指定してください。

```json
{{
  "pss": {{
    "opening": {{"level": "A/B/C/D", "comment": "評価コメント（なぜその評価なのか理由を明記）"}},
    "need_identification": {{"level": "A/B/C/D", "comment": "評価コメント（期待展開率との関連性を含める）"}},
    "presentation": {{"level": "A/B/C/D", "comment": "評価コメント（改善アクションを含める）"}},
    "handling_objections": {{"level": "A/B/C/D", "comment": "評価コメント（具体的な改善方法を含める）"}},
    "closing": {{"level": "A/B/C/D", "comment": "評価コメント（基本動作としての重要性を示す）"}}
  }},
  "ads": {{
    "adaptability": {{"level": "A/B/C/D", "comment": "評価コメント"}},
    "rapport_building": {{"level": "A/B/C/D", "comment": "評価コメント"}},
    "value_delivery": {{"level": "A/B/C/D", "comment": "評価コメント"}}
  }},
  "good_points": ["評価できる点1（評価しつつ成長への期待を示す）", "評価できる点2", "評価できる点3"],
  "improvement_points": ["【重要/必須/緊急】改善点1（理由と期待展開率との関連を含む）", "改善点2", "改善点3"],
  "specific_advice": "具体的な改善アクション。ステップバイステップで実行可能な内容。フレームワークや具体的なフレーズを含める。期待展開率8%達成のため必須。",
  "next_goals": "次回通話での必須改善目標。スコアに応じた適切な厳しさで、具体的な数値目標や行動を指定。成長を信じて期待を込めた表現。"
}}
```

JSONのみを出力し、それ以外のテキストは含めないでください。
"""

        message = client.messages.create(
            model="claude-3-5-sonnet-20241022",  # 最新のClaude 3.5 Sonnetモデル
            max_tokens=4000,  # より長いレスポンスに対応
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
