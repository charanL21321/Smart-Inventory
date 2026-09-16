"""
Comprehensive test suite for Phase 2: Authentication & Role-Based Access Control.
Verifies registration, login, password hashing, JWT operations, protected endpoints,
RBAC authorization, and Phase 1 regression.
"""

from datetime import timedelta
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api.deps import get_db
from app.core.security import create_access_token, verify_password
from app.database.base import Base
from app.main import app
from app.models.user import User, UserRole

# Use an in-memory SQLite database for isolated test execution
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create all database tables
Base.metadata.create_all(bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


# Apply dependency override
app.dependency_overrides[get_db] = override_get_db

client = TestClient(app)


def test_phase1_regression():
    """Verify that existing Phase 1 endpoints still function correctly."""
    # Root endpoint
    res_root = client.get("/")
    assert res_root.status_code == 200
    assert res_root.json() == {
        "message": "Smart Inventory & Stock Replenishment Platform API",
        "status": "running",
    }

    # Health endpoint
    res_health = client.get("/health")
    assert res_health.status_code == 200
    assert res_health.json() == {"status": "healthy"}

    # Docs endpoints
    res_docs = client.get("/docs")
    assert res_docs.status_code == 200

    res_redoc = client.get("/redoc")
    assert res_redoc.status_code == 200

    # OpenAPI schema check for securitySchemes
    res_openapi = client.get("/openapi.json")
    assert res_openapi.status_code == 200
    schema = res_openapi.json()
    assert "components" in schema
    assert "securitySchemes" in schema["components"]
    assert "HTTPBearer" in schema["components"]["securitySchemes"]


def test_user_registration_success():
    """Verify successful user registration and field exposure safety."""
    payload = {
        "username": "warehouse_user",
        "email": "warehouse@example.com",
        "password": "Password123!",
        "full_name": "Warehouse Specialist",
        "role": "WAREHOUSE_STAFF",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 201, response.text
    data = response.json()

    assert data["username"] == "warehouse_user"
    assert data["email"] == "warehouse@example.com"
    assert data["full_name"] == "Warehouse Specialist"
    assert data["role"] == "WAREHOUSE_STAFF"
    assert data["is_active"] is True
    assert "id" in data
    assert "created_at" in data

    # Verify sensitive fields are NEVER exposed
    assert "password" not in data
    assert "hashed_password" not in data

    # Verify password was hashed in the database
    with TestingSessionLocal() as db:
        user_in_db = db.query(User).filter(User.username == "warehouse_user").first()
        assert user_in_db is not None
        assert user_in_db.hashed_password != "Password123!"
        assert verify_password("Password123!", user_in_db.hashed_password)


def test_user_registration_duplicate_username():
    """Verify rejection of duplicate username."""
    payload = {
        "username": "warehouse_user",  # Duplicate
        "email": "different_email@example.com",
        "password": "Password123!",
        "role": "WAREHOUSE_STAFF",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "Username is already registered" in response.json()["detail"]


def test_user_registration_duplicate_email():
    """Verify rejection of duplicate email (case-insensitive)."""
    payload = {
        "username": "different_username",
        "email": "WAREHOUSE@example.com",  # Duplicate uppercase email
        "password": "Password123!",
        "role": "WAREHOUSE_STAFF",
    }
    response = client.post("/auth/register", json=payload)
    assert response.status_code == 400
    assert "Email is already registered" in response.json()["detail"]


def test_login_success():
    """Verify successful authentication with username and email."""
    # Login via username
    res_user = client.post("/auth/login", json={
        "username": "warehouse_user",
        "password": "Password123!",
    })
    assert res_user.status_code == 200
    token_data = res_user.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Login via email
    res_email = client.post("/auth/login", json={
        "username": "warehouse@example.com",
        "password": "Password123!",
    })
    assert res_email.status_code == 200
    assert "access_token" in res_email.json()


def test_login_invalid_credentials():
    """Verify authentication failure on wrong credentials."""
    # Wrong password
    res_wrong_pw = client.post("/auth/login", json={
        "username": "warehouse_user",
        "password": "WrongPassword!",
    })
    assert res_wrong_pw.status_code == 401
    assert "Incorrect username or password" in res_wrong_pw.json()["detail"]

    # Non-existent user
    res_nonexistent = client.post("/auth/login", json={
        "username": "non_existent_user",
        "password": "SomePassword123!",
    })
    assert res_nonexistent.status_code == 401
    assert "Incorrect username or password" in res_nonexistent.json()["detail"]


def test_protected_users_me():
    """Verify access to /users/me with valid, missing, and invalid tokens."""
    # Obtain valid token
    login_res = client.post("/auth/login", json={
        "username": "warehouse_user",
        "password": "Password123!",
    })
    token = login_res.json()["access_token"]

    # 1. Valid token
    headers = {"Authorization": f"Bearer {token}"}
    res_me = client.get("/users/me", headers=headers)
    assert res_me.status_code == 200
    me_data = res_me.json()
    assert me_data["username"] == "warehouse_user"
    assert me_data["email"] == "warehouse@example.com"
    assert "password" not in me_data
    assert "hashed_password" not in me_data

    # 2. Missing token
    res_no_token = client.get("/users/me")
    assert res_no_token.status_code == 401
    assert "Authentication credentials were not provided" in res_no_token.json()["detail"]

    # 3. Invalid token
    res_bad_token = client.get("/users/me", headers={"Authorization": "Bearer invalid.token.value"})
    assert res_bad_token.status_code == 401
    assert "Invalid or expired token" in res_bad_token.json()["detail"]

    # 4. Expired token
    expired_token = create_access_token(
        data={"sub": str(me_data["id"]), "username": me_data["username"], "role": me_data["role"]},
        expires_delta=timedelta(minutes=-10),  # expired 10 minutes ago
    )
    res_expired = client.get("/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res_expired.status_code == 401
    assert "Invalid or expired token" in res_expired.json()["detail"]


def test_role_based_access_control():
    """Verify RBAC permissions for ADMIN vs non-admin roles on /users/admin-test."""
    # Register Admin user
    client.post("/auth/register", json={
        "username": "admin_boss",
        "email": "admin@example.com",
        "password": "AdminPassword123!",
        "full_name": "System Administrator",
        "role": "ADMIN",
    })

    # Register Inventory Manager user
    client.post("/auth/register", json={
        "username": "inv_manager",
        "email": "manager@example.com",
        "password": "ManagerPassword123!",
        "full_name": "Inventory Manager",
        "role": "INVENTORY_MANAGER",
    })

    # 1. Admin login & access test
    login_admin = client.post("/auth/login", json={
        "username": "admin_boss",
        "password": "AdminPassword123!",
    })
    admin_token = login_admin.json()["access_token"]
    res_admin = client.get("/users/admin-test", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_admin.status_code == 200
    assert "Admin authorization verified successfully" in res_admin.json()["message"]
    assert res_admin.json()["admin_user"] == "admin_boss"

    # 2. Inventory Manager login & access test (Forbidden)
    login_mgr = client.post("/auth/login", json={
        "username": "inv_manager",
        "password": "ManagerPassword123!",
    })
    mgr_token = login_mgr.json()["access_token"]
    res_mgr = client.get("/users/admin-test", headers={"Authorization": f"Bearer {mgr_token}"})
    assert res_mgr.status_code == 403
    assert "Operation not permitted" in res_mgr.json()["detail"]

    # 3. Warehouse Staff access test (Forbidden)
    login_staff = client.post("/auth/login", json={
        "username": "warehouse_user",
        "password": "Password123!",
    })
    staff_token = login_staff.json()["access_token"]
    res_staff = client.get("/users/admin-test", headers={"Authorization": f"Bearer {staff_token}"})
    assert res_staff.status_code == 403
    assert "Operation not permitted" in res_staff.json()["detail"]


def test_inactive_user_rejected():
    """Verify that inactive users cannot log in or access endpoints."""
    # Register user then deactivate
    client.post("/auth/register", json={
        "username": "disabled_user",
        "email": "disabled@example.com",
        "password": "Password123!",
        "role": "WAREHOUSE_STAFF",
    })

    with TestingSessionLocal() as db:
        user = db.query(User).filter(User.username == "disabled_user").first()
        user.is_active = False
        db.commit()
        user_id = user.id

    # Try login
    login_res = client.post("/auth/login", json={
        "username": "disabled_user",
        "password": "Password123!",
    })
    assert login_res.status_code == 400
    assert "Inactive user account" in login_res.json()["detail"]

    # Try using pre-generated token with inactive user
    token = create_access_token(data={"sub": str(user_id), "username": "disabled_user", "role": "WAREHOUSE_STAFF"})
    res_me = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 400
    assert "Inactive user account" in res_me.json()["detail"]
