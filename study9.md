# study9. 테스트와 디버깅

## ① 목표

서버를 켜지 않고 API를 호출하는 테스트와, 실패했을 때 로그와 요청 id로 원인을 찾는 순서를 익힌다.

## ② 📖 이론

### 왜 쓰는지

브라우저로 열 번 눌러 보는 확인은 다음 수정에서 깨져도 아무도 모른다. 테스트는 상태 코드와 JSON 키를 고정한다. 디버깅은 "어느 요청이었는지"를 로그에서 찾는 일이다.

### 핵심 개념

- `pytest`는 `test_`로 시작하는 함수를 실행하고, `assert`가 거짓이면 실패다.
- `TestClient`는 소켓을 열지 않고 앱을 호출한다.
- `dependency_overrides`는 `get_db`를 테스트용 세션으로 바꿔 끼운다. 실제 `demo.db`는 건드리지 않는다.
- 테스트 DB는 `sqlite:///:memory:`와 `StaticPool`이다. 메모리 DB는 커넥션마다 파일이 달라지므로 풀을 하나로 고정해야 여러 요청이 같은 데이터를 본다.
- 로거는 `logging.getLogger("app")`. 500 핸들러가 `logger.exception`으로 스택을 남긴다.

### 비유

테스트 클라이언트는 매장 문을 열지 않고 주방에 모의 주문을 넣는 창구다. `dependency_overrides`는 그 주문만 연습용 냉장고를 쓰게 하는 스위치다.

## ③ 🛠️ 실기

`demo/tests/conftest.py`의 핵심:

```python
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)

def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(autouse=True)
def _reset_database():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    reset_auth_state()
    reset_idempotency()
    yield
```

줄별 설명:

1. 파일로 남지 않는 SQLite 엔진.
2. 주소가 `:memory:`다.
3. 테스트 스레드가 달라도 접속을 허용한다.
4. 접속을 하나로 유지해 같은 메모리 DB를 공유한다.
5. 엔진 생성 끝.
6. 빈 줄.
7. 진짜 `get_db` 대신 쓸 함수. 시그니처가 같아야 교체가 된다.
8. 테스트 세션을 연다.
9. 예외가 나도 닫히게 `try`를 연다.
10. 경로 함수에 세션을 넘긴다.
11. 요청이 끝나면 여기로 돌아온다.
12. 세션을 닫는다.
13. 함수 끝.
14. 빈 줄.
15. 앱이 들고 있는 `get_db` 함수 객체를 테스트 함수로 바꾼다. 라우터 코드를 수정하지 않는다.
16. 빈 줄.
17. `autouse`라서 테스트가 이름을 몰라도 매번 실행된다.
18. 함수 정의.
19. 테이블을 지운다.
20. 빈 테이블을 다시 만든다. 이전 테스트의 회원이 남지 않는다.
21. 로그아웃으로 쌓인 토큰 폐기 목록을 비운다.
22. 중복 제출 키와 캐시를 비운다.
23. 이 아래에서 테스트 본문이 실행된다.

실행은 각 앱 폴더에서 한다.

```powershell
cd demo
.venv\Scripts\Activate.ps1
pytest -q
```

`project`도 같은 명령이다. `demo`는 11개, `project`는 업로드·AI·웹소켓을 포함해 13개다.

디버깅 순서:

1. 응답의 `error.requestId`를 복사한다.
2. 같은 값이 응답 헤더 `X-Request-Id`에 있는지 본다.
3. 서버 터미널에서 그 시각의 `ERROR:app` 스택을 찾는다.
4. Swagger `/docs`에서 같은 요청을 다시 보내 재현한다.
5. 테스트로 그 상태 코드를 assert에 고정한다.

자주 나는 오류:

| # | 증상 | 어디를 볼지 |
| --- | --- | --- |
| 1 | `ModuleNotFoundError: app` | pytest를 `demo` 또는 `project` 안에서 실행했는가 |
| 2 | 401 | `Bearer` 접두어와 토큰 폐기 |
| 3 | 403 | 작성자 id |
| 4 | 404 | id가 테스트 DB에 있는가. 시드 데이터는 테스트 DB에 없다 |
| 5 | 400 VALIDATION_ERROR | `fields`의 키 |
| 6 | 409 | 같은 이메일을 두 번 넣었는가 |
| 7 | CORS는 테스트는 통과하고 브라우저만 실패 | TestClient는 브라우저가 아니다. `CORS_ORIGINS`를 본다 |
| 8 | `no such column` | 개발용 `demo.db`가 옛 스키마. 테스트 메모리 DB와는 별개 |
| 9 | 500이 테스트에서 예외로 터짐 | `raise_server_exceptions=False`로 응답을 본다 |
| 10 | 목록이 이전 테스트 데이터를 포함 | `autouse`로 `drop_all`이 도는지 확인 |

외부 API를 흉내 내는 자리는 study13 이후의 메일·결제·AI다. 키가 없으면 네트워크를 호출하지 않고 로그와 mock 답을 쓴다. 테스트는 `LLM_PROVIDER=mock`으로 그 분기를 고정한다. DB를 가짜로 바꾸는 공식 자리는 위의 `dependency_overrides`다.

## ④ 🔗 연동 포인트

테스트가 기대하는 JSON은 study4와 study6의 계약이다. `dependency_overrides`는 운영 코드의 `get_db`를 유지한 채 연습용 엔진만 바꾼다. CI(study16)는 이 `pytest -q`를 `demo`와 `project`에서 각각 실행한다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 테스트가 서로 영향을 줌 | 폐기 목록이나 DB를 안 비움 | `reset_auth_state`와 `drop_all`을 autouse에 둔다 |
| 메모리 DB가 항상 비어 보임 | `StaticPool` 없이 커넥션마다 DB가 달라짐 | `poolclass=StaticPool` |
| assert가 한글에서 실패 | 기대한 문장과 핸들러 문장이 다름 | 응답 JSON을 출력해 문구를 맞춘다 |
| 로그가 안 보임 | 레벨이 WARNING 이상 | `logging.basicConfig(level=logging.INFO)` |

## ⑥ 직접 해보기

1. `pytest -q`를 `demo`와 `project`에서 각각 실행한다.
2. 목록 테스트의 기대값을 일부러 깨뜨려 실패 메시지를 읽고, 다시 고친다.
3. `/debug/boom` 테스트가 본문에 예외 문자열이 없다는 것을 확인한다.

## ⑦ ☐ 체크리스트

- [ ] `TestClient`로 가입, 로그인, 글 CRUD를 검증했다.
- [ ] 테스트 DB가 파일 `demo.db`와 분리되어 있다.
- [ ] 401, 403, 404, 400의 `error.code`를 assert했다.
- [ ] 500 로그에는 스택이 있고 응답에는 없다.
- [ ] 테스트코드로 API 테스트

## ⑧ 다음 단계

테스트로 회귀를 잡을 수 있으면 study10에서 이 앱을 다른 환경에서 어떻게 띄우고, 띄운 뒤에 무엇을 확인하는지 정리한다.
