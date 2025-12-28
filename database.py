"""
Database configuration and initialization module.

This module handles SQLAlchemy engine setup, session management,
and database initialization for PostgreSQL.
"""

import os
from typing import Generator
from sqlalchemy import create_engine, event
from sqlalchemy.orm import sessionmaker, Session, declarative_base
from sqlalchemy.pool import NullPool
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database URL configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql://user:password@localhost:5432/personal_blog_assistant"
)

# SQLAlchemy engine configuration
# Using NullPool to avoid connection pooling issues in certain environments
engine = create_engine(
    DATABASE_URL,
    echo=os.getenv("SQL_ECHO", "False").lower() == "true",
    pool_pre_ping=True,  # Test connections before using them
    pool_recycle=3600,   # Recycle connections after 1 hour
)

# Session factory
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)

# Declarative base for ORM models
Base = declarative_base()


def get_db() -> Generator[Session, None, None]:
    """
    Dependency function for FastAPI to get database sessions.
    
    Yields:
        Session: SQLAlchemy database session
        
    Example:
        @app.get("/items")
        def read_items(db: Session = Depends(get_db)):
            return db.query(Item).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_conn, connection_record):
    """
    Configure PostgreSQL session settings on connection.
    
    This is called automatically when a new connection is created.
    """
    # Set isolation level and other connection parameters if needed
    pass


def init_db() -> None:
    """
    Initialize the database by creating all tables.
    
    This function creates all tables defined in the Base.metadata.
    It should be called once during application startup.
    
    Example:
        from database import init_db
        init_db()
    """
    Base.metadata.create_all(bind=engine)
    print("Database tables initialized successfully.")


def drop_db() -> None:
    """
    Drop all database tables.
    
    WARNING: This is a destructive operation and will delete all data.
    Use with caution, typically only for testing or development.
    
    Example:
        from database import drop_db
        drop_db()
    """
    Base.metadata.drop_all(bind=engine)
    print("All database tables dropped successfully.")


def get_engine():
    """
    Get the SQLAlchemy engine instance.
    
    Returns:
        Engine: SQLAlchemy engine for database connections
    """
    return engine


def get_session_factory():
    """
    Get the session factory.
    
    Returns:
        sessionmaker: SQLAlchemy session factory
    """
    return SessionLocal


if __name__ == "__main__":
    # Initialize database tables when this module is run directly
    init_db()
