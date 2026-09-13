def _register_and_login(client, username="alice", password="secret123"):
    client.post("/auth/register", json={"username": username, "password": password})
    response = client.post("/auth/login", data={"username": username, "password": password})
    return response.json()["access_token"]


def test_list_posts_empty(client):
    response = client.get("/posts")
    assert response.status_code == 200
    assert response.json() == []


def test_get_post_404(client):
    response = client.get("/posts/999")
    assert response.status_code == 404
    assert response.json()["detail"] == "post 999를 찾을 수 없습니다."


def test_create_post_requires_auth(client):
    response = client.post("/posts", json={"title": "t", "content": "c"})
    assert response.status_code == 401


def test_create_and_get_post(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/posts", json={"title": "hello", "content": "world"}, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "hello"
    assert body["author_id"] is not None

    response = client.get(f"/posts/{body['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "hello"


def test_update_post_forbidden_for_non_owner(client):
    token_alice = _register_and_login(client, "alice", "secret123")
    created = client.post(
        "/posts",
        json={"title": "alice post", "content": "..."},
        headers={"Authorization": f"Bearer {token_alice}"},
    ).json()

    token_bob = _register_and_login(client, "bob", "hunter2")
    response = client.put(
        f"/posts/{created['id']}",
        json={"title": "hijack", "content": "..."},
        headers={"Authorization": f"Bearer {token_bob}"},
    )
    assert response.status_code == 403


def test_owner_can_update_and_delete(client):
    token = _register_and_login(client)
    headers = {"Authorization": f"Bearer {token}"}
    created = client.post(
        "/posts", json={"title": "before", "content": "..."}, headers=headers
    ).json()

    response = client.put(
        f"/posts/{created['id']}",
        json={"title": "after", "content": "...", "published": False},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "after"

    response = client.delete(f"/posts/{created['id']}", headers=headers)
    assert response.status_code == 204

    response = client.get(f"/posts/{created['id']}")
    assert response.status_code == 404
