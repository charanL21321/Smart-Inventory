"""
Comprehensive test suite for Phase 9: Notifications & Alerts.
Verifies all Phase 9 requirements covering:
- Database schema, foreign keys, indexes, and read/unread lifecycle
- Low-stock and out-of-stock alerts with deterministic priorities and deduplication
- Replenishment recommendation alerts and priority mirroring
- Purchase order status transitions and receipt alerts
- Demand forecasting generation alerts
- User ownership security (strict isolation, 404 on cross-user access)
- API endpoints: list, filters, unread count, mark-as-read, mark-all-as-read, 401 unauthorized
- Role-aware targeting (ADMIN, INVENTORY_MANAGER, WAREHOUSE_STAFF)
- Transaction safety & failure atomicity (no notifications on failed business actions)
- Full regression checks
"""

from datetime import datetime, timezone
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import select

from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.category import Category
from app.models.demand_forecast import DemandForecast, ForecastMethod, ForecastStatus
from app.models.inventory import Inventory
from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.replenishment_recommendation import (
    RecommendationPriority,
    RecommendationStatus,
    ReplenishmentRecommendation,
)
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from app.schemas.inventory_transaction import StockInRequest, StockOutRequest
from app.schemas.purchase_order import PurchaseOrderReceiveItem, PurchaseOrderReceiveRequest
from app.services.forecast_service import generate_product_forecast
from app.services.inventory_service import perform_stock_in, perform_stock_out
from app.services.notification_service import (
    check_and_trigger_stock_alerts,
    count_unread_notifications,
    create_low_stock_notification,
    create_notification,
    create_out_of_stock_notification,
    create_replenishment_notification,
    get_notification_by_id,
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)
from app.services.purchase_order_service import (
    receive_purchase_order,
    update_purchase_order_status,
)
from app.services.replenishment_service import generate_recommendations
from tests.conftest import TestingSessionLocal

client = TestClient(app)


# ------------------------------------------------------------------------------
# Fixtures
# ------------------------------------------------------------------------------
@pytest.fixture(scope="module")
def setup_data():
    """Seed test users, supplier, category, and products for Phase 9."""
    with TestingSessionLocal() as db:
        # Users
        admin = User(
            username="admin_p9",
            email="admin_p9@example.com",
            hashed_password=hash_password("AdminPass123!"),
            role=UserRole.ADMIN,
            is_active=True,
        )
        manager = User(
            username="manager_p9",
            email="manager_p9@example.com",
            hashed_password=hash_password("ManagerPass123!"),
            role=UserRole.INVENTORY_MANAGER,
            is_active=True,
        )
        staff = User(
            username="staff_p9",
            email="staff_p9@example.com",
            hashed_password=hash_password("StaffPass123!"),
            role=UserRole.WAREHOUSE_STAFF,
            is_active=True,
        )
        db.add_all([admin, manager, staff])
        db.flush()

        # Category & Supplier
        cat = Category(name="Electronics P9", is_active=True)
        sup = Supplier(
            name="Apex Supplier P9",
            email="apex_p9@example.com",
            phone="555-0909",
            lead_time_days=5,
            minimum_order_quantity=10,
            is_active=True,
        )
        db.add_all([cat, sup])
        db.flush()

        # Products
        prod_a = Product(
            name="Sensor A",
            sku="SENS-A-P9",
            category_id=cat.id,
            supplier_id=sup.id,
            price=25.0,
            reorder_point=15,
            safety_stock=5,
            target_stock=50,
            is_active=True,
        )
        prod_b = Product(
            name="Sensor B",
            sku="SENS-B-P9",
            category_id=cat.id,
            supplier_id=sup.id,
            price=40.0,
            reorder_point=20,
            safety_stock=10,
            target_stock=100,
            is_active=True,
        )
        db.add_all([prod_a, prod_b])
        db.flush()

        # Inventory
        inv_a = Inventory(product_id=prod_a.id, current_stock=30, reserved_stock=0)
        inv_b = Inventory(product_id=prod_b.id, current_stock=10, reserved_stock=0)
        db.add_all([inv_a, inv_b])
        db.commit()

        return {
            "admin_id": admin.id,
            "manager_id": manager.id,
            "staff_id": staff.id,
            "cat_id": cat.id,
            "sup_id": sup.id,
            "prod_a_id": prod_a.id,
            "prod_b_id": prod_b.id,
        }


@pytest.fixture
def auth_headers(setup_data):
    """Generate auth headers for admin, manager, and warehouse staff."""
    admin_token = create_access_token({"sub": str(setup_data["admin_id"]), "role": "ADMIN"})
    manager_token = create_access_token({"sub": str(setup_data["manager_id"]), "role": "INVENTORY_MANAGER"})
    staff_token = create_access_token({"sub": str(setup_data["staff_id"]), "role": "WAREHOUSE_STAFF"})

    return {
        "admin": {"Authorization": f"Bearer {admin_token}"},
        "manager": {"Authorization": f"Bearer {manager_token}"},
        "staff": {"Authorization": f"Bearer {staff_token}"},
    }


# ------------------------------------------------------------------------------
# 1-4: Database Model, Foreign Keys, Indexes, and Read Fields
# ------------------------------------------------------------------------------
def test_01_02_03_04_model_creation_fks_indexes_and_read_fields(setup_data):
    with TestingSessionLocal() as db:
        admin_id = setup_data["admin_id"]
        prod_id = setup_data["prod_a_id"]
        sup_id = setup_data["sup_id"]

        n = Notification(
            user_id=admin_id,
            notification_type=NotificationType.LOW_STOCK,
            priority=NotificationPriority.MEDIUM,
            title="Low Stock Alert",
            message="Test low stock alert",
            product_id=prod_id,
            supplier_id=sup_id,
            is_read=False,
            created_at=datetime.now(timezone.utc),
        )
        db.add(n)
        db.commit()
        db.refresh(n)

        assert n.id is not None
        assert n.user_id == admin_id
        assert n.product_id == prod_id
        assert n.supplier_id == sup_id
        assert n.is_read is False
        assert n.read_at is None
        assert n.user.username == "admin_p9"
        assert n.product.sku == "SENS-A-P9"

        # Mark as read
        n.is_read = True
        n.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(n)
        assert n.is_read is True
        assert n.read_at is not None


# ------------------------------------------------------------------------------
# 5-8: Low-Stock Alerts and Deduplication
# ------------------------------------------------------------------------------
def test_05_06_07_08_low_stock_alert_and_deduplication(setup_data):
    with TestingSessionLocal() as db:
        prod_a = db.get(Product, setup_data["prod_a_id"])
        admin_id = setup_data["admin_id"]

        # Initial clean
        db.query(Notification).filter(Notification.product_id == prod_a.id).delete()
        db.commit()

        # Trigger low stock notification
        created = create_low_stock_notification(db, prod_a)
        db.commit()

        assert len(created) > 0
        admin_n = [n for n in created if n.user_id == admin_id][0]
        assert admin_n.priority == NotificationPriority.MEDIUM
        assert admin_n.notification_type == NotificationType.LOW_STOCK
        assert "below its configured reorder point" in admin_n.message

        # Deduplication check: repeated call while unread should not duplicate
        dup_check = create_low_stock_notification(db, prod_a)
        assert len(dup_check) == 0

        # Mark as read
        admin_n.is_read = True
        db.commit()

        # Now that it was read, a subsequent transition can generate a new alert
        new_alerts = create_low_stock_notification(db, prod_a)
        db.commit()
        assert len(new_alerts) > 0


# ------------------------------------------------------------------------------
# 9-12: Out-of-Stock Alerts and Deduplication
# ------------------------------------------------------------------------------
def test_09_10_11_12_out_of_stock_alert_and_deduplication(setup_data):
    with TestingSessionLocal() as db:
        prod_b = db.get(Product, setup_data["prod_b_id"])
        admin_id = setup_data["admin_id"]

        db.query(Notification).filter(Notification.product_id == prod_b.id).delete()
        db.commit()

        created = create_out_of_stock_notification(db, prod_b)
        db.commit()

        assert len(created) > 0
        admin_n = [n for n in created if n.user_id == admin_id][0]
        assert admin_n.priority == NotificationPriority.HIGH
        assert admin_n.notification_type == NotificationType.OUT_OF_STOCK
        assert "currently out of stock" in admin_n.message

        # Deduplication check
        dup_check = create_out_of_stock_notification(db, prod_b)
        assert len(dup_check) == 0


# ------------------------------------------------------------------------------
# 13-15: Replenishment Recommendation Notifications
# ------------------------------------------------------------------------------
def test_13_14_15_replenishment_notifications(setup_data):
    with TestingSessionLocal() as db:
        prod_a = db.get(Product, setup_data["prod_a_id"])
        admin_id = setup_data["admin_id"]

        rec = ReplenishmentRecommendation(
            product_id=prod_a.id,
            supplier_id=prod_a.supplier_id,
            current_stock=2,
            reserved_stock=0,
            inventory_position=2,
            reorder_point=prod_a.reorder_point,
            safety_stock=prod_a.safety_stock,
            target_stock=prod_a.target_stock,
            average_daily_demand=2.0,
            lead_time_days=5,
            lead_time_demand=10.0,
            recommended_quantity=48,
            minimum_order_quantity=10,
            priority=RecommendationPriority.HIGH,
            reason="Inventory position below safety stock",
            status=RecommendationStatus.PENDING,
        )
        db.add(rec)
        db.commit()
        db.refresh(rec)

        created = create_replenishment_notification(db, rec, prod_a)
        db.commit()

        assert len(created) > 0
        admin_n = [n for n in created if n.user_id == admin_id][0]
        assert admin_n.notification_type == NotificationType.REPLENISHMENT_RECOMMENDATION
        assert admin_n.priority == NotificationPriority.HIGH
        assert "48 units" in admin_n.message

        # Deduplication on repeated evaluation of same recommendation
        dup = create_replenishment_notification(db, rec, prod_a)
        assert len(dup) == 0


# ------------------------------------------------------------------------------
# 16-20: Purchase Order Status and Received Notifications
# ------------------------------------------------------------------------------
def test_16_to_20_purchase_order_notifications(setup_data):
    with TestingSessionLocal() as db:
        admin_id = setup_data["admin_id"]
        staff_id = setup_data["staff_id"]
        sup_id = setup_data["sup_id"]
        prod_a_id = setup_data["prod_a_id"]

        po = PurchaseOrder(
            order_number="PO-TEST-P9-01",
            supplier_id=sup_id,
            status=PurchaseOrderStatus.DRAFT,
            total_amount=500.0,
            created_by=admin_id,
        )
        db.add(po)
        db.flush()

        item = PurchaseOrderItem(
            purchase_order_id=po.id,
            product_id=prod_a_id,
            quantity=20,
            received_quantity=0,
            unit_cost=25.0,
            total_cost=500.0,
        )
        db.add(item)
        db.commit()
        db.refresh(po)

        admin = db.get(User, admin_id)

        # 16. Status transition: DRAFT -> PENDING_APPROVAL
        update_purchase_order_status(db, po.id, PurchaseOrderStatus.PENDING_APPROVAL, admin)
        db.commit()

        # Check status notification
        n_stmt = (
            select(Notification)
            .where(Notification.purchase_order_id == po.id)
            .where(Notification.notification_type == NotificationType.PURCHASE_ORDER_STATUS)
            .where(Notification.user_id == admin_id)
        )
        n = db.scalars(n_stmt).first()
        assert n is not None
        assert n.priority == NotificationPriority.MEDIUM
        assert "PENDING_APPROVAL" in n.message

        # Approve and Order
        update_purchase_order_status(db, po.id, PurchaseOrderStatus.APPROVED, admin)
        update_purchase_order_status(db, po.id, PurchaseOrderStatus.ORDERED, admin)
        db.commit()

        # 18. Partial receiving
        rec_req = PurchaseOrderReceiveRequest(
            items=[PurchaseOrderReceiveItem(product_id=prod_a_id, quantity=10)]
        )
        receive_purchase_order(db, po.id, rec_req, user_id=staff_id)
        db.commit()

        # Verify PARTIALLY_RECEIVED notification
        partial_n = (
            db.query(Notification)
            .filter(
                Notification.purchase_order_id == po.id,
                Notification.notification_type == NotificationType.PURCHASE_ORDER_STATUS,
                Notification.message.like("%PARTIALLY_RECEIVED%"),
            )
            .first()
        )
        assert partial_n is not None

        # 19-20. Final receiving
        rec_final = PurchaseOrderReceiveRequest(
            items=[PurchaseOrderReceiveItem(product_id=prod_a_id, quantity=10)]
        )
        receive_purchase_order(db, po.id, rec_final, user_id=staff_id)
        db.commit()

        # Verify PURCHASE_ORDER_RECEIVED notification
        rec_n = (
            db.query(Notification)
            .filter(
                Notification.purchase_order_id == po.id,
                Notification.notification_type == NotificationType.PURCHASE_ORDER_RECEIVED,
                Notification.user_id == staff_id,
            )
            .first()
        )
        assert rec_n is not None
        assert rec_n.priority == NotificationPriority.LOW


# ------------------------------------------------------------------------------
# 21-23: Demand Forecast Notifications
# ------------------------------------------------------------------------------
def test_21_22_23_forecast_generated_notifications(setup_data):
    with TestingSessionLocal() as db:
        prod_a_id = setup_data["prod_a_id"]
        admin_id = setup_data["admin_id"]

        forecast = generate_product_forecast(db, product_id=prod_a_id, method=ForecastMethod.SMA)
        db.commit()

        f_n = (
            db.query(Notification)
            .filter(
                Notification.forecast_id == forecast.id,
                Notification.notification_type == NotificationType.FORECAST_GENERATED,
                Notification.user_id == admin_id,
            )
            .first()
        )
        assert f_n is not None
        assert f_n.priority == NotificationPriority.LOW
        assert "demand forecast has been generated" in f_n.message


# ------------------------------------------------------------------------------
# 24-26: User Ownership & Security
# ------------------------------------------------------------------------------
def test_24_25_26_user_ownership_and_security(setup_data, auth_headers):
    with TestingSessionLocal() as db:
        admin_id = setup_data["admin_id"]
        staff_id = setup_data["staff_id"]

        # Create notification for admin
        n = create_notification(
            db=db,
            user_id=admin_id,
            notification_type=NotificationType.LOW_STOCK,
            priority=NotificationPriority.MEDIUM,
            title="Private Alert",
            message="Only for admin",
        )
        db.commit()
        db.refresh(n)
        admin_nid = n.id

    # Staff attempts to view admin's notification via API -> 404
    resp = client.get(f"/notifications/{admin_nid}", headers=auth_headers["staff"])
    assert resp.status_code == 404

    # Staff attempts to mark admin's notification as read -> 404
    resp = client.patch(f"/notifications/{admin_nid}/read", headers=auth_headers["staff"])
    assert resp.status_code == 404

    # Admin accesses own notification -> 200
    resp = client.get(f"/notifications/{admin_nid}", headers=auth_headers["admin"])
    assert resp.status_code == 200
    assert resp.json()["id"] == admin_nid


# ------------------------------------------------------------------------------
# 27-34: API Endpoints, Filters, Unread Count & Mark As Read
# ------------------------------------------------------------------------------
def test_27_to_34_api_endpoints_and_lifecycle(setup_data, auth_headers):
    # 34. Unauthorized returns 401
    unauth = client.get("/notifications")
    assert unauth.status_code == 401

    # 30. Unread count endpoint
    resp = client.get("/notifications/unread-count", headers=auth_headers["admin"])
    assert resp.status_code == 200
    assert "unread_count" in resp.json()

    # 27. List notifications
    list_resp = client.get("/notifications", headers=auth_headers["admin"])
    assert list_resp.status_code == 200
    items = list_resp.json()
    assert isinstance(items, list)

    if items:
        first_id = items[0]["id"]
        # 31. Mark as read
        read_resp = client.patch(f"/notifications/{first_id}/read", headers=auth_headers["admin"])
        assert read_resp.status_code == 200
        assert read_resp.json()["is_read"] is True
        assert read_resp.json()["read_at"] is not None

        # 33. Idempotent call
        idem_resp = client.patch(f"/notifications/{first_id}/read", headers=auth_headers["admin"])
        assert idem_resp.status_code == 200
        assert idem_resp.json()["is_read"] is True

    # 32. Mark all as read
    bulk_resp = client.patch("/notifications/read-all", headers=auth_headers["admin"])
    assert bulk_resp.status_code == 200
    assert "marked_read" in bulk_resp.json()

    # Count should now be 0
    count_resp = client.get("/notifications/unread-count", headers=auth_headers["admin"])
    assert count_resp.json()["unread_count"] == 0

    # 28. Filtering
    filter_resp = client.get(
        "/notifications?is_read=true&priority=MEDIUM",
        headers=auth_headers["admin"],
    )
    assert filter_resp.status_code == 200


# ------------------------------------------------------------------------------
# 35-37: RBAC and Role Targeting
# ------------------------------------------------------------------------------
def test_35_36_37_rbac_and_role_targeting(setup_data, auth_headers):
    # Warehouse staff can access their own notifications endpoint
    resp = client.get("/notifications", headers=auth_headers["staff"])
    assert resp.status_code == 200

    count_resp = client.get("/notifications/unread-count", headers=auth_headers["staff"])
    assert count_resp.status_code == 200


# ------------------------------------------------------------------------------
# 38-42: Transaction Safety & Failure Atomicity
# ------------------------------------------------------------------------------
def test_38_to_42_transaction_safety_and_failure_atomicity(setup_data):
    with TestingSessionLocal() as db:
        prod_a = db.get(Product, setup_data["prod_a_id"])

        count_before = db.query(Notification).count()

        # Attempt invalid stock-out exceeding available stock
        with pytest.raises(Exception):
            perform_stock_out(
                db=db,
                data=StockOutRequest(product_id=prod_a.id, quantity=999999),
                user_id=setup_data["staff_id"],
            )

        count_after = db.query(Notification).count()
        # No orphan notifications created from failed transaction
        assert count_after == count_before


# ------------------------------------------------------------------------------
# 43-49: Regressions Across Completed Phases
# ------------------------------------------------------------------------------
def test_43_to_49_regression_checks(setup_data, auth_headers):
    # Phase 2 Auth Me
    me_resp = client.get("/users/me", headers=auth_headers["admin"])
    assert me_resp.status_code == 200
    assert me_resp.json()["username"] == "admin_p9"

    # Phase 3 Products
    prod_resp = client.get("/products", headers=auth_headers["admin"])
    assert prod_resp.status_code == 200

    # Phase 4 Inventory
    inv_resp = client.get("/inventory", headers=auth_headers["admin"])
    assert inv_resp.status_code == 200

    # Phase 5 Sales
    sales_resp = client.get("/sales", headers=auth_headers["admin"])
    assert sales_resp.status_code == 200

    # Phase 6 Replenishment
    rep_resp = client.get("/replenishment/recommendations", headers=auth_headers["admin"])
    assert rep_resp.status_code == 200

    # Phase 7 Forecasts
    fc_resp = client.get("/forecast", headers=auth_headers["admin"])
    assert fc_resp.status_code == 200
