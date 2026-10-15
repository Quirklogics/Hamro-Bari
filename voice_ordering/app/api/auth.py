"""Administrator authentication API.

Cookie-session based (Flask-Login) with CSRF protection on every state change.
The same endpoints serve the dashboard JavaScript and any API client.
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user, login_user, logout_user

from ..extensions import db, limiter
from ..models import User, utcnow
from ..security import ApiError, json_body

auth_bp = Blueprint("auth", __name__)


def _limit(config_key: str):
    return lambda: current_app.config.get(config_key, "10 per minute")


@auth_bp.post("/login")
@limiter.limit(_limit("RATELIMIT_LOGIN"))
def login():
    data = json_body()
    username = (data.get("username") or "").strip()
    password = data.get("password") or ""
    if not username or not password:
        raise ApiError(
            "Username and password are required.", code="missing_credentials", http_status=422
        )

    user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
    # Constant message for both unknown user and wrong password.
    if user is None or not user.check_password(password):
        current_app.logger.warning("Failed admin sign-in for %r", username)
        raise ApiError(
            "Incorrect username or password.", code="invalid_credentials", http_status=401
        )
    if not user.is_active:
        raise ApiError("This account is disabled.", code="account_disabled", http_status=403)

    login_user(user, remember=bool(data.get("remember")), fresh=True)
    user.last_login_at = utcnow()
    db.session.commit()
    return jsonify({"ok": True, "user": user.to_dict()})


@auth_bp.post("/logout")
def logout():
    logout_user()
    return jsonify({"ok": True, "message": "Signed out."})


@auth_bp.get("/me")
def me():
    if not current_user.is_authenticated:
        return jsonify({"ok": True, "authenticated": False, "user": None})
    return jsonify(
        {
            "ok": True,
            "authenticated": True,
            "user": current_user.to_dict(),
            "is_admin": current_user.is_admin,
        }
    )


@auth_bp.errorhandler(ApiError)
def _handle_api_error(error: ApiError):  # noqa: ANN202
    return (
        jsonify(
            {
                "ok": False,
                "error": {"code": error.code, "message": error.message, "details": error.details},
            }
        ),
        error.http_status,
    )
