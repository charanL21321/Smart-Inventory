"""Pydantic data schemas package for request validation and response serialization."""

from app.schemas.category import CategoryCreate, CategoryResponse, CategoryUpdate
from app.schemas.inventory import InventoryResponse, InventoryStatus
from app.schemas.inventory_transaction import (
    AdjustmentType,
    InventoryTransactionResponse,
    StockAdjustmentRequest,
    StockInRequest,
    StockOutRequest,
    TransactionType,
)
from app.schemas.forecast import (
    DemandForecastDetailResponse,
    DemandForecastResponse,
    DemandForecastValueResponse,
    ForecastGenerateRequest,
    ForecastMethod,
    ForecastStatus,
)
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
from app.schemas.purchase_order import (
    PurchaseOrderCreate,
    PurchaseOrderItemCreate,
    PurchaseOrderItemResponse,
    PurchaseOrderReceiveItem,
    PurchaseOrderReceiveRequest,
    PurchaseOrderResponse,
    PurchaseOrderStatus,
    PurchaseOrderStatusUpdate,
    PurchaseOrderUpdate,
)
from app.schemas.replenishment import (
    RecommendationPriority,
    RecommendationStatus,
    ReplenishmentDismissRequest,
    ReplenishmentRecommendationResponse,
)
from app.schemas.sale import SaleCreate, SaleResponse
from app.schemas.supplier import SupplierCreate, SupplierResponse, SupplierUpdate
from app.schemas.user import LoginRequest, Token, TokenData, UserCreate, UserResponse, UserRole

__all__ = [
    # User / Auth
    "UserRole",
    "UserCreate",
    "UserResponse",
    "LoginRequest",
    "Token",
    "TokenData",
    # Category
    "CategoryCreate",
    "CategoryUpdate",
    "CategoryResponse",
    # Supplier
    "SupplierCreate",
    "SupplierUpdate",
    "SupplierResponse",
    # Product
    "ProductCreate",
    "ProductUpdate",
    "ProductResponse",
    # Inventory
    "InventoryResponse",
    "InventoryStatus",
    "StockInRequest",
    "StockOutRequest",
    "StockAdjustmentRequest",
    "InventoryTransactionResponse",
    "TransactionType",
    "AdjustmentType",
    # Sales
    "SaleCreate",
    "SaleResponse",
    # Purchase Orders
    "PurchaseOrderStatus",
    "PurchaseOrderItemCreate",
    "PurchaseOrderItemResponse",
    "PurchaseOrderCreate",
    "PurchaseOrderUpdate",
    "PurchaseOrderStatusUpdate",
    "PurchaseOrderReceiveItem",
    "PurchaseOrderReceiveRequest",
    "PurchaseOrderResponse",
    # Replenishment
    "RecommendationStatus",
    "RecommendationPriority",
    "ReplenishmentDismissRequest",
    "ReplenishmentRecommendationResponse",
    # Demand Forecasting
    "ForecastMethod",
    "ForecastStatus",
    "ForecastGenerateRequest",
    "DemandForecastValueResponse",
    "DemandForecastResponse",
    "DemandForecastDetailResponse",
    # Notifications
    "NotificationResponse",
    "UnreadCountResponse",
]
