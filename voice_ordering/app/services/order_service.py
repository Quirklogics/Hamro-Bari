"""Order request workflow.

All writes live here so the API routes stay thin and every status change is
atomic: status + history + notification + audit row are committed in a single
transaction, or none of them are.

Guarantees
----------
* a request is always created as ``pending`` - nothing auto-approves;
* status transitions follow :data:`app.constants.ALLOWED_TRANSITIONS` and are
  rejected with 409 when they are not allowed;
* an ``client_request_id`` (idempotency key) can never produce a second row;
* every administrator correction is recorded field by field.
"""
from __future__ import annotations

import hashlib
import secrets
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Iterable

from sqlalchemy import func, or_
from sqlalchemy.exc import IntegrityError

from .. import constants as C
from ..extensions import db
from ..models import OrderRequest, OrderRequestEdit, OrderStatusHistory, User, utcnow
from . import notification_service
from .validation import (
    EDITABLE_FIELDS,
    CleanedOrder,
    clean_order_payload,
    compute_missing_fields,
    validate_for_submission,
)

PAGE_SIZE_DEFAULT = 20
PAGE_SIZE_MAX = 100


class OrderServiceError(Exception):
    """Domain error carrying an HTTP status for the API layer."""

    def __init__(self, message: str, *, code: str = "error", http_status: int = 400, details=None):
        super().__init__(message)
        self.message = message
        self.code = code
        self.http_status = http_status
        self.details = details or []


# --- tokens & codes -----------------------------------------------------------
def generate_tracking_token() -> tuple[str, str]:
    """Return ``(raw_token, sha256_hash)`` for an anonymous submitter."""
    raw = secrets.token_urlsafe(32)
    return raw, hash_tracking_token(raw)


def hash_tracking_token(raw_token: str) -> str:
    return hashlib.sha256((raw_token or "").encode("utf-8")).hexdigest()


def find_by_tracking_token(raw_token: str) -> OrderRequest | None:
    if not raw_token or len(raw_token) > 200:
        return None
    return OrderRequest.query.filter(
        OrderRequest.tracking_token_hash == hash_tracking_token(raw_token)
    ).first()


def _next_request_code() -> str:
    highest = db.session.query(func.max(OrderRequest.id)).scalar() or 0
    return f"HB-{date.today().year}-{highest + 1:05d}"


# --- creation -----------------------------------------------------------------
def create_request(
    cleaned: CleanedOrder,
    *,
    transcript: str | None = None,
    source: str = "voice",
    client_request_id: str | None = None,
    parsed_data: dict | None = None,
) -> tuple[OrderRequest, str | None, bool]:
    """Validate and store a new pending request.

    Returns ``(request, raw_tracking_token, created)``. When the client retries
    with the same idempotency key the existing row is returned and
    ``created`` is ``False``.
    """
    client_request_id = (client_request_id or "").strip() or None
    if client_request_id and len(client_request_id) > 64:
        raise OrderServiceError(
            "client_request_id must be at most 64 characters.",
            code="invalid_idempotency_key",
            http_status=422,
        )

    if client_request_id:
        existing = OrderRequest.query.filter(
            OrderRequest.client_request_id == client_request_id
        ).first()
        if existing:
            return existing, None, False

    problems = validate_for_submission(cleaned)
    if problems:
        raise OrderServiceError(
            "This request cannot be submitted yet: some details are missing or invalid.",
            code="validation_failed",
            http_status=422,
            details=problems,
        )

    raw_token, token_hash = generate_tracking_token()
    values = cleaned.values
    request_kwargs = dict(
        tracking_token_hash=token_hash,
        client_request_id=client_request_id,
        requester_name=values.get("requester_name"),
        phone=values.get("phone"),
        user_type=values.get("user_type"),
        request_type=values.get("request_type"),
        product_name=values.get("product_name"),
        quantity=values.get("quantity"),
        unit=values.get("unit"),
        price_per_unit=values.get("price_per_unit"),
        expected_total=values.get("expected_total"),
        location=values.get("location"),
        fulfillment_type=values.get("fulfillment_type"),
        requested_date=values.get("requested_date"),
        requested_date_text=values.get("requested_date_text"),
        transcript=transcript if transcript is not None else cleaned.transcript,
        parsed_data=_parsed_snapshot(cleaned, source=source, extra=parsed_data),
        ai_confidence=cleaned.confidence,
        missing_fields=compute_missing_fields(values),
        ambiguities=cleaned.ambiguities,
        language=cleaned.language,
        status=C.STATUS_PENDING,
    )

    # Each attempt builds a fresh instance: a rolled back savepoint expunges the
    # object, and the unique request_code / client_request_id may collide when two
    # people submit at the same moment.
    request: OrderRequest | None = None
    last_error: IntegrityError | None = None
    for _attempt in range(8):
        candidate = OrderRequest(request_code=_next_request_code(), **request_kwargs)
        try:
            with db.session.begin_nested():
                db.session.add(candidate)
                db.session.flush()
            request = candidate
            break
        except IntegrityError as exc:
            last_error = exc
            if client_request_id:
                existing = OrderRequest.query.filter(
                    OrderRequest.client_request_id == client_request_id
                ).first()
                if existing:
                    return existing, None, False
    if request is None:  # pragma: no cover - extremely unlikely
        db.session.rollback()
        raise OrderServiceError(
            "Could not allocate a request number. Please try again.",
            code="code_generation_failed",
            http_status=500,
        ) from last_error

    try:
        db.session.add(
            OrderStatusHistory(
                order_request_id=request.id,
                from_status=None,
                to_status=C.STATUS_PENDING,
                action=C.ACTION_CREATED,
                actor_label="system",
                reason=f"Request submitted via {source}",
                context={
                    "language": cleaned.language,
                    "ai_confidence": cleaned.confidence,
                    "missing_fields": compute_missing_fields(cleaned.values),
                },
            )
        )
        notification_service.notify_new_request(request)
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise

    return request, raw_token, True


def _parsed_snapshot(cleaned: CleanedOrder, *, source: str, extra: dict | None = None) -> dict:
    """JSON snapshot of what was extracted, kept for the administrator."""
    snapshot = {
        "source": source,
        "values": {
            key: (str(value) if isinstance(value, Decimal) else value)
            for key, value in cleaned.values.items()
        },
        "field_errors": cleaned.errors,
        "ambiguities": cleaned.ambiguities,
        "confidence": cleaned.confidence,
        "language": cleaned.language,
    }
    # Never store an API key or raw payload blobs.
    runtime = {k: v for k, v in (cleaned.raw or {}).items() if k not in {"api_key"}}
    if runtime:
        snapshot["model_meta"] = runtime
    if extra:
        snapshot.update(extra)
    return snapshot


# --- reads --------------------------------------------------------------------
def get_request(request_id: int) -> OrderRequest:
    request = db.session.get(OrderRequest, int(request_id))
    if request is None:
        raise OrderServiceError("Request not found.", code="not_found", http_status=404)
    return request


def list_requests(
    *,
    q: str | None = None,
    status: Iterable[str] | None = None,
    request_type: str | None = None,
    user_type: str | None = None,
    product: str | None = None,
    date_from: date | None = None,
    date_to: date | None = None,
    sort: str = "newest",
    page: int = 1,
    per_page: int = PAGE_SIZE_DEFAULT,
):
    """Filtered, paginated query. Returns a Flask-SQLAlchemy Pagination object."""
    query = OrderRequest.query

    if q:
        needle = f"%{q.strip().lower()}%"
        query = query.filter(
            or_(
                func.lower(OrderRequest.request_code).like(needle),
                func.lower(func.coalesce(OrderRequest.requester_name, "")).like(needle),
                func.lower(func.coalesce(OrderRequest.phone, "")).like(needle),
                func.lower(func.coalesce(OrderRequest.product_name, "")).like(needle),
                func.lower(func.coalesce(OrderRequest.location, "")).like(needle),
                func.lower(func.coalesce(OrderRequest.transcript, "")).like(needle),
            )
        )
    if status:
        wanted = [s for s in status if s in C.STATUSES]
        if wanted:
            query = query.filter(OrderRequest.status.in_(wanted))
    if request_type in C.REQUEST_TYPES:
        query = query.filter(OrderRequest.request_type == request_type)
    if user_type in C.USER_TYPES:
        query = query.filter(OrderRequest.user_type == user_type)
    if product:
        query = query.filter(func.lower(func.coalesce(OrderRequest.product_name, "")).like(f"%{product.strip().lower()}%"))
    if date_from:
        query = query.filter(OrderRequest.created_at >= datetime.combine(date_from, datetime.min.time()))
    if date_to:
        query = query.filter(OrderRequest.created_at <= datetime.combine(date_to, datetime.max.time()))

    order = {
        "oldest": OrderRequest.created_at.asc(),
        "quantity": OrderRequest.quantity.desc(),
        "product": func.lower(func.coalesce(OrderRequest.product_name, "")).asc(),
        "status": OrderRequest.status.asc(),
    }.get(sort, OrderRequest.created_at.desc())

    per_page = max(1, min(int(per_page or PAGE_SIZE_DEFAULT), PAGE_SIZE_MAX))
    return query.order_by(order, OrderRequest.id.desc()).paginate(
        page=max(1, int(page or 1)), per_page=per_page, error_out=False
    )


def status_counts() -> dict[str, int]:
    rows = db.session.query(OrderRequest.status, func.count(OrderRequest.id)).group_by(OrderRequest.status).all()
    counts = {status: 0 for status in C.STATUSES}
    for status, total in rows:
        counts[status] = int(total)
    counts["total"] = sum(counts[status] for status in C.STATUSES)
    return counts


def recent_requests(limit: int = 5) -> list[OrderRequest]:
    return (
        OrderRequest.query.order_by(OrderRequest.created_at.desc(), OrderRequest.id.desc())
        .limit(max(1, limit))
        .all()
    )


def distinct_products(limit: int = 50) -> list[str]:
    rows = (
        db.session.query(OrderRequest.product_name)
        .filter(OrderRequest.product_name.isnot(None))
        .distinct()
        .order_by(func.lower(OrderRequest.product_name).asc())
        .limit(limit)
        .all()
    )
    return [row[0] for row in rows if row[0]]


# --- transitions --------------------------------------------------------------
def _actor_label(actor: User | None) -> str:
    if actor is None:
        return "system"
    return f"{actor.username}"


def _record_history(
    request: OrderRequest,
    *,
    from_status: str | None,
    to_status: str,
    action: str,
    actor: User | None,
    reason: str | None = None,
    context: dict | None = None,
) -> OrderStatusHistory:
    """Append an immutable history row (``from_status`` is the previous state)."""
    entry = OrderStatusHistory(
        order_request_id=request.id,
        from_status=from_status,
        to_status=to_status,
        action=action,
        actor_id=actor.id if actor else None,
        actor_label=_actor_label(actor),
        reason=reason,
        context=context,
    )
    db.session.add(entry)
    return entry


def _ensure_transition(request: OrderRequest, to_status: str) -> None:
    allowed = C.ALLOWED_TRANSITIONS.get(request.status, ())
    if to_status not in allowed:
        if not allowed:
            raise OrderServiceError(
                f"This request is already {C.STATUS_LABELS[request.status]['en'].lower()} and "
                "cannot be changed again. Submit a new request instead.",
                code="invalid_transition",
                http_status=409,
            )
        raise OrderServiceError(
            f"Cannot move a {C.STATUS_LABELS[request.status]['en'].lower()} request to "
            f"{C.STATUS_LABELS[to_status]['en'].lower()}.",
            code="invalid_transition",
            http_status=409,
        )


def approve(request: OrderRequest, *, actor: User, note: str | None = None) -> OrderRequest:
    _ensure_transition(request, C.STATUS_APPROVED)
    note = (note or "").strip() or None
    previous = request.status
    try:
        request.status = C.STATUS_APPROVED
        request.decided_at = utcnow()
        request.decided_by_id = actor.id
        if note:
            request.admin_notes = note[:2000]
        _record_history(
            request,
            from_status=previous,
            to_status=C.STATUS_APPROVED,
            action=C.ACTION_APPROVED,
            actor=actor,
            reason=note,
            context={"reviewed_from": previous},
        )
        notification_service.notify_decision(
            request,
            C.EVENT_APPROVED,
            f"Request {request.request_code} approved",
            f"Your request for {request.quantity_display} of {request.product_name or 'produce'} "
            f"was approved by the Hamro Baari team."
            + (f" Note: {note}" if note else ""),
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return request


def reject(request: OrderRequest, *, actor: User, reason: str) -> OrderRequest:
    reason = (reason or "").strip()
    if not reason:
        raise OrderServiceError(
            "A reason is required to reject a request.",
            code="reason_required",
            http_status=422,
        )
    if len(reason) > 2000:
        raise OrderServiceError("The rejection reason is too long.", code="reason_too_long", http_status=422)
    _ensure_transition(request, C.STATUS_REJECTED)
    previous = request.status
    try:
        request.status = C.STATUS_REJECTED
        request.decided_at = utcnow()
        request.decided_by_id = actor.id
        request.admin_notes = reason
        _record_history(
            request,
            from_status=previous,
            to_status=C.STATUS_REJECTED,
            action=C.ACTION_REJECTED,
            actor=actor,
            reason=reason,
        )
        notification_service.notify_decision(
            request,
            C.EVENT_REJECTED,
            f"Request {request.request_code} rejected",
            f"Your request was rejected. Reason: {reason}",
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return request


def request_clarification(request: OrderRequest, *, actor: User, question: str) -> OrderRequest:
    question = (question or "").strip()
    if not question:
        raise OrderServiceError(
            "A clarification question is required.",
            code="question_required",
            http_status=422,
        )
    if len(question) > 1000:
        raise OrderServiceError("The question is too long.", code="question_too_long", http_status=422)
    _ensure_transition(request, C.STATUS_CLARIFICATION)
    previous = request.status
    try:
        request.status = C.STATUS_CLARIFICATION
        request.admin_notes = question
        _record_history(
            request,
            from_status=previous,
            to_status=C.STATUS_CLARIFICATION,
            action=C.ACTION_CLARIFICATION,
            actor=actor,
            reason=question,
            context={"missing_fields": request.missing_fields or []},
        )
        notification_service.notify_decision(
            request,
            C.EVENT_CLARIFICATION,
            f"Clarification needed for {request.request_code}",
            question,
        )
        db.session.commit()
    except Exception:
        db.session.rollback()
        raise
    return request


def _serialise(field_name: str, value: Any) -> str | None:
    if value is None:
        return None
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, (date, datetime)):
        return value.isoformat()
    return str(value)


def edit_details(
    request: OrderRequest,
    *,
    actor: User,
    changes: dict,
    note: str | None = None,
) -> tuple[OrderRequest, list[dict]]:
    """Correct request details, recording an audit row per changed field."""
    if request.status not in C.EDITABLE_STATUSES:
        raise OrderServiceError(
            f"{C.STATUS_LABELS[request.status]['en']} requests can no longer be edited.",
            code="not_editable",
            http_status=409,
        )
    if not isinstance(changes, dict) or not changes:
        raise OrderServiceError("No changes were supplied.", code="empty_changes", http_status=422)

    allowed = {k: v for k, v in changes.items() if k in EDITABLE_FIELDS}
    if not allowed:
        raise OrderServiceError(
            "None of the supplied fields can be edited.",
            code="no_editable_fields",
            http_status=422,
            details=[{"field": k, "code": "not_editable"} for k in changes],
        )

    admin_notes = allowed.pop("admin_notes", None)
    cleaned = clean_order_payload(allowed)
    if cleaned.errors:
        raise OrderServiceError(
            "Some edited values are invalid.",
            code="validation_failed",
            http_status=422,
            details=[{"field": f, "code": "invalid", "message": m} for f, m in cleaned.errors.items()],
        )

    audit: list[dict] = []
    try:
        for field_name, new_value in cleaned.values.items():
            if field_name not in allowed:
                continue
            old_value = getattr(request, field_name)
            if _serialise(field_name, old_value) == _serialise(field_name, new_value):
                continue
            setattr(request, field_name, new_value)
            db.session.add(
                OrderRequestEdit(
                    order_request_id=request.id,
                    field=field_name,
                    old_value=_serialise(field_name, old_value),
                    new_value=_serialise(field_name, new_value),
                    actor_id=actor.id,
                    actor_label=_actor_label(actor),
                )
            )
            audit.append(
                {
                    "field": field_name,
                    "old_value": _serialise(field_name, old_value),
                    "new_value": _serialise(field_name, new_value),
                }
            )

        if admin_notes is not None:
            admin_notes = str(admin_notes).strip()[:2000] or None
            if admin_notes != request.admin_notes:
                db.session.add(
                    OrderRequestEdit(
                        order_request_id=request.id,
                        field="admin_notes",
                        old_value=request.admin_notes,
                        new_value=admin_notes,
                        actor_id=actor.id,
                        actor_label=_actor_label(actor),
                    )
                )
                audit.append(
                    {
                        "field": "admin_notes",
                        "old_value": request.admin_notes,
                        "new_value": admin_notes,
                    }
                )
                request.admin_notes = admin_notes

        if not audit:
            db.session.rollback()
            raise OrderServiceError("Nothing changed.", code="no_changes", http_status=422)

        # Edited values may have resolved (or created) missing required fields.
        values = {name: getattr(request, name) for name in C.REQUIRED_FIELDS}
        request.missing_fields = compute_missing_fields(values)
        _record_history(
            request,
            from_status=request.status,
            to_status=request.status,
            action=C.ACTION_EDITED,
            actor=actor,
            reason=(note or "").strip() or "Details corrected by administrator",
            context={"changes": audit},
        )
        notification_service.notify_requester(
            request,
            C.EVENT_UPDATED,
            f"Request {request.request_code} was updated",
            "An administrator corrected some details on your request: "
            + ", ".join(sorted({entry["field"] for entry in audit})),
        )
        db.session.commit()
    except OrderServiceError:
        raise
    except Exception:
        db.session.rollback()
        raise
    return request, audit


# --- requester-facing view ----------------------------------------------------
def requester_view(request: OrderRequest) -> dict:
    """Status payload for the anonymous submitter's tracking page."""
    return {
        "request_code": request.request_code,
        "status": request.status,
        "status_label": request.status_label,
        "product_name": request.product_name,
        "quantity_display": request.quantity_display,
        "requester_name": request.requester_name,
        "request_type": request.request_type,
        "user_type": request.user_type,
        "location": request.location,
        "created_at": request.created_at.isoformat() if request.created_at else None,
        "updated_at": request.updated_at.isoformat() if request.updated_at else None,
        "clarification_question": request.open_clarification,
        "missing_fields": request.missing_fields or [],
        "notifications": [
            n.to_dict()
            for n in notification_service.notifications_for_request(
                request.id, audience=C.AUDIENCE_REQUESTER
            )
        ],
        "history": [
            {
                "action": entry.action,
                "to_status": entry.to_status,
                "reason": entry.reason,
                "created_at": entry.created_at.isoformat() if entry.created_at else None,
            }
            for entry in reversed(request.status_history)
        ],
    }


__all__ = [
    "OrderServiceError",
    "approve",
    "create_request",
    "distinct_products",
    "edit_details",
    "find_by_tracking_token",
    "generate_tracking_token",
    "get_request",
    "hash_tracking_token",
    "list_requests",
    "recent_requests",
    "reject",
    "request_clarification",
    "requester_view",
    "status_counts",
]
