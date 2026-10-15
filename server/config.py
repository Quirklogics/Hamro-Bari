import os
from typing import List
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

class Settings:
    APP_NAME: str = os.getenv("APP_NAME", "Hamro Baari Organic Produce API")
    APP_ENV: str = os.getenv("APP_ENV", "development")
    APP_PORT: int = int(os.getenv("APP_PORT", 8000))
    APP_HOST: str = os.getenv("APP_HOST", "0.0.0.0")
    DEBUG: bool = os.getenv("DEBUG", "True").lower() in ("true", "1", "yes")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "default-dev-secret-key")

    # Supabase / PostgreSQL Database URL
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", 
        "postgresql://postgres:postgres@localhost:5432/hamro_baari_db"
    )

    # Supabase Client Credentials
    SUPABASE_URL: str = os.getenv("SUPABASE_URL", "")
    SUPABASE_ANON_KEY: str = os.getenv("SUPABASE_ANON_KEY", "")
    SUPABASE_SERVICE_ROLE_KEY: str = os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")

    # CORS origins parsed as a list
    raw_cors: str = os.getenv("CORS_ORIGINS", "*")
    CORS_ORIGINS: List[str] = [origin.strip() for origin in raw_cors.split(",") if origin.strip()]

    # Pooling
    DB_POOL_SIZE: int = int(os.getenv("DB_POOL_SIZE", 5))
    DB_MAX_OVERFLOW: int = int(os.getenv("DB_MAX_OVERFLOW", 10))
    DB_POOL_TIMEOUT: int = int(os.getenv("DB_POOL_TIMEOUT", 30))

settings = Settings()
