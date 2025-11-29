#!/usr/bin/env python3
"""
参考資料ファイルを追加して、CAマニュアルに自動リンクを追加するスクリプト
"""

import sys
from pathlib import Path

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))


def update_ca_manual(reference_dir: Path, ca_manual_path: Path) -> None:
    """CAマニュアルの参考資料セクションを更新"""
    # 参考資料ディレクトリのファイルをスキャン
    pdf_files = sorted(reference_dir.glob("*.pdf"))
    ppt_files = sorted(reference_dir.glob("*.ppt*"))
    
    # CAマニュアルを読み込む
    content = ca_manual_path.read_text(encoding="utf-8")
    
    # 既存のローカルファイルセクションを探す
    section_start = "### CA運作用資料（ローカルファイル）\n\n"
    section_end = "\n\n### by エス・エム・エス"
    
    if section_start not in content:
        print("⚠️  CAマニュアルに該当セクションが見つかりませんでした")
        return
    
    start_idx = content.find(section_start) + len(section_start)
    end_idx = content.find(section_end)
    
    if end_idx == -1:
        print("⚠️  セクションの終了位置が見つかりませんでした")
        return
    
    # 新しいリストを作成
    lines = []
    
    # PDFファイル
    for pdf_file in pdf_files:
        relative_path = pdf_file.relative_to(ca_manual_path.parent)
        filename = pdf_file.name
        # ファイル名から説明を生成（拡張子を除く）
        description = filename.replace(".pdf", "").replace("-", " ").replace("_", " ")
        lines.append(f"- [{filename}](./{relative_path}) - {description}")
    
    # PPTファイル
    for ppt_file in ppt_files:
        relative_path = ppt_file.relative_to(ca_manual_path.parent)
        filename = ppt_file.name
        # ファイル名から説明を生成（拡張子を除く）
        description = filename.replace(".pptx", "").replace(".ppt", "").replace("-", " ").replace("_", " ")
        lines.append(f"- [{filename}](./{relative_path}) - {description}")
    
    # セクションを置き換え
    new_section = "\n".join(lines) + "\n"
    new_content = content[:start_idx] + new_section + content[end_idx:]
    
    # ファイルを保存
    ca_manual_path.write_text(new_content, encoding="utf-8")
    print(f"✅ CAマニュアルを更新しました: {ca_manual_path}")


def main():
    """メイン処理"""
    import argparse
    
    parser = argparse.ArgumentParser(description="参考資料ファイルを追加してCAマニュアルを更新")
    parser.add_argument(
        "--reference-dir",
        type=Path,
        default=Path("docs/references/ca-operations"),
        help="参考資料ディレクトリ",
    )
    parser.add_argument(
        "--ca-manual",
        type=Path,
        default=Path("docs/ca-manual.md"),
        help="CAマニュアルファイルのパス",
    )
    parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="追加するファイル（省略時はディレクトリ内の全ファイルを確認）",
    )
    
    args = parser.parse_args()
    
    print("=" * 70)
    print("参考資料ファイル追加・CAマニュアル更新")
    print("=" * 70)
    print()
    
    # ディレクトリを確認
    if not args.reference_dir.exists():
        print(f"❌ ディレクトリが見つかりません: {args.reference_dir}")
        sys.exit(1)
    
    # ファイルが指定された場合はコピー
    if args.files:
        print("📁 ファイルをコピー中...")
        for source_file in args.files:
            if not source_file.exists():
                print(f"⚠️  ファイルが見つかりません: {source_file}")
                continue
            
            target_file = args.reference_dir / source_file.name
            if target_file.exists():
                print(f"⚠️  既に存在します: {target_file.name}")
                continue
            
            import shutil
            shutil.copy2(source_file, target_file)
            print(f"✅ コピーしました: {source_file.name} → {target_file}")
        print()
    
    # 現在のファイル一覧を表示
    pdf_files = sorted(args.reference_dir.glob("*.pdf"))
    ppt_files = sorted(args.reference_dir.glob("*.ppt*"))
    
    print(f"📊 参考資料ディレクトリ: {args.reference_dir}")
    print(f"   PDFファイル: {len(pdf_files)}件")
    print(f"   PPTファイル: {len(ppt_files)}件")
    print()
    
    if pdf_files or ppt_files:
        print("📋 ファイル一覧:")
        for pdf_file in pdf_files:
            print(f"   📄 {pdf_file.name}")
        for ppt_file in ppt_files:
            print(f"   📊 {ppt_file.name}")
        print()
    
    # CAマニュアルを更新
    print("📝 CAマニュアルを更新中...")
    update_ca_manual(args.reference_dir, args.ca_manual)
    
    print()
    print("✅ 完了しました！")


if __name__ == "__main__":
    main()

