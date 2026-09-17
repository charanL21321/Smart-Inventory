from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.models.notification import NotificationPriority, NotificationType


class NotificationResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    notification_type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    product_id: Optional[int] = None
    supplier_id: Optional[int] = None
    purchase_order_id: Optional[int] = None
    replenishment_recommendation_id: Optional[int] = None
    forecast_id: Optional[int] = None
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None


class UnreadCountResponse(BaseModel):
    unread_count: int
