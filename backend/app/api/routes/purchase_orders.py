from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database.connection import get_db
from app.models.purchase_order import PurchaseOrderStatus
from app.models.user import User, UserRole
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderReceiveRequest,
    PurchaseOrderResponse,
    PurchaseOrderStatusUpdate,
    PurchaseOrderUpdate,
)
from app.services.purchase_order_service import (
    create_purchase_order,
    get_purchase_order_by_id,
    get_purchase_orders,
    receive_purchase_order,
    update_purchase_order,
    update_purchase_order_status,
)

router = APIRouter()


@router.post(
    "",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a purchase order",
    description="Creates a new purchase order in DRAFT status. Order total and item totals are calculated by the backend.",
)
def create_purchase_order_route(
    data: PurchaseOrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> PurchaseOrderResponse:
    """
    Creates a new purchase order in DRAFT status.
    Requires ADMIN or INVENTORY_MANAGER role.
    """
    po = create_purchase_order(db=db, data=data, user_id=current_user.id)
    return PurchaseOrderResponse.model_validate(po)


@router.get(
    "",
    response_model=List[PurchaseOrderResponse],
    status_code=status.HTTP_200_OK,
    summary="List purchase orders",
    description="Retrieves purchase orders with optional filtering by supplier, status, creator, or date range.",
)
def list_purchase_orders_route(
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    status_filter: Optional[PurchaseOrderStatus] = Query(None, alias="status", description="Filter by PO status"),
    created_by: Optional[int] = Query(None, description="Filter by creator user ID"),
    start_date: Optional[datetime] = Query(None, description="Filter POs created starting from date"),
    end_date: Optional[datetime] = Query(None, description="Filter POs created up to date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> List[PurchaseOrderResponse]:
    """
    Lists purchase orders. Accessible to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    """
    orders = get_purchase_orders(
        db=db,
        supplier_id=supplier_id,
        status=status_filter,
        created_by=created_by,
        start_date=start_date,
        end_date=end_date,
    )
    return [PurchaseOrderResponse.model_validate(o) for o in orders]


@router.get(
    "/{purchase_order_id}",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Get purchase order detail",
    description="Retrieves a specific purchase order including line items and current receipt quantities.",
)
def get_purchase_order_route(
    purchase_order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> PurchaseOrderResponse:
    """
    Retrieves purchase order by ID.
    """
    po = get_purchase_order_by_id(db=db, po_id=purchase_order_id)
    return PurchaseOrderResponse.model_validate(po)


@router.put(
    "/{purchase_order_id}",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update purchase order",
    description="Updates a purchase order while in DRAFT status. Cannot modify ordered, received, or cancelled orders.",
)
def update_purchase_order_route(
    purchase_order_id: int,
    data: PurchaseOrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> PurchaseOrderResponse:
    """
    Modifies an existing DRAFT purchase order.
    Requires ADMIN or INVENTORY_MANAGER role.
    """
    po = update_purchase_order(db=db, po_id=purchase_order_id, data=data, user_id=current_user.id)
    return PurchaseOrderResponse.model_validate(po)


@router.patch(
    "/{purchase_order_id}/status",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Update purchase order status",
    description="Transitions purchase order status according to the valid workflow state machine. Warehouse staff cannot approve or modify order status.",
)
def update_purchase_order_status_route(
    purchase_order_id: int,
    data: PurchaseOrderStatusUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> PurchaseOrderResponse:
    """
    Updates purchase order status following lifecycle rules (DRAFT -> PENDING_APPROVAL -> APPROVED -> ORDERED, or CANCELLED).
    Requires ADMIN or INVENTORY_MANAGER role.
    """
    po = update_purchase_order_status(
        db=db,
        po_id=purchase_order_id,
        target_status=data.status,
        current_user=current_user,
    )
    return PurchaseOrderResponse.model_validate(po)


@router.post(
    "/{purchase_order_id}/receive",
    response_model=PurchaseOrderResponse,
    status_code=status.HTTP_200_OK,
    summary="Receive stock for purchase order",
    description="Processes full or partial goods receipt. Atomically increments stock via inventory service and records STOCK_IN transaction.",
)
def receive_purchase_order_route(
    purchase_order_id: int,
    data: PurchaseOrderReceiveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> PurchaseOrderResponse:
    """
    Receives stock for an ORDERED or PARTIALLY_RECEIVED purchase order.
    Allowed for ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    """
    po = receive_purchase_order(
        db=db,
        po_id=purchase_order_id,
        data=data,
        user_id=current_user.id,
    )
    return PurchaseOrderResponse.model_validate(po)
