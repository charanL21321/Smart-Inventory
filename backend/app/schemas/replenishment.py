from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from app.models.replenishment_recommendation import (
    RecommendationPriority,
    RecommendationStatus,
)


class ReplenishmentDismissRequest(BaseModel):
    """
    Request schema to dismiss a pending replenishment recommendation.
    Dismissal reason is strictly required.
    """
    reason: str = Field(
        ...,
        min_length=1,
        max_length=500,
        description="Mandatory business reason explaining why this recommendation is being dismissed",
    )


class ReplenishmentRecommendationResponse(BaseModel):
    """
    Response schema returning comprehensive replenishment recommendation analysis.
    """
    id: int
    product_id: int
    supplier_id: int
    current_stock: int
    reserved_stock: int
    inventory_position: int
    reorder_point: int
    safety_stock: int
    target_stock: int
    average_daily_demand: float
    lead_time_days: int
    lead_time_demand: float
    recommended_quantity: int
    minimum_order_quantity: int
    priority: RecommendationPriority
    reason: str
    dismissal_reason: Optional[str] = None
    status: RecommendationStatus
    generated_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
