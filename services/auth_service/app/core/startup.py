import logging

from fastapi import FastAPI

from app.common.db.session import SessionLocal
from app.core.logging import setup_logging
from app.core.security import ensure_keys_ready


def register_startup(app: FastAPI) -> None:
  setup_logging()

  @app.on_event("startup")
  async def _on_startup():
    ensure_keys_ready()
    async with SessionLocal() as db:
      try:
        await db.execute("SELECT 1")
        logging.getLogger(__name__).info("Learning Platform started")
      except Exception as e:
        logging.getLogger(__name__).exception("Bootstrap failed: %s", e)
