# study5. 실습5 — User 모델과 회원가입 (`/auth/register`)

Notion 학습 목표 대응: (회원 도메인 준비 — JWT 인증의 기반)

공통 스펙 `/posts` CRUD + `/auth/login` 중 아직 손대지 않은 `/auth` 쪽을 시작합니다. 로그인(JWT 발급)은 인증 개념을 따로 다루는 study7에서 구현하고, 이번 문서에서는 그 전 단계인 **회원 모델 설계 + 비밀번호 해시 + 회원가입**을 만듭니다.

## 1. User 모델

`app/models.py`에 추가:

```python
class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String, nullable=False)
```

- `unique=True`: DB 레벨에서 username 중복을 막습니다. 다만 이번 실습에서는 애플리케이션 레벨(`store.create_user`)에서도 먼저 확인해, 사용자에게 500 에러 대신 의미 있는 400 에러를 보여주도록 했습니다.
- 비밀번호는 **절대 평문으로 저장하지 않습니다.** 컬럼 이름부터 `hashed_password`로 지어 "여기 들어가는 값은 해시된 값"이라는 의도를 코드로 드러냈습니다.

## 2. 비밀번호 해시: `passlib`

```bash
pip install passlib
```

`app/security.py`:

```python
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
```

- `CryptContext`는 여러 해시 알고리즘을 추상화해줍니다. 알고리즘을 `bcrypt`에서 `argon2`로 바꾸는 식의 마이그레이션도 스킴 목록만 바꾸면 됩니다.
- 이번 실습에서는 `pbkdf2_sha256`을 사용했습니다. `bcrypt`가 더 널리 쓰이지만 OS별로 컴파일된 확장이 필요해 환경에 따라 설치가 까다로울 수 있는 반면, `pbkdf2_sha256`은 순수 파이썬(hashlib 표준 라이브러리 기반)으로 동작해 별도 컴파일 없이 어디서나 동일하게 동작합니다.
- `verify_password`는 해시를 복호화하는 게 아니라, 입력값을 같은 방식으로 다시 해시해서 저장된 해시와 **비교**하는 함수입니다(단방향 해시의 특징).

## 3. 회원가입 스키마 + 라우트

`app/schemas.py`:

```python
class UserCreate(BaseModel):
    username: str
    password: str


class UserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str
```

- `UserCreate`(요청)에는 `password`가 있지만, `UserResponse`(응답)에는 **`password`도 `hashed_password`도 없습니다.** `response_model=UserResponse`를 지정해두면 라우트가 실수로 `User` ORM 객체를 통째로 반환하더라도 FastAPI가 `UserResponse` 스키마 기준으로 다시 걸러서 직렬화하므로, 해시값이 응답에 실려 나갈 위험이 없습니다.

`app/store.py`에 추가:

```python
def create_user(db: Session, user: UserCreate) -> models.User:
    if get_user_by_username(db, user.username) is not None:
        raise HTTPException(status_code=400, detail="이미 존재하는 username입니다.")
    new_user = models.User(username=user.username, hashed_password=hash_password(user.password))
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user
```

`app/routers/auth.py` (새 라우터):

```python
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=UserResponse, status_code=201)
def register(user: UserCreate, db: Session = Depends(get_db)):
    return store.create_user(db, user)
```

`app/main.py`에 `app.include_router(auth.router)` 한 줄을 추가해 등록했습니다. 이제 `/posts`(게시글)와 `/auth`(회원)가 각자 별도 라우터 모듈로 나뉘어 있습니다.

## 4. 실습5: 동작 확인

```bash
uvicorn app.main:app --reload --port 8001
```

```bash
$ curl -X POST http://127.0.0.1:8001/auth/register \
    -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}'
{"id":1,"username":"alice"}

$ curl -o - -w "\n%{http_code}\n" -X POST http://127.0.0.1:8001/auth/register \
    -H "Content-Type: application/json" -d '{"username":"alice","password":"anything"}'
{"detail":"이미 존재하는 username입니다."}
400

$ curl -X POST http://127.0.0.1:8001/auth/register \
    -H "Content-Type: application/json" -d '{"username":"bob","password":"hunter2"}'
{"id":2,"username":"bob"}
```

응답에 비밀번호가 전혀 노출되지 않는 것도 확인했고, DB에 실제로 어떤 값이 저장됐는지 직접 열어봤습니다.

```bash
$ sqlite3 demo.db "select id, username, hashed_password from users;"
1|alice|$pbkdf2-sha256$29000$XEtJ6f3/X6vVWkuJUcq5lw$Vro5s74HB0WmV/aP.U5h2zEeF8fRS5EtsFlfvfHNndI
2|bob|$pbkdf2-sha256$29000$iRGiFKIUYkwphVCKMaYUwg$cjgTk7OgWPuZop63ofvY5SyW1ex/Ee0ccfGcvSljQKI
```

평문 `secret123`, `hunter2`가 아니라 매번 다른 salt가 섞인 해시값이 저장된 것을 확인했습니다.

다음 문서(study6)부터는 "고급 기술 구현" 파트로 넘어가, 먼저 **비동기 라우트**(`async def`, 블로킹 I/O 문제, `BackgroundTasks`)를 다룹니다.
