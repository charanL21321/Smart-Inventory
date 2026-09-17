from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator

from app.models.purchase_order import PurchaseOrderStatus


# ------------------------------------------------------------------------------
# Purchase Order Item Schemas
# ------------------------------------------------------------------------------
class PurchaseOrderItemCreate(BaseModel):
    """
    Schema for adding an item to a purchase order.
    """
    product_id: int = Field(..., gt=0, description="Product ID to order")
    quantity: int = Field(..., gt=0, description="Quantity ordered (> 0)")
    unit_cost: float = Field(..., ge=0.0, description="Agreed unit cost (>= 0)")


class PurchaseOrderItemResponse(BaseModel):
    """
    Response schema for purchase order line item details.
    """
    id: int
    purchase_order_id: int
    product_id: int
    quantity: int
    received_quantity: int
    unit_cost: float
    total_cost: float
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ------------------------------------------------------------------------------
# Purchase Order Schemas
# ------------------------------------------------------------------------------
class PurchaseOrderCreate(BaseModel):
    """
    Request schema to create a purchase order.
    Initial status will be DRAFT. Total amount and order number are backend-calculated.
    """
    supplier_id: int = Field(..., gt=0, description="Supplier ID")
    items: List[PurchaseOrderItemCreate] = Field(
        ...,
        min_length=1,
        description="Purchase order line items (at least one item required)",
    )
    expected_delivery_date: Optional[datetime] = Field(
        default=None,
        description="Expected arrival date/time",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional internal notes regarding procurement",
    )


class PurchaseOrderUpdate(BaseModel):
    """
    Request schema to update an existing DRAFT purchase order.
    """
    supplier_id: Optional[int] = Field(default=None, gt=0, description="Supplier ID")
    items: Optional[List[PurchaseOrderItemCreate]] = Field(
        default=None,
        min_length=1,
        description="Updated items list (replaces existing draft items)",
    )
    expected_delivery_date: Optional[datetime] = Field(
        default=None,
        description="Updated expected delivery date",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Updated procurement notes",
    )


class PurchaseOrderStatusUpdate(BaseModel):
    """
    Request schema to transition purchase order status.
    """
    status: PurchaseOrderStatus = Field(..., description="Target status for transition")


class PurchaseOrderReceiveItem(BaseModel):
    """
    Line item receipt specification.
    Supports targeting by item_id or product_id.
    """
    item_id: Optional[int] = Field(default=None, gt=0, description="Specific line item ID")
    product_id: Optional[int] = Field(default=None, gt=0, description="Product ID in this PO")
    quantity: int = Field(..., gt=0, description="Quantity being received in this batch")

    @model_validator(mode="after")
    def validate_item_or_product(self) -> "PurchaseOrderReceiveItem":
        if self.item_id is None and self.product_id is None:
            raise ValueError("Either item_id or product_id must be provided to receive items")
        return self


class PurchaseOrderReceiveRequest(BaseModel):
    """
    Request schema to receive full or partial stock for an ordered purchase order.
    """
    items: List[PurchaseOrderReceiveItem] = Field(
        ...,
        min_length=1,
        description="List of line items and received quantities",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=500,
        description="Optional notes regarding the delivery / goods receipt",
    )


class PurchaseOrderResponse(BaseModel):
    """
    Full response representation of a purchase order including line items.
    """
    id: int
    order_number: str
    supplier_id: int
    status: PurchaseOrderStatus
    total_amount: float
    created_by: int
    approved_by: Optional[int] = None
    ordered_at: Optional[datetime] = None
    expected_delivery_date: Optional[datetime] = None
    received_at: Optional[datetime] = None
    notes: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    items: List[PurchaseOrderItemResponse]

    model_config = ConfigDict(from_attributes=True)
