from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.inventory_transaction import TransactionType


class AdjustmentType(str, Enum):
    """Adjustment direction for manual stock reconciliations."""
    ADJUSTMENT_IN = "ADJUSTMENT_IN"
    ADJUSTMENT_OUT = "ADJUSTMENT_OUT"


class StockInRequest(BaseModel):
    """Schema for receiving stock into inventory."""
    product_id: int = Field(..., description="ID of product to receive stock for")
    quantity: int = Field(..., gt=0, description="Quantity to add (must be > 0)")
    reason: Optional[str] = Field(None, max_length=255, description="Optional note or reason")
    reference: Optional[str] = Field(None, max_length=100, description="Optional external reference (e.g. PO/Invoice number)")


class StockOutRequest(BaseModel):
    """Schema for dispatching or deducting stock from inventory."""
    product_id: int = Field(..., description="ID of product to deduct stock from")
    quantity: int = Field(..., gt=0, description="Quantity to deduct (must be > 0)")
    reason: Optional[str] = Field(None, max_length=255, description="Optional note or reason")
    reference: Optional[str] = Field(None, max_length=100, description="Optional external reference (e.g. Order/Dispatch number)")


class StockAdjustmentRequest(BaseModel):
    """Schema for manual stock correction."""
    product_id: int = Field(..., description="ID of product being adjusted")
    quantity: int = Field(..., gt=0, description="Adjustment quantity magnitude (must be > 0)")
    adjustment_type: AdjustmentType = Field(..., description="ADJUSTMENT_IN (increase) or ADJUSTMENT_OUT (decrease)")
    reason: str = Field(..., min_length=1, max_length=255, description="Mandatory reason for reconciliation")
    reference: Optional[str] = Field(None, max_length=100, description="Optional audit or reconciliation ticket reference")


class InventoryTransactionResponse(BaseModel):
    """Schema for immutable transaction log entries."""
    id: int
    product_id: int
    transaction_type: TransactionType
    quantity: int
    previous_stock: int
    resulting_stock: int
    reason: Optional[str]
    reference: Optional[str]
    performed_by: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
