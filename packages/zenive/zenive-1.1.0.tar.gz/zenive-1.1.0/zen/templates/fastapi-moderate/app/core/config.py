"""
Configuration settings for the FastAPI application.
"""
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=False
    )
    
    # Application
    project_name: str = "{{project_name}}"
    version: str = "1.0.0"
    description: str = "FastAPI application with authentication and database"
    debug: bool = False
    
    # Security
    secret_key: str = Field(default="{{secret_key}}", description="Secret key for JWT tokens")
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    refresh_token_expire_days: int = 7
    
    # Database
    database_url: str = Field(
        default="{{database_url}}",
        description="Database URL"
    )
    database_echo: bool = False
    
    # Redis
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis URL for caching"
    )
    
    # CORS
    backend_cors_origins: list[str] = ["http://localhost:3000", "http://localhost:8080"]
    
    # API
    api_v1_str: str = "/api/v1"


# Global settings instance
settings = Settings()