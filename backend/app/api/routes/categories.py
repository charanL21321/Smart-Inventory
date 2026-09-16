from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user, require_roles
from app.database.connection import get_db
from app.models.user import User, UserRole
from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.services.category_service import (
    create_category,
    delete_category,
    get_categories,
    get_category_by_id,
    update_category,
)

router = APIRouter()


@router.post(
    "",
    response_model=CategoryResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles. Rejects duplicate names.",
)
def create_new_category(
    category_in: CategoryCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> CategoryResponse:
    """
    Creates a new product category.
    """
    return create_category(db, category_in)


@router.get(
    "",
    response_model=List[CategoryResponse],
    status_code=status.HTTP_200_OK,
    summary="List all categories",
    description="Accessible by all authenticated roles (ADMIN, INVENTORY_MANAGER, WAREHOUSE_STAFF). Supports filtering by is_active.",
)
def list_categories(
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[CategoryResponse]:
    """
    Retrieves categories list.
    """
    return get_categories(db, is_active=is_active)


@router.get(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get category by ID",
    description="Accessible by all authenticated roles.",
)
def read_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> CategoryResponse:
    """
    Retrieves a single category by ID.
    """
    category = get_category_by_id(db, category_id)
    if not category:
        from fastapi import HTTPException
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found",
        )
    return category


@router.put(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Update category details",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles. Validates unique name if changed.",
)
def update_existing_category(
    category_id: int,
    category_in: CategoryUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> CategoryResponse:
    """
    Updates an existing category.
    """
    return update_category(db, category_id, category_in)


@router.delete(
    "/{category_id}",
    response_model=CategoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Deactivate or delete category",
    description="Accessible by ADMIN and INVENTORY_MANAGER roles. Rejects deletion if referenced by products.",
)
def delete_existing_category(
    category_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> CategoryResponse:
    """
    Deactivates a category if no products reference it.
    """
    return delete_category(db, category_id)
