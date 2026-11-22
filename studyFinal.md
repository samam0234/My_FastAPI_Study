# studyFinal. 심화까지 포함한 게시판

## ① 목표

study11부터 study18, 그리고 midpoint의 게시판을 `project/` 하나의 FastAPI 서비스로 맞춘다.

## ② 📖 이론

### 왜 따로 모으나

midpoint의 `demo/`는 기초 기능만으로 동작해야 한다. 심화 코드를 거기에 넣으면 업로드나 웹소켓이 없을 때도 파일이 필요하다. `project/`는 같은 CRUD 위에 DB 교체 방법, 외부 호출, AI, 컨테이너를 더한 완성본이다.

### 핵심 개념

완성본이 지키는 계약은 바뀌지 않는다. `/api`, `data`+`meta`, `error.code`, camelCase, Bearer 토큰. 더한 것은 경로와 실행 방법이다.

### 비유

demo는 주방만 있는 가게고 project는 벨과 서류 질문 창구와 포장 상자까지 갖춘 가게다. 주문 양식은 같다.

## ③ 🛠️ 실기

### 기능 목록

midpoint의 기능에 더해 다음이 있다.

- 업로드, 메일 로그, 결제 초안, 구글 인가 URL
- 문서 인덱싱, 발췌 답변, SSE 스트림
- `/ws/posts` 새 글 id 알림
- 목록 캐시(`CACHE_TTL_MS`)
- Dockerfile, compose, GitHub Actions, SQLite 백업 스크립트
- SQLModel·MongoDB·PostgreSQL URL 예시

### 연동 구성

```text
React :3000
   │  /api  JSON, Bearer
   ▼
project FastAPI :8000
   ├─ SQLAlchemy ── SQLite 파일 (기본)
   │                 또는 DATABASE_URL의 MySQL / PostgreSQL
   ├─ uploads/      파일
   ├─ 메모리        메일 outbox, AI 청크, 웹소켓 허브, 목록 캐시
   └─ 선택         OpenAI (키), Ollama 이름, Google 인가 URL
```

MongoDB 예시는 이 상자 밖에 있다. 앱이 그 드라이버를 import하지 않는다.

### 구현 순서

1. midpoint까지 동작하는 `demo`를 기준으로 삼는다.
2. 같은 모델과 라우터를 `project`에 두고 포트만 8000으로 연다.
3. study11: `.env.example`에 MariaDB·PostgreSQL URL을 적고 `build_engine`이 SQLite만 특별 취급하는지 확인한다. 실서버 접속은 체크하지 않는다.
4. study12: `project/frontend`가 `accessToken`, `data`, `meta`를 읽게 한다.
5. study13: `routers/integrations.py`를 `/api`에 포함한다.
6. study14: `/docs`와 `/api-docs`, 오류 표, 페이지 메타를 테스트로 고정한다.
7. study15: 캐시 TTL 0 기본값, 백그라운드 알림, `demo`의 async 비교 경로를 유지한다.
8. study16: Dockerfile의 `0.0.0.0`, Actions의 두 폴더 테스트, 백업 스크립트.
9. study17: 생성 뒤 `post.created`와 id만 방송한다. demo에는 이 모듈이 없다.
10. study18: mock 문서 답변, 스트림, `examples/mcp/server.py`. DocuForge의 404/503과 SocialForge의 제공자 선택을 이 FastAPI 경로에만 대응시킨다.
11. `project`에서 `pytest -q`를 실행한다.

### 배포 체크리스트

- [ ] `pytest -q`가 project에서 통과한다.
- [ ] `/health`와 `/api/posts`가 기대한 모양이다.
- [ ] 토큰 없이 글 작성과 업로드는 401이다.
- [ ] 남의 글 수정은 403, 없는 글은 404다.
- [ ] 검증 실패는 400이고 `fields`가 있다.
- [ ] `SECRET_KEY`와 API 키가 저장소에 없다.
- [ ] CORS 출처가 프론트 주소와 같다.
- [ ] 컨테이너를 쓰면 바인드가 `0.0.0.0`이다.
- [ ] SQLite를 쓰면 백업 복사본을 만들 수 있다.
- [ ] AI 키가 없어도 `/api/ai/ask`가 mock으로 답한다.
- [ ] PostgreSQL 실서버 접속은 아직 완료로 표시하지 않는다.

### 최종 회고

기초만으로도 회원과 게시글이 돌아갔고, 심화는 그 계약 위에 경로를 더하는 방식이었다. 목록을 파이썬에서 자르지 않고 SQL로 옮긴 점, 오류를 `detail`이 아닌 `error`로 모은 점, 비밀번호를 응답 스키마에서 뺀 점이 화면을 붙일 때 가장 많이 줄인 분기였다. 메모리에 둔 캐시, 폐기 토큰, AI 인덱스, 웹소켓 목록은 프로세스가 하나일 때의 학습용 한계다. 프로세스를 늘리기 전에 그 넷을 공유 저장소로 바꾸는 일이 다음 작업이다.

## ④ 🔗 연동 포인트

`demo`와 `project`의 게시글 JSON은 같다. 화면은 포트만 다르다. Actions는 둘 다 테스트해서 기초 앱이 심화 수정 때문에 깨지지 않았는지 본다. PostgreSQL로 옮길 때는 라우터를 건드리지 않고 `DATABASE_URL`과 드라이버만 바꾼다. AI와 업로드는 글 테이블에 자동으로 쓰이지 않으므로, 화면이 순서를 정해야 한다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| project 테스트가 demo 경로를 찾지 못함 | pytest를 저장소 루트에서 실행 | `cd project` 후 `pytest -q` |
| 웹소켓이 demo에 없음 | 의도된 분리 | 알림은 project에서 확인 |
| AI 문서가 재시작 후 사라짐 | 인덱스가 메모리 | 다시 `POST /api/ai/documents` |
| 배포 환경이 개발 SQLite를 봄 | 환경 변수 누락 | `DATABASE_URL`을 프로세스에 넣는다 |

## ⑥ 직접 해보기

1. project에서 가입, 글, 댓글, 업로드, 문서 질문을 순서대로 호출한다.
2. `pytest -q` 결과를 배포 체크리스트 첫 칸에 적는다.
3. 회고의 "메모리에 둔 네 가지"가 코드에서 어느 변수인지 찾아 이름을 적는다.

## ⑦ ☐ 체크리스트

- [ ] demo는 기초 게시판, project는 심화 포함이라는 구분이 맞다.
- [ ] 공통 계약(`/api`, `data`+`meta`, `error`, camelCase, Bearer)이 테스트로 고정되어 있다.
- [ ] 외부 호출은 키가 없으면 네트워크를 타지 않는다.
- [ ] Docker·Actions·백업 파일의 위치를 말할 수 있다.
- [ ] PostgreSQL 실연결은 완료로 체크하지 않았다.
- [ ] 최종 회고의 다음 작업(공유 저장소)을 이해했다.

## ⑧ 다음 단계

이 게시판의 다음 실제 작업은 메모리에 둔 캐시·폐기 토큰·문서 인덱스·웹소켓 목록을 프로세스 밖으로 옮기고, PostgreSQL에 연결해 본 뒤에만 study11의 남은 체크를 채우는 것이다.
