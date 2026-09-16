"""API route endpoints package."""

from app.api.routes import auth, categories, inventory, products, suppliers, users

__all__ = [
    "auth",
    "users",
    "categories",
    "suppliers",
    "products",
    "inventory",
]
