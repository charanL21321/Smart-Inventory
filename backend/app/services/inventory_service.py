from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.inventory_transaction import InventoryTransaction, TransactionType
from app.models.product import Product
from app.schemas.inventory import InventoryResponse, InventoryStatus
from app.schemas.inventory_transaction import (
    AdjustmentType,
    InventoryTransactionResponse,
    StockAdjustmentRequest,
    StockInRequest,
    StockOutRequest,
)


def calculate_inventory_status(current_stock: int, reorder_point: int) -> InventoryStatus:
    """
    Calculates dynamic stock status based on current stock and reorder point threshold.
    """
    if current_stock == 0:
        return InventoryStatus.OUT_OF_STOCK
    elif current_stock <= reorder_point:
        return InventoryStatus.LOW_STOCK
    else:
        return InventoryStatus.IN_STOCK


def to_inventory_response(inventory: Inventory, reorder_point: int) -> InventoryResponse:
    """
    Constructs an InventoryResponse with calculated available stock and status.
    """
    available_stock = max(0, inventory.current_stock - inventory.reserved_stock)
    status_val = calculate_inventory_status(inventory.current_stock, reorder_point)
    return InventoryResponse(
        id=inventory.id,
        product_id=inventory.product_id,
        current_stock=inventory.current_stock,
        reserved_stock=inventory.reserved_stock,
        available_stock=available_stock,
        status=status_val,
        created_at=inventory.created_at,
        updated_at=inventory.updated_at,
    )


def get_or_create_inventory(
    db: Session,
    product_id: int,
    lock: bool = False,
) -> Tuple[Inventory, Product]:
    """
    Retrieves or lazily initializes an inventory record for a product.
    Optionally applies row-level locking (with_for_update) to prevent race conditions.
    """
    # 1. Verify product exists
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    # 2. Verify product is active
    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot perform inventory operations on inactive product '{product.name}'",
        )

    # 3. Retrieve inventory with row locking if requested
    stmt = select(Inventory).where(Inventory.product_id == product_id)
    if lock:
        stmt = stmt.with_for_update()

    inventory = db.scalars(stmt).first()

    # 4. Lazy initialize if not yet present
    if not inventory:
        inventory = Inventory(
            product_id=product_id,
            current_stock=0,
            reserved_stock=0,
        )
        db.add(inventory)
        db.flush()
        if lock:
            # Refresh with lock now that it exists
            stmt = select(Inventory).where(Inventory.id == inventory.id).with_for_update()
            inventory = db.scalars(stmt).first()

    return inventory, product


def perform_stock_in(
    db: Session,
    data: StockInRequest,
    user_id: int,
) -> InventoryResponse:
    """
    Atomically receives stock, increments inventory balance, and logs a STOCK_IN transaction.
    """
    if data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock-in quantity must be greater than 0",
        )

    try:
        inventory, product = get_or_create_inventory(db, data.product_id, lock=True)

        previous_stock = inventory.current_stock
        resulting_stock = previous_stock + data.quantity
        inventory.current_stock = resulting_stock

        transaction = InventoryTransaction(
            product_id=data.product_id,
            transaction_type=TransactionType.STOCK_IN,
            quantity=data.quantity,
            previous_stock=previous_stock,
            resulting_stock=resulting_stock,
            reason=data.reason.strip() if data.reason else None,
            reference=data.reference.strip() if data.reference else None,
            performed_by=user_id,
        )
        db.add(transaction)
        db.commit()
        db.refresh(inventory)
        return to_inventory_response(inventory, product.reorder_point)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete stock-in operation: {exc}",
        ) from exc


def perform_stock_out(
    db: Session,
    data: StockOutRequest,
    user_id: int,
) -> InventoryResponse:
    """
    Atomically dispatches stock, decrements inventory balance, and logs a STOCK_OUT transaction.
    Ensures stock never drops below 0 or below reserved stock.
    """
    if data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Stock-out quantity must be greater than 0",
        )

    try:
        inventory, product = get_or_create_inventory(db, data.product_id, lock=True)

        previous_stock = inventory.current_stock
        available_stock = previous_stock - inventory.reserved_stock

        if data.quantity > available_stock:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Insufficient available stock",
            )

        resulting_stock = previous_stock - data.quantity
        if resulting_stock < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Stock cannot become negative",
            )

        inventory.current_stock = resulting_stock

        transaction = InventoryTransaction(
            product_id=data.product_id,
            transaction_type=TransactionType.STOCK_OUT,
            quantity=data.quantity,
            previous_stock=previous_stock,
            resulting_stock=resulting_stock,
            reason=data.reason.strip() if data.reason else None,
            reference=data.reference.strip() if data.reference else None,
            performed_by=user_id,
        )
        db.add(transaction)
        db.commit()
        db.refresh(inventory)
        return to_inventory_response(inventory, product.reorder_point)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete stock-out operation: {exc}",
        ) from exc


def perform_stock_adjustment(
    db: Session,
    data: StockAdjustmentRequest,
    user_id: int,
) -> InventoryResponse:
    """
    Atomically reconciles physical stock discrepancies.
    Mandates a valid reason and records an ADJUSTMENT_IN or ADJUSTMENT_OUT transaction.
    """
    cleaned_reason = data.reason.strip() if data.reason else ""
    if not cleaned_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment reason is mandatory",
        )

    if data.quantity <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Adjustment quantity must be greater than 0",
        )

    try:
        inventory, product = get_or_create_inventory(db, data.product_id, lock=True)

        previous_stock = inventory.current_stock

        if data.adjustment_type == AdjustmentType.ADJUSTMENT_IN:
            resulting_stock = previous_stock + data.quantity
            trans_type = TransactionType.ADJUSTMENT_IN
        elif data.adjustment_type == AdjustmentType.ADJUSTMENT_OUT:
            if previous_stock - data.quantity < 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Adjustment would result in negative stock",
                )
            available_stock = previous_stock - inventory.reserved_stock
            if data.quantity > available_stock:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Adjustment exceeds available stock",
                )
            resulting_stock = previous_stock - data.quantity
            trans_type = TransactionType.ADJUSTMENT_OUT
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported adjustment type '{data.adjustment_type}'",
            )

        inventory.current_stock = resulting_stock

        transaction = InventoryTransaction(
            product_id=data.product_id,
            transaction_type=trans_type,
            quantity=data.quantity,
            previous_stock=previous_stock,
            resulting_stock=resulting_stock,
            reason=cleaned_reason,
            reference=data.reference.strip() if data.reference else None,
            performed_by=user_id,
        )
        db.add(transaction)
        db.commit()
        db.refresh(inventory)
        return to_inventory_response(inventory, product.reorder_point)
    except HTTPException:
        db.rollback()
        raise
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to complete stock adjustment: {exc}",
        ) from exc


def get_inventory_by_product_id(db: Session, product_id: int) -> InventoryResponse:
    """
    Retrieves current stock for a specific product.
    If no inventory record exists yet for a valid product, initializes with 0 stock.
    """
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    stmt = select(Inventory).where(Inventory.product_id == product_id)
    inventory = db.scalars(stmt).first()
    if not inventory:
        # Initialize default 0 stock record
        inventory = Inventory(
            product_id=product_id,
            current_stock=0,
            reserved_stock=0,
        )
        db.add(inventory)
        db.commit()
        db.refresh(inventory)

    return to_inventory_response(inventory, product.reorder_point)


def get_inventory_list(
    db: Session,
    product_id: Optional[int] = None,
    low_stock: Optional[bool] = None,
    out_of_stock: Optional[bool] = None,
) -> List[InventoryResponse]:
    """
    Queries inventory records joining Product to evaluate dynamic status filters.
    """
    stmt = select(Inventory, Product).join(Product, Inventory.product_id == Product.id)

    if product_id is not None:
        stmt = stmt.where(Inventory.product_id == product_id)

    if out_of_stock is True:
        stmt = stmt.where(Inventory.current_stock == 0)
    elif out_of_stock is False:
        stmt = stmt.where(Inventory.current_stock > 0)

    if low_stock is True:
        # Low stock: current_stock <= reorder_point and current_stock > 0
        stmt = stmt.where(
            (Inventory.current_stock <= Product.reorder_point) & (Inventory.current_stock > 0)
        )
    elif low_stock is False:
        stmt = stmt.where(Inventory.current_stock > Product.reorder_point)

    stmt = stmt.order_by(Product.name.asc())
    results = db.execute(stmt).all()

    return [to_inventory_response(inv, prod.reorder_point) for inv, prod in results]


def get_transactions(
    db: Session,
    product_id: Optional[int] = None,
    transaction_type: Optional[TransactionType] = None,
    performed_by: Optional[int] = None,
) -> List[InventoryTransactionResponse]:
    """
    Queries historical immutable inventory transactions with optional filters.
    """
    stmt = select(InventoryTransaction)

    if product_id is not None:
        stmt = stmt.where(InventoryTransaction.product_id == product_id)

    if transaction_type is not None:
        stmt = stmt.where(InventoryTransaction.transaction_type == transaction_type)

    if performed_by is not None:
        stmt = stmt.where(InventoryTransaction.performed_by == performed_by)

    stmt = stmt.order_by(InventoryTransaction.created_at.desc())
    records = db.scalars(stmt).all()
    return [InventoryTransactionResponse.model_validate(r) for r in records]


def get_transaction_by_id(db: Session, transaction_id: int) -> InventoryTransactionResponse:
    """
    Retrieves a single immutable transaction by ID.
    """
    stmt = select(InventoryTransaction).where(InventoryTransaction.id == transaction_id)
    transaction = db.scalars(stmt).first()
    if not transaction:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Inventory transaction with ID {transaction_id} not found",
        )
    return InventoryTransactionResponse.model_validate(transaction)
