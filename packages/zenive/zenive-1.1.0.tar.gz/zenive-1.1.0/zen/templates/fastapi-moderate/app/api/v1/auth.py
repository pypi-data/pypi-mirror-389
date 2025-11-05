"""
Authentication endpoints for user registration, login, and token management.
"""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from ...core.database import get_db
from ...core.security import verify_password, create_token_response, verify_token
from ...crud.user import user_crud
from ...schemas.user import (
    UserCreate, UserResponse, UserLogin, TokenResponse, 
    TokenRefresh, UserProfile
)
from ..dependencies import get_current_active_user
from ...models.user import User

router = APIRouter()


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new user.
    
    Args:
        user_data: User registration data
        db: Database session
        
    Returns:
        The created user
        
    Raises:
        HTTPException: If email or username already exists
    """
    # Check if user already exists
    existing_user = await user_crud.get_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    existing_username = await user_crud.get_by_username(db, username=user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )
    
    # Create new user
    user = await user_crud.create(db, obj_in=user_data)
    return user


@router.post("/login", response_model=TokenResponse)
async def login(
    user_credentials: UserLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login user and return JWT tokens.
    
    Args:
        user_credentials: User login credentials
        db: Database session
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by email
    user = await user_crud.get_by_email(db, email=user_credentials.email)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Verify password
    if not verify_password(user_credentials.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    await user_crud.update_last_login(db, user_id=user.id)
    
    # Create tokens
    token_data = create_token_response(user.id, user.email)
    return TokenResponse(**token_data)


@router.post("/login/oauth2", response_model=TokenResponse)
async def login_oauth2(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db)
):
    """
    OAuth2 compatible login endpoint.
    
    Args:
        form_data: OAuth2 form data
        db: Database session
        
    Returns:
        JWT access and refresh tokens
        
    Raises:
        HTTPException: If credentials are invalid
    """
    # Get user by username (OAuth2 uses username field)
    user = await user_crud.get_by_email(db, email=form_data.username)
    if not user:
        # Try by username if email lookup fails
        user = await user_crud.get_by_username(db, username=form_data.username)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Verify password
    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Update last login
    await user_crud.update_last_login(db, user_id=user.id)
    
    # Create tokens
    token_data = create_token_response(user.id, user.email)
    return TokenResponse(**token_data)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(
    token_data: TokenRefresh,
    db: AsyncSession = Depends(get_db)
):
    """
    Refresh JWT access token using refresh token.
    
    Args:
        token_data: Refresh token data
        db: Database session
        
    Returns:
        New JWT access and refresh tokens
        
    Raises:
        HTTPException: If refresh token is invalid
    """
    # Verify refresh token
    payload = verify_token(token_data.refresh_token, token_type="refresh")
    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user from token
    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )
    
    # Get user from database
    user = await user_crud.get(db, id=int(user_id))
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )
    
    # Create new tokens
    token_response = create_token_response(user.id, user.email)
    return TokenResponse(**token_response)


@router.get("/me", response_model=UserProfile)
async def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
):
    """
    Get current user profile information.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        User profile information
    """
    return current_user


@router.post("/logout")
async def logout():
    """
    Logout user (client should discard tokens).
    
    Returns:
        Success message
    """
    return {"message": "Successfully logged out"}


@router.post("/verify-token")
async def verify_user_token(
    current_user: User = Depends(get_current_active_user)
):
    """
    Verify if the current token is valid.
    
    Args:
        current_user: The current authenticated user
        
    Returns:
        Token validity status and user info
    """
    return {
        "valid": True,
        "user_id": current_user.id,
        "email": current_user.email,
        "role": current_user.role
    }