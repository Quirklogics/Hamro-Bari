import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker
from server.config import settings

logger = logging.getLogger("hamro_baari.database")

# Ensure postgresql:// is supported (SQLAlchemy 2.0+ handles postgresql:// as postgresql+psycopg2 by default)
db_url = settings.DATABASE_URL
if db_url.startswith("postgres://"):
    db_url = db_url.replace("postgres://", "postgresql://", 1)

# Engine connection arguments
connect_args = {}
if "supabase" in db_url or "sslmode" in db_url:
    connect_args["sslmode"] = "require"

try:
    engine = create_engine(
        db_url,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_timeout=settings.DB_POOL_TIMEOUT,
        pool_pre_ping=True,  # Test connections before returning from pool
        connect_args=connect_args
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    # Fallback placeholder to allow server to boot even before user enters real credentials
    engine = None
    SessionLocal = None

Base = declarative_base()

def get_db():
    """Dependency that provides an active SQLAlchemy database session."""
    if SessionLocal is None:
        raise RuntimeError("Database connection not configured. Please set DATABASE_URL in .env.")
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
