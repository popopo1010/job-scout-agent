# 事業戦略

このディレクトリには、人材紹介事業の事業戦略に関するドキュメントを格納します。

事業戦略は、システム実装とは独立して随時更新・改善されるため、専用ディレクトリで管理します。

## 📁 ディレクトリ構成

```
strategy/
├── README.md                          # このファイル
├── CHECKLIST.md                       # 定期チェックリスト
├── MONITORING_RESOURCES.md            # 監視リソース一覧
├── 01-mission-vision.md               # Mission/Vision
├── 02-pest-analysis.md                # PEST分析（外部環境分析）
├── 03-competitor-analysis.md          # 競合分析・差別化要因
├── 04-swot-analysis.md                # SWOT分析
├── 05-stakeholder-analysis.md         # ステークホルダー分析
├── 06-business-plan.md                # 経営計画（経営P）
├── 07-kpi.md                          # 成功指標（KPI）
├── 08-roadmap.md                      # ロードマップ・マイルストーン
├── 09-organization.md                 # 組織体制・役割分担
├── 10-market-analysis.md              # マーケットサイズ分析
└── 11-risk-management.md              # リスク管理・前提条件
```

## 📋 各ドキュメントの説明

| ファイル | 内容 | 更新頻度 |
|---------|------|---------|
| **01-mission-vision.md** | プロジェクトの使命、ビジョン、価値提供 | 低（基本方針） |
| **02-pest-analysis.md** | 政治・経済・社会・技術の外部環境分析 | 中（外部環境変化時） |
| **03-competitor-analysis.md** | 競合分析、USP、差別化要因 | 中（競合動向確認時） |
| **04-swot-analysis.md** | 強み・弱み・機会・脅威の分析 | 中（戦略見直し時） |
| **05-stakeholder-analysis.md** | ステークホルダー分析、エンゲージメント戦略 | 低 |
| **06-business-plan.md** | 経営計画（Marketing/Cost/CA/RA/OPS） | 高（四半期ごと） |
| **07-kpi.md** | 成功指標、目標値 | 高（月次/四半期ごと） |
| **08-roadmap.md** | ロードマップ、マイルストーン | 中（四半期ごと） |
| **09-organization.md** | 組織体制、役割分担 | 中（組織変更時） |
| **10-market-analysis.md** | マーケットサイズ分析、市場予測 | 中（年次） |
| **11-risk-management.md** | リスク管理、前提条件、制約事項 | 中（リスク発生時） |

## 🔄 更新フロー

### 定期更新
- **月次**: KPI実績の更新（`07-kpi.md`）
- **四半期**: 経営計画の見直し（`06-business-plan.md`）、ロードマップの更新（`08-roadmap.md`）
- **年次**: マーケット分析の更新（`10-market-analysis.md`）、PEST分析の見直し（`02-pest-analysis.md`）

### 随時更新
- 競合動向の変化 → `03-competitor-analysis.md`
- 外部環境の変化 → `02-pest-analysis.md`
- リスクの発生・変化 → `11-risk-management.md`
- 組織変更 → `09-organization.md`

## 🔍 自動チェック

事業戦略の更新状況を自動チェックするスクリプトが利用可能です：

```bash
# 事業戦略の更新チェックを実行
python scripts/check_strategy_updates.py
```

詳細は以下を参照：
- [定期チェックリスト](CHECKLIST.md)
- [監視リソース一覧](MONITORING_RESOURCES.md)

## 📝 更新時の注意事項

1. **更新履歴の記録**: 各ファイルの最終更新日を明記
2. **バージョン管理**: 重要な変更はGitでコミット
3. **関連ドキュメントの同期**: 関連するシステム仕様書（`spec/`）との整合性を保つ
4. **レビュー**: 戦略変更時は関係者のレビューを実施

## 🔗 関連ドキュメント

- **システム仕様**: `spec/00-specification.md` - システム実装の詳細
- **要件定義**: `spec/01-requirements.md` - システム要件
- **アーキテクチャ**: `spec/03-architecture.md` - システム設計

## 📌 原則

- **事業戦略とシステム実装の分離**: 事業戦略は独立して管理し、システム実装に影響を与えない
- **随時更新の促進**: 戦略変更を迅速に反映できる構造
- **長期視点**: 3年、5年先を見据えた戦略策定

---

*最終更新: 2025年11月30日*

