"""Business logic and service layer package."""

from app.services.auth_service import (
    authenticate_user,
    generate_user_token,
    get_user_by_email,
    get_user_by_id,
    get_user_by_username,
    register_user,
)
from app.services.category_service import (
    create_category,
    delete_category,
    get_categories,
    get_category_by_id,
    get_category_by_name,
    update_category,
)
from app.services.inventory_service import (
    calculate_inventory_status,
    get_inventory_by_product_id,
    get_inventory_list,
    get_or_create_inventory,
    get_transaction_by_id,
    get_transactions,
    perform_stock_adjustment,
    perform_stock_in,
    perform_stock_out,
)
from app.services.product_service import (
    create_product,
    delete_product,
    get_product_by_id,
    get_product_by_sku,
    get_products,
    update_product,
)
from app.services.supplier_service import (
    create_supplier,
    delete_supplier,
    get_supplier_by_id,
    get_suppliers,
    update_supplier,
)

__all__ = [
    # Auth
    "register_user",
    "authenticate_user",
    "generate_user_token",
    "get_user_by_id",
    "get_user_by_username",
    "get_user_by_email",
    # Category
    "get_category_by_id",
    "get_category_by_name",
    "get_categories",
    "create_category",
    "update_category",
    "delete_category",
    # Supplier
    "get_supplier_by_id",
    "get_suppliers",
    "create_supplier",
    "update_supplier",
    "delete_supplier",
    # Product
    "get_product_by_id",
    "get_product_by_sku",
    "get_products",
    "create_product",
    "update_product",
    "delete_product",
    # Inventory
    "calculate_inventory_status",
    "get_or_create_inventory",
    "perform_stock_in",
    "perform_stock_out",
    "perform_stock_adjustment",
    "get_inventory_by_product_id",
    "get_inventory_list",
    "get_transactions",
    "get_transaction_by_id",
]
