# Template System API Reference

## Overview

This document provides detailed API reference for the Zenive template system components. It covers all classes, methods, and functions available for programmatic use of the template system.

## Core Classes

### TemplateSchema

Pydantic model representing a template definition.

```python
from zen.schemas.template import TemplateSchema, TemplateFile

class TemplateSchema(BaseModel):
    name: str
    version: str
    description: str
    category: str = "web"
    complexity: str  # minimal, moderate, industry
    extends: Optional[str] = None
    dependencies: List[str] = []
    dev_dependencies: List[str] = []
    files: List[TemplateFile] = []
    directories: List[str] = []
    python_requires: str = ">=3.8"
    template_vars: Dict[str, Any] = {}
    author: Optional[str] = None
    license: str = "MIT"
    keywords: List[str] = []
```

**Fields:**
- `name`: Unique template identifier
- `version`: Semantic version string
- `description`: Human-readable description
- `category`: Template category (web, api, cli, etc.)
- `complexity`: Complexity level (minimal, moderate, industry)
- `extends`: Parent template name for inheritance
- `dependencies`: List of Python package dependencies
- `dev_dependencies`: List of development dependencies
- `files`: List of template files
- `directories`: List of directories to create
- `python_requires`: Python version requirement
- `template_vars`: Template variables for customization
- `author`: Template author name
- `license`: License identifier
- `keywords`: List of keywords for categorization

### TemplateFile

Represents a file within a template.

```python
class TemplateFile(BaseModel):
    name: str
    path: str
    content: Optional[str] = None
    url: Optional[str] = None
    executable: bool = False
    template_vars: Dict[str, Any] = {}
```

**Fields:**
- `name`: Display name of the file
- `path`: Target path in the generated project
- `content`: Direct file content (optional)
- `url`: URL to fetch content from (optional)
- `executable`: Whether file should be executable
- `template_vars`: File-specific template variables

### TemplateRegistry

Manages template discovery, loading, and inheritance resolution.

```python
from zen.core.template_registry import TemplateRegistry

registry = TemplateRegistry()
```

#### Methods

##### `register_template(template: TemplateSchema) -> None`

Register a template in the registry.

**Parameters:**
- `template`: TemplateSchema instance to register

**Example:**
```python
template = TemplateSchema(
    name="my-template",
    version="1.0.0",
    description="My custom template"
)
registry.register_template(template)
```

##### `get_template(name: str) -> TemplateSchema`

Retrieve a template by name.

**Parameters:**
- `name`: Template name

**Returns:**
- TemplateSchema instance

**Raises:**
- `KeyError`: If template not found

**Example:**
```python
template = registry.get_template("fastapi-minimal")
```

##### `list_templates() -> List[TemplateSchema]`

Get all registered templates.

**Returns:**
- List of TemplateSchema instances

**Example:**
```python
templates = registry.list_templates()
for template in templates:
    print(f"{template.name}: {template.description}")
```

##### `load_from_url(url: str) -> TemplateSchema`

Load template from URL.

**Parameters:**
- `url`: URL to template.json file

**Returns:**
- TemplateSchema instance

**Example:**
```python
template = registry.load_from_url("https://example.com/template.json")
```

##### `resolve_inheritance(template: TemplateSchema) -> TemplateSchema`

Resolve template inheritance chain.

**Parameters:**
- `template`: Template with potential inheritance

**Returns:**
- Resolved template with merged properties

**Example:**
```python
resolved = registry.resolve_inheritance(template)
```

### ProjectInitializer

Handles project creation from templates.

```python
from zen.core.project_initializer import ProjectInitializer

initializer = ProjectInitializer(registry)
```

#### Methods

##### `create_project(project_name: str, template_name: str, **kwargs) -> ProjectResult`

Create a project from a template.

**Parameters:**
- `project_name`: Name of the project to create
- `template_name`: Name of the template to use
- `template_variables`: Dict of template variables (optional)
- `install_dependencies`: Whether to install dependencies (default: True)
- `create_venv`: Whether to create virtual environment (default: True)

**Returns:**
- ProjectResult instance with creation details

**Example:**
```python
result = initializer.create_project(
    project_name="my-api",
    template_name="fastapi-minimal",
    template_variables={"author": "John Doe"},
    install_dependencies=True
)
```

##### `validate_project_name(name: str) -> List[str]`

Validate project name format.

**Parameters:**
- `name`: Project name to validate

**Returns:**
- List of validation issues (empty if valid)

**Example:**
```python
issues = initializer.validate_project_name("my-project")
if not issues:
    print("Valid project name")
```

##### `check_project_directory_availability(name: str, target_dir: Optional[str] = None) -> bool`

Check if project directory is available.

**Parameters:**
- `name`: Project name
- `target_dir`: Target directory (optional, defaults to current)

**Returns:**
- True if directory is available

**Example:**
```python
available = initializer.check_project_directory_availability("my-project")
```

### TemplateController

High-level interface for template operations.

```python
from zen.core.template_controller import TemplateController

controller = TemplateController()
```

#### Methods

##### `list_available_templates() -> List[TemplateInfo]`

Get list of available templates with basic information.

**Returns:**
- List of TemplateInfo named tuples

**Example:**
```python
templates = controller.list_available_templates()
for template in templates:
    print(f"{template.name} ({template.complexity}): {template.description}")
```

##### `get_template_details(template_name: str) -> TemplateDetails`

Get detailed information about a template.

**Parameters:**
- `template_name`: Name of the template

**Returns:**
- TemplateDetails named tuple

**Raises:**
- `KeyError`: If template not found

**Example:**
```python
details = controller.get_template_details("fastapi-moderate")
print(f"Dependencies: {details.dependencies}")
```

##### `create_project_interactive(project_name: str, template_name: Optional[str] = None) -> ProjectResult`

Create project with interactive prompts.

**Parameters:**
- `project_name`: Name of the project
- `template_name`: Template name (optional, will prompt if not provided)

**Returns:**
- ProjectResult instance

**Example:**
```python
result = controller.create_project_interactive("my-api")
```

## Validation Classes

### TemplateValidator

Validates template schemas and files.

```python
from zen.core.template_validator import TemplateValidator, ValidationResult

validator = TemplateValidator(registry)
```

#### Methods

##### `validate_template(template: TemplateSchema, template_path: Optional[Path] = None) -> ValidationResult`

Validate a complete template.

**Parameters:**
- `template`: Template schema to validate
- `template_path`: Optional path to template directory

**Returns:**
- ValidationResult instance

**Example:**
```python
result = validator.validate_template(template)
if result.is_valid:
    print("Template is valid")
else:
    for error in result.errors:
        print(f"Error: {error}")
```

##### `validate_schema(template: TemplateSchema) -> ValidationResult`

Validate template schema structure.

**Parameters:**
- `template`: Template schema

**Returns:**
- ValidationResult instance

##### `validate_inheritance(template: TemplateSchema) -> ValidationResult`

Validate template inheritance.

**Parameters:**
- `template`: Template with inheritance

**Returns:**
- ValidationResult instance

##### `validate_template_files(template: TemplateSchema, template_path: Path) -> ValidationResult`

Validate template files exist and are accessible.

**Parameters:**
- `template`: Template schema
- `template_path`: Path to template directory

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

### TemplateTestFramework

Framework for testing templates.

```python
from zen.core.template_validator import TemplateTestFramework

test_framework = TemplateTestFramework(registry)
```

#### Methods

##### `test_template(template_name: str, template_path: Optional[Path] = None) -> ValidationResult`

Test a template comprehensively.

**Parameters:**
- `template_name`: Name of template to test
- `template_path`: Optional path to template directory

**Returns:**
- ValidationResult with test results

**Example:**
```python
result = test_framework.test_template("fastapi-minimal")
```

##### `test_all_templates() -> Dict[str, ValidationResult]`

Test all templates in the registry.

**Returns:**
- Dictionary mapping template names to test results

**Example:**
```python
results = test_framework.test_all_templates()
for name, result in results.items():
    print(f"{name}: {'✓' if result.is_valid else '✗'}")
```

## Utility Classes

### TemplateIntegrityChecker

Checks template file integrity and consistency.

```python
from zen.core.template_utils import TemplateIntegrityChecker

checker = TemplateIntegrityChecker()
```

#### Methods

##### `check_template_integrity(template_name: str) -> ValidationResult`

Check integrity of a specific template.

**Parameters:**
- `template_name`: Name of template to check

**Returns:**
- ValidationResult with integrity status

##### `generate_template_checksums(template_name: str) -> Dict[str, str]`

Generate checksums for all template files.

**Parameters:**
- `template_name`: Name of template

**Returns:**
- Dictionary mapping file paths to checksums

### TemplateDependencyAnalyzer

Analyzes template dependencies and conflicts.

```python
from zen.core.template_utils import TemplateDependencyAnalyzer

analyzer = TemplateDependencyAnalyzer()
```

#### Methods

##### `analyze_template_dependencies(template_name: str) -> Dict[str, Any]`

Analyze dependencies for a template.

**Parameters:**
- `template_name`: Name of template to analyze

**Returns:**
- Dictionary with dependency analysis results

##### `find_dependency_conflicts_between_templates() -> List[Dict[str, Any]]`

Find dependency conflicts between different templates.

**Returns:**
- List of conflict descriptions

## Data Types

### ProjectResult

Result of project creation operation.

```python
class ProjectResult(NamedTuple):
    project_name: str
    project_path: Path
    template_name: str
    template_version: str
    files_created: int
    directories_created: int
    dependencies_installed: bool
    success: bool
    message: str
```

### TemplateInfo

Basic template information for display.

```python
class TemplateInfo(NamedTuple):
    name: str
    version: str
    description: str
    complexity: str
    category: str
    file_count: int
    dependency_count: int
```

### TemplateDetails

Detailed template information.

```python
class TemplateDetails(NamedTuple):
    name: str
    version: str
    description: str
    complexity: str
    category: str
    extends: Optional[str]
    dependencies: List[str]
    dev_dependencies: List[str]
    directories: List[str]
    files: List[str]
    template_vars: Dict[str, Any]
    python_requires: str
    author: Optional[str]
    license: str
    keywords: List[str]
```

## Exceptions

### Template System Exceptions

All template system exceptions inherit from `TemplateError`:

```python
from zen.core.exceptions import (
    TemplateError,
    TemplateNotFoundError,
    TemplateInheritanceError,
    ProjectCreationError,
    TemplateValidationError,
    TemplateVariableError
)
```

#### TemplateError

Base exception for template system errors.

**Attributes:**
- `message`: Error message
- `template_name`: Name of template (optional)
- `details`: Additional error details (optional)

#### TemplateNotFoundError

Raised when a template is not found in the registry.

**Attributes:**
- `template_name`: Name of the missing template

#### TemplateInheritanceError

Raised when template inheritance resolution fails.

**Attributes:**
- `template_name`: Name of template with inheritance issue
- `parent_template`: Name of parent template (optional)

#### ProjectCreationError

Raised when project creation from template fails.

**Attributes:**
- `project_name`: Name of project being created (optional)
- `template_name`: Name of template being used (optional)

#### TemplateValidationError

Raised when template schema validation fails.

**Attributes:**
- `template_name`: Name of template with validation issues
- `validation_errors`: List of specific validation errors

#### TemplateVariableError

Raised when template variable validation or substitution fails.

**Attributes:**
- `template_name`: Name of template
- `variable_name`: Name of problematic variable (optional)

## Usage Examples

### Basic Template Usage

```python
from zen.core.template_registry import TemplateRegistry
from zen.core.project_initializer import ProjectInitializer

# Initialize components
registry = TemplateRegistry()
initializer = ProjectInitializer(registry)

# List available templates
templates = registry.list_templates()
print(f"Available templates: {[t.name for t in templates]}")

# Create a project
result = initializer.create_project(
    project_name="my-api",
    template_name="fastapi-minimal",
    template_variables={
        "author": "John Doe",
        "description": "My awesome API"
    }
)

if result.success:
    print(f"Project created at: {result.project_path}")
else:
    print(f"Creation failed: {result.message}")
```

### Template Validation

```python
from zen.core.template_validator import TemplateValidator

validator = TemplateValidator(registry)

# Validate a specific template
template = registry.get_template("fastapi-minimal")
result = validator.validate_template(template)

if result.is_valid:
    print("Template is valid")
else:
    print("Validation errors:")
    for error in result.errors:
        print(f"  - {error}")
    
    print("Warnings:")
    for warning in result.warnings:
        print(f"  - {warning}")
```

### Custom Template Creation

```python
from zen.schemas.template import TemplateSchema, TemplateFile

# Create a custom template
custom_template = TemplateSchema(
    name="my-custom-template",
    version="1.0.0",
    description="My custom FastAPI template",
    complexity="minimal",
    category="web",
    dependencies=["fastapi>=0.104.0", "uvicorn>=0.24.0"],
    files=[
        TemplateFile(
            name="main.py",
            path="app/main.py",
            content='from fastapi import FastAPI\napp = FastAPI(title="{{project_name}}")'
        )
    ],
    template_vars={
        "project_name": "my_project"
    }
)

# Register the template
registry.register_template(custom_template)

# Use the template
result = initializer.create_project(
    project_name="test-project",
    template_name="my-custom-template"
)
```

### Programmatic Template Management

```python
from zen.core.template_utils import TemplateMaintenanceUtils

utils = TemplateMaintenanceUtils()

# Generate comprehensive report
report = utils.generate_all_templates_report()

print(f"Total templates: {report['template_count']}")
print(f"Valid templates: {report['summary']['valid_templates']}")
print(f"Templates with errors: {report['summary']['templates_with_errors']}")

# Check specific template
template_report = utils.generate_template_report("fastapi-minimal")
print(f"Template integrity: {template_report['integrity']['is_valid']}")
```

## Configuration

### Environment Variables

The template system respects these environment variables:

- `ZEN_TEMPLATE_PATH`: Additional paths to search for templates
- `ZEN_CACHE_DIR`: Directory for template caching
- `ZEN_LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)

### Registry Configuration

```python
# Custom template paths
registry = TemplateRegistry(
    template_paths=[
        Path("custom/templates"),
        Path("/usr/local/share/zen/templates")
    ]
)
```

## Performance Considerations

### Template Caching

Templates are cached after first load for performance:

```python
# Clear template cache
registry.clear_cache()

# Reload templates
registry.reload_templates()
```

### Large Template Handling

For templates with many files:

```python
# Use streaming for large files
result = initializer.create_project(
    project_name="large-project",
    template_name="industry-template",
    stream_large_files=True  # Process files in chunks
)
```

## Thread Safety

The template system is thread-safe for read operations:

```python
import threading
from concurrent.futures import ThreadPoolExecutor

def create_project(name, template):
    return initializer.create_project(name, template)

# Safe to use in multiple threads
with ThreadPoolExecutor(max_workers=4) as executor:
    futures = [
        executor.submit(create_project, f"project-{i}", "fastapi-minimal")
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
logger = logging.getLogger("zen.core.template_registry")
logger.setLevel(logging.DEBUG)
```

### Template Inspection

```python
# Inspect resolved template
template = registry.get_template("fastapi-moderate")
resolved = registry.resolve_inheritance(template)

print(f"Original files: {len(template.files)}")
print(f"Resolved files: {len(resolved.files)}")
print(f"Dependencies: {resolved.dependencies}")
```