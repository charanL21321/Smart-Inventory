from datetime import datetime
from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.product import Product
from app.models.sale import Sale
from app.schemas.sale import SaleCreate
from app.services.inventory_service import apply_stock_out


def create_sale(
    db: Session,
    data: SaleCreate,
    user_id: int,
) -> Sale:
    """
    Atomically records a sale and decrements inventory through the inventory service.
    Ensures transactional consistency: if inventory deduction fails (e.g. insufficient stock),
    no sale record or partial inventory change is committed.
    """
    # 1. Quantity validation
    if data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale quantity must be greater than 0",
        )

    # 2. Verify product existence
    product = db.get(Product, data.product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {data.product_id} not found",
        )

    # 3. Verify product is active
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot record sale for inactive product '{product.name}'",
        )

    # 4. Resolve unit price
    unit_price = data.unit_price if data.unit_price is not None else product.price
    if unit_price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Sale unit price cannot be negative",
        )

    # 5. Calculate total amount
    total_amount = round(data.quantity * unit_price, 2)

    try:
        # 6. Apply stock-out via Phase 4 inventory service (uses row-level locking & creates STOCK_OUT ledger)
        ref_text = data.reference.strip() if data.reference else None
        inventory, _, transaction = apply_stock_out(
            db=db,
            product_id=data.product_id,
            quantity=data.quantity,
            user_id=user_id,
            reference=ref_text,
            reason=f"Sale of {data.quantity} units",
        )

        # 7. Create Sale record
        sale = Sale(
            product_id=data.product_id,
            quantity=data.quantity,
            unit_price=unit_price,
            total_amount=total_amount,
            sold_by=user_id,
            reference=ref_text,
        )
        db.add(sale)
        db.flush()

        # If transaction reference was not explicitly provided, tie it to the created sale ID
        if not ref_text:
            transaction.reference = f"SALE-{sale.id}"
            sale.reference = transaction.reference

        # 8. Commit atomically
        db.commit()
        db.refresh(sale)
        return sale
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to record sale: {exc}",
        ) from exc


def get_sale_by_id(db: Session, sale_id: int) -> Sale:
    """
    Retrieves a single historical sale record by ID.
    """
    sale = db.get(Sale, sale_id)
    if not sale:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Sale with ID {sale_id} not found",
        )
    return sale


def get_sales(
    db: Session,
    product_id: Optional[int] = None,
    sold_by: Optional[int] = None,
    start_date: Optional[datetime] = None,
    end_date: Optional[datetime] = None,
    reference: Optional[str] = None,
) -> List[Sale]:
    """
    Queries historical sales records with dynamic filtering.
    """
    stmt = select(Sale)

    if product_id is not None:
        stmt = stmt.where(Sale.product_id == product_id)

    if sold_by is not None:
        stmt = stmt.where(Sale.sold_by == sold_by)

    if reference:
        stmt = stmt.where(Sale.reference.ilike(f"%{reference.strip()}%"))

    if start_date:
        stmt = stmt.where(Sale.created_at >= start_date)

    if end_date:
        stmt = stmt.where(Sale.created_at <= end_date)

    stmt = stmt.order_by(Sale.created_at.desc())
    return list(db.scalars(stmt).all())
