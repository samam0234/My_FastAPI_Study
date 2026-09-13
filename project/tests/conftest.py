import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# 실제 서비스용 demo.db 대신, 테스트 전용 인메모리 SQLite를 사용한다.
# StaticPool을 쓰는 이유: SQLite 인메모리 DB는 기본적으로 커넥션마다 별도 DB이므로,
# 커넥션 하나만 계속 재사용해야 여러 요청(TestClient 호출)이 같은 데이터를 공유한다.
TEST_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def _reset_database():
    """테스트 함수마다 깨끗한 테이블 상태에서 시작하도록 한다."""
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    yield


@pytest.fixture
def client():
    return TestClient(app)
