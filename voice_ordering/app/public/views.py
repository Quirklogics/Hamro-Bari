"""Requester facing pages: the voice ordering interface and request tracking.

Both pages are server-rendered shells; all interaction goes through the REST API
with the CSRF token rendered into a meta tag. Tracking tokens are kept in the
browser's localStorage and never embedded in a URL.
"""
from __future__ import annotations

from flask import Blueprint, current_app, render_template

from .. import constants as C
from ..services import gemini_service

public_bp = Blueprint("public", __name__)


@public_bp.get("/")
def voice_home():
    """Voice ordering screen (microphone + confirmation form)."""
    return render_template(
        "public/voice.html",
        languages=C.SUPPORTED_LANGUAGES,
        language_labels=C.LANGUAGE_LABELS,
        units=C.SUPPORTED_UNITS,
        unit_labels=C.UNIT_LABELS,
        user_types=C.USER_TYPES,
        user_type_labels=C.USER_TYPE_LABELS,
        request_types=C.REQUEST_TYPES,
        request_type_labels=C.REQUEST_TYPE_LABELS,
        fulfillment_types=C.FULFILLMENT_TYPES,
        fulfillment_labels=C.FULFILLMENT_LABELS,
        required_fields=C.REQUIRED_FIELDS,
        field_labels=C.FIELD_LABELS,
        product_aliases=sorted({v["en"] for v in C.PRODUCT_ALIASES.values()}),
        gemini_configured=gemini_service.is_configured(),
        max_audio_bytes=int(current_app.config["MAX_AUDIO_BYTES"]),
        max_transcript_chars=int(current_app.config["MAX_TRANSCRIPT_CHARS"]),
        max_content_length=int(current_app.config["MAX_CONTENT_LENGTH"]),
    )


@public_bp.get("/track")
def track_page():
    """'My requests' page: statuses fetched with the local tracking tokens."""
    return render_template("public/track.html")


__all__ = ["public_bp"]
