# ─────────────────────────────────────────────────────────────
# dependencies.py : 여러 라우터에서 재사용하는 "의존성(Depends)" 모음
#   의존성 주입(DI): 라우트 함수가 필요로 하는 값/객체를 FastAPI가 대신 만들어서 넣어주는 기능.
# ─────────────────────────────────────────────────────────────
import time  # 시간 측정용 표준 라이브러리

# Query: 쿼리스트링(?skip=0&limit=10) 파라미터의 기본값과 검증 규칙을 선언하는 도구.
from fastapi import Query


class Pagination:
    """여러 라우터에서 재사용하는 페이지네이션 쿼리 파라미터 의존성."""

    # 클래스를 Depends()에 넘기면 FastAPI가 __init__의 매개변수를 쿼리 파라미터로 받아
    # 인스턴스를 만들어 준다. → 라우트에서 pagination.skip / pagination.limit 로 사용.
    def __init__(
        self,
        # skip: 앞에서 몇 개를 건너뛸지. default=0, ge=0 → "0 이상"(greater or equal)만 허용.
        skip: int = Query(default=0, ge=0),
        # limit: 한 번에 가져올 개수. default=10, ge=1(1 이상), le=100(100 이하; less or equal).
        limit: int = Query(default=10, ge=1, le=100),
    ):
        # 범위를 벗어나면 FastAPI가 자동으로 422 에러를 반환하므로 여기서 따로 검사할 필요가 없다.
        self.skip = skip
        self.limit = limit


def log_request_time():
    """라우터 단위 의존성 예시: 요청 처리 시간을 로그로 남긴다."""
    # perf_counter(): 짧은 시간 간격을 정밀하게 재는 타이머(초 단위).
    start = time.perf_counter()
    # yield 이전 = 요청 처리 "전"에 실행, yield 이후 = 응답 처리 "후"에 실행된다.
    yield
    # 경과 시간(초)을 밀리초로 환산 (×1000)
    elapsed_ms = (time.perf_counter() - start) * 1000
    # f-string의 {값:.2f} → 소수점 둘째 자리까지 표시
    print(f"[dependency] request handled in {elapsed_ms:.2f}ms")
