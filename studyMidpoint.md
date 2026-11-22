# studyMidpoint. 기초만으로 만드는 미니 게시판

## ① 목표

study0부터 study10까지로 `demo/`에 로그인과 게시글 CRUD가 되는 작은 서비스를 만든다.

## ② 📖 이론

### 왜 이 중간 지점이 있는지

심화(DB 교체, 결제, 웹소켓, AI)를 넣기 전에, 기초 기술만으로 한 바퀴가 도는지 확인한다. 여기서 안 되는 기능은 study11 이후에 더한다. 이 문서의 코드는 `demo/`다.

### 핵심 개념

범위 안에 있는 것: 환경 변수, JSON 응답, 라우터와 의존성, 스키마, `/api`, 검증, SQLite, JWT, CORS, pytest.

범위 밖에 두는 것: PostgreSQL 실서버, 파일 업로드, 결제, 웹소켓, 문서 질의. 그것들은 `project/`와 study11~18이다.

### 비유

중간 점검은 간판을 달기 전에 주문이 주방으로 들어가는지 보는 영업 전 리허설이다.

## ③ 🛠️ 실기

### 기능 목록

- `GET /health`
- 회원가입, 로그인, 내 정보, 로그아웃
- 게시글 목록·상세·작성·부분 수정·삭제
- 댓글 목록·작성·삭제
- 검색 `q`, 페이지 `page`/`limit`
- 작성자만 수정·삭제
- Swagger `/docs`
- React 화면: 가입, 로그인, 검색, 작성, 삭제, 댓글

### 폴더

```text
demo/
├── app/
│   ├── main.py
│   ├── config.py
│   ├── database.py
│   ├── security.py
│   ├── exceptions.py
│   ├── middleware.py
│   ├── dependencies.py
│   ├── models/
│   ├── schemas/
│   ├── repositories/
│   ├── services/
│   └── routers/
│       ├── auth.py
│       ├── post.py
│       ├── comment.py
│       └── async_demo.py
├── tests/
├── frontend/
├── requirements.txt
└── .env.example
```

`async_demo.py`는 비동기 비교용 보조 경로다. 게시판 기능에는 필요 없고, study15에서 다시 본다.

### 구현 순서

1. study0: `demo` 가상환경, `.env`, `uvicorn --reload --port 8001`.
2. study1: `/health`와 `/hello`.
3. study2: `APIRouter`와 `Depends(get_db)`.
4. study3: `PostCreate`, `UserCreate`, `APIModel`의 camelCase.
5. study4: `APIRouter(prefix="/api")`, 오류 핸들러.
6. study5: 검증 400, `Idempotency-Key`, 화면의 제출 중 버튼.
7. study6: 모델과 저장소, 목록 `data`+`meta`, SQL `offset/limit`.
8. study7: 해시, 로그인, Bearer, 403.
9. study8: CORS와 설정을 `main.py`와 `.env`로 모은다.
10. study9: `pytest -q`가 통과하는지 확인한다.
11. 화면: `frontend`에서 `npm install`, `.env`에 `VITE_API_BASE_URL=http://127.0.0.1:8001`, `npm run dev`.

### DB와 API

```text
브라우저 :3000
    │  JSON, Authorization: Bearer
    ▼
demo FastAPI :8001
    │  SQLAlchemy
    ▼
sqlite 파일 demo/demo.db
```

인증이 필요 없는 읽기: 건강 체크, 글 목록, 글 상세, 댓글 목록.  
인증이 필요한 쓰기: 글·댓글 작성과 삭제, 내 정보, 로그아웃.

### 1차 배포 체크리스트

- [ ] `demo`에서 `pytest -q`가 통과한다.
- [ ] `/health`가 ok다.
- [ ] 가입한 사용자만 글을 쓰고, 그 사용자만 지운다.
- [ ] 목록 메타에 `page`, `limit`, `total`, `totalPages`가 있다.
- [ ] `.env`가 커밋에 없다.
- [ ] 프론트 주소가 CORS 목록에 있다.
- [ ] 서버 로그에 비밀번호가 없다.

## ④ 🔗 연동 포인트

이 게시판의 경로와 오류 형식은 이후 화면과 배포가 기대하는 계약이다. study11에서 DB URL을 바꿔도 라우터는 그대로다. study12는 이 `demo/frontend`를 그 계약에 맞춰 읽는다. `project/`는 이 구조에 업로드, 메일 로그, 결제 초안, AI, 웹소켓을 더한 완성본이다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 화면이 8000을 봄 | demo 프론트 기본값이 project 포트 | `VITE_API_BASE_URL`을 8001로 |
| 테스트는 되는데 화면 목록이 비지 않음 | 서버의 `demo.db`에 시드가 있음 | 정상이다. 테스트 DB와 파일이 다르다 |
| 글 작성이 CORS로 실패 | 3000이 허용 목록에 없음 | `.env`의 `CORS_ORIGINS` 확인 후 재시작 |

## ⑥ 직접 해보기

1. 빈 계정으로 가입하고 글 하나와 댓글 하나를 화면에서 남긴다.
2. 다른 브라우저(또는 시크릿 창)로 그 글을 지우려 해 실패하는지 본다.
3. `pytest -q`를 실행해 방금 남긴 파일 DB와 테스트가 분리되어 있는지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 기능 목록의 읽기와 쓰기를 한 번씩 호출했다.
- [ ] 폴더가 라우터/서비스/저장소로 나뉘어 있다.
- [ ] SQLite 파일과 `.env`로 접속한다.
- [ ] 1차 배포 체크리스트를 통과했다.
- [ ] 심화 기능을 넣지 않고도 게시판이 동작한다.

## ⑧ 다음 단계

같은 게시판을 유지한 채 DB 종류를 바꾸는 방법은 study11에서 다룬다.
