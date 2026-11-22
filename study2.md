# study2. 핵심 구조

## ① 목표

FastAPI 앱을 라우터, 서비스, 저장소로 나누고, `Depends`로 그 단위가 값을 주고받게 만든다.

## ② 📖 이론

### 왜 쓰는지

경로 함수 안에 SQL과 권한 검사와 JSON 모양을 모두 넣으면 한 파일이 금방 커진다. 역할을 나누면 테스트할 때 HTTP를 흉내 내지 않고 규칙만 부를 수 있다.

### 핵심 개념

- **앱**: `FastAPI()` 인스턴스. 미들웨어와 라우터를 모은다.
- **라우터**: `APIRouter`. 관련 URL만 모은 작은 앱. `include_router`로 본체에 붙인다.
- **서비스**: 404인지, 내 글인지 같은 규칙.
- **저장소**: `db.query`만 있는 파일. HTTP를 모른다.
- **의존성 주입**: 함수 매개변수 기본값에 `Depends(...)`를 적으면 FastAPI가 그 함수를 먼저 실행해 결과를 넣어 준다.

호출 방향은 한쪽으로만 간다.

```text
router → service → repository → model
```

서비스가 라우터를 import하면 순환이 생긴다. 아래층은 위층을 몰라야 한다.

### 비유

식당에서 홀(라우터)은 주문을 받아 주방(서비스)에 넘긴다. 주방은 창고(저장소)에서 재료를 꺼낸다. 홀 직원이 창고 선반을 직접 열지 않는다. `Depends`는 테이블마다 물컵을 미리 올려 두는 직원이다.

## ③ 🛠️ 실기

여러 목록 경로가 같은 쿼리를 받게 하려고 클래스 의존성을 둔다. `demo/app/dependencies.py` 전체는 다음과 같다.

```python
import time

from fastapi import Query


class PageParams:
    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="1부터 세는 페이지 번호"),
        limit: int = Query(default=10, ge=1, description="한 페이지 개수. 50을 넘으면 50"),
        q: str = Query(default="", description="제목·본문 검색어"),
        sort: str = Query(default="-createdAt", description="createdAt, -createdAt, -commentCount"),
    ) -> None:
        self.page = page
        self.limit = min(limit, 50)
        self.q = q
        self.sort = sort


def log_request_time():
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"[dependency] request handled in {elapsed_ms:.2f}ms")
```

줄별 설명:

1. 경과 시간을 재는 표준 라이브러리.
2. 빈 줄.
3. `Query`는 쿼리 문자열의 기본값과 범위를 선언한다.
4. 빈 줄 두 칸.
6. 클래스 이름이 곧 의존성 이름이다.
7. FastAPI는 `Depends()`에 클래스를 넘기면 `__init__` 매개변수를 요청에서 채운다.
8. `page`는 1 이상. 0이나 음수면 요청이 함수에 들어가기 전에 거절된다.
9. `limit` 기본 10, 1 이상.
10. 검색어. 없으면 빈 문자열.
11. 정렬 키의 기본값은 최신 글.
12. 생성자 끝.
13. 검증을 통과한 page를 속성으로 보관한다.
14. 50을 넘기면 50으로 자른다. 오류 대신 상한을 맞추는 규칙이다.
15. 검색어 보관.
16. 정렬 키 보관.
17. 클래스 끝.
18. 빈 줄.
19. 제너레이터 의존성. `yield`가 있으면 요청 전과 후를 한 함수에서 처리한다.
20. 시작 시각.
21. 여기서 경로 함수가 실행된다. yield 위는 전, 아래는 후.
22. 밀리초로 바꾼다.
23. 터미널에 찍는다. 응답 본문에는 넣지 않는다.

라우터는 이 의존성을 이렇게 받는다.

```python
router = APIRouter(
    prefix="/posts",
    tags=["posts"],
    dependencies=[Depends(log_request_time)],
)

@router.get("")
def list_posts(page: PageParams = Depends(), db: Session = Depends(get_db)):
    return service.list_posts(db, q=page.q, sort=page.sort, page=page.page, limit=page.limit)
```

- `dependencies=[...]`는 이 라우터의 모든 경로에 `log_request_time`을 건다. 매개변수로 받지 않아도 실행된다.
- `Depends()`의 빈 괄호는 "PageParams를 만들어 달라"는 뜻이다.
- `get_db`도 의존성이다. 요청이 끝나면 세션을 닫는다. 정의는 `database.py`의 `yield`에 있다.
- 경로 함수는 서비스를 호출만 한다. 규칙을 if로 쓰지 않는다.

`demo`와 `project` 모두 이 파일을 같은 내용으로 둔다. `project`는 여기에 업로드·AI·웹소켓 라우터를 더 붙일 뿐이다.

## ④ 🔗 연동 포인트

`PageParams`가 모아 둔 `page`, `limit`, `q`, `sort`는 study6 목록 쿼리와 study14 페이지 규칙의 입력이다. `get_db`가 열어 준 세션은 저장소를 거쳐 서비스의 404/403 판단에 쓰이고, 그 결과가 라우터의 응답 모델로 직렬화된다. 단위 사이에 딕셔너리를 몰래 주고받지 않고, 함수 인자로만 넘긴다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 라우트를 추가했는데 404 | `include_router`를 안 함 | `main.py`에서 라우터를 앱에 연결 |
| 순환 import | 서비스가 라우터를 import | 호출은 라우터 → 서비스만 |
| `Depends`가 동작 안 함 | 기본값이 아니라 호출 위치에 씀 | 매개변수 기본값으로 `Depends(...)` |
| yield 의존성이 응답 후에 안 돔 | 일반 return만 있음 | 전/후가 필요하면 `yield` |

## ⑥ 직접 해보기

1. `GET /api/posts`를 호출하고 터미널에 `request handled in ...ms`가 찍히는지 본다.
2. `?limit=1000`으로 호출해 응답의 limit가 50인지 확인한다.
3. `services/post.py`에서 라우터를 import하지 않았다는 것을 검색으로 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 라우터, 서비스, 저장소가 서로 다른 파일이라는 것을 말할 수 있다.
- [ ] 호출 방향이 router → service → repository → model이다.
- [ ] `Depends`로 페이지 파라미터와 DB 세션을 넣었다.
- [ ] `yield` 의존성으로 요청 시간을 로그에 남겼다.
- [ ] 의존성 주입

## ⑧ 다음 단계

단위가 서로를 부를 수 있게 되었으면, study3에서 그 사이로 오가는 데이터의 모양을 Pydantic 스키마로 고정한다.
