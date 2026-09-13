# study11. 고급 기술 구현 6 — 레이어별 폴더 구조(models/repositories/schemas/services/routers)

## 왜 다시 구조를 손보는가

study3에서 `routers/`, `schemas.py`, `models.py`, `store.py`로 계층을 나눴습니다. 그런데 그 구조를 study10까지 그대로 끌고 오면서 문제가 하나 있었습니다.

```
app/
├── routers/
│   ├── posts.py
│   └── auth.py
├── schemas.py   # PostCreate, PostResponse, PaginatedPosts, UserCreate, UserResponse, Token 전부
├── models.py    # Post, User 전부
└── store.py     # posts용 함수 + users용 함수 전부
```

`routers/`만 폴더로 분리되어 있고, `schemas.py`/`models.py`/`store.py`는 여러 기능이 뒤섞인 파일 하나로 남아 있었습니다. 지금은 게시글(posts)과 회원(users) 두 기능뿐이라 봐줄 만했지만, 여기에 댓글·카테고리 같은 기능이 늘어나면 파일 하나가 계속 불어나는 구조입니다.

이번 문서에서는 아래처럼 **레이어(계층)마다 폴더를 만들고, 그 폴더 안에 기능별 파일을 두는 구조**로 정리합니다.

```
app/
├── __init__.py
├── main.py
├── config.py          # pydantic-settings 기반 환경설정
├── database.py        # SQLAlchemy Engine/Session
├── security.py         # 비밀번호 해시, JWT 인코딩 (범용 유틸)
├── exceptions.py       # 전역 예외 핸들러
├── dependencies.py     # Pagination 등 여러 라우터가 공유하는 의존성
├── models/              # 모델단
│   ├── post.py            # Post (SQLAlchemy)
│   └── user.py            # User (SQLAlchemy)
├── schemas/             # 스키마단
│   ├── post.py            # PostCreate, PostResponse, PaginatedPosts (Pydantic)
│   └── user.py            # UserCreate, UserResponse, Token (Pydantic)
├── repositories/        # 레포지토리단
│   ├── post.py            # DB 접근만 (SQL 쿼리)
│   └── user.py
├── services/            # 서비스단
│   ├── post.py            # 비즈니스 로직 (404 변환, 소유권 검사, 백그라운드 작업)
│   └── user.py            # 회원가입 규칙, 로그인 인증, get_current_user
└── routers/             # 라우터단
    ├── post.py            # HTTP 계층, prefix="/posts"
    ├── auth.py             # HTTP 계층, prefix="/auth"
    └── async_demo.py       # study6 개념 확인용 (실제 기능 아님)
```

`models`, `schemas`, `repositories`, `services`, `routers` 각각이 폴더가 되고, 그 안에 `post.py`, `user.py`처럼 기능별 파일을 둡니다. 기능이 늘어나면(예: 댓글) 다섯 폴더 각각에 `comment.py` 파일 하나씩만 추가하면 됩니다.

## 레이어별 역할

**`models/post.py`** — SQLAlchemy ORM 모델. 테이블 구조만 정의합니다.

**`schemas/post.py`** — Pydantic 스키마. 요청/응답 데이터 형태만 정의합니다.

**`repositories/post.py`** — DB 접근 전용. HTTP나 "무엇이 잘못된 요청인지"는 전혀 모르고, SQLAlchemy 쿼리만 있습니다.

```python
def get_by_id(db: Session, post_id: int) -> Optional[Post]:
    return db.get(Post, post_id)


def create(db: Session, post: PostCreate, author_id: int) -> Post:
    new_post = Post(**post.model_dump(), author_id=author_id)
    db.add(new_post)
    db.commit()
    db.refresh(new_post)
    return new_post
```

**`services/post.py`** — 비즈니스 규칙. "존재하지 않으면 404", "본인 글이 아니면 403", "글을 쓰면 알림 작업을 예약한다" 같은 판단을 여기서 내리고, repository를 호출해 실제 DB 작업을 위임합니다.

```python
def get_post_or_404(db: Session, post_id: int) -> Post:
    post = repository.get_by_id(db, post_id)
    if post is None:
        raise HTTPException(status_code=404, detail=f"post {post_id}를 찾을 수 없습니다.")
    return post


def update_post(db: Session, post_id: int, data: PostCreate, current_user: User) -> Post:
    existing = get_post_or_404(db, post_id)
    _check_owner(existing, current_user)      # 소유권 검사(비즈니스 규칙)
    return repository.update(db, existing, data)
```

**`routers/post.py`** — HTTP 계층. 요청을 파싱해서 service를 호출하고, service가 돌려준 값을 그대로 응답합니다. 이제 라우터 함수 안에는 SQL도, 소유권 검사도 없습니다.

```python
@router.put("/{post_id}", response_model=PostResponse)
def update_post(
    post_id: int,
    post: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    return service.update_post(db, post_id, post, current_user)
```

이렇게 나누면:

- **테스트하기 쉬워진다**: `service.update_post()`는 FastAPI/HTTP와 무관한 순수 함수라서, 나중에 CLI 스크립트나 배치 작업에서도 재사용할 수 있습니다.
- **책임이 분명해진다**: "쿼리가 잘못됐나?"는 `repositories/`를, "왜 403이 나지?"는 `services/`를, "이 경로가 어떤 응답 모델을 쓰는지"는 `routers/`를 보면 됩니다.
- **기능이 늘어나도 규칙이 같다**: 댓글 기능을 추가하면 `models/comment.py`, `schemas/comment.py`, `repositories/comment.py`, `services/comment.py`, `routers/comment.py`를 각 폴더에 하나씩 추가하면 됩니다.

## import 예시로 보는 흐름

```python
# repositories/post.py
from app.models.post import Post
from app.schemas.post import PostCreate

# services/post.py
from app.models.post import Post
from app.models.user import User
from app.repositories import post as repository
from app.schemas.post import PaginatedPosts, PostCreate

# routers/post.py
from app.schemas.post import PaginatedPosts, PostCreate, PostResponse
from app.services import post as service
from app.services.user import get_current_user
```

`routers → services → repositories → models` 순서로만 의존하고, 반대 방향(`models`가 `services`를 알거나 하는 것)은 없습니다. `services/post.py`가 `models/user.py`, `services/user.py`를 가져다 쓰는 것처럼, "게시글(post)" 기능이 "회원(user)" 기능의 결과물을 참조하는 것은 자연스럽지만, 그 반대(`services/user.py`가 `post`를 참조하는 것)는 없습니다.

## 실습11: 리팩터링 후 회귀 확인

폴더 구조만 바꿨을 뿐 동작은 study10과 완전히 동일해야 합니다. `tests/conftest.py`의 import 경로(`app.core.database` → `app.database`)만 고치고, 나머지 테스트 코드는 손대지 않았습니다.

```bash
$ pytest -v
...
======================== 9 passed, 2 warnings in 3.32s ========================
```

study9에서 만든 9개 테스트가 구조 변경 후에도 그대로 통과했습니다.

```bash
$ uvicorn app.main:app --reload --port 8001
$ curl http://127.0.0.1:8001/posts
{"items":[...],"total":2,"skip":0,"limit":10}

$ curl -X POST http://127.0.0.1:8001/auth/register -d '{"username":"alice","password":"secret123"}' -H "Content-Type: application/json"
{"id":1,"username":"alice"}
# 로그인 → 토큰으로 글쓰기 → 미인증 글쓰기 차단(401) → /async-demo/* 및 /docs 정상 응답까지 재확인 완료
```

다음 단계(`studyFinal`)에서는 `project/`도 이 구조로 다시 정리합니다.
