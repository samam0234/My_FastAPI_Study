# ─────────────────────────────────────────────────────────────
# config.py : 앱 전체 설정값을 한 곳에서 관리하는 모듈
#   - 환경변수 / .env 파일의 값을 읽어 타입에 맞게 변환해 준다.
#   - 비밀키·DB 주소처럼 코드에 박아두면 위험한 값을 코드 밖으로 뺄 때 쓴다.
# ─────────────────────────────────────────────────────────────

# lru_cache: 함수의 반환값을 기억(캐싱)해 두는 표준 라이브러리 데코레이터.
#   같은 함수를 여러 번 불러도 처음 한 번만 실행하고 이후엔 저장된 결과를 재사용한다.
from functools import lru_cache

# BaseSettings: 환경변수/.env 값을 자동으로 읽어 클래스 필드에 채워주는 Pydantic 클래스.
# SettingsConfigDict: BaseSettings의 동작 옵션(.env 경로, 인코딩 등)을 지정하는 타입.
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # env_file=".env": 프로젝트 루트의 .env 파일에서 값을 읽는다.
    # env_file_encoding="utf-8": .env 파일을 UTF-8로 읽는다 (한글 주석이 있어도 깨지지 않음).
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # 필드 이름(소문자)은 환경변수 이름(대소문자 무시)과 매칭된다.
    #   예) .env에 DATABASE_URL=... 이 있으면 database_url 필드에 그 값이 들어간다.
    #   없으면 "=" 뒤의 기본값을 사용한다.
    database_url: str = "sqlite:///./demo.db"  # 접속할 DB 주소 (SQLite 파일)
    secret_key: str = "study-only-secret-key-do-not-use-in-production"  # JWT 서명용 비밀키 (학습용 기본값!)
    algorithm: str = "HS256"  # JWT 서명 알고리즘 (HMAC + SHA-256)
    access_token_expire_minutes: int = 30  # 로그인 토큰 유효 시간(분)
    # CORS 허용 origin 목록: 이 주소의 프론트엔드에서 오는 요청만 브라우저가 허용한다.
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


# @lru_cache: get_settings()를 여러 곳에서 호출해도 Settings()를 한 번만 만들어 재사용한다.
#   (.env 파일을 매번 다시 읽지 않기 위함 — 사실상 싱글톤처럼 동작)
@lru_cache
def get_settings() -> Settings:
    return Settings()
