#!/usr/bin/env python3
"""
サンプルデータを使用した動作確認デモ

3つのサブシステムの動作を確認:
1. 経営分析基盤 - セグメント分類・CA別パフォーマンス
2. フィードバックシステム - 書き起こし分析・レポート生成
3. 求人データ整備 - 法人比較・新規検出
"""

from pathlib import Path


def demo_analytics():
    """経営分析基盤のデモ"""
    print("\n" + "=" * 70)
    print("【システム1】経営分析基盤")
    print("=" * 70)

    from src.analytics import AnalyticsEngine

    # エンジン初期化
    data_dir = Path("data/sample/analytics")
    engine = AnalyticsEngine(data_dir=data_dir)

    # データ読み込み
    print("\n▶ サンプルデータを読み込み中...")
    leads = engine.load_leads_from_csv()
    cas = engine.load_cas_from_csv()
    engine.assign_leads_to_cas()

    print(f"  - リード件数: {len(leads)}件")
    print(f"  - CA数: {len(cas)}名")

    # セグメント別レポート
    print("\n" + engine.generate_segment_report())

    # CA別レポート
    print("\n" + engine.generate_ca_report())

    # 新規リードの振り分け提案デモ
    from src.analytics.models import Lead

    print("\n▶ 新規リード振り分け提案:")
    new_lead = Lead(
        lead_id="NEW001",
        name="テスト太郎",
        age=32,
        prefecture="東京都",
        qualification="第一種電気工事士",
        has_qualification=True,
        assigned_ca_id="",
        status="new",
    )

    suggestions = engine.get_lead_allocation_suggestion(new_lead)
    print(f"  新規リード: {new_lead.name} ({new_lead.age}歳, 資格あり)")
    print(f"  → セグメント: {new_lead.segment_id.value} (期待展開率: {new_lead.conversion_rate:.0%})")
    print("\n  推奨振り分け先:")
    for i, s in enumerate(suggestions[:3], 1):
        print(
            f"  {i}. {s['name']} ({s['team']}) - "
            f"空き{s['vacancy']}件, 達成率{s['achievement_rate']:.0%}"
        )


def demo_feedback():
    """フィードバックシステムのデモ"""
    print("\n" + "=" * 70)
    print("【システム2】フィードバックシステム")
    print("=" * 70)

    from src.feedback import FeedbackEngine

    # エンジン初期化
    transcripts_dir = Path("data/sample/feedback/transcripts")
    criteria_path = Path("data/sample/feedback/pss_ads_criteria.md")

    engine = FeedbackEngine(
        transcripts_dir=transcripts_dir,
        criteria_path=criteria_path,
        use_ai=False,  # ルールベース評価を使用
    )

    # 書き起こしを処理
    print("\n▶ 書き起こしファイルを処理中...")
    feedbacks = engine.process_all_pending()
    print(f"  - 処理件数: {len(feedbacks)}件")

    # 個別フィードバック表示
    for fb in feedbacks:
        print("\n" + "-" * 50)
        print(fb.to_text_report())

    # サマリーレポート
    print("\n" + engine.generate_summary_report())


def demo_job_data():
    """求人データ整備のデモ"""
    print("\n" + "=" * 70)
    print("【システム3】求人データ整備")
    print("=" * 70)

    from src.job_data import JobDataEngine

    # エンジン初期化
    data_dir = Path("data/sample/job_data")
    engine = JobDataEngine(data_dir=data_dir)

    # データ読み込み
    print("\n▶ サンプルデータを読み込み中...")
    engine.load_all_data()

    print(f"  - スクレイピング求人: {len(engine.scraped_jobs)}件")
    print(f"  - 自社保有求人: {len(engine.owned_jobs)}件")
    print(f"  - 既存法人: {len(engine.existing_companies)}社")

    # 新規法人検出
    print("\n" + engine.generate_new_companies_report())

    # 新規エリア検出
    print("\n" + engine.generate_new_areas_report())

    # 給与比較レポート
    print("\n" + engine.generate_salary_comparison_report())


def main():
    """メインエントリーポイント"""
    print("=" * 70)
    print("人材紹介事業 AIエージェントシステム - デモ実行")
    print("=" * 70)

    try:
        # 経営分析基盤
        demo_analytics()
    except Exception as e:
        print(f"\n[エラー] 経営分析基盤: {e}")

    try:
        # フィードバックシステム
        demo_feedback()
    except Exception as e:
        print(f"\n[エラー] フィードバックシステム: {e}")

    try:
        # 求人データ整備
        demo_job_data()
    except Exception as e:
        print(f"\n[エラー] 求人データ整備: {e}")

    print("\n" + "=" * 70)
    print("デモ完了")
    print("=" * 70)


if __name__ == "__main__":
    main()
