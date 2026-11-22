"""요청마다 같은 요청 ID를 응답 헤더에 붙인다."""

import uuid


class RequestIdMiddleware:
    """ASGI 미들웨어. X-Request-Id가 오면 그대로 쓰고, 없으면 새로 만든다."""

    def __init__(self, app) -> None:
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        headers = {key.decode("latin-1").lower(): value.decode("latin-1") for key, value in scope.get("headers", [])}
        request_id = headers.get("x-request-id") or str(uuid.uuid4())
        scope.setdefault("state", {})["request_id"] = request_id

        async def send_with_id(message):
            if message["type"] == "http.response.start":
                raw = list(message.get("headers") or [])
                raw.append((b"x-request-id", request_id.encode("latin-1")))
                message["headers"] = raw
            await send(message)

        await self.app(scope, receive, send_with_id)
