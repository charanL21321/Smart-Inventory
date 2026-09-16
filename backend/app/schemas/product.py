from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    """Base schema containing product definition fields."""
    name: str = Field(..., min_length=1, max_length=150, description="Product name")
    sku: str = Field(..., min_length=1, max_length=50, description="Unique Stock Keeping Unit")
    description: Optional[str] = Field(None, max_length=500, description="Product description")
    category_id: int = Field(..., description="Foreign key ID of associated Category")
    supplier_id: int = Field(..., description="Foreign key ID of associated Supplier")
    price: float = Field(..., ge=0.0, description="Product unit price (>= 0)")
    reorder_point: int = Field(..., ge=0, description="Threshold quantity to trigger reorder (>= 0)")
    safety_stock: int = Field(..., ge=0, description="Buffer stock to prevent stockouts (>= 0)")
    target_stock: int = Field(..., gt=0, description="Ideal target inventory level (> 0)")


class ProductCreate(ProductBase):
    """Schema for registering a new product item."""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating product specifications and thresholds."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    sku: Optional[str] = Field(None, min_length=1, max_length=50)
    description: Optional[str] = Field(None, max_length=500)
    category_id: Optional[int] = None
    supplier_id: Optional[int] = None
    price: Optional[float] = Field(None, ge=0.0)
    reorder_point: Optional[int] = Field(None, ge=0)
    safety_stock: Optional[int] = Field(None, ge=0)
    target_stock: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class ProductResponse(ProductBase):
    """Schema for returning product details."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
