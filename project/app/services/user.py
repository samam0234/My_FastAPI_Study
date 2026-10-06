"""비즈니스 로직 계층: 회원가입 규칙, 로그인 인증, 토큰 발급/검증."""

from datetime import timedelta

# Depends: 의존성 주입 표시 / HTTPException: 에러 응답용 예외 / status: 상태코드 상수
from fastapi import Depends, HTTPException, status

# OAuth2PasswordBearer: 요청 헤더 "Authorization: Bearer <토큰>"에서 토큰을 꺼내주는 도구
from fastapi.security import OAuth2PasswordBearer

# JWTError: 토큰이 위조/만료/형식오류일 때 발생하는 예외 / jwt: 토큰 해석(decode)에 사용
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.user import User
from app.repositories import user as repository
from app.schemas.user import Token, UserCreate
from app.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    hash_password,
    verify_password,
)

# tokenUrl은 "로그인 요청을 어디로 보내는지"를 /docs(Swagger UI)에게 알려주는 값일 뿐이고,
# 토큰 검증 로직 자체는 아래 get_current_user()에서 직접 수행한다.
# oauth2_scheme을 Depends()에 넣으면 /docs에 🔒 Authorize 버튼이 생긴다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def register_user(db: Session, user: UserCreate) -> User:
    # 이미 같은 username이 있으면 400(잘못된 요청)으로 거절한다 — 이것이 "중복 검사" 규칙.
    if repository.get_by_username(db, user.username) is not None:
        raise HTTPException(status_code=400, detail="이미 존재하는 username입니다.")
    # 비밀번호는 반드시 해시해서 저장한다 (평문 저장 금지).
    return repository.create(db, user.username, hash_password(user.password))


def authenticate(db: Session, username: str, password: str) -> Token:
    user = repository.get_by_username(db, username)
    # 사용자가 없거나 비밀번호가 틀리면 같은 에러를 준다.
    #   (어느 쪽이 틀렸는지 알려주면 공격자가 존재하는 username을 알아낼 수 있기 때문)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="username 또는 password가 올바르지 않습니다.",
            # 401 응답 표준 헤더: "Bearer 방식으로 인증해라"라고 클라이언트에 알려준다.
            headers={"WWW-Authenticate": "Bearer"},
        )
    # 토큰 payload의 "sub"(subject)는 JWT 표준 클레임: 이 토큰이 누구의 것인지(여기서는 username)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),  # 유효 시간 지정
    )
    return Token(access_token=access_token, token_type="bearer")


def get_current_user(
    # Depends(oauth2_scheme): 헤더에서 Bearer 토큰 문자열을 꺼내 token에 넣어준다 (없으면 자동 401).
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Authorization: Bearer <token> 헤더를 검증해 로그인한 User를 주입한다."""
    # 인증 실패 시 공통으로 던질 예외를 미리 만들어 둔다 (아래에서 여러 번 재사용).
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        # decode: 서명과 만료시간(exp)을 함께 검증하고 payload(dict)를 돌려준다.
        #   algorithms=[...]: 허용할 알고리즘을 명시해 다른 알고리즘으로 위조된 토큰을 막는다.
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        # "str | None": 문자열이거나 None (payload.get은 키가 없으면 None을 돌려준다)
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        # 위조·만료·형식 오류 등 토큰 문제는 모두 같은 401로 처리한다.
        raise credentials_exception

    # 토큰이 유효해도 그 사이 회원이 삭제됐을 수 있으므로 DB에서 다시 확인한다.
    user = repository.get_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user
