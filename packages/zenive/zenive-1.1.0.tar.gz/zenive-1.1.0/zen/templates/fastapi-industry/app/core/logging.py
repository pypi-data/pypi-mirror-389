"""
Structured logging configuration for FastAPI Industry Template.

Provides JSON-formatted logging with correlation IDs, performance metrics,
and integration with monitoring systems.
"""

import logging
import sys
from typing import Any, Dict

import structlog
from pythonjsonlogger import jsonlogger

from app.core.config import settings


def setup_logging() -> None:
    """
    Configure structured logging with JSON format and correlation IDs.
    
    Sets up:
    - JSON formatted logs for production
    - Colored console logs for development
    - Correlation ID tracking
    - Performance metrics
    - Error context capture
    """
    
    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )
    
    # Disable uvicorn access logs (we'll handle them in middleware)
    logging.getLogger("uvicorn.access").disabled = True
    
    # Configure structlog
    processors = [
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]
    
    if settings.LOG_FORMAT == "json":
        # Production JSON logging
        processors.append(structlog.processors.JSONRenderer())
    else:
        # Development console logging with colors
        processors.extend([
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    
    structlog.configure(
        processors=processors,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )


class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to log records."""
    
    def filter(self, record: logging.LogRecord) -> bool:
        """Add correlation ID to the log record."""
        # This will be set by middleware
        correlation_id = getattr(record, 'correlation_id', None)
        if not correlation_id:
            record.correlation_id = "no-correlation-id"
        return True


class PerformanceLogger:
    """Logger for performance metrics and monitoring."""
    
    def __init__(self):
        self.logger = structlog.get_logger("performance")
    
    def log_request_performance(
        self,
        method: str,
        path: str,
        status_code: int,
        duration: float,
        correlation_id: str,
        user_id: str = None,
        **kwargs
    ) -> None:
        """Log request performance metrics."""
        self.logger.info(
            "Request completed",
            method=method,
            path=path,
            status_code=status_code,
            duration_ms=round(duration * 1000, 2),
            correlation_id=correlation_id,
            user_id=user_id,
            **kwargs
        )
    
    def log_database_query(
        self,
        query_type: str,
        table: str,
        duration: float,
        correlation_id: str,
        **kwargs
    ) -> None:
        """Log database query performance."""
        self.logger.info(
            "Database query executed",
            query_type=query_type,
            table=table,
            duration_ms=round(duration * 1000, 2),
            correlation_id=correlation_id,
            **kwargs
        )
    
    def log_cache_operation(
        self,
        operation: str,
        key: str,
        hit: bool,
        duration: float,
        correlation_id: str,
        **kwargs
    ) -> None:
        """Log cache operation metrics."""
        self.logger.info(
            "Cache operation",
            operation=operation,
            key=key,
            hit=hit,
            duration_ms=round(duration * 1000, 2),
            correlation_id=correlation_id,
            **kwargs
        )


class SecurityLogger:
    """Logger for security events and audit trails."""
    
    def __init__(self):
        self.logger = structlog.get_logger("security")
    
    def log_authentication_attempt(
        self,
        email: str,
        success: bool,
        ip_address: str,
        user_agent: str,
        correlation_id: str,
        **kwargs
    ) -> None:
        """Log authentication attempts."""
        self.logger.info(
            "Authentication attempt",
            email=email,
            success=success,
            ip_address=ip_address,
            user_agent=user_agent,
            correlation_id=correlation_id,
            **kwargs
        )
    
    def log_authorization_failure(
        self,
        user_id: str,
        resource: str,
        action: str,
        ip_address: str,
        correlation_id: str,
        **kwargs
    ) -> None:
        """Log authorization failures."""
        self.logger.warning(
            "Authorization failure",
            user_id=user_id,
            resource=resource,
            action=action,
            ip_address=ip_address,
            correlation_id=correlation_id,
            **kwargs
        )
    
    def log_suspicious_activity(
        self,
        activity_type: str,
        details: Dict[str, Any],
        ip_address: str,
        correlation_id: str,
        **kwargs
    ) -> None:
        """Log suspicious activities."""
        self.logger.warning(
            "Suspicious activity detected",
            activity_type=activity_type,
            details=details,
            ip_address=ip_address,
            correlation_id=correlation_id,
            **kwargs
        )


class BusinessLogger:
    """Logger for business events and metrics."""
    
    def __init__(self):
        self.logger = structlog.get_logger("business")
    
    def log_user_action(
        self,
        user_id: str,
        action: str,
        resource: str,
        correlation_id: str,
        **kwargs
    ) -> None:
        """Log user business actions."""
        self.logger.info(
            "User action",
            user_id=user_id,
            action=action,
            resource=resource,
            correlation_id=correlation_id,
            **kwargs
        )
    
    def log_business_metric(
        self,
        metric_name: str,
        value: float,
        unit: str,
        correlation_id: str,
        **kwargs
    ) -> None:
        """Log business metrics."""
        self.logger.info(
            "Business metric",
            metric_name=metric_name,
            value=value,
            unit=unit,
            correlation_id=correlation_id,
            **kwargs
        )


# Create logger instances
performance_logger = PerformanceLogger()
security_logger = SecurityLogger()
business_logger = BusinessLogger()