from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.schemas.sale import SaleCreate, SaleResponse
from app.services.sales_service import create_sale, get_sale_by_id, get_sales

router = APIRouter()


@router.post(
    "",
    response_model=SaleResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Record a business sale",
    description="Atomically creates a sales record, decreases stock, and registers a STOCK_OUT transaction.",
)
def record_sale_route(
    data: SaleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> SaleResponse:
    """
    Records a sale and atomically updates inventory via inventory service ledger.
    Authorized for ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    """
    sale = create_sale(db=db, data=data, user_id=current_user.id)
    return SaleResponse.model_validate(sale)


@router.get(
    "",
    response_model=List[SaleResponse],
    status_code=status.HTTP_200_OK,
    summary="Query sales history",
    description="Retrieves historical sales records with optional filtering by product, seller, reference, or date range.",
)
def list_sales_route(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    sold_by: Optional[int] = Query(None, description="Filter by user who made the sale"),
    reference: Optional[str] = Query(None, description="Filter by sale reference"),
    start_date: Optional[datetime] = Query(None, description="Filter sales starting from date"),
    end_date: Optional[datetime] = Query(None, description="Filter sales up to date"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> List[SaleResponse]:
    """
    Lists historical sales records.
    """
    sales = get_sales(
        db=db,
        product_id=product_id,
        sold_by=sold_by,
        start_date=start_date,
        end_date=end_date,
        reference=reference,
    )
    return [SaleResponse.model_validate(s) for s in sales]


@router.get(
    "/{sale_id}",
    response_model=SaleResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single sale detail",
    description="Retrieves a specific historical sale record. Sales are immutable and cannot be updated or deleted.",
)
def get_sale_route(
    sale_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> SaleResponse:
    """
    Retrieves a single historical sale.
    """
    sale = get_sale_by_id(db=db, sale_id=sale_id)
    return SaleResponse.model_validate(sale)
