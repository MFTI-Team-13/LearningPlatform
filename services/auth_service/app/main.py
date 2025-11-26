import os

from app.api.main_router import main_router
from app.core.config import settings
from app.core.startup import register_startup
from app.middleware.auth import setup_auth
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def try_pycharm_attach():
  if os.getenv("PYCHARM_ATTACH", "0").lower() in ("1", "true", "yes"):
    try:
      import pydevd_pycharm  # type: ignore[import-not-found] # noqa: PLC0415

      host = os.getenv("PYCHARM_HOST", "host.docker.internal")
      port = int(os.getenv("PYCHARM_PORT", "5678"))
      pydevd_pycharm.settrace(
        host=host,
        port=port,
        suspend=False,
        trace_only_current_thread=False,
      )
      print(f"[debug] ✅ Attached to PyCharm at {host}:{port}")
    except Exception as e:
      print(f"[debug] ❌ Failed to attach to PyCharm: {e}")


def create_app() -> FastAPI:
  try_pycharm_attach()
  app = FastAPI(
    title="Auth Service",
    version="1.0.0",
    docs_url="/auth_service/docs",
    redoc_url="/auth_service/redoc",
    openapi_url="/auth_service/openapi.json",
  )
  setup_auth(app)

  origins = settings.cors_origins

  app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

  async def _startup_attach():
    try_pycharm_attach()

  app.include_router(main_router)
  register_startup(app)
  return app
