from datetime import datetime, timezone
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.demand_forecast import DemandForecast
    from app.models.inventory import Inventory
    from app.models.inventory_transaction import InventoryTransaction
    from app.models.purchase_order_item import PurchaseOrderItem
    from app.models.replenishment_recommendation import ReplenishmentRecommendation
    from app.models.sale import Sale
    from app.models.supplier import Supplier


class Product(Base):
    """
    SQLAlchemy Product model representing inventory items and replenishment configurations.
    NOTE: Stock levels (current_stock) and transactions are deferred to Phase 4.
    """
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(150), index=True, nullable=False)
    sku: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)

    # Foreign Keys
    category_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("categories.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    supplier_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("suppliers.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )

    # Pricing & Replenishment Configurations
    price: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    reorder_point: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    safety_stock: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    target_stock: Mapped[int] = mapped_column(Integer, default=1, nullable=False)

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

    # Relationships
    category: Mapped["Category"] = relationship(
        "Category",
        back_populates="products",
    )
    supplier: Mapped["Supplier"] = relationship(
        "Supplier",
        back_populates="products",
    )
    inventory: Mapped[Optional["Inventory"]] = relationship(
        "Inventory",
        back_populates="product",
        uselist=False,
    )
    inventory_transactions: Mapped[List["InventoryTransaction"]] = relationship(
        "InventoryTransaction",
        back_populates="product",
    )
    sales: Mapped[List["Sale"]] = relationship(
        "Sale",
        back_populates="product",
        cascade="none",
    )
    purchase_order_items: Mapped[List["PurchaseOrderItem"]] = relationship(
        "PurchaseOrderItem",
        back_populates="product",
        cascade="none",
    )
    replenishment_recommendations: Mapped[List["ReplenishmentRecommendation"]] = relationship(
        "ReplenishmentRecommendation",
        back_populates="product",
        cascade="none",
    )
    demand_forecasts: Mapped[List["DemandForecast"]] = relationship(
        "DemandForecast",
        back_populates="product",
        cascade="none",
    )

    def __repr__(self) -> str:
        return f"<Product id={self.id} sku='{self.sku}' name='{self.name}'>"
