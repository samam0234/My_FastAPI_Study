import time

from fastapi import Query


class Pagination:
    """여러 라우터에서 재사용하는 페이지네이션 쿼리 파라미터 의존성."""

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
