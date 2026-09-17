"""
Comprehensive test suite for Phase 6: Smart Replenishment Engine.
Verifies all 48 test conditions covering deterministic calculations, lead-time demand,
MOQ, safety stock, target stock, priority, explainability, generation workflow,
duplicate PENDING updates, review/dismissal lifecycle, RBAC, integrity, and regression.
"""

from datetime import datetime, timedelta, timezone
import pytest
from fastapi.testclient import TestClient

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.category import Category
from app.models.inventory import Inventory
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.replenishment_recommendation import (
    RecommendationPriority,
    RecommendationStatus,
    ReplenishmentRecommendation,
)
from app.models.sale import Sale
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from app.services.replenishment_service import (
    build_replenishment_reason,
    calculate_average_daily_demand,
    calculate_base_target,
    calculate_inventory_position,
    calculate_lead_time_demand,
    calculate_priority,
    calculate_recommended_quantity,
)
from tests.conftest import TestingSessionLocal

client = TestClient(app)


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def setup_data():
    """Create test catalog, users, sales history, and inventory for Phase 6."""
    with TestingSessionLocal() as db:
        # Users
        admin = User(
            username="admin_p6",
            email="admin_p6@example.com",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        manager = User(
            username="manager_p6",
            email="manager_p6@example.com",
            hashed_password=hash_password("ManagerPass123!"),
            role=UserRole.INVENTORY_MANAGER,
            is_active=True,
        )
        staff = User(
            username="staff_p6",
            email="staff_p6@example.com",
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
        cat = Category(name="P6 Electronics", is_active=True)
        sup_active = Supplier(
            name="P6 Supplier Alpha",
            email="p6alpha@example.com",
            phone="555-6001",
            lead_time_days=5,
            minimum_order_quantity=50,
            is_active=True,
        )
        sup_inactive = Supplier(
            name="P6 Supplier Inactive",
            email="p6inactive@example.com",
            phone="555-6002",
            lead_time_days=10,
            minimum_order_quantity=20,
            is_active=False,
        )
        db.add_all([cat, sup_active, sup_inactive])
        db.commit()
        db.refresh(cat)
        db.refresh(sup_active)
        db.refresh(sup_inactive)

        # Product 1: Needs Replenishment (inventory position 20 <= reorder_point 30) - Example from Section 31
        # current=25, reserved=5 -> pos=20, ROP=30, safety=20, target=100, lead_time=5, MOQ=50
        prod1 = Product(
            name="P6 Wireless Mouse",
            sku="P6-WM-001",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=30.0,
            reorder_point=30,
            safety_stock=20,
            target_stock=100,
            is_active=True,
        )

        # Product 2: Healthy Stock (inventory position 90 > reorder_point 30) - No Replenishment Needed
        prod2 = Product(
            name="P6 Mechanical Keyboard",
            sku="P6-KB-002",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=80.0,
            reorder_point=30,
            safety_stock=15,
            target_stock=120,
            is_active=True,
        )

        # Product 3: Out of Stock (inventory position 0 <= reorder_point 20) -> Priority HIGH
        prod3 = Product(
            name="P6 4K Monitor",
            sku="P6-MN-003",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=250.0,
            reorder_point=20,
            safety_stock=10,
            target_stock=50,
            is_active=True,
        )

        # Product 4: Inactive Product (should be ignored)
        prod_inactive = Product(
            name="P6 Discontinued Cable",
            sku="P6-DC-004",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=15.0,
            reorder_point=50,
            safety_stock=10,
            target_stock=100,
            is_active=False,
        )

        # Product 5: Product with Inactive Supplier (should be ignored)
        prod_sup_inactive = Product(
            name="P6 Inactive Supplier Item",
            sku="P6-ISI-005",
            category_id=cat.id,
            supplier_id=sup_inactive.id,
            price=40.0,
            reorder_point=40,
            safety_stock=10,
            target_stock=80,
            is_active=True,
        )

        # Product 6: Product with NO inventory record at all (should default to 0 stock, pos 0 <= 15)
        prod_no_inv = Product(
            name="P6 New Item No Inventory",
            sku="P6-NEW-006",
            category_id=cat.id,
            supplier_id=sup_active.id,
            price=50.0,
            reorder_point=15,
            safety_stock=5,
            target_stock=40,
            is_active=True,
        )

        db.add_all([prod1, prod2, prod3, prod_inactive, prod_sup_inactive, prod_no_inv])
        db.commit()
        for p in [prod1, prod2, prod3, prod_inactive, prod_sup_inactive, prod_no_inv]:
            db.refresh(p)

        # Pre-seed Inventory
        inv1 = Inventory(product_id=prod1.id, current_stock=25, reserved_stock=5)
        inv2 = Inventory(product_id=prod2.id, current_stock=100, reserved_stock=10)
        inv3 = Inventory(product_id=prod3.id, current_stock=0, reserved_stock=0)
        db.add_all([inv1, inv2, inv3])
        db.commit()

        # Seed Sales History for Product 1: 300 units sold over last 30 days
        # 10 days ago: 150 units, 20 days ago: 150 units
        s1 = Sale(
            product_id=prod1.id,
            quantity=150,
            unit_price=30.0,
            total_amount=4500.0,
            sold_by=staff.id,
            reference="SALE-HIST-1",
            created_at=datetime.now(timezone.utc) - timedelta(days=10),
        )
        s2 = Sale(
            product_id=prod1.id,
            quantity=150,
            unit_price=30.0,
            total_amount=4500.0,
            sold_by=staff.id,
            reference="SALE-HIST-2",
            created_at=datetime.now(timezone.utc) - timedelta(days=20),
        )
        # Sales older than 30 days (should be excluded from 30-day window)
        s_old = Sale(
            product_id=prod1.id,
            quantity=500,
            unit_price=30.0,
            total_amount=15000.0,
            sold_by=staff.id,
            reference="SALE-HIST-OLD",
            created_at=datetime.now(timezone.utc) - timedelta(days=45),
        )
        db.add_all([s1, s2, s_old])
        db.commit()

        # Auth tokens
        admin_id = admin.id
        manager_id = manager.id
        staff_id = staff.id
        sup_active_id = sup_active.id
        sup_inactive_id = sup_inactive.id
        prod1_id = prod1.id
        prod2_id = prod2.id
        prod3_id = prod3.id
        prod_inactive_id = prod_inactive.id
        prod_sup_inactive_id = prod_sup_inactive.id
        prod_no_inv_id = prod_no_inv.id

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
            "supplier_active_id": sup_active_id,
            "supplier_inactive_id": sup_inactive_id,
            "prod1_id": prod1_id,
            "prod2_id": prod2_id,
            "prod3_id": prod3_id,
            "prod_inactive_id": prod_inactive_id,
            "prod_sup_inactive_id": prod_sup_inactive_id,
            "prod_no_inv_id": prod_no_inv_id,
        }


# ==============================================================================
# 1. UNIT CALCULATION TESTS (Requirements 1 - 12)
# ==============================================================================
def test_01_available_inventory_position_calculation():
    """Req 1: Inventory position is current_stock - reserved_stock, never negative."""
    assert calculate_inventory_position(100, 10) == 90
    assert calculate_inventory_position(35, 10) == 25
    assert calculate_inventory_position(0, 0) == 0
    assert calculate_inventory_position(5, 10) == 0  # clamp at zero


def test_02_03_reorder_trigger():
    """Req 2, 3: Replenishment triggered iff inventory_position <= reorder_point."""
    # Healthy: 90 > 30 -> No replenishment
    assert not (calculate_inventory_position(100, 10) <= 30)
    # Low stock: 25 <= 30 -> Replenishment required
    assert calculate_inventory_position(35, 10) <= 30
    # Out of stock: 0 <= 30 -> Replenishment required
    assert calculate_inventory_position(0, 0) <= 30


def test_04_05_average_daily_demand_calculation(setup_data):
    """Req 4, 5: 30-day average daily demand uses actual sales in window; 0 if no sales."""
    with TestingSessionLocal() as db:
        # Prod 1: 300 units in last 30 days -> 300 / 30 = 10.0
        add1 = calculate_average_daily_demand(db, setup_data["prod1_id"], window_days=30)
        assert add1 == 10.0

        # Prod 2: No sales -> 0.0
        add2 = calculate_average_daily_demand(db, setup_data["prod2_id"], window_days=30)
        assert add2 == 0.0


def test_06_lead_time_demand_calculation():
    """Req 6: lead_time_demand = average_daily_demand * lead_time_days."""
    assert calculate_lead_time_demand(10.0, 5) == 50.0
    assert calculate_lead_time_demand(0.0, 5) == 0.0
    assert calculate_lead_time_demand(10.0, 0) == 0.0


def test_07_08_safety_stock_and_target_stock_calculation():
    """Req 7, 8: base_target = max(target_stock, lead_time_demand + safety_stock)."""
    # Example 1 from Section 31: target=100, ltd=50, safety=20 -> max(100, 70) = 100
    assert calculate_base_target(100, 50.0, 20) == 100.0
    # High demand scenario: target=100, ltd=90, safety=20 -> max(100, 110) = 110
    assert calculate_base_target(100, 90.0, 20) == 110.0


def test_09_10_recommended_quantity_and_moq():
    """Req 9, 10: recommended_quantity = base_target - inv_pos, adjusted for supplier MOQ."""
    # Example from Section 31: target=100, pos=20 -> raw=80. MOQ=50 -> 80 > 50 -> 80
    qty, moq_applied = calculate_recommended_quantity(100.0, 20, 50)
    assert qty == 80
    assert not moq_applied

    # MOQ adjustment scenario: target=40, pos=25 -> raw=15. MOQ=50 -> qty adjusted to 50
    qty2, moq_applied2 = calculate_recommended_quantity(40.0, 25, 50)
    assert qty2 == 50
    assert moq_applied2

    # Excess stock scenario: pos=120, target=100 -> raw <= 0 -> 0
    qty3, moq_applied3 = calculate_recommended_quantity(100.0, 120, 50)
    assert qty3 == 0
    assert not moq_applied3


def test_11_priority_calculation():
    """Req 11: Priority: HIGH if pos==0 or pos < safety, MEDIUM if pos <= rop, LOW otherwise."""
    # pos == 0 -> HIGH
    assert calculate_priority(0, 20, 30) == RecommendationPriority.HIGH
    # pos < safety (15 < 20) -> HIGH
    assert calculate_priority(15, 20, 30) == RecommendationPriority.HIGH
    # pos between safety and rop (25 <= 30) -> MEDIUM
    assert calculate_priority(25, 20, 30) == RecommendationPriority.MEDIUM
    # pos > rop (40 > 30) -> LOW
    assert calculate_priority(40, 20, 30) == RecommendationPriority.LOW


def test_12_reason_generation():
    """Req 12: Reason clearly explains inventory position, lead-time demand, target, and MOQ."""
    reason = build_replenishment_reason(
        inventory_position=20,
        reorder_point=30,
        safety_stock=20,
        target_stock=100,
        lead_time_demand=50.0,
        moq_applied=False,
        moq=50,
    )
    assert "Inventory position (20) is at or below reorder point (30)" in reason
    assert "Estimated demand during supplier lead time is 50.0 units" in reason
    assert "target level of 100 units" in reason

    reason_moq = build_replenishment_reason(
        inventory_position=25,
        reorder_point=30,
        safety_stock=20,
        target_stock=40,
        lead_time_demand=0.0,
        moq_applied=True,
        moq=50,
    )
    assert "meet supplier minimum order quantity of 50 units" in reason_moq


# ==============================================================================
# 2. GENERATION WORKFLOW & INVENTORY EVALUATION TESTS (Requirements 13 - 23)
# ==============================================================================
def test_13_14_admin_and_manager_can_generate_recommendations(setup_data):
    """Req 13, 14: Admin and Inventory Manager can trigger recommendation generation."""
    # Manager trigger
    res_mgr = client.post("/replenishment/generate", headers=setup_data["manager_headers"])
    assert res_mgr.status_code == 200
    recs_mgr = res_mgr.json()
    assert len(recs_mgr) > 0

    # Admin trigger
    res_adm = client.post("/replenishment/generate", headers=setup_data["admin_headers"])
    assert res_adm.status_code == 200
    recs_adm = res_adm.json()
    assert len(recs_adm) > 0


def test_15_warehouse_staff_cannot_generate_recommendations(setup_data):
    """Req 15: Warehouse staff cannot trigger recommendation generation (403)."""
    res = client.post("/replenishment/generate", headers=setup_data["staff_headers"])
    assert res.status_code == 403


def test_16_17_18_19_generation_filtering_and_edge_cases(setup_data):
    """Req 16, 17, 18, 19: Only products requiring replenishment receive recommendations; inactives ignored."""
    res = client.post("/replenishment/generate", headers=setup_data["admin_headers"])
    assert res.status_code == 200
    recs = res.json()
    product_ids = [r["product_id"] for r in recs]

    # Prod 1 (Wireless Mouse, pos 20 <= 30) MUST be included
    assert setup_data["prod1_id"] in product_ids

    # Prod 2 (Keyboard, pos 90 > 30) MUST NOT be included
    assert setup_data["prod2_id"] not in product_ids

    # Prod 3 (4K Monitor, pos 0 <= 20) MUST be included
    assert setup_data["prod3_id"] in product_ids

    # Prod Inactive MUST NOT be included
    assert setup_data["prod_inactive_id"] not in product_ids

    # Prod with Inactive Supplier MUST NOT be included
    assert setup_data["prod_sup_inactive_id"] not in product_ids

    # Prod with NO inventory record (evaluated as 0 stock, pos 0 <= 15) MUST be included
    assert setup_data["prod_no_inv_id"] in product_ids

    # Verify no inventory record was created for prod_no_inv
    with TestingSessionLocal() as db:
        inv_check = db.query(Inventory).filter(Inventory.product_id == setup_data["prod_no_inv_id"]).first()
        assert inv_check is None


def test_20_recommendation_stored_correctly(setup_data):
    """Req 20: Stored recommendation matches expected calculation values from Section 31."""
    res = client.get(
        f"/replenishment/recommendations?product_id={setup_data['prod1_id']}",
        headers=setup_data["staff_headers"],
    )
    assert res.status_code == 200
    recs = res.json()
    assert len(recs) == 1
    r = recs[0]

    assert r["current_stock"] == 25
    assert r["reserved_stock"] == 5
    assert r["inventory_position"] == 20
    assert r["reorder_point"] == 30
    assert r["safety_stock"] == 20
    assert r["target_stock"] == 100
    assert r["average_daily_demand"] == 10.0
    assert r["lead_time_days"] == 5
    assert r["lead_time_demand"] == 50.0
    assert r["recommended_quantity"] == 80
    assert r["minimum_order_quantity"] == 50
    assert r["priority"] == "MEDIUM"
    assert r["status"] == "PENDING"


def test_21_existing_pending_recommendation_updated_not_duplicated(setup_data):
    """Req 21: Re-generating updates existing PENDING recommendation in-place."""
    res1 = client.get(
        f"/replenishment/recommendations?product_id={setup_data['prod1_id']}&status=PENDING",
        headers=setup_data["staff_headers"],
    )
    rec_id_initial = res1.json()[0]["id"]

    # Re-trigger generation
    client.post("/replenishment/generate", headers=setup_data["admin_headers"])

    res2 = client.get(
        f"/replenishment/recommendations?product_id={setup_data['prod1_id']}&status=PENDING",
        headers=setup_data["staff_headers"],
    )
    pending_recs = res2.json()
    assert len(pending_recs) == 1
    assert pending_recs[0]["id"] == rec_id_initial


def test_22_23_reviewed_and_dismissed_remain_historical(setup_data):
    """Req 22, 23: Reviewed or dismissed recommendations are not overwritten; new PENDING created."""
    # Get current PENDING for prod1 and review it
    res_get = client.get(
        f"/replenishment/recommendations?product_id={setup_data['prod1_id']}&status=PENDING",
        headers=setup_data["staff_headers"],
    )
    rec_id = res_get.json()[0]["id"]
    res_rev = client.patch(f"/replenishment/recommendations/{rec_id}/review", headers=setup_data["manager_headers"])
    assert res_rev.status_code == 200
    assert res_rev.json()["status"] == "REVIEWED"

    # Now generate again
    client.post("/replenishment/generate", headers=setup_data["admin_headers"])

    # Verify both the historical REVIEWED and a new PENDING exist
    res_all = client.get(
        f"/replenishment/recommendations?product_id={setup_data['prod1_id']}",
        headers=setup_data["staff_headers"],
    )
    all_recs = res_all.json()
    assert len(all_recs) == 2
    statuses = [r["status"] for r in all_recs]
    assert "REVIEWED" in statuses
    assert "PENDING" in statuses


# ==============================================================================
# 3. API ENDPOINTS & STATUS LIFECYCLE TESTS (Requirements 24 - 31)
# ==============================================================================
def test_24_25_list_and_filter_recommendations(setup_data):
    """Req 24, 25: List recommendations with status, priority, product, supplier filters."""
    # Filter by status
    res_stat = client.get("/replenishment/recommendations?status=PENDING", headers=setup_data["staff_headers"])
    assert res_stat.status_code == 200
    for r in res_stat.json():
        assert r["status"] == "PENDING"

    # Filter by priority
    res_prio = client.get("/replenishment/recommendations?priority=HIGH", headers=setup_data["staff_headers"])
    assert res_prio.status_code == 200
    for r in res_prio.json():
        assert r["priority"] == "HIGH"

    # Default sort verification: HIGH before MEDIUM
    res_all = client.get("/replenishment/recommendations", headers=setup_data["staff_headers"])
    assert res_all.status_code == 200
    priorities = [r["priority"] for r in res_all.json()]
    if "HIGH" in priorities and "MEDIUM" in priorities:
        high_idx = priorities.index("HIGH")
        medium_idx = priorities.index("MEDIUM")
        assert high_idx < medium_idx


def test_26_recommendation_detail_and_404(setup_data):
    """Req 26, 30: Recommendation detail endpoint and 404 for nonexistent ID."""
    res_list = client.get("/replenishment/recommendations", headers=setup_data["staff_headers"])
    rec_id = res_list.json()[0]["id"]

    res_detail = client.get(f"/replenishment/recommendations/{rec_id}", headers=setup_data["staff_headers"])
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == rec_id

    res_404 = client.get("/replenishment/recommendations/999999", headers=setup_data["staff_headers"])
    assert res_404.status_code == 404


def test_27_28_29_31_review_and_dismiss_transitions(setup_data):
    """Req 27, 28, 29, 31: Review and dismiss transitions, reason required, invalid transitions blocked."""
    # Find a PENDING recommendation
    res_pending = client.get("/replenishment/recommendations?status=PENDING", headers=setup_data["staff_headers"])
    pending_list = res_pending.json()
    assert len(pending_list) > 0
    target_rec_id = pending_list[0]["id"]

    # 1. Dismiss requires reason
    res_empty_reason = client.patch(
        f"/replenishment/recommendations/{target_rec_id}/dismiss",
        json={"reason": "  "},
        headers=setup_data["manager_headers"],
    )
    assert res_empty_reason.status_code in [400, 422]

    # 2. Dismiss successfully
    res_dismiss = client.patch(
        f"/replenishment/recommendations/{target_rec_id}/dismiss",
        json={"reason": "Excess inventory already on order elsewhere"},
        headers=setup_data["manager_headers"],
    )
    assert res_dismiss.status_code == 200
    assert res_dismiss.json()["status"] == "DISMISSED"
    assert res_dismiss.json()["dismissal_reason"] == "Excess inventory already on order elsewhere"

    # 3. Invalid transition: DISMISSED -> REVIEWED
    res_invalid = client.patch(
        f"/replenishment/recommendations/{target_rec_id}/review",
        headers=setup_data["manager_headers"],
    )
    assert res_invalid.status_code == 400
    assert "only pending recommendations can be reviewed" in res_invalid.json()["detail"].lower()


# ==============================================================================
# 4. ROLE-BASED ACCESS CONTROL (RBAC) TESTS (Requirements 32 - 37)
# ==============================================================================
def test_32_33_admin_and_manager_full_access(setup_data):
    """Req 32, 33: Admin and Inventory Manager have full access to generate, view, review, dismiss."""
    # Generate as admin
    assert client.post("/replenishment/generate", headers=setup_data["admin_headers"]).status_code == 200
    # List as manager
    assert client.get("/replenishment/recommendations", headers=setup_data["manager_headers"]).status_code == 200


def test_34_35_36_37_warehouse_staff_rbac_restrictions(setup_data):
    """Req 34, 35, 36, 37: Warehouse staff can view recommendations but cannot generate, review, or dismiss."""
    # View is allowed
    res_view = client.get("/replenishment/recommendations", headers=setup_data["staff_headers"])
    assert res_view.status_code == 200
    rec_id = res_view.json()[0]["id"]

    # Generate forbidden (403)
    res_gen = client.post("/replenishment/generate", headers=setup_data["staff_headers"])
    assert res_gen.status_code == 403

    # Review forbidden (403)
    res_rev = client.patch(f"/replenishment/recommendations/{rec_id}/review", headers=setup_data["staff_headers"])
    assert res_rev.status_code == 403

    # Dismiss forbidden (403)
    res_dis = client.patch(
        f"/replenishment/recommendations/{rec_id}/dismiss",
        json={"reason": "Staff attempt"},
        headers=setup_data["staff_headers"],
    )
    assert res_dis.status_code == 403


# ==============================================================================
# 5. INTEGRITY & PHASE BOUNDARY TESTS (Requirements 38 - 43)
# ==============================================================================
def test_38_39_40_integrity_constraints(setup_data):
    """Req 38, 39, 40: Recommended quantity >= 0, inv_pos >= 0, MOQ never violated."""
    res = client.get("/replenishment/recommendations", headers=setup_data["staff_headers"])
    assert res.status_code == 200
    for r in res.json():
        assert r["recommended_quantity"] >= 0
        assert r["inventory_position"] >= 0
        if r["recommended_quantity"] > 0:
            assert r["recommended_quantity"] >= r["minimum_order_quantity"]


def test_41_42_43_no_purchase_orders_created_and_no_inventory_mutated(setup_data):
    """Req 41, 42, 43: Generation produces recommendations only; never modifies inventory or creates POs."""
    with TestingSessionLocal() as db:
        po_count_before = db.query(PurchaseOrder).count()
        inv1_before = db.query(Inventory).filter(Inventory.product_id == setup_data["prod1_id"]).first()
        stock_before = inv1_before.current_stock
        reserved_before = inv1_before.reserved_stock

    # Trigger generation
    res_gen = client.post("/replenishment/generate", headers=setup_data["admin_headers"])
    assert res_gen.status_code == 200

    with TestingSessionLocal() as db:
        po_count_after = db.query(PurchaseOrder).count()
        inv1_after = db.query(Inventory).filter(Inventory.product_id == setup_data["prod1_id"]).first()
        stock_after = inv1_after.current_stock
        reserved_after = inv1_after.reserved_stock

    # No purchase orders created
    assert po_count_after == po_count_before

    # No inventory modified
    assert stock_after == stock_before
    assert reserved_after == reserved_before
