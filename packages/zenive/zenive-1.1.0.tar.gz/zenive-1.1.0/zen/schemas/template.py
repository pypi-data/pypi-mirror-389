"""
Template schema for zen - project template system.

This module defines the schema for project templates that can create complete
project structures with boilerplate code, configuration files, and dependencies.
Templates support inheritance, allowing complex templates to build upon simpler ones.

Supported template sources:
- Local file paths (preferred for built-in templates)
- GitHub repositories 
- HTTP/HTTPS URLs
- Template inheritance and merging
"""
from __future__ import annotations

import json
import re
import string
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator, model_validator


class TemplateFile(BaseModel):
    """Represents a file in a template.
    
    Files can either contain embedded content or reference external files.
    Template variables in content will be substituted during project creation.
    """
    name: str = Field(..., description="Name of the file")
    path: str = Field(..., description="Target path where file should be installed in the project")
    content: Optional[str] = Field(None, description="File content (embedded)")
    content_path: Optional[str] = Field(None, description="Path to template file in Zenive repo")
    url: Optional[str] = Field(None, description="URL to fetch file content from")
    executable: bool = Field(default=False, description="Whether the file should be executable")
    template_vars: Dict[str, Any] = Field(default_factory=dict, description="File-specific template variables")

    @model_validator(mode='before')
    @classmethod
    def require_content_source(cls, values):
        """Ensure at least one content source is provided."""
        if isinstance(values, dict):
            content = values.get("content")
            content_path = values.get("content_path") 
            url = values.get("url")
            if not any([content, content_path, url]):
                raise ValueError("Either 'content', 'content_path', or 'url' must be provided for each file")
        return values


class TemplateSchema(BaseModel):
    """Schema for project templates."""
    name: str = Field(..., description="Template name")
    version: str = Field(..., description="Template version")
    description: str = Field(..., description="Template description")
    category: str = Field(default="web", description="Template category")
    complexity: str = Field(..., description="Template complexity level (minimal, moderate, industry)")
    
    # Template inheritance
    extends: Optional[str] = Field(None, description="Base template to inherit from")
    
    # Dependencies
    dependencies: List[str] = Field(default_factory=list, description="Python package dependencies")
    dev_dependencies: List[str] = Field(default_factory=list, description="Development dependencies")
    
    # Files and structure
    files: List[TemplateFile] = Field(default_factory=list, description="List of template files")
    directories: List[str] = Field(default_factory=list, description="Directories to create")
    
    # Configuration
    python_requires: str = Field(default=">=3.8", description="Python version requirement")
    template_vars: Dict[str, Any] = Field(default_factory=dict, description="Global template variables")
    
    # Metadata
    author: Optional[str] = Field(None, description="Template author")
    license: str = Field(default="MIT", description="Template license")
    keywords: List[str] = Field(default_factory=list, description="Template keywords")

    @validator('name')
    def validate_name(cls, v):
        """Validate template name format."""
        if not v or not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('Template name must be alphanumeric with optional hyphens/underscores')
        return v.lower()

    @validator('version')
    def validate_version(cls, v):
        """Validate version format (basic semver)."""
        if not re.match(r'^\d+\.\d+\.\d+', v):
            raise ValueError('Version must follow semantic versioning (e.g., 1.0.0)')
        return v

    @validator('complexity')
    def validate_complexity(cls, v):
        """Validate complexity level."""
        valid_levels = ['minimal', 'moderate', 'industry']
        if v not in valid_levels:
            raise ValueError(f'Complexity must be one of: {", ".join(valid_levels)}')
        return v

    @validator('python_requires')
    def validate_python_requires(cls, v):
        """Validate Python version requirement format."""
        if not re.match(r'^>=?\d+\.\d+', v):
            raise ValueError('Python requires must be in format ">=3.8" or "3.8"')
        return v


class TemplateVariableSubstitution:
    """Handles template variable substitution in file content and paths."""
    
    def __init__(self, variables: Dict[str, Any]):
        """Initialize with template variables.
        
        Args:
            variables: Dictionary of template variables to substitute
        """
        self.variables = variables
        self.template = string.Template("")
    
    def substitute_content(self, content: str) -> str:
        """Substitute template variables in content.
        
        Supports both ${var} and {{var}} syntax for compatibility.
        
        Args:
            content: Content with template variables
            
        Returns:
            Content with variables substituted
        """
        if not content:
            return content
            
        # Convert {{var}} to ${var} for string.Template compatibility
        converted_content = re.sub(r'\{\{(\w+)\}\}', r'${\1}', content)
        
        try:
            template = string.Template(converted_content)
            return template.safe_substitute(self.variables)
        except (KeyError, ValueError) as e:
            # If substitution fails, return original content
            return content
    
    def substitute_path(self, path: str) -> str:
        """Substitute template variables in file paths.
        
        Args:
            path: Path with template variables
            
        Returns:
            Path with variables substituted
        """
        return self.substitute_content(path)
    
    def get_missing_variables(self, content: str) -> List[str]:
        """Get list of template variables that are missing values.
        
        Args:
            content: Content to check for variables
            
        Returns:
            List of missing variable names
        """
        # Find all template variables in content
        var_pattern = r'\$\{(\w+)\}|\{\{(\w+)\}\}'
        matches = re.findall(var_pattern, content)
        
        # Flatten the matches (regex returns tuples)
        variables = [match[0] or match[1] for match in matches]
        
        # Return variables that don't have values
        return [var for var in variables if var not in self.variables]


class TemplateInheritanceResolver:
    """Handles template inheritance and merging."""
    
    def __init__(self, template_loader_func):
        """Initialize with a function to load templates by name.
        
        Args:
            template_loader_func: Function that takes template name and returns TemplateSchema
        """
        self.load_template = template_loader_func
        self._resolution_stack = []
    
    def resolve_inheritance(self, template: TemplateSchema) -> TemplateSchema:
        """Resolve template inheritance by merging with base templates.
        
        Args:
            template: Template to resolve inheritance for
            
        Returns:
            Resolved template with inheritance applied
            
        Raises:
            ValueError: If circular inheritance is detected
        """
        if not template.extends:
            return template
        
        # Check for circular inheritance
        if template.name in self._resolution_stack:
            cycle = " -> ".join(self._resolution_stack + [template.name])
            raise ValueError(f"Circular template inheritance detected: {cycle}")
        
        self._resolution_stack.append(template.name)
        
        try:
            # Load and resolve base template
            base_template = self.load_template(template.extends)
            resolved_base = self.resolve_inheritance(base_template)
            
            # Merge templates
            merged_template = self._merge_templates(resolved_base, template)
            
            return merged_template
        finally:
            self._resolution_stack.pop()
    
    def _merge_templates(self, base: TemplateSchema, child: TemplateSchema) -> TemplateSchema:
        """Merge child template with base template.
        
        Args:
            base: Base template to inherit from
            child: Child template that extends base
            
        Returns:
            Merged template
        """
        # Start with base template data
        merged_data = base.dict()
        
        # Override with child template data
        child_data = child.dict()
        
        # Merge lists (dependencies, files, directories, keywords)
        for list_field in ['dependencies', 'dev_dependencies', 'files', 'directories', 'keywords']:
            base_items = merged_data.get(list_field, [])
            child_items = child_data.get(list_field, [])
            
            if list_field == 'files':
                # For files, merge by path - child files override base files with same path
                merged_files = {f['path']: f for f in base_items}
                for child_file in child_items:
                    merged_files[child_file['path']] = child_file
                merged_data[list_field] = list(merged_files.values())
            else:
                # For other lists, combine and deduplicate
                merged_items = list(dict.fromkeys(base_items + child_items))
                merged_data[list_field] = merged_items
        
        # Merge dictionaries (template_vars)
        for dict_field in ['template_vars']:
            base_dict = merged_data.get(dict_field, {})
            child_dict = child_data.get(dict_field, {})
            merged_data[dict_field] = {**base_dict, **child_dict}
        
        # Override scalar fields with child values
        scalar_fields = ['name', 'version', 'description', 'category', 'complexity', 
                        'python_requires', 'author', 'license']
        for field in scalar_fields:
            if field in child_data and child_data[field] is not None:
                merged_data[field] = child_data[field]
        
        # Clear extends field in merged template
        merged_data['extends'] = None
        
        return TemplateSchema(**merged_data)


class TemplateValidator:
    """Validates template definitions and content."""
    
    @staticmethod
    def validate_template_structure(template: TemplateSchema) -> List[str]:
        """Validate template structure and return list of issues.
        
        Args:
            template: Template to validate
            
        Returns:
            List of validation error messages
        """
        issues = []
        
        # Check for required files based on complexity
        if template.complexity == 'minimal':
            required_files = ['main.py', 'requirements.txt', 'README.md']
        elif template.complexity == 'moderate':
            required_files = ['main.py', 'requirements.txt', 'README.md', 'docker-compose.yml']
        else:  # industry
            required_files = ['main.py', 'requirements.txt', 'README.md', 'Dockerfile', 'docker-compose.yml']
        
        template_paths = [f.path for f in template.files]
        for required_file in required_files:
            if not any(required_file in path for path in template_paths):
                issues.append(f"Missing required file for {template.complexity} template: {required_file}")
        
        # Validate file paths
        for file in template.files:
            if '..' in file.path:
                issues.append(f"File path contains '..' which is not allowed: {file.path}")
            if file.path.startswith('/'):
                issues.append(f"File path should be relative, not absolute: {file.path}")
        
        # Validate directories
        for directory in template.directories:
            if '..' in directory:
                issues.append(f"Directory path contains '..' which is not allowed: {directory}")
            if directory.startswith('/'):
                issues.append(f"Directory path should be relative, not absolute: {directory}")
        
        return issues
    
    @staticmethod
    def validate_template_variables(template: TemplateSchema, variables: Dict[str, Any]) -> List[str]:
        """Validate that all required template variables are provided.
        
        Args:
            template: Template to validate
            variables: Provided template variables
            
        Returns:
            List of missing variable names
        """
        substitution = TemplateVariableSubstitution(variables)
        missing_vars = set()
        
        # Check global template variables
        for var_name in template.template_vars:
            if var_name not in variables:
                missing_vars.add(var_name)
        
        # Check file content for missing variables
        for file in template.files:
            if file.content:
                missing_in_file = substitution.get_missing_variables(file.content)
                missing_vars.update(missing_in_file)
            
            # Check file path for variables
            missing_in_path = substitution.get_missing_variables(file.path)
            missing_vars.update(missing_in_path)
        
        return list(missing_vars)


def load_template_from_json(json_content: str, base: Optional[str] = None) -> TemplateSchema:
    """Load template from JSON string.
    
    Args:
        json_content: JSON string containing template definition
        base: Optional base path/URL for resolving relative file paths
        
    Returns:
        TemplateSchema instance
        
    Raises:
        ValueError: If JSON is invalid or template schema is invalid
    """
    try:
        data = json.loads(json_content)
        template = TemplateSchema(**data)
        return template
    except json.JSONDecodeError as e:
        raise ValueError(f"Invalid JSON: {e}")
    except Exception as e:
        raise ValueError(f"Invalid template schema: {e}")


def create_sample_template_json() -> str:
    """Create a sample template JSON for testing."""
    sample = {
        "name": "fastapi-minimal",
        "version": "1.0.0",
        "description": "Minimal FastAPI project template",
        "category": "web",
        "complexity": "minimal",
        "dependencies": [
            "fastapi>=0.104.0",
            "uvicorn[standard]>=0.24.0",
            "pydantic>=2.5.0"
        ],
        "files": [
            {
                "name": "main.py",
                "path": "app/main.py",
                "content_path": "templates/fastapi-minimal/app/main.py"
            },
            {
                "name": "requirements.txt",
                "path": "requirements.txt", 
                "content_path": "templates/fastapi-minimal/requirements.txt"
            },
            {
                "name": "README.md",
                "path": "README.md",
                "content_path": "templates/fastapi-minimal/README.md"
            }
        ],
        "directories": [
            "app",
            "tests"
        ],
        "template_vars": {
            "project_name": "my-fastapi-project",
            "author": "Developer"
        },
        "author": "Zenive",
        "license": "MIT"
    }
    return json.dumps(sample, indent=2)