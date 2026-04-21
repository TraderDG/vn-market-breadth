from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.config import settings
from typing import AsyncGenerator


class Base(DeclarativeBase):
    pass


# Async engine for FastAPI endpoints
async_engine = create_async_engine(settings.DATABASE_URL, echo=False, pool_pre_ping=True)
AsyncSessionLocal = async_sessionmaker(async_engine, expire_on_commit=False)

# Sync engine for data_loader (Pandas bulk inserts)
sync_engine = create_engine(settings.SYNC_DATABASE_URL, echo=False, pool_pre_ping=True)
SyncSessionLocal = sessionmaker(sync_engine)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session


async def create_tables():
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
