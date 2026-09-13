# study10. 고급 기술 구현 5 — 설정 관리(.env)와 페이지네이션 응답 다듬기

Notion 학습 목표 (마무리): 지금까지 하드코딩되어 있던 값들을 정리하고, studyFinal에서 그대로 재사용할 수 있도록 마무리합니다.

## 1. 지금까지 쌓인 문제: 하드코딩된 설정값

- `app/database.py`: `SQLALCHEMY_DATABASE_URL = "sqlite:///./demo.db"`가 코드에 박혀 있음
- `app/security.py`: `SECRET_KEY`가 소스코드에 그대로 노출되어 있음(study7에서 "실제로는 .env로 분리해야 한다"고 예고했던 부분)
- `app/main.py`: CORS 허용 origin 목록이 코드에 고정되어 있음

운영 환경(로컬 개발 / 테스트 / 배포)마다 이 값들이 달라야 하는데, 지금 구조로는 코드를 직접 고쳐야 합니다. 이를 [pydantic-settings](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)로 분리합니다.

```bash
pip install pydantic-settings
```

## 2. `Settings` 클래스

`app/config.py`:

```python
from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    database_url: str = "sqlite:///./demo.db"
    secret_key: str = "study-only-secret-key-do-not-use-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    cors_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- `BaseSettings`는 Pydantic `BaseModel`과 거의 같지만, **필드 값을 환경변수(`.env` 파일 포함)에서 자동으로 읽어옵니다.** 필드명 `database_url` → 환경변수 `DATABASE_URL`처럼 대소문자만 다르게 매칭됩니다.
- `@lru_cache`를 붙인 `get_settings()`: 매 요청마다 `.env`를 다시 읽지 않도록, 앱이 실행되는 동안 `Settings` 인스턴스를 한 번만 만들어 재사용합니다(Depends로 라우트에 주입할 수도 있지만, 이 실습에서는 모듈 로드 시 한 번 호출해 값만 꺼내 쓰는 단순한 방식을 사용했습니다).
- `.env` 파일 자체는 `.gitignore`에 있어 커밋되지 않으므로, 팀원이 값을 채워 넣을 수 있도록 `demo/.env.example`(실제 값 대신 예시만 담음)을 함께 커밋해두었습니다.

`demo/.env.example`:

```bash
DATABASE_URL=sqlite:///./demo.db
# MySQL을 쓴다면: DATABASE_URL=mysql+pymysql://user:password@localhost:3306/demo

SECRET_KEY=change-me-to-a-long-random-value
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 리스트 형태 값은 JSON 배열 문자열로 지정합니다.
CORS_ORIGINS=["http://localhost:3000", "http://127.0.0.1:3000"]
```

## 3. 기존 모듈들이 설정값을 가져다 쓰도록 수정

`app/database.py`:

```python
settings = get_settings()
SQLALCHEMY_DATABASE_URL = settings.database_url

connect_args = {}
if SQLALCHEMY_DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args=connect_args)
```

- SQLite 전용 옵션(`check_same_thread`)을 연결 문자열이 `sqlite`로 시작할 때만 붙이도록 조건을 추가해서, `.env`의 `DATABASE_URL`을 MySQL로 바꿔도(`mysql+pymysql://...`) 코드 수정 없이 그대로 동작하게 했습니다(study4에서 예고했던 부분의 완성).

`app/security.py`, `app/main.py`도 각각 `SECRET_KEY`/`ALGORITHM`/`ACCESS_TOKEN_EXPIRE_MINUTES`, `cors_origins`를 하드코딩 대신 `get_settings()`에서 읽어오도록 바꿨습니다. 나머지 라우터/스토어 코드는 전혀 손대지 않았습니다 — study3에서 계층을 분리해둔 효과가 여기서도 이어집니다.

## 4. 목록 API 응답에 페이지네이션 메타데이터 추가

지금까지 `GET /posts`는 배열만 반환해서, 프론트엔드가 "전체 몇 개 중 몇 개를 보고 있는지" 알 수 없었습니다. `app/schemas.py`에 추가:

```python
class PaginatedPosts(BaseModel):
    items: list[PostResponse]
    total: int
    skip: int
    limit: int
```

`app/routers/posts.py`:

```python
@router.get("", response_model=PaginatedPosts)
def list_posts(
    published: Optional[bool] = Query(default=None, description="공개 여부로 필터링"),
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db),
):
    result = store.list_posts(db)
    if published is not None:
        result = [p for p in result if p.published == published]
    page = result[pagination.skip : pagination.skip + pagination.limit]
    return PaginatedPosts(items=page, total=len(result), skip=pagination.skip, limit=pagination.limit)
```

응답 형태가 배열(`[...]`)에서 `{"items": [...], "total": ..., "skip": ..., "limit": ...}`로 바뀌었으므로, study9에서 만든 `test_list_posts_empty` 테스트도 새 포맷에 맞게 함께 수정했습니다.

## 5. 실습10: 동작 확인

```bash
cp .env.example .env   # 값은 예시 그대로 사용
uvicorn app.main:app --reload --port 8001
```

```bash
$ curl http://127.0.0.1:8001/posts
{"items":[{"title":"첫 번째 글","content":"FastAPI 공부를 시작합니다.","published":true,"id":1,"author_id":null},
          {"title":"비공개 초안","content":"아직 다듬는 중입니다.","published":false,"id":2,"author_id":null}],
 "total":2,"skip":0,"limit":10}

$ curl "http://127.0.0.1:8001/posts?limit=1"
{"items":[{"title":"첫 번째 글", ...}], "total":2, "skip":0, "limit":1}
```

`.env` 파일의 값이 실제로 적용되는지(설정 분리가 제대로 동작하는지) 확인했고, `total`이 필터링 전 전체 개수(2)로 정확히 집계되는 것도 확인했습니다.

```bash
$ pytest -v
...
======================== 9 passed, 2 warnings in 3.32s ========================
```

설정을 분리하고 응답 포맷을 바꾼 뒤에도 study9에서 만든 테스트 9개가 모두 그대로 통과하는 것을 확인했습니다 — 회귀가 없다는 뜻입니다.

여기까지 Notion 학습 목표(경로/Path/Query/Pydantic, 의존성 주입, SQLAlchemy+DB, 비동기 라우트, JWT 인증, CORS/예외 핸들러, 테스트코드)를 모두 다뤘습니다. 다음 문서(studyFinal)에서는 `demo/`에서 익힌 내용을 전부 모아 `project/`에 완결된 미니 게시판 API를 처음부터 다시 설계해 만듭니다.
