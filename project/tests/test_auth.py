def test_register_duplicate_username(client):
    payload = {"username": "alice", "password": "secret123"}
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400


def test_login_wrong_password(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    response = client.post("/auth/login", data={"username": "alice", "password": "wrong"})
    assert response.status_code == 401


def test_login_success(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    response = client.post("/auth/login", data={"username": "alice", "password": "secret123"})
    assert response.status_code == 200
    body = response.json()
    assert body["token_type"] == "bearer"
    assert "access_token" in body
