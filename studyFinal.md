# studyFinal. 미니 게시판 API 종합 프로젝트

지금까지 `demo/`에서 study0~study11을 거치며 단계적으로 쌓아온 내용을 모두 모아, `project/`에 **완결된 미니 게시판 API**를 처음부터 다시 설계해서 만들었습니다. 공통 스펙이었던 `/posts` CRUD + `/auth/login`을 갖춘 완성형 서비스입니다.

## 1. `demo/`와 `project/`의 차이

- `demo/`: study1의 파일 하나짜리 앱에서 시작해, study11까지 매 단계 "이번에 뭘 배웠고 무엇이 바뀌었는지"를 보여주기 위해 점진적으로 리팩터링해온 **학습용 기록**입니다. (`/async-demo/*`, `/debug/boom` 같은 개념 확인용 라우트도 `practice/` 아래 남아있습니다.)
- `project/`: 그 학습 결과를 반영해 **처음부터 완성된 구조**로 다시 만든 결과물입니다. 도메인별 폴더(`core/`, `posts/`, `users/`) + `repository`/`service` 계층 분리, 설정 분리(`.env`), DB 연동, JWT 인증, CORS, 전역 예외 처리, 테스트가 첫 커밋부터 모두 갖춰져 있고, 순수 학습/실험용 라우트는 제외했습니다.

## 2. 적용한 기능과 대응 study

| 기능 | 설명 | 대응 study |
|---|---|---|
| `app/` 패키지 구조 | 도메인별 폴더(`core/`, `posts/`, `users/`), 폴더마다 `models/schemas/repository/service/router` 계층 | study1, study3, study11 |
| `/posts` CRUD | Path/Query 파라미터 + Pydantic 스키마(`PostCreate`/`PostResponse`) | study2 |
| 의존성 주입 | `Pagination`(페이지네이션), `get_current_user`(인증) | study3, study7 |
| SQLAlchemy 연동 | `Post`, `User` 모델, `.env`의 `DATABASE_URL`로 SQLite/MySQL 전환 가능 | study4 |
| 회원 도메인 | `passlib`(pbkdf2_sha256) 비밀번호 해시, `/auth/register` | study5 |
| `BackgroundTasks` | 글 작성 시 알림 발송을 흉내내는 백그라운드 작업 | study6 |
| JWT 인증 | `/auth/login`(`OAuth2PasswordBearer` + `python-jose`), 작성자 소유권 검사(403) | study7 |
| CORS / 예외 핸들러 | `CORSMiddleware`, `{"detail": ...}` 공통 에러 포맷 | study8 |
| 테스트 | `pytest` + `TestClient`, 인메모리 DB로 격리된 9개 테스트 | study9 |
| 설정 관리 | `pydantic-settings`로 `SECRET_KEY`/`DATABASE_URL`/`CORS_ORIGINS` 등을 `.env`로 분리, `items/total/skip/limit` 페이지네이션 응답 | study10 |
| 도메인별 폴더링 | `posts`/`users` 도메인 분리, DB 접근(`repository`)과 비즈니스 로직(`service`) 분리 | study11 |

`project/app/` 내부 각 파일의 코드는 `demo/`의 study11 시점 코드와 거의 동일합니다 — 다른 점은 학습용으로만 존재했던 `practice/async_demo.py`, `/debug/boom` 라우트를 제외하고, `/`를 간단한 헬스 체크로 정리했다는 것입니다. 자세한 코드 설명은 각 study 문서를, 실행 방법은 [project/README.md](../project/README.md)를 참고하세요.

## 3. 실행 및 동작 확인

```bash
cd project
python -m venv .venv
.venv/Scripts/Activate.ps1
pip install -r requirements.txt
cp .env.example .env
uvicorn app.main:app --reload
```

### 전체 흐름 스모크 테스트

```bash
$ curl http://127.0.0.1:8000/
{"status":"ok","service":"Mini Board API"}

$ curl http://127.0.0.1:8000/posts
{"items":[{"title":"첫 번째 글","content":"Mini Board API에 오신 것을 환영합니다.","published":true,"id":1,"author_id":null},
          {"title":"비공개 초안","content":"아직 다듬는 중입니다.","published":false,"id":2,"author_id":null}],
 "total":2,"skip":0,"limit":10}

$ curl -X POST http://127.0.0.1:8000/auth/register \
    -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}'
{"id":1,"username":"alice"}

$ curl -X POST http://127.0.0.1:8000/auth/login \
    -H "Content-Type: application/x-www-form-urlencoded" -d "username=alice&password=secret123"
{"access_token":"eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...", "token_type":"bearer"}

$ curl -X POST http://127.0.0.1:8000/posts \
    -H "Content-Type: application/json" -H "Authorization: Bearer <위에서 받은 토큰>" \
    -d '{"title":"studyFinal post","content":"final project smoke test","published":true}'
{"title":"studyFinal post","content":"final project smoke test","published":true,"id":3,"author_id":1}

$ curl -o - -w "\n%{http_code}\n" -X POST http://127.0.0.1:8000/posts \
    -H "Content-Type: application/json" -d '{"title":"x","content":"y"}'
{"detail":"Not authenticated"}
401
```

헬스 체크, 시드 데이터 조회, 회원가입, 로그인, 인증된 글쓰기, 인증 없는 글쓰기 차단까지 처음부터 끝까지 정상 동작하는 것을 확인했습니다.

### 테스트 스위트

```bash
$ pytest -v
collected 9 items
tests/test_auth.py::test_register_duplicate_username PASSED
tests/test_auth.py::test_login_wrong_password PASSED
tests/test_auth.py::test_login_success PASSED
tests/test_posts.py::test_list_posts_empty PASSED
tests/test_posts.py::test_get_post_404 PASSED
tests/test_posts.py::test_create_post_requires_auth PASSED
tests/test_posts.py::test_create_and_get_post PASSED
tests/test_posts.py::test_update_post_forbidden_for_non_owner PASSED
tests/test_posts.py::test_owner_can_update_and_delete PASSED
======================== 9 passed, 2 warnings in 3.35s ========================
```

## 4. Notion 학습 목표 최종 점검

| 학습 목표 | 완료 여부 |
|---|---|
| 경로, Path/Query, Pydantic 스키마 | ✅ study2 |
| 의존성 주입 | ✅ study3, study7 |
| SQLAlchemy / SQLModel + MySQL | ✅ study4 (SQLAlchemy, `.env`로 MySQL 전환 가능) |
| 비동기 라우트 | ✅ study6 |
| JWT 인증 | ✅ study7 |
| CORS, 예외 핸들러 | ✅ study8 |
| 테스트코드로 API 테스트 | ✅ study9 |
| 공통 스펙(`/posts` CRUD + `/auth/login`) | ✅ `project/` |

## 5. 다음 단계로 이어갈 수 있는 것들

- 댓글(Comment) 모델을 추가해 게시글-댓글 1:N 관계와 nested response 다뤄보기
- Alembic으로 실제 마이그레이션 이력 관리 도입
- `DATABASE_URL`을 실제 MySQL 인스턴스로 바꿔 운영 환경에 가깝게 배포해보기
- Refresh Token, 로그아웃 시 토큰 무효화 같은 인증 흐름 보강
- React/Vue로 만든 실제 프론트엔드를 붙여 이 API를 소비하는 풀스택 앱 완성

여기까지 [Notion: FastAPI 학습 목표](https://app.notion.com/p/FastAPI-3d6d7dec5e2e810fb6f5fa9e53bcb9a2)에서 시작한 커리큘럼을 모두 마쳤습니다.
