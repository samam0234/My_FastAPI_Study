from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./demo.db"
    secret_key: str = "study-only-secret-key-do-not-use-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
