from sqlalchemy.ext.asyncio import (
  AsyncEngine,
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)
from sqlalchemy.pool import NullPool

from app.common.db import models_registry  # noqa: F401
from app.core.config import settings

engine: AsyncEngine = create_async_engine(
  settings.db_dsn,
  poolclass=NullPool,
)

SessionLocal = async_sessionmaker(
  bind=engine,
  expire_on_commit=False,
  class_=AsyncSession,
)


async def get_db():
  async with SessionLocal() as session:
    yield session
