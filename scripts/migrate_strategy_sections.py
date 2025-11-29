#!/usr/bin/env python3
"""
spec/00-specification.mdから事業戦略セクションを抽出して、
strategy/ファイルに移行するスクリプト
"""

import re
from pathlib import Path
from typing import Tuple, List

project_root = Path(__file__).parent.parent
spec_file = project_root / "spec" / "00-specification.md"
strategy_dir = project_root / "strategy"


def extract_section(content: str, start_pattern: str, end_pattern: str = None) -> Tuple[str, int, int]:
    """
    セクションを抽出
    
    Returns:
        (section_content, start_line, end_line)
    """
    lines = content.split('\n')
    start_line = None
    end_line = None
    
    # 開始行を探す
    for i, line in enumerate(lines):
        if re.search(start_pattern, line):
            start_line = i
            break
    
    if start_line is None:
        return None, None, None
    
    # 終了行を探す
    if end_pattern:
        for i in range(start_line + 1, len(lines)):
            if re.search(end_pattern, lines[i]):
                end_line = i - 1
                break
    else:
        # 次の## セクションまで
        for i in range(start_line + 1, len(lines)):
            if lines[i].startswith('## ') and not lines[i].startswith('###'):
                end_line = i - 1
                break
    
    if end_line is None:
        end_line = len(lines) - 1
    
    section_lines = lines[start_line:end_line + 1]
    return '\n'.join(section_lines), start_line + 1, end_line + 1


def update_strategy_file(file_path: Path, new_content: str, header: str = None):
    """戦略ファイルを更新"""
    if file_path.exists():
        current = file_path.read_text(encoding='utf-8')
        # 既存の内容を保持して、新しい内容に置き換え
        if "詳細は元のspec/00-specification.mdから抽出・移動予定です" in current:
            # 簡潔版を完全版に置き換え
            if header:
                new_full_content = f"{header}\n\n{new_content}\n\n---\n\n*最終更新: 2025年11月30日*\n"
            else:
                new_full_content = f"{new_content}\n\n---\n\n*最終更新: 2025年11月30日*\n"
            file_path.write_text(new_full_content, encoding='utf-8')
            return True
    return False


def main():
    """メイン処理"""
    print("事業戦略セクションの移行を開始します...")
    
    spec_content = spec_file.read_text(encoding='utf-8')
    
    # PEST分析を抽出
    print("\n1. PEST分析を抽出中...")
    pest_content, start, end = extract_section(
        spec_content,
        r'^## 2\.4 PEST分析',
        r'^## 3\.'
    )
    if pest_content:
        print(f"   PEST分析: {start}-{end}行を抽出")
        header = "# PEST分析\n\n電気工事士・電気施工管理人材紹介事業の外部環境分析\n"
        update_strategy_file(strategy_dir / "02-pest-analysis.md", pest_content.replace("## 2.4 PEST分析", "## PEST分析"), header)
        print("   ✅ strategy/02-pest-analysis.mdを更新しました")
    
    # 競合分析を抽出
    print("\n2. 競合分析を抽出中...")
    competitor_content, start, end = extract_section(
        spec_content,
        r'^## 10\. 競合分析',
        r'^## 11\.'
    )
    if competitor_content:
        print(f"   競合分析: {start}-{end}行を抽出")
        header = "# 競合分析・差別化要因\n\n主要競合の詳細分析とUSPについて記載\n"
        update_strategy_file(strategy_dir / "03-competitor-analysis.md", competitor_content.replace("## 10. 競合分析・差別化要因", "## 競合分析・差別化要因"), header)
        print("   ✅ strategy/03-competitor-analysis.mdを更新しました")
    
    # マーケットサイズ分析を抽出
    print("\n3. マーケットサイズ分析を抽出中...")
    market_content, start, end = extract_section(
        spec_content,
        r'^## 19\. マーケットサイズ分析',
        r'^## 20\.'
    )
    if market_content:
        print(f"   マーケットサイズ分析: {start}-{end}行を抽出")
        header = "# マーケットサイズ分析\n\n電気工事士人材紹介市場のサイズ分析と予測\n"
        update_strategy_file(strategy_dir / "10-market-analysis.md", market_content.replace("## 19. マーケットサイズ分析", "## マーケットサイズ分析"), header)
        print("   ✅ strategy/10-market-analysis.mdを更新しました")
    
    print("\n✅ 移行が完了しました！")


if __name__ == "__main__":
    main()

