from pathlib import Path
from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# Base directory for the backend (where .env file typically resides)
BACKEND_DIR = Path(__file__).resolve().parent.parent.parent


class Settings(BaseSettings):
    """
    Application Settings loaded from environment variables or .env file.
    Utilizes Pydantic Settings for strict validation and typing.
    """
    APP_NAME: str = "Smart Inventory & Stock Replenishment Platform"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True
    DATABASE_URL: str = "postgresql+psycopg2://username:password@localhost:5432/smart_inventory"

    # Startup database connectivity verification flag
    CHECK_DB_ON_STARTUP: bool = False

    # JWT Authentication Settings
    JWT_SECRET_KEY: str = "smart-inventory-secret-key-phase2-default-change-in-production"
    JWT_ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    # Phase 7: Demand Forecasting Settings
    DEMAND_FORECAST_HISTORY_DAYS: int = 30
    DEMAND_FORECAST_HORIZON_DAYS: int = 7
    DEMAND_FORECAST_WMA_WINDOW: int = 7

    @model_validator(mode="after")
    def validate_forecast_settings(self) -> "Settings":
        if self.DEMAND_FORECAST_HISTORY_DAYS <= 0:
            raise ValueError("DEMAND_FORECAST_HISTORY_DAYS must be greater than 0")
        if self.DEMAND_FORECAST_HORIZON_DAYS <= 0:
            raise ValueError("DEMAND_FORECAST_HORIZON_DAYS must be greater than 0")
        if self.DEMAND_FORECAST_WMA_WINDOW <= 0:
            raise ValueError("DEMAND_FORECAST_WMA_WINDOW must be greater than 0")
        if self.DEMAND_FORECAST_WMA_WINDOW > self.DEMAND_FORECAST_HISTORY_DAYS:
            raise ValueError("DEMAND_FORECAST_WMA_WINDOW must be less than or equal to DEMAND_FORECAST_HISTORY_DAYS")
        return self

    model_config = SettingsConfigDict(
        env_file=(str(BACKEND_DIR / ".env"), ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        case_sensitive=True,
    )


settings = Settings()
