import os

from fastapi import FastAPI

from app.api.main_router import main_router

def try_pycharm_attach() -> None:
  if os.getenv("PYCHARM_ATTACH", "0").lower() in ("1", "true", "yes"):
    try:
      import pydevd_pycharm  # noqa: PLC0415

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
    title="Progress Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
  )

  async def _startup_attach() -> None:
    try_pycharm_attach()

  # app.add_event_handler("startup", _startup_attach)

  app.include_router(main_router)
  return app
