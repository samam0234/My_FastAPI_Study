# FastAPI 학습 저장소

Python [FastAPI](https://fastapi.tiangolo.com/)를 기초 이론부터 인증·테스트·구조 설계까지 단계별로 공부한 기록입니다.
`study*.md` 문서로 개념을 정리하고, 같은 내용을 `demo/`(단계별 누적 실습)와 `project/`(최종 완성본)에 코드로 옮겼습니다.

- 공통 목표: **`/posts` CRUD + `/auth/login`** 을 인메모리 → SQLAlchemy(DB) → JWT 인증 순으로 발전시키기
- 학습 목표와 전체 로드맵: [Notion: FastAPI 학습 목표](https://app.notion.com/p/FastAPI-3d6d7dec5e2e810fb6f5fa9e53bcb9a2)

## 학습 로드맵

| 문서 | 주제 | 코드 반영 |
|---|---|---|
| [study0.md](study0.md) | FastAPI 기초이론 (ASGI, Pydantic, 동기/비동기, 자동 문서화) | 실습 없음 |
| [study1.md](study1.md) | 개발 환경 준비, 가상환경, 첫 라우트 띄우기 | `demo/` 최초 생성 |
| [study2.md](study2.md) | Path/Query 파라미터, Pydantic 스키마로 `/posts` CRUD | `demo/app/routers/post.py`, `schemas/post.py` |
| [study3.md](study3.md) | 의존성 주입(`Depends`), `APIRouter` 분리, 프로젝트 구조화 | `dependencies.py`, 라우터 분리 |
| [study4.md](study4.md) | SQLAlchemy 연동, SQLite → MySQL 전환 | `database.py`, `models/post.py` |
| [study5.md](study5.md) | `User` 모델, 비밀번호 해시, `/auth/register` | `models/user.py`, `security.py` |
| [study6.md](study6.md) | 비동기 라우트(`async`/`def`) 비교, `BackgroundTasks` | `routers/async_demo.py` |
| [study7.md](study7.md) | JWT 발급/검증, `/auth/login`, 작성자 소유권 검사(403) | `services/user.py`, `get_current_user` |
| [study8.md](study8.md) | CORS 미들웨어, 전역 예외 핸들러로 에러 포맷 통일 | `exceptions.py`, `main.py` |
| [study9.md](study9.md) | pytest + TestClient, 테스트 전용 DB 분리 | `tests/` |
| [study10.md](study10.md) | `pydantic-settings`로 `.env` 설정 분리, 페이지네이션 응답 | `config.py` |
| [study11.md](study11.md) | 레이어별 폴더 구조(models/repositories/schemas/services/routers) | 전체 구조 |
| [studyFinal.md](studyFinal.md) | 지금까지 배운 것을 합친 미니 게시판 API 최종 프로젝트 | `project/` |

## 저장소 구조

```
FastApi/
├── study0.md ~ study11.md, studyFinal.md   # 학습 기록 (번호가 클수록 최신 진도)
├── demo/                                   # study1~10 실습을 누적한 프로젝트
│   ├── app/                                # FastAPI 백엔드
│   ├── tests/                              # pytest 테스트
│   ├── frontend/                           # React + Vite 최소 프론트엔드
│   ├── requirements.txt
│   └── .env.example
├── project/                                # studyFinal: 완결된 미니 게시판 API
│   ├── README.md                           # 프로젝트 전용 상세 설명
│   ├── app/ · tests/ · frontend/ · requirements.txt · .env.example
└── .agent/ · .claude/ · .codex/ · .grok/   # 에이전트별 인수인계 문서
```

### demo vs project

| 구분 | `demo/` | `project/` |
|---|---|---|
| 목적 | study1~10 실습을 순서대로 쌓아 가는 학습용 프로젝트 | 배운 내용을 처음부터 한 번에 갖춘 완성본 |
| 제목 / 버전 | `FastAPI Demo` | `Mini Board API` 1.0.0 |
| 루트 경로 | `/`, `/hello`, `/debug/boom` (예외 핸들러 실습) | `/` 헬스 체크 (`status: ok`) |
| 추가 실습 | `routers/async_demo.py` (async/blocking 비교) | 없음 |
| 백엔드 포트 | 8001 (프론트엔드 `.env.example` 기준) | 8000 |

두 프로젝트의 `app/`은 대부분 같고, `main.py`와 `async_demo.py`만 다릅니다.

## 실행 방법

FastAPI 프로젝트(`demo/`, `project/`)는 각자 독립된 가상환경(`.venv`)과 `requirements.txt`를 가집니다. 아래는 `demo/` 기준이며, `project/`도 같은 순서로 실행합니다.

```powershell
cd demo

# 1. 가상환경 생성 및 활성화 (Windows PowerShell)
python -m venv .venv
.venv\Scripts\Activate.ps1

# 2. 패키지 설치
pip install -r requirements.txt

# 3. 환경변수 파일 준비 (.env는 커밋되지 않는다)
copy .env.example .env

# 4. 개발 서버 실행 (최초 실행 시 테이블 자동 생성 + 샘플 글 시드)
uvicorn app.main:app --reload --port 8001
```

- API 문서: `http://127.0.0.1:8001/docs` (Swagger UI), `http://127.0.0.1:8001/redoc` (ReDoc)
- 테스트: `pytest -v` (테스트마다 인메모리 SQLite를 새로 만들어 실제 DB 파일은 건드리지 않습니다)

### 프론트엔드 (React + Vite)

백엔드를 띄운 상태에서 별도 터미널에서 실행합니다.

```powershell
cd demo\frontend        # 또는 project\frontend
npm install
copy .env.example .env  # VITE_API_BASE_URL로 백엔드 주소를 지정
npm run dev             # http://localhost:3000 (CORS 허용 포트와 일치)
```

## 주요 API

| 메서드 | 경로 | 설명 | 인증 |
|---|---|---|---|
| GET | `/posts` | 게시글 목록 (`?published=`, `?skip=`, `?limit=`) | 불필요 |
| GET | `/posts/{id}` | 게시글 단건 조회 (없으면 404) | 불필요 |
| POST | `/posts` | 게시글 작성 (작성 후 백그라운드 알림) | 필요 (Bearer) |
| PUT | `/posts/{id}` | 게시글 수정 | 필요 + 작성자 본인 (아니면 403) |
| DELETE | `/posts/{id}` | 게시글 삭제 | 필요 + 작성자 본인 (아니면 403) |
| POST | `/auth/register` | 회원가입 (중복 username이면 400) | 불필요 |
| POST | `/auth/login` | 로그인, JWT 발급 (`username`/`password` 폼 데이터) | 불필요 |

`demo/`에는 추가로 `/async-demo/bad-async`, `/async-demo/good-async`, `/async-demo/sync-def`가 있습니다.

## 설정 (.env)

`.env.example`을 복사해 값을 채웁니다. 주요 항목은 다음과 같습니다.

| 변수 | 기본값 | 설명 |
|---|---|---|
| `DATABASE_URL` | `sqlite:///./demo.db` | DB 연결 문자열 (MySQL 전환 시 `mysql+pymysql://...`) |
| `SECRET_KEY` | 학습용 기본값 | JWT 서명 키. **운영에서는 반드시 긴 임의 값으로 바꿀 것** |
| `ALGORITHM` | `HS256` | JWT 서명 알고리즘 |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `30` | 토큰 유효 시간(분) |
| `CORS_ORIGINS` | `["http://localhost:3000", ...]` | 허용할 프론트엔드 주소 (JSON 배열 문자열) |

## 공부 방법과 커밋 규칙

- 새 작업을 시작하기 전에 `study*.md`를 번호 순서대로 읽고 진도를 파악합니다.
- 커밋은 학습 진도 파트 단위로 나누고, 메시지는 `type: 한글 설명` 형식을 따릅니다. 자세한 규칙은 [.agent/COMMIT_GUIDE.md](.agent/COMMIT_GUIDE.md)를 참고하세요.
- 에이전트 공통 규칙은 [.agent/AGENTS.md](.agent/AGENTS.md)에 있습니다.
