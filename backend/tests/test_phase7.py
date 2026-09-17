"""
Comprehensive test suite for Phase 7: Demand Analysis & Forecasting.
Verifies all 56 testing requirements covering:
- Daily continuous sales aggregation (including zero-demand days)
- Deterministic SMA & WMA calculations
- Forecast generation, future horizon dating, persistence, and archiving
- No-sales edge cases
- REST API endpoints and query filtering
- RBAC enforcement (ADMIN/MANAGER write, STAFF read-only, 401 unauthenticated)
- Strict boundary checks (zero inventory/sales/PO mutations, unchanged configs)
- Regressions across Phases 1 through 6
"""

from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.category import Category
from app.models.demand_forecast import (
    DemandForecast,
    DemandForecastValue,
    ForecastMethod,
    ForecastStatus,
)
from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder
from app.models.sale import Sale
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from app.services.forecast_service import (
    calculate_sma,
    calculate_wma,
    generate_forecast_dates,
    generate_product_forecast,
    get_daily_sales_history,
)
from tests.conftest import TestingSessionLocal

client = TestClient(app)


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def setup_data():
    """Seed test users, categories, suppliers, products, and sales for Phase 7."""
    with TestingSessionLocal() as db:
        # 1. Users
        admin = User(
            username="admin_p7",
            email="admin_p7@example.com",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        manager = User(
            username="manager_p7",
            email="manager_p7@example.com",
            hashed_password=hash_password("ManagerPass123!"),
            role=UserRole.INVENTORY_MANAGER,
            is_active=True,
        )
        staff = User(
            username="staff_p7",
            email="staff_p7@example.com",
            hashed_password=hash_password("StaffPass123!"),
            role=UserRole.WAREHOUSE_STAFF,
            is_active=True,
        )
        db.add_all([admin, manager, staff])
        db.commit()
        db.refresh(admin)
        db.refresh(manager)
        db.refresh(staff)

        # 2. Catalog
        cat = Category(name="P7 Electronics", description="Phase 7 Category", is_active=True)
        sup = Supplier(
            name="P7 Tech Supplier",
            email="sup_p7@example.com",
            phone="123-456-7890",
            lead_time_days=5,
            minimum_order_quantity=10,
            is_active=True,
        )
        db.add_all([cat, sup])
        db.commit()
        db.refresh(cat)
        db.refresh(sup)

        # Product 1: Active Product with sales matching Example 40 & 41
        # Days 1 to 7: 10, 20, 15, 5, 10, 20, 20
        prod_active = Product(
            name="P7 Multi-Sale Widget",
            sku="P7-MSW-001",
            category_id=cat.id,
            supplier_id=sup.id,
            price=25.0,
            reorder_point=20,
            safety_stock=10,
            target_stock=80,
            is_active=True,
        )
        # Product 2: Inactive Product
        prod_inactive = Product(
            name="P7 Inactive Gadget",
            sku="P7-INACT-002",
            category_id=cat.id,
            supplier_id=sup.id,
            price=50.0,
            reorder_point=10,
            safety_stock=5,
            target_stock=40,
            is_active=False,
        )
        # Product 3: Product with NO sales
        prod_no_sales = Product(
            name="P7 Brand New Item",
            sku="P7-NEW-003",
            category_id=cat.id,
            supplier_id=sup.id,
            price=15.0,
            reorder_point=15,
            safety_stock=5,
            target_stock=50,
            is_active=True,
        )
        db.add_all([prod_active, prod_inactive, prod_no_sales])
        db.commit()
        db.refresh(prod_active)
        db.refresh(prod_inactive)
        db.refresh(prod_no_sales)

        # Inventory records
        inv1 = Inventory(product_id=prod_active.id, current_stock=100, reserved_stock=0)
        inv2 = Inventory(product_id=prod_inactive.id, current_stock=20, reserved_stock=0)
        inv3 = Inventory(product_id=prod_no_sales.id, current_stock=30, reserved_stock=0)
        db.add_all([inv1, inv2, inv3])
        db.commit()

        # Seed 7 days of sales for prod_active
        # Today is reference day. Let's seed for 7 days ending today:
        # Day -6: 10, Day -5: 20 (as two sales: 12 + 8), Day -4: 15, Day -3: 5, Day -2: 10, Day -1: 20, Day 0: 20
        now = datetime.now(timezone.utc)
        sales_data = [
            (6, 10),
            (5, 12),  # Day -5 part 1
            (5, 8),   # Day -5 part 2 (total 20 on Day -5)
            (4, 15),
            (3, 5),
            (2, 10),
            (1, 20),
            (0, 20),
        ]
        sales = []
        for days_ago, qty in sales_data:
            s = Sale(
                product_id=prod_active.id,
                quantity=qty,
                unit_price=25.0,
                total_amount=qty * 25.0,
                sold_by=staff.id,
                reference=f"P7-SALE-D{days_ago}",
                created_at=now - timedelta(days=days_ago),
            )
            sales.append(s)
        db.add_all(sales)
        db.commit()

        # Tokens
        admin_token = create_access_token({"sub": str(admin.id)})
        manager_token = create_access_token({"sub": str(manager.id)})
        staff_token = create_access_token({"sub": str(staff.id)})

        return {
            "admin_token": admin_token,
            "manager_token": manager_token,
            "staff_token": staff_token,
            "prod_active_id": prod_active.id,
            "prod_inactive_id": prod_inactive.id,
            "prod_no_sales_id": prod_no_sales.id,
            "cat_id": cat.id,
            "sup_id": sup.id,
        }


# ==============================================================================
# 1. Daily Sales Aggregation Tests (Requirements 1-5)
# ==============================================================================
def test_01_02_daily_sales_aggregation_and_summing(setup_data):
    """1. Sales aggregated by day. 2. Multiple sales on same day are summed."""
    prod_id = setup_data["prod_active_id"]
    with TestingSessionLocal() as db:
        series = get_daily_sales_history(db, prod_id, history_days=7)
        assert len(series) == 7
        # Day -5 had two sales (12 and 8) -> sum must be 20.0
        # Check that total of all 7 days is 100.0
        total_demand = sum(qty for _, qty in series)
        assert total_demand == 100.0


def test_03_04_zero_sales_days_included_and_date_range(setup_data):
    """3. Zero-sales days are included as 0.0. 4. Historical date range is correct."""
    prod_id = setup_data["prod_active_id"]
    with TestingSessionLocal() as db:
        # Request 14 days of history (only the last 7 days have sales, earlier 7 days must be 0.0)
        series = get_daily_sales_history(db, prod_id, history_days=14)
        assert len(series) == 14
        # First 7 days must have 0.0 sales
        for d, qty in series[:7]:
            assert qty == 0.0
        # Continuous dates in strict sequence
        for i in range(1, len(series)):
            assert series[i][0] == series[i - 1][0] + timedelta(days=1)


def test_05_inactive_products_excluded_from_generation(setup_data):
    """5. Inactive products are excluded from batch generation and return 400 on single generation."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    inactive_id = setup_data["prod_inactive_id"]

    # Single product generation on inactive product must return 400
    res = client.post(f"/forecast/generate/{inactive_id}", headers=headers)
    assert res.status_code == 400
    assert "inactive" in res.json()["detail"].lower()


# ==============================================================================
# 2. Simple Moving Average (SMA) Tests (Requirements 6-9)
# ==============================================================================
def test_06_sma_calculation_accuracy():
    """6. SMA calculation matches Example 40: (10+20+15+5+10+20+20)/7 = 100/7 = 14.285714..."""
    daily_demands = [10.0, 20.0, 15.0, 5.0, 10.0, 20.0, 20.0]
    sma = calculate_sma(daily_demands, history_days=7)
    assert abs(sma - (100.0 / 7.0)) < 1e-6
    assert abs(sma - 14.285714) < 1e-4


def test_07_sma_handles_zero_demand():
    """7. SMA handles zero-demand data cleanly."""
    zero_demands = [0.0, 0.0, 0.0, 0.0, 0.0]
    sma = calculate_sma(zero_demands, history_days=5)
    assert sma == 0.0


def test_08_09_sma_sparse_sales_and_decimal_precision():
    """8. SMA handles sparse sales. 9. Preserves decimal precision."""
    sparse_demands = [0.0, 0.0, 10.0, 0.0]
    sma = calculate_sma(sparse_demands, history_days=4)
    assert sma == 2.5
    assert isinstance(sma, float)


# ==============================================================================
# 3. Weighted Moving Average (WMA) Tests (Requirements 10-15)
# ==============================================================================
def test_10_11_wma_calculation_and_recency_weights():
    """10. WMA matches Example 41: Numerator 425, Denominator 28 -> 15.178571... 11. Recent days higher weights."""
    daily_demands = [10.0, 20.0, 15.0, 5.0, 10.0, 20.0, 20.0]
    wma = calculate_wma(daily_demands, wma_window=7)
    expected = 425.0 / 28.0
    assert abs(wma - expected) < 1e-6
    assert abs(wma - 15.178571) < 1e-4


def test_12_wma_handles_zero_demand():
    """12. WMA handles zero-demand data cleanly."""
    zero_demands = [0.0] * 7
    wma = calculate_wma(zero_demands, wma_window=7)
    assert wma == 0.0


def test_13_14_wma_sparse_sales_and_decimal_precision():
    """13. WMA handles sparse sales. 14. Preserves decimal precision without integer truncation."""
    # Only the most recent day has 7 units (weight 7 / 28 = 49 / 28 = 1.75)
    sparse = [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 7.0]
    wma = calculate_wma(sparse, wma_window=7)
    assert wma == 1.75


def test_15_invalid_wma_window_rejected():
    """15. Invalid WMA window is rejected."""
    with pytest.raises(ValueError):
        calculate_wma([10.0, 20.0], wma_window=0)
    with pytest.raises(ValueError):
        calculate_wma([10.0, 20.0], wma_window=-1)


# ==============================================================================
# 4. Forecast Generation, Horizon, and Persistence (Requirements 16-26)
# ==============================================================================
def test_16_sma_forecast_generation(setup_data):
    """16. SMA forecast generation works and produces correct metadata."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    prod_id = setup_data["prod_active_id"]
    res = client.post(f"/forecast/generate/{prod_id}?method=SMA", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["forecast_method"] == "SMA"
    assert data["status"] == "GENERATED"
    assert data["model_version"] == "v1"
    assert data["history_days"] == 30
    assert data["forecast_horizon_days"] == 7
    assert len(data["values"]) == 7


def test_17_wma_forecast_generation(setup_data):
    """17. WMA forecast generation works and produces correct metadata."""
    headers = {"Authorization": f"Bearer {setup_data['manager_token']}"}
    prod_id = setup_data["prod_active_id"]
    res = client.post(f"/forecast/generate/{prod_id}?method=WMA", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert data["forecast_method"] == "WMA"
    assert data["status"] == "GENERATED"
    assert data["model_version"] == "v1"
    assert "weighted moving-average" in data["explanation"].lower()


def test_18_19_20_horizon_and_next_day_dating(setup_data):
    """18. Forecast horizon is generated. 19. Starts on next calendar day. 20. Exactly horizon count."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    prod_id = setup_data["prod_active_id"]
    res = client.post(f"/forecast/generate/{prod_id}?method=SMA", headers=headers)
    data = res.json()
    values = data["values"]
    assert len(values) == 7

    # Check future dates start tomorrow relative to today
    today = datetime.now(timezone.utc).date()
    expected_first_date = today + timedelta(days=1)
    actual_first_date = date.fromisoformat(values[0]["forecast_date"])
    assert actual_first_date == expected_first_date

    for i in range(1, len(values)):
        cur = date.fromisoformat(values[i]["forecast_date"])
        prev = date.fromisoformat(values[i - 1]["forecast_date"])
        assert cur == prev + timedelta(days=1)


def test_21_22_23_persistence_and_model_version(setup_data):
    """21. Forecast values persisted. 22. Metadata persisted. 23. Model version v1."""
    with TestingSessionLocal() as db:
        prod_id = setup_data["prod_active_id"]
        fc = db.query(DemandForecast).filter(DemandForecast.product_id == prod_id).order_by(DemandForecast.generated_at.desc()).first()
        assert fc is not None
        assert fc.model_version == "v1"
        assert fc.history_days == 30
        assert fc.forecast_horizon_days == 7
        assert len(fc.values) == 7
        for v in fc.values:
            assert v.forecast_quantity >= 0.0


def test_24_25_archiving_previous_forecast_and_history_preserved(setup_data):
    """24. Previous forecast archived when new one generated. 25. Archived forecasts remain accessible."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    prod_id = setup_data["prod_active_id"]

    # Generate first forecast
    r1 = client.post(f"/forecast/generate/{prod_id}?method=SMA", headers=headers)
    f1_id = r1.json()["id"]

    # Generate second forecast
    r2 = client.post(f"/forecast/generate/{prod_id}?method=WMA", headers=headers)
    f2_id = r2.json()["id"]
    assert f1_id != f2_id

    # Check first forecast is now ARCHIVED and still accessible
    r1_check = client.get(f"/forecast/{f1_id}", headers=headers)
    assert r1_check.status_code == 200
    assert r1_check.json()["status"] == "ARCHIVED"

    # Second forecast is GENERATED
    r2_check = client.get(f"/forecast/{f2_id}", headers=headers)
    assert r2_check.status_code == 200
    assert r2_check.json()["status"] == "GENERATED"


def test_26_no_duplicate_forecast_dates_constraint(setup_data):
    """26. Database uniqueness constraint prevents duplicate forecast dates within a forecast."""
    with TestingSessionLocal() as db:
        fc = db.query(DemandForecast).first()
        duplicate_val = DemandForecastValue(
            forecast_id=fc.id,
            forecast_date=fc.values[0].forecast_date,
            forecast_quantity=5.0,
        )
        db.add(duplicate_val)
        with pytest.raises(IntegrityError):
            db.commit()
        db.rollback()


# ==============================================================================
# 5. No-Sales Product Tests (Requirements 27-29)
# ==============================================================================
def test_27_28_29_product_with_no_sales_generates_zeroes(setup_data):
    """27. Zero historical demand. 28. Zero SMA forecast. 29. Zero WMA forecast."""
    no_sales_id = setup_data["prod_no_sales_id"]
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}

    # 27. Test daily sales series is all 0
    with TestingSessionLocal() as db:
        series = get_daily_sales_history(db, no_sales_id, history_days=7)
        assert all(qty == 0.0 for _, qty in series)

    # 28. SMA forecast produces 0.0 values
    res_sma = client.post(f"/forecast/generate/{no_sales_id}?method=SMA", headers=headers)
    assert res_sma.status_code == 200
    assert res_sma.json()["total_forecast_quantity"] == 0.0
    assert res_sma.json()["average_daily_forecast"] == 0.0
    for v in res_sma.json()["values"]:
        assert v["forecast_quantity"] == 0.0

    # 29. WMA forecast produces 0.0 values
    res_wma = client.post(f"/forecast/generate/{no_sales_id}?method=WMA", headers=headers)
    assert res_wma.status_code == 200
    assert res_wma.json()["total_forecast_quantity"] == 0.0
    for v in res_wma.json()["values"]:
        assert v["forecast_quantity"] == 0.0


# ==============================================================================
# 6. REST API Endpoints & Queries (Requirements 30-38)
# ==============================================================================
def test_30_generate_all_forecasts_endpoint(setup_data):
    """30. POST /forecast/generate processes all active products and returns results."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    res = client.post("/forecast/generate?method=SMA", headers=headers)
    assert res.status_code == 200
    data = res.json()
    assert isinstance(data, list)
    # Active products are prod_active and prod_no_sales (prod_inactive excluded)
    product_ids = [item["product_id"] for item in data]
    assert setup_data["prod_active_id"] in product_ids
    assert setup_data["prod_no_sales_id"] in product_ids
    assert setup_data["prod_inactive_id"] not in product_ids


def test_31_product_specific_generation_endpoint(setup_data):
    """31. POST /forecast/generate/{product_id} generates for specific product."""
    headers = {"Authorization": f"Bearer {setup_data['manager_token']}"}
    prod_id = setup_data["prod_active_id"]
    res = client.post(f"/forecast/generate/{prod_id}?method=WMA", headers=headers)
    assert res.status_code == 200
    assert res.json()["product_id"] == prod_id


def test_32_33_forecast_list_and_filters(setup_data):
    """32. GET /forecast works. 33. Query filters work (product_id, method, status)."""
    headers = {"Authorization": f"Bearer {setup_data['staff_token']}"}
    prod_id = setup_data["prod_active_id"]

    # Filter by product_id
    res = client.get(f"/forecast?product_id={prod_id}", headers=headers)
    assert res.status_code == 200
    assert all(item["product_id"] == prod_id for item in res.json())

    # Filter by method
    res_method = client.get("/forecast?method=SMA", headers=headers)
    assert res_method.status_code == 200
    assert all(item["forecast_method"] == "SMA" for item in res_method.json())

    # Filter by status
    res_status = client.get("/forecast?status=ARCHIVED", headers=headers)
    assert res_status.status_code == 200
    assert all(item["status"] == "ARCHIVED" for item in res_status.json())


def test_34_35_forecast_detail_and_product_latest(setup_data):
    """34. GET /forecast/{id} works. 35. GET /forecast/products/{product_id} works."""
    headers = {"Authorization": f"Bearer {setup_data['staff_token']}"}
    prod_id = setup_data["prod_active_id"]

    # Latest product forecast
    res_prod = client.get(f"/forecast/products/{prod_id}", headers=headers)
    assert res_prod.status_code == 200
    data_prod = res_prod.json()
    assert data_prod["product_id"] == prod_id
    assert "values" in data_prod

    # Forecast detail by ID
    forecast_id = data_prod["id"]
    res_detail = client.get(f"/forecast/{forecast_id}", headers=headers)
    assert res_detail.status_code == 200
    assert res_detail.json()["id"] == forecast_id
    assert len(res_detail.json()["values"]) == 7


def test_36_37_38_api_error_handling(setup_data):
    """36. Invalid forecast ID -> 404. 37. Invalid product ID -> 404. 38. Invalid method rejected."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}

    # 36. Invalid forecast ID
    assert client.get("/forecast/999999", headers=headers).status_code == 404

    # 37. Invalid product ID
    assert client.get("/forecast/products/999999", headers=headers).status_code == 404
    assert client.post("/forecast/generate/999999", headers=headers).status_code == 404

    # 38. Invalid forecast method string
    res_invalid = client.post("/forecast/generate?method=INVALID_METHOD", headers=headers)
    assert res_invalid.status_code == 422


# ==============================================================================
# 7. Role-Based Access Control (RBAC) Tests (Requirements 39-43)
# ==============================================================================
def test_39_40_admin_and_manager_can_generate(setup_data):
    """39. Admin can generate. 40. Inventory manager can generate."""
    admin_hdr = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    manager_hdr = {"Authorization": f"Bearer {setup_data['manager_token']}"}
    prod_id = setup_data["prod_active_id"]

    res1 = client.post(f"/forecast/generate/{prod_id}?method=SMA", headers=admin_hdr)
    assert res1.status_code == 200

    res2 = client.post(f"/forecast/generate/{prod_id}?method=WMA", headers=manager_hdr)
    assert res2.status_code == 200


def test_41_warehouse_staff_cannot_generate(setup_data):
    """41. Warehouse staff cannot generate forecasts (403 Forbidden)."""
    staff_hdr = {"Authorization": f"Bearer {setup_data['staff_token']}"}
    prod_id = setup_data["prod_active_id"]

    res_all = client.post("/forecast/generate", headers=staff_hdr)
    assert res_all.status_code == 403

    res_single = client.post(f"/forecast/generate/{prod_id}", headers=staff_hdr)
    assert res_single.status_code == 403


def test_42_43_all_roles_can_view_and_unauthenticated_rejected(setup_data):
    """42. All authenticated roles can view. 43. Unauthenticated requests rejected (401)."""
    staff_hdr = {"Authorization": f"Bearer {setup_data['staff_token']}"}

    # Warehouse staff can view
    res_list = client.get("/forecast", headers=staff_hdr)
    assert res_list.status_code == 200

    # Unauthenticated rejected
    assert client.get("/forecast").status_code == 401
    assert client.post("/forecast/generate").status_code == 401


# ==============================================================================
# 8. Integration Safety & Boundary Isolation (Requirements 44-50)
# ==============================================================================
def test_44_45_46_forecast_generation_does_not_modify_inventory_sales_or_po(setup_data):
    """44. No inventory modification. 45. No sales modification. 46. No PO creation."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}

    with TestingSessionLocal() as db:
        inv_before = [(inv.product_id, inv.current_stock, inv.reserved_stock) for inv in db.query(Inventory).all()]
        tx_count_before = db.query(InventoryTransaction).count()
        sales_count_before = db.query(Sale).count()
        po_count_before = db.query(PurchaseOrder).count()

    # Trigger generation
    res = client.post("/forecast/generate?method=SMA", headers=headers)
    assert res.status_code == 200

    with TestingSessionLocal() as db:
        inv_after = [(inv.product_id, inv.current_stock, inv.reserved_stock) for inv in db.query(Inventory).all()]
        tx_count_after = db.query(InventoryTransaction).count()
        sales_count_after = db.query(Sale).count()
        po_count_after = db.query(PurchaseOrder).count()

        assert inv_before == inv_after
        assert tx_count_before == tx_count_after
        assert sales_count_before == sales_count_after
        assert po_count_before == po_count_after


def test_47_48_49_product_replenishment_configs_unmodified(setup_data):
    """47. No reorder_point change. 48. No safety_stock change. 49. No target_stock change."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    prod_id = setup_data["prod_active_id"]

    with TestingSessionLocal() as db:
        p_before = db.query(Product).filter(Product.id == prod_id).first()
        rop_before = p_before.reorder_point
        safety_before = p_before.safety_stock
        target_before = p_before.target_stock

    client.post(f"/forecast/generate/{prod_id}?method=WMA", headers=headers)

    with TestingSessionLocal() as db:
        p_after = db.query(Product).filter(Product.id == prod_id).first()
        assert p_after.reorder_point == rop_before
        assert p_after.safety_stock == safety_before
        assert p_after.target_stock == target_before


def test_50_phase6_replenishment_logic_intact(setup_data):
    """50. Phase 6 replenishment engine continues to function properly without alteration."""
    headers = {"Authorization": f"Bearer {setup_data['admin_token']}"}
    res = client.post("/replenishment/generate", headers=headers)
    assert res.status_code == 200
    assert isinstance(res.json(), list)


# ==============================================================================
# 9. Cross-Phase Regression Tests (Requirements 51-56)
# ==============================================================================
def test_51_to_56_regression_checks(setup_data):
    """51-56. Full cross-phase sanity regression checks (Phases 1-6 endpoints remain accessible)."""
    admin_hdr = {"Authorization": f"Bearer {setup_data['admin_token']}"}

    # Phase 1: Health
    r1 = client.get("/health")
    assert r1.status_code == 200
    assert r1.json()["status"] == "healthy"

    # Phase 2: Users/Me
    r2 = client.get("/users/me", headers=admin_hdr)
    assert r2.status_code == 200

    # Phase 3: Products
    r3 = client.get("/products", headers=admin_hdr)
    assert r3.status_code == 200

    # Phase 4: Inventory
    r4 = client.get("/inventory", headers=admin_hdr)
    assert r4.status_code == 200

    # Phase 5: Sales & Purchase Orders
    r5_sales = client.get("/sales", headers=admin_hdr)
    assert r5_sales.status_code == 200
    r5_pos = client.get("/purchase-orders", headers=admin_hdr)
    assert r5_pos.status_code == 200

    # Phase 6: Replenishment Recommendations
    r6 = client.get("/replenishment/recommendations", headers=admin_hdr)
    assert r6.status_code == 200
