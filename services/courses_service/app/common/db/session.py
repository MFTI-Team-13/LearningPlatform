from sqlalchemy.ext.asyncio import (
  AsyncEngine,
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)

from app.common.db.base import Base
from app.core.config import settings

engine: AsyncEngine = create_async_engine(settings.db_dsn, pool_pre_ping=False)

SessionLocal = async_sessionmaker(
  bind=engine,
  expire_on_commit=False,
  class_=AsyncSession,
)


async def create_tables():
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

async def get_session():
  async with SessionLocal() as session:
    yield session
