"""study6 개념 확인용 라우트 모음 (async/blocking 비교 실습 전용)."""

import asyncio  # 비동기 프로그래밍용 표준 라이브러리 (asyncio.sleep 등)
import time  # 동기(블로킹) 대기용 time.sleep 사용

from fastapi import APIRouter

router = APIRouter(prefix="/async-demo", tags=["async-demo"])


# async def: "코루틴" 함수. FastAPI가 이벤트 루프(한 스레드)에서 직접 실행한다.
@router.get("/bad-async")
async def bad_async():
    """async def 안에서 blocking 코드(time.sleep)를 직접 호출한 나쁜 예.

    이벤트 루프 자체가 멈춰버려서, 동시에 들어온 다른 요청도 이 응답이
    끝날 때까지 기다리게 된다.
    """
    time.sleep(2)  # 블로킹: 2초간 이벤트 루프 전체를 붙잡는다 (다른 요청 처리 불가)
    return {"done": "bad-async"}


@router.get("/good-async")
async def good_async():
    """asyncio.sleep처럼 진짜 비동기 I/O로 대기하는 좋은 예.

    대기하는 동안 이벤트 루프가 다른 요청을 동시에 처리할 수 있다.
    """
    # await: "여기서 기다리는 동안 제어권을 이벤트 루프에 넘긴다"는 표시.
    #   await는 async def 안에서만 쓸 수 있고, await 가능한 대상(asyncio.sleep 등)에만 붙인다.
    await asyncio.sleep(2)
    return {"done": "good-async"}


# 그냥 def(동기 함수): FastAPI가 별도 스레드풀에서 실행하므로 이벤트 루프를 막지 않는다.
@router.get("/sync-def")
def sync_def():
    """일반 def 라우트. FastAPI가 자동으로 별도 스레드풀에서 실행해준다.

    time.sleep처럼 블로킹 코드를 써도 이벤트 루프는 막히지 않는다
    (단, 스레드풀 크기만큼만 동시 처리 가능).
    """
    time.sleep(2)
    return {"done": "sync-def"}
