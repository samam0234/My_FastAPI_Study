"""study6 개념 확인용 라우트 모음. 실제 도메인이 아니라 async/blocking 비교 실습 전용이라
posts/users 같은 도메인 폴더와 분리해 practice/ 아래에 둔다.
"""

import asyncio
import time

from fastapi import APIRouter

router = APIRouter(prefix="/async-demo", tags=["async-demo"])


@router.get("/bad-async")
async def bad_async():
    """async def 안에서 blocking 코드(time.sleep)를 직접 호출한 나쁜 예.

    이벤트 루프 자체가 멈춰버려서, 동시에 들어온 다른 요청도 이 응답이
    끝날 때까지 기다리게 된다.
    """
    time.sleep(2)
    return {"done": "bad-async"}


@router.get("/good-async")
async def good_async():
    """asyncio.sleep처럼 진짜 비동기 I/O로 대기하는 좋은 예.

    대기하는 동안 이벤트 루프가 다른 요청을 동시에 처리할 수 있다.
    """
    await asyncio.sleep(2)
    return {"done": "good-async"}


@router.get("/sync-def")
def sync_def():
    """일반 def 라우트. FastAPI가 자동으로 별도 스레드풀에서 실행해준다.

    time.sleep처럼 블로킹 코드를 써도 이벤트 루프는 막히지 않는다
    (단, 스레드풀 크기만큼만 동시 처리 가능).
    """
    time.sleep(2)
    return {"done": "sync-def"}
