"""SQLAlchemy models for the voice ordering system.

Tables
------
``users``                 administrators (the only accounts in the system)
``order_requests``        every buying / selling request, pending review
``order_status_history``  immutable audit trail of status changes
``order_request_edits``   field level audit trail of administrator corrections
``notifications``         in-app notifications for admins and requesters
"""
from datetime import date, datetime, timezone

from flask_login import UserMixin
from sqlalchemy import CheckConstraint, Index
from werkzeug.security import check_password_hash, generate_password_hash

from . import constants as C
from .extensions import db, login_manager


def utcnow() -> datetime:
    """Naive UTC timestamp (stored identically on SQLite and PostgreSQL)."""
    return datetime.now(timezone.utc).replace(tzinfo=None)


def _in_list(column: str, values) -> str:
    joined = ", ".join(f"'{v}'" for v in values)
    return f"{column} IN ({joined})"


class User(UserMixin, db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False, index=True)
    full_name = db.Column(db.String(120), nullable=True)
    email = db.Column(db.String(160), nullable=True)
    password_hash = db.Column(db.String(255), nullable=False)
    role = db.Column(db.String(20), nullable=False, default="admin", server_default="admin")
    is_active_flag = db.Column("is_active", db.Boolean, nullable=False, default=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow)
    last_login_at = db.Column(db.DateTime, nullable=True)

    decisions = db.relationship("OrderRequest", back_populates="decided_by", lazy="select")

    __table_args__ = (
        CheckConstraint(_in_list("role", ("admin", "reviewer")), name="ck_users_role"),
    )

    # -- password helpers ---------------------------------------------------
    def set_password(self, raw_password: str) -> None:
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password: str) -> bool:
        if not self.password_hash or not raw_password:
            return False
        return check_password_hash(self.password_hash, raw_password)

    @property
    def is_active(self) -> bool:  # Flask-Login contract
        return bool(self.is_active_flag)

    @property
    def is_admin(self) -> bool:
        return self.role == "admin"

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "role": self.role,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<User {self.username} ({self.role})>"


@login_manager.user_loader
def load_user(user_id: str):
    try:
        return db.session.get(User, int(user_id))
    except (TypeError, ValueError):
        return None


class OrderRequest(db.Model):
    __tablename__ = "order_requests"

    id = db.Column(db.Integer, primary_key=True)
    request_code = db.Column(db.String(24), unique=True, nullable=False, index=True)
    # Idempotency: the browser generates this once per submission attempt and
    # reuses it on retry, so a flaky connection cannot create duplicates.
    client_request_id = db.Column(db.String(64), unique=True, nullable=True, index=True)
    # Capability token: sha256 of the token handed to the submitter so they can
    # follow their request without an account. Never returned by list APIs.
    tracking_token_hash = db.Column(db.String(64), unique=True, nullable=False, index=True)

    requester_name = db.Column(db.String(120), nullable=True)
    phone = db.Column(db.String(20), nullable=True, index=True)
    user_type = db.Column(db.String(20), nullable=True)
    request_type = db.Column(db.String(20), nullable=True)

    product_name = db.Column(db.String(120), nullable=True, index=True)
    quantity = db.Column(db.Numeric(12, 3), nullable=True)
    unit = db.Column(db.String(20), nullable=True)
    price_per_unit = db.Column(db.Numeric(12, 2), nullable=True)
    expected_total = db.Column(db.Numeric(14, 2), nullable=True)

    location = db.Column(db.String(200), nullable=True)
    fulfillment_type = db.Column(db.String(20), nullable=True)
    requested_date = db.Column(db.Date, nullable=True)
    requested_date_text = db.Column(db.String(120), nullable=True)

    transcript = db.Column(db.Text, nullable=True)
    parsed_data = db.Column(db.JSON, nullable=True)
    ai_confidence = db.Column(db.Float, nullable=True)
    missing_fields = db.Column(db.JSON, nullable=True)
    ambiguities = db.Column(db.JSON, nullable=True)
    language = db.Column(db.String(20), nullable=True)

    status = db.Column(db.String(30), nullable=False, default=C.STATUS_PENDING, index=True)
    admin_notes = db.Column(db.Text, nullable=True)
    decided_at = db.Column(db.DateTime, nullable=True)
    decided_by_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)
    updated_at = db.Column(db.DateTime, nullable=False, default=utcnow, onupdate=utcnow)

    decided_by = db.relationship("User", back_populates="decisions")
    status_history = db.relationship(
        "OrderStatusHistory",
        back_populates="order_request",
        cascade="all, delete-orphan",
        order_by="OrderStatusHistory.created_at.desc(), OrderStatusHistory.id.desc()",
        lazy="select",
    )
    edits = db.relationship(
        "OrderRequestEdit",
        back_populates="order_request",
        cascade="all, delete-orphan",
        order_by="OrderRequestEdit.created_at.desc()",
        lazy="select",
    )
    notifications = db.relationship(
        "Notification",
        back_populates="order_request",
        cascade="all, delete-orphan",
        lazy="select",
    )

    __table_args__ = (
        CheckConstraint(_in_list("status", C.STATUSES), name="ck_order_requests_status"),
        CheckConstraint(
            "user_type IS NULL OR " + _in_list("user_type", C.USER_TYPES),
            name="ck_order_requests_user_type",
        ),
        CheckConstraint(
            "request_type IS NULL OR " + _in_list("request_type", C.REQUEST_TYPES),
            name="ck_order_requests_request_type",
        ),
        CheckConstraint(
            "fulfillment_type IS NULL OR " + _in_list("fulfillment_type", C.FULFILLMENT_TYPES),
            name="ck_order_requests_fulfillment",
        ),
        CheckConstraint("quantity IS NULL OR quantity > 0", name="ck_order_requests_quantity"),
        CheckConstraint(
            "price_per_unit IS NULL OR price_per_unit > 0",
            name="ck_order_requests_price",
        ),
        Index("ix_order_requests_status_created", "status", "created_at"),
        Index("ix_order_requests_type_product", "request_type", "product_name"),
    )

    # -- derived helpers ----------------------------------------------------
    @property
    def quantity_display(self) -> str:
        if self.quantity is None:
            return "—"
        value = float(self.quantity)
        text = f"{value:,.3f}".rstrip("0").rstrip(".") if value % 1 else f"{int(value):,}"
        return f"{text} {C.UNIT_LABELS.get(self.unit or '', {}).get('en', self.unit or '')}".strip()

    @property
    def status_label(self) -> dict:
        return C.STATUS_LABELS.get(self.status, {"ne": self.status, "en": self.status, "tone": "info"})

    @property
    def open_clarification(self) -> str | None:
        """Latest clarification question that the requester still has to answer."""
        if self.status != C.STATUS_CLARIFICATION:
            return None
        for entry in self.status_history:
            if entry.action == C.ACTION_CLARIFICATION and entry.reason:
                return entry.reason
        return None

    def to_dict(self, *, detail: bool = False) -> dict:
        data = {
            "id": self.id,
            "request_code": self.request_code,
            "requester_name": self.requester_name,
            "phone": self.phone,
            "user_type": self.user_type,
            "request_type": self.request_type,
            "product_name": self.product_name,
            "quantity": float(self.quantity) if self.quantity is not None else None,
            "unit": self.unit,
            "quantity_display": self.quantity_display,
            "price_per_unit": float(self.price_per_unit) if self.price_per_unit is not None else None,
            "expected_total": float(self.expected_total) if self.expected_total is not None else None,
            "location": self.location,
            "fulfillment_type": self.fulfillment_type,
            "requested_date": self.requested_date.isoformat() if self.requested_date else None,
            "requested_date_text": self.requested_date_text,
            "language": self.language,
            "status": self.status,
            "status_label": self.status_label,
            "ai_confidence": self.ai_confidence,
            "missing_fields": self.missing_fields or [],
            "ambiguities": self.ambiguities or [],
            "admin_notes": self.admin_notes,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "decided_at": self.decided_at.isoformat() if self.decided_at else None,
            "decided_by": self.decided_by.username if self.decided_by else None,
        }
        if detail:
            data.update(
                {
                    "transcript": self.transcript,
                    "parsed_data": self.parsed_data,
                    "clarification_question": self.open_clarification,
                    "status_history": [h.to_dict() for h in self.status_history],
                    "edits": [e.to_dict() for e in self.edits],
                }
            )
        return data

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<OrderRequest {self.request_code} {self.status}>"


class OrderStatusHistory(db.Model):
    __tablename__ = "order_status_history"

    id = db.Column(db.Integer, primary_key=True)
    order_request_id = db.Column(
        db.Integer,
        db.ForeignKey("order_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    from_status = db.Column(db.String(30), nullable=True)
    to_status = db.Column(db.String(30), nullable=False)
    action = db.Column(db.String(40), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_label = db.Column(db.String(120), nullable=False, default="system")
    reason = db.Column(db.Text, nullable=True)
    context = db.Column(db.JSON, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    order_request = db.relationship("OrderRequest", back_populates="status_history")
    actor = db.relationship("User", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "from_status": self.from_status,
            "to_status": self.to_status,
            "action": self.action,
            "actor": self.actor_label,
            "reason": self.reason,
            "context": self.context,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }

    def __repr__(self) -> str:  # pragma: no cover - debug helper
        return f"<OrderStatusHistory {self.action} {self.from_status}->{self.to_status}>"


class OrderRequestEdit(db.Model):
    """Field-level audit record for administrator corrections."""

    __tablename__ = "order_request_edits"

    id = db.Column(db.Integer, primary_key=True)
    order_request_id = db.Column(
        db.Integer,
        db.ForeignKey("order_requests.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    field = db.Column(db.String(60), nullable=False)
    old_value = db.Column(db.Text, nullable=True)
    new_value = db.Column(db.Text, nullable=True)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    actor_label = db.Column(db.String(120), nullable=False, default="system")
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    order_request = db.relationship("OrderRequest", back_populates="edits")
    actor = db.relationship("User", lazy="select")

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "field": self.field,
            "old_value": self.old_value,
            "new_value": self.new_value,
            "actor": self.actor_label,
            "created_at": self.created_at.isoformat() if self.created_at else None,
        }


class Notification(db.Model):
    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    audience = db.Column(db.String(20), nullable=False, index=True)  # admin | requester
    recipient_user_id = db.Column(
        db.Integer, db.ForeignKey("users.id", ondelete="CASCADE"), nullable=True, index=True
    )
    order_request_id = db.Column(
        db.Integer, db.ForeignKey("order_requests.id", ondelete="CASCADE"), nullable=True, index=True
    )
    event = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(200), nullable=False)
    message = db.Column(db.Text, nullable=False)
    # Only in-app notifications exist. No SMS / email / push provider is wired
    # up, so nothing here claims an external delivery.
    channel = db.Column(db.String(20), nullable=False, default=C.NOTIFICATION_CHANNEL_IN_APP)
    is_read = db.Column(db.Boolean, nullable=False, default=False, index=True)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, nullable=False, default=utcnow, index=True)

    recipient = db.relationship("User", lazy="select")
    order_request = db.relationship("OrderRequest", back_populates="notifications")

    __table_args__ = (
        CheckConstraint(_in_list("audience", (C.AUDIENCE_ADMIN, C.AUDIENCE_REQUESTER)), name="ck_notifications_audience"),
        CheckConstraint(_in_list("channel", (C.NOTIFICATION_CHANNEL_IN_APP,)), name="ck_notifications_channel"),
        Index("ix_notifications_audience_unread", "audience", "is_read", "created_at"),
    )

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "audience": self.audience,
            "event": self.event,
            "title": self.title,
            "message": self.message,
            "channel": self.channel,
            "is_read": self.is_read,
            "read_at": self.read_at.isoformat() if self.read_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "order_request_id": self.order_request_id,
            "request_code": self.order_request.request_code if self.order_request else None,
        }


__all__ = [
    "User",
    "OrderRequest",
    "OrderStatusHistory",
    "OrderRequestEdit",
    "Notification",
    "utcnow",
]
