"""
Registry schema validation.
"""

from typing import List, Dict, Any, Optional
from pydantic import BaseModel, Field

class RegistrySchema(BaseModel):
    """Schema for registry configuration."""
    
    name: str = Field(..., description="Registry name")
    url: str = Field(..., description="Registry URL")
    timeout: int = Field(default=30, description="Request timeout in seconds")
    cache_ttl: int = Field(default=3600, description="Cache TTL in seconds")
    api_key: Optional[str] = Field(None, description="API key for authentication")
    verify_ssl: bool = Field(default=True, description="Verify SSL certificates")
