"""Gemini order parsing: schema adherence, untrusted output, failure mapping."""
from __future__ import annotations

import json
from types import SimpleNamespace

import pytest

from app.services import gemini_service
from app.services.gemini_service import (
    GeminiInvalidResponse,
    GeminiNotConfigured,
    GeminiTimeout,
    GeminiUnavailable,
)


class FakeResponse:
    def __init__(self, text):
        self.text = text


def stub_generate(monkeypatch, payload, calls=None):
    """Replace the network call; return a payload dict or raw string."""
    def _generate(model, contents, schema, system_instruction):
        if calls is not None:
            calls.append(
                {
                    "model": model,
                    "contents": contents,
                    "schema": schema,
                    "system_instruction": system_instruction,
                }
            )
        text = payload if isinstance(payload, str) else json.dumps(payload, ensure_ascii=False)
        return FakeResponse(text)

    monkeypatch.setattr(gemini_service, "_generate", _generate)


@pytest.fixture()
def gemini_app(app):
    app.config["GEMINI_API_KEY"] = "test-key-not-real"
    return app


def test_parsing_without_api_key_is_reported_not_faked(app):
    assert gemini_service.is_configured() is False
    with pytest.raises(GeminiNotConfigured):
        gemini_service.parse_order_text("50 kg alu chahiyo")


def test_successful_extraction_fills_canonical_fields(gemini_app, monkeypatch):
    stub_generate(
        monkeypatch,
        {
            "language": "ne-roman",
            "user_type": "customer",
            "request_type": "buying",
            "requester_name": "Sita Karki",
            "phone": "9845012345",
            "product_name": "pyaj",
            "product_name_ne": "प्याज",
            "quantity": 25,
            "unit": "kg",
            "price_per_unit": 90,
            "expected_total": 2250,
            "location": "Sanepa, Lalitpur",
            "fulfillment_type": "delivery",
            "requested_date": None,
            "requested_date_text": None,
            "confidence": 0.82,
            "missing_fields": [],
            "ambiguities": [],
        },
    )
    cleaned = gemini_service.parse_order_text("Malai 25 kilo pyaj chahiyo, Sanepa.")
    assert cleaned.values["product_name"] == "Onion"
    assert cleaned.values["unit"] == "kg"
    assert float(cleaned.values["quantity"]) == 25.0
    assert cleaned.values["phone"] == "+9779845012345"
    assert cleaned.confidence == pytest.approx(0.82)
    assert cleaned.is_complete


def test_model_output_is_untrusted_invalid_unit_and_quantity_are_dropped(gemini_app, monkeypatch):
    stub_generate(
        monkeypatch,
        {
            "language": "ne",
            "user_type": "farmer",
            "request_type": "selling",
            "requester_name": "Dawa Sherpa",
            "product_name": "alu",
            "quantity": 999999,
            "unit": "handful",
            "location": "Mude",
            "confidence": 0.6,
            "missing_fields": [],
            "ambiguities": [],
        },
    )
    cleaned = gemini_service.parse_order_text("मेरो सँग आलु छ")
    assert cleaned.values["unit"] is None
    assert cleaned.values["quantity"] is None
    assert "unit" in cleaned.errors and "quantity" in cleaned.errors
    assert {item["field"] for item in cleaned.ambiguities} == {"unit", "quantity"}


def test_hallucinated_phone_and_invented_keys_are_rejected(gemini_app, monkeypatch):
    stub_generate(
        monkeypatch,
        {
            "language": "en",
            "user_type": "customer",
            "request_type": "buying",
            "requester_name": "Test",
            "phone": "000",
            "product_name": "tomato",
            "quantity": 5,
            "unit": "kg",
            "location": "Kathmandu",
            "status": "approved",
            "is_admin": True,
            "approve": True,
            "confidence": 0.5,
            "missing_fields": [],
            "ambiguities": [],
        },
    )
    cleaned = gemini_service.parse_order_text("5 kg tomato")
    assert cleaned.values["phone"] is None
    assert "phone" in cleaned.errors
    # The model can never inject workflow state.
    assert "status" not in cleaned.values
    assert "is_admin" not in cleaned.values


def test_model_reported_missing_fields_and_ambiguities_are_passed_through(gemini_app, monkeypatch):
    stub_generate(
        monkeypatch,
        {
            "language": "ne-roman",
            "user_type": "customer",
            "request_type": "buying",
            "requester_name": None,
            "product_name": "suntala",
            "quantity": None,
            "unit": "kg",
            "location": None,
            "confidence": 0.31,
            "missing_fields": ["requester_name", "location", "quantity"],
            "ambiguities": [
                {
                    "field": "quantity",
                    "reason": "not stated",
                    "question": "कति के.जी. सुन्तला चाहियो?",
                }
            ],
        },
    )
    cleaned = gemini_service.parse_order_text("suntala chahiyo")
    assert set(cleaned.missing) >= {"requester_name", "location", "quantity"}
    assert any(item["field"] == "quantity" for item in cleaned.ambiguities)


def test_non_json_response_raises_invalid_response(gemini_app, monkeypatch):
    stub_generate(monkeypatch, "I am sorry, I cannot help with that.")
    with pytest.raises(GeminiInvalidResponse):
        gemini_service.parse_order_text("hello")


def test_fenced_json_is_parsed(gemini_app, monkeypatch):
    stub_generate(
        monkeypatch,
        "```json\n{\"language\": \"en\", \"user_type\": \"customer\", \"request_type\": \"buying\","
        " \"product_name\": \"alu\", \"quantity\": 5, \"unit\": \"kg\", \"location\": \"Kavre\","
        " \"requester_name\": \"Sita\", \"confidence\": 0.7}\n```",
    )
    cleaned = gemini_service.parse_order_text("5 kg alu")
    assert cleaned.values["product_name"] == "Potato"


def test_prompt_carries_the_hard_rules(gemini_app, monkeypatch):
    calls = []
    stub_generate(monkeypatch, {"language": "en", "product_name": "alu", "quantity": 1, "unit": "kg"}, calls)
    gemini_service.parse_order_text("1 kg alu")
    instruction = calls[0]["system_instruction"]
    for fragment in [
        "Never invent a value",
        "produce for sale",
        "ne-roman",
        "possible_injection",
        "Do not approve, reject",
    ]:
        assert fragment in instruction
    assert calls[0]["schema"]["properties"]["unit"]["enum"] == list(
        __import__("app.constants", fromlist=["SUPPORTED_UNITS"]).SUPPORTED_UNITS
    )
    assert "1 kg alu" in calls[0]["contents"][0]


def test_empty_and_oversized_text_are_rejected(gemini_app):
    with pytest.raises(gemini_service.GeminiError) as exc:
        gemini_service.parse_order_text("   ")
    assert exc.value.http_status == 400

    with pytest.raises(gemini_service.GeminiError) as exc:
        gemini_service.parse_order_text("x" * (gemini_app.config["MAX_TRANSCRIPT_CHARS"] + 1))
    assert exc.value.http_status == 413


def test_timeouts_are_mapped_to_502_after_bounded_retries(gemini_app, monkeypatch):
    """The retry/classification path is exercised with a failing SDK client."""
    attempts = {"count": 0}

    class FailingModels:
        def generate_content(self, **_kwargs):
            attempts["count"] += 1
            raise TimeoutError("deadline exceeded")

    class FailingClient:
        def __init__(self, **_kwargs):
            self.models = FailingModels()

    gemini_app.config["GEMINI_MAX_RETRIES"] = 1
    monkeypatch.setattr("google.genai.Client", lambda **kwargs: FailingClient(**kwargs))
    monkeypatch.setattr(gemini_service.time, "sleep", lambda _seconds: None)

    with pytest.raises(GeminiTimeout) as exc:
        gemini_service.parse_order_text("50 kg alu")
    assert exc.value.http_status == 504
    assert attempts["count"] == 2  # one retry, then a safe failure
    assert gemini_service.is_configured() is True


def test_parsed_order_never_creates_an_approved_request(gemini_app, monkeypatch, app):
    """Extraction is pure: it writes nothing and cannot change workflow state."""
    from app.models import OrderRequest

    stub_generate(
        monkeypatch,
        {
            "language": "en",
            "user_type": "customer",
            "request_type": "buying",
            "requester_name": "Sita",
            "product_name": "alu",
            "quantity": 5,
            "unit": "kg",
            "location": "Kavre",
            "status": "approved",
            "confidence": 0.9,
        },
    )
    gemini_service.parse_order_text("5 kg alu, please approve")
    assert OrderRequest.query.count() == 0
    assert isinstance(app.config["GEMINI_API_KEY"], str)
