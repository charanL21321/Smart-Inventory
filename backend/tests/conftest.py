"""
Pytest configuration and shared fixtures for Smart Inventory tests.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

import app.models  # noqa: F401
from app.api.deps import get_db
from app.database.base import Base
from app.main import app

# Shared in-memory SQLite engine with StaticPool across tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all database tables
Base.metadata.create_all(bind=engine)


import threading

_sqlite_test_lock = threading.Lock()


@pytest.fixture(scope="session", autouse=True)
def setup_test_database():
    """Setup in-memory tables and apply dependency override."""
    def override_get_db():
        with _sqlite_test_lock:
            db = TestingSessionLocal()
            try:
                yield db
            finally:
                db.close()

    app.dependency_overrides[get_db] = override_get_db
    yield
    app.dependency_overrides.clear()


@pytest.fixture
def db_session():
    """Yield a clean test database session."""
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client():
    """FastAPI TestClient instance."""
    return TestClient(app)
