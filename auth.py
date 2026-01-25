"""
Authentication module for JWT-based authentication and authorization.

This module provides:
- Password hashing and verification
- JWT token creation and validation
- Authentication dependencies for protected endpoints
- Role-based authorization helpers
"""
from datetime import datetime, timedelta
from typing import List, Callable
import secrets
import jwt
from passlib.context import CryptContext
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthCredentials
from sqlalchemy.orm import Session

from database import get_db
from models import User, UserRole, UserStatus
from config import settings


# ============================================================================
# Password Hashing
# ============================================================================

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password

    Returns:
        Hashed password string
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Args:
        plain_password: Plain text password to verify
        hashed_password: Hashed password to check against

    Returns:
        True if password matches, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ============================================================================
# JWT Token Functions
# ============================================================================

def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token.

    Args:
        data: Dictionary of claims to encode in the token
        expires_delta: Optional custom expiration time

    Returns:
        Encoded JWT token string
    """
    to_encode = data.copy()

    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.jwt.access_token_expire_minutes
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode,
        settings.jwt.secret_key,
        algorithm=settings.jwt.algorithm
    )
    return encoded_jwt


def decode_token(token: str) -> dict:
    """
    Decode and verify a JWT token.

    Args:
        token: JWT token string to decode

    Returns:
        Dictionary of token payload/claims

    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        payload = jwt.decode(
            token,
            settings.jwt.secret_key,
            algorithms=[settings.jwt.algorithm]
        )
        return payload
    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired"
        )
    except jwt.InvalidTokenError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token"
        )


# ============================================================================
# Token Generation for Email and Password Reset
# ============================================================================

def create_email_verification_token() -> str:
    """
    Generate a random token for email verification.

    Returns:
        Random 32-byte hex-encoded token string
    """
    return secrets.token_hex(32)


def create_password_reset_token() -> str:
    """
    Generate a random token for password reset.

    Returns:
        Random 32-byte hex-encoded token string
    """
    return secrets.token_hex(32)


# ============================================================================
# Authentication Dependencies
# ============================================================================

security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.

    This dependency:
    1. Extracts and validates the JWT token
    2. Fetches the user from the database
    3. Checks if the user account is active

    Args:
        credentials: HTTP Bearer credentials with JWT token
        db: Database session

    Returns:
        User model instance

    Raises:
        HTTPException: If token is invalid, user not found, or account not active
    """
    token = credentials.credentials
    payload = decode_token(token)
    user_id: int = payload.get("sub")

    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )

    # Fetch user from database
    user = db.query(User).filter(User.id == user_id).first()
    if user is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    # Check user status
    if user.status == UserStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email verification required"
        )

    if user.status == UserStatus.SUSPENDED:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account suspended"
        )

    if user.status != UserStatus.ACTIVE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account not active"
        )

    return user


def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current authenticated user with email verification check.

    This dependency wraps get_current_user and adds an additional
    check to ensure the user's email is verified.

    Use this for most protected endpoints that require verified users.

    Args:
        current_user: User from get_current_user dependency

    Returns:
        User model instance

    Raises:
        HTTPException: If email is not verified
    """
    if not current_user.email_verified:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Email not verified"
        )

    return current_user


# ============================================================================
# Role-Based Authorization
# ============================================================================

def require_role(allowed_roles: List[UserRole]) -> Callable:
    """
    Dependency factory for role-based access control.

    Creates a dependency function that checks if the current user
    has one of the allowed roles.

    Usage:
        @router.get("/admin")
        def admin_endpoint(user: User = Depends(require_role([UserRole.ADMIN]))):
            ...

    Args:
        allowed_roles: List of UserRole enums that are allowed access

    Returns:
        Dependency function that validates user role
    """
    def role_checker(current_user: User = Depends(get_current_active_user)) -> User:
        """
        Check if current user has required role.

        Args:
            current_user: User from get_current_active_user dependency

        Returns:
            User model instance if authorized

        Raises:
            HTTPException: If user doesn't have required role
        """
        if current_user.role not in allowed_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user

    return role_checker
