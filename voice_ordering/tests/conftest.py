"""Shared pytest fixtures.

The tests never call the real Gemini API: the service module is mocked, and the
credential-free behaviour (503 + manual fallback) is asserted explicitly.
"""
from __future__ import annotations

import os
import re
import sys

import pytest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from app import create_app  # noqa: E402
from app.extensions import db as _db  # noqa: E402
from app.models import User  # noqa: E402

ADMIN_PASSWORD = "TestPassword123!"
REVIEWER_PASSWORD = "ReviewerPassword123!"


def _build_app(tmp_path, **overrides):
    config = {
        "SQLALCHEMY_DATABASE_URI": f"sqlite:///{(tmp_path / 'test.db').as_posix()}",
        "SQLALCHEMY_ENGINE_OPTIONS": {"connect_args": {"check_same_thread": False}},
        "GEMINI_API_KEY": "",
        "WTF_CSRF_ENABLED": False,
        "RATELIMIT_ENABLED": False,
        "TESTING": True,
        "SERVER_NAME": None,
    }
    config.update(overrides)
    application = create_app("testing", overrides=config)
    with application.app_context():
        _db.create_all()
        yield application
        _db.session.remove()
        _db.drop_all()


@pytest.fixture()
def app(tmp_path):
    yield from _build_app(tmp_path)


@pytest.fixture()
def csrf_app(tmp_path):
    """App with CSRF protection enabled, to prove tokens are enforced."""
    yield from _build_app(tmp_path, WTF_CSRF_ENABLED=True)


@pytest.fixture()
def client(app):
    return app.test_client()


@pytest.fixture()
def csrf_client(csrf_app):
    return csrf_app.test_client()


@pytest.fixture()
def admin_user(app):
    user = User(username="admin", full_name="Test Admin", role="admin")
    user.set_password(ADMIN_PASSWORD)
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture()
def reviewer_user(app):
    user = User(username="reviewer", full_name="Test Reviewer", role="reviewer")
    user.set_password(REVIEWER_PASSWORD)
    _db.session.add(user)
    _db.session.commit()
    return user


@pytest.fixture()
def admin_client(client, admin_user):
    response = client.post(
        "/api/auth/login", json={"username": "admin", "password": ADMIN_PASSWORD}
    )
    assert response.status_code == 200, response.get_json()
    return client


def csrf_token_from(client, path: str = "/admin/login") -> str:
    """Scrape the CSRF token out of a rendered page."""
    response = client.get(path)
    match = re.search(r'name="csrf_token" value="([^"]+)"', response.get_data(as_text=True))
    assert match, f"no CSRF token on {path}"
    return match.group(1)


COMPLETE_ORDER = {
    "requester_name": "Ram Bahadur Shrestha",
    "phone": "9845012345",
    "user_type": "farmer",
    "request_type": "selling",
    "product_name": "alu",
    "quantity": 200,
    "unit": "kilo",
    "location": "Panchkhal, Kavre",
    "fulfillment_type": "delivery",
}
