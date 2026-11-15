import time
from sqlalchemy import select
from backend.models import AuthSession, User

ACCOUNT = {"login": "listener", "password": "Strong123!"}


def sign_in(client):
    assert client.post("/api/register", json=ACCOUNT).status_code == 201
    result = client.post("/api/login", json=ACCOUNT)
    assert result.status_code == 200
    return result


def test_register_and_duplicate(client, db_factory):
    result = client.post("/api/register", json={**ACCOUNT, "email": "listener@example.com", "is_music_account": True})
    assert result.status_code == 201
    assert result.json()["user"]["clearance_level"] == 1
    with db_factory() as db:
        user = db.scalar(select(User))
        assert user.password_hash.startswith("$argon2id$")
        assert user.is_music_account
    assert client.post("/api/register", json=ACCOUNT).status_code == 409
    assert client.post("/api/register", json={**ACCOUNT, "login": "LISTENER"}).status_code == 409


def test_validation_and_privilege_injection(client):
    for payload in ({**ACCOUNT, "password": "weak"}, {**ACCOUNT, "email": "bad"},
                    {**ACCOUNT, "clearance_level": 3}, {**ACCOUNT, "password": "Strong123 "}):
        result = client.post("/api/register", json=payload)
        assert result.status_code == 422
        assert '"input"' not in result.text


def test_login_me_logout_and_cookie(client, db_factory):
    result = sign_in(client)
    cookie = result.headers["set-cookie"]
    assert "HttpOnly" in cookie and "SameSite=lax" in cookie
    token = client.cookies.get("musicaccess_session")
    with db_factory() as db:
        assert db.scalar(select(AuthSession)).token_hash != token
    assert client.get("/api/me").json()["user"]["login"] == "listener"
    assert client.post("/api/logout").status_code == 403
    assert client.post("/api/logout", headers={"X-CSRF-Token": result.json()["csrf_token"]}).status_code == 204
    assert client.get("/api/me").status_code == 401
    client.cookies.set("musicaccess_session", token)
    assert client.get("/api/me").status_code == 401


def test_invalid_login_and_expired_session(client, db_factory):
    sign_in(client)
    assert client.post("/api/login", json={**ACCOUNT, "password": "wrong"}).status_code == 401
    assert client.post("/api/login", json={**ACCOUNT, "login": "missing"}).status_code == 401
    with db_factory() as db:
        db.scalar(select(AuthSession)).expires_at = int(time.time()) - 1
        db.commit()
    assert client.get("/api/me").status_code == 401


def test_delete_account_revokes_all_sessions(client, db_factory):
    sign_in(client)
    old = client.cookies.get("musicaccess_session")
    client.cookies.clear()
    second = client.post("/api/login", json=ACCOUNT)
    headers = {"X-CSRF-Token": second.json()["csrf_token"]}
    assert client.request("DELETE", "/api/me", json={"password": ACCOUNT["password"]}).status_code == 403
    assert client.request("DELETE", "/api/me", headers=headers, json={"password": "wrong"}).status_code == 400
    assert client.request("DELETE", "/api/me", headers=headers, json={"password": ACCOUNT["password"]}).status_code == 204
    client.cookies.set("musicaccess_session", old)
    assert client.get("/api/me").status_code == 401
    with db_factory() as db:
        assert db.scalar(select(User)) is None
        assert db.scalar(select(AuthSession)) is None


def test_cross_site_mutation_blocked(client):
    assert client.post("/api/register", json=ACCOUNT, headers={"X-MusicAccess": ""}).status_code == 403
    assert client.post("/api/login", json=ACCOUNT, headers={"Sec-Fetch-Site": "cross-site"}).status_code == 403
