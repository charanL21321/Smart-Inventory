from typing import List, Optional

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.product import Product
from app.models.supplier import Supplier
from app.schemas.product import ProductCreate, ProductUpdate
from app.services.category_service import get_category_by_id
from app.services.supplier_service import get_supplier_by_id


def get_product_by_id(db: Session, product_id: int) -> Optional[Product]:
    """Retrieves a single Product by primary key ID."""
    stmt = select(Product).where(Product.id == product_id)
    return db.scalars(stmt).first()


def get_product_by_sku(db: Session, sku: str) -> Optional[Product]:
    """Retrieves a Product by SKU (case-insensitive)."""
    stmt = select(Product).where(func.lower(Product.sku) == sku.strip().lower())
    return db.scalars(stmt).first()


def get_products(
    db: Session,
    category_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
    is_active: Optional[bool] = None,
    search: Optional[str] = None,
    sku: Optional[str] = None,
) -> List[Product]:
    """
    Returns products with flexible, database-efficient filtering.
    """
    stmt = select(Product)

    if category_id is not None:
        stmt = stmt.where(Product.category_id == category_id)

    if supplier_id is not None:
        stmt = stmt.where(Product.supplier_id == supplier_id)

    if is_active is not None:
        stmt = stmt.where(Product.is_active == is_active)

    if sku:
        cleaned_sku = sku.strip()
        stmt = stmt.where(func.lower(Product.sku).contains(cleaned_sku.lower()))

    if search:
        cleaned_search = search.strip()
        stmt = stmt.where(func.lower(Product.name).contains(cleaned_search.lower()))

    stmt = stmt.order_by(Product.name.asc())
    return list(db.scalars(stmt).all())


def create_product(db: Session, product_in: ProductCreate) -> Product:
    """
    Creates a new Product after validating category, supplier, SKU uniqueness, and thresholds.
    """
    # 1. Verify category exists
    category = get_category_by_id(db, product_in.category_id)
    if not category:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category with ID {product_in.category_id} does not exist",
        )

    # 2. Verify supplier exists
    supplier = get_supplier_by_id(db, product_in.supplier_id)
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier with ID {product_in.supplier_id} does not exist",
        )

    # 3. Verify category is active
    if not category.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Category '{category.name}' is inactive and cannot accept new products",
        )

    # 4. Verify supplier is active
    if not supplier.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Supplier '{supplier.name}' is inactive and cannot supply new products",
        )

    # 5. Check SKU uniqueness
    cleaned_sku = product_in.sku.strip()
    if not cleaned_sku:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product SKU cannot be empty",
        )

    if get_product_by_sku(db, cleaned_sku):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Product with SKU '{cleaned_sku}' already exists",
        )

    # 6. Validate numerical thresholds
    if product_in.price < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product price must be greater than or equal to 0",
        )

    if product_in.reorder_point < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reorder point must be greater than or equal to 0",
        )

    if product_in.safety_stock < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Safety stock must be greater than or equal to 0",
        )

    if product_in.target_stock <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Target stock must be greater than 0",
        )

    cleaned_name = product_in.name.strip()
    if not cleaned_name:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product name cannot be empty",
        )

    product = Product(
        name=cleaned_name,
        sku=cleaned_sku,
        description=product_in.description.strip() if product_in.description else None,
        category_id=product_in.category_id,
        supplier_id=product_in.supplier_id,
        price=product_in.price,
        reorder_point=product_in.reorder_point,
        safety_stock=product_in.safety_stock,
        target_stock=product_in.target_stock,
        is_active=True,
    )
    db.add(product)
    db.commit()
    db.refresh(product)
    return product


def update_product(db: Session, product_id: int, product_in: ProductUpdate) -> Product:
    """
    Updates an existing product item, validating changed relationships and SKU.
    """
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    update_data = product_in.model_dump(exclude_unset=True)

    # Validate category change
    if "category_id" in update_data and update_data["category_id"] is not None:
        cat_id = update_data["category_id"]
        category = get_category_by_id(db, cat_id)
        if not category:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with ID {cat_id} does not exist",
            )
        if not category.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category '{category.name}' is inactive",
            )
        product.category_id = cat_id

    # Validate supplier change
    if "supplier_id" in update_data and update_data["supplier_id"] is not None:
        sup_id = update_data["supplier_id"]
        supplier = get_supplier_by_id(db, sup_id)
        if not supplier:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with ID {sup_id} does not exist",
            )
        if not supplier.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier '{supplier.name}' is inactive",
            )
        product.supplier_id = sup_id

    # Validate SKU change
    if "sku" in update_data and update_data["sku"] is not None:
        cleaned_sku = update_data["sku"].strip()
        if not cleaned_sku:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product SKU cannot be empty",
            )
        existing = get_product_by_sku(db, cleaned_sku)
        if existing and existing.id != product.id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Product with SKU '{cleaned_sku}' already exists",
            )
        product.sku = cleaned_sku

    if "name" in update_data and update_data["name"] is not None:
        cleaned_name = update_data["name"].strip()
        if not cleaned_name:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product name cannot be empty",
            )
        product.name = cleaned_name

    if "description" in update_data:
        product.description = update_data["description"].strip() if update_data["description"] else None

    if "price" in update_data and update_data["price"] is not None:
        if update_data["price"] < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Product price must be greater than or equal to 0",
            )
        product.price = update_data["price"]

    if "reorder_point" in update_data and update_data["reorder_point"] is not None:
        if update_data["reorder_point"] < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Reorder point must be greater than or equal to 0",
            )
        product.reorder_point = update_data["reorder_point"]

    if "safety_stock" in update_data and update_data["safety_stock"] is not None:
        if update_data["safety_stock"] < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Safety stock must be greater than or equal to 0",
            )
        product.safety_stock = update_data["safety_stock"]

    if "target_stock" in update_data and update_data["target_stock"] is not None:
        if update_data["target_stock"] <= 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Target stock must be greater than 0",
            )
        product.target_stock = update_data["target_stock"]

    if "is_active" in update_data and update_data["is_active"] is not None:
        product.is_active = update_data["is_active"]

    db.commit()
    db.refresh(product)
    return product


def delete_product(db: Session, product_id: int) -> Product:
    """
    Soft-deletes / deactivates a product item (is_active = False).
    Preserves audit history and references for inventory transactions.
    """
    product = get_product_by_id(db, product_id)
    if not product:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Product with ID {product_id} not found",
        )

    product.is_active = False
    db.commit()
    db.refresh(product)
    return product
