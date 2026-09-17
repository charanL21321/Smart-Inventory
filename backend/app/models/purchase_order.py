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
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.notification import Notification
    from app.models.purchase_order_item import PurchaseOrderItem
    from app.models.supplier import Supplier
    from app.models.user import User


class PurchaseOrderStatus(str, Enum):
    """
    Lifecycle status enumeration for Purchase Orders.
    """
    DRAFT = "DRAFT"
    PENDING_APPROVAL = "PENDING_APPROVAL"
    APPROVED = "APPROVED"
    ORDERED = "ORDERED"
    PARTIALLY_RECEIVED = "PARTIALLY_RECEIVED"
    RECEIVED = "RECEIVED"
    CANCELLED = "CANCELLED"


class PurchaseOrder(Base):
    """
    SQLAlchemy PurchaseOrder model representing procurement orders placed with suppliers.
    """
    __tablename__ = "purchase_orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="chk_purchase_orders_total_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    order_number: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    status: Mapped[PurchaseOrderStatus] = mapped_column(
        SQLEnum(PurchaseOrderStatus, name="purchase_order_status", native_enum=False, length=30),
        default=PurchaseOrderStatus.DRAFT,
        index=True,
        nullable=False,
    )
    total_amount: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    created_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    approved_by: Mapped[Optional[int]] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        nullable=True,
    )
    ordered_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    expected_delivery_date: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    received_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    notes: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
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
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="purchase_orders",
    )
    creator: Mapped["User"] = relationship(
        "User",
        foreign_keys=[created_by],
        back_populates="created_purchase_orders",
    )
    approver: Mapped[Optional["User"]] = relationship(
        "User",
        foreign_keys=[approved_by],
        back_populates="approved_purchase_orders",
    )
    items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem",
        back_populates="purchase_order",
        cascade="all, delete-orphan",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="purchase_order",
        cascade="none",
    )

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrder id={self.id} order_number='{self.order_number}' "
            f"status='{self.status}' total={self.total_amount}>"
        )
