# study13. 외부 서비스 연동

## ① 목표

파일 업로드, 메일, 결제, 소셜 로그인처럼 우리 서버 밖에 있는 일을, 비밀키 없이도 호출 형태만 안전하게 붙여 본다.

## ② 📖 이론

### 왜 쓰는지

게시판 데이터는 우리 DB에 있지만, 파일 보관·메일·결제·구글 로그인은 다른 서비스의 자격 증명이 필요하다. 키가 없을 때 네트워크를 치면 테스트가 그 회사의 장애에 같이 죽는다. 그래서 키가 없으면 로그나 가짜 주소만 만들고, 키가 있으면 그 자리만 진짜 호출로 바꾼다.

### 핵심 개념

- 업로드: 확장자를 허용 목록으로 제한하고, 저장 이름은 UUID로 만든다. 사용자가 준 경로를 그대로 쓰지 않는다.
- 메일: `SMTP_HOST`가 비어 있으면 `mode: "log"`로 메모리에만 남긴다.
- 결제: 금액과 주문명으로 가짜 `checkoutUrl`을 만든다. 카드 번호는 우리 서버가 받지 않는다.
- OAuth: `GOOGLE_CLIENT_ID`가 없으면 400. 있으면 구글 인가 URL만 만들어 돌려준다. 인가 코드를 토큰으로 바꾸는 교환은 그 다음 단계다.

### 비유

외부 서비스는 옆 가게다. 간판 주소(URL)와 우리 명의 열쇠(키)가 있을 때만 문을 연다. 열쇠가 없으면 주문서 사본을 서랍에 넣어 두고 손님이 흐름을 연습하게 한다.

## ③ 🛠️ 실기

라우터는 `project/app/routers/integrations.py`이고 앱에서는 `/api` 아래에 붙는다.

업로드의 핵심:

```python
suffix = Path(file.filename or "").suffix.lower()
if suffix not in _ALLOWED:
    raise AppError(400, "BAD_REQUEST", "허용되지 않은 파일 형식입니다.")
content = await file.read()
if len(content) > settings.max_upload_bytes:
    raise AppError(413, "PAYLOAD_TOO_LARGE", "업로드 한도를 넘었습니다.")
stored = f"{uuid.uuid4().hex}{suffix}"
(folder / stored).write_bytes(content)
```

줄별 설명:

1. 원본 이름에서 확장자만 떼고 소문자로 만든다. 디렉터리 부분은 버린다.
2. `.txt`, `.md`, `.pdf`, `.png`, `.jpg`, `.jpeg`만 허용한다.
3. 그 외는 400이다. 실행 파일을 저장하지 않는다.
4. 본문을 메모리에 읽는다. 한도보다 큰 파일을 디스크에 쓰기 전에 거절한다.
5. `MAX_UPLOAD_BYTES` 기본값은 1_000_000이다.
6. 413 `PAYLOAD_TOO_LARGE`.
7. 저장 이름은 우리가 만든 UUID다. `../../` 같은 이름이 경로가 되지 않는다.
8. `UPLOAD_DIR` 아래에 바이트를 쓴다.

메일 전송은 `SMTP_HOST`가 있을 때 `mode`만 `smtp`로 표시하고, 이 학습 코드는 실제로 소켓을 열지 않는다. 운영에서 붙일 때는 이 분기에 `smtplib`을 넣고, 비밀번호는 `SMTP_PASSWORD` 환경 변수로만 읽는다.

결제 초안은 `amount`가 100 이상 10_000_000 이하여야 한다. 응답의 `checkoutUrl`은 `https://pay.example.test/...`라서 결제가 나가지 않는다.

구글 시작 URL:

```python
query = urlencode({
    "client_id": settings.google_client_id,
    "redirect_uri": settings.google_redirect_uri,
    "response_type": "code",
    "scope": "openid email profile",
})
```

`redirect_uri`는 구글 콘솔에 등록한 값과 글자 단위로 같아야 한다. 기본값은 `http://localhost:3000/oauth/callback`이다.

호출은 모두 로그인 토큰이 필요하다. OAuth 주소 조회만 공개다. 키가 없는 공개 조회는 400 `GOOGLE_CLIENT_ID가 없습니다.`

## ④ 🔗 연동 포인트

업로드한 파일 이름과 크기는 글 본문에 자동으로 붙지 않는다. 글을 쓰는 API와 파일을 올리는 API를 화면에서 순서대로 호출해야 연결된다. 메일 로그는 study15의 백그라운드 알림이 나중에 호출할 자리다. 결제 URL은 브라우저를 그 주소로 보내는 용도이고, 우리 DB의 주문 행은 이 예제에 없다. OAuth는 study7의 비밀번호 로그인 옆에 놓는 두 번째 입구다. 인가 코드를 받은 뒤의 사용자 생성은 기존 `register_user`와 같은 사용자 테이블을 쓰면 된다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 413 | 파일이 한도를 넘음 | 파일을 줄이거나 `MAX_UPLOAD_BYTES`를 환경 변수로 올린다 |
| 400 허용되지 않은 형식 | 확장자가 목록 밖 | txt, md, pdf, png, jpg만 |
| 메일이 실제로 안 감 | `SMTP_HOST`가 비어 있어 로그 모드 | 학습 중에는 outbox로 확인한다 |
| OAuth 400 | 클라이언트 id가 없음 | `.env`에 `GOOGLE_CLIENT_ID`를 넣기 전에는 400이 정상이다 |

## ⑥ 직접 해보기

1. 로그인한 토큰으로 `note.txt`를 `/api/uploads`에 보내고 `filename`이 원본 이름이 아닌지 본다.
2. `/api/mail/send` 뒤에 `/api/mail/outbox`에 제목이 남는지 확인한다.
3. 클라이언트 id 없이 `/api/oauth/google`이 400인지 확인한다.

## ⑦ ☐ 체크리스트

- [ ] 저장 파일 이름에 사용자 경로가 들어가지 않는다.
- [ ] 크기 초과는 413 `PAYLOAD_TOO_LARGE`다.
- [ ] 메일과 결제는 키가 없어도 테스트가 네트워크를 타지 않는다.
- [ ] OAuth는 인가 URL만 만들고 비밀을 응답에 넣지 않는다.
- [ ] 업로드·메일·결제 초안은 로그인 토큰이 필요하다.

## ⑧ 다음 단계

외부 호출의 입구가 생겼으면 study14에서 경로, 문서, 페이지, 오류 규칙을 한 계약으로 다시 읽어 본다.
