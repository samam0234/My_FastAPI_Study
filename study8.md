# study8. 구조화와 재사용

## ① 목표

폴더와 설정을 나눠 같은 규칙을 한 곳에서만 고치게 만들고, 개발용 값과 운영용 값을 코드 밖으로 뺀다.

## ② 📖 이론

### 왜 쓰는지

CORS 허용 출처를 라우터마다 적으면 하나를 빼먹기 쉽다. 예외 문장도 라우터마다 `{"detail": ...}`로 만들면 화면이 두 가지 형식을 처리해야 한다. 공통 모듈로 올리면 등록은 `main.py` 한 번이다.

### 핵심 개념

- `config.py`: `.env`를 `Settings`로 읽는다. `get_settings()`는 캐시해서 파일을 매번 다시 읽지 않는다.
- `exceptions.py`: HTTP 오류, 검증 오류, 예상 못한 오류를 한 JSON으로 만든다.
- `middleware.py`: `X-Request-Id`.
- `security.py`: 해시와 JWT. DB를 모른다.
- 개발과 운영의 차이는 코드 분기가 아니라 `.env`의 값이다. 개발은 SQLite와 짧은 연습용 키, 운영은 긴 `SECRET_KEY`와 서버 DB URL, 실제 프론트 출처다.

### 비유

건물 수위실이 `main.py`다. 출입 명단(CORS), 사고 일지 양식(예외 핸들러), 방문증 번호(request id)를 수위실에서만 나눈다. 각 사무실(라우터)이 명단을 따로 복사해 두지 않는다.

## ③ 🛠️ 실기

`demo/app/main.py`와 `project/app/main.py`의 공통 조립은 같다. project만 업로드·AI·웹소켓을 더 등록한다.

```python
app.add_middleware(RequestIdMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["X-Request-Id"],
)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, unhandled_exception_handler)
```

줄별 설명:

1. 요청 id 미들웨어를 먼저 등록한다. 나중에 등록할수록 더 바깥이라, CORS가 이 미들웨어를 감싼다.
2. CORS 등록 시작.
3. Starlette가 브라우저 출처를 검사할 때 쓰는 클래스.
4. `.env`의 `CORS_ORIGINS`. 코드에 `localhost:3000`을 하드코딩하지 않는다.
5. 인증 헤더를 브라우저가 보내도 되게 한다.
6. GET만 열었다가 DELETE가 막히는 일을 피하려고 메서드는 모두 연다.
7. `Authorization`과 `Idempotency-Key`, `X-Request-Id`를 막지 않는다.
8. 브라우저의 자바스크립트가 `X-Request-Id`를 읽을 수 있게 노출한다.
9. CORS 등록 끝.
10. 우리가 던진 `AppError`를 `error.code` JSON으로 바꾼다.
11. 라우트가 없는 404처럼 프레임워크가 던진 HTTP 오류도 같은 모양으로 바꾼다.
12. 검증 오류를 400과 `fields`로 바꾼다.
13. 그 외 예외는 로그에만 스택을 남기고 500 `INTERNAL`과 일반 문장을 준다.

예외 핸들러가 500 본문에 `str(exc)`를 넣지 않는 이유는 파일 경로와 SQL이 사용자에게 가지 않게 하기 위해서다. `demo`의 `GET /debug/boom`이 일부러 `ValueError`를 던진다. 응답 본문에는 그 문장이 없고 코드만 `INTERNAL`이다. 테스트 클라이언트는 기본적으로 이런 예외를 다시 던지므로, 응답 JSON을 보려면 `TestClient(..., raise_server_exceptions=False)`가 필요하다. uvicorn으로 띄운 서버는 그 옵션 없이 JSON을 돌려준다.

설정 클래스의 기본값은 개발용이다. 운영에서는 같은 변수 이름에 다른 값을 넣는다.

```env
DATABASE_URL=sqlite:///./demo.db
SECRET_KEY=change-me-to-a-long-random-value
CORS_ORIGINS=["http://localhost:3000"]
```

운영 예시:

```env
DATABASE_URL=postgresql+psycopg://user:password@db:5432/demo
SECRET_KEY=길고-무작위한-값
CORS_ORIGINS=["https://board.example.com"]
```

코드의 `if production` 분기는 없다.

중복을 줄인 자리:

- 페이지 쿼리는 `PageParams` 하나.
- 404 문장은 `get_post_or_404` 하나.
- 오류 JSON은 핸들러 하나.
- 회원 공개 필드는 `UserResponse` 하나.

## ④ 🔗 연동 포인트

study7에서 설명한 CORS가 실제로 등록되는 곳이 이 파일이다. study4의 `requestId`도 여기서 미들웨어로 붙는다. study10과 study16은 이 `.env`를 배포 환경의 변수로 옮긴다. 개발 PC의 `.env`를 서버에 복사하지 않고, 서버의 환경 변수 화면에 같은 키를 다시 입력한다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 브라우저만 CORS 오류 | 출처가 목록에 없음 | `CORS_ORIGINS`에 스킴과 포트까지 같은 문자열을 넣는다 |
| `.env`를 고쳤는데 반영이 안 됨 | 설정이 프로세스 시작 때 캐시됨 | uvicorn을 재시작. `--reload`면 저장만으로 되는 경우가 많다 |
| 500 응답에 스택이 보임 | 일반 예외 핸들러가 없음 | `Exception` 핸들러가 일반 문장만 반환하는지 확인 |
| 테스트에서 boom이 예외로 실패 | TestClient의 기본값 | `raise_server_exceptions=False` |

## ⑥ 직접 해보기

1. `CORS_ORIGINS`에서 3000을 빼 보고 브라우저 콘솔의 CORS 문장을 확인한 뒤 되돌린다.
2. `/debug/boom`을 uvicorn으로 호출해 본문에 `ValueError`가 없는지 본다.
3. `SECRET_KEY`를 `.env`에서만 바꾸고, `security.py` 안에 키 문자열이 없는지 검색한다.

## ⑦ ☐ 체크리스트

- [ ] 라우터에 CORS와 오류 JSON을 복사해 두지 않았다.
- [ ] 비밀키와 DB 주소는 `Settings`만 읽는다.
- [ ] 개발용 기본값과 운영용 `.env`가 같은 키를 쓴다.
- [ ] 예상 못한 예외의 스택은 로그에만 있다.
- [ ] CORS, 예외 핸들러

## ⑧ 다음 단계

조립이 한곳으로 모였으면 study9에서 이 경로들을 서버를 띄우지 않고 테스트하고, DB는 테스트용으로 바꿔 끼운다.
