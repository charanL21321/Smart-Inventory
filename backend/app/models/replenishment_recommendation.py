from datetime import datetime, timezone
from enum import Enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Enum as SQLEnum,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.notification import Notification
    from app.models.product import Product
    from app.models.supplier import Supplier


class RecommendationStatus(str, Enum):
    """
    Status lifecycle of a replenishment recommendation.
    """
    PENDING = "PENDING"
    REVIEWED = "REVIEWED"
    DISMISSED = "DISMISSED"


class RecommendationPriority(str, Enum):
    """
    Deterministic operational priority of a replenishment recommendation.
    """
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class ReplenishmentRecommendation(Base):
    """
    SQLAlchemy model storing rule-based replenishment recommendations.
    Each record represents a snapshot of calculations at generation time.
    """
    __tablename__ = "replenishment_recommendations"
    __table_args__ = (
        CheckConstraint("current_stock >= 0", name="chk_rec_current_stock_non_negative"),
        CheckConstraint("reserved_stock >= 0", name="chk_rec_reserved_stock_non_negative"),
        CheckConstraint("inventory_position >= 0", name="chk_rec_inv_pos_non_negative"),
        CheckConstraint("reorder_point >= 0", name="chk_rec_reorder_point_non_negative"),
        CheckConstraint("safety_stock >= 0", name="chk_rec_safety_stock_non_negative"),
        CheckConstraint("target_stock > 0", name="chk_rec_target_stock_positive"),
        CheckConstraint("average_daily_demand >= 0", name="chk_rec_avg_daily_demand_non_negative"),
        CheckConstraint("lead_time_days >= 0", name="chk_rec_lead_time_days_non_negative"),
        CheckConstraint("lead_time_demand >= 0", name="chk_rec_lead_time_demand_non_negative"),
        CheckConstraint("recommended_quantity >= 0", name="chk_rec_recommended_qty_non_negative"),
        CheckConstraint("minimum_order_quantity > 0", name="chk_rec_moq_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    # Inventory & Policy Snapshot
    current_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    reserved_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    inventory_position: Mapped[int] = mapped_column(Integer, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, nullable=False)
    target_stock: Mapped[int] = mapped_column(Integer, nullable=False)

    # Demand & Lead-Time Analysis
    average_daily_demand: Mapped[float] = mapped_column(Float, nullable=False)
    lead_time_days: Mapped[int] = mapped_column(Integer, nullable=False)
    lead_time_demand: Mapped[float] = mapped_column(Float, nullable=False)

    # Recommendation Outputs
    recommended_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    minimum_order_quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    priority: Mapped[RecommendationPriority] = mapped_column(
        SQLEnum(RecommendationPriority, name="recommendation_priority", native_enum=False, length=20),
        index=True,
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    dismissal_reason: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Status Lifecycle
    status: Mapped[RecommendationStatus] = mapped_column(
        SQLEnum(RecommendationStatus, name="recommendation_status", native_enum=False, length=20),
        default=RecommendationStatus.PENDING,
        index=True,
        nullable=False,
    )
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="replenishment_recommendations",
    )
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="replenishment_recommendations",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="replenishment_recommendation",
        cascade="none",
    )

    def __repr__(self) -> str:
        return (
            f"<ReplenishmentRecommendation id={self.id} product_id={self.product_id} "
            f"rec_qty={self.recommended_quantity} priority='{self.priority}' status='{self.status}'>"
        )
