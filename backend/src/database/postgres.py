from contextlib import asynccontextmanager
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from src.settings import settings
from src.database.exceptions import PostgreSQLUnavailable


class Base(DeclarativeBase):
    pass


engine = create_async_engine(
    settings.POSTGRES_URL,
    pool_pre_ping=True,
    echo=False,
    pool_recycle=300,
    pool_size=10,
    max_overflow=20,
    pool_timeout=30,
    connect_args={
        "command_timeout": 60,
    },
)

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
)


@asynccontextmanager
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def get_postgres() -> AsyncGenerator[AsyncSession, None]:
    try:
        async with get_db_session() as session:
            yield session
    except OSError:
        raise PostgreSQLUnavailable()