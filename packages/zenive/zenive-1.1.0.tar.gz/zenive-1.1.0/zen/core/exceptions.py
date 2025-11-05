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


# Template System Exceptions

class TemplateError(ZeniveError):
    """Base exception for template system errors."""
    
    def __init__(self, message: str, template_name: str = None, details: dict = None):
        super().__init__(message, details)
        self.template_name = template_name


class TemplateNotFoundError(TemplateError):
    """Raised when a template is not found in the registry."""
    
    def __init__(self, template_name: str, details: dict = None):
        message = f"Template '{template_name}' not found in registry"
        super().__init__(message, template_name, details)


class TemplateInheritanceError(TemplateError):
    """Raised when template inheritance resolution fails."""
    
    def __init__(self, message: str, template_name: str = None, parent_template: str = None, details: dict = None):
        super().__init__(message, template_name, details)
        self.parent_template = parent_template


class ProjectCreationError(TemplateError):
    """Raised when project creation from template fails."""
    
    def __init__(self, message: str, project_name: str = None, template_name: str = None, details: dict = None):
        super().__init__(message, template_name, details)
        self.project_name = project_name


class TemplateValidationError(TemplateError):
    """Raised when template schema validation fails."""
    
    def __init__(self, message: str, template_name: str = None, validation_errors: list = None, details: dict = None):
        super().__init__(message, template_name, details)
        self.validation_errors = validation_errors or []


class TemplateVariableError(TemplateError):
    """Raised when template variable validation or substitution fails."""
    
    def __init__(self, message: str, template_name: str = None, variable_name: str = None, details: dict = None):
        super().__init__(message, template_name, details)
        self.variable_name = variable_name
