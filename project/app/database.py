from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()

# 연결 문자열을 .env(DATABASE_URL)에서 읽어온다.
# SQLite면 "sqlite:///"로 시작하고, MySQL이면 "mysql+pymysql://"로 시작한다.
SQLALCHEMY_DATABASE_URL = settings.database_url

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite는 기본적으로 커넥션을 연 스레드에서만 쓸 수 있게 제한하는데,
    # uvicorn은 요청마다 다른 스레드를 쓸 수 있어 이 제한을 풀어줘야 한다.
    # MySQL 등 다른 DB에서는 필요 없는 SQLite 전용 옵션이다.
    connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
