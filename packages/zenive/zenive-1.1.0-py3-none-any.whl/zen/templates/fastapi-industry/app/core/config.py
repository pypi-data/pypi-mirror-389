"""
Configuration settings for FastAPI Industry Template.

Comprehensive configuration management with environment-based settings,
monitoring configuration, and production-ready defaults.
"""

import secrets
from typing import Any, Dict, List, Optional, Union

from pydantic import AnyHttpUrl, EmailStr, HttpUrl, PostgresDsn, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with comprehensive configuration options."""
    
    model_config = SettingsConfigDict(
        case_sensitive=True,
        env_file=".env"
    )
    
    # Basic application settings
    PROJECT_NAME: str = "{{project_name}}"
    VERSION: str = "1.0.0"
    DESCRIPTION: str = "Enterprise FastAPI application"
    API_V1_STR: str = "/api/v1"
    
    # Environment
    ENVIRONMENT: str = "development"  # development, staging, production
    DEBUG: bool = False
    
    # Security
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 8  # 8 days
    REFRESH_TOKEN_EXPIRE_MINUTES: int = 60 * 24 * 30  # 30 days
    
    # CORS settings
    BACKEND_CORS_ORIGINS: List[AnyHttpUrl] = []
    
    @field_validator("BACKEND_CORS_ORIGINS", mode="before")
    @classmethod
    def assemble_cors_origins(cls, v: Union[str, List[str]]) -> Union[List[str], str]:
        if isinstance(v, str) and not v.startswith("["):
            return [i.strip() for i in v.split(",")]
        elif isinstance(v, (list, str)):
            return v
        raise ValueError(v)
    
    # Database settings
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "password"
    POSTGRES_DB: str = "{{project_name}}_db"
    POSTGRES_PORT: str = "5432"
    DATABASE_URL: Optional[PostgresDsn] = None
    
    @field_validator("DATABASE_URL", mode="before")
    @classmethod
    def assemble_db_connection(cls, v: Optional[str], info) -> Any:
        if isinstance(v, str):
            return v
        # Access other field values through info.data
        values = info.data if hasattr(info, 'data') else {}
        return PostgresDsn.build(
            scheme="postgresql+asyncpg",
            username=values.get("POSTGRES_USER"),
            password=values.get("POSTGRES_PASSWORD"),
            host=values.get("POSTGRES_SERVER"),
            port=int(values.get("POSTGRES_PORT", 5432)),
            path=values.get('POSTGRES_DB') or '',
        )
    
    # Redis settings
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 300  # 5 minutes default TTL
    
    # Celery settings
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # Monitoring and Observability
    SENTRY_DSN: Optional[HttpUrl] = None
    SENTRY_TRACES_SAMPLE_RATE: float = 0.1
    
    # Prometheus metrics
    METRICS_ENABLED: bool = True
    METRICS_PATH: str = "/metrics"
    
    # Logging configuration
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"  # json or text
    LOG_FILE: Optional[str] = None
    
    # Rate limiting
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS: int = 100
    RATE_LIMIT_WINDOW: int = 60  # seconds
    
    # Security headers
    SECURITY_HEADERS_ENABLED: bool = True
    
    # Health check settings
    HEALTH_CHECK_TIMEOUT: int = 30
    
    # Email settings (for notifications)
    SMTP_TLS: bool = True
    SMTP_PORT: Optional[int] = None
    SMTP_HOST: Optional[str] = None
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    EMAILS_FROM_EMAIL: Optional[EmailStr] = None
    EMAILS_FROM_NAME: Optional[str] = None
    
    @field_validator("EMAILS_FROM_NAME", mode="before")
    @classmethod
    def get_project_name(cls, v: Optional[str], info) -> str:
        if not v:
            values = info.data if hasattr(info, 'data') else {}
            return values.get("PROJECT_NAME", "{{project_name}}")
        return v
    
    # Admin user settings
    FIRST_SUPERUSER: EmailStr = "admin@{{project_name}}.com"
    FIRST_SUPERUSER_PASSWORD: str = "changethis"
    
    # API settings
    API_RATE_LIMIT: str = "1000/hour"
    API_KEY_HEADER: str = "X-API-Key"
    
    # File upload settings
    MAX_UPLOAD_SIZE: int = 10 * 1024 * 1024  # 10MB
    ALLOWED_UPLOAD_EXTENSIONS: List[str] = [".jpg", ".jpeg", ".png", ".gif", ".pdf"]
    
    # Cache settings
    CACHE_ENABLED: bool = True
    CACHE_DEFAULT_TTL: int = 300
    
    # Background tasks
    BACKGROUND_TASKS_ENABLED: bool = True
    
    # Feature flags
    FEATURE_FLAGS: Dict[str, bool] = {
        "new_user_registration": True,
        "email_verification": True,
        "two_factor_auth": False,
        "api_versioning": True,
    }
    
    # Performance settings
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_TIMEOUT: int = 30
    
    # Kubernetes settings
    K8S_NAMESPACE: str = "default"
    K8S_SERVICE_NAME: str = "{{project_name}}-api"
    
    # Monitoring URLs
    GRAFANA_URL: Optional[str] = None
    PROMETHEUS_URL: Optional[str] = None
    
    # Compatibility properties for moderate template
    @property
    def database_url(self) -> str:
        """Database URL for compatibility with moderate template."""
        if self.DATABASE_URL:
            return str(self.DATABASE_URL)
        return f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
    
    @property
    def database_echo(self) -> bool:
        """Database echo setting."""
        return self.DEBUG
    
    @property
    def secret_key(self) -> str:
        """Secret key for compatibility."""
        return self.SECRET_KEY
    
    @property
    def project_name(self) -> str:
        """Project name for compatibility."""
        return self.PROJECT_NAME
    
    @property
    def version(self) -> str:
        """Version for compatibility."""
        return self.VERSION
    
    @property
    def api_v1_str(self) -> str:
        """API v1 string for compatibility."""
        return self.API_V1_STR
    
    @property
    def backend_cors_origins(self) -> List[str]:
        """CORS origins for compatibility."""
        return [str(origin) for origin in self.BACKEND_CORS_ORIGINS]


# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings