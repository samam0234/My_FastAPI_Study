# study9. 고급 기술 구현 4 — 테스트코드로 API 테스트

Notion 학습 목표 대응: **테스트코드로 API 테스트**

지금까지는 `curl`로 손수 요청을 보내며 동작을 확인했습니다. 이번 문서에서는 그 확인 과정을 `pytest` 테스트 코드로 자동화해서, 코드가 바뀔 때마다 매번 손으로 재현하지 않아도 회귀를 잡아낼 수 있게 만듭니다.

## 1. 설치

```bash
pip install pytest httpx
```

- `pytest`: Python 테스트 실행기. Django의 `python manage.py test`(unittest 기반)에 대응합니다.
- `httpx`: FastAPI의 `TestClient`가 실제 서버를 띄우지 않고도 앱에 요청을 보내기 위해 내부적으로 사용하는 HTTP 클라이언트 라이브러리입니다.

## 2. 테스트 DB 분리: `get_db` 오버라이드

실제 서비스에서 쓰는 `demo.db`를 테스트가 어지럽히면 안 됩니다. FastAPI는 의존성을 테스트용으로 갈아끼울 수 있는 `app.dependency_overrides`를 제공합니다. `tests/conftest.py`:

```python
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
```

- `app.dependency_overrides[get_db] = override_get_db`: study3~4에서 만든 `Depends(get_db)`를 테스트 실행 중에는 `override_get_db`로 바꿔치기합니다. **라우트/서비스 코드는 전혀 건드리지 않고, 의존성만 교체**해서 테스트 환경을 완전히 분리할 수 있다는 점이 `Depends()` 패턴의 실질적인 장점입니다.
- SQLite 인메모리 DB(`sqlite:///:memory:`)는 커넥션마다 별도의 DB이므로, `poolclass=StaticPool`로 커넥션 하나를 계속 재사용해야 테스트 안에서 여러 요청이 같은 데이터를 공유합니다.
- `autouse=True` 픽스처로 **테스트 함수 하나가 끝날 때마다 테이블을 지우고 새로 만들어서**, 테스트 간에 데이터가 서로 영향을 주지 않게 했습니다(테스트 격리).

> **참고**: `app/main.py`의 `_seed_initial_posts()`는 모듈을 임포트하는 시점에 실제 `demo.db`에 초기 데이터를 넣습니다. 테스트는 `get_db`만 오버라이드하므로 이 시드 로직 자체를 막지는 못하지만, 시드가 쓰는 DB(`demo.db`)와 테스트가 쓰는 DB(인메모리)가 다르기 때문에 테스트 결과에는 영향이 없습니다. 다만 "테스트를 실행하면 `demo.db` 파일이 생성된다"는 부작용은 남는데, 이런 문제를 근본적으로 없애려면 환경별 설정 분리가 필요합니다 — study10에서 다룹니다.

## 3. 테스트 작성

`tests/test_auth.py`:

```python
def test_register_duplicate_username(client):
    payload = {"username": "alice", "password": "secret123"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_login_wrong_password(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    response = client.post("/auth/login", data={"username": "alice", "password": "wrong"})
    assert response.status_code == 401
```

`tests/test_posts.py`(발췌):

```python
def test_create_post_requires_auth(client):
    response = client.post("/posts", json={"title": "t", "content": "c"})
    assert response.status_code == 401


def test_update_post_forbidden_for_non_owner(client):
    token_alice = _register_and_login(client, "alice", "secret123")
    created = client.post(
        "/posts", json={"title": "alice post", "content": "..."},
        headers={"Authorization": f"Bearer {token_alice}"},
    ).json()

    token_bob = _register_and_login(client, "bob", "hunter2")
    response = client.put(
        f"/posts/{created['id']}", json={"title": "hijack", "content": "..."},
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert response.status_code == 403
```

- study2(CRUD), study7(JWT 인증/소유권 검사), study8(에러 포맷)에서 `curl`로 직접 확인했던 시나리오들을 그대로 `assert`로 옮겼습니다. 새로 코드를 고치다가 이 중 하나라도 깨지면 `pytest` 한 번으로 바로 알아챌 수 있습니다.

## 4. 실습9: 테스트 실행

```bash
pytest -v
```

### 실행 결과

```
collected 9 items

tests/test_auth.py::test_register_duplicate_username PASSED              [ 11%]
tests/test_auth.py::test_login_wrong_password PASSED                     [ 22%]
tests/test_auth.py::test_login_success PASSED                            [ 33%]
tests/test_posts.py::test_list_posts_empty PASSED                        [ 44%]
tests/test_posts.py::test_get_post_404 PASSED                            [ 55%]
tests/test_posts.py::test_create_post_requires_auth PASSED               [ 66%]
tests/test_posts.py::test_create_and_get_post PASSED                     [ 77%]
tests/test_posts.py::test_update_post_forbidden_for_non_owner PASSED     [ 88%]
tests/test_posts.py::test_owner_can_update_and_delete PASSED             [100%]

======================== 9 passed, 2 warnings in 3.33s ========================
```

9개 테스트가 모두 통과했습니다. 회원가입 중복 방지, 로그인 성공/실패, 인증 없는 글쓰기 차단(401), 소유권 검사(403), CRUD 전체 흐름(생성→수정→삭제→재조회 404)까지 이 커리큘럼에서 다뤄온 핵심 시나리오가 코드로 고정되었습니다.

다음 문서(study10)에서는 하드코딩되어 있던 `SECRET_KEY` 같은 값들을 `.env` 기반 설정으로 분리하고, 목록 API에 페이지네이션 응답 형태를 다듬어 studyFinal 프로젝트를 위한 마무리 작업을 합니다.
