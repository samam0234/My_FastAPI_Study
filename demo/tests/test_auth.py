"""회원가입, 로그인, 내 정보, 로그아웃."""


def test_signup_hides_password_and_duplicate_is_409(client):
    payload = {"email": "mina@example.com", "password": "password123", "nickname": "mina"}
    first = client.post("/api/auth/signup", json=payload)
    assert first.status_code == 201
    body = first.json()["data"]
    assert body["email"] == "mina@example.com"
    assert body["nickname"] == "mina"
    assert "password" not in body
    assert "hashedPassword" not in body
    assert "hashed_password" not in first.text

    second = client.post("/api/auth/signup", json=payload)
    assert second.status_code == 409
    assert second.json()["error"]["code"] == "EMAIL_TAKEN"


def test_login_wrong_password_hides_which_field_failed(client):
    client.post(
        "/api/auth/signup",
        json={"email": "mina@example.com", "password": "password123", "nickname": "mina"},
    )
    response = client.post(
        "/api/auth/login",
        json={"email": "mina@example.com", "password": "wrong-pass"},
    )
    assert response.status_code == 401
    assert response.json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_login_json_and_form_and_me_and_logout(client):
    client.post(
        "/api/auth/signup",
        json={"email": "mina@example.com", "password": "password123", "nickname": "mina"},
    )
    logged = client.post(
        "/api/auth/login",
        json={"email": "mina@example.com", "password": "password123"},
    )
    assert logged.status_code == 200
    data = logged.json()["data"]
    assert "accessToken" in data
    assert data["user"]["nickname"] == "mina"
    token = data["accessToken"]

    form = client.post(
        "/api/auth/login",
        data={"username": "mina@example.com", "password": "password123"},
    )
    assert form.status_code == 200
    assert "accessToken" in form.json()["data"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["data"]["email"] == "mina@example.com"

    gone = client.post("/api/auth/logout", headers={"Authorization": f"Bearer {token}"})
    assert gone.status_code == 204
    assert gone.content == b""

    again = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert again.status_code == 401
    assert again.json()["error"]["code"] == "UNAUTHORIZED"


def test_signup_validation_error_shape(client):
    response = client.post("/api/auth/signup", json={"email": "not-email", "password": "short", "nickname": ""})
    assert response.status_code == 400
    error = response.json()["error"]
    assert error["code"] == "VALIDATION_ERROR"
    assert "fields" in error
    assert error["requestId"]
    assert response.headers["x-request-id"] == error["requestId"]
