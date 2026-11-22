"""여러 라우터가 같이 쓰는 의존성."""

import time

from fastapi import Query


class PageParams:
    """목록 쿼리. page는 1부터, limit는 1~50이며 50을 넘으면 50으로 자른다."""

    def __init__(
        self,
        page: int = Query(default=1, ge=1, description="1부터 세는 페이지 번호"),
        limit: int = Query(default=10, ge=1, description="한 페이지 개수. 50을 넘으면 50"),
        q: str = Query(default="", description="제목·본문 검색어"),
        sort: str = Query(default="-createdAt", description="createdAt, -createdAt, -commentCount"),
    ) -> None:
        self.page = page
        self.limit = min(limit, 50)
        self.q = q
        self.sort = sort


def log_request_time():
    """yield 위는 요청 전, 아래는 응답 후. 라우터 dependencies에 걸어 모든 경로에 적용한다."""
    start = time.perf_counter()
    yield
    elapsed_ms = (time.perf_counter() - start) * 1000
    print(f"[dependency] request handled in {elapsed_ms:.2f}ms")
