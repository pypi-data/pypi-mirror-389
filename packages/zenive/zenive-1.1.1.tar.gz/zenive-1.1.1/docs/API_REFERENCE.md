# zen Component Registry API Reference

## Overview

This document provides detailed API reference for the zen component registry system. It covers all classes, methods, and functions available for programmatic use of the component installation and management system.

## Core Classes

### ComponentSchema

Pydantic model representing a component definition.

```python
from zen.schemas.component import ComponentSchema, ComponentFile

class ComponentSchema(BaseModel):
    name: str
    version: str
    description: str
    category: str = "utils"
    dependencies: List[str] = []
    dev_dependencies: List[str] = []
    files: List[ComponentFile] = []
    python_requires: str = ">=3.8"
    author: Optional[str] = None
    license: str = "MIT"
    keywords: List[str] = []
```

**Fields:**
- `name`: Unique component identifier
- `version`: Semantic version string
- `description`: Human-readable description
- `category`: Component category (utils, auth, data, etc.)
- `dependencies`: List of Python package dependencies
- `dev_dependencies`: List of development dependencies
- `files`: List of component files
- `python_requires`: Python version requirement
- `author`: Component author name
- `license`: License identifier
- `keywords`: List of keywords for categorization

### ComponentFile

Represents a file within a component.

```python
class ComponentFile(BaseModel):
    name: str
    path: str
    content: Optional[str] = None
    url: Optional[str] = None
    executable: bool = False
```

**Fields:**
- `name`: Display name of the file
- `path`: Target path in the project
- `content`: Direct file content (optional)
- `url`: URL to fetch content from (optional)
- `executable`: Whether file should be executable

### ComponentRegistry

Manages component discovery, loading, and installation.

```python
from zen.core.component_registry import ComponentRegistry

registry = ComponentRegistry()
```

#### Methods

##### `register_component(component: ComponentSchema) -> None`

Register a component in the registry.

**Parameters:**
- `component`: ComponentSchema instance to register

**Example:**
```python
component = ComponentSchema(
    name="my-component",
    version="1.0.0",
    description="My custom component"
)
registry.register_component(component)
```

##### `get_component(name: str) -> ComponentSchema`

Retrieve a component by name.

**Parameters:**
- `name`: Component name

**Returns:**
- ComponentSchema instance

**Raises:**
- `KeyError`: If component not found

**Example:**
```python
component = registry.get_component("email-validator")
```

##### `list_components() -> List[ComponentSchema]`

Get all registered components.

**Returns:**
- List of ComponentSchema instances

**Example:**
```python
components = registry.list_components()
for component in components:
    print(f"{component.name}: {component.description}")
```

##### `load_from_url(url: str) -> ComponentSchema`

Load component from URL.

**Parameters:**
- `url`: URL to component.json file

**Returns:**
- ComponentSchema instance

**Example:**
```python
component = registry.load_from_url("https://example.com/component.json")
```

### ComponentInstaller

Handles component installation into projects.

```python
from zen.core.component_installer import ComponentInstaller

installer = ComponentInstaller(registry)
```

#### Methods

##### `install_component(component_url: str, **kwargs) -> InstallResult`

Install a component from URL.

**Parameters:**
- `component_url`: URL to component repository or component.json
- `install_path`: Target installation path (optional)
- `install_dependencies`: Whether to install dependencies (default: True)
- `overwrite`: Whether to overwrite existing files (default: False)

**Returns:**
- InstallResult instance with installation details

**Example:**
```python
result = installer.install_component(
    component_url="https://github.com/user/component",
    install_path="src/utils",
    install_dependencies=True
)
```

##### `validate_component_url(url: str) -> List[str]`

Validate component URL format.

**Parameters:**
- `url`: Component URL to validate

**Returns:**
- List of validation issues (empty if valid)

**Example:**
```python
issues = installer.validate_component_url("https://github.com/user/component")
if not issues:
    print("Valid component URL")
```

##### `check_installation_conflicts(component: ComponentSchema, install_path: str) -> List[str]`

Check for potential installation conflicts.

**Parameters:**
- `component`: Component to install
- `install_path`: Target installation path

**Returns:**
- List of potential conflicts

**Example:**
```python
conflicts = installer.check_installation_conflicts(component, "src/utils")
```

### ComponentController

High-level interface for component operations.

```python
from zen.core.component_controller import ComponentController

controller = ComponentController()
```

#### Methods

##### `list_installed_components() -> List[ComponentInfo]`

Get list of installed components with basic information.

**Returns:**
- List of ComponentInfo named tuples

**Example:**
```python
components = controller.list_installed_components()
for component in components:
    print(f"{component.name} ({component.category}): {component.description}")
```

##### `get_component_details(component_name: str) -> ComponentDetails`

Get detailed information about a component.

**Parameters:**
- `component_name`: Name of the component

**Returns:**
- ComponentDetails named tuple

**Raises:**
- `KeyError`: If component not found

**Example:**
```python
details = controller.get_component_details("email-validator")
print(f"Dependencies: {details.dependencies}")
```

##### `install_component_interactive(component_url: str) -> InstallResult`

Install component with interactive prompts.

**Parameters:**
- `component_url`: URL of the component to install

**Returns:**
- InstallResult instance

**Example:**
```python
result = controller.install_component_interactive("https://github.com/user/component")
```

## Validation Classes

### ComponentValidator

Validates component schemas and files.

```python
from zen.core.component_validator import ComponentValidator, ValidationResult

validator = ComponentValidator(registry)
```

#### Methods

##### `validate_component(component: ComponentSchema, component_path: Optional[Path] = None) -> ValidationResult`

Validate a complete component.

**Parameters:**
- `component`: Component schema to validate
- `component_path`: Optional path to component directory

**Returns:**
- ValidationResult instance

**Example:**
```python
result = validator.validate_component(component)
if result.is_valid:
    print("Component is valid")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

##### `validate_schema(component: ComponentSchema) -> ValidationResult`

Validate component schema structure.

**Parameters:**
- `component`: Component schema

**Returns:**
- ValidationResult instance

##### `validate_component_files(component: ComponentSchema, component_path: Path) -> ValidationResult`

Validate component files exist and are accessible.

**Parameters:**
- `component`: Component schema
- `component_path`: Path to component directory

**Returns:**
- ValidationResult instance

### ValidationResult

Contains validation results.

```python
class ValidationResult:
    is_valid: bool
    errors: List[str]
    warnings: List[str]
    info: List[str]
    
    def add_error(self, message: str) -> None
    def add_warning(self, message: str) -> None
    def add_info(self, message: str) -> None
    def merge(self, other: 'ValidationResult') -> None
```

### ComponentTestFramework

Framework for testing components.

```python
from zen.core.component_validator import ComponentTestFramework

test_framework = ComponentTestFramework(registry)
```

#### Methods

##### `test_component(component_name: str, component_path: Optional[Path] = None) -> ValidationResult`

Test a component comprehensively.

**Parameters:**
- `component_name`: Name of component to test
- `component_path`: Optional path to component directory

**Returns:**
- ValidationResult with test results

**Example:**
```python
result = test_framework.test_component("email-validator")
```

##### `test_all_components() -> Dict[str, ValidationResult]`

Test all components in the registry.

**Returns:**
- Dictionary mapping component names to test results

**Example:**
```python
results = test_framework.test_all_components()
for name, result in results.items():
    print(f"{name}: {'✓' if result.is_valid else '✗'}")
```

## Utility Classes

### ComponentIntegrityChecker

Checks component file integrity and consistency.

```python
from zen.core.component_utils import ComponentIntegrityChecker

checker = ComponentIntegrityChecker()
```

#### Methods

##### `check_component_integrity(component_name: str) -> ValidationResult`

Check integrity of a specific component.

**Parameters:**
- `component_name`: Name of component to check

**Returns:**
- ValidationResult with integrity status

##### `generate_component_checksums(component_name: str) -> Dict[str, str]`

Generate checksums for all component files.

**Parameters:**
- `component_name`: Name of component

**Returns:**
- Dictionary mapping file paths to checksums

### ComponentDependencyAnalyzer

Analyzes component dependencies and conflicts.

```python
from zen.core.component_utils import ComponentDependencyAnalyzer

analyzer = ComponentDependencyAnalyzer()
```

#### Methods

##### `analyze_component_dependencies(component_name: str) -> Dict[str, Any]`

Analyze dependencies for a component.

**Parameters:**
- `component_name`: Name of component to analyze

**Returns:**
- Dictionary with dependency analysis results

##### `find_dependency_conflicts_between_components() -> List[Dict[str, Any]]`

Find dependency conflicts between different components.

**Returns:**
- List of conflict descriptions

## Data Types

### InstallResult

Result of component installation operation.

```python
class InstallResult(NamedTuple):
    component_name: str
    component_url: str
    install_path: Path
    component_version: str
    files_installed: int
    dependencies_added: int
    success: bool
    message: str
```

### ComponentInfo

Basic component information for display.

```python
class ComponentInfo(NamedTuple):
    name: str
    version: str
    description: str
    category: str
    install_path: str
    file_count: int
    dependency_count: int
```

### ComponentDetails

Detailed component information.

```python
class ComponentDetails(NamedTuple):
    name: str
    version: str
    description: str
    category: str
    dependencies: List[str]
    dev_dependencies: List[str]
    files: List[str]
    python_requires: str
    author: Optional[str]
    license: str
    keywords: List[str]
    install_path: str
    installed_at: str
```

## Exceptions

### Component System Exceptions

All component system exceptions inherit from `ComponentError`:

```python
from zen.core.exceptions import (
    ComponentError,
    ComponentNotFoundError,
    ComponentInstallationError,
    ComponentValidationError,
    ComponentUrlError
)
```

#### ComponentError

Base exception for component system errors.

**Attributes:**
- `message`: Error message
- `component_name`: Name of component (optional)
- `details`: Additional error details (optional)

#### ComponentNotFoundError

Raised when a component is not found.

**Attributes:**
- `component_name`: Name of the missing component
- `component_url`: URL where component was expected (optional)

#### ComponentInstallationError

Raised when component installation fails.

**Attributes:**
- `component_name`: Name of component being installed (optional)
- `component_url`: URL of component being installed (optional)
- `install_path`: Target installation path (optional)

#### ComponentValidationError

Raised when component schema validation fails.

**Attributes:**
- `component_name`: Name of component with validation issues
- `validation_errors`: List of specific validation errors

#### ComponentUrlError

Raised when component URL is invalid or inaccessible.

**Attributes:**
- `component_url`: The problematic URL
- `error_type`: Type of URL error (invalid, not_found, access_denied, etc.)

## Usage Examples

### Basic Component Usage

```python
from zen.core.component_registry import ComponentRegistry
from zen.core.component_installer import ComponentInstaller

# Initialize components
registry = ComponentRegistry()
installer = ComponentInstaller(registry)

# List installed components
components = registry.list_components()
print(f"Installed components: {[c.name for c in components]}")

# Install a component
result = installer.install_component(
    component_url="https://github.com/user/email-validator",
    install_path="src/utils",
    install_dependencies=True
)

if result.success:
    print(f"Component installed at: {result.install_path}")
else:
    print(f"Installation failed: {result.message}")
```

### Component Validation

```python
from zen.core.component_validator import ComponentValidator

validator = ComponentValidator(registry)

# Validate a specific component
component = registry.get_component("email-validator")
result = validator.validate_component(component)

if result.is_valid:
    print("Component is valid")
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
    
    print("Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

### Custom Component Creation

```python
from zen.schemas.component import ComponentSchema, ComponentFile

# Create a custom component
custom_component = ComponentSchema(
    name="my-custom-component",
    version="1.0.0",
    description="My custom utility component",
    category="utils",
    dependencies=["requests>=2.25.0"],
    files=[
        ComponentFile(
            name="utils.py",
            path="src/utils/utils.py",
            content='import requests\n\ndef fetch_data(url):\n    return requests.get(url).json()'
        )
    ]
)

# Register the component
registry.register_component(custom_component)

# Install the component
result = installer.install_component(
    component_url="local://my-custom-component"
)
```

### Programmatic Component Management

```python
from zen.core.component_utils import ComponentMaintenanceUtils

utils = ComponentMaintenanceUtils()

# Generate comprehensive report
report = utils.generate_all_components_report()

print(f"Total components: {report['component_count']}")
print(f"Valid components: {report['summary']['valid_components']}")
print(f"Components with errors: {report['summary']['components_with_errors']}")

# Check specific component
component_report = utils.generate_component_report("email-validator")
print(f"Component integrity: {component_report['integrity']['is_valid']}")
```

## Configuration

### Environment Variables

The component system respects these environment variables:

- `ZEN_COMPONENT_CACHE_DIR`: Directory for component caching
- `ZEN_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ZEN_DEFAULT_INSTALL_PATH`: Default installation path for components

### Registry Configuration

```python
# Custom component registry configuration
registry = ComponentRegistry(
    cache_dir=Path("~/.zen/cache"),
    default_install_path="src/components"
)
```

## Performance Considerations

### Component Caching

Components are cached after first download for performance:

```python
# Clear component cache
registry.clear_cache()

# Reload component registry
registry.reload_registry()
```

### Large Component Handling

For components with many files:

```python
# Use streaming for large files
result = installer.install_component(
    component_url="https://github.com/user/large-component",
    stream_large_files=True  # Process files in chunks
)
```

## Thread Safety

The component system is thread-safe for read operations:

```python
import threading
from concurrent.futures import ThreadPoolExecutor

def install_component(url, path):
    return installer.install_component(url, install_path=path)

# Safe to use in multiple threads
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(install_component, f"https://github.com/user/component-{i}", f"src/utils{i}")
        for i in range(10)
    ]
    
    results = [future.result() for future in futures]
```

## Debugging

### Enable Debug Logging

```python
import logging
from zen.core.logger import setup_logging

setup_logging(verbose=True)
logger = logging.getLogger("zen.core.component_registry")
logger.setLevel(logging.DEBUG)
```

### Component Inspection

```python
# Inspect component details
component = registry.get_component("email-validator")

print(f"Component files: {len(component.files)}")
print(f"Dependencies: {component.dependencies}")
print(f"Install path: {component.install_path}")
```