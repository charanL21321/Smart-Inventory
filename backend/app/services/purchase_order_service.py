from datetime import datetime, timezone
from typing import List, Optional
import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models.product import Product
from app.models.purchase_order import PurchaseOrder, PurchaseOrderStatus
from app.models.purchase_order_item import PurchaseOrderItem
from app.models.supplier import Supplier
from app.models.user import User, UserRole
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderReceiveRequest,
    PurchaseOrderUpdate,
)
from app.services.inventory_service import apply_stock_in


def generate_order_number() -> str:
    """
    Generates a unique, standardized purchase order number.
    Format: PO-YYYYMMDD-XXXXXX
    """
    today_str = datetime.now(timezone.utc).strftime("%Y%m%d")
    unique_suffix = uuid.uuid4().hex[:6].upper()
    return f"PO-{today_str}-{unique_suffix}"


def create_purchase_order(
    db: Session,
    data: PurchaseOrderCreate,
    user_id: int,
) -> PurchaseOrder:
    """
    Creates a new purchase order in DRAFT status.
    Calculates item and order totals in the backend; client cannot manipulate totals.
    Does NOT modify inventory at this stage.
    """
    # 1. Validate supplier existence and active state
    supplier = db.get(Supplier, data.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {data.supplier_id} not found",
        )
    if not supplier.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot create purchase order for inactive supplier '{supplier.name}'",
        )

    # 2. Validate at least one item
    if not data.items:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order must contain at least one item",
        )

    # 3. Validate items and products
    total_order_amount = 0.0
    po_items: List[PurchaseOrderItem] = []

    for item in data.items:
        if item.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Quantity for product ID {item.product_id} must be greater than 0",
            )
        if item.unit_cost < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unit cost for product ID {item.product_id} cannot be negative",
            )

        product = db.get(Product, item.product_id)
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with ID {item.product_id} not found",
            )
        if not product.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot add inactive product '{product.name}' to purchase order",
            )

        total_cost = round(item.quantity * item.unit_cost, 2)
        total_order_amount += total_cost

        po_item = PurchaseOrderItem(
            product_id=item.product_id,
            quantity=item.quantity,
            received_quantity=0,
            unit_cost=item.unit_cost,
            total_cost=total_cost,
        )
        po_items.append(po_item)

    total_order_amount = round(total_order_amount, 2)
    order_number = generate_order_number()

    try:
        po = PurchaseOrder(
            order_number=order_number,
            supplier_id=data.supplier_id,
            status=PurchaseOrderStatus.DRAFT,
            total_amount=total_order_amount,
            created_by=user_id,
            expected_delivery_date=data.expected_delivery_date,
            notes=data.notes.strip() if data.notes else None,
            items=po_items,
        )
        db.add(po)
        db.commit()
        db.refresh(po)
        return po
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create purchase order: {exc}",
        ) from exc


def get_purchase_order_by_id(db: Session, po_id: int) -> PurchaseOrder:
    """
    Retrieves a single purchase order by ID including line items.
    """
    stmt = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .options(selectinload(PurchaseOrder.items))
    )
    po = db.scalars(stmt).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found",
        )
    return po


def get_purchase_orders(
    db: Session,
    supplier_id: Optional[int] = None,
    status: Optional[PurchaseOrderStatus] = None,
    created_by: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
) -> List[PurchaseOrder]:
    """
    Queries purchase orders with optional filtering, ordered newest first.
    """
    stmt = select(PurchaseOrder).options(selectinload(PurchaseOrder.items))

    if supplier_id is not None:
        stmt = stmt.where(PurchaseOrder.supplier_id == supplier_id)

    if status is not None:
        stmt = stmt.where(PurchaseOrder.status == status)

    if created_by is not None:
        stmt = stmt.where(PurchaseOrder.created_by == created_by)

    if start_date:
        stmt = stmt.where(PurchaseOrder.created_at >= start_date)

    if end_date:
        stmt = stmt.where(PurchaseOrder.created_at <= end_date)

    stmt = stmt.order_by(PurchaseOrder.created_at.desc())
    return list(db.scalars(stmt).all())


def update_purchase_order(
    db: Session,
    po_id: int,
    data: PurchaseOrderUpdate,
    user_id: int,
) -> PurchaseOrder:
    """
    Updates purchase order details. Allowed ONLY when status is DRAFT.
    """
    po = get_purchase_order_by_id(db, po_id)

    if po.status != PurchaseOrderStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot modify purchase order with status '{po.status.value}'. Only DRAFT orders can be modified.",
        )

    # 1. Update supplier if requested
    if data.supplier_id is not None and data.supplier_id != po.supplier_id:
        supplier = db.get(Supplier, data.supplier_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Supplier with ID {data.supplier_id} not found",
            )
        if not supplier.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot assign inactive supplier '{supplier.name}' to purchase order",
            )
        po.supplier_id = data.supplier_id

    # 2. Update expected delivery date and notes
    if data.expected_delivery_date is not None:
        po.expected_delivery_date = data.expected_delivery_date
    if data.notes is not None:
        po.notes = data.notes.strip() if data.notes else None

    # 3. Update items if provided
    if data.items is not None:
        if len(data.items) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Purchase order must contain at least one item",
            )

        # Clear existing items
        po.items.clear()
        total_order_amount = 0.0

        for item in data.items:
            if item.quantity <= 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Quantity for product ID {item.product_id} must be greater than 0",
                )
            if item.unit_cost < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Unit cost for product ID {item.product_id} cannot be negative",
                )

            product = db.get(Product, item.product_id)
            if not product:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Product with ID {item.product_id} not found",
                )
            if not product.is_active:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Cannot add inactive product '{product.name}' to purchase order",
                )

            total_cost = round(item.quantity * item.unit_cost, 2)
            total_order_amount += total_cost

            po_item = PurchaseOrderItem(
                purchase_order_id=po.id,
                product_id=item.product_id,
                quantity=item.quantity,
                received_quantity=0,
                unit_cost=item.unit_cost,
                total_cost=total_cost,
            )
            po.items.append(po_item)

        po.total_amount = round(total_order_amount, 2)

    po.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(po)
        return po
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update purchase order: {exc}",
        ) from exc


def update_purchase_order_status(
    db: Session,
    po_id: int,
    target_status: PurchaseOrderStatus,
    current_user: User,
) -> PurchaseOrder:
    """
    Enforces valid purchase order state machine transitions.
    Warehouse staff are strictly forbidden from approving or changing commercial order statuses.
    """
    if current_user.role == UserRole.WAREHOUSE_STAFF:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Warehouse staff are not authorized to update purchase order commercial status",
        )

    stmt = select(PurchaseOrder).where(PurchaseOrder.id == po_id).with_for_update()
    po = db.scalars(stmt).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found",
        )

    current_st = po.status

    # Terminal state checks
    if current_st == PurchaseOrderStatus.RECEIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change status of an order that has already been RECEIVED",
        )
    if current_st == PurchaseOrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change status of a CANCELLED purchase order",
        )

    # Disallow direct jump to receiving statuses via PATCH status endpoint
    if target_status in (PurchaseOrderStatus.PARTIALLY_RECEIVED, PurchaseOrderStatus.RECEIVED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order status cannot be manually set to receiving statuses. Use the receive endpoint instead.",
        )

    # Valid transitions mapping
    valid_transitions = {
        PurchaseOrderStatus.DRAFT: [
            PurchaseOrderStatus.PENDING_APPROVAL,
            PurchaseOrderStatus.CANCELLED,
        ],
        PurchaseOrderStatus.PENDING_APPROVAL: [
            PurchaseOrderStatus.APPROVED,
            PurchaseOrderStatus.CANCELLED,
        ],
        PurchaseOrderStatus.APPROVED: [
            PurchaseOrderStatus.ORDERED,
            PurchaseOrderStatus.CANCELLED,
        ],
        PurchaseOrderStatus.ORDERED: [],
        PurchaseOrderStatus.PARTIALLY_RECEIVED: [],
    }

    allowed_targets = valid_transitions.get(current_st, [])
    if target_status not in allowed_targets:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid status transition from '{current_st.value}' to '{target_status.value}'",
        )

    # Handle transitions
    if target_status == PurchaseOrderStatus.APPROVED:
        po.approved_by = current_user.id
    elif target_status == PurchaseOrderStatus.ORDERED:
        po.ordered_at = datetime.now(timezone.utc)

    po.status = target_status
    po.updated_at = datetime.now(timezone.utc)

    # Trigger PURCHASE_ORDER_STATUS notification
    from app.services.notification_service import create_purchase_order_status_notification
    create_purchase_order_status_notification(db, po)

    try:
        db.commit()
        db.refresh(po)
        return get_purchase_order_by_id(db, po.id)
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update purchase order status: {exc}",
        ) from exc


def receive_purchase_order(
    db: Session,
    po_id: int,
    data: PurchaseOrderReceiveRequest,
    user_id: int,
) -> PurchaseOrder:
    """
    Receives full or partial quantities for an ordered purchase order.
    Atomically updates inventory (via inventory_service.apply_stock_in), creates STOCK_IN
    transactions, updates item received_quantities, and evaluates PO status.
    Uses row-level locking to prevent concurrency race conditions.
    """
    # 1. Lock the PurchaseOrder row to serialize receipt operations
    stmt = (
        select(PurchaseOrder)
        .where(PurchaseOrder.id == po_id)
        .options(selectinload(PurchaseOrder.items))
        .with_for_update()
    )
    po = db.scalars(stmt).first()
    if not po:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Purchase order with ID {po_id} not found",
        )

    # 2. Check order status
    if po.status == PurchaseOrderStatus.CANCELLED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot receive stock for a CANCELLED purchase order",
        )
    if po.status == PurchaseOrderStatus.RECEIVED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Purchase order has already been fully received",
        )
    if po.status not in (PurchaseOrderStatus.ORDERED, PurchaseOrderStatus.PARTIALLY_RECEIVED):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                f"Cannot receive stock for purchase order with status '{po.status.value}'. "
                "Order must be in ORDERED or PARTIALLY_RECEIVED state."
            ),
        )

    # 3. Index items by ID and product_id for fast lookup
    items_by_id = {item.id: item for item in po.items}
    items_by_prod = {item.product_id: item for item in po.items}

    # 4. Pre-validate receipt items and remaining quantities
    matched_receipts = []
    for req_item in data.items:
        if req_item.quantity <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Received quantity must be greater than 0",
            )

        po_item = None
        if req_item.item_id is not None:
            po_item = items_by_id.get(req_item.item_id)
        elif req_item.product_id is not None:
            po_item = items_by_prod.get(req_item.product_id)

        if not po_item:
            identifier = f"item_id={req_item.item_id}" if req_item.item_id else f"product_id={req_item.product_id}"
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Item with {identifier} does not belong to purchase order {po.order_number}",
            )

        product = db.get(Product, po_item.product_id)
        if not product or not product.is_active:
            prod_name = product.name if product else str(po_item.product_id)
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Cannot receive stock for inactive product '{prod_name}'",
            )

        remaining_qty = po_item.quantity - po_item.received_quantity
        if req_item.quantity > remaining_qty:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=(
                    f"Cannot receive {req_item.quantity} units for product ID {po_item.product_id}. "
                    f"Only {remaining_qty} units remaining to be received (ordered: {po_item.quantity}, "
                    f"already received: {po_item.received_quantity})."
                ),
            )

        matched_receipts.append((po_item, req_item.quantity))

    # 5. Apply inventory updates and update received quantities atomically
    try:
        now_dt = datetime.now(timezone.utc)
        for po_item, qty in matched_receipts:
            # Integrate via inventory_service (maintains row locking, stock balance, and ledger)
            apply_stock_in(
                db=db,
                product_id=po_item.product_id,
                quantity=qty,
                user_id=user_id,
                reference=po.order_number,
                reason=f"Stock received from Purchase Order {po.order_number}",
            )
            po_item.received_quantity += qty
            po_item.updated_at = now_dt

        # 6. Evaluate new purchase order status
        all_fully_received = all(item.received_quantity == item.quantity for item in po.items)
        from app.services.notification_service import (
            create_purchase_order_received_notification,
            create_purchase_order_status_notification,
        )
        if all_fully_received:
            po.status = PurchaseOrderStatus.RECEIVED
            po.received_at = now_dt
            create_purchase_order_received_notification(db, po)
        else:
            po.status = PurchaseOrderStatus.PARTIALLY_RECEIVED
            create_purchase_order_status_notification(db, po)

        po.updated_at = now_dt

        # 7. Atomically commit all changes together
        db.commit()
        db.refresh(po)
        return get_purchase_order_by_id(db, po.id)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to process purchase order receiving: {exc}",
        ) from exc
