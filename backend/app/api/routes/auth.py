from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.user import LoginRequest, Token, UserCreate, UserResponse
from app.services.auth_service import authenticate_user, generate_user_token, register_user

router = APIRouter()


@router.post(
    "/register",
    response_model=UserResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a new user",
    description="Registers a new platform user with unique username and email, returning public user profile.",
)
def register(
    user_in: UserCreate,
    db: Session = Depends(get_db),
) -> UserResponse:
    """
    Register a new user account.
    Validates credentials, hashes password, and persists user in the database.
    """
    user = register_user(db, user_in)
    return user


@router.post(
    "/login",
    response_model=Token,
    status_code=status.HTTP_200_OK,
    summary="Authenticate user and obtain JWT token",
    description="Authenticates user credentials (username or email and password) and returns a Bearer access token.",
)
def login(
    login_data: LoginRequest,
    db: Session = Depends(get_db),
) -> Token:
    """
    User login endpoint.
    Verifies credentials and generates a signed JWT access token.
    """
    user = authenticate_user(db, login_data)
    token = generate_user_token(user)
    return token
