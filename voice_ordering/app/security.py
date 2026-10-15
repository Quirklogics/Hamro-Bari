"""Security helpers shared by the API and the pages.

* Same-origin enforcement on state-changing requests (plus CSRF tokens).
* Security headers, including ``Permissions-Policy: microphone=(self)`` so other
  origins cannot embed these pages and ask for the microphone.
* ``admin_required`` / ``reviewer_required`` decorators that answer JSON for
  API calls and redirect for page calls.
"""
from __future__ import annotations

from functools import wraps
from urllib.parse import urlparse

from flask import current_app, jsonify, redirect, request, url_for
from flask_login import current_user
from flask_wtf.csrf import CSRFError

SAFE_METHODS = {"GET", "HEAD", "OPTIONS", "TRACE"}
API_PREFIX = "/api/"

# Endpoints that only need a valid CSRF token, no session (anonymous requesters).
PUBLIC_API_PREFIXES = (
    "/api/voice/",
    "/api/orders/parse",
    "/api/orders/submit",
    "/api/orders/track",
)


class ApiError(Exception):
    """Raised inside API views; rendered as a consistent JSON error."""

    def __init__(self, message: str, *, code: str = "bad_request", http_status: int = 400, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details or []


def wants_json() -> bool:
    return request.path.startswith(API_PREFIX) or request.accept_mimetypes.best == "application/json"


def _origin_allowed(origin: str) -> bool:
    parsed = urlparse(origin)
    if not parsed.scheme or not parsed.netloc:
        return False
    if parsed.netloc.lower() == request.host.lower():
        return True
    allowed = {o.rstrip("/").lower() for o in current_app.config.get("EXTRA_ALLOWED_ORIGINS", [])}
    return f"{parsed.scheme}://{parsed.netloc}".lower() in allowed


def register_security_hooks(app) -> None:
    @app.before_request
    def _enforce_same_origin():  # noqa: ANN202
        if request.method in SAFE_METHODS:
            return None
        origin = request.headers.get("Origin")
        if origin and not _origin_allowed(origin):
            app.logger.warning("Blocked cross-origin %s %s from %s", request.method, request.path, origin)
            if wants_json():
                return jsonify(
                    {
                        "ok": False,
                        "error": {
                            "code": "cross_origin_blocked",
                            "message": "This origin is not allowed to call the API.",
                        },
                    }
                ), 403
            return "Cross-origin request blocked.", 403
        return None

    @app.after_request
    def _security_headers(response):  # noqa: ANN202
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("X-Frame-Options", "DENY")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        response.headers.setdefault(
            "Permissions-Policy", "microphone=(self), camera=(), geolocation=()"
        )
        response.headers.setdefault(
            "Content-Security-Policy",
            "default-src 'self'; "
            "script-src 'self'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data:; "
            "media-src 'self' blob:; "
            "connect-src 'self'; "
            "font-src 'self'; "
            "frame-ancestors 'none'; "
            "base-uri 'self'; "
            "form-action 'self'",
        )
        if request.path.startswith(API_PREFIX):
            # Never let a proxy or browser cache authenticated API payloads.
            response.headers["Cache-Control"] = "no-store, private"
            response.headers.setdefault("Pragma", "no-cache")
        return response

    @app.errorhandler(CSRFError)
    def _csrf_error(error):  # noqa: ANN202
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "csrf_failed",
                        "message": "Security token missing or expired. Reload the page and try again.",
                    },
                }
            ),
            400,
        )

    @app.login_manager.unauthorized_handler
    def _unauthorized():  # noqa: ANN202
        if not wants_json():
            return redirect(url_for("admin.login", next=request.path))
        return (
            jsonify({"ok": False, "error": {"code": "unauthorized", "message": "Sign-in required."}}),
            401,
        )


def current_actor():
    """The signed-in administrator, or raise 401."""
    if not current_user.is_authenticated:
        raise ApiError("Administrator sign-in required.", code="unauthorized", http_status=401)
    return current_user


def admin_required(view):
    """Protect an API view: must be signed in with the ``admin`` role."""

    @wraps(view)
    def wrapper(*args, **kwargs):
        if not current_user.is_authenticated:
            raise ApiError("Administrator sign-in required.", code="unauthorized", http_status=401)
        if not getattr(current_user, "is_admin", False):
            raise ApiError(
                "Your account does not have permission to perform this action.",
                code="forbidden",
                http_status=403,
            )
        return view(*args, **kwargs)

    return wrapper


def json_body(*, required: bool = True) -> dict:
    """Parse and type-check a JSON body."""
    if not request.is_json:
        if required:
            raise ApiError(
                "Expected a JSON request body with Content-Type: application/json.",
                code="invalid_content_type",
                http_status=415,
            )
        return {}
    data = request.get_json(silent=True)
    if data is None:
        raise ApiError("Malformed JSON body.", code="invalid_json", http_status=400)
    if not isinstance(data, dict):
        raise ApiError("JSON body must be an object.", code="invalid_json", http_status=400)
    return data


__all__ = [
    "ApiError",
    "admin_required",
    "current_actor",
    "json_body",
    "register_security_hooks",
    "wants_json",
]
