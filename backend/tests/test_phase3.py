"""
Comprehensive test suite for Phase 3: Product, Category & Supplier Management.
Verifies all 40 required test cases including CRUD, RBAC, integrity checks,
validation, filtering, and Phase 1/2 regression.
"""

import pytest
from fastapi.testclient import TestClient
from app.core.security import create_access_token
from app.main import app
from app.models.category import Category
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal

client = TestClient(app)


# ------------------------------------------------------------------------------
# Fixtures for Authentication Tokens
# ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def tokens():
    """Seed test users and return authentication headers for each role."""
    with TestingSessionLocal() as db:
        admin = User(
            username="admin_p3",
            email="admin_p3@example.com",
            hashed_password=create_access_token.__globals__["hash_password"]("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        manager = User(
            username="manager_p3",
            email="manager_p3@example.com",
            hashed_password=create_access_token.__globals__["hash_password"]("ManagerPass123!"),
            role=UserRole.INVENTORY_MANAGER,
            is_active=True,
        )
        staff = User(
            username="staff_p3",
            email="staff_p3@example.com",
            hashed_password=create_access_token.__globals__["hash_password"]("StaffPass123!"),
            role=UserRole.WAREHOUSE_STAFF,
            is_active=True,
        )
        db.add_all([admin, manager, staff])
        db.commit()
        db.refresh(admin)
        db.refresh(manager)
        db.refresh(staff)

        admin_token = create_access_token({"sub": str(admin.id), "username": admin.username, "role": admin.role.value})
        manager_token = create_access_token({"sub": str(manager.id), "username": manager.username, "role": manager.role.value})
        staff_token = create_access_token({"sub": str(staff.id), "username": staff.username, "role": staff.role.value})

    return {
        "admin": {"Authorization": f"Bearer {admin_token}"},
        "manager": {"Authorization": f"Bearer {manager_token}"},
        "staff": {"Authorization": f"Bearer {staff_token}"},
    }


# ==============================================================================
# CATEGORY TESTS (1-8)
# ==============================================================================
def test_01_admin_can_create_category(tokens):
    res = client.post("/categories", headers=tokens["admin"], json={
        "name": "Electronics",
        "description": "Electronic gadgets and devices",
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Electronics"
    assert data["is_active"] is True
    assert "id" in data


def test_02_inventory_manager_can_create_category(tokens):
    res = client.post("/categories", headers=tokens["manager"], json={
        "name": "Hardware",
        "description": "Tools and industrial hardware",
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Hardware"


def test_03_warehouse_staff_cannot_create_category(tokens):
    res = client.post("/categories", headers=tokens["staff"], json={
        "name": "Office Supplies",
        "description": "Stationery and supplies",
    })
    assert res.status_code == 403
    assert "Operation not permitted" in res.json()["detail"]


def test_04_category_list_works(tokens):
    res = client.get("/categories", headers=tokens["staff"])
    assert res.status_code == 200
    names = [c["name"] for c in res.json()]
    assert "Electronics" in names
    assert "Hardware" in names


def test_05_category_retrieval_works(tokens):
    # Retrieve category with ID 1
    res = client.get("/categories/1", headers=tokens["staff"])
    assert res.status_code == 200
    assert res.json()["name"] == "Electronics"

    # Non-existent category
    res_404 = client.get("/categories/9999", headers=tokens["staff"])
    assert res_404.status_code == 404


def test_06_duplicate_category_name_is_rejected(tokens):
    res = client.post("/categories", headers=tokens["admin"], json={
        "name": "Electronics",  # duplicate
        "description": "Duplicate category",
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_07_category_update_works(tokens):
    res = client.put("/categories/2", headers=tokens["manager"], json={
        "description": "Updated hardware description",
    })
    assert res.status_code == 200
    assert res.json()["description"] == "Updated hardware description"


def test_08_category_deactivation_deletion_behavior_works(tokens):
    # Create category for deletion test
    create_res = client.post("/categories", headers=tokens["admin"], json={
        "name": "Temporary Category",
    })
    cat_id = create_res.json()["id"]

    del_res = client.delete(f"/categories/{cat_id}", headers=tokens["admin"])
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False


# ==============================================================================
# SUPPLIER TESTS (9-17)
# ==============================================================================
def test_09_admin_can_create_supplier(tokens):
    res = client.post("/suppliers", headers=tokens["admin"], json={
        "name": "Apex Logistics Inc",
        "contact_person": "Alice Smith",
        "email": "alice@apexlogistics.com",
        "phone": "+1-555-0199",
        "address": "123 Industrial Parkway",
        "lead_time_days": 5,
        "minimum_order_quantity": 50,
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Apex Logistics Inc"
    assert data["lead_time_days"] == 5
    assert data["minimum_order_quantity"] == 50
    assert data["is_active"] is True


def test_10_inventory_manager_can_create_supplier(tokens):
    res = client.post("/suppliers", headers=tokens["manager"], json={
        "name": "Global Components Ltd",
        "contact_person": "Bob Jones",
        "email": "bob@globalcomp.com",
        "phone": "+1-555-0288",
        "lead_time_days": 10,
        "minimum_order_quantity": 100,
    })
    assert res.status_code == 201
    assert res.json()["name"] == "Global Components Ltd"


def test_11_warehouse_staff_cannot_modify_supplier(tokens):
    res = client.post("/suppliers", headers=tokens["staff"], json={
        "name": "Unauthorized Supplier",
        "email": "unauth@example.com",
        "phone": "555-1234",
        "lead_time_days": 2,
        "minimum_order_quantity": 10,
    })
    assert res.status_code == 403

    res_put = client.put("/suppliers/1", headers=tokens["staff"], json={
        "name": "Modified by Staff",
    })
    assert res_put.status_code == 403


def test_12_supplier_list_works(tokens):
    res = client.get("/suppliers", headers=tokens["staff"])
    assert res.status_code == 200
    names = [s["name"] for s in res.json()]
    assert "Apex Logistics Inc" in names
    assert "Global Components Ltd" in names


def test_13_supplier_retrieval_works(tokens):
    res = client.get("/suppliers/1", headers=tokens["staff"])
    assert res.status_code == 200
    assert res.json()["name"] == "Apex Logistics Inc"

    res_404 = client.get("/suppliers/9999", headers=tokens["staff"])
    assert res_404.status_code == 404


def test_14_invalid_email_is_rejected(tokens):
    res = client.post("/suppliers", headers=tokens["admin"], json={
        "name": "Bad Email Supplier",
        "email": "not-an-email",
        "phone": "555-0123",
        "lead_time_days": 3,
        "minimum_order_quantity": 10,
    })
    assert res.status_code == 422


def test_15_invalid_lead_time_is_rejected(tokens):
    res = client.post("/suppliers", headers=tokens["admin"], json={
        "name": "Negative Lead Time Supplier",
        "email": "valid@example.com",
        "phone": "555-0123",
        "lead_time_days": -5,  # Invalid
        "minimum_order_quantity": 10,
    })
    assert res.status_code in (400, 422)


def test_16_invalid_minimum_order_quantity_is_rejected(tokens):
    res = client.post("/suppliers", headers=tokens["admin"], json={
        "name": "Zero MOQ Supplier",
        "email": "valid@example.com",
        "phone": "555-0123",
        "lead_time_days": 3,
        "minimum_order_quantity": 0,  # Invalid (> 0 required)
    })
    assert res.status_code in (400, 422)


def test_17_supplier_update_works(tokens):
    res = client.put("/suppliers/1", headers=tokens["manager"], json={
        "lead_time_days": 7,
        "contact_person": "Alice Smith-Davis",
    })
    assert res.status_code == 200
    assert res.json()["lead_time_days"] == 7
    assert res.json()["contact_person"] == "Alice Smith-Davis"


# ==============================================================================
# PRODUCT TESTS (18-30)
# ==============================================================================
def test_18_admin_can_create_product(tokens):
    res = client.post("/products", headers=tokens["admin"], json={
        "name": "Wireless Ergonomic Mouse",
        "sku": "TECH-MOU-001",
        "description": "High-precision wireless optical mouse",
        "category_id": 1,  # Electronics
        "supplier_id": 1,  # Apex Logistics Inc
        "price": 49.99,
        "reorder_point": 20,
        "safety_stock": 10,
        "target_stock": 100,
    })
    assert res.status_code == 201
    data = res.json()
    assert data["name"] == "Wireless Ergonomic Mouse"
    assert data["sku"] == "TECH-MOU-001"
    assert data["price"] == 49.99
    assert data["target_stock"] == 100
    assert data["is_active"] is True


def test_19_inventory_manager_can_create_product(tokens):
    res = client.post("/products", headers=tokens["manager"], json={
        "name": "Mechanical Keyboard RGB",
        "sku": "TECH-KEY-002",
        "description": "Tactile switch keyboard",
        "category_id": 1,
        "supplier_id": 2,
        "price": 119.50,
        "reorder_point": 15,
        "safety_stock": 5,
        "target_stock": 80,
    })
    assert res.status_code == 201
    assert res.json()["sku"] == "TECH-KEY-002"


def test_20_warehouse_staff_cannot_create_product(tokens):
    res = client.post("/products", headers=tokens["staff"], json={
        "name": "Staff Created Monitor",
        "sku": "TECH-MON-003",
        "category_id": 1,
        "supplier_id": 1,
        "price": 299.99,
        "reorder_point": 5,
        "safety_stock": 2,
        "target_stock": 20,
    })
    assert res.status_code == 403


def test_21_product_creation_fails_for_nonexistent_category(tokens):
    res = client.post("/products", headers=tokens["admin"], json={
        "name": "Bad Category Product",
        "sku": "BAD-CAT-001",
        "category_id": 9999,  # Non-existent
        "supplier_id": 1,
        "price": 10.0,
        "reorder_point": 5,
        "safety_stock": 2,
        "target_stock": 20,
    })
    assert res.status_code == 400
    assert "Category with ID 9999 does not exist" in res.json()["detail"]


def test_22_product_creation_fails_for_nonexistent_supplier(tokens):
    res = client.post("/products", headers=tokens["admin"], json={
        "name": "Bad Supplier Product",
        "sku": "BAD-SUP-001",
        "category_id": 1,
        "supplier_id": 9999,  # Non-existent
        "price": 10.0,
        "reorder_point": 5,
        "safety_stock": 2,
        "target_stock": 20,
    })
    assert res.status_code == 400
    assert "Supplier with ID 9999 does not exist" in res.json()["detail"]


def test_23_product_creation_fails_for_inactive_category(tokens):
    # Category with ID 3 was deactivated in test_08
    res = client.post("/products", headers=tokens["admin"], json={
        "name": "Inactive Cat Product",
        "sku": "INACT-CAT-001",
        "category_id": 3,
        "supplier_id": 1,
        "price": 15.0,
        "reorder_point": 5,
        "safety_stock": 2,
        "target_stock": 20,
    })
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"]


def test_24_product_creation_fails_for_inactive_supplier(tokens):
    # Create supplier and deactivate it
    sup_res = client.post("/suppliers", headers=tokens["admin"], json={
        "name": "Inactive Supplier Corp",
        "email": "inact@supplier.com",
        "phone": "555-9988",
        "lead_time_days": 5,
        "minimum_order_quantity": 25,
    })
    inact_sup_id = sup_res.json()["id"]
    client.delete(f"/suppliers/{inact_sup_id}", headers=tokens["admin"])

    res = client.post("/products", headers=tokens["admin"], json={
        "name": "Inactive Sup Product",
        "sku": "INACT-SUP-001",
        "category_id": 1,
        "supplier_id": inact_sup_id,
        "price": 20.0,
        "reorder_point": 5,
        "safety_stock": 2,
        "target_stock": 20,
    })
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"]


def test_25_duplicate_sku_is_rejected(tokens):
    res = client.post("/products", headers=tokens["admin"], json={
        "name": "Duplicate Mouse",
        "sku": "TECH-MOU-001",  # already exists
        "category_id": 1,
        "supplier_id": 1,
        "price": 39.99,
        "reorder_point": 10,
        "safety_stock": 5,
        "target_stock": 50,
    })
    assert res.status_code == 400
    assert "already exists" in res.json()["detail"]


def test_26_product_retrieval_works(tokens):
    res = client.get("/products/1", headers=tokens["staff"])
    assert res.status_code == 200
    assert res.json()["sku"] == "TECH-MOU-001"

    res_404 = client.get("/products/9999", headers=tokens["staff"])
    assert res_404.status_code == 404


def test_27_product_update_works(tokens):
    res = client.put("/products/1", headers=tokens["manager"], json={
        "price": 54.99,
        "target_stock": 120,
    })
    assert res.status_code == 200
    assert res.json()["price"] == 54.99
    assert res.json()["target_stock"] == 120


def test_28_product_filtering_works(tokens):
    # Filter by category_id
    res_cat = client.get("/products?category_id=1", headers=tokens["staff"])
    assert res_cat.status_code == 200
    assert len(res_cat.json()) >= 2

    # Filter by supplier_id
    res_sup = client.get("/products?supplier_id=2", headers=tokens["staff"])
    assert res_sup.status_code == 200
    assert all(p["supplier_id"] == 2 for p in res_sup.json())

    # Filter by is_active
    res_act = client.get("/products?is_active=true", headers=tokens["staff"])
    assert res_act.status_code == 200
    assert all(p["is_active"] is True for p in res_act.json())


def test_29_product_search_works(tokens):
    # Search by name substring
    res_name = client.get("/products?search=keyboard", headers=tokens["staff"])
    assert res_name.status_code == 200
    assert any("Keyboard" in p["name"] for p in res_name.json())

    # Search by SKU
    res_sku = client.get("/products?sku=TECH-MOU", headers=tokens["staff"])
    assert res_sku.status_code == 200
    assert any(p["sku"] == "TECH-MOU-001" for p in res_sku.json())


def test_30_product_deactivation_works(tokens):
    # Soft delete product 2
    del_res = client.delete("/products/2", headers=tokens["admin"])
    assert del_res.status_code == 200
    assert del_res.json()["is_active"] is False

    # Confirm it is still retrievable with is_active = False
    get_res = client.get("/products/2", headers=tokens["staff"])
    assert get_res.status_code == 200
    assert get_res.json()["is_active"] is False


def test_referential_integrity_blocks_deletion_of_referenced_category(tokens):
    """Verify that deleting a category referenced by products is blocked."""
    res = client.delete("/categories/1", headers=tokens["admin"])
    assert res.status_code == 400
    assert "referenced by existing products" in res.json()["detail"]


def test_referential_integrity_blocks_deletion_of_referenced_supplier(tokens):
    """Verify that deleting a supplier referenced by products is blocked."""
    res = client.delete("/suppliers/1", headers=tokens["admin"])
    assert res.status_code == 400
    assert "referenced by existing products" in res.json()["detail"]


# ==============================================================================
# SECURITY & RBAC TESTS (31-33)
# ==============================================================================
def test_31_unauthenticated_requests_are_rejected():
    res_cat = client.get("/categories")
    assert res_cat.status_code == 401

    res_sup = client.get("/suppliers")
    assert res_sup.status_code == 401

    res_prod = client.get("/products")
    assert res_prod.status_code == 401


def test_32_role_restrictions_work(tokens):
    # Staff cannot modify category
    res1 = client.put("/categories/1", headers=tokens["staff"], json={"name": "New Name"})
    assert res1.status_code == 403

    # Staff cannot delete supplier
    res2 = client.delete("/suppliers/1", headers=tokens["staff"])
    assert res2.status_code == 403

    # Staff cannot delete product
    res3 = client.delete("/products/1", headers=tokens["staff"])
    assert res3.status_code == 403


def test_33_phase2_authentication_remains_functional():
    # Register new user
    reg_res = client.post("/auth/register", json={
        "username": "phase3_test_user",
        "email": "p3test@example.com",
        "password": "Password123!",
        "role": "INVENTORY_MANAGER",
    })
    assert reg_res.status_code == 201

    # Login
    log_res = client.post("/auth/login", json={
        "username": "phase3_test_user",
        "password": "Password123!",
    })
    assert log_res.status_code == 200
    assert "access_token" in log_res.json()


# ==============================================================================
# REGRESSION TESTS (34-40)
# ==============================================================================
def test_34_get_root_works():
    res = client.get("/")
    assert res.status_code == 200
    assert res.json() == {
        "message": "Smart Inventory & Stock Replenishment Platform API",
        "status": "running",
    }


def test_35_get_health_works():
    res = client.get("/health")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


def test_36_docs_works():
    res = client.get("/docs")
    assert res.status_code == 200


def test_37_redoc_works():
    res = client.get("/redoc")
    assert res.status_code == 200


def test_38_existing_auth_endpoints_work():
    res = client.post("/auth/login", json={
        "username": "admin_p3",
        "password": "WrongPassword!",
    })
    assert res.status_code == 401


def test_39_existing_users_me_works(tokens):
    res = client.get("/users/me", headers=tokens["admin"])
    assert res.status_code == 200
    assert res.json()["username"] == "admin_p3"


def test_40_existing_admin_authorization_test_works(tokens):
    # Admin accesses admin-test -> 200
    res_admin = client.get("/users/admin-test", headers=tokens["admin"])
    assert res_admin.status_code == 200

    # Manager accesses admin-test -> 403
    res_mgr = client.get("/users/admin-test", headers=tokens["manager"])
    assert res_mgr.status_code == 403
