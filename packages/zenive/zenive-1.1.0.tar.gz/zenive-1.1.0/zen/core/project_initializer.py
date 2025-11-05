"""
Project initializer for zen - creates projects from templates.

This module provides the ProjectInitializer class that handles creating complete
project structures from templates, including directory creation, file installation,
dependency management, and template variable substitution.
"""

import os
import stat
import subprocess
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, NamedTuple
from zen.schemas.template import (
    TemplateSchema, 
    TemplateFile,
    TemplateVariableSubstitution,
    TemplateValidator
)
from zen.core.template_registry import TemplateRegistry, TemplateLoader
from zen.core.logger import get_logger
from zen.core.exceptions import InstallationError

logger = get_logger()


class ProjectResult(NamedTuple):
    """Result of project creation."""
    project_name: str
    project_path: Path
    template_name: str
    template_version: str
    files_created: int
    directories_created: int
    dependencies_installed: bool
    success: bool
    message: str


class FileManager:
    """Handles file operations for project creation."""
    
    def __init__(self, project_path: Path):
        """Initialize file manager.
        
        Args:
            project_path: Root path of the project being created
        """
        self.project_path = project_path
    
    def create_directory(self, directory: str) -> bool:
        """Create a directory in the project.
        
        Args:
            directory: Directory path relative to project root
            
        Returns:
            True if directory was created, False if it already existed
        """
        dir_path = self.project_path / directory
        
        if dir_path.exists():
            logger.debug(f"Directory already exists: {dir_path}")
            return False
        
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Created directory: {dir_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise InstallationError(f"Failed to create directory {dir_path}: {e}")
    
    def create_file(self, file_path: str, content: str, executable: bool = False) -> None:
        """Create a file with content.
        
        Args:
            file_path: File path relative to project root
            content: File content
            executable: Whether to make file executable
            
        Raises:
            InstallationError: If file creation fails
        """
        target_path = self.project_path / file_path
        
        # Create parent directories if needed
        target_path.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(target_path, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Make executable if requested
            if executable:
                current_mode = target_path.stat().st_mode
                target_path.chmod(current_mode | stat.S_IEXEC)
            
            logger.debug(f"Created file: {target_path}")
            
        except Exception as e:
            logger.error(f"Failed to create file {target_path}: {e}")
            raise InstallationError(f"Failed to create file {target_path}: {e}")
    
    def file_exists(self, file_path: str) -> bool:
        """Check if a file exists in the project.
        
        Args:
            file_path: File path relative to project root
            
        Returns:
            True if file exists
        """
        return (self.project_path / file_path).exists()


class DependencyManager:
    """Handles dependency installation for projects."""
    
    def __init__(self, project_path: Path):
        """Initialize dependency manager.
        
        Args:
            project_path: Root path of the project
        """
        self.project_path = project_path
    
    def create_requirements_file(self, dependencies: List[str], dev_dependencies: List[str] = None) -> None:
        """Create requirements.txt and requirements-dev.txt files.
        
        Args:
            dependencies: Production dependencies
            dev_dependencies: Development dependencies
        """
        if dependencies:
            req_file = self.project_path / "requirements.txt"
            with open(req_file, 'w', encoding='utf-8') as f:
                for dep in dependencies:
                    f.write(f"{dep}\n")
            logger.debug(f"Created requirements.txt with {len(dependencies)} dependencies")
        
        if dev_dependencies:
            dev_req_file = self.project_path / "requirements-dev.txt"
            with open(dev_req_file, 'w', encoding='utf-8') as f:
                for dep in dev_dependencies:
                    f.write(f"{dep}\n")
            logger.debug(f"Created requirements-dev.txt with {len(dev_dependencies)} dependencies")
    
    def create_virtual_environment(self) -> bool:
        """Create a virtual environment for the project.
        
        Returns:
            True if virtual environment was created successfully
        """
        venv_path = self.project_path / "venv"
        
        if venv_path.exists():
            logger.debug("Virtual environment already exists")
            return True
        
        try:
            logger.progress("Creating virtual environment...")
            subprocess.run([
                sys.executable, "-m", "venv", str(venv_path)
            ], check=True, capture_output=True, text=True)
            
            logger.info("Virtual environment created successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to create virtual environment: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error creating virtual environment: {e}")
            return False
    
    def install_dependencies(self, create_venv: bool = True) -> bool:
        """Install project dependencies.
        
        Args:
            create_venv: Whether to create and use a virtual environment
            
        Returns:
            True if dependencies were installed successfully
        """
        req_file = self.project_path / "requirements.txt"
        
        if not req_file.exists():
            logger.debug("No requirements.txt found, skipping dependency installation")
            return True
        
        try:
            # Create virtual environment if requested
            if create_venv:
                if not self.create_virtual_environment():
                    logger.warning("Proceeding without virtual environment")
            
            # Determine pip executable
            if create_venv and (self.project_path / "venv").exists():
                if os.name == 'nt':  # Windows
                    pip_executable = str(self.project_path / "venv" / "Scripts" / "pip.exe")
                else:  # Unix-like
                    pip_executable = str(self.project_path / "venv" / "bin" / "pip")
            else:
                pip_executable = "pip"
            
            logger.progress("Installing dependencies...")
            
            # Install production dependencies
            subprocess.run([
                pip_executable, "install", "-r", str(req_file)
            ], check=True, capture_output=True, text=True, cwd=self.project_path)
            
            # Install development dependencies if they exist
            dev_req_file = self.project_path / "requirements-dev.txt"
            if dev_req_file.exists():
                subprocess.run([
                    pip_executable, "install", "-r", str(dev_req_file)
                ], check=True, capture_output=True, text=True, cwd=self.project_path)
            
            logger.success("Dependencies installed successfully")
            return True
            
        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to install dependencies: {e}")
            return False
        except Exception as e:
            logger.warning(f"Unexpected error installing dependencies: {e}")
            return False


class ConfigurationManager:
    """Handles project configuration and metadata."""
    
    def __init__(self, project_path: Path):
        """Initialize configuration manager.
        
        Args:
            project_path: Root path of the project
        """
        self.project_path = project_path
    
    def create_project_config(self, template: TemplateSchema, variables: Dict[str, Any]) -> None:
        """Create project configuration file.
        
        Args:
            template: Template used to create the project
            variables: Template variables used
        """
        config_dir = self.project_path / ".zen"
        config_dir.mkdir(exist_ok=True)
        
        config_data = {
            "name": variables.get("project_name", self.project_path.name),
            "version": "1.0.0",
            "description": f"Project created from {template.name} template",
            "project": {
                "name": variables.get("project_name", self.project_path.name),
                "created_from_template": template.name,
                "template_version": template.version,
                "template_variables": variables,
                "created_at": self._get_current_timestamp()
            },
            "template": {
                "name": template.name,
                "version": template.version,
                "complexity": template.complexity,
                "category": template.category,
                "extends": template.extends
            },
            "components": {},  # For future component installations
            "structure": self._get_project_structure_config(template)
        }
        
        try:
            import yaml
            config_file = config_dir / "config.yaml"
            with open(config_file, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            logger.debug("Created project configuration file")
            
        except ImportError:
            # Fallback to JSON if PyYAML not available
            import json
            config_file = config_dir / "config.json"
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config_data, f, indent=2)
            
            logger.debug("Created project configuration file (JSON)")
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp in ISO format.
        
        Returns:
            Current timestamp as ISO string
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def _get_project_structure_config(self, template: TemplateSchema) -> Dict[str, str]:
        """Get project structure configuration based on template.
        
        Args:
            template: Template schema
            
        Returns:
            Dictionary mapping categories to paths
        """
        # Default structure based on template complexity
        if template.complexity == "minimal":
            return {
                "components": "src/components",
                "utils": "src/utils",
                "models": "src/models"
            }
        elif template.complexity == "moderate":
            return {
                "components": "src/components",
                "utils": "src/utils",
                "models": "app/models",
                "schemas": "app/schemas",
                "api": "app/api",
                "core": "app/core",
                "crud": "app/crud"
            }
        else:  # industry
            return {
                "components": "src/components",
                "utils": "src/utils",
                "models": "app/models",
                "schemas": "app/schemas",
                "api": "app/api",
                "core": "app/core",
                "crud": "app/crud",
                "middleware": "app/middleware",
                "worker": "app/worker",
                "monitoring": "monitoring",
                "deployment": "deployment"
            }
    
    def create_gitignore(self, template: TemplateSchema) -> None:
        """Create .gitignore file if not provided by template.
        
        Args:
            template: Template schema
        """
        gitignore_path = self.project_path / ".gitignore"
        
        # Check if template already provides .gitignore
        has_gitignore = any(f.path == ".gitignore" for f in template.files)
        
        if has_gitignore or gitignore_path.exists():
            return
        
        # Create basic Python .gitignore
        gitignore_content = """# Byte-compiled / optimized / DLL files
__pycache__/
*.py[cod]
*$py.class

# C extensions
*.so

# Distribution / packaging
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# PyInstaller
*.manifest
*.spec

# Installer logs
pip-log.txt
pip-delete-this-directory.txt

# Unit test / coverage reports
htmlcov/
.tox/
.coverage
.coverage.*
.cache
nosetests.xml
coverage.xml
*.cover
.hypothesis/
.pytest_cache/

# Translations
*.mo
*.pot

# Django stuff:
*.log
local_settings.py
db.sqlite3

# Flask stuff:
instance/
.webassets-cache

# Scrapy stuff:
.scrapy

# Sphinx documentation
docs/_build/

# PyBuilder
target/

# Jupyter Notebook
.ipynb_checkpoints

# pyenv
.python-version

# celery beat schedule file
celerybeat-schedule

# SageMath parsed files
*.sage.py

# Environments
.env
.venv
env/
venv/
ENV/
env.bak/
venv.bak/

# Spyder project settings
.spyderproject
.spyproject

# Rope project settings
.ropeproject

# mkdocs documentation
/site

# mypy
.mypy_cache/
.dmypy.json
dmypy.json

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db
"""
        
        with open(gitignore_path, 'w', encoding='utf-8') as f:
            f.write(gitignore_content)
        
        logger.debug("Created .gitignore file")


class ProjectInitializer:
    """Handles project creation from templates."""
    
    def __init__(self, template_registry: TemplateRegistry):
        """Initialize project initializer.
        
        Args:
            template_registry: Registry containing available templates
        """
        self.registry = template_registry
    
    def create_project(self, 
                      project_name: str, 
                      template_name: str, 
                      target_directory: Optional[str] = None,
                      template_variables: Optional[Dict[str, Any]] = None,
                      install_dependencies: bool = True,
                      create_venv: bool = True) -> ProjectResult:
        """Create a new project from a template.
        
        Args:
            project_name: Name of the project to create
            template_name: Name of the template to use
            target_directory: Directory to create project in (defaults to current directory)
            template_variables: Variables for template substitution
            install_dependencies: Whether to install dependencies
            create_venv: Whether to create virtual environment
            
        Returns:
            ProjectResult with creation details
        """
        try:
            logger.step(f"Creating project '{project_name}' from template '{template_name}'")
            
            # Get and resolve template
            template = self.registry.get_resolved_template(template_name)
            logger.info(f"Using template: {template.name} v{template.version} ({template.complexity})")
            
            # Setup project path
            if target_directory:
                project_path = Path(target_directory) / project_name
            else:
                project_path = Path.cwd() / project_name
            
            project_path = project_path.resolve()
            
            # Check if project directory already exists
            if project_path.exists():
                raise InstallationError(f"Project directory already exists: {project_path}")
            
            # Prepare template variables
            variables = self._prepare_template_variables(project_name, template, template_variables)
            
            # Validate template variables
            validation_issues = TemplateValidator.validate_template_variables(template, variables)
            if validation_issues:
                raise InstallationError(f"Template validation failed: {'; '.join(validation_issues)}")
            
            # Create project directory
            project_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created project directory: {project_path}")
            
            # Initialize managers
            file_manager = FileManager(project_path)
            dependency_manager = DependencyManager(project_path)
            config_manager = ConfigurationManager(project_path)
            
            # Create directory structure
            directories_created = self._create_directory_structure(file_manager, template)
            
            # Install template files
            files_created = self._install_template_files(file_manager, template, variables)
            
            # Setup dependencies
            dependency_manager.create_requirements_file(template.dependencies, template.dev_dependencies)
            dependencies_installed = False
            if install_dependencies:
                dependencies_installed = dependency_manager.install_dependencies(create_venv)
            
            # Create project configuration
            config_manager.create_project_config(template, variables)
            config_manager.create_gitignore(template)
            
            logger.success(f"Project '{project_name}' created successfully!")
            logger.info(f"Location: {project_path}")
            logger.info(f"Files created: {files_created}")
            logger.info(f"Directories created: {directories_created}")
            
            return ProjectResult(
                project_name=project_name,
                project_path=project_path,
                template_name=template.name,
                template_version=template.version,
                files_created=files_created,
                directories_created=directories_created,
                dependencies_installed=dependencies_installed,
                success=True,
                message="Project created successfully"
            )
            
        except Exception as e:
            logger.error(f"Project creation failed: {e}")
            return ProjectResult(
                project_name=project_name,
                project_path=project_path if 'project_path' in locals() else Path(),
                template_name=template_name,
                template_version="",
                files_created=0,
                directories_created=0,
                dependencies_installed=False,
                success=False,
                message=str(e)
            )
    
    def _prepare_template_variables(self, 
                                  project_name: str, 
                                  template: TemplateSchema, 
                                  user_variables: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Prepare template variables for substitution.
        
        Args:
            project_name: Name of the project
            template: Template schema
            user_variables: User-provided variables
            
        Returns:
            Complete set of template variables
        """
        # Start with template defaults
        variables = template.template_vars.copy()
        
        # Add standard variables
        variables.update({
            "project_name": project_name,
            "project_name_snake": project_name.lower().replace("-", "_"),
            "project_name_pascal": "".join(word.capitalize() for word in project_name.replace("-", "_").split("_")),
            "project_name_kebab": project_name.lower().replace("_", "-")
        })
        
        # Override with user variables
        if user_variables:
            variables.update(user_variables)
        
        return variables
    
    def _create_directory_structure(self, file_manager: FileManager, template: TemplateSchema) -> int:
        """Create directory structure from template.
        
        Args:
            file_manager: File manager instance
            template: Template schema
            
        Returns:
            Number of directories created
        """
        logger.progress("Creating directory structure...")
        
        directories_created = 0
        for directory in template.directories:
            if file_manager.create_directory(directory):
                directories_created += 1
        
        logger.debug(f"Created {directories_created} directories")
        return directories_created
    
    def _install_template_files(self, 
                              file_manager: FileManager, 
                              template: TemplateSchema, 
                              variables: Dict[str, Any]) -> int:
        """Install template files with variable substitution.
        
        Args:
            file_manager: File manager instance
            template: Template schema
            variables: Template variables
            
        Returns:
            Number of files created
        """
        logger.progress("Installing template files...")
        
        substitution = TemplateVariableSubstitution(variables)
        # Get the specific template directory
        template_directory = self.registry.template_dir / template.name
        template_loader = TemplateLoader(template_directory)
        files_created = 0
        
        # First, install explicitly defined files from template.json
        explicit_files = set()
        for template_file in template.files:
            try:
                # Try to load from current template directory first
                content = None
                content_path = None
                
                if template_file.content_path:
                    # Try current template directory
                    content_path = template_directory / template_file.content_path
                    if content_path.exists():
                        with open(content_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                    else:
                        # Try parent template directories if this template extends another
                        original_template = self.registry.get_template(template.name)
                        if original_template.extends:
                            parent_template_dir = self.registry.template_dir / original_template.extends
                            parent_content_path = parent_template_dir / template_file.content_path
                            if parent_content_path.exists():
                                with open(parent_content_path, 'r', encoding='utf-8') as f:
                                    content = f.read()
                
                if content is None:
                    # Fallback to template loader
                    content = template_loader.load_template_file_content(template, template_file.name)
                
                # Apply variable substitution to content
                substituted_content = substitution.substitute_content(content)
                
                # Apply variable substitution to file path
                substituted_path = substitution.substitute_path(template_file.path)
                
                # Create the file
                file_manager.create_file(substituted_path, substituted_content, template_file.executable)
                files_created += 1
                explicit_files.add(template_file.content_path or template_file.name)
                
            except Exception as e:
                logger.warning(f"Failed to install file '{template_file.name}': {e}")
        
        # Second, auto-discover and install any additional files in template directory
        # that aren't explicitly listed in template.json
        if template_directory.exists():
            for file_path in template_directory.rglob('*'):
                if file_path.is_file() and file_path.name != 'template.json':
                    # Get relative path from template directory
                    relative_path = file_path.relative_to(template_directory)
                    relative_path_str = str(relative_path)
                    
                    # Skip if already processed as explicit file
                    if relative_path_str not in explicit_files:
                        try:
                            # Read file content
                            with open(file_path, 'r', encoding='utf-8') as f:
                                content = f.read()
                            
                            # Apply variable substitution to content
                            substituted_content = substitution.substitute_content(content)
                            
                            # Apply variable substitution to file path
                            substituted_path = substitution.substitute_path(relative_path_str)
                            
                            # Create the file
                            file_manager.create_file(substituted_path, substituted_content, False)
                            files_created += 1
                            
                        except Exception as e:
                            logger.warning(f"Failed to auto-install file '{relative_path_str}': {e}")
        
        logger.debug(f"Installed {files_created} files")
        return files_created
    
    def validate_project_name(self, project_name: str) -> List[str]:
        """Validate project name format.
        
        Args:
            project_name: Project name to validate
            
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        if not project_name:
            issues.append("Project name cannot be empty")
            return issues
        
        if not project_name.replace("-", "").replace("_", "").isalnum():
            issues.append("Project name must be alphanumeric with optional hyphens and underscores")
        
        if project_name.startswith("-") or project_name.startswith("_"):
            issues.append("Project name cannot start with hyphen or underscore")
        
        if project_name.endswith("-") or project_name.endswith("_"):
            issues.append("Project name cannot end with hyphen or underscore")
        
        if len(project_name) > 50:
            issues.append("Project name must be 50 characters or less")
        
        if len(project_name) < 2:
            issues.append("Project name must be at least 2 characters")
        
        # Check for reserved names
        reserved_names = ["con", "prn", "aux", "nul", "com1", "com2", "com3", "com4", 
                         "com5", "com6", "com7", "com8", "com9", "lpt1", "lpt2", 
                         "lpt3", "lpt4", "lpt5", "lpt6", "lpt7", "lpt8", "lpt9"]
        if project_name.lower() in reserved_names:
            issues.append(f"Project name '{project_name}' is reserved")
        
        return issues
    
    def check_project_directory_availability(self, project_name: str, target_directory: Optional[str] = None) -> bool:
        """Check if project directory is available.
        
        Args:
            project_name: Name of the project
            target_directory: Target directory (defaults to current directory)
            
        Returns:
            True if directory is available
        """
        if target_directory:
            project_path = Path(target_directory) / project_name
        else:
            project_path = Path.cwd() / project_name
        
        return not project_path.exists()