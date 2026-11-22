"""비밀번호 해시와 JWT 발급.

해시 알고리즘은 pbkdf2_sha256이다. bcrypt는 OS별 확장이 필요해서
학습 환경에서는 passlib의 순수 파이썬 해시를 쓴다.
"""

import uuid
from datetime import datetime, timedelta, timezone

from jose import jwt
from passlib.context import CryptContext

from app.config import get_settings

pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
_settings = get_settings()
SECRET_KEY = _settings.secret_key
ALGORITHM = _settings.algorithm
ACCESS_TOKEN_EXPIRE_MINUTES = _settings.access_token_expire_minutes

_revoked_jti: set[str] = set()


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(subject: str, expires_delta: timedelta | None = None) -> tuple[str, str]:
    """(토큰 문자열, jti)를 돌려준다. jti는 로그아웃 때 폐기 목록에 넣는다."""
    jti = str(uuid.uuid4())
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    payload = {"sub": subject, "exp": expire, "jti": jti}
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    return token, jti


def revoke_jti(jti: str) -> None:
    _revoked_jti.add(jti)


def is_revoked(jti: str | None) -> bool:
    return bool(jti) and jti in _revoked_jti


def reset_revoked_tokens() -> None:
    """테스트마다 메모리 폐기 목록을 비운다."""
    _revoked_jti.clear()
