"""
Comments Router Module

This module provides API endpoints for managing comments on blog posts.
It includes endpoints for creating, reading, updating, and deleting comments.
"""

from fastapi import APIRouter, HTTPException, Depends, status, Query
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# Import your database models and schemas
# Adjust imports based on your project structure
from models import Comment, Post, User  # Update import path as needed
from schemas import CommentCreate, CommentUpdate, CommentResponse  # Update import path as needed
from database import get_db  # Update import path as needed
from auth import get_current_user  # Update import path as needed

router = APIRouter(
    prefix="/api/posts/{post_id}/comments",
    tags=["comments"],
    responses={404: {"description": "Not found"}},
)


@router.post(
    "",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new comment",
    description="Create a new comment on a specific post"
)
def create_comment(
    post_id: int,
    comment: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new comment on a post.
    
    Args:
        post_id: The ID of the post to comment on
        comment: CommentCreate schema with comment content
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        CommentResponse: The created comment
        
    Raises:
        HTTPException: If post not found or user not authenticated
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    # Create new comment
    new_comment = Comment(
        content=comment.content,
        post_id=post_id,
        author_id=current_user.id,
        created_at=datetime.utcnow(),
        updated_at=datetime.utcnow(),
    )
    
    db.add(new_comment)
    db.commit()
    db.refresh(new_comment)
    
    return new_comment


@router.get(
    "",
    response_model=List[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get all comments for a post",
    description="Retrieve all comments for a specific post with optional pagination"
)
def get_post_comments(
    post_id: int,
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(10, ge=1, le=100, description="Maximum number of records to return"),
    sort_by: str = Query("created_at", description="Field to sort by (created_at, updated_at)"),
    order: str = Query("desc", regex="^(asc|desc)$", description="Sort order"),
    db: Session = Depends(get_db),
):
    """
    Get all comments for a specific post.
    
    Args:
        post_id: The ID of the post
        skip: Number of records to skip for pagination
        limit: Maximum number of records to return
        sort_by: Field to sort by
        order: Sort order (asc or desc)
        db: Database session
        
    Returns:
        List[CommentResponse]: List of comments for the post
        
    Raises:
        HTTPException: If post not found
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    # Build query
    query = db.query(Comment).filter(Comment.post_id == post_id)
    
    # Apply sorting
    if sort_by == "created_at":
        query = query.order_by(Comment.created_at.desc() if order == "desc" else Comment.created_at.asc())
    elif sort_by == "updated_at":
        query = query.order_by(Comment.updated_at.desc() if order == "desc" else Comment.updated_at.asc())
    
    # Apply pagination
    comments = query.offset(skip).limit(limit).all()
    
    return comments


@router.get(
    "/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Get a specific comment",
    description="Retrieve a specific comment by ID"
)
def get_comment(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
):
    """
    Get a specific comment by ID.
    
    Args:
        post_id: The ID of the post
        comment_id: The ID of the comment
        db: Database session
        
    Returns:
        CommentResponse: The requested comment
        
    Raises:
        HTTPException: If post or comment not found
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    # Get comment
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.post_id == post_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found on post {post_id}"
        )
    
    return comment


@router.put(
    "/{comment_id}",
    response_model=CommentResponse,
    status_code=status.HTTP_200_OK,
    summary="Update a comment",
    description="Update an existing comment (only by author or admin)"
)
def update_comment(
    post_id: int,
    comment_id: int,
    comment_update: CommentUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Update an existing comment.
    
    Args:
        post_id: The ID of the post
        comment_id: The ID of the comment to update
        comment_update: CommentUpdate schema with updated content
        db: Database session
        current_user: Currently authenticated user
        
    Returns:
        CommentResponse: The updated comment
        
    Raises:
        HTTPException: If post/comment not found or user not authorized
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    # Get comment
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.post_id == post_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found on post {post_id}"
        )
    
    # Check authorization (only author or admin can update)
    if comment.author_id != current_user.id and not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to update this comment"
        )
    
    # Update comment
    if comment_update.content:
        comment.content = comment_update.content
    comment.updated_at = datetime.utcnow()
    
    db.add(comment)
    db.commit()
    db.refresh(comment)
    
    return comment


@router.delete(
    "/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a comment",
    description="Delete an existing comment (only by author or admin)"
)
def delete_comment(
    post_id: int,
    comment_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Delete an existing comment.
    
    Args:
        post_id: The ID of the post
        comment_id: The ID of the comment to delete
        db: Database session
        current_user: Currently authenticated user
        
    Raises:
        HTTPException: If post/comment not found or user not authorized
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    # Get comment
    comment = db.query(Comment).filter(
        Comment.id == comment_id,
        Comment.post_id == post_id
    ).first()
    
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comment with id {comment_id} not found on post {post_id}"
        )
    
    # Check authorization (only author or admin can delete)
    if comment.author_id != current_user.id and not getattr(current_user, 'is_admin', False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to delete this comment"
        )
    
    # Delete comment
    db.delete(comment)
    db.commit()


@router.get(
    "/author/{author_id}",
    response_model=List[CommentResponse],
    status_code=status.HTTP_200_OK,
    summary="Get comments by author",
    description="Retrieve all comments by a specific author on a post"
)
def get_comments_by_author(
    post_id: int,
    author_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    Get all comments by a specific author on a post.
    
    Args:
        post_id: The ID of the post
        author_id: The ID of the author
        skip: Number of records to skip
        limit: Maximum number of records to return
        db: Database session
        
    Returns:
        List[CommentResponse]: List of comments by the author on the post
        
    Raises:
        HTTPException: If post not found
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    # Get comments by author
    comments = db.query(Comment).filter(
        Comment.post_id == post_id,
        Comment.author_id == author_id
    ).order_by(Comment.created_at.desc()).offset(skip).limit(limit).all()
    
    return comments


@router.get(
    "/count",
    status_code=status.HTTP_200_OK,
    summary="Get comment count for a post",
    description="Get the total number of comments on a post"
)
def get_comment_count(
    post_id: int,
    db: Session = Depends(get_db),
):
    """
    Get the total number of comments on a post.
    
    Args:
        post_id: The ID of the post
        db: Database session
        
    Returns:
        dict: Dictionary with comment count
        
    Raises:
        HTTPException: If post not found
    """
    # Check if post exists
    post = db.query(Post).filter(Post.id == post_id).first()
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Post with id {post_id} not found"
        )
    
    count = db.query(Comment).filter(Comment.post_id == post_id).count()
    
    return {"post_id": post_id, "comment_count": count}
