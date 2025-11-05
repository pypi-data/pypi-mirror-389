"""
Dependency injection for FastAPI endpoints.
"""
from typing import Generator, Optional
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from ..core.database import get_db
from ..core.security import verify_token
from ..crud.user import user_crud
from ..models.user import User, UserRole

# Security scheme for JWT tokens
security = HTTPBearer()


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db)
) -> User:
    """
    Get the current authenticated user from JWT token.
    
    Args:
        credentials: The HTTP authorization credentials
        db: Database session
        
    Returns:
        The current user
        
    Raises:
        HTTPException: If token is invalid or user not found
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    
    # Verify the token
    payload = verify_token(credentials.credentials)
    if payload is None:
        raise credentials_exception
    
    # Get user ID from token
    user_id: str = payload.get("sub")
    if user_id is None:
        raise credentials_exception
    
    # Get user from database
    user = await user_crud.get(db, id=int(user_id))
    if user is None:
        raise credentials_exception
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    return user


async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """
    Get the current active user.
    
    Args:
        current_user: The current user from token
        
    Returns:
        The current active user
        
    Raises:
        HTTPException: If user is inactive
    """
    if not current_user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    return current_user


async def get_current_admin_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current user if they are an admin.
    
    Args:
        current_user: The current active user
        
    Returns:
        The current admin user
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user.is_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


async def get_current_moderator_user(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """
    Get the current user if they can access admin features.
    
    Args:
        current_user: The current active user
        
    Returns:
        The current user with admin access
        
    Raises:
        HTTPException: If user cannot access admin features
    """
    if not current_user.can_access_admin():
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not enough permissions"
        )
    return current_user


def require_role(required_role: UserRole):
    """
    Dependency factory for role-based access control.
    
    Args:
        required_role: The required user role
        
    Returns:
        A dependency function that checks user role
    """
    async def check_role(current_user: User = Depends(get_current_active_user)) -> User:
        if not current_user.has_role(required_role) and not current_user.is_admin():
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Role '{required_role}' required"
            )
        return current_user
    
    return check_role