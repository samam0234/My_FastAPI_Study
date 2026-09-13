# study4. 실습4 — SQLAlchemy로 DB 연동 (`/posts`를 실제 DB 기반으로 전환)

Notion 학습 목표 대응: **SQLAlchemy / SQLModel + MySQL**

지금까지 `store.py`는 파이썬 리스트를 저장소로 썼습니다. 이번 문서에서 SQLAlchemy를 도입해 실제 데이터베이스에 저장하도록 바꿉니다.

## 1. SQLAlchemy 설치

```bash
pip install sqlalchemy
```

- SQLAlchemy는 Python에서 가장 널리 쓰이는 ORM(Object-Relational Mapping) 라이브러리입니다. Django의 내장 ORM에 대응하지만, Django와 달리 어떤 프레임워크와도 독립적으로 사용할 수 있습니다.
- FastAPI 자체는 어떤 DB/ORM을 쓸지 강제하지 않습니다. SQLAlchemy 외에 SQLModel(SQLAlchemy + Pydantic을 합친 라이브러리)도 많이 쓰이지만, 이 커리큘럼에서는 원리를 더 잘 보여주는 SQLAlchemy를 기준으로 진행합니다.

## 2. SQLite로 실습하고, MySQL로 바꾸는 법

실습 환경에 별도 DB 서버를 띄우기 번거로우므로, 개발 중에는 **SQLite**(파일 하나가 곧 DB인 경량 DB)를 사용합니다. `app/database.py`:

```python
from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

# 개발/실습용 SQLite 연결 문자열.
# 운영 환경에서 MySQL을 쓰려면 아래처럼 드라이버와 접속 정보만 바꾸면 됩니다.
#   pip install pymysql
#   SQLALCHEMY_DATABASE_URL = "mysql+pymysql://user:password@localhost:3306/demo"
SQLALCHEMY_DATABASE_URL = "sqlite:///./demo.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},  # SQLite 전용 옵션
)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- **핵심은 연결 문자열(`SQLALCHEMY_DATABASE_URL`)만 바꾸면 나머지 코드(모델, 쿼리)는 그대로 재사용된다는 점**입니다. SQLite(`sqlite:///`)든 MySQL(`mysql+pymysql://`)이든 SQLAlchemy가 같은 `Engine`/`Session` 인터페이스로 감싸주기 때문입니다.
- `connect_args={"check_same_thread": False}`는 SQLite에서만 필요한 옵션입니다. SQLite는 기본적으로 커넥션을 연 스레드에서만 쓸 수 있게 제한하는데, uvicorn은 요청마다 다른 스레드를 쓸 수 있어 이 제한을 풀어줘야 합니다. MySQL에서는 이 옵션이 필요 없습니다.
- `get_db()`는 study3에서 배운 "제너레이터 의존성" 패턴입니다. 요청이 들어오면 세션을 열고(`yield db`), 라우트 처리가 끝나면(응답 생성 후) `finally`에서 세션을 닫습니다 — DB 커넥션이 요청마다 새로 열리고 안전하게 닫히는 것을 보장합니다.

## 3. 모델 정의

`app/models.py`:

```python
from sqlalchemy import Boolean, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.database import Base


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    content: Mapped[str] = mapped_column(String, nullable=False)
    published: Mapped[bool] = mapped_column(Boolean, default=True)
```

- `Mapped[...]` + `mapped_column(...)`은 SQLAlchemy 2.0 스타일의 모델 선언 방식입니다. Django의 `models.py`에서 `CharField`, `BooleanField`를 쓰던 것과 같은 역할입니다.
- Django의 `makemigrations` + `migrate`에 해당하는 작업은, 이 실습 수준에서는 `Base.metadata.create_all(bind=engine)` 한 줄로 대신합니다 (`app/main.py`에서 앱 시작 시 실행). 실무에서는 스키마 변경 이력을 관리하기 위해 [Alembic](https://alembic.sqlalchemy.org/)이라는 마이그레이션 도구를 함께 씁니다.

## 4. Pydantic 스키마를 ORM과 연결하기

`app/schemas.py`의 `PostResponse`에 `model_config = ConfigDict(from_attributes=True)`를 추가했습니다.

```python
class PostResponse(PostCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
```

- 기본적으로 Pydantic은 dict나 Pydantic 모델에서만 값을 읽습니다. `from_attributes=True`를 켜면 SQLAlchemy 객체(`post.title`처럼 속성 접근)에서도 값을 읽어 변환할 수 있습니다.
- 덕분에 라우트가 `models.Post` 객체를 그대로 반환해도, `response_model=PostResponse` 덕분에 FastAPI가 자동으로 올바른 JSON으로 직렬화합니다.

## 5. `store.py`를 DB 기반으로 교체

라우터 코드(`routers/posts.py`)의 구조는 study3과 거의 동일하고, `store.py` 함수들만 SQL 쿼리로 바뀌었습니다.

```python
def get_post_or_404(db: Session, post_id: int) -> models.Post:
    post = db.get(models.Post, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"post {post_id}를 찾을 수 없습니다.")
    return post


def create_post(db: Session, post: PostCreate) -> models.Post:
    new_post = models.Post(**post.model_dump())
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post
```

- 라우터는 `db: Session = Depends(get_db)`로 세션을 주입받아 `store.xxx(db, ...)` 형태로 그대로 호출합니다. **의존성 주입 덕분에 "DB 세션을 어떻게 얻는가"가 라우트 코드에서 완전히 분리**되어 있습니다 — study3에서 만든 구조가 그대로 빛을 발하는 지점입니다.
- `db.add()` → `db.commit()` → `db.refresh()` 흐름: 세션에 객체를 등록 → 실제 DB에 반영 → DB가 채워준 값(자동 증가 `id` 등)을 다시 읽어옴.

## 6. 실습4: 동작 확인 (DB 영속성 검증)

```bash
uvicorn app.main:app --reload --port 8001
```

앱 시작 시 `demo.db` 파일이 생성되고, 테이블이 비어 있으면 초기 게시글 2개를 자동으로 넣어줍니다(`_seed_initial_posts`).

```bash
$ curl http://127.0.0.1:8001/posts
[{"title":"첫 번째 글","content":"FastAPI 공부를 시작합니다.","published":true,"id":1},
 {"title":"비공개 초안","content":"아직 다듬는 중입니다.","published":false,"id":2}]

$ curl -X POST http://127.0.0.1:8001/posts \
    -H "Content-Type: application/json" \
    -d '{"title":"study4 practice","content":"SQLAlchemy DB integration","published":true}'
{"title":"study4 practice","content":"SQLAlchemy DB integration","published":true,"id":3}
```

**서버를 완전히 종료했다가 다시 실행**해서 인메모리가 아니라 진짜 DB에 저장되는지 확인했습니다.

```bash
$ ls -la demo.db
-rw-r--r-- 1 User 197121 12288  9월 14 02:39 demo.db

$ curl http://127.0.0.1:8001/posts   # 서버 재시작 후
[{"title":"첫 번째 글", ..., "id":1},
 {"title":"비공개 초안", ..., "id":2},
 {"title":"study4 practice","content":"SQLAlchemy DB integration","published":true,"id":3}]
```

방금 만들었던 `id=3` 게시글이 재시작 후에도 그대로 남아있는 것을 확인했습니다 — study2의 인메모리 리스트였다면 서버를 재시작하는 순간 사라졌을 데이터입니다.

다음 문서(study5)에서는 이 커리큘럼의 또 다른 축인 **회원(User) 도메인**을 SQLAlchemy 모델로 추가하고, 비밀번호 해시와 회원가입을 구현합니다 (JWT 로그인 자체는 study7에서 진행).
