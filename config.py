"""
Configuration module for Personal Blog Assistant.

This module uses Pydantic V2 for settings management, providing type-safe
configuration for database, JWT, and application settings.
"""

from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings


class DatabaseSettings(BaseSettings):
    """Database configuration settings."""

    url: str = Field(
        default="sqlite:///./blog.db",
        description="Database connection URL",
        examples=["postgresql://user:password@localhost/blog_db"],
    )
    echo: bool = Field(
        default=False,
        description="Enable SQL echo logging",
    )
    pool_size: int = Field(
        default=5,
        description="Database connection pool size",
        ge=1,
    )
    max_overflow: int = Field(
        default=10,
        description="Maximum overflow connections",
        ge=0,
    )
    pool_pre_ping: bool = Field(
        default=True,
        description="Enable connection health checks",
    )

    class Config:
        env_prefix = "DB_"


class JWTSettings(BaseSettings):
    """JWT (JSON Web Token) configuration settings."""

    secret_key: str = Field(
        default="your-secret-key-change-in-production",
        description="Secret key for JWT encoding/decoding",
        min_length=32,
    )
    algorithm: str = Field(
        default="HS256",
        description="JWT algorithm for signing",
    )
    access_token_expire_minutes: int = Field(
        default=30,
        description="Access token expiration time in minutes",
        ge=1,
    )
    refresh_token_expire_days: int = Field(
        default=7,
        description="Refresh token expiration time in days",
        ge=1,
    )

    class Config:
        env_prefix = "JWT_"


class ApplicationSettings(BaseSettings):
    """General application configuration settings."""

    app_name: str = Field(
        default="Personal Blog Assistant",
        description="Application name",
    )
    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    environment: str = Field(
        default="development",
        description="Application environment",
        pattern="^(development|staging|production)$",
    )
    api_prefix: str = Field(
        default="/api/v1",
        description="API URL prefix",
    )
    cors_origins: list[str] = Field(
        default=["http://localhost:3000", "http://localhost:8000"],
        description="CORS allowed origins",
    )
    cors_credentials: bool = Field(
        default=True,
        description="Allow credentials in CORS requests",
    )
    max_request_size: int = Field(
        default=10485760,  # 10MB in bytes
        description="Maximum request body size in bytes",
        ge=1024,
    )
    log_level: str = Field(
        default="INFO",
        description="Logging level",
        pattern="^(DEBUG|INFO|WARNING|ERROR|CRITICAL)$",
    )

    class Config:
        env_prefix = "APP_"


class Settings(BaseSettings):
    """Main settings class combining all configuration modules."""

    database: DatabaseSettings = Field(default_factory=DatabaseSettings)
    jwt: JWTSettings = Field(default_factory=JWTSettings)
    application: ApplicationSettings = Field(default_factory=ApplicationSettings)

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.application.environment == "production"

    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.application.environment == "development"


# Global settings instance
settings = Settings()
