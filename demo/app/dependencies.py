import time

from fastapi import Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app import models, store
from app.database import get_db
from app.security import ALGORITHM, SECRET_KEY

# tokenUrl은 "로그인 요청을 어디로 보내는지"를 /docs(Swagger UI)에게 알려주는 값일 뿐이고,
# 토큰 검증 로직 자체는 아래 get_current_user()에서 직접 수행한다.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")


class Pagination:
    """여러 라우트에서 재사용하는 페이지네이션 쿼리 파라미터 의존성."""

    def __init__(
        self,
        skip: int = Query(default=0, ge=0),
        limit: int = Query(default=10, ge=1, le=100),
    ):
        self.skip = skip
        self.limit = limit


def log_request_time():
    """라우터 단위 의존성 예시: 요청 처리 시간을 로그로 남긴다."""
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"[dependency] request handled in {elapsed_ms:.2f}ms")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> models.User:
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

    user = store.get_user_by_username(db, username)
    if user is None:
        raise credentials_exception
    return user
