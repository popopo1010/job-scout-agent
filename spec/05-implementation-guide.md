# 実装ガイド

## 1. 開発環境セットアップ

### 1.1 必要条件
- Python 3.11以上
- Git
- 各種APIアカウント（Anthropic, OpenAI, Zoom, Slack）

### 1.2 初期セットアップ

```bash
# リポジトリクローン
git clone <repository-url>
cd job-scout-agent

# 仮想環境作成
python -m venv .venv
source .venv/bin/activate

# 依存関係インストール
pip install -e ".[dev]"

# 環境変数設定
cp .env.example .env
# .envを編集してAPIキーを設定
```

### 1.3 IDE設定（VS Code推奨）

```json
// .vscode/settings.json
{
  "python.defaultInterpreterPath": ".venv/bin/python",
  "python.linting.enabled": true,
  "python.linting.ruffEnabled": true,
  "python.formatting.provider": "black",
  "editor.formatOnSave": true
}
```

---

## 2. コーディング規約

### 2.1 スタイルガイド

- **フォーマッタ**: Black（デフォルト設定）
- **リンター**: Ruff
- **型チェック**: mypy（strict mode）

### 2.2 命名規則

| 対象 | 規則 | 例 |
|------|------|-----|
| クラス | PascalCase | `SegmentAnalyzer` |
| 関数/メソッド | snake_case | `calculate_rate()` |
| 変数 | snake_case | `lead_count` |
| 定数 | UPPER_SNAKE | `MAX_RETRY_COUNT` |
| プライベート | 先頭アンダースコア | `_internal_method()` |

### 2.3 ドキュメンテーション

```python
def calculate_expectation_rate(
    segment: Segment,
    historical_data: list[LeadResult]
) -> float:
    """セグメントの期待展開率を計算する。

    Args:
        segment: 分析対象のセグメント
        historical_data: 過去の展開実績データ

    Returns:
        期待展開率（0.0〜1.0）

    Raises:
        InsufficientDataError: データが不足している場合
    """
    pass
```

### 2.4 エラーハンドリング

```python
# カスタム例外の定義
class JobScoutError(Exception):
    """基底例外クラス"""
    pass

class APIError(JobScoutError):
    """外部API関連エラー"""
    pass

class DataValidationError(JobScoutError):
    """データ検証エラー"""
    pass

# 使用例
try:
    result = zoom_client.get_recordings()
except ZoomAPIError as e:
    logger.error(f"Zoom API error: {e}")
    raise APIError("録音データの取得に失敗しました") from e
```

---

## 3. モジュール実装パターン

### 3.1 共通基盤モジュール

#### Config（設定管理）

```python
# src/common/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # API Keys
    anthropic_api_key: str
    openai_api_key: str
    slack_bot_token: str

    # Zoom OAuth
    zoom_client_id: str
    zoom_client_secret: str

    # Database
    database_url: str = "sqlite:///data/app.db"

    # Feature flags
    debug_mode: bool = False

    class Config:
        env_file = ".env"

settings = Settings()
```

#### Logger

```python
# src/common/logger.py
import logging
from logging.handlers import RotatingFileHandler

def setup_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.INFO)

    # Console handler
    console = logging.StreamHandler()
    console.setFormatter(logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    ))
    logger.addHandler(console)

    # File handler
    file_handler = RotatingFileHandler(
        'logs/app.log',
        maxBytes=10*1024*1024,
        backupCount=5
    )
    logger.addHandler(file_handler)

    return logger
```

#### Database

```python
# src/common/database.py
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from .config import settings

engine = create_engine(settings.database_url)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

### 3.2 外部連携クライアント

#### Claude AIクライアント

```python
# src/common/ai_client.py
from anthropic import Anthropic

from .config import settings
from .logger import setup_logger

logger = setup_logger(__name__)

class AIClient:
    def __init__(self):
        self.client = Anthropic(api_key=settings.anthropic_api_key)

    def analyze(self, prompt: str, context: str) -> str:
        """Claude AIで分析を実行"""
        try:
            response = self.client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=4096,
                messages=[
                    {"role": "user", "content": f"{context}\n\n{prompt}"}
                ]
            )
            return response.content[0].text
        except Exception as e:
            logger.error(f"AI analysis failed: {e}")
            raise
```

#### Slackクライアント

```python
# src/integrations/slack.py
from slack_sdk import WebClient
from slack_sdk.errors import SlackApiError

from src.common.config import settings
from src.common.logger import setup_logger

logger = setup_logger(__name__)

class SlackClient:
    def __init__(self):
        self.client = WebClient(token=settings.slack_bot_token)

    def send_message(self, channel: str, text: str, blocks: list = None):
        """メッセージを送信"""
        try:
            response = self.client.chat_postMessage(
                channel=channel,
                text=text,
                blocks=blocks
            )
            return response
        except SlackApiError as e:
            logger.error(f"Slack API error: {e.response['error']}")
            raise

    def send_dm(self, user_id: str, text: str, blocks: list = None):
        """DMを送信"""
        return self.send_message(channel=user_id, text=text, blocks=blocks)
```

---

## 4. テスト方針

### 4.1 テスト構成

```
tests/
├── conftest.py              # 共通fixture
├── unit/                    # ユニットテスト
│   ├── test_analytics/
│   ├── test_feedback/
│   └── test_job_data/
├── integration/             # 統合テスト
│   ├── test_zoom_integration.py
│   └── test_slack_integration.py
└── e2e/                     # E2Eテスト
```

### 4.2 テスト例

```python
# tests/unit/test_analytics/test_segment_analyzer.py
import pytest
from src.analytics.segment_analyzer import SegmentAnalyzer
from src.analytics.models import Segment

class TestSegmentAnalyzer:
    @pytest.fixture
    def analyzer(self):
        return SegmentAnalyzer()

    def test_calculate_rate_with_sufficient_data(self, analyzer):
        segment = Segment(
            area="東京",
            age_group="30代",
            qualification="第一種電気工事士"
        )
        # モックデータ準備
        rate = analyzer.calculate_rate(segment)
        assert 0.0 <= rate <= 1.0

    def test_calculate_rate_with_insufficient_data(self, analyzer):
        segment = Segment(
            area="未知のエリア",
            age_group="未知",
            qualification="未知"
        )
        with pytest.raises(InsufficientDataError):
            analyzer.calculate_rate(segment)
```

### 4.3 モック/スタブ

```python
# tests/conftest.py
import pytest
from unittest.mock import Mock, patch

@pytest.fixture
def mock_ai_client():
    with patch('src.common.ai_client.AIClient') as mock:
        mock_instance = Mock()
        mock_instance.analyze.return_value = "分析結果"
        mock.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_slack_client():
    with patch('src.integrations.slack.SlackClient') as mock:
        mock_instance = Mock()
        mock_instance.send_dm.return_value = {"ok": True}
        mock.return_value = mock_instance
        yield mock_instance
```

---

## 5. Git運用

### 5.1 ブランチ戦略

```
main          # 本番リリース
  └── develop # 開発ブランチ
       ├── feature/analytics-segment   # 機能開発
       ├── feature/feedback-zoom       # 機能開発
       └── fix/slack-notification      # バグ修正
```

### 5.2 コミットメッセージ

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Type:**
- `feat`: 新機能
- `fix`: バグ修正
- `docs`: ドキュメント
- `refactor`: リファクタリング
- `test`: テスト
- `chore`: その他

**例:**
```
feat(analytics): セグメント分析機能を実装

- エリア×年齢×資格の掛け合わせ分析
- 期待展開率の計算ロジック

Refs: #10
```

---

## 6. 依存関係管理

### 6.1 pyproject.toml

```toml
[project]
dependencies = [
    "anthropic>=0.18.0",
    "openai>=1.0.0",
    "slack-sdk>=3.20.0",
    "sqlalchemy>=2.0.0",
    "pydantic>=2.0.0",
    "pydantic-settings>=2.0.0",
    "httpx>=0.25.0",
    "beautifulsoup4>=4.12.0",
    "apscheduler>=3.10.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=7.4.0",
    "pytest-cov>=4.1.0",
    "ruff>=0.1.0",
    "mypy>=1.5.0",
    "black>=23.9.0",
]
```

---

*最終更新: 2025-01-15*
