"""MongoDB는 SQLAlchemy 엔진으로 붙이지 않는다.

이 파일은 실행하지 않는 연결 예시이다. 드라이버는 따로 설치한다.

    pip install motor
    MONGO_URL=mongodb://localhost:27017

게시판 본 앱은 관계형 DB와 SQLAlchemy를 유지한다.
"""

MONGO_URL = "mongodb://localhost:27017"
DATABASE_NAME = "board"


async def example_insert(title: str, body: str) -> None:
    from motor.motor_asyncio import AsyncIOMotorClient

    client = AsyncIOMotorClient(MONGO_URL)
    await client[DATABASE_NAME].posts.insert_one({"title": title, "body": body})
    client.close()
