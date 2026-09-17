from collections import defaultdict
from datetime import date, datetime, timedelta, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy.orm import Session, joinedload

from app.core.config import settings
from app.models.demand_forecast import (
    DemandForecast,
    DemandForecastValue,
    ForecastMethod,
    ForecastStatus,
)
from app.models.product import Product
from app.models.sale import Sale


# ==============================================================================
# 1. Pure Calculation & Statistical Helpers
# ==============================================================================

def get_daily_sales_history(
    db: Session,
    product_id: int,
    history_days: int,
    reference_date: Optional[date] = None,
) -> List[Tuple[date, float]]:
    """
    Constructs a continuous daily demand series for a product covering exactly
    history_days calendar days up to and including reference_date.
    Zero-sales calendar days are explicitly represented with 0.0 units.
    """
    if history_days <= 0:
        return []

    if reference_date is None:
        reference_date = datetime.now(timezone.utc).date()

    start_date = reference_date - timedelta(days=history_days - 1)
    start_dt = datetime.combine(start_date, datetime.min.time(), tzinfo=timezone.utc)
    end_dt = datetime.combine(reference_date, datetime.max.time(), tzinfo=timezone.utc)

    # Query all historical sales within the datetime range for this product
    sales = (
        db.query(Sale)
        .filter(
            Sale.product_id == product_id,
            Sale.created_at >= start_dt,
            Sale.created_at <= end_dt,
        )
        .all()
    )

    # Aggregate sales quantities by calendar date
    daily_map = defaultdict(float)
    for s in sales:
        s_date = s.created_at.date() if isinstance(s.created_at, datetime) else s.created_at
        daily_map[s_date] += float(s.quantity)

    # Build continuous chronological series with zero-sales days
    series: List[Tuple[date, float]] = []
    for i in range(history_days):
        day = start_date + timedelta(days=i)
        series.append((day, daily_map.get(day, 0.0)))

    return series


def calculate_sma(daily_demand_values: List[float], history_days: int) -> float:
    """
    Calculates Simple Moving Average (SMA) across the continuous daily demand series:
    SMA = sum(daily_demand_values) / history_days
    Preserves decimal precision.
    """
    if history_days <= 0:
        return 0.0
    total_demand = sum(daily_demand_values)
    return total_demand / float(history_days)


def calculate_wma(daily_demand_values: List[float], wma_window: int) -> float:
    """
    Calculates Weighted Moving Average (WMA) using the most recent wma_window days.
    Weights scale linearly from 1 (oldest in window) to wma_window (most recent day):
    WMA = sum(demand_i * weight_i) / sum(weight_i)
    Preserves decimal precision.
    """
    if wma_window <= 0:
        raise ValueError("WMA window must be greater than 0")

    if not daily_demand_values:
        return 0.0

    # Ensure window has exactly wma_window entries (pad with leading zeros if fewer days available)
    if len(daily_demand_values) < wma_window:
        window_values = [0.0] * (wma_window - len(daily_demand_values)) + daily_demand_values
    else:
        window_values = daily_demand_values[-wma_window:]

    # Oldest in window has weight 1, latest has weight wma_window
    numerator = sum(window_values[i - 1] * i for i in range(1, wma_window + 1))
    denominator = sum(range(1, wma_window + 1))

    if denominator == 0:
        return 0.0

    return numerator / float(denominator)


def build_forecast_explanation(
    method: ForecastMethod,
    history_days: int,
    horizon_days: int,
    wma_window: int,
) -> str:
    """
    Generates explainable, transparent metadata explaining the forecast methodology.
    """
    if method == ForecastMethod.WMA:
        return f"{wma_window}-day weighted moving-average forecast based on historical daily sales over {horizon_days}-day horizon."
    return f"{history_days}-day simple moving-average forecast based on historical daily sales over {horizon_days}-day horizon."


def generate_forecast_dates(reference_date: date, horizon_days: int) -> List[date]:
    """
    Generates future calendar dates starting on the next calendar day after reference_date.
    """
    return [reference_date + timedelta(days=i) for i in range(1, horizon_days + 1)]


# ==============================================================================
# 2. Forecast Lifecycle & Persistence
# ==============================================================================

def archive_previous_forecasts(db: Session, product_id: int) -> int:
    """
    Marks all currently active GENERATED forecasts for a product as ARCHIVED.
    Historical forecast records are preserved and never deleted.
    """
    now = datetime.now(timezone.utc)
    active_forecasts = (
        db.query(DemandForecast)
        .filter(
            DemandForecast.product_id == product_id,
            DemandForecast.status == ForecastStatus.GENERATED.value,
        )
        .all()
    )
    for f in active_forecasts:
        f.status = ForecastStatus.ARCHIVED.value
        f.updated_at = now
    return len(active_forecasts)


def generate_product_forecast(
    db: Session,
    product_id: int,
    method: ForecastMethod = ForecastMethod.SMA,
    history_days: Optional[int] = None,
    horizon_days: Optional[int] = None,
    wma_window: Optional[int] = None,
    reference_date: Optional[date] = None,
) -> DemandForecast:
    """
    Generates and persists a deterministic forecast for a single active product.
    Archives previous active forecasts for the product without deleting history.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    if not product.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product '{product.name}' is inactive. Forecasts can only be generated for active products.",
        )

    # Resolve configuration parameters
    h_days = history_days if history_days is not None else settings.DEMAND_FORECAST_HISTORY_DAYS
    hor_days = horizon_days if horizon_days is not None else settings.DEMAND_FORECAST_HORIZON_DAYS
    w_window = wma_window if wma_window is not None else settings.DEMAND_FORECAST_WMA_WINDOW

    if h_days <= 0 or hor_days <= 0 or w_window <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="history_days, horizon_days, and wma_window must all be greater than 0",
        )

    if w_window > h_days:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="wma_window cannot be greater than history_days",
        )

    ref_date = reference_date or datetime.now(timezone.utc).date()

    # Retrieve continuous daily sales history
    history = get_daily_sales_history(db, product_id, h_days, ref_date)
    daily_demand_values = [qty for _, qty in history]

    # Calculate daily forecast rate using selected deterministic method
    if method == ForecastMethod.SMA:
        daily_rate = calculate_sma(daily_demand_values, h_days)
    elif method == ForecastMethod.WMA:
        daily_rate = calculate_wma(daily_demand_values, w_window)
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported forecast method: {method}",
        )

    # Archive previous GENERATED forecasts for this product
    archive_previous_forecasts(db, product_id)

    # Create new DemandForecast run
    now = datetime.now(timezone.utc)
    forecast = DemandForecast(
        product_id=product_id,
        forecast_method=method.value if isinstance(method, ForecastMethod) else str(method),
        history_days=h_days,
        forecast_horizon_days=hor_days,
        generated_at=now,
        model_version="v1",
        status=ForecastStatus.GENERATED.value,
        created_at=now,
        updated_at=now,
    )
    db.add(forecast)
    db.flush()

    # Generate daily future forecast values (Numeric 12, 4 precision)
    future_dates = generate_forecast_dates(ref_date, hor_days)
    rounded_qty = round(daily_rate, 4)
    for f_date in future_dates:
        val = DemandForecastValue(
            forecast_id=forecast.id,
            forecast_date=f_date,
            forecast_quantity=rounded_qty,
            created_at=now,
        )
        db.add(val)

    product = db.get(Product, product_id)
    if product:
        from app.services.notification_service import create_forecast_generated_notification
        create_forecast_generated_notification(db, forecast, product)

    db.commit()
    db.refresh(forecast)
    return forecast


def generate_all_forecasts(
    db: Session,
    method: ForecastMethod = ForecastMethod.SMA,
    history_days: Optional[int] = None,
    horizon_days: Optional[int] = None,
    wma_window: Optional[int] = None,
    reference_date: Optional[date] = None,
) -> List[DemandForecast]:
    """
    Generates deterministic demand forecasts for all active products in the system.
    Inactive products are automatically skipped.
    """
    active_products = (
        db.query(Product)
        .filter(Product.is_active.is_(True))
        .order_by(Product.id.asc())
        .all()
    )

    results: List[DemandForecast] = []
    for product in active_products:
        fc = generate_product_forecast(
            db=db,
            product_id=product.id,
            method=method,
            history_days=history_days,
            horizon_days=horizon_days,
            wma_window=wma_window,
            reference_date=reference_date,
        )
        results.append(fc)

    return results


# ==============================================================================
# 3. Query & Retrieval
# ==============================================================================

def get_forecast(db: Session, forecast_id: int) -> DemandForecast:
    """
    Retrieves a DemandForecast by ID with eager loading of values and product.
    Raises 404 if not found.
    """
    forecast = (
        db.query(DemandForecast)
        .options(
            joinedload(DemandForecast.values),
            joinedload(DemandForecast.product),
        )
        .filter(DemandForecast.id == forecast_id)
        .first()
    )
    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Demand forecast with ID {forecast_id} not found",
        )
    return forecast


def get_product_latest_forecast(db: Session, product_id: int) -> DemandForecast:
    """
    Retrieves the latest forecast for a product (preferring GENERATED, or most recent).
    Raises 404 if no forecast exists.
    """
    product = db.query(Product).filter(Product.id == product_id).first()
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    forecast = (
        db.query(DemandForecast)
        .options(
            joinedload(DemandForecast.values),
            joinedload(DemandForecast.product),
        )
        .filter(
            DemandForecast.product_id == product_id,
            DemandForecast.status == ForecastStatus.GENERATED.value,
        )
        .order_by(DemandForecast.generated_at.desc())
        .first()
    )

    if not forecast:
        # Fall back to any latest forecast (e.g. ARCHIVED)
        forecast = (
            db.query(DemandForecast)
            .options(
                joinedload(DemandForecast.values),
                joinedload(DemandForecast.product),
            )
            .filter(DemandForecast.product_id == product_id)
            .order_by(DemandForecast.generated_at.desc())
            .first()
        )

    if not forecast:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No demand forecast found for product ID {product_id}",
        )

    return forecast


def get_forecasts(
    db: Session,
    product_id: Optional[int] = None,
    method: Optional[ForecastMethod] = None,
    status_filter: Optional[ForecastStatus] = None,
    generated_from: Optional[datetime] = None,
    generated_to: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
) -> List[DemandForecast]:
    """
    Retrieves a list of demand forecasts matching query filters, ordered by generated_at desc.
    """
    query = (
        db.query(DemandForecast)
        .options(
            joinedload(DemandForecast.values),
            joinedload(DemandForecast.product),
        )
    )

    if product_id is not None:
        query = query.filter(DemandForecast.product_id == product_id)

    if method is not None:
        m_val = method.value if isinstance(method, ForecastMethod) else str(method)
        query = query.filter(DemandForecast.forecast_method == m_val)

    if status_filter is not None:
        s_val = status_filter.value if isinstance(status_filter, ForecastStatus) else str(status_filter)
        query = query.filter(DemandForecast.status == s_val)

    if generated_from is not None:
        query = query.filter(DemandForecast.generated_at >= generated_from)

    if generated_to is not None:
        query = query.filter(DemandForecast.generated_at <= generated_to)

    return (
        query
        .order_by(DemandForecast.generated_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )
