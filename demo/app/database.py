from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 개발/실습용 SQLite 연결 문자열.
# 운영 환경에서 MySQL을 쓰려면 아래처럼 드라이버와 접속 정보만 바꾸면 됩니다.
#   pip install pymysql
#   SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/demo"
# SQLAlchemy가 만들어주는 Engine/Session 인터페이스는 동일하므로,
# study.py의 CRUD 코드는 DB 종류와 무관하게 그대로 재사용됩니다.
SQLALCHEMY_DATABASE_URL = "sqlite:///./demo.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    # SQLite는 기본적으로 하나의 스레드에서만 연결을 쓰도록 제한하는데,
    # FastAPI(uvicorn)는 요청마다 다른 스레드를 쓸 수 있어 이 옵션이 필요합니다.
    # MySQL 등 다른 DB에서는 필요 없는 SQLite 전용 옵션입니다.
    connect_args={"check_same_thread": False},
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
