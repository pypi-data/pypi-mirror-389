# Template Development Guide

## Overview

This guide covers how to create, modify, and maintain templates for the Zenive template system. Templates are structured project scaffolds that provide developers with pre-configured, working applications.

## Template Structure

### Directory Layout

Each template is organized in a specific directory structure:

```
zen/templates/my-template/
├── template.json           # Template metadata and configuration
├── app/                   # Application source files
│   ├── main.py
│   ├── models.py
│   └── config.py
├── tests/                 # Test files
│   └── test_main.py
├── deployment/            # Deployment configurations
│   ├── Dockerfile
│   └── docker-compose.yml
├── requirements.txt       # Python dependencies
├── requirements-dev.txt   # Development dependencies
├── .env.example          # Environment variables template
├── .gitignore            # Git ignore patterns
└── README.md             # Project documentation
```

### Template Metadata (template.json)

The `template.json` file defines the template's metadata, files, and configuration:

```json
{
  "name": "my-template",
  "version": "1.0.0",
  "description": "Description of what this template provides",
  "complexity": "minimal",
  "category": "web",
  "extends": null,
  "python_requires": ">=3.8",
  "author": "Your Name",
  "license": "MIT",
  "keywords": ["fastapi", "web", "api"],
  
  "dependencies": [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0"
  ],
  
  "dev_dependencies": [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0"
  ],
  
  "directories": [
    "app",
    "tests",
    "deployment"
  ],
  
  "files": [
    {
      "name": "main.py",
      "path": "app/main.py",
      "content_path": "zen/templates/my-template/app/main.py"
    },
    {
      "name": "requirements.txt",
      "path": "requirements.txt", 
      "content_path": "zen/templates/my-template/requirements.txt"
    }
  ],
  
  "template_vars": {
    "project_name": "my_project",
    "database_url": {
      "default": "sqlite:///./app.db",
      "description": "Database connection URL",
      "type": "str"
    },
    "debug_mode": {
      "default": false,
      "description": "Enable debug mode",
      "type": "bool"
    }
  }
}
```

## Creating a New Template

### Step 1: Plan Your Template

Before creating a template, define:

1. **Purpose**: What problem does this template solve?
2. **Complexity Level**: minimal, moderate, or industry
3. **Target Audience**: beginners, production teams, enterprise
4. **Key Features**: What will be included?
5. **Dependencies**: What packages are required?

### Step 2: Create Directory Structure

```bash
# Create template directory
mkdir -p zen/templates/my-template

# Create subdirectories
mkdir -p zen/templates/my-template/{app,tests,deployment,docs}
```

### Step 3: Write Template Files

Create functional, working code files. **Important**: Never create empty placeholder files. Every file must contain real, working code.

#### Example: app/main.py
```python
"""
{{project_name}} - FastAPI Application

This is the main application file for {{project_name}}.
Generated from template: {{template_name}}
"""

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create FastAPI application
app = FastAPI(
    title="{{project_name}}",
    description="API for {{project_name}}",
    version="1.0.0"
)

# Pydantic models
class Item(BaseModel):
    id: Optional[int] = None
    name: str
    description: Optional[str] = None
    price: float
    
class ItemCreate(BaseModel):
    name: str
    description: Optional[str] = None
    price: float

# In-memory storage (replace with database in production)
items_db: List[Item] = []
next_id = 1

@app.get("/")
async def root():
    """Root endpoint returning API information."""
    return {
        "message": "Welcome to {{project_name}} API",
        "version": "1.0.0",
        "docs": "/docs"
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}

@app.get("/items", response_model=List[Item])
async def get_items():
    """Get all items."""
    return items_db

@app.get("/items/{item_id}", response_model=Item)
async def get_item(item_id: int):
    """Get a specific item by ID."""
    for item in items_db:
        if item.id == item_id:
            return item
    raise HTTPException(status_code=404, detail="Item not found")

@app.post("/items", response_model=Item)
async def create_item(item: ItemCreate):
    """Create a new item."""
    global next_id
    
    new_item = Item(
        id=next_id,
        name=item.name,
        description=item.description,
        price=item.price
    )
    
    items_db.append(new_item)
    next_id += 1
    
    logger.info(f"Created item: {new_item.name}")
    return new_item

@app.put("/items/{item_id}", response_model=Item)
async def update_item(item_id: int, item: ItemCreate):
    """Update an existing item."""
    for i, existing_item in enumerate(items_db):
        if existing_item.id == item_id:
            updated_item = Item(
                id=item_id,
                name=item.name,
                description=item.description,
                price=item.price
            )
            items_db[i] = updated_item
            logger.info(f"Updated item: {item_id}")
            return updated_item
    
    raise HTTPException(status_code=404, detail="Item not found")

@app.delete("/items/{item_id}")
async def delete_item(item_id: int):
    """Delete an item."""
    for i, item in enumerate(items_db):
        if item.id == item_id:
            deleted_item = items_db.pop(i)
            logger.info(f"Deleted item: {item_id}")
            return {"message": f"Item {item_id} deleted successfully"}
    
    raise HTTPException(status_code=404, detail="Item not found")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
```### St
ep 4: Create Template Configuration

Write the `template.json` file with complete metadata:

```json
{
  "name": "my-template",
  "version": "1.0.0",
  "description": "A comprehensive FastAPI template with CRUD operations",
  "complexity": "minimal",
  "category": "web",
  "extends": null,
  "python_requires": ">=3.8",
  "author": "Your Name",
  "license": "MIT",
  "keywords": ["fastapi", "crud", "api", "rest"],
  
  "dependencies": [
    "fastapi>=0.104.0",
    "uvicorn[standard]>=0.24.0",
    "pydantic>=2.5.0"
  ],
  
  "dev_dependencies": [
    "pytest>=7.4.0",
    "pytest-asyncio>=0.21.0",
    "httpx>=0.25.0",
    "black>=23.0.0",
    "ruff>=0.1.0"
  ],
  
  "directories": [
    "app",
    "tests"
  ],
  
  "files": [
    {
      "name": "main.py",
      "path": "app/main.py",
      "content_path": "zen/templates/my-template/app/main.py"
    },
    {
      "name": "requirements.txt",
      "path": "requirements.txt",
      "content_path": "zen/templates/my-template/requirements.txt"
    },
    {
      "name": "test_main.py",
      "path": "tests/test_main.py",
      "content_path": "zen/templates/my-template/tests/test_main.py"
    },
    {
      "name": "README.md",
      "path": "README.md",
      "content_path": "zen/templates/my-template/README.md"
    }
  ],
  
  "template_vars": {
    "project_name": "my_project",
    "project_description": {
      "default": "A FastAPI project",
      "description": "Brief description of the project",
      "type": "str"
    },
    "author_name": {
      "default": "Developer",
      "description": "Author name for the project",
      "type": "str"
    },
    "include_examples": {
      "default": true,
      "description": "Include example CRUD operations",
      "type": "bool"
    }
  }
}
```

### Step 5: Test Your Template

```bash
# Validate template structure
zenive validate -t my-template

# Test template creation
zenive create test-project -t my-template

# Verify the created project works
cd test-project
pip install -r requirements.txt
uvicorn app.main:app --reload
```

## Template Inheritance

Templates can inherit from other templates to build complexity gradually.

### Creating an Extended Template

```json
{
  "name": "my-advanced-template",
  "version": "1.0.0",
  "description": "Advanced template extending my-template",
  "complexity": "moderate",
  "extends": "my-template",
  
  "dependencies": [
    "sqlalchemy>=2.0.0",
    "alembic>=1.12.0",
    "python-jose[cryptography]>=3.3.0"
  ],
  
  "files": [
    {
      "name": "database.py",
      "path": "app/core/database.py",
      "content_path": "zen/templates/my-advanced-template/app/core/database.py"
    },
    {
      "name": "auth.py",
      "path": "app/core/auth.py",
      "content_path": "zen/templates/my-advanced-template/app/core/auth.py"
    }
  ]
}
```

### Inheritance Rules

1. **Files**: Child template files are added to parent files
2. **Dependencies**: Child dependencies are merged with parent dependencies
3. **Directories**: Child directories are added to parent directories
4. **Variables**: Child variables override parent variables with same name
5. **Metadata**: Child metadata takes precedence

## Template Variables

### Variable Types

Templates support several variable types for customization:

```json
{
  "template_vars": {
    "string_var": "default_value",
    
    "advanced_string": {
      "default": "default_value",
      "description": "Description for user",
      "type": "str"
    },
    
    "integer_var": {
      "default": 8000,
      "description": "Port number",
      "type": "int"
    },
    
    "boolean_var": {
      "default": true,
      "description": "Enable feature",
      "type": "bool"
    },
    
    "choice_var": {
      "default": "postgresql",
      "description": "Database type",
      "type": "str",
      "choices": ["postgresql", "mysql", "sqlite"]
    },
    
    "required_var": {
      "description": "Required configuration",
      "type": "str",
      "required": true
    }
  }
}
```

### Using Variables in Files

Variables are substituted using double curly braces:

```python
# In template files
DATABASE_URL = "{{database_url}}"
PROJECT_NAME = "{{project_name}}"
DEBUG = {{debug_mode}}

# String interpolation
app = FastAPI(
    title="{{project_name}} API",
    description="{{project_description}}",
    version="1.0.0"
)
```

### Variable Naming Conventions

- Use `snake_case` for variable names
- Use descriptive names: `database_url` not `db_url`
- Group related variables: `auth_secret_key`, `auth_algorithm`
- Provide sensible defaults
- Include helpful descriptions

## Best Practices

### Code Quality

1. **Functional Code**: Every file must contain working, functional code
2. **Real Examples**: Include realistic examples, not placeholder comments
3. **Error Handling**: Implement proper error handling patterns
4. **Documentation**: Add docstrings and comments explaining the code
5. **Type Hints**: Use Python type hints throughout
6. **Testing**: Include comprehensive tests

### Template Design

1. **Progressive Complexity**: Build templates that extend simpler ones
2. **Modular Structure**: Organize code into logical modules
3. **Configuration**: Use environment variables for configuration
4. **Security**: Follow security best practices from the start
5. **Performance**: Consider performance implications
6. **Maintainability**: Write code that's easy to maintain and extend

### File Organization

1. **Consistent Structure**: Follow established patterns across templates
2. **Logical Grouping**: Group related files in appropriate directories
3. **Clear Naming**: Use descriptive file and directory names
4. **Separation of Concerns**: Keep different aspects in separate files

### Dependencies

1. **Minimal Dependencies**: Only include necessary packages
2. **Version Pinning**: Use appropriate version constraints
3. **Security**: Keep dependencies up to date
4. **Compatibility**: Ensure dependencies work together
5. **Documentation**: Document why each dependency is needed

## Validation and Testing

### Template Validation

```bash
# Validate template structure
zenive validate -t my-template

# Validate all templates
zenive validate --all

# Run comprehensive tests
zenive validate -t my-template --test
```

### Manual Testing

1. **Create Test Project**: Generate a project from your template
2. **Install Dependencies**: Verify all dependencies install correctly
3. **Run Application**: Ensure the application starts and works
4. **Test Features**: Verify all included features function properly
5. **Check Documentation**: Ensure README and docs are accurate

### Automated Testing

Create tests for your template:

```python
# tests/test_template.py
import pytest
from pathlib import Path
from zen.core.template_registry import TemplateRegistry
from zen.core.project_initializer import ProjectInitializer

def test_my_template_creation():
    """Test that my-template creates a working project."""
    registry = TemplateRegistry()
    initializer = ProjectInitializer(registry)
    
    # Test template exists
    template = registry.get_template("my-template")
    assert template is not None
    
    # Test template validation
    from zen.core.template_validator import TemplateValidator
    validator = TemplateValidator(registry)
    result = validator.validate_template(template)
    assert result.is_valid
    
    # Test project creation (dry run)
    # Add specific tests for your template
```

## Maintenance

### Updating Templates

1. **Version Bumping**: Update version in template.json
2. **Dependency Updates**: Keep dependencies current
3. **Security Patches**: Apply security updates promptly
4. **Feature Additions**: Add new features thoughtfully
5. **Breaking Changes**: Document breaking changes clearly

### Monitoring Template Health

```bash
# Check template integrity
zenive validate --all

# Generate template reports
python -c "
from zen.core.template_utils import TemplateMaintenanceUtils
utils = TemplateMaintenanceUtils()
report = utils.generate_all_templates_report()
print(report)
"
```

### Documentation Updates

Keep documentation current:
- Update README files when features change
- Maintain accurate setup instructions
- Document new configuration options
- Update troubleshooting guides

## Advanced Topics

### Custom Template Variables

For complex customization needs:

```json
{
  "template_vars": {
    "database_config": {
      "default": {
        "host": "localhost",
        "port": 5432,
        "name": "{{project_name}}_db"
      },
      "description": "Database configuration",
      "type": "dict"
    }
  }
}
```

### Conditional File Inclusion

Use template variables to conditionally include files:

```json
{
  "files": [
    {
      "name": "docker-compose.yml",
      "path": "docker-compose.yml",
      "content_path": "zen/templates/my-template/docker-compose.yml",
      "condition": "{{include_docker}}"
    }
  ]
}
```

### Template Hooks

For advanced template processing:

```python
# In template files, use Python code blocks
# {{#if include_auth}}
from app.core.auth import get_current_user
# {{/if}}

@app.get("/protected")
# {{#if include_auth}}
async def protected_route(current_user: User = Depends(get_current_user)):
# {{else}}
async def protected_route():
# {{/if}}
    return {"message": "This is a protected route"}
```

## Contributing Templates

### Submission Process

1. **Create Template**: Follow this guide to create your template
2. **Test Thoroughly**: Ensure template works in various scenarios
3. **Document**: Provide comprehensive documentation
4. **Submit PR**: Create pull request with template and documentation
5. **Review Process**: Address feedback from maintainers

### Template Guidelines

Templates should:
- Solve a real problem or use case
- Follow established patterns and conventions
- Include comprehensive documentation
- Be thoroughly tested
- Follow security best practices
- Be maintainable and extensible

### Community Standards

- Use clear, descriptive names
- Follow Python and FastAPI best practices
- Include proper error handling
- Provide realistic examples
- Document configuration options
- Include appropriate tests

## Troubleshooting

### Common Issues

#### Template Not Loading
```
Error: Template 'my-template' not found
```
**Solution**: Ensure template.json exists and is valid JSON.

#### File Path Errors
```
Error: Template file content not found: path/to/file
```
**Solution**: Verify content_path in template.json points to existing files.

#### Variable Substitution Errors
```
Error: Variable 'undefined_var' not found
```
**Solution**: Ensure all variables used in files are defined in template_vars.

#### Inheritance Errors
```
Error: Parent template 'parent-template' not found
```
**Solution**: Verify parent template exists and is properly named.

### Debugging Tips

1. **Validate Early**: Run `zenive validate` frequently during development
2. **Test Incrementally**: Test template after each major change
3. **Check Logs**: Review error messages carefully
4. **Use Simple Variables**: Start with simple string variables
5. **Verify Paths**: Double-check all file paths in template.json

For more help:
- Check existing templates for examples
- Review validation error messages
- Test with minimal configurations first
- Ask for help in community forums