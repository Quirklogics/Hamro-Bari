"""Administrator dashboard pages.

Server-rendered with Jinja; every action (approve / reject / clarify / edit and
notification handling) is performed through the REST API by ``admin.js`` so the
pages and any API client behave identically.
"""
from __future__ import annotations

from datetime import datetime
from functools import wraps

from flask import (
    Blueprint,
    abort,
    current_app,
    flash,
    redirect,
    render_template,
    request,
    url_for,
)
from flask_login import current_user, login_required, login_user, logout_user

from .. import constants as C
from ..extensions import db, limiter
from ..models import User, utcnow
from ..services import notification_service, order_service

admin_bp = Blueprint("admin", __name__, template_folder="../templates/admin")


def admin_page_required(view):
    """Page-level guard: signed in *and* holding the admin role."""

    @wraps(view)
    @login_required
    def wrapper(*args, **kwargs):
        if not current_user.is_admin:
            abort(403)
        return view(*args, **kwargs)

    return wrapper


def _safe_next(target: str | None) -> str:
    """Only allow same-site relative redirects."""
    if target and target.startswith("/") and not target.startswith("//"):
        return target
    return url_for("admin.dashboard")


@admin_bp.route("/login", methods=["GET", "POST"])
@limiter.limit(lambda: current_app.config.get("RATELIMIT_LOGIN", "10 per minute"), methods=["POST"])
def login():
    if current_user.is_authenticated and current_user.is_admin:
        return redirect(_safe_next(request.args.get("next")))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""
        user = User.query.filter(db.func.lower(User.username) == username.lower()).first()
        if user is None or not user.check_password(password) or not user.is_active:
            current_app.logger.warning("Failed admin page sign-in for %r", username)
            flash("Incorrect username or password.", "error")
            return render_template("admin/login.html", username=username), 401

        login_user(user, remember=bool(request.form.get("remember")), fresh=True)
        user.last_login_at = utcnow()
        db.session.commit()
        return redirect(_safe_next(request.form.get("next") or request.args.get("next")))

    return render_template("admin/login.html", username="")


@admin_bp.post("/logout")
@login_required
def logout():
    """CSRF-protected sign-out (POST only, so a link cannot log you out)."""
    username = current_user.username
    logout_user()
    flash(f"Signed out of {username}.", "success")
    return redirect(url_for("admin.login"))


@admin_bp.get("/")
@admin_page_required
def dashboard():
    counts = order_service.status_counts()
    return render_template(
        "admin/dashboard.html",
        counts=counts,
        recent=order_service.recent_requests(6),
        notifications=notification_service.list_notifications(
            audience=C.AUDIENCE_ADMIN, user_id=current_user.id, limit=6
        ),
        unread=notification_service.unread_count(C.AUDIENCE_ADMIN, current_user.id),
        active_nav="dashboard",
    )


@admin_bp.get("/requests")
@admin_page_required
def requests_page():
    args = request.args
    status_values = [s for s in args.getlist("status") if s in C.STATUSES]
    date_from = _parse_date(args.get("date_from"))
    date_to = _parse_date(args.get("date_to"))
    try:
        page = max(1, int(args.get("page", "1")))
    except ValueError:
        page = 1

    pagination = order_service.list_requests(
        q=args.get("q"),
        status=status_values,
        request_type=args.get("request_type"),
        user_type=args.get("user_type"),
        product=args.get("product"),
        date_from=date_from,
        date_to=date_to,
        sort=args.get("sort", "newest"),
        page=page,
        per_page=current_app.config["DEFAULT_PAGE_SIZE"],
    )
    return render_template(
        "admin/requests.html",
        pagination=pagination,
        filters={
            "q": args.get("q", ""),
            "status": status_values,
            "request_type": args.get("request_type", ""),
            "user_type": args.get("user_type", ""),
            "product": args.get("product", ""),
            "date_from": args.get("date_from", ""),
            "date_to": args.get("date_to", ""),
            "sort": args.get("sort", "newest"),
        },
        products=order_service.distinct_products(),
        counts=order_service.status_counts(),
        active_nav="requests",
    )


@admin_bp.get("/requests/<int:request_id>")
@admin_page_required
def request_detail(request_id: int):
    try:
        order_request = order_service.get_request(request_id)
    except order_service.OrderServiceError:
        abort(404)
    return render_template(
        "admin/request_detail.html",
        req=order_request,
        units=C.SUPPORTED_UNITS,
        unit_labels=C.UNIT_LABELS,
        active_nav="requests",
        editable=order_request.status in C.EDITABLE_STATUSES,
        transitions=C.ALLOWED_TRANSITIONS.get(order_request.status, ()),
    )


@admin_bp.get("/notifications")
@admin_page_required
def notifications_page():
    return render_template(
        "admin/notifications.html",
        items=notification_service.list_notifications(
            audience=C.AUDIENCE_ADMIN, user_id=current_user.id, limit=100
        ),
        unread=notification_service.unread_count(C.AUDIENCE_ADMIN, current_user.id),
        active_nav="notifications",
    )


def _parse_date(value: str | None):
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


__all__ = ["admin_bp"]
