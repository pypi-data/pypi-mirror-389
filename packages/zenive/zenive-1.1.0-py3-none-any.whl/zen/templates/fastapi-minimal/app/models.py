"""
Pydantic models for {{project_name}}

This module contains all the data models used throughout the application.
"""

from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional


class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = Field(description="Health status of the application")
    environment: str = Field(description="Current environment")
    debug: bool = Field(description="Debug mode status")


class ErrorResponse(BaseModel):
    """Error response model."""
    error: str = Field(description="Error type")
    message: str = Field(description="Error message")


class ItemBase(BaseModel):
    """Base item model with common fields."""
    name: str = Field(min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    price: float = Field(gt=0, description="Item price (must be positive)")

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: str) -> str:
        if not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip()

    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v: float) -> float:
        if v <= 0:
            raise ValueError('Price must be positive')
        return round(v, 2)


class ItemCreate(ItemBase):
    """Model for creating new items."""
    pass


class ItemResponse(ItemBase):
    """Model for item responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int = Field(description="Unique item identifier")
    is_active: bool = Field(True, description="Whether the item is active")


class ItemUpdate(BaseModel):
    """Model for updating existing items."""
    name: Optional[str] = Field(None, min_length=1, max_length=100, description="Item name")
    description: Optional[str] = Field(None, max_length=500, description="Item description")
    price: Optional[float] = Field(None, gt=0, description="Item price (must be positive)")
    is_active: Optional[bool] = Field(None, description="Whether the item is active")

    @field_validator('name')
    @classmethod
    def name_must_not_be_empty(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError('Name cannot be empty or whitespace only')
        return v.strip() if v else v

    @field_validator('price')
    @classmethod
    def price_must_be_positive(cls, v: Optional[float]) -> Optional[float]:
        if v is not None and v <= 0:
            raise ValueError('Price must be positive')
        return round(v, 2) if v else v