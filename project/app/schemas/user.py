# ─────────────────────────────────────────────────────────────
# schemas/user.py : 회원가입/응답/토큰의 데이터 형태(Pydantic 스키마)
# ─────────────────────────────────────────────────────────────
from pydantic import BaseModel, ConfigDict


# 회원가입 요청 본문: 클라이언트가 보내는 값
class UserCreate(BaseModel):
    username: str
    password: str  # 평문 비밀번호 (저장 전에 서버에서 해시 처리한다)


# 회원 정보 응답: 비밀번호(hashed_password)를 일부러 포함하지 않아 외부로 노출되지 않게 한다.
class UserResponse(BaseModel):
    # ORM 객체(User)를 그대로 넘겨도 변환되도록 허용
    model_config = ConfigDict(from_attributes=True)

    id: int
    username: str


# 로그인 성공 응답: JWT 토큰과 그 종류
class Token(BaseModel):
    access_token: str  # 발급된 JWT 문자열
    token_type: str  # 항상 "bearer" → 요청 시 "Authorization: Bearer <토큰>" 형태로 사용
