from sqlalchemy import event
from sqlalchemy.engine import Engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from typing import AsyncGenerator
from app.core.config import settings


DATABASE_URL = f"sqlite+aiosqlite:///{settings.DB_PATH}"

# 비동기 엔진 생성
async_engine = create_async_engine(DATABASE_URL, echo=False, future=True)
# 비동기 세션 팩토리 생성
AsyncSessionLocal = async_sessionmaker(bind=async_engine, autoflush=False, expire_on_commit=False)
# 모델 베이스 생성
Base = declarative_base()


if DATABASE_URL.startswith("sqlite"):
    @event.listens_for(Engine, "connect")
    def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# 세션 생성 함수
async def async_get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as db:
        yield db
