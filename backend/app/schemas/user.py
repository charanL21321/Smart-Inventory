from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field

from app.models.user import UserRole


class UserBase(BaseModel):
    """Base user fields shared across schemas."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="Unique email address")
    full_name: Optional[str] = Field(None, max_length=100, description="Full name of user")


class UserCreate(UserBase):
    """Schema for user registration."""
    password: str = Field(..., min_length=6, max_length=128, description="Plain-text password")
    role: Optional[UserRole] = Field(
        default=UserRole.WAREHOUSE_STAFF,
        description="Assigned user role (defaults to WAREHOUSE_STAFF)",
    )


class UserResponse(BaseModel):
    """Schema for returning public user information (never exposes password hashes)."""
    id: int
    username: str
    email: str
    full_name: Optional[str]
    role: UserRole
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class LoginRequest(BaseModel):
    """Schema for user authentication credentials."""
    username: str = Field(..., description="Username or email address")
    password: str = Field(..., min_length=1, description="Password")


class Token(BaseModel):
    """Schema for JWT access token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema representing extracted token payload data."""
    user_id: Optional[int] = None
    username: Optional[str] = None
    role: Optional[UserRole] = None
