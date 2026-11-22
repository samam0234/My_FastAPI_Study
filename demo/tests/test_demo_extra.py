"""demo에만 있는 기초 실습 경로."""


def test_hello_and_hidden_internal_error():
    from fastapi.testclient import TestClient

    from app.main import app

    # 테스트 클라이언트는 기본적으로 500 예외를 다시 던진다.
    # 실제 서버가 돌려주는 JSON을 보려면 이 옵션을 끈다.
    client = TestClient(app, raise_server_exceptions=False)
    hello = client.get("/hello")
    assert hello.status_code == 200
    assert "board" in hello.json()["message"]

    boom = client.get("/debug/boom")
    assert boom.status_code == 500
    assert boom.json()["error"]["code"] == "INTERNAL"
    assert "일부러" not in boom.text
    assert "ValueError" not in boom.text
