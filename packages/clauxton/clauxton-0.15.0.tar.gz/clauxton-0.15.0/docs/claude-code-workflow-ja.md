# Claude Code × Clauxton 実践ワークフロー

**新規プロジェクトでMCPを使い、KB/Taskに基づいてコード生成・テストする完全ガイド**

このガイドでは、実際の新規プロジェクトを例に、Claude Codeが自動的にClauxtonのMCPツールを使いながら開発を進める流れを、**実際のコマンドとClaude Codeの応答付き**で解説します。

---

## 📋 前提条件

以下がすでに完了していることを前提とします：

- Clauxtonインストール済み（`pip install clauxton[semantic]`）
- プロジェクトで `clauxton init` 実行済み
- MCP設定完了（`clauxton mcp setup`）
- Claude Code 再起動済み

**まだの方は**: [getting-started-ja.md](getting-started-ja.md) を参照してください（5分で完了）

---

## 🎯 実践シナリオ: ToDoアプリAPI開発

このガイドでは、FastAPI を使った ToDo アプリ API を例に、以下を実践します：

1. プロジェクト要件を知識ベースに記録
2. タスクを分解して管理
3. Claude Codeがコードを自動生成
4. テスト実行と修正

---

## Phase 1: プロジェクト要件の定義（知識ベースへの登録）

### Step 1-1: Claude Code との初回会話

**あなた（ユーザー）**:
```
新しいプロジェクトを始めます。以下の要件があります：

- FastAPI を使った REST API
- PostgreSQL をデータベースに使用
- ユーザー認証に JWT を使用
- Python 3.11+ 必須
- すべての関数に型ヒント必須
- Pytest でテストカバレッジ 90% 以上

これらを記録してください。
```

**Claude Code の動作**:

Claude Codeは自動的に以下のMCPツールを呼び出します：

```
🔧 Tool: kb_add()
Arguments:
  title: "FastAPI をバックエンドフレームワークに採用"
  category: "architecture"
  content: "REST API のバックエンドは FastAPI で実装します。"
  tags: ["fastapi", "backend", "api"]

✓ Result: KB-20251028-001

🔧 Tool: kb_add()
Arguments:
  title: "PostgreSQL をデータベースに使用"
  category: "architecture"
  content: "本番環境では PostgreSQL を使用します。"
  tags: ["database", "postgresql"]

✓ Result: KB-20251028-002

🔧 Tool: kb_add()
Arguments:
  title: "JWT 認証を使用"
  category: "architecture"
  content: "ユーザー認証には JWT トークンを使用します。"
  tags: ["jwt", "auth", "security"]

✓ Result: KB-20251028-003

🔧 Tool: kb_add()
Arguments:
  title: "Python 3.11+ 必須"
  category: "constraint"
  content: "このプロジェクトは Python 3.11 以降を必須とします。"
  tags: ["python", "version"]

✓ Result: KB-20251028-004

🔧 Tool: kb_add()
Arguments:
  title: "型ヒント必須"
  category: "convention"
  content: "すべての関数に型ヒント（引数と戻り値）を必須とします。"
  tags: ["python", "typing", "convention"]

✓ Result: KB-20251028-005

🔧 Tool: kb_add()
Arguments:
  title: "テストカバレッジ 90% 以上"
  category: "convention"
  content: "Pytest でテストカバレッジ 90% 以上を維持します。"
  tags: ["testing", "pytest", "coverage"]

✓ Result: KB-20251028-006
```

**Claude Code の応答**:
```
了解しました。以下の6つの要件を知識ベースに記録しました：

- KB-20251028-001: FastAPI をバックエンドフレームワークに採用
- KB-20251028-002: PostgreSQL をデータベースに使用
- KB-20251028-003: JWT 認証を使用
- KB-20251028-004: Python 3.11+ 必須
- KB-20251028-005: 型ヒント必須
- KB-20251028-006: テストカバレッジ 90% 以上

次に、実装すべきタスクを提案します：

1. プロジェクト構造のセットアップ
2. データベースモデルの定義
3. FastAPI アプリケーションの初期化
4. JWT 認証の実装
5. CRUD エンドポイントの実装
6. テストの作成

これらをタスクとして追加しますか？
```

### Step 1-2: タスク追加

**あなた**:
```
はい、タスクを追加してください。優先度も設定してください。
```

**Claude Code の動作**:

```
🔧 Tool: task_add()
Arguments:
  name: "プロジェクト構造のセットアップ"
  priority: "high"
  status: "pending"
  description: "pyproject.toml, ディレクトリ構成、依存関係の設定"
  tags: ["setup", "infrastructure"]

✓ Result: TASK-001

🔧 Tool: task_add()
Arguments:
  name: "データベースモデルの定義"
  priority: "high"
  status: "pending"
  description: "SQLAlchemy モデル（User, Todo）の定義"
  tags: ["database", "models"]
  depends_on: ["TASK-001"]

✓ Result: TASK-002

🔧 Tool: task_add()
Arguments:
  name: "FastAPI アプリケーション初期化"
  priority: "high"
  status: "pending"
  description: "main.py の作成、ルーターの設定、CORS設定"
  tags: ["fastapi", "api"]
  depends_on: ["TASK-001"]

✓ Result: TASK-003

🔧 Tool: task_add()
Arguments:
  name: "JWT 認証の実装"
  priority: "high"
  status: "pending"
  description: "JWT トークン生成、認証ミドルウェア、依存関係の作成"
  tags: ["auth", "jwt", "security"]
  depends_on: ["TASK-002", "TASK-003"]

✓ Result: TASK-004

🔧 Tool: task_add()
Arguments:
  name: "ToDo CRUD エンドポイント実装"
  priority: "medium"
  status: "pending"
  description: "GET/POST/PUT/DELETE エンドポイントの実装"
  tags: ["api", "crud"]
  depends_on: ["TASK-004"]

✓ Result: TASK-005

🔧 Tool: task_add()
Arguments:
  name: "テストの作成"
  priority: "medium"
  status: "pending"
  description: "各エンドポイントのテストを作成し、カバレッジ 90% を達成"
  tags: ["testing", "pytest"]
  depends_on: ["TASK-005"]

✓ Result: TASK-006
```

**Claude Code の応答**:
```
6つのタスクを追加しました。依存関係に基づく推奨順序は以下の通りです：

1. TASK-001: プロジェクト構造のセットアップ [high]
2. TASK-002: データベースモデルの定義 [high]
3. TASK-003: FastAPI アプリケーション初期化 [high]
4. TASK-004: JWT 認証の実装 [high]
5. TASK-005: ToDo CRUD エンドポイント実装 [medium]
6. TASK-006: テストの作成 [medium]

最初のタスク (TASK-001) から始めますか？
```

### Step 1-3: CLIでの確認（オプション）

```bash
# 知識ベースの確認
clauxton kb list

# タスク一覧の確認
clauxton task list

# 次のタスクを確認
clauxton task next
```

---

## Phase 2: コード実装（TASK-001: プロジェクト構造）

### Step 2-1: タスク開始

**あなた**:
```
TASK-001 を開始してください。
```

**Claude Code の動作**:

```
🔧 Tool: task_update()
Arguments:
  task_id: "TASK-001"
  status: "in_progress"

✓ Result: Task updated
```

**Claude Code の応答**:
```
TASK-001 を開始します。プロジェクト構造をセットアップします。

知識ベースから以下の制約を確認しました：
- Python 3.11+ 必須 (KB-20251028-004)
- 型ヒント必須 (KB-20251028-005)
- テストカバレッジ 90% 以上 (KB-20251028-006)

以下のファイルを作成します：
1. pyproject.toml
2. ディレクトリ構成
3. 基本ファイル (.gitignore, README.md)

作成してもよろしいですか？
```

**あなた**:
```
はい、お願いします。
```

**Claude Code**:

Claude Code がファイルを作成します（実際にWrite toolを使用）：

**1. `pyproject.toml` の作成**

```toml
[tool.poetry]
name = "todo-api"
version = "0.1.0"
description = "FastAPI-based Todo API with JWT authentication"
authors = ["Your Name <you@example.com>"]
readme = "README.md"
requires-python = ">=3.11"

[tool.poetry.dependencies]
python = "^3.11"
fastapi = "^0.104.1"
uvicorn = {extras = ["standard"], version = "^0.24.0"}
sqlalchemy = "^2.0.23"
psycopg2-binary = "^2.9.9"
python-jose = {extras = ["cryptography"], version = "^3.3.0"}
passlib = {extras = ["bcrypt"], version = "^1.7.4"}
pydantic = {extras = ["email"], version = "^2.5.0"}
alembic = "^1.12.1"

[tool.poetry.group.dev.dependencies]
pytest = "^7.4.3"
pytest-cov = "^4.1.0"
pytest-asyncio = "^0.21.1"
httpx = "^0.25.1"
mypy = "^1.7.1"
ruff = "^0.1.6"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]
python_files = ["test_*.py"]
addopts = "--cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=90"

[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
```

**2. ディレクトリ構成の作成**

```bash
mkdir -p app/{api,models,core,schemas}
mkdir -p tests/{api,models,core}
touch app/__init__.py
touch app/main.py
touch app/api/__init__.py
touch app/models/__init__.py
touch app/core/__init__.py
touch app/schemas/__init__.py
```

**3. `.gitignore` の作成**

```gitignore
__pycache__/
*.py[cod]
*$py.class
.pytest_cache/
.coverage
htmlcov/
.env
.venv
venv/
*.db
.DS_Store
```

**4. `README.md` の作成**

```markdown
# Todo API

FastAPI-based REST API for managing todos with JWT authentication.

## Requirements

- Python 3.11+
- PostgreSQL

## Setup

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

## Testing

```bash
poetry run pytest
```
```

**Claude Code の応答**:
```
✓ プロジェクト構造を作成しました。

作成したファイル:
- pyproject.toml (依存関係とテスト設定)
- app/ ディレクトリ (アプリケーションコード)
- tests/ ディレクトリ (テストコード)
- .gitignore
- README.md

TASK-001 を完了にしますか？
```

**あなた**:
```
はい、完了にしてください。
```

**Claude Code の動作**:

```
🔧 Tool: task_update()
Arguments:
  task_id: "TASK-001"
  status: "completed"

✓ Result: Task updated

🔧 Tool: task_next()

✓ Result: TASK-002 (データベースモデルの定義)
```

**Claude Code の応答**:
```
TASK-001 を完了にしました。

次のタスクは TASK-002 (データベースモデルの定義) です。
このタスクに進みますか？
```

---

## Phase 3: データベースモデルの実装（TASK-002）

### Step 3-1: タスク開始とコード生成

**あなた**:
```
TASK-002 を開始して、User と Todo のモデルを作成してください。
```

**Claude Code の動作**:

```
🔧 Tool: task_update()
Arguments:
  task_id: "TASK-002"
  status: "in_progress"

✓ Result: Task updated

🔧 Tool: kb_search()
Arguments:
  query: "database postgresql"
  category: "architecture"

✓ Result: [KB-20251028-002: PostgreSQL をデータベースに使用]

🔧 Tool: kb_search()
Arguments:
  query: "type hints typing"
  category: "convention"

✓ Result: [KB-20251028-005: 型ヒント必須]
```

**Claude Code の応答**:
```
知識ベースから以下の制約を確認しました：
- PostgreSQL を使用 (KB-20251028-002)
- 型ヒント必須 (KB-20251028-005)

これに基づいて User と Todo のモデルを作成します。
```

**Claude Code がコード生成**:

**1. `app/models/base.py`**

```python
from datetime import datetime
from typing import Any

from sqlalchemy import DateTime
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    """Base class for all database models."""

    pass


class TimestampMixin:
    """Mixin for adding timestamp fields to models."""

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
        nullable=False,
    )
```

**2. `app/models/user.py`**

```python
from typing import TYPE_CHECKING

from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.todo import Todo


class User(Base, TimestampMixin):
    """User model for authentication."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)

    # Relationships
    todos: Mapped[list["Todo"]] = relationship(
        "Todo",
        back_populates="owner",
        cascade="all, delete-orphan",
    )
```

**3. `app/models/todo.py`**

```python
from typing import TYPE_CHECKING

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, TimestampMixin

if TYPE_CHECKING:
    from app.models.user import User


class Todo(Base, TimestampMixin):
    """Todo item model."""

    __tablename__ = "todos"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text, nullable=True)
    completed: Mapped[bool] = mapped_column(default=False, nullable=False)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="todos")
```

**4. `app/models/__init__.py`**

```python
from app.models.base import Base, TimestampMixin
from app.models.todo import Todo
from app.models.user import User

__all__ = ["Base", "TimestampMixin", "User", "Todo"]
```

**Claude Code の応答**:
```
✓ データベースモデルを作成しました。

作成したファイル:
- app/models/base.py (Base model + TimestampMixin)
- app/models/user.py (User model with JWT authentication fields)
- app/models/todo.py (Todo model with foreign key to User)
- app/models/__init__.py

すべてのモデルに型ヒントが付いています (KB-20251028-005 に準拠)。

TASK-002 を完了にして、次のタスクに進みますか？
```

---

## Phase 4: FastAPI アプリ初期化（TASK-003）

**あなた**:
```
TASK-002 を完了にして、TASK-003 に進んでください。
```

**Claude Code**:

```
🔧 Tool: task_update()
Arguments:
  task_id: "TASK-002"
  status: "completed"

✓ Result: Task updated

🔧 Tool: task_update()
Arguments:
  task_id: "TASK-003"
  status: "in_progress"

✓ Result: Task updated
```

**Claude Code がコード生成**:

**1. `app/core/config.py`**

```python
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Database
    database_url: str = "postgresql://user:password@localhost/todo_db"

    # JWT
    secret_key: str = "your-secret-key-change-this"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    # CORS
    cors_origins: list[str] = ["http://localhost:3000"]


settings = Settings()
```

**2. `app/core/database.py`**

```python
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# Convert sync URL to async
async_database_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")

engine = create_async_engine(async_database_url, echo=True)
AsyncSessionLocal = sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Dependency for getting database session."""
    async with AsyncSessionLocal() as session:
        yield session
```

**3. `app/main.py`**

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings

app = FastAPI(
    title="Todo API",
    description="FastAPI-based REST API for managing todos with JWT authentication",
    version="0.1.0",
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health")
async def health_check() -> dict[str, str]:
    """Health check endpoint."""
    return {"status": "ok"}
```

**Claude Code の応答**:
```
✓ FastAPI アプリケーションを初期化しました。

作成したファイル:
- app/core/config.py (環境変数からの設定管理)
- app/core/database.py (データベース接続)
- app/main.py (FastAPI アプリケーション + CORS設定)

次に、アプリケーションを起動してヘルスチェックを確認しますか？
```

**あなた**:
```
はい、起動してください。
```

**Claude Code**:

```bash
poetry install
poetry run uvicorn app.main:app --reload
```

**出力**:
```
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

**Claude Code の応答**:
```
✓ アプリケーションが http://127.0.0.1:8000 で起動しました。

ヘルスチェック:
- GET http://127.0.0.1:8000/health → {"status": "ok"}

TASK-003 を完了にして、次のタスク (TASK-004: JWT 認証) に進みますか？
```

---

## Phase 5: テストの実行（TASK-006 の一部）

この時点で、作成したコードのテストを実行してみます。

**あなた**:
```
ここまでのコードに対するテストを書いて実行してください。
```

**Claude Code の動作**:

```
🔧 Tool: kb_search()
Arguments:
  query: "test coverage pytest"
  category: "convention"

✓ Result: [KB-20251028-006: テストカバレッジ 90% 以上]
```

**Claude Code の応答**:
```
知識ベースから以下の制約を確認しました：
- テストカバレッジ 90% 以上 (KB-20251028-006)

現在のモデルとアプリケーションに対するテストを作成します。
```

**Claude Code がテストコード生成**:

**1. `tests/conftest.py`**

```python
import asyncio
from typing import AsyncGenerator, Generator

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.database import get_db
from app.main import app
from app.models.base import Base

# Test database URL
TEST_DATABASE_URL = "postgresql+asyncpg://test:test@localhost/test_todo_db"

# Create test engine
test_engine = create_async_engine(TEST_DATABASE_URL, echo=True)
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@pytest.fixture(scope="session")
def event_loop() -> Generator[asyncio.AbstractEventLoop, None, None]:
    """Create event loop for tests."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(autouse=True)
async def setup_database() -> AsyncGenerator[None, None]:
    """Create tables before each test and drop after."""
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Get test database session."""
    async with TestSessionLocal() as session:
        yield session


@pytest.fixture
async def client(db_session: AsyncSession) -> AsyncGenerator[AsyncClient, None]:
    """Get test client with overridden database dependency."""

    async def override_get_db() -> AsyncGenerator[AsyncSession, None]:
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
```

**2. `tests/test_health.py`**

```python
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_health_check(client: AsyncClient) -> None:
    """Test health check endpoint."""
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
```

**3. `tests/models/test_user.py`**

```python
import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


@pytest.mark.asyncio
async def test_create_user(db_session: AsyncSession) -> None:
    """Test creating a user."""
    user = User(
        email="test@example.com",
        hashed_password="hashed_password",
        full_name="Test User",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert user.id is not None
    assert user.email == "test@example.com"
    assert user.is_active is True


@pytest.mark.asyncio
async def test_user_unique_email(db_session: AsyncSession) -> None:
    """Test that user email must be unique."""
    user1 = User(email="test@example.com", hashed_password="password1")
    user2 = User(email="test@example.com", hashed_password="password2")

    db_session.add(user1)
    await db_session.commit()

    db_session.add(user2)
    with pytest.raises(Exception):  # IntegrityError
        await db_session.commit()
```

**4. `tests/models/test_todo.py`**

```python
import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.todo import Todo
from app.models.user import User


@pytest.mark.asyncio
async def test_create_todo(db_session: AsyncSession) -> None:
    """Test creating a todo."""
    user = User(email="test@example.com", hashed_password="password")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    todo = Todo(
        title="Test Todo",
        description="Test Description",
        owner_id=user.id,
    )
    db_session.add(todo)
    await db_session.commit()
    await db_session.refresh(todo)

    assert todo.id is not None
    assert todo.title == "Test Todo"
    assert todo.completed is False
    assert todo.owner_id == user.id
```

**Claude Code の応答**:
```
✓ テストを作成しました。

作成したファイル:
- tests/conftest.py (テスト用のフィクスチャとデータベース設定)
- tests/test_health.py (ヘルスチェックのテスト)
- tests/models/test_user.py (Userモデルのテスト)
- tests/models/test_todo.py (Todoモデルのテスト)

テストを実行しますか？
```

**あなた**:
```
はい、実行してください。
```

**Claude Code**:

```bash
poetry run pytest --cov=app --cov-report=term-missing -v
```

**出力**:
```
======================== test session starts =========================
collected 4 items

tests/test_health.py::test_health_check PASSED                  [ 25%]
tests/models/test_user.py::test_create_user PASSED              [ 50%]
tests/models/test_user.py::test_user_unique_email PASSED        [ 75%]
tests/models/test_todo.py::test_create_todo PASSED              [100%]

---------- coverage: platform linux, python 3.11.6-final-0 ----------
Name                          Stmts   Miss  Cover   Missing
-----------------------------------------------------------
app/__init__.py                   0      0   100%
app/core/__init__.py              0      0   100%
app/core/config.py               11      0   100%
app/core/database.py             12      2    83%   20-21
app/main.py                      14      0   100%
app/models/__init__.py            3      0   100%
app/models/base.py               11      0   100%
app/models/todo.py               13      0   100%
app/models/user.py               14      0   100%
-----------------------------------------------------------
TOTAL                            78      2    97%

======================== 4 passed in 2.35s ===========================
```

**Claude Code の応答**:
```
✓ テストが成功しました！

カバレッジ: 97% (目標: 90%、KB-20251028-006)

すべてのテストが通っています：
- ✓ ヘルスチェック
- ✓ Userモデルの作成
- ✓ メールアドレスの一意性制約
- ✓ Todoモデルの作成と外部キー

次に TASK-004 (JWT 認証) の実装に進みますか？
```

---

## Phase 6: 進捗確認と次のアクション

### Step 6-1: 現在の進捗を確認

**あなた**:
```
現在の進捗状況を教えてください。
```

**Claude Code の動作**:

```
🔧 Tool: task_list()

✓ Result: [
  {id: "TASK-001", status: "completed", name: "プロジェクト構造のセットアップ"},
  {id: "TASK-002", status: "completed", name: "データベースモデルの定義"},
  {id: "TASK-003", status: "completed", name: "FastAPI アプリケーション初期化"},
  {id: "TASK-004", status: "pending", name: "JWT 認証の実装"},
  {id: "TASK-005", status: "pending", name: "ToDo CRUD エンドポイント実装"},
  {id: "TASK-006", status: "pending", name: "テストの作成"}
]

🔧 Tool: kb_list()

✓ Result: 6 entries (architecture: 3, constraint: 1, convention: 2)
```

**Claude Code の応答**:
```
📊 プロジェクト進捗

完了タスク (3/6):
- ✓ TASK-001: プロジェクト構造のセットアップ
- ✓ TASK-002: データベースモデルの定義
- ✓ TASK-003: FastAPI アプリケーション初期化

残りタスク:
- ⏳ TASK-004: JWT 認証の実装 [high priority]
- ⏳ TASK-005: ToDo CRUD エンドポイント実装 [medium priority]
- ⏳ TASK-006: テストの作成 [medium priority]

知識ベース: 6 エントリ
- アーキテクチャ: 3
- 制約: 1
- 規約: 2

テストカバレッジ: 97% (目標: 90% 達成 ✓)

次のタスクは TASK-004 (JWT 認証) です。
```

### Step 6-2: CLIでの確認（オプション）

ターミナルで直接確認することもできます：

```bash
# タスクの進捗
clauxton task list

# 次のタスク推薦
clauxton task next

# 知識ベース確認
clauxton kb list

# 今日の作業サマリー
clauxton daily
```

**出力例**:
```bash
$ clauxton daily

📊 Daily Summary (2025-10-28)

✅ Tasks Completed: 3
- TASK-001: プロジェクト構造のセットアップ
- TASK-002: データベースモデルの定義
- TASK-003: FastAPI アプリケーション初期化

📝 KB Entries Added: 6
- KB-20251028-001: FastAPI をバックエンドフレームワークに採用
- KB-20251028-002: PostgreSQL をデータベースに使用
- KB-20251028-003: JWT 認証を使用
- KB-20251028-004: Python 3.11+ 必須
- KB-20251028-005: 型ヒント必須
- KB-20251028-006: テストカバレッジ 90% 以上

⏱️  Total Work Time: 2h 15m
🔥 Productivity: High
✅ Test Coverage: 97% (Target: 90%)

🎯 Next Recommended Task:
TASK-004: JWT 認証の実装 [high priority]
```

---

## 🎯 重要ポイント

### 1. 透過的な統合

- Claude Codeと**普通に会話するだけ**
- MCPツールは**自動的に呼び出される**（ユーザーは意識しない）
- 知識ベースとタスクは**バックグラウンドで管理**される

### 2. 知識ベース駆動の開発

- Claude Codeは実装前に**知識ベースを検索**（`kb_search()`）
- 制約や規約を**自動的に遵守**
- 一貫性のあるコードが生成される

### 3. タスク依存関係の自動管理

- タスクの依存関係（`depends_on`）を自動推論
- `task_next()` で次の安全なタスクを推薦
- 並行作業時のコンフリクトを回避

### 4. テスト駆動開発

- 知識ベースに「カバレッジ90%」が記録されている
- Claude Codeは常にテスト付きでコードを生成
- 実装後、自動的にテストを実行して検証

### 5. CLIでのオーバーライド

- Claude Codeの動作に問題があれば、CLIで直接修正可能
- `clauxton task update TASK-001 --status completed`
- `clauxton kb add` で手動追加

---

## 📊 実際のMCPツール使用頻度

このワークフローで使われたツールの内訳：

| ツール                  | 使用回数 | 用途                         |
|-------------------------|----------|------------------------------|
| `kb_add()`              | 6        | 要件の記録                   |
| `kb_search()`           | 4        | 制約の確認                   |
| `task_add()`            | 6        | タスクの作成                 |
| `task_update()`         | 6        | ステータス更新               |
| `task_next()`           | 3        | 次タスクの推薦               |
| `task_list()`           | 2        | 進捗確認                     |
| `kb_list()`             | 1        | 知識ベース確認               |
| **合計**                | **28**   |                              |

**ポイント**: ユーザーは28回のツール呼び出しを**一度も意識していません**。

---

## 🚀 次のステップ

### 残りのタスクを完了する

引き続きClaude Codeと会話して、以下を完了できます：

1. **TASK-004**: JWT 認証の実装
2. **TASK-005**: CRUD エンドポイントの実装
3. **TASK-006**: 完全なテストスイート

### プロジェクトのドキュメント化

```bash
# 知識ベースをMarkdownにエクスポート
clauxton kb export

# プロジェクトサマリー生成（MCP経由）
# Claude Codeに「プロジェクトのサマリーを作ってください」と依頼
```

**Claude Codeの動作**:
```
🔧 Tool: generate_project_summary()

✓ Result: (プロジェクト全体のMarkdownドキュメント)
```

### チームとの共有

```bash
# .clauxton/ をGitにコミット
git add .clauxton/
git commit -m "Add project knowledge and task management"
git push
```

チームメンバーも同じ知識ベースを共有できます。

---

## 🎉 まとめ

このワークフローで実現できたこと：

1. ✅ **要件定義**: 口頭で伝えた要件が自動的に知識ベースに記録
2. ✅ **タスク分解**: 自動的にタスクが作成され、依存関係も管理
3. ✅ **コード生成**: 知識ベースの制約に基づいた一貫性のあるコード
4. ✅ **テスト実行**: カバレッジ目標を達成するテストが自動生成
5. ✅ **進捗管理**: タスクステータスが自動更新され、次のタスクが推薦される

**すべてがClaude Codeとの自然な会話で完了しました。**

---

## 📚 関連ドキュメント

- **[quickstart-ja.md](quickstart-ja.md)** - 5分でセットアップ
- **[getting-started-ja.md](getting-started-ja.md)** - 詳細なセットアップ手順
- **[MCP Tools Documentation](mcp-index.md)** - 全36ツールのリファレンス
- **[CLAUDE.md](../CLAUDE.md)** - Clauxton開発者向けガイド

**Happy Coding with Clauxton!** 🚀
