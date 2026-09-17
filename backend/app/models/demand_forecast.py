import enum
from datetime import date, datetime, timezone
from typing import TYPE_CHECKING, List

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    ForeignKey,
    Integer,
    Numeric,
    String,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.notification import Notification
    from app.models.product import Product


class ForecastMethod(str, enum.Enum):
    """
    Deterministic forecasting methodologies supported by Phase 7.
    """
    SMA = "SMA"
    WMA = "WMA"


class ForecastStatus(str, enum.Enum):
    """
    Lifecycle status for a demand forecast run.
    """
    GENERATED = "GENERATED"
    ARCHIVED = "ARCHIVED"


class DemandForecast(Base):
    """
    SQLAlchemy DemandForecast model representing a generated time-series forecast run
    for a specific product over a configured future horizon.
    """
    __tablename__ = "demand_forecasts"
    __table_args__ = (
        CheckConstraint("history_days > 0", name="chk_forecast_history_days_positive"),
        CheckConstraint("forecast_horizon_days > 0", name="chk_forecast_horizon_positive"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("products.id", ondelete="RESTRICT"),
        index=True,
        nullable=False,
    )
    forecast_method: Mapped[str] = mapped_column(String(20), index=True, nullable=False)
    history_days: Mapped[int] = mapped_column(Integer, nullable=False)
    forecast_horizon_days: Mapped[int] = mapped_column(Integer, nullable=False)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        index=True,
        nullable=False,
    )
    model_version: Mapped[str] = mapped_column(String(50), default="v1", nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ForecastStatus.GENERATED.value,
        index=True,
        nullable=False,
    )
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
    product: Mapped["Product"] = relationship(
        "Product",
        back_populates="demand_forecasts",
    )
    values: Mapped[List["DemandForecastValue"]] = relationship(
        "DemandForecastValue",
        back_populates="forecast",
        cascade="all, delete-orphan",
        order_by="DemandForecastValue.forecast_date",
    )
    notifications: Mapped[List["Notification"]] = relationship(
        "Notification",
        back_populates="forecast",
        cascade="none",
    )

    def __repr__(self) -> str:
        return (
            f"<DemandForecast id={self.id} product_id={self.product_id} "
            f"method='{self.forecast_method}' status='{self.status}'>"
        )


class DemandForecastValue(Base):
    """
    SQLAlchemy DemandForecastValue model representing an individual future calendar day's
    projected demand quantity in a forecast run.
    """
    __tablename__ = "demand_forecast_values"
    __table_args__ = (
        CheckConstraint("forecast_quantity >= 0", name="chk_forecast_val_qty_non_negative"),
        UniqueConstraint("forecast_id", "forecast_date", name="uq_forecast_val_date"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True, autoincrement=True)
    forecast_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("demand_forecasts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    forecast_date: Mapped[date] = mapped_column(Date, index=True, nullable=False)
    forecast_quantity: Mapped[float] = mapped_column(Numeric(12, 4), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    forecast: Mapped["DemandForecast"] = relationship(
        "DemandForecast",
        back_populates="values",
    )

    def __repr__(self) -> str:
        return (
            f"<DemandForecastValue id={self.id} forecast_id={self.forecast_id} "
            f"date='{self.forecast_date}' qty={self.forecast_quantity}>"
        )
