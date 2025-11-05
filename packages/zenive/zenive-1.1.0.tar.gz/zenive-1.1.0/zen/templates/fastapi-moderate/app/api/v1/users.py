"""
User management endpoints.
"""
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...crud.user import user_crud
from ...schemas.user import (
    UserResponse, UserUpdate, UserPasswordUpdate, UserProfile
)
from ..dependencies import (
    get_current_active_user, get_current_admin_user, 
    get_current_moderator_user
)
from ...models.user import User

router = APIRouter()


@router.get("/me", response_model=UserProfile)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user's profile information.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        Current user's profile
    """
    return current_user


@router.put("/me", response_model=UserResponse)
async def update_current_user(
    user_update: UserUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's information.
    
    Args:
        user_update: User update data
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        Updated user information
    """
    # Check if email is being updated and if it's already taken
    if user_update.email and user_update.email != current_user.email:
        existing_user = await user_crud.get_by_email(db, email=user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if username is being updated and if it's already taken
    if user_update.username and user_update.username != current_user.username:
        existing_user = await user_crud.get_by_username(db, username=user_update.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    # Update user
    updated_user = await user_crud.update(db, db_obj=current_user, obj_in=user_update)
    return updated_user


@router.put("/me/password")
async def update_current_user_password(
    password_update: UserPasswordUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update current user's password.
    
    Args:
        password_update: Password update data
        current_user: The current authenticated user
        db: Database session
        
    Returns:
        Success message
    """
    from ...core.security import verify_password
    
    # Verify current password
    if not verify_password(password_update.current_password, current_user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect current password"
        )
    
    # Update password
    await user_crud.update_password(db, user=current_user, new_password=password_update.new_password)
    
    return {"message": "Password updated successfully"}


@router.get("/", response_model=List[UserResponse])
async def get_users(
    skip: int = Query(0, ge=0, description="Number of users to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Number of users to return"),
    current_user: User = Depends(get_current_moderator_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get list of users (admin/moderator only).
    
    Args:
        skip: Number of users to skip
        limit: Maximum number of users to return
        current_user: The current authenticated user (must be admin/moderator)
        db: Database session
        
    Returns:
        List of users
    """
    users = await user_crud.get_multi(db, skip=skip, limit=limit)
    return users


@router.get("/{user_id}", response_model=UserResponse)
async def get_user_by_id(
    user_id: int,
    current_user: User = Depends(get_current_moderator_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Get user by ID (admin/moderator only).
    
    Args:
        user_id: User ID
        current_user: The current authenticated user (must be admin/moderator)
        db: Database session
        
    Returns:
        User information
        
    Raises:
        HTTPException: If user not found
    """
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    return user


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Update user by ID (admin only).
    
    Args:
        user_id: User ID
        user_update: User update data
        current_user: The current authenticated user (must be admin)
        db: Database session
        
    Returns:
        Updated user information
        
    Raises:
        HTTPException: If user not found
    """
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if email is being updated and if it's already taken
    if user_update.email and user_update.email != user.email:
        existing_user = await user_crud.get_by_email(db, email=user_update.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
    
    # Check if username is being updated and if it's already taken
    if user_update.username and user_update.username != user.username:
        existing_user = await user_crud.get_by_username(db, username=user_update.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Username already taken"
            )
    
    updated_user = await user_crud.update(db, db_obj=user, obj_in=user_update)
    return updated_user


@router.delete("/{user_id}")
async def delete_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Delete user by ID (admin only).
    
    Args:
        user_id: User ID
        current_user: The current authenticated user (must be admin)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or trying to delete self
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot delete your own account"
        )
    
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user_crud.remove(db, id=user_id)
    return {"message": "User deleted successfully"}


@router.post("/{user_id}/activate")
async def activate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Activate user account (admin only).
    
    Args:
        user_id: User ID
        current_user: The current authenticated user (must be admin)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found
    """
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user_crud.activate_user(db, user=user)
    return {"message": "User activated successfully"}


@router.post("/{user_id}/deactivate")
async def deactivate_user(
    user_id: int,
    current_user: User = Depends(get_current_admin_user),
    db: AsyncSession = Depends(get_db)
):
    """
    Deactivate user account (admin only).
    
    Args:
        user_id: User ID
        current_user: The current authenticated user (must be admin)
        db: Database session
        
    Returns:
        Success message
        
    Raises:
        HTTPException: If user not found or trying to deactivate self
    """
    if user_id == current_user.id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot deactivate your own account"
        )
    
    user = await user_crud.get(db, id=user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    await user_crud.deactivate_user(db, user=user)
    return {"message": "User deactivated successfully"}