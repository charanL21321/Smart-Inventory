from datetime import datetime
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database.connection import get_db
from app.models.demand_forecast import ForecastMethod, ForecastStatus
from app.models.user import User, UserRole
from app.schemas.forecast import (
    DemandForecastDetailResponse,
    DemandForecastResponse,
    ForecastGenerateRequest,
)
from app.services.forecast_service import (
    generate_all_forecasts,
    generate_product_forecast,
    get_forecast,
    get_forecasts,
    get_product_latest_forecast,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=List[DemandForecastResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate demand forecasts for all active products",
    description="Calculates deterministic time-series forecasts (SMA or WMA) across all active products and stores projected future daily values.",
)
def generate_all_forecasts_route(
    method: ForecastMethod = Query(ForecastMethod.SMA, description="Forecasting method: SMA or WMA"),
    payload: Optional[ForecastGenerateRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> List[DemandForecastResponse]:
    """
    Triggers forecast generation for all active products.
    Requires ADMIN or INVENTORY_MANAGER role.
    """
    selected_method = payload.method if payload is not None else method
    forecasts = generate_all_forecasts(db=db, method=selected_method)
    return [DemandForecastResponse.model_validate(f) for f in forecasts]


@router.post(
    "/generate/{product_id}",
    response_model=DemandForecastDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate demand forecast for a single product",
    description="Calculates a deterministic forecast (SMA or WMA) for a specific active product and stores future daily values.",
)
def generate_single_forecast_route(
    product_id: int,
    method: ForecastMethod = Query(ForecastMethod.SMA, description="Forecasting method: SMA or WMA"),
    payload: Optional[ForecastGenerateRequest] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> DemandForecastDetailResponse:
    """
    Triggers forecast generation for a single active product.
    Requires ADMIN or INVENTORY_MANAGER role.
    """
    selected_method = payload.method if payload is not None else method
    forecast = generate_product_forecast(db=db, product_id=product_id, method=selected_method)
    return DemandForecastDetailResponse.model_validate(forecast)


@router.get(
    "",
    response_model=List[DemandForecastResponse],
    status_code=status.HTTP_200_OK,
    summary="List demand forecasts",
    description="Retrieves a list of generated and archived demand forecasts with optional filters, ordered by generated_at descending.",
)
def list_forecasts_route(
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    method: Optional[ForecastMethod] = Query(None, description="Filter by forecast method"),
    status_filter: Optional[ForecastStatus] = Query(None, alias="status", description="Filter by status"),
    generated_from: Optional[datetime] = Query(None, description="Filter by generation start datetime"),
    generated_to: Optional[datetime] = Query(None, description="Filter by generation end datetime"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(100, ge=1, le=500, description="Page size limit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> List[DemandForecastResponse]:
    """
    Lists forecasts with optional filtering.
    Accessible to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    """
    forecasts = get_forecasts(
        db=db,
        product_id=product_id,
        method=method,
        status_filter=status_filter,
        generated_from=generated_from,
        generated_to=generated_to,
        skip=skip,
        limit=limit,
    )
    return [DemandForecastResponse.model_validate(f) for f in forecasts]


@router.get(
    "/products/{product_id}",
    response_model=DemandForecastDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get latest forecast for product",
    description="Retrieves the latest generated demand forecast with daily projection values for a specific product.",
)
def get_product_forecast_route(
    product_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> DemandForecastDetailResponse:
    """
    Retrieves the latest forecast for a product.
    Accessible to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    """
    forecast = get_product_latest_forecast(db=db, product_id=product_id)
    return DemandForecastDetailResponse.model_validate(forecast)


@router.get(
    "/{forecast_id}",
    response_model=DemandForecastDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single demand forecast details",
    description="Retrieves complete details of a specific demand forecast run by ID, including daily forecasted quantities.",
)
def get_forecast_detail_route(
    forecast_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> DemandForecastDetailResponse:
    """
    Retrieves forecast by ID.
    Accessible to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    """
    forecast = get_forecast(db=db, forecast_id=forecast_id)
    return DemandForecastDetailResponse.model_validate(forecast)
