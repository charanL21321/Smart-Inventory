from datetime import datetime, timezone
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select, update
from sqlalchemy.orm import Session

from app.models.demand_forecast import DemandForecast
from app.models.inventory import Inventory
from app.models.notification import (
    Notification,
    NotificationPriority,
    NotificationType,
)
from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.replenishment_recommendation import (
    RecommendationPriority,
    ReplenishmentRecommendation,
)
from app.models.user import User, UserRole


def get_target_users(db: Session, roles: List[UserRole]) -> List[User]:
    """
    Retrieves all active users with any of the specified roles.
    """
    stmt = (
        select(User)
        .where(User.is_active == True)  # noqa: E712
        .where(User.role.in_(roles))
    )
    return list(db.scalars(stmt).all())


def create_notification(
    db: Session,
    user_id: int,
    notification_type: NotificationType,
    priority: NotificationPriority,
    title: str,
    message: str,
    product_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    purchase_order_id: Optional[int] = None,
    replenishment_recommendation_id: Optional[int] = None,
    forecast_id: Optional[int] = None,
) -> Notification:
    """
    Creates and persists a single in-app notification for a specific user.
    """
    now = datetime.now(timezone.utc)
    notification = Notification(
        user_id=user_id,
        notification_type=notification_type,
        priority=priority,
        title=title,
        message=message,
        product_id=product_id,
        supplier_id=supplier_id,
        purchase_order_id=purchase_order_id,
        replenishment_recommendation_id=replenishment_recommendation_id,
        forecast_id=forecast_id,
        is_read=False,
        created_at=now,
    )
    db.add(notification)
    return notification


def create_low_stock_notification(db: Session, product: Product) -> List[Notification]:
    """
    Emits LOW_STOCK alerts (MEDIUM priority) to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    Deduplicates: skips if an unread LOW_STOCK alert already exists for the product.
    """
    target_roles = [UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF]
    users = get_target_users(db, target_roles)
    created: List[Notification] = []

    title = "Low Stock Alert"
    message = f"{product.name} is below its configured reorder point."

    for user in users:
        # Check for unread duplicate
        stmt = (
            select(Notification)
            .where(Notification.user_id == user.id)
            .where(Notification.product_id == product.id)
            .where(Notification.notification_type == NotificationType.LOW_STOCK)
            .where(Notification.is_read == False)  # noqa: E712
        )
        existing = db.scalars(stmt).first()
        if not existing:
            n = create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.LOW_STOCK,
                priority=NotificationPriority.MEDIUM,
                title=title,
                message=message,
                product_id=product.id,
                supplier_id=product.supplier_id,
            )
            created.append(n)

    return created


def create_out_of_stock_notification(db: Session, product: Product) -> List[Notification]:
    """
    Emits OUT_OF_STOCK alerts (HIGH priority) to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    Deduplicates: skips if an unread OUT_OF_STOCK alert already exists for the product.
    """
    target_roles = [UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF]
    users = get_target_users(db, target_roles)
    created: List[Notification] = []

    title = "Out of Stock"
    message = f"{product.name} is currently out of stock."

    for user in users:
        # Check for unread duplicate
        stmt = (
            select(Notification)
            .where(Notification.user_id == user.id)
            .where(Notification.product_id == product.id)
            .where(Notification.notification_type == NotificationType.OUT_OF_STOCK)
            .where(Notification.is_read == False)  # noqa: E712
        )
        existing = db.scalars(stmt).first()
        if not existing:
            n = create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.OUT_OF_STOCK,
                priority=NotificationPriority.HIGH,
                title=title,
                message=message,
                product_id=product.id,
                supplier_id=product.supplier_id,
            )
            created.append(n)

    return created


def check_and_trigger_stock_alerts(db: Session, product_id: int) -> List[Notification]:
    """
    Evaluates current inventory status for a product against reorder point and triggers alerts.
    """
    product = db.get(Product, product_id)
    if not product or not product.is_active:
        return []

    stmt = select(Inventory).where(Inventory.product_id == product_id)
    inv = db.scalars(stmt).first()
    if not inv:
        return []

    if inv.current_stock == 0:
        return create_out_of_stock_notification(db, product)
    elif inv.current_stock <= product.reorder_point:
        return create_low_stock_notification(db, product)

    return []


def create_replenishment_notification(
    db: Session,
    recommendation: ReplenishmentRecommendation,
    product: Product,
) -> List[Notification]:
    """
    Emits REPLENISHMENT_RECOMMENDATION alerts to ADMIN and INVENTORY_MANAGER.
    Deduplicates: skips if recommendation already generated an alert for the user.
    Priority mirrors underlying recommendation priority.
    """
    target_roles = [UserRole.ADMIN, UserRole.INVENTORY_MANAGER]
    users = get_target_users(db, target_roles)
    created: List[Notification] = []

    # Map priority deterministically
    priority_map = {
        RecommendationPriority.HIGH: NotificationPriority.HIGH,
        RecommendationPriority.MEDIUM: NotificationPriority.MEDIUM,
        RecommendationPriority.LOW: NotificationPriority.LOW,
    }
    priority = priority_map.get(recommendation.priority, NotificationPriority.MEDIUM)

    title = "Replenishment Recommended"
    message = f"{product.name} requires a recommended replenishment of {recommendation.recommended_quantity} units."

    for user in users:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user.id)
            .where(Notification.replenishment_recommendation_id == recommendation.id)
            .where(Notification.notification_type == NotificationType.REPLENISHMENT_RECOMMENDATION)
        )
        existing = db.scalars(stmt).first()
        if not existing:
            n = create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.REPLENISHMENT_RECOMMENDATION,
                priority=priority,
                title=title,
                message=message,
                product_id=product.id,
                supplier_id=recommendation.supplier_id,
                replenishment_recommendation_id=recommendation.id,
            )
            created.append(n)

    return created


def create_purchase_order_status_notification(
    db: Session,
    po: PurchaseOrder,
) -> List[Notification]:
    """
    Emits PURCHASE_ORDER_STATUS alerts (MEDIUM priority).
    PARTIALLY_RECEIVED goes to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    Other status changes go to ADMIN and INVENTORY_MANAGER.
    """
    if po.status == PurchaseOrderStatus.PARTIALLY_RECEIVED:
        target_roles = [UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF]
    else:
        target_roles = [UserRole.ADMIN, UserRole.INVENTORY_MANAGER]

    users = get_target_users(db, target_roles)
    created: List[Notification] = []

    title = "Purchase Order Status Updated"
    status_str = po.status.value if isinstance(po.status, PurchaseOrderStatus) else str(po.status)
    message = f"Purchase order {po.order_number} is now {status_str}."

    for user in users:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user.id)
            .where(Notification.purchase_order_id == po.id)
            .where(Notification.notification_type == NotificationType.PURCHASE_ORDER_STATUS)
            .where(Notification.message == message)
        )
        existing = db.scalars(stmt).first()
        if not existing:
            n = create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.PURCHASE_ORDER_STATUS,
                priority=NotificationPriority.MEDIUM,
                title=title,
                message=message,
                supplier_id=po.supplier_id,
                purchase_order_id=po.id,
            )
            created.append(n)

    return created


def create_purchase_order_received_notification(
    db: Session,
    po: PurchaseOrder,
) -> List[Notification]:
    """
    Emits PURCHASE_ORDER_RECEIVED alerts (LOW priority) to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    Deduplicates: skips if already created for the PO.
    """
    target_roles = [UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF]
    users = get_target_users(db, target_roles)
    created: List[Notification] = []

    title = "Purchase Order Received"
    message = f"Purchase order {po.order_number} has been received."

    for user in users:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user.id)
            .where(Notification.purchase_order_id == po.id)
            .where(Notification.notification_type == NotificationType.PURCHASE_ORDER_RECEIVED)
        )
        existing = db.scalars(stmt).first()
        if not existing:
            n = create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.PURCHASE_ORDER_RECEIVED,
                priority=NotificationPriority.LOW,
                title=title,
                message=message,
                supplier_id=po.supplier_id,
                purchase_order_id=po.id,
            )
            created.append(n)

    return created


def create_forecast_generated_notification(
    db: Session,
    forecast: DemandForecast,
    product: Product,
) -> List[Notification]:
    """
    Emits FORECAST_GENERATED alerts (LOW priority) to ADMIN and INVENTORY_MANAGER.
    Deduplicates: skips if already created for this forecast.
    """
    target_roles = [UserRole.ADMIN, UserRole.INVENTORY_MANAGER]
    users = get_target_users(db, target_roles)
    created: List[Notification] = []

    title = "Demand Forecast Generated"
    method_str = forecast.forecast_method
    message = f"A new {method_str} demand forecast has been generated for {product.name}."

    for user in users:
        stmt = (
            select(Notification)
            .where(Notification.user_id == user.id)
            .where(Notification.forecast_id == forecast.id)
            .where(Notification.notification_type == NotificationType.FORECAST_GENERATED)
        )
        existing = db.scalars(stmt).first()
        if not existing:
            n = create_notification(
                db=db,
                user_id=user.id,
                notification_type=NotificationType.FORECAST_GENERATED,
                priority=NotificationPriority.LOW,
                title=title,
                message=message,
                product_id=product.id,
                forecast_id=forecast.id,
            )
            created.append(n)

    return created


# ------------------------------------------------------------------------------
# Query & Lifecycle APIs
# ------------------------------------------------------------------------------
def get_user_notifications(
    db: Session,
    user_id: int,
    is_read: Optional[bool] = None,
    notification_type: Optional[NotificationType] = None,
    priority: Optional[NotificationPriority] = None,
    skip: int = 0,
    limit: int = 50,
) -> List[Notification]:
    """
    Retrieves authenticated user's notifications with optional filters, newest first.
    """
    stmt = select(Notification).where(Notification.user_id == user_id)

    if is_read is not None:
        stmt = stmt.where(Notification.is_read == is_read)
    if notification_type is not None:
        stmt = stmt.where(Notification.notification_type == notification_type)
    if priority is not None:
        stmt = stmt.where(Notification.priority == priority)

    stmt = stmt.order_by(Notification.created_at.desc()).offset(skip).limit(limit)
    return list(db.scalars(stmt).all())


def get_notification_by_id(db: Session, notification_id: int, user_id: int) -> Notification:
    """
    Retrieves a single notification strictly enforcing ownership.
    Returns 404 if notification doesn't exist or does not belong to user.
    """
    stmt = (
        select(Notification)
        .where(Notification.id == notification_id)
        .where(Notification.user_id == user_id)
    )
    notification = db.scalars(stmt).first()
    if not notification:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Notification with ID {notification_id} not found",
        )
    return notification


def count_unread_notifications(db: Session, user_id: int) -> int:
    """
    Counts unread notifications belonging to the authenticated user.
    """
    stmt = (
        select(func.count(Notification.id))
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)  # noqa: E712
    )
    return db.scalar(stmt) or 0


def mark_notification_read(db: Session, notification_id: int, user_id: int) -> Notification:
    """
    Idempotently marks a single notification as read. Strictly enforces ownership.
    """
    notification = get_notification_by_id(db, notification_id, user_id)
    if not notification.is_read:
        notification.is_read = True
        notification.read_at = datetime.now(timezone.utc)
        db.commit()
        db.refresh(notification)
    return notification


def mark_all_notifications_read(db: Session, user_id: int) -> int:
    """
    Idempotently marks all unread notifications belonging to the user as read.
    """
    now = datetime.now(timezone.utc)
    stmt = (
        update(Notification)
        .where(Notification.user_id == user_id)
        .where(Notification.is_read == False)  # noqa: E712
        .values(is_read=True, read_at=now)
    )
    result = db.execute(stmt)
    db.commit()
    return result.rowcount
