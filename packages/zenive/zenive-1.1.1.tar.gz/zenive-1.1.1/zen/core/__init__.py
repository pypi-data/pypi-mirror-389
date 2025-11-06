"""
Core functionality for zen.
"""

from zen.core.exceptions import InstallationError, ConfigurationError
from zen.core.logger import get_logger, setup_logging

__all__ = [
    "InstallationError",
    "ConfigurationError", 
    "get_logger",
    "setup_logging"
]
