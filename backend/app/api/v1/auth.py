"""
Authentication API endpoints.
Handles login, token refresh, and user management.
"""
from datetime import timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import (
    Token,
    create_access_token,
    create_refresh_token,
    get_password_hash,
    verify_password,
    verify_token,
    get_current_user,
)
from app.core.config import settings
from app.core.rate_limit import limiter, RateLimits
from app.models.user import User

router = APIRouter()


# Request/Response Models
class LoginRequest(BaseModel):
    """Login request body. Uses a plain string for email to allow simple usernames like 'admin' in local dev."""
    email: str
    password: str


class RegisterRequest(BaseModel):
    """User registration request."""
    email: EmailStr
    password: str
    full_name: str
    role: str = "user"


class RefreshRequest(BaseModel):
    """Token refresh request."""
    refresh_token: str


class UserResponse(BaseModel):
    """User response model."""
    id: int
    email: str
    full_name: str
    role: str
    is_active: bool


class PasswordChangeRequest(BaseModel):
    """Password change request."""
    current_password: str
    new_password: str


# Helper function to get user by email
def get_user_by_email(db: Session, email: str) -> Optional[User]:
    """Get user from database by email."""
    return db.query(User).filter(User.email == email).first()


def get_user_by_id(db: Session, user_id: int) -> Optional[User]:
    """Get user from database by ID."""
    return db.query(User).filter(User.id == user_id).first()


@router.post("/login", response_model=Token)
@limiter.limit(RateLimits.AUTH_LOGIN)
async def login(request: Request, login_data: LoginRequest, db: Session = Depends(get_db)):
    """
    Authenticate user and return JWT tokens.

    - **email**: User's email address
    - **password**: User's password

    Returns access and refresh tokens on successful authentication.
    """
    # Check if user exists in database
    user = get_user_by_email(db, login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Verify password
    if not verify_password(login_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account",
        )

    # Create tokens (sub must be a string per JWT spec)
    token_data = {
        "sub": str(user.id),
        "email": user.email,
        "role": user.role,
    }

    access_token = create_access_token(token_data)
    refresh_token = create_refresh_token(token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.post("/refresh", response_model=Token)
@limiter.limit(RateLimits.AUTH_REFRESH)
async def refresh_token(request: Request, refresh_data: RefreshRequest):
    """
    Refresh access token using refresh token.

    - **refresh_token**: Valid refresh token

    Returns new access and refresh tokens.
    """
    # Verify refresh token
    token_data = verify_token(refresh_data.refresh_token, token_type="refresh")

    # Create new tokens (sub must be a string per JWT spec)
    new_token_data = {
        "sub": str(token_data.user_id),
        "email": token_data.email,
        "role": token_data.role,
    }

    access_token = create_access_token(new_token_data)
    refresh_token = create_refresh_token(new_token_data)

    return Token(
        access_token=access_token,
        refresh_token=refresh_token,
    )


@router.get("/me", response_model=UserResponse)
async def get_current_user_info(
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get current authenticated user's information.

    Requires valid JWT access token in Authorization header.
    """
    # Get full user data from database
    user = get_user_by_id(db, current_user["id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    return UserResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name or "",
        role=user.role,
        is_active=user.is_active,
    )


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
@limiter.limit(RateLimits.AUTH_REGISTER)
async def register_user(request: Request, register_data: RegisterRequest, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **email**: User's email address (must be unique)
    - **password**: User's password (min 8 characters)
    - **full_name**: User's full name
    - **role**: User role (default: "user")

    Note: In production, this endpoint should be admin-only or have email verification.
    """
    # Check if user already exists in database
    existing_user = get_user_by_email(db, register_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Validate password strength
    if len(register_data.password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Password must be at least 8 characters",
        )

    # Create user in database
    new_user = User(
        email=register_data.email,
        full_name=register_data.full_name,
        hashed_password=get_password_hash(register_data.password),
        role=register_data.role,
        is_active=True,
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return UserResponse(
        id=new_user.id,
        email=new_user.email,
        full_name=new_user.full_name or "",
        role=new_user.role,
        is_active=new_user.is_active,
    )


@router.post("/change-password")
async def change_password(
    request: PasswordChangeRequest,
    current_user: dict = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change current user's password.

    - **current_password**: Current password for verification
    - **new_password**: New password (min 8 characters)
    """
    # Get user from database
    user = get_user_by_id(db, current_user["id"])

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found",
        )

    # Verify current password
    if not verify_password(request.current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect",
        )

    # Validate new password
    if len(request.new_password) < 8:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New password must be at least 8 characters",
        )

    # Update password in database
    user.hashed_password = get_password_hash(request.new_password)
    db.commit()

    return {"message": "Password changed successfully"}


@router.post("/logout")
async def logout(current_user: dict = Depends(get_current_user)):
    """
    Logout current user.

    In a production system, this would invalidate the token
    (e.g., add to a blacklist in Redis).
    """
    # In production, you would:
    # 1. Add the token to a blacklist in Redis
    # 2. Clear any server-side session data

    return {"message": "Successfully logged out"}
