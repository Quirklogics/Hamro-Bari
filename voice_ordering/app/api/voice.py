"""Voice endpoints.

``POST /api/voice/transcribe`` accepts the browser recording (multipart field
``audio`` or a raw ``audio/*`` body) and returns the transcript produced by
Gemini. The audio is never written to disk and never logged; only its size and
duration of the call are recorded.
"""
from __future__ import annotations

from flask import Blueprint, current_app, jsonify, request

from .. import constants as C
from ..extensions import limiter
from ..security import ApiError
from ..services import gemini_service

voice_bp = Blueprint("voice", __name__)


def _limit(config_key: str):
    return lambda: current_app.config.get(config_key, "20 per minute")


@voice_bp.get("/status")
def voice_status():
    """Tells the UI whether AI features are available (no secrets returned)."""
    return jsonify(
        {
            "ok": True,
            "gemini_configured": gemini_service.is_configured(),
            "transcribe_model": current_app.config.get("GEMINI_TRANSCRIBE_MODEL"),
            "parse_model": current_app.config.get("GEMINI_MODEL"),
            "max_audio_bytes": int(current_app.config["MAX_AUDIO_BYTES"]),
            "max_transcript_chars": int(current_app.config["MAX_TRANSCRIPT_CHARS"]),
            "supported_languages": list(C.SUPPORTED_LANGUAGES),
        }
    )


@voice_bp.post("/transcribe")
@limiter.limit(_limit("RATELIMIT_TRANSCRIBE"))
def transcribe():
    audio_bytes: bytes | None = None
    mime_type = "audio/webm"

    if "audio" in request.files:
        upload = request.files["audio"]
        if upload.filename == "" and not upload.stream:
            raise ApiError("The uploaded audio file is empty.", code="empty_audio", http_status=400)
        audio_bytes = upload.read()
        mime_type = upload.mimetype or request.form.get("mime_type") or mime_type
    elif request.data:
        audio_bytes = request.data
        mime_type = (request.content_type or mime_type).split(";")[0]
    else:
        raise ApiError(
            "No audio received. Send a multipart field named 'audio'.",
            code="missing_audio",
            http_status=400,
        )

    max_bytes = int(current_app.config["MAX_AUDIO_BYTES"])
    if len(audio_bytes) > max_bytes:
        raise ApiError(
            f"The recording is too large ({len(audio_bytes)} bytes). Limit is {max_bytes} bytes.",
            code="audio_too_large",
            http_status=413,
        )
    if not audio_bytes:
        raise ApiError("The recording is empty.", code="empty_audio", http_status=400)

    language = request.form.get("language") or request.args.get("language")
    result = gemini_service.transcribe_audio(audio_bytes, mime_type, language_hint=language)
    return jsonify({"ok": True, **result})


@voice_bp.errorhandler(ApiError)
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


@voice_bp.errorhandler(gemini_service.GeminiNotConfigured)
def _handle_not_configured(error: gemini_service.GeminiNotConfigured):  # noqa: ANN202
    return (
        jsonify(
            {
                "ok": False,
                "error": {
                    "code": error.kind,
                    "message": str(error),
                    "fallback": "manual_entry",
                },
            }
        ),
        error.http_status,
    )
