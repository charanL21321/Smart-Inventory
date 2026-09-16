from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class SupplierBase(BaseModel):
    """Base schema containing supplier attributes."""
    name: str = Field(..., min_length=1, max_length=150, description="Supplier company or trade name")
    contact_person: Optional[str] = Field(None, max_length=100, description="Primary contact name")
    email: EmailStr = Field(..., description="Valid supplier email address")
    phone: str = Field(..., min_length=3, max_length=50, description="Contact phone number")
    address: Optional[str] = Field(None, max_length=255, description="Physical/mailing address")
    lead_time_days: int = Field(..., ge=0, description="Expected delivery lead time in days (>= 0)")
    minimum_order_quantity: int = Field(..., gt=0, description="Minimum allowable order quantity (> 0)")


class SupplierCreate(SupplierBase):
    """Schema for registering a new supplier."""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating supplier details."""
    name: Optional[str] = Field(None, min_length=1, max_length=150)
    contact_person: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None
    phone: Optional[str] = Field(None, min_length=3, max_length=50)
    address: Optional[str] = Field(None, max_length=255)
    lead_time_days: Optional[int] = Field(None, ge=0)
    minimum_order_quantity: Optional[int] = Field(None, gt=0)
    is_active: Optional[bool] = None


class SupplierResponse(SupplierBase):
    """Schema for returning supplier information."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
