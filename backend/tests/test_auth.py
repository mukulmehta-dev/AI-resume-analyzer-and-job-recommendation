from backend.app.models.user import User, UserRole
from backend.app.core.security import hash_password
from backend.app.db.seed import seed_admin
from backend.app.core.config import settings


def test_register_and_login_flow(client):
    reg_payload = {
        "name": "Jane Tester",
        "email": "jane@example.com",
        "password": "strongpassword123"
    }
    reg_res = client.post("/api/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["email"] == "jane@example.com"
    assert reg_data["role"] == "user"
    assert "access_token" in reg_res.cookies

    me_res = client.get("/api/auth/me")
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "jane@example.com"

    logout_res = client.post("/api/auth/logout")
    assert logout_res.status_code == 200

    login_payload = {
        "email": "jane@example.com",
        "password": "strongpassword123"
    }
    login_res = client.post("/api/auth/login", json=login_payload)
    assert login_res.status_code == 200
    assert "access_token" in login_res.cookies

    bad_login = client.post("/api/auth/login", json={"email": "jane@example.com", "password": "wrong"})
    assert bad_login.status_code == 401


def test_unauthenticated_me_returns_401(client):
    client.cookies.clear()
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    assert res.json()["detail"] == "Not authenticated"


def test_deactivated_user_cannot_login(client, db_session):
    user = User(
        name="Deactivated Person",
        email="inactive@example.com",
        password_hash=hash_password("password123"),
        role=UserRole.user,
        is_active=False
    )
    db_session.add(user)
    db_session.commit()

    login_res = client.post("/api/auth/login", json={"email": "inactive@example.com", "password": "password123"})
    assert login_res.status_code == 403
    assert "deactivated" in login_res.json()["detail"].lower()


def test_duplicate_email_returns_400(client):
    payload = {
        "name": "Alice Duplicate",
        "email": "alice_dup@example.com",
        "password": "securepassword123"
    }
    res1 = client.post("/api/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/auth/register", json=payload)
    assert res2.status_code == 400
    assert "already registered" in res2.json()["detail"].lower()


def test_short_password_returns_422(client):
    payload = {
        "name": "Short Password",
        "email": "short_pw@example.com",
        "password": "short"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_password_over_72_bytes_returns_422(client):
    payload = {
        "name": "Long Password",
        "email": "long_pw@example.com",
        "password": "a" * 73
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_invalid_email_returns_422(client):
    payload = {
        "name": "Invalid Email",
        "email": "not-an-email-address",
        "password": "securepassword123"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_name_too_short_returns_422(client):
    payload = {
        "name": "A",
        "email": "valid_email@example.com",
        "password": "securepassword123"
    }
    res = client.post("/api/auth/register", json=payload)
    assert res.status_code == 422


def test_wrong_password_returns_401(client):
    payload = {
        "name": "Bob Password",
        "email": "bob_pw@example.com",
        "password": "correctpassword123"
    }
    reg = client.post("/api/auth/register", json=payload)
    assert reg.status_code == 201

    res = client.post("/api/auth/login", json={"email": "bob_pw@example.com", "password": "wrongpassword999"})
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_logout_clears_the_cookie(client):
    payload = {
        "name": "Logout Tester",
        "email": "logout_test@example.com",
        "password": "logoutpassword123"
    }
    reg = client.post("/api/auth/register", json=payload)
    assert reg.status_code == 201
    assert "access_token" in reg.cookies

    res = client.post("/api/auth/logout")
    assert res.status_code == 200
    token_val = res.cookies.get("access_token", "")
    assert token_val == '""' or token_val == "" or res.headers.get("set-cookie", "").find("access_token=;") != -1 or "Max-Age=0" in res.headers.get("set-cookie", "")


def test_admin_seed_creates_one_admin_only(db_session):
    settings.ADMIN_EMAIL = "admin_seed@example.com"
    settings.ADMIN_PASSWORD = "superadminpassword123"

    seed_admin(db_session)
    seed_admin(db_session)
    seed_admin(db_session)

    admin_count = db_session.query(User).filter(User.role == UserRole.admin).count()
    assert admin_count == 1
    admin_user = db_session.query(User).filter(User.email == "admin_seed@example.com").first()
    assert admin_user is not None
    assert admin_user.role == UserRole.admin
