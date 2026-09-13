# study11. 고급 기술 구현 6 — 도메인별 폴더 구조와 repository/service 계층 분리

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

**`schemas.py`, `models.py`, `store.py`가 "레이어" 기준으로만 나뉘어 있고, "도메인(기능)" 기준으로는 나뉘어 있지 않았습니다.** 지금은 게시글(posts)과 회원(users) 두 도메인뿐이라 파일 하나에 다 들어가도 봐줄 만했지만, 여기에 댓글(comments), 카테고리(categories), 알림(notifications) 같은 도메인이 하나씩 늘어난다고 생각해보면:

- `schemas.py` 하나에 6~8개 도메인의 스키마가 전부 쌓여서 파일이 수백 줄로 불어남
- "댓글 기능만 담당하는 사람"이 "회원가입 스키마가 들어있는 파일"을 열어야 자기 코드를 추가할 수 있음 → Git 충돌이 잦아짐
- `store.py`에 DB 쿼리와 비즈니스 규칙(중복 체크, 소유권 검사)이 뒤섞여 있어서, "이 함수가 그냥 조회인지, 검증까지 하는지"를 이름만 보고 알기 어려움

즉, **레이어(routers/schemas/models)로만 나누는 구조는 도메인 개수가 늘어날수록 안 맞습니다.** 실무에서 흔히 쓰는 FastAPI 구조는 "도메인 폴더 안에 레이어를 다시 두는" 방식입니다.

## 새 구조

```
app/
├── main.py
├── core/                     # 도메인에 속하지 않는 공용 인프라
│   ├── config.py              # pydantic-settings
│   ├── database.py            # Engine/Session/Base
│   ├── security.py            # 비밀번호 해시, JWT 인코딩 (범용 암호화 유틸)
│   ├── exceptions.py          # 전역 예외 핸들러
│   └── dependencies.py        # Pagination 등 여러 도메인이 공유하는 의존성
├── posts/                     # "게시글" 도메인
│   ├── models.py               # Post (SQLAlchemy)
│   ├── schemas.py              # PostCreate, PostResponse, PaginatedPosts (Pydantic)
│   ├── repository.py           # DB 접근만 (SQL 쿼리)
│   ├── service.py              # 비즈니스 로직 (404 변환, 소유권 검사, 백그라운드 작업)
│   └── router.py                # HTTP 계층 (요청 파싱 → service 호출 → 응답)
├── users/                      # "회원/인증" 도메인
│   ├── models.py, schemas.py, repository.py, service.py, router.py  # 위와 동일한 구성
└── practice/                   # 실제 도메인이 아닌 개념 실습용 (study6 async 비교)
    └── async_demo.py
```

포인트는 두 가지입니다.

1. **폴더를 기능(도메인) 기준으로 나눈다.** 댓글 기능이 추가되면 `app/comments/`를 통째로 추가하면 되고, 다른 도메인 폴더는 건드릴 필요가 없습니다.
2. **폴더 안에서는 레이어(models → repository → service → router)를 유지한다.** 도메인별로 나눴다고 계층 분리를 포기하는 게 아니라, "계층 분리 + 도메인 분리"를 동시에 하는 것입니다.

## repository와 service를 분리한 이유

기존 `store.py`에는 DB 쿼리와 비즈니스 규칙이 같이 있었습니다. 이번에 두 계층으로 쪼갰습니다.

**`repository.py` (posts 예시)** — SQLAlchemy 쿼리만 있고, HTTP나 "무엇이 잘못된 요청인지"는 전혀 모릅니다.

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

**`service.py` (posts 예시)** — "존재하지 않으면 404", "본인 글이 아니면 403", "글을 쓰면 알림 작업을 예약한다" 같은 **업무 규칙**을 담당합니다. repository를 호출하되, repository가 반환한 값을 가지고 판단을 내립니다.

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

**`router.py`**는 이제 HTTP 요청/응답 변환 말고는 아무 로직도 없습니다.

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

이렇게 나누면 얻는 것:

- **테스트하기 쉬워진다**: `service.update_post()`는 FastAPI/HTTP와 무관한 순수 함수라서, 나중에 CLI 스크립트나 배치 작업에서도 그대로 재사용할 수 있습니다.
- **책임이 분명해진다**: "이 쿼리가 잘못됐나?"는 repository를 보고, "왜 403이 나지?"는 service를 보면 됩니다. router는 "이 경로가 어떤 응답 모델을 쓰는지"만 보면 됩니다.
- **회원(users)과 게시글(posts)이 서로의 내부 구현을 몰라도 된다**: `posts` 도메인은 `users.models.User`, `users.service.get_current_user`처럼 users의 **공개 인터페이스**만 가져다 쓰고, users의 repository나 내부 쿼리 방식은 알 필요가 없습니다.

## `users`(회원)와 `posts`(게시글) 사이의 의존 방향

`Post` 모델은 `author_id`로 `users.id`를 참조하지만, `posts/models.py`는 `User` 클래스를 import하지 않습니다 — `ForeignKey("users.id")`처럼 **테이블 이름 문자열**로만 참조합니다. SQLAlchemy가 앱이 뜰 때(두 모델이 모두 import된 뒤) 이 문자열을 실제 테이블과 연결해주기 때문에, `posts` 모듈이 `users` 모듈의 클래스를 직접 알 필요가 없습니다.

반대로 `posts/service.py`, `posts/router.py`는 로그인한 사용자가 누구인지 알아야 하므로 `users.models.User`, `users.service.get_current_user`를 가져다 씁니다. 즉 **의존성은 `posts → users` 한 방향으로만 흐르고, `users`는 `posts`를 전혀 모릅니다.** 도메인이 늘어나도 이 원칙(하위 도메인이 상위 도메인을 모르게 하기)을 지키면 순환 참조 없이 폴더를 계속 추가할 수 있습니다.

## `core/`에는 무엇을 두는가

`core/security.py`의 비밀번호 해시·JWT 인코딩 함수는 "회원(User)이 무엇인지" 몰라도 동작하는 **범용 암호화 유틸리티**라서 `users/` 안이 아니라 `core/`에 남겨뒀습니다. 반면 `get_current_user()`(토큰으로 실제 `User`를 조회하는 함수)는 `users` 도메인을 알아야 하므로 `users/service.py`로 옮겼습니다. **"도메인 지식이 필요한가"가 core냐 도메인 폴더냐를 가르는 기준**입니다.

## 실습11: 리팩터링 후 회귀 확인

파일 구조만 바꿨을 뿐 동작은 study10과 완전히 동일해야 합니다. `tests/conftest.py`의 import 경로(`app.database` → `app.core.database`)만 고치고, 나머지 테스트 코드는 손대지 않았습니다.

```bash
$ pytest -v
...
======================== 9 passed, 2 warnings in 3.30s ========================
```

study9에서 만든 9개 테스트가 구조 변경 후에도 그대로 통과했습니다 — 도메인/계층을 재배치해도 외부에서 관찰되는 동작(API 응답)은 바뀌지 않았다는 뜻입니다.

```bash
$ uvicorn app.main:app --reload --port 8001
$ curl http://127.0.0.1:8001/posts
{"items":[...],"total":2,"skip":0,"limit":10}

$ curl -X POST http://127.0.0.1:8001/auth/register -d '{"username":"alice","password":"secret123"}' -H "Content-Type: application/json"
{"id":1,"username":"alice"}
# 로그인 → 토큰으로 글쓰기 → 미인증 글쓰기 차단(401) → /async-demo/* 및 /docs 정상 응답까지 재확인 완료
```

다음 단계(`studyFinal`)에서는 `project/`도 이 구조로 다시 정리합니다.
