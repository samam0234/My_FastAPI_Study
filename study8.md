# study8. 고급 기술 구현 3 — CORS, 예외 핸들러

Notion 학습 목표 대응: **CORS, 예외 핸들러**

FastAPI는 API 전용 서버라서, 실제로는 React/Vue 같은 별도 프론트엔드(다른 origin)에서 호출되는 경우가 많습니다. 이번 문서에서는 **CORS 설정**으로 그걸 허용하고, 지금까지 라우트마다 제각각이던 에러 응답을 **전역 예외 핸들러**로 통일합니다.

## 1. CORS(Cross-Origin Resource Sharing)란?

브라우저는 기본적으로 "지금 보고 있는 페이지의 origin(스킴+호스트+포트)"과 다른 origin으로의 요청을 보안상 제한합니다. 예를 들어 `http://localhost:3000`(React 개발 서버)에서 `http://127.0.0.1:8001`(FastAPI)로 fetch 요청을 보내면, 서버가 "이 origin은 허용한다"고 명시적으로 응답하지 않는 한 브라우저가 응답을 막아버립니다.

`app/main.py`:

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

- `allow_origins`: 허용할 프론트엔드 주소 목록. 운영에서는 `["https://myapp.com"]`처럼 실제 배포 도메인만 명시하는 것이 안전합니다(`["*"]`는 `allow_credentials=True`와 함께 쓸 수 없고, 실습 이상의 환경에서는 지양).
- `allow_credentials=True`: 쿠키/Authorization 헤더를 포함한 요청을 허용.
- 브라우저는 실제 요청 전에 `OPTIONS` 메서드로 "이 요청 보내도 되는지" 먼저 물어보는 **프리플라이트(preflight)** 요청을 보냅니다. `CORSMiddleware`가 이 프리플라이트에 자동으로 응답해줍니다.

### 동작 확인

```bash
$ curl -i -X OPTIONS http://127.0.0.1:8001/posts \
    -H "Origin: http://localhost:3000" \
    -H "Access-Control-Request-Method: POST" \
    -H "Access-Control-Request-Headers: content-type"
HTTP/1.1 200 OK
access-control-allow-methods: DELETE, GET, HEAD, OPTIONS, PATCH, POST, PUT
access-control-allow-credentials: true
access-control-allow-origin: http://localhost:3000
access-control-allow-headers: content-type

$ curl -i -X OPTIONS http://127.0.0.1:8001/posts \
    -H "Origin: http://evil.example.com" \
    -H "Access-Control-Request-Method: POST"
HTTP/1.1 400 Bad Request   # access-control-allow-origin 헤더 자체가 없음
```

허용 목록에 없는 `evil.example.com`은 `access-control-allow-origin` 헤더 없이 400으로 거부되는 것을 확인했습니다 — 브라우저는 이 응답을 받으면 실제 요청을 보내지 않고 차단합니다.

## 2. 전역 예외 핸들러로 에러 포맷 통일

지금까지는 `HTTPException`(404/401/403)은 `{"detail": "..."}`, Pydantic 검증 실패(422)는 FastAPI 기본 포맷(`{"detail": [{"type":..., "loc":...}, ...]}`), 예상 못한 버그는 스택트레이스가 그대로 노출될 수 있는 500까지 — 상황마다 응답 형태가 달랐습니다. `app/exceptions.py`에서 세 종류를 각각 핸들러로 정리했습니다.

```python
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTPException(404, 401, 403 등)을 공통 포맷으로 응답한다."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 검증 실패(422)를 프론트엔드가 다루기 쉬운 형태로 통일한다."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "요청 데이터가 올바르지 않습니다.", "errors": exc.errors()},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """예상하지 못한 예외(버그)는 500으로 감싸고, 상세 내용은 서버 로그에만 남긴다."""
    logger.exception("unhandled error while processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "서버 내부 오류가 발생했습니다."},
    )
```

`app/main.py`에서 등록:

```python
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
```

- 세 핸들러 덕분에 이제 **어떤 종류의 에러든 클라이언트는 항상 `{"detail": ...}` 키를 기대할 수 있습니다.** 프론트엔드에서 에러 처리 로직을 한 곳으로 통일할 수 있다는 뜻입니다.
- 특히 `unhandled_exception_handler`가 중요합니다. 버그로 인한 예외(예: `None` 참조, 잘못된 타입 연산 등)가 그대로 밖으로 나가면 스택트레이스에 서버 내부 경로, 사용 중인 라이브러리 버전 같은 정보가 노출될 수 있습니다. `logger.exception(...)`으로 **서버 로그에는 전체 스택트레이스를 남기되, 클라이언트에게는 "서버 내부 오류가 발생했습니다"라는 안전한 메시지만** 돌려줍니다.
- 확인용으로 `app/main.py`에 일부러 예외를 던지는 `/debug/boom` 라우트를 추가했습니다.

## 3. 실습8: 세 가지 에러 케이스 확인

```bash
uvicorn app.main:app --reload --port 8001
```

### 404 (HTTPException)

```bash
$ curl -o - -w "\n%{http_code}\n" http://127.0.0.1:8001/posts/999
{"detail":"post 999를 찾을 수 없습니다."}
404
```

### 422 (검증 실패, 공통 포맷)

```bash
$ curl -o - -w "\n%{http_code}\n" -X POST http://127.0.0.1:8001/auth/register \
    -H "Content-Type: application/json" -d '{"username":"charlie"}'
{"detail":"요청 데이터가 올바르지 않습니다.","errors":[{"type":"missing","loc":["body","password"],"msg":"Field required","input":{"username":"charlie"}}]}
422
```

### 500 (예상하지 못한 예외)

```bash
$ curl -o - -w "\n%{http_code}\n" http://127.0.0.1:8001/debug/boom
{"detail":"서버 내부 오류가 발생했습니다."}
500
```

서버 로그에는 `ValueError: 일부러 발생시킨 예외입니다.`와 전체 스택트레이스가 남았지만, 클라이언트 응답에는 그 내용이 전혀 노출되지 않은 것을 확인했습니다.

다음 문서(study9)에서는 지금까지 `curl`로 손으로 확인해온 것들을 **pytest 테스트 코드**로 자동화합니다.
