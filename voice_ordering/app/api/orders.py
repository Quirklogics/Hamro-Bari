"""Order endpoints.

Public (anonymous requesters, CSRF protected):
    POST /api/orders/parse          speech text -> structured order (Gemini)
    POST /api/orders                validate + store a new ``pending`` request
    POST /api/orders/track          status lookup with the capability token

Administrator only (session + role ``admin``):
    GET   /api/orders               paginated, filterable list
    GET   /api/orders/summary       dashboard counters
    GET   /api/orders/products      distinct product names for filters
    GET   /api/orders/<id>          one request with history + audit trail
    PATCH /api/orders/<id>          correct details (audit recorded)
    PATCH /api/orders/<id>/approve  approve (requires confirmation)
    PATCH /api/orders/<id>/reject   reject with a mandatory reason
    PATCH /api/orders/<id>/clarification  ask the requester a question
"""
from __future__ import annotations

from datetime import date, datetime

from flask import Blueprint, current_app, jsonify, request
from flask_login import current_user

from .. import constants as C
from ..extensions import limiter
from ..extensions import db
from ..security import ApiError, admin_required, current_actor, json_body
from ..services import gemini_service, notification_service, order_service
from ..services.order_service import OrderServiceError
from ..services.validation import clean_order_payload, clean_transcript, validate_for_submission

orders_bp = Blueprint("orders", __name__)


def _ok(payload: dict | None = None, status: int = 200):
    body = {"ok": True}
    if payload:
        body.update(payload)
    return jsonify(body), status


def _limit(config_key: str):
    return lambda: current_app.config.get(config_key, "100 per minute")


def _parse_date(value: str | None, field: str) -> date | None:
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), "%Y-%m-%d").date()
    except ValueError as exc:
        raise ApiError(
            f"'{value}' is not a valid date (use YYYY-MM-DD).",
            code="invalid_filter",
            http_status=422,
            details=[{"field": field, "code": "invalid_date"}],
        ) from exc


# --- public: parse ------------------------------------------------------------
@orders_bp.post("/parse")
@limiter.limit(_limit("RATELIMIT_PARSE"))
def parse_order():
    """Turn a transcript into validated order fields. Nothing is stored."""
    data = json_body()
    text = data.get("text") or data.get("transcript")
    if not isinstance(text, str) or not text.strip():
        raise ApiError("Provide the spoken text in 'text'.", code="missing_text", http_status=422)

    max_chars = int(current_app.config["MAX_TRANSCRIPT_CHARS"])
    if len(text) > max_chars:
        raise ApiError(
            f"That message is longer than {max_chars} characters.",
            code="text_too_long",
            http_status=413,
        )

    language = data.get("language")
    defaults = data.get("defaults") if isinstance(data.get("defaults"), dict) else None
    try:
        cleaned = gemini_service.parse_order_text(text, language_hint=language, defaults=defaults)
    except gemini_service.GeminiNotConfigured as exc:
        # Honest failure: the UI offers manual entry instead of fake extraction.
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": exc.kind,
                        "message": str(exc),
                        "fallback": "manual_entry",
                    },
                }
            ),
            503,
        )

    return _ok(
        {
            "extracted": cleaned.to_dict(),
            "missing_fields": cleaned.missing,
            "ambiguities": cleaned.ambiguities,
            "transcript": cleaned.transcript or text,
            "gemini_configured": True,
        }
    )


# --- public: submit -----------------------------------------------------------
@orders_bp.post("")
@limiter.limit(_limit("RATELIMIT_SUBMIT"))
def submit_order():
    """Validate and store a new pending request for manual review."""
    data = json_body()
    payload = data.get("order") if isinstance(data.get("order"), dict) else data
    # Transcripts are sanitised and capped here too - never stored raw.
    transcript = clean_transcript(data.get("transcript"), 4000)

    cleaned = clean_order_payload(payload, require_complete=True)
    if transcript and not cleaned.transcript:
        cleaned.transcript = transcript

    problems = validate_for_submission(cleaned)
    if problems:
        return (
            jsonify(
                {
                    "ok": False,
                    "error": {
                        "code": "validation_failed",
                        "message": "Some details are missing or invalid. Please complete them.",
                        "details": problems,
                    },
                }
            ),
            422,
        )

    request_obj, raw_token, created = order_service.create_request(
        cleaned,
        transcript=transcript or cleaned.transcript,
        source=data.get("source", "voice"),
        client_request_id=data.get("client_request_id"),
    )
    if current_user.is_authenticated:
        # An administrator entering a request on someone's behalf is noted in the
        # stored snapshot (never a secret, just who typed it).
        request_obj.parsed_data = {
            **(request_obj.parsed_data or {}),
            "submitted_by_admin": current_user.username,
        }
        db.session.commit()

    return (
        _ok(
            {
                "request": request_obj.to_dict(detail=True),
                "request_code": request_obj.request_code,
                # Returned once, only to the submitting browser: the anonymous
                # requester uses it to follow the request. Never listed anywhere.
                "tracking_token": raw_token,
                "created": created,
                "duplicate": not created,
                "message": (
                    f"Request {request_obj.request_code} was submitted and is waiting for review."
                    if created
                    else f"Request {request_obj.request_code} was already submitted."
                ),
            },
            201 if created else 200,
        )
    )


# --- public: track ------------------------------------------------------------
@orders_bp.post("/track")
@limiter.limit(_limit("RATELIMIT_TRACK"))
def track_order():
    """Status view for the anonymous submitter (capability token required)."""
    data = json_body(required=False)
    token = (data.get("tracking_token") or request.args.get("token") or "").strip()
    if not token:
        raise ApiError("A tracking token is required.", code="missing_token", http_status=422)
    request_obj = order_service.find_by_tracking_token(token)
    if request_obj is None:
        raise ApiError(
            "That tracking link is not valid.", code="invalid_token", http_status=404
        )
    return _ok({"request": order_service.requester_view(request_obj)})


# --- admin: list & stats ------------------------------------------------------
@orders_bp.get("")
@admin_required
def list_orders():
    status_values = [
        value.strip()
        for raw in request.args.getlist("status")
        for value in raw.split(",")
        if value.strip()
    ]
    page = request.args.get("page", "1")
    per_page = request.args.get("per_page", str(current_app.config["DEFAULT_PAGE_SIZE"]))
    try:
        page = int(page)
        per_page = int(per_page)
    except ValueError as exc:
        raise ApiError("page and per_page must be integers.", code="invalid_filter", http_status=422) from exc

    pagination = order_service.list_requests(
        q=request.args.get("q"),
        status=status_values,
        request_type=request.args.get("request_type"),
        user_type=request.args.get("user_type"),
        product=request.args.get("product"),
        date_from=_parse_date(request.args.get("date_from"), "date_from"),
        date_to=_parse_date(request.args.get("date_to"), "date_to"),
        sort=request.args.get("sort", "newest"),
        page=page,
        per_page=per_page,
    )
    return _ok(
        {
            "items": [item.to_dict() for item in pagination.items],
            "pagination": {
                "page": pagination.page,
                "per_page": pagination.per_page,
                "pages": pagination.pages,
                "total": pagination.total,
                "has_next": pagination.has_next,
                "has_prev": pagination.has_prev,
            },
            "filters": {
                "status": status_values,
                "request_type": request.args.get("request_type"),
                "user_type": request.args.get("user_type"),
                "product": request.args.get("product"),
                "q": request.args.get("q"),
                "date_from": request.args.get("date_from"),
                "date_to": request.args.get("date_to"),
                "sort": request.args.get("sort", "newest"),
            },
        }
    )


@orders_bp.get("/summary")
@admin_required
def summary():
    counts = order_service.status_counts()
    return _ok(
        {
            "counts": counts,
            "recent": [item.to_dict() for item in order_service.recent_requests(5)],
            "unread_notifications": notification_service.unread_count(
                C.AUDIENCE_ADMIN, current_user.id
            ),
        }
    )


@orders_bp.get("/products")
@admin_required
def products():
    return _ok({"products": order_service.distinct_products()})


# --- admin: single request ----------------------------------------------------
@orders_bp.get("/<int:request_id>")
@admin_required
def get_order(request_id: int):
    request_obj = order_service.get_request(request_id)
    return _ok({"request": request_obj.to_dict(detail=True)})


@orders_bp.patch("/<int:request_id>/approve")
@admin_required
def approve_order(request_id: int):
    data = json_body(required=False)
    if data.get("confirm") is not True:
        raise ApiError(
            "Approval must be confirmed (send {\"confirm\": true}).",
            code="confirmation_required",
            http_status=422,
        )
    actor = current_actor()
    request_obj = order_service.get_request(request_id)
    order_service.approve(request_obj, actor=actor, note=data.get("note"))
    return _ok({"request": request_obj.to_dict(detail=True), "message": "Request approved."})


@orders_bp.patch("/<int:request_id>/reject")
@admin_required
def reject_order(request_id: int):
    data = json_body()
    if data.get("confirm") is not True:
        raise ApiError(
            "Rejection must be confirmed (send {\"confirm\": true}).",
            code="confirmation_required",
            http_status=422,
        )
    actor = current_actor()
    request_obj = order_service.get_request(request_id)
    order_service.reject(request_obj, actor=actor, reason=data.get("reason", ""))
    return _ok({"request": request_obj.to_dict(detail=True), "message": "Request rejected."})


@orders_bp.patch("/<int:request_id>/clarification")
@admin_required
def clarify_order(request_id: int):
    data = json_body()
    actor = current_actor()
    request_obj = order_service.get_request(request_id)
    order_service.request_clarification(
        request_obj, actor=actor, question=data.get("question") or data.get("reason") or ""
    )
    return _ok(
        {
            "request": request_obj.to_dict(detail=True),
            "message": "Clarification requested from the requester.",
        }
    )


@orders_bp.patch("/<int:request_id>")
@admin_required
def edit_order(request_id: int):
    data = json_body()
    changes = data.get("changes") if isinstance(data.get("changes"), dict) else None
    if changes is None:
        # Flat body: every key except the envelope ones is treated as a field.
        changes = {k: v for k, v in data.items() if k not in {"note", "confirm"}}
    actor = current_actor()
    request_obj = order_service.get_request(request_id)
    request_obj, audit = order_service.edit_details(
        request_obj, actor=actor, changes=changes, note=data.get("note")
    )
    return _ok(
        {
            "request": request_obj.to_dict(detail=True),
            "changes": audit,
            "message": f"{len(audit)} field(s) updated and recorded in the audit trail.",
        }
    )


# Service errors raised inside views become consistent JSON errors.
@orders_bp.errorhandler(OrderServiceError)
def _handle_service_error(error: OrderServiceError):  # noqa: ANN202
    return (
        jsonify(
            {
                "ok": False,
                "error": {"code": error.code, "message": error.message, "details": error.details},
            }
        ),
        error.http_status,
    )


@orders_bp.errorhandler(ApiError)
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
