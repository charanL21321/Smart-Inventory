from datetime import datetime, timezone
from enum import Enum

from typing import TYPE_CHECKING, List

from sqlalchemy import Boolean, DateTime, Enum as SQLEnum, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.inventory_transaction import InventoryTransaction
    from app.models.purchase_order import PurchaseOrder
    from app.models.sale import Sale


class UserRole(str, Enum):
    """
    Role enumeration for user authorization levels.
    """
    ADMIN = "ADMIN"
    INVENTORY_MANAGER = "INVENTORY_MANAGER"
    WAREHOUSE_STAFF = "WAREHOUSE_STAFF"


class User(Base):
    """
    SQLAlchemy User model representing platform users.
    """
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True, nullable=False)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True, nullable=False)
    hashed_password: Mapped[str] = mapped_column(String(255), nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole, name="user_role", native_enum=False, length=30),
        default=UserRole.WAREHOUSE_STAFF,
        nullable=False,
    )
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
    inventory_transactions: Mapped[List["InventoryTransaction"]] = relationship(
        "InventoryTransaction",
        back_populates="user",
    )
    sales: Mapped[List["Sale"]] = relationship(
        "Sale",
        back_populates="user",
        cascade="none",
    )
    created_purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys="PurchaseOrder.created_by",
        back_populates="creator",
        cascade="none",
    )
    approved_purchase_orders: Mapped[List["PurchaseOrder"]] = relationship(
        "PurchaseOrder",
        foreign_keys="PurchaseOrder.approved_by",
        back_populates="approver",
        cascade="none",
    )

    def __repr__(self) -> str:
        return f"<User id={self.id} username='{self.username}' role='{self.role}'>"
