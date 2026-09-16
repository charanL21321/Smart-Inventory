import logging
import sys
from typing import Generator

from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import settings

logger = logging.getLogger(__name__)

# SQLAlchemy 2.x Engine configured with connection health checking
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    echo=settings.DEBUG,
)

# Thread-local session factory for database transactions
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
    expire_on_commit=False,
)


def get_db() -> Generator[Session, None, None]:
    """
    FastAPI dependency yielding a database session for the duration of a request.
    Guarantees the session is properly closed once the request finishes.
    """
    db: Session = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def check_db_connection() -> bool:
    """
    Verifies that the application can connect to the configured PostgreSQL database.
    Executes a simple 'SELECT 1' query using the configured engine.
    Fails clearly with a descriptive RuntimeError if the database configuration
    or connectivity is invalid.
    """
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Successfully established connection to the PostgreSQL database.")
        return True
    except SQLAlchemyError as exc:
        error_msg = (
            f"Database connectivity check failed for URL '{settings.DATABASE_URL}'. "
            f"Please verify your DATABASE_URL in .env and ensure the PostgreSQL service is accessible. "
            f"Error details: {exc}"
        )
        logger.error(error_msg)
        raise RuntimeError(error_msg) from exc


if __name__ == "__main__":
    print(f"Testing database connection to: {settings.DATABASE_URL}")
    try:
        check_db_connection()
        print("SUCCESS: Database connection verified successfully!")
    except Exception as err:
        print(f"FAILURE: {err}", file=sys.stderr)
        sys.exit(1)
