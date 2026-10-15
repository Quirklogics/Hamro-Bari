"""End-to-end workflow: submit, review, decide, edit, audit, track."""
from __future__ import annotations

import json

import pytest

from app import constants as C
from app.extensions import db
from app.models import Notification, OrderRequest, OrderRequestEdit, OrderStatusHistory
from app.services import order_service

from conftest import COMPLETE_ORDER


def submit(client, **overrides):
    payload = dict(COMPLETE_ORDER)
    payload.update(overrides)
    return client.post(
        "/api/orders",
        json={
            "order": payload,
            "transcript": "Mero sanga 200 kilo alu cha",
            "language": "ne-roman",
            "client_request_id": overrides.pop("client_request_id", None),
        },
    )


# --- submission ---------------------------------------------------------------
def test_submit_creates_a_pending_request_with_history_and_token(client, app):
    response = submit(client)
    assert response.status_code == 201, response.get_json()
    body = response.get_json()
    assert body["created"] is True
    assert body["request"]["status"] == C.STATUS_PENDING
    assert body["request"]["product_name"] == "Potato"
    assert body["tracking_token"]
    assert len(body["tracking_token"]) > 20

    stored = OrderRequest.query.one()
    assert stored.request_code.startswith("HB-")
    assert stored.decided_at is None  # nothing is auto-approved
    assert stored.parsed_data["source"] == "voice"
    assert stored.status_history[0].action == C.ACTION_CREATED
    # The raw token is never persisted.
    assert body["tracking_token"] != stored.tracking_token_hash
    assert stored.tracking_token_hash == order_service.hash_tracking_token(body["tracking_token"])


def test_submit_reports_missing_fields_and_stores_nothing(client):
    response = client.post(
        "/api/orders",
        json={"order": {"product_name": "alu", "quantity": 5, "unit": "kg"}},
    )
    assert response.status_code == 422
    body = response.get_json()
    assert body["error"]["code"] == "validation_failed"
    missing = {item["field"] for item in body["error"]["details"]}
    assert {"requester_name", "user_type", "request_type", "location"} <= missing
    assert OrderRequest.query.count() == 0


def test_submit_rejects_invalid_values(client):
    response = client.post(
        "/api/orders",
        json={
            "order": {
                **COMPLETE_ORDER,
                "unit": "handful",
                "quantity": 999999,
                "phone": "???",
            }
        },
    )
    assert response.status_code == 422
    invalid = {item["field"] for item in response.get_json()["error"]["details"]}
    assert {"unit", "quantity", "phone"} <= invalid


def test_idempotency_key_prevents_duplicate_requests(client):
    first = submit(client, client_request_id="attempt-123")
    second = submit(client, client_request_id="attempt-123")

    assert first.status_code == 201
    assert second.status_code == 200
    assert second.get_json()["duplicate"] is True
    assert second.get_json()["request_code"] == first.get_json()["request_code"]
    assert OrderRequest.query.count() == 1
    assert Notification.query.filter(Notification.event == C.EVENT_NEW_REQUEST).count() == 1


def test_transcripts_are_truncated_to_the_storage_limit(client):
    response = client.post(
        "/api/orders", json={"order": COMPLETE_ORDER, "transcript": "क" * 6000}
    )
    assert response.status_code == 201
    stored = OrderRequest.query.one()
    assert len(stored.transcript) == 4000


def test_client_supplied_ambiguity_flags_are_sanitised_metadata(client):
    """Ambiguity flags are advisory only: they never affect validation or status."""
    response = client.post(
        "/api/orders",
        json={
            "order": {
                **COMPLETE_ORDER,
                "ambiguities": [
                    {"field": "quantity", "reason": "approximate", "question": "Is 200 kg right?"},
                    {"field": "x" * 500, "reason": "y" * 900, "question": "z" * 900},
                    "not-an-object",
                ],
                "missing_fields": ["requester_name"],
            }
        },
    )
    assert response.status_code == 201
    stored = OrderRequest.query.one()
    assert stored.status == C.STATUS_PENDING
    # Client-claimed missing fields are recomputed from real values, not trusted.
    assert stored.missing_fields == []
    assert len(stored.ambiguities) == 1
    assert stored.ambiguities[0]["field"] == "quantity"


# --- parsing endpoint ---------------------------------------------------------
def test_parse_endpoint_reports_unconfigured_ai_with_a_fallback(client):
    response = client.post("/api/orders/parse", json={"text": "50 kilo alu chahiyo"})
    assert response.status_code == 503
    body = response.get_json()
    assert body["error"]["code"] == "gemini_not_configured"
    assert body["error"]["fallback"] == "manual_entry"


def test_parse_endpoint_validates_input(client, app):
    assert client.post("/api/orders/parse", json={}).status_code == 422
    assert client.post("/api/orders/parse", json={"text": "x" * 5000}).status_code == 413


# --- listing & filters --------------------------------------------------------
def test_listing_is_paginated_and_filterable(admin_client):
    for index in range(3):
        submit(admin_client, product_name="alu" if index else "golbheda", client_request_id=f"c-{index}")

    first = admin_client.get("/api/orders?page=1&per_page=2").get_json()
    assert len(first["items"]) == 2
    assert first["pagination"]["total"] == 3
    assert first["pagination"]["has_next"] is True

    second = admin_client.get("/api/orders?page=2&per_page=2").get_json()
    assert len(second["items"]) == 1

    filtered = admin_client.get("/api/orders?status=pending&request_type=selling").get_json()
    assert filtered["pagination"]["total"] == 3

    empty = admin_client.get("/api/orders?status=approved").get_json()
    assert empty["pagination"]["total"] == 0

    search = admin_client.get("/api/orders?q=Potato").get_json()
    assert search["pagination"]["total"] == 2

    summary = admin_client.get("/api/orders/summary").get_json()
    assert summary["counts"]["pending"] == 3
    assert len(summary["recent"]) == 3


def test_detail_includes_transcript_and_history(admin_client):
    code = submit(admin_client, client_request_id="detail-1").get_json()["request_code"]
    listed = admin_client.get("/api/orders?q=" + code).get_json()
    request_id = listed["items"][0]["id"]

    detail = admin_client.get(f"/api/orders/{request_id}").get_json()["request"]
    assert detail["transcript"] == "Mero sanga 200 kilo alu cha"
    assert detail["parsed_data"]["source"] == "voice"
    assert detail["status_history"][0]["action"] == C.ACTION_CREATED
    assert admin_client.get("/api/orders/999999").status_code == 404


# --- decisions ----------------------------------------------------------------
def _pending_id(client, **overrides):
    response = submit(client, **overrides)
    body = response.get_json()
    listed = client.get("/api/orders?q=" + body["request_code"]).get_json()
    return listed["items"][0]["id"]


def test_approve_requires_confirmation_and_is_recorded(admin_client, admin_user):
    request_id = _pending_id(admin_client, client_request_id="ap-1")

    unconfirmed = admin_client.patch(f"/api/orders/{request_id}/approve", json={})
    assert unconfirmed.status_code == 422
    assert unconfirmed.get_json()["error"]["code"] == "confirmation_required"

    response = admin_client.patch(
        f"/api/orders/{request_id}/approve", json={"confirm": True, "note": "Verified stock."}
    )
    assert response.status_code == 200, response.get_json()
    detail = response.get_json()["request"]
    assert detail["status"] == C.STATUS_APPROVED
    assert detail["decided_by"] == "admin"
    assert detail["decided_at"] is not None
    assert detail["admin_notes"] == "Verified stock."

    stored = db.session.get(OrderRequest, request_id)
    history = stored.status_history[0]
    assert history.action == C.ACTION_APPROVED
    assert history.from_status == C.STATUS_PENDING
    assert history.to_status == C.STATUS_APPROVED
    assert history.actor_label == "admin"


def test_approved_request_cannot_change_status_again(admin_client):
    request_id = _pending_id(admin_client, client_request_id="ap-2")
    admin_client.patch(f"/api/orders/{request_id}/approve", json={"confirm": True})

    again = admin_client.patch(f"/api/orders/{request_id}/approve", json={"confirm": True})
    assert again.status_code == 409
    assert again.get_json()["error"]["code"] == "invalid_transition"

    rejected = admin_client.patch(
        f"/api/orders/{request_id}/reject", json={"confirm": True, "reason": "changed my mind"}
    )
    assert rejected.status_code == 409


def test_reject_requires_a_reason(admin_client):
    request_id = _pending_id(admin_client, client_request_id="rej-1")

    no_reason = admin_client.patch(
        f"/api/orders/{request_id}/reject", json={"confirm": True, "reason": "   "}
    )
    assert no_reason.status_code == 422
    assert no_reason.get_json()["error"]["code"] == "reason_required"

    ok = admin_client.patch(
        f"/api/orders/{request_id}/reject",
        json={"confirm": True, "reason": "Quantity unavailable this cycle."},
    )
    assert ok.status_code == 200
    stored = db.session.get(OrderRequest, request_id)
    assert stored.status == C.STATUS_REJECTED
    assert stored.admin_notes == "Quantity unavailable this cycle."
    assert stored.status_history[0].reason == "Quantity unavailable this cycle."


def test_clarification_question_is_stored_and_visible_to_the_requester(admin_client):
    body = submit(admin_client, client_request_id="cl-1").get_json()
    request_id = admin_client.get("/api/orders?q=" + body["request_code"]).get_json()["items"][0]["id"]

    empty = admin_client.patch(f"/api/orders/{request_id}/clarification", json={"question": ""})
    assert empty.status_code == 422

    response = admin_client.patch(
        f"/api/orders/{request_id}/clarification",
        json={"question": "के तपाईं २५ के.जी. नाकि २५ क्रेट भन्न खोज्नुभएको हो?"},
    )
    assert response.status_code == 200
    assert response.get_json()["request"]["status"] == C.STATUS_CLARIFICATION
    assert response.get_json()["request"]["clarification_question"].startswith("के तपाईं")

    tracked = admin_client.post(
        "/api/orders/track", json={"tracking_token": body["tracking_token"]}
    ).get_json()["request"]
    assert tracked["status"] == C.STATUS_CLARIFICATION
    assert "२५ क्रेट" in tracked["clarification_question"]


# --- edits + audit ------------------------------------------------------------
def test_edit_records_a_field_level_audit_trail(admin_client):
    body = submit(
        admin_client,
        quantity=25,
        unit="crate",
        product_name="pyaj",
        client_request_id="edit-1",
    ).get_json()
    request_id = admin_client.get("/api/orders?q=" + body["request_code"]).get_json()["items"][0]["id"]

    # Sending the canonical name back unchanged must not create a noisy audit row.
    noop = admin_client.patch(
        f"/api/orders/{request_id}", json={"changes": {"product_name": "Onion"}}
    )
    assert noop.status_code == 422
    assert noop.get_json()["error"]["code"] == "no_changes"

    response = admin_client.patch(
        f"/api/orders/{request_id}",
        json={"changes": {"quantity": 25, "unit": "kg", "product_name": "Potato"}, "note": "Unit corrected"},
    )
    assert response.status_code == 200, response.get_json()
    changes = {item["field"]: item for item in response.get_json()["changes"]}
    assert set(changes) == {"unit", "product_name"}
    assert changes["unit"]["old_value"] == "crate"
    assert changes["unit"]["new_value"] == "kg"

    stored = db.session.get(OrderRequest, request_id)
    assert float(stored.quantity) == 25.0
    assert stored.unit == "kg"
    audits = OrderRequestEdit.query.filter_by(order_request_id=request_id).all()
    assert {row.field for row in audits} == {"unit", "product_name"}
    assert changes["product_name"]["old_value"] == "Onion"
    assert changes["product_name"]["new_value"] == "Potato"
    assert all(row.actor_label == "admin" for row in audits)
    assert stored.status == C.STATUS_PENDING
    assert stored.status_history[0].action == C.ACTION_EDITED


def test_edit_rejects_invalid_values_and_no_op_changes(admin_client):
    body = submit(admin_client, client_request_id="edit-2").get_json()
    request_id = admin_client.get("/api/orders?q=" + body["request_code"]).get_json()["items"][0]["id"]

    invalid = admin_client.patch(
        f"/api/orders/{request_id}", json={"changes": {"unit": "handful"}}
    )
    assert invalid.status_code == 422

    no_change = admin_client.patch(
        f"/api/orders/{request_id}", json={"changes": {"unit": COMPLETE_ORDER["unit"]}}
    )
    assert no_change.status_code == 422
    assert no_change.get_json()["error"]["code"] == "no_changes"


def test_edit_is_blocked_after_a_decision(admin_client):
    request_id = _pending_id(admin_client, client_request_id="edit-3")
    admin_client.patch(f"/api/orders/{request_id}/approve", json={"confirm": True})

    blocked = admin_client.patch(
        f"/api/orders/{request_id}", json={"changes": {"quantity": 42}}
    )
    assert blocked.status_code == 409
    assert blocked.get_json()["error"]["code"] == "not_editable"


def test_service_refuses_to_store_incomplete_requests(app):
    """Only complete requests reach the database; the rest go back to the user."""
    cleaned = order_service.clean_order_payload(
        {
            "requester_name": None,
            "user_type": "farmer",
            "request_type": "selling",
            "product_name": "alu",
            "quantity": 5,
            "unit": "kg",
            "location": None,
        }
    )
    with pytest.raises(order_service.OrderServiceError) as exc:
        order_service.create_request(cleaned, transcript="partial")
    assert exc.value.http_status == 422
    assert exc.value.code == "validation_failed"
    assert OrderRequest.query.count() == 0


def test_edit_can_clear_fields_and_is_audited(admin_client):
    body = submit(admin_client, client_request_id="clear-1").get_json()
    request_id = admin_client.get("/api/orders?q=" + body["request_code"]).get_json()["items"][0]["id"]

    response = admin_client.patch(
        f"/api/orders/{request_id}", json={"changes": {"phone": None, "expected_total": 15000}}
    )
    assert response.status_code == 200
    stored = db.session.get(OrderRequest, request_id)
    assert stored.phone is None
    assert float(stored.expected_total) == 15000.0
    assert {row.field for row in stored.edits} == {"phone", "expected_total"}


# --- tracking -----------------------------------------------------------------
def test_tracking_requires_a_valid_token(client):
    body = submit(client, client_request_id="track-1").get_json()

    ok = client.post("/api/orders/track", json={"tracking_token": body["tracking_token"]})
    assert ok.status_code == 200
    tracked = ok.get_json()["request"]
    assert tracked["request_code"] == body["request_code"]
    assert tracked["status"] == C.STATUS_PENDING
    assert tracked["history"]

    assert client.post("/api/orders/track", json={"tracking_token": "nope"}).status_code == 404
    assert client.post("/api/orders/track", json={}).status_code == 422


def test_tracking_does_not_leak_other_requests_or_tokens(client):
    first = submit(client, client_request_id="track-2").get_json()
    second = submit(client, client_request_id="track-3").get_json()

    tracked = client.post(
        "/api/orders/track", json={"tracking_token": first["tracking_token"]}
    ).get_json()["request"]
    assert tracked["request_code"] == first["request_code"]
    assert second["request_code"] not in json.dumps(tracked)
    assert second["tracking_token"] not in json.dumps(tracked)
    assert "tracking_token" not in tracked


def test_status_counts_helper(app):
    cleaned = order_service.clean_order_payload(COMPLETE_ORDER)
    order_service.create_request(cleaned, transcript="a")
    order_service.create_request(order_service.clean_order_payload(COMPLETE_ORDER), transcript="b")
    counts = order_service.status_counts()
    assert counts["pending"] == 2
    assert counts["total"] == 2


def test_history_rows_accumulate_and_are_never_deleted(app, admin_user):
    cleaned = order_service.clean_order_payload(COMPLETE_ORDER)
    request, _token, _created = order_service.create_request(cleaned, transcript="x")
    order_service.request_clarification(request, actor=admin_user, question="कति के.जी.?")
    order_service.approve(request, actor=admin_user)

    history = OrderStatusHistory.query.filter_by(order_request_id=request.id).all()
    assert len(history) == 3
    assert {row.action for row in history} == {
        C.ACTION_CREATED,
        C.ACTION_CLARIFICATION,
        C.ACTION_APPROVED,
    }
    assert db.session.get(OrderRequest, request.id).status == C.STATUS_APPROVED


def test_public_pages_render(client):
    assert client.get("/").status_code == 200
    assert client.get("/track").status_code == 200
