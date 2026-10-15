"""Voice endpoint + Gemini SDK usage (no network calls)."""
from __future__ import annotations

import io
import json
from types import SimpleNamespace

import pytest

from app.services import gemini_service

WAV_BYTES = b"RIFF$\x00\x00\x00WAVEfmt \x10\x00\x00\x00" + b"\x00" * 64


class _FakeModels:
    def __init__(self, recorder, text):
        self._recorder = recorder
        self._text = text

    def generate_content(self, **kwargs):
        self._recorder.append(kwargs)
        return SimpleNamespace(text=self._text)


class _FakeClient:
    def __init__(self, recorder, text, **kwargs):
        self.init_kwargs = kwargs
        self.models = _FakeModels(recorder, text)


@pytest.fixture()
def gemini_app(app):
    app.config["GEMINI_API_KEY"] = "test-key-not-real"
    return app


def test_transcribe_endpoint_uses_the_sdk_correctly(gemini_app, monkeypatch):
    """Verifies our google-genai usage: model id, inline audio part, JSON mode."""
    from google.genai import types

    calls: list[dict] = []
    text = json.dumps({"transcript": "मलाई २५ किलो प्याज चाहियो", "language": "ne", "confidence": 0.9})

    def fake_client_factory(**kwargs):
        return _FakeClient(calls, text, **kwargs)

    monkeypatch.setattr("google.genai.Client", fake_client_factory)

    client = gemini_app.test_client()
    response = client.post(
        "/api/voice/transcribe",
        data={"audio": (io.BytesIO(WAV_BYTES), "order.wav", "audio/wav"), "language": "ne"},
        content_type="multipart/form-data",
    )
    assert response.status_code == 200, response.get_json()
    payload = response.get_json()
    assert payload["transcript"].startswith("मलाई")
    assert payload["language"] == "ne"
    assert payload["model"] == gemini_app.config["GEMINI_TRANSCRIBE_MODEL"]

    assert len(calls) == 1
    sent = calls[0]
    assert sent["model"] == gemini_app.config["GEMINI_TRANSCRIBE_MODEL"]
    assert sent["config"].response_mime_type == "application/json"

    audio_part = sent["contents"][0]
    assert isinstance(audio_part, types.Part)
    assert audio_part.inline_data.mime_type == "audio/wav"
    assert audio_part.inline_data.data == WAV_BYTES


def test_transcribe_requires_an_api_key(app):
    client = app.test_client()
    response = client.post(
        "/api/voice/transcribe",
        data={"audio": (io.BytesIO(WAV_BYTES), "order.wav", "audio/wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 503
    body = response.get_json()
    assert body["error"]["code"] == "gemini_not_configured"
    assert body["error"]["fallback"] == "manual_entry"


def test_transcribe_rejects_missing_empty_and_oversized_audio(gemini_app):
    client = gemini_app.test_client()

    missing = client.post("/api/voice/transcribe", data={}, content_type="multipart/form-data")
    assert missing.status_code == 400
    assert missing.get_json()["error"]["code"] == "missing_audio"

    empty = client.post(
        "/api/voice/transcribe",
        data={"audio": (io.BytesIO(b""), "order.wav", "audio/wav")},
        content_type="multipart/form-data",
    )
    assert empty.status_code == 400

    gemini_app.config["MAX_AUDIO_BYTES"] = 1024
    oversized = client.post(
        "/api/voice/transcribe",
        data={"audio": (io.BytesIO(b"\x00" * 4096), "order.wav", "audio/wav")},
        content_type="multipart/form-data",
    )
    assert oversized.status_code == 413
    assert oversized.get_json()["error"]["code"] == "audio_too_large"


def test_transcribe_rejects_unsupported_format(gemini_app):
    client = gemini_app.test_client()
    response = client.post(
        "/api/voice/transcribe",
        data={"audio": (io.BytesIO(WAV_BYTES), "notes.txt", "text/plain")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 415
    assert response.get_json()["error"]["code"] == "unsupported_audio"


def test_transcribe_surfaces_empty_recording(gemini_app, monkeypatch):
    def stub_generate(model, contents, schema, system_instruction):
        return SimpleNamespace(text=json.dumps({"transcript": "", "language": "unknown"}))

    monkeypatch.setattr(gemini_service, "_generate", stub_generate)
    client = gemini_app.test_client()
    response = client.post(
        "/api/voice/transcribe",
        data={"audio": (io.BytesIO(WAV_BYTES), "order.wav", "audio/wav")},
        content_type="multipart/form-data",
    )
    assert response.status_code == 502
    assert response.get_json()["error"]["code"] == "gemini_invalid_response"


def test_voice_status_reports_configuration_without_secrets(app):
    client = app.test_client()
    response = client.get("/api/voice/status")
    assert response.status_code == 200
    body = response.get_json()
    assert body["gemini_configured"] is False
    assert "GEMINI_API_KEY" not in json.dumps(body)
    assert "api_key" not in json.dumps(body).lower()
