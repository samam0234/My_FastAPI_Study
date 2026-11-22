"""환경 변수와 .env를 한 곳에서 읽는다.

개발 기본값은 SQLite다. MySQL·PostgreSQL로 바꿀 때는 DATABASE_URL만 교체한다.
- MySQL: mysql+pymysql://user:password@localhost:3306/demo
- PostgreSQL: postgresql+psycopg://user:password@localhost:5432/demo
연결 정보는 코드에 적지 않는다.
"""

from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    database_url: str = "sqlite:///./demo.db"
    secret_key: str = "study-only-secret-key-do-not-use-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60
    cors_origins: list[str] = [
        "http://localhost:3000",
        "http://127.0.0.1:3000",
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
    cache_ttl_ms: int = 0
    upload_dir: str = "uploads"
    max_upload_bytes: int = 1_000_000
    smtp_host: str = ""
    smtp_port: int = 587
    smtp_from: str = "noreply@example.com"
    openai_api_key: str = ""
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: str = "gemma4:12b"
    google_client_id: str = ""
    google_redirect_uri: str = "http://localhost:3000/oauth/callback"


@lru_cache
def get_settings() -> Settings:
    return Settings()
