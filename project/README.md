# Mini Board API (studyFinal 프로젝트)

`study0.md` ~ `study10.md`에서 배운 내용을 모두 적용해 만든 완결된 미니 게시판 API입니다. `demo/`에서 단계별로 실습했던 기능을, 처음부터 한 번에 갖춘 형태로 다시 설계했습니다.

## 기능 요약

| 영역 | 내용 | 대응 study |
|---|---|---|
| 프로젝트 구조 | `app/` 패키지(`routers/`, `schemas.py`, `models.py`, `database.py`, `dependencies.py`) | study1, study3 |
| CRUD | Path/Query 파라미터 + Pydantic 스키마 기반 `/posts` CRUD | study2 |
| 의존성 주입 | 페이지네이션 의존성, `APIRouter` 분리 | study3 |
| DB 연동 | SQLAlchemy(SQLite 개발용, `.env`로 MySQL 전환 가능) | study4 |
| 회원 도메인 | `User` 모델, `passlib` 비밀번호 해시, 회원가입 | study5 |
| 백그라운드 작업 | 글 작성 시 `BackgroundTasks`로 알림 발송 흉내 | study6 |
| JWT 인증 | `/auth/login`(OAuth2PasswordBearer), 작성자 소유권 검사(403) | study7 |
| CORS / 예외 처리 | `CORSMiddleware`, 전역 예외 핸들러로 에러 포맷 통일 | study8 |
| 테스트 | `pytest` + `TestClient`, 테스트 전용 인메모리 DB | study9 |
| 설정 관리 | `pydantic-settings` 기반 `.env` 분리, 페이지네이션 응답(`items/total/skip/limit`) | study10 |

## 실행 방법

```bash
# 1. 가상환경 생성 및 활성화
python -m venv .venv
.venv/Scripts/Activate.ps1     # Windows PowerShell

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 파일 준비
cp .env.example .env

# 4. 개발 서버 실행 (최초 실행 시 테이블 자동 생성 + 샘플 게시글 2개 시드)
uvicorn app.main:app --reload
```

- API 문서: `http://127.0.0.1:8000/docs` (Swagger UI), `http://127.0.0.1:8000/redoc`
- 테스트 실행: `pytest -v`

## 주요 경로

| 메서드 | 경로 | 설명 |
|---|---|---|
| GET | `/` | 헬스 체크 |
| GET | `/posts` | 게시글 목록 (`?published=`, `?skip=`, `?limit=`) |
| GET | `/posts/{id}` | 게시글 단건 조회 |
| POST | `/posts` | 게시글 작성 (로그인 필요) |
| PUT | `/posts/{id}` | 게시글 수정 (작성자 본인만) |
| DELETE | `/posts/{id}` | 게시글 삭제 (작성자 본인만) |
| POST | `/auth/register` | 회원가입 |
| POST | `/auth/login` | 로그인 (JWT 발급, `username`/`password` 폼 데이터) |

## 폴더 구조

```
project/
├── requirements.txt
├── .env.example
└── app/
    ├── main.py           # 앱 조립: 미들웨어, 예외 핸들러, 라우터 등록
    ├── config.py          # pydantic-settings 기반 환경설정
    ├── database.py        # SQLAlchemy Engine/Session
    ├── models.py          # Post, User 모델
    ├── schemas.py         # Pydantic 요청/응답 스키마
    ├── security.py        # 비밀번호 해시, JWT 발급
    ├── dependencies.py    # Pagination, get_current_user 등 의존성
    ├── exceptions.py      # 전역 예외 핸들러
    ├── store.py           # DB 접근 계층(CRUD 함수)
    └── routers/
        ├── posts.py
        └── auth.py
└── tests/                 # pytest (posts/auth 통합 테스트)
```

## 확장 아이디어 (다음 단계)

- 댓글(Comment) 모델 추가, 게시글-댓글 1:N 관계
- Alembic으로 스키마 마이그레이션 이력 관리
- `DATABASE_URL`을 실제 MySQL로 바꿔 배포 환경 구성
- Refresh Token, 로그아웃(토큰 블랙리스트) 등 인증 흐름 보강
- 실제 React/Vue 프론트엔드를 붙여 이 API를 소비하는 SPA 구현
