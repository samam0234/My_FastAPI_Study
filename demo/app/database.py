# ─────────────────────────────────────────────────────────────
# database.py : DB 연결(엔진), 세션 팩토리, 모델 공통 부모(Base), 요청별 세션 의존성
# ─────────────────────────────────────────────────────────────

# create_engine: DB와의 "연결 통로(엔진)"를 만드는 함수. 연결 풀도 함께 관리한다.
from sqlalchemy import create_engine

# DeclarativeBase: 모든 ORM 모델 클래스가 상속할 부모 클래스를 만들 때 쓰는 기반 클래스.
# sessionmaker: DB 세션(작업 단위)을 찍어내는 공장(팩토리)을 만든다.
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from app.config import get_settings

settings = get_settings()  # 캐싱된 설정 객체를 가져온다.

# 연결 문자열을 .env(DATABASE_URL)에서 읽어온다.
# SQLite면 "sqlite:///"로 시작하고, MySQL이면 "mysql+pymysql://"로 시작한다.
SQLALCHEMY_DATABASE_URL = settings.database_url

# create_engine에 넘길 추가 옵션을 담는 딕셔너리 (기본은 비어 있음).
connect_args = {}
# str.startswith(): 문자열이 특정 접두사로 시작하는지 검사 → SQLite일 때만 아래 옵션 추가.
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    # SQLite는 기본적으로 커넥션을 연 스레드에서만 쓸 수 있게 제한하는데,
    # uvicorn은 요청마다 다른 스레드를 쓸 수 있어 이 제한을 풀어줘야 한다.
    # MySQL 등 다른 DB에서는 필요 없는 SQLite 전용 옵션이다.
    connect_args = {"check_same_thread": False}

# engine: DB 접속 통로. 이후 세션/테이블 생성 등 모든 DB 작업이 이 엔진을 통해 나간다.
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)

# SessionLocal: 호출할 때마다 새 DB 세션을 만들어 주는 팩토리.
#   autocommit=False : commit()을 직접 호출해야만 변경이 DB에 확정된다(안전한 기본 동작).
#   autoflush=False  : 쿼리 실행 전에 변경사항을 자동으로 DB에 밀어 넣지 않는다.
#   bind=engine      : 이 세션이 사용할 DB 엔진을 지정한다.
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# Base: 모든 모델(Post, User ...)이 상속하는 부모 클래스.
#   상속받은 클래스들의 테이블 정보가 Base.metadata에 모여, create_all()로 한 번에 테이블을 만들 수 있다.
class Base(DeclarativeBase):
    pass


# get_db: FastAPI 의존성(Depends)으로 쓰는 "요청 1건당 DB 세션 1개" 제공 함수.
def get_db():
    db = SessionLocal()  # 새 세션 생성
    try:
        # yield: 세션을 라우트 함수에 건네주고, 요청 처리가 끝날 때까지 여기서 잠시 멈춘다.
        yield db
    finally:
        # 성공하든 예외가 나든 반드시 실행 → 세션을 닫아 연결이 새는 것을 막는다.
        db.close()
