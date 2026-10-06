# ─────────────────────────────────────────────────────────────
# test_auth.py : 회원가입/로그인 API 테스트
#   pytest는 "test_"로 시작하는 함수를 테스트로 인식하고, assert가 거짓이면 실패로 처리한다.
#   매개변수 client는 conftest.py의 client 픽스처가 자동으로 주입된다.
# ─────────────────────────────────────────────────────────────


def test_register_duplicate_username(client):
    payload = {"username": "alice", "password": "secret123"}
    # json=: 요청 본문을 JSON으로 보낸다 (회원가입은 JSON body)
    first = client.post("/auth/register", json=payload)
    assert first.status_code == 201  # 첫 가입은 성공(201 Created)

    second = client.post("/auth/register", json=payload)
    assert second.status_code == 400  # 같은 username으로 다시 가입하면 400


def test_login_wrong_password(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    # data=: 요청 본문을 form-data로 보낸다 (로그인은 OAuth2 폼 방식이라 json이 아닌 data 사용)
    response = client.post("/auth/login", data={"username": "alice", "password": "wrong"})
    assert response.status_code == 401  # 비밀번호 불일치 → 401


def test_login_success(client):
    client.post("/auth/register", json={"username": "alice", "password": "secret123"})
    response = client.post("/auth/login", data={"username": "alice", "password": "secret123"})
    assert response.status_code == 200
    body = response.json()  # 응답 JSON을 dict로 변환
    assert body["token_type"] == "bearer"
    assert "access_token" in body  # 토큰이 응답에 들어있는지 확인
