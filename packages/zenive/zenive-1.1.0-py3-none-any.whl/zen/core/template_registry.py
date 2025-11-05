"""
Template registry for zen - manages and loads project templates.

This module provides the TemplateRegistry class that handles template discovery,
loading, inheritance resolution, and management of available project templates.
"""

import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Any
from zen.schemas.template import (
    TemplateSchema, 
    TemplateInheritanceResolver,
    TemplateValidator,
    load_template_from_json
)
from zen.schemas.component import fetch_file_content
from zen.core.logger import get_logger
from zen.core.exceptions import ConfigurationError

logger = get_logger()


class TemplateRegistry:
    """Manages available project templates."""
    
    def __init__(self, template_dir: Optional[str] = None):
        """Initialize template registry.
        
        Args:
            template_dir: Directory containing template definitions. 
                         Defaults to 'templates' in the zen package directory.
        """
        self.templates: Dict[str, TemplateSchema] = {}
        self.template_dir = self._get_template_directory(template_dir)
        self.inheritance_resolver = TemplateInheritanceResolver(self._load_template_by_name)
        
        # Load built-in templates
        self._load_builtin_templates()
        
        logger.debug(f"Template registry initialized with {len(self.templates)} templates")
    
    def _get_template_directory(self, template_dir: Optional[str]) -> Path:
        """Get the template directory path."""
        if template_dir:
            return Path(template_dir).resolve()
        
        # Default to templates directory in zen package
        zen_package_dir = Path(__file__).parent.parent
        return zen_package_dir / "templates"
    
    def register_template(self, template: TemplateSchema) -> None:
        """Register a template in the registry.
        
        Args:
            template: Template to register
            
        Raises:
            ValueError: If template validation fails
        """
        # Validate template structure
        issues = TemplateValidator.validate_template_structure(template)
        if issues:
            raise ValueError(f"Template validation failed: {'; '.join(issues)}")
        
        self.templates[template.name] = template
        logger.debug(f"Registered template: {template.name} v{template.version}")
    
    def get_template(self, name: str) -> TemplateSchema:
        """Get a template by name.
        
        Args:
            name: Template name
            
        Returns:
            Template schema
            
        Raises:
            KeyError: If template not found
        """
        if name not in self.templates:
            raise KeyError(f"Template '{name}' not found in registry")
        
        return self.templates[name]
    
    def list_templates(self) -> List[TemplateSchema]:
        """Get list of all available templates.
        
        Returns:
            List of template schemas
        """
        return list(self.templates.values())
    
    def list_templates_by_complexity(self, complexity: str) -> List[TemplateSchema]:
        """Get templates filtered by complexity level.
        
        Args:
            complexity: Complexity level (minimal, moderate, industry)
            
        Returns:
            List of templates matching complexity
        """
        return [t for t in self.templates.values() if t.complexity == complexity]
    
    def list_templates_by_category(self, category: str) -> List[TemplateSchema]:
        """Get templates filtered by category.
        
        Args:
            category: Template category
            
        Returns:
            List of templates matching category
        """
        return [t for t in self.templates.values() if t.category == category]
    
    def load_from_url(self, url: str) -> TemplateSchema:
        """Load template from URL.
        
        Args:
            url: URL to template JSON definition
            
        Returns:
            Loaded template schema
            
        Raises:
            ValueError: If template cannot be loaded or is invalid
        """
        try:
            logger.debug(f"Loading template from URL: {url}")
            
            # Fetch template content
            content = fetch_file_content(url)
            template = load_template_from_json(content, base=url)
            
            # Register the template
            self.register_template(template)
            
            logger.info(f"Loaded template from URL: {template.name} v{template.version}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template from URL {url}: {e}")
            raise ValueError(f"Failed to load template from {url}: {e}")
    
    def load_from_file(self, file_path: str) -> TemplateSchema:
        """Load template from local file.
        
        Args:
            file_path: Path to template JSON file
            
        Returns:
            Loaded template schema
            
        Raises:
            ValueError: If template cannot be loaded or is invalid
        """
        try:
            path = Path(file_path)
            logger.debug(f"Loading template from file: {path}")
            
            if not path.exists():
                raise FileNotFoundError(f"Template file not found: {path}")
            
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            template = load_template_from_json(content, base=str(path.parent))
            
            # Register the template
            self.register_template(template)
            
            logger.info(f"Loaded template from file: {template.name} v{template.version}")
            return template
            
        except Exception as e:
            logger.error(f"Failed to load template from file {file_path}: {e}")
            raise ValueError(f"Failed to load template from {file_path}: {e}")
    
    def resolve_inheritance(self, template: TemplateSchema) -> TemplateSchema:
        """Resolve template inheritance.
        
        Args:
            template: Template to resolve inheritance for
            
        Returns:
            Template with inheritance resolved
            
        Raises:
            ValueError: If inheritance resolution fails
        """
        try:
            return self.inheritance_resolver.resolve_inheritance(template)
        except Exception as e:
            logger.error(f"Failed to resolve inheritance for template {template.name}: {e}")
            raise ValueError(f"Template inheritance resolution failed: {e}")
    
    def get_resolved_template(self, name: str) -> TemplateSchema:
        """Get template with inheritance resolved.
        
        Args:
            name: Template name
            
        Returns:
            Template with inheritance resolved
        """
        template = self.get_template(name)
        return self.resolve_inheritance(template)
    
    def _load_template_by_name(self, name: str) -> TemplateSchema:
        """Load template by name for inheritance resolver.
        
        Args:
            name: Template name
            
        Returns:
            Template schema
        """
        return self.get_template(name)
    
    def _load_builtin_templates(self) -> None:
        """Load built-in templates from the templates directory."""
        if not self.template_dir.exists():
            logger.warning(f"Template directory not found: {self.template_dir}")
            return
        
        logger.debug(f"Loading built-in templates from: {self.template_dir}")
        
        # Look for template.json files in subdirectories
        for template_path in self.template_dir.iterdir():
            if template_path.is_dir():
                template_json = template_path / "template.json"
                if template_json.exists():
                    try:
                        self.load_from_file(str(template_json))
                    except Exception as e:
                        logger.warning(f"Failed to load template from {template_json}: {e}")
    
    def discover_templates(self, directory: str) -> List[TemplateSchema]:
        """Discover templates in a directory.
        
        Args:
            directory: Directory to search for templates
            
        Returns:
            List of discovered templates
        """
        discovered = []
        search_dir = Path(directory)
        
        if not search_dir.exists():
            logger.warning(f"Template discovery directory not found: {search_dir}")
            return discovered
        
        logger.debug(f"Discovering templates in: {search_dir}")
        
        # Recursively search for template.json files
        for template_file in search_dir.rglob("template.json"):
            try:
                template = self.load_from_file(str(template_file))
                discovered.append(template)
            except Exception as e:
                logger.warning(f"Failed to load discovered template {template_file}: {e}")
        
        logger.info(f"Discovered {len(discovered)} templates in {directory}")
        return discovered
    
    def get_template_info(self, name: str) -> Dict[str, Any]:
        """Get detailed information about a template.
        
        Args:
            name: Template name
            
        Returns:
            Dictionary with template information
        """
        template = self.get_template(name)
        resolved_template = self.resolve_inheritance(template)
        
        return {
            "name": template.name,
            "version": template.version,
            "description": template.description,
            "category": template.category,
            "complexity": template.complexity,
            "extends": template.extends,
            "dependencies": resolved_template.dependencies,
            "dev_dependencies": resolved_template.dev_dependencies,
            "file_count": len(resolved_template.files),
            "directory_count": len(resolved_template.directories),
            "python_requires": resolved_template.python_requires,
            "author": template.author,
            "license": template.license,
            "keywords": template.keywords
        }
    
    def validate_template(self, name: str, variables: Optional[Dict[str, Any]] = None) -> List[str]:
        """Validate a template and its variables.
        
        Args:
            name: Template name
            variables: Template variables to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        try:
            template = self.get_template(name)
            resolved_template = self.resolve_inheritance(template)
            
            # Validate template structure
            issues = TemplateValidator.validate_template_structure(resolved_template)
            
            # Validate template variables if provided
            if variables:
                missing_vars = TemplateValidator.validate_template_variables(resolved_template, variables)
                if missing_vars:
                    issues.extend([f"Missing template variable: {var}" for var in missing_vars])
            
            return issues
            
        except Exception as e:
            return [f"Template validation error: {e}"]
    
    def get_template_dependencies(self, name: str) -> Dict[str, List[str]]:
        """Get all dependencies for a template (including inherited).
        
        Args:
            name: Template name
            
        Returns:
            Dictionary with 'dependencies' and 'dev_dependencies' lists
        """
        resolved_template = self.get_resolved_template(name)
        
        return {
            "dependencies": resolved_template.dependencies,
            "dev_dependencies": resolved_template.dev_dependencies
        }
    
    def clear_registry(self) -> None:
        """Clear all registered templates."""
        self.templates.clear()
        logger.debug("Template registry cleared")
    
    def reload_builtin_templates(self) -> None:
        """Reload built-in templates from disk."""
        # Clear existing templates
        self.templates.clear()
        
        # Reload built-in templates
        self._load_builtin_templates()
        
        logger.info(f"Reloaded {len(self.templates)} built-in templates")


class TemplateLoader:
    """Utility class for loading template files and content."""
    
    def __init__(self, template_dir: Path):
        """Initialize template loader.
        
        Args:
            template_dir: Base directory for template files
        """
        self.template_dir = template_dir
    
    def load_template_file_content(self, template: TemplateSchema, file_name: str) -> str:
        """Load content for a specific template file.
        
        Args:
            template: Template schema
            file_name: Name of file to load content for
            
        Returns:
            File content
            
        Raises:
            FileNotFoundError: If template file not found
            ValueError: If file has no content source
        """
        # Find the file in template
        template_file = None
        for f in template.files:
            if f.name == file_name:
                template_file = f
                break
        
        if not template_file:
            raise FileNotFoundError(f"File '{file_name}' not found in template '{template.name}'")
        
        # Return embedded content if available
        if template_file.content:
            return template_file.content
        
        # Load from content_path if available
        if template_file.content_path:
            content_path = self.template_dir / template_file.content_path
            if content_path.exists():
                with open(content_path, 'r', encoding='utf-8') as f:
                    return f.read()
            else:
                raise FileNotFoundError(f"Template file not found: {content_path}")
        
        # Load from URL if available
        if template_file.url:
            try:
                return fetch_file_content(template_file.url)
            except Exception as e:
                raise ValueError(f"Failed to fetch file content from URL: {e}")
        
        raise ValueError(f"No content source available for file '{file_name}' in template '{template.name}'")
    
    def get_all_template_files_content(self, template: TemplateSchema) -> Dict[str, str]:
        """Load content for all files in a template.
        
        Args:
            template: Template schema
            
        Returns:
            Dictionary mapping file names to their content
        """
        content_map = {}
        
        for template_file in template.files:
            try:
                content = self.load_template_file_content(template, template_file.name)
                content_map[template_file.name] = content
            except Exception as e:
                logger.warning(f"Failed to load content for file '{template_file.name}': {e}")
                content_map[template_file.name] = ""
        
        return content_map