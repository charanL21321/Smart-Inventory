from typing import Optional

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.security import create_access_token, hash_password, verify_password
from app.models.user import User, UserRole
from app.schemas.user import LoginRequest, Token, UserCreate


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Retrieves a user by username."""
    stmt = select(User).where(User.username == username)
    return db.scalars(stmt).first()


def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Retrieves a user by normalized email."""
    stmt = select(User).where(User.email == email.strip().lower())
    return db.scalars(stmt).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Retrieves a user by primary key ID."""
    stmt = select(User).where(User.id == user_id)
    return db.scalars(stmt).first()


def register_user(db: Session, user_in: UserCreate) -> User:
    """
    Registers a new user after verifying username and email uniqueness.
    Hashes the password securely and stores the user.
    """
    # Verify username uniqueness
    if get_user_by_username(db, user_in.username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username is already registered",
        )

    # Normalize email and verify uniqueness
    normalized_email = user_in.email.strip().lower()
    if get_user_by_email(db, normalized_email):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email is already registered",
        )

    # Hash the password
    hashed_pwd = hash_password(user_in.password)

    # Instantiate user
    user = User(
        username=user_in.username,
        email=normalized_email,
        hashed_password=hashed_pwd,
        full_name=user_in.full_name,
        role=user_in.role or UserRole.WAREHOUSE_STAFF,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def authenticate_user(db: Session, login_data: LoginRequest) -> User:
    """
    Authenticates a user via username or email and password.
    Returns the User object upon success.
    Raises HTTPException 401 on invalid credentials, or 400 if user is inactive.
    """
    identifier = login_data.username.strip()

    # Search by username or email
    stmt = select(User).where(
        (User.username == identifier) | (User.email == identifier.lower())
    )
    user = db.scalars(stmt).first()

    # Verify user exists and password matches
    if not user or not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check active status
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    return user


def generate_user_token(user: User) -> Token:
    """
    Generates a JWT access token for an authenticated user.
    """
    token_payload = {
        "sub": str(user.id),
        "username": user.username,
        "role": user.role.value,
    }
    access_token = create_access_token(data=token_payload)
    return Token(access_token=access_token, token_type="bearer")
