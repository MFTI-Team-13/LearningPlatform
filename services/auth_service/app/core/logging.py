from __future__ import annotations

import json
import logging
import os
from logging.config import dictConfig
from typing import Literal

_LogLevel = Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG", "NOTSET"]


class JsonFormatter(logging.Formatter):
  def format(self, record: logging.LogRecord) -> str:
    data = {
      "ts": self.formatTime(record, datefmt="%Y-%m-%dT%H:%M:%S%z"),
      "level": record.levelname,
      "logger": record.name,
      "msg": record.getMessage(),
    }
    if record.exc_info:
      data["exc_info"] = self.formatException(record.exc_info)

    for key in ("request_id", "user_id", "path", "method"):
      if hasattr(record, key):
        data[key] = getattr(record, key)
    return json.dumps(data, ensure_ascii=False)


def _base_config(level: _LogLevel, json_logs: bool) -> dict:
  formatter_name = "json" if json_logs else "plain"

  return {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
      "plain": {
        "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S%z",
      },
      "uvicorn": {
        "format": "%(asctime)s %(levelname)s %(name)s: %(message)s",
        "datefmt": "%Y-%m-%d %H:%M:%S%z",
      },
      "json": {
        "()": f"{__name__}.JsonFormatter",
      },
    },
    "handlers": {
      "console": {
        "class": "logging.StreamHandler",
        "formatter": formatter_name,
        "level": level,
      },
      "uvicorn_console": {
        "class": "logging.StreamHandler",
        "formatter": "uvicorn" if not json_logs else formatter_name,
        "level": level,
      },
    },
    "loggers": {
      "": {
        "handlers": ["console"],
        "level": level,
      },
      "uvicorn": {
        "handlers": ["uvicorn_console"],
        "level": level,
        "propagate": False,
      },
      "uvicorn.error": {
        "handlers": ["uvicorn_console"],
        "level": level,
        "propagate": False,
      },
      "uvicorn.access": {
        "handlers": ["uvicorn_console"],
        "level": level,
        "propagate": False,
      },
      # Полезные шумные логгеры можно опустить уровнем
      "sqlalchemy.engine": {"level": os.getenv("SQL_LOG_LEVEL", "WARNING")},
      "alembic": {"level": "INFO"},
    },
  }


def setup_logging(
  level: _LogLevel | None = None,
  *,
  json_logs: bool | None = None,
) -> None:
  env_level = os.getenv("APP_LOG_LEVEL")
  if level is None:
    level = (env_level or "INFO").upper()

  if json_logs is None:
    json_logs = os.getenv("JSON_LOGS", "false").lower() in ("1", "true", "yes")

  config = _base_config(level, json_logs)
  dictConfig(config)

  logging.getLogger(__name__).debug(
    "Logging configured",
    extra={"level": level, "json_logs": json_logs},
  )


def get_logger(name: str | None = None) -> logging.Logger:
  return logging.getLogger(name or __name__)
