from app.core.config import settings
from sqlalchemy.ext.asyncio import (
  AsyncEngine,
  AsyncSession,
  async_sessionmaker,
  create_async_engine,
)

engine: AsyncEngine = create_async_engine(settings.db_dsn, pool_pre_ping=False)

SessionLocal = async_sessionmaker(
  bind=engine,
  expire_on_commit=False,
  class_=AsyncSession,
)


async def get_db():
  async with SessionLocal() as session:
    yield session
