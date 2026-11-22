# study4. 라우팅과 요청 처리

## ① 목표

URL, 경로 파라미터, 쿼리, 요청 본문이 한 함수로 모이는 흐름을 만들고, 실패는 같은 오류 JSON으로 돌려준다.

## ② 📖 이론

### 왜 쓰는지

클라이언트가 외울 주소가 제각각이면 화면을 붙일 때마다 경로를 다시 짠다. 공통으로 쓰는 게시판 API는 `/api` 아래에 자원을 두고, 건강 체크만 밖에 둔다. 오류도 `detail` 문자열 하나가 아니라 코드와 필드 이유를 주면 화면이 칸마다 메시지를 찍을 수 있다.

### 핵심 개념

- `APIRouter(prefix="/api")`: 이 라우터에 올린 모든 경로 앞에 `/api`가 붙는다.
- `Path`: URL의 `{post_id}`처럼 경로 한 조각을 검증한다.
- `Query`: `?page=1&q=안녕`을 검증한다.
- 본문 매개변수 타입이 Pydantic이면 JSON 바디다.
- 없는 경로는 404, 숫자여야 하는 id에 문자가 오면 400 `BAD_REQUEST`, 값 검증 실패는 400 `VALIDATION_ERROR`다. FastAPI의 기본 검증 코드는 422이지만, 이 앱은 공통 스펙에 맞추려고 400으로 바꾼다.

### 비유

`/api`는 건물 이름이고 `/posts/3`은 방 번호다. 방 번호 칸에 글자를 쓰면 안내 데스크가 "번호가 아니다"라고 돌려보내고, 방 안에 없는 번호를 누르면 "그 방은 없다"고 한다. 안내문은 항상 같은 양식이다.

## ③ 🛠️ 실기

조립은 `project/app/main.py`의 이 부분이다.

```python
api = APIRouter(prefix="/api")
api.include_router(post.router)
api.include_router(auth.router)
api.include_router(comment.router)
app.include_router(api)
```

줄별 설명:

1. prefix가 `/api`인 빈 라우터를 만든다. 체크리스트의 `APIRouter(prefix="/api")`가 이 줄이다.
2. 게시글 라우터의 `/posts`가 붙어 최종 경로는 `/api/posts`가 된다.
3. 회원 경로는 `/api/auth/...`가 된다.
4. 댓글 경로도 같은 접두어를 받는다.
5. 이 묶음을 앱에 등록해야 실제로 열린다.

게시글 라우터 `project/app/routers/post.py`의 조회와 생성은 다음과 같다.

```python
router = APIRouter(prefix="/posts", tags=["posts"], dependencies=[Depends(log_request_time)])

@router.get("", response_model=PostList)
def list_posts(page: PageParams = Depends(), db: Session = Depends(get_db)):
    return service.list_posts(db, q=page.q, sort=page.sort, page=page.page, limit=page.limit)

@router.get("/{post_id}", response_model=PostEnvelope)
def get_post(post_id: int = Path(..., gt=0), db: Session = Depends(get_db)):
    return PostEnvelope(data=service.present_one(db, service.get_post_or_404(db, post_id)))

@router.post("", response_model=PostEnvelope, status_code=201)
def create_post(post: PostCreate, response: Response, ...):
    created = service.create_post(...)
    response.headers["Location"] = f"/api/posts/{created.id}"
    return PostEnvelope(data=created)
```

- `""`는 prefix 그 자체, 즉 `/api/posts`다.
- `/{post_id}`는 동적 경로. `gt=0`이라 0과 음수는 거절된다.
- `post: PostCreate`는 JSON 본문이다. 쿼리와 경로는 `Path`/`Query`, 본문은 스키마다.
- 생성 성공은 201이고 `Location` 헤더에 새 글의 경로를 적는다.
- 수정은 `PATCH /api/posts/{id}`다. 보낸 필드만 바뀐다.
- 삭제는 `DELETE`와 204, 본문은 비어 있다.

없는 글은 서비스가 `AppError(404, "NOT_FOUND", ...)`를 던진다. 핸들러 `exceptions.py`가 이를 다음 모양으로 바꾼다.

```json
{
  "error": {
    "code": "NOT_FOUND",
    "message": "해당 게시글을 찾을 수 없습니다.",
    "requestId": "req-1"
  }
}
```

검증 실패는 `fields`가 더 붙는다.

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값을 확인하세요.",
    "fields": { "title": ["1~200자로 입력하세요."] },
    "requestId": "..."
  }
}
```

제목 길이 실패만 그 한글 문장으로 바꾸고, 나머지 검증 문장은 Pydantic 메시지를 필드별로 모은다. 경로 id가 숫자가 아니거나 JSON이 깨지면 코드는 `BAD_REQUEST`다.

요청에 `X-Request-Id`를 넣으면 응답 헤더가 같은 값을 돌려주고, 오류 본문의 `requestId`도 그 값이다. 헤더가 없으면 서버가 UUID를 만든다.

프론트 주소와 백엔드 주소를 맞출 때 화면은 `http://localhost:3000`, API는 `demo` 8001 / `project` 8000이다. 화면의 `VITE_API_BASE_URL`이 그 포트를 가리켜야 `/api/posts`가 같은 자원을 본다.

## ④ 🔗 연동 포인트

쿼리 `page`, `limit`, `q`, `sort`는 study3의 목록 메타와 study6의 SQL `offset/limit`로 이어진다. `Location`은 생성 직후 상세 조회로 이동할 때 쓴다. 프론트 `api.js`는 경로를 `/api/...`로만 부른다. 오류의 `error.message`와 `fields`는 study5 입력칸 아래에 그대로 표시한다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| `/posts`는 되고 `/api/posts`는 404 | 접두어 라우터를 앱에 안 붙임 | `APIRouter(prefix="/api")` 등록을 확인 |
| 검증이 422로 나감 | 기본 핸들러를 덮지 않음 | `RequestValidationError` 핸들러가 400을 반환하는지 확인 |
| `{"detail": ...}`만 보임 | `HTTPException` 기본 응답 | `http_exception_handler`가 `error` 객체를 만드는지 확인 |
| id에 `nope`을 넣었더니 422 | 경로 오류를 값 검증과 같은 코드로 봄 | 핸들러가 path 위치를 `BAD_REQUEST`로 나누는지 확인 |

## ⑥ 직접 해보기

1. `GET /api/posts?q=안녕&page=1&limit=10`의 쿼리가 메타에 반영되는지 본다.
2. `GET /api/posts/nope`과 `GET /api/posts/999`의 `error.code`가 다른지 비교한다.
3. 제목을 빈 문자열로 POST해 `fields.title`에 `1~200자로 입력하세요.`가 있는지 본다.

## ⑦ ☐ 체크리스트

- [ ] `/health`에는 `/api`가 없고 게시글·회원에는 있다.
- [ ] 동적 경로 `/{post_id}`와 쿼리 `page`, `q`를 구분할 수 있다.
- [ ] 생성은 201과 `Location`, 삭제는 204다.
- [ ] 경로, Path/Query, Pydantic 스키마
- [ ] 경로에 `/api` 접두어 (`APIRouter(prefix="/api")`)
- [ ] FastAPI 기본 `detail` 오류를 예외 핸들러로 `error.code/message/fields`로 통일

## ⑧ 다음 단계

경로가 요청을 받으면, study5에서 그 입력값을 거절·표시하고 같은 내용이 두 번 저장되지 않게 한다.
