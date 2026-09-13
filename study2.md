# study2. 실습2 — Path/Query 파라미터와 Pydantic 스키마로 `/posts` CRUD 구현

Notion 학습 목표 대응: **경로, Path/Query, Pydantic 스키마**

이 커리큘럼의 공통 스펙인 `/posts` CRUD를 이번 문서에서 처음 만듭니다. 아직 DB는 연결하지 않고, 파이썬 리스트를 임시 저장소로 사용합니다(DB 연동은 study4).

## 1. 경로(Path) 파라미터

URL 경로 자체에 포함된 값입니다. 함수 인자로 받으면 타입힌트에 따라 자동 변환·검증됩니다.

```python
@app.get("/posts/{post_id}")
def get_post(post_id: int = Path(..., gt=0, description="조회할 게시글 id")):
    ...
```

- `{post_id}`가 함수 인자 `post_id: int`와 이름으로 매칭됩니다.
- `Path(..., gt=0)`: `...`(Ellipsis)는 "필수값"이라는 의미이고, `gt=0`은 "0보다 커야 함"이라는 검증 규칙입니다.
- `/posts/abc`처럼 int로 변환할 수 없는 값이 오면 FastAPI가 자동으로 422 에러를 응답합니다.

## 2. 쿼리(Query) 파라미터

경로에 포함되지 않고 `?key=value` 형태로 전달되는 값입니다. 함수 인자의 기본값 유무로 Path/Query가 구분됩니다 — 경로에 `{}`로 선언되지 않은 인자는 자동으로 Query 파라미터가 됩니다.

```python
@app.get("/posts", response_model=list[PostResponse])
def list_posts(
    published: Optional[bool] = Query(default=None, description="공개 여부로 필터링"),
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=10, ge=1, le=100),
):
    ...
```

- `published`: 생략 가능(옵션) 쿼리 파라미터. `?published=false`처럼 넘기면 문자열 `"false"`를 FastAPI가 알아서 `bool`로 변환합니다.
- `skip`, `limit`: 페이지네이션에 자주 쓰이는 패턴. `ge`(>=), `le`(<=)로 범위를 제한해 잘못된 값이 들어오는 것을 애초에 막습니다.

## 3. Pydantic 스키마 설계

```python
class PostCreate(BaseModel):
    title: str
    content: str
    published: bool = True


class PostResponse(PostCreate):
    id: int
```

- `PostCreate`: 클라이언트가 **보내는** 데이터(요청 바디)의 형태. `id`는 서버가 생성하므로 포함하지 않습니다.
- `PostResponse`: 클라이언트에게 **돌려주는** 데이터의 형태. `PostCreate`를 상속해 `id` 필드만 추가했습니다.
- 라우트 함수 인자에 `post: PostCreate`처럼 타입힌트를 주면, FastAPI가 요청 바디(JSON)를 자동으로 파싱·검증해서 `PostCreate` 인스턴스로 넘겨줍니다. 검증 실패 시 422 응답이 자동 생성됩니다.
- `response_model=PostResponse`를 지정하면 라우트가 무엇을 반환하든 이 스키마 기준으로 필터링·직렬화되고, `/docs`에도 응답 형태가 정확히 문서화됩니다.

## 4. `/posts` CRUD 라우트

`demo/main.py`에 아래 라우트를 추가했습니다.

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/posts` | 목록 조회 (`published`, `skip`, `limit` 쿼리 파라미터 지원) |
| GET | `/posts/{post_id}` | 단건 조회 (없으면 404) |
| POST | `/posts` | 생성 (201 Created) |
| PUT | `/posts/{post_id}` | 전체 수정 (없으면 404) |
| DELETE | `/posts/{post_id}` | 삭제 (204 No Content, 없으면 404) |

없는 게시글을 조회/수정/삭제하면 공통으로 사용하는 `get_post_or_404()` 헬퍼가 `HTTPException(status_code=404, ...)`를 발생시킵니다. FastAPI는 `HTTPException`을 잡아서 지정한 상태 코드 + `{"detail": "..."}` 형태의 JSON 에러 응답으로 자동 변환해줍니다(커스텀 예외 핸들러는 study8에서 다룸).

## 5. 실습2: 동작 확인

```bash
uvicorn main:app --reload --port 8001
```

### 목록/필터 조회

```bash
$ curl http://127.0.0.1:8001/posts
[{"title":"첫 번째 글","content":"FastAPI 공부를 시작합니다.","published":true,"id":1},
 {"title":"비공개 초안","content":"아직 다듬는 중입니다.","published":false,"id":2}]

$ curl "http://127.0.0.1:8001/posts?published=false"
[{"title":"비공개 초안","content":"아직 다듬는 중입니다.","published":false,"id":2}]
```

### 단건 조회 / 404

```bash
$ curl http://127.0.0.1:8001/posts/1
{"title":"첫 번째 글","content":"FastAPI 공부를 시작합니다.","published":true,"id":1}

$ curl -o - -w "\n%{http_code}\n" http://127.0.0.1:8001/posts/999
{"detail":"post 999를 찾을 수 없습니다."}
404
```

### 생성 / 수정 / 삭제

```bash
$ curl -X POST http://127.0.0.1:8001/posts \
    -H "Content-Type: application/json" \
    -d '{"title":"study2 practice","content":"Path/Query/Pydantic practice","published":true}'
{"title":"study2 practice","content":"Path/Query/Pydantic practice","published":true,"id":3}

$ curl -X PUT http://127.0.0.1:8001/posts/3 \
    -H "Content-Type: application/json" \
    -d '{"title":"study2 practice (updated)","content":"content updated","published":false}'
{"title":"study2 practice (updated)","content":"content updated","published":false,"id":3}

$ curl -o /dev/null -w "%{http_code}\n" -X DELETE http://127.0.0.1:8001/posts/3
204
```

> **참고**: Windows Git Bash 터미널에서 `curl -d`로 한글이 포함된 JSON을 보내면 터미널 코드페이지 문제로 `{"detail":"There was an error parsing the body"}`가 발생할 수 있습니다(실제로 재현됨). 이런 smoke test는 영어 payload로 검증하고, 한글 데이터 검증은 `/docs`(Swagger UI)나 브라우저에서 직접 진행하는 것이 안전합니다. 이 내용은 [.claude/CLAUDE.md](../.claude/CLAUDE.md)에도 기록해두었습니다.

## 6. `/docs`에서 확인하기

`http://127.0.0.1:8001/docs`에 접속하면 위 5개 라우트가 요청/응답 스키마(`PostCreate`, `PostResponse`)와 함께 자동 문서화된 것을 볼 수 있고, 브라우저에서 바로 "Try it out"으로 한글 데이터를 포함한 요청도 테스트할 수 있습니다.

다음 문서(study3)부터는 `Depends()`로 의존성을 주입하고, `main.py` 하나에 몰려있던 코드를 `routers/`, `schemas.py` 등으로 구조화합니다.
