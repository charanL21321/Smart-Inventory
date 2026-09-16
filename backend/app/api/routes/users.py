from typing import Any, Dict

from fastapi import APIRouter, Depends, status

from app.api.deps import get_current_user, require_roles
from app.models.user import User, UserRole
from app.schemas.user import UserResponse

router = APIRouter()


@router.get(
    "/me",
    response_model=UserResponse,
    status_code=status.HTTP_200_OK,
    summary="Get current user profile",
    description="Retrieves the profile information of the currently authenticated user.",
)
def read_current_user(
    current_user: User = Depends(get_current_user),
) -> UserResponse:
    """
    Returns the authenticated user's profile details.
    Requires a valid JWT Bearer token.
    """
    return current_user


@router.get(
    "/admin-test",
    response_model=Dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Administrator access verification test",
    description="Protected endpoint accessible only by users with ADMIN role.",
)
def admin_only_test(
    current_user: User = Depends(require_roles(UserRole.ADMIN)),
) -> Dict[str, Any]:
    """
    Test endpoint verifying role-based access control.
    Accessible exclusively to users with the ADMIN role.
    """
    return {
        "message": "Admin authorization verified successfully.",
        "admin_user": current_user.username,
        "role": current_user.role.value,
    }
