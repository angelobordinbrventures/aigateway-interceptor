from typing import List

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/aigateway"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "change-me-in-production-use-a-real-secret-key"
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    LOG_RETENTION_DAYS: int = 90
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60

    model_config = {"env_prefix": "AIGATEWAY_", "env_file": ".env", "extra": "ignore"}


settings = Settings()
