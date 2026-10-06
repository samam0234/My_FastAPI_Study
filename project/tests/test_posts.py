# ─────────────────────────────────────────────────────────────
# test_posts.py : 게시글 CRUD API 테스트 (조회 / 인증 필요 / 소유자 권한 검사)
# ─────────────────────────────────────────────────────────────


# 앞의 "_"가 붙은 함수는 테스트가 아니라 여러 테스트가 같이 쓰는 도우미 함수 (pytest가 실행하지 않음).
# 회원가입 → 로그인까지 한 번에 하고 access_token 문자열을 돌려준다.
def _register_and_login(client, username="alice", password="secret123"):
    client.post("/auth/register", json={"username": username, "password": password})
    response = client.post("/auth/login", data={"username": username, "password": password})
    return response.json()["access_token"]


def test_list_posts_empty(client):
    response = client.get("/posts")
    assert response.status_code == 200
    # 테스트 DB는 매번 비어 있으므로(시드 데이터 없음) 기본 페이지네이션 값과 함께 빈 목록이 나온다.
    assert response.json() == {"items": [], "total": 0, "skip": 0, "limit": 10}


def test_get_post_404(client):
    response = client.get("/posts/999")  # 존재하지 않는 id
    assert response.status_code == 404
    assert response.json()["detail"] == "post 999를 찾을 수 없습니다."


def test_create_post_requires_auth(client):
    # Authorization 헤더 없이 글 작성 시도 → 401로 막혀야 한다.
    response = client.post("/posts", json={"title": "t", "content": "c"})
    assert response.status_code == 401


def test_create_and_get_post(client):
    token = _register_and_login(client)
    # 인증 헤더: "Bearer <토큰>" 형식으로 보내야 get_current_user가 로그인 사용자를 인식한다.
    headers = {"Authorization": f"Bearer {token}"}

    response = client.post("/posts", json={"title": "hello", "content": "world"}, headers=headers)
    assert response.status_code == 201
    body = response.json()
    assert body["title"] == "hello"
    assert body["author_id"] is not None  # 작성자 id가 자동으로 채워졌는지 확인

    # 방금 만든 글을 id로 다시 조회 (인증 없이도 조회 가능)
    response = client.get(f"/posts/{body['id']}")
    assert response.status_code == 200
    assert response.json()["title"] == "hello"


def test_update_post_forbidden_for_non_owner(client):
    # alice가 글을 작성
    token_alice = _register_and_login(client, "alice", "secret123")
    created = client.post(
        "/posts",
        json={"title": "alice post", "content": "..."},
        headers={"Authorization": f"Bearer {token_alice}"},
    ).json()

    # 다른 사용자 bob이 alice의 글을 수정하려 하면 403(권한 없음)이어야 한다.
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

    # 본인 글 수정 → 200
    response = client.put(
        f"/posts/{created['id']}",
        json={"title": "after", "content": "...", "published": False},
        headers=headers,
    )
    assert response.status_code == 200
    assert response.json()["title"] == "after"

    # 본인 글 삭제 → 204 (본문 없음)
    response = client.delete(f"/posts/{created['id']}", headers=headers)
    assert response.status_code == 204

    # 삭제 후 다시 조회하면 404
    response = client.get(f"/posts/{created['id']}")
    assert response.status_code == 404
