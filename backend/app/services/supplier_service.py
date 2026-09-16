from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.supplier import Supplier
from app.schemas.supplier import SupplierCreate, SupplierUpdate


def get_supplier_by_id(db: Session, supplier_id: int) -> Optional[Supplier]:
    """Retrieves a single Supplier by primary key ID."""
    stmt = select(Supplier).where(Supplier.id == supplier_id)
    return db.scalars(stmt).first()


def get_suppliers(db: Session, is_active: Optional[bool] = None) -> List[Supplier]:
    """
    Returns suppliers, optionally filtered by active status.
    """
    stmt = select(Supplier)
    if is_active is not None:
        stmt = stmt.where(Supplier.is_active == is_active)
    stmt = stmt.order_by(Supplier.name.asc())
    return list(db.scalars(stmt).all())


def create_supplier(db: Session, supplier_in: SupplierCreate) -> Supplier:
    """
    Registers a new supplier after validating operational thresholds.
    """
    cleaned_name = supplier_in.name.strip()
    if not cleaned_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier name cannot be empty",
        )

    if supplier_in.lead_time_days < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Lead time days must be greater than or equal to 0",
        )

    if supplier_in.minimum_order_quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Minimum order quantity must be greater than 0",
        )

    cleaned_phone = supplier_in.phone.strip()
    if len(cleaned_phone) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier phone number must be a valid contact value",
        )

    supplier = Supplier(
        name=cleaned_name,
        contact_person=supplier_in.contact_person.strip() if supplier_in.contact_person else None,
        email=supplier_in.email.strip().lower(),
        phone=cleaned_phone,
        address=supplier_in.address.strip() if supplier_in.address else None,
        lead_time_days=supplier_in.lead_time_days,
        minimum_order_quantity=supplier_in.minimum_order_quantity,
        is_active=True,
    )
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


def update_supplier(db: Session, supplier_id: int, supplier_in: SupplierUpdate) -> Supplier:
    """
    Updates an existing supplier's details and constraints.
    """
    supplier = get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    update_data = supplier_in.model_dump(exclude_unset=True)

    if "name" in update_data and update_data["name"] is not None:
        cleaned_name = update_data["name"].strip()
        if not cleaned_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier name cannot be empty",
            )
        supplier.name = cleaned_name

    if "contact_person" in update_data:
        supplier.contact_person = update_data["contact_person"].strip() if update_data["contact_person"] else None

    if "email" in update_data and update_data["email"] is not None:
        supplier.email = update_data["email"].strip().lower()

    if "phone" in update_data and update_data["phone"] is not None:
        cleaned_phone = update_data["phone"].strip()
        if len(cleaned_phone) < 3:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Supplier phone number must be a valid contact value",
            )
        supplier.phone = cleaned_phone

    if "address" in update_data:
        supplier.address = update_data["address"].strip() if update_data["address"] else None

    if "lead_time_days" in update_data and update_data["lead_time_days"] is not None:
        if update_data["lead_time_days"] < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Lead time days must be greater than or equal to 0",
            )
        supplier.lead_time_days = update_data["lead_time_days"]

    if "minimum_order_quantity" in update_data and update_data["minimum_order_quantity"] is not None:
        if update_data["minimum_order_quantity"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Minimum order quantity must be greater than 0",
            )
        supplier.minimum_order_quantity = update_data["minimum_order_quantity"]

    if "is_active" in update_data and update_data["is_active"] is not None:
        supplier.is_active = update_data["is_active"]

    db.commit()
    db.refresh(supplier)
    return supplier


def delete_supplier(db: Session, supplier_id: int) -> Supplier:
    """
    Safely deletes/deactivates a supplier.
    Rejects deletion if any products reference the supplier.
    """
    supplier = get_supplier_by_id(db, supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with ID {supplier_id} not found",
        )

    # Check for referencing products to protect referential integrity
    prod_stmt = select(Product).where(Product.supplier_id == supplier_id)
    referenced_product = db.scalars(prod_stmt).first()
    if referenced_product:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete supplier: it is referenced by existing products. Deactivate it instead.",
        )

    # Soft-delete / deactivate supplier
    supplier.is_active = False
    db.commit()
    db.refresh(supplier)
    return supplier
