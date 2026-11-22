# study5. 폼, 입력, 검증

## ① 목표

사용자 입력을 검증하고, 실패 이유를 필드별로 보여 주며, 같은 제출이 두 번 저장되지 않게 한다.

## ② 📖 이론

### 왜 쓰는지

제목이 비었는데도 저장되면 목록이 쓰레기로 찬다. 화면이 "실패"만 말하면 사용자는 어느 칸을 고칠지 모른다. 저장 버튼이 느릴 때 두 번 누르면 같은 글이 두 개 생긴다.

### 핵심 개념

- 회원가입: `email`, `password`(8자 이상), `nickname`.
- 로그인: JSON `{ "email", "password" }`. Swagger의 Authorize는 폼의 `username`에 이메일을 넣어도 된다.
- 검증 실패는 **400** `VALIDATION_ERROR`와 `fields`. FastAPI가 원래 주는 422는 핸들러가 400으로 바꾼 상태다. 둘을 혼동하지 않기 위해, 고친 뒤의 계약은 400이라고 기억한다.
- 로그인 실패는 401 `INVALID_CREDENTIALS`. 이메일과 비밀번호 중 어느 쪽이 틀렸는지는 말하지 않는다.
- 중복 이메일은 409 `EMAIL_TAKEN`.
- `Idempotency-Key` 헤더가 같으면 첫 생성 결과를 다시 돌려주고 두 번째 줄은 만들지 않는다.

### 비유

양식의 빨간 칸이 `fields`다. 창구에서 "서류가 잘못됐다"만 말하면 전체를 다시 쓰게 된다. 접수 번호 스티커가 `Idempotency-Key`다. 같은 스티커로 다시 내면 새 접수증을 뽑지 않고 아까 것을 보여 준다.

## ③ 🛠️ 실기

회원 생성 스키마 `project/app/schemas/user.py`:

```python
class UserCreate(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nickname: str = Field(min_length=1, max_length=50)
```

줄별 설명:

1. 가입 본문의 클래스. `APIModel`이라 별칭 규칙을 물려받는다.
2. 이메일 형식. `@`가 없거나 도메인이 없으면 요청이 서비스까지 가지 않는다.
3. 비밀번호 길이. 8자 미만은 `fields.password`에 "비밀번호는 8자 이상이어야 합니다."
4. 닉네임 길이. 빈 문자열은 거절된다.

서비스는 형식을 통과한 뒤에 한 번 더 다듬는다. 이메일은 소문자로 저장하고, 닉네임의 앞뒤 공백을 지운 결과가 비면 400이다.

화면 `frontend/src/App.jsx`의 가입 폼은 전송 중에 `pending`을 켜서 버튼을 막는다. 그게 연타에 대한 1차 방지다. 서버의 2차 방지는 글 작성 헤더다.

```python
def create_post(..., idempotency_key: str | None = Header(default=None, alias="Idempotency-Key")):
    created = service.create_post(db, post, current_user, background_tasks, idempotency_key)
```

서비스는 키를 메모리 딕셔너리에 글 id와 함께 기억한다. 같은 키가 다시 오면 그 id의 글을 조회해 반환한다. 프로세스를 재시작하면 기억이 사라진다. 운영에서는 이 딕셔너리를 Redis 같은 저장소로 바꾸면 된다. 학습 앱은 프로세스 메모리로 동작을 보여 주는 데서 멈춘다.

상태 코드에 따라 화면이 하는 일:

| 코드 | 화면 |
| --- | --- |
| 200, 201 | 목록을 다시 읽고 입력칸을 비운다 |
| 400 | `error.message`와 `fields`를 에러 박스에 보여 주고 입력값은 유지한다 |
| 401 | 로그인 폼으로 되돌린다 |
| 422 | 이 프로젝트의 계약에서는 나오지 않는다. 나온다면 핸들러가 빠진 것 |

`frontend/src/api.js`는 `data.error.message`와 `data.error.fields`를 한 문장으로 합쳐 `throw new Error` 한다. 컴포넌트는 그 문장을 `error` state에 넣는다.

## ④ 🔗 연동 포인트

검증을 통과한 `PostCreate`만 study6 저장소의 `INSERT`로 간다. 실패 응답의 `requestId`는 study4 미들웨어가 만든 값이라, 사용자가 에러 문장을 알려 주면 서버 로그에서 같은 시각의 요청을 찾을 수 있다. 프론트 포트 3000에서 백엔드로 이 JSON을 보내려면 study7의 CORS가 그 출처를 허용해야 한다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 짧은 비밀번호가 201 | `UserCreate`가 아니라 평범한 dict로 받음 | 본문 타입을 `UserCreate`로 선언 |
| 422가 그대로 보임 | 검증 핸들러 미등록 | `RequestValidationError` 핸들러가 400을 주는지 확인 |
| 같은 키로 글이 두 개 | 헤더 이름이 다름 | `Idempotency-Key` 철자와 대시를 확인 |
| 이메일이 같은데 409가 아님 | 대소문자만 다름 | 저장 전에 `lower()` 했는지 확인 |
| 버튼을 두 번 눌렀더니 가입이 두 번 | 이메일이 달라서 409가 아님 | 화면의 `pending`으로 버튼을 막는지 확인 |

## ⑥ 직접 해보기

1. 비밀번호 7자로 가입해 400과 `fields.password`를 확인한다.
2. 같은 이메일로 다시 가입해 409 `EMAIL_TAKEN`을 확인한다.
3. 글 작성에 같은 `Idempotency-Key`를 두 번 보내고, 두 응답의 `id`가 같은지 본다.

## ⑦ ☐ 체크리스트

- [ ] 이메일 형식, 비밀번호 길이, 빈 제목을 서버가 거절한다.
- [ ] 실패 본문에 `fields`가 있고 화면이 그 문장을 보여 준다.
- [ ] 성공은 200 또는 201, 검증 실패는 400이다.
- [ ] 같은 `Idempotency-Key`는 글을 새로 만들지 않는다.
- [ ] 제출 중에는 버튼이 비활성화된다.

## ⑧ 다음 단계

입력이 깨끗해졌으면 study6에서 그 값을 SQLite에 저장하고 목록·상세·수정·삭제를 SQL로 끝낸다.
