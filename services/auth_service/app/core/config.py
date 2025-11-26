import os

from pydantic import Field
from pydantic_settings import BaseSettings
from sqlalchemy import URL


class Settings(BaseSettings):
  db_dsn: str | None = Field(alias="DB_DSN", default=None)

  env: str = Field(alias="ENV", default="dev")

  password_scheme: str = Field(alias="PASSWORD_SCHEME", default="argon2")
  argon2_time_cost: str = Field(alias="ARGON2_TIME_COST", default="3")
  argon2_memory_cost: str = Field(alias="ARGON2_MEMORY_COST", default="65536")
  argon2_parallelism: str = Field(alias="ARGON2_PARALLELISM", default="2")
  cors_origins: list[str] = Field(alias="CORS_ORIGINS", default_factory=list)

  api_prefix: str = Field(alias="API_PREFIX", default="/api/v1")

  jwt_iss: str = Field(alias="JWT_ISS", default="auth-service")
  jwt_alg: str = Field(alias="JWT_ALG", default="RS256")

  jwt_secret: str | None = Field(alias="JWT_SECRET", default=None)
  jwt_private_key_path: str | None = Field(alias="JWT_PRIVATE_KEY_PATH", default=None)
  jwt_public_key_path: str | None = Field(alias="JWT_PUBLIC_KEY_PATH", default=None)

  jwt_access_ttl_min: int = Field(alias="JWT_ACCESS_TTL_MIN", default=15)
  jwt_refresh_ttl_days: int = Field(alias="JWT_REFRESH_TTL_DAYS", default=30)

  cookie_domain: str = Field(alias="COOKIE_DOMAIN")
  cookie_secure: bool = Field(alias="COOKIE_SECURE")
  cookie_samesite: str = Field(alias="COOKIE_SAMESITE")

  model_config = {
    "env_file": "auth_service.env",
    "case_sensitive": True,
    "env_nested_delimiter": ",",
  }


DATABASE_URL = URL.create(
  drivername="postgresql+psycopg",
  username=os.getenv("DB_USER"),
  password=os.getenv("DB_PASSWORD"),
  host=os.getenv("DB_HOST", "db_auth"),
  port=int(os.getenv("DB_PORT", "5432")),
  database=os.getenv("DB_NAME", "auth"),
)

settings = Settings()
