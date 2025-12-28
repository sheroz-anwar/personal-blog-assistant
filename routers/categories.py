"""
API router for managing blog post categories.
Provides endpoints for CRUD operations on blog post categories.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Initialize router
router = APIRouter(
    prefix="/api/categories",
    tags=["categories"],
    responses={404: {"description": "Category not found"}}
)


# ============================================================================
# Pydantic Models
# ============================================================================

class CategoryBase(BaseModel):
    """Base category model with common fields."""
    name: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    is_active: bool = True

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Technology",
                "description": "Posts about technology and software development",
                "slug": "technology",
                "color": "#FF5733",
                "is_active": True
            }
        }


class CategoryCreate(CategoryBase):
    """Model for creating a new category."""
    pass


class CategoryUpdate(BaseModel):
    """Model for updating a category."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    description: Optional[str] = Field(None, max_length=500)
    slug: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = Field(None, regex="^#[0-9A-Fa-f]{6}$")
    is_active: Optional[bool] = None

    class Config:
        json_schema_extra = {
            "example": {
                "name": "Technology",
                "is_active": True
            }
        }


class Category(CategoryBase):
    """Complete category model with metadata."""
    id: int = Field(..., description="Unique category ID")
    post_count: int = Field(default=0, description="Number of posts in this category")
    created_at: datetime
    updated_at: datetime

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "name": "Technology",
                "description": "Posts about technology and software development",
                "slug": "technology",
                "color": "#FF5733",
                "is_active": True,
                "post_count": 5,
                "created_at": "2025-12-28T14:25:53",
                "updated_at": "2025-12-28T14:25:53"
            }
        }


# ============================================================================
# In-memory storage (replace with database in production)
# ============================================================================

# Mock database for demonstration
categories_db = {}
category_counter = 1


# ============================================================================
# Helper Functions
# ============================================================================

def generate_slug(name: str) -> str:
    """Generate a URL-friendly slug from a category name."""
    return name.lower().replace(" ", "-").replace("_", "-")


def get_category_or_404(category_id: int):
    """Get a category by ID or raise 404 error."""
    if category_id not in categories_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Category with ID {category_id} not found"
        )
    return categories_db[category_id]


# ============================================================================
# API Endpoints
# ============================================================================

@router.get(
    "",
    response_model=List[Category],
    summary="List all categories",
    description="Retrieve a list of all blog post categories with optional filtering"
)
async def list_categories(
    skip: int = Query(0, ge=0, description="Number of categories to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of categories to return"),
    is_active: Optional[bool] = Query(None, description="Filter by active status"),
    search: Optional[str] = Query(None, min_length=1, description="Search categories by name or slug")
) -> List[Category]:
    """
    List all categories with optional filtering.
    
    Query Parameters:
    - skip: Number of records to skip (pagination)
    - limit: Maximum number of records to return (default: 10, max: 100)
    - is_active: Filter by active status (true/false)
    - search: Search by category name or slug
    """
    results = list(categories_db.values())
    
    # Apply filters
    if is_active is not None:
        results = [c for c in results if c["is_active"] == is_active]
    
    if search:
        search_lower = search.lower()
        results = [
            c for c in results 
            if search_lower in c["name"].lower() or search_lower in c.get("slug", "").lower()
        ]
    
    # Apply pagination
    return results[skip : skip + limit]


@router.get(
    "/{category_id}",
    response_model=Category,
    summary="Get a specific category",
    description="Retrieve details of a specific category by ID"
)
async def get_category(category_id: int) -> Category:
    """Get a specific category by ID."""
    return get_category_or_404(category_id)


@router.post(
    "",
    response_model=Category,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new category",
    description="Create a new blog post category"
)
async def create_category(category_data: CategoryCreate) -> Category:
    """
    Create a new blog post category.
    
    Request body should include:
    - name (required): Category name
    - description (optional): Category description
    - slug (optional): URL-friendly slug (auto-generated if not provided)
    - color (optional): Hex color code for the category
    - is_active (optional): Whether the category is active
    """
    global category_counter
    
    # Generate slug if not provided
    slug = category_data.slug or generate_slug(category_data.name)
    
    # Check for duplicate slug
    for cat in categories_db.values():
        if cat["slug"] == slug:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Category with slug '{slug}' already exists"
            )
    
    category_id = category_counter
    category_counter += 1
    
    now = datetime.utcnow()
    new_category = {
        "id": category_id,
        "name": category_data.name,
        "description": category_data.description,
        "slug": slug,
        "color": category_data.color,
        "is_active": category_data.is_active,
        "post_count": 0,
        "created_at": now,
        "updated_at": now
    }
    
    categories_db[category_id] = new_category
    return new_category


@router.put(
    "/{category_id}",
    response_model=Category,
    summary="Update a category",
    description="Update an existing blog post category"
)
async def update_category(
    category_id: int,
    category_data: CategoryUpdate
) -> Category:
    """
    Update a specific category.
    
    Path Parameters:
    - category_id: ID of the category to update
    
    Request body can include any of:
    - name: Updated category name
    - description: Updated category description
    - slug: Updated URL-friendly slug
    - color: Updated hex color code
    - is_active: Updated active status
    """
    category = get_category_or_404(category_id)
    
    # Validate slug uniqueness if being updated
    if category_data.slug and category_data.slug != category["slug"]:
        for cat_id, cat in categories_db.items():
            if cat_id != category_id and cat["slug"] == category_data.slug:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Category with slug '{category_data.slug}' already exists"
                )
    
    # Update fields
    if category_data.name is not None:
        category["name"] = category_data.name
        # Auto-update slug if name changed and slug wasn't explicitly provided
        if not category_data.slug:
            category["slug"] = generate_slug(category_data.name)
    
    if category_data.description is not None:
        category["description"] = category_data.description
    
    if category_data.slug is not None:
        category["slug"] = category_data.slug
    
    if category_data.color is not None:
        category["color"] = category_data.color
    
    if category_data.is_active is not None:
        category["is_active"] = category_data.is_active
    
    category["updated_at"] = datetime.utcnow()
    
    return category


@router.delete(
    "/{category_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a category",
    description="Delete a blog post category"
)
async def delete_category(category_id: int):
    """
    Delete a specific category.
    
    Path Parameters:
    - category_id: ID of the category to delete
    
    Returns: No content (204 status code)
    """
    category = get_category_or_404(category_id)
    
    # Check if category has posts
    if category["post_count"] > 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Cannot delete category with {category['post_count']} associated posts. "
                   "Please reassign or delete the posts first."
        )
    
    del categories_db[category_id]


@router.get(
    "/{category_id}/posts",
    summary="Get posts in a category",
    description="Retrieve all blog posts in a specific category"
)
async def get_category_posts(
    category_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100)
):
    """
    Get all posts in a specific category.
    
    Path Parameters:
    - category_id: ID of the category
    
    Query Parameters:
    - skip: Number of posts to skip
    - limit: Maximum number of posts to return
    
    Note: Returns empty list if no posts found (actual implementation would fetch from posts table)
    """
    category = get_category_or_404(category_id)
    
    return {
        "category_id": category_id,
        "category_name": category["name"],
        "posts": [],  # Placeholder - would be populated from posts table in real implementation
        "total": category["post_count"]
    }


@router.post(
    "/{category_id}/activate",
    response_model=Category,
    summary="Activate a category",
    description="Activate a deactivated blog post category"
)
async def activate_category(category_id: int) -> Category:
    """Activate a category."""
    category = get_category_or_404(category_id)
    category["is_active"] = True
    category["updated_at"] = datetime.utcnow()
    return category


@router.post(
    "/{category_id}/deactivate",
    response_model=Category,
    summary="Deactivate a category",
    description="Deactivate a blog post category"
)
async def deactivate_category(category_id: int) -> Category:
    """Deactivate a category."""
    category = get_category_or_404(category_id)
    category["is_active"] = False
    category["updated_at"] = datetime.utcnow()
    return category
