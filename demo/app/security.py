from passlib.context import CryptContext

# bcrypt는 OS별로 컴파일된 확장이 필요해 환경에 따라 설치가 까다로울 수 있어,
# 순수 파이썬으로 동작하는 pbkdf2_sha256을 사용합니다. 운영에서는 bcrypt/argon2도 흔히 씁니다.
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")


def hash_password(plain_password: str) -> str:
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)
