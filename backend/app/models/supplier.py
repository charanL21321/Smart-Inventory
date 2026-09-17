from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.notification import Notification
    from app.models.product import Product
    from app.models.purchase_order import PurchaseOrder
    from app.models.replenishment_recommendation import ReplenishmentRecommendation


class Supplier(Base):
    """
    SQLAlchemy Supplier model representing goods vendors/distributors.
    """
    __tablename__ = "suppliers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    contact_person: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    email: Mapped[str] = mapped_column(String(255), nullable=False)
    phone: Mapped[str] = mapped_column(String(50), nullable=False)
    address: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    lead_time_days: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    minimum_order_quantity: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationship to products
    products: Mapped[List["Product"]] = relationship(
        "Product",
        back_populates="supplier",
        cascade="none",
    )
    purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        back_populates="supplier",
        cascade="none",
    )
    replenishment_recommendations: Mapped[List["ReplenishmentRecommendation"]] = relationship(
        "ReplenishmentRecommendation",
        back_populates="supplier",
        cascade="none",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="supplier",
        cascade="none",
    )

    def __repr__(self) -> str:
        return f"<Supplier id={self.id} name='{self.name}' active={self.is_active}>"
