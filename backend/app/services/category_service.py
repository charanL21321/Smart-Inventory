from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.schemas.category import CategoryCreate, CategoryUpdate


def get_category_by_id(db: Session, category_id: int) -> Optional[Category]:
    """Retrieves a single Category by primary key ID."""
    stmt = select(Category).where(Category.id == category_id)
    return db.scalars(stmt).first()


def get_category_by_name(db: Session, name: str) -> Optional[Category]:
    """Retrieves a Category by name (case-insensitive)."""
    stmt = select(Category).where(func.lower(Category.name) == name.strip().lower())
    return db.scalars(stmt).first()


def get_categories(db: Session, is_active: Optional[bool] = None) -> List[Category]:
    """
    Returns categories, optionally filtered by active status.
    """
    stmt = select(Category)
    if is_active is not None:
        stmt = stmt.where(Category.is_active == is_active)
    stmt = stmt.order_by(Category.name.asc())
    return list(db.scalars(stmt).all())


def create_category(db: Session, category_in: CategoryCreate) -> Category:
    """
    Creates a new category after validating name uniqueness.
    """
    cleaned_name = category_in.name.strip()
    if not cleaned_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Category name cannot be empty",
        )

    if get_category_by_name(db, cleaned_name):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with name '{cleaned_name}' already exists",
        )

    category = Category(
        name=cleaned_name,
        description=category_in.description.strip() if category_in.description else None,
        is_active=True,
    )
    db.add(category)
    db.commit()
    db.refresh(category)
    return category


def update_category(db: Session, category_id: int, category_in: CategoryUpdate) -> Category:
    """
    Updates an existing category. Validates duplicate names if name is changed.
    """
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found",
        )

    update_data = category_in.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        cleaned_name = update_data["name"].strip()
        if not cleaned_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Category name cannot be empty",
            )
        existing = get_category_by_name(db, cleaned_name)
        if existing and existing.id != category.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with name '{cleaned_name}' already exists",
            )
        category.name = cleaned_name

    if "description" in update_data:
        category.description = update_data["description"].strip() if update_data["description"] else None

    if "is_active" in update_data and update_data["is_active"] is not None:
        category.is_active = update_data["is_active"]

    db.commit()
    db.refresh(category)
    return category


def delete_category(db: Session, category_id: int) -> Category:
    """
    Safely deletes/deactivates a category.
    Rejects deletion if any products reference the category.
    """
    category = get_category_by_id(db, category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found",
        )

    # Check for referencing products to preserve referential integrity
    prod_stmt = select(Product).where(Product.category_id == category_id)
    referenced_product = db.scalars(prod_stmt).first()
    if referenced_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete category: it is referenced by existing products. Deactivate it instead.",
        )

    # Soft-delete / deactivate category
    category.is_active = False
    db.commit()
    db.refresh(category)
    return category
