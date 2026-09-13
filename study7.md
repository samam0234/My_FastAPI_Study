# study7. 고급 기술 구현 2 — JWT 인증 (`/auth/login`)

Notion 학습 목표 대응: **JWT 인증**

공통 스펙의 마지막 조각인 `/auth/login`을 완성합니다. 로그인하면 JWT(JSON Web Token)를 발급하고, `/posts` 작성/수정/삭제는 이 토큰을 가진 사용자만 할 수 있도록 만듭니다. 더 나아가 "본인 글만 수정/삭제 가능"한 소유권 검사도 추가합니다.

## 1. 세션(Django) vs JWT(FastAPI)

- Django는 기본적으로 **세션 기반 인증**을 씁니다. 로그인하면 서버가 세션을 DB/캐시에 저장하고, 브라우저에는 세션 id가 담긴 쿠키만 내려줍니다. 서버가 "누가 로그인했는지"를 기억합니다(stateful).
- FastAPI(API 서버)는 보통 **JWT 기반 인증**을 씁니다. 로그인 성공 시 사용자 정보를 담은 토큰을 암호 서명해서 발급하고, 이후 요청마다 클라이언트가 `Authorization: Bearer <토큰>` 헤더로 그 토큰을 실어 보냅니다. 서버는 세션을 저장할 필요 없이 **토큰 서명만 검증**하면 되어(stateless) 여러 서버로 수평 확장하기 쉽습니다.

```bash
pip install "python-jose[cryptography]" python-multipart
```

- `python-jose`: JWT를 만들고(encode) 검증하는(decode) 라이브러리.
- `python-multipart`: FastAPI가 폼 데이터(`application/x-www-form-urlencoded`, 파일 업로드 등)를 파싱하는 데 필요합니다. 로그인에 쓰는 `OAuth2PasswordRequestForm`이 내부적으로 폼 파싱을 사용하므로 반드시 설치해야 합니다(없으면 서버 실행 시 에러가 납니다).

## 2. 토큰 발급 함수

`app/security.py`에 추가:

```python
SECRET_KEY = "study-only-secret-key-do-not-use-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
```

- `SECRET_KEY`는 서버만 알고 있는 값으로, 이 키로 서명한 토큰만 "우리 서버가 발급한 진짜 토큰"임을 검증할 수 있습니다. 실습용으로 하드코딩했지만, 실제 서비스에서는 반드시 `.env` 등 환경변수로 분리해야 합니다(study10에서 설정 관리를 다룰 때 정리).
- `exp` 클레임으로 만료 시각을 넣어두면, 만료된 토큰은 서명이 맞아도 `jwt.decode()`가 자동으로 거부합니다.

## 3. `/auth/login` 라우트

`app/routers/auth.py`:

```python
@router.post("/login", response_model=Token)
def login(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    user = store.get_user_by_username(db, form_data.username)
    if user is None or not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="username 또는 password가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")
```

- `OAuth2PasswordRequestForm`은 FastAPI가 제공하는 표준 로그인 폼 스키마입니다. JSON이 아니라 `username=...&password=...` 형태의 폼 데이터를 받는다는 점이 다른 라우트와 다릅니다(OAuth2 표준 방식).
- 아이디가 없거나 비밀번호가 study5에서 만든 `verify_password()` 검증을 통과하지 못하면 401을 반환합니다.
- 성공하면 `{"sub": username}`을 담아 토큰을 발급합니다. `sub`(subject)는 JWT 표준 클레임으로 "이 토큰이 누구 것인가"를 나타냅니다.

## 4. 토큰 검증 의존성: `get_current_user`

`app/dependencies.py`:

```python
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = store.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user
```

- `OAuth2PasswordBearer(tokenUrl="auth/login")`는 요청의 `Authorization: Bearer <토큰>` 헤더에서 토큰 문자열을 자동으로 뽑아줍니다. `tokenUrl`은 실제 검증과는 무관하고, `/docs`의 "Authorize" 버튼이 어디로 로그인 요청을 보낼지 알려주는 용도입니다.
- 이 함수 자체가 study3에서 배운 **의존성**입니다. `current_user: models.User = Depends(get_current_user)`처럼 라우트 인자에 선언하기만 하면, "로그인 여부 확인 + 로그인한 User 객체 조회"가 자동으로 이루어집니다.
- 토큰이 없거나(`Not authenticated`는 `oauth2_scheme` 자체가 던짐), 위조/만료됐거나(`JWTError`), 토큰은 유효한데 그 사이 사용자가 삭제된 경우 모두 401로 처리합니다.

## 5. `/posts` 보호 + 작성자(소유권) 검사

- `POST /posts`: `current_user: models.User = Depends(get_current_user)`를 추가해 로그인한 사용자만 글을 쓸 수 있게 하고, `store.create_post(db, post, author_id=current_user.id)`로 작성자를 기록합니다. (`Post` 모델에 `author_id: Mapped[Optional[int]] = mapped_column(ForeignKey("users.id"))` 컬럼을 추가했습니다.)
- `PUT /posts/{id}`, `DELETE /posts/{id}`: 역시 로그인을 요구하고, 게시글의 `author_id`가 현재 로그인한 사용자와 다르면 `403 Forbidden`을 반환하는 `_check_owner()` 헬퍼로 소유권을 검사합니다.
- `GET /posts`, `GET /posts/{id}`(조회)는 그대로 로그인 없이 열람 가능하게 두었습니다 — "쓰기만 보호"하는 흔한 정책입니다.

## 6. 실습7: 전체 인증 흐름 확인

```bash
uvicorn app.main:app --reload --port 8001
```

### 인증 없이 글쓰기 시도 → 401

```bash
$ curl -o - -w "\n%{http_code}\n" -X POST http://127.0.0.1:8001/posts \
    -H "Content-Type: application/json" -d '{"title":"no auth","content":"should fail","published":true}'
{"detail":"Not authenticated"}
401
```

### 로그인 → 토큰 발급

```bash
$ curl -X POST http://127.0.0.1:8001/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" \
    -d "username=alice&password=secret123"
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type":"bearer"}
```

### 토큰으로 글쓰기 → author_id 자동 기록

```bash
$ curl -X POST http://127.0.0.1:8001/posts \
    -H "Content-Type: application/json" -H "Authorization: Bearer <alice의 토큰>" \
    -d '{"title":"study7 jwt post","content":"created by alice","published":true}'
{"title":"study7 jwt post","content":"created by alice","published":true,"id":3,"author_id":1}
```

### 다른 사람(bob)이 alice 글을 수정 시도 → 403

```bash
$ curl -o - -w "\n%{http_code}\n" -X PUT http://127.0.0.1:8001/posts/3 \
    -H "Content-Type: application/json" -H "Authorization: Bearer <bob의 토큰>" \
    -d '{"title":"hijacked","content":"bob trying to edit","published":true}'
{"detail":"본인이 작성한 글만 수정/삭제할 수 있습니다."}
403
```

### 본인(alice)이 수정 → 200

```bash
$ curl -X PUT http://127.0.0.1:8001/posts/3 \
    -H "Content-Type: application/json" -H "Authorization: Bearer <alice의 토큰>" \
    -d '{"title":"study7 jwt post (edited)","content":"edited by alice","published":true}'
{"title":"study7 jwt post (edited)","content":"edited by alice","published":true,"id":3,"author_id":1}
```

### 위조/조작된 토큰 → 401

```bash
$ curl -o - -w "\n%{http_code}\n" -X POST http://127.0.0.1:8001/posts \
    -H "Authorization: Bearer garbage.token.value" \
    -H "Content-Type: application/json" -d '{"title":"x","content":"y","published":true}'
{"detail":"인증 정보를 확인할 수 없습니다."}
401
```

로그인 없이 쓰기 차단(401), 다른 사람 글 수정 차단(403), 위조 토큰 차단(401), 본인 글 정상 처리(200/201)까지 네 가지 케이스를 모두 실제로 재현해 확인했습니다.

`/docs`(Swagger UI) 오른쪽 위의 **Authorize** 버튼에 `username`/`password`를 입력하면 브라우저에서도 토큰 발급부터 인증이 필요한 라우트 호출까지 한 번에 테스트할 수 있습니다.

다음 문서(study8)에서는 프론트엔드 연동을 위한 **CORS 설정**과, 지금까지 각 라우트에서 개별적으로 처리하던 에러를 **전역 예외 핸들러**로 통일합니다.
