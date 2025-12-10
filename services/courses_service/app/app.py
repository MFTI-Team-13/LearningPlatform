import os

from fastapi import FastAPI
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.main_router import main_router
from app.common.db.session import engine
from app.common.db.base import Base
from app.middleware.auth import setup_auth_middleware


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
    title="Courses Service",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_url="/openapi.json",
  )

  async def _startup_attach() -> None:
    try_pycharm_attach()

  # app.add_event_handler("startup", _startup_attach)

  async def on_startup():
    async with engine.begin() as conn:
      #await conn.run_sync(Base.metadata.drop_all)
      await conn.run_sync(Base.metadata.create_all)
    print("[DB] ✅ Tables created or already exist.")

  async def course_validation_handler(request, exc: RequestValidationError):
    errors = exc.errors()

    for err in errors:
      if err["type"] == "value_error":
        msg = err.get("msg", "Некорректные данные")
        return JSONResponse(
          status_code=422,
          content={"detail": msg}
        )

    return JSONResponse(
      status_code=422,
      content={"detail": errors}
    )

  app.add_event_handler("startup", on_startup)
  app.add_exception_handler(RequestValidationError, course_validation_handler)
  setup_auth_middleware(app)
  app.include_router(main_router)
  return app
