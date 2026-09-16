from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class CategoryBase(BaseModel):
    """Base schema containing category fields."""
    name: str = Field(..., min_length=1, max_length=100, description="Unique category name")
    description: Optional[str] = Field(None, max_length=500, description="Optional category description")


class CategoryCreate(CategoryBase):
    """Schema for creating a category."""
    pass


class CategoryUpdate(BaseModel):
    """Schema for updating an existing category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Updated category name")
    description: Optional[str] = Field(None, max_length=500, description="Updated category description")
    is_active: Optional[bool] = Field(None, description="Active status")


class CategoryResponse(CategoryBase):
    """Schema for returning category information."""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
