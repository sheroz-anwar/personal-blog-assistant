"""
Blog Posts API Router

This module provides FastAPI router endpoints for managing blog posts.
Includes CRUD operations: Create, Read, Update, and Delete.
"""

from fastapi import APIRouter, HTTPException, status, Query
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field

# Initialize router
router = APIRouter(prefix="/posts", tags=["posts"])

# ==================== Pydantic Models ====================

class PostBase(BaseModel):
    """Base model for blog post data."""
    title: str = Field(..., min_length=1, max_length=255, description="Post title")
    content: str = Field(..., min_length=1, description="Post content")
    author: str = Field(..., min_length=1, description="Post author name")
    tags: Optional[List[str]] = Field(default=[], description="List of tags for the post")
    is_published: bool = Field(default=False, description="Publication status")

class PostCreate(PostBase):
    """Model for creating a new blog post."""
    pass

class PostUpdate(BaseModel):
    """Model for updating a blog post."""
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    content: Optional[str] = Field(None, min_length=1)
    author: Optional[str] = Field(None, min_length=1)
    tags: Optional[List[str]] = None
    is_published: Optional[bool] = None

class Post(PostBase):
    """Complete blog post model with metadata."""
    id: int = Field(..., description="Unique post identifier")
    created_at: datetime = Field(..., description="Post creation timestamp")
    updated_at: datetime = Field(..., description="Post last update timestamp")

    class Config:
        from_attributes = True


# ==================== In-Memory Database (Demo) ====================
# In production, replace this with actual database

posts_db: dict[int, dict] = {}
post_id_counter = 1


# ==================== Helper Functions ====================

def get_post_by_id(post_id: int) -> dict:
    """Retrieve a post by ID or raise 404 error."""
    if post_id not in posts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found"
        )
    return posts_db[post_id]


# ==================== API Endpoints ====================

@router.post(
    "",
    response_model=Post,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new blog post",
    description="Create a new blog post with the provided title, content, and metadata."
)
async def create_post(post: PostCreate) -> dict:
    """
    Create a new blog post.

    Args:
        post: PostCreate object containing post details

    Returns:
        The newly created post with generated ID and timestamps
    """
    global post_id_counter

    new_post = {
        "id": post_id_counter,
        "title": post.title,
        "content": post.content,
        "author": post.author,
        "tags": post.tags or [],
        "is_published": post.is_published,
        "created_at": datetime.utcnow(),
        "updated_at": datetime.utcnow()
    }

    posts_db[post_id_counter] = new_post
    post_id_counter += 1

    return new_post


@router.get(
    "",
    response_model=List[Post],
    summary="Retrieve all blog posts",
    description="Get all blog posts with optional filtering by author, tags, and publication status."
)
async def get_posts(
    author: Optional[str] = Query(None, description="Filter by author name"),
    tag: Optional[str] = Query(None, description="Filter by tag"),
    published_only: bool = Query(False, description="Only return published posts"),
    skip: int = Query(0, ge=0, description="Number of posts to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of posts to return")
) -> List[dict]:
    """
    Retrieve all blog posts with optional filtering and pagination.

    Args:
        author: Optional author name filter
        tag: Optional tag filter
        published_only: If True, only return published posts
        skip: Number of posts to skip (pagination)
        limit: Maximum number of posts to return

    Returns:
        List of posts matching the filter criteria
    """
    filtered_posts = list(posts_db.values())

    # Apply filters
    if author:
        filtered_posts = [p for p in filtered_posts if p["author"].lower() == author.lower()]

    if tag:
        filtered_posts = [p for p in filtered_posts if tag.lower() in [t.lower() for t in p["tags"]]]

    if published_only:
        filtered_posts = [p for p in filtered_posts if p["is_published"]]

    # Sort by created_at (most recent first)
    filtered_posts.sort(key=lambda x: x["created_at"], reverse=True)

    # Apply pagination
    return filtered_posts[skip:skip + limit]


@router.get(
    "/{post_id}",
    response_model=Post,
    summary="Retrieve a specific blog post",
    description="Get a blog post by its ID."
)
async def get_post(post_id: int) -> dict:
    """
    Retrieve a specific blog post by ID.

    Args:
        post_id: The ID of the post to retrieve

    Returns:
        The requested post

    Raises:
        HTTPException: If post is not found
    """
    return get_post_by_id(post_id)


@router.put(
    "/{post_id}",
    response_model=Post,
    summary="Update a blog post",
    description="Update a blog post's content, title, or other metadata."
)
async def update_post(post_id: int, post_update: PostUpdate) -> dict:
    """
    Update an existing blog post.

    Args:
        post_id: The ID of the post to update
        post_update: PostUpdate object with fields to update

    Returns:
        The updated post

    Raises:
        HTTPException: If post is not found
    """
    existing_post = get_post_by_id(post_id)

    # Update only provided fields
    update_data = post_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        existing_post[field] = value

    # Update the timestamp
    existing_post["updated_at"] = datetime.utcnow()

    posts_db[post_id] = existing_post
    return existing_post


@router.patch(
    "/{post_id}",
    response_model=Post,
    summary="Partially update a blog post",
    description="Partially update a blog post with specific fields."
)
async def partial_update_post(post_id: int, post_update: PostUpdate) -> dict:
    """
    Partially update a blog post (same as PUT for this implementation).

    Args:
        post_id: The ID of the post to update
        post_update: PostUpdate object with fields to update

    Returns:
        The updated post

    Raises:
        HTTPException: If post is not found
    """
    return await update_post(post_id, post_update)


@router.delete(
    "/{post_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a blog post",
    description="Delete a blog post by its ID."
)
async def delete_post(post_id: int) -> None:
    """
    Delete a blog post by ID.

    Args:
        post_id: The ID of the post to delete

    Raises:
        HTTPException: If post is not found
    """
    if post_id not in posts_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with ID {post_id} not found"
        )
    del posts_db[post_id]


@router.get(
    "/{post_id}/publish",
    response_model=Post,
    summary="Publish a blog post",
    description="Publish a blog post by setting its published status to true."
)
async def publish_post(post_id: int) -> dict:
    """
    Publish a blog post.

    Args:
        post_id: The ID of the post to publish

    Returns:
        The published post

    Raises:
        HTTPException: If post is not found
    """
    existing_post = get_post_by_id(post_id)
    existing_post["is_published"] = True
    existing_post["updated_at"] = datetime.utcnow()
    posts_db[post_id] = existing_post
    return existing_post


@router.get(
    "/{post_id}/unpublish",
    response_model=Post,
    summary="Unpublish a blog post",
    description="Unpublish a blog post by setting its published status to false."
)
async def unpublish_post(post_id: int) -> dict:
    """
    Unpublish a blog post.

    Args:
        post_id: The ID of the post to unpublish

    Returns:
        The unpublished post

    Raises:
        HTTPException: If post is not found
    """
    existing_post = get_post_by_id(post_id)
    existing_post["is_published"] = False
    existing_post["updated_at"] = datetime.utcnow()
    posts_db[post_id] = existing_post
    return existing_post
