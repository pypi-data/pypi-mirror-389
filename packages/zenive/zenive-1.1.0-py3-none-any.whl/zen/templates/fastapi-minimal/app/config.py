"""
Configuration management for {{project_name}}

This module handles all application configuration using environment variables
with sensible defaults for development.
"""

import os
from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False
    )
    
    # Application settings
    app_name: str = Field(default="{{project_name}}")
    environment: str = Field(default="development")
    debug: bool = Field(default=True)
    
    # Server settings
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8000)
    
    # Logging
    log_level: str = Field(default="INFO")
    
    # CORS settings
    allowed_origins: List[str] = Field(
        default=["http://localhost:3000", "http://127.0.0.1:3000"]
    )
    
    # Database (for future use)
    database_url: str = Field(default="sqlite:///./app.db")
    
    # Security (for future use)
    secret_key: str = Field(default="your-secret-key-change-in-production")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        
        # Parse comma-separated ALLOWED_ORIGINS if provided as string
        if isinstance(self.allowed_origins, str):
            self.allowed_origins = [origin.strip() for origin in self.allowed_origins.split(",")]
        
        # Convert string boolean values
        if isinstance(self.debug, str):
            self.debug = self.debug.lower() in ("true", "1", "yes", "on")


# Create global settings instance
settings = Settings()