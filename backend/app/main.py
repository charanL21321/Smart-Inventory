import logging
from contextlib import asynccontextmanager
from typing import Dict

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    auth,
    categories,
    forecast,
    inventory,
    notifications,
    products,
    purchase_orders,
    replenishment,
    sales,
    suppliers,
    users,
)
from app.core.config import settings
from app.database.connection import check_db_connection

# Configure application logging
logging.basicConfig(
    level=logging.DEBUG if settings.DEBUG else logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager managing startup and shutdown routines.
    Optionally verifies database connectivity on startup if CHECK_DB_ON_STARTUP is enabled.
    """
    logger.info("Starting %s v%s...", settings.APP_NAME, settings.APP_VERSION)
    if settings.CHECK_DB_ON_STARTUP:
        logger.info("Verifying database connectivity on startup...")
        check_db_connection()
    yield
    logger.info("Shutting down %s...", settings.APP_NAME)


# Initialize FastAPI application
app = FastAPI(
    title=settings.APP_NAME,
    description="Scalable API backend for inventory tracking, demand forecasting, and automated stock replenishment.",
    version=settings.APP_VERSION,
    lifespan=lifespan,
    swagger_ui_parameters={"persistAuthorization": True},
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
        "http://localhost:3000",
        "http://127.0.0.1:3000",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Routers
app.include_router(auth.router, prefix="/auth", tags=["Authentication"])
app.include_router(users.router, prefix="/users", tags=["Users"])
app.include_router(categories.router, prefix="/categories", tags=["Categories"])
app.include_router(suppliers.router, prefix="/suppliers", tags=["Suppliers"])
app.include_router(products.router, prefix="/products", tags=["Products"])
app.include_router(inventory.router, prefix="/inventory", tags=["Inventory"])
app.include_router(sales.router, prefix="/sales", tags=["Sales"])
app.include_router(purchase_orders.router, prefix="/purchase-orders", tags=["Purchase Orders"])
app.include_router(replenishment.router, prefix="/replenishment", tags=["Replenishment"])
app.include_router(forecast.router, prefix="/forecast", tags=["Demand Forecasting"])
app.include_router(notifications.router, prefix="/notifications", tags=["Notifications"])



@app.get("/", tags=["System"])
def read_root() -> Dict[str, str]:
    """
    Root endpoint confirming API service status.
    """
    return {
        "message": "Smart Inventory & Stock Replenishment Platform API",
        "status": "running",
    }


@app.get("/health", tags=["System"])
def health_check() -> Dict[str, str]:
    """
    Basic health check endpoint returning operational status.
    """
    return {
        "status": "healthy",
    }
