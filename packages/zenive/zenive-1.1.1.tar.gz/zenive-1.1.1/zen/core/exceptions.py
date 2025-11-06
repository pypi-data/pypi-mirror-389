"""
Custom exceptions for Zenive.
"""


class ZeniveError(Exception):
    """Base exception for all Zenive errors."""
    
    def __init__(self, message: str, details: dict = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}


class ComponentNotFoundError(ZeniveError):
    """Raised when a component cannot be found in the registry."""
    
    def __init__(self, component_path: str, details: dict = None):
        message = f"Component '{component_path}' not found in registry"
        super().__init__(message, details)
        self.component_path = component_path


class RegistryError(ZeniveError):
    """Raised when there's an issue communicating with the registry."""
    
    def __init__(self, message: str, status_code: int = None, details: dict = None):
        super().__init__(message, details)
        self.status_code = status_code


class ConfigurationError(ZeniveError):
    """Raised when there's an issue with configuration."""
    
    def __init__(self, message: str, config_path: str = None, details: dict = None):
        super().__init__(message, details)
        self.config_path = config_path


class InstallationError(ZeniveError):
    """Raised when component installation fails."""
    
    def __init__(self, message: str, component_path: str = None, details: dict = None):
        super().__init__(message, details)
        self.component_path = component_path


class ValidationError(ZeniveError):
    """Raised when component or configuration validation fails."""
    
    def __init__(self, message: str, validation_errors: list = None, details: dict = None):
        super().__init__(message, details)
        self.validation_errors = validation_errors or []


class DependencyConflictError(ZeniveError):
    """Raised when there are dependency conflicts during installation."""
    
    def __init__(self, message: str, conflicts: list = None, details: dict = None):
        super().__init__(message, details)
        self.conflicts = conflicts or []


class PermissionError(ZeniveError):
    """Raised when there are permission issues during file operations."""
    
    def __init__(self, message: str, file_path: str = None, details: dict = None):
        super().__init__(message, details)
        self.file_path = file_path


class NetworkError(ZeniveError):
    """Raised when there are network connectivity issues."""
    
    def __init__(self, message: str, endpoint: str = None, details: dict = None):
        super().__init__(message, details)
        self.endpoint = endpoint



