"""Authentication, authorisation, CSRF, origin checks and security headers."""
from __future__ import annotations

import pytest

from app.extensions import db
from app.models import User

from conftest import ADMIN_PASSWORD, REVIEWER_PASSWORD, csrf_token_from

ADMIN_ENDPOINTS = [
    ("get", "/api/orders"),
    ("get", "/api/orders/summary"),
    ("get", "/api/orders/products"),
    ("get", "/api/notifications"),
    ("patch", "/api/orders/1/approve"),
    ("patch", "/api/orders/1/reject"),
    ("patch", "/api/orders/1/clarification"),
    ("patch", "/api/orders/1"),
]


@pytest.mark.parametrize("method,path", ADMIN_ENDPOINTS)
def test_admin_endpoints_require_sign_in(client, method, path):
    response = getattr(client, method)(path, json={"confirm": True})
    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "unauthorized"


def test_non_admin_role_is_forbidden(reviewer_user, client):
    client.post("/api/auth/login", json={"username": "reviewer", "password": REVIEWER_PASSWORD})
    response = client.get("/api/orders")
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "forbidden"


def test_admin_pages_redirect_to_login(client):
    response = client.get("/admin/")
    assert response.status_code == 302
    assert "/admin/login" in response.headers["Location"]


def test_login_rejects_bad_credentials_without_leaking_which_part_failed(client, admin_user):
    wrong_password = client.post("/api/auth/login", json={"username": "admin", "password": "nope"})
    unknown_user = client.post("/api/auth/login", json={"username": "ghost", "password": "nope"})
    assert wrong_password.status_code == unknown_user.status_code == 401
    assert (
        wrong_password.get_json()["error"]["message"]
        == unknown_user.get_json()["error"]["message"]
    )


def test_login_and_logout_cycle(client, admin_user):
    logged_in = client.post(
        "/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD}
    )
    assert logged_in.status_code == 200
    assert logged_in.get_json()["user"]["role"] == "admin"

    me = client.get("/api/auth/me").get_json()
    assert me["authenticated"] is True

    client.post("/api/auth/logout")
    assert client.get("/api/auth/me").get_json()["authenticated"] is False
    assert client.get("/api/orders").status_code == 401


def test_disabled_account_cannot_sign_in(app, client):
    user = User(username="retired", role="admin", is_active_flag=False)
    user.set_password(ADMIN_PASSWORD)
    db.session.add(user)
    db.session.commit()

    response = client.post(
        "/api/auth/login", json={"username": "retired", "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 403
    assert response.get_json()["error"]["code"] == "account_disabled"


def test_password_is_hashed_not_stored_in_clear(app, admin_user):
    assert admin_user.password_hash != ADMIN_PASSWORD
    assert admin_user.password_hash.startswith(("pbkdf2:", "scrypt:"))
    assert admin_user.check_password(ADMIN_PASSWORD) is True
    assert admin_user.check_password("wrong") is False


def test_csrf_token_is_required_for_mutations(csrf_client):
    blocked = csrf_client.post(
        "/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD}
    )
    assert blocked.status_code == 400
    assert blocked.get_json()["error"]["code"] == "csrf_failed"

    token = csrf_token_from(csrf_client)
    allowed = csrf_client.post(
        "/api/auth/login",
        json={"username": "admin", "password": ADMIN_PASSWORD},
        headers={"X-CSRFToken": token},
    )
    assert allowed.status_code in (200, 401)  # no admin seeded here: credentials path reached

    unsigned = csrf_client.post(
        "/api/orders",
        json={"order": {}},
    )
    assert unsigned.status_code == 400


def test_cross_origin_posts_are_blocked(client):
    blocked = client.post(
        "/api/orders",
        json={"order": {}},
        headers={"Origin": "https://evil.example"},
    )
    assert blocked.status_code == 403
    assert blocked.get_json()["error"]["code"] == "cross_origin_blocked"

    same_origin = client.post(
        "/api/orders",
        json={"order": {}},
        headers={"Origin": "http://localhost"},
    )
    assert same_origin.status_code == 422  # reached validation, origin accepted


def test_security_headers_and_api_no_store(client):
    page = client.get("/")
    assert page.status_code == 200
    assert page.headers["X-Frame-Options"] == "DENY"
    assert "microphone=(self)" in page.headers["Permissions-Policy"]
    assert "script-src 'self'" in page.headers["Content-Security-Policy"]

    api = client.get("/api/voice/status")
    assert api.headers["Cache-Control"] == "no-store, private"


def test_api_errors_use_a_consistent_json_shape(client):
    response = client.get("/api/orders")
    body = response.get_json()
    assert body["ok"] is False
    assert set(body["error"]) >= {"code", "message"}
    assert set(response.headers["Content-Type"].split(";")[0].split("/")) == {"application", "json"}


def test_unknown_api_route_returns_json_404(client):
    response = client.get("/api/does-not-exist")
    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "not_found"


def test_no_secrets_are_exposed_through_pages(admin_client):
    for path in ["/", "/admin/", "/admin/login"]:
        html = admin_client.get(path).get_data(as_text=True)
        assert "AIza" not in html  # Google API keys start with AIza
        assert "GEMINI_API_KEY=" not in html
        assert "SECRET_KEY=" not in html
