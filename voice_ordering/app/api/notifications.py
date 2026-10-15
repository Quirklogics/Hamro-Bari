"""Notification endpoints (administrator only).

Only in-app notifications exist. Nothing here sends an SMS, email or push
message, and no response claims that it did.
"""
from __future__ import annotations

from flask import Blueprint, jsonify, request
from flask_login import current_user

from .. import constants as C
from ..extensions import db
from ..models import Notification
from ..security import ApiError, admin_required
from ..services import notification_service

notifications_bp = Blueprint("notifications", __name__)


@notifications_bp.get("")
@admin_required
def list_notifications():
    unread_only = request.args.get("unread_only", "").lower() in ("1", "true", "yes")
    try:
        limit = min(int(request.args.get("limit", "50")), 200)
    except ValueError as exc:
        raise ApiError("limit must be an integer.", code="invalid_filter", http_status=422) from exc

    items = notification_service.list_notifications(
        audience=C.AUDIENCE_ADMIN,
        user_id=current_user.id,
        unread_only=unread_only,
        limit=limit,
    )
    return jsonify(
        {
            "ok": True,
            "items": [item.to_dict() for item in items],
            "unread_count": notification_service.unread_count(C.AUDIENCE_ADMIN, current_user.id),
            "channels": [C.NOTIFICATION_CHANNEL_IN_APP],
        }
    )


@notifications_bp.patch("/<int:notification_id>/read")
@admin_required
def mark_read(notification_id: int):
    notification = db.session.get(Notification, notification_id)
    if notification is None:
        raise ApiError("Notification not found.", code="not_found", http_status=404)
    if notification.audience != C.AUDIENCE_ADMIN:
        raise ApiError(
            "This notification does not belong to an administrator.",
            code="forbidden",
            http_status=403,
        )
    if notification.recipient_user_id not in (None, current_user.id):
        raise ApiError("You cannot modify this notification.", code="forbidden", http_status=403)

    notification_service.mark_as_read(notification, actor=current_user)
    return jsonify(
        {
            "ok": True,
            "notification": notification.to_dict(),
            "unread_count": notification_service.unread_count(C.AUDIENCE_ADMIN, current_user.id),
        }
    )


@notifications_bp.post("/read-all")
@admin_required
def mark_all_read():
    updated = notification_service.mark_all_as_read(
        audience=C.AUDIENCE_ADMIN, user_id=current_user.id
    )
    return jsonify({"ok": True, "updated": updated, "unread_count": 0})


@notifications_bp.errorhandler(ApiError)
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
