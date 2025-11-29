# 事業戦略

このディレクトリには、人材紹介事業の事業戦略に関するドキュメントを格納します。

事業戦略は、システム実装とは独立して随時更新・改善されるため、専用ディレクトリで管理します。

## ⭐ 投資家向けエグゼクティブサマリー

投資判断に必要な情報を1ページにまとめたサマリーを作成しました：

- **[エグゼクティブサマリー](EXECUTIVE_SUMMARY.md)** - 投資家向け（市場機会、競争優位性、財務予測、成長戦略を簡潔にまとめ）

詳細な戦略情報は、以下の各事業ディレクトリとドキュメントをご参照ください。

## 📁 ディレクトリ構成

```
strategy/
├── README.md                          # このファイル
├── EXECUTIVE_SUMMARY.md               # エグゼクティブサマリー（投資家向け）⭐
├── CHECKLIST.md                       # 定期チェックリスト
├── MONITORING_RESOURCES.md            # 監視リソース一覧
│
├── electrical-engineering/            # 電気工事士事業戦略 ⭐
│   ├── README.md
│   ├── 01-mission-vision.md
│   ├── 02-pest-analysis.md
│   ├── 03-competitor-analysis.md
│   ├── 04-swot-analysis.md
│   ├── 05-stakeholder-analysis.md
│   ├── 06-business-plan.md
│   ├── 07-kpi.md
│   ├── 08-roadmap.md
│   ├── 09-organization.md
│   ├── 10-market-analysis.md
│   ├── 11-risk-management.md
│   └── 12-financial-model.md
│
├── electrical-construction-management/ # 電気工事施工管理事業戦略 ⭐
│   ├── README.md
│   ├── 01-mission-vision.md
│   ├── 02-pest-analysis.md
│   ├── 03-competitor-analysis.md
│   ├── 04-swot-analysis.md
│   ├── 05-stakeholder-analysis.md
│   ├── 06-business-plan.md
│   ├── 07-kpi.md
│   ├── 08-roadmap.md
│   ├── 09-organization.md
│   ├── 10-market-analysis.md
│   ├── 11-risk-management.md
│   └── 12-financial-model.md
│
└── construction-management/           # 施工管理（一般）事業戦略 ⭐
    ├── README.md
    ├── 01-mission-vision.md
    ├── 02-pest-analysis.md
    ├── 03-competitor-analysis.md
    ├── 04-swot-analysis.md
    ├── 05-stakeholder-analysis.md
    ├── 06-business-plan.md
    ├── 07-kpi.md
    ├── 08-roadmap.md
    ├── 09-organization.md
    ├── 10-market-analysis.md
    ├── 11-risk-management.md
    └── 12-financial-model.md
```

## 🎯 3つの事業戦略

### 1. 電気工事士事業（electrical-engineering）

**対象資格**: 第一種・第二種電気工事士  
**単価**: 175万円/内定  
**FY25**: PMF達成目標  
**詳細**: [電気工事士事業戦略](electrical-engineering/README.md)

### 2. 電気工事施工管理事業（electrical-construction-management）

**対象資格**: 1級・2級電気工事施工管理技士  
**単価**: 240万円/内定  
**FY26**: PMF達成目標  
**詳細**: [電気工事施工管理事業戦略](electrical-construction-management/README.md)

### 3. 施工管理（一般）事業（construction-management）

**対象資格**: 建築、土木、電気工事、管工事、造園、建設機械等の施工管理技士全般  
**単価**: 240万円/内定  
**FY26**: PMF達成目標  
**詳細**: [施工管理（一般）事業戦略](construction-management/README.md)

---

## 📋 各ドキュメントの説明

各事業ディレクトリ内のドキュメント構成は統一されています：

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
| **12-financial-model.md** | 財務モデル、3年間P&L | 中（四半期ごと） |

---

## 🔄 更新フロー

### 定期更新
- **月次**: KPI実績の更新（各事業の`07-kpi.md`）
- **四半期**: 経営計画の見直し（各事業の`06-business-plan.md`）、ロードマップの更新（各事業の`08-roadmap.md`）
- **年次**: マーケット分析の更新（各事業の`10-market-analysis.md`）、PEST分析の見直し（各事業の`02-pest-analysis.md`）

### 随時更新
- 競合動向の変化 → 各事業の`03-competitor-analysis.md`
- 外部環境の変化 → 各事業の`02-pest-analysis.md`
- リスクの発生・変化 → 各事業の`11-risk-management.md`
- 組織変更 → 各事業の`09-organization.md`

---

## 🔍 自動チェック・監視

事業戦略の更新状況を自動チェックするスクリプトが利用可能です。

### ✅ 週1回自動チェック（設定済み）

毎週月曜日9時に自動実行されます：

```bash
# 手動でチェックを実行（テスト用）
python scripts/check_strategy_updates.py

# 自動実行の状態確認
launchctl list | grep strategy-check
```

詳細は [週1回自動チェックの設定状況](WEEKLY_CHECK_STATUS.md) を参照してください。

### 関連ドキュメント

- **[週1回自動チェックの設定状況](WEEKLY_CHECK_STATUS.md)** - 現在の設定状況と管理方法 ⭐
- **[定期チェックリスト](CHECKLIST.md)** - 月次/四半期/年次のチェック項目
- **[監視リソース一覧](MONITORING_RESOURCES.md)** - 市場データ、競合情報、法規制などのリソース
- **[自動更新セットアップ](AUTO_UPDATE_SETUP.md)** - 自動化のセットアップ方法

---

## 📝 更新時の注意事項

1. **更新履歴の記録**: 各ファイルの最終更新日を明記
2. **バージョン管理**: 重要な変更はGitでコミット
3. **関連ドキュメントの同期**: 関連するシステム仕様書（`spec/`）との整合性を保つ
4. **レビュー**: 戦略変更時は関係者のレビューを実施
5. **事業間の整合性**: 3つの事業間で共通する前提条件（CA生産性、展開率等）の整合性を保つ

---

## 🔗 関連ドキュメント

- **システム仕様**: `spec/00-specification.md` - システム実装の詳細
- **要件定義**: `spec/01-requirements.md` - システム要件
- **アーキテクチャ**: `spec/03-architecture.md` - システム設計
- **電気工事士**: `spec/09-audio-feedback-requirements.md` - 音声データフィードバック要件
- **電気施工管理**: `spec/10-electrical-construction-management-requirements.md` - 電気工事施工管理要件
- **施工管理（一般）**: `spec/11-construction-management-requirements.md` - 施工管理要件

---

## 📌 原則

- **事業戦略とシステム実装の分離**: 事業戦略は独立して管理し、システム実装に影響を与えない
- **随時更新の促進**: 戦略変更を迅速に反映できる構造
- **長期視点**: 3年、5年先を見据えた戦略策定
- **事業間の独立性**: 各事業は独立した戦略を持つが、共通の前提条件は整合性を保つ

---

*最終更新: 2025-01-15*
