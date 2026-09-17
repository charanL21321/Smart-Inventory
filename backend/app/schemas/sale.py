from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class SaleCreate(BaseModel):
    """
    Request schema to record a new business sale.
    Unit price is optional; if omitted, it is automatically obtained from the product's price.
    """
    product_id: int = Field(..., gt=0, description="ID of the product sold")
    quantity: int = Field(..., gt=0, description="Quantity sold, must be greater than 0")
    unit_price: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Sale unit price. If not provided, current product catalog price will be used.",
    )
    reference: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Optional business reference or transaction code",
    )


class SaleResponse(BaseModel):
    """
    Response schema returning historical sale record details.
    """
    id: int
    product_id: int
    quantity: int
    unit_price: float
    total_amount: float
    sold_by: int
    reference: Optional[str] = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
