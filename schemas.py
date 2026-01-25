"""
Pydantic schemas for request/response validation.

This module defines all Pydantic v2 schemas used across the application
for input validation and response serialization.
"""
from pydantic import BaseModel, EmailStr, Field, field_validator
from typing import Optional
from datetime import datetime
import re


# ============================================================================
# User Schemas
# ============================================================================

class UserBase(BaseModel):
    """Base user schema with common fields"""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Ensure email is lowercase"""
        return v.lower()

    @field_validator('username')
    @classmethod
    def username_alphanumeric(cls, v: str) -> str:
        """Ensure username is alphanumeric with underscores only"""
        if not re.match(r'^[a-zA-Z0-9_]+$', v):
            raise ValueError('Username must be alphanumeric with underscores only')
        return v


class UserCreate(UserBase):
    """Schema for user registration"""
    password: str = Field(..., min_length=8)


class UserUpdate(BaseModel):
    """Schema for updating user profile"""
    first_name: Optional[str] = Field(None, max_length=100)
    last_name: Optional[str] = Field(None, max_length=100)
    email: Optional[EmailStr] = None

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: Optional[str]) -> Optional[str]:
        """Ensure email is lowercase"""
        return v.lower() if v else None


class PasswordChange(BaseModel):
    """Schema for changing password"""
    current_password: Optional[str] = None  # Optional for OAuth users setting first password
    new_password: str = Field(..., min_length=8)
    confirm_password: str


class UserLogin(BaseModel):
    """Schema for user login"""
    email: EmailStr
    password: str

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Ensure email is lowercase"""
        return v.lower()


class TokenResponse(BaseModel):
    """Schema for token response"""
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class UserResponseEnhanced(BaseModel):
    """Enhanced user response schema with all fields"""
    id: int
    email: EmailStr
    username: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: str
    status: str
    email_verified: bool
    oauth_provider: Optional[str] = None
    last_login: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserResponse(UserBase):
    """Basic user response schema (for backward compatibility)"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class UserDetailResponse(UserResponse):
    """Detailed user response with additional information"""
    last_login: Optional[datetime] = None
    email_verified: bool = False


class TokenPayload(BaseModel):
    """Schema for JWT token payload"""
    sub: int  # user_id
    email: str
    role: str
    status: str
    email_verified: bool
    exp: int  # expiration timestamp


# ============================================================================
# Email Verification Schemas
# ============================================================================

class EmailVerificationRequest(BaseModel):
    """Schema for requesting email verification"""
    email: EmailStr

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Ensure email is lowercase"""
        return v.lower()


class EmailVerificationConfirm(BaseModel):
    """Schema for confirming email verification"""
    token: str


# ============================================================================
# Password Reset Schemas
# ============================================================================

class PasswordResetRequest(BaseModel):
    """Schema for requesting password reset"""
    email: EmailStr

    @field_validator('email')
    @classmethod
    def email_lowercase(cls, v: str) -> str:
        """Ensure email is lowercase"""
        return v.lower()


class PasswordResetConfirm(BaseModel):
    """Schema for confirming password reset"""
    token: str
    new_password: str = Field(..., min_length=8)


# ============================================================================
# OAuth Schemas
# ============================================================================

class OAuthGoogleRequest(BaseModel):
    """Schema for Google OAuth authentication"""
    code: str
    redirect_uri: str


# ============================================================================
# Comment Schemas
# ============================================================================

class CommentCreate(BaseModel):
    """Schema for creating a comment"""
    content: str = Field(..., min_length=1, max_length=5000)


class CommentUpdate(BaseModel):
    """Schema for updating a comment"""
    content: str = Field(..., min_length=1, max_length=5000)


class CommentResponse(BaseModel):
    """Schema for comment response"""
    id: int
    content: str
    post_id: int
    author_id: int
    author: UserResponseEnhanced
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


# ============================================================================
# Admin Schemas
# ============================================================================

class RoleUpdate(BaseModel):
    """Schema for updating user role (admin only)"""
    role: str = Field(..., pattern="^(USER|AUTHOR|EDITOR|ADMIN)$")


class StatusUpdate(BaseModel):
    """Schema for updating user status (admin only)"""
    status: str = Field(..., pattern="^(ACTIVE|SUSPENDED)$")
