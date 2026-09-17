import enum
from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import Boolean, DateTime, Enum, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.demand_forecast import DemandForecast
    from app.models.product import Product
    from app.models.purchase_order import PurchaseOrder
    from app.models.replenishment_recommendation import ReplenishmentRecommendation
    from app.models.supplier import Supplier
    from app.models.user import User


class NotificationType(str, enum.Enum):
    LOW_STOCK = "LOW_STOCK"
    OUT_OF_STOCK = "OUT_OF_STOCK"
    REPLENISHMENT_RECOMMENDATION = "REPLENISHMENT_RECOMMENDATION"
    PURCHASE_ORDER_STATUS = "PURCHASE_ORDER_STATUS"
    PURCHASE_ORDER_RECEIVED = "PURCHASE_ORDER_RECEIVED"
    FORECAST_GENERATED = "FORECAST_GENERATED"


class NotificationPriority(str, enum.Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"


class Notification(Base):
    __tablename__ = "notifications"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    notification_type: Mapped[NotificationType] = mapped_column(
        Enum(NotificationType, native_enum=False, length=50),
        nullable=False,
        index=True,
    )
    priority: Mapped[NotificationPriority] = mapped_column(
        Enum(NotificationPriority, native_enum=False, length=20),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)

    # Optional Entity References
    product_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    supplier_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    purchase_order_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("purchase_orders.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    replenishment_recommendation_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("replenishment_recommendations.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    forecast_id: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("demand_forecasts.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    # Status tracking
    is_read: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False, index=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Relationships
    user: Mapped["User"] = relationship("User", back_populates="notifications")
    product: Mapped[Optional["Product"]] = relationship("Product", back_populates="notifications")
    supplier: Mapped[Optional["Supplier"]] = relationship("Supplier", back_populates="notifications")
    purchase_order: Mapped[Optional["PurchaseOrder"]] = relationship(
        "PurchaseOrder", back_populates="notifications"
    )
    replenishment_recommendation: Mapped[Optional["ReplenishmentRecommendation"]] = relationship(
        "ReplenishmentRecommendation", back_populates="notifications"
    )
    forecast: Mapped[Optional["DemandForecast"]] = relationship(
        "DemandForecast", back_populates="notifications"
    )

    def __repr__(self) -> str:
        return (
            f"<Notification(id={self.id}, user_id={self.user_id}, "
            f"type='{self.notification_type}', priority='{self.priority}', is_read={self.is_read})>"
        )
