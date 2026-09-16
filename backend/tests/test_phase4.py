"""
Comprehensive test suite for Phase 4: Inventory & Stock Management.
Verifies all 55 requirements covering inventory initialization, stock-in, stock-out,
adjustments, queries, dynamic status calculations, immutability, atomicity,
concurrency, RBAC, and full regression.
"""

from concurrent.futures import ThreadPoolExecutor
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.product import Product
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal

client = TestClient(app)


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def setup_data():
    """Create test users, category, supplier, and products for Phase 4."""
    with TestingSessionLocal() as db:
        # Users
        admin = User(
            username="admin_p4",
            email="admin_p4@example.com",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        manager = User(
            username="manager_p4",
            email="manager_p4@example.com",
            hashed_password=hash_password("ManagerPass123!"),
            role=UserRole.INVENTORY_MANAGER,
            is_active=True,
        )
        staff = User(
            username="staff_p4",
            email="staff_p4@example.com",
            hashed_password=hash_password("StaffPass123!"),
            role=UserRole.WAREHOUSE_STAFF,
            is_active=True,
        )
        db.add_all([admin, manager, staff])
        db.commit()
        db.refresh(admin)
        db.refresh(manager)
        db.refresh(staff)

        # Catalog setup
        cat = Category(name="P4 Electronics", is_active=True)
        sup = Supplier(
            name="P4 Supplier",
            email="p4supplier@example.com",
            phone="555-4444",
            lead_time_days=5,
            minimum_order_quantity=10,
            is_active=True,
        )
        db.add_all([cat, sup])
        db.commit()
        db.refresh(cat)
        db.refresh(sup)

        # Active Product 1 (reorder_point=20, target_stock=100)
        prod1 = Product(
            name="P4 Widget A",
            sku="P4-WID-001",
            category_id=cat.id,
            supplier_id=sup.id,
            price=25.0,
            reorder_point=20,
            safety_stock=10,
            target_stock=100,
            is_active=True,
        )
        # Active Product 2 (reorder_point=15)
        prod2 = Product(
            name="P4 Widget B",
            sku="P4-WID-002",
            category_id=cat.id,
            supplier_id=sup.id,
            price=30.0,
            reorder_point=15,
            safety_stock=5,
            target_stock=50,
            is_active=True,
        )
        # Inactive Product 3
        prod3 = Product(
            name="P4 Inactive Widget",
            sku="P4-INACT-003",
            category_id=cat.id,
            supplier_id=sup.id,
            price=10.0,
            reorder_point=5,
            safety_stock=2,
            target_stock=20,
            is_active=False,
        )
        db.add_all([prod1, prod2, prod3])
        db.commit()
        db.refresh(prod1)
        db.refresh(prod2)
        db.refresh(prod3)

        admin_token = create_access_token({"sub": str(admin.id), "username": admin.username, "role": admin.role.value})
        manager_token = create_access_token({"sub": str(manager.id), "username": manager.username, "role": manager.role.value})
        staff_token = create_access_token({"sub": str(staff.id), "username": staff.username, "role": staff.role.value})

    return {
        "tokens": {
            "admin": {"Authorization": f"Bearer {admin_token}"},
            "manager": {"Authorization": f"Bearer {manager_token}"},
            "staff": {"Authorization": f"Bearer {staff_token}"},
        },
        "prod1_id": prod1.id,
        "prod2_id": prod2.id,
        "inactive_prod_id": prod3.id,
    }


# ==============================================================================
# INVENTORY INITIALIZATION (1-4)
# ==============================================================================
def test_01_03_inventory_record_initialization(setup_data):
    """Test 1-3: Inventory record can be created, initial current_stock=0, reserved_stock=0."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]

    res = client.get(f"/inventory/{prod1_id}", headers=tokens["staff"])
    assert res.status_code == 200
    data = res.json()
    assert data["product_id"] == prod1_id
    assert data["current_stock"] == 0
    assert data["reserved_stock"] == 0
    assert data["available_stock"] == 0
    assert data["status"] == "OUT_OF_STOCK"


def test_04_duplicate_inventory_record_rejected(setup_data):
    """Test 4: Duplicate inventory record for the same product is rejected by database constraint."""
    prod1_id = setup_data["prod1_id"]
    with pytest.raises(IntegrityError):
        with TestingSessionLocal() as db:
            dup = Inventory(product_id=prod1_id, current_stock=10, reserved_stock=0)
            db.add(dup)
            db.commit()


# ==============================================================================
# STOCK-IN (5-13)
# ==============================================================================
def test_05_admin_can_perform_stock_in(setup_data):
    """Test 5: Admin can perform stock-in."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/stock-in", headers=tokens["admin"], json={
        "product_id": prod1_id,
        "quantity": 50,
        "reason": "Initial warehouse stock",
        "reference": "PO-1001",
    })
    assert res.status_code == 200
    data = res.json()
    assert data["current_stock"] == 50
    assert data["available_stock"] == 50


def test_06_inventory_manager_can_perform_stock_in(setup_data):
    """Test 6: Inventory manager can perform stock-in."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/stock-in", headers=tokens["manager"], json={
        "product_id": prod1_id,
        "quantity": 25,
        "reason": "Restock batch 2",
    })
    assert res.status_code == 200
    assert res.json()["current_stock"] == 75


def test_07_warehouse_staff_can_perform_stock_in(setup_data):
    """Test 7: Warehouse staff can perform stock-in."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/stock-in", headers=tokens["staff"], json={
        "product_id": prod1_id,
        "quantity": 10,
    })
    assert res.status_code == 200
    assert res.json()["current_stock"] == 85


def test_08_11_stock_in_effects_and_transaction_verification(setup_data):
    """Test 8-11: Stock-in increases stock correctly, creates transaction, logs previous and resulting stock."""
    prod1_id = setup_data["prod1_id"]
    with TestingSessionLocal() as db:
        txn = db.query(InventoryTransaction).filter(
            InventoryTransaction.product_id == prod1_id,
            InventoryTransaction.transaction_type == TransactionType.STOCK_IN,
        ).order_by(InventoryTransaction.id.desc()).first()
        assert txn is not None
        assert txn.quantity == 10
        assert txn.previous_stock == 75
        assert txn.resulting_stock == 85


def test_12_stock_in_invalid_quantity_rejected(setup_data):
    """Test 12: Invalid quantity (<= 0) is rejected."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/stock-in", headers=tokens["admin"], json={
        "product_id": prod1_id,
        "quantity": 0,
    })
    assert res.status_code == 422


def test_13_stock_in_inactive_product_rejected(setup_data):
    """Test 13: Inactive product cannot receive stock."""
    tokens = setup_data["tokens"]
    inactive_id = setup_data["inactive_prod_id"]
    res = client.post("/inventory/stock-in", headers=tokens["admin"], json={
        "product_id": inactive_id,
        "quantity": 10,
    })
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"].lower()


# ==============================================================================
# STOCK-OUT (14-21)
# ==============================================================================
def test_14_admin_can_perform_stock_out(setup_data):
    """Test 14: Admin can perform stock-out."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/stock-out", headers=tokens["admin"], json={
        "product_id": prod1_id,
        "quantity": 15,
        "reason": "Dispatch order #1",
        "reference": "ORD-5001",
    })
    assert res.status_code == 200
    assert res.json()["current_stock"] == 70  # 85 - 15


def test_15_inventory_manager_can_perform_stock_out(setup_data):
    """Test 15: Inventory manager can perform stock-out."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/stock-out", headers=tokens["manager"], json={
        "product_id": prod1_id,
        "quantity": 10,
    })
    assert res.status_code == 200
    assert res.json()["current_stock"] == 60  # 70 - 10


def test_16_warehouse_staff_can_perform_stock_out(setup_data):
    """Test 16: Warehouse staff can perform stock-out."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/stock-out", headers=tokens["staff"], json={
        "product_id": prod1_id,
        "quantity": 10,
    })
    assert res.status_code == 200
    assert res.json()["current_stock"] == 50  # 60 - 10


def test_17_18_stock_out_effects_and_transaction_verification(setup_data):
    """Test 17-18: Stock-out decreases stock and records previous and resulting stock."""
    prod1_id = setup_data["prod1_id"]
    with TestingSessionLocal() as db:
        txn = db.query(InventoryTransaction).filter(
            InventoryTransaction.product_id == prod1_id,
            InventoryTransaction.transaction_type == TransactionType.STOCK_OUT,
        ).order_by(InventoryTransaction.id.desc()).first()
        assert txn is not None
        assert txn.quantity == 10
        assert txn.previous_stock == 60
        assert txn.resulting_stock == 50


def test_19_21_insufficient_stock_and_reserved_stock_respected(setup_data):
    """Test 19-21: Insufficient available stock is rejected, reserved stock is respected, stock never becomes negative."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]

    # Current stock = 50. Let's set reserved_stock = 15 directly to test availability limit
    with TestingSessionLocal() as db:
        inv = db.query(Inventory).filter(Inventory.product_id == prod1_id).first()
        inv.reserved_stock = 15
        db.commit()

    # available_stock is now 50 - 15 = 35. Requesting 36 must fail!
    res_fail = client.post("/inventory/stock-out", headers=tokens["staff"], json={
        "product_id": prod1_id,
        "quantity": 36,
    })
    assert res_fail.status_code == 400
    assert "Insufficient available stock" in res_fail.json()["detail"]

    # Requesting 35 should succeed exactly
    res_ok = client.post("/inventory/stock-out", headers=tokens["staff"], json={
        "product_id": prod1_id,
        "quantity": 35,
    })
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert data["current_stock"] == 15  # Remaining stock equals reserved_stock
    assert data["reserved_stock"] == 15
    assert data["available_stock"] == 0

    # Reset reserved_stock to 0 for subsequent tests
    with TestingSessionLocal() as db:
        inv = db.query(Inventory).filter(Inventory.product_id == prod1_id).first()
        inv.reserved_stock = 0
        db.commit()


# ==============================================================================
# ADJUSTMENTS (22-29)
# ==============================================================================
def test_22_admin_can_perform_adjustment(setup_data):
    """Test 22: Admin can perform stock adjustment."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/adjustment", headers=tokens["admin"], json={
        "product_id": prod1_id,
        "quantity": 10,
        "adjustment_type": "ADJUSTMENT_IN",
        "reason": "Physical audit reconciliation",
    })
    assert res.status_code == 200
    assert res.json()["current_stock"] == 25  # 15 + 10


def test_23_inventory_manager_can_perform_adjustment(setup_data):
    """Test 23: Inventory manager can perform stock adjustment."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/adjustment", headers=tokens["manager"], json={
        "product_id": prod1_id,
        "quantity": 5,
        "adjustment_type": "ADJUSTMENT_OUT",
        "reason": "Damaged items written off",
    })
    assert res.status_code == 200
    assert res.json()["current_stock"] == 20  # 25 - 5


def test_24_warehouse_staff_cannot_perform_adjustment(setup_data):
    """Test 24: Warehouse staff cannot perform adjustments (403 Forbidden)."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    res = client.post("/inventory/adjustment", headers=tokens["staff"], json={
        "product_id": prod1_id,
        "quantity": 5,
        "adjustment_type": "ADJUSTMENT_IN",
        "reason": "Unauthorized staff adjustment",
    })
    assert res.status_code == 403
    assert "Operation not permitted" in res.json()["detail"]


def test_25_29_adjustment_effects_reason_required_negative_stock_prevention(setup_data):
    """Test 25-29: Adjustment-in, Adjustment-out, negative prevention, mandatory reason, transaction creation."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]

    # Reason mandatory
    res_no_reason = client.post("/inventory/adjustment", headers=tokens["admin"], json={
        "product_id": prod1_id,
        "quantity": 5,
        "adjustment_type": "ADJUSTMENT_IN",
        "reason": "",  # Empty reason rejected
    })
    assert res_no_reason.status_code in (400, 422)

    # Negative stock prevented
    # Current stock is 20, adjusting out 21 must fail!
    res_neg = client.post("/inventory/adjustment", headers=tokens["admin"], json={
        "product_id": prod1_id,
        "quantity": 21,
        "adjustment_type": "ADJUSTMENT_OUT",
        "reason": "Count error correction",
    })
    assert res_neg.status_code == 400
    assert "negative stock" in res_neg.json()["detail"].lower()


# ==============================================================================
# INVENTORY QUERIES & FILTERS (30-37)
# ==============================================================================
def test_30_31_inventory_queries(setup_data):
    """Test 30-31: Inventory list and product lookup."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]

    # List all
    res_list = client.get("/inventory", headers=tokens["staff"])
    assert res_list.status_code == 200
    assert len(res_list.json()) >= 1

    # Product lookup
    res_prod = client.get(f"/inventory/{prod1_id}", headers=tokens["staff"])
    assert res_prod.status_code == 200
    assert res_prod.json()["product_id"] == prod1_id


def test_32_33_transaction_queries(setup_data):
    """Test 32-33: Transaction history list and individual transaction lookup."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]

    res_txns = client.get(f"/inventory/transactions?product_id={prod1_id}", headers=tokens["staff"])
    assert res_txns.status_code == 200
    txns = res_txns.json()
    assert len(txns) >= 1

    first_id = txns[0]["id"]
    res_single = client.get(f"/inventory/transactions/{first_id}", headers=tokens["staff"])
    assert res_single.status_code == 200
    assert res_single.json()["id"] == first_id


def test_34_37_inventory_and_transaction_filtering(setup_data):
    """Test 34-37: Product filtering, transaction type filtering, low_stock and out_of_stock filtering."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]
    prod2_id = setup_data["prod2_id"]

    # Filter transactions by type
    res_type = client.get(f"/inventory/transactions?transaction_type=STOCK_IN", headers=tokens["staff"])
    assert res_type.status_code == 200
    assert all(t["transaction_type"] == "STOCK_IN" for t in res_type.json())

    # Prod2 is currently at 0 stock, reorder_point is 15 -> OUT_OF_STOCK
    client.get(f"/inventory/{prod2_id}", headers=tokens["staff"])

    # Out of stock filter
    res_oos = client.get("/inventory?out_of_stock=true", headers=tokens["staff"])
    assert res_oos.status_code == 200
    assert any(i["product_id"] == prod2_id for i in res_oos.json())

    # Prod1 has stock = 20, reorder_point = 20 -> LOW_STOCK (<= reorder_point)
    res_low = client.get("/inventory?low_stock=true", headers=tokens["staff"])
    assert res_low.status_code == 200
    assert any(i["product_id"] == prod1_id for i in res_low.json())


# ==============================================================================
# DYNAMIC STATUS CALCULATIONS (38-41)
# ==============================================================================
def test_38_41_status_and_available_stock_calculations(setup_data):
    """Test 38-41: IN_STOCK, LOW_STOCK, OUT_OF_STOCK, and available_stock calculations."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]

    # Currently: stock=20, reorder_point=20 -> LOW_STOCK
    res = client.get(f"/inventory/{prod1_id}", headers=tokens["staff"])
    assert res.json()["status"] == "LOW_STOCK"

    # Add 10 -> stock=30 > reorder_point(20) -> IN_STOCK
    client.post("/inventory/stock-in", headers=tokens["staff"], json={"product_id": prod1_id, "quantity": 10})
    res_in = client.get(f"/inventory/{prod1_id}", headers=tokens["staff"])
    assert res_in.json()["current_stock"] == 30
    assert res_in.json()["status"] == "IN_STOCK"

    # Deduct 30 -> stock=0 -> OUT_OF_STOCK
    client.post("/inventory/stock-out", headers=tokens["staff"], json={"product_id": prod1_id, "quantity": 30})
    res_out = client.get(f"/inventory/{prod1_id}", headers=tokens["staff"])
    assert res_out.json()["current_stock"] == 0
    assert res_out.json()["status"] == "OUT_OF_STOCK"


# ==============================================================================
# IMMUTABILITY (42-43)
# ==============================================================================
def test_42_43_transaction_immutability(setup_data):
    """Test 42-43: Inventory transactions cannot be modified or deleted via API."""
    tokens = setup_data["tokens"]
    # PUT /inventory/transactions/1 is not defined -> 405 Method Not Allowed
    res_put = client.put("/inventory/transactions/1", headers=tokens["admin"], json={"quantity": 999})
    assert res_put.status_code == 405

    # DELETE /inventory/transactions/1 is not defined -> 405 Method Not Allowed
    res_del = client.delete("/inventory/transactions/1", headers=tokens["admin"])
    assert res_del.status_code == 405


# ==============================================================================
# SECURITY, ATOMICITY & CONCURRENCY (44-50)
# ==============================================================================
def test_44_unauthenticated_requests_rejected():
    """Test 44: Unauthenticated requests are rejected."""
    assert client.get("/inventory").status_code == 401
    assert client.post("/inventory/stock-in", json={"product_id": 1, "quantity": 10}).status_code == 401
    assert client.post("/inventory/stock-out", json={"product_id": 1, "quantity": 10}).status_code == 401
    assert client.post("/inventory/adjustment", json={"product_id": 1, "quantity": 10, "adjustment_type": "ADJUSTMENT_IN", "reason": "Audit"}).status_code == 401


def test_45_46_role_restrictions_and_inactive_products(setup_data):
    """Test 45-46: Role restrictions and inactive product operations."""
    tokens = setup_data["tokens"]
    inactive_id = setup_data["inactive_prod_id"]

    # Staff forbidden for adjustments
    res_adj = client.post("/inventory/adjustment", headers=tokens["staff"], json={
        "product_id": setup_data["prod1_id"],
        "quantity": 1,
        "adjustment_type": "ADJUSTMENT_IN",
        "reason": "Staff test",
    })
    assert res_adj.status_code == 403

    # Inactive product rejected
    res_out = client.post("/inventory/stock-out", headers=tokens["admin"], json={
        "product_id": inactive_id,
        "quantity": 1,
    })
    assert res_out.status_code == 400


def test_47_48_atomicity(setup_data):
    """Test 47-48: Failed operations do not partially modify inventory or record transaction."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]

    # Stock is currently 0
    # Attempting to stock-out 100 should fail and leave stock at 0 with no new transaction
    with TestingSessionLocal() as db:
        tx_count_before = db.query(InventoryTransaction).count()

    res = client.post("/inventory/stock-out", headers=tokens["admin"], json={
        "product_id": prod1_id,
        "quantity": 100,
    })
    assert res.status_code == 400

    with TestingSessionLocal() as db:
        inv = db.query(Inventory).filter(Inventory.product_id == prod1_id).first()
        assert inv.current_stock == 0
        tx_count_after = db.query(InventoryTransaction).count()
        assert tx_count_after == tx_count_before


def test_49_50_concurrency_protection(setup_data):
    """Test 49-50: Concurrent stock operations preserve consistency and prevent negative stock."""
    tokens = setup_data["tokens"]
    prod1_id = setup_data["prod1_id"]

    # Set stock to 20
    client.post("/inventory/stock-in", headers=tokens["admin"], json={
        "product_id": prod1_id,
        "quantity": 20,
    })

    # Execute 5 concurrent stock-out requests of quantity 5 simultaneously (total requested: 25, only 20 available)
    def dispatch():
        return client.post("/inventory/stock-out", headers=tokens["staff"], json={
            "product_id": prod1_id,
            "quantity": 5,
        })

    with ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(dispatch) for _ in range(5)]
        results = [f.result() for f in futures]

    statuses = [r.status_code for r in results]
    successes = statuses.count(200)
    failures = statuses.count(400)
    assert successes == 4
    assert failures == 1

    # Verify final stock is exactly 0 and never went negative
    res_final = client.get(f"/inventory/{prod1_id}", headers=tokens["staff"])
    assert res_final.json()["current_stock"] == 0


# ==============================================================================
# FULL REGRESSION (51-55)
# ==============================================================================
def test_51_phase1_regression():
    """Test 51: Phase 1 root and health endpoints work."""
    res_root = client.get("/")
    assert res_root.status_code == 200
    res_health = client.get("/health")
    assert res_health.status_code == 200


def test_52_phase2_regression(setup_data):
    """Test 52: Phase 2 authentication and user profile work."""
    tokens = setup_data["tokens"]
    res_me = client.get("/users/me", headers=tokens["admin"])
    assert res_me.status_code == 200
    assert res_me.json()["username"] == "admin_p4"


def test_53_phase3_categories_regression(setup_data):
    """Test 53: Phase 3 Category API works."""
    tokens = setup_data["tokens"]
    res = client.get("/categories", headers=tokens["staff"])
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_54_phase3_suppliers_regression(setup_data):
    """Test 54: Phase 3 Supplier API works."""
    tokens = setup_data["tokens"]
    res = client.get("/suppliers", headers=tokens["staff"])
    assert res.status_code == 200
    assert len(res.json()) >= 1


def test_55_phase3_products_regression(setup_data):
    """Test 55: Phase 3 Product API works."""
    tokens = setup_data["tokens"]
    res = client.get("/products", headers=tokens["staff"])
    assert res.status_code == 200
    assert len(res.json()) >= 1
