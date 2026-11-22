"""회원 HTTP. 경로는 /api 라우터 아래에서 /auth/* 가 된다."""

from fastapi import APIRouter, Depends, Request, status
from fastapi.responses import Response
from pydantic import ValidationError
from sqlalchemy.orm import Session

from app.database import get_db
from app.errors import AppError
from app.models.user import User
from app.schemas.user import LoginEnvelope, LoginRequest, UserCreate, UserEnvelope
from app.services import user as service
from app.services.user import get_current_user, oauth2_scheme

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/signup", response_model=UserEnvelope, status_code=status.HTTP_201_CREATED)
def signup(user: UserCreate, db: Session = Depends(get_db)):
    return UserEnvelope(data=service.register_user(db, user))


@router.post("/login", response_model=LoginEnvelope)
async def login(request: Request, db: Session = Depends(get_db)):
    """JSON 본문(email, password)과 Swagger용 폼(username, password)을 모두 받는다."""
    content_type = request.headers.get("content-type", "")
    if "application/json" in content_type:
        try:
            payload = await request.json()
        except Exception as exc:
            raise AppError(status.HTTP_400_BAD_REQUEST, "BAD_REQUEST", "JSON 형식이 올바르지 않습니다.") from exc
        if not isinstance(payload, dict):
            raise AppError(status.HTTP_400_BAD_REQUEST, "BAD_REQUEST", "JSON 형식이 올바르지 않습니다.")
        email = payload.get("email") or payload.get("username")
        password = payload.get("password")
    else:
        form = await request.form()
        email = form.get("username") or form.get("email")
        password = form.get("password")
    if not email or password is None or password == "":
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "VALIDATION_ERROR",
            "입력값을 확인하세요.",
            fields={"email": ["이메일과 비밀번호를 입력하세요."]},
        )
    try:
        parsed = LoginRequest.model_validate({"email": email, "password": password})
    except ValidationError as exc:
        raise AppError(
            status.HTTP_400_BAD_REQUEST,
            "VALIDATION_ERROR",
            "입력값을 확인하세요.",
            fields={"email": ["이메일 형식을 확인하세요."]},
        ) from exc
    return service.authenticate(db, str(parsed.email), parsed.password)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(
    token: str | None = Depends(oauth2_scheme),
    current_user: User = Depends(get_current_user),
):
    if token:
        service.revoke_token(token)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserEnvelope)
def me(current_user: User = Depends(get_current_user)):
    return UserEnvelope(data=service.to_user_response(current_user))
