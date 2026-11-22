"""HTTP로 바꿀 수 있는 애플리케이션 오류.

라우터와 서비스는 이 예외를 던지고, exceptions.py가 공통 JSON으로 바꾼다.
"""


class AppError(Exception):
    def __init__(
        self,
        status_code: int,
        code: str,
        message: str,
        fields: dict | None = None,
        headers: dict | None = None,
    ) -> None:
        self.status_code = status_code
        self.code = code
        self.message = message
        self.fields = fields or None
        self.headers = headers or None
        super().__init__(message)
