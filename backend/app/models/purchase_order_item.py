from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.purchase_order import PurchaseOrder


class PurchaseOrderItem(Base):
    """
    SQLAlchemy PurchaseOrderItem model representing individual line items within a purchase order.
    """
    __tablename__ = "purchase_order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_po_items_quantity_positive"),
        CheckConstraint("received_quantity >= 0", name="chk_po_items_received_quantity_non_negative"),
        CheckConstraint("received_quantity <= quantity", name="chk_po_items_received_lte_quantity"),
        CheckConstraint("unit_cost >= 0", name="chk_po_items_unit_cost_non_negative"),
        CheckConstraint("total_cost >= 0", name="chk_po_items_total_cost_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    purchase_order_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("purchase_orders.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    received_quantity: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    unit_cost: Mapped[float] = mapped_column(Float, nullable=False)
    total_cost: Mapped[float] = mapped_column(Float, nullable=False)
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

    # Relationships
    purchase_order: Mapped["PurchaseOrder"] = relationship(
        "PurchaseOrder",
        back_populates="items",
    )
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="purchase_order_items",
    )

    def __repr__(self) -> str:
        return (
            f"<PurchaseOrderItem id={self.id} po_id={self.purchase_order_id} "
            f"prod_id={self.product_id} qty={self.quantity} received={self.received_quantity}>"
        )
