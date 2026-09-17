from datetime import datetime, timedelta, timezone
import math
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.models.inventory import Inventory
from app.models.product import Product
from app.models.replenishment_recommendation import (
    RecommendationPriority,
    RecommendationStatus,
    ReplenishmentRecommendation,
)
from app.models.sale import Sale
from app.models.supplier import Supplier


# ------------------------------------------------------------------------------
# 1. Deterministic Calculation Helpers
# ------------------------------------------------------------------------------
def calculate_inventory_position(current_stock: int, reserved_stock: int) -> int:
    """
    Calculates dynamic inventory position: max(0, current_stock - reserved_stock).
    Ensures position never drops below zero.
    """
    return max(0, current_stock - reserved_stock)


def calculate_average_daily_demand(
    db: Session,
    product_id: int,
    window_days: int = 30,
) -> float:
    """
    Calculates historical average daily demand from completed sales records
    over the configured calendar day window (default: 30 days).
    Returns 0.0 if no historical sales occurred.
    """
    if window_days <= 0:
        window_days = 30

    window_start = datetime.now(timezone.utc) - timedelta(days=window_days)
    stmt = (
        select(func.coalesce(func.sum(Sale.quantity), 0))
        .where(Sale.product_id == product_id)
        .where(Sale.created_at >= window_start)
    )
    total_units_sold = db.scalar(stmt) or 0
    if total_units_sold == 0:
        return 0.0

    return round(float(total_units_sold) / float(window_days), 4)


def calculate_lead_time_demand(average_daily_demand: float, lead_time_days: int) -> float:
    """
    Calculates expected demand incurred during supplier replenishment lead time.
    Formula: average_daily_demand * lead_time_days
    """
    if lead_time_days <= 0 or average_daily_demand <= 0.0:
        return 0.0
    return round(average_daily_demand * float(lead_time_days), 4)


def calculate_base_target(
    target_stock: int,
    lead_time_demand: float,
    safety_stock: int,
) -> float:
    """
    Calculates the base replenishment target level.
    Formula: max(target_stock, lead_time_demand + safety_stock)
    """
    return max(float(target_stock), float(lead_time_demand + safety_stock))


def calculate_recommended_quantity(
    base_target: float,
    inventory_position: int,
    minimum_order_quantity: int,
) -> Tuple[int, bool]:
    """
    Calculates the recommended order quantity and applies supplier MOQ constraints.
    Returns: (recommended_quantity: int, moq_applied: bool)
    """
    raw_qty = base_target - float(inventory_position)
    if raw_qty <= 0:
        return 0, False

    qty = int(math.ceil(raw_qty))
    moq_applied = False
    if minimum_order_quantity > 0 and qty < minimum_order_quantity:
        qty = minimum_order_quantity
        moq_applied = True

    return qty, moq_applied


def calculate_priority(
    inventory_position: int,
    safety_stock: int,
    reorder_point: int,
) -> RecommendationPriority:
    """
    Calculates deterministic operational replenishment priority:
    - HIGH: inventory_position == 0 or inventory_position < safety_stock
    - MEDIUM: inventory_position <= reorder_point
    - LOW: inventory_position > reorder_point
    """
    if inventory_position == 0 or inventory_position < safety_stock:
        return RecommendationPriority.HIGH
    elif inventory_position <= reorder_point:
        return RecommendationPriority.MEDIUM
    else:
        return RecommendationPriority.LOW


def build_replenishment_reason(
    inventory_position: int,
    reorder_point: int,
    safety_stock: int,
    target_stock: int,
    lead_time_demand: float,
    moq_applied: bool,
    moq: int,
) -> str:
    """
    Generates an explainable, fact-based description of why replenishment is recommended.
    """
    reasons: List[str] = []

    if inventory_position == 0:
        reasons.append("Stock is completely depleted (0 available).")
    elif inventory_position < safety_stock:
        reasons.append(
            f"Inventory position ({inventory_position}) has breached safety stock threshold ({safety_stock})."
        )
    else:
        reasons.append(
            f"Inventory position ({inventory_position}) is at or below reorder point ({reorder_point})."
        )

    if lead_time_demand > 0:
        reasons.append(f"Estimated demand during supplier lead time is {lead_time_demand:.1f} units.")

    reasons.append(f"Replenishment restores stock to target level of {target_stock} units.")

    if moq_applied:
        reasons.append(f"Order quantity adjusted up to meet supplier minimum order quantity of {moq} units.")

    return " ".join(reasons)


# ------------------------------------------------------------------------------
# 2. Product Evaluation & Recommendation Generation
# ------------------------------------------------------------------------------
def evaluate_product_replenishment(
    db: Session,
    product: Product,
    window_days: int = 30,
) -> Optional[dict]:
    """
    Evaluates an active product against its inventory, sales velocity, and supplier settings.
    Returns recommendation parameters dictionary if replenishment is required, or None if healthy.
    """
    # Verify product and supplier active status
    if not product.is_active or not product.supplier or not product.supplier.is_active:
        return None

    # Retrieve current inventory state without modifying or initializing inventory
    inv_stmt = select(Inventory).where(Inventory.product_id == product.id)
    inv = db.scalars(inv_stmt).first()

    current_stock = inv.current_stock if inv else 0
    reserved_stock = inv.reserved_stock if inv else 0
    inv_pos = calculate_inventory_position(current_stock, reserved_stock)

    # Replenishment Trigger: inventory_position <= reorder_point
    if inv_pos > product.reorder_point:
        return None

    # Calculate demand metrics
    avg_daily_demand = calculate_average_daily_demand(db, product.id, window_days=window_days)
    lead_time_days = product.supplier.lead_time_days
    lead_time_demand = calculate_lead_time_demand(avg_daily_demand, lead_time_days)

    # Calculate target and recommended order quantities
    base_target = calculate_base_target(product.target_stock, lead_time_demand, product.safety_stock)
    moq = product.supplier.minimum_order_quantity
    rec_qty, moq_applied = calculate_recommended_quantity(base_target, inv_pos, moq)

    # Determine operational priority
    priority = calculate_priority(inv_pos, product.safety_stock, product.reorder_point)

    # Construct explainable reason
    reason = build_replenishment_reason(
        inventory_position=inv_pos,
        reorder_point=product.reorder_point,
        safety_stock=product.safety_stock,
        target_stock=product.target_stock,
        lead_time_demand=lead_time_demand,
        moq_applied=moq_applied,
        moq=moq,
    )

    return {
        "product_id": product.id,
        "supplier_id": product.supplier_id,
        "current_stock": current_stock,
        "reserved_stock": reserved_stock,
        "inventory_position": inv_pos,
        "reorder_point": product.reorder_point,
        "safety_stock": product.safety_stock,
        "target_stock": product.target_stock,
        "average_daily_demand": avg_daily_demand,
        "lead_time_days": lead_time_days,
        "lead_time_demand": lead_time_demand,
        "recommended_quantity": rec_qty,
        "minimum_order_quantity": moq,
        "priority": priority,
        "reason": reason,
    }


def generate_recommendations(db: Session) -> List[ReplenishmentRecommendation]:
    """
    Scans all active products and evaluates replenishment requirements.
    Updates existing PENDING recommendations in-place to avoid duplicate clutter.
    Preserves REVIEWED and DISMISSED historical recommendations.
    Does NOT modify inventory or create purchase orders.
    """
    stmt = (
        select(Product)
        .join(Supplier, Product.supplier_id == Supplier.id)
        .where(Product.is_active == True)
        .where(Supplier.is_active == True)
        .order_by(Product.id.asc())
    )
    products = list(db.scalars(stmt).all())

    recommendations: List[ReplenishmentRecommendation] = []
    now_dt = datetime.now(timezone.utc)

    for prod in products:
        eval_data = evaluate_product_replenishment(db, prod)
        if not eval_data:
            continue

        # Check for existing PENDING recommendation for this product
        existing_stmt = (
            select(ReplenishmentRecommendation)
            .where(ReplenishmentRecommendation.product_id == prod.id)
            .where(ReplenishmentRecommendation.status == RecommendationStatus.PENDING)
        )
        existing_rec = db.scalars(existing_stmt).first()

        if existing_rec:
            # Update existing pending recommendation in-place
            existing_rec.current_stock = eval_data["current_stock"]
            existing_rec.reserved_stock = eval_data["reserved_stock"]
            existing_rec.inventory_position = eval_data["inventory_position"]
            existing_rec.reorder_point = eval_data["reorder_point"]
            existing_rec.safety_stock = eval_data["safety_stock"]
            existing_rec.target_stock = eval_data["target_stock"]
            existing_rec.average_daily_demand = eval_data["average_daily_demand"]
            existing_rec.lead_time_days = eval_data["lead_time_days"]
            existing_rec.lead_time_demand = eval_data["lead_time_demand"]
            existing_rec.recommended_quantity = eval_data["recommended_quantity"]
            existing_rec.minimum_order_quantity = eval_data["minimum_order_quantity"]
            existing_rec.priority = eval_data["priority"]
            existing_rec.reason = eval_data["reason"]
            existing_rec.updated_at = now_dt
            recommendations.append(existing_rec)
        else:
            # Create new recommendation
            new_rec = ReplenishmentRecommendation(
                product_id=eval_data["product_id"],
                supplier_id=eval_data["supplier_id"],
                current_stock=eval_data["current_stock"],
                reserved_stock=eval_data["reserved_stock"],
                inventory_position=eval_data["inventory_position"],
                reorder_point=eval_data["reorder_point"],
                safety_stock=eval_data["safety_stock"],
                target_stock=eval_data["target_stock"],
                average_daily_demand=eval_data["average_daily_demand"],
                lead_time_days=eval_data["lead_time_days"],
                lead_time_demand=eval_data["lead_time_demand"],
                recommended_quantity=eval_data["recommended_quantity"],
                minimum_order_quantity=eval_data["minimum_order_quantity"],
                priority=eval_data["priority"],
                reason=eval_data["reason"],
                status=RecommendationStatus.PENDING,
                generated_at=now_dt,
                updated_at=now_dt,
            )
            db.add(new_rec)
            recommendations.append(new_rec)

    try:
        db.commit()
        for rec in recommendations:
            db.refresh(rec)
        return recommendations
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate replenishment recommendations: {exc}",
        ) from exc


# ------------------------------------------------------------------------------
# 3. Query & Status Management
# ------------------------------------------------------------------------------
def get_recommendation_by_id(db: Session, rec_id: int) -> ReplenishmentRecommendation:
    """
    Retrieves a single replenishment recommendation by ID.
    """
    rec = db.get(ReplenishmentRecommendation, rec_id)
    if not rec:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Replenishment recommendation with ID {rec_id} not found",
        )
    return rec


def get_recommendations(
    db: Session,
    status: Optional[RecommendationStatus] = None,
    priority: Optional[RecommendationPriority] = None,
    product_id: Optional[int] = None,
    supplier_id: Optional[int] = None,
) -> List[ReplenishmentRecommendation]:
    """
    Queries replenishment recommendations with optional filters.
    Default ordering: HIGH priority first, then MEDIUM, then LOW; within priority sorted by oldest generated_at first.
    """
    stmt = select(ReplenishmentRecommendation)

    if status is not None:
        stmt = stmt.where(ReplenishmentRecommendation.status == status)

    if priority is not None:
        stmt = stmt.where(ReplenishmentRecommendation.priority == priority)

    if product_id is not None:
        stmt = stmt.where(ReplenishmentRecommendation.product_id == product_id)

    if supplier_id is not None:
        stmt = stmt.where(ReplenishmentRecommendation.supplier_id == supplier_id)

    # Priority sorting expression
    priority_order = case(
        (ReplenishmentRecommendation.priority == RecommendationPriority.HIGH, 1),
        (ReplenishmentRecommendation.priority == RecommendationPriority.MEDIUM, 2),
        (ReplenishmentRecommendation.priority == RecommendationPriority.LOW, 3),
        else_=4,
    )

    stmt = stmt.order_by(priority_order.asc(), ReplenishmentRecommendation.generated_at.asc())
    return list(db.scalars(stmt).all())


def review_recommendation(db: Session, rec_id: int) -> ReplenishmentRecommendation:
    """
    Transitions a recommendation from PENDING to REVIEWED.
    """
    rec = get_recommendation_by_id(db, rec_id)

    if rec.status != RecommendationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot review recommendation with status '{rec.status.value}'. Only PENDING recommendations can be reviewed.",
        )

    rec.status = RecommendationStatus.REVIEWED
    rec.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(rec)
        return rec
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to review recommendation: {exc}",
        ) from exc


def dismiss_recommendation(
    db: Session,
    rec_id: int,
    reason: str,
) -> ReplenishmentRecommendation:
    """
    Transitions a recommendation from PENDING to DISMISSED.
    Requires a mandatory non-empty dismissal reason.
    """
    cleaned_reason = reason.strip() if reason else ""
    if not cleaned_reason:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dismissal reason is mandatory",
        )

    rec = get_recommendation_by_id(db, rec_id)

    if rec.status != RecommendationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot dismiss recommendation with status '{rec.status.value}'. Only PENDING recommendations can be dismissed.",
        )

    rec.status = RecommendationStatus.DISMISSED
    rec.dismissal_reason = cleaned_reason
    rec.updated_at = datetime.now(timezone.utc)

    try:
        db.commit()
        db.refresh(rec)
        return rec
    except Exception as exc:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to dismiss recommendation: {exc}",
        ) from exc
