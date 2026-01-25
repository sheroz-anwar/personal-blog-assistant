"""
User Management API Router

This module provides REST API endpoints for:
- User registration and authentication
- Email verification
- Password reset
- OAuth authentication (Google)
- Profile management
- User administration
"""

from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List
from datetime import datetime, timedelta

from database import get_db
from models import User, UserRole, UserStatus
from schemas import (
    UserCreate,
    UserLogin,
    UserUpdate,
    PasswordChange,
    TokenResponse,
    UserResponseEnhanced,
    PasswordResetRequest,
    PasswordResetConfirm,
    EmailVerificationRequest,
    OAuthGoogleRequest,
    RoleUpdate,
    StatusUpdate,
)
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_current_active_user,
    require_role,
    create_email_verification_token,
    create_password_reset_token,
)
from services.email_service import send_verification_email, send_password_reset_email
from services.oauth_service import (
    exchange_google_code_for_token,
    get_google_user_info,
    find_or_create_oauth_user,
)
from config import settings


router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)


# ============================================================================
# Authentication Endpoints
# ============================================================================

@router.post("/register", response_model=UserResponseEnhanced, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate, db: Session = Depends(get_db)):
    """
    Register a new user.

    - **email**: User's email address (must be unique)
    - **username**: Username (must be unique, 3-50 characters, alphanumeric + underscores)
    - **password**: Password (minimum 8 characters)
    - **first_name**: Optional first name
    - **last_name**: Optional last name

    Returns the created user object with PENDING status.
    User must verify email before accessing protected resources.
    """
    # Check if email already exists
    existing_email = db.query(User).filter(User.email == user_data.email.lower()).first()
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    # Check if username already exists
    existing_username = db.query(User).filter(User.username == user_data.username).first()
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    # Hash password
    hashed_password = hash_password(user_data.password)

    # Generate email verification token
    verification_token = create_email_verification_token()

    # Create new user
    new_user = User(
        email=user_data.email.lower(),
        username=user_data.username,
        hashed_password=hashed_password,
        first_name=user_data.first_name,
        last_name=user_data.last_name,
        role=UserRole.USER,
        status=UserStatus.PENDING,
        email_verified=False,
        email_verification_token=verification_token,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Send verification email (non-blocking, errors are logged)
    send_verification_email(new_user.email, new_user.username, verification_token)

    return new_user


@router.post("/login", response_model=TokenResponse)
async def login_user(credentials: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate user and return access token.

    - **email**: User's email address
    - **password**: User's password

    Returns JWT access token valid for 30 minutes (configurable).
    """
    # Query user by email
    user = db.query(User).filter(User.email == credentials.email.lower()).first()

    # Check if user exists and password is correct
    if not user or not verify_password(credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Check user status
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required. Check your email."
        )

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended. Contact support."
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active"
        )

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create JWT token
    access_token_expires = timedelta(minutes=settings.jwt.access_token_expire_minutes)
    access_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value,
            "email_verified": user.email_verified
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": settings.jwt.access_token_expire_minutes * 60
    }


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(current_user: User = Depends(get_current_active_user)):
    """
    Logout the current user.

    Requires authentication with valid Bearer token.
    Note: JWT tokens are stateless and cannot be invalidated server-side.
    Client must discard the token.
    """
    return {
        "message": "Logged out successfully. Please discard your token."
    }


# ============================================================================
# Email Verification Endpoints
# ============================================================================

@router.get("/verify-email", status_code=status.HTTP_200_OK)
async def verify_email(token: str = Query(...), db: Session = Depends(get_db)):
    """
    Verify user email with verification token.

    - **token**: Email verification token sent to user's email (query parameter)

    Activates the user account and sets status to ACTIVE.
    """
    # Find user by verification token
    user = db.query(User).filter(User.email_verification_token == token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired verification token"
        )

    # Check if already verified
    if user.email_verified:
        return {"message": "Email already verified"}

    # Verify email
    user.email_verified = True
    user.status = UserStatus.ACTIVE
    user.email_verification_token = None  # Clear token
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Email verified successfully. You can now login."}


@router.post("/resend-verification", status_code=status.HTTP_200_OK)
async def resend_verification(request: EmailVerificationRequest, db: Session = Depends(get_db)):
    """
    Resend verification email if user didn't receive it.

    - **email**: User's email address

    Always returns success message for security (doesn't reveal if email exists).
    """
    # Query user by email
    user = db.query(User).filter(User.email == request.email.lower()).first()

    # For security, always return same message
    message = "If the email exists, verification link sent"

    if user and not user.email_verified:
        # Generate new token
        new_token = create_email_verification_token()
        user.email_verification_token = new_token
        user.updated_at = datetime.utcnow()
        db.commit()

        # Send verification email
        send_verification_email(user.email, user.username, new_token)

    return {"message": message}


# ============================================================================
# Password Reset Endpoints
# ============================================================================

@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(request: PasswordResetRequest, db: Session = Depends(get_db)):
    """
    Request password reset for user account.

    - **email**: User's email address

    Sends password reset token to user's email (or console in development mode).
    Always returns success message for security (doesn't reveal if email exists).
    """
    # Query user by email
    user = db.query(User).filter(User.email == request.email.lower()).first()

    # For security, always return same message
    message = "If the email exists, reset instructions sent"

    if user:
        # Generate reset token
        reset_token = create_password_reset_token()
        reset_expires = datetime.utcnow() + timedelta(hours=1)

        user.password_reset_token = reset_token
        user.password_reset_expires = reset_expires
        user.updated_at = datetime.utcnow()
        db.commit()

        # Send reset email (development mode: prints to console)
        send_password_reset_email(user.email, user.username, reset_token)

    return {"message": message}


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(request: PasswordResetConfirm, db: Session = Depends(get_db)):
    """
    Reset user password using reset token.

    - **token**: Password reset token from email
    - **new_password**: New password (minimum 8 characters)
    """
    # Find user by reset token
    user = db.query(User).filter(User.password_reset_token == request.token).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid or expired reset token"
        )

    # Check if token expired
    if user.password_reset_expires < datetime.utcnow():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Reset token expired. Please request a new one."
        )

    # Hash new password
    user.hashed_password = hash_password(request.new_password)
    user.password_reset_token = None  # Clear token
    user.password_reset_expires = None
    user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password reset successfully"}


# ============================================================================
# OAuth Endpoints
# ============================================================================

@router.post("/oauth/google", response_model=TokenResponse)
async def oauth_google(request: OAuthGoogleRequest, db: Session = Depends(get_db)):
    """
    Exchange Google OAuth authorization code for JWT token.

    - **code**: Authorization code from Google OAuth flow
    - **redirect_uri**: Redirect URI (must match OAuth app configuration)

    Creates new user or links to existing account based on email.
    Returns JWT access token.
    """
    # Exchange authorization code for access token
    token_data = exchange_google_code_for_token(request.code, request.redirect_uri)
    access_token = token_data.get("access_token")

    # Fetch user info from Google
    user_info = get_google_user_info(access_token)

    # Extract user data
    oauth_id = user_info.get("id")
    email = user_info.get("email")
    name = user_info.get("name", "")
    verified_email = user_info.get("verified_email", False)

    # Check if email is verified on Google
    if not verified_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google account email not verified"
        )

    # Find or create OAuth user
    user = find_or_create_oauth_user(db, "google", oauth_id, email, name)

    # Update last login
    user.last_login = datetime.utcnow()
    db.commit()

    # Create JWT token
    access_token_expires = timedelta(minutes=settings.jwt.access_token_expire_minutes)
    jwt_token = create_access_token(
        data={
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "status": user.status.value,
            "email_verified": user.email_verified
        },
        expires_delta=access_token_expires
    )

    return {
        "access_token": jwt_token,
        "token_type": "bearer",
        "expires_in": settings.jwt.access_token_expire_minutes * 60
    }


# ============================================================================
# Profile Management Endpoints
# ============================================================================

@router.get("/profile", response_model=UserResponseEnhanced)
async def get_user_profile(current_user: User = Depends(get_current_active_user)):
    """
    Get current user's profile information.

    Requires authentication with valid Bearer token and verified email.
    """
    return current_user


@router.put("/profile", response_model=UserResponseEnhanced)
async def update_user_profile(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Update current user's profile information.

    Requires authentication with valid Bearer token.

    - **first_name**: User's first name (optional)
    - **last_name**: User's last name (optional)
    - **email**: User's email address (optional, requires re-verification if changed)
    """
    # Update email if provided and different
    if user_update.email and user_update.email.lower() != current_user.email:
        # Check if new email is already in use
        existing = db.query(User).filter(
            User.email == user_update.email.lower(),
            User.id != current_user.id
        ).first()

        if existing:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already in use"
            )

        # Update email and require re-verification
        current_user.email = user_update.email.lower()
        current_user.email_verified = False
        current_user.status = UserStatus.PENDING

        # Generate new verification token
        new_token = create_email_verification_token()
        current_user.email_verification_token = new_token

        # Send verification email
        send_verification_email(current_user.email, current_user.username, new_token)

    # Update other fields
    if user_update.first_name is not None:
        current_user.first_name = user_update.first_name

    if user_update.last_name is not None:
        current_user.last_name = user_update.last_name

    current_user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(current_user)

    return current_user


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Change user's password.

    Requires authentication with valid Bearer token.

    - **current_password**: Current password for verification (optional for OAuth users)
    - **new_password**: New password (minimum 8 characters)
    - **confirm_password**: Confirmation of new password (must match)
    """
    # Check if passwords match
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )

    # Check if OAuth user setting first password
    is_oauth_user = current_user.oauth_provider is not None and current_user.hashed_password == ""

    if not is_oauth_user:
        # Regular user: verify current password
        if not password_data.current_password:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is required"
            )

        if not verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Current password is incorrect"
            )

    # Update password
    current_user.hashed_password = hash_password(password_data.new_password)
    current_user.updated_at = datetime.utcnow()
    db.commit()

    return {"message": "Password changed successfully"}


# ============================================================================
# User List and Detail Endpoints
# ============================================================================

@router.get("/", response_model=List[UserResponseEnhanced])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    List all users (admin only).

    Requires authentication with ADMIN role.

    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 10, max: 100)
    """
    # Enforce max limit
    if limit > 100:
        limit = 100

    users = db.query(User).offset(skip).limit(limit).all()
    return users


@router.get("/{user_id}", response_model=UserResponseEnhanced)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Get a specific user by ID.

    Requires authentication with valid Bearer token.
    Users can view their own profile, admins can view any profile.
    """
    # Query user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Authorization check
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot view other users' profiles"
        )

    return user


# ============================================================================
# Admin User Management Endpoints
# ============================================================================

@router.patch("/{user_id}/role", response_model=UserResponseEnhanced)
async def update_user_role(
    user_id: int,
    role_update: RoleUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Update user's role (admin only).

    Requires ADMIN role.

    - **role**: New role (USER, AUTHOR, EDITOR, or ADMIN)
    """
    # Query user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from changing their own role
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own role"
        )

    # Update role
    try:
        user.role = UserRole[role_update.role]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid role"
        )

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return user


@router.patch("/{user_id}/status", response_model=UserResponseEnhanced)
async def update_user_status(
    user_id: int,
    status_update: StatusUpdate,
    current_user: User = Depends(require_role([UserRole.ADMIN])),
    db: Session = Depends(get_db)
):
    """
    Update user's status (admin only).

    Requires ADMIN role.

    - **status**: New status (ACTIVE or SUSPENDED)

    Note: Cannot manually set status to PENDING.
    """
    # Query user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Prevent admin from changing their own status
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change your own status"
        )

    # Validate status
    if status_update.status == "PENDING":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot manually set status to PENDING"
        )

    # Update status
    try:
        user.status = UserStatus[status_update.status]
    except KeyError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid status"
        )

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)

    return user


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """
    Delete a user account (admin only or self).

    Requires authentication with valid Bearer token.
    Users can delete their own account, admins can delete any account.
    """
    # Query user
    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    # Authorization check
    if current_user.id != user_id and current_user.role != UserRole.ADMIN:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Cannot delete other users"
        )

    # Delete user
    db.delete(user)
    db.commit()

    return None
