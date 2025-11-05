"""
Template validation utilities for zen.

This module provides comprehensive validation for template schemas,
file integrity checking, and dependency validation to ensure templates
are properly structured and functional.
"""

import json
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from zen.schemas.template import TemplateSchema, TemplateFile
from zen.core.template_registry import TemplateRegistry
from zen.core.logger import get_logger
from zen.core.exceptions import TemplateValidationError, TemplateInheritanceError

logger = get_logger()


class ValidationResult:
    """Result of template validation."""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
    
    def add_error(self, message: str) -> None:
        """Add validation error."""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str) -> None:
        """Add validation warning."""
        self.warnings.append(message)
    
    def add_info(self, message: str) -> None:
        """Add validation info."""
        self.info.append(message)
    
    def merge(self, other: 'ValidationResult') -> None:
        """Merge another validation result into this one."""
        if not other.is_valid:
            self.is_valid = False
        self.errors.extend(other.errors)
        self.warnings.extend(other.warnings)
        self.info.extend(other.info)


class TemplateValidator:
    """Validates template schemas and files."""
    
    def __init__(self, registry: Optional[TemplateRegistry] = None):
        """Initialize template validator.
        
        Args:
            registry: Template registry for inheritance validation
        """
        self.registry = registry or TemplateRegistry()
    
    def validate_template(self, template: TemplateSchema, template_path: Optional[Path] = None) -> ValidationResult:
        """Validate a complete template.
        
        Args:
            template: Template schema to validate
            template_path: Optional path to template directory for file validation
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        # Validate schema structure
        schema_result = self.validate_schema(template)
        result.merge(schema_result)
        
        # Validate inheritance if applicable
        if template.extends:
            inheritance_result = self.validate_inheritance(template)
            result.merge(inheritance_result)
        
        # Validate files if template path provided
        if template_path:
            file_result = self.validate_template_files(template, template_path)
            result.merge(file_result)
        
        # Validate dependencies
        deps_result = self.validate_dependencies(template)
        result.merge(deps_result)
        
        # Validate template variables
        vars_result = self.validate_template_variables(template)
        result.merge(vars_result)
        
        return result
    
    def validate_schema(self, template: TemplateSchema) -> ValidationResult:
        """Validate template schema structure.
        
        Args:
            template: Template schema to validate
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        # Required fields validation
        if not template.name:
            result.add_error("Template name is required")
        elif not template.name.replace("-", "").replace("_", "").isalnum():
            result.add_error("Template name must contain only alphanumeric characters, hyphens, and underscores")
        
        if not template.version:
            result.add_error("Template version is required")
        elif not self._is_valid_version(template.version):
            result.add_error("Template version must follow semantic versioning (e.g., 1.0.0)")
        
        if not template.description:
            result.add_warning("Template description is recommended")
        
        # Complexity validation
        valid_complexities = {"minimal", "moderate", "industry"}
        if template.complexity not in valid_complexities:
            result.add_error(f"Template complexity must be one of: {', '.join(valid_complexities)}")
        
        # Category validation
        valid_categories = {"web", "api", "cli", "library", "data", "ml", "game"}
        if template.category not in valid_categories:
            result.add_warning(f"Template category '{template.category}' is not standard. Consider using: {', '.join(valid_categories)}")
        
        # Python version validation
        if not template.python_requires:
            result.add_warning("Python version requirement is recommended")
        elif not self._is_valid_python_version(template.python_requires):
            result.add_error("Invalid Python version requirement format")
        
        # Files validation
        if not template.files:
            result.add_warning("Template has no files defined")
        else:
            file_paths = set()
            for file_info in template.files:
                if not file_info.name:
                    result.add_error("Template file must have a name")
                if not file_info.path:
                    result.add_error(f"Template file '{file_info.name}' must have a path")
                elif file_info.path in file_paths:
                    result.add_error(f"Duplicate file path: {file_info.path}")
                else:
                    file_paths.add(file_info.path)
        
        # Directories validation
        if template.directories:
            dir_paths = set()
            for directory in template.directories:
                if directory in dir_paths:
                    result.add_error(f"Duplicate directory: {directory}")
                else:
                    dir_paths.add(directory)
        
        return result
    
    def validate_inheritance(self, template: TemplateSchema) -> ValidationResult:
        """Validate template inheritance.
        
        Args:
            template: Template schema with inheritance
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        if not template.extends:
            return result
        
        try:
            # Check if parent template exists
            parent_template = self.registry.get_template(template.extends)
            
            # Validate inheritance chain doesn't create cycles
            inheritance_chain = self._get_inheritance_chain(template)
            if len(inheritance_chain) != len(set(inheritance_chain)):
                result.add_error("Circular inheritance detected")
            
            # Validate complexity hierarchy
            complexity_order = {"minimal": 0, "moderate": 1, "industry": 2}
            parent_complexity = complexity_order.get(parent_template.complexity, -1)
            child_complexity = complexity_order.get(template.complexity, -1)
            
            if child_complexity <= parent_complexity:
                result.add_warning(f"Template complexity '{template.complexity}' should be higher than parent '{parent_template.complexity}'")
            
            # Validate category compatibility
            if template.category != parent_template.category:
                result.add_warning(f"Template category '{template.category}' differs from parent '{parent_template.category}'")
            
        except KeyError:
            result.add_error(f"Parent template '{template.extends}' not found")
        except Exception as e:
            result.add_error(f"Inheritance validation failed: {e}")
        
        return result
    
    def validate_template_files(self, template: TemplateSchema, template_path: Path) -> ValidationResult:
        """Validate template files exist and are accessible.
        
        Args:
            template: Template schema
            template_path: Path to template directory
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        for file_info in template.files:
            # Check if file has content or URL
            if not file_info.content and not file_info.url and not hasattr(file_info, 'content_path'):
                result.add_error(f"File '{file_info.name}' has no content source")
                continue
            
            # If file has content_path, validate it exists
            if hasattr(file_info, 'content_path') and file_info.content_path:
                content_path = Path(file_info.content_path)
                if not content_path.is_absolute():
                    # Relative to template path
                    content_path = template_path / file_info.content_path
                
                if not content_path.exists():
                    result.add_error(f"Template file content not found: {content_path}")
                elif not content_path.is_file():
                    result.add_error(f"Template file content path is not a file: {content_path}")
                else:
                    # Validate file is readable
                    try:
                        with open(content_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                            if not content.strip():
                                result.add_warning(f"Template file '{file_info.name}' is empty")
                    except UnicodeDecodeError:
                        # Binary file, check if it's reasonable size
                        try:
                            size = content_path.stat().st_size
                            if size > 10 * 1024 * 1024:  # 10MB
                                result.add_warning(f"Template file '{file_info.name}' is very large ({size} bytes)")
                        except OSError:
                            result.add_error(f"Cannot access template file: {content_path}")
                    except Exception as e:
                        result.add_error(f"Cannot read template file '{file_info.name}': {e}")
            
            # Validate file path format
            if file_info.path.startswith('/') or '..' in file_info.path:
                result.add_error(f"Invalid file path '{file_info.path}' - must be relative and safe")
        
        return result
    
    def validate_dependencies(self, template: TemplateSchema) -> ValidationResult:
        """Validate template dependencies.
        
        Args:
            template: Template schema
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        # Validate dependency format
        all_deps = template.dependencies + template.dev_dependencies
        
        for dep in all_deps:
            if not self._is_valid_dependency_format(dep):
                result.add_error(f"Invalid dependency format: {dep}")
        
        # Check for duplicate dependencies
        if len(set(template.dependencies)) != len(template.dependencies):
            result.add_error("Duplicate dependencies found")
        
        if len(set(template.dev_dependencies)) != len(template.dev_dependencies):
            result.add_error("Duplicate development dependencies found")
        
        # Check for overlap between regular and dev dependencies
        regular_deps = {dep.split('>=')[0].split('==')[0].split('~=')[0] for dep in template.dependencies}
        dev_deps = {dep.split('>=')[0].split('==')[0].split('~=')[0] for dep in template.dev_dependencies}
        
        overlap = regular_deps.intersection(dev_deps)
        if overlap:
            result.add_warning(f"Dependencies appear in both regular and dev: {', '.join(overlap)}")
        
        return result
    
    def validate_template_variables(self, template: TemplateSchema) -> ValidationResult:
        """Validate template variables configuration.
        
        Args:
            template: Template schema
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        for var_name, var_config in template.template_vars.items():
            # Validate variable name
            if not var_name.replace('_', '').isalnum():
                result.add_error(f"Invalid variable name '{var_name}' - must be alphanumeric with underscores")
            
            # Validate variable configuration
            if isinstance(var_config, dict):
                # Advanced configuration
                if 'type' in var_config:
                    valid_types = {'str', 'int', 'float', 'bool'}
                    if var_config['type'] not in valid_types:
                        result.add_error(f"Invalid variable type '{var_config['type']}' for '{var_name}'")
                
                if 'choices' in var_config:
                    choices = var_config['choices']
                    if not isinstance(choices, list) or not choices:
                        result.add_error(f"Variable '{var_name}' choices must be a non-empty list")
                
                if 'required' in var_config and not isinstance(var_config['required'], bool):
                    result.add_error(f"Variable '{var_name}' required field must be boolean")
        
        return result
    
    def validate_template_integrity(self, template_path: Path) -> ValidationResult:
        """Validate template directory integrity.
        
        Args:
            template_path: Path to template directory
            
        Returns:
            Validation result
        """
        result = ValidationResult()
        
        if not template_path.exists():
            result.add_error(f"Template directory does not exist: {template_path}")
            return result
        
        if not template_path.is_dir():
            result.add_error(f"Template path is not a directory: {template_path}")
            return result
        
        # Check for template.json
        template_json = template_path / "template.json"
        if not template_json.exists():
            result.add_error("Template directory must contain template.json")
            return result
        
        # Validate template.json format
        try:
            with open(template_json, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            
            # Basic structure validation
            required_fields = ['name', 'version', 'description']
            for field in required_fields:
                if field not in template_data:
                    result.add_error(f"template.json missing required field: {field}")
        
        except json.JSONDecodeError as e:
            result.add_error(f"Invalid JSON in template.json: {e}")
        except Exception as e:
            result.add_error(f"Cannot read template.json: {e}")
        
        return result
    
    def _get_inheritance_chain(self, template: TemplateSchema) -> List[str]:
        """Get the full inheritance chain for a template.
        
        Args:
            template: Template schema
            
        Returns:
            List of template names in inheritance chain
        """
        chain = [template.name]
        current = template
        
        while current.extends:
            try:
                parent = self.registry.get_template(current.extends)
                chain.append(parent.name)
                current = parent
            except KeyError:
                break
        
        return chain
    
    def _is_valid_version(self, version: str) -> bool:
        """Check if version follows semantic versioning.
        
        Args:
            version: Version string to validate
            
        Returns:
            True if valid semantic version
        """
        import re
        pattern = r'^(\d+)\.(\d+)\.(\d+)(?:-([a-zA-Z0-9\-\.]+))?(?:\+([a-zA-Z0-9\-\.]+))?$'
        return bool(re.match(pattern, version))
    
    def _is_valid_python_version(self, version_spec: str) -> bool:
        """Check if Python version specification is valid.
        
        Args:
            version_spec: Python version specification
            
        Returns:
            True if valid Python version spec
        """
        import re
        pattern = r'^>=?\d+\.\d+(?:\.\d+)?$'
        return bool(re.match(pattern, version_spec))
    
    def _is_valid_dependency_format(self, dependency: str) -> bool:
        """Check if dependency format is valid.
        
        Args:
            dependency: Dependency specification
            
        Returns:
            True if valid dependency format
        """
        import re
        # Basic pattern for package names with optional version specifiers
        pattern = r'^[a-zA-Z0-9\-_\.]+(?:\[[a-zA-Z0-9\-_,]+\])?(?:[><=~!]+[\d\.]+(?:,\s*[><=~!]+[\d\.]+)*)?$'
        return bool(re.match(pattern, dependency))


class TemplateTestFramework:
    """Framework for testing templates."""
    
    def __init__(self, registry: Optional[TemplateRegistry] = None):
        """Initialize template test framework.
        
        Args:
            registry: Template registry
        """
        self.registry = registry or TemplateRegistry()
        self.validator = TemplateValidator(self.registry)
    
    def test_template(self, template_name: str, template_path: Optional[Path] = None) -> ValidationResult:
        """Test a template comprehensively.
        
        Args:
            template_name: Name of template to test
            template_path: Optional path to template directory
            
        Returns:
            Test result
        """
        result = ValidationResult()
        
        try:
            # Get template from registry
            template = self.registry.get_template(template_name)
            
            # Validate template
            validation_result = self.validator.validate_template(template, template_path)
            result.merge(validation_result)
            
            # Test template resolution
            resolution_result = self.test_template_resolution(template)
            result.merge(resolution_result)
            
            # Test template instantiation if path provided
            if template_path:
                instantiation_result = self.test_template_instantiation(template, template_path)
                result.merge(instantiation_result)
            
        except Exception as e:
            result.add_error(f"Template test failed: {e}")
        
        return result
    
    def test_template_resolution(self, template: TemplateSchema) -> ValidationResult:
        """Test template inheritance resolution.
        
        Args:
            template: Template schema
            
        Returns:
            Test result
        """
        result = ValidationResult()
        
        try:
            resolved_template = self.registry.resolve_inheritance(template)
            
            # Verify resolved template has all expected properties
            if not resolved_template.files:
                result.add_warning("Resolved template has no files")
            
            if not resolved_template.dependencies:
                result.add_info("Resolved template has no dependencies")
            
            # Check for file conflicts in inheritance
            file_paths = set()
            for file_info in resolved_template.files:
                if file_info.path in file_paths:
                    result.add_error(f"File path conflict after resolution: {file_info.path}")
                file_paths.add(file_info.path)
            
        except Exception as e:
            result.add_error(f"Template resolution failed: {e}")
        
        return result
    
    def test_template_instantiation(self, template: TemplateSchema, template_path: Path) -> ValidationResult:
        """Test template instantiation (dry run).
        
        Args:
            template: Template schema
            template_path: Path to template directory
            
        Returns:
            Test result
        """
        result = ValidationResult()
        
        try:
            # Simulate project creation without actually creating files
            resolved_template = self.registry.resolve_inheritance(template)
            
            # Test variable substitution
            test_variables = {
                "project_name": "test_project",
                "author": "Test Author",
                "description": "Test project description"
            }
            
            # Add default values for template variables
            for var_name, var_config in resolved_template.template_vars.items():
                if var_name not in test_variables:
                    if isinstance(var_config, dict):
                        test_variables[var_name] = var_config.get('default', '')
                    else:
                        test_variables[var_name] = var_config
            
            # Test file content processing
            for file_info in resolved_template.files:
                if hasattr(file_info, 'content_path') and file_info.content_path:
                    content_path = Path(file_info.content_path)
                    if not content_path.is_absolute():
                        content_path = template_path / file_info.content_path
                    
                    if content_path.exists():
                        try:
                            with open(content_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Test variable substitution
                            for var_name, var_value in test_variables.items():
                                placeholder = f"{{{{{var_name}}}}}"
                                if placeholder in content:
                                    result.add_info(f"Variable '{var_name}' found in {file_info.name}")
                        
                        except UnicodeDecodeError:
                            # Binary file, skip content testing
                            result.add_info(f"Skipping binary file: {file_info.name}")
                        except Exception as e:
                            result.add_warning(f"Cannot test file content for {file_info.name}: {e}")
            
        except Exception as e:
            result.add_error(f"Template instantiation test failed: {e}")
        
        return result
    
    def test_all_templates(self) -> Dict[str, ValidationResult]:
        """Test all templates in the registry.
        
        Returns:
            Dictionary mapping template names to test results
        """
        results = {}
        templates = self.registry.list_templates()
        
        for template in templates:
            try:
                result = self.test_template(template.name)
                results[template.name] = result
            except Exception as e:
                error_result = ValidationResult()
                error_result.add_error(f"Failed to test template: {e}")
                results[template.name] = error_result
        
        return results