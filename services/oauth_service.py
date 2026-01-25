"""
OAuth service for handling Google OAuth 2.0 authentication.

This module provides:
- Google OAuth code exchange for access tokens
- Fetching user information from Google
- Creating or finding users based on OAuth data
"""
import requests
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from datetime import datetime

from models import User, UserRole, UserStatus
from config import settings


def exchange_google_code_for_token(code: str, redirect_uri: str) -> dict:
    """
    Exchange Google OAuth authorization code for access token.

    Args:
        code: Authorization code from Google OAuth flow
        redirect_uri: Redirect URI that must match OAuth app configuration

    Returns:
        Dictionary containing access_token, expires_in, token_type

    Raises:
        HTTPException: If code exchange fails
    """
    token_url = "https://oauth2.googleapis.com/token"

    payload = {
        "code": code,
        "client_id": settings.oauth.google_client_id,
        "client_secret": settings.oauth.google_client_secret,
        "redirect_uri": redirect_uri,
        "grant_type": "authorization_code"
    }

    try:
        response = requests.post(token_url, data=payload, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid authorization code: {str(e)}"
        )


def get_google_user_info(access_token: str) -> dict:
    """
    Fetch user information from Google using access token.

    Args:
        access_token: Google OAuth access token

    Returns:
        Dictionary containing id, email, name, picture, verified_email

    Raises:
        HTTPException: If fetching user info fails
    """
    userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
    headers = {"Authorization": f"Bearer {access_token}"}

    try:
        response = requests.get(userinfo_url, headers=headers, timeout=10)
        response.raise_for_status()
        return response.json()
    except requests.RequestException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to fetch user info: {str(e)}"
        )


def _generate_unique_username(db: Session, base_username: str) -> str:
    """
    Generate a unique username by appending random numbers if needed.

    Args:
        db: Database session
        base_username: Base username to start with

    Returns:
        Unique username string
    """
    import random

    # Clean base username
    base_username = base_username.lower().replace(" ", "_")[:46]  # Leave room for suffix

    # Check if base username is available
    existing = db.query(User).filter(User.username == base_username).first()
    if not existing:
        return base_username

    # Append random numbers until unique
    for _ in range(10):  # Try up to 10 times
        suffix = random.randint(1000, 9999)
        username = f"{base_username}{suffix}"
        existing = db.query(User).filter(User.username == username).first()
        if not existing:
            return username

    # Fallback: use timestamp
    import time
    return f"{base_username}{int(time.time() % 10000)}"


def find_or_create_oauth_user(
    db: Session,
    provider: str,
    oauth_id: str,
    email: str,
    name: str
) -> User:
    """
    Find existing OAuth user or create new one.

    Flow:
    1. Check if user exists with this OAuth provider and ID
    2. If not, check if user exists with this email
    3. If email exists, link OAuth to existing account
    4. If neither exists, create new user

    Args:
        db: Database session
        provider: OAuth provider name (e.g., 'google')
        oauth_id: OAuth user ID from provider
        email: User's email from OAuth provider
        name: User's name from OAuth provider

    Returns:
        User model instance (existing or newly created)
    """
    # 1. Check for existing OAuth user
    user = db.query(User).filter(
        User.oauth_provider == provider,
        User.oauth_id == oauth_id
    ).first()

    if user:
        return user

    # 2. Check for existing user by email
    user = db.query(User).filter(User.email == email.lower()).first()

    if user:
        # Link OAuth to existing account
        user.oauth_provider = provider
        user.oauth_id = oauth_id
        user.updated_at = datetime.utcnow()
        db.commit()
        db.refresh(user)
        return user

    # 3. Create new user
    # Generate username from email
    base_username = email.split('@')[0]
    username = _generate_unique_username(db, base_username)

    # Parse first name from name
    name_parts = name.split() if name else []
    first_name = name_parts[0] if name_parts else None
    last_name = " ".join(name_parts[1:]) if len(name_parts) > 1 else None

    new_user = User(
        email=email.lower(),
        username=username,
        hashed_password="",  # OAuth users don't have password initially
        first_name=first_name,
        last_name=last_name,
        role=UserRole.USER,
        status=UserStatus.ACTIVE,  # OAuth users are pre-verified
        email_verified=True,  # Email verified by OAuth provider
        oauth_provider=provider,
        oauth_id=oauth_id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow()
    )

    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    return new_user
