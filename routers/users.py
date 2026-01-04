"""
User Management API Router

This module provides REST API endpoints for:
- User registration
- User login/authentication
- User profile management
- User password management
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Optional, List
from datetime import datetime, timedelta
import jwt
from passlib.context import CryptContext

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    responses={404: {"description": "Not found"}},
)

# Password hashing configuration
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration
SECRET_KEY = "your-secret-key-change-in-production"
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


# ============================================================================
# Schemas (Pydantic Models)
# ============================================================================

from pydantic import BaseModel, EmailStr, Field

class UserBase(BaseModel):
    """Base user schema"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: str
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponse(UserBase):
    """Schema for user response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class UserDetailResponse(UserResponse):
    """Detailed user response with additional information"""
    last_login: Optional[datetime] = None
    email_verified: bool = False


# ============================================================================
# Utility Functions
# ============================================================================

def hash_password(password: str) -> str:
    """Hash a password using bcrypt"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a password against its hash"""
    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create a JWT access token"""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    
    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


def decode_token(token: str) -> dict:
    """Decode and verify a JWT token"""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
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
# Authentication Dependencies
# ============================================================================

from fastapi.security import HTTPBearer, HTTPAuthCredentials

security = HTTPBearer()


async def get_current_user(credentials: HTTPAuthCredentials = Depends(security)):
    """
    Get the current authenticated user from token.
    This is a dependency that should be used with database integration.
    """
    token = credentials.credentials
    payload = decode_token(token)
    user_id: int = payload.get("sub")
    
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication credentials"
        )
    
    # TODO: Fetch user from database using user_id
    # db_user = get_user_by_id(db, user_id)
    # if db_user is None:
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="User not found"
    #     )
    # return db_user
    
    return {"user_id": user_id}


# ============================================================================
# API Endpoints
# ============================================================================

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register_user(user_data: UserCreate):
    """
    Register a new user.
    
    - **email**: User's email address (must be unique)
    - **username**: Username (must be unique, 3-50 characters)
    - **password**: Password (minimum 8 characters)
    - **first_name**: Optional first name
    - **last_name**: Optional last name
    
    Returns the created user object.
    """
    # TODO: Implement database logic
    # Check if email already exists
    # existing_user = db.query(User).filter(User.email == user_data.email).first()
    # if existing_user:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Email already registered"
    #     )
    
    # Check if username already exists
    # existing_username = db.query(User).filter(User.username == user_data.username).first()
    # if existing_username:
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Username already taken"
    #     )
    
    # Hash password
    hashed_password = hash_password(user_data.password)
    
    # Create user object
    # new_user = User(
    #     email=user_data.email,
    #     username=user_data.username,
    #     first_name=user_data.first_name,
    #     last_name=user_data.last_name,
    #     hashed_password=hashed_password,
    #     is_active=True,
    #     created_at=datetime.utcnow(),
    #     updated_at=datetime.utcnow()
    # )
    
    # db.add(new_user)
    # db.commit()
    # db.refresh(new_user)
    
    return {
        "id": 1,
        "email": user_data.email,
        "username": user_data.username,
        "first_name": user_data.first_name,
        "last_name": user_data.last_name,
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }


@router.post("/login", response_model=TokenResponse)
async def login_user(credentials: UserLogin):
    """
    Authenticate user and return access token.
    
    - **email**: User's email address
    - **password**: User's password
    
    Returns JWT access token valid for 30 minutes.
    """
    # TODO: Implement database logic
    # user = db.query(User).filter(User.email == credentials.email).first()
    # if not user or not verify_password(credentials.password, user.hashed_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Invalid email or password",
    #         headers={"WWW-Authenticate": "Bearer"}
    #     )
    
    # if not user.is_active:
    #     raise HTTPException(
    #         status_code=status.HTTP_403_FORBIDDEN,
    #         detail="User account is disabled"
    #     )
    
    # Update last login
    # user.last_login = datetime.utcnow()
    # db.commit()
    
    # Create access token
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": 1},  # TODO: Replace with actual user_id
        expires_delta=access_token_expires
    )
    
    return {
        "access_token": access_token,
        "token_type": "bearer",
        "expires_in": ACCESS_TOKEN_EXPIRE_MINUTES * 60
    }


@router.get("/profile", response_model=UserDetailResponse)
async def get_user_profile(current_user = Depends(get_current_user)):
    """
    Get current user's profile information.
    
    Requires authentication with valid Bearer token.
    """
    # TODO: Implement database logic
    # user = db.query(User).filter(User.id == current_user.id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )
    
    return {
        "id": current_user["user_id"],
        "email": "user@example.com",
        "username": "username",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": datetime.utcnow(),
        "email_verified": False
    }


@router.put("/profile", response_model=UserDetailResponse)
async def update_user_profile(
    user_update: UserUpdate,
    current_user = Depends(get_current_user)
):
    """
    Update current user's profile information.
    
    Requires authentication with valid Bearer token.
    
    - **first_name**: User's first name (optional)
    - **last_name**: User's last name (optional)
    - **email**: User's email address (optional)
    """
    # TODO: Implement database logic
    # user = db.query(User).filter(User.id == current_user.id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )
    
    # if user_update.email and user_update.email != user.email:
    #     existing = db.query(User).filter(User.email == user_update.email).first()
    #     if existing:
    #         raise HTTPException(
    #             status_code=status.HTTP_400_BAD_REQUEST,
    #             detail="Email already in use"
    #         )
    
    # Update fields
    # if user_update.first_name:
    #     user.first_name = user_update.first_name
    # if user_update.last_name:
    #     user.last_name = user_update.last_name
    # if user_update.email:
    #     user.email = user_update.email
    
    # user.updated_at = datetime.utcnow()
    # db.commit()
    # db.refresh(user)
    
    return {
        "id": current_user["user_id"],
        "email": user_update.email or "user@example.com",
        "username": "username",
        "first_name": user_update.first_name or "John",
        "last_name": user_update.last_name or "Doe",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": datetime.utcnow(),
        "email_verified": False
    }


@router.post("/change-password", status_code=status.HTTP_200_OK)
async def change_password(
    password_data: PasswordChange,
    current_user = Depends(get_current_user)
):
    """
    Change user's password.
    
    Requires authentication with valid Bearer token.
    
    - **current_password**: Current password for verification
    - **new_password**: New password (minimum 8 characters)
    - **confirm_password**: Confirmation of new password (must match)
    """
    if password_data.new_password != password_data.confirm_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="New passwords do not match"
        )
    
    # TODO: Implement database logic
    # user = db.query(User).filter(User.id == current_user.id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )
    
    # if not verify_password(password_data.current_password, user.hashed_password):
    #     raise HTTPException(
    #         status_code=status.HTTP_401_UNAUTHORIZED,
    #         detail="Current password is incorrect"
    #     )
    
    # Update password
    # user.hashed_password = hash_password(password_data.new_password)
    # user.updated_at = datetime.utcnow()
    # db.commit()
    
    return {
        "message": "Password changed successfully"
    }


@router.get("/", response_model=List[UserResponse])
async def list_users(
    skip: int = 0,
    limit: int = 10,
    current_user = Depends(get_current_user)
):
    """
    List all users (admin only).
    
    Requires authentication with valid Bearer token.
    
    - **skip**: Number of records to skip (default: 0)
    - **limit**: Maximum number of records to return (default: 10, max: 100)
    """
    if limit > 100:
        limit = 100
    
    # TODO: Implement database logic with pagination
    # Check if current_user is admin
    # users = db.query(User).offset(skip).limit(limit).all()
    
    return [
        {
            "id": 1,
            "email": "user@example.com",
            "username": "username",
            "first_name": "John",
            "last_name": "Doe",
            "is_active": True,
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
    ]


@router.get("/{user_id}", response_model=UserDetailResponse)
async def get_user_by_id(
    user_id: int,
    current_user = Depends(get_current_user)
):
    """
    Get a specific user by ID.
    
    Requires authentication with valid Bearer token.
    """
    # TODO: Implement database logic
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )
    
    return {
        "id": user_id,
        "email": "user@example.com",
        "username": "username",
        "first_name": "John",
        "last_name": "Doe",
        "is_active": True,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow(),
        "last_login": datetime.utcnow(),
        "email_verified": False
    }


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: int,
    current_user = Depends(get_current_user)
):
    """
    Delete a user account (admin only or self).
    
    Requires authentication with valid Bearer token.
    """
    # TODO: Implement database logic
    # Check if current_user is admin or deleting their own account
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )
    
    # db.delete(user)
    # db.commit()
    
    return None


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout_user(current_user = Depends(get_current_user)):
    """
    Logout the current user.
    
    Requires authentication with valid Bearer token.
    Note: JWT tokens cannot be invalidated server-side. 
    For production, consider implementing token blacklist.
    """
    # TODO: Implement token blacklist in production
    # Add token to blacklist
    # blacklist_token(token)
    
    return {
        "message": "Logged out successfully"
    }


@router.post("/verify-email/{token}", status_code=status.HTTP_200_OK)
async def verify_email(token: str):
    """
    Verify user email with verification token.
    
    - **token**: Email verification token sent to user's email
    """
    # TODO: Implement email verification logic
    # payload = decode_token(token)
    # user_id = payload.get("sub")
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )
    
    # user.email_verified = True
    # db.commit()
    
    return {
        "message": "Email verified successfully"
    }


@router.post("/request-password-reset", status_code=status.HTTP_200_OK)
async def request_password_reset(email: str):
    """
    Request password reset for user account.
    
    - **email**: User's email address
    
    Sends password reset token to user's email.
    """
    # TODO: Implement password reset logic
    # user = db.query(User).filter(User.email == email).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )
    
    # Create password reset token
    # reset_token = create_access_token(
    #     data={"sub": user.id, "type": "password_reset"},
    #     expires_delta=timedelta(hours=1)
    # )
    
    # Send email with reset token
    # send_password_reset_email(user.email, reset_token)
    
    return {
        "message": "Password reset instructions sent to your email"
    }


@router.post("/reset-password", status_code=status.HTTP_200_OK)
async def reset_password(
    token: str,
    new_password: str = Field(..., min_length=8)
):
    """
    Reset user password using reset token.
    
    - **token**: Password reset token from email
    - **new_password**: New password (minimum 8 characters)
    """
    # TODO: Implement password reset logic
    # payload = decode_token(token)
    # if payload.get("type") != "password_reset":
    #     raise HTTPException(
    #         status_code=status.HTTP_400_BAD_REQUEST,
    #         detail="Invalid token type"
    #     )
    
    # user_id = payload.get("sub")
    # user = db.query(User).filter(User.id == user_id).first()
    # if not user:
    #     raise HTTPException(
    #         status_code=status.HTTP_404_NOT_FOUND,
    #         detail="User not found"
    #     )
    
    # user.hashed_password = hash_password(new_password)
    # db.commit()
    
    return {
        "message": "Password reset successfully"
    }
