"""In-app notifications: creation, read state and audience isolation."""
from __future__ import annotations

from app import constants as C
from app.models import Notification, OrderRequest

from conftest import COMPLETE_ORDER


def _submit(client, **overrides):
    payload = dict(COMPLETE_ORDER)
    payload.update(overrides)
    return client.post("/api/orders", json={"order": payload, "transcript": "test order"}).get_json()


def test_new_request_notifies_administrators_only(admin_client):
    body = _submit(admin_client)
    notifications = Notification.query.all()
    assert len(notifications) == 1
    note = notifications[0]
    assert note.audience == C.AUDIENCE_ADMIN
    assert note.event == C.EVENT_NEW_REQUEST
    assert note.channel == C.NOTIFICATION_CHANNEL_IN_APP
    assert note.is_read is False
    assert body["request_code"] in note.title

    listed = admin_client.get("/api/notifications").get_json()
    assert listed["unread_count"] == 1
    assert listed["items"][0]["request_code"] == body["request_code"]
    # The API is explicit that only in-app delivery exists.
    assert listed["channels"] == ["in_app"]


def test_marking_a_notification_read_is_scoped_to_the_admin(admin_client):
    _submit(admin_client)
    note = Notification.query.one()

    response = admin_client.patch(f"/api/notifications/{note.id}/read")
    assert response.status_code == 200
    assert response.get_json()["notification"]["is_read"] is True
    assert response.get_json()["unread_count"] == 0
    assert Notification.query.one().read_at is not None

    unread_only = admin_client.get("/api/notifications?unread_only=true").get_json()
    assert unread_only["items"] == []

    assert admin_client.patch("/api/notifications/99999/read").status_code == 404


def test_read_all_clears_the_badge(admin_client):
    for index in range(3):
        payload = dict(COMPLETE_ORDER)
        payload["requester_name"] = f"Requester {index}"
        payload["location"] = f"Ward {index}"
        admin_client.post("/api/orders", json={"order": payload})

    assert Notification.query.count() == 3
    response = admin_client.post("/api/notifications/read-all")
    assert response.status_code == 200
    assert response.get_json()["updated"] == 3
    assert Notification.query.filter_by(is_read=False).count() == 0


def test_decisions_notify_the_requester_and_admin_reads_them(admin_client):
    body = _submit(admin_client)
    request = OrderRequest.query.one()

    admin_client.patch(f"/api/orders/{request.id}/approve", json={"confirm": True})

    requester_notes = Notification.query.filter_by(audience=C.AUDIENCE_REQUESTER).all()
    assert len(requester_notes) == 1
    requester_note = requester_notes[0]
    assert requester_note.event == C.EVENT_APPROVED
    assert "approved" in requester_note.message.lower()

    tracked = admin_client.post(
        "/api/orders/track", json={"tracking_token": body["tracking_token"]}
    ).get_json()["request"]
    assert tracked["notifications"][0]["event"] == C.EVENT_APPROVED
    assert tracked["status"] == C.STATUS_APPROVED

    # Administrators cannot see the requester's in-app inbox and vice versa.
    admin_items = admin_client.get("/api/notifications").get_json()["items"]
    assert all(item["audience"] == C.AUDIENCE_ADMIN for item in admin_items)

    # Marking someone else's notification as read is refused (not an admin note).
    blocked = admin_client.patch(f"/api/notifications/{requester_note.id}/read")
    assert blocked.status_code == 403


def test_rejection_and_clarification_messages_reach_the_requester(admin_client):
    first = _submit(admin_client, requester_name="Sita")
    second = _submit(admin_client, requester_name="Hari")

    reject_id = OrderRequest.query.filter_by(requester_name="Sita").one().id
    clarify_id = OrderRequest.query.filter_by(requester_name="Hari").one().id

    admin_client.patch(
        f"/api/orders/{reject_id}/reject",
        json={"confirm": True, "reason": "Out of season this week."},
    )
    admin_client.patch(
        f"/api/orders/{clarify_id}/clarification",
        json={"question": "कति के.जी. चाहियो?"},
    )

    reject_note = Notification.query.filter_by(event=C.EVENT_REJECTED).one()
    assert "Out of season this week." in reject_note.message

    clarify_note = Notification.query.filter_by(event=C.EVENT_CLARIFICATION).one()
    assert clarify_note.message == "कति के.जी. चाहियो?"

    rejected = admin_client.post(
        "/api/orders/track", json={"tracking_token": first["tracking_token"]}
    ).get_json()["request"]
    assert rejected["status"] == C.STATUS_REJECTED

    clarified = admin_client.post(
        "/api/orders/track", json={"tracking_token": second["tracking_token"]}
    ).get_json()["request"]
    assert clarified["status"] == C.STATUS_CLARIFICATION
    assert clarified["clarification_question"] == "कति के.जी. चाहियो?"


def test_no_notification_claims_an_external_delivery(admin_client):
    _submit(admin_client)
    OrderRequest.query.one()
    admin_client.patch(
        f"/api/orders/{OrderRequest.query.one().id}/approve", json={"confirm": True}
    )

    for note in Notification.query.all():
        assert note.channel == C.NOTIFICATION_CHANNEL_IN_APP
        payload = note.to_dict()
        assert payload["channel"] == "in_app"
        assert not any(word in note.message.lower() for word in ("sms", "email sent", "push sent"))
