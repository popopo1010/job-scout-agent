#!/usr/bin/env python3
"""
フィードバックシステム実行スクリプト

書き起こしファイルをLLMで分析してフィードバックを生成
"""

from pathlib import Path
import sys

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.feedback import FeedbackEngine


def main():
    """メイン処理"""
    # パス設定
    transcripts_dir = Path("data/sample/feedback/transcripts")
    criteria_path = Path("data/sample/feedback/pss_ads_criteria.md")
    output_dir = Path("data/exports/feedback")

    print("=" * 70)
    print("フィードバックシステム - LLM分析実行")
    print("=" * 70)
    print()

    # エンジン初期化（LLM使用）
    engine = FeedbackEngine(
        transcripts_dir=transcripts_dir,
        criteria_path=criteria_path,
        use_ai=True,  # Claude APIを使用
    )

    # 書き起こしファイルを確認
    pending_files = engine.loader.find_pending_files()
    print(f"処理対象ファイル: {len(pending_files)}件")
    for f in pending_files:
        print(f"  - {f.name}")
    print()

    # 処理実行
    print("▶ LLM分析を実行中...")
    feedbacks = engine.process_all_pending()
    print(f"  完了: {len(feedbacks)}件処理")
    print()

    # 結果表示
    for fb in feedbacks:
        print("=" * 70)
        print(fb.to_text_report())
        print()

    # サマリー
    print(engine.generate_summary_report())

    # エクスポート
    output_dir.mkdir(parents=True, exist_ok=True)
    engine.export_all_feedbacks(output_dir)
    print(f"\n▶ レポートを出力: {output_dir}")


if __name__ == "__main__":
    main()
