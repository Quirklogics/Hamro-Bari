"""Application factory for the Hamro Baari Voice Ordering System."""
from __future__ import annotations

import logging
import os
from datetime import timedelta

from flask import Flask, jsonify, render_template, request

from config import get_config

from . import constants as C
from .extensions import csrf, db, limiter, login_manager, migrate
from .security import register_security_hooks

__version__ = "1.0.0"


def create_app(config_name: str | None = None, overrides: dict | None = None) -> Flask:
    """Build the Flask app. ``overrides`` is used by tests and tooling."""
    app = Flask(
        __name__,
        template_folder="templates",
        static_folder="static",
        instance_path=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "instance"),
        instance_relative_config=False,
    )
    app.config.from_object(get_config(config_name))
    if overrides:
        app.config.update(overrides)

    _configure_logging(app)
    _init_extensions(app)
    _register_blueprints(app)
    _register_error_handlers(app)
    register_security_hooks(app)
    _register_template_helpers(app)
    _register_cli(app)

    app.logger.info(
        "Hamro Baari Voice Orders starting (env=%s, db=%s, gemini=%s)",
        app.config.get("ENV_NAME"),
        app.config["SQLALCHEMY_DATABASE_URI"].split("://", 1)[0],
        "configured" if app.config.get("GEMINI_API_KEY") else "NOT configured",
    )
    return app


def _configure_logging(app: Flask) -> None:
    if app.debug and not app.testing:
        logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")


def _init_extensions(app: Flask) -> None:
    db.init_app(app)
    migrate.init_app(app, db, directory=os.path.join(app.root_path, "..", "migrations"))
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Import models so Alembic autogenerate and db.create_all see every table.
    from . import models  # noqa: F401

    if app.config.get("SQLALCHEMY_DATABASE_URI", "").startswith("sqlite"):
        app.config.setdefault("SQLALCHEMY_ENGINE_OPTIONS", {})
        # SQLite in-memory + threads needs this; harmless otherwise.
        app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
            **app.config.get("SQLALCHEMY_ENGINE_OPTIONS", {}),
            "connect_args": {"check_same_thread": False},
        }


def _register_blueprints(app: Flask) -> None:
    from .admin.views import admin_bp
    from .api.auth import auth_bp
    from .api.notifications import notifications_bp
    from .api.orders import orders_bp
    from .api.voice import voice_bp
    from .public.views import public_bp

    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(auth_bp, url_prefix="/api/auth")
    app.register_blueprint(voice_bp, url_prefix="/api/voice")
    app.register_blueprint(orders_bp, url_prefix="/api/orders")
    app.register_blueprint(notifications_bp, url_prefix="/api/notifications")


def _register_error_handlers(app: Flask) -> None:
    from .security import ApiError
    from .services.gemini_service import GeminiError
    from .services.order_service import OrderServiceError

    def _service_error(error):  # noqa: ANN202
        return jsonify(
            {
                "ok": False,
                "error": {
                    "code": getattr(error, "code", getattr(error, "kind", "error")),
                    "message": getattr(error, "message", str(error)),
                    "details": getattr(error, "details", []),
                },
            }
        ), getattr(error, "http_status", 400)

    app.register_error_handler(ApiError, _service_error)
    app.register_error_handler(OrderServiceError, _service_error)
    app.register_error_handler(GeminiError, _service_error)

    @app.errorhandler(400)
    def bad_request(error):  # noqa: ANN001
        return _error_response("bad_request", "The request could not be understood.", 400, error)

    @app.errorhandler(401)
    def unauthorized(error):  # noqa: ANN001
        return _error_response("unauthorized", "Sign-in required.", 401, error)

    @app.errorhandler(403)
    def forbidden(error):  # noqa: ANN001
        return _error_response("forbidden", "You do not have access to this resource.", 403, error)

    @app.errorhandler(404)
    def not_found(error):  # noqa: ANN001
        if request.path.startswith("/api/"):
            return _error_response("not_found", "Resource not found.", 404, error)
        return render_template("errors/404.html"), 404

    @app.errorhandler(413)
    def payload_too_large(error):  # noqa: ANN001
        return _error_response(
            "payload_too_large",
            "The upload is too large. Record a shorter message.",
            413,
            error,
        )

    @app.errorhandler(429)
    def rate_limited(error):  # noqa: ANN001
        return _error_response(
            "rate_limited", "Too many requests. Please slow down and try again.", 429, error
        )

    @app.errorhandler(500)
    def server_error(error):  # noqa: ANN001
        app.logger.exception("Unhandled error on %s", request.path)
        return _error_response("server_error", "Something went wrong on our side.", 500, error)

    @app.errorhandler(Exception)
    def unhandled(error):  # noqa: ANN001
        # Registered class handlers above deal with the expected cases; anything
        # reaching here is a genuine bug, so tests surface it instead of a 500.
        if app.testing:
            raise error
        app.logger.exception("Unhandled error on %s", request.path)
        return _error_response("server_error", "Something went wrong on our side.", 500, error)


def _error_response(code: str, message: str, status: int, error=None):
    """JSON for API calls, readable HTML page for browser navigation."""
    if request.path.startswith("/api/") or request.accept_mimetypes.best == "application/json":
        payload = {"ok": False, "error": {"code": code, "message": message}}
        if error is not None and getattr(error, "description", None):
            payload["error"]["detail"] = str(error.description)
        return jsonify(payload), status
    return render_template("errors/error.html", code=code, message=message, status=status), status


def _register_template_helpers(app: Flask) -> None:
    @app.context_processor
    def inject_globals():  # noqa: ANN202
        from flask_login import current_user

        from .models import Notification
        from .services import gemini_service

        unread = 0
        if current_user.is_authenticated and current_user.is_admin:
            try:
                unread = (
                    Notification.query.filter(
                        Notification.audience == C.AUDIENCE_ADMIN,
                        Notification.is_read.is_(False),
                    ).count()
                )
            except Exception:  # noqa: BLE001 - pages must still render pre-migration
                unread = 0
        return {
            "C": C,
            "current_user": current_user,
            "gemini_configured": gemini_service.is_configured(),
            "admin_unread_count": unread,
            "app_name": app.config.get("APP_NAME", "Hamro Baari Voice Orders"),
        }

    @app.template_filter("nepali_number")
    def nepali_number(value):  # noqa: ANN001
        digits = str.maketrans("0123456789", "०१२३४५६७८९")
        return str(value).translate(digits)

    @app.template_filter("datetime_npt")
    def datetime_npt(value, fmt: str = "%Y-%m-%d %H:%M"):  # noqa: ANN001
        if not value:
            return "—"
        # Stored as UTC; display in Nepal time (UTC+5:45).
        return (value + timedelta(hours=5, minutes=45)).strftime(fmt)


def _register_cli(app: Flask) -> None:
    from .cli import register_cli

    register_cli(app)


__all__ = ["create_app", "__version__"]
