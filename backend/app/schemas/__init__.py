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
from app.schemas.product import ProductCreate, ProductResponse, ProductUpdate
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
]
