# ─────────────────────────────────────────────────────────────
# security.py : 비밀번호 해싱/검증 + JWT(로그인 토큰) 생성
#   "보안 관련 순수 함수"만 모아둔 모듈. DB나 HTTP는 전혀 모른다.
# ─────────────────────────────────────────────────────────────
# datetime: 날짜·시간 / timedelta: 시간 간격(예: 30분) / timezone: 시간대(UTC 등)
from datetime import datetime, timedelta, timezone
from typing import Optional

# jose.jwt: JWT(JSON Web Token)를 만들고(encode) 해석하는(decode) 라이브러리
from jose import jwt

# CryptContext: 비밀번호 해싱 알고리즘을 설정하고 hash/verify를 제공하는 passlib 도구
from passlib.context import CryptContext

from app.config import get_settings

# bcrypt는 OS별로 컴파일된 확장이 필요해 환경에 따라 설치가 까다로울 수 있어,
# 순수 파이썬으로 동작하는 pbkdf2_sha256을 사용합니다. 운영에서는 bcrypt/argon2도 흔히 씁니다.
# schemes: 사용할 해시 알고리즘 목록 / deprecated="auto": 목록의 옛 알고리즘은 자동으로 '구식' 처리
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")

settings = get_settings()
# 설정값을 모듈 상수로 꺼내 둔다 (관례상 상수는 대문자로 쓴다). 다른 모듈에서 import해 사용한다.
SECRET_KEY = settings.secret_key  # 토큰에 서명할 때 쓰는 비밀키 (유출되면 토큰 위조 가능!)
ALGORITHM = settings.algorithm  # 서명 알고리즘 (HS256)
ACCESS_TOKEN_EXPIRE_MINUTES = settings.access_token_expire_minutes  # 토큰 기본 유효 시간(분)


def hash_password(plain_password: str) -> str:
    # 평문 → 해시. 해시는 되돌릴 수 없고(단방향), 같은 비밀번호라도 salt 때문에 매번 값이 달라진다.
    return pwd_context.hash(plain_password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    # 입력한 평문을 같은 방식으로 해시해 저장된 해시와 일치하는지 비교한다 (True/False).
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    # data.copy(): 원본 딕셔너리를 건드리지 않도록 복사본을 만든다.
    to_encode = data.copy()
    # 만료 시각 = 현재 UTC 시각 + 유효 시간 (expires_delta가 없으면 기본 분 단위 값 사용)
    #   "A or B": A가 None이면 B를 쓴다.
    expire = datetime.now(timezone.utc) + (
        expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    # "exp"는 JWT 표준 클레임(claim, 토큰에 담긴 정보 항목) 이름: 이 시각이 지나면 토큰이 무효가 된다.
    to_encode.update({"exp": expire})
    # 내용(payload)을 SECRET_KEY로 서명해 "xxxx.yyyy.zzzz" 형태의 JWT 문자열로 만든다.
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
