"""
Database models for the Personal Blog Assistant application.

This module defines SQLAlchemy ORM models for users, posts, and comments.
"""
import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum as SQLEnum,
    Index,
    UniqueConstraint,
)
from sqlalchemy.orm import relationship
from database import Base


class UserRole(str, enum.Enum):
    """User role enumeration for role-based access control."""
    USER = "USER"
    AUTHOR = "AUTHOR"
    EDITOR = "EDITOR"
    ADMIN = "ADMIN"


class UserStatus(str, enum.Enum):
    """User account status enumeration."""
    PENDING = "PENDING"  # Awaiting email verification
    ACTIVE = "ACTIVE"    # Email verified, can access features
    SUSPENDED = "SUSPENDED"  # Account suspended by admin


class User(Base):
    """User model for authentication and authorization."""

    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Authentication fields
    email = Column(String(255), unique=True, nullable=False, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)

    # Profile fields
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)

    # Authorization fields
    role = Column(SQLEnum(UserRole), nullable=False, default=UserRole.USER)
    status = Column(SQLEnum(UserStatus), nullable=False, default=UserStatus.PENDING)

    # Email verification fields
    email_verified = Column(Boolean, nullable=False, default=False)
    email_verification_token = Column(String(255), nullable=True, unique=True, index=True)

    # Password reset fields
    password_reset_token = Column(String(255), nullable=True, unique=True, index=True)
    password_reset_expires = Column(DateTime, nullable=True)

    # OAuth fields
    oauth_provider = Column(String(50), nullable=True)  # 'google', 'github', etc.
    oauth_id = Column(String(255), nullable=True)  # External OAuth user ID

    # Timestamps
    last_login = Column(DateTime, nullable=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    posts = relationship("Post", back_populates="author", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="author", cascade="all, delete-orphan")

    # Composite indexes
    __table_args__ = (
        Index("idx_oauth_provider_id", "oauth_provider", "oauth_id"),
        UniqueConstraint("oauth_provider", "oauth_id", name="uq_oauth_provider_id"),
    )

    def __repr__(self):
        return f"<User(id={self.id}, email={self.email}, username={self.username}, role={self.role})>"


class Post(Base):
    """Post model for blog posts."""

    __tablename__ = "posts"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Content fields
    title = Column(String(255), nullable=False)
    content = Column(Text, nullable=False)

    # Foreign key to User
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="posts")
    comments = relationship("Comment", back_populates="post", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Post(id={self.id}, title={self.title}, author_id={self.author_id})>"


class Comment(Base):
    """Comment model for post comments."""

    __tablename__ = "comments"

    # Primary key
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)

    # Content field
    content = Column(Text, nullable=False)

    # Foreign keys
    post_id = Column(Integer, ForeignKey("posts.id"), nullable=False)
    author_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    author = relationship("User", back_populates="comments")
    post = relationship("Post", back_populates="comments")

    def __repr__(self):
        return f"<Comment(id={self.id}, post_id={self.post_id}, author_id={self.author_id})>"
