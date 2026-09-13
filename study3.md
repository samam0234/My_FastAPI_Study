# study3. 실습3 — 의존성 주입(Depends)과 프로젝트 구조화

Notion 학습 목표 대응: **의존성 주입**

지금까지는 `demo/main.py` 파일 하나에 모든 코드가 있었습니다. 이번 문서에서는 FastAPI의 핵심 기능인 `Depends()`를 배우고, 그 김에 프로젝트를 여러 모듈로 구조화합니다.

## 1. 의존성 주입(Dependency Injection)이란?

여러 라우트에서 공통으로 필요한 로직(페이지네이션 파라미터 파싱, 인증 확인, DB 세션 획득 등)을 함수(또는 클래스)로 뽑아내고, FastAPI가 라우트를 호출하기 **전에 그 함수를 실행해서 결과를 인자로 주입**해주는 방식입니다.

```python
def common_dependency():
    return "무언가"

@app.get("/example")
def example(value: str = Depends(common_dependency)):
    return {"value": value}
```

- `Depends(common_dependency)`가 붙은 인자는 FastAPI가 `common_dependency()`를 먼저 호출한 뒤 그 반환값을 `value`에 넣어줍니다.
- 의존성 함수도 일반 라우트 함수처럼 `Query`, `Path`, 다른 `Depends`를 인자로 받을 수 있어 **중첩(의존성이 의존성을 가짐)**이 가능합니다.
- Django에는 이런 범용 메커니즘이 없고, 미들웨어나 믹스인, 데코레이터로 각자 다르게 구현해야 하는 것과 대비됩니다.

## 2. 함수형 의존성: 페이지네이션

`app/dependencies.py`:

```python
class Pagination:
    """여러 라우트에서 재사용하는 페이지네이션 쿼리 파라미터 의존성."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=100),
    ):
        self.skip = skip
        self.limit = limit
```

- 클래스도 의존성으로 쓸 수 있습니다. `__init__`의 인자들이 그대로 `Query`/`Path`/`Depends` 선언이 됩니다.
- 라우트에서는 `pagination: Pagination = Depends()`처럼 쓰면 `Pagination(skip=.., limit=..)` 인스턴스가 주입됩니다. `Depends()`처럼 인자를 생략하면 타입힌트(`Pagination`)를 보고 알아서 그 클래스를 호출합니다.
- study2에서 `list_posts` 함수 인자에 직접 있던 `skip`, `limit`이 이제 `Pagination` 하나로 묶여 재사용 가능해졌습니다.

## 3. 제너레이터 의존성: 요청 처리 시간 로그

```python
def log_request_time():
    """라우터 단위 의존성 예시: 요청 처리 시간을 로그로 남긴다."""
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"[dependency] request handled in {elapsed_ms:.2f}ms")
```

- `return` 대신 `yield`를 쓰면 **"준비 → 라우트 실행 → 정리"** 구조의 의존성을 만들 수 있습니다. `yield` 이전은 요청 처리 전, 이후는 응답을 만든 후에 실행됩니다.
- DB 세션을 열고(`yield session`) 요청이 끝나면 닫는 패턴(study4)이 바로 이 구조를 사용합니다.
- 이 의존성은 개별 라우트가 아니라 **라우터 전체**에 걸어서, "posts 관련 요청은 전부 로그를 남긴다"는 공통 정책을 표현합니다.

## 4. 라우터 분리: `APIRouter`

`app/routers/posts.py`:

```python
router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    dependencies=[Depends(log_request_time)],
)

@router.get("", response_model=list[PostResponse])
def list_posts(
    published: Optional[bool] = Query(default=None, description="공개 여부로 필터링"),
    pagination: Pagination = Depends(),
):
    ...
```

- `APIRouter`는 Django의 앱별 `urls.py`에 대응합니다. `prefix="/posts"`를 지정해두면 각 라우트 데코레이터에는 `/posts`를 반복해서 쓰지 않아도 됩니다.
- `dependencies=[Depends(log_request_time)]`처럼 **라우터 생성 시점에 의존성을 걸면**, 이 라우터에 속한 모든 라우트에 자동 적용됩니다(반환값을 쓰지 않는 "부수효과 전용" 의존성에 적합).
- `tags=["posts"]`는 `/docs`에서 라우트를 그룹으로 묶어 보여주는 용도입니다.

## 5. 프로젝트 구조 재편

```
demo/
├── requirements.txt
└── app/
    ├── __init__.py
    ├── main.py          # FastAPI 앱 생성 + 라우터 등록
    ├── dependencies.py  # 공용 의존성 (Pagination, log_request_time)
    ├── schemas.py        # Pydantic 스키마 (PostCreate, PostResponse)
    ├── store.py          # 인메모리 저장소 (DB 연동 전 임시 구현, study4에서 교체)
    └── routers/
        ├── __init__.py
        └── posts.py       # /posts 라우터
```

- `main.py`가 이제 "앱 조립"만 담당하고, 실제 라우트 로직은 `routers/posts.py`, 데이터 접근은 `store.py`로 분리되었습니다.
- 실행 명령어가 `uvicorn main:app`에서 `uvicorn app.main:app`으로 바뀌었습니다(`<패키지>.<모듈>:<변수명>`).
- `store.py`는 지금은 파이썬 리스트를 다루지만, study4에서 이 파일의 함수들을 SQLAlchemy 쿼리로 바꾸기만 하면 라우터 코드는 거의 그대로 유지됩니다 — 계층을 분리해두는 이유입니다.

## 6. 실습3: 동작 확인

```bash
uvicorn app.main:app --reload --port 8001
```

```bash
$ curl http://127.0.0.1:8001/
{"message":"Hello, FastAPI!"}

$ curl http://127.0.0.1:8001/posts
[{"title":"첫 번째 글","content":"FastAPI 공부를 시작합니다.","published":true,"id":1},
 {"title":"비공개 초안","content":"아직 다듬는 중입니다.","published":false,"id":2}]

$ curl "http://127.0.0.1:8001/posts?limit=1"
[{"title":"첫 번째 글","content":"FastAPI 공부를 시작합니다.","published":true,"id":1}]
```

서버 로그에서 `/posts` 요청에만 의존성이 남긴 로그가 찍히는 것도 확인했습니다(`/`는 posts 라우터 소속이 아니므로 찍히지 않음).

```
INFO:     127.0.0.1:59025 - "GET /posts HTTP/1.1" 200 OK
[dependency] request handled in 0.89ms
INFO:     127.0.0.1:59026 - "GET /posts?limit=1 HTTP/1.1" 200 OK
[dependency] request handled in 1.20ms
```

다음 문서(study4)부터는 `store.py`의 인메모리 리스트를 SQLAlchemy + 실제 DB로 교체합니다.
