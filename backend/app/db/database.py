from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import logging
from app.core.config import settings

logger = logging.getLogger("meteora.db")

Base = declarative_base()

try:
    # Attempt connecting to PostgreSQL
    engine = create_engine(
        settings.DATABASE_URL,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    logger.info("Configured PostgreSQL connection pool successfully.")
except Exception as e:
    logger.warning(f"PostgreSQL connection failed ({e}). Falling back to local SQLite engine.")
    engine = create_engine(
        "sqlite:///./meteora_local.db",
        connect_args={"check_same_thread": False}
    )
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI Dependency for database sessions."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def init_db():
    """Create all tables in the PostgreSQL database."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database schemas initialized.")
    except Exception as e:
        logger.error(f"Error initializing database tables: {e}")
