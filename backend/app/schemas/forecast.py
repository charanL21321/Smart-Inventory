from datetime import date, datetime
from typing import Any, List, Optional

from pydantic import BaseModel, ConfigDict, field_validator, model_validator

from app.models.demand_forecast import ForecastMethod, ForecastStatus


class ForecastGenerateRequest(BaseModel):
    """
    Request schema for triggering forecast generation.
    """
    method: ForecastMethod = ForecastMethod.SMA


class DemandForecastValueResponse(BaseModel):
    """
    Schema representing an individual day's forecast value in the horizon.
    """
    id: int
    forecast_id: int
    forecast_date: date
    forecast_quantity: float
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("forecast_quantity", mode="before")
    @classmethod
    def parse_forecast_quantity(cls, value: Any) -> float:
        if value is None:
            return 0.0
        return round(float(value), 4)


class DemandForecastResponse(BaseModel):
    """
    Summary schema for a demand forecast run.
    """
    id: int
    product_id: int
    product_name: Optional[str] = None
    forecast_method: ForecastMethod
    history_days: int
    forecast_horizon_days: int
    model_version: str
    status: ForecastStatus
    generated_at: datetime
    total_forecast_quantity: float
    average_daily_forecast: float
    explanation: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True, extra="ignore")

    @model_validator(mode="before")
    @classmethod
    def populate_computed_fields(cls, data: Any) -> Any:
        if isinstance(data, dict):
            return data

        prod_name = None
        if hasattr(data, "product") and data.product is not None:
            prod_name = getattr(data.product, "name", None)

        vals = getattr(data, "values", []) or []
        total_qty = round(sum(float(v.forecast_quantity) for v in vals), 4)
        horizon = getattr(data, "forecast_horizon_days", 1) or 1
        avg_daily = round(total_qty / horizon, 4) if horizon > 0 else 0.0

        method_str = getattr(data, "forecast_method", "SMA")
        if isinstance(method_str, ForecastMethod):
            method_str = method_str.value

        hist_days = getattr(data, "history_days", 30)
        if method_str == "WMA":
            expl = f"7-day weighted moving-average forecast based on historical daily sales over {horizon}-day horizon."
        else:
            expl = f"{hist_days}-day simple moving-average forecast based on historical daily sales over {horizon}-day horizon."

        return {
            "id": data.id,
            "product_id": data.product_id,
            "product_name": prod_name,
            "forecast_method": data.forecast_method,
            "history_days": data.history_days,
            "forecast_horizon_days": data.forecast_horizon_days,
            "model_version": data.model_version,
            "status": data.status,
            "generated_at": data.generated_at,
            "total_forecast_quantity": total_qty,
            "average_daily_forecast": avg_daily,
            "explanation": expl,
            "created_at": data.created_at,
            "updated_at": data.updated_at,
            "values": vals,
        }


class DemandForecastDetailResponse(DemandForecastResponse):
    """
    Detailed forecast response including individual future daily values.
    """
    values: List[DemandForecastValueResponse] = []
