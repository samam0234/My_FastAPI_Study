"""심화 경로: 업로드, 메일 로그, 결제 초안, OAuth URL, 문서 질의."""

from app.ai_engine import relevant_chunks
from app.config import get_settings
from app.routers.ai import reset_documents
from app.routers.integrations import reset_integrations


def _token(client):
    client.post(
        "/api/auth/signup",
        json={"email": "mina@example.com", "password": "password123", "nickname": "mina"},
    )
    logged = client.post("/api/auth/login", json={"email": "mina@example.com", "password": "password123"})
    return logged.json()["data"]["accessToken"]


def test_upload_mail_payment_and_oauth(client, tmp_path, monkeypatch):
    reset_integrations()
    monkeypatch.setenv("UPLOAD_DIR", str(tmp_path))
    get_settings.cache_clear()
    token = _token(client)
    headers = {"Authorization": f"Bearer {token}"}

    uploaded = client.post(
        "/api/uploads",
        files={"file": ("note.txt", b"hello file", "text/plain")},
        headers=headers,
    )
    assert uploaded.status_code == 201
    assert uploaded.json()["data"]["size"] == len(b"hello file")
    assert list(tmp_path.glob("*.txt"))

    denied = client.post("/api/uploads", files={"file": ("a.exe", b"x", "application/octet-stream")}, headers=headers)
    assert denied.status_code == 400

    mail = client.post(
        "/api/mail/send",
        json={"to": "mina@example.com", "subject": "안녕", "body": "본문"},
        headers=headers,
    )
    assert mail.status_code == 202
    assert mail.json()["data"]["mode"] == "log"
    assert client.get("/api/mail/outbox", headers=headers).json()["data"][0]["subject"] == "안녕"

    draft = client.post(
        "/api/payments/draft",
        json={"amount": 1200, "orderName": "스터디"},
        headers=headers,
    )
    assert draft.status_code == 201
    assert draft.json()["data"]["checkoutUrl"].startswith("https://pay.example.test/checkout/")

    oauth = client.get("/api/oauth/google")
    assert oauth.status_code == 400
    assert oauth.json()["error"]["code"] == "BAD_REQUEST"
    get_settings.cache_clear()


def test_document_ask_uses_excerpt_only(client, monkeypatch):
    reset_documents()
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    indexed = client.post(
        "/api/ai/documents",
        json={"documentId": "doc-1", "text": "FastAPI는 타입 힌트로 요청을 검증한다."},
    )
    assert indexed.status_code == 201

    answer = client.post("/api/ai/ask", json={"documentId": "doc-1", "question": "타입 힌트"})
    assert answer.status_code == 200
    body = answer.json()["data"]
    assert body["model"] == "mock"
    assert "발췌 1" in body["answer"]
    assert "FastAPI" in body["answer"]

    missing = client.post("/api/ai/ask", json={"documentId": "missing", "question": "질문"})
    assert missing.status_code == 404
    assert "인덱스를 찾을 수 없습니다" in missing.json()["error"]["message"]

    unrelated = relevant_chunks(["전혀 다른 문장"], "타입 힌트")
    assert unrelated == []

    stream = client.get("/api/ai/ask/stream", params={"documentId": "doc-1", "question": "타입"})
    assert stream.status_code == 200
    assert "data:" in stream.text
    reset_documents()


def test_websocket_accepts(client):
    with client.websocket_connect("/ws/posts") as socket:
        socket.send_text("ping")
