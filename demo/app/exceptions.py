# ─────────────────────────────────────────────────────────────
# exceptions.py : 전역 예외 핸들러 모음
#   예외가 발생했을 때 응답 형식(JSON)을 한 곳에서 통일해 프론트엔드가 다루기 쉽게 만든다.
#   실제 등록은 main.py의 app.add_exception_handler(...) 에서 한다.
# ─────────────────────────────────────────────────────────────
import logging  # 표준 로깅 라이브러리 (서버 로그에 기록할 때 사용)

# Request: 들어온 HTTP 요청 객체 / status: HTTP 상태 코드 상수 모음(예: status.HTTP_422_...)
from fastapi import Request, status

# RequestValidationError: 요청 데이터가 Pydantic 검증에 실패했을 때 FastAPI가 던지는 예외.
from fastapi.exceptions import RequestValidationError

# JSONResponse: JSON 형태로 응답을 직접 만들어 돌려줄 때 쓰는 응답 클래스.
from fastapi.responses import JSONResponse

# Starlette의 HTTPException: FastAPI의 HTTPException의 부모 클래스.
#   이걸로 등록해야 FastAPI가 던진 예외와 Starlette 내부에서 던진 예외(예: 없는 URL 404)를 모두 잡는다.
from starlette.exceptions import HTTPException as StarletteHTTPException

# "app"이라는 이름의 로거를 얻는다. 이후 logger.exception() 등으로 로그를 남길 수 있다.
logger = logging.getLogger("app")


# async def: 비동기 함수. 예외 핸들러는 (요청, 예외 객체) 두 인자를 받는 규칙이다.
async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """HTTPException(404, 401, 403 등)을 공통 포맷으로 응답한다."""
    return JSONResponse(
        status_code=exc.status_code,  # 예외에 담긴 상태 코드를 그대로 사용
        content={"detail": exc.detail},  # 응답 본문: {"detail": "에러 메시지"}
        # getattr(객체, "속성명", 기본값): 속성이 없으면 None을 돌려준다.
        #   401 응답의 WWW-Authenticate 같은 헤더를 그대로 전달하기 위해 사용.
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """Pydantic 검증 실패(422)를 프론트엔드가 다루기 쉬운 형태로 통일한다."""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,  # 422: 형식은 맞지만 값이 잘못됨
        # exc.errors(): 어떤 필드가 왜 잘못됐는지 담긴 상세 오류 목록(리스트)
        content={"detail": "요청 데이터가 올바르지 않습니다.", "errors": exc.errors()},
    )


async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """예상하지 못한 예외(버그)는 500으로 감싸고, 상세 내용은 서버 로그에만 남긴다."""
    # logger.exception(): 에러 메시지 + 스택트레이스(traceback)를 서버 로그에 기록한다.
    #   %s 자리에 뒤의 인자(요청 메서드, URL)가 순서대로 채워진다.
    logger.exception("unhandled error while processing %s %s", request.method, request.url)
    # 사용자에게는 내부 정보를 숨기고 일반적인 메시지만 보여준다 (보안상 스택트레이스 노출 금지).
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": "서버 내부 오류가 발생했습니다."},
    )
