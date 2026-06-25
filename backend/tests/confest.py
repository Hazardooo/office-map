# tests/conftest.py
import asyncio
import pytest
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from src.database import Base  # Путь к твоему Base

# Укажи урл к ТЕСТОВОЙ базе данных (не сломай продакшн/дев!)
TEST_DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/test_printers_db"

engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestingSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

@pytest.fixture(scope="session")
def event_loop():
    """Создает event loop для всего цикла тестов."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

@pytest.fixture(scope="session", autouse=True)
async def init_db():
    """Перед началом тестов создает все таблицы, после тестов — дропает."""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

@pytest.fixture
async def db_session() -> AsyncSession:
    """Фикстура выдает чистую сессию на каждый тест и откатывает изменения после."""
    async with TestingSessionLocal() as session:
        yield session
        # Откатываем трансляцию, чтобы тесты не влияли друг на друга
        await session.rollback()