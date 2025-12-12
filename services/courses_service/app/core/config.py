import os

from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy import URL


class Settings(BaseSettings):
  db_dsn: str | None = Field(alias="DB_DSN", default=None)

  env: str = Field(alias="ENV", default="dev")

  api_prefix: str = Field(alias="API_PREFIX", default="/api/v1")

  auth_jwks_url: str | None = Field(alias="AUTH_JWKS_URL", default=None)
  auth_issuer: str | None = Field(alias="AUTH_ISSUER", default=None)
  auth_audience: str | None = Field(alias="AUTH_AUDIENCE", default=None)

  model_config = {
    "env_file": "courses_service.env",
    "case_sensitive": True,
    "env_nested_delimiter": ",",
  }


DATABASE_URL = URL.create(
  drivername="postgresql+psycopg",
  username=os.getenv("DB_USER"),
  password=os.getenv("DB_PASSWORD"),
  host=os.getenv("DB_HOST", "db_courses"),
  port=int(os.getenv("DB_PORT", "5432")),
  database=os.getenv("DB_NAME", "courses"),
)

settings = Settings()
