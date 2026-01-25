"""
Personal Blog Assistant - FastAPI Application

Main application entry point that configures and runs the FastAPI server.
"""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from config import settings
from database import engine, Base

# Import routers
from routers import users, comments

# Create database tables
# Note: In production, use Alembic migrations instead
Base.metadata.create_all(bind=engine)

# Create FastAPI application
app = FastAPI(
    title=settings.application.app_name,
    description="A personal blog assistant API with authentication and authorization",
    version="1.0.0",
    debug=settings.application.debug,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.application.cors_origins,
    allow_credentials=settings.application.cors_credentials,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(users.router)
app.include_router(comments.router)


@app.get("/")
async def root():
    """Root endpoint - health check"""
    return {
        "message": "Personal Blog Assistant API",
        "version": "1.0.0",
        "status": "running"
    }


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "environment": settings.application.environment
    }


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.application.debug
    )
