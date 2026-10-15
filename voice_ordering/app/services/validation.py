"""Sanitisation and validation of order data.

Every value that reaches the database passes through this module. Two sources
are treated as untrusted:

* **Gemini output** - the model may hallucinate, so its JSON is coerced field by
  field, unknown keys are dropped, enums/units/ranges are re-checked and
  anything questionable becomes a clarification question instead of data.
* **The browser** - request bodies are cleaned the same way, with strict
  errors for a submission that claims to be complete.

No function here ever invents a value: unknown stays ``None``.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field as dc_field
from datetime import date, datetime, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

from .. import constants as C

# --- primitives ---------------------------------------------------------------
_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]")
_WHITESPACE = re.compile(r"\s+")
_NUMERIC_ONLY = re.compile(r"^([0-9]+(?:[.,][0-9]+)?)\s*(.*)$")
_ISO_DATE = re.compile(r"^(\d{4})[-/.](\d{1,2})[-/.](\d{1,2})$")

MAX_NAME = 120
MAX_PRODUCT = 120
MAX_LOCATION = 200
MAX_PHONE = 25
MAX_DATE_TEXT = 120
MAX_NOTES = 2000

# Fields accepted from the API / the AI. Anything else is dropped silently.
ALLOWED_FIELDS = (
    "requester_name",
    "phone",
    "user_type",
    "request_type",
    "product_name",
    "product_name_ne",
    "quantity",
    "unit",
    "price_per_unit",
    "expected_total",
    "location",
    "fulfillment_type",
    "requested_date",
    "requested_date_text",
)

# Fields an administrator is allowed to correct after submission.
EDITABLE_FIELDS = (
    "requester_name",
    "phone",
    "user_type",
    "request_type",
    "product_name",
    "quantity",
    "unit",
    "price_per_unit",
    "expected_total",
    "location",
    "fulfillment_type",
    "requested_date",
    "admin_notes",
)


class FieldError(Exception):
    """A single field failed validation. ``field`` is the API field name."""

    def __init__(self, field: str, code: str, message: str):
        super().__init__(message)
        self.field = field
        self.code = code
        self.message = message


@dataclass
class CleanedOrder:
    """Result of cleaning an order payload."""

    values: dict[str, Any] = dc_field(default_factory=dict)
    errors: dict[str, str] = dc_field(default_factory=dict)
    ambiguities: list[dict] = dc_field(default_factory=list)
    missing: list[str] = dc_field(default_factory=list)
    confidence: float | None = None
    language: str | None = None
    transcript: str | None = None
    raw: dict = dc_field(default_factory=dict)

    @property
    def is_complete(self) -> bool:
        return not self.missing and not self.errors

    def to_dict(self) -> dict:
        return {
            **self.values,
            "confidence": self.confidence,
            "language": self.language,
            "missing_fields": self.missing,
            "ambiguities": self.ambiguities,
            "field_errors": self.errors,
            "is_complete": self.is_complete,
        }


# --- text helpers -------------------------------------------------------------
def clean_text(
    value: Any,
    *,
    field: str,
    max_length: int,
    required: bool = False,
) -> str | None:
    """Normalise free text; raise :class:`FieldError` on unusable input."""
    if value is None:
        if required:
            raise FieldError(field, "required", f"{_label(field)} is required.")
        return None
    if isinstance(value, bool):
        raise FieldError(field, "type", f"{_label(field)} must be text.")
    if not isinstance(value, (str, int, float)):
        raise FieldError(field, "type", f"{_label(field)} must be text.")

    text = unicodedata.normalize("NFKC", str(value))
    text = _CONTROL_CHARS.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()

    if not text:
        if required:
            raise FieldError(field, "required", f"{_label(field)} is required.")
        return None
    if len(text) > max_length:
        raise FieldError(
            field, "too_long", f"{_label(field)} must be at most {max_length} characters."
        )
    return text


def _label(field_name: str) -> str:
    return C.FIELD_LABELS.get(field_name, {}).get("en", field_name.replace("_", " "))


def _enum(value: Any, aliases: dict[str, str], allowed: tuple[str, ...], field: str) -> str | None:
    text = clean_text(value, field=field, max_length=40)
    if text is None:
        return None
    key = text.lower().strip().replace("-", " ").replace("_", " ")
    key = _WHITESPACE.sub(" ", key)
    canonical = aliases.get(key) or aliases.get(key.replace(" ", ""))
    if canonical is None:
        raise FieldError(
            field,
            "unsupported_value",
            f"'{text}' is not one of: {', '.join(allowed)}.",
        )
    return canonical


def normalize_user_type(value: Any) -> str | None:
    return _enum(value, C.USER_TYPE_ALIASES, C.USER_TYPES, "user_type")


def normalize_request_type(value: Any) -> str | None:
    return _enum(value, C.REQUEST_TYPE_ALIASES, C.REQUEST_TYPES, "request_type")


def normalize_fulfillment(value: Any) -> str | None:
    return _enum(value, C.FULFILLMENT_ALIASES, C.FULFILLMENT_TYPES, "fulfillment_type")


def normalize_unit(value: Any, field: str = "unit") -> str | None:
    text = clean_text(value, field=field, max_length=24)
    if text is None:
        return None
    key = text.lower().strip().rstrip(".").replace(" ", "")
    unit = C.UNIT_ALIASES.get(key)
    if unit is None and key.endswith("s"):
        unit = C.UNIT_ALIASES.get(key[:-1])
    if unit is None:
        raise FieldError(
            field,
            "unsupported_unit",
            f"'{text}' is not a supported unit ({', '.join(C.SUPPORTED_UNITS)}).",
        )
    return unit


def normalize_quantity(value: Any, unit: str | None) -> Decimal | None:
    """Return a positive quantity, checking it against the unit's plausible range."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise FieldError("quantity", "type", "Quantity must be a number.")

    number: Decimal
    if isinstance(value, (int, float, Decimal)):
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            raise FieldError("quantity", "type", "Quantity must be a number.")
    elif isinstance(value, str):
        match = _NUMERIC_ONLY.match(value.strip().replace(" ", ""))
        if not match:
            raise FieldError("quantity", "not_a_number", f"'{value}' is not a number.")
        try:
            number = Decimal(match.group(1).replace(",", "."))
        except InvalidOperation:
            raise FieldError("quantity", "not_a_number", f"'{value}' is not a number.")
    else:
        raise FieldError("quantity", "type", "Quantity must be a number.")

    if number <= 0:
        raise FieldError("quantity", "out_of_range", "Quantity must be greater than zero.")

    # With a known unit we check its own plausible range; with an unknown or
    # missing unit we still reject implausible magnitudes (a hallucinated
    # 999999 is out of bounds for every supported unit).
    bounds = C.UNIT_QUANTITY_RANGE.get(unit or "")
    if bounds is None:
        bounds = (
            min(low for low, _ in C.UNIT_QUANTITY_RANGE.values()),
            max(high for _, high in C.UNIT_QUANTITY_RANGE.values()),
        )
    low, high = bounds
    if not (Decimal(str(low)) <= number <= Decimal(str(high))):
        label = C.UNIT_LABELS.get(unit or "", {}).get("en") or "the stated unit"
        raise FieldError(
            "quantity",
            "out_of_range",
            f"Quantity for {label} must be between {low:g} and {high:g}.",
        )
    return number.quantize(Decimal("0.001"))


def split_quantity_and_unit(value: Any) -> tuple[Decimal | None, str | None]:
    """Pull ``200`` and ``kilo`` out of ``"200 kilo"``.

    ``None`` means "not found" - never a guessed value.
    """
    if not isinstance(value, str):
        return None, None
    match = _NUMERIC_ONLY.match(value.strip().replace(" ", ""))
    if not match:
        return None, None
    quantity, unit = None, None
    try:
        quantity = Decimal(match.group(1).replace(",", "."))
    except InvalidOperation:
        quantity = None
    tail = match.group(2).strip()
    if tail:
        try:
            unit = normalize_unit(tail)
        except FieldError:
            unit = None
    return quantity, unit


def normalize_phone(value: Any) -> str | None:
    """Normalise a Nepali phone number, or reject it. Never invents digits."""
    text = clean_text(value, field="phone", max_length=MAX_PHONE)
    if text is None:
        return None
    digits = re.sub(r"[^\d]", "", text)
    if digits.startswith("00977"):
        digits = digits[2:]
    if not digits:
        raise FieldError("phone", "invalid_phone", "Phone number has no digits.")
    # 10-digit mobile (98xxxxxxxx / 97xxxxxxxx) -> +977...
    if len(digits) == 10 and digits.startswith("9"):
        return "+977" + digits
    if len(digits) == 12 and digits.startswith("9779"):
        return "+" + digits
    # 11-digit national with trunk 0 (e.g. 098xxxxxxxx mobile)
    if len(digits) == 11 and digits.startswith("0"):
        return "+977" + digits[1:]
    # 9-digit landline with trunk 0 (e.g. 014444444 -> +977 1 4444444)
    if len(digits) == 9 and digits.startswith("0"):
        return "+977" + digits[1:]
    if 7 <= len(digits) <= 15:
        return "+" + digits if not text.startswith("+") else "+" + digits
    raise FieldError("phone", "invalid_phone", f"'{text}' is not a valid phone number.")


def normalize_date(value: Any) -> date | None:
    """Accept an ISO-ish date; reject past dates and absurd futures."""
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    parsed: date | None = None
    if isinstance(value, datetime):
        parsed = value.date()
    elif isinstance(value, date):
        parsed = value
    elif isinstance(value, str):
        text = value.strip()
        match = _ISO_DATE.match(text)
        if match:
            try:
                parsed = date(int(match.group(1)), int(match.group(2)), int(match.group(3)))
            except ValueError:
                raise FieldError("requested_date", "invalid_date", f"'{text}' is not a valid date.")
        else:
            raise FieldError(
                "requested_date",
                "invalid_date",
                f"'{text}' is not a valid ISO date (use YYYY-MM-DD).",
            )
    else:
        raise FieldError("requested_date", "type", "Date must be text or a date.")

    today = date.today()
    if parsed < today - timedelta(days=1):
        raise FieldError(
            "requested_date", "invalid_date", "Requested date is in the past."
        )
    if parsed > today + timedelta(days=400):
        raise FieldError(
            "requested_date", "invalid_date", "Requested date is too far in the future."
        )
    return parsed


def normalize_money(value: Any, field: str, maximum: float) -> Decimal | None:
    if value is None or (isinstance(value, str) and not value.strip()):
        return None
    if isinstance(value, bool):
        raise FieldError(field, "type", f"{_label(field)} must be a number.")
    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        cleaned = re.sub(r"^(rs\.?|npr\.?|nrs\.?|रु\.?)\s*", "", cleaned, flags=re.IGNORECASE).strip()
        try:
            number = Decimal(cleaned)
        except InvalidOperation:
            raise FieldError(field, "not_a_number", f"'{value}' is not a number.")
    elif isinstance(value, (int, float, Decimal)):
        try:
            number = Decimal(str(value))
        except InvalidOperation:
            raise FieldError(field, "not_a_number", f"'{value}' is not a number.")
    else:
        raise FieldError(field, "type", f"{_label(field)} must be a number.")

    if number <= 0:
        raise FieldError(field, "out_of_range", f"{_label(field)} must be greater than zero.")
    if number > Decimal(str(maximum)):
        raise FieldError(field, "out_of_range", f"{_label(field)} is unrealistically large.")
    return number.quantize(Decimal("0.01"))


def normalize_product(value: Any) -> dict | None:
    """Return ``{"name": display, "name_ne": canonical ne, "matched": bool}``."""
    text = clean_text(value, field="product_name", max_length=MAX_PRODUCT)
    if text is None:
        return None
    key = text.lower().strip().strip("।.,!?\"'")
    key = _WHITESPACE.sub(" ", key)
    lookup = C.PRODUCT_ALIASES.get(key) or C.PRODUCT_ALIASES.get(key.replace(" ", ""))
    if lookup:
        return {"name": lookup["en"], "name_ne": lookup["ne"], "matched": True, "raw": text}
    # Unknown produce: keep exactly what was said.
    return {"name": text, "name_ne": None, "matched": False, "raw": text}


def clean_transcript(value: Any, max_length: int) -> str | None:
    """Sanitise a transcript: non-text is dropped, long text is truncated."""
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, (str, int, float)):
        return None
    text = unicodedata.normalize("NFKC", str(value))
    text = _CONTROL_CHARS.sub(" ", text)
    text = _WHITESPACE.sub(" ", text).strip()
    if not text:
        return None
    if len(text) > max_length:
        text = text[:max_length]
    return text


# --- ambiguity handling -------------------------------------------------------
def _question_for(field_name: str, reason: str) -> str:
    label = _label(field_name)
    return f"Please confirm the {label.lower()} ({reason})."


def _safe_text(value: Any, max_length: int) -> str | None:
    """Tolerant variant of :func:`clean_text`: never raises, trims oversize."""
    if value is None or isinstance(value, bool):
        return None
    if not isinstance(value, (str, int, float)):
        return None
    text = _WHITESPACE.sub(" ", _CONTROL_CHARS.sub(" ", str(value))).strip()
    if not text:
        return None
    return text[:max_length]


MAX_AMBIGUITY_ITEMS = 20


def _collect_ambiguities(raw_items: Any, errors: dict[str, str]) -> list[dict]:
    """Sanitise the ambiguity list.

    Advisory metadata only (it can never change validation or a request status):
    junk is dropped, oversize text is trimmed, and the list is capped.
    """
    items: list[dict] = []
    seen: set[str] = set()
    if isinstance(raw_items, list):
        for item in raw_items:
            if not isinstance(item, dict) or len(items) >= MAX_AMBIGUITY_ITEMS:
                continue
            name = _safe_text(item.get("field"), 60)
            if not name or len(str(item.get("field") or "")) > 80:
                continue
            if len(str(item.get("reason") or "")) > 400 or len(str(item.get("question") or "")) > 400:
                continue
            if name in seen:
                continue
            seen.add(name)
            reason = _safe_text(item.get("reason"), 240)
            items.append(
                {
                    "field": name,
                    "reason": reason or "uncertain",
                    "question": _safe_text(item.get("question"), 240)
                    or _question_for(name, reason or "uncertain"),
                }
            )
    # Validation failures are ambiguities too.
    for name, message in errors.items():
        if any(existing["field"] == name for existing in items):
            continue
        items.append({"field": name, "reason": "invalid_value", "question": message})
    return items


# --- main entry points --------------------------------------------------------
def clean_order_payload(raw: Any, *, require_complete: bool = False) -> CleanedOrder:
    """Clean an AI/browser payload. Invalid fields become ``None`` + an issue."""
    result = CleanedOrder()
    if not isinstance(raw, dict):
        result.errors["payload"] = "Expected a JSON object."
        return result

    # Drop anything not on the whitelist (defence against prompt-driven keys).
    data = {k: raw.get(k) for k in ALLOWED_FIELDS if k in raw}
    result.raw = {k: raw[k] for k in raw if not isinstance(raw[k], (dict, list))}

    def attempt(field_name: str, fn, *args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except FieldError as exc:
            result.errors[exc.field] = exc.message
            return None

    values: dict[str, Any] = {}

    values["requester_name"] = attempt(
        "requester_name", clean_text, data.get("requester_name"),
        field="requester_name", max_length=MAX_NAME,
        required=require_complete,
    )
    values["phone"] = attempt("phone", normalize_phone, data.get("phone"))
    values["user_type"] = attempt("user_type", normalize_user_type, data.get("user_type"))
    values["request_type"] = attempt(
        "request_type", normalize_request_type, data.get("request_type")
    )
    values["location"] = attempt(
        "location", clean_text, data.get("location"),
        field="location", max_length=MAX_LOCATION,
        required=require_complete,
    )
    values["fulfillment_type"] = attempt(
        "fulfillment_type", normalize_fulfillment, data.get("fulfillment_type")
    )

    # --- quantity + unit (they inform each other) ---------------------------
    quantity_raw = data.get("quantity")
    unit = attempt("unit", normalize_unit, data.get("unit"))
    if unit is None and isinstance(quantity_raw, str):
        embedded_qty, embedded_unit = split_quantity_and_unit(quantity_raw)
        if embedded_unit:
            unit = embedded_unit
            quantity_raw = embedded_qty
    values["unit"] = unit
    quantity = attempt("quantity", normalize_quantity, quantity_raw, unit)
    if quantity is None and isinstance(quantity_raw, str):
        embedded_qty, _ = split_quantity_and_unit(quantity_raw)
        if embedded_qty is not None:
            quantity = attempt("quantity", normalize_quantity, embedded_qty, unit)
    values["quantity"] = quantity

    # --- product -----------------------------------------------------------
    product = attempt("product_name", normalize_product, data.get("product_name"))
    if product:
        values["product_name"] = product["name"]
        values["product_name_ne"] = product["name_ne"] or attempt(
            "product_name_ne", clean_text, data.get("product_name_ne"),
            field="product_name_ne", max_length=MAX_PRODUCT,
        )
        values["product_matched"] = product["matched"]
        values["product_raw"] = product["raw"]
    else:
        values["product_name"] = None
        values["product_name_ne"] = attempt(
            "product_name_ne", clean_text, data.get("product_name_ne"),
            field="product_name_ne", max_length=MAX_PRODUCT,
        )
        values["product_matched"] = False

    values["price_per_unit"] = attempt(
        "price_per_unit", normalize_money, data.get("price_per_unit"),
        "price_per_unit", C.MAX_PRICE_PER_UNIT,
    )
    values["expected_total"] = attempt(
        "expected_total", normalize_money, data.get("expected_total"),
        "expected_total", C.MAX_EXPECTED_TOTAL,
    )
    values["requested_date"] = attempt(
        "requested_date", normalize_date, data.get("requested_date")
    )
    values["requested_date_text"] = attempt(
        "requested_date_text", clean_text, data.get("requested_date_text"),
        field="requested_date_text", max_length=MAX_DATE_TEXT,
    )

    if "requested_date" in result.errors:
        # Keep the spoken wording so an administrator still sees what was said.
        result.ambiguities.append(
            {
                "field": "requested_date",
                "reason": "unparsed_date",
                "question": "Which date do you need the order? (YYYY-MM-DD)",
            }
        )

    # --- AI bookkeeping ----------------------------------------------------
    confidence = raw.get("confidence") if "confidence" in raw else raw.get("ai_confidence")
    if isinstance(confidence, (int, float)) and not isinstance(confidence, bool):
        result.confidence = max(0.0, min(1.0, float(confidence)))
    language = clean_text(raw.get("language"), field="language", max_length=20)
    if language and language not in C.SUPPORTED_LANGUAGES:
        language = "unknown"
    result.language = language

    result.values = values
    result.transcript = clean_transcript(raw.get("transcript"), 4000)
    result.missing = compute_missing_fields(values)
    result.ambiguities = _collect_ambiguities(raw.get("ambiguities"), result.errors)
    result.missing.extend(
        name for name in raw.get("missing_fields", []) if isinstance(name, str) and name in C.REQUIRED_FIELDS
    )
    result.missing = _dedupe(result.missing)
    return result


def _dedupe(items: list[str]) -> list[str]:
    seen: list[str] = []
    for item in items:
        if item not in seen:
            seen.append(item)
    return seen


def compute_missing_fields(values: dict) -> list[str]:
    """Required fields that are still absent (``None`` counts as absent)."""
    missing: list[str] = []
    for name in C.REQUIRED_FIELDS:
        value = values.get(name)
        if value is None or (isinstance(value, str) and not value.strip()):
            missing.append(name)
    return missing


def validate_for_submission(cleaned: CleanedOrder) -> list[dict]:
    """Return per-field errors that block submission (empty list = valid)."""
    problems: list[dict] = []
    missing = compute_missing_fields(cleaned.values)
    for name in missing:
        problems.append(
            {
                "field": name,
                "code": "required",
                "message": f"{_label(name)} is required before submission.",
            }
        )
    for name, message in cleaned.errors.items():
        if name in {p["field"] for p in problems}:
            continue
        problems.append({"field": name, "code": "invalid", "message": message})

    # Cross-field sanity: a total without a unit price is fine (spoken total),
    # but a wildly inconsistent pair is worth flagging, not guessing.
    quantity = cleaned.values.get("quantity")
    price = cleaned.values.get("price_per_unit")
    total = cleaned.values.get("expected_total")
    if quantity and price and total:
        computed = (Decimal(quantity) * Decimal(price)).quantize(Decimal("0.01"))
        if abs(computed - Decimal(total)) > (computed * Decimal("0.25")) and computed > 0:
            problems.append(
                {
                    "field": "expected_total",
                    "code": "inconsistent",
                    "message": (
                        f"Expected total {total} does not match quantity x price "
                        f"({computed}). Please confirm."
                    ),
                }
            )
    return problems


__all__ = [
    "FieldError",
    "CleanedOrder",
    "ALLOWED_FIELDS",
    "EDITABLE_FIELDS",
    "clean_text",
    "clean_transcript",
    "normalize_date",
    "normalize_fulfillment",
    "normalize_money",
    "normalize_phone",
    "normalize_product",
    "normalize_quantity",
    "normalize_request_type",
    "normalize_unit",
    "normalize_user_type",
    "split_quantity_and_unit",
    "clean_order_payload",
    "compute_missing_fields",
    "validate_for_submission",
]
