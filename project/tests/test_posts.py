"""게시글·댓글 CRUD와 공통 응답 형식."""


def _auth(client, email="mina@example.com", nickname="mina"):
    client.post(
        "/api/auth/signup",
        json={"email": email, "password": "password123", "nickname": nickname},
    )
    logged = client.post("/api/auth/login", json={"email": email, "password": "password123"})
    return logged.json()["data"]["accessToken"]


def test_health_and_request_id_and_empty_list(client):
    health = client.get("/health", headers={"X-Request-Id": "req-1"})
    assert health.status_code == 200
    assert health.json() == {"status": "ok"}
    assert health.headers["x-request-id"] == "req-1"

    listed = client.get("/api/posts")
    assert listed.status_code == 200
    assert listed.json() == {
        "data": [],
        "meta": {"page": 1, "limit": 10, "total": 0, "totalPages": 0, "q": ""},
    }


def test_missing_post_and_bad_id(client):
    missing = client.get("/api/posts/999")
    assert missing.status_code == 404
    assert missing.json()["error"]["code"] == "NOT_FOUND"

    bad = client.get("/api/posts/nope")
    assert bad.status_code == 400
    assert bad.json()["error"]["code"] == "BAD_REQUEST"


def test_create_requires_auth_and_validation(client):
    denied = client.post("/api/posts", json={"title": "제목", "body": "본문"})
    assert denied.status_code == 401
    assert denied.json()["error"]["code"] == "UNAUTHORIZED"

    token = _auth(client)
    invalid = client.post(
        "/api/posts",
        json={"title": "", "body": "본문"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert invalid.status_code == 400
    error = invalid.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "1~200자로 입력하세요." in error["fields"]["title"]


def test_create_get_search_and_camel_case(client):
    token = _auth(client)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/api/posts",
        json={"title": "첫 글", "body": "안녕하세요", "tags": ["intro"]},
        headers=headers,
    )
    assert created.status_code == 201
    assert created.headers["location"].endswith(f"/api/posts/{created.json()['data']['id']}")
    data = created.json()["data"]
    assert data["title"] == "첫 글"
    assert data["body"] == "안녕하세요"
    assert data["tags"] == ["intro"]
    assert data["author"]["nickname"] == "mina"
    assert data["commentCount"] == 0
    assert data["createdAt"].endswith("Z")
    assert "created_at" not in data
    assert "password" not in created.text

    fetched = client.get(f"/api/posts/{data['id']}")
    assert fetched.status_code == 200
    assert fetched.json()["data"]["title"] == "첫 글"

    found = client.get("/api/posts", params={"q": "안녕", "page": 1, "limit": 10})
    assert found.json()["meta"]["total"] == 1
    assert found.json()["meta"]["q"] == "안녕"

    missed = client.get("/api/posts", params={"q": "없는말"})
    assert missed.json()["meta"]["total"] == 0


def test_owner_patch_delete_and_other_user_forbidden(client):
    alice = _auth(client, "alice@example.com", "alice")
    created = client.post(
        "/api/posts",
        json={"title": "alice post", "body": "원문"},
        headers={"Authorization": f"Bearer {alice}"},
    ).json()["data"]

    bob = _auth(client, "bob@example.com", "bob")
    forbidden = client.patch(
        f"/api/posts/{created['id']}",
        json={"title": "hijack"},
        headers={"Authorization": f"Bearer {bob}"},
    )
    assert forbidden.status_code == 403
    assert forbidden.json()["error"]["code"] == "FORBIDDEN"

    updated = client.patch(
        f"/api/posts/{created['id']}",
        json={"title": "고친 글", "tags": ["edited"]},
        headers={"Authorization": f"Bearer {alice}"},
    )
    assert updated.status_code == 200
    assert updated.json()["data"]["title"] == "고친 글"
    assert updated.json()["data"]["body"] == "원문"

    deleted = client.delete(
        f"/api/posts/{created['id']}",
        headers={"Authorization": f"Bearer {alice}"},
    )
    assert deleted.status_code == 204
    assert client.get(f"/api/posts/{created['id']}").status_code == 404


def test_comments_idempotency_and_page_limit(client):
    token = _auth(client)
    headers = {"Authorization": f"Bearer {token}", "Idempotency-Key": "same-key"}
    first = client.post("/api/posts", json={"title": "한 번", "body": "본문"}, headers=headers)
    second = client.post("/api/posts", json={"title": "두 번", "body": "다른 본문"}, headers=headers)
    assert first.status_code == 201
    assert second.json()["data"]["id"] == first.json()["data"]["id"]
    assert second.json()["data"]["title"] == "한 번"

    post_id = first.json()["data"]["id"]
    comment = client.post(
        f"/api/posts/{post_id}/comments",
        json={"body": "첫 댓글"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert comment.status_code == 201
    assert comment.json()["data"]["body"] == "첫 댓글"

    listed = client.get(f"/api/posts/{post_id}/comments")
    assert listed.json()["meta"]["total"] == 1
    detail = client.get(f"/api/posts/{post_id}")
    assert detail.json()["data"]["commentCount"] == 1

    capped = client.get("/api/posts", params={"limit": 80})
    assert capped.json()["meta"]["limit"] == 50
