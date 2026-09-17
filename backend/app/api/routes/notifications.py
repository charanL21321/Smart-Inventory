from typing import Dict, List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_user
from app.database.connection import get_db
from app.models.notification import NotificationPriority, NotificationType
from app.models.user import User
from app.schemas.notification import NotificationResponse, UnreadCountResponse
from app.services.notification_service import (
    count_unread_notifications,
    get_notification_by_id,
    get_user_notifications,
    mark_all_notifications_read,
    mark_notification_read,
)

router = APIRouter()


@router.get(
    "",
    response_model=List[NotificationResponse],
    status_code=status.HTTP_200_OK,
    summary="List authenticated user notifications",
    description="Retrieves the current authenticated user's notifications, ordered by newest first.",
)
def list_notifications_route(
    is_read: Optional[bool] = Query(None, description="Filter by read/unread status"),
    notification_type: Optional[NotificationType] = Query(None, description="Filter by notification type"),
    priority: Optional[NotificationPriority] = Query(None, description="Filter by priority level"),
    skip: int = Query(0, ge=0, description="Offset for pagination"),
    limit: int = Query(50, ge=1, le=200, description="Page size limit"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> List[NotificationResponse]:
    """
    Returns user-scoped notifications. Strict isolation enforced.
    """
    notifications = get_user_notifications(
        db=db,
        user_id=current_user.id,
        is_read=is_read,
        notification_type=notification_type,
        priority=priority,
        skip=skip,
        limit=limit,
    )
    return [NotificationResponse.model_validate(n) for n in notifications]


@router.get(
    "/unread-count",
    response_model=UnreadCountResponse,
    status_code=status.HTTP_200_OK,
    summary="Get unread notification count",
    description="Returns the total number of unread notifications for the authenticated user.",
)
def get_unread_count_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> UnreadCountResponse:
    """
    Returns count of unread notifications for the active user session.
    """
    count = count_unread_notifications(db=db, user_id=current_user.id)
    return UnreadCountResponse(unread_count=count)


@router.get(
    "/{notification_id}",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Get notification detail",
    description="Retrieves a specific notification if owned by the authenticated user. Returns 404 if not found or unauthorized.",
)
def get_notification_detail_route(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    """
    Enforces strict user ownership of notification records.
    """
    notification = get_notification_by_id(db=db, notification_id=notification_id, user_id=current_user.id)
    return NotificationResponse.model_validate(notification)


@router.patch(
    "/{notification_id}/read",
    response_model=NotificationResponse,
    status_code=status.HTTP_200_OK,
    summary="Mark single notification as read",
    description="Idempotently marks a notification as read and records read_at timestamp. Only the owner can perform this.",
)
def mark_notification_as_read_route(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> NotificationResponse:
    """
    Marks notification as read for the authenticated owner.
    """
    notification = mark_notification_read(db=db, notification_id=notification_id, user_id=current_user.id)
    return NotificationResponse.model_validate(notification)


@router.patch(
    "/read-all",
    response_model=Dict[str, int],
    status_code=status.HTTP_200_OK,
    summary="Mark all user notifications as read",
    description="Idempotently marks all unread notifications of the current user as read.",
)
def mark_all_notifications_read_route(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Dict[str, int]:
    """
    Bulk marks all user's unread notifications as read.
    """
    marked_count = mark_all_notifications_read(db=db, user_id=current_user.id)
    return {"marked_read": marked_count}
