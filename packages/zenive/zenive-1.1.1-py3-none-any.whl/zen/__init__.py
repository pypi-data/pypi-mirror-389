"""
zen - A component registry for discovering, installing, and managing reusable code components
"""

__version__ = "1.1.1"
__author__ = "TheRaj71"
__description__ = "A component registry for discovering, installing, and managing reusable code components"

# Core imports
from zen.core.exceptions import InstallationError, ConfigurationError
from zen.schemas.component import ComponentSchema, load_component_from_json, load_component_from_url

__all__ = [
    "InstallationError",
    "ConfigurationError", 
    "ComponentSchema",
    "load_component_from_json",
    "load_component_from_url"
]
