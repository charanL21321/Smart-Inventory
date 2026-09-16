from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.services.product_service import (
    create_product,
    delete_product,
    get_product_by_id,
    get_products,
    update_product,
)

router = APIRouter()


@router.post(
    "",
    response_model=ProductResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new product item",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles. Validates active category, active supplier, and unique SKU.",
)
def create_new_product(
    product_in: ProductCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> ProductResponse:
    """
    Registers a new product.
    """
    return create_product(db, product_in)


@router.get(
    "",
    response_model=List[ProductResponse],
    status_code=status.HTTP_200_OK,
    summary="List all products with filtering",
    description="Accessible by all authenticated roles. Supports filtering by category_id, supplier_id, is_active, SKU, and name search.",
)
def list_products(
    category_id: Optional[int] = Query(None, description="Filter by category ID"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, description="Case-insensitive search by product name"),
    sku: Optional[str] = Query(None, description="Filter by SKU substring"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[ProductResponse]:
    """
    Retrieves a list of products with optional filters.
    """
    return get_products(
        db,
        category_id=category_id,
        supplier_id=supplier_id,
        is_active=is_active,
        search=search,
        sku=sku,
    )


@router.get(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Get product by ID",
    description="Accessible by all authenticated roles.",
)
def read_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> ProductResponse:
    """
    Retrieves a single product by primary ID.
    """
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )
    return product


@router.put(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Update product details",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles. Validates updated SKU and relationships.",
)
def update_existing_product(
    product_id: int,
    product_in: ProductUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> ProductResponse:
    """
    Updates an existing product item.
    """
    return update_product(db, product_id, product_in)


@router.delete(
    "/{product_id}",
    response_model=ProductResponse,
    status_code=status.HTTP_200_OK,
    summary="Soft-delete / deactivate product",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles. Sets is_active to False to preserve inventory history.",
)
def delete_existing_product(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> ProductResponse:
    """
    Deactivates a product item without destroying referential data.
    """
    return delete_product(db, product_id)
