from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.services.supplier_service import (
    create_supplier,
    delete_supplier,
    get_supplier_by_id,
    get_suppliers,
    update_supplier,
)

router = APIRouter()


@router.post(
    "",
    response_model=SupplierResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new supplier",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles. Validates lead time and MOQ.",
)
def create_new_supplier(
    supplier_in: SupplierCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> SupplierResponse:
    """
    Registers a new goods supplier.
    """
    return create_supplier(db, supplier_in)


@router.get(
    "",
    response_model=List[SupplierResponse],
    status_code=status.HTTP_200_OK,
    summary="List all suppliers",
    description="Accessible by all authenticated roles (ADMIN, INVENTORY_MANAGER, WAREHOUSE_STAFF). Supports filtering by is_active.",
)
def list_suppliers(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[SupplierResponse]:
    """
    Retrieves suppliers list.
    """
    return get_suppliers(db, is_active=is_active)


@router.get(
    "/{supplier_id}",
    response_model=SupplierResponse,
    status_code=status.HTTP_200_OK,
    summary="Get supplier by ID",
    description="Accessible by all authenticated roles.",
)
def read_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SupplierResponse:
    """
    Retrieves a single supplier by ID.
    """
    supplier = get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )
    return supplier


@router.put(
    "/{supplier_id}",
    response_model=SupplierResponse,
    status_code=status.HTTP_200_OK,
    summary="Update supplier details",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles.",
)
def update_existing_supplier(
    supplier_id: int,
    supplier_in: SupplierUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> SupplierResponse:
    """
    Updates an existing supplier's details.
    """
    return update_supplier(db, supplier_id, supplier_in)


@router.delete(
    "/{supplier_id}",
    response_model=SupplierResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate or delete supplier",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles. Rejects deletion if referenced by products.",
)
def delete_existing_supplier(
    supplier_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> SupplierResponse:
    """
    Deactivates a supplier if no products reference it.
    """
    return delete_supplier(db, supplier_id)
