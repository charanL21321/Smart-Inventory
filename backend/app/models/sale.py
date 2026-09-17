from datetime import datetime, timezone
from typing import TYPE_CHECKING, Optional

from sqlalchemy import CheckConstraint, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.product import Product
    from app.models.user import User


class Sale(Base):
    """
    SQLAlchemy Sale model representing an immutable historical record of a sales transaction.
    A sale directly consumes inventory via the inventory service ledger.
    """
    __tablename__ = "sales"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="chk_sales_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="chk_sales_unit_price_non_negative"),
        CheckConstraint("total_amount >= 0", name="chk_sales_total_amount_non_negative"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False)
    unit_price: Mapped[float] = mapped_column(Float, nullable=False)
    total_amount: Mapped[float] = mapped_column(Float, nullable=False)
    sold_by: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("users.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    reference: Mapped[Optional[str]] = mapped_column(String(100), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )

    # Relationships
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="sales",
    )
    user: Mapped["User"] = relationship(
        "User",
        back_populates="sales",
    )

    def __repr__(self) -> str:
        return (
            f"<Sale id={self.id} product_id={self.product_id} "
            f"qty={self.quantity} total={self.total_amount}>"
        )
