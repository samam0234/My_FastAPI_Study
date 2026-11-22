"""회원 요청/응답 스키마. 비밀번호 해시는 어떤 응답에도 없다."""

from pydantic import EmailStr, Field

from app.schemas.common import APIModel


class UserCreate(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)
    nickname: str = Field(min_length=1, max_length=50)


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=1)


class UserResponse(APIModel):
    id: int
    email: EmailStr
    nickname: str


class UserEnvelope(APIModel):
    data: UserResponse


class LoginData(APIModel):
    user: UserResponse
    access_token: str


class LoginEnvelope(APIModel):
    data: LoginData
