"""In-app notifications.

Only **in-app** delivery exists. No SMS, email or push provider is integrated,
so nothing in this module (or anywhere else) claims a message was delivered to a
phone or inbox. Requester notifications are tied to the request and shown on the
tracking page that is reachable with the submitter's capability token.
"""
from __future__ import annotations

from .. import constants as C
from ..extensions import db
from ..models import Notification, OrderRequest, User, utcnow


def _describe(request: OrderRequest) -> str:
    product = request.product_name or "unspecified product"
    return f"{request.request_code}: {request.quantity_display} {product}".strip()


def notify_admins(
    request: OrderRequest,
    event: str,
    title: str,
    message: str,
    *,
    recipient_user_id: int | None = None,
) -> Notification:
    """Queue an in-app notification for administrators."""
    notification = Notification(
        audience=C.AUDIENCE_ADMIN,
        recipient_user_id=recipient_user_id,
        order_request_id=request.id if request else None,
        event=event,
        title=title,
        message=message,
        channel=C.NOTIFICATION_CHANNEL_IN_APP,
    )
    db.session.add(notification)
    return notification


def notify_requester(request: OrderRequest, event: str, title: str, message: str) -> Notification:
    """Queue an in-app notification for the person who submitted the request."""
    notification = Notification(
        audience=C.AUDIENCE_REQUESTER,
        recipient_user_id=None,  # anonymous submitter: reached via tracking token
        order_request_id=request.id,
        event=event,
        title=title,
        message=message,
        channel=C.NOTIFICATION_CHANNEL_IN_APP,
    )
    db.session.add(notification)
    return notification


def notify_new_request(request: OrderRequest) -> Notification:
    return notify_admins(
        request,
        C.EVENT_NEW_REQUEST,
        f"New {request.request_type or 'order'} request {request.request_code}",
        f"{_describe(request)} submitted by {request.requester_name or 'unknown'}.",
    )


def notify_decision(request: OrderRequest, event: str, title: str, message: str) -> Notification:
    return notify_requester(request, event, title, message)


# --- queries ------------------------------------------------------------------
def unread_count(audience: str = C.AUDIENCE_ADMIN, user_id: int | None = None) -> int:
    query = Notification.query.filter(
        Notification.audience == audience, Notification.is_read.is_(False)
    )
    if user_id is not None:
        query = query.filter(
            (Notification.recipient_user_id == user_id)
            | (Notification.recipient_user_id.is_(None))
        )
    return query.count()


def list_notifications(
    *,
    audience: str = C.AUDIENCE_ADMIN,
    user_id: int | None = None,
    unread_only: bool = False,
    limit: int = 50,
) -> list[Notification]:
    query = Notification.query.filter(Notification.audience == audience)
    if user_id is not None:
        query = query.filter(
            (Notification.recipient_user_id == user_id)
            | (Notification.recipient_user_id.is_(None))
        )
    if unread_only:
        query = query.filter(Notification.is_read.is_(False))
    return query.order_by(Notification.created_at.desc(), Notification.id.desc()).limit(limit).all()


def notifications_for_request(request_id: int, *, audience: str = C.AUDIENCE_REQUESTER) -> list[Notification]:
    return (
        Notification.query.filter(
            Notification.order_request_id == request_id,
            Notification.audience == audience,
        )
        .order_by(Notification.created_at.desc())
        .all()
    )


def mark_as_read(notification: Notification, *, actor: User | None = None) -> Notification:
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = utcnow()
        db.session.commit()
    return notification


def mark_all_as_read(*, audience: str = C.AUDIENCE_ADMIN, user_id: int | None = None) -> int:
    query = Notification.query.filter(
        Notification.audience == audience, Notification.is_read.is_(False)
    )
    if user_id is not None:
        query = query.filter(
            (Notification.recipient_user_id == user_id)
            | (Notification.recipient_user_id.is_(None))
        )
    updated = 0
    for notification in query.all():
        notification.is_read = True
        notification.read_at = utcnow()
        updated += 1
    if updated:
        db.session.commit()
    return updated


__all__ = [
    "notify_admins",
    "notify_requester",
    "notify_new_request",
    "notify_decision",
    "unread_count",
    "list_notifications",
    "notifications_for_request",
    "mark_as_read",
    "mark_all_as_read",
]
