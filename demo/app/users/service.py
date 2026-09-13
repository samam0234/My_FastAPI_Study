"""비즈니스 로직 계층: 회원가입 규칙, 로그인 인증, 토큰 발급/검증."""

from datetime import timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    ACCESS_TOKEN_EXPIRE_MINUTES,
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    hash_password,
    verify_password,
)
from app.users import repository
from app.users.models import User
from app.users.schemas import Token, UserCreate

# tokenUrl은 "로그인 요청을 어디로 보내는지"를 /docs(Swagger UI)에게 알려주는 값일 뿐이고,
# 토큰 검증 로직 자체는 아래 get_current_user()에서 직접 수행한다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


def register_user(db: Session, user: UserCreate) -> User:
    if repository.get_by_username(db, user.username) is not None:
        raise HTTPException(status_code=400, detail="이미 존재하는 username입니다.")
    return repository.create(db, user.username, hash_password(user.password))


def authenticate(db: Session, username: str, password: str) -> Token:
    user = repository.get_by_username(db, username)
    if user is None or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="username 또는 password가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES),
    )
    return Token(access_token=access_token, token_type="bearer")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> User:
    """Authorization: Bearer <token> 헤더를 검증해 로그인한 User를 주입한다."""
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise credentials_exception
    except JWTError:
        raise credentials_exception

    user = repository.get_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user
