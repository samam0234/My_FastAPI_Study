# study7. 인증과 보안 기초

## ① 목표

회원가입과 로그인으로 JWT를 발급하고, 토큰으로 사용자를 확인하며, 비밀번호와 브라우저 출처를 함부로 다루지 않는다.

## ② 📖 이론

### 왜 쓰는지

누구의 글인지 알려면 요청마다 신원을 실어야 한다. 세션은 서버가 표를 기억한다. JWT는 서명한 문자열이라 서버 표 없이도 검증할 수 있다. 대신 로그아웃은 "그 문자열을 잊어라"고 서버에 말해야 하므로, 이 앱은 토큰 id(`jti`)를 메모리 폐기 목록에 넣는다.

### 핵심 개념

- 비밀번호는 `passlib`의 `pbkdf2_sha256`으로만 저장한다. 원문은 저장하지 않고, 응답 스키마에도 넣지 않는다.
- `POST /api/auth/signup` 201, `POST /api/auth/login` 200, `GET /api/auth/me` 200, `POST /api/auth/logout` 204.
- 로그인 성공 본문:

```json
{ "data": { "user": { "id": 3, "email": "mina@example.com", "nickname": "mina" }, "accessToken": "eyJ..." } }
```

- 다음 요청은 `Authorization: Bearer <accessToken>`.
- `get_current_user`가 서명을 확인하고, DB에 그 이메일이 아직 있는지도 다시 본다.
- 글 수정·삭제는 먼저 404, 그 다음 작성자가 아니면 403 `FORBIDDEN`.
- **CORS**: 브라우저는 `localhost:3000`에서 `127.0.0.1:8000`을 부를 때 출처가 다르다고 보고 막는다. `CORSMiddleware`의 `CORS_ORIGINS`에 프론트 주소를 넣어야 실제 브라우저 요청이 통과한다.
- **XSS**: API는 HTML을 렌더링하지 않는다. React는 텍스트를 이스케이프한다. 응답 문자열을 `dangerouslySetInnerHTML`에 넣지 않는다.
- **CSRF**: 이 앱은 쿠키가 아니라 Authorization 헤더를 쓴다. 다른 사이트의 폼이 우리 쿠키를 몰래 붙이는 유형의 공격은 이 방식에서 성립하기 어렵다. 쿠키로 바꾸는 날에는 CSRF 토큰이 다시 필요해진다.

### 비유

토큰은 기간이 적힌 출입증이다. 경비(`get_current_user`)는 도장을 확인하고, 명단에 이름이 있는지도 본다. 분실 신고(`logout`)가 된 출입증은 도장이 맞아도 들여보내지 않는다. 비밀번호 해시는 지문 기록이지, 열쇠를 서랍에 그대로 넣는 일이 아니다.

## ③ 🛠️ 실기

해시와 발급은 `app/security.py`에 있다.

```python
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(subject: str, expires_delta: timedelta | None = None) -> tuple[str, str]:
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    payload = {"sub": subject, "exp": expire, "jti": jti}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti
```

줄별 설명:

1. 해시 알고리즘을 pbkdf2_sha256 하나로 고정한다. bcrypt는 환경마다 설치가 달라 학습 기본값으로 쓰지 않는다.
2. 빈 줄.
3. 평문을 해시로 바꾼다. 같은 비밀번호도 호출마다 다른 문자열이 된다.
4. passlib이 salt를 포함해 저장용 문자열을 만든다.
5. 빈 줄.
6. 로그인 때 평문과 저장값을 비교한다. 비교 결과를 뒤집어서 "왜 틀렸는지"를 설명하지 않는다.
7. 일치하면 True.
8. 빈 줄.
9. 이메일(`subject`)을 담은 토큰과 폐기용 id를 함께 돌려준다.
10. 토큰마다 고유한 jti.
11. 만료 시각은 UTC다. 설정이 없으면 `ACCESS_TOKEN_EXPIRE_MINUTES`.
12. `sub`는 누구의 토큰인지, `exp`는 언제 죽는지, `jti`는 폐기 목록의 키다.
13. `SECRET_KEY`로 서명한다. 이 키가 새면 아무 토큰이나 만들 수 있다.
14. 문자열과 jti를 반환한다.

`get_current_user`는 `OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)`로 헤더에서 문자열을 꺼낸다. 없거나, 서명이 틀리거나, 폐기되었거나, 그 사이 회원이 지워졌으면 401 `UNAUTHORIZED`다.

프론트는 로그인 응답의 `accessToken`과 사용자 `id`를 `localStorage`의 `auth`에 넣는다. 새로고침 뒤에도 글 삭제 버튼(내 id와 `author.id`가 같을 때만)을 그릴 수 있다. 로그아웃은 서버에 POST한 뒤 localStorage를 지운다. 서버가 이미 401을 줘도 화면의 로그인 상태는 지운다.

CORS 허용 목록의 기본값은 `http://localhost:3000`과 `http://localhost:5173`이다. 쿠키를 쓰지 않아도 브라우저의 cross-origin 요청에는 이 허용이 필요하다.

## ④ 🔗 연동 포인트

study6의 `author_id`와 토큰으로 찾은 `user.id`가 같아야 수정·삭제가 된다. 화면과 서버가 로그인 상태를 공유하는 방법은 쿠키가 아니라 `Authorization` 헤더와 `localStorage`다. 서버는 토큰만 믿고, 화면은 토큰이 있을 때만 보호된 버튼을 그린다. 실제 권한 판단은 항상 서버가 다시 한다.

## ⑤ 오류 노트

| 증상 | 원인 | 해결 |
| --- | --- | --- |
| 토큰을 넣었는데 401 | `Bearer ` 접두어가 없음 | `Authorization: Bearer <token>` |
| 로그아웃 후에도 글이 써짐 | 폐기 목록을 안 봄 | `is_revoked(jti)`를 `get_current_user`에서 확인 |
| 브라우저만 실패하고 curl은 성공 | CORS 출처가 다름 | `CORS_ORIGINS`에 프론트 출처를 추가하고 서버 재시작 |
| 비밀번호가 응답에 보임 | 응답 모델에 해시 필드를 넣음 | `UserResponse`에서 그 필드를 제거 |
| 남의 글 수정이 200 | 404보다 403을 먼저 하거나 검사를 빠뜨림 | 존재 확인 다음에 `_check_owner` |

## ⑥ 직접 해보기

1. 로그인 JSON에서 `accessToken`을 복사해 `/api/auth/me`에 Bearer로 붙인다.
2. 로그아웃한 같은 토큰으로 `/api/auth/me`를 다시 호출해 401을 확인한다.
3. 두 계정으로 같은 글을 수정해 작성자가 아닌 쪽이 403인지 본다.

## ⑦ ☐ 체크리스트

- [ ] 비밀번호는 pbkdf2_sha256 해시로만 저장된다.
- [ ] 로그인 응답에 `accessToken`과 사용자 정보가 `data` 안에 있다.
- [ ] 토큰이 없거나 폐기되면 401이다.
- [ ] 없는 글은 404, 남의 글은 403이다.
- [ ] 화면은 localStorage의 토큰을 Authorization 헤더로 되돌린다.
- [ ] JWT 인증

## ⑧ 다음 단계

신원 확인이 붙었으면 study8에서 폴더와 설정 파일을 정리해 개발용 값과 운영용 값이 코드 안에 섞이지 않게 한다.
