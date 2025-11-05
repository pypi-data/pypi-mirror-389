"""
User schemas for request/response validation.
"""
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from ..models.user import UserRole


class UserBase(BaseModel):
    """Base user schema with common fields."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: bool = True
    role: UserRole = UserRole.USER


class UserCreate(BaseModel):
    """Schema for user creation."""
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    password: str = Field(..., min_length=8, max_length=100)
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "username": "johndoe",
                "full_name": "John Doe",
                "password": "securepassword123"
            }
        }
    )


class UserUpdate(BaseModel):
    """Schema for user updates."""
    email: Optional[EmailStr] = None
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None
    role: Optional[UserRole] = None


class UserPasswordUpdate(BaseModel):
    """Schema for password updates."""
    current_password: str
    new_password: str = Field(..., min_length=8, max_length=100)


class UserResponse(UserBase):
    """Schema for user responses."""
    id: int
    is_verified: bool
    created_at: datetime
    updated_at: datetime
    last_login: Optional[datetime] = None
    
    model_config = ConfigDict(from_attributes=True)


class UserLogin(BaseModel):
    """Schema for user login."""
    email: EmailStr
    password: str
    
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "email": "user@example.com",
                "password": "securepassword123"
            }
        }
    )


class TokenResponse(BaseModel):
    """Schema for token responses."""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int = 1800  # 30 minutes in seconds


class TokenRefresh(BaseModel):
    """Schema for token refresh requests."""
    refresh_token: str


class UserProfile(BaseModel):
    """Schema for user profile information."""
    id: int
    email: EmailStr
    username: str
    full_name: Optional[str]
    role: UserRole
    is_verified: bool
    created_at: datetime
    last_login: Optional[datetime]
    
    model_config = ConfigDict(from_attributes=True)