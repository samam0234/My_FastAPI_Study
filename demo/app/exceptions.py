"""예외를 공통 오류 JSON으로 바꾼다.

성공이 아닌 응답은 모두 이 모양이다.

    {"error": {"code": "...", "message": "...", "fields": {...}, "requestId": "..."}}

fields는 검증 실패처럼 필드별 이유가 있을 때만 넣는다.
스택 원문은 500 응답에 넣지 않고 로그에만 남긴다.
"""

import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.errors import AppError
from app.schemas.common import to_camel

logger = logging.getLogger("app")

_STATUS_CODE = {
    400: "BAD_REQUEST",
    401: "UNAUTHORIZED",
    403: "FORBIDDEN",
    404: "NOT_FOUND",
    405: "BAD_REQUEST",
    409: "EMAIL_TAKEN",
    413: "PAYLOAD_TOO_LARGE",
    422: "VALIDATION_ERROR",
    429: "RATE_LIMITED",
    500: "INTERNAL",
    503: "INTERNAL",
}


def request_id_of(request: Request) -> str:
    return getattr(request.state, "request_id", "") or ""


def error_payload(code: str, message: str, request_id: str, fields: dict | None = None) -> dict:
    error: dict = {"code": code, "message": message, "requestId": request_id}
    if fields:
        error["fields"] = fields
    return {"error": error}


def _field_message(err: dict) -> str:
    loc = [str(part) for part in err.get("loc", []) if part not in ("body", "query", "path")]
    name = loc[-1] if loc else ""
    err_type = err.get("type", "")
    if name == "title" and err_type in {"string_too_short", "string_too_long"}:
        return "1~200자로 입력하세요."
    if name == "password" and err_type == "string_too_short":
        return "비밀번호는 8자 이상이어야 합니다."
    msg = str(err.get("msg", "입력값을 확인하세요."))
    if msg.startswith("Value error, "):
        msg = msg.removeprefix("Value error, ")
    return msg


def fields_from_validation(exc: RequestValidationError) -> dict[str, list[str]]:
    grouped: dict[str, list[str]] = {}
    for err in exc.errors():
        loc = [str(part) for part in err.get("loc", []) if part not in ("body", "query", "path")]
        key = to_camel(loc[-1]) if loc else "request"
        grouped.setdefault(key, []).append(_field_message(err))
    return grouped


def validation_code(exc: RequestValidationError) -> str:
    """경로 id가 숫자가 아니거나 JSON 문법이 깨지면 BAD_REQUEST, 값 검증은 VALIDATION_ERROR."""
    for err in exc.errors():
        loc = err.get("loc", ())
        if loc and loc[0] == "path":
            return "BAD_REQUEST"
        if err.get("type") in {"json_invalid", "json_type"}:
            return "BAD_REQUEST"
    return "VALIDATION_ERROR"


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(exc.code, exc.message, request_id_of(request), exc.fields),
        headers=exc.headers,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    code = _STATUS_CODE.get(exc.status_code, "BAD_REQUEST")
    message = exc.detail if isinstance(exc.detail, str) else "요청을 처리할 수 없습니다."
    if exc.status_code == 404 and message == "Not Found":
        message = "요청한 경로를 찾을 수 없습니다."
        code = "NOT_FOUND"
    return JSONResponse(
        status_code=exc.status_code,
        content=error_payload(code, message, request_id_of(request)),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    code = validation_code(exc)
    return JSONResponse(
        status_code=status.HTTP_400_BAD_REQUEST,
        content=error_payload(code, "입력값을 확인하세요.", request_id_of(request), fields_from_validation(exc)),
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.exception("unhandled error while processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=error_payload("INTERNAL", "서버 내부 오류가 발생했습니다.", request_id_of(request)),
    )
