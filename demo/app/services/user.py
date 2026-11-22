"""회원가입, 로그인, 현재 사용자."""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from fastapi import Depends, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from app.database import get_db
from app.errors import AppError
from app.models.user import User
from app.repositories import user as repository
from app.schemas.user import LoginData, LoginEnvelope, UserCreate, UserResponse
from app.security import (
    ALGORITHM,
    SECRET_KEY,
    create_access_token,
    hash_password,
    is_revoked,
    reset_revoked_tokens,
    revoke_jti,
    verify_password,
)

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)


def _unauthorized() -> AppError:
    return AppError(
        status.HTTP_401_UNAUTHORIZED,
        "UNAUTHORIZED",
        "인증 정보를 확인할 수 없습니다.",
        headers={"WWW-Authenticate": "Bearer"},
    )


def reset_auth_state() -> None:
    reset_revoked_tokens()


def to_user_response(user: User) -> UserResponse:
    return UserResponse(id=user.id, email=user.email, nickname=user.nickname)


def register_user(db: Session, data: UserCreate) -> UserResponse:
    email = str(data.email).lower()
    nickname = data.nickname.strip()
    if not nickname:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "VALIDATION_ERROR",
            "입력값을 확인하세요.",
            fields={"nickname": ["닉네임을 입력하세요."]},
        )
    if repository.get_by_email(db, email) is not None:
        raise AppError(status.HTTP_409_CONFLICT, "EMAIL_TAKEN", "이미 가입된 이메일입니다.")
    try:
        user = repository.create(db, email, nickname, hash_password(data.password))
    except IntegrityError:
        raise AppError(status.HTTP_409_CONFLICT, "EMAIL_TAKEN", "이미 가입된 이메일입니다.") from None
    return to_user_response(user)


def authenticate(db: Session, email: str, password: str) -> LoginEnvelope:
    user = repository.get_by_email(db, email.lower())
    if user is None or not verify_password(password, user.hashed_password):
        raise AppError(
            status.HTTP_401_UNAUTHORIZED,
            "INVALID_CREDENTIALS",
            "이메일 또는 비밀번호가 올바르지 않습니다.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token, _jti = create_access_token(user.email)
    return LoginEnvelope(data=LoginData(user=to_user_response(user), access_token=token))


def get_current_user(token: str | None = Depends(oauth2_scheme), db: Session = Depends(get_db)) -> User:
    if not token:
        raise _unauthorized()
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email = payload.get("sub")
        jti = payload.get("jti")
        if not isinstance(email, str) or is_revoked(jti if isinstance(jti, str) else None):
            raise _unauthorized()
    except JWTError:
        raise _unauthorized()
    user = repository.get_by_email(db, email)
    if user is None:
        raise _unauthorized()
    return user


def revoke_token(token: str) -> None:
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
    except JWTError:
        return
    jti = payload.get("jti")
    if isinstance(jti, str):
        revoke_jti(jti)
