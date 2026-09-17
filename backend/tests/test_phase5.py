"""
Comprehensive test suite for Phase 5: Sales & Purchase Order Management.
Verifies all 55 requirements covering sales recording, sales history, PO creation,
PO items, status transitions, partial/full receiving, inventory ledger integration,
concurrency, atomicity, RBAC, and full regression.
"""

from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.sale import Sale
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from tests.conftest import TestingSessionLocal

client = TestClient(app)


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def setup_data():
    """Create test users, categories, suppliers, and products for Phase 5."""
    with TestingSessionLocal() as db:
        # Users
        admin = User(
            username="admin_p5",
            email="admin_p5@example.com",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        manager = User(
            username="manager_p5",
            email="manager_p5@example.com",
            hashed_password=hash_password("ManagerPass123!"),
            role=UserRole.INVENTORY_MANAGER,
            is_active=True,
        )
        staff = User(
            username="staff_p5",
            email="staff_p5@example.com",
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
        cat = Category(name="P5 Electronics", is_active=True)
        sup_active = Supplier(
            name="P5 Active Supplier",
            email="p5active@example.com",
            phone="555-5001",
            lead_time_days=3,
            minimum_order_quantity=5,
            is_active=True,
        )
        sup_inactive = Supplier(
            name="P5 Inactive Supplier",
            email="p5inactive@example.com",
            phone="555-5002",
            lead_time_days=10,
            minimum_order_quantity=1,
            is_active=False,
        )
        db.add_all([cat, sup_active, sup_inactive])
        db.commit()
        db.refresh(cat)
        db.refresh(sup_active)
        db.refresh(sup_inactive)

        # Products
        prod1 = Product(
            name="P5 Keyboard Pro",
            sku="P5-KB-001",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=100.0,
            reorder_point=20,
            safety_stock=10,
            target_stock=150,
            is_active=True,
        )
        prod2 = Product(
            name="P5 Mouse Wireless",
            sku="P5-MS-002",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=50.0,
            reorder_point=15,
            safety_stock=5,
            target_stock=80,
            is_active=True,
        )
        prod3 = Product(
            name="P5 Monitor 4K",
            sku="P5-MN-003",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=300.0,
            reorder_point=5,
            safety_stock=2,
            target_stock=30,
            is_active=True,
        )
        prod_inactive = Product(
            name="P5 Discontinued Item",
            sku="P5-DISC-004",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=25.0,
            reorder_point=0,
            safety_stock=0,
            target_stock=1,
            is_active=False,
        )
        db.add_all([prod1, prod2, prod3, prod_inactive])
        db.commit()
        db.refresh(prod1)
        db.refresh(prod2)
        db.refresh(prod3)
        db.refresh(prod_inactive)

        # Pre-seed Inventory
        inv1 = Inventory(product_id=prod1.id, current_stock=100, reserved_stock=0)
        inv2 = Inventory(product_id=prod2.id, current_stock=50, reserved_stock=0)
        inv3 = Inventory(product_id=prod3.id, current_stock=0, reserved_stock=0)
        db.add_all([inv1, inv2, inv3])
        db.commit()

        # Auth tokens
        admin_id = admin.id
        manager_id = manager.id
        staff_id = staff.id
        supplier_active_id = sup_active.id
        supplier_inactive_id = sup_inactive.id
        prod1_id = prod1.id
        prod2_id = prod2.id
        prod3_id = prod3.id
        prod_inactive_id = prod_inactive.id

        admin_token = create_access_token(data={"sub": str(admin_id), "role": admin.role.value})
        manager_token = create_access_token(data={"sub": str(manager_id), "role": manager.role.value})
        staff_token = create_access_token(data={"sub": str(staff_id), "role": staff.role.value})

        return {
            "admin_id": admin_id,
            "manager_id": manager_id,
            "staff_id": staff_id,
            "admin_headers": {"Authorization": f"Bearer {admin_token}"},
            "manager_headers": {"Authorization": f"Bearer {manager_token}"},
            "staff_headers": {"Authorization": f"Bearer {staff_token}"},
            "supplier_active_id": supplier_active_id,
            "supplier_inactive_id": supplier_inactive_id,
            "prod1_id": prod1_id,
            "prod2_id": prod2_id,
            "prod3_id": prod3_id,
            "prod_inactive_id": prod_inactive_id,
        }


# ==============================================================================
# 1. SALES WORKFLOW TESTS (Requirements 1 - 18)
# ==============================================================================
def test_01_authorized_users_can_create_sale(setup_data):
    """Req 1: Admin, Inventory Manager, and Warehouse Staff can record sales."""
    for headers in [setup_data["admin_headers"], setup_data["manager_headers"], setup_data["staff_headers"]]:
        res = client.post(
            "/sales",
            json={"product_id": setup_data["prod1_id"], "quantity": 2, "unit_price": 95.0},
            headers=headers,
        )
        assert res.status_code == 201
        data = res.json()
        assert data["quantity"] == 2
        assert data["unit_price"] == 95.0
        assert data["total_amount"] == 190.0


def test_02_unauthorized_user_cannot_create_sale(setup_data):
    """Req 2: Unauthenticated and unauthorized users cannot create sales."""
    # No auth
    res = client.post("/sales", json={"product_id": setup_data["prod1_id"], "quantity": 1})
    assert res.status_code == 401

    # Invalid token
    res = client.post(
        "/sales",
        json={"product_id": setup_data["prod1_id"], "quantity": 1},
        headers={"Authorization": "Bearer invalid.jwt.token"},
    )
    assert res.status_code == 401


def test_03_sale_validates_product_existence(setup_data):
    """Req 3: Sale creation rejects nonexistent products."""
    res = client.post(
        "/sales",
        json={"product_id": 999999, "quantity": 1},
        headers=setup_data["staff_headers"],
    )
    assert res.status_code == 404
    assert "not found" in res.json()["detail"].lower()


def test_04_sale_rejects_inactive_product(setup_data):
    """Req 4: Sale creation rejects inactive products."""
    res = client.post(
        "/sales",
        json={"product_id": setup_data["prod_inactive_id"], "quantity": 1},
        headers=setup_data["staff_headers"],
    )
    assert res.status_code == 400
    assert "inactive product" in res.json()["detail"].lower()


def test_05_sale_validates_quantity(setup_data):
    """Req 5: Sale rejects zero or negative quantities."""
    for invalid_qty in [0, -5]:
        res = client.post(
            "/sales",
            json={"product_id": setup_data["prod1_id"], "quantity": invalid_qty},
            headers=setup_data["staff_headers"],
        )
        assert res.status_code in [400, 422]


def test_06_sale_rejects_insufficient_stock(setup_data):
    """Req 6: Sale creation is rejected when stock is insufficient."""
    # prod3 currently has 0 stock
    res = client.post(
        "/sales",
        json={"product_id": setup_data["prod3_id"], "quantity": 1},
        headers=setup_data["staff_headers"],
    )
    assert res.status_code == 400
    assert "insufficient available stock" in res.json()["detail"].lower()


def test_07_08_09_10_successful_sale_updates_inventory_and_creates_ledger(setup_data):
    """Req 7, 8, 9, 10: Sale reduces current_stock and registers immutable STOCK_OUT transaction."""
    prod_id = setup_data["prod2_id"]
    # Check current stock
    res_inv = client.get(f"/inventory/{prod_id}", headers=setup_data["staff_headers"])
    assert res_inv.status_code == 200
    pre_stock = res_inv.json()["current_stock"]

    # Execute sale
    res_sale = client.post(
        "/sales",
        json={"product_id": prod_id, "quantity": 10, "reference": "INV-2026-TEST"},
        headers=setup_data["staff_headers"],
    )
    assert res_sale.status_code == 201

    # Check updated stock
    res_inv2 = client.get(f"/inventory/{prod_id}", headers=setup_data["staff_headers"])
    post_stock = res_inv2.json()["current_stock"]
    assert post_stock == pre_stock - 10

    # Verify transaction ledger
    res_tx = client.get(f"/inventory/transactions?product_id={prod_id}", headers=setup_data["staff_headers"])
    assert res_tx.status_code == 200
    txs = res_tx.json()
    assert len(txs) > 0
    latest_tx = txs[0]
    assert latest_tx["transaction_type"] == "STOCK_OUT"
    assert latest_tx["quantity"] == 10
    assert latest_tx["previous_stock"] == pre_stock
    assert latest_tx["resulting_stock"] == post_stock
    assert latest_tx["reference"] == "INV-2026-TEST"


def test_11_sale_total_is_calculated_correctly(setup_data):
    """Req 11: Sale total is calculated from quantity * unit_price (using product price when omitted)."""
    # Explicit price: 3 * 80.0 = 240.0
    res = client.post(
        "/sales",
        json={"product_id": setup_data["prod1_id"], "quantity": 3, "unit_price": 80.0},
        headers=setup_data["staff_headers"],
    )
    assert res.status_code == 201
    assert res.json()["total_amount"] == 240.0

    # Omitted price: prod1 price is 100.0, 2 * 100.0 = 200.0
    res2 = client.post(
        "/sales",
        json={"product_id": setup_data["prod1_id"], "quantity": 2},
        headers=setup_data["staff_headers"],
    )
    assert res2.status_code == 201
    assert res2.json()["unit_price"] == 100.0
    assert res2.json()["total_amount"] == 200.0


def test_12_sale_history_and_filters(setup_data):
    """Req 12: Sales history endpoint supports product, user, reference, and date filters."""
    res = client.get("/sales", headers=setup_data["staff_headers"])
    assert res.status_code == 200
    all_sales = res.json()
    assert len(all_sales) > 0

    # Filter by product
    res_filt = client.get(f"/sales?product_id={setup_data['prod2_id']}", headers=setup_data["staff_headers"])
    assert res_filt.status_code == 200
    for s in res_filt.json():
        assert s["product_id"] == setup_data["prod2_id"]


def test_13_sale_detail_works(setup_data):
    """Req 13: Sale detail endpoint retrieves specific sale."""
    res_list = client.get("/sales", headers=setup_data["staff_headers"])
    sale_id = res_list.json()[0]["id"]

    res_detail = client.get(f"/sales/{sale_id}", headers=setup_data["staff_headers"])
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == sale_id

    # 404 for nonexistent sale
    res_404 = client.get("/sales/999999", headers=setup_data["staff_headers"])
    assert res_404.status_code == 404


def test_14_15_sales_cannot_be_modified_or_deleted(setup_data):
    """Req 14, 15: Sales are immutable historical records; PUT and DELETE return 405."""
    res_list = client.get("/sales", headers=setup_data["staff_headers"])
    sale_id = res_list.json()[0]["id"]

    res_put = client.put(f"/sales/{sale_id}", json={"quantity": 1}, headers=setup_data["admin_headers"])
    assert res_put.status_code == 405

    res_del = client.delete(f"/sales/{sale_id}", headers=setup_data["admin_headers"])
    assert res_del.status_code == 405


def test_16_17_failed_sale_does_not_modify_inventory_or_create_record(setup_data):
    """Req 16, 17: Atomicity: failed sale does not alter stock or create records."""
    prod_id = setup_data["prod2_id"]
    res_inv = client.get(f"/inventory/{prod_id}", headers=setup_data["staff_headers"])
    initial_stock = res_inv.json()["current_stock"]

    res_count = client.get("/sales", headers=setup_data["staff_headers"])
    initial_sales_count = len(res_count.json())

    # Attempt sale exceeding stock
    res_fail = client.post(
        "/sales",
        json={"product_id": prod_id, "quantity": initial_stock + 100},
        headers=setup_data["staff_headers"],
    )
    assert res_fail.status_code == 400

    # Verify inventory and sales count remain strictly unchanged
    res_inv2 = client.get(f"/inventory/{prod_id}", headers=setup_data["staff_headers"])
    assert res_inv2.json()["current_stock"] == initial_stock

    res_count2 = client.get("/sales", headers=setup_data["staff_headers"])
    assert len(res_count2.json()) == initial_sales_count


def test_18_concurrent_sales_cannot_produce_negative_stock(setup_data):
    """Req 18: Concurrency: simultaneous sales cannot drive stock below 0."""
    # Product with exactly 10 units available
    with TestingSessionLocal() as db:
        prod_conc = Product(
            name="P5 Concurrent Test Item",
            sku="P5-CONC-001",
            category_id=1,
            supplier_id=setup_data["supplier_active_id"],
            price=10.0,
            is_active=True,
        )
        db.add(prod_conc)
        db.commit()
        db.refresh(prod_conc)

        inv_conc = Inventory(product_id=prod_conc.id, current_stock=10, reserved_stock=0)
        db.add(inv_conc)
        db.commit()
        prod_conc_id = prod_conc.id

    def attempt_sale(_):
        return client.post(
            "/sales",
            json={"product_id": prod_conc_id, "quantity": 4},
            headers=setup_data["staff_headers"],
        )

    # Launch 5 concurrent threads each trying to purchase 4 units (total demand 20, stock 10)
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(attempt_sale, range(5)))

    successes = [r for r in results if r.status_code == 201]
    failures = [r for r in results if r.status_code == 400]

    # Exactly 2 should succeed (2 * 4 = 8 units sold, 2 remaining), others fail
    assert len(successes) == 2
    assert len(failures) == 3

    # Check final stock
    res_inv = client.get(f"/inventory/{prod_conc_id}", headers=setup_data["staff_headers"])
    assert res_inv.json()["current_stock"] == 2


# ==============================================================================
# 2. PURCHASE ORDER WORKFLOW TESTS (Requirements 19 - 39)
# ==============================================================================
def test_19_20_admin_and_manager_can_create_purchase_order(setup_data):
    """Req 19, 20: Admin and Inventory Manager can create purchase orders."""
    po_payload = {
        "supplier_id": setup_data["supplier_active_id"],
        "items": [
            {"product_id": setup_data["prod1_id"], "quantity": 20, "unit_cost": 75.0},
            {"product_id": setup_data["prod2_id"], "quantity": 10, "unit_cost": 40.0},
        ],
        "notes": "Initial test order",
    }

    # Admin creation
    res_admin = client.post("/purchase-orders", json=po_payload, headers=setup_data["admin_headers"])
    assert res_admin.status_code == 201
    assert res_admin.json()["status"] == "DRAFT"

    # Manager creation
    res_mgr = client.post("/purchase-orders", json=po_payload, headers=setup_data["manager_headers"])
    assert res_mgr.status_code == 201
    assert res_mgr.json()["status"] == "DRAFT"


def test_21_warehouse_staff_cannot_create_or_approve_purchase_order(setup_data):
    """Req 21: Warehouse staff cannot create or approve purchase orders."""
    po_payload = {
        "supplier_id": setup_data["supplier_active_id"],
        "items": [{"product_id": setup_data["prod1_id"], "quantity": 10, "unit_cost": 50.0}],
    }
    # Creation forbidden
    res_create = client.post("/purchase-orders", json=po_payload, headers=setup_data["staff_headers"])
    assert res_create.status_code == 403

    # Create order as manager first
    res_mgr = client.post("/purchase-orders", json=po_payload, headers=setup_data["manager_headers"])
    po_id = res_mgr.json()["id"]

    # Approval forbidden for warehouse staff
    res_approve = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "APPROVED"},
        headers=setup_data["staff_headers"],
    )
    assert res_approve.status_code == 403


def test_22_23_po_supplier_validation(setup_data):
    """Req 22, 23: Supplier existence and active status are strictly validated."""
    item = [{"product_id": setup_data["prod1_id"], "quantity": 5, "unit_cost": 10.0}]

    # Nonexistent supplier
    res_404 = client.post(
        "/purchase-orders",
        json={"supplier_id": 999999, "items": item},
        headers=setup_data["admin_headers"],
    )
    assert res_404.status_code == 404

    # Inactive supplier
    res_400 = client.post(
        "/purchase-orders",
        json={"supplier_id": setup_data["supplier_inactive_id"], "items": item},
        headers=setup_data["admin_headers"],
    )
    assert res_400.status_code == 400
    assert "inactive supplier" in res_400.json()["detail"].lower()


def test_24_25_po_product_validation(setup_data):
    """Req 24, 25: Product existence and active status are validated."""
    # Nonexistent product
    res_404 = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": 999999, "quantity": 5, "unit_cost": 10.0}],
        },
        headers=setup_data["admin_headers"],
    )
    assert res_404.status_code == 404

    # Inactive product
    res_400 = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": setup_data["prod_inactive_id"], "quantity": 5, "unit_cost": 10.0}],
        },
        headers=setup_data["admin_headers"],
    )
    assert res_400.status_code == 400
    assert "inactive product" in res_400.json()["detail"].lower()


def test_26_27_28_po_items_and_cost_validation(setup_data):
    """Req 26, 27, 28: Empty items, invalid quantities, and negative costs are rejected."""
    # Empty items
    res_empty = client.post(
        "/purchase-orders",
        json={"supplier_id": setup_data["supplier_active_id"], "items": []},
        headers=setup_data["admin_headers"],
    )
    assert res_empty.status_code in [400, 422]

    # Invalid quantity <= 0
    res_qty = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": setup_data["prod1_id"], "quantity": 0, "unit_cost": 10.0}],
        },
        headers=setup_data["admin_headers"],
    )
    assert res_qty.status_code in [400, 422]

    # Negative unit cost
    res_cost = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": setup_data["prod1_id"], "quantity": 5, "unit_cost": -10.0}],
        },
        headers=setup_data["admin_headers"],
    )
    assert res_cost.status_code in [400, 422]


def test_29_30_po_total_calculation_and_tamper_resistance(setup_data):
    """Req 29, 30: Backend calculates total_amount; client manipulation is ignored/prevented."""
    # Item 1: 10 * 100 = 1000; Item 2: 5 * 250 = 1250; Expected total: 2250.0
    payload = {
        "supplier_id": setup_data["supplier_active_id"],
        "total_amount": 99.99,  # Attempted manipulation
        "items": [
            {"product_id": setup_data["prod1_id"], "quantity": 10, "unit_cost": 100.0},
            {"product_id": setup_data["prod2_id"], "quantity": 5, "unit_cost": 250.0},
        ],
    }
    res = client.post("/purchase-orders", json=payload, headers=setup_data["admin_headers"])
    assert res.status_code == 201
    data = res.json()
    assert data["total_amount"] == 2250.0


def test_31_unique_order_number_generated(setup_data):
    """Req 31: Unique purchase order numbers are generated."""
    payload = {
        "supplier_id": setup_data["supplier_active_id"],
        "items": [{"product_id": setup_data["prod1_id"], "quantity": 5, "unit_cost": 10.0}],
    }
    res1 = client.post("/purchase-orders", json=payload, headers=setup_data["admin_headers"])
    res2 = client.post("/purchase-orders", json=payload, headers=setup_data["admin_headers"])
    assert res1.status_code == 201
    assert res2.status_code == 201
    num1 = res1.json()["order_number"]
    num2 = res2.json()["order_number"]
    assert num1 != num2
    assert num1.startswith("PO-")


def test_32_draft_order_can_be_updated(setup_data):
    """Req 32: DRAFT order can be modified."""
    # Create draft
    res_create = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "notes": "Draft v1",
            "items": [{"product_id": setup_data["prod1_id"], "quantity": 5, "unit_cost": 50.0}],
        },
        headers=setup_data["manager_headers"],
    )
    po_id = res_create.json()["id"]

    # Update draft
    res_update = client.put(
        f"/purchase-orders/{po_id}",
        json={
            "notes": "Draft v2 updated",
            "items": [{"product_id": setup_data["prod1_id"], "quantity": 10, "unit_cost": 45.0}],
        },
        headers=setup_data["manager_headers"],
    )
    assert res_update.status_code == 200
    data = res_update.json()
    assert data["notes"] == "Draft v2 updated"
    assert data["total_amount"] == 450.0


def test_33_34_status_transitions_and_validation(setup_data):
    """Req 33, 34: Lifecycle transitions (DRAFT -> PENDING_APPROVAL -> APPROVED -> ORDERED)."""
    # Create draft
    res = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": setup_data["prod1_id"], "quantity": 5, "unit_cost": 50.0}],
        },
        headers=setup_data["admin_headers"],
    )
    po_id = res.json()["id"]

    # Invalid jump: DRAFT -> ORDERED
    res_bad = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "ORDERED"},
        headers=setup_data["admin_headers"],
    )
    assert res_bad.status_code == 400

    # Step 1: DRAFT -> PENDING_APPROVAL
    res_pnd = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "PENDING_APPROVAL"},
        headers=setup_data["manager_headers"],
    )
    assert res_pnd.status_code == 200
    assert res_pnd.json()["status"] == "PENDING_APPROVAL"

    # Step 2: PENDING_APPROVAL -> APPROVED
    res_app = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "APPROVED"},
        headers=setup_data["admin_headers"],
    )
    assert res_app.status_code == 200
    assert res_app.json()["status"] == "APPROVED"
    assert res_app.json()["approved_by"] == setup_data["admin_id"]

    # Step 3: APPROVED -> ORDERED
    res_ord = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "ORDERED"},
        headers=setup_data["manager_headers"],
    )
    assert res_ord.status_code == 200
    assert res_ord.json()["status"] == "ORDERED"
    assert res_ord.json()["ordered_at"] is not None

    # Invalid jump: ORDERED -> DRAFT
    res_draft_back = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "DRAFT"},
        headers=setup_data["admin_headers"],
    )
    assert res_draft_back.status_code == 400


def test_35_36_order_cancellation_and_cannot_receive_cancelled(setup_data):
    """Req 35, 36: Allowed cancellation and blocked receipt of cancelled orders."""
    # Create draft and cancel
    res = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": setup_data["prod1_id"], "quantity": 10, "unit_cost": 50.0}],
        },
        headers=setup_data["admin_headers"],
    )
    po_id = res.json()["id"]

    res_cancel = client.patch(
        f"/purchase-orders/{po_id}/status",
        json={"status": "CANCELLED"},
        headers=setup_data["admin_headers"],
    )
    assert res_cancel.status_code == 200
    assert res_cancel.json()["status"] == "CANCELLED"

    # Attempt receive on cancelled order
    res_rec = client.post(
        f"/purchase-orders/{po_id}/receive",
        json={"items": [{"product_id": setup_data["prod1_id"], "quantity": 5}]},
        headers=setup_data["staff_headers"],
    )
    assert res_rec.status_code == 400
    assert "cancelled" in res_rec.json()["detail"].lower()


def test_37_received_or_ordered_po_cannot_be_modified(setup_data):
    """Req 37: Ordered and received orders cannot be edited via PUT."""
    # Create and order a PO
    res = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": setup_data["prod1_id"], "quantity": 5, "unit_cost": 50.0}],
        },
        headers=setup_data["admin_headers"],
    )
    po_id = res.json()["id"]
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "PENDING_APPROVAL"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "APPROVED"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "ORDERED"}, headers=setup_data["admin_headers"])

    # Attempt PUT
    res_put = client.put(
        f"/purchase-orders/{po_id}",
        json={"notes": "Illegal edit on ordered PO"},
        headers=setup_data["admin_headers"],
    )
    assert res_put.status_code == 400
    assert "only draft orders can be modified" in res_put.json()["detail"].lower()


def test_38_39_purchase_order_query_and_detail(setup_data):
    """Req 38, 39: PO query with filters and single PO detail."""
    res_list = client.get("/purchase-orders", headers=setup_data["staff_headers"])
    assert res_list.status_code == 200
    orders = res_list.json()
    assert len(orders) > 0

    po_id = orders[0]["id"]
    res_detail = client.get(f"/purchase-orders/{po_id}", headers=setup_data["staff_headers"])
    assert res_detail.status_code == 200
    detail = res_detail.json()
    assert detail["id"] == po_id
    assert "items" in detail


# ==============================================================================
# 3. RECEIVING WORKFLOW TESTS (Requirements 40 - 55)
# ==============================================================================
def test_40_41_42_43_44_receive_ordered_po_and_verify_inventory_integration(setup_data):
    """Req 40, 41, 42, 43, 44: Receiving increases inventory and records STOCK_IN ledger."""
    prod_id = setup_data["prod3_id"]  # Initial stock is 0
    res_pre = client.get(f"/inventory/{prod_id}", headers=setup_data["staff_headers"])
    pre_stock = res_pre.json()["current_stock"]

    # Create and advance PO to ORDERED
    res_po = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": prod_id, "quantity": 40, "unit_cost": 200.0}],
        },
        headers=setup_data["admin_headers"],
    )
    po_id = res_po.json()["id"]
    order_num = res_po.json()["order_number"]

    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "PENDING_APPROVAL"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "APPROVED"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "ORDERED"}, headers=setup_data["admin_headers"])

    # Warehouse staff receives the goods
    res_recv = client.post(
        f"/purchase-orders/{po_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 40}]},
        headers=setup_data["staff_headers"],
    )
    assert res_recv.status_code == 200
    assert res_recv.json()["status"] == "RECEIVED"

    # Verify inventory increased
    res_post = client.get(f"/inventory/{prod_id}", headers=setup_data["staff_headers"])
    assert res_post.json()["current_stock"] == pre_stock + 40

    # Verify transaction ledger entry
    res_tx = client.get(f"/inventory/transactions?product_id={prod_id}", headers=setup_data["staff_headers"])
    latest_tx = res_tx.json()[0]
    assert latest_tx["transaction_type"] == "STOCK_IN"
    assert latest_tx["quantity"] == 40
    assert latest_tx["previous_stock"] == pre_stock
    assert latest_tx["resulting_stock"] == pre_stock + 40
    assert latest_tx["reference"] == order_num


def test_45_46_47_48_49_partial_receiving_workflow(setup_data):
    """Req 45, 46, 47, 48, 49: Partial receiving tracks received_quantity and lifecycle transitions."""
    prod_id = setup_data["prod1_id"]

    # Create PO for 100 units
    res_po = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": prod_id, "quantity": 100, "unit_cost": 80.0}],
        },
        headers=setup_data["admin_headers"],
    )
    po_id = res_po.json()["id"]

    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "PENDING_APPROVAL"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "APPROVED"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "ORDERED"}, headers=setup_data["admin_headers"])

    # Batch 1: Receive 40 units -> Status PARTIALLY_RECEIVED
    res_b1 = client.post(
        f"/purchase-orders/{po_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 40}]},
        headers=setup_data["staff_headers"],
    )
    assert res_b1.status_code == 200
    data_b1 = res_b1.json()
    assert data_b1["status"] == "PARTIALLY_RECEIVED"
    assert data_b1["items"][0]["received_quantity"] == 40

    # Batch 2: Receive 30 units -> Still PARTIALLY_RECEIVED, received_quantity = 70
    res_b2 = client.post(
        f"/purchase-orders/{po_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 30}]},
        headers=setup_data["staff_headers"],
    )
    assert res_b2.status_code == 200
    data_b2 = res_b2.json()
    assert data_b2["status"] == "PARTIALLY_RECEIVED"
    assert data_b2["items"][0]["received_quantity"] == 70

    # Batch 3: Receive remaining 30 units -> Status RECEIVED, received_at recorded
    res_b3 = client.post(
        f"/purchase-orders/{po_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 30}]},
        headers=setup_data["staff_headers"],
    )
    assert res_b3.status_code == 200
    data_b3 = res_b3.json()
    assert data_b3["status"] == "RECEIVED"
    assert data_b3["items"][0]["received_quantity"] == 100
    assert data_b3["received_at"] is not None


def test_50_over_receiving_is_rejected(setup_data):
    """Req 50: Attempting to receive more than remaining quantity is rejected."""
    prod_id = setup_data["prod2_id"]

    res_po = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": prod_id, "quantity": 50, "unit_cost": 40.0}],
        },
        headers=setup_data["admin_headers"],
    )
    po_id = res_po.json()["id"]

    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "PENDING_APPROVAL"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "APPROVED"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "ORDERED"}, headers=setup_data["admin_headers"])

    # Receive 30 first
    client.post(
        f"/purchase-orders/{po_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 30}]},
        headers=setup_data["staff_headers"],
    )

    # Remaining is 20; attempt to receive 21
    res_over = client.post(
        f"/purchase-orders/{po_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 21}]},
        headers=setup_data["staff_headers"],
    )
    assert res_over.status_code == 400
    assert "remaining to be received" in res_over.json()["detail"].lower()


def test_51_52_receiving_cancelled_or_fully_received_order_rejected(setup_data):
    """Req 51, 52: Cannot receive cancelled or already completed orders."""
    prod_id = setup_data["prod1_id"]

    # 1. Cancelled order
    res_c = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": prod_id, "quantity": 10, "unit_cost": 10.0}],
        },
        headers=setup_data["admin_headers"],
    )
    c_id = res_c.json()["id"]
    client.patch(f"/purchase-orders/{c_id}/status", json={"status": "CANCELLED"}, headers=setup_data["admin_headers"])

    res_rec_c = client.post(
        f"/purchase-orders/{c_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 5}]},
        headers=setup_data["staff_headers"],
    )
    assert res_rec_c.status_code == 400

    # 2. Fully received order
    res_f = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": prod_id, "quantity": 10, "unit_cost": 10.0}],
        },
        headers=setup_data["admin_headers"],
    )
    f_id = res_f.json()["id"]
    client.patch(f"/purchase-orders/{f_id}/status", json={"status": "PENDING_APPROVAL"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{f_id}/status", json={"status": "APPROVED"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{f_id}/status", json={"status": "ORDERED"}, headers=setup_data["admin_headers"])
    client.post(
        f"/purchase-orders/{f_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 10}]},
        headers=setup_data["staff_headers"],
    )

    # Attempt to receive again on already completed order
    res_rec_f = client.post(
        f"/purchase-orders/{f_id}/receive",
        json={"items": [{"product_id": prod_id, "quantity": 1}]},
        headers=setup_data["staff_headers"],
    )
    assert res_rec_f.status_code == 400
    assert "already been fully received" in res_rec_f.json()["detail"].lower()


def test_53_54_failed_receiving_atomicity(setup_data):
    """Req 53, 54: If any line item in a receiving batch fails, no inventory or quantities are updated."""
    prod1_id = setup_data["prod1_id"]
    prod2_id = setup_data["prod2_id"]

    res_po = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [
                {"product_id": prod1_id, "quantity": 10, "unit_cost": 50.0},
                {"product_id": prod2_id, "quantity": 10, "unit_cost": 25.0},
            ],
        },
        headers=setup_data["admin_headers"],
    )
    po_id = res_po.json()["id"]

    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "PENDING_APPROVAL"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "APPROVED"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "ORDERED"}, headers=setup_data["admin_headers"])

    # Stock before
    stock1_before = client.get(f"/inventory/{prod1_id}", headers=setup_data["staff_headers"]).json()["current_stock"]

    # Batch with item 1 valid (5), item 2 invalid over-receive (15 > 10)
    res_batch = client.post(
        f"/purchase-orders/{po_id}/receive",
        json={
            "items": [
                {"product_id": prod1_id, "quantity": 5},
                {"product_id": prod2_id, "quantity": 15},
            ]
        },
        headers=setup_data["staff_headers"],
    )
    assert res_batch.status_code == 400

    # Verify prod1 inventory was NOT incremented
    stock1_after = client.get(f"/inventory/{prod1_id}", headers=setup_data["staff_headers"]).json()["current_stock"]
    assert stock1_after == stock1_before

    # Verify PO item received_quantities remain 0
    po_after = client.get(f"/purchase-orders/{po_id}", headers=setup_data["staff_headers"]).json()
    assert po_after["items"][0]["received_quantity"] == 0
    assert po_after["items"][1]["received_quantity"] == 0


def test_55_concurrent_receiving_cannot_exceed_ordered_quantity(setup_data):
    """Req 55: Concurrent receiving requests serialize correctly and cannot exceed ordered quantity."""
    # Create product and PO with 15 units ordered
    with TestingSessionLocal() as db:
        prod_recv = Product(
            name="P5 Concurrent Receive Item",
            sku="P5-CRECV-001",
            category_id=1,
            supplier_id=setup_data["supplier_active_id"],
            price=20.0,
            is_active=True,
        )
        db.add(prod_recv)
        db.commit()
        db.refresh(prod_recv)
        prod_recv_id = prod_recv.id

    res_po = client.post(
        "/purchase-orders",
        json={
            "supplier_id": setup_data["supplier_active_id"],
            "items": [{"product_id": prod_recv_id, "quantity": 15, "unit_cost": 15.0}],
        },
        headers=setup_data["admin_headers"],
    )
    po_id = res_po.json()["id"]

    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "PENDING_APPROVAL"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "APPROVED"}, headers=setup_data["admin_headers"])
    client.patch(f"/purchase-orders/{po_id}/status", json={"status": "ORDERED"}, headers=setup_data["admin_headers"])

    def attempt_receive(_):
        return client.post(
            f"/purchase-orders/{po_id}/receive",
            json={"items": [{"product_id": prod_recv_id, "quantity": 5}]},
            headers=setup_data["staff_headers"],
        )

    # Launch 5 concurrent threads each trying to receive 5 units (total 25, ordered 15)
    with ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(attempt_receive, range(5)))

    successes = [r for r in results if r.status_code == 200]
    failures = [r for r in results if r.status_code == 400]

    # Exactly 3 should succeed (3 * 5 = 15 units), others fail
    assert len(successes) == 3
    assert len(failures) == 2

    # Check total received quantity
    po_final = client.get(f"/purchase-orders/{po_id}", headers=setup_data["staff_headers"]).json()
    assert po_final["items"][0]["received_quantity"] == 15
    assert po_final["status"] == "RECEIVED"
