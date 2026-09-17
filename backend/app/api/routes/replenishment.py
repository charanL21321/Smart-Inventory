from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import require_roles
from app.database.connection import get_db
from app.models.replenishment_recommendation import (
    RecommendationPriority,
    RecommendationStatus,
)
from app.models.user import User, UserRole
from app.schemas.replenishment import (
    ReplenishmentDismissRequest,
    ReplenishmentRecommendationResponse,
)
from app.services.replenishment_service import (
    dismiss_recommendation,
    generate_recommendations,
    get_recommendation_by_id,
    get_recommendations,
    review_recommendation,
)

router = APIRouter()


@router.post(
    "/generate",
    response_model=List[ReplenishmentRecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="Generate replenishment recommendations",
    description="Analyzes inventory position, sales velocity over 30 days, lead-time demand, and supplier MOQ to produce rule-based recommendations.",
)
def generate_recommendations_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> List[ReplenishmentRecommendationResponse]:
    """
    Triggers deterministic replenishment analysis across all active products.
    Requires ADMIN or INVENTORY_MANAGER role.
    """
    recs = generate_recommendations(db=db)
    return [ReplenishmentRecommendationResponse.model_validate(r) for r in recs]


@router.get(
    "/recommendations",
    response_model=List[ReplenishmentRecommendationResponse],
    status_code=status.HTTP_200_OK,
    summary="List replenishment recommendations",
    description="Retrieves replenishment recommendations with optional filters, sorted by priority (HIGH, MEDIUM, LOW) then oldest first.",
)
def list_recommendations_route(
    status_filter: Optional[RecommendationStatus] = Query(None, alias="status", description="Filter by status"),
    priority: Optional[RecommendationPriority] = Query(None, description="Filter by priority"),
    product_id: Optional[int] = Query(None, description="Filter by product ID"),
    supplier_id: Optional[int] = Query(None, description="Filter by supplier ID"),
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> List[ReplenishmentRecommendationResponse]:
    """
    Lists replenishment recommendations.
    Accessible to ADMIN, INVENTORY_MANAGER, and WAREHOUSE_STAFF.
    """
    recs = get_recommendations(
        db=db,
        status=status_filter,
        priority=priority,
        product_id=product_id,
        supplier_id=supplier_id,
    )
    return [ReplenishmentRecommendationResponse.model_validate(r) for r in recs]


@router.get(
    "/recommendations/{recommendation_id}",
    response_model=ReplenishmentRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get single replenishment recommendation",
    description="Retrieves complete details of a specific replenishment recommendation by ID.",
)
def get_recommendation_route(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(
        require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER, UserRole.WAREHOUSE_STAFF)
    ),
) -> ReplenishmentRecommendationResponse:
    """
    Retrieves recommendation by ID.
    """
    rec = get_recommendation_by_id(db=db, rec_id=recommendation_id)
    return ReplenishmentRecommendationResponse.model_validate(rec)


@router.patch(
    "/recommendations/{recommendation_id}/review",
    response_model=ReplenishmentRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Review recommendation",
    description="Marks a PENDING recommendation as REVIEWED by an inventory manager or admin.",
)
def review_recommendation_route(
    recommendation_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> ReplenishmentRecommendationResponse:
    """
    Transitions recommendation from PENDING to REVIEWED.
    Requires ADMIN or INVENTORY_MANAGER role.
    """
    rec = review_recommendation(db=db, rec_id=recommendation_id)
    return ReplenishmentRecommendationResponse.model_validate(rec)


@router.patch(
    "/recommendations/{recommendation_id}/dismiss",
    response_model=ReplenishmentRecommendationResponse,
    status_code=status.HTTP_200_OK,
    summary="Dismiss recommendation",
    description="Dismisses a PENDING recommendation with a mandatory business explanation reason.",
)
def dismiss_recommendation_route(
    recommendation_id: int,
    data: ReplenishmentDismissRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.INVENTORY_MANAGER)),
) -> ReplenishmentRecommendationResponse:
    """
    Transitions recommendation from PENDING to DISMISSED.
    Requires ADMIN or INVENTORY_MANAGER role and a mandatory dismissal reason.
    """
    rec = dismiss_recommendation(db=db, rec_id=recommendation_id, reason=data.reason)
    return ReplenishmentRecommendationResponse.model_validate(rec)
