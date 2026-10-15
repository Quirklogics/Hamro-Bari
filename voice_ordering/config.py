"""
Configuration for the Hamro Baari Voice Ordering System.

Every secret comes from the environment (``voice_ordering/.env``). Nothing is
hardcoded: if ``GEMINI_API_KEY`` is missing the AI endpoints report a
configuration error instead of faking a result, and if ``DATABASE_URL`` is
missing or still a placeholder the app falls back to local SQLite.
"""
import os
import secrets
from datetime import timedelta

from dotenv import load_dotenv

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
INSTANCE_DIR = os.path.join(BASE_DIR, "instance")

# Load voice_ordering/.env (this app is self-contained; it does not read the
# parent project's .env so the two backends can never cross-configure).
load_dotenv(os.path.join(BASE_DIR, ".env"))


def _env_bool(name: str, default: bool = False) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on")


def _env_int(name: str, default: int) -> int:
    try:
        return int(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        return default


def _env_float(name: str, default: float) -> float:
    try:
        return float(str(os.getenv(name, default)).strip())
    except (TypeError, ValueError):
        return default


# Values that mean "the user has not filled this in yet".
_PLACEHOLDER_MARKERS = (
    "yourprojectref",
    "your-password",
    "[project_ref]",
    "[your_password]",
    "changeme",
    "change_this",
    "example.com",
    "postgres:postgres@localhost",
)


def resolve_database_url() -> str:
    """Return a usable SQLAlchemy URL, falling back to local SQLite.

    PostgreSQL is used for production when a real ``DATABASE_URL`` is present;
    otherwise the app runs on SQLite so it works with zero setup.
    """
    raw = (os.getenv("DATABASE_URL") or "").strip()
    lowered = raw.lower()
    if not raw or any(marker in lowered for marker in _PLACEHOLDER_MARKERS):
        os.makedirs(INSTANCE_DIR, exist_ok=True)
        sqlite_path = os.path.join(INSTANCE_DIR, "voice_orders.db").replace("\\", "/")
        return f"sqlite:///{sqlite_path}"
    if raw.startswith("postgres://"):
        raw = "postgresql://" + raw[len("postgres://") :]
    return raw


class Config:
    """Base configuration shared by every environment."""

    APP_NAME = os.getenv("APP_NAME", "Hamro Baari Voice Orders")
    ENV_NAME = os.getenv("APP_ENV", "development")

    # --- Core / security -----------------------------------------------------
    SECRET_KEY = os.getenv("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = resolve_database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True}
    PREFERRED_URL_SCHEME = "https" if _env_bool("COOKIE_SECURE", False) else "http"

    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = "Lax"
    SESSION_COOKIE_SECURE = _env_bool("COOKIE_SECURE", False)
    REMEMBER_COOKIE_HTTPONLY = True
    REMEMBER_COOKIE_SAMESITE = "Lax"
    REMEMBER_COOKIE_SECURE = _env_bool("COOKIE_SECURE", False)
    PERMANENT_SESSION_LIFETIME = timedelta(hours=_env_int("SESSION_HOURS", 8))

    # CSRF: cookie sessions are protected; the browser sends the token in the
    # X-CSRFToken header for fetch() based API calls.
    WTF_CSRF_TIME_LIMIT = None
    WTF_CSRF_HEADERS = ["X-CSRFToken", "X-CSRF-Token"]

    # --- Gemini ------------------------------------------------------------
    # The key stays server-side and is never sent to the browser.
    GEMINI_API_KEY = (os.getenv("GEMINI_API_KEY") or "").strip()
    GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash-lite").strip()
    GEMINI_TRANSCRIBE_MODEL = os.getenv(
        "GEMINI_TRANSCRIBE_MODEL", "gemini-3.5-flash-lite"
    ).strip()
    GEMINI_TIMEOUT_MS = _env_int("GEMINI_TIMEOUT_MS", 45000)
    GEMINI_MAX_RETRIES = _env_int("GEMINI_MAX_RETRIES", 1)
    GEMINI_TEMPERATURE = _env_float("GEMINI_TEMPERATURE", 0.1)

    # --- Request size limits ----------------------------------------------
    MAX_CONTENT_LENGTH = _env_int("MAX_CONTENT_LENGTH_BYTES", 12 * 1024 * 1024)
    MAX_AUDIO_BYTES = _env_int("MAX_AUDIO_BYTES", 8 * 1024 * 1024)
    MAX_TRANSCRIPT_CHARS = _env_int("MAX_TRANSCRIPT_CHARS", 2000)
    ALLOWED_AUDIO_MIME_TYPES = (
        "audio/webm",
        "audio/ogg",
        "audio/wav",
        "audio/x-wav",
        "audio/wave",
        "audio/mpeg",
        "audio/mp3",
        "audio/mp4",
        "audio/m4a",
        "audio/aac",
        "audio/flac",
        "video/webm",
    )

    # --- Rate limits (per remote address) ----------------------------------
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "300 per hour")
    RATELIMIT_TRANSCRIBE = os.getenv("RATELIMIT_TRANSCRIBE", "20 per minute")
    RATELIMIT_PARSE = os.getenv("RATELIMIT_PARSE", "40 per minute")
    RATELIMIT_SUBMIT = os.getenv("RATELIMIT_SUBMIT", "20 per minute")
    RATELIMIT_TRACK = os.getenv("RATELIMIT_TRACK", "60 per minute")
    RATELIMIT_LOGIN = os.getenv("RATELIMIT_LOGIN", "10 per minute")

    # --- Pagination --------------------------------------------------------
    DEFAULT_PAGE_SIZE = _env_int("DEFAULT_PAGE_SIZE", 20)
    MAX_PAGE_SIZE = _env_int("MAX_PAGE_SIZE", 100)

    # --- Origin checking for state changing requests -----------------------
    # Comma separated extra origins allowed to call the API (e.g. a separate
    # frontend host). Same-origin requests are always allowed.
    EXTRA_ALLOWED_ORIGINS = [
        o.strip()
        for o in (os.getenv("EXTRA_ALLOWED_ORIGINS") or "").split(",")
        if o.strip()
    ]

    JSON_SORT_KEYS = False


class DevelopmentConfig(Config):
    DEBUG = _env_bool("DEBUG", True)
    RATELIMIT_ENABLED = _env_bool("RATELIMIT_ENABLED", True)


class TestingConfig(Config):
    TESTING = True
    DEBUG = False
    SECRET_KEY = "testing-secret-key-not-for-production"
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    WTF_CSRF_ENABLED = False
    RATELIMIT_ENABLED = False
    GEMINI_API_KEY = ""

    @staticmethod
    def enable_csrf():
        TestingConfig.WTF_CSRF_ENABLED = True


class ProductionConfig(Config):
    DEBUG = False
    SESSION_COOKIE_SECURE = True
    REMEMBER_COOKIE_SECURE = True
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")


CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(name: str | None = None):
    key = (name or os.getenv("APP_ENV") or "development").strip().lower()
    return CONFIGS.get(key, DevelopmentConfig)
