# study14. API 설계

## ① 목표

게시판 API의 경로, 문서, 버전, 페이지, 오류를 한 규칙으로 설명한다.

## ② 📖 이론

### 왜 쓰는지

화면과 테스트와 Swagger가 서로 다른 이름을 쓰면 하나를 고칠 때마다 셋이 깨진다. 규칙을 먼저 적으면 구현이 그 규칙을 따르는지 테스트로 확인할 수 있다.

### 핵심 개념

- 자원은 복수 명사다. `/api/posts`, `/api/posts/{id}`, `/api/posts/{id}/comments`.
- 동작은 경로의 동사가 아니라 HTTP 메서드다. 수정은 PUT 대신 PATCH다.
- 목록 쿼리는 `page`(1부터), `limit`(기본 10, 상한 50), `q`, `sort`.
- 성공 목록은 `data`와 `meta`. `meta`에는 `page`, `limit`, `total`, `totalPages`, `q`.
- 오류는 `error.code`, `error.message`, 필요하면 `error.fields`, 항상 `error.requestId`.
- 문서 주소는 FastAPI 기본값인 `/docs`와 `/redoc`이다. 공통으로 부르기 쉬운 `/api-docs`는 `/docs`로 보낸다.
- 버전은 URL에 `/v1`을 넣지 않고 앱의 `version="1.0.0"`과 이 문서의 계약으로 표시한다. 계약을 깨는 변경을 할 때만 `/api/v2`를 새로 여는 식으로 나눈다.

### 비유

메뉴판이 OpenAPI다. 주방에서 나오는 접시 모양이 메뉴와 다르면 손님이 포크를 어디 대야 할지 모른다.

## ③ 🛠️ 실기

상태와 코드:

| 상태 | code | 언제 |
| --- | --- | --- |
| 200 | 없음 | 조회, 수정, 로그인 |
| 201 | 없음 | 가입, 글·댓글 생성. 글은 `Location` |
| 204 | 없음 | 삭제, 로그아웃. 본문 없음 |
| 400 | `VALIDATION_ERROR` | 필드 값이 규칙에 어긋남. `fields` 포함 |
| 400 | `BAD_REQUEST` | JSON이 깨짐, id가 숫자가 아님, 정렬 키가 틀림 |
| 401 | `UNAUTHORIZED` | 토큰 없음·위조·만료·폐기 |
| 401 | `INVALID_CREDENTIALS` | 로그인 실패. 어느 칸이 틀렸는지 숨김 |
| 403 | `FORBIDDEN` | 남의 글·댓글 |
| 404 | `NOT_FOUND` | 없는 자원, 없는 경로 |
| 409 | `EMAIL_TAKEN` | 중복 이메일 |
| 413 | `PAYLOAD_TOO_LARGE` | 업로드 한도 |
| 500 | `INTERNAL` | 처리하지 못한 예외. 스택은 로그에만 |

정렬 허용 값: `createdAt`, `-createdAt`, `-commentCount`. 앞의 `-`는 내림차순이다.

문서화는 스키마와 `tags`, `Query(description=...)`에서 자동으로 만들어진다. 따로 JSON 파일을 작성하지 않는다. 로그인만 예외다. Swagger의 Authorize 버튼은 폼을 보내고, 화면은 JSON을 보낸다. 라우터가 둘 다 받는다. `/docs`의 Try it out에서 로그인 본문 스키마가 폼과 달라 보이면, Authorize에는 이메일을 username 칸에 넣으면 된다.

버전을 코드에서 보는 곳:

```python
app = FastAPI(
    title="Mini Board API",
    description="FastAPI 학습용 게시판 API. 공통 스펙 v1의 /api, data+meta, error 형식을 따른다.",
    version="1.0.0",
)
```

`/api-docs`는 `RedirectResponse("/docs")`다.

페이지 계산은 서비스에 있다.

```python
offset = (page - 1) * limit
total_pages = (total + limit - 1) // limit if total else 0
```

0으로 나누지 않으려고 글이 없으면 `totalPages`는 0이다.

## ④ 🔗 연동 포인트

study12의 `api.js`와 study9의 assert가 이 표의 코드를 그대로 기대한다. 새 필드를 추가할 때는 응답에만 넣고 기존 키를 지우지 않으면 버전을 올리지 않아도 된다. 키 이름을 바꾸거나 상태 코드를 바꾸는 순간이 `/api` 계약을 깨는 때다. 그때는 옛 경로를 잠시 남기고 새 경로를 문서에 따로 적는다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| Swagger 로그인만 실패 | Authorize가 폼을 보냄 | username 칸에 이메일을 넣거나 JSON으로 호출 |
| `/api-docs`가 404 | 리다이렉트 라우트 누락 | `main.py`의 `/api-docs` 확인 |
| 페이지가 0부터 시작 | `page` 기본값을 0으로 둠 | 1부터. `ge=1` |
| 오류에 코드가 없고 detail만 있음 | 핸들러 이전의 기본 응답 | study4 핸들러가 등록됐는지 확인 |

## ⑥ 직접 해보기

1. `/docs`에서 글 목록의 쿼리 설명과 `/api-docs` 이동을 확인한다.
2. 정렬에 `title`을 넣어 400 `BAD_REQUEST`인지 본다.
3. 글이 없을 때 `totalPages`가 0인지, 글이 11개이고 limit가 10일 때 2인지 계산과 맞춘다.

## ⑦ ☐ 체크리스트

- [ ] 경로는 복수 명사와 HTTP 메서드로만 동작을 나타낸다.
- [ ] 목록 메타에 `page`, `limit`, `total`, `totalPages`, `q`가 있다.
- [ ] 오류 표의 401 두 가지와 403, 404, 409를 구분한다.
- [ ] `/docs`가 스키마에서 자동으로 만들어진다.
- [ ] 깨지지 않는 추가와 버전을 나눠야 하는 변경을 구분할 수 있다.

## ⑧ 다음 단계

계약이 고정되었으면 study15에서 같은 목록을 짧게 기억하고, 느린 일을 응답 뒤로 미루는 방법을 본다.
