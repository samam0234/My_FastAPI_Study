from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import jwt
from passlib.context import CryptContext

# bcrypt는 OS별로 컴파일된 확장이 필요해 환경에 따라 설치가 까다로울 수 있어,
# 순수 파이썬으로 동작하는 pbkdf2_sha256을 사용합니다. 운영에서는 bcrypt/argon2도 흔히 씁니다.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

# 실습용 시크릿 키입니다. 실제 서비스에서는 반드시 환경변수(.env)로 분리해야 합니다(study10 참고).
SECRET_KEY = "study-only-secret-key-do-not-use-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
