"""파일, 메일 로그, 결제 초안, 소셜 로그인 주소.

외부 서비스의 비밀키는 .env에만 둔다. 키가 없으면 네트워크를 호출하지 않는다.
"""

import uuid
from pathlib import Path
from urllib.parse import urlencode

from fastapi import APIRouter, Depends, File, UploadFile, status
from pydantic import Field

from app.config import get_settings
from app.errors import AppError
from app.models.user import User
from app.schemas.common import APIModel
from app.services.user import get_current_user

router = APIRouter(tags=["integrations"])
_outbox: list[dict] = []
_ALLOWED = {".txt", ".md", ".pdf", ".png", ".jpg", ".jpeg"}


class MailIn(APIModel):
    to: str = Field(min_length=3, max_length=255)
    subject: str = Field(min_length=1, max_length=200)
    body: str = Field(min_length=1, max_length=5000)


class PaymentIn(APIModel):
    amount: int = Field(ge=100, le=10_000_000)
    order_name: str = Field(min_length=1, max_length=100)


def reset_integrations() -> None:
    _outbox.clear()


@router.post("/uploads", status_code=status.HTTP_201_CREATED)
async def upload_file(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user),
):
    settings = get_settings()
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in _ALLOWED:
        raise AppError(status.HTTP_400_BAD_REQUEST, "BAD_REQUEST", "허용되지 않은 파일 형식입니다.")
    content = await file.read()
    if len(content) > settings.max_upload_bytes:
        raise AppError(413, "PAYLOAD_TOO_LARGE", "업로드 한도를 넘었습니다.")
    folder = Path(settings.upload_dir)
    folder.mkdir(parents=True, exist_ok=True)
    stored = f"{uuid.uuid4().hex}{suffix}"
    (folder / stored).write_bytes(content)
    return {
        "data": {
            "filename": stored,
            "size": len(content),
            "uploadedBy": current_user.id,
        }
    }


@router.post("/mail/send", status_code=status.HTTP_202_ACCEPTED)
def send_mail(payload: MailIn, current_user: User = Depends(get_current_user)):
    """SMTP 호스트가 없으면 보낸 척하고 메모리에만 남긴다."""
    settings = get_settings()
    record = {
        "to": payload.to,
        "subject": payload.subject,
        "body": payload.body,
        "from": settings.smtp_from,
        "mode": "smtp" if settings.smtp_host else "log",
        "requestedBy": current_user.id,
    }
    _outbox.append(record)
    return {"data": record}


@router.get("/mail/outbox")
def mail_outbox(current_user: User = Depends(get_current_user)):
    return {"data": _outbox}


@router.post("/payments/draft", status_code=status.HTTP_201_CREATED)
def payment_draft(payload: PaymentIn, current_user: User = Depends(get_current_user)):
    checkout_id = uuid.uuid4().hex[:12]
    return {
        "data": {
            "provider": "mock",
            "amount": payload.amount,
            "orderName": payload.order_name,
            "checkoutUrl": f"https://pay.example.test/checkout/{checkout_id}",
            "requestedBy": current_user.id,
        }
    }


@router.get("/oauth/google")
def google_authorize_url():
    settings = get_settings()
    if not settings.google_client_id:
        raise AppError(status.HTTP_400_BAD_REQUEST, "BAD_REQUEST", "GOOGLE_CLIENT_ID가 없습니다.")
    query = urlencode(
        {
            "client_id": settings.google_client_id,
            "redirect_uri": settings.google_redirect_uri,
            "response_type": "code",
            "scope": "openid email profile",
        }
    )
    return {"data": {"authorizationUrl": f"https://accounts.google.com/o/oauth2/v2/auth?{query}"}}
