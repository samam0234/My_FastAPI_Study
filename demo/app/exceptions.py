import logging

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("app")


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTPException(404, 401, 403 등)을 공통 포맷으로 응답한다."""
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 검증 실패(422)를 프론트엔드가 다루기 쉬운 형태로 통일한다."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": "요청 데이터가 올바르지 않습니다.", "errors": exc.errors()},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """예상하지 못한 예외(버그)는 500으로 감싸고, 상세 내용은 서버 로그에만 남긴다."""
    logger.exception("unhandled error while processing %s %s", request.method, request.url)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "서버 내부 오류가 발생했습니다."},
    )
