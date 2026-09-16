from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class InventoryStatus(str, Enum):
    """Dynamically calculated inventory status."""
    IN_STOCK = "IN_STOCK"
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"


class InventoryResponse(BaseModel):
    """Schema for current stock status of a product."""
    id: int
    product_id: int
    current_stock: int
    reserved_stock: int
    available_stock: int = Field(..., description="Calculated as current_stock - reserved_stock")
    status: InventoryStatus = Field(..., description="Dynamically evaluated against product reorder_point")
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
