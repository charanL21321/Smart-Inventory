from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database.connection import get_db
from app.models.inventory_transaction import TransactionType
from app.models.user import User, UserRole
from app.schemas.inventory import InventoryResponse
from app.schemas.inventory_transaction import (
    InventoryTransactionResponse,
    StockAdjustmentRequest,
    StockInRequest,
    StockOutRequest,
)
from app.services.inventory_service import (
    get_inventory_by_product_id,
    get_inventory_list,
    get_transaction_by_id,
    get_transactions,
    perform_stock_adjustment,
    perform_stock_in,
    perform_stock_out,
)

router = APIRouter()


@router.post(
    "/stock-in",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Receive stock into inventory",
    description="Accessible by ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF. Atomically increments stock and creates an immutable transaction log.",
)
def stock_in(
    data: StockInRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryResponse:
    """
    Performs a stock-in operation.
    """
    return perform_stock_in(db, data, current_user.id)


@router.post(
    "/stock-out",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Dispatch stock from inventory",
    description="Accessible by ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF. Atomically decrements stock and ensures available stock is sufficient.",
)
def stock_out(
    data: StockOutRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryResponse:
    """
    Performs a stock-out operation.
    """
    return perform_stock_out(db, data, current_user.id)


@router.post(
    "/adjustment",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Perform manual stock adjustment",
    description="Accessible ONLY by ADMIN and INVENTORY_MANAGER. WAREHOUSE_STAFF is strictly forbidden. Mandatory audit reason required.",
)
def stock_adjustment(
    data: StockAdjustmentRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> InventoryResponse:
    """
    Reconciles inventory counts through manual adjustments.
    """
    return perform_stock_adjustment(db, data, current_user.id)


@router.get(
    "",
    response_model=List[InventoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List inventory balances",
    description="Accessible by all authenticated roles. Supports filtering by product_id, low_stock, and out_of_stock.",
)
def list_inventory(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    low_stock: Optional[bool] = Query(None, description="Filter items at or below reorder point"),
    out_of_stock: Optional[bool] = Query(None, description="Filter items with zero current stock"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[InventoryResponse]:
    """
    Queries current stock balances and evaluated status.
    """
    return get_inventory_list(
        db,
        product_id=product_id,
        low_stock=low_stock,
        out_of_stock=out_of_stock,
    )


@router.get(
    "/transactions",
    response_model=List[InventoryTransactionResponse],
    status_code=status.HTTP_200_OK,
    summary="List historical inventory transactions",
    description="Accessible by all authenticated roles. Transactions are strictly immutable and historical.",
)
def list_transactions(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    transaction_type: Optional[TransactionType] = Query(None, description="Filter by transaction type"),
    performed_by: Optional[int] = Query(None, description="Filter by user ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[InventoryTransactionResponse]:
    """
    Queries the immutable transaction audit trail.
    """
    return get_transactions(
        db,
        product_id=product_id,
        transaction_type=transaction_type,
        performed_by=performed_by,
    )


@router.get(
    "/transactions/{transaction_id}",
    response_model=InventoryTransactionResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single transaction detail",
    description="Accessible by all authenticated roles. Read-only historical record.",
)
def read_transaction(
    transaction_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryTransactionResponse:
    """
    Retrieves a single historical transaction by ID.
    """
    return get_transaction_by_id(db, transaction_id)


@router.get(
    "/{product_id}",
    response_model=InventoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get inventory balance for a product",
    description="Accessible by all authenticated roles. Returns calculated available stock and status.",
)
def read_inventory_for_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> InventoryResponse:
    """
    Retrieves stock balance for a product.
    """
    return get_inventory_by_product_id(db, product_id)
