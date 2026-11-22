"""DB 엔진, 세션, 모델 공통 부모.

SQLAlchemy는 URL 앞부분(sqlite, mysql+pymysql, postgresql+psycopg)만 바꾸면
같은 모델 코드를 다른 관계형 DB에 붙일 수 있다. MongoDB는 이 엔진으로 붙이지 않는다.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings


def build_engine(url: str):
    """URL 종류에 맞는 엔진 옵션을 고른다."""
    connect_args: dict = {}
    if url.startswith("sqlite"):
        # SQLite는 연결을 연 스레드 밖에서의 사용을 막는다. uvicorn은 스레드가 바뀔 수 있다.
        connect_args["check_same_thread"] = False
    # pool_pre_ping: MySQL/PostgreSQL이 끊긴 연결을 다음 요청 전에 한 번 확인한다.
    return create_engine(url, connect_args=connect_args, pool_pre_ping=True)


engine = build_engine(get_settings().database_url)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    """요청 하나당 세션 하나. yield 아래는 응답이 끝난 뒤 실행된다."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
