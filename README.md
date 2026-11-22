# FastAPI 학습 저장소

FastAPI만으로 게시판 API를 기초부터 심화까지 만든 기록이다. 개념은 `study*.md`에 있고, 실행은 `demo/`와 `project/`에 있다.

- 기초·중간 점검: `demo/` (포트 8001)
- 심화·최종: `project/` (포트 8000)
- 공통 계약: `/api`, 목록 `data`+`meta`, 오류 `error.code` / `message` / `fields` / `requestId`, JSON 필드 camelCase, Bearer 토큰
- 노트: [Notion FastAPI](https://app.notion.com/p/3d6d7dec5e2e810fb6f5fa9e53bcb9a2)

## 문서

| 문서 | 내용 |
| --- | --- |
| [study0.md](study0.md) | 설치, 버전, 폴더, Git, `.env` |
| [study1.md](study1.md) | 첫 JSON, `/health`, 자동 새로고침 |
| [study2.md](study2.md) | 라우터·서비스·저장소, 의존성 주입 |
| [study3.md](study3.md) | Pydantic, camelCase |
| [study4.md](study4.md) | `/api`, Path/Query, 오류 형식 |
| [study5.md](study5.md) | 입력 검증, 400, 중복 제출 |
| [study6.md](study6.md) | SQLite CRUD, MySQL URL, `data`+`meta` |
| [study7.md](study7.md) | 비밀번호 해시, JWT, 403 |
| [study8.md](study8.md) | 설정 분리, CORS, 예외 핸들러 |
| [study9.md](study9.md) | pytest, 테스트 DB 교체 |
| [study10.md](study10.md) | 실행과 배포 후 점검 |
| [studyMidpoint.md](studyMidpoint.md) | 기초만으로 게시판 |
| [study11.md](study11.md) | MariaDB, PostgreSQL, MongoDB, SQLModel |
| [study12.md](study12.md) | React 화면 |
| [study13.md](study13.md) | 업로드, 메일 로그, 결제 초안, OAuth URL |
| [study14.md](study14.md) | REST, Swagger, 페이지, 오류 표 |
| [study15.md](study15.md) | 캐시, 백그라운드, 비동기 라우트 |
| [study16.md](study16.md) | Docker, GitHub Actions, 백업 |
| [study17.md](study17.md) | 웹소켓 |
| [study18.md](study18.md) | 문서 답변, 스트리밍, MCP |
| [studyFinal.md](studyFinal.md) | `project/` 완성본 |

## 실행

```powershell
cd demo
python -m venv .venv
.venv\Scripts\Activate.ps1
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8001
pytest -q
```

`project`도 같은 순서이고 포트는 8000이다. 문서는 `http://127.0.0.1:8000/docs` (demo는 8001).

화면:

```powershell
cd project\frontend
npm install
copy .env.example .env
npm run dev
```

demo 화면은 `demo\frontend`이고 API 주소는 `http://127.0.0.1:8001`이다.

## 주요 경로

| 메서드 | 경로 | 인증 |
| --- | --- | --- |
| GET | `/health` | 없음 |
| POST | `/api/auth/signup` | 없음 |
| POST | `/api/auth/login` | 없음 |
| POST | `/api/auth/logout` | 필요 |
| GET | `/api/auth/me` | 필요 |
| GET | `/api/posts` | 없음 |
| POST | `/api/posts` | 필요 |
| PATCH | `/api/posts/{id}` | 작성자 |
| DELETE | `/api/posts/{id}` | 작성자 |
| GET | `/api/posts/{id}/comments` | 없음 |
| POST | `/api/posts/{id}/comments` | 필요 |
| DELETE | `/api/comments/{id}` | 작성자 |

`project`에는 `/api/uploads`, `/api/mail/send`, `/api/payments/draft`, `/api/oauth/google`, `/api/ai/documents`, `/api/ai/ask`, `/ws/posts`가 더 있다. `demo`에는 `/hello`, `/debug/boom`, `/async-demo/*`가 더 있다.

기본 DB는 SQLite다. MySQL·PostgreSQL은 `DATABASE_URL`로 바꾸고, 실서버 접속은 환경이 있을 때 study11을 따라 확인한다.
