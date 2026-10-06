# ─────────────────────────────────────────────────────────────
# conftest.py : pytest가 테스트 실행 전에 자동으로 읽는 공용 설정/픽스처 파일
#   픽스처(fixture) = 테스트에 필요한 준비물(테스트용 클라이언트, 깨끗한 DB 등)을 만들어 주는 함수
# ─────────────────────────────────────────────────────────────
import pytest

# TestClient: 서버를 실제로 띄우지 않고 파이썬 코드로 API를 호출해 볼 수 있는 테스트용 클라이언트
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# StaticPool: 항상 하나의 커넥션만 재사용하는 커넥션 풀
from sqlalchemy.pool import StaticPool

from app.database import Base, get_db
from app.main import app

# 실제 서비스용 demo.db 대신, 테스트 전용 인메모리 SQLite를 사용한다.
# StaticPool을 쓰는 이유: SQLite 인메모리 DB는 기본적으로 커넥션마다 별도 DB이므로,
# 커넥션 하나만 계속 재사용해야 여러 요청(TestClient 호출)이 같은 데이터를 공유한다.
TEST_DATABASE_URL = "sqlite:///:memory:"  # ":memory:" = 파일 없이 RAM에만 존재하는 DB

# 테스트 전용 엔진과 세션 팩토리 (database.py와 같은 구조, DB 주소만 다르다)
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


# 실제 get_db 대신 사용할 테스트용 의존성 (구조는 동일하지만 테스트 DB 세션을 준다)
def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# dependency_overrides: 앱 안의 get_db 의존성을 테스트용 함수로 "바꿔치기"한다.
#   → 코드를 수정하지 않고도 라우트가 테스트 DB를 사용하게 만드는 FastAPI의 테스트 기능.
app.dependency_overrides[get_db] = override_get_db


# autouse=True: 테스트 함수가 이름을 명시하지 않아도 "모든 테스트 전에" 자동으로 실행된다.
@pytest.fixture(autouse=True)
def _reset_database():
    """테스트 함수마다 깨끗한 테이블 상태에서 시작하도록 한다."""
    Base.metadata.drop_all(bind=engine)  # 기존 테이블 전부 삭제
    Base.metadata.create_all(bind=engine)  # 빈 테이블 다시 생성
    yield  # 여기서 테스트 함수가 실행된다


# 테스트 함수의 매개변수 이름이 "client"이면 pytest가 이 픽스처의 반환값을 자동으로 넣어준다.
@pytest.fixture
def client():
    return TestClient(app)
